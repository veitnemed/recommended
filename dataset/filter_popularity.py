"""Read-only popularity aggregates from watched dataset for filter chip UI."""

from __future__ import annotations

from collections import Counter

from candidates.models import country_schema
from candidates.sources.tmdb import country_options as tmdb_country_options
from dataset.score_analytics import collect_analytics_entry_items
from dataset.title_resolve import extract_country_value


def _dataset_entries(data: dict) -> list[tuple[str, dict, dict]]:
    entries: list[tuple[str, dict, dict]] = []
    if not isinstance(data, dict):
        return entries
    for key, movie in data.items():
        if isinstance(movie, dict):
            entries.append((str(key), movie, {}))
    return entries


def _sort_popularity_rows(rows: list[dict], *, label_key: str = "label") -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (-int(row.get("count") or 0), str(row.get(label_key) or "").casefold()),
    )


def build_dataset_genre_popularity(data: dict) -> list[dict]:
    """Count watched titles per genre label; most popular first."""
    counter: Counter[str] = Counter()
    for item in collect_analytics_entry_items(_dataset_entries(data)):
        seen_in_title: set[str] = set()
        for genre in item.get("genres") or []:
            label = str(genre or "").strip()
            if label == "" or label in seen_in_title:
                continue
            seen_in_title.add(label)
            counter[label] += 1

    rows = [{"label": label, "count": count} for label, count in counter.items()]
    return _sort_popularity_rows(rows)


def _country_parts(raw: str) -> list[str]:
    text = str(raw or "").strip()
    if text == "":
        return []
    parts = [part.strip() for part in text.replace(";", ",").split(",")]
    return [part for part in parts if part]


def build_dataset_country_popularity(data: dict) -> list[dict]:
    """Count watched titles per ISO country; most popular first."""
    labels_by_code = tmdb_country_options.COUNTRY_NAMES_RU_BY_CODE
    counter: Counter[str] = Counter()

    for _key, movie, _card in _dataset_entries(data):
        merged = dict(movie)
        main_info = movie.get("main_info")
        if isinstance(main_info, dict):
            merged.update(main_info)
        raw = extract_country_value(merged)
        parts = _country_parts(raw)
        if not parts:
            continue

        seen_in_title: set[str] = set()
        for part in parts:
            iso2 = country_schema.country_value_to_iso2(part)
            if iso2 is None or iso2 in seen_in_title:
                continue
            seen_in_title.add(iso2)
            counter[iso2] += 1

    rows = [
        {
            "code": code,
            "label": labels_by_code.get(code, code),
            "count": count,
        }
        for code, count in counter.items()
    ]
    return _sort_popularity_rows(rows)


def merge_genre_popularity_with_pool(
    dataset_rows: list[dict],
    pool_labels: list[str],
) -> list[dict]:
    """Keep dataset order (popular first), append pool-only genres with count=0."""
    merged = list(dataset_rows)
    seen = {str(row.get("label") or "").casefold() for row in merged}
    extras: list[dict] = []
    for label in pool_labels:
        text = str(label or "").strip()
        if text == "" or text.casefold() in seen:
            continue
        seen.add(text.casefold())
        extras.append({"label": text, "count": 0})
    extras.sort(key=lambda row: str(row.get("label") or "").casefold())
    merged.extend(extras)
    return merged


def merge_country_popularity_with_pool(
    dataset_rows: list[dict],
    pool_rows: list[dict],
) -> list[dict]:
    """Keep dataset order (popular first), append pool-only countries with count=0."""
    merged = list(dataset_rows)
    seen = {str(row.get("code") or "").strip().upper() for row in merged if str(row.get("code") or "").strip()}
    extras: list[dict] = []
    for row in pool_rows:
        code = str(row.get("code") or "").strip().upper()
        label = str(row.get("label") or code).strip()
        if code == "" or code in seen:
            continue
        seen.add(code)
        extras.append({"code": code, "label": label, "count": 0})
    extras.sort(key=lambda row: str(row.get("label") or "").casefold())
    merged.extend(extras)
    return merged
