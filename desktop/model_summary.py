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


def format_metrics_status_kpi(*, is_stale: bool) -> str:
    return "Устарело" if is_stale else "Актуально"


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


def format_stale_retrain_message(stale_reason: str | None) -> str:
    if stale_reason == "user_score_changed":
        return "Оценки в dataset изменились — нужно повторное LOO обучение."
    return "Dataset изменился — нужно повторное LOO обучение."


def format_training_result_message(result: dict) -> str:
    if result.get("ok") is not True:
        return str(result.get("message") or "LOO обучение не выполнено.")

    save_result = result.get("save_result") or {}
    new_loo = save_result.get("new_loo_mae")
    best_alpha = result.get("best_alpha")
    if new_loo is None or best_alpha is None:
        return "LOO обучение завершено."

    return f"LOO обучение завершено. Новый LOO MAE: {float(new_loo):.2f}, alpha={best_alpha}"


def build_weights_summary(weights: dict, top_n: int = 10) -> dict:
    """Build read-only model weights blocks for the Model tab details panel."""
    bias = float(weights.get("bias", 0.0))
    weighted_features = []
    for name, value in weights.items():
        if name == "bias":
            continue
        try:
            weight = float(value)
        except (TypeError, ValueError):
            continue
        weighted_features.append((name, weight))

    positive_weights = sorted(
        ((name, weight) for name, weight in weighted_features if weight > 0),
        key=lambda item: item[1],
        reverse=True,
    )
    negative_weights = sorted(
        ((name, weight) for name, weight in weighted_features if weight < 0),
        key=lambda item: item[1],
    )

    positive_lines = [
        f"{index}. {name}: {weight:+.4f}"
        for index, (name, weight) in enumerate(positive_weights[:top_n], start=1)
    ]
    negative_lines = [
        f"{index}. {name}: {weight:+.4f}"
        for index, (name, weight) in enumerate(negative_weights[:top_n], start=1)
    ]

    text_lines = [f"bias: {bias:.4f}", ""]
    if positive_lines:
        text_lines.append("Топ положительных весов:")
        text_lines.extend(positive_lines)
    else:
        text_lines.append("Топ положительных весов: нет")
    text_lines.append("")
    if negative_lines:
        text_lines.append("Топ отрицательных весов:")
        text_lines.extend(negative_lines)
    else:
        text_lines.append("Топ отрицательных весов: нет")

    return {
        "bias": bias,
        "positive_lines": positive_lines,
        "negative_lines": negative_lines,
        "text_block": "\n".join(text_lines),
    }


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
        "metrics_status_kpi": format_metrics_status_kpi(is_stale=is_stale),
        "stale_reason": stale_reason,
        "stale_retrain_message": format_stale_retrain_message(stale_reason) if is_stale else "",
        "updated_at": metrics_status.get("updated_at"),
        "dataset_changed_at": metrics_status.get("dataset_changed_at"),
    }
