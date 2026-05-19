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

def selection_weights(data: list, default_weights = constant.DEFAULT_WEIGHTS):
    
    if len(data) == 0:
        return default_weights.copy()
    weights_select = default_weights.copy()
    for feature in constant.FEATURES:     
        min_error = mean_absolute_error(data, weights_select)
        min_weight = weights_select[feature]
        for i in range(int(1/constant.STEP)+1):
            k = i*constant.STEP
            weights_select[feature] = k
            error = mean_absolute_error(data,weights_select)
            if min_error > error:
                min_error = error
                min_weight = k
        weights_select[feature] = min_weight
    return weights_select  

print()