import storage
import ui
import valid
import constant
import model
import time
import math

def show_all_movies():
    '''Показать все сериалы и оценку user_score'''

    data = storage.load_dataset()
    if len(data) == 0:
        print('Датасет пуст!')
        return
    
    for idx, object in enumerate(data):
        title = object['title']
        user_score = object['user_score']
        print(f"{idx+1}) {title} | оценка: {user_score}")

def loop_input(text: str, funcs_list: list) -> str:
    '''Цикл ввода параметров и проверка валидации'''

    while True:
        ans = input(text)

        for f in funcs_list:
            if f(ans) is False:
                print('Некорректный ввод')
                break
        else:
            return ans
   
def get_predict(weights: dict) -> None:
    
    title = loop_input(text='Введите название: ', funcs_list=[valid.is_correct_title])
    
    features = {}
    for feature in constant.FEATURES:   
        answer = loop_input(
            text=f'{feature} >> ',
            funcs_list=[valid.is_correct_score]
        )
        features[feature] = float(answer)
    score = model.predict_score(features, weights)
    
    print(f'Оценка модели для {title}: {score}')

def popularity_score(imdb_votes: int, year: int) -> float:
    age = max(1, constant.NOW_YEAR - year)

    adjusted_votes = imdb_votes / (age ** 0.5)

    min_votes = 150
    max_votes = 7000

    if adjusted_votes <= min_votes:
        return 0

    score = math.log(adjusted_votes / min_votes) / math.log(max_votes / min_votes) * 10

    return max(0, min(10, score))

def ask_raw_meta() -> dict:
    raw = {}

    for field in constant.RAW_META_FIELDS:
        label = constant.RAW_META_RUSSIAN.get(field, field)

        if field == "imdb_votes":
            answer = loop_input(
                text=f'{label}: ',
                funcs_list=[valid.is_correct_votes]
            )
            raw[field] = int(answer)

        elif field == "year":
            answer = loop_input(
                text=f'{label}: ',
                funcs_list=[valid.is_correct_year]
            )
            raw[field] = int(answer)

        else:
            answer = loop_input(
                text=f'{label}: ',
                funcs_list=[valid.is_correct_score]
            )
            raw[field] = float(answer)

    return raw

def ask_llm_features() -> dict:
    features = {}

    for feature in constant.LLM_FEATURES:
        label = constant.FEATURES_RUSSIAN.get(feature, feature)

        answer = loop_input(
            text=f'{label}: ',
            funcs_list=[valid.is_correct_score]
        )
        features[feature] = float(answer)

    return features

def ask_object() -> None:
    '''Ввод сериала: raw-данные в meta + LLM-признаки в dataset'''

    title = loop_input(
        text='Введите название: ',
        funcs_list=[valid.is_correct_title, storage.is_origin_title]
    )

    user_score = loop_input(
        text='Оценка по общему впечатлению: ',
        funcs_list=[valid.is_correct_score]
    )

    print('\n--- Постоянные данные для meta ---')
    raw = ask_raw_meta()

    print('\n--- Параметры эксперимента ---')
    features = ask_llm_features()

    meta_result = storage.add_movies_to_meta(
        title=title,
        user_score=user_score,
        raw=raw
    )

    if meta_result is False:
        print('Ошибка! Запись в meta не добавлена')
        return

    result = storage.add_movies(
        title=title,
        user_score=user_score,
        features=features
    )

    if result:
        print('Новая запись добавлена!')
    else:
        print('Ошибка! Новая запись не добавлена')

def train_model(data, weights):
    start_time = time.perf_counter()

    old_error = model.mean_absolute_error(data, weights)
    new_weights = model.fit_weights(data, weights)
    new_error = model.mean_absolute_error(data, new_weights)

    storage.save_weights(new_weights)

    print('Новые веса:\n')
    for weight, value in new_weights.items():
        print(f'{weight}: {round(value, 4)}')

    print('\nОшибка до обучения:', round(old_error, 4))
    print('Ошибка после обучения:', round(new_error, 4))

    end_time = time.perf_counter()
    print(f'\nВремя подбора весов: {round(end_time - start_time, 4)} сек.')
    
def show_feature_importance(data: list):
    '''Вычилсяем ошибку без каждого параметра'''
    
    data = storage.load_dataset()
    for feature in constant.FEATURES:
        weights_without_holding = model.selection_weights_without_feature(data,excluded_feature=feature)
        error_without_holding = model.mean_absolute_error(data, weights_without_holding)
        print(f"\nВеса без {feature}:")
        for weight, value in weights_without_holding.items():
            print(f"{weight}: {round(value, 2)}")

            print(f"Ошибка без {feature}:", round(error_without_holding,4))

def main_loop():
    
    storage.init_meta()
    storage.init_dataset()
    storage.init_weights()
    storage.init_txt()
    storage.create_backup()
    
    while True:
        ui.clean_terminal()
        data = storage.load_dataset()
        weights = storage.load_weights()
        movies_counter = len(data)
        ui.show_main_menu(movies_counter)
        
        command = loop_input(text=">> ", funcs_list=[valid.is_correct_main_menu_command])
        if command == '0':
            break
        elif command == '1':
            ui.clean_terminal()
            ask_object()
        elif command == "2":
            ui.clean_terminal()
            storage.input_txt()
        elif command == '3':
            ui.clean_terminal()
            print()
            show_all_movies()
        elif command == '4':
            ui.clean_terminal()
            error = model.mean_absolute_error(data,weights)
            print(f'\nСредняя ошибка модели: {round(error,2)}')
        elif command == '5':
            ui.clean_terminal()
            train_model(data, weights)   
        elif command == '6':
            ui.clean_terminal()
            print('Веса модели: \n')
            for weight, value in weights.items():
                print(f'{weight}: {round(value,2)}')
        elif command == "7":
            ui.clean_terminal()
            show_feature_importance(data)
        elif command == "8":
            ui.clean_terminal()
            lenth = len(storage.load_dataset())
            model.one_to_one_error(data,min(10,lenth))
        elif command == "9":
            ui.clean_terminal()
            get_predict(weights)
        elif command == "10":
            storage.clean_dataset()
            print('Датасет отчищен')
        
        input('Enter, чтобы продолжить >>')


if __name__ == "__main__":
    main_loop()



