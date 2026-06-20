"""Canonical genre normalization for runtime candidate-pool filters."""

from __future__ import annotations


GENRE_ALIASES: dict[str, list[str]] = {
    "drama": ["drama", "драма"],
    "mystery": ["mystery", "детектив", "мистика"],
    "crime": ["crime", "криминал", "преступление", "преступления"],
    "comedy": ["comedy", "комедия"],
    "thriller": ["thriller", "триллер"],
    "action_adventure": [
        "action & adventure",
        "action and adventure",
        "боевик",
        "приключения",
        "боевик и приключения",
    ],
    "sci_fi_fantasy": [
        "sci-fi & fantasy",
        "sci fi fantasy",
        "sci-fi and fantasy",
        "фантастика",
        "фэнтези",
        "научная фантастика",
    ],
    "animation": ["animation", "анимация", "мультфильм", "мультфильмы"],
    "soap": ["soap", "мыльная опера"],
    "reality": ["reality", "реалити", "реалити-шоу"],
    "talk": ["talk", "ток-шоу", "ток шоу"],
    "news": ["news", "новости"],
}


def _normalize_key(value: str) -> str:
    text = str(value or "").strip().casefold()
    text = text.replace("ё", "е")
    text = text.replace("&", " and ")
    while "  " in text:
        text = text.replace("  ", " ")
    return text.strip()


_ALIAS_TO_CANONICAL: dict[str, str] = {}
for canonical, aliases in GENRE_ALIASES.items():
    _ALIAS_TO_CANONICAL[_normalize_key(canonical)] = canonical
    for alias in aliases:
        _ALIAS_TO_CANONICAL[_normalize_key(alias)] = canonical


def normalize_genre_name(value) -> str:
    """Returns canonical genre key for one genre label."""
    normalized = _normalize_key(str(value or ""))
    if normalized == "":
        return ""
    return _ALIAS_TO_CANONICAL.get(normalized, normalized)


def _iter_genre_values(values) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        parts = [item.strip() for item in values.split(",")]
        return [item for item in parts if item != ""]
    if isinstance(values, (list, tuple, set)):
        result = []
        for item in values:
            text = str(item or "").strip()
            if text != "":
                result.append(text)
        return result
    text = str(values).strip()
    return [text] if text != "" else []


def normalize_genre_list(values) -> list[str]:
    """Returns ordered unique canonical genre keys."""
    normalized = []
    seen = set()
    for raw_value in _iter_genre_values(values):
        canonical = normalize_genre_name(raw_value)
        if canonical == "" or canonical in seen:
            continue
        seen.add(canonical)
        normalized.append(canonical)
    return normalized


def _candidate_genre_keys(candidate_genres) -> set[str]:
    return set(normalize_genre_list(candidate_genres))


def genres_match_any(candidate_genres, required_genres) -> bool:
    """True when candidate has at least one required genre after normalization."""
    candidate_keys = _candidate_genre_keys(candidate_genres)
    required_keys = normalize_genre_list(required_genres)
    if len(required_keys) == 0:
        return True
    return len(candidate_keys & set(required_keys)) > 0


def genres_match_all(candidate_genres, required_genres) -> bool:
    """True when candidate has all required genres after normalization."""
    candidate_keys = _candidate_genre_keys(candidate_genres)
    required_keys = normalize_genre_list(required_genres)
    if len(required_keys) == 0:
        return True
    return set(required_keys).issubset(candidate_keys)


def genres_match_none(candidate_genres, excluded_genres) -> bool:
    """True when excluded genres do not intersect with candidate genres."""
    candidate_keys = _candidate_genre_keys(candidate_genres)
    excluded_keys = set(normalize_genre_list(excluded_genres))
    if len(excluded_keys) == 0:
        return True
    return len(candidate_keys & excluded_keys) == 0
