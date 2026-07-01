"""Watched data loading, filtering, formatting and write helpers (no Qt widgets)."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from desktop.theme import COLOR_IMDB_ACCENT, COLOR_KP_ACCENT
from storage import data as storage_data
from web.export import build_export_lookup_cache, build_watched_movie_card

_poster_cache = None
_lookup_cache = None


def reload_poster_cache() -> dict:
    """Reload poster cache from disk (after add/delete or poster download)."""
    global _poster_cache
    try:
        from posters.cache import load_poster_cache

        _poster_cache = load_poster_cache()
    except Exception:
        _poster_cache = {}
    return _poster_cache


def _get_poster_cache() -> dict:
    global _poster_cache
    if _poster_cache is None:
        return reload_poster_cache()
    return _poster_cache


def _get_lookup_cache() -> dict:
    global _lookup_cache
    if _lookup_cache is None:
        _lookup_cache = build_export_lookup_cache()
    return _lookup_cache

WatchedEntry = tuple[str, dict, dict]

SORT_OPTIONS: tuple[tuple[str, str], ...] = (
    ("user_score", "Моя оценка"),
    ("year", "Год"),
    ("imdb_score", "IMDb"),
    ("kp_score", "КП"),
    ("title", "Название"),
)


def load_watched_entries() -> list[WatchedEntry]:
    """Load dataset and return (dataset_key, movie, card) tuples."""
    data = storage_data.load_dataset()
    poster_cache = reload_poster_cache()
    lookup_cache = _get_lookup_cache()
    return [
        (key, movie, build_watched_movie_card(movie, poster_cache=poster_cache, lookup_cache=lookup_cache))
        for key, movie in data.items()
    ]


def prepare_card_for_display(movie: dict) -> dict:
    """Build a card dict for GUI display without mutating the source movie."""
    original = deepcopy(movie)
    card = build_watched_movie_card(
        movie,
        poster_cache=_get_poster_cache(),
        lookup_cache=_get_lookup_cache(),
    )
    if movie != original:
        raise RuntimeError("build_watched_movie_card mutated the source movie")
    return card


def filter_by_title(entries: list[WatchedEntry], query: str) -> list[WatchedEntry]:
    """Return entries whose title matches the search query (case-insensitive)."""
    from desktop.shared.widgets.list_search import normalize_search_query

    normalized = normalize_search_query(query)
    if normalized == "":
        return list(entries)

    result: list[WatchedEntry] = []
    for key, movie, card in entries:
        title = (card.get("title") or key or "").casefold()
        if normalized in title or normalized in str(key).casefold():
            result.append((key, movie, card))
    return result


def watched_entry_search_haystack(entry: WatchedEntry) -> str:
    """Precomputed haystack for watched title search."""
    key, _movie, card = entry
    title = str(card.get("title") or key or "").strip().casefold()
    return f"{str(key).casefold()} {title}".strip()


def build_watched_search_index(entries: list[WatchedEntry]):
    """Build reusable search index for watched list filtering."""
    from desktop.shared.widgets.list_search import SearchIndex, SearchIndexItem

    items = [
        SearchIndexItem(
            item=entry,
            haystack=watched_entry_search_haystack(entry),
            selection_key=entry[0],
        )
        for entry in entries
    ]
    return SearchIndex(items)


def _coerce_filter_score(value) -> float | None:
    if value is None:
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if score < USER_SCORE_MIN or score > USER_SCORE_MAX:
        return None
    return score


def filter_entries_by_user_score(
    entries: list[WatchedEntry],
    min_score: float | None = None,
    max_score: float | None = None,
) -> list[WatchedEntry]:
    """Return entries whose user_score is inside the inclusive range."""
    lower = USER_SCORE_MIN if min_score is None else float(min_score)
    upper = USER_SCORE_MAX if max_score is None else float(max_score)
    if lower > upper:
        lower, upper = upper, lower
    if lower <= USER_SCORE_MIN and upper >= USER_SCORE_MAX:
        return list(entries)

    result: list[WatchedEntry] = []
    for entry in entries:
        _key, _movie, card = entry
        score = _coerce_filter_score(card.get("user_score"))
        if score is None:
            continue
        if lower <= score <= upper:
            result.append(entry)
    return result


def _coerce_filter_year(value) -> int | None:
    if value is None:
        return None
    try:
        year = int(value)
    except (TypeError, ValueError):
        return None
    return year


def _entry_year(entry: WatchedEntry) -> int | None:
    _key, movie, card = entry
    main_info = movie.get("main_info", {}) if isinstance(movie, dict) else {}
    if isinstance(main_info, dict):
        year = _coerce_filter_year(main_info.get("year"))
        if year is not None:
            return year
    return _coerce_filter_year(card.get("year"))


def filter_entries_by_year(
    entries: list[WatchedEntry],
    year_from: int | None = None,
    year_to: int | None = None,
) -> list[WatchedEntry]:
    """Return entries whose main year is inside the inclusive range."""
    lower = YEAR_FILTER_MIN if year_from is None else int(year_from)
    upper = YEAR_FILTER_MAX if year_to is None else int(year_to)
    if lower > upper:
        lower, upper = upper, lower
    if lower <= YEAR_FILTER_MIN and upper >= YEAR_FILTER_MAX:
        return list(entries)

    result: list[WatchedEntry] = []
    for entry in entries:
        year = _entry_year(entry)
        if year is None:
            continue
        if lower <= year <= upper:
            result.append(entry)
    return result


GENRE_FILTER_ALL = "Все жанры"


def _entry_genres(entry: WatchedEntry) -> list[str]:
    _key, _movie, card = entry
    genres = card.get("genres") or []
    if isinstance(genres, str):
        genres = [genres]
    result: list[str] = []
    for genre in genres:
        text = str(genre).strip()
        if text:
            result.append(text)
    return result


def get_available_genres(entries: list[WatchedEntry]) -> list[str]:
    """Return sorted genre labels present in watched entries."""
    genres: set[str] = set()
    for entry in entries:
        genres.update(_entry_genres(entry))
    return sorted(genres, key=str.casefold)


def filter_entries_by_genre(entries: list[WatchedEntry], genre: str | None = None) -> list[WatchedEntry]:
    """Return entries containing the selected watched-card genre."""
    if genre is None:
        return list(entries)
    selected = str(genre).strip()
    if selected == "" or selected == GENRE_FILTER_ALL:
        return list(entries)

    result: list[WatchedEntry] = []
    for entry in entries:
        if selected in _entry_genres(entry):
            result.append(entry)
    return result


def sort_entries(entries: list[WatchedEntry], sort_key: str) -> list[WatchedEntry]:
    """Return a sorted copy of entries without mutating source data."""
    items = list(entries)

    if sort_key == "title":
        return sorted(
            items,
            key=lambda entry: (entry[2].get("title") or entry[0] or "").lower(),
        )

    def numeric_sort_key(entry: WatchedEntry) -> tuple[int, float | int]:
        value = entry[2].get(sort_key)
        if value is None:
            return (1, 0)
        return (0, value)

    return sorted(items, key=numeric_sort_key, reverse=True)


def apply_view(
    entries: list[WatchedEntry],
    query: str,
    sort_key: str,
    min_score: float | None = None,
    max_score: float | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    genre: str | None = None,
    title_index=None,
) -> list[WatchedEntry]:
    """Filter and sort entries for display."""
    if title_index is not None:
        filtered = title_index.filter_by_query(query)
    else:
        filtered = filter_by_title(entries, query)
    filtered = filter_entries_by_user_score(filtered, min_score, max_score)
    filtered = filter_entries_by_year(filtered, year_from, year_to)
    filtered = filter_entries_by_genre(filtered, genre)
    return sort_entries(filtered, sort_key)


def _round_one_decimal(value) -> str:
    """Round to one decimal place (half up), e.g. 8.25 -> 8.3."""
    rounded = Decimal(str(float(value))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{rounded:.1f}"


def format_user_score_display(user_score) -> str:
    """Format user score for detail card display."""
    if user_score is None:
        return "—"
    try:
        return _round_one_decimal(user_score)
    except (TypeError, ValueError):
        return "—"


USER_SCORE_MIN = 0.0
USER_SCORE_MAX = 10.0
USER_SCORE_STEP = 0.1
YEAR_FILTER_MIN = 1980
YEAR_FILTER_MAX = date.today().year
YEAR_FILTER_DEFAULT_FROM = 2000
YEAR_FILTER_DEFAULT_TO = date.today().year


def normalize_user_score_value(score) -> float:
    """Normalize user score to one decimal place for storage/display."""
    return float(Decimal(str(float(score))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def get_user_score_spin_value(card: dict) -> float:
    """Return user_score formatted for QDoubleSpinBox."""
    score = card.get("user_score")
    if score is None:
        return USER_SCORE_MIN
    return normalize_user_score_value(score)


def build_user_score_update_payload(user_score: float) -> dict:
    """Build update_dataset_record patch for user_score only."""
    return {"main_info": {"user_score": normalize_user_score_value(user_score)}}


def save_watched_user_score(dataset_key: str, user_score: float):
    """Save user_score for a watched record via the dataset update pipeline."""
    from dataset.dataset_records import update_dataset_record

    return update_dataset_record(
        dataset_key,
        build_user_score_update_payload(user_score),
        source_name="desktop_gui",
    )


def format_save_user_score_status(result) -> str:
    """Short GUI status text after save attempt."""
    if result.ok and result.reason == "updated":
        return "Оценка сохранена"
    if result.ok and result.reason == "nothing_changed":
        return "Изменений нет"
    return result.message


def validate_score_edit_entry(entry: WatchedEntry | None) -> tuple[bool, str]:
    """Validate that a watched entry can be used for score edit dialog."""
    if entry is None:
        return False, "Запись не выбрана"

    dataset_key, _movie, _card = entry
    if str(dataset_key).strip() == "":
        return False, "Запись не выбрана"

    return True, ""


def format_rating_score_display(score) -> str | None:
    """Format external rating for pill badges."""
    if score is None:
        return None
    try:
        return _round_one_decimal(score)
    except (TypeError, ValueError):
        return None


def build_meta_pill_items(card: dict) -> list[dict]:
    """Build IMDb/KP pill display items for the detail card."""
    items: list[dict] = []
    imdb = format_rating_score_display(card.get("imdb_score"))
    if imdb is not None:
        items.append(format_imdb_pill(imdb))

    kp = format_rating_score_display(card.get("kp_score"))
    if kp is not None:
        items.append(format_kp_pill(kp))

    return items


def build_meta_pill_labels(card: dict) -> list[str]:
    """Plain-text pill labels (legacy helper for tests)."""
    labels: list[str] = []
    year = card.get("year")
    if year not in (None, ""):
        labels.append(str(year))

    imdb = format_rating_score_display(card.get("imdb_score"))
    if imdb is not None:
        labels.append(f"IMDb {imdb}")

    kp = format_rating_score_display(card.get("kp_score"))
    if kp is not None:
        labels.append(f"КП {kp}")

    return labels


def format_year_pill(year) -> str:
    return str(year)


def _rating_indicator_item(source: str, score: str, label: str) -> dict:
    return {
        "kind": "rating_indicator",
        "source": source,
        "label": label,
        "score": score,
        "accent": COLOR_IMDB_ACCENT if source == "imdb" else COLOR_KP_ACCENT,
    }


def format_imdb_pill(score: str) -> dict:
    return _rating_indicator_item("imdb", score, "IMDb")


def format_kp_pill(score: str) -> dict:
    return _rating_indicator_item("kp", score, "КП")


def format_genre_pill_label(genre: str) -> str:
    return str(genre).strip()


def build_genre_pill_labels(card: dict) -> list[str]:
    """Build genre pill labels for the detail card."""
    genres = card.get("genres") or []
    return [format_genre_pill_label(genre) for genre in genres if str(genre).strip()]


def build_detail_info_pill_labels(card: dict) -> list[str]:
    """Build lower info pills shown near genres."""
    labels: list[str] = []
    year = card.get("year")
    if year not in (None, ""):
        labels.append(format_year_pill(year))
    labels.extend(build_genre_pill_labels(card))
    country = get_country_display(card)
    if country is not None:
        labels.append(country)
    return labels


def get_country_display(card: dict) -> str | None:
    """Return country label for detail card or None when missing."""
    country = card.get("country")
    if country in (None, ""):
        return None
    text = str(country).strip()
    return text if text else None


def has_overview_text(card: dict) -> bool:
    """Return True when the card has non-empty overview text."""
    overview = card.get("overview")
    if overview in (None, ""):
        return False
    return bool(str(overview).strip())


def get_overview_display(card: dict) -> str:
    """Return overview text for detail card."""
    return str(card.get("overview", "")).strip()


def format_list_label(card: dict) -> str:
    """Compact label for the left-hand list."""
    title = card.get("title") or "Без названия"
    year = card.get("year")
    score_label = format_user_score_display(card.get("user_score"))
    parts = [title]
    if year is not None:
        parts.append(f"({year})")
    label = " ".join(parts)
    if score_label != "—":
        label = f"{label}  ·  {score_label}"
    return label


def format_watched_list_status(
    visible_count: int,
    total_count: int,
    query: str = "",
    has_score_filter: bool = False,
    has_year_filter: bool = False,
    has_genre_filter: bool = False,
) -> str:
    """Status bar text for watched list filter results."""
    normalized = query.strip()
    has_filter = bool(normalized) or has_score_filter or has_year_filter or has_genre_filter
    if visible_count == 0:
        return "Ничего не найдено" if has_filter else "Список пуст"
    if has_filter:
        return f"Показано {visible_count} из {total_count}"
    return f"Всего {visible_count}"


def format_watched_list_counter(
    visible_count: int,
    total_count: int,
    query: str = "",
    has_score_filter: bool = False,
    has_year_filter: bool = False,
    has_genre_filter: bool = False,
) -> str:
    """Compact counter shown above the watched list."""
    normalized = query.strip()
    has_filter = bool(normalized) or has_score_filter or has_year_filter or has_genre_filter
    if visible_count == 0:
        return "Ничего не найдено" if has_filter else "Список пуст"
    if has_filter or visible_count != total_count:
        return f"{visible_count} из {total_count}"
    return f"Всего {visible_count}"


def count_active_filters(
    has_score_filter: bool = False,
    has_year_filter: bool = False,
    has_genre_filter: bool = False,
) -> int:
    """Return the number of active score/year/genre filters (search excluded)."""
    return int(has_score_filter) + int(has_year_filter) + int(has_genre_filter)


def score_filter_is_active(min_score: float, max_score: float) -> bool:
    """Return True when user score range differs from the default 0.0–10.0."""
    return float(min_score) > USER_SCORE_MIN or float(max_score) < USER_SCORE_MAX


def year_filter_is_active(year_from: int, year_to: int) -> bool:
    """Return True when year range differs from the default 2000–current year."""
    return int(year_from) != YEAR_FILTER_DEFAULT_FROM or int(year_to) != YEAR_FILTER_DEFAULT_TO


def genre_filter_is_active(genre: str | None) -> bool:
    """Return True when a specific genre is selected instead of all genres."""
    if genre is None:
        return False
    selected = str(genre).strip()
    return selected != "" and selected != GENRE_FILTER_ALL


def watched_filters_are_active(
    has_score_filter: bool = False,
    has_year_filter: bool = False,
    has_genre_filter: bool = False,
) -> bool:
    """Return True when at least one score/year/genre filter is active."""
    return bool(has_score_filter or has_year_filter or has_genre_filter)


def watched_filters_are_active_from_ranges(
    min_score: float = USER_SCORE_MIN,
    max_score: float = USER_SCORE_MAX,
    year_from: int = YEAR_FILTER_DEFAULT_FROM,
    year_to: int = YEAR_FILTER_DEFAULT_TO,
    genre: str | None = None,
) -> bool:
    """Return True when any filter range/genre differs from defaults."""
    return (
        score_filter_is_active(min_score, max_score)
        or year_filter_is_active(year_from, year_to)
        or genre_filter_is_active(genre)
    )


def format_watched_filters_label(
    has_score_filter: bool = False,
    has_year_filter: bool = False,
    has_genre_filter: bool = False,
    is_expanded: bool = False,
) -> str:
    """Build the watched filters toggle label for the sidebar."""
    arrow = "▾" if is_expanded else "▸"
    if watched_filters_are_active(has_score_filter, has_year_filter, has_genre_filter):
        return f"{arrow} Фильтры активны"
    return f"{arrow} Фильтры"


def _local_path(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.startswith(("http://", "https://")):
        return None
    return text


def resolve_local_poster_path(movie: dict, card: dict | None = None) -> str | None:
    """Return a local filesystem poster path when available. Never uses network."""
    display_card = card if card is not None else build_watched_movie_card(movie)
    candidates: list[str | None] = [
        display_card.get("poster_path"),
        _local_path(display_card.get("poster_src")),
        _local_path(movie.get("poster_src")),
        _local_path(movie.get("poster_path")),
        _local_path(_nested_poster_value(movie, "path")),
        _local_path(_nested_poster_value(movie, "poster_path")),
    ]

    for candidate in candidates:
        if candidate is None:
            continue
        path = Path(candidate)
        if path.is_file():
            return str(path)

    poster_url = display_card.get("poster_url") or movie.get("poster_url")
    if poster_url not in (None, ""):
        from posters.download_images import local_preview_poster_path_if_cached

        preview_path = local_preview_poster_path_if_cached(str(poster_url))
        if preview_path not in (None, ""):
            path = Path(preview_path)
            if path.is_file():
                return str(path)

    main_info = movie.get("main_info") if isinstance(movie.get("main_info"), dict) else {}
    title = display_card.get("title") or main_info.get("title") or movie.get("title")
    year = display_card.get("year", main_info.get("year", movie.get("year")))
    if title not in (None, ""):
        from posters.cache import default_local_poster_path

        default_path = default_local_poster_path(str(title), year)
        if default_path not in (None, ""):
            return default_path
    return None


def get_poster_cache_directory() -> str:
    """Return the default poster-cache directory path."""
    from posters.cache import DEFAULT_POSTER_CACHE_DIR

    return str(DEFAULT_POSTER_CACHE_DIR)


def format_poster_path_display(path: str | None, *, max_len: int = 44) -> str:
    """Build a compact read-only poster path line for the detail card."""
    if path is None:
        return "Локальный файл не найден"
    text = str(path)
    if len(text) <= max_len:
        return text
    head = max(8, max_len // 2 - 1)
    tail = max(8, max_len - head - 1)
    return f"{text[:head]}…{text[-tail:]}"


def open_path_in_shell(path: str) -> tuple[bool, str | None]:
    """Open a local file or folder with the OS default handler."""
    target = Path(path)
    if not target.exists():
        return False, f"Путь не найден: {path}"
    try:
        from storage.files import open_file

        open_file(str(target))
        return True, None
    except OSError as error:
        return False, str(error)


def _nested_poster_value(movie: dict, field: str) -> str | None:
    poster = movie.get("poster")
    if isinstance(poster, dict):
        return poster.get(field)
    return None


