"""Meta title lookup in data/watched/meta.json."""

from dataset.models.identity import find_case_insensitive_key
from storage.data import get_meta_obj, load_meta


def find_meta_title(meta: dict, title: str) -> str | None:
    """Return the meta dict key for a title, or None if not found."""
    return find_case_insensitive_key(meta, title)


def get_meta_for_title(title: str) -> dict | None:
    """Load meta.json and return the meta object for title, if any."""
    return get_meta_obj(title)
