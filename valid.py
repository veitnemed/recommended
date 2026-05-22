import constant


def is_valid_features(features: dict) -> bool:
    '''Проверка корректности ключей словаря features'''
    return set(constant.FEATURES) == set(features.keys()) 

def is_valid_features_meta(features_const: dict) -> bool:
    '''Проверка корректности ключей словаря features'''
    return set(constant.FEATURES_CONST) == set(features_const.keys()) 

def is_valid_grade(nums: list, max_value = 10) -> bool:
    '''Проверка числа от 0 до max_value'''
    
    if isinstance(nums,list):
        for n in nums:
            if isinstance(n,(int,float)) is False:
                return False
            if n < 0 or n > max_value:
                return False
        return True
    
    if isinstance(nums,(int,float)):
        return 0 <= nums <= max_value
    return False

def is_correct_title(title):
    title = title.strip()
    if title == '':
        return False
    return len(set(constant.BAD_CHARACTERS) & set(title)) == 0

def is_correct_score(score: str):
    
    try:
        sc_flt = float(score)
        return 0 <= sc_flt <= 10
    except:
        return False

def is_correct_year(year: str) -> bool:
   
    try:
        year_int = int(year)
        return 2000 <= year_int <= constant.NOW_YEAR
    except:
        return False

def is_correct_main_menu_command(command: str):
    if command in constant.COMMANDS:
        return True
    return False

def is_correct_votes(votes: str) -> bool:
    try:
        votes_int = int(votes)
        return votes_int >= 0
    except:
        return False


def is_valid_raw_meta(raw: dict) -> bool:
    if set(raw.keys()) != set(constant.RAW_META_FIELDS):
        return False

    if is_correct_score(raw["kp_score"]) is False:
        return False

    if is_correct_votes(raw["imdb_votes"]) is False:
        return False

    if is_correct_year(raw["year"]) is False:
        return False

    if is_correct_score(raw["first_episode_score"]) is False:
        return False

    if is_correct_score(raw["last_episode_score"]) is False:
        return False

    return True

def is_correct_votes(votes: str) -> bool:
    try:
        votes_int = int(votes)
        return votes_int >= 0
    except:
        return False