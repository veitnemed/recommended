"""QSS for the Candidates filters and list tabs."""

from __future__ import annotations

from desktop.theme.tokens import *  # noqa: F403


def build_candidates_shell_style() -> str:
    """Return stylesheet for candidate search filters and list."""
    return f"""
QLineEdit#candidateListSearch {{
    font-size: {FONT_BASE}px;
}}
QWidget#candidateSearchSidebar {{
    background: transparent;
}}
QLabel#candidateSearchHeader {{
    background: transparent;
    color: {COLOR_TEXT};
    font-size: {FONT_SECTION}px;
    font-weight: 700;
}}
QFrame#candidateFiltersIntro {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_CARD}px;
}}
QLabel#candidateFiltersIntroLead {{
    background: transparent;
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_BASE}px;
    line-height: 1.35;
}}
QLabel#candidateFiltersIntroStats {{
    background: transparent;
    color: {COLOR_TEXT};
    font-size: {FONT_SECTION}px;
    font-weight: 600;
}}
QLabel#candidateSearchHint,
QLabel#candidateSearchResultsSummary,
QLabel#candidateSearchDetailPlaceholder,
QLabel#candidateSearchExplanation {{
    background: transparent;
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_BASE}px;
}}
QLabel#candidateSearchFieldLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: {FONT_BASE}px;
    font-weight: 600;
    padding-top: 2px;
}}
QListWidget#candidateListWidget {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_CARD}px;
    color: {COLOR_TEXT};
    font-size: {FONT_SMALL}px;
    padding: 8px;
    outline: none;
}}
QListWidget#candidateListWidget::item {{
    padding: 0;
    border: none;
    margin: 1px 0;
    background: transparent;
}}
QListWidget#candidateListWidget::item:selected {{
    background: transparent;
    color: {COLOR_TEXT};
}}
QListWidget#candidateListWidget::item:hover {{
    background: transparent;
}}
QLabel#candidateListCounter {{
    background: transparent;
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_SMALL}px;
    font-weight: 600;
    padding: 0 4px;
}}
QWidget#candidateSortRow {{
    background: transparent;
}}
QLabel#candidateSortLabel {{
    background: transparent;
    color: {COLOR_TEXT};
    font-size: {FONT_BASE}px;
    font-weight: 600;
}}
QComboBox#candidateListSort {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_INPUT}px;
    color: {COLOR_TEXT};
    font-size: {FONT_BASE}px;
    padding: {INPUT_PADDING_Y}px {INPUT_PADDING_X}px;
    min-height: 20px;
    max-width: 160px;
}}
QComboBox#candidateListSort:focus {{
    border: 1px solid {COLOR_ACCENT};
}}
QComboBox#candidateListSort::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox#candidateListSort::down-arrow {{
    width: 10px;
    height: 10px;
}}
QWidget#candidateFiltersRoot {{
    font-size: {FONT_BASE}px;
}}
QPushButton#candidateSearchApplyTopButton {{
    background-color: {COLOR_ADD_BUTTON};
    border: 1px solid {COLOR_ADD_BUTTON_BORDER};
    border-radius: {RADIUS_BUTTON_SMALL}px;
    color: {COLOR_TEXT};
    font-size: {FONT_SMALL}px;
    font-weight: 600;
    padding: 4px 12px;
    min-height: 28px;
    max-height: 32px;
}}
QPushButton#candidateSearchApplyTopButton:hover {{
    background-color: {COLOR_ADD_BUTTON_TOP};
}}
QPushButton#candidateSearchButton,
QPushButton#candidateSearchAddWatched {{
    background-color: {COLOR_ADD_BUTTON};
    border: 1px solid {COLOR_ADD_BUTTON_BORDER};
    border-radius: {RADIUS_BUTTON}px;
    color: {COLOR_TEXT};
    font-size: {FONT_BASE}px;
    font-weight: 600;
    padding: 10px 16px;
    min-height: 40px;
}}
QPushButton#candidateSearchButton:hover,
QPushButton#candidateSearchAddWatched:hover {{
    background-color: {COLOR_ADD_BUTTON_TOP};
}}
QPushButton#candidateSearchWatchlist,
QPushButton#candidateSearchHide {{
    background-color: {COLOR_CARD_ALT};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_BUTTON}px;
    color: {COLOR_TEXT};
    font-size: {FONT_SMALL}px;
    padding: 8px 12px;
}}
QPushButton#candidateSearchWatchlist:hover,
QPushButton#candidateSearchHide:hover {{
    background-color: {COLOR_CONTROL_HOVER};
}}
QFrame#candidateSearchDetailCard {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_CARD}px;
}}
"""
