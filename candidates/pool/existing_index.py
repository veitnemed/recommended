"""Read-only index for skipping already known discover candidates."""

from __future__ import annotations

from typing import Any

from apis import tmdb_api
from candidates.models.keys import normalize_key_part
from candidates.pool.normalization import normalize_storage_pool


def _coerce_tmdb_id(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_year(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(str(value)[:4])
    except (TypeError, ValueError):
        return None


def _title_year_key(title, year) -> str | None:
    normalized_title = normalize_key_part(title)
    normalized_year = _coerce_year(year)
    if normalized_title == "" or normalized_year is None:
        return None
    return f"{normalized_title}|{normalized_year}"


def _candidate_title_year_key(candidate: dict[str, Any]) -> str | None:
    title = (
        candidate.get("title")
        or candidate.get("name")
        or candidate.get("alternative_title")
        or candidate.get("original_title")
        or candidate.get("original_name")
        or ""
    )
    return _title_year_key(title, candidate.get("year"))


def _discover_title_year_key(item: dict[str, Any]) -> str | None:
    title = item.get("name") or item.get("original_name") or ""
    return _title_year_key(title, tmdb_api.get_year(item.get("first_air_date")))


def build_existing_candidate_index(pool) -> dict[str, set]:
    """Build tmdb_id and normalized title/year sets from saved pool records."""
    normalized_pool = normalize_storage_pool(pool if isinstance(pool, dict) else {})
    tmdb_ids: set[int] = set()
    title_year_keys: set[str] = set()

    for candidate in normalized_pool.values():
        if isinstance(candidate, dict) is False:
            continue
        tmdb_id = _coerce_tmdb_id(candidate.get("tmdb_id"))
        if tmdb_id is not None:
            tmdb_ids.add(tmdb_id)

        title_year_key = _candidate_title_year_key(candidate)
        if title_year_key is not None:
            title_year_keys.add(title_year_key)

    return {
        "tmdb_ids": tmdb_ids,
        "title_year_keys": title_year_keys,
    }


def discover_item_existing_reason(item: dict[str, Any], index: dict) -> str | None:
    """Return the first existing-match reason for one TMDb discover item."""
    tmdb_id = _coerce_tmdb_id(item.get("id"))
    if tmdb_id is not None and tmdb_id in (index.get("tmdb_ids") or set()):
        return "tmdb_id"

    title_year_key = _discover_title_year_key(item)
    if title_year_key is not None and title_year_key in (index.get("title_year_keys") or set()):
        return "title_year"

    return None


def is_discover_item_existing(item: dict[str, Any], index: dict) -> bool:
    """Return True when a TMDb discover item already exists in the saved pool."""
    return discover_item_existing_reason(item, index) is not None


def filter_existing_discover_items(items: list[dict[str, Any]], index: dict) -> list[dict[str, Any]]:
    """Filter discover items already present in saved candidate pool."""
    return [
        item
        for item in items
        if is_discover_item_existing(item, index) is False
    ]
