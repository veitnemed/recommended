"""Tests for the experimental Lordfilm Playwright scraper helpers."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from integrations import lordfilm_scraper


def assert_check(text: str, result: bool) -> None:
    print(f"{text}: {result}")
    assert result, text


def test_normalize_search_card() -> None:
    card = lordfilm_scraper.normalize_search_card(
        {
            "title": "Триггер",
            "year": "2018",
            "kp_score": "",
            "imdb_score": "7.3",
            "url": "https://vs.lordfilm135.ru/serialy/47431-trigger-2018.html",
            "poster": "/uploads/posts/poster.jpg",
        },
        query="Триггер",
    )

    assert_check("Title is extracted", card["title"] == "Триггер")
    assert_check("Year is parsed", card["year"] == 2018)
    assert_check("Unavailable country is explicit", card["country"] is None)
    assert_check("IMDb rating is parsed", card["ratings"]["imdb_score"] == 7.3)
    assert_check("Empty KP rating is None", card["ratings"]["kp_score"] is None)
    assert_check("Available metrics list contains IMDb only", card["available_metrics"] == ["imdb_score"])
    assert_check("Poster URL is absolutized", card["poster"].startswith(lordfilm_scraper.BASE_URL))
    assert_check("Exact title has full match score", card["match_score"] == 1.0)


def test_choose_best_result_prefers_exact_title() -> None:
    results = [
        lordfilm_scraper.normalize_search_card({"title": "Триггер. Фильм", "year": "2023"}, query="Триггер"),
        lordfilm_scraper.normalize_search_card({"title": "Триггер", "year": "2018"}, query="Триггер"),
    ]

    best = lordfilm_scraper.choose_best_result(results, "Триггер")

    assert_check("Exact title is preferred over first result", best["title"] == "Триггер")
    assert_check("Exact result keeps its year", best["year"] == 2018)


def test_parse_float_and_year() -> None:
    assert_check("Comma rating is parsed", lordfilm_scraper.parse_float("6,4") == 6.4)
    assert_check("Missing rating is None", lordfilm_scraper.parse_float("") is None)
    assert_check("Year is parsed from text", lordfilm_scraper.parse_year("сериал 2021") == 2021)


def run_tests() -> None:
    print("=== Tests: lordfilm scraper ===")
    test_normalize_search_card()
    test_choose_best_result_prefers_exact_title()
    test_parse_float_and_year()
    print("\nLordfilm scraper checks passed: True")


if __name__ == "__main__":
    run_tests()
