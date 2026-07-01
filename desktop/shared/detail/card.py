"""Shared detail card widgets for watched, candidate and add-title flows."""

from __future__ import annotations

from dataclasses import dataclass, replace

from desktop.theme import (
    COLOR_ACCENT,
    COLOR_BORDER,
    COLOR_CARD,
    COLOR_CARD_ALT,
    COLOR_SURFACE,
    COLOR_TEXT,
    COLOR_TEXT_SECONDARY,
    FONT_FAMILY,
    FONT_RATING_LABEL_POINT,
    FONT_RATING_VALUE_POINT,
    TRANSPARENT_STYLE,
    OVERVIEW_DIVIDER_TEXT_SPACING,
    OVERVIEW_SECTION_TOP_SPACING,
    OVERVIEW_TITLE_DIVIDER_SPACING,
    build_detail_card_style,
    build_poster_image_style,
    build_poster_placeholder_style,
)
from desktop.watched.model import (
    WatchedEntry,
    build_detail_info_pill_labels,
    build_meta_pill_items,
    format_user_score_display,
    get_overview_display,
    get_poster_cache_directory,
    has_overview_text,
    open_path_in_shell,
    resolve_local_poster_path,
)

POSTER_BASE_WIDTH = 220
POSTER_BASE_HEIGHT = 330
POSTER_DISPLAY_SCALE = 1.25
POSTER_WIDTH = int(POSTER_BASE_WIDTH * POSTER_DISPLAY_SCALE)
POSTER_HEIGHT = int(POSTER_BASE_HEIGHT * POSTER_DISPLAY_SCALE)
POSTER_TOP_ROW_SPACING = int(22 * POSTER_DISPLAY_SCALE)
LIST_ITEM_HEIGHT = 72
LIST_THUMB_WIDTH = 40
LIST_THUMB_HEIGHT = 60
LIST_ITEM_H_PADDING = 10
LIST_ITEM_V_PADDING = 6
LIST_TEXT_GAP = 10
GENRES_PER_ROW = 4
CARD_PADDING = 22
RATING_CIRCLE_WIDGET_SIZE = 88
RATING_CIRCLE_DIAMETER = 78

POSTER_PLACEHOLDER_STYLE = build_poster_placeholder_style()
POSTER_IMAGE_STYLE = build_poster_image_style()
DETAIL_CARD_STYLE = build_detail_card_style()


@dataclass(frozen=True)
class DetailCardLayoutProfile:
    """Layout sizing for WatchedDetailCard (full watched view vs compact add-preview)."""

    poster_width: int
    poster_height: int
    poster_row_spacing: int
    card_padding: int
    rating_widget_size: int
    rating_circle_diameter: int
    rating_value_font_point: int
    rating_label_font_point: int
    show_user_score: bool = True
    show_mark_watched_button: bool = False
    include_bottom_stretch: bool = True


DETAIL_CARD_LAYOUT_PROFILE = DetailCardLayoutProfile(
    poster_width=POSTER_WIDTH,
    poster_height=POSTER_HEIGHT,
    poster_row_spacing=POSTER_TOP_ROW_SPACING,
    card_padding=CARD_PADDING,
    rating_widget_size=RATING_CIRCLE_WIDGET_SIZE,
    rating_circle_diameter=RATING_CIRCLE_DIAMETER,
    rating_value_font_point=FONT_RATING_VALUE_POINT,
    rating_label_font_point=FONT_RATING_LABEL_POINT,
    show_user_score=True,
)

ADD_TITLE_PREVIEW_CARD_PROFILE = DetailCardLayoutProfile(
    poster_width=POSTER_WIDTH // 2,
    poster_height=POSTER_HEIGHT // 2,
    poster_row_spacing=max(10, POSTER_TOP_ROW_SPACING // 2),
    card_padding=14,
    rating_widget_size=50,
    rating_circle_diameter=44,
    rating_value_font_point=11,
    rating_label_font_point=7,
    show_user_score=False,
    include_bottom_stretch=False,
)

CANDIDATE_DETAIL_CARD_PROFILE = replace(
    DETAIL_CARD_LAYOUT_PROFILE,
    show_user_score=False,
    show_mark_watched_button=True,
)

_thumb_pixmap_cache: dict[str, object] = {}
_detail_poster_source_cache: dict[str, object] = {}


def fit_poster_pixmap_for_display(pixmap, max_width: int, max_height: int):
    """Fit a poster into the display box without unnecessary upscale blur."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QPixmap

    if pixmap.isNull():
        return pixmap
    source_size = pixmap.size()
    if source_size.isEmpty():
        return pixmap

    target_size = source_size.scaled(max_width, max_height, Qt.AspectRatioMode.KeepAspectRatio)
    if target_size.isEmpty():
        return pixmap

    needs_downscale = target_size.width() < source_size.width() or target_size.height() < source_size.height()
    if not needs_downscale:
        return pixmap

    return pixmap.scaled(
        target_size.width(),
        target_size.height(),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def _load_list_thumb_pixmap(poster_path: str | None):
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QPixmap

    if poster_path is None:
        return None
    cached = _thumb_pixmap_cache.get(poster_path)
    if cached is not None:
        return cached if cached is not False else None
    pixmap = QPixmap(poster_path)
    if pixmap.isNull():
        _thumb_pixmap_cache[poster_path] = False
        return None
    scaled = pixmap.scaled(
        LIST_THUMB_WIDTH,
        LIST_THUMB_HEIGHT,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    _thumb_pixmap_cache[poster_path] = scaled
    return scaled


def _load_detail_poster_source_pixmap(poster_path: str):
    from PyQt6.QtGui import QPixmap

    cached = _detail_poster_source_cache.get(poster_path)
    if cached is not None:
        return cached if cached is not False else None
    pixmap = QPixmap(poster_path)
    if pixmap.isNull():
        _detail_poster_source_cache[poster_path] = False
        return None
    _detail_poster_source_cache[poster_path] = pixmap
    return pixmap


class WatchedListItemDelegate:
    """Rich list row: thumbnail, title, year and user score."""

    def __new__(cls, parent=None):
        from PyQt6.QtCore import QRect, QSize, Qt
        from PyQt6.QtGui import QColor, QFont, QPainter, QPen
        from PyQt6.QtWidgets import QStyledItemDelegate, QStyle

        class _WatchedListItemDelegate(QStyledItemDelegate):
            def sizeHint(self, option, index):
                width = option.rect.width() if option.rect.width() > 0 else 280
                return QSize(width, LIST_ITEM_HEIGHT)

            def paint(self, painter, option, index) -> None:
                entry = index.data(Qt.ItemDataRole.UserRole)
                if not isinstance(entry, tuple) or len(entry) != 3:
                    super().paint(painter, option, index)
                    return

                _key, movie, card = entry
                rect = option.rect.adjusted(2, 1, -2, -1)
                is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
                is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)

                painter.save()
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

                if is_selected:
                    painter.setPen(QPen(QColor(COLOR_ACCENT), 2))
                    painter.setBrush(QColor(COLOR_ACCENT_SOFT))
                elif is_hovered:
                    painter.setPen(QPen(QColor(COLOR_BORDER), 1))
                    painter.setBrush(QColor(COLOR_CARD_ALT))
                else:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)

                if is_selected or is_hovered:
                    painter.drawRoundedRect(rect, 10, 10)

                thumb_left = rect.left() + LIST_ITEM_H_PADDING
                thumb_top = rect.top() + (rect.height() - LIST_THUMB_HEIGHT) // 2
                thumb_rect = QRect(thumb_left, thumb_top, LIST_THUMB_WIDTH, LIST_THUMB_HEIGHT)

                poster_path = resolve_local_poster_path(movie, card)
                thumb = _load_list_thumb_pixmap(poster_path)
                if thumb is not None:
                    clip = thumb_rect.adjusted(1, 1, -1, -1)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(COLOR_CARD))
                    painter.drawRoundedRect(clip, 6, 6)
                    painter.drawPixmap(clip, thumb)
                else:
                    painter.setPen(QPen(QColor(COLOR_BORDER), 1))
                    painter.setBrush(QColor(COLOR_CARD))
                    painter.drawRoundedRect(thumb_rect, 6, 6)
                    placeholder_font = QFont(FONT_FAMILY, 8)
                    painter.setFont(placeholder_font)
                    painter.setPen(QColor(COLOR_TEXT_SECONDARY))
                    painter.drawText(thumb_rect, Qt.AlignmentFlag.AlignCenter, "—")

                text_left = thumb_rect.right() + LIST_TEXT_GAP
                text_right = rect.right() - LIST_ITEM_H_PADDING
                text_width = max(40, text_right - text_left)

                title = str(card.get("title") or _key or "Без названия")
                year = card.get("year")
                year_text = str(year) if year not in (None, "") else ""
                score_text = format_user_score_display(card.get("user_score"))
                meta_parts = [part for part in (year_text, score_text if score_text != "—" else "") if part]
                meta_text = " · ".join(meta_parts)

                title_font = QFont(FONT_FAMILY)
                title_font.setPointSize(10)
                title_font.setBold(True)
                meta_font = QFont(FONT_FAMILY)
                meta_font.setPointSize(9)

                title_rect = QRect(text_left, rect.top() + LIST_ITEM_V_PADDING, text_width, 28)
                meta_rect = QRect(text_left, title_rect.bottom(), text_width, 20)

                painter.setFont(title_font)
                painter.setPen(QColor(COLOR_TEXT if is_selected else COLOR_TEXT))
                painter.drawText(
                    title_rect,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    _elide_text(painter, title, title_rect.width()),
                )

                if meta_text:
                    painter.setFont(meta_font)
                    painter.setPen(QColor(COLOR_ACCENT if is_selected else COLOR_TEXT_SECONDARY))
                    painter.drawText(
                        meta_rect,
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                        meta_text,
                    )

                painter.restore()

        return _WatchedListItemDelegate(parent)


def _elide_text(painter, text: str, max_width: int) -> str:
    from PyQt6.QtCore import Qt

    metrics = painter.fontMetrics()
    return metrics.elidedText(text, Qt.TextElideMode.ElideRight, max(20, max_width))


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


class RatingCircleIndicator:
    """Small circular score indicator with a radial progress ring."""

    def __new__(
        cls,
        label: str,
        score=None,
        accent: str = COLOR_ACCENT,
        *,
        widget_size: int = RATING_CIRCLE_WIDGET_SIZE,
        circle_diameter: int = RATING_CIRCLE_DIAMETER,
        value_font_point: int = FONT_RATING_VALUE_POINT,
        label_font_point: int = FONT_RATING_LABEL_POINT,
    ):
        from PyQt6.QtWidgets import QWidget

        class _RatingCircleWidget(QWidget):
            def __init__(self, label_text: str, score_value, accent_color: str) -> None:
                super().__init__()
                self._label = label_text
                self._score = score_value
                self._accent = accent_color
                self._widget_size = widget_size
                self._circle_diameter = circle_diameter
                self._value_font_point = value_font_point
                self._label_font_point = label_font_point
                self.setFixedSize(self._widget_size, self._widget_size)
                self.setStyleSheet(TRANSPARENT_STYLE)

            def set_score(self, score_value) -> None:
                self._score = score_value
                self.update()

            def paintEvent(self, _event) -> None:
                from PyQt6.QtCore import QRectF, Qt
                from PyQt6.QtGui import QColor, QFont, QPainter, QPen

                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

                left = (self.width() - self._circle_diameter) / 2
                top = (self.height() - self._circle_diameter) / 2
                rect = QRectF(left, top, self._circle_diameter, self._circle_diameter)
                inner_pad = max(4, int(self._circle_diameter * 0.08))
                inner_rect = rect.adjusted(inner_pad, inner_pad, -inner_pad, -inner_pad)
                ring_pen_width = max(3, int(self._circle_diameter * 0.06))

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(COLOR_SURFACE))
                painter.drawEllipse(rect)

                ring_rect = rect.adjusted(ring_pen_width, ring_pen_width, -ring_pen_width, -ring_pen_width)
                track_pen = QPen(QColor(COLOR_BORDER), ring_pen_width)
                track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(track_pen)
                painter.drawArc(ring_rect, 90 * 16, -360 * 16)

                progress = _score_progress(self._score)
                if progress > 0:
                    accent_pen = QPen(QColor(self._accent), ring_pen_width)
                    accent_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                    painter.setPen(accent_pen)
                    painter.drawArc(ring_rect, 90 * 16, -int(360 * 16 * progress))

                painter.setPen(QColor(COLOR_TEXT))
                value_font = QFont(FONT_FAMILY)
                value_font.setPointSize(self._value_font_point)
                value_font.setBold(True)
                painter.setFont(value_font)
                value_offset = max(4, int(self._circle_diameter * 0.1))
                painter.drawText(
                    inner_rect.adjusted(0, -value_offset, 0, 0),
                    Qt.AlignmentFlag.AlignCenter,
                    _score_text(self._score),
                )

                painter.setPen(QColor(COLOR_TEXT_SECONDARY))
                label_font = QFont(FONT_FAMILY)
                label_font.setPointSize(self._label_font_point)
                label_font.setBold(True)
                painter.setFont(label_font)
                label_offset = max(18, int(self._circle_diameter * 0.48))
                painter.drawText(
                    inner_rect.adjusted(0, label_offset, 0, -4),
                    Qt.AlignmentFlag.AlignCenter,
                    self._label,
                )

        return _RatingCircleWidget(label, score, accent)


def _score_progress(score) -> float:
    try:
        value = float(score)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, value / 10.0))


def _score_text(score) -> str:
    return format_user_score_display(score)


def _make_meta_pill(item: dict, profile: DetailCardLayoutProfile = DETAIL_CARD_LAYOUT_PROFILE):
    return RatingCircleIndicator(
        item.get("label", ""),
        item.get("score"),
        item.get("accent", COLOR_ACCENT),
        widget_size=profile.rating_widget_size,
        circle_diameter=profile.rating_circle_diameter,
        value_font_point=profile.rating_value_font_point,
        label_font_point=profile.rating_label_font_point,
    )


def _fill_meta_pill_row(
    layout,
    items: list[dict],
    profile: DetailCardLayoutProfile = DETAIL_CARD_LAYOUT_PROFILE,
) -> None:
    _clear_layout(layout)
    layout.setSpacing(8)
    for item in items:
        layout.addWidget(_make_meta_pill(item, profile))
    layout.addStretch()


def _fill_pill_rows(container_layout, labels: list[str], object_name: str) -> None:
    _clear_layout(container_layout)
    container_layout.setSpacing(8)
    if len(labels) == 0:
        return
    from PyQt6.QtWidgets import QHBoxLayout

    for index in range(0, len(labels), GENRES_PER_ROW):
        row = QHBoxLayout()
        row.setSpacing(8)
        for text in labels[index : index + GENRES_PER_ROW]:
            row.addWidget(_make_pill_label(text, object_name))
        row.addStretch()
        container_layout.addLayout(row)


class WatchedDetailCard:
    """Detail card widget for the selected watched title."""

    def __init__(self, parent=None, profile: DetailCardLayoutProfile | None = None) -> None:
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import (
            QFrame,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QSizePolicy,
            QVBoxLayout,
            QWidget,
        )

        self._profile = profile or DETAIL_CARD_LAYOUT_PROFILE
        self._poster_source_pixmap = None
        self._local_poster_path: str | None = None
        self._mark_watched_handler = None
        self._mark_watched_button = None
        card = self

        class DetailCardFrame(QFrame):
            def resizeEvent(self, event) -> None:
                super().resizeEvent(event)
                card._schedule_poster_height_sync()

        self._frame = DetailCardFrame(parent)
        self._frame.setObjectName("detailCard")
        self._frame.setStyleSheet(DETAIL_CARD_STYLE)
        self._frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        root = QVBoxLayout(self._frame)
        root.setContentsMargins(
            self._profile.card_padding,
            self._profile.card_padding,
            self._profile.card_padding,
            self._profile.card_padding,
        )
        root.setSpacing(OVERVIEW_SECTION_TOP_SPACING)

        top_row = QHBoxLayout()
        top_row.setSpacing(self._profile.poster_row_spacing)

        self._poster_label = QLabel("Нет постера")
        self._poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._poster_label.setFixedSize(self._profile.poster_width, self._profile.poster_height)
        self._poster_label.setScaledContents(False)
        self._poster_label.setStyleSheet(POSTER_PLACEHOLDER_STYLE)
        self._poster_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._poster_label.customContextMenuRequested.connect(self._show_poster_context_menu)

        self._info_column_widget = QWidget()
        self._info_column_widget.setStyleSheet(TRANSPARENT_STYLE)
        self._info_column_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        info_column = QVBoxLayout(self._info_column_widget)
        info_column.setContentsMargins(0, 0, 0, 0)
        info_column.setSpacing(12)

        self._title_label = QLabel("Выберите тайтл слева")
        self._title_label.setObjectName("detailTitle")
        self._title_label.setWordWrap(True)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._title_label.setMinimumHeight(36)
        self._title_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        metrics_row_widget = QWidget()
        metrics_row_widget.setStyleSheet(TRANSPARENT_STYLE)
        self._metrics_row_widget = metrics_row_widget
        self._metrics_row = QHBoxLayout(metrics_row_widget)
        self._metrics_row.setContentsMargins(0, 0, 0, 0)
        self._metrics_row.setSpacing(10)

        self._score_indicator = None
        if self._profile.show_user_score:
            self._score_indicator = RatingCircleIndicator(
                "моя",
                None,
                COLOR_ACCENT,
                widget_size=self._profile.rating_widget_size,
                circle_diameter=self._profile.rating_circle_diameter,
                value_font_point=self._profile.rating_value_font_point,
                label_font_point=self._profile.rating_label_font_point,
            )

        self._meta_pills_widget = QWidget()
        self._meta_pills_widget.setStyleSheet(TRANSPARENT_STYLE)
        self._meta_pills_layout = QHBoxLayout(self._meta_pills_widget)
        self._meta_pills_layout.setContentsMargins(0, 0, 0, 0)
        self._meta_pills_layout.setSpacing(10)

        if self._score_indicator is not None:
            self._metrics_row.addWidget(self._score_indicator, alignment=Qt.AlignmentFlag.AlignLeft)
        self._metrics_row.addWidget(self._meta_pills_widget, alignment=Qt.AlignmentFlag.AlignVCenter)
        if self._profile.show_mark_watched_button:
            self._mark_watched_button = QPushButton("👁")
            self._mark_watched_button.setObjectName("candidateMarkWatchedButton")
            self._mark_watched_button.setToolTip("Перенести в просмотренные")
            self._mark_watched_button.setFixedSize(36, 36)
            self._mark_watched_button.setEnabled(False)
            self._mark_watched_button.clicked.connect(self._on_mark_watched_clicked)
            self._metrics_row.addWidget(self._mark_watched_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        self._metrics_row.addStretch()

        self._genre_section = QWidget()
        self._genre_section.setStyleSheet(TRANSPARENT_STYLE)
        self._genre_pills_layout = QVBoxLayout(self._genre_section)
        self._genre_pills_layout.setContentsMargins(0, 0, 0, 0)
        self._genre_pills_layout.setSpacing(8)

        self._overview_frame = QFrame()
        self._overview_frame.setObjectName("overviewBlock")
        self._overview_frame.setFrameShape(QFrame.Shape.NoFrame)
        self._overview_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        overview_layout = QVBoxLayout(self._overview_frame)
        overview_layout.setContentsMargins(0, 0, 0, 0)
        overview_layout.setSpacing(0)

        self._overview_title_label = QLabel("Описание")
        self._overview_title_label.setObjectName("overviewTitle")
        self._overview_title_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self._overview_divider = QFrame()
        self._overview_divider.setObjectName("overviewDivider")
        self._overview_divider.setFrameShape(QFrame.Shape.HLine)
        self._overview_divider.setFixedHeight(1)

        self._overview_label = QLabel("")
        self._overview_label.setObjectName("overviewText")
        self._overview_label.setWordWrap(True)
        self._overview_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._overview_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        overview_layout.addWidget(self._overview_title_label)
        overview_layout.addSpacing(OVERVIEW_TITLE_DIVIDER_SPACING)
        overview_layout.addWidget(self._overview_divider)
        overview_layout.addSpacing(OVERVIEW_DIVIDER_TEXT_SPACING)
        overview_layout.addWidget(self._overview_label)

        info_column.addWidget(self._title_label)
        info_column.addSpacing(2)
        info_column.addWidget(self._genre_section)
        info_column.addSpacing(2)
        info_column.addWidget(metrics_row_widget)

        top_row.addWidget(self._poster_label, alignment=Qt.AlignmentFlag.AlignTop)
        top_row.addWidget(self._info_column_widget, stretch=1, alignment=Qt.AlignmentFlag.AlignTop)
        root.addLayout(top_row)
        root.addWidget(self._overview_frame)
        if self._profile.include_bottom_stretch:
            root.addStretch(1)

    @property
    def widget(self):
        return self._frame

    def set_mark_watched_handler(self, handler) -> None:
        """Optional callback for candidate transfer to watched dataset."""
        self._mark_watched_handler = handler
        if self._mark_watched_button is not None:
            self._mark_watched_button.setEnabled(handler is not None)

    def _on_mark_watched_clicked(self) -> None:
        if self._mark_watched_handler is not None:
            self._mark_watched_handler()

    def _metrics_row_should_show(self, meta_pill_count: int) -> bool:
        if self._profile.show_user_score:
            return True
        if meta_pill_count > 0:
            return True
        return self._profile.show_mark_watched_button

    def _info_column_content_width(self) -> int:
        width = self._info_column_widget.width()
        if width > 0:
            return width
        frame_width = self._frame.width()
        if frame_width <= 0:
            return 0
        return max(
            120,
            frame_width
            - self._profile.poster_width
            - self._profile.poster_row_spacing
            - (2 * self._profile.card_padding),
        )

    def _sync_poster_display(self) -> None:
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QPixmap

        poster_width = self._profile.poster_width
        poster_height = self._profile.poster_height
        if self._poster_source_pixmap is not None and not self._poster_source_pixmap.isNull():
            display_pixmap = fit_poster_pixmap_for_display(
                self._poster_source_pixmap,
                poster_width,
                poster_height,
            )
            width = max(display_pixmap.width(), 1)
            height = max(display_pixmap.height(), 1)
            self._poster_label.setFixedSize(width, height)
            self._poster_label.setStyleSheet(POSTER_IMAGE_STYLE)
            self._poster_label.setText("")
            self._poster_label.setPixmap(display_pixmap)
            return

        self._poster_label.setFixedSize(poster_width, poster_height)
        if self._poster_label.pixmap() is None or self._poster_label.pixmap().isNull():
            self._poster_label.setPixmap(QPixmap())
            if self._poster_label.text() == "":
                self._poster_label.setText("Нет постера")
            self._poster_label.setStyleSheet(POSTER_PLACEHOLDER_STYLE)

    def _schedule_poster_height_sync(self) -> None:
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(0, self._sync_poster_display)

    def _set_poster_placeholder(self) -> None:
        from PyQt6.QtGui import QPixmap

        self._poster_source_pixmap = None
        self._poster_label.setPixmap(QPixmap())
        self._poster_label.setText("Нет постера")
        self._poster_label.setStyleSheet(POSTER_PLACEHOLDER_STYLE)

    def _set_poster_image(self, poster_path: str) -> bool:
        pixmap = _load_detail_poster_source_pixmap(poster_path)
        if pixmap is None:
            return False

        self._poster_source_pixmap = pixmap
        self._sync_poster_display()
        return True

    def _set_local_poster_path(self, local_path: str | None) -> None:
        self._local_poster_path = local_path
        self._poster_label.setToolTip(local_path or "")

    def _show_poster_context_menu(self, position) -> None:
        from PyQt6.QtWidgets import QMenu

        menu = QMenu(self._poster_label)
        open_action = menu.addAction("Открыть постер")
        open_action.setEnabled(self._local_poster_path is not None)
        cache_action = menu.addAction("Папка poster-cache")
        chosen_action = menu.exec(self._poster_label.mapToGlobal(position))
        if chosen_action is open_action:
            self._open_local_poster()
        elif chosen_action is cache_action:
            self._open_poster_cache_directory()

    def _open_local_poster(self) -> None:
        from PyQt6.QtWidgets import QMessageBox

        if self._local_poster_path is None:
            return
        ok, error = open_path_in_shell(self._local_poster_path)
        if not ok:
            QMessageBox.warning(self._frame, "Постер", error or "Не удалось открыть файл постера.")

    def _open_poster_cache_directory(self) -> None:
        from PyQt6.QtWidgets import QMessageBox

        cache_dir = get_poster_cache_directory()
        ok, error = open_path_in_shell(cache_dir)
        if not ok:
            QMessageBox.warning(
                self._frame,
                "Poster-cache",
                error or "Не удалось открыть папку poster-cache.",
            )

    def show_empty(self, title: str = "Выберите тайтл слева") -> None:
        self._set_poster_placeholder()
        self._set_local_poster_path(None)
        self._title_label.setText(title)
        if self._score_indicator is not None:
            self._score_indicator.set_score(None)
        _fill_meta_pill_row(self._meta_pills_layout, [], self._profile)
        self._meta_pills_widget.setVisible(False)
        _fill_pill_rows(self._genre_pills_layout, [], "genrePill")
        self._genre_section.setVisible(False)
        self._overview_label.setText("")
        self._overview_frame.setVisible(False)
        if self._mark_watched_button is not None:
            self._mark_watched_button.setEnabled(self._mark_watched_handler is not None)
        self._metrics_row_widget.setVisible(self._metrics_row_should_show(0))
        self._schedule_poster_height_sync()

    def show_entry(self, entry: WatchedEntry) -> None:
        _, movie, card = entry
        self._title_label.setText(card.get("title") or entry[0])
        if self._score_indicator is not None:
            self._score_indicator.set_score(card.get("user_score"))

        meta_pills = build_meta_pill_items(card)
        _fill_meta_pill_row(self._meta_pills_layout, meta_pills, self._profile)
        self._meta_pills_widget.setVisible(len(meta_pills) > 0)
        if self._mark_watched_button is not None:
            self._mark_watched_button.setEnabled(self._mark_watched_handler is not None)
        self._metrics_row_widget.setVisible(self._metrics_row_should_show(len(meta_pills)))

        detail_pills = build_detail_info_pill_labels(card)
        _fill_pill_rows(self._genre_pills_layout, detail_pills, "genrePill")
        self._genre_section.setVisible(len(detail_pills) > 0)

        if has_overview_text(card):
            self._overview_label.setText(get_overview_display(card))
            self._overview_frame.setVisible(True)
        else:
            self._overview_label.setText("")
            self._overview_frame.setVisible(False)

        poster_path = resolve_local_poster_path(movie, card)
        if poster_path is None or self._set_poster_image(poster_path) is False:
            self._set_poster_placeholder()
        self._set_local_poster_path(poster_path)
        self._schedule_poster_height_sync()

    def apply_local_poster_path(self, poster_path: str | None) -> None:
        """Update only the poster area after async download."""
        if poster_path not in (None, "") and self._set_poster_image(poster_path):
            self._set_local_poster_path(poster_path)
        else:
            self._set_poster_placeholder()
        self._schedule_poster_height_sync()
