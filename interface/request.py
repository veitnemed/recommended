"""Запрашивает данные у пользователя и собирает объект фильма."""

from data_work import storage
from core import valid
from core import format_score
from config import genre_tags
from config import scheme
import copy
from config import constant
from integrations import api


def get_request_schema() -> dict:
    """Собирает актуальную схему ручного ввода."""
    sections = [
        scheme.MAIN_INFO,
        scheme.RAW_SCORES,
        scheme.TAGS_VIBE,
        scheme.GENRE,
    ]
    return {
        section_name: copy.deepcopy(scheme.get_schema(section_name))
        for section_name in sections
    }

def get_validators(tags_validators: list, max_value: int = 1) -> list:
    """Собирает валидаторы для поля схемы."""
    validators = []
    for tag in tags_validators:
        if tag == "tags_score":
            validators.append(lambda value, max_value=max_value: valid.is_tags_score(value, max_value))
        else:
            validators.append(valid.VALIDATORS[tag])
    return validators
    

def get_label(feature: str) -> str:
    """Возвращает подпись поля."""
    return constant.FIELD_LABELS.get(feature, feature)


def get_section_label(section_name: str) -> str:
    """Возвращает подпись секции."""
    return constant.SECTION_LABELS.get(section_name, section_name)


def loop_input(text, funcs_list):
    """Запрашивает ввод до прохождения проверок."""
    
    while True:
        value = input(text)
        for func in funcs_list:
            if func(value) is False:
                break
        else:
            break      
    return value


def loop_input_with_default(text: str, funcs_list: list, default_value=None):
    """Запрашивает ввод и подставляет значение по умолчанию при пустом ответе."""
    while True:
        value = input(text)
        if value.strip() == "" and default_value is not None:
            value = str(default_value)
        for func in funcs_list:
            if func(value) is False:
                break
        else:
            break
    return value


def short_text(value, limit: int = 50) -> str:
    """Обрезает текст для короткого предпросмотра."""
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def extract_api_genres(series: dict) -> list:
    """Извлекает список жанров из ответа API."""
    genres = []
    for item in series.get("genres", []) or []:
        if isinstance(item, dict) and item.get("name"):
            genres.append(str(item["name"]).strip())
        elif isinstance(item, str):
            genres.append(item.strip())
    return genres


def build_genre_defaults(genres: list) -> dict:
    """Собирает значения genre по списку жанров."""
    genre_tags.ensure_genre_fields(genres)
    constant.refresh_dynamic_fields()

    genre_defaults = {feature: 0 for feature in constant.GENRE}
    for genre_name in genres:
        feature = genre_tags.genre_to_feature_name(genre_name)
        if feature in genre_defaults:
            genre_defaults[feature] = 1
    return genre_defaults


def confirm_or_edit_api_genres(series: dict) -> list:
    """Показывает жанры из API и дает принять или изменить их."""
    genres = extract_api_genres(series)
    genres_line = ", ".join(genres) if len(genres) > 0 else "жанры не найдены"

    print(f"Краткое описание: {short_text(series.get('description'), 80)}")
    print(f"Жанры из API: {genres_line}")
    answer = input("Принять жанры из API? yes / edit >> ").strip().lower()
    if answer in ("yes", "y", "да"):
        return genres

    print("Введите жанры через запятую.")
    print("Можно оставить пусто, тогда жанровая разметка стартует пустой.")
    manual_line = input("Жанры >> ").strip()
    return extract_api_genres({"genres": manual_line.split(",")}) if manual_line != "" else []


def build_api_defaults(series: dict, genres: list | None = None) -> dict:
    """Собирает значения API для подстановки в ручную форму."""
    if genres is None:
        genres = extract_api_genres(series)

    genre_defaults = build_genre_defaults(genres)

    return {
        scheme.MAIN_INFO: {
            "title": series.get("title"),
            "user_score": None,
            "year": series.get("year"),
        },
        scheme.RAW_SCORES: {
            "kp_score": series.get("kp_score"),
            "kp_votes": series.get("kp_votes"),
            "imdb_score": series.get("imdb_score"),
            "imdb_votes": series.get("imdb_votes"),
        },
        scheme.TAGS_VIBE: {},
        scheme.GENRE: genre_defaults,
    }


def request_api_defaults(confirm_genres: bool = False) -> dict:
    """Ищет сериал через API и возвращает значения для ручной формы."""
    title = loop_input(
        text="Название сериала >> ",
        funcs_list=[valid.is_correct_title]
    )
    country = "Россия"
    result = api.find_series(title, country)

    if result["ok"] is False:
        print(f'API не нашёл подходящий сериал: {result["details"]}')
        return None

    series = result["data"]
    print("\nНайден сериал:")
    print(f'Название: {series.get("title")}')
    print(f'Год: {series.get("year")}')
    print(f'Страна: {", ".join(series.get("countries", []))}')
    print(f'Описание: {short_text(series.get("description"), 50)}')

    answer = input("\nЭто нужный сериал? Введи yes >> ").strip().lower()
    if answer != "yes":
        print("Операция отменена.")
        return None

    genres = None
    if confirm_genres:
        print("")
        genres = confirm_or_edit_api_genres(series)

    return build_api_defaults(series, genres)


def request_predict_features(defaults: dict) -> dict:
    """Запрашивает данные для прогноза и собирает признаки модели."""
    funcs = get_request_schema()
    main_info = {}
    raw_scores = {}
    tags_vibe = {}
    genre_values = {}

    print(f'\n--- {get_section_label(scheme.MAIN_INFO)} ---')
    year_settings = funcs[scheme.MAIN_INFO]["year"]
    year_default = defaults.get(scheme.MAIN_INFO, {}).get("year")
    year_answer = loop_input_with_default(
        text=f'>> {get_label("year")} [{year_default}]: ',
        funcs_list=get_validators(year_settings["tag"]),
        default_value=year_default
    )
    main_info["year"] = int(year_answer)

    print(f'\n--- {get_section_label(scheme.RAW_SCORES)} ---')
    for feature, field_settings in funcs[scheme.RAW_SCORES].items():
        default_value = defaults.get(scheme.RAW_SCORES, {}).get(feature)
        answer = loop_input_with_default(
            text=f'>> {get_label(feature)} [{default_value}]: ',
            funcs_list=get_validators(field_settings["tag"]),
            default_value=default_value
        )
        if field_settings["type"] is float:
            raw_scores[feature] = valid.parse_float(answer)
        else:
            raw_scores[feature] = field_settings["type"](answer)

    print(f'\n--- {get_section_label(scheme.TAGS_VIBE)} ---')
    for feature, field_settings in funcs[scheme.TAGS_VIBE].items():
        show_score_help(feature)
        default_value = defaults.get(scheme.TAGS_VIBE, {}).get(feature, 0)
        answer = loop_input_with_default(
            text=f'>> {get_label(feature)} [{default_value}]: ',
            funcs_list=get_validators(field_settings["tag"], field_settings.get("max_value", 1)),
            default_value=default_value
        )
        tags_vibe[feature] = int(answer)

    print(f'\n--- {get_section_label(scheme.GENRE)} ---')
    for feature, field_settings in funcs[scheme.GENRE].items():
        default_value = defaults.get(scheme.GENRE, {}).get(feature, 0)
        answer = loop_input_with_default(
            text=f'>> {get_label(feature)} [{default_value}]: ',
            funcs_list=get_validators(field_settings["tag"], field_settings.get("max_value", 1)),
            default_value=default_value
        )
        genre_values[feature] = int(answer)

    features = {
        constant.BIAS_FEATURE: 1.0
    }
    features.update(format_score.raw_to_struct(raw_scores, main_info))
    features.update(format_score.tags_to_features(tags_vibe))
    features.update(format_score.tags_to_features(genre_values, scheme.GENRE))
    return features


def show_score_help(feature: str) -> None:
    """Показывает подсказку по шкале тега."""
    help_info = constant.TAG_RULES.get(feature)
    if help_info is None:
        return

    print("\n" + "-" * 40)
    print(help_info["title"])
    print(help_info["question"])
    print("Шкала оценки:")
    for line in help_info["scale"]:
        print(f"  {line}")

def request_all_scores(defaults: dict = None) -> dict:
    """Запрашивает все данные фильма."""
    if defaults is None:
        defaults = {}
    funcs = get_request_schema()

    movie = {}

    for section_name, section_fields in funcs.items():
        section = {}

        print(f'\n--- {get_section_label(section_name)} ---')

        for feature, field_settings in section_fields.items():
            if section_name == scheme.TAGS_VIBE:
                show_score_help(feature)

            tags_validators = field_settings["tag"]
            type_func = field_settings["type"]
            funcs = get_validators(tags_validators, field_settings.get("max_value", 1))
            default_value = defaults.get(section_name, {}).get(feature)
            answer = loop_input_with_default(
                text=f'>> {get_label(feature)} [{default_value}]: ',
                funcs_list=funcs,
                default_value=default_value
            )
            if type_func is float:
                section[feature] = valid.parse_float(answer)
            else:
                section[feature] = type_func(answer)

        movie[section_name] = section

    return movie
