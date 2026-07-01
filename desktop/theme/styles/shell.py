"""QSS for main window chrome: tabs, scrollbars, status bar, menus."""

from __future__ import annotations

from desktop.theme.tokens import *  # noqa: F403


def build_shell_style() -> str:
    """Return stylesheet for application shell widgets."""
    return f"""
QMainWindow, QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    font-family: {FONT_FAMILY_QSS};
    font-size: {FONT_APP}px;
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
"""
