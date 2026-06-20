"""TMDb result import helpers for the common candidate pool."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from candidates import candidate_pool as legacy_candidate_pool
from candidates.keys import DEFAULT_CRITERIA_NAME, pool_entry_key
from candidates.schema import normalize_candidate_record


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "data" / "candidate_pool"


def list_tmdb_result_files() -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = [
        path for path in OUTPUT_DIR.glob("*candidate_pool_*.json")
        if path.is_file()
    ]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return files


def normalize_tmdb_candidate_for_common_import(candidate: dict[str, Any], criteria_name: str) -> dict[str, Any]:
    normalized = dict(candidate)
    normalized.update({
        "id": candidate.get("kp_id"),
        "title": candidate.get("title"),
        "alternative_title": candidate.get("original_title"),
        "year": candidate.get("year"),
        "type": candidate.get("type") or "series",
        "description": candidate.get("description") or candidate.get("overview") or "",
        "kp_score": candidate.get("kp_score") if candidate.get("kp_score") is not None else candidate.get("kp_rating"),
        "kp_votes": candidate.get("kp_votes"),
        "imdb_score": candidate.get("imdb_score") if candidate.get("imdb_score") is not None else candidate.get("imdb_rating"),
        "imdb_votes": candidate.get("imdb_votes"),
        "countries": candidate.get("countries") or candidate.get("tmdb_origin_countries") or [],
        "genres": candidate.get("genres") or candidate.get("imdb_genres") or candidate.get("genres_tmdb") or [],
        "criteria_name": criteria_name,
        "source": "tmdb_imdb_kp_v1",
        "tmdb_id": candidate.get("tmdb_id"),
        "imdb_id": candidate.get("imdb_id"),
        "kp_id": candidate.get("kp_id"),
        "tmdb_score": candidate.get("tmdb_score") if candidate.get("tmdb_score") is not None else candidate.get("tmdb_rating"),
        "tmdb_votes": candidate.get("tmdb_votes"),
        "kp_status": candidate.get("kp_status"),
        "is_complete": candidate.get("is_complete"),
        "signals": candidate.get("signals") or [],
        "saved_at": datetime.now().isoformat(timespec="seconds"),
    })
    return normalize_candidate_record(normalized)


def tmdb_import_default_criteria_name(result: dict[str, Any]) -> str | None:
    candidates = result.get("candidates") or []
    for value in [
        result.get("criteria_name"),
        (result.get("criteria") or {}).get("criteria_name") if isinstance(result.get("criteria"), dict) else None,
        (result.get("settings") or {}).get("criteria_name") if isinstance(result.get("settings"), dict) else None,
    ]:
        text = str(value or "").strip()
        if text:
            return text

    for candidate in candidates:
        value = str(candidate.get("criteria_name") or "").strip()
        if value:
            return value

    country = str(result.get("country") or "").strip()
    mode = str(result.get("mode") or "").strip()
    if country and mode:
        return f"tmdb_{country}_{mode}"
    return None


def resolve_tmdb_import_criteria_name(result: dict[str, Any], criteria_name: str | None = None) -> str:
    resolved = str(criteria_name or tmdb_import_default_criteria_name(result) or "").strip()
    return resolved or DEFAULT_CRITERIA_NAME


def _base_import_stats(read: int, criteria_name: str, pool_size_before: int) -> dict[str, Any]:
    return {
        "ok": True,
        "error": None,
        "read": read,
        "added": 0,
        "updated": 0,
        "watched_skipped": 0,
        "skipped_watched": 0,
        "duplicates": 0,
        "skipped_duplicates": 0,
        "errors": 0,
        "criteria_name": criteria_name,
        "source": "tmdb_imdb_kp_v1",
        "pool_size_before": pool_size_before,
        "pool_size_after": pool_size_before,
        "pool_size": pool_size_before,
    }


def import_tmdb_candidates_to_common_pool(
    candidates: list[dict[str, Any]],
    criteria_name: str | None = None,
    *,
    result_metadata: dict[str, Any] | None = None,
    result_path: str | Path | None = None,
) -> dict[str, Any]:
    result_metadata = result_metadata or {}
    resolved_criteria_name = resolve_tmdb_import_criteria_name(result_metadata, criteria_name)
    pool = legacy_candidate_pool.normalize_pool(legacy_candidate_pool.load_candidate_pool())
    watched_signatures = legacy_candidate_pool.build_watched_signatures()
    stats = _base_import_stats(len(candidates), resolved_criteria_name, len(pool))

    for raw_candidate in candidates:
        if isinstance(raw_candidate, dict) is False:
            stats["errors"] += 1
            continue

        candidate = normalize_tmdb_candidate_for_common_import(raw_candidate, resolved_criteria_name)
        if not candidate.get("title") or not candidate.get("year"):
            stats["errors"] += 1
            continue

        if legacy_candidate_pool.is_watched_candidate(candidate, watched_signatures):
            stats["watched_skipped"] += 1
            stats["skipped_watched"] += 1
            continue

        matched_key = pool_entry_key(candidate)
        matched_candidate = pool.get(matched_key)
        if matched_candidate is None:
            pool[matched_key] = candidate
            stats["added"] += 1
            continue

        if legacy_candidate_pool.candidate_sort_score(candidate) > legacy_candidate_pool.candidate_sort_score(matched_candidate):
            pool[matched_key] = candidate
            stats["updated"] += 1
        else:
            stats["duplicates"] += 1
            stats["skipped_duplicates"] += 1

    legacy_candidate_pool.save_named_criteria(resolved_criteria_name, {
        "country": result_metadata.get("country"),
        "count": len(candidates),
        "min_kp": None,
        "min_imdb": None,
        "min_kp_votes": None,
        "min_imdb_votes": None,
        "min_year": None,
        "max_year": None,
        "genres": [],
        "excluded_genres": [],
        "source": "tmdb_imdb_kp_v1",
        "settings": result_metadata.get("settings") or {},
        "result_file": str(result_path) if result_path is not None else "",
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    })
    legacy_candidate_pool.save_candidate_pool(pool)
    pool_size_after = len(legacy_candidate_pool.load_candidate_pool())
    stats["pool_size_after"] = pool_size_after
    stats["pool_size"] = pool_size_after
    return stats


def import_tmdb_result_to_common_pool(result_path: str | Path, criteria_name: str | None = None) -> dict[str, Any]:
    result_path = Path(result_path)
    try:
        with open(result_path, "r", encoding="utf-8-sig") as file:
            result = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        return {
            "ok": False,
            "error": str(error),
            "read": 0,
            "added": 0,
            "updated": 0,
            "watched_skipped": 0,
            "skipped_watched": 0,
            "duplicates": 0,
            "skipped_duplicates": 0,
            "errors": 1,
            "criteria_name": str(criteria_name or "").strip(),
            "pool_size_before": 0,
            "pool_size_after": 0,
            "pool_size": 0,
        }

    candidates = result.get("candidates") if isinstance(result, dict) else None
    if isinstance(candidates, list) is False:
        return {
            "ok": False,
            "error": "В файле нет списка candidates.",
            "read": 0,
            "added": 0,
            "updated": 0,
            "watched_skipped": 0,
            "skipped_watched": 0,
            "duplicates": 0,
            "skipped_duplicates": 0,
            "errors": 1,
            "criteria_name": str(criteria_name or "").strip(),
            "pool_size_before": 0,
            "pool_size_after": 0,
            "pool_size": 0,
        }

    return import_tmdb_candidates_to_common_pool(
        candidates,
        criteria_name=criteria_name,
        result_metadata=result if isinstance(result, dict) else {},
        result_path=result_path,
    )
