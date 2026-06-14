"""Работает с каталогом жанровых признаков модели."""

import copy
import json
from pathlib import Path


GENRE_TAGS_JSON = str(Path(__file__).resolve().with_name("genre_tags.json"))

GENRE_NAME_TO_FEATURE = {
    "драма": "has_drama",
    "криминал": "has_crime",
    "триллер": "has_thriller",
    "комедия": "has_comedy",
    "детектив": "has_detective",
    "мелодрама": "has_melodrama",
    "боевик": "has_action",
    "фантастика": "has_fantasy",
    "ужасы": "has_horror",
    "приключения": "has_adventure",
    "фэнтези": "has_fantasy",
    "аниме": "has_anime",
    "мультфильм": "has_animation",
    "документальный": "has_documentary",
    "биография": "has_biography",
    "история": "has_history",
    "военный": "has_war",
    "семейный": "has_family",
    "музыка": "has_music",
    "мюзикл": "has_musical",
    "вестерн": "has_western",
    "спорт": "has_sport",
}

DEFAULT_GENRE_TAGS = {
    feature: {
        "label": genre_name[:1].upper() + genre_name[1:],
        "translation": feature.removeprefix("has_").replace("_", " ").title(),
        "source": genre_name,
    }
    for genre_name, feature in GENRE_NAME_TO_FEATURE.items()
}

LEGACY_GENRE_FIELDS = {
    feature: settings["source"]
    for feature, settings in DEFAULT_GENRE_TAGS.items()
}

CYRILLIC_TO_LATIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
    "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
    "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
    " ": "_", "-": "_", "/": "_",
}


def normalize_genre_name(genre_name: str) -> str:
    """Нормализует имя жанра из API."""
    return str(genre_name).strip().casefold()


def make_label(genre_name: str) -> str:
    """Преобразует техническое имя жанра в человекочитаемую подпись."""
    if genre_name == "":
        return ""
    return genre_name[:1].upper() + genre_name[1:]


def transliterate_to_ascii(text: str) -> str:
    """Переводит кириллицу в ASCII fallback для имён признаков."""
    pieces = []
    for char in normalize_genre_name(text):
        pieces.append(CYRILLIC_TO_LATIN.get(char, char if char.isascii() and char.isalnum() else "_"))

    slug = "".join(pieces)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


def genre_to_feature_name(genre_name: str) -> str:
    """Возвращает имя признака модели для жанра."""
    normalized = normalize_genre_name(genre_name)
    if normalized in GENRE_NAME_TO_FEATURE:
        return GENRE_NAME_TO_FEATURE[normalized]

    ascii_name = transliterate_to_ascii(normalized)
    if ascii_name == "":
        ascii_name = "unknown_genre"
    return f"has_{ascii_name}"


def build_genre_settings(genre_name: str) -> dict:
    """Создает настройки нового жанрового признака."""
    normalized = normalize_genre_name(genre_name)
    feature = genre_to_feature_name(normalized)
    return {
        "label": make_label(normalized),
        "translation": feature.removeprefix("has_").replace("_", " ").title(),
        "source": normalized,
    }


def normalize_loaded_tags(tags: dict) -> tuple[dict, dict]:
    """Приводит каталог жанров к каноническим именам и возвращает карту миграции."""
    normalized = {}
    migrated = {}

    for feature, settings in tags.items():
        source = normalize_genre_name(settings.get("source", ""))
        if source == "":
            if feature.startswith("genre_"):
                source = normalize_genre_name(feature.removeprefix("genre_"))
            elif feature.startswith("has_"):
                source = normalize_genre_name(feature.removeprefix("has_").replace("_", " "))
            else:
                source = normalize_genre_name(feature)

        active_feature = genre_to_feature_name(source)
        migrated[feature] = active_feature

        normalized[active_feature] = {
            "label": settings.get("label", make_label(source)),
            "translation": settings.get(
                "translation",
                active_feature.removeprefix("has_").replace("_", " ").title(),
            ),
            "source": source,
        }

    return normalized, migrated


def load_genre_tags() -> dict:
    """Загружает каталог жанровых признаков из JSON."""
    path = Path(GENRE_TAGS_JSON)
    if path.exists() is False:
        return copy.deepcopy(DEFAULT_GENRE_TAGS)

    with open(path, "r", encoding="utf-8-sig") as file:
        data = json.load(file)

    normalized, migrated = normalize_loaded_tags(data)
    if normalized != data:
        save_genre_tags(normalized)
    return normalized


def save_genre_tags(tags: dict) -> None:
    """Сохраняет каталог жанровых признаков."""
    with open(GENRE_TAGS_JSON, "w", encoding="UTF-8") as file:
        json.dump(tags, file, ensure_ascii=False, indent=4)


def get_genre_fields() -> list:
    """Возвращает имена жанровых тегов."""
    return list(load_genre_tags().keys())


def get_genre_labels() -> dict:
    """Возвращает подписи жанровых тегов."""
    return {
        feature: settings["label"]
        for feature, settings in load_genre_tags().items()
    }


def get_genre_translations() -> dict:
    """Возвращает переводы жанровых тегов."""
    return {
        feature: settings["translation"]
        for feature, settings in load_genre_tags().items()
    }


def get_legacy_feature_map() -> dict:
    """Возвращает карту старых имён genre-признаков в актуальные."""
    tags = load_genre_tags()
    legacy = {}
    for feature, settings in tags.items():
        source = settings["source"]
        legacy[f"genre_{source}"] = feature
    return legacy


def map_feature_name(feature: str) -> str:
    """Возвращает актуальное имя genre-признака для старого ключа."""
    if feature in load_genre_tags():
        return feature

    legacy = get_legacy_feature_map()
    if feature in legacy:
        return legacy[feature]

    if feature in LEGACY_GENRE_FIELDS:
        return genre_to_feature_name(LEGACY_GENRE_FIELDS[feature])

    return feature


def ensure_genre_fields(genre_names: list) -> list:
    """Добавляет в каталог новые жанры и возвращает список новых признаков."""
    tags = load_genre_tags()
    added = []

    for genre_name in genre_names:
        normalized = normalize_genre_name(genre_name)
        if normalized == "":
            continue

        feature = genre_to_feature_name(normalized)
        if feature in tags:
            continue

        tags[feature] = build_genre_settings(normalized)
        added.append(feature)

    if len(added) > 0:
        save_genre_tags(tags)

    return added
