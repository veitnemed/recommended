"""Main window shell: tab bar, status bar and cross-tab coordination."""

from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QTabWidget

from desktop.analytics.view import AnalyticsView
from desktop.candidates.filters_view import CandidateFiltersView
from desktop.candidates.list_view import CandidateListView
from desktop.candidates.session import CandidateSearchSession
from desktop.shell.tabs import MainTabRegistry, ShellTabSpec
from desktop.theme import build_app_style
from desktop.watched.model import WatchedEntry
from desktop.watched.tab import WatchedTabView

DARK_STYLE = build_app_style()


class WatchedMoviesWindow(QMainWindow):
    """Main window shell: tab bar, status bar and cross-tab coordination."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Terminal Movies Learn Desktop")
        self.resize(1180, 720)
        self.setStyleSheet(DARK_STYLE)
        self.statusBar().showMessage("")

        tabs = QTabWidget()
        self.setCentralWidget(tabs)
        self._main_tabs = tabs
        self._tab_registry = MainTabRegistry(tabs)

        self._watched_tab_view = WatchedTabView(
            parent=self,
            on_status_message=self._show_status_message,
            on_entries_changed=self._on_watched_entries_changed,
        )
        self._tab_registry.register(ShellTabSpec("watched", "Watched", self._watched_tab_view))

        self._candidate_session = CandidateSearchSession()
        self._candidate_filters_view = CandidateFiltersView(
            self._candidate_session,
            on_applied=self._focus_candidates_tab,
        )
        self._candidate_list_view = CandidateListView(
            self._candidate_session,
            on_watched_added=self._on_candidate_moved_to_watched,
        )
        self._tab_registry.register(ShellTabSpec("filters", "Фильтры", self._candidate_filters_view))
        self._tab_registry.register(ShellTabSpec("candidates", "Кандидаты", self._candidate_list_view))

        self._analytics_view = AnalyticsView(
            self._watched_tab_view.entries,
            entries_provider=lambda: self._watched_tab_view.entries,
        )
        self._tab_registry.register(ShellTabSpec("analytics", "Analytics", self._analytics_view))

        tabs.currentChanged.connect(self._tab_registry.on_current_changed)

    def _show_status_message(self, message: str, timeout_ms: int) -> None:
        self.statusBar().showMessage(message, timeout_ms)

    def _on_watched_entries_changed(self, entries: list[WatchedEntry]) -> None:
        self._analytics_view.update_entries(entries)

    def _on_candidate_moved_to_watched(self, result) -> None:
        added_key = getattr(result, "title", None)
        self._watched_tab_view.reload_entries(added_key=added_key)
        message = getattr(result, "message", None) or "Кандидат перенесён в просмотренные."
        self.statusBar().showMessage(message, 5000)

    def _focus_candidates_tab(self) -> None:
        self._tab_registry.focus("candidates")
