"""Shared debounced substring search for desktop list views."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLineEdit


DEFAULT_SEARCH_DEBOUNCE_MS = 200

T = TypeVar("T")


def normalize_search_query(query: str) -> str:
    """Normalize user query for case-insensitive substring matching."""
    return str(query or "").strip().casefold()


def haystack_matches(haystack: str, query: str) -> bool:
    """Return True when normalized query is empty or contained in haystack."""
    normalized = normalize_search_query(query)
    if normalized == "":
        return True
    return normalized in haystack


@dataclass(frozen=True)
class SearchIndexItem(Generic[T]):
    """One searchable list row with precomputed haystack and stable selection key."""

    item: T
    haystack: str
    selection_key: str


class SearchIndex(Generic[T]):
    """Precomputed haystacks for fast repeated title filtering."""

    def __init__(self, items: list[SearchIndexItem[T]] | None = None) -> None:
        self._items: list[SearchIndexItem[T]] = list(items or [])

    def __len__(self) -> int:
        return len(self._items)

    def rebuild(self, items: list[SearchIndexItem[T]]) -> None:
        self._items = list(items)

    def filter_by_query(self, query: str) -> list[T]:
        if normalize_search_query(query) == "":
            return [item.item for item in self._items]
        return [item.item for item in self._items if haystack_matches(item.haystack, query)]


def resolve_selection_row(
    previous_key: str | None,
    visible_items: list[T],
    *,
    key_getter: Callable[[T], str],
) -> int:
    """Pick row to select after filtering; preserve previous item when possible."""
    if previous_key is not None:
        for index, item in enumerate(visible_items):
            if key_getter(item) == previous_key:
                return index
    if visible_items:
        return 0
    return -1


class DebouncedLineEditSearch:
    """Debounce QLineEdit text changes before running an expensive list refresh."""

    def __init__(
        self,
        line_edit: QLineEdit,
        on_search: Callable[[], None],
        *,
        debounce_ms: int = DEFAULT_SEARCH_DEBOUNCE_MS,
        parent=None,
    ) -> None:
        self._line_edit = line_edit
        self._on_search = on_search
        self._timer = QTimer(parent)
        self._timer.setSingleShot(True)
        self._timer.setInterval(max(0, int(debounce_ms)))
        self._timer.timeout.connect(self._emit_search)
        self._line_edit.textChanged.connect(self._schedule_search)

    def _schedule_search(self, _text: str = "") -> None:
        self._timer.start()

    def _emit_search(self) -> None:
        self._on_search()

    def flush(self) -> None:
        """Apply the current query immediately."""
        self._timer.stop()
        self._on_search()

    def cancel(self) -> None:
        self._timer.stop()


def build_search_index(
    items: list[T],
    *,
    haystack_getter: Callable[[T], str],
    key_getter: Callable[[T], str],
) -> SearchIndex[T]:
    """Build a reusable search index from visible list items."""
    indexed = [
        SearchIndexItem(
            item=item,
            haystack=haystack_getter(item),
            selection_key=key_getter(item),
        )
        for item in items
    ]
    return SearchIndex(indexed)
