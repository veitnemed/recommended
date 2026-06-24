"""Safe deletion of watched dataset records with linked meta and poster-cache."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from config import constant
from posters.cache import (
    DEFAULT_POSTER_CACHE_JSON,
    load_poster_cache,
    poster_identity_key,
    save_poster_cache,
)
from storage import data as storage_data


def _movie_title_year(dataset_key: str, movie: dict) -> tuple[str, object]:
    main_info = movie.get("main_info") or {}
    title = str(main_info.get("title") or movie.get("title") or dataset_key).strip()
    year = main_info.get("year", movie.get("year"))
    return title, year


def _find_meta_key(meta: dict, title: str) -> str | None:
    expected = str(title).strip().lower()
    for meta_title in meta.keys():
        if meta_title.strip().lower() == expected:
            return meta_title
    return None


def search_watched_records_by_query(query: str, data: dict | None = None) -> list[dict]:
    """Return watched records whose title matches query (case-insensitive substring)."""
    dataset = data if data is not None else storage_data.load_dataset()
    normalized_query = str(query or "").strip().casefold()
    if normalized_query == "":
        return []

    matches: list[dict] = []
    for dataset_key, movie in dataset.items():
        if isinstance(movie, dict) is False:
            continue
        title, year = _movie_title_year(dataset_key, movie)
        haystack = f"{dataset_key} {title}".casefold()
        if normalized_query not in haystack:
            continue

        main_info = movie.get("main_info") or {}
        raw_scores = movie.get("raw_scores") or {}
        matches.append(
            {
                "dataset_key": dataset_key,
                "title": title,
                "year": year,
                "user_score": main_info.get("user_score"),
                "kp_score": raw_scores.get("kp_score"),
                "imdb_score": raw_scores.get("imdb_score"),
            }
        )

    matches.sort(key=lambda item: (str(item["title"]).casefold(), str(item.get("year") or "")))
    return matches


def build_watched_delete_preview(dataset_key: str, data: dict | None = None) -> dict | None:
    """Build read-only preview for one dataset record before deletion."""
    dataset = data if data is not None else storage_data.load_dataset()
    movie = dataset.get(dataset_key)
    if isinstance(movie, dict) is False:
        return None

    title, year = _movie_title_year(dataset_key, movie)
    main_info = movie.get("main_info") or {}
    raw_scores = movie.get("raw_scores") or {}
    meta = storage_data.load_meta()
    meta_key = _find_meta_key(meta, title)
    meta_obj = meta.get(meta_key) if meta_key is not None else None

    poster_cache = load_poster_cache()
    cache_identity = poster_identity_key(title, year)
    cache_entry = poster_cache.get(cache_identity)
    if isinstance(cache_entry, dict) is False:
        cache_entry = None

    local_path = None
    if isinstance(cache_entry, dict):
        local_path = cache_entry.get("local_path")

    return {
        "dataset_key": dataset_key,
        "title": title,
        "year": year,
        "user_score": main_info.get("user_score"),
        "kp_score": raw_scores.get("kp_score"),
        "imdb_score": raw_scores.get("imdb_score"),
        "has_meta": meta_key is not None,
        "meta_key": meta_key,
        "has_poster_cache": cache_entry is not None,
        "poster_cache_identity": cache_identity,
        "poster_local_path": local_path,
        "poster_status": cache_entry.get("status") if isinstance(cache_entry, dict) else None,
    }


def backup_before_watched_delete(timestamp: str | None = None) -> list[str]:
    """Backup dataset, meta and poster-cache before delete. Returns created backup paths."""
    stamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f".backup_before_delete_{stamp}"
    backups: list[str] = []

    dataset_path = Path(constant.FILE_NAME)
    if dataset_path.is_file():
        destination = dataset_path.with_name(dataset_path.name + suffix)
        shutil.copy2(dataset_path, destination)
        backups.append(str(destination))

    meta_path = Path(constant.META_JSON)
    if meta_path.is_file():
        destination = meta_path.with_name(meta_path.name + suffix)
        shutil.copy2(meta_path, destination)
        backups.append(str(destination))

    poster_cache_path = DEFAULT_POSTER_CACHE_JSON
    if poster_cache_path.is_file():
        destination = poster_cache_path.with_name(poster_cache_path.name + suffix)
        shutil.copy2(poster_cache_path, destination)
        backups.append(str(destination))

    return backups


def delete_watched_record(dataset_key: str, *, timestamp: str | None = None) -> dict:
    """Delete one watched record from dataset, meta and poster-cache after backup."""
    dataset = storage_data.load_dataset()
    movie = dataset.get(dataset_key)
    if isinstance(movie, dict) is False:
        return {
            "ok": False,
            "message": "Запись не найдена в dataset.",
            "deleted_dataset": 0,
            "deleted_meta": 0,
            "deleted_poster_cache": 0,
            "dataset_count": len(dataset),
            "backups": [],
        }

    title, year = _movie_title_year(dataset_key, movie)
    meta = storage_data.load_meta()
    poster_cache = load_poster_cache()

    meta_key = _find_meta_key(meta, title)
    cache_identity = poster_identity_key(title, year)
    had_cache_entry = isinstance(poster_cache.get(cache_identity), dict)

    backups = backup_before_watched_delete(timestamp=timestamp)

    prepared_dataset = dict(dataset)
    prepared_meta = dict(meta)
    prepared_cache = dict(poster_cache)

    deleted_dataset = 0
    if dataset_key in prepared_dataset:
        del prepared_dataset[dataset_key]
        deleted_dataset = 1

    deleted_meta = 0
    if meta_key is not None and meta_key in prepared_meta:
        del prepared_meta[meta_key]
        deleted_meta = 1

    deleted_poster_cache = 0
    if cache_identity in prepared_cache:
        del prepared_cache[cache_identity]
        deleted_poster_cache = 1

    try:
        storage_data.save_dataset(prepared_dataset)
        storage_data.save_meta(prepared_meta)
        save_poster_cache(prepared_cache)
    except OSError as error:
        return {
            "ok": False,
            "message": f"Ошибка сохранения: {error}",
            "deleted_dataset": 0,
            "deleted_meta": 0,
            "deleted_poster_cache": 0,
            "dataset_count": len(dataset),
            "backups": backups,
        }

    return {
        "ok": True,
        "message": "Запись удалена.",
        "title": title,
        "year": year,
        "deleted_dataset": deleted_dataset,
        "deleted_meta": deleted_meta,
        "deleted_poster_cache": deleted_poster_cache if had_cache_entry else 0,
        "dataset_count": len(prepared_dataset),
        "backups": backups,
    }


def format_watched_delete_preview(preview: dict) -> str:
    """Format delete preview for console output."""
    lines = [
        "Preview удаления:",
        f"  Название: {preview.get('title')}",
        f"  Год: {preview.get('year')}",
        f"  Моя оценка: {preview.get('user_score')}",
    ]

    kp_score = preview.get("kp_score")
    imdb_score = preview.get("imdb_score")
    if kp_score not in (None, ""):
        lines.append(f"  КП: {kp_score}")
    if imdb_score not in (None, ""):
        lines.append(f"  IMDb: {imdb_score}")

    lines.append(f"  Meta: {'да' if preview.get('has_meta') else 'нет'}")
    lines.append(f"  Poster-cache: {'да' if preview.get('has_poster_cache') else 'нет'}")
    if preview.get("poster_local_path"):
        lines.append(f"  Poster local_path: {preview.get('poster_local_path')}")
    return "\n".join(lines)


def format_watched_delete_report(result: dict) -> str:
    """Format delete result report for console output."""
    lines = [
        f"Удалено из dataset: {result.get('deleted_dataset', 0)}",
        f"Удалено из meta: {result.get('deleted_meta', 0)}",
        f"Удалено из poster-cache: {result.get('deleted_poster_cache', 0)}",
        f"Dataset теперь: {result.get('dataset_count', 0)} записей",
        "Backup:",
    ]
    backups = result.get("backups") or []
    if len(backups) == 0:
        lines.append("  —")
    else:
        for backup_path in backups:
            lines.append(f"  - {backup_path}")

    message = result.get("message")
    if message:
        lines.insert(0, str(message))
    return "\n".join(lines)
