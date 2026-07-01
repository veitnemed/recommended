import importlib


def test_raw_genres_to_dataset_genres_maps_mystery_and_drama() -> None:
    from dataset.genres.mapping import raw_genres_to_dataset_genres

    result = raw_genres_to_dataset_genres(["Mystery", "драма"])
    genre = result["dataset_genre"]
    assert genre["has_detective"] == 1
    assert genre["has_drama"] == 1
    assert result["status"] in {"ok", "partial"}


def test_candidate_genre_keys_to_dataset_genres() -> None:
    from dataset.genres.mapping import candidate_genre_keys_to_dataset_genres

    result = candidate_genre_keys_to_dataset_genres(["crime", "drama"])
    genre = result["dataset_genre"]
    assert genre["has_crime"] == 1
    assert genre["has_drama"] == 1
    assert result["status"] == "ok"


def test_title_resolve_does_not_import_candidates_to_dataset() -> None:
    title_resolve = importlib.import_module("dataset.title_resolve")
    source = importlib.import_module(title_resolve.__name__).__file__
    assert source is not None
    with open(source, encoding="utf-8") as handle:
        text = handle.read()
    assert "candidates.to_dataset" not in text
    assert "candidates import genre_schema" not in text


def test_candidates_to_dataset_is_wrapper() -> None:
    from candidates import to_dataset

    assert to_dataset.raw_genres_to_dataset_genres is not None
    from dataset.genres import mapping

    assert to_dataset.raw_genres_to_dataset_genres is mapping.raw_genres_to_dataset_genres
