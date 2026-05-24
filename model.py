import constant


def iter_movies(data):
    if isinstance(data, dict):
        return list(data.values())
    return data


def get_movie_title(movie: dict) -> str:
    """Возвращает название фильма или сериала из записи датасета."""
    return movie["main_info"]["title"]


def get_user_score(movie: dict) -> float:
    """Возвращает пользовательскую оценку из записи датасета."""
    return movie["main_info"]["user_score"]


def get_features(movie: dict) -> dict:
    """Собирает признаки модели из computed_scores и subjective_scores."""
    features = {}

    for feature in movie["computed_scores"]:
        features[feature] = movie["computed_scores"][feature]

    for feature in movie["subjective_scores"]:
        features[feature] = movie["subjective_scores"][feature]

    return features


def predict_score(features: dict, weights=constant.DEFAULT_WEIGHTS) -> float:
    """Считает прогноз оценки как взвешенную сумму признаков."""
    score = 0
    for key, value in weights.items():
        score += features[key] * value
    return score


def calc_error(movie: dict, weights=constant.DEFAULT_WEIGHTS) -> float:
    """Возвращает разницу между прогнозом модели и пользовательской оценкой."""
    user_score = get_user_score(movie)
    score = predict_score(get_features(movie), weights)
    return score - user_score


def mean_absolute_error(data: list, weights=constant.DEFAULT_WEIGHTS) -> float:
    """Считает среднюю абсолютную ошибку модели на датасете."""
    movies = iter_movies(data)
    length = len(movies)
    absolute_error = 0
    if length == 0:
        return 0
    for obj in movies:
        absolute_error += abs(calc_error(obj, weights)) / length
    return absolute_error


def mean_error(data: list, weights=constant.DEFAULT_WEIGHTS) -> float:
    """Считает среднее отклонение модели с учетом знака ошибки."""
    movies = iter_movies(data)
    length = len(movies)
    error = 0
    if length == 0:
        return 0
    for obj in movies:
        error += calc_error(obj, weights) / length
    return error


def fit_weights(data: list, start_weights=constant.DEFAULT_WEIGHTS, passes: int = 3) -> dict:
    """Подбирает веса признаков перебором с заданным шагом."""
    data = iter_movies(data)
    
    if len(data) == 0:
        return start_weights.copy()

    weights = start_weights.copy()

    for _ in range(passes):
        for feature in weights.keys():
            best_error = mean_absolute_error(data, weights)
            best_weight = weights[feature]

            for i in range(int(1 / constant.STEP) + 1):
                test_weight = i * constant.STEP
                weights[feature] = test_weight

                error = mean_absolute_error(data, weights)

                if error < best_error:
                    best_error = error
                    best_weight = test_weight

            weights[feature] = best_weight

    return weights


def one_to_one_error(data: list, top_n):
    """Проверяет модель методом leave-one-out и выводит самые большие ошибки."""
    data = iter_movies(data)

    if len(data) < 2:
        print('Недостаточно данных для leave-one-out проверки')
        return 0

    length_data = len(data)
    mean_error = 0
    result = []
    for idx in range(length_data):
        train_data = data.copy()
        test_movie = train_data.pop(idx)

        user_score = get_user_score(test_movie)
        new_weights = fit_weights(train_data)

        predict = predict_score(get_features(test_movie), new_weights)
        error = abs(user_score - predict)
        result.append((error, get_movie_title(test_movie), round(user_score, 1), round(predict, 1)))
        mean_error += error / length_data

    sorted_result = sorted(result, key=lambda x: x[0], reverse=True)

    counter = 0

    for error, title, user_score, predict in sorted_result:
        counter += 1
        print(f"\n{title} ({round(user_score, 2)})")
        print('Оценка модели:', round(predict, 2))
        print('Ошибка:', round(error, 2))
        if counter == top_n:
            break

    print('Средняя ошибка:', round(mean_error, 4))
    return mean_error


def selection_weights_without_feature(
        data: list,
        excluded_feature,
        default_weights: dict = constant.DEFAULT_WEIGHTS
):
    """Подбирает веса модели без одного исключенного признака."""
    data = iter_movies(data)

    if len(data) == 0:
        return default_weights.copy()

    weights_select = default_weights.copy()

    if excluded_feature in weights_select:
        weights_select.pop(excluded_feature)

    features = list(weights_select.keys())

    for feature in features:
        min_error = mean_absolute_error(data, weights_select)
        min_weight = weights_select[feature]

        for i in range(int(1 / constant.STEP) + 1):
            weight = i * constant.STEP
            weights_select[feature] = weight

            error = mean_absolute_error(data, weights_select)

            if error < min_error:
                min_error = error
                min_weight = weight

        weights_select[feature] = min_weight

    return weights_select
