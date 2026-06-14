"""Scraper for public Kino-Teatr.ru movie and series pages."""

from __future__ import annotations

import argparse
import json
import re
from difflib import SequenceMatcher
from html import unescape
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


BASE_URL = "https://www.kino-teatr.ru"
SEARCH_URL = f"{BASE_URL}/search/"
ENCODING = "cp1251"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


def make_response(ok: bool, data=None, error: str = None, details: str = None) -> dict:
    return {
        "ok": ok,
        "data": data,
        "error": error,
        "details": details,
    }


def normalize_text(value) -> str:
    text = strip_html(str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def normalize_title(value) -> str:
    value = normalize_text(value).casefold().replace("ё", "е")
    return re.sub(r"[^0-9a-zа-я]+", "", value)


def strip_html(value: str) -> str:
    value = re.sub(r"<!--.*?-->", " ", str(value or ""), flags=re.DOTALL)
    value = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"<style[\s\S]*?</style>", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    return unescape(value)


def parse_float(value):
    text = normalize_text(value).replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if match is None:
        return None
    return float(match.group(0))


def parse_int(value):
    match = re.search(r"-?\d+", str(value or ""))
    if match is None:
        return None
    return int(match.group(0))


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


def fetch_html(url: str, data: bytes = None, opener=urlopen, timeout: int = 20) -> str:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = Request(url, data=data, headers=headers)
    with opener(request, timeout=timeout) as response:
        raw = response.read()
    return raw.decode(ENCODING, errors="replace")


def build_search_payload(title: str) -> bytes:
    params = {
        "text": title,
        "movie": "1",
        "content": "1",
    }
    return urlencode(params, encoding=ENCODING).encode("ascii")


def first_match(pattern: str, text: str, flags: int = 0) -> str | None:
    match = re.search(pattern, text, flags)
    if match is None:
        return None
    return unescape(match.group(1)).strip()


def find_blocks(html: str, class_name: str) -> list:
    pattern = rf'<div[^>]+class=["\'][^"\']*{re.escape(class_name)}[^"\']*["\'][^>]*>(.*?)</div>\s*</div>'
    return re.findall(pattern, html, flags=re.IGNORECASE | re.DOTALL)


def split_people(value: str) -> list:
    text = normalize_text(value)
    text = re.sub(r"\s*полный список.*$", "", text, flags=re.IGNORECASE)
    if text == "":
        return []
    return [item.strip() for item in text.split(",") if item.strip() != ""]


def extract_search_field(block: str, label: str) -> str | None:
    value = first_match(
        rf'<div class="list_item_content">\s*<span class="text_blue">{re.escape(label)}:</span>\s*(.*?)</div>',
        block,
        re.IGNORECASE | re.DOTALL,
    )
    return normalize_text(value) or None


def extract_meta_content(html: str, attr_name: str, attr_value: str) -> str | None:
    pattern = (
        rf'<meta[^>]+{attr_name}=["\']{re.escape(attr_value)}["\'][^>]+content=["\']([^"\']*)["\']'
        rf'|<meta[^>]+content=["\']([^"\']*)["\'][^>]+{attr_name}=["\']{re.escape(attr_value)}["\']'
    )
    match = re.search(pattern, html, flags=re.IGNORECASE)
    if match is None:
        return None
    return unescape(match.group(1) or match.group(2) or "").strip() or None


def extract_search_results(html: str, query: str) -> list:
    blocks = []
    for chunk in html.split('<div class="list_item"')[1:]:
        block = '<div class="list_item"' + chunk
        if "/kino/movie/" in block and "/annot/" in block:
            blocks.append(block)
    results = []
    for block in blocks:
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', block, flags=re.IGNORECASE)
        url = next((href for href in hrefs if "/kino/movie/" in href and "/annot/" in href), None)
        title = (
            first_match(r'<strong[^>]+itemprop=["\']?name["\']?[^>]*>(.*?)</strong>', block, re.IGNORECASE | re.DOTALL)
            or first_match(r'<a[^>]+title=["\']([^"\']+)["\']', block, re.IGNORECASE)
            or first_match(r'<img[^>]+alt=["\']([^"\']+)["\']', block, re.IGNORECASE)
        )
        if url is None or title is None:
            continue

        text = normalize_text(block)
        description = first_match(r'<span[^>]+itemprop=["\']description["\'][^>]*>(.*?)</span>', block, re.IGNORECASE | re.DOTALL)
        if description is None and "Подробнее" in text:
            description = text.rsplit("Актеры:", 1)[-1].split("Подробнее", 1)[0]

        results.append({
            "title": normalize_text(title),
            "year": parse_year(first_match(r'<span class="text_blue">Год:</span>\s*([^<]+)', block, re.IGNORECASE)),
            "url": urljoin(BASE_URL, url),
            "poster": urljoin(BASE_URL, first_match(r'<img[^>]+src=["\']([^"\']+)["\']', block, re.IGNORECASE) or ""),
            "director": extract_search_field(block, "Режиссер"),
            "actors": split_people(extract_search_field(block, "Актеры") or ""),
            "description": normalize_text(description),
            "source": "kino_teatr_html",
            "match_score": round(title_similarity(query, title), 3),
        })
    return results


def extract_info_table(html: str) -> dict:
    fields = {}
    pairs = re.findall(
        r'<div class="info_table_param">(.*?)</div>\s*<div class="info_table_data">(.*?)</div>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for label, value in pairs:
        label = normalize_text(label)
        value = normalize_text(value)
        if label and value:
            fields[label] = value
    return fields


def extract_person_blocks(html: str) -> dict:
    fields = {}
    blocks = re.findall(
        r'<div class="film_persons_block">\s*<div class="film_persons_type">(.*?)</div>\s*<div class="film_persons_names">(.*?)</div>\s*</div>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for label, value in blocks:
        label = normalize_text(label)
        value = normalize_text(value)
        if label and value:
            fields[label] = value
    return fields


def extract_ratings(html: str) -> dict:
    ratings = {}
    for chunk in html.split('<div class="rating_block">')[1:]:
        block = chunk.split('<div class="rating_block">', 1)[0]
        label = normalize_text(first_match(r'<div class="rating_head">(.*?)</div>', block, re.IGNORECASE | re.DOTALL))
        score = parse_float(first_match(r'<span class=["\']nowrap rating_digits["\'][^>]*>\s*<b[^>]*>(.*?)</b>', block, re.IGNORECASE | re.DOTALL))
        votes = parse_int(first_match(r'<span class=["\']nowrap rating_digits["\'][^>]*>[\s\S]*?</b>\s*/\s*<span[^>]*>(.*?)</span>', block, re.IGNORECASE | re.DOTALL))
        if label.startswith("Ожидания"):
            ratings["expectation_score"] = score
            ratings["expectation_votes"] = votes
        elif label.startswith("Рейтинг"):
            ratings["site_rating"] = score
            ratings["site_rating_votes"] = votes
    return ratings


def extract_description(html: str) -> str | None:
    value = first_match(r'<div[^>]+itemprop=["\']description["\'][^>]*>(.*?)</div>', html, re.IGNORECASE | re.DOTALL)
    return normalize_text(value) or None


def extract_last_update(html: str) -> str | None:
    value = first_match(r'<p class=["\']last_update_text["\']>(.*?)</p>', html, re.IGNORECASE | re.DOTALL)
    value = normalize_text(value)
    return value.replace("последнее обновление информации:", "").strip() or None


def parse_detail_page(html: str, url: str) -> dict:
    info = extract_info_table(html)
    persons = extract_person_blocks(html)
    ratings = extract_ratings(html)

    title = normalize_text(first_match(r'<h1[^>]*itemprop=["\']name["\'][^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL))
    clean_title = re.sub(r"\s*\((19|20)\d{2}\)\s*$", "", title).strip()
    country = info.get("Страна")
    genre = persons.get("Жанр")

    data = {
        "title": clean_title or title or extract_meta_content(html, "property", "og:title"),
        "year": parse_year(title) or parse_year(info.get("Год")),
        "country": country,
        "countries": [country] if country else [],
        "poster": extract_meta_content(html, "property", "og:image"),
        "url": url,
        "page_title": normalize_text(first_match(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)),
        "description": extract_description(html),
        "director": persons.get("Режиссер"),
        "screenwriters": split_people(persons.get("Сценаристы")),
        "operator": persons.get("Оператор"),
        "artist": persons.get("Художник"),
        "producers": split_people(persons.get("Продюсеры")),
        "casting_directors": split_people(persons.get("Кастинг-директора")),
        "actors": split_people(persons.get("Актеры")),
        "production": persons.get("Производство"),
        "premiere": persons.get("Премьера"),
        "episodes": parse_int(persons.get("Cерий") or persons.get("Серий")),
        "genres": [genre] if genre else [],
        "ratings": ratings,
        "available_metrics": [key for key, value in ratings.items() if value is not None],
        "last_update": extract_last_update(html),
        "detail_fields": {**info, **persons},
        "source": "kino_teatr_html",
    }
    return {key: value for key, value in data.items() if value not in (None, "", [], {})}


def choose_best_result(results: list, query: str) -> dict | None:
    if len(results) == 0:
        return None
    exact = [item for item in results if normalize_title(item.get("title")) == normalize_title(query)]
    if len(exact) > 0:
        return exact[0]
    return max(results, key=lambda item: item.get("match_score") or 0)


def find_title(title: str, limit: int = 5, opener=urlopen) -> dict:
    title = normalize_text(title)
    if title == "":
        return make_response(False, error="empty_title", details="Название не задано.")

    try:
        search_html = fetch_html(SEARCH_URL, data=build_search_payload(title), opener=opener)
    except Exception as error:
        return make_response(False, error="network_error", details=str(error))

    results = extract_search_results(search_html, title)[:limit]
    if len(results) == 0:
        return make_response(False, error="not_found", details="Kino-Teatr.ru не вернул результатов по фильмам/сериалам.")

    best = choose_best_result(results, title)
    if best and best.get("url"):
        try:
            detail_html = fetch_html(best["url"], opener=opener)
            detail = parse_detail_page(detail_html, best["url"])
            detail["match_score"] = best.get("match_score")
            best = {**best, **detail}
        except Exception as error:
            best["detail_error"] = str(error)

    return make_response(True, data={
        "query": title,
        "best": best,
        "results": results,
        "source_url": SEARCH_URL,
    })


def print_search_result(result: dict) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Search Kino-Teatr.ru by title.")
    parser.add_argument("title", help="Movie or series title.")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    print_search_result(find_title(args.title, limit=args.limit))


if __name__ == "__main__":
    main()
