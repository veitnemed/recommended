"""QSS for genre/country chip selectors and expand toggles."""

from __future__ import annotations

from desktop.theme.tokens import *  # noqa: F403


def build_chip_selector_style() -> str:
    """Return stylesheet for collapsible chip selectors."""
    return f"""
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
"""
