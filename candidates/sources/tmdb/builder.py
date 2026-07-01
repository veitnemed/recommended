"""Build orchestration for TMDb + local IMDb SQL candidate pools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from candidates.models.keys import COMMON_POOL_CRITERIA_NAME
from candidates.pool.existing_index import (
    build_existing_candidate_index,
    discover_item_existing_reason,
)
from candidates.repositories.pool_repository import load_candidate_pool
from candidates.sources.tmdb import debug as kp_tmdb_build_debug
from candidates.sources.tmdb.discover_dedupe import (
    deduplicate_discover_results,
    remove_watched_discover,
    sort_discover_for_details,
)
from candidates.sources.tmdb.discover_query import (
    apply_discover_filters,
    discover_defaults,
    is_iso2_country_code,
    normalize_country_code,
    normalize_optional_tmdb_genre_filter,
)
from candidates.sources.tmdb.transformer import (
    NETWORK_ERROR_SKIP_THRESHOLD,
    append_signal,
    compute_final_score,
    compute_hidden_gem_score,
    compute_quality_score,
    connect_imdb,
    enrich_from_imdb_sql,
    enrich_from_kp_api_if_needed,
    enrich_from_kp_cache_only,
    mark_kp_pending_limit,
    normalize_tmdb_candidate_for_common_pool,
    passes_imdb_filters,
    prepare_candidate,
    report_progress,
)
from apis import imdb_sql as sql_search
from apis import tmdb_api as api_tmdb


ENRICHMENT_MODES = {"full", "fast", "kp_cache", "kp_top"}


def _sort_candidates_by_scores(candidates: list[dict[str, Any]]) -> None:
    candidates.sort(
        key=lambda candidate: (
            -(candidate.get("final_score") or 0),
            -(candidate.get("quality_score") or 0),
            -(candidate.get("tmdb_votes") or 0),
            candidate.get("title") or "",
        )
    )


def build_candidate_pool(
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
    db_path: str | Path = sql_search.DEFAULT_DB_PATH,
    kp_api_limit: int | None = None,
    kp_build_debug: bool = True,
    skip_existing_pool: bool = False,
    enrichment_mode: str = "full",
    kp_top_limit: int | None = None,
) -> dict[str, Any]:
    country = normalize_country_code(country)
    if is_iso2_country_code(country) is False:
        raise ValueError("country must be a 2-letter ISO code")
    if mode not in {"quality", "hidden_gems"}:
        raise ValueError("mode должен быть quality или hidden_gems")
    if enrichment_mode not in ENRICHMENT_MODES:
        raise ValueError("enrichment_mode должен быть full, fast, kp_cache или kp_top")
    criteria_name = str(criteria_name or "").strip() or COMMON_POOL_CRITERIA_NAME

    token = api_tmdb.load_tmdb_token()
    query = apply_discover_filters(
        discover_defaults(country),
        year_min=year_min,
        year_max=year_max,
        min_tmdb_score=min_tmdb_score,
        min_tmdb_votes=min_tmdb_votes,
        with_genres=with_genres,
        without_genres=without_genres,
    )
    report_progress("TMDb Discover", "Ожидание ответа")
    try:
        discover_results = api_tmdb.discover_tv_candidates(
            max_pages=pages,
            force_refresh=force_refresh,
            token=token,
            **query,
        )
    except Exception:
        report_progress("TMDb Discover", "Ошибка сети")
        raise
    report_progress("TMDb Discover", f"Успешно, кандидатов: {len(discover_results)}")
    unique_results, duplicates_removed = deduplicate_discover_results(discover_results)
    not_watched_results, watched_skipped = remove_watched_discover(unique_results)
    novelty_source_total = len(not_watched_results)
    existing_pool_skipped_tmdb_id = 0
    existing_pool_skipped_title_year = 0
    if skip_existing_pool:
        existing_index = build_existing_candidate_index(load_candidate_pool())
        novel_results: list[dict[str, Any]] = []
        for item in not_watched_results:
            existing_reason = discover_item_existing_reason(item, existing_index)
            if existing_reason == "tmdb_id":
                existing_pool_skipped_tmdb_id += 1
                continue
            if existing_reason == "title_year":
                existing_pool_skipped_title_year += 1
                continue
            novel_results.append(item)
        not_watched_results = novel_results

    sorted_results = sort_discover_for_details(not_watched_results)
    details_candidates = sorted_results[: int(details_limit)]
    novelty_rate_before_details = (
        len(not_watched_results) / novelty_source_total
        if novelty_source_total > 0
        else 0.0
    )

    use_imdb_sql = enrichment_mode == "full"
    use_kp_cache = enrichment_mode in {"full", "kp_cache", "kp_top"}
    use_kp_api = enrichment_mode in {"full", "kp_top"}
    kp_top_limit_value = int(kp_top_limit) if kp_top_limit is not None else int(kp_api_limit or 50)
    kp_top_limit_value = max(0, kp_top_limit_value)

    conn = connect_imdb(db_path) if use_imdb_sql and len(details_candidates) > 0 else None
    candidates: list[dict[str, Any]] = []
    stats = {
        "discover_total": len(discover_results),
        "discover_filters": {
            "year_min": year_min,
            "year_max": year_max,
            "min_tmdb_score": min_tmdb_score,
            "min_tmdb_votes": min_tmdb_votes,
            "with_genres": normalize_optional_tmdb_genre_filter(with_genres),
            "without_genres": normalize_optional_tmdb_genre_filter(without_genres),
        },
        "duplicates_removed": duplicates_removed,
        "watched_skipped": watched_skipped,
        "existing_pool_skipped_tmdb_id": existing_pool_skipped_tmdb_id,
        "existing_pool_skipped_title_year": existing_pool_skipped_title_year,
        "novel_before_details": len(not_watched_results),
        "novelty_rate_before_details": round(novelty_rate_before_details, 4),
        "details_requested": len(details_candidates),
        "tmdb_details_errors": 0,
        "tmdb_details_skipped_after_errors": 0,
        "has_imdb_id": 0,
        "found_in_imdb_sql": 0,
        "country_passed": 0,
        "country_borderline": 0,
        "country_rejected": 0,
        "imdb_filter_rejected": 0,
        "adult_title_type_rejected": 0,
        "kp_cache_hit": 0,
        "kp_api_requested": 0,
        "kp_api_found": 0,
        "kp_api_not_found": 0,
        "kp_api_rejected_by_match": 0,
        "kp_api_errors": 0,
        "kp_api_skipped_after_errors": 0,
        "kp_api_skipped_cache": 0,
        "kp_api_skipped_not_top": 0,
        "kp_pending_limit": 0,
        "kp_incomplete_candidates": 0,
        "complete_candidates": 0,
        "final_candidates": 0,
        "enrichment_mode": enrichment_mode,
        "kp_top_limit": kp_top_limit_value if enrichment_mode == "kp_top" else None,
    }

    tmdb_details_consecutive_errors = 0
    tmdb_details_skip_network = False
    kp_api_consecutive_errors = 0
    kp_api_skip_network = False
    kp_debug_session = None
    if kp_build_debug:
        kp_debug_session = kp_tmdb_build_debug.KpBuildDebugSession(
            country=country,
            criteria_name=criteria_name,
        )

    try:
        for detail_index, item in enumerate(details_candidates, start=1):
            if tmdb_details_skip_network:
                stats["tmdb_details_skipped_after_errors"] += 1
                report_progress("TMDb Details", f"Пропущено [{detail_index}/{len(details_candidates)}]")
                continue

            report_progress("TMDb Details", f"Ожидание ответа [{detail_index}/{len(details_candidates)}]")
            try:
                details = api_tmdb.get_tv_details(
                    int(item["id"]),
                    language=query["language"],
                    force_refresh=force_refresh,
                    token=token,
                )
            except Exception:
                stats["tmdb_details_errors"] += 1
                tmdb_details_consecutive_errors += 1
                report_progress("TMDb Details", "Ошибка сети")
                if tmdb_details_consecutive_errors >= NETWORK_ERROR_SKIP_THRESHOLD:
                    tmdb_details_skip_network = True
                continue
            tmdb_details_consecutive_errors = 0
            report_progress("TMDb Details", f"Успешно [{detail_index}/{len(details_candidates)}]")
            candidate = prepare_candidate(details, country, source_query=query)
            if candidate.get("imdb_id"):
                stats["has_imdb_id"] += 1
            if use_imdb_sql:
                report_progress("IMDb dataset", f"Поиск [{detail_index}/{len(details_candidates)}]")
                candidate = enrich_from_imdb_sql(candidate, conn)
                if candidate.get("imdb_found_in_sql"):
                    stats["found_in_imdb_sql"] += 1
                    report_progress("IMDb dataset", f"Успешно [{detail_index}/{len(details_candidates)}]")
                else:
                    report_progress("IMDb dataset", f"Нет кандидатов [{detail_index}/{len(details_candidates)}]")

            if use_kp_cache:
                candidate = enrich_from_kp_cache_only(candidate)
                if "kp_cache_hit" in candidate.get("signals", []):
                    stats["kp_cache_hit"] += 1
            else:
                candidate["kp_id"] = None
                candidate["kp_rating"] = None
                candidate["kp_votes"] = None
                candidate["kp_status"] = "not_requested"
                candidate["is_complete"] = False

            if candidate["country_score"] >= 0.70:
                stats["country_passed"] += 1
            elif candidate["country_score"] >= 0.40:
                stats["country_borderline"] += 1
                append_signal(candidate, "borderline_country_score")
            else:
                stats["country_rejected"] += 1
                continue

            passes, reason = passes_imdb_filters(candidate)
            if passes is False:
                stats["imdb_filter_rejected"] += 1
                if reason in {"adult", "title_type"}:
                    stats["adult_title_type_rejected"] += 1
                append_signal(candidate, f"rejected_{reason}")
                continue

            candidate["quality_score"] = compute_quality_score(candidate)
            candidate["hidden_gem_score"] = compute_hidden_gem_score(candidate)
            candidate["final_score"] = compute_final_score(candidate, mode)
            candidates.append(candidate)
    finally:
        if conn is not None:
            conn.close()

    _sort_candidates_by_scores(candidates)
    if use_kp_api:
        kp_api_candidates = candidates
        if enrichment_mode == "kp_top":
            kp_api_candidates = candidates[:kp_top_limit_value]
            stats["kp_api_skipped_not_top"] = max(0, len(candidates) - len(kp_api_candidates))

        kp_api_candidate_ids = {id(candidate) for candidate in kp_api_candidates}
        for candidate in candidates:
            if id(candidate) not in kp_api_candidate_ids:
                continue

            if kp_api_skip_network:
                candidate = enrich_from_kp_api_if_needed(
                    candidate, country, stats, skip_network=True, kp_debug_session=kp_debug_session,
                )
            elif candidate.get("kp_status") == "cache_hit":
                candidate = enrich_from_kp_api_if_needed(
                    candidate, country, stats, kp_debug_session=kp_debug_session,
                )
            elif (
                enrichment_mode == "full"
                and kp_api_limit is not None
                and stats["kp_api_requested"] >= int(kp_api_limit)
            ):
                candidate = mark_kp_pending_limit(candidate)
                report_progress("KP API", "Лимит, добрать позже")
            else:
                kp_errors_before = stats["kp_api_errors"]
                kp_requested_before = stats["kp_api_requested"]
                candidate = enrich_from_kp_api_if_needed(
                    candidate, country, stats, kp_debug_session=kp_debug_session,
                )
                if stats["kp_api_errors"] > kp_errors_before:
                    kp_api_consecutive_errors += 1
                    if kp_api_consecutive_errors >= NETWORK_ERROR_SKIP_THRESHOLD:
                        kp_api_skip_network = True
                elif stats["kp_api_requested"] > kp_requested_before:
                    kp_api_consecutive_errors = 0

            candidate["quality_score"] = compute_quality_score(candidate)
            candidate["hidden_gem_score"] = compute_hidden_gem_score(candidate)
            candidate["final_score"] = compute_final_score(candidate, mode)

        _sort_candidates_by_scores(candidates)

    normalized_candidates = [
        normalize_tmdb_candidate_for_common_pool(candidate, criteria_name=criteria_name)
        for candidate in candidates
    ]
    stats["final_candidates"] = len(candidates)
    stats["kp_pending_limit"] = sum(
        1 for candidate in normalized_candidates if candidate.get("kp_status") == "pending_limit"
    )
    stats["kp_incomplete_candidates"] = sum(
        1 for candidate in normalized_candidates if candidate.get("is_complete") is not True
    )
    stats["complete_candidates"] = sum(1 for candidate in normalized_candidates if candidate.get("is_complete") is True)

    result_payload = {
        "criteria_name": criteria_name,
        "country": country,
        "mode": mode,
        "source": "tmdb_discover_imdb_sql",
        "query": query,
        "settings": {
            "criteria_name": criteria_name,
            "country": country,
            "mode": mode,
            "pages": int(pages),
            "details_limit": int(details_limit),
            "year_min": year_min,
            "year_max": year_max,
            "min_tmdb_score": min_tmdb_score,
            "min_tmdb_votes": min_tmdb_votes,
            "with_genres": normalize_optional_tmdb_genre_filter(with_genres),
            "without_genres": normalize_optional_tmdb_genre_filter(without_genres),
            "skip_existing_pool": bool(skip_existing_pool),
            "enrichment_mode": enrichment_mode,
            "kp_top_limit": kp_top_limit_value if enrichment_mode == "kp_top" else None,
        },
        "stats": stats,
        "candidates": normalized_candidates,
    }
    if kp_debug_session is not None:
        result_payload["kp_debug"] = kp_debug_session.to_report()
    return result_payload


from candidates.sources.tmdb.discover_dedupe import *  # noqa: E402, F403
from candidates.sources.tmdb.discover_query import *  # noqa: E402, F403
from candidates.sources.tmdb.output import *  # noqa: E402, F403
from candidates.sources.tmdb.transformer import *  # noqa: E402, F403
