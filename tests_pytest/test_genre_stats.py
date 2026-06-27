from dataset.genre_stats import build_model_genre_catalog


def test_build_model_genre_catalog_uses_russian_labels() -> None:
    items = build_model_genre_catalog()

    assert len(items) >= 9
    labels = {item["feature"]: item["label_ru"] for item in items}
    assert labels["has_drama"] == "Драма"
    assert labels["has_crime"] == "Криминал"
    assert labels["has_romance"] == "Романтика"
