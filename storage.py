import json
import os
import valid
import constant



def is_json_exists(file_name):
    return os.path.exists(file_name)

def init_dataset():
    empty_list = []

    if is_json_exists(constant.FILE_NAME) is False:
        os.makedirs(constant.DATA_DIR, exist_ok=True)
        with open(constant.FILE_NAME, 'w', encoding='UTF-8') as file:
            json.dump(empty_list, file, ensure_ascii=False, indent=4)


def load_dataset() -> list:
    '''Возвращает список dict-объектов'''

    with open(constant.FILE_NAME, 'r', encoding='UTF-8') as file:
        return json.load(file)

def save_dataset(data: list):
    '''Перезаписываем новый список в json'''
    with open(constant.FILE_NAME, 'w', encoding='UTF-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def is_origin_title(new_title: str) -> bool:
    data = load_dataset()
    
    for d in data:
        if d['title'].strip().lower() == new_title.strip().lower():
            return False
    return True


def add_movies(title: str, user_score: str, features: dict) -> bool:
    ''' Добавляем ещё один объект в json'''
    
    title = title.strip()
    if valid.is_correct_title(title) is False:
        print('Ошибка добавления! Некорректное название')
        return False
    if is_origin_title(title) is False:
        print('Ошибка добавления! Такой объект добавлен')
        return False
    
    if valid.is_valid_features(features) is False:
        print('Ошибка добавления! Не хватает параметров')
        return False
    
    if valid.is_valid_grade(list(features.values())) is False:
        print('Ошибка добавления! Неверное значение параметров')
        return False
    
    if valid.is_correct_score(user_score) is False:
        print('Ошибка добавления! Некорректное значение user_score')
        return False
    
    user_score_float = float(user_score)
    
    data = load_dataset()
    new_obj = {}
    
    new_obj['title'] = title
    new_obj['user_score'] = user_score_float
    new_obj['liked'] = 1 if user_score_float >= constant.THRESHOLD else 0
    new_obj['features'] = features

    data.append(new_obj)
    save_dataset(data)
    return True




    
    