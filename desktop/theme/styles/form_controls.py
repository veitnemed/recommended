"""QSS for shared form controls and range sliders."""

from __future__ import annotations

from desktop.theme.tokens import *  # noqa: F403


def build_form_controls_style() -> str:
    """Return stylesheet for inputs, combos, spinboxes and range sliders."""
    return f"""
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
"""
