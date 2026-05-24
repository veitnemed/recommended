import constant

def is_valid_features(features: dict) -> bool:
    """Проверяет, что features содержит ровно ожидаемые признаки модели."""
    return set(constant.FEATURES) == set(features.keys())


def is_valid_features_meta(features_const: dict) -> bool:
    """Проверяет, что вычисленные признаки содержат ожидаемые ключи."""
    return set(constant.FEATURES_CONST) == set(features_const.keys())


def is_valid_grade(nums: list, max_value=10) -> bool:
    """Проверяет, что число или список чисел находится в диапазоне от 0 до max_value."""
    if isinstance(nums, list):
        for num in nums:
            if isinstance(num, (int, float)) is False:
                return False
            if num < 0 or num > max_value:
                return False
        return True

    if isinstance(nums, (int, float)):
        return 0 <= nums <= max_value
    return False


def is_correct_title(title):
    """Проверяет, что название не пустое и не содержит запрещенных символов."""
    title = title.strip()
    if title == '':
        return False
    return len(set(constant.BAD_CHARACTERS) & set(title)) == 0


def is_correct_score(score: str):
    """Проверяет, что значение можно привести к оценке от 0 до 10."""
    try:
        score_float = float(score)
        return 0 <= score_float <= 10
    except:
        return False


def is_correct_year(year: str) -> bool:
    """Проверяет, что год находится в допустимом диапазоне проекта."""
    try:
        year_int = int(year)
        return 2000 <= year_int <= constant.NOW_YEAR
    except:
        return False


def is_correct_main_menu_command(command: str):
    """Проверяет, что команда есть в списке команд главного меню."""
    return command in constant.COMMANDS


def is_correct_votes(votes: str) -> bool:
    """Проверяет, что количество голосов является неотрицательным целым числом."""
    try:
        votes_int = int(votes)
        return votes_int >= 0
    except:
        return False


def is_valid_raw_meta(raw: dict) -> bool:
    """Проверяет структуру и значения сырых данных фильма."""
    if set(raw.keys()) != set(constant.RAW_META_FIELDS):
        return False

    if is_correct_score(raw["kp_score"]) is False:
        return False

    if is_correct_votes(raw["imdb_votes"]) is False:
        return False

    if is_correct_year(raw["year"]) is False:
        return False

    if is_correct_votes(raw["kp_votes"]) is False:
        return False

    if is_correct_score(raw["imdb_score"]) is False:
        return False

    return True

def is_correct_bool(bool_score: int):
    try:
        bool_score_int = int(bool_score)
        return 0 <= bool_score_int <= 1
    except:
        return False

def is_origin_title(title: str) -> bool:
    import storage
    dataset = storage.load_dataset()
    title = title.strip()
    for k in dataset.keys():
        if k.lower() == title.lower():
            return False
    return True
    

VALIDATORS = {
    "score": is_correct_score,
    "year":  is_correct_year,
    "votes": is_correct_votes,
    "title": is_correct_title,
    "origin_title": is_origin_title
    }
