"""Экспериментальный парсер страниц Кинопоиска без официального API."""

import json
import re
from html import unescape
from urllib.parse import quote_plus, urljoin
from urllib.request import Request, urlopen


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
BASE_URL = "https://www.kinopoisk.ru"


def make_response(ok: bool, data=None, error: str = None, details: str = None) -> dict:
    """Собирает единый ответ scraper-модуля."""
    return {
        "ok": ok,
        "data": data,
        "error": error,
        "details": details,
    }


def build_search_urls(title: str) -> list:
    """Возвращает несколько вариантов URL поиска по названию."""
    query = quote_plus(str(title or "").strip())
    return [
        f"{BASE_URL}/index.php?kp_query={query}",
        f"{BASE_URL}/s/?query={query}",
    ]


def fetch_html(url: str, opener=urlopen, timeout: int = 20) -> str:
    """Загружает HTML-страницу и возвращает её как UTF-8 строку."""
    request = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    })
    with opener(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_meta_content(html: str, attr_name: str, attr_value: str) -> str | None:
    """Извлекает content у meta-тега по имени атрибута."""
    pattern = (
        rf'<meta[^>]+{attr_name}=["\']{re.escape(attr_value)}["\'][^>]+content=["\']([^"\']+)["\']'
        rf'|<meta[^>]+content=["\']([^"\']+)["\'][^>]+{attr_name}=["\']{re.escape(attr_value)}["\']'
    )
    match = re.search(pattern, html, flags=re.IGNORECASE)
    if match is None:
        return None
    return unescape(match.group(1) or match.group(2) or "").strip() or None


def strip_html(value: str) -> str:
    """Очищает HTML от тегов и лишних пробелов."""
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_json_blocks(html: str) -> list:
    """Достает все JSON-блоки из script type=application/ld+json."""
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return [block.strip() for block in blocks if block.strip() != ""]


def parse_json_block(block: str):
    """Пытается распарсить JSON-блок."""
    try:
        return json.loads(block)
    except json.JSONDecodeError:
        return None


def iter_ld_objects(html: str) -> list:
    """Возвращает плоский список объектов из ld+json блоков."""
    objects = []
    for block in extract_json_blocks(html):
        parsed = parse_json_block(block)
        if isinstance(parsed, list):
            objects.extend(item for item in parsed if isinstance(item, dict))
        elif isinstance(parsed, dict):
            if isinstance(parsed.get("@graph"), list):
                objects.extend(item for item in parsed["@graph"] if isinstance(item, dict))
            else:
                objects.append(parsed)
    return objects


def normalize_genres(value) -> list:
    """Приводит жанры к списку строк."""
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        return []

    genres = []
    for item in items:
        genre = strip_html(item)
        if genre != "" and genre not in genres:
            genres.append(genre)
    return genres


def extract_year_from_text(value: str) -> int | None:
    """Ищет год в строке."""
    match = re.search(r"(19|20)\d{2}", str(value or ""))
    if match is None:
        return None
    return int(match.group(0))


def choose_best_ld_object(objects: list) -> dict | None:
    """Выбирает наиболее полезный ld+json объект страницы."""
    preferred_types = {
        "TVSeries",
        "Movie",
        "CreativeWork",
        "WebPage",
    }
    for obj in objects:
        object_type = obj.get("@type")
        if isinstance(object_type, list):
            object_type = next((item for item in object_type if item in preferred_types), None)
        if object_type in preferred_types and (
            obj.get("name") or obj.get("headline") or obj.get("alternativeHeadline")
        ):
            return obj
    return objects[0] if len(objects) > 0 else None


def extract_title_from_html(html: str, ld_object: dict | None) -> str | None:
    """Ищет название сериала на странице."""
    if isinstance(ld_object, dict):
        for key in ["name", "headline", "alternativeHeadline"]:
            value = strip_html(ld_object.get(key))
            if value != "":
                return value

    for attr_name, attr_value in [
        ("property", "og:title"),
        ("name", "title"),
    ]:
        value = extract_meta_content(html, attr_name, attr_value)
        if value:
            return value

    title_match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if title_match is None:
        return None
    return strip_html(title_match.group(1))


def extract_description_from_html(html: str, ld_object: dict | None) -> str | None:
    """Ищет описание сериала на странице."""
    if isinstance(ld_object, dict):
        value = strip_html(ld_object.get("description"))
        if value != "":
            return value

    for attr_name, attr_value in [
        ("property", "og:description"),
        ("name", "description"),
    ]:
        value = extract_meta_content(html, attr_name, attr_value)
        if value:
            return value
    return None


def extract_year_from_html(html: str, ld_object: dict | None) -> int | None:
    """Ищет год сериала на странице."""
    if isinstance(ld_object, dict):
        year = extract_year_from_text(ld_object.get("datePublished"))
        if year is not None:
            return year

    og_title = extract_meta_content(html, "property", "og:title")
    year = extract_year_from_text(og_title)
    if year is not None:
        return year

    title_text = extract_title_from_html(html, ld_object)
    return extract_year_from_text(title_text)


def extract_genres_from_html(html: str, ld_object: dict | None) -> list:
    """Ищет жанры сериала на странице."""
    if isinstance(ld_object, dict):
        genres = normalize_genres(ld_object.get("genre"))
        if len(genres) > 0:
            return genres

    meta_keywords = extract_meta_content(html, "name", "keywords")
    if meta_keywords:
        return normalize_genres([item.strip() for item in meta_keywords.split(",")])

    return []


def extract_first_content_link(search_html: str) -> str | None:
    """Находит первую ссылку на страницу фильма или сериала в HTML поиска."""
    patterns = [
        r'href=["\'](/series/\d+/[^"\']*)["\']',
        r'href=["\'](/film/\d+/[^"\']*)["\']',
        r'href=["\'](/series/\d+/)["\']',
        r'href=["\'](/film/\d+/)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, search_html, flags=re.IGNORECASE)
        if match is not None:
            return urljoin(BASE_URL, unescape(match.group(1)))
    return None


def is_anti_bot_page(html: str) -> bool:
    """Определяет, что Кинопоиск вернул антибот-страницу вместо контента."""
    lowered = str(html or "").lower()
    normalized = lowered.replace("\\u002f", "/").replace("\\/", "/")
    markers = [
        "sso.kinopoisk.ru/install",
        "form.submit()",
        "retpath",
        "container",
    ]
    return all(marker in normalized for marker in markers)


def parse_series_page(html: str, url: str | None = None) -> dict:
    """Разбирает HTML страницы и собирает краткую структуру сериала."""
    objects = iter_ld_objects(html)
    ld_object = choose_best_ld_object(objects)
    title = extract_title_from_html(html, ld_object)

    if title is None or title == "":
        return make_response(False, error="parse_error", details="Не удалось извлечь название со страницы.")

    return make_response(True, data={
        "url": url,
        "title": title,
        "year": extract_year_from_html(html, ld_object),
        "description": extract_description_from_html(html, ld_object),
        "genres": extract_genres_from_html(html, ld_object),
        "source": "kinopoisk_html",
    })


def find_series_page_url(title: str, opener=urlopen) -> dict:
    """Ищет URL страницы сериала через HTML-поиск Кинопоиска."""
    if str(title or "").strip() == "":
        return make_response(False, error="empty_title", details="Название сериала не задано.")

    last_error = None
    for url in build_search_urls(title):
        try:
            html = fetch_html(url, opener=opener)
        except Exception as error:
            last_error = str(error)
            continue

        if is_anti_bot_page(html):
            return make_response(
                False,
                error="anti_bot",
                details="Кинопоиск вернул антибот-страницу вместо HTML поиска.",
            )

        page_url = extract_first_content_link(html)
        if page_url:
            return make_response(True, data=page_url)

    if last_error is not None:
        return make_response(False, error="network_error", details=last_error)
    return make_response(False, error="not_found", details="Не удалось найти ссылку на страницу сериала.")


def find_series(title: str, opener=urlopen) -> dict:
    """Пробует найти и распарсить сериал напрямую со страниц Кинопоиска."""
    page_result = find_series_page_url(title, opener=opener)
    if page_result["ok"] is False:
        return page_result

    page_url = page_result["data"]
    try:
        html = fetch_html(page_url, opener=opener)
    except Exception as error:
        return make_response(False, error="network_error", details=str(error))

    return parse_series_page(html, url=page_url)
