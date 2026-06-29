from app.core.explain import explain_candidate
from app.core.filters import candidate_matches, filter_candidates
from app.core.ranking import calculate_quality_score, rank_candidates
from candidates.keys import title_identity_key


def _candidate(**overrides):
    base = {
        "title": "Метод",
        "year": 2015,
        "countries": ["Россия"],
        "genres": ["драма", "детектив"],
        "kp_score": 8.1,
        "kp_votes": 12000,
        "imdb_score": 7.3,
        "imdb_votes": 2500,
        "is_complete": True,
    }
    base.update(overrides)
    return base


def test_candidate_matches_search_criteria() -> None:
    criteria = {
        "country": "Россия",
        "year_min": 2010,
        "year_max": 2020,
        "include_genres": ["Драма"],
        "exclude_genres": ["Комедия"],
        "min_kp_score": 7.0,
        "min_kp_votes": 1000,
        "min_imdb_score": 7.0,
        "min_imdb_votes": 1000,
        "only_complete": True,
    }

    assert candidate_matches(_candidate(), criteria) is True
    assert candidate_matches(_candidate(genres=["комедия"]), criteria) is False
    assert candidate_matches(_candidate(kp_score=6.9), criteria) is False


def test_candidate_matches_skips_watched_and_hidden() -> None:
    candidate = _candidate()
    identity = title_identity_key(candidate)

    assert candidate_matches(candidate, {"watched_identities": {identity}}) is False
    assert candidate_matches(candidate, {"hidden_identities": {identity}}) is False
    assert candidate_matches(candidate, {"watched_identities": {identity}, "only_unwatched": False}) is True
    assert filter_candidates([candidate], {"hidden_identities": set()})[0]["title"] == "Метод"


def test_quality_score_prefers_reliable_kp_and_votes() -> None:
    reliable = _candidate(title="Надёжный", kp_score=8.0, kp_votes=20000, imdb_score=7.0, imdb_votes=200)
    noisy_imdb = _candidate(title="Шумный", kp_score=7.0, kp_votes=500, imdb_score=9.8, imdb_votes=50)

    assert calculate_quality_score(reliable) > calculate_quality_score(noisy_imdb)
    assert rank_candidates([noisy_imdb, reliable])[0]["title"] == "Надёжный"


def test_explain_candidate_returns_search_reasons() -> None:
    reasons = explain_candidate(
        _candidate(),
        {
            "country": "Россия",
            "year_min": 2010,
            "include_genres": ["Драма"],
            "only_unwatched": True,
            "hide_hidden": True,
            "only_complete": True,
        },
    )

    text = "\n".join(reasons)
    assert "Оценка качества" in text
    assert "Высокий KP" in text
    assert "IMDb учтён" in text
    assert "Подходит по жанрам" in text
    assert "Не просмотрен" in text
    assert "Не скрыт" in text
