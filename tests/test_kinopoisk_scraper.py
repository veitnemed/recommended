"""Тесты экспериментального парсера HTML-страниц Кинопоиска."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from integrations import kinopoisk_scraper


def assert_check(text: str, result: bool) -> None:
    print(f"{text}: {result}")
    assert result, text


class FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self.text.encode("utf-8")


def make_multi_page_opener(mapping: dict):
    def opener(request, timeout=20):
        url = getattr(request, "full_url", str(request))
        return FakeResponse(mapping[url])
    return opener


def test_extract_first_content_link() -> None:
    html = """
    <html><body>
      <a href="/film/404900/">Во все тяжкие</a>
    </body></html>
    """
    result = kinopoisk_scraper.extract_first_content_link(html)
    assert_check("Ссылка на контент извлекается из HTML поиска", result == "https://www.kinopoisk.ru/film/404900/")


def test_parse_series_page_from_ld_json() -> None:
    html = """
    <html>
      <head>
        <meta property="og:title" content="Во все тяжкие (2008)">
        <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "@type": "TVSeries",
            "name": "Во все тяжкие",
            "datePublished": "2008-01-20",
            "description": "Учитель химии начинает опасную двойную жизнь.",
            "genre": ["драма", "криминал", "триллер"]
          }
        </script>
      </head>
    </html>
    """
    result = kinopoisk_scraper.parse_series_page(html, url="https://www.kinopoisk.ru/film/404900/")

    assert_check("Парсинг страницы возвращает ok", result["ok"] is True)
    assert_check("Название извлечено", result["data"]["title"] == "Во все тяжкие")
    assert_check("Год извлечён", result["data"]["year"] == 2008)
    assert_check("Описание извлечено", "Учитель химии" in result["data"]["description"])
    assert_check("Жанры извлечены", result["data"]["genres"] == ["драма", "криминал", "триллер"])


def test_parse_series_page_from_meta_fallback() -> None:
    html = """
    <html>
      <head>
        <title>Тьма (2017) — Кинопоиск</title>
        <meta property="og:title" content="Тьма (2017)">
        <meta property="og:description" content="Немецкий научно-фантастический сериал.">
        <meta name="keywords" content="драма, фантастика, триллер">
      </head>
    </html>
    """
    result = kinopoisk_scraper.parse_series_page(html)

    assert_check("Meta fallback возвращает ok", result["ok"] is True)
    assert_check("Название взято из meta", result["data"]["title"] == "Тьма (2017)")
    assert_check("Год взят из meta", result["data"]["year"] == 2017)
    assert_check("Жанры взяты из keywords", result["data"]["genres"] == ["драма", "фантастика", "триллер"])


def test_find_series_by_search_and_page() -> None:
    search_url = kinopoisk_scraper.build_search_urls("Тестовый сериал")[0]
    page_url = "https://www.kinopoisk.ru/series/123456/"
    opener = make_multi_page_opener({
        search_url: '<a href="/series/123456/">Тестовый сериал</a>',
        page_url: """
            <script type="application/ld+json">
            {
              "@type": "TVSeries",
              "name": "Тестовый сериал",
              "datePublished": "2024-01-01",
              "description": "Описание тестового сериала",
              "genre": ["комедия"]
            }
            </script>
        """,
    })

    result = kinopoisk_scraper.find_series("Тестовый сериал", opener=opener)

    assert_check("Поиск по HTML возвращает ok", result["ok"] is True)
    assert_check("Распарсено название найденного сериала", result["data"]["title"] == "Тестовый сериал")
    assert_check("Сохраняется URL найденной страницы", result["data"]["url"] == page_url)


def test_detect_anti_bot_page() -> None:
    html = """
    <body></body>
    <script>
    var it = {"host":"https://sso.kinopoisk.ru/install","retpath":"https://www.kinopoisk.ru/s/?query=test"};
    form.submit();
    var container = "abc";
    </script>
    """
    result = kinopoisk_scraper.find_series_page_url(
        "Тест",
        opener=make_multi_page_opener({
            kinopoisk_scraper.build_search_urls("Тест")[0]: html,
        }),
    )

    assert_check("Антибот-страница распознана отдельно", result["error"] == "anti_bot")


def run_tests() -> None:
    print("=== Тесты experimental scraper ===")
    test_extract_first_content_link()
    test_parse_series_page_from_ld_json()
    test_parse_series_page_from_meta_fallback()
    test_find_series_by_search_and_page()
    test_detect_anti_bot_page()
    print("\nПроверки experimental scraper пройдены: True")


if __name__ == "__main__":
    run_tests()
