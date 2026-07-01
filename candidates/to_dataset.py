"""Maps candidate-pool canonical fields to dataset payload shapes."""

from __future__ import annotations

from dataset.genres.mapping import (
    GENRE_KEY_TO_DATASET_FEATURE,
    candidate_genre_keys_to_dataset_genres,
    raw_genres_to_dataset_genres,
)

__all__ = [
    "GENRE_KEY_TO_DATASET_FEATURE",
    "candidate_genre_keys_to_dataset_genres",
    "raw_genres_to_dataset_genres",
]
