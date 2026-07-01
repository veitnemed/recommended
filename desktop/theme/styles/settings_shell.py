"""QSS for the Settings/Tools tab."""

from __future__ import annotations

from desktop.theme.tokens import *  # noqa: F403


def build_settings_shell_style() -> str:
    """Return stylesheet for settings tab sections and metric tiles."""
    return f"""
QWidget#settingsToolsRoot {{
    font-size: {FONT_BASE}px;
}}
QLabel#settingsPageTitle {{
    background: transparent;
    color: {COLOR_TEXT};
    font-size: {FONT_SECTION}px;
    font-weight: 700;
}}
QLabel#settingsPageSubtitle {{
    background: transparent;
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_BASE}px;
}}
QFrame#settingsSection {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_CARD}px;
}}
QLabel#settingsSectionTitle {{
    background: transparent;
    color: {COLOR_TEXT};
    font-size: {FONT_BASE}px;
    font-weight: 600;
}}
QLabel#settingsSectionHint {{
    background: transparent;
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_SMALL}px;
}}
QLabel#settingsBodyText {{
    background: transparent;
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_BASE}px;
}}
QLabel#settingsEmptyText {{
    background: transparent;
    color: {COLOR_TEXT_MUTED};
    font-size: {FONT_BASE}px;
}}
QFrame#settingsMetricCard {{
    background-color: {COLOR_CARD_ALT};
    border: 1px solid {COLOR_BORDER};
    border-radius: {RADIUS_INPUT}px;
    min-height: 72px;
}}
QLabel#settingsMetricLabel {{
    background: transparent;
    color: {COLOR_TEXT_SECONDARY};
    font-size: {FONT_SMALL}px;
    font-weight: 600;
}}
QLabel#settingsMetricValue {{
    background: transparent;
    color: {COLOR_TEXT};
    font-size: {FONT_KPI_VALUE}px;
    font-weight: 700;
}}
QLabel#settingsMetricIcon {{
    background: transparent;
    color: {COLOR_ACCENT};
    font-size: {FONT_SECTION}px;
    font-weight: 700;
}}
QComboBox#settingsTmdbImportFile {{
    min-height: 34px;
}}
QPushButton#settingsDangerButton {{
    background-color: {COLOR_CARD_ALT};
    border: 1px solid {COLOR_DELETE_BUTTON};
    border-radius: {RADIUS_BUTTON_SMALL}px;
    color: {COLOR_TEXT};
    font-size: {FONT_SMALL}px;
    font-weight: 600;
    padding: 8px 14px;
    min-height: 32px;
}}
QPushButton#settingsDangerButton:hover {{
    background-color: {COLOR_DELETE_BUTTON};
    border-color: {COLOR_DELETE_BUTTON_HOVER};
}}
QPushButton#settingsDangerButton:disabled {{
    color: {COLOR_TEXT_MUTED};
    border-color: {COLOR_BORDER};
    background-color: {COLOR_CARD};
}}
"""
