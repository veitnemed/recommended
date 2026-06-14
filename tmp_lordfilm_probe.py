from pathlib import Path
import json

from playwright.sync_api import sync_playwright


def main():
    out = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 1000})
        page.goto("https://vs.lordfilm135.ru/podborki/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        out["forms"] = page.locator("form").evaluate_all(
            """(els) => els.map(f => ({
                action: f.action,
                method: f.method,
                html: f.outerHTML.slice(0, 1200)
            }))"""
        )

        search = page.locator("input[placeholder='Введите название']").first
        out["search_exists"] = search.count() > 0
        if search.count() > 0:
            search.fill("Триггер")
            search.press("Enter")
            page.wait_for_timeout(5000)
            out["after_search_url"] = page.url
            out["after_search_title"] = page.title()
            out["after_search_text"] = page.locator("body").inner_text()[:3000]
            out["first_links"] = page.locator("a").evaluate_all(
                """(els) => els.slice(0, 40).map(a => ({
                    text: (a.innerText || a.textContent || "").trim(),
                    href: a.href
                }))"""
            )
            out["search_result_links"] = page.locator("a[href*='/film/'], a[href*='/serialy/'], a[href*='/mult/'], a[href*='/anime/']").evaluate_all(
                """(els) => els.slice(0, 20).map(a => ({
                    text: (a.innerText || a.textContent || "").trim(),
                    href: a.href
                }))"""
            )

            result_link = page.locator("a[href*='/film/'], a[href*='/serialy/'], a[href*='/mult/'], a[href*='/anime/']").first
            if result_link.count() > 0:
                out["first_result_text"] = result_link.inner_text()
                out["first_result_href"] = result_link.get_attribute("href")
                result_link.click()
                page.wait_for_timeout(5000)
                out["detail_url"] = page.url
                out["detail_title"] = page.title()
                out["detail_text"] = page.locator("body").inner_text()[:4000]
                out["detail_links"] = page.locator("a").evaluate_all(
                    """(els) => els.slice(0, 30).map(a => ({
                        text: (a.innerText || a.textContent || "").trim(),
                        href: a.href
                    }))"""
                )

        Path("tmp_lordfilm_probe.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        browser.close()


if __name__ == "__main__":
    main()
