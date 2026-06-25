"""Read-only helpers for the desktop watched-movies view."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from storage import data as storage_data
from web.export import build_export_lookup_cache, build_watched_movie_card

_poster_cache = None
_lookup_cache = None


def _get_poster_cache() -> dict:
    global _poster_cache
    if _poster_cache is None:
        try:
            from posters.cache import load_poster_cache

            _poster_cache = load_poster_cache()
        except Exception:
            _poster_cache = {}
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
    poster_cache = _get_poster_cache()
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
    normalized = query.strip().lower()
    if normalized == "":
        return list(entries)

    result: list[WatchedEntry] = []
    for key, movie, card in entries:
        title = (card.get("title") or key or "").lower()
        if normalized in title or normalized in key.lower():
            result.append((key, movie, card))
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


def apply_view(entries: list[WatchedEntry], query: str, sort_key: str) -> list[WatchedEntry]:
    """Filter and sort entries for display."""
    return sort_entries(filter_by_title(entries, query), sort_key)


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
    """Build year/IMDb/KP pill display items for the detail card."""
    items: list[dict] = []
    year = card.get("year")
    if year not in (None, ""):
        items.append({"text": format_year_pill(year), "rich": False})

    imdb = format_rating_score_display(card.get("imdb_score"))
    if imdb is not None:
        items.append({"text": format_imdb_pill(imdb), "rich": False})

    kp = format_rating_score_display(card.get("kp_score"))
    if kp is not None:
        items.append({"text": format_kp_pill(kp), "rich": True})

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
    return f"📅 {year}"


def format_imdb_pill(score: str) -> str:
    return f"★ IMDb {score}"


def format_kp_pill(score: str) -> str:
    return f'<span style="color:#10a37f;font-weight:600">КП</span> {score}'


GENRE_ICONS: dict[str, str] = {
    "драма": "🎭",
    "триллер": "🎯",
    "боевик": "🛡",
    "криминал": "🔫",
    "комедия": "😄",
    "фантастика": "🚀",
    "фэнтези": "✨",
    "ужасы": "👻",
    "мелодрама": "💕",
    "детектив": "🔍",
    "приключения": "🧭",
    "семейный": "👨‍👩‍👧",
    "история": "📜",
    "военный": "⚔",
    "биография": "📖",
    "музыка": "🎵",
    "спорт": "⚽",
    "вестерн": "🤠",
    "аниме": "🎌",
    "мультфильм": "🎬",
}


def format_genre_pill_label(genre: str) -> str:
    text = str(genre).strip()
    if text == "":
        return text
    icon = GENRE_ICONS.get(text.lower())
    if icon:
        return f"{icon} {text}"
    return text


def build_genre_pill_labels(card: dict) -> list[str]:
    """Build genre pill labels for the detail card."""
    genres = card.get("genres") or []
    return [format_genre_pill_label(genre) for genre in genres if str(genre).strip()]


def get_country_display(card: dict) -> str | None:
    """Return country label for detail card or None when missing."""
    country = card.get("country")
    if country in (None, ""):
        return None
    text = str(country).strip()
    return text if text else None


def get_overview_display(card: dict) -> str:
    """Return overview text for detail card."""
    overview = card.get("overview")
    if overview in (None, ""):
        return "Описание отсутствует."
    return str(overview).strip()


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
    return None


def _local_path(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.startswith(("http://", "https://")):
        return None
    return text


def _nested_poster_value(movie: dict, field: str) -> str | None:
    poster = movie.get("poster")
    if isinstance(poster, dict):
        return poster.get(field)
    return None


POSTER_WIDTH = 220
POSTER_HEIGHT = 330
GENRES_PER_ROW = 4
CARD_PADDING = 18

POSTER_PLACEHOLDER_STYLE = (
    "background-color: #171719; border: 1px solid #2a2a2e; border-radius: 16px; color: #71717a;"
)
POSTER_IMAGE_STYLE = "background: transparent; border-radius: 16px;"

DETAIL_CARD_STYLE = """
QFrame#detailCard {
    background-color: #171719;
    border: 1px solid #2a2a2e;
    border-radius: 18px;
}
QFrame#scoreCard {
    background-color: transparent;
    border: 1px solid #10a37f;
    border-radius: 14px;
}
QLabel#scoreCardCaption {
    color: #10a37f;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.5px;
}
QLabel#scoreCardValue {
    color: #f4f4f5;
    font-size: 24px;
    font-weight: 700;
}
QLabel#detailTitle {
    background: transparent;
    color: #f4f4f5;
}
QLabel#metaPill, QLabel#genrePill {
    background-color: #1c1c1f;
    border: 1px solid #2a2a2e;
    border-radius: 14px;
    padding: 5px 11px;
    color: #d4d4d8;
    font-size: 13px;
}
QFrame#overviewBlock {
    background-color: #1c1c1f;
    border: 1px solid #2a2a2e;
    border-radius: 16px;
}
QLabel#overviewTitle {
    background: transparent;
    color: #f4f4f5;
    font-size: 13px;
    font-weight: 600;
}
QLabel#overviewText {
    background: transparent;
    color: #d4d4d8;
    font-size: 15px;
}
QLabel#countryHeader {
    color: #71717a;
    font-size: 12px;
}
QLabel#countryValue {
    color: #f4f4f5;
    font-size: 14px;
}
"""


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        child_layout = item.layout()
        if child_layout is not None:
            _clear_layout(child_layout)
            continue
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


def _make_pill_label(text: str, object_name: str, rich: bool = False):
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QLabel

    pill = QLabel()
    pill.setObjectName(object_name)
    if rich:
        pill.setTextFormat(Qt.TextFormat.RichText)
    pill.setText(text)
    return pill


def _fill_meta_pill_row(layout, items: list[dict]) -> None:
    _clear_layout(layout)
    layout.setSpacing(8)
    for item in items:
        layout.addWidget(
            _make_pill_label(item["text"], "metaPill", rich=item.get("rich", False))
        )
    layout.addStretch()


def _fill_pill_rows(container_layout, labels: list[str], object_name: str) -> None:
    _clear_layout(container_layout)
    container_layout.setSpacing(6)
    if len(labels) == 0:
        return
    from PyQt6.QtWidgets import QHBoxLayout

    for index in range(0, len(labels), GENRES_PER_ROW):
        row = QHBoxLayout()
        row.setSpacing(6)
        for text in labels[index : index + GENRES_PER_ROW]:
            row.addWidget(_make_pill_label(text, object_name))
        row.addStretch()
        container_layout.addLayout(row)


class WatchedDetailCard:
    """Detail card widget for the selected watched title."""

    def __init__(self, parent=None) -> None:
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont
        from PyQt6.QtWidgets import (
            QFrame,
            QHBoxLayout,
            QLabel,
            QVBoxLayout,
            QWidget,
        )

        self._frame = QFrame(parent)
        self._frame.setObjectName("detailCard")
        self._frame.setStyleSheet(DETAIL_CARD_STYLE)

        root = QHBoxLayout(self._frame)
        root.setContentsMargins(CARD_PADDING, CARD_PADDING, CARD_PADDING, CARD_PADDING)
        root.setSpacing(16)

        self._poster_label = QLabel("Нет постера")
        self._poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._poster_label.setFixedSize(POSTER_WIDTH, POSTER_HEIGHT)
        self._poster_label.setScaledContents(False)
        self._poster_label.setStyleSheet(POSTER_PLACEHOLDER_STYLE)

        info_column = QVBoxLayout()
        info_column.setSpacing(14)

        self._title_label = QLabel("Выберите тайтл слева")
        self._title_label.setObjectName("detailTitle")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        self._title_label.setFont(title_font)
        self._title_label.setWordWrap(True)

        metrics_row_widget = QWidget()
        metrics_row_widget.setStyleSheet("background: transparent;")
        self._metrics_row = QHBoxLayout(metrics_row_widget)
        self._metrics_row.setContentsMargins(0, 0, 0, 0)
        self._metrics_row.setSpacing(10)

        self._score_card = QFrame()
        self._score_card.setObjectName("scoreCard")
        score_layout = QVBoxLayout(self._score_card)
        score_layout.setContentsMargins(10, 8, 14, 8)
        score_layout.setSpacing(2)

        self._score_caption = QLabel("МОЯ ОЦЕНКА")
        self._score_caption.setObjectName("scoreCardCaption")

        self._score_value = QLabel("—")
        self._score_value.setObjectName("scoreCardValue")

        score_layout.addWidget(self._score_caption)
        score_layout.addWidget(self._score_value)

        self._meta_pills_widget = QWidget()
        self._meta_pills_widget.setStyleSheet("background: transparent;")
        self._meta_pills_layout = QHBoxLayout(self._meta_pills_widget)
        self._meta_pills_layout.setContentsMargins(0, 0, 0, 0)
        self._meta_pills_layout.setSpacing(8)

        self._metrics_row.addWidget(self._score_card, alignment=Qt.AlignmentFlag.AlignLeft)
        self._metrics_row.addWidget(self._meta_pills_widget, alignment=Qt.AlignmentFlag.AlignVCenter)
        self._metrics_row.addStretch()

        self._genre_section = QWidget()
        self._genre_section.setStyleSheet("background: transparent;")
        self._genre_pills_layout = QVBoxLayout(self._genre_section)
        self._genre_pills_layout.setContentsMargins(0, 0, 0, 0)
        self._genre_pills_layout.setSpacing(8)

        self._country_section = QWidget()
        self._country_section.setStyleSheet("background: transparent;")
        country_layout = QVBoxLayout(self._country_section)
        country_layout.setContentsMargins(0, 0, 0, 0)
        country_layout.setSpacing(4)

        self._country_header_label = QLabel("🌐 Страна")
        self._country_header_label.setObjectName("countryHeader")
        self._country_value_label = QLabel("")
        self._country_value_label.setObjectName("countryValue")
        country_layout.addWidget(self._country_header_label)
        country_layout.addWidget(self._country_value_label)

        self._overview_frame = QFrame()
        self._overview_frame.setObjectName("overviewBlock")
        self._overview_frame.setFrameShape(QFrame.Shape.NoFrame)
        overview_layout = QVBoxLayout(self._overview_frame)
        overview_layout.setContentsMargins(14, 12, 14, 12)
        overview_layout.setSpacing(8)

        self._overview_title_label = QLabel("📄 Описание")
        self._overview_title_label.setObjectName("overviewTitle")
        self._overview_label = QLabel("")
        self._overview_label.setObjectName("overviewText")
        self._overview_label.setWordWrap(True)
        self._overview_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        overview_layout.addWidget(self._overview_title_label)
        overview_layout.addWidget(self._overview_label)

        info_column.addWidget(self._title_label)
        info_column.addWidget(metrics_row_widget)
        info_column.addWidget(self._genre_section)
        info_column.addWidget(self._country_section)
        info_column.addWidget(self._overview_frame)
        info_column.addStretch()

        root.addWidget(self._poster_label, alignment=Qt.AlignmentFlag.AlignTop)
        root.addLayout(info_column, stretch=1)

    @property
    def widget(self):
        return self._frame

    def _set_poster_placeholder(self) -> None:
        from PyQt6.QtGui import QPixmap

        self._poster_label.setPixmap(QPixmap())
        self._poster_label.setText("Нет постера")
        self._poster_label.setStyleSheet(POSTER_PLACEHOLDER_STYLE)

    def _set_poster_image(self, poster_path: str) -> bool:
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QPixmap

        pixmap = QPixmap(poster_path)
        if pixmap.isNull():
            return False

        scaled = pixmap.scaled(
            POSTER_WIDTH,
            POSTER_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._poster_label.setStyleSheet(POSTER_IMAGE_STYLE)
        self._poster_label.setText("")
        self._poster_label.setPixmap(scaled)
        return True

    def show_empty(self, title: str = "Выберите тайтл слева") -> None:
        self._set_poster_placeholder()
        self._title_label.setText(title)
        self._score_value.setText("—")
        _fill_meta_pill_row(self._meta_pills_layout, [])
        self._meta_pills_widget.setVisible(False)
        _fill_pill_rows(self._genre_pills_layout, [], "genrePill")
        self._genre_section.setVisible(False)
        self._country_value_label.setText("")
        self._country_section.setVisible(False)
        self._overview_label.setText("")
        self._overview_frame.setVisible(False)

    def show_entry(self, entry: WatchedEntry) -> None:
        _, movie, card = entry
        self._title_label.setText(card.get("title") or entry[0])
        self._score_value.setText(format_user_score_display(card.get("user_score")))

        meta_pills = build_meta_pill_items(card)
        _fill_meta_pill_row(self._meta_pills_layout, meta_pills)
        self._meta_pills_widget.setVisible(len(meta_pills) > 0)

        genre_pills = build_genre_pill_labels(card)
        _fill_pill_rows(self._genre_pills_layout, genre_pills, "genrePill")
        self._genre_section.setVisible(len(genre_pills) > 0)

        country = get_country_display(card)
        if country is None:
            self._country_value_label.setText("")
            self._country_section.setVisible(False)
        else:
            self._country_value_label.setText(country)
            self._country_section.setVisible(True)

        self._overview_label.setText(get_overview_display(card))
        self._overview_frame.setVisible(True)

        poster_path = resolve_local_poster_path(movie, card)
        if poster_path is None or self._set_poster_image(poster_path) is False:
            self._set_poster_placeholder()
