import json

from common import format_score
from config import constant
from config import scheme


def _make_movie(title: str, user_score: float, year: int, raw_score: float = 8.0) -> dict:
    raw_scores = {
        "kp_score": raw_score,
        "kp_votes": 120000,
        "imdb_score": raw_score,
        "imdb_votes": 1200,
    }
    main_info = {
        "title": title,
        "user_score": user_score,
        "year": year,
    }
    return {
        "main_info": main_info,
        "raw_scores": raw_scores,
        "computed_scores": format_score.raw_to_struct(raw_scores, main_info),
        scheme.TAGS_VIBE: {feature: 0 for feature in constant.TAGS_VIBE},
        constant.GENRE_SECTION: {feature: 0 for feature in constant.GENRE},
    }


def test_format_metrics_status_label_fresh() -> None:
    from desktop.model_summary import format_metrics_status_label

    assert format_metrics_status_label(is_stale=False, stale_reason=None) == "Актуально"


def test_format_metrics_status_label_stale_score_change() -> None:
    from desktop.model_summary import format_metrics_status_label

    assert (
        format_metrics_status_label(is_stale=True, stale_reason="user_score_changed")
        == "Устарело после изменения оценки"
    )


def test_format_metrics_status_label_stale_dataset() -> None:
    from desktop.model_summary import format_metrics_status_label

    assert (
        format_metrics_status_label(is_stale=True, stale_reason="dataset_changed")
        == "Устарело после изменения dataset"
    )


def test_baseline_mae_or_none_without_scores() -> None:
    from desktop.model_summary import baseline_mae_or_none

    movie = _make_movie("Alpha", 8.0, 2020)
    movie["raw_scores"] = {}

    assert baseline_mae_or_none({"Alpha": movie}, "imdb_score") is None
    assert baseline_mae_or_none({"Alpha": movie}, "kp_score") is None


def test_baseline_mae_or_none_with_scores() -> None:
    from desktop.model_summary import baseline_mae_or_none

    data = {"Alpha": _make_movie("Alpha", 8.0, 2020, raw_score=7.0)}

    assert baseline_mae_or_none(data, "imdb_score") == 1.0
    assert baseline_mae_or_none(data, "kp_score") == 1.0


def test_format_stale_retrain_message() -> None:
    from desktop.model_summary import format_stale_retrain_message

    assert "Оценки" in format_stale_retrain_message("user_score_changed")
    assert "Dataset" in format_stale_retrain_message("dataset_changed")


def test_format_metrics_status_kpi() -> None:
    from desktop.model_summary import format_metrics_status_kpi

    assert format_metrics_status_kpi(is_stale=False) == "Актуально"
    assert format_metrics_status_kpi(is_stale=True) == "Устарело"


def test_build_weights_summary() -> None:
    from config import constant
    from desktop.model_summary import build_weights_summary

    weights = constant.DEFAULT_WEIGHTS.copy()
    weights["bias"] = 0.5
    summary = build_weights_summary(weights, top_n=3)

    assert "bias: 0.5000" in summary["text_block"]
    assert isinstance(summary["positive_lines"], list)
    assert isinstance(summary["negative_lines"], list)


def test_build_model_tab_summary_reads_saved_metrics(monkeypatch) -> None:
    import tempfile
    from pathlib import Path

    from desktop.model_summary import build_model_tab_summary

    with tempfile.TemporaryDirectory() as temp_root:
        root = Path(temp_root)
        metrics_path = root / "model_metrics.json"
        metrics_path.write_text(
            json.dumps(
                {
                    "loo_mae": 0.7366,
                    "is_stale": True,
                    "stale_reason": "user_score_changed",
                }
            ),
            encoding="utf-8",
        )
        dataset_path = root / "dataset.json"
        dataset_path.write_text(
            json.dumps({"Alpha": _make_movie("Alpha", 8.0, 2020)}),
            encoding="utf-8",
        )
        weights_path = root / "weights.json"
        weights_path.write_text(json.dumps(constant.DEFAULT_WEIGHTS), encoding="utf-8")

        monkeypatch.setattr(constant, "MODEL_METRICS_JSON", str(metrics_path))
        monkeypatch.setattr(constant, "FILE_NAME", str(dataset_path))
        monkeypatch.setattr(constant, "WEIGHTS_JSON", str(weights_path))

        summary = build_model_tab_summary()

    assert summary["loo_mae_display"] == "0.74"
    assert summary["imdb_baseline_display"] == "0.00"
    assert summary["kp_baseline_display"] == "0.00"
    assert summary["dataset_size"] == 1
    assert summary["metrics_status_display"] == "Устарело после изменения оценки"
    assert summary["metrics_status_kpi"] == "Устарело"
    assert summary["is_stale"] is True
    assert "повторное LOO обучение" in summary["stale_retrain_message"]
