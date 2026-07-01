"""QSS builders for main application shell."""

from __future__ import annotations

from desktop.theme.tokens import *  # noqa: F403

def build_app_style() -> str:
    """Return the main desktop application stylesheet."""
    return f"""
QMainWindow, QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    font-family: {FONT_FAMILY_QSS};
    font-size: {FONT_APP}px;
}}
QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_INPUT}px;
    padding: {INPUT_PADDING_Y}px {INPUT_PADDING_X}px;
    color: {COLOR_TEXT};
    selection-background-color: {COLOR_ACCENT};
}}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 1px solid {COLOR_ACCENT};
}}
QDoubleSpinBox::up-button,
QDoubleSpinBox::down-button,
QSpinBox::up-button,
QSpinBox::down-button {{
    background-color: {COLOR_CARD_ALT};
    border: none;
    width: 16px;
}}
QDoubleSpinBox::up-button:hover,
QDoubleSpinBox::down-button:hover,
QSpinBox::up-button:hover,
QSpinBox::down-button:hover {{
    background-color: {COLOR_CONTROL_HOVER};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT};
    selection-background-color: {COLOR_ACCENT_SOFT};
}}
QListWidget {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_CARD}px;
    padding: {SPACING_SMALL}px;
    outline: none;
}}
QListWidget#watchedList {{
    padding: 8px;
}}
QListWidget::item {{
    padding: 0;
    border: none;
    color: {COLOR_TEXT_SOFT};
    margin: 1px 0;
    background: transparent;
}}
QListWidget::item:selected {{
    background: transparent;
    color: {COLOR_TEXT};
}}
QListWidget::item:selected:!active {{
    background: transparent;
    color: {COLOR_TEXT};
}}
QListWidget::item:hover {{
    background: transparent;
}}
QWidget#watchedSidebar {{
    background: transparent;
}}
QLineEdit#watchedSearch {{
    font-size: {FONT_BASE}px;
}}
QLineEdit#candidateListSearch {{
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
QWidget#watchedScoreRange,
QWidget#watchedYearRange,
QWidget#candidateSearchYearRange,
QWidget#candidateSearchKpScoreRange,
QWidget#candidateSearchImdbScoreRange,
QWidget#candidateSearchKpVotesRange,
QWidget#candidateSearchImdbVotesRange {{
    background: transparent;
}}
QLabel#candidateSearchYearRangeLabel,
QLabel#candidateSearchFilterValue {{
    background: transparent;
    color: {COLOR_TEXT};
    font-size: {FONT_BASE}px;
    font-weight: 600;
}}
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QStatusBar {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT_SECONDARY};
    border-top: 1px solid {COLOR_BORDER};
}}
QMenu {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_INPUT}px;
    padding: {SPACING_SMALL}px;
    color: {COLOR_TEXT};
}}
QMenu::item {{
    padding: {BUTTON_PADDING_Y}px {BUTTON_PADDING_X}px;
    border-radius: {RADIUS_BUTTON_SMALL}px;
}}
QMenu::item:selected {{
    background-color: {COLOR_ACCENT_SOFT};
}}
QSplitter::handle {{
    background-color: {COLOR_BG};
}}
QSplitter::handle:hover {{
    background-color: {COLOR_BORDER};
}}
QScrollBar:vertical {{
    background: {COLOR_BG};
    width: 10px;
    margin: {SPACING_XSMALL}px;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_BORDER};
    border-radius: {RADIUS_SCROLLBAR}px;
    min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLOR_BORDER_HOVER};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {COLOR_BG};
    height: 10px;
    margin: {SPACING_XSMALL}px;
}}
QScrollBar::handle:horizontal {{
    background: {COLOR_BORDER};
    border-radius: {RADIUS_SCROLLBAR}px;
    min-width: 28px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QTabWidget::pane {{
    border: none;
}}
QTabBar::tab {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_INPUT}px;
    color: {COLOR_TEXT_SECONDARY};
    padding: 9px 16px;
    margin-right: {SPACING_SMALL}px;
}}
QTabBar::tab:selected {{
    background-color: {COLOR_CARD_ALT};
    color: {COLOR_TEXT};
    border-color: {COLOR_ACCENT};
}}
QTabBar::tab:hover {{
    background-color: {COLOR_HOVER};
    color: {COLOR_TEXT};
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
QPushButton#candidateMarkWatchedButton {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 18px;
    color: {COLOR_TEXT};
    font-size: 16px;
    padding: 0;
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
}}
QPushButton#candidateMarkWatchedButton:hover {{
    border-color: {COLOR_ACCENT};
    background-color: {COLOR_CARD_ALT};
}}
QPushButton#candidateMarkWatchedButton:disabled {{
    color: {COLOR_TEXT_SECONDARY};
    border-color: {COLOR_BORDER};
}}
QPushButton#genreFilterChip {{
    background-color: {COLOR_CARD_ALT};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_CHIP}px;
    color: {COLOR_TEXT_CHIP};
    font-size: {FONT_BASE}px;
    font-weight: 500;
    padding: 8px 14px;
    min-height: 36px;
}}
QPushButton#genreFilterChip:hover {{
    background-color: {COLOR_HOVER};
    border-color: {COLOR_BORDER_HOVER};
}}
QPushButton#genreFilterChip:checked {{
    background-color: {COLOR_ACCENT_SOFT};
    border-color: {COLOR_ACCENT};
    color: {COLOR_TEXT};
}}
QPushButton#genreChipClear {{
    background: transparent;
    border: none;
    color: {COLOR_TEXT_MUTED};
    font-size: {FONT_BASE}px;
    padding: 4px 6px;
    min-height: 28px;
}}
QPushButton#genreChipClear:hover {{
    color: {COLOR_TEXT_SECONDARY};
}}
QLabel#genreChipCount {{
    background: transparent;
    color: {COLOR_TEXT_MUTED};
    font-size: {FONT_BASE}px;
}}
QWidget#genreChipHost {{
    background: transparent;
    padding-top: 2px;
}}
QWidget#candidateFiltersRoot {{
    font-size: {FONT_BASE}px;
}}
QPushButton#countryFilterChip {{
    background-color: {COLOR_CARD_ALT};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_CHIP}px;
    color: {COLOR_TEXT_CHIP};
    font-size: {FONT_BASE}px;
    font-weight: 500;
    padding: 8px 14px;
    min-height: 36px;
}}
QPushButton#countryFilterChip:hover {{
    background-color: {COLOR_HOVER};
    border-color: {COLOR_BORDER_HOVER};
}}
QPushButton#countryFilterChip:checked {{
    background-color: {COLOR_ACCENT_SOFT};
    border-color: {COLOR_ACCENT};
    color: {COLOR_TEXT};
}}
QPushButton#countryChipClear {{
    background: transparent;
    border: none;
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_SMALL}px;
    padding: 0 4px;
}}
QPushButton#countryChipClear:hover {{
    color: {COLOR_TEXT};
}}
QLabel#countryChipCount {{
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_SMALL}px;
}}
QWidget#countryChipHost {{
    background: transparent;
    padding-top: 2px;
}}
QPushButton#chipExpandToggle {{
    background: transparent;
    border: none;
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_SMALL}px;
    padding: 0 4px;
    text-align: left;
}}
QPushButton#chipExpandToggle:hover {{
    color: {COLOR_TEXT};
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
QComboBox#candidateSearchCriteria,
QSpinBox#candidateSearchYearMin,
QSpinBox#candidateSearchYearMax,
QSpinBox#candidateSearchTopN {{
    background-color: {COLOR_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_INPUT}px;
    color: {COLOR_TEXT};
    font-size: {FONT_BASE}px;
    padding: 6px 10px;
    min-height: 34px;
}}
QCheckBox#candidateSearchOnlyComplete,
QCheckBox#candidateSearchOnlyUnwatched,
QCheckBox#candidateSearchHideHidden {{
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_BASE}px;
    spacing: 8px;
    min-height: 28px;
}}
QCheckBox#candidateSearchOnlyComplete::indicator,
QCheckBox#candidateSearchOnlyUnwatched::indicator,
QCheckBox#candidateSearchHideHidden::indicator {{
    width: 18px;
    height: 18px;
}}
QFrame#candidateSearchDetailCard {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_CARD}px;
}}
"""
