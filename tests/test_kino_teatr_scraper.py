"""Tests for Kino-Teatr scraper parsing helpers."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from integrations import kino_teatr_scraper


def assert_check(text: str, result: bool) -> None:
    print(f"{text}: {result}")
    assert result, text


def test_extract_search_results() -> None:
    html = """
    <div class="list_item" itemscope itemtype="http://schema.org/Movie">
      <a href="/kino/movie/ros/196212/annot/" title="Санкционер">
        <img src="/movie/posters/big/2/1/196212.jpg" alt="Санкционер">
      </a>
      <h4><a href="/kino/movie/ros/196212/annot/" itemprop="url">
        <strong itemprop="name">Санкционер</strong>
      </a></h4>
      <div class="list_item_content"><span class="text_blue">Год:</span> 2025</div>
      <div class="list_item_content"><span class="text_blue">Режиссер:</span> Артём Захарьян</div>
      <div class="list_item_content"><span class="text_blue">Актеры:</span> Дмитрий Нагиев, Любовь Толкалина</div>
      <span itemprop="description">Описание сериала. Подробнее &gt;&gt;</span>
    </div>
    """
    results = kino_teatr_scraper.extract_search_results(html, "Санкционер")

    assert_check("Search result is extracted", len(results) == 1)
    assert_check("Title is parsed", results[0]["title"] == "Санкционер")
    assert_check("Year is parsed", results[0]["year"] == 2025)
    assert_check("Director is parsed", results[0]["director"] == "Артём Захарьян")
    assert_check("Actors are parsed", results[0]["actors"] == ["Дмитрий Нагиев", "Любовь Толкалина"])


def test_parse_detail_page() -> None:
    html = """
    <html><head>
      <title>Санкционер (2025) - сериал</title>
      <meta property="og:image" content="https://www.kino-teatr.ru/poster.jpg">
    </head><body>
      <h1 itemprop="name">Санкционер (2025)</h1>
      <div class="info_table_param">Год</div><div class="info_table_data">2025</div>
      <div class="info_table_param">Страна</div><div class="info_table_data">Россия</div>
      <div class="rating_block">
        <div class="rating_head">Рейтинг:</div>
        <span class='nowrap rating_digits'><b itemprop='ratingValue'>4.595</b> / <span itemprop='reviewCount'>74</span> голоса</span>
      </div>
      <div class="film_persons_block">
        <div class="film_persons_type">Режиссер</div>
        <div class="film_persons_names">Артём Захарьян</div>
      </div>
      <div class="film_persons_block">
        <div class="film_persons_type">Cерий</div>
        <div class="film_persons_names">17</div>
      </div>
      <div class="film_persons_block">
        <div class="film_persons_type">Жанр</div>
        <div class="film_persons_names">комедия</div>
      </div>
      <div itemprop="description">Описание карточки.</div>
      <p class="last_update_text">последнее обновление информации: 03.06.26</p>
    </body></html>
    """
    data = kino_teatr_scraper.parse_detail_page(html, "https://www.kino-teatr.ru/kino/movie/ros/196212/annot/")

    assert_check("Detail title is parsed", data["title"] == "Санкционер")
    assert_check("Country is parsed", data["country"] == "Россия")
    assert_check("Episodes are parsed", data["episodes"] == 17)
    assert_check("Site rating is parsed", data["ratings"]["site_rating"] == 4.595)
    assert_check("Site rating votes are parsed", data["ratings"]["site_rating_votes"] == 74)
    assert_check("Genre is parsed", data["genres"] == ["комедия"])


def run_tests() -> None:
    print("=== Tests: kino-teatr scraper ===")
    test_extract_search_results()
    test_parse_detail_page()
    print("\nKino-Teatr scraper checks passed: True")


if __name__ == "__main__":
    run_tests()
