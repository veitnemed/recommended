"""Интерактивное меню жанров dataset."""

from dataset import genre_stats


def show_dataset_genre_catalog() -> None:
    """Показывает все жанровые признаки dataset."""
    genre_stats.show_dataset_genre_catalog()
