"""Experimental Playwright scraper for Lordfilm search pages."""

from __future__ import annotations

import argparse
import json
import os
import re
from difflib import SequenceMatcher
from urllib.parse import urljoin


BASE_URL = os.getenv("LORDFILM_BASE_URL", "https://vs.lordfilm135.ru")
SEARCH_PATH = "/search-result/"
DEFAULT_TIMEOUT = 60000
CONTENT_URL_MARKERS = ("/filmy/", "/serialy/", "/mult/", "/anime/")


def make_response(ok: bool, data=None, error: str = None, details: str = None) -> dict:
    return {
        "ok": ok,
        "data": data,
        "error": error,
        "details": details,
    }


def normalize_text(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_title(value) -> str:
    value = normalize_text(value).casefold()
    value = value.replace("ё", "е")
    return re.sub(r"[^0-9a-zа-я]+", "", value)


def parse_float(value):
    text = normalize_text(value).replace(",", ".")
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_year(value):
    match = re.search(r"(19|20)\d{2}", str(value or ""))
    if match is None:
        return None
    return int(match.group(0))


def title_similarity(left: str, right: str) -> float:
    left_key = normalize_title(left)
    right_key = normalize_title(right)
    if left_key == "" or right_key == "":
        return 0.0
    if left_key == right_key:
        return 1.0
    return SequenceMatcher(None, left_key, right_key).ratio()


def get_metric_names(ratings: dict) -> list:
    names = []
    for key, value in ratings.items():
        if value is not None:
            names.append(key)
    return names


def get_available_metrics(item: dict) -> list:
    metrics = get_metric_names(item.get("ratings") or {})
    site_metrics = item.get("site_metrics") or {}
    for key, value in site_metrics.items():
        if value is not None:
            metrics.append(key)
    return metrics


def normalize_search_card(raw: dict, query: str = "") -> dict:
    ratings = {
        "kp_score": parse_float(raw.get("kp_score")),
        "imdb_score": parse_float(raw.get("imdb_score")),
    }

    poster = raw.get("poster")
    if poster:
        poster = urljoin(BASE_URL, poster)

    title = normalize_text(raw.get("title"))
    year = parse_year(raw.get("year"))

    return {
        "title": title or None,
        "year": year,
        "country": None,
        "countries": [],
        "ratings": ratings,
        "available_metrics": get_metric_names(ratings),
        "url": raw.get("url"),
        "poster": poster,
        "source": "lordfilm_playwright",
        "match_score": round(title_similarity(query, title), 3) if query else None,
        "country_note": "Country is not present in Lordfilm search cards.",
    }


def choose_best_result(results: list, query: str) -> dict | None:
    if len(results) == 0:
        return None

    exact = [item for item in results if normalize_title(item.get("title")) == normalize_title(query)]
    if len(exact) > 0:
        return exact[0]

    return max(results, key=lambda item: item.get("match_score") or 0)


def import_playwright():
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        return make_response(
            False,
            error="missing_dependency",
            details="Install Playwright: py -m pip install playwright && py -m playwright install chromium",
        )
    return make_response(True, data={
        "sync_playwright": sync_playwright,
        "timeout_error": PlaywrightTimeoutError,
    })


def wait_for_js_challenge(page, timeout: int) -> None:
    page.goto(f"{BASE_URL}/podborki/", wait_until="domcontentloaded", timeout=timeout)
    page.wait_for_timeout(4000)


def submit_search(page, title: str, timeout: int) -> None:
    search = page.locator("form#quicksearch input[name='story']").first
    search.wait_for(state="visible", timeout=timeout)
    search.fill(title)
    page.locator("form#quicksearch").first.evaluate("form => form.submit()")
    page.wait_for_timeout(3000)


def extract_search_cards(page, query: str) -> list:
    raw_cards = page.locator(".th-item").evaluate_all(
        """cards => cards.map(card => {
            const pickText = selector => {
                const node = card.querySelector(selector);
                return node ? (node.innerText || node.textContent || "").trim() : "";
            };
            const pickAttr = (selector, attr) => {
                const node = card.querySelector(selector);
                return node ? node.getAttribute(attr) : null;
            };
            const link = card.querySelector("a[href]");
            return {
                title: pickText(".th-title") || pickAttr("img[alt]", "alt"),
                year: pickText(".th-series"),
                kp_score: pickText(".th-rate-kp span"),
                imdb_score: pickText(".th-rate-imdb span"),
                url: link ? link.href : null,
                poster: pickAttr("img[src]", "src")
            };
        })"""
    )

    results = []
    for raw in raw_cards:
        url = raw.get("url")
        if url and any(marker in url for marker in CONTENT_URL_MARKERS):
            results.append(normalize_search_card(raw, query=query))
    return results


def split_people(value: str) -> list:
    text = normalize_text(value)
    if text == "":
        return []
    return [item.strip() for item in text.split(",") if item.strip() != ""]


def parse_int(value):
    match = re.search(r"-?\d+", str(value or ""))
    if match is None:
        return None
    return int(match.group(0))


def extract_detail_data(page) -> dict:
    raw = page.locator("article.full, .full.ignore-select").first.evaluate(
        """root => {
            const text = node => node ? (node.innerText || node.textContent || "").trim() : "";
            const attr = (selector, name) => {
                const node = root.querySelector(selector);
                return node ? node.getAttribute(name) : null;
            };
            const fields = {};
            root.querySelectorAll(".flist li").forEach(li => {
                const labelNode = li.querySelector("span:first-child");
                if (!labelNode) return;
                const label = text(labelNode).replace(/:$/, "").trim();
                const clone = li.cloneNode(true);
                const first = clone.querySelector("span:first-child");
                if (first) first.remove();
                const value = text(clone);
                if (label && value) fields[label] = value;
            });
            return {
                page_title: document.title,
                heading: text(root.querySelector("h1")),
                description: text(root.querySelector("#descr, [itemprop='description'], .fdesc")),
                poster: attr(".fposter img, .fleft-img img, img[itemprop='image']", "src"),
                fields,
                categories: Array.from(root.querySelectorAll("[itemprop='genre'] a")).map(a => text(a)).filter(Boolean),
                kp_score: text(root.querySelector(".frate-kp span")),
                imdb_score: text(root.querySelector(".frate-imdb span")),
                site_likes: text(root.querySelector(".rate-plus .psc, .rate-plus")),
                site_dislikes: text(root.querySelector(".rate-minus .msc, .rate-minus"))
            };
        }"""
    )

    fields = raw.get("fields") or {}
    title = normalize_text(fields.get("Название"))
    year = parse_year(fields.get("Год выхода"))
    country = normalize_text(fields.get("Страна"))
    categories = raw.get("categories") or split_people(fields.get("Категории"))
    quality = normalize_text(fields.get("Качество"))
    director = normalize_text(fields.get("Режиссер") or fields.get("Режиссёр"))
    actors = split_people(fields.get("Актеры") or fields.get("Актёры"))
    poster = raw.get("poster")
    if poster:
        poster = urljoin(BASE_URL, poster)

    detail = {
        "detail_title": normalize_text(raw.get("heading")),
        "page_title": normalize_text(raw.get("page_title")),
        "description": normalize_text(raw.get("description")),
        "title": title or None,
        "year": year,
        "country": country or None,
        "countries": [country] if country else [],
        "quality": quality or None,
        "categories": categories,
        "genres": categories,
        "director": director or None,
        "actors": actors,
        "poster": poster,
        "ratings": {
            "kp_score": parse_float(raw.get("kp_score")),
            "imdb_score": parse_float(raw.get("imdb_score")),
        },
        "site_metrics": {
            "site_likes": parse_int(raw.get("site_likes")),
            "site_dislikes": parse_int(raw.get("site_dislikes")),
        },
        "detail_fields": fields,
    }
    return {key: value for key, value in detail.items() if value not in (None, "", [], {})}


def merge_detail_data(item: dict, detail: dict) -> dict:
    for key, value in detail.items():
        if key == "ratings":
            item.setdefault("ratings", {})
            for rating_key, rating_value in value.items():
                if rating_value is not None:
                    item["ratings"][rating_key] = rating_value
        elif key == "poster":
            if value:
                item[key] = value
        else:
            item[key] = value

    item["available_metrics"] = get_available_metrics(item)
    if item.get("country"):
        item.pop("country_note", None)
    return item


def load_detail_data(page, url: str, timeout: int) -> dict:
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        page.wait_for_timeout(2000)
    except Exception:
        return {"detail_access": "detail_unavailable"}

    text = page.locator("body").inner_text(timeout=timeout)
    lowered = text.casefold()
    if "доступен только зарегистрированным пользователям" in lowered:
        return {"detail_access": "registered_only"}
    if "обнаружена ошибка" in lowered:
        return {"detail_access": "error_page"}

    detail = extract_detail_data(page)
    detail["detail_access"] = "opened"
    return detail


def search_title(title: str, limit: int = 5, headless: bool = True, timeout: int = DEFAULT_TIMEOUT) -> dict:
    title = normalize_text(title)
    if title == "":
        return make_response(False, error="empty_title", details="Title is empty.")

    playwright = import_playwright()
    if playwright["ok"] is False:
        return playwright

    sync_playwright = playwright["data"]["sync_playwright"]
    timeout_error = playwright["data"]["timeout_error"]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page(viewport={"width": 1400, "height": 1000})
            try:
                wait_for_js_challenge(page, timeout)
                submit_search(page, title, timeout)
                results = extract_search_cards(page, query=title)
                results = results[:limit]
                best = choose_best_result(results, title)
                if best is not None and best.get("url"):
                    detail = load_detail_data(page, best["url"], timeout)
                    best = merge_detail_data(best, detail)
                    if best["detail_access"] == "registered_only":
                        best["country_note"] = (
                            "Country is not present in search cards, and the detail page is "
                            "available only for registered users."
                        )
            finally:
                browser.close()
    except timeout_error as error:
        return make_response(False, error="timeout", details=str(error))
    except Exception as error:
        return make_response(False, error="browser_error", details=str(error))

    if len(results) == 0:
        return make_response(False, error="not_found", details="No Lordfilm search results found.")

    return make_response(True, data={
        "query": title,
        "best": best,
        "results": results,
        "source_url": f"{BASE_URL}{SEARCH_PATH}",
    })


def print_search_result(result: dict) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Lordfilm by title via Playwright.")
    parser.add_argument("title", help="Movie or series title.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--headed", action="store_true", help="Run browser in headed mode.")
    args = parser.parse_args()

    result = search_title(args.title, limit=args.limit, headless=not args.headed)
    print_search_result(result)


if __name__ == "__main__":
    main()
