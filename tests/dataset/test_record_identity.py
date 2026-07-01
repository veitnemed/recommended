from dataset.models.identity import (
    duplicate_title_exists,
    find_case_insensitive_key,
    find_dataset_title,
    normalize_title_key,
)


def test_normalize_title_key() -> None:
    assert normalize_title_key("  Breaking Bad  ") == "breaking bad"


def test_find_dataset_title_case_insensitive() -> None:
    data = {"Breaking Bad": {}, "The Wire": {}}
    assert find_dataset_title(data, "breaking bad") == "Breaking Bad"
    assert find_dataset_title(data, "THE WIRE") == "The Wire"
    assert find_dataset_title(data, "missing") is None


def test_duplicate_title_exists() -> None:
    data = {"Breaking Bad": {}}
    assert duplicate_title_exists(data, "breaking bad") is True
    assert duplicate_title_exists(data, "The Wire") is False


def test_find_case_insensitive_key_for_meta() -> None:
    meta = {"Breaking Bad": {"description": "test"}}
    assert find_case_insensitive_key(meta, "BREAKING BAD") == "Breaking Bad"
    assert find_case_insensitive_key(meta, "other") is None
