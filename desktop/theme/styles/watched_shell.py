"""QSS for the Watched tab sidebar, filters and list."""

from __future__ import annotations

from desktop.theme.tokens import *  # noqa: F403


def build_watched_shell_style() -> str:
    """Return stylesheet for watched sidebar and filter panel."""
    return f"""
QListWidget#watchedList {{
    padding: 8px;
}}
QWidget#watchedSidebar {{
    background: transparent;
}}
QLineEdit#watchedSearch {{
    font-size: {FONT_BASE}px;
}}
QPushButton#watchedAddTitle {{
    background-color: {COLOR_ADD_BUTTON};
    border: 1px solid {COLOR_ADD_BUTTON_BORDER};
    border-radius: {RADIUS_BUTTON}px;
    color: {COLOR_TEXT};
    font-size: {FONT_BASE}px;
    font-weight: 600;
    padding: 12px 14px;
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLOR_ADD_BUTTON_TOP},
        stop:1 {COLOR_ADD_BUTTON}
    );
}}
QPushButton#watchedAddTitle:hover {{
    border-color: {COLOR_ADD_BUTTON_HOVER};
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLOR_ADD_BUTTON_HOVER_TOP},
        stop:1 {COLOR_ADD_BUTTON_HOVER}
    );
}}
QPushButton#watchedFilterToggle {{
    background-color: transparent;
    border: none;
    border-radius: {RADIUS_BUTTON_SMALL}px;
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_SMALL}px;
    font-weight: 600;
    padding: 6px 4px;
    text-align: left;
}}
QPushButton#watchedFilterToggle:hover {{
    color: {COLOR_TEXT};
    background-color: {COLOR_CARD_ALT};
}}
QPushButton#watchedFilterToggle[watchedFiltersActive="true"] {{
    color: {COLOR_TEXT};
}}
QFrame#watchedFiltersPanel {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_INPUT}px;
}}
QPushButton#watchedFilterResetAll {{
    background-color: {COLOR_CARD_ALT};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_BUTTON_SMALL}px;
    color: {COLOR_TEXT};
    font-size: {FONT_SMALL}px;
    font-weight: 600;
    padding: 8px 10px;
}}
QPushButton#watchedFilterResetAll:hover {{
    background-color: {COLOR_CONTROL_HOVER};
    border-color: {COLOR_BORDER_HOVER};
}}
QLabel#watchedListCounter {{
    background: transparent;
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_SMALL}px;
    font-weight: 600;
    padding: 0 4px;
}}
QWidget#watchedSortRow {{
    background: transparent;
}}
QLabel#watchedSortLabel {{
    background: transparent;
    color: {COLOR_TEXT};
    font-size: {FONT_BASE}px;
    font-weight: 600;
}}
QComboBox#watchedSort {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_INPUT}px;
    color: {COLOR_TEXT};
    font-size: {FONT_BASE}px;
    padding: {INPUT_PADDING_Y}px {INPUT_PADDING_X}px;
    min-height: 20px;
}}
QComboBox#watchedSort:focus {{
    border: 1px solid {COLOR_ACCENT};
}}
QComboBox#watchedSort::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox#watchedSort::down-arrow {{
    width: 10px;
    height: 10px;
}}
QFrame#watchedScoreFilter,
QFrame#watchedYearFilter,
QFrame#watchedGenreFilter {{
    background-color: transparent;
    border: none;
    border-radius: 0;
}}
QLabel#watchedScoreFilterTitle,
QLabel#watchedYearFilterTitle,
QLabel#watchedGenreFilterTitle {{
    background: transparent;
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_SMALL}px;
    font-weight: 600;
}}
QComboBox#watchedGenre {{
    background-color: {COLOR_SURFACE};
    font-size: {FONT_SMALL}px;
    padding: 5px 8px;
}}
QLabel#watchedScoreFilterLabel,
QLabel#watchedYearFilterLabel {{
    background: transparent;
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_SMALL}px;
}}
QLabel#watchedFilterValue {{
    background: transparent;
    color: {COLOR_TEXT};
    font-size: {FONT_SMALL}px;
    font-weight: 600;
}}
"""
