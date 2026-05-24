import math

import constant


def clip_0_10(value: float) -> float:
    """Ограничивает число диапазоном от 0 до 10."""
    return max(0, min(10, value))

def popularity_kp(kp_votes: int, year: int) -> float:
    """Считает популярность по голосам kp с учетом года выхода."""
    
    age = max(1, constant.NOW_YEAR - year)
    adjusted_votes = kp_votes / (age ** 0.5)

    min_votes = 5000
    max_votes = 5000000

    if adjusted_votes <= min_votes:
        return 0

    score = math.log(adjusted_votes / min_votes) / math.log(max_votes / min_votes) * 15
    return clip_0_10(score)


def popularity_score(imdb_votes: int, year: int) -> float:
    """Считает популярность по голосам IMDb с учетом года выхода."""
    age = max(1, constant.NOW_YEAR - year)
    adjusted_votes = imdb_votes / (age ** 0.5)

    min_votes = 50
    max_votes = 5000

    if adjusted_votes <= min_votes:
        return 0

    score = math.log(adjusted_votes / min_votes) / math.log(max_votes / min_votes) * 15
    return clip_0_10(score)


def get_delta_score(first, last):
    """Считает изменение оценки между первой и последней серией."""
    return 5 + last - first


def raw_to_struct(raw: dict):
    """Преобразует сырые данные фильма в вычисленные признаки модели."""
    computed_scores = {}
    computed_scores["kp_score"] = raw["kp_score"]
    computed_scores["kp_popularity"] = popularity_kp(raw["kp_votes"], raw["year"])
    computed_scores["imdb_score"] = raw["imdb_score"]
    computed_scores["imdb_popularity"] = popularity_score(raw["imdb_votes"], raw["year"])
    return computed_scores


def build_features(raw_scores: dict, subjective_scores: dict) -> dict:
    """Объединяет вычисленные и субъективные признаки в общий словарь features."""
    computed_scores = raw_to_struct(raw_scores)
    features = {}

    for feature in computed_scores:
        features[feature] = computed_scores[feature]

    for feature in subjective_scores:
        features[feature] = subjective_scores[feature]

    return features
