"""Собирает текущее состояние приложения для экранов меню."""

from storage import data as storage_data


def get_menu_state():
    """Возвращает датасет и количество просмотренных записей без расчёта модели."""
    data = storage_data.load_dataset()
    movies_counter = len(data)
    return data, None, movies_counter, 0.0
