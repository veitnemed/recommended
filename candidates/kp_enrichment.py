"""Shared KP API match/fill helpers for TMDb build and common pool retry."""

from __future__ import annotations

from typing import Any, Callable

from apis import kp_api


KP_COUNTRY_BY_ISO2 = {
    "RU": "Россия",
    "KR": "Южная Корея",
    "US": "США",
    "GB": "Великобритания",
    "DE": "Германия",
}


def normalize_iso2_country(value: str | None) -> str:
    return str(value or "").strip().upper()


def kp_country_from_iso2(country: str) -> str:
    """Maps ISO-2 country code to KP API country label."""
    return KP_COUNTRY_BY_ISO2.get(normalize_iso2_country(country), "")


def safe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def unique_non_empty(values: list[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        if value in (None, ""):
            continue
        key = str(value).strip()
        if key == "" or key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def candidate_year(candidate: dict[str, Any]) -> int | None:
    return safe_int(candidate.get("year") or candidate.get("imdb_start_year"))


def candidate_kp_queries(candidate: dict[str, Any], *, include_alternative_title: bool = False) -> list[Any]:
    fields = ["title", "original_title"]
    if include_alternative_title:
        fields.append("alternative_title")
    return unique_non_empty([candidate.get(field_name) for field_name in fields])


def kp_api_description(movie: dict[str, Any]) -> str:
    return str(movie.get("description") or movie.get("shortDescription") or "").strip()


def kp_match_is_safe(candidate: dict[str, Any], movie: dict[str, Any]) -> tuple[bool, str | None]:
    if kp_api.is_series(movie) is False:
        return False, "not_series"

    candidate_titles = unique_non_empty([
        candidate.get("title"),
        candidate.get("original_title"),
    ])
    title_score = 0.0
    for title in candidate_titles:
        title_score = max(title_score, kp_api.title_match_score(str(title), movie))
    if title_score < 0.78:
        return False, "title_mismatch"

    expected_year = candidate_year(candidate)
    kp_year = safe_int(movie.get("year"))
    if expected_year is not None and kp_year is not None and abs(kp_year - expected_year) > 1:
        return False, "year_mismatch"

    return True, None


def fill_candidate_from_kp_api(candidate: dict[str, Any], movie: dict[str, Any]) -> None:
    kp_rating = kp_api.safe_nested(movie, "rating", "kp")
    kp_votes = kp_api.safe_nested(movie, "votes", "kp")
    if movie.get("id") not in (None, ""):
        candidate["kp_id"] = movie.get("id")
    if kp_rating not in (None, ""):
        candidate["kp_rating"] = kp_rating
    if kp_votes not in (None, ""):
        candidate["kp_votes"] = kp_votes

    description = kp_api_description(movie)
    if description and not str(candidate.get("overview") or "").strip():
        candidate["overview"] = description
    if movie.get("name"):
        candidate["kp_title"] = movie.get("name")


def lookup_kp_via_api(
    candidate: dict[str, Any],
    queries: list[Any],
    country: str,
    *,
    find_series_raw: Callable[..., dict[str, Any]] | None = None,
    continue_on_reject: bool = False,
) -> dict[str, Any]:
    """Looks up KP data for candidate queries and applies shared match-check."""
    find_series_raw = find_series_raw or kp_api.find_series_raw
    year = candidate_year(candidate)
    last_error = None
    last_reject = None

    if len(queries) == 0:
        return {
            "status": "no_query",
            "movie": None,
            "error": "empty_query",
            "reject_reason": None,
            "query": None,
            "attempts": 0,
        }

    attempts = 0
    for query in queries:
        attempts += 1
        result = find_series_raw(str(query), country, year=year)
        if result.get("ok") is False:
            error_code = result.get("error") or "unknown"
            if error_code in {"not_found", "country_not_found", "empty_title"}:
                last_error = error_code
                continue
            return {
                "status": "error",
                "movie": None,
                "error": error_code,
                "reject_reason": None,
                "query": str(query),
                "attempts": attempts,
            }

        movie = result.get("data") or {}
        is_safe, reason = kp_match_is_safe(candidate, movie)
        if is_safe is False:
            last_reject = reason
            last_error = f"rejected_{reason}"
            if continue_on_reject:
                continue
            return {
                "status": "rejected",
                "movie": None,
                "error": last_error,
                "reject_reason": reason,
                "query": str(query),
                "attempts": attempts,
            }

        return {
            "status": "found",
            "movie": movie,
            "error": None,
            "reject_reason": None,
            "query": str(query),
            "attempts": attempts,
        }

    return {
        "status": "not_found",
        "movie": None,
        "error": last_error or "not_found",
        "reject_reason": last_reject,
        "query": None,
        "attempts": attempts,
    }
