"""Интерактивное меню жанров модели."""

from dataset import genre_stats


def show_model_genres() -> None:
    """Показывает все жанровые признаки модели."""
    genre_stats.show_model_genres()
