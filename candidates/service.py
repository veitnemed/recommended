"""Thin facade for candidate pool console flows (read views and selected write actions)."""

from __future__ import annotations

import json
from pathlib import Path

from candidates import candidate_pool
from candidates import import_tmdb as tmdb_import
from candidates import tmdb_candidate_pool as tmdb_build


def get_pool_view(criteria_name: str | None = None) -> list:
    """Returns candidates for display without writing candidate_pool.json."""
    if criteria_name is None:
        return candidate_pool.get_all_candidates()
    return candidate_pool.get_candidates_by_criteria(criteria_name)


def get_pool_stats_view(criteria_name: str | None = None) -> dict:
    """Returns pool stats and formatted lines for UI without writing JSON."""
    stats = candidate_pool.get_pool_stats(criteria_name=criteria_name)
    return {
        "stats": stats,
        "lines": candidate_pool.format_pool_stats_lines(stats),
        "summary": candidate_pool.format_pool_stats_summary(stats),
    }


def get_contribution_ready_view(candidates: list) -> dict:
    """Prepares ready/incomplete split for contributions UI without model scoring."""
    ready_candidates = candidate_pool.select_ready_candidates_for_contributions(candidates)
    skipped_incomplete = [
        candidate for candidate in candidates
        if candidate_pool.candidate_not_ready_for_contributions_message(candidate) is not None
    ]
    not_ready_messages = [
        {
            "title": candidate.get("title"),
            "year": candidate.get("year"),
            "message": candidate_pool.candidate_not_ready_for_contributions_message(candidate),
        }
        for candidate in skipped_incomplete
    ]

    return {
        "ready_candidates": ready_candidates,
        "skipped_incomplete": skipped_incomplete,
        "skipped_count": len(skipped_incomplete),
        "not_ready_messages": not_ready_messages,
    }


def get_global_top_prediction_view() -> dict:
    """Read-only pool overview for global top prediction screen."""
    stats_view = get_pool_stats_view()
    candidates = get_pool_view()
    return {
        "stats": stats_view["stats"],
        "lines": stats_view["lines"],
        "summary": stats_view["summary"],
        "candidates": candidates,
        "is_empty": stats_view["stats"]["storage_total"] == 0,
    }


def get_prediction_filter_view(candidates: list, filters: dict) -> dict:
    """Applies runtime filters and splits ready/incomplete without model scoring."""
    filtered_candidates = candidate_pool.filter_saved_candidates_for_prediction(candidates, filters)
    ready_candidates = [
        candidate for candidate in filtered_candidates
        if candidate_pool.is_candidate_ready_for_prediction(candidate)
    ]
    incomplete_candidates = [
        candidate for candidate in filtered_candidates
        if candidate_pool.is_candidate_incomplete(candidate)
    ]

    return {
        "filtered_candidates": filtered_candidates,
        "ready_candidates": ready_candidates,
        "incomplete_candidates": incomplete_candidates,
        "filtered_count": len(filtered_candidates),
        "ready_count": len(ready_candidates),
        "skipped_incomplete_count": len(filtered_candidates) - len(ready_candidates),
    }


def get_prediction_filter_defaults_view(criteria_name: str | None = None) -> dict:
    """Returns saved top prediction filter defaults for UI without writing JSON."""
    defaults = candidate_pool.build_prediction_filter_defaults(criteria_name)
    lines = candidate_pool.format_prediction_filter_default_lines(defaults)
    return {
        "defaults": defaults,
        "lines": lines,
        "has_defaults": criteria_name is not None,
    }


def get_prediction_genre_options_view(criteria_name: str | None = None) -> dict:
    """Returns saved-pool genres available for top prediction filters without writing JSON."""
    candidates = get_pool_view(criteria_name)
    genres = candidate_pool.collect_prediction_genre_options(candidates)
    return {
        "criteria_name": criteria_name,
        "genres": genres,
        "count": len(genres),
        "label": "Доступные жанры для top prediction (по сохранённым данным pool)",
    }


def mark_candidate_watched_in_pool(candidate: dict) -> dict:
    """Removes watched candidate from pool via existing title+year write-path."""
    removed_count = candidate_pool.remove_candidate_from_pool(candidate)
    if removed_count > 0:
        message = f"Из pool удалено записей: {removed_count}"
    else:
        message = "Совпадающих записей в pool не найдено"

    return {
        "removed": removed_count > 0,
        "removed_count": removed_count,
        "message": message,
        "candidate": candidate,
    }


def get_retry_kp_view(criteria_name: str | None = None) -> dict:
    """Prepares incomplete-candidate data for retry KP UI without writing JSON."""
    pool = candidate_pool.load_candidate_pool()
    incomplete_candidates = candidate_pool.get_incomplete_candidates(pool, criteria_name=criteria_name)
    all_criteria = candidate_pool.load_candidate_criteria()
    criteria_options = []
    for name in sorted(all_criteria.keys()):
        criteria_options.append({
            "criteria_name": name,
            "label": candidate_pool.build_criteria_label(name, all_criteria[name]),
            "incomplete_count": len(
                candidate_pool.get_incomplete_candidates(pool, criteria_name=name)
            ),
        })

    return {
        "is_empty": len(pool) == 0,
        "incomplete_candidates": incomplete_candidates,
        "incomplete_count": len(incomplete_candidates),
        "criteria_options": criteria_options,
    }


def retry_kp_enrichment_in_pool(limit: int = 10, criteria_name: str | None = None) -> dict:
    """Retries KP enrichment for incomplete pool candidates via existing write-path."""
    stats = candidate_pool.retry_kp_enrichment_for_pool(
        limit=limit,
        criteria_name=criteria_name,
    )
    return {
        "stats": stats,
        "attempted": stats.get("attempted", 0),
        "saved_pool": stats.get("attempted", 0) > 0,
    }


def get_tmdb_import_files_view() -> dict:
    """Returns available TMDb result JSON files for import UI without writing JSON."""
    files = tmdb_import.list_tmdb_result_files()
    return {
        "files": files,
        "file_names": [path.name for path in files],
        "is_empty": len(files) == 0,
    }


def load_tmdb_result_import_preview(result_path: str | Path) -> dict:
    """Loads TMDb result JSON preview for import UI without mutating pool."""
    result_path = Path(result_path)
    try:
        with open(result_path, "r", encoding="utf-8-sig") as file:
            result = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        return {
            "ok": False,
            "error": str(error),
            "result_path": result_path,
            "candidates": [],
            "candidate_count": 0,
            "default_criteria_name": "",
        }

    candidates = result.get("candidates") if isinstance(result, dict) else None
    if isinstance(candidates, list) is False:
        return {
            "ok": False,
            "error": "В файле нет списка candidates.",
            "result_path": result_path,
            "candidates": [],
            "candidate_count": 0,
            "default_criteria_name": "",
        }

    default_criteria_name = tmdb_import.tmdb_import_default_criteria_name(result) or ""
    return {
        "ok": True,
        "error": None,
        "result_path": result_path,
        "result": result,
        "candidates": candidates,
        "candidate_count": len(candidates),
        "default_criteria_name": default_criteria_name,
    }


def import_tmdb_result_to_pool(result_path: str | Path, criteria_name: str | None = None) -> dict:
    """Imports TMDb result JSON into common candidate_pool via existing write-path."""
    result_path = Path(result_path)
    stats = tmdb_import.import_tmdb_result_to_common_pool(result_path, criteria_name=criteria_name)
    resolved_criteria_name = stats.get("criteria_name") or criteria_name
    return {
        "ok": stats.get("ok", False),
        "stats": stats,
        "result_file": str(result_path),
        "criteria_name": resolved_criteria_name,
        "error": stats.get("error"),
    }


def build_tmdb_criteria_name(
    country: str,
    mode: str,
    year_min: int | None = None,
    min_tmdb_score: float | None = None,
) -> str:
    """Returns default criteria_name for TMDb build flow without writing JSON."""
    return tmdb_build.build_tmdb_criteria_name(
        country,
        mode,
        year_min=year_min,
        min_tmdb_score=min_tmdb_score,
    )


def build_tmdb_candidate_pool(
    country: str,
    pages: int = 3,
    details_limit: int = 50,
    mode: str = "quality",
    criteria_name: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    min_tmdb_score: float | None = None,
    min_tmdb_votes: int | None = None,
    with_genres: str | None = None,
    without_genres: str | None = None,
    force_refresh: bool = False,
    db_path=None,
    kp_api_limit: int | None = None,
) -> dict:
    """Builds TMDb candidate snapshot via existing discover/details path."""
    build_kwargs = {
        "country": country,
        "pages": pages,
        "details_limit": details_limit,
        "mode": mode,
        "criteria_name": criteria_name,
        "year_min": year_min,
        "year_max": year_max,
        "min_tmdb_score": min_tmdb_score,
        "min_tmdb_votes": min_tmdb_votes,
        "with_genres": with_genres,
        "without_genres": without_genres,
        "force_refresh": force_refresh,
        "kp_api_limit": kp_api_limit,
    }
    if db_path is not None:
        build_kwargs["db_path"] = db_path
    return tmdb_build.build_candidate_pool(**build_kwargs)


def save_tmdb_build_result(result: dict, *, is_test_run: bool = False) -> dict:
    """Saves TMDb build snapshot JSON/CSV via existing write-path."""
    if is_test_run:
        json_path, csv_path = tmdb_build.save_candidate_pool_test_result(result)
    else:
        json_path, csv_path = tmdb_build.save_candidate_pool_result(result)

    return {
        "ok": True,
        "json_path": json_path,
        "csv_path": csv_path,
        "is_test_run": is_test_run,
        "criteria_name": result.get("criteria_name"),
    }


def build_and_save_tmdb_candidate_pool(*, is_test_run: bool = False, **build_kwargs) -> dict:
    """Builds and saves TMDb snapshot via existing write-path without auto-import prompt."""
    try:
        result = build_tmdb_candidate_pool(**build_kwargs)
    except Exception as error:
        return {
            "ok": False,
            "error": str(error),
            "result": None,
            "json_path": None,
            "csv_path": None,
            "criteria_name": build_kwargs.get("criteria_name"),
            "is_test_run": is_test_run,
            "stats": {},
            "candidates": [],
        }

    save_result = save_tmdb_build_result(result, is_test_run=is_test_run)
    return {
        "ok": True,
        "error": None,
        "result": result,
        "json_path": save_result["json_path"],
        "csv_path": save_result["csv_path"],
        "criteria_name": result.get("criteria_name") or build_kwargs.get("criteria_name"),
        "is_test_run": is_test_run,
        "stats": result.get("stats") or {},
        "candidates": result.get("candidates") or [],
    }


def get_mark_watched_view(criteria_name: str) -> dict:
    """Prepares candidate list and pool stats for mark-watched UI without writing JSON."""
    candidates = get_pool_view(criteria_name)
    stats_view = get_pool_stats_view(criteria_name=criteria_name)
    return {
        "criteria_name": criteria_name,
        "candidates": candidates,
        "stats": stats_view["stats"],
        "lines": stats_view["lines"],
        "summary": stats_view["summary"],
        "is_empty": len(candidates) == 0,
    }


def is_pool_candidate_incomplete(candidate: dict) -> bool:
    """Returns incomplete flag for mark-watched UI without writing JSON."""
    return candidate_pool.is_candidate_incomplete(candidate)


def delete_candidate_pool_criteria(criteria_name: str) -> dict:
    """Deletes criteria and related candidates via existing write-path."""
    result = candidate_pool.delete_criteria_and_candidates(criteria_name)
    return {
        "deleted": result.get("deleted_criteria", False),
        "deleted_criteria": result.get("deleted_criteria", False),
        "deleted_candidates": result.get("deleted_candidates", 0),
        "criteria_name": criteria_name,
    }


def get_suspicious_duplicates_view() -> dict:
    """Prepares suspicious duplicate pairs for diagnostics UI without writing JSON."""
    pairs = candidate_pool.find_suspicious_duplicates()
    return {
        "pairs": pairs,
        "count": len(pairs),
        "is_empty": len(pairs) == 0,
    }


def get_criteria_catalog_view() -> dict:
    """Returns saved criteria names, labels and payloads for UI pickers."""
    all_criteria = candidate_pool.load_candidate_criteria()
    items = []
    for name in sorted(all_criteria.keys()):
        criteria = all_criteria[name]
        items.append({
            "criteria_name": name,
            "criteria": criteria,
            "label": candidate_pool.build_criteria_label(name, criteria),
        })
    return {
        "items": items,
        "by_name": all_criteria,
        "is_empty": len(items) == 0,
    }


def collect_candidates_legacy(criteria_name: str, criteria: dict) -> dict:
    """Collects candidates via legacy KP Discover write-path."""
    return candidate_pool.collect_candidates(criteria_name, criteria)


def rank_top_prediction_candidates(candidates: list, weights: dict) -> dict:
    """Ranks and dedupes candidates for top prediction UI."""
    scored_candidates = candidate_pool.rank_candidates_by_predict(candidates, weights)
    before_dedupe_count = len(scored_candidates)
    scored_candidates = candidate_pool.dedupe_ranked_predictions_by_title_identity(scored_candidates)
    return {
        "candidates": scored_candidates,
        "before_dedupe_count": before_dedupe_count,
        "hidden_duplicates": before_dedupe_count - len(scored_candidates),
    }


def build_contribution_reports(candidates: list, weights: dict) -> list:
    """Builds model contribution reports for ready pool candidates."""
    return candidate_pool.build_contribution_reports_for_ready_candidates(candidates, weights)


def format_candidate_description(candidate: dict, limit: int = 200) -> str:
    """Returns truncated candidate description for UI cards."""
    return candidate_pool.format_candidate_description(candidate, limit=limit)
