"""Интерактивное меню жанров dataset."""

from dataset import service


def show_dataset_genre_catalog() -> None:
    """Показывает все жанровые признаки dataset."""
    service.show_dataset_genre_catalog()
