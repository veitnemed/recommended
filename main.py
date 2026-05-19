import storage
import ui
import valid
import constant
import model

def show_all_movies():
    data = storage.load_dataset()
    if len(data) == 0:
        print('Датасет пуст!')
        return
    
    for idx, obj in enumerate(data):
        title = obj['title']
        user_score = obj['user_score']
        print(f"{idx+1}) {title} | оценка: {user_score}")


def loop_input(text: str, funcs_list: list):
    while True:
        w = input(text)

        for f in funcs_list:
            if f(w) is False:
                print('Некорректный ввод')
                break
        else:
            return w
        
def ask_object():   
    title = loop_input(
        text='Введите название: ',
        funcs_list=[valid.is_correct_title, storage.is_origin_title]
    )

    user_score = loop_input(
        text='Оценка по общему впечатлению: ',
        funcs_list=[valid.is_correct_score]
    )

    new_dict = {}

    for feature in constant.FEATURES:   
        answer = loop_input(
            text=f'{feature} >> ',
            funcs_list=[valid.is_correct_score]
        )
        new_dict[feature] = float(answer)

    result = storage.add_movies(
        title=title,
        user_score=user_score,
        features=new_dict
    )

    if result:
        print('Новая запись добавлена!')
    else:
        print('Ошибка! Новая запись не добавлена')


    
def main_loop():
    
    storage.init_dataset()
    while True:
        ui.clean_terminal()
        data = storage.load_dataset()
        movies_counter = len(data)
        ui.show_main_menu(movies_counter)
        
        command = loop_input(text=">> ", funcs_list=[valid.is_correct_main_menu_command])
        if command == '0':
            break
        elif command == '1':
            ask_object()
        elif command == '2':
           show_all_movies()
        elif command == '3':
            error = model.mean_absolute_error(data)
            print(f'Средняя ошибка модели: {error}')
        elif command == '4':
            old_error = model.mean_absolute_error(data)
            new_w = model.selection_weights(data)
            new_error = model.mean_absolute_error(data, new_w)
            
            print('Новые веса: ',*new_w)
            print('Ошибка до обучения: ',old_error)
            print('Ошибка после обучения: ', new_error)
        input('Enter, чтобы продолжить >>')
    
if __name__ == "__main__":
    main_loop()
    