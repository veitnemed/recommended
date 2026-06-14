"""Собирает и хранит пул кандидатов по сохраненным критериям."""

import json
import os
import time
from datetime import datetime
from difflib import SequenceMatcher

from config import constant
from config import genre_tags
from core import valid
from core import format_score
from integrations import api

DISCOVER_PAGE_LIMIT = 30
DISCOVER_PAGE_PAUSE_SECONDS = 1.0


def format_optional_default(value) -> str:
    """Возвращает подпись значения по умолчанию для необязательного фильтра."""
    if value in (None, ""):
        return "не важно"
    if isinstance(value, list):
        return ", ".join(value) if len(value) > 0 else "не важно"
    return str(value)


def init_candidate_criteria() -> None:
    """Создает JSON с критериями подбора, если его еще нет."""
    if os.path.exists(constant.CRITERIA_POOL_JSON):
        return
    os.makedirs(constant.DATA_DIR, exist_ok=True)
    with open(constant.CRITERIA_POOL_JSON, "w", encoding="utf-8") as file:
        json.dump({}, file, ensure_ascii=False, indent=4)


def init_candidate_pool() -> None:
    """Создает JSON с пулом кандидатов, если его еще нет."""
    if os.path.exists(constant.CANDIDATE_POOL_JSON):
        return
    os.makedirs(constant.DATA_DIR, exist_ok=True)
    with open(constant.CANDIDATE_POOL_JSON, "w", encoding="utf-8") as file:
        json.dump({}, file, ensure_ascii=False, indent=4)


def load_candidate_criteria() -> dict:
    """Загружает сохраненные критерии подбора."""
    init_candidate_criteria()
    with open(constant.CRITERIA_POOL_JSON, "r", encoding="utf-8-sig") as file:
        data = json.load(file)
    return data if isinstance(data, dict) else {}


def save_candidate_criteria(data: dict) -> None:
    """Сохраняет критерии подбора."""
    with open(constant.CRITERIA_POOL_JSON, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_candidate_pool() -> dict:
    """Загружает текущий пул кандидатов."""
    init_candidate_pool()
    with open(constant.CANDIDATE_POOL_JSON, "r", encoding="utf-8-sig") as file:
        data = json.load(file)
    if isinstance(data, dict) is False:
        return {}
    normalized = remove_watched_candidates(deduplicate_pool(data))
    if normalized != data:
        save_candidate_pool(normalized)
    return normalized


def save_candidate_pool(data: dict) -> None:
    """Сохраняет пул кандидатов."""
    data = remove_watched_candidates(deduplicate_pool(data))
    with open(constant.CANDIDATE_POOL_JSON, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def prompt_optional_int(label: str, default=None, min_value: int = 0) -> int | None:
    """Запрашивает необязательное целое число."""
    while True:
        suffix = f" [{format_optional_default(default)}]"
        answer = input(f"{label}{suffix} >> ").strip()
        if answer == "":
            return default
        if valid.is_correct_votes(answer) is False:
            print("Введите целое число 0 или больше.")
            continue
        value = int(answer)
        if value < min_value:
            print(f"Введите число не меньше {min_value}.")
            continue
        return value


def prompt_optional_year(label: str, default=None) -> int | None:
    """Запрашивает необязательный год."""
    while True:
        suffix = f" [{format_optional_default(default)}]"
        answer = input(f"{label}{suffix} >> ").strip()
        if answer == "":
            return default
        if valid.is_correct_year(answer) is False:
            print(f"Введите год в диапазоне 2000-{constant.NOW_YEAR}.")
            continue
        return int(answer)


def prompt_optional_score(label: str, default=None) -> float | None:
    """Запрашивает необязательную оценку."""
    while True:
        suffix = f" [{format_optional_default(default)}]"
        answer = input(f"{label}{suffix} >> ").strip()
        if answer == "":
            return default
        if valid.is_correct_score(answer) is False:
            print("Введите число от 0 до 10.")
            continue
        return valid.parse_float(answer)


def normalize_genre_list(raw_value: str) -> list:
    """Нормализует строку жанров через запятую."""
    genres = []
    for item in str(raw_value or "").split(","):
        genre = item.strip()
        if genre != "":
            genres.append(genre)
    return genres


def get_available_genres() -> list:
    """Возвращает список доступных жанров для выбора в критериях."""
    tags = genre_tags.load_genre_tags()
    genres = []
    for settings in tags.values():
        source = str(settings.get("source", "")).strip()
        if source != "":
            genres.append(source)
    return sorted(set(genres))


def choose_genres_by_numbers(current_genres: list | None = None) -> list:
    """Дает выбрать жанры по номерам из списка."""
    if current_genres is None:
        current_genres = []

    genres = get_available_genres()
    if len(genres) == 0:
        print("Список жанров пока пуст.")
        return current_genres

    print("Выберите жанры по номерам через пробел.")
    print("Можно оставить пусто, тогда фильтра по жанрам не будет.\n")
    for idx, genre_name in enumerate(genres, start=1):
        print(f"{idx}. {genre_name[:1].upper() + genre_name[1:]}")

    current_label = ", ".join(current_genres) if len(current_genres) > 0 else "не важно"
    while True:
        answer = input(f"\nНомера жанров [{current_label}] >> ").strip()
        if answer == "":
            return current_genres

        parts = answer.split()
        selected_indexes = []
        for part in parts:
            try:
                index = int(part)
            except ValueError:
                selected_indexes = []
                break
            if 1 <= index <= len(genres):
                selected_indexes.append(index)
            else:
                selected_indexes = []
                break

        if len(selected_indexes) == 0:
            print("Введите номера жанров через пробел, например: 1 2 3")
            continue

        selected_genres = []
        for index in selected_indexes:
            genre_name = genres[index - 1]
            if genre_name not in selected_genres:
                selected_genres.append(genre_name)
        return selected_genres


def build_criteria_label(criteria_name: str, criteria: dict) -> str:
    """Формирует короткую подпись сохраненного набора критериев."""
    parts = [criteria_name]
    if criteria.get("count"):
        parts.append(f"count={criteria['count']}")
    if criteria.get("min_kp") is not None:
        parts.append(f"KP>={criteria['min_kp']}")
    if criteria.get("min_year") is not None:
        parts.append(f"year>={criteria['min_year']}")
    if criteria.get("country"):
        parts.append(criteria["country"])
    return " | ".join(parts)


def choose_or_create_criteria() -> tuple[str, dict] | None:
    """Дает выбрать сохраненный набор критериев или создать новый."""
    all_criteria = load_candidate_criteria()
    criteria_names = sorted(all_criteria.keys())

    print("Сохраненные критерии:\n")
    print(" 0 >> Создать новый набор")
    for idx, name in enumerate(criteria_names, start=1):
        print(f" {idx} >> {build_criteria_label(name, all_criteria[name])}")

    while True:
        answer = input("\nВыбор >> ").strip()
        try:
            select = int(answer)
        except ValueError:
            print("Введите номер пункта.")
            continue

        if 0 <= select <= len(criteria_names):
            break
        print("Такого пункта нет.")

    if select == 0:
        return create_criteria_interactive()

    name = criteria_names[select - 1]
    return name, all_criteria[name]


def choose_existing_criteria() -> tuple[str, dict] | None:
    """Дает выбрать только существующий набор критериев."""
    all_criteria = load_candidate_criteria()
    criteria_names = sorted(all_criteria.keys())
    if len(criteria_names) == 0:
        print("Сохраненных критериев пока нет.")
        return None

    print("Сохраненные критерии:\n")
    for idx, name in enumerate(criteria_names, start=1):
        print(f" {idx} >> {build_criteria_label(name, all_criteria[name])}")

    while True:
        answer = input("\nВыбор >> ").strip()
        try:
            select = int(answer)
        except ValueError:
            print("Введите номер пункта.")
            continue

        if 1 <= select <= len(criteria_names):
            break
        print("Такого пункта нет.")

    name = criteria_names[select - 1]
    return name, all_criteria[name]


def delete_criteria_and_candidates(criteria_name: str) -> dict:
    """Удаляет набор критериев и все связанные с ним объекты из общего пула."""
    all_criteria = load_candidate_criteria()
    if criteria_name not in all_criteria:
        return {
            "deleted_criteria": False,
            "deleted_candidates": 0,
        }

    all_criteria.pop(criteria_name, None)
    save_candidate_criteria(all_criteria)

    pool = load_candidate_pool()
    filtered_pool = {}
    deleted_candidates = 0
    for key, candidate in pool.items():
        if candidate.get("criteria_name") == criteria_name:
            deleted_candidates += 1
            continue
        filtered_pool[key] = candidate
    save_candidate_pool(filtered_pool)

    return {
        "deleted_criteria": True,
        "deleted_candidates": deleted_candidates,
    }


def create_criteria_interactive() -> tuple[str, dict] | None:
    """Запрашивает новый набор критериев и сохраняет его."""
    all_criteria = load_candidate_criteria()

    while True:
        criteria_name = input("Название набора критериев >> ").strip()
        if criteria_name == "":
            print("Название не должно быть пустым.")
            continue
        break

    current = all_criteria.get(criteria_name, {})
    country_default = current.get("country")
    country_answer = input(f"Страна [{format_optional_default(country_default)}] >> ").strip()
    country = country_answer if country_answer != "" else country_default
    count = prompt_optional_int("Сколько кандидатов собрать", current.get("count", 20), min_value=1)
    min_kp = prompt_optional_score("Минимальный рейтинг KP", current.get("min_kp"))
    min_imdb = prompt_optional_score("Минимальный рейтинг IMDb", current.get("min_imdb"))
    min_kp_votes = prompt_optional_int("Минимум голосов KP", current.get("min_kp_votes"))
    min_imdb_votes = prompt_optional_int("Минимум голосов IMDb", current.get("min_imdb_votes"))
    min_year = prompt_optional_year("Минимальный год", current.get("min_year"))
    max_year = prompt_optional_year("Максимальный год", current.get("max_year"))
    genres_default = current.get("genres", [])
    genres = choose_genres_by_numbers(genres_default)

    criteria = {
        "country": country,
        "count": count,
        "min_kp": min_kp,
        "min_imdb": min_imdb,
        "min_kp_votes": min_kp_votes,
        "min_imdb_votes": min_imdb_votes,
        "min_year": min_year,
        "max_year": max_year,
        "genres": genres,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }

    all_criteria[criteria_name] = criteria
    save_candidate_criteria(all_criteria)
    return criteria_name, criteria


def candidate_key(movie: dict) -> str:
    """Строит стабильный ключ кандидата для дедупликации."""
    title = normalized_title_key(
        movie.get("name")
        or movie.get("title")
        or movie.get("alternativeName")
        or movie.get("alternative_title")
        or movie.get("enName")
        or ""
    )
    year = movie.get("year") or ""
    return f"{title}|{year}"


def normalized_title_key(title: str) -> str:
    """Нормализует название для дедупликации кандидатов."""
    title = str(title or "").strip().casefold()
    title = title.replace("ё", "е")
    for char in [".", ",", "!", "?", ":", ";", "\"", "'", "`", "«", "»", "(", ")", "[", "]"]:
        title = title.replace(char, " ")
    while "  " in title:
        title = title.replace("  ", " ")
    return title.strip()


def compact_title_key(title: str) -> str:
    """Возвращает компактное название без пробелов для мягкого сравнения."""
    return normalized_title_key(title).replace(" ", "")


def titles_are_similar(left_title: str, right_title: str) -> bool:
    """Проверяет, что два названия достаточно похожи для дедупликации."""
    left = normalized_title_key(left_title)
    right = normalized_title_key(right_title)
    if left == "" or right == "":
        return False
    if left == right:
        return True

    left_compact = compact_title_key(left)
    right_compact = compact_title_key(right)
    if left_compact == right_compact:
        return True

    ratio = SequenceMatcher(None, left_compact, right_compact).ratio()
    if ratio >= 0.92:
        return True

    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if left_tokens and right_tokens and left_tokens == right_tokens:
        return True

    return False


def candidate_sort_score(candidate: dict) -> tuple:
    """Возвращает ключ качества кандидата для выбора лучшего дубля."""
    return (
        candidate.get("kp_score") or 0,
        candidate.get("kp_votes") or 0,
        candidate.get("imdb_score") or 0,
        candidate.get("imdb_votes") or 0,
    )


def candidate_pool_key(candidate: dict) -> str:
    """Строит ключ дедупликации для уже сохраненного кандидата."""
    title = normalized_title_key(candidate.get("title") or candidate.get("alternative_title") or "")
    year = candidate.get("year") or ""
    criteria_name = candidate.get("criteria_name") or ""
    return f"{criteria_name}|{title}|{year}"


def candidate_title(candidate: dict) -> str:
    """Возвращает лучшее доступное название кандидата."""
    return candidate.get("title") or candidate.get("alternative_title") or ""


def candidates_are_same(candidate: dict, other_candidate: dict, include_criteria: bool = True) -> bool:
    """Проверяет, относятся ли два кандидата к одному сериалу."""
    if include_criteria and (candidate.get("criteria_name") or "") != (other_candidate.get("criteria_name") or ""):
        return False

    left_year = candidate.get("year") or ""
    right_year = other_candidate.get("year") or ""
    if left_year != right_year:
        return False

    return titles_are_similar(candidate_title(candidate), candidate_title(other_candidate))


def deduplicate_pool(pool: dict) -> dict:
    """Удаляет дубли из пула, оставляя лучший вариант по рейтингу и голосам."""
    best_candidates = []
    for candidate in pool.values():
        matched_index = None
        for idx, current_best in enumerate(best_candidates):
            if candidates_are_same(candidate, current_best, include_criteria=True):
                matched_index = idx
                break

        if matched_index is None:
            best_candidates.append(candidate)
            continue

        current_best = best_candidates[matched_index]
        if candidate_sort_score(candidate) > candidate_sort_score(current_best):
            best_candidates[matched_index] = candidate

    deduplicated = {}
    for candidate in best_candidates:
        deduplicated[candidate_key(candidate)] = candidate
    return deduplicated


def build_watched_signatures() -> set:
    """Собирает сигнатуры уже просмотренных объектов из основного датасета."""
    from data_work import storage

    dataset = storage.load_dataset()
    signatures = set()
    for movie in dataset.values():
        main_info = movie.get("main_info", {})
        title = normalized_title_key(main_info.get("title"))
        year = main_info.get("year") or ""
        if title != "":
            signatures.add(f"{title}|{year}")
    return signatures


def is_watched_candidate(candidate: dict, watched_signatures: set | None = None) -> bool:
    """Проверяет, есть ли кандидат уже в основном датасете."""
    if watched_signatures is None:
        watched_signatures = build_watched_signatures()

    title = normalized_title_key(candidate.get("title") or candidate.get("alternative_title") or "")
    year = candidate.get("year") or ""
    exact_signature = f"{title}|{year}"
    if exact_signature in watched_signatures:
        return True

    candidate_compact = compact_title_key(title)
    for watched_signature in watched_signatures:
        watched_title, _, watched_year = watched_signature.partition("|")
        if str(watched_year) != str(year):
            continue
        if titles_are_similar(candidate_compact, watched_title):
            return True
    return False


def remove_watched_candidates(pool: dict) -> dict:
    """Удаляет из пула кандидатов уже просмотренные объекты."""
    watched_signatures = build_watched_signatures()
    filtered = {}
    for key, candidate in pool.items():
        if is_watched_candidate(candidate, watched_signatures):
            continue
        filtered[key] = candidate
    return filtered


def movie_matches_genres(movie: dict, expected_genres: list) -> bool:
    """Проверяет совпадение хотя бы по одному жанру."""
    if len(expected_genres) == 0:
        return True
    actual = {
        str(item.get("name", "")).strip().casefold()
        for item in movie.get("genres", []) or []
        if isinstance(item, dict) and item.get("name")
    }
    wanted = {genre.casefold() for genre in expected_genres}
    return len(actual & wanted) > 0


def normalize_candidate(movie: dict, criteria_name: str) -> dict:
    """Оставляет в пуле кандидатов полезные поля."""
    return {
        "id": movie.get("id"),
        "title": movie.get("name") or movie.get("alternativeName") or movie.get("enName"),
        "alternative_title": movie.get("alternativeName") or movie.get("enName"),
        "year": movie.get("year"),
        "type": movie.get("type"),
        "description": movie.get("shortDescription") or movie.get("description"),
        "kp_score": api.safe_nested(movie, "rating", "kp"),
        "kp_votes": api.safe_nested(movie, "votes", "kp"),
        "imdb_score": api.safe_nested(movie, "rating", "imdb"),
        "imdb_votes": api.safe_nested(movie, "votes", "imdb"),
        "countries": [item.get("name") for item in movie.get("countries", []) or [] if isinstance(item, dict) and item.get("name")],
        "genres": [item.get("name") for item in movie.get("genres", []) or [] if isinstance(item, dict) and item.get("name")],
        "criteria_name": criteria_name,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
    }


def collect_candidates(criteria_name: str, criteria: dict) -> dict:
    """Собирает новых кандидатов из API по критериям."""
    pool = load_candidate_pool()
    watched_signatures = build_watched_signatures()
    target_count = int(criteria.get("count") or 20)
    availability = api.check_api_available()
    if availability["ok"] is False:
        return {
            "criteria_name": criteria_name,
            "target_count": target_count,
            "added": 0,
            "duplicates": 0,
            "watched_skipped": 0,
            "scanned": 0,
            "last_page": 0,
            "pool_size": len(pool),
            "errors": [availability["details"]],
            "reached_end": False,
            "api_unavailable": True,
        }

    page = 1
    scanned = 0
    added = 0
    duplicates = 0
    watched_skipped = 0
    errors = []
    reached_end = False

    while added < target_count and page <= 20:
        result = api.discover_series_by_filters(criteria, page=page, limit=DISCOVER_PAGE_LIMIT)
        if result["ok"] is False:
            errors.append(result["details"] or result["error"] or "unknown_error")
            break

        docs = result["data"]
        if len(docs) == 0:
            reached_end = True
            break

        for movie in docs:
            scanned += 1

            if movie_matches_genres(movie, criteria.get("genres", [])) is False:
                continue

            candidate = normalize_candidate(movie, criteria_name)
            if is_watched_candidate(candidate, watched_signatures):
                watched_skipped += 1
                continue

            key = candidate_key(movie)
            if key in pool:
                duplicates += 1
                continue

            pool[key] = candidate
            added += 1

            if added >= target_count:
                break

        page += 1
        if added < target_count:
            time.sleep(DISCOVER_PAGE_PAUSE_SECONDS)

    save_candidate_pool(pool)
    return {
        "criteria_name": criteria_name,
        "target_count": target_count,
        "added": added,
        "duplicates": duplicates,
        "watched_skipped": watched_skipped,
        "scanned": scanned,
        "last_page": page,
        "pool_size": len(pool),
        "errors": errors,
        "reached_end": reached_end,
        "api_unavailable": False,
    }


def get_candidates_by_criteria(criteria_name: str) -> list:
    """Возвращает кандидатов, собранных по выбранному набору критериев."""
    pool = load_candidate_pool()
    candidates = [
        candidate
        for candidate in pool.values()
        if candidate.get("criteria_name") == criteria_name
    ]
    candidates.sort(
        key=lambda item: (
            -(item.get("kp_score") or 0),
            -(item.get("kp_votes") or 0),
            str(item.get("title") or "")
        )
    )
    return candidates


def get_all_candidates() -> list:
    """Возвращает всех кандидатов из общего пула."""
    pool = load_candidate_pool()
    candidates = list(pool.values())
    candidates.sort(
        key=lambda item: (
            -(item.get("kp_score") or 0),
            -(item.get("kp_votes") or 0),
            str(item.get("title") or "")
        )
    )
    return candidates


def remove_candidate_from_pool(target_candidate: dict) -> int:
    """Удаляет из общего пула все варианты кандидата, совпадающие по названию и году."""
    pool = load_candidate_pool()
    filtered_pool = {}
    removed = 0

    for key, candidate in pool.items():
        if candidates_are_same(candidate, target_candidate, include_criteria=False):
            removed += 1
            continue
        filtered_pool[key] = candidate

    if removed > 0:
        save_candidate_pool(filtered_pool)
    return removed


def build_candidate_features(candidate: dict) -> dict:
    """Собирает признаки модели для кандидата из пула без вайб-тегов."""
    year = int(candidate.get("year") or constant.NOW_YEAR)
    raw_scores = {
        "kp_score": float(candidate.get("kp_score") or 0),
        "kp_votes": int(candidate.get("kp_votes") or 0),
        "imdb_score": float(candidate.get("imdb_score") or 0),
        "imdb_votes": int(candidate.get("imdb_votes") or 0),
    }
    main_info = {"year": year}

    genre_features = {feature: 0 for feature in constant.GENRE}
    for genre_name in candidate.get("genres", []):
        feature = genre_tags.genre_to_feature_name(genre_name)
        if feature in genre_features:
            genre_features[feature] = 1

    features = {constant.BIAS_FEATURE: 1.0}
    features.update(format_score.raw_to_struct(raw_scores, main_info))
    features.update({feature: 0 for feature in constant.TAGS_VIBE})
    features.update(format_score.tags_to_features(genre_features, constant.GENRE_SECTION))
    return features


def find_suspicious_duplicates() -> list:
    """Ищет подозрительно похожие пары кандидатов в общем пуле."""
    candidates = get_all_candidates()
    suspicious_pairs = []

    for left_index in range(len(candidates)):
        left = candidates[left_index]
        left_title = candidate_title(left)
        left_year = left.get("year") or ""
        if left_title == "":
            continue

        for right_index in range(left_index + 1, len(candidates)):
            right = candidates[right_index]
            right_title = candidate_title(right)
            right_year = right.get("year") or ""
            if right_title == "":
                continue
            if left_year != right_year:
                continue

            left_normalized = normalized_title_key(left_title)
            right_normalized = normalized_title_key(right_title)
            if left_normalized == right_normalized:
                continue

            ratio = SequenceMatcher(
                None,
                compact_title_key(left_title),
                compact_title_key(right_title),
            ).ratio()

            if ratio < 0.80:
                continue

            suspicious_pairs.append({
                "left": left,
                "right": right,
                "ratio": ratio,
            })

    suspicious_pairs.sort(key=lambda item: item["ratio"], reverse=True)
    return suspicious_pairs
