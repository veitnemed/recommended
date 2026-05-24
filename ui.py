import os


def clean_terminal():
    """Очищает окно консоли."""
    os.system('cls')


def show_main_menu(movies_counter: int, error: int):
    """Выводит главное меню приложения и количество записей в датасете."""
    print('======= TERMINAL MOVIES LEARN =======')
    if movies_counter == 0:
        print('Датасет пуст!\n')
    else:
        print(' '*7,f'Количество записей: {movies_counter}')
    print(' '*12,f"MAE: {error*10} %\n")
    print(' 1 >> Добавить запись')
    print(' 2 >> Импорт записей CSV')
    print(' 3 >> Показать все записи')
    print(' 4 >> Обучение')
    print(' 5 >> Показать веса')
    print(' 6 >> Расчет влияния каждого параметра')
    print(' 7 >> Прогноз для каждого объекта')
    print(' 8 >> Сделать прогноз')
    print(' 9 >> Очистить датасет\n')
    print(' 0 >> Выход\n')


def show_result_train(new_weights: dict, old_error: float, new_error: float, delta_time: float):
    """Выводит результат обучения модели: веса, ошибки и время подбора."""
    print('=' * 50)
    print('Новые веса:\n')
    for weight, value in new_weights.items():
        print(f'{weight}: {round(value, 4)}')

    print('\nОшибка до обучения:', round(old_error, 4))
    print('Ошибка после обучения:', round(new_error, 4))
    print(f'\nВремя подбора весов: {round(delta_time, 4)} сек.\n')
    print('=' * 50)


def show_result_importance():
    """Зарезервированная функция для вывода важности признаков."""
    pass
