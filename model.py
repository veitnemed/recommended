import constant

def predict_score(features: dict, weights = constant.DEFAULT_WEIGHTS) -> float:
    score = 0
    for k,v in weights.items():
        score += features[k]*v
    return score

def calc_error(movie: dict, weights = constant.DEFAULT_WEIGHTS) -> float:
    user_score = movie['user_score']
    score = predict_score(movie['features'],weights)
    return score - user_score

def mean_absolute_error(data: list, weights = constant.DEFAULT_WEIGHTS) -> float:
    l = len(data)
    absolute_error = 0
    if l == 0:
        return 0
    for obj in data:
       absolute_error += abs(calc_error(obj,weights))/l
    return absolute_error


def fit_weights(data: list, start_weights=constant.DEFAULT_WEIGHTS, passes: int = 3) -> dict:
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
    
    if len(data) < 2:
        print('Недостаточно данных для leave-one-out проверки')
        return 0

    length_data = len(data)
    mean_error = 0
    res = []
    for idx in range(length_data):
        train_data = data.copy()
        test_movie = train_data.pop(idx)

        user_score = test_movie['user_score']
        new_weights = fit_weights(train_data)

        predict = predict_score(test_movie["features"], new_weights)
        error = abs(user_score - predict)
        res.append((error, test_movie['title'], round(user_score, 1),round(predict, 1)))
        mean_error += error / length_data
        
    sorted_res = sorted(res, key=lambda x: x[0], reverse=True)
    
    k = 0
    
    for er, ti, us, pr in sorted_res:
        k+=1
        print(f"\n{ti} ({round(us,2)})")
        print('Оценка модели:', round(pr,2))
        print('Ошибка:', round(er,2))
        if k == top_n:
            break
        
    print('Средняя ошибка:', round(mean_error, 4))
    return mean_error

def selection_weights_without_feature(
        data: list,
        excluded_feature,
        default_weights: dict = constant.DEFAULT_WEIGHTS
):
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
            k = i * constant.STEP
            weights_select[feature] = k

            error = mean_absolute_error(data, weights_select)

            if error < min_error:
                min_error = error
                min_weight = k

        weights_select[feature] = min_weight

    return weights_select

