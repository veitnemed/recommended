"""Main window tab registry and activation dispatch."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import QTabWidget, QWidget


@dataclass(frozen=True)
class ShellTabSpec:
    """One registered main-window tab."""

    tab_id: str
    label: str
    view: object


class MainTabRegistry:
    """Register feature views with QTabWidget and dispatch on_tab_activated."""

    def __init__(self, tabs_widget: QTabWidget) -> None:
        self._tabs = tabs_widget
        self._specs: dict[str, ShellTabSpec] = {}
        self._widget_to_id: dict[QWidget, str] = {}

    def register(self, spec: ShellTabSpec) -> None:
        self._tabs.addTab(spec.view.widget, spec.label)
        self._specs[spec.tab_id] = spec
        self._widget_to_id[spec.view.widget] = spec.tab_id

    def focus(self, tab_id: str) -> None:
        spec = self._specs[tab_id]
        self._tabs.setCurrentWidget(spec.view.widget)

    def on_current_changed(self, index: int) -> None:
        if index < 0:
            return
        widget = self._tabs.widget(index)
        if widget is None:
            return
        tab_id = self._widget_to_id.get(widget)
        if tab_id is None:
            return
        view = self._specs[tab_id].view
        activated = getattr(view, "on_tab_activated", None)
        if callable(activated):
            activated()
