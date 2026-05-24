import csv
import json
import os
from datetime import datetime

import constant
import format_score as format
import valid


def is_json_exists(file_name):
    """Проверяет, существует ли файл по переданному пути."""
    return os.path.exists(file_name)


def init_dataset():
    """Создает пустой файл датасета, если он еще не существует."""
    empty_dict = {}

    if is_json_exists(constant.FILE_NAME) is False:
        os.makedirs(constant.DATA_DIR, exist_ok=True)
        with open(constant.FILE_NAME, 'w', encoding='UTF-8') as file:
            json.dump(empty_dict, file, ensure_ascii=False, indent=4)


def init_meta():
    """Создает пустой файл метаданных, если он еще не существует."""
    empty_dict = {}

    if is_json_exists(constant.META_JSON) is False:
        os.makedirs(constant.DIR_META, exist_ok=True)
        with open(constant.META_JSON, 'w', encoding='UTF-8') as file:
            json.dump(empty_dict, file, ensure_ascii=False, indent=4)


def load_meta() -> dict:
    """Загружает метаданные фильмов из JSON-файла."""
    with open(constant.META_JSON, 'r', encoding='UTF-8') as file:
        return json.load(file)


def save_meta(meta: dict):
    """Сохраняет метаданные фильмов в JSON-файл."""
    with open(constant.META_JSON, 'w', encoding='UTF-8') as file:
        json.dump(meta, file, ensure_ascii=False, indent=4)


def load_dataset() -> dict:
    """Загружает список фильмов из JSON-файла датасета."""
    with open(constant.FILE_NAME, 'r', encoding='UTF-8') as file:
        data = json.load(file)

    if isinstance(data, list):
        converted_data = {}
        for movie in data:
            title = movie["main_info"]["title"]
            converted_data[title] = movie
        return converted_data

    return data


def save_dataset(data: dict):
    """Сохраняет список фильмов в JSON-файл датасета."""
    with open(constant.FILE_NAME, 'w', encoding='UTF-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def is_origin_title(new_title: str) -> bool:
    """Проверяет, что фильма с таким названием еще нет в датасете."""
    data = load_dataset()

    for title in data.keys():
        if title.strip().lower() == new_title.strip().lower():
            return False
    return True


def normalize_raw_scores(raw: dict) -> dict:
    normalized_raw = {}

    for feature in constant.RAW_SCORES:
        if feature == "year" or feature.endswith("_votes"):
            normalized_raw[feature] = int(raw[feature])
        else:
            normalized_raw[feature] = float(raw[feature])

    return normalized_raw


def add_movies_to_meta(title: str, user_score: str, raw: dict) -> bool:
    """Добавляет постоянные raw-данные фильма в файл метаданных."""
    title = title.strip()
    meta = load_meta()

    if valid.is_correct_title(title) is False:
        print('Ошибка добавления в meta! Некорректное название')
        return False

    if valid.is_correct_score(user_score) is False:
        print('Ошибка добавления в meta! Некорректное значение user_score')
        return False

    if valid.is_valid_raw_meta(raw) is False:
        print('Ошибка добавления в meta! Некорректные raw-данные')
        return False

    normalized_raw = normalize_raw_scores(raw)

    meta_obj = {}
    meta_obj["user_score"] = float(user_score)
    meta_obj["raw"] = normalized_raw
    meta[title] = meta_obj

    save_meta(meta)
    return True


def add_movie(movie: dict) -> bool:
    """Добавляет фильм в датасет, используя постоянные raw-поля из meta."""
    main_info = movie["main_info"]
    input_raw_scores = movie["raw_scores"]
    subjective_scores = movie["subjective_scores"]

    title = str(main_info["title"]).strip()
    user_score = main_info["user_score"]

    if valid.is_correct_title(title) is False:
        print('Ошибка добавления! Некорректное название')
        return False

    if is_origin_title(title) is False:
        print('Ошибка добавления! Такой объект уже добавлен')
        return False

    if valid.is_correct_score(str(user_score)) is False:
        print('Ошибка добавления! Некорректное значение user_score')
        return False

    if set(subjective_scores.keys()) != set(constant.SUBJECTIVE_SCORES):
        print('Ошибка добавления! Некорректные subjective_scores')
        return False

    if valid.is_valid_grade(list(subjective_scores.values())) is False:
        print('Ошибка добавления! Неверное значение субъективных параметров')
        return False

    meta_obj = get_meta_obj(title)
    if meta_obj is None:
        if valid.is_valid_raw_meta(input_raw_scores) is False:
            print('Ошибка добавления! Некорректные raw_scores')
            return False

        raw_scores = normalize_raw_scores(input_raw_scores)

        if add_movies_to_meta(title, user_score, raw_scores) is False:
            return False
    else:
        raw_scores = meta_obj["raw"]

    computed_scores = format.raw_to_struct(raw_scores)
    features = {}
    for feature in computed_scores:
        features[feature] = computed_scores[feature]
    for feature in subjective_scores:
        features[feature] = subjective_scores[feature]

    if valid.is_valid_features(features) is False:
        print('Ошибка добавления! Не хватает параметров')
        print('Ожидались:', constant.FEATURES)
        print('Получены:', list(features.keys()))
        return False

    data = load_dataset()

    new_main_info = {}
    new_main_info["title"] = title
    new_main_info["user_score"] = float(user_score)

    new_movie = {}
    new_movie["main_info"] = new_main_info
    new_movie["raw_scores"] = raw_scores
    new_movie["computed_scores"] = computed_scores
    new_movie["subjective_scores"] = subjective_scores


    data[title] = new_movie
    save_dataset(data)
    return True


def add_movies(title: str, user_score: str, raw_scores: dict, subjective_scores: dict) -> bool:
    """Поддерживает старый формат вызова добавления фильма через add_movie."""
    main_info = {}
    main_info["title"] = title
    main_info["user_score"] = user_score

    movie = {}
    movie["main_info"] = main_info
    movie["raw_scores"] = raw_scores
    movie["subjective_scores"] = subjective_scores

    return add_movie(movie)


def clean_dataset():
    """Очищает датасет и оставляет в файле пустой список."""
    empty_dict = {}
    with open(constant.FILE_NAME, 'w', encoding='UTF-8') as file:
        json.dump(empty_dict, file, ensure_ascii=False, indent=4)


def init_weights():
    """Создает файл весов модели со значениями по умолчанию."""
    if is_json_exists(constant.WEIGHTS_JSON) is False:
        with open(constant.WEIGHTS_JSON, 'w', encoding='UTF-8') as file:
            json.dump(constant.DEFAULT_WEIGHTS, file, ensure_ascii=False, indent=4)


def load_weights() -> list:
    """Загружает веса модели из JSON-файла."""
    with open(constant.WEIGHTS_JSON, 'r', encoding='UTF-8') as file:
        return json.load(file)


def save_weights(data: dict):
    """Сохраняет веса модели в JSON-файл."""
    with open(constant.WEIGHTS_JSON, 'w', encoding='UTF-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def uppdate_weights(weights: dict):
    """Перезаписывает сохраненные веса модели."""
    save_weights(weights)


def init_txt():
    """Создает пустой txt-файл для старого импорта, если он еще не существует."""
    if is_json_exists(constant.TXT_INPUT) is False:
        with open(constant.TXT_INPUT, 'w', encoding='UTF-8') as file:
            return


def init_csv():
    """Создает CSV-файл для импорта с заголовками, если он еще не существует."""
    if is_json_exists(constant.CSV_INPUT) is False:
        os.makedirs(constant.DATA_DIR, exist_ok=True)
        with open(constant.CSV_INPUT, 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=constant.CSV_FIELDS)
            writer.writeheader()


def build_movie_from_row(row: dict, row_number: int) -> dict:
    """Преобразует строку CSV в структуру фильма для add_movie."""
    title = row["title"].strip()
    user_score = row["user_score"].strip()

    if valid.is_correct_title(title) is False:
        print(f'Строка {row_number}: некорректное название')
        return None

    if valid.is_correct_score(user_score) is False:
        print(f'Строка {row_number}: некорректное значение user_score')
        return None

    raw_scores = {}
    for feature in constant.RAW_SCORES:
        value = row[feature].strip()
        if feature == "year":
            if valid.is_correct_year(value) is False:
                print(f'Строка {row_number}: некорректный год')
                return None
            raw_scores[feature] = int(value)
        elif feature.endswith("_votes"):
            if valid.is_correct_votes(value) is False:
                print(f'Строка {row_number}: некорректное количество голосов')
                return None
            raw_scores[feature] = int(value)
        else:
            if valid.is_correct_score(value) is False:
                print(f'Строка {row_number}: некорректное значение {feature}')
                return None
            raw_scores[feature] = float(value)

    subjective_scores = {}
    for feature in constant.SUBJECTIVE_SCORES:
        value = row[feature].strip()
        if valid.is_correct_score(value) is False:
            print(f'Строка {row_number}: некорректное значение {feature}')
            return None
        subjective_scores[feature] = float(value)

    main_info = {}
    main_info["title"] = title
    main_info["user_score"] = float(user_score)

    movie = {}
    movie["main_info"] = main_info
    movie["raw_scores"] = raw_scores
    movie["subjective_scores"] = subjective_scores
    return movie


def input_csv() -> bool:
    """Импортирует фильмы из CSV-файла в датасет."""
    added_count = 0

    with open(constant.CSV_INPUT, 'r', encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            print('CSV-файл пуст!')
            return False

        if reader.fieldnames != constant.CSV_FIELDS:
            print('Ошибка CSV! Заголовки не совпадают с ожидаемыми')
            print('Ожидались:', constant.CSV_FIELDS)
            print('Получены:', reader.fieldnames)
            return False

        for row_number, row in enumerate(reader, start=2):
            if all(row[field].strip() == "" for field in constant.CSV_FIELDS):
                continue

            movie = build_movie_from_row(row, row_number)
            if movie is None:
                return False

            if add_movie(movie) is False:
                print(f'Ошибка импорта CSV! Строка {row_number}')
                return False

            added_count += 1

    if added_count == 0:
        print('Нет строк для импорта из CSV')
        return False

    print(f'Импорт CSV завершен. Добавлено записей: {added_count}')
    return True


def input_txt() -> bool:
    """Импортирует фильмы из txt-файла в датасет через старый формат с разделителем ;."""
    expected_len = len(constant.RAW_SCORES) + len(constant.SUBJECTIVE_SCORES) + 2
    added_count = 0
    with open(constant.TXT_INPUT, 'r', encoding='utf-8-sig') as file:
        data = file.readlines()

        if len(data) == 0:
            print('Текстовый файл пуст!')
            return False

    for idx, line in enumerate(data):
        if line.strip() == "":
            continue

        params = [param.strip() for param in line.strip().split(';')]

        if len(params) != expected_len:
            print(f'Ошибка парсинга из текстового файла! Строка {idx + 1}')
            return False

        if params[0].strip().lower() == 'title':
            continue

        row = {}
        for field, value in zip(constant.CSV_FIELDS, params):
            row[field] = value

        movie = build_movie_from_row(row, idx + 1)
        if movie is None:
            return False

        result = add_movie(movie)
        if result is False:
            print(f'Ошибка парсинга! Строка {idx + 1}')
            return False
        added_count += 1

    if added_count == 0:
        print('Нет строк для импорта')
        return False

    print(f'Импорт завершен. Добавлено записей: {added_count}')
    return True


def restart_txt():
    """Очищает txt-файл для импорта."""
    with open(constant.TXT_INPUT, 'w', encoding='UTF-8') as file:
        return


def restart_csv():
    """Очищает CSV-файл для импорта и оставляет только заголовки."""
    with open(constant.CSV_INPUT, 'w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=constant.CSV_FIELDS)
        writer.writeheader()


def create_backup():
    """Создает резервную копию текущего датасета."""
    dataset = load_dataset()
    date_name = datetime.now().strftime('%d-%m-%Y %H-%M-%S')
    backup_file = constant.BACKUP_DIR + date_name + '.json'
    if is_json_exists(backup_file) is False:
        os.makedirs(constant.BACKUP_DIR, exist_ok=True)

    with open(backup_file, 'w', encoding='UTF-8') as file:
        json.dump(dataset, file, ensure_ascii=False, indent=4)


def title_in_meta(title: str) -> bool:
    """Проверяет, есть ли фильм с таким названием в метаданных."""
    title = title.strip()
    meta = load_meta()

    return any(meta_title.lower() == title.lower() for meta_title in meta.keys())


def get_meta_obj(title: str) -> dict:
    """Возвращает объект метаданных фильма по названию."""
    title = title.strip()
    meta = load_meta()

    for meta_title, obj in meta.items():
        if meta_title.lower() == title.lower():
            return obj
    return None
