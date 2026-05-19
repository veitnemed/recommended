import os

def clean_terminal():
    os.system('cls')

def show_main_menu(movies_counter: int):
    print('===== TERMINAL MOVIES LERN =====')
    if movies_counter == 0:
        print('Датасет пуст!\n')
    else:
        print(f'Количество записей: {movies_counter}\n')
    print('>> 1 Добавить запись')
    print('>> 2 Показать все записи')
    print('>> 3 Показать ошибку модели')
    print('>> 4 Подобрать веса')
    print('>> 0 Выход\n')


    


    