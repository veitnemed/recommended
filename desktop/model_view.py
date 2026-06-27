"""Read-only desktop Model tab (stage 1: saved metrics summary)."""

from __future__ import annotations

from desktop.analytics_view import (
    ANALYTICS_ROOT_MARGIN,
    ANALYTICS_ROOT_SPACING,
    ANALYTICS_SUMMARY_CARD_PADDING,
    ANALYTICS_SUMMARY_CARD_SPACING,
    ANALYTICS_SUMMARY_SPACING,
    SUMMARY_CARD_HEIGHT,
    SUMMARY_ICON_BADGE_SIZE,
)
from desktop.model_summary import build_model_tab_summary
from desktop.theme import (
    FONT_BASE,
    FONT_KPI_VALUE,
    FONT_SECTION,
    FONT_SMALL,
    FONT_TITLE,
    build_analytics_style,
)


MODEL_FONT_BASE = FONT_BASE
MODEL_FONT_PAGE_TITLE = FONT_TITLE
MODEL_FONT_SUBTITLE = FONT_BASE
MODEL_FONT_SUMMARY_LABEL = FONT_SMALL
MODEL_FONT_SUMMARY_VALUE = FONT_KPI_VALUE

MODEL_STYLE = build_analytics_style(
    font_base=MODEL_FONT_BASE,
    font_page_title=MODEL_FONT_PAGE_TITLE,
    font_subtitle=MODEL_FONT_SUBTITLE,
    font_summary_label=MODEL_FONT_SUMMARY_LABEL,
    font_summary_value=MODEL_FONT_SUMMARY_VALUE,
    font_section_title=FONT_SECTION,
)

SUMMARY_CARD_ICONS = {
    "LOO MAE": "◎",
    "IMDb baseline": "★",
    "КП baseline": "К",
    "Dataset size": "▦",
    "Статус metrics": "●",
}


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


class ModelView:
    """Read-only summary of saved model metrics."""

    def __init__(self) -> None:
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(MODEL_STYLE)

        self._root = QWidget()
        self._root.setObjectName("modelRoot")
        self._root.setStyleSheet(MODEL_STYLE)
        self._scroll.setWidget(self._root)

        root_layout = QVBoxLayout(self._root)
        root_layout.setContentsMargins(
            ANALYTICS_ROOT_MARGIN,
            ANALYTICS_ROOT_MARGIN,
            ANALYTICS_ROOT_MARGIN,
            ANALYTICS_ROOT_MARGIN,
        )
        root_layout.setSpacing(ANALYTICS_ROOT_SPACING)

        title = QLabel("Модель")
        title.setObjectName("modelTitle")
        root_layout.addWidget(title)

        subtitle = QLabel("Сохранённые метрики — read-only, без обучения и сохранения")
        subtitle.setObjectName("modelSubtitle")
        root_layout.addWidget(subtitle)

        self._summary_layout = QHBoxLayout()
        self._summary_layout.setSpacing(ANALYTICS_SUMMARY_SPACING)
        self._summary_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        root_layout.addLayout(self._summary_layout)

        root_layout.addStretch()
        self.refresh()

    @property
    def widget(self):
        return self._scroll

    def refresh(self) -> None:
        summary = build_model_tab_summary()
        self._fill_summary(summary)

    def _fill_summary(self, summary: dict) -> None:
        _clear_layout(self._summary_layout)
        items = (
            ("LOO MAE", summary["loo_mae_display"]),
            ("IMDb baseline", summary["imdb_baseline_display"]),
            ("КП baseline", summary["kp_baseline_display"]),
            ("Dataset size", summary["dataset_size_display"]),
            ("Статус metrics", summary["metrics_status_display"]),
        )
        for label, value in items:
            icon = SUMMARY_CARD_ICONS.get(label, "•")
            self._summary_layout.addWidget(
                self._make_summary_card(label, value, icon),
                stretch=1,
            )

    def _make_summary_card(self, label_text: str, value_text: str, icon_text: str):
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

        frame = QFrame()
        frame.setObjectName("summaryCard")
        frame.setFixedHeight(SUMMARY_CARD_HEIGHT)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(
            ANALYTICS_SUMMARY_CARD_PADDING,
            ANALYTICS_SUMMARY_CARD_PADDING,
            ANALYTICS_SUMMARY_CARD_PADDING,
            ANALYTICS_SUMMARY_CARD_PADDING,
        )
        layout.setSpacing(10)

        icon_badge = QFrame()
        icon_badge.setObjectName("summaryIconBadge")
        icon_badge.setFixedSize(SUMMARY_ICON_BADGE_SIZE, SUMMARY_ICON_BADGE_SIZE)
        badge_layout = QVBoxLayout(icon_badge)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        icon = QLabel(icon_text)
        icon.setObjectName("summaryIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_layout.addWidget(icon)

        text_column = QVBoxLayout()
        text_column.setContentsMargins(0, 0, 0, 0)
        text_column.setSpacing(ANALYTICS_SUMMARY_CARD_SPACING)

        label = QLabel(label_text)
        label.setObjectName("summaryLabel")
        value = QLabel(value_text)
        value.setObjectName("summaryValue")
        value.setWordWrap(True)
        text_column.addWidget(label)
        text_column.addWidget(value)
        text_column.addStretch()

        layout.addWidget(icon_badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(text_column, stretch=1)
        return frame
