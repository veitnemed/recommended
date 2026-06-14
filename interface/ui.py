"""Печатает экраны, заголовки и пункты терминального меню."""

import os


MENU_WIDTH = 38


def clean_terminal():
    """Очищает терминал."""
    os.system('cls')


def press_enter():
    """Ждет нажатия Enter."""
    input('Enter, чтобы продолжить >>')


def show_menu_title(title: str):
    """Печатает центрированный заголовок подменю."""
    print(f'\n{title.center(MENU_WIDTH)}\n')


def show_header(movies_counter: int, error: int):
    """Печатает общий заголовок приложения."""
    print('======= TERMINAL MOVIES LEARN =======')
    if movies_counter == 0:
        print('Датасет пуст!\n')
    else:
        print(' ' * 7, f'Количество записей: {movies_counter}')
    print(' ' * 12, f"MAE: {round(error * 10, 2)} %\n")


def show_global_menu(movies_counter: int, error: int, kp_error: int):
    """Печатает главное меню."""
    show_header(movies_counter, error)
    print(' ' * 9, f"KP_MAE: {round(kp_error * 10, 2)} %\n")
    print(' 1 >> Данные')
    print(' 2 >> Обучение')
    print(' 3 >> Модель')
    print(' 4 >> Дополнительно')
    print(' 5 >> Пулл кандидатов')
    print(' 6 >> Выгрузить отчёт')
    print(' 0 >> Выход\n')


def show_data_menu(movies_counter: int, error: int):
    """Печатает меню данных."""
    show_header(movies_counter, error)
    show_menu_title('ДАННЫЕ')
    print(' 1 >> Открыть Excel')
    print(' 2 >> Загрузить Excel')
    print(' 3 >> Добавить запись')
    print(' 4 >> Показать мои оценки')
    print(' 5 >> Данные о датасете')
    print(' 6 >> Прочитать оценки TST')
    print(' 7 >> Бэкап')
    print(' 8 >> Переименовать запись')
    print(' 0 >> Главное меню\n')


def show_candidate_pool_menu(movies_counter: int, error: int, candidates_count: int):
    """Печатает меню работы с общим пулом кандидатов."""
    show_header(movies_counter, error)
    show_menu_title('ПУЛЛ КАНДИДАТОВ')
    print(f'Всего кандидатов: {candidates_count}\n')
    print(' 1 >> Собрать пулл кандидатов')
    print(' 2 >> Посмотреть пуллы кандидатов')
    print(' 3 >> Собрать топ из общего пула')
    print(' 4 >> Удалить пулл')
    print(' 5 >> Отметить просмотренные из пулла')
    print(' 6 >> Показать подозрительные дубли')
    print(' 0 >> Главное меню\n')


def show_train_menu(movies_counter: int, error: int, step: float, plateau_score: int):
    """Печатает меню обучения."""
    show_header(movies_counter, error)
    show_menu_title('ОБУЧЕНИЕ')
    print(f'Шаг: {step} | Плато: {plateau_score} попыток без улучшения\n')
    print(' 1 >> Быстрое обучение')
    print(' 2 >> Случайная оптимизация')
    print(' 3 >> Многошаговый координатный поиск')
    print(' 4 >> Гибридная оптимизация')
    print(' 5 >> Линейная регрессия')
    print(' 6 >> Параметры обучения\n')
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
    print(' 0 >> Назад\n')


def show_extra_menu(movies_counter: int, error: int):
    """Печатает дополнительное меню."""
    show_header(movies_counter, error)
    show_menu_title('ДОПОЛНИТЕЛЬНО')
    print(' 1 >> Просмотр API признаков')
    print(' 2 >> Показать все жанры датасета')
    print(' 3 >> Показать влияние голосов')
    print(' 4 >> Пересчитать raw оценки')
    print(' 5 >> Тест Kino-Teatr скрапера')
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
