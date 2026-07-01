"""Case-insensitive title/key lookup for watched dataset and meta."""


def normalize_title_key(title: str) -> str:
    """Normalize a title for case-insensitive comparison."""
    return str(title).strip().lower()


def find_case_insensitive_key(mapping: dict, title: str) -> str | None:
    """Return the actual dict key matching title (strip + casefold)."""
    expected = normalize_title_key(title)
    for current_key in mapping.keys():
        if normalize_title_key(current_key) == expected:
            return current_key
    return None


def find_dataset_title(data: dict, title: str) -> str | None:
    """Return the dataset key for a title, or None if not found."""
    return find_case_insensitive_key(data, title)


def duplicate_title_exists(data: dict, title: str) -> bool:
    """Return True if a case-insensitive duplicate title exists in dataset."""
    return find_dataset_title(data, title) is not None
