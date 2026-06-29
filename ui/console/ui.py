"""Печатает экраны, заголовки и пункты терминального меню."""

import os
import sys


MENU_WIDTH = 38


def clean_terminal():
    """Очищает терминал."""
    if sys.stdout.isatty():
        os.system('cls')


def press_enter():
    """Ждет нажатия Enter."""
    input('Enter, чтобы продолжить >>')


def show_menu_title(title: str):
    """Печатает центрированный заголовок подменю."""
    print(f'\n{title.center(MENU_WIDTH)}\n')


def show_header(movies_counter: int, error: int):
    """Печатает общий заголовок приложения."""
    print('======= SERIES LIST =======')
    if movies_counter == 0:
        print('Список просмотренного пуст!\n')
    else:
        print(' ' * 4, f'Просмотрено записей: {movies_counter}\n')


def format_loo_mae_display(loo_mae=None, model_metrics_status: dict | None = None) -> str:
    if loo_mae is None and isinstance(model_metrics_status, dict):
        loo_mae = model_metrics_status.get("loo_mae")

    if loo_mae is None:
        return "Сохранённый LOO MAE: не рассчитан"

    suffix = ""
    if isinstance(model_metrics_status, dict) and model_metrics_status.get("is_stale") is True:
        suffix = " (устарело после изменения dataset)"
    return f"Сохранённый LOO MAE: {float(loo_mae):.4f}{suffix}"


def show_global_menu(movies_counter: int, error: int = 0, kp_error: int | None = None, loo_mae=None, model_metrics_status: dict | None = None):
    """Печатает главное меню."""
    show_header(movies_counter, error)
    print(' 1 >> Просмотренное')
    print(' 2 >> Поиск сериалов')
    print(' 3 >> Жанры')
    print(' 4 >> Дополнительно')
    print(' 0 >> Выход\n')


def show_data_menu(movies_counter: int, error: int):
    """Печатает меню данных."""
    show_header(movies_counter, error)
    show_menu_title('ПРОСМОТРЕННОЕ')
    print(' 1 >> Открыть Excel')
    print(' 2 >> Загрузить Excel')
    print(' 3 >> Добавить запись')
    print(' 4 >> Показать просмотренное')
    print(' 5 >> Данные о датасете')
    print(' 6 >> Бэкап')
    print(' 7 >> Переименовать запись')
    print(' 8 >> Удалить просмотренную запись')
    print(' 0 >> Главное меню\n')


def show_candidate_pool_menu(movies_counter: int, error: int, pool_stats_line: str):
    """Печатает меню работы с общим пулом кандидатов."""
    show_header(movies_counter, error)
    show_menu_title('ПОИСК СЕРИАЛОВ')
    print(f'{pool_stats_line}\n')
    print(' 1 >> Собрать новый пул кандидатов')
    print(' 2 >> Посмотреть сохранённые пулы')
    print(' 3 >> Найти сериалы в общем пуле')
    print(' 4 >> Отметить просмотренные из пула')
    print(' 5 >> Управление пулами')
    print(' 6 >> Диагностика и обслуживание')
    print(' 0 >> Главное меню\n')

def show_candidate_pool_management_menu():
    """Печатает подменю управления сохранёнными пулами."""
    show_menu_title('УПРАВЛЕНИЕ ПУЛАМИ')
    print(' 1 >> Удалить пул')
    print(' 2 >> Defaults фильтров поиска')
    print(' 3 >> Импортировать TMDb result в общий пул')
    print(' 4 >> Собрать пул через KP API (legacy)')
    print(' 0 >> Назад\n')


def show_candidate_pool_diagnostics_menu():
    """Печатает подменю диагностики и обслуживания пула."""
    show_menu_title('ДИАГНОСТИКА И ОБСЛУЖИВАНИЕ')
    print(' 1 >> Показать подозрительные дубли')
    print(' 2 >> Добрать KP для неполных кандидатов')
    print(' 3 >> Показать TMDb жанры по dataset')
    print(' 0 >> Назад\n')


def show_train_menu(movies_counter: int, error: int):
    """Печатает меню обучения."""
    show_header(movies_counter, error)
    show_menu_title('ОБУЧЕНИЕ')
    print(' 1 >> Линейная регрессия')
    print(' 2 >> Проверка устойчивости к шуму')
    print(' 3 >> LOO обучение')
    print(' 0 >> Главное меню\n')


def show_model_menu(movies_counter: int, error: int):
    """Печатает меню модели."""
    show_header(movies_counter, error)
    show_menu_title('МОДЕЛЬ')
    print(' 1 >> Признаки')
    print(' 2 >> Тесты эффективности')
    print(' 3 >> Сделать прогноз\n')
    print(' 0 >> Главное меню\n')


def show_feature_menu():
    """Печатает меню признаков."""
    show_menu_title('ПРИЗНАКИ')
    print(' 1 >> Вайб-тэги')
    print(' 2 >> Жанровая разметка')
    print(' 3 >> Показать веса модели')
    print(' 4 >> Сбросить веса модели')
    print(' 0 >> Назад\n')


def show_efficiency_menu(movies_counter: int, error: int):
    """Печатает меню тестов эффективности."""
    show_header(movies_counter, error)
    show_menu_title('ТЕСТЫ ЭФФЕКТИВНОСТИ')
    print(' 1 >> Оценить вклады')
    print(' 2 >> Рассчитать ошибку для топ N')
    print(' 3 >> Leave-one-out проверка')
    print(' 4 >> Проверка устойчивости к шуму')
    print(' 5 >> Показать влияние голосов')
    print(' 6 >> Пересчитать raw оценки')
    print(' 7 >> Диагностика признаков / feature ablation')
    print(' 8 >> Эффективность жанровой разметки')
    print(' 0 >> Назад\n')


def show_genres_menu():
    """Печатает меню жанров модели."""
    show_menu_title('ЖАНРЫ')
    print(' 1 >> Показать все жанры')
    print(' 0 >> Главное меню\n')


def show_extra_menu(movies_counter: int, error: int):
    """Печатает дополнительное меню."""
    show_header(movies_counter, error)
    show_menu_title('ДОПОЛНИТЕЛЬНО')
    print(' 1 >> Просмотр API признаков')
    print(' 2 >> Показать все жанры датасета')
    print(' 3 >> Поиск в SQL по названию')
    print(' 4 >> Обновить описания и poster-cache для просмотренных')
    print(' 5 >> Загрузить poster URL из TMDb (metadata)')
    print(' 6 >> Скачать poster images локально')
    print(' 7 >> Загрузить TMDb metadata для просмотренных')
    print(' 8 >> Диагностика unresolved TMDb metadata')
    print(' 9 >> Пинг API')
    print(' 0 >> Главное меню\n')


def show_tags_menu():
    """Печатает меню тегов."""
    show_menu_title('НАСТРОЙКА ТЕГОВ')
    print(' 1 >> Показать теги')
    print(' 2 >> Добавить тег')
    print(' 3 >> Удалить тег')
    print(' 4 >> Удалить все теги')
    print(' 0 >> Назад\n')


def show_result_train(new_weights: dict, old_error: float, new_error: float, delta_time: float):
    """Печатает результат обучения модели."""
    print('=' * 50)
    print('Новые веса:\n')
    for weight, value in new_weights.items():
        print(f'{weight}: {round(value, 4)}')

    print('\nОшибка до обучения:', round(old_error, 4))
    print('Ошибка после обучения:', round(new_error, 4))
    print(f'\nВремя подбора весов: {round(delta_time, 4)} сек.\n')
    print('=' * 50)
