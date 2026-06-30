"""Shared filter/sort state between desktop Filters and Candidates tabs."""

from __future__ import annotations

from typing import Callable

from candidates import service as candidate_service

DEFAULT_TOP_N = 20
DEFAULT_SORT_MODE = "kp_score"


class CandidateSearchSession:
    """Runtime candidate search state shared across desktop tabs."""

    def __init__(self) -> None:
        self.filters: dict | None = None
        self.filtered_candidates: list[dict] = []
        self.filtered_count: int = 0
        self.hidden_duplicates: int = 0
        self.sort_mode: str = DEFAULT_SORT_MODE
        self.top_n: int = DEFAULT_TOP_N
        self._sorted_all: list[dict] = []
        self._display_candidates: list[dict] = []
        self._listeners: list[Callable[[], None]] = []

    def add_listener(self, callback: Callable[[], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def _notify_listeners(self) -> None:
        for callback in self._listeners:
            callback()

    def _clear_sorted_cache(self) -> None:
        self._sorted_all = []
        self._display_candidates = []
        self.hidden_duplicates = 0

    def _rebuild_sorted_cache(self) -> None:
        if not self.filtered_candidates:
            self._clear_sorted_cache()
            return
        sort_view = candidate_service.sort_search_candidates(
            self.filtered_candidates,
            self.sort_mode,
        )
        self.hidden_duplicates = int(sort_view.get("hidden_duplicates") or 0)
        self._sorted_all = list(sort_view.get("candidates") or [])
        self._apply_top_n_slice()

    def _apply_top_n_slice(self) -> None:
        if not self._sorted_all:
            self._display_candidates = []
            return
        limit = min(self.top_n, len(self._sorted_all))
        self._display_candidates = self._sorted_all[:limit]

    @property
    def has_results(self) -> bool:
        return self.filters is not None

    def apply_filters(self, filters: dict) -> dict:
        """Filter saved pool candidates without sorting."""
        overview = candidate_service.get_search_overview_view()
        if overview.get("is_empty"):
            self.filters = None
            self.filtered_candidates = []
            self.filtered_count = 0
            self._clear_sorted_cache()
            result = {
                "ok": False,
                "is_empty_pool": True,
                "filtered_count": 0,
                "message": "Общий candidate pool пуст.",
            }
            self._notify_listeners()
            return result

        search_view = candidate_service.search_candidate_pool(overview["candidates"], filters)
        self.filters = dict(filters)
        self.filtered_candidates = list(search_view.get("candidates") or [])
        self.filtered_count = int(search_view.get("filtered_count") or 0)
        self._rebuild_sorted_cache()
        result = {
            "ok": True,
            "is_empty_pool": False,
            "filtered_count": self.filtered_count,
            "message": f"После фильтра: {self.filtered_count}",
        }
        self._notify_listeners()
        return result

    def set_sort_mode(self, sort_mode: str) -> None:
        if sort_mode in candidate_service.SEARCH_SORT_MODES:
            self.sort_mode = sort_mode
            self._rebuild_sorted_cache()
            self._notify_listeners()

    def set_top_n(self, top_n: int) -> None:
        self.top_n = max(1, int(top_n))
        self._apply_top_n_slice()
        self._notify_listeners()

    def sorted_candidates(self) -> list[dict]:
        """Return top-N candidates sorted by the active sort mode."""
        return list(self._display_candidates)

    def sorted_total_count(self) -> int:
        return len(self._sorted_all)
