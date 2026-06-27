"""Read-only summary assembly for the desktop Model tab."""

from __future__ import annotations

from model import model
from storage import data as storage_data


def format_mae_value(value: float | None) -> str:
    if value is None:
        return "нет данных"
    return f"{float(value):.2f}"


def format_loo_mae_kpi(loo_mae: float | None) -> str:
    if loo_mae is None:
        return "не рассчитан"
    return f"{float(loo_mae):.2f}"


def format_metrics_status_label(*, is_stale: bool, stale_reason: str | None) -> str:
    if not is_stale:
        return "Актуально"
    if stale_reason == "user_score_changed":
        return "Устарело после изменения оценки"
    return "Устарело после изменения dataset"


def count_scored_baseline(data: dict, score_field: str) -> int:
    scored = 0
    for movie in model.iter_movies(data):
        raw_scores = movie.get("raw_scores", {})
        try:
            float(raw_scores[score_field])
            float(model.get_user_score(movie))
        except (KeyError, TypeError, ValueError):
            continue
        scored += 1
    return scored


def baseline_mae_or_none(data: dict, score_field: str) -> float | None:
    if count_scored_baseline(data, score_field) == 0:
        return None
    if score_field == "kp_score":
        return model.kp_mean_absolute_error(data)
    if score_field == "imdb_score":
        return model.imdb_mean_absolute_error(data)
    return None


def build_model_tab_summary() -> dict:
    """Load saved metrics and lightweight baseline MAE for the Model tab."""
    metrics_status = storage_data.get_model_metrics_status()
    data = storage_data.load_dataset()
    dataset_size = len(data)

    loo_mae = metrics_status.get("loo_mae")
    is_stale = bool(metrics_status.get("is_stale"))
    stale_reason = metrics_status.get("stale_reason")

    imdb_mae = baseline_mae_or_none(data, "imdb_score")
    kp_mae = baseline_mae_or_none(data, "kp_score")

    return {
        "loo_mae": loo_mae,
        "loo_mae_display": format_loo_mae_kpi(loo_mae),
        "imdb_baseline": imdb_mae,
        "imdb_baseline_display": format_mae_value(imdb_mae),
        "kp_baseline": kp_mae,
        "kp_baseline_display": format_mae_value(kp_mae),
        "dataset_size": dataset_size,
        "dataset_size_display": str(dataset_size),
        "is_stale": is_stale,
        "metrics_status_display": format_metrics_status_label(
            is_stale=is_stale,
            stale_reason=stale_reason,
        ),
        "stale_reason": stale_reason,
        "updated_at": metrics_status.get("updated_at"),
        "dataset_changed_at": metrics_status.get("dataset_changed_at"),
    }
