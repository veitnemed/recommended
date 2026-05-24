import time

import constant
import model
import request
import storage
import ui
import valid


def show_all_movies():
    """Выводит список всех сохраненных фильмов и пользовательских оценок."""
    data = storage.load_dataset()
    if len(data) == 0:
        print('Датасет пуст!')
        return

    for idx, movie in enumerate(data.values()):
        main_info = movie["main_info"]
        print(f"{idx + 1}) {main_info['title']} | оценка: {main_info['user_score']}")


def get_predict(weights: dict) -> None:
    """Запрашивает признаки вручную и выводит прогноз модели для одного фильма."""
    title = request.loop_input(
        text='Введите название: ',
        funcs_list=[valid.is_correct_title]
    )

    features = {}
    for feature in constant.FEATURES:
        answer = request.loop_input(
            text=f'{feature} >> ',
            funcs_list=[valid.is_correct_score]
        )
        features[feature] = float(answer)

    score = model.predict_score(features, weights)
    print(f'Оценка модели для {title}: {score}')


def request_object() -> None:
    """Запрашивает данные фильма из консоли и сохраняет его в датасет."""
    ui.clean_terminal()

    movie_request = request.request_all_scores()
    result = storage.add_movie(movie_request)

    if result:
        print('Новая запись добавлена!')
    else:
        print('Ошибка! Новая запись не добавлена')


def train_model(data, weights):
    """Подбирает веса модели на текущем датасете и сохраняет результат."""
    start_time = time.perf_counter()

    old_error = model.mean_absolute_error(data, weights)
    new_weights = model.fit_weights(data, weights)
    new_error = model.mean_absolute_error(data, new_weights)

    storage.save_weights(new_weights)
    end_time = time.perf_counter()
    delta_time = end_time - start_time

    ui.show_result_train(new_weights, old_error, new_error, delta_time)


def show_mean_error(data, weights):
    """Выводит среднюю абсолютную ошибку модели для переданных данных."""
    ui.clean_terminal()
    abs_error = model.mean_absolute_error(data, weights)
    error = model.mean_error(data, weights)
    print(f'\nСредняя ошибка модели: {round(abs_error, 2)}')
    print(f'\nСреднее линейное отклонение: {round(error, 2)}')

def show_weights_model(weights):
    """Выводит текущие веса признаков модели."""
    ui.clean_terminal()
    print('Веса модели:\n')
    for weight, value in weights.items():
        print(f'{weight}: {round(value, 2)}')


def show_feature_importance():
    """Показывает ошибку модели при исключении каждого признака по очереди."""
    ui.clean_terminal()
    data = storage.load_dataset()
    for feature in constant.FEATURES:
        weights_without_feature = model.selection_weights_without_feature(
            data,
            excluded_feature=feature
        )
        error_without_feature = model.mean_absolute_error(data, weights_without_feature)

        print(f"\nВеса без {feature}:")
        for weight, value in weights_without_feature.items():
            print(f"{weight}: {round(value, 2)}")
        print(f"Ошибка без {feature}: {round(error_without_feature, 5)}")


def main_loop():
    """Запускает главный цикл консольного меню приложения."""
    
    storage.init_meta()
    storage.init_dataset()
    storage.init_weights()
    storage.init_txt()
    storage.init_csv()
    storage.create_backup()

    while True:
        ui.clean_terminal()
        data = storage.load_dataset()
        weights = storage.load_weights()
        movies_counter = len(data)
        abs_error = model.mean_absolute_error(data, weights)
        ui.show_main_menu(movies_counter,round(abs_error,2))

        command = request.loop_input(text=">> ", funcs_list=[valid.is_correct_main_menu_command])
        if command == '0':
            break
        elif command == '1':
            request_object()
        elif command == "2":
            storage.input_csv()
        elif command == '3':
            show_all_movies()
        elif command == '4':
            train_model(data, weights)
        elif command == '5':
            show_weights_model(weights)
        elif command == "6":
            show_feature_importance()
        elif command == "7":
            length = len(storage.load_dataset())
            model.one_to_one_error(data, min(10, length))
        elif command == "8":
            get_predict(weights)
        elif command == "9":
            storage.clean_dataset()

        input('Enter, чтобы продолжить >>')


if __name__ == "__main__":
    main_loop()
