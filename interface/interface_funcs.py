"""Содержит действия интерфейса, которые запускаются из пунктов меню."""

from config import constant
from core import format_score as format
from data_work import candidate_pool
from data_work import dataset_stats
from data_work import genre_import
from data_work import genre_stats
from data_work import tst_scores
from model_work import model
from interface import request
from data_work import storage
from interface import ui
from core import valid
from integrations import api
from integrations import kino_teatr_scraper


def show_all_movies():
    """Показывает все фильмы из датасета."""
    data = storage.load_dataset()
    if len(data) == 0:
        print('Датасет пуст!')
        return

    for idx, movie in enumerate(data.values()):
        main_info = movie["main_info"]
        print(f"{idx + 1}) {main_info['title']} | оценка: {main_info['user_score']}")


def get_predict(weights: dict) -> None:
    """Запрашивает признаки и показывает прогноз модели."""
    defaults = request.request_api_defaults()
    if defaults is None:
        return

    title = defaults["main_info"]["title"]
    features = request.request_predict_features(defaults)
    score = model.predict_score(features, weights)
    print(f'Оценка модели для {title}: {score}')


def request_object() -> None:
    """Запрашивает фильм и добавляет его в датасет."""
    ui.clean_terminal()

    defaults = request.request_api_defaults(confirm_genres=True)
    if defaults is None:
        return

    movie_request = request.request_all_scores(defaults)
    result = storage.add_movie(movie_request)

    if result:
        print('Новая запись добавлена!')
    else:
        print('Ошибка! Новая запись не добавлена')


def mark_candidate_as_watched() -> None:
    """Переносит кандидата из пула в основной датасет через обычный сценарий добавления."""
    ui.clean_terminal()
    selected = candidate_pool.choose_existing_criteria()
    if selected is None:
        return

    criteria_name, criteria = selected
    candidates = candidate_pool.get_candidates_by_criteria(criteria_name)

    print(f"\nПулл кандидатов: {criteria_name}")
    print(f"Страна: {criteria.get('country')}")
    print(f"Кандидатов: {len(candidates)}\n")

    if len(candidates) == 0:
        print("Для этого набора критериев кандидатов пока нет.")
        return

    for idx, candidate in enumerate(candidates, start=1):
        title = candidate.get("title") or "Без названия"
        year = candidate.get("year") or "?"
        description = request.short_text(candidate.get("description"), 50) or "без описания"
        print(f"{idx}) {title} ({year})")
        print(f"   Описание: {description}")

    selected_index = request.loop_input(
        text="\nНомер просмотренного кандидата >> ",
        funcs_list=[lambda value: value.isdigit() and 1 <= int(value) <= len(candidates)]
    )
    candidate = candidates[int(selected_index) - 1]

    print("")
    defaults = request.build_api_defaults(candidate)
    movie_request = request.request_all_scores(defaults)
    result = storage.add_movie(movie_request)

    if result:
        removed = candidate_pool.remove_candidate_from_pool(candidate)
        print('Новая запись добавлена!')
        print(f'Из общего пула удалено совпадений: {removed}')
    else:
        print('Ошибка! Новая запись не добавлена')


def show_mean_error(data, weights):
    """Показывает средние ошибки модели."""
    ui.clean_terminal()
    abs_error = model.mean_absolute_error(data, weights)
    error = model.mean_error(data, weights)
    print(f'\nСредняя ошибка модели: {round(abs_error, 2)}')
    print(f'\nСреднее линейное отклонение: {round(error, 2)}')


def show_weights_model(weights):
    """Показывает веса модели."""
    ui.clean_terminal()
    print('Веса модели:\n')
    for weight, value in weights.items():
        print(f'{weight}: {round(value, 2)}')


def reset_weights_model():
    """Сбрасывает веса модели."""
    storage.save_weights(constant.DEFAULT_WEIGHTS.copy())
    print('Веса сброшены на значения по умолчанию.')


def votes_impact():
    """Показывает влияние количества голосов на популярность."""
    data = storage.load_meta()
    for title, obj in data.items():
        raw_scores = obj.get("raw_scores", obj.get("raw"))
        main_info = obj.get("main_info", {})
        year = main_info.get("year", raw_scores.get("year"))
        kp_votes, imdb_votes = raw_scores["kp_votes"], raw_scores["imdb_votes"]
        kp = format.popularity_kp(kp_votes, year)
        imdb = format.popularity_score(imdb_votes, year)
        print(f'{title} ({year})\n')
        print(f'KP: {kp_votes} -> {round(kp, 1)}')
        print(f'IMDB: {imdb_votes} -> {round(imdb, 1)}\n')


def show_feature_importance(weights, full_error):
    """Показывает влияние каждого признака."""
    ui.clean_terminal()
    data = storage.load_dataset()
    if len(data) == 0:
        print('Датасет пуст!')
        return

    groups = [
        ("Количественные", [constant.BIAS_FEATURE] + constant.COMPUTED_SCORES),
        ("Вайб", constant.TAGS_VIBE),
        ("Жанры", constant.GENRE),
    ]

    feature_rows = {}
    for feature in constant.FEATURES:
        weights_without_feature = model.selection_weights_without_feature(data, feature, weights)
        error_without_feature = model.mean_absolute_error(data, weights_without_feature)
        feature_rows[feature] = {
            "label": constant.FIELD_LABELS.get(feature, feature),
            "error_without_feature": error_without_feature,
            "delta": error_without_feature - full_error,
        }

    print('Оценка вклада признаков\n')
    print(f"Текущая ошибка полной модели: {round(full_error * 10, 2)} %\n")

    for group_title, features in groups:
        rows = [
            (feature, feature_rows[feature])
            for feature in features
            if feature in feature_rows
        ]
        rows.sort(key=lambda item: item[1]["delta"], reverse=True)

        print(group_title)
        print('-' * len(group_title))

        if len(rows) == 0:
            print('Нет признаков.\n')
            continue

        for feature, row in rows:
            print(
                f"{row['label']} ({feature}) | "
                f"ошибка без признака: {row['error_without_feature'] * 10:.2f} % | "
                f"вклад: {row['delta']:.4f}"
            )

        group_delta = sum(row["delta"] for _, row in rows)
        group_avg = group_delta / len(rows)
        print(f"Итого по группе: {group_delta:.4f}")
        print(f"Средний вклад: {group_avg:.4f}\n")


def show_data_info():
    """Показывает сводку по датасету."""
    data = storage.load_dataset()
    for line in dataset_stats.build_dataset_info_lines(data):
        print(line)


def rename_movie_record() -> None:
    """Переименовывает запись в основном датасете и meta."""
    ui.clean_terminal()
    titles = storage.get_all_titles()
    if len(titles) == 0:
        print("Датасет пуст!")
        return

    print("Текущие записи:\n")
    for idx, title in enumerate(titles, start=1):
        print(f"{idx}) {title}")

    old_title = request.loop_input(
        text="\nСтарое название >> ",
        funcs_list=[valid.is_correct_title]
    )
    new_title = request.loop_input(
        text="Новое название >> ",
        funcs_list=[valid.is_correct_title]
    )

    if storage.rename_movie_title(old_title, new_title):
        print("Название записи обновлено.")
    else:
        print("Переименование не выполнено.")


def load_genre_markup():
    """Загружает жанровую разметку для текущего датасета с подтверждением."""
    ui.clean_terminal()
    result = genre_import.apply_genre_markup()
    print(f"\nОбработано записей: {result['total']}")
    print(f"Подтверждено: {result['updated']}")
    print(f"Пропущено: {result['skipped']}")
    print(f"Не найдено: {len(result['not_found'])}")
    print(f"Ошибок API: {len(result['errors'])}")


def read_tst_scores():
    """Читает оценки из TST JSON и обновляет оценки совпавших сериалов."""
    try:
        result = tst_scores.apply_tst_scores()
    except FileNotFoundError:
        print(f'Файл TST не найден: {constant.TST_SCORES_JSON}')
        return
    except ValueError as error:
        print(f'Ошибка чтения TST: {error}')
        return

    print('Оценки TST прочитаны.')
    print(f'Всего в TST: {result["total"]}')
    print(f'Обновлено оценок: {result["updated"]}')
    print(f'Без изменений: {result["unchanged"]}')
    print(f'Не найдены в датасете: {len(result["not_found"])}')
    print(f'Некорректные оценки: {len(result["invalid"])}')

    if len(result["not_found"]) > 0:
        print('\nПервые ненайденные:')
        for title in result["not_found"][:10]:
            print(f'- {title}')

    if len(result["invalid"]) > 0:
        print('\nПервые с некорректной оценкой:')
        for title in result["invalid"][:10]:
            print(f'- {title}')


def show_api_features():
    """Ищет сериал через API и печатает полный JSON найденного объекта."""
    title = request.loop_input(
        text='Название сериала >> ',
        funcs_list=[valid.is_correct_title]
    )
    result = api.find_series_raw(title, "Россия")

    if result["ok"] is False:
        print(f'Сериал не найден в списке API: {result["details"]}')
        return

    print('\nСериал найден в списке API.\n')
    for line in api.format_api_movie_lines(result["data"]):
        print(line)


def format_scraper_value(value) -> str:
    """Форматирует пустые значения для отчета скрапера."""
    if value is None or value == "" or value == []:
        return "нет данных"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if len(value) > 0 else "нет данных"
    return str(value)


def format_scraper_rating(value) -> str:
    """Форматирует оценку или показывает, что ее нет."""
    if value is None:
        return "-"
    return str(value)


def print_kino_teatr_result_item(item: dict, index: int | None = None) -> None:
    """Печатает один найденный элемент Kino-Teatr в коротком виде."""
    prefix = f"{index}) " if index is not None else ""
    ratings = item.get("ratings") or {}
    countries = item.get("countries") or []
    country = item.get("country") or ", ".join(countries)
    metrics = item.get("available_metrics") or []

    print(f"{prefix}{format_scraper_value(item.get('title'))} ({format_scraper_value(item.get('year'))})")
    print(f"   Страна: {format_scraper_value(country)}")
    print(f"   Жанры: {format_scraper_value(item.get('genres'))}")
    print(f"   Режиссер: {format_scraper_value(item.get('director'))}")
    print(f"   Сценаристы: {request.short_text(format_scraper_value(item.get('screenwriters')), 160)}")
    print(f"   Актеры: {request.short_text(format_scraper_value(item.get('actors')), 160)}")
    print(f"   Производство: {format_scraper_value(item.get('production'))}")
    print(f"   Премьера: {format_scraper_value(item.get('premiere'))}")
    print(f"   Серий: {format_scraper_value(item.get('episodes'))}")
    print(
        "   Рейтинг сайта: "
        f"{format_scraper_rating(ratings.get('site_rating'))} "
        f"/ голосов {format_scraper_rating(ratings.get('site_rating_votes'))}"
    )
    print(
        "   Ожидания: "
        f"{format_scraper_rating(ratings.get('expectation_score'))} "
        f"/ голосов {format_scraper_rating(ratings.get('expectation_votes'))}"
    )
    print(f"   Метрики: {format_scraper_value(metrics)}")
    print(f"   Описание: {request.short_text(format_scraper_value(item.get('description')), 240)}")
    print(f"   Обновлено: {format_scraper_value(item.get('last_update'))}")
    print(f"   Совпадение: {format_scraper_value(item.get('match_score'))}")
    print(f"   URL: {format_scraper_value(item.get('url'))}")
    print(f"   Постер: {format_scraper_value(item.get('poster'))}")


def show_kino_teatr_scraper_test() -> None:
    """Запрашивает название и печатает информативный отчет Kino-Teatr-скрапера."""
    title = request.loop_input(
        text='Название для Kino-Teatr >> ',
        funcs_list=[valid.is_correct_title]
    )

    print("\nЗапускаю поиск Kino-Teatr...")
    result = kino_teatr_scraper.find_title(title, limit=5)

    if result["ok"] is False:
        print(f'Kino-Teatr scraper не вернул данные: {result["details"] or result["error"]}')
        return

    data = result["data"]
    best = data.get("best")
    results = data.get("results") or []

    print("\nKino-Teatr scraper: краткий отчет")
    print("=" * 60)
    print(f"Запрос: {data.get('query')}")
    print(f"Источник: {data.get('source_url')}")
    print(f"Найдено результатов: {len(results)}")

    if best is not None:
        print("\nЛучшее совпадение:")
        print_kino_teatr_result_item(best)

    if len(results) > 0:
        print("\nПервые результаты:")
        for idx, item in enumerate(results[:5], start=1):
            print_kino_teatr_result_item(item, index=idx)


def show_dataset_genres() -> None:
    """Показывает все жанры текущего датасета через API."""
    ui.clean_terminal()
    genre_stats.show_dataset_genres()


def collect_candidate_pool() -> None:
    """Собирает пул кандидатов по сохраненным критериям."""
    ui.clean_terminal()
    selected = candidate_pool.choose_or_create_criteria()
    if selected is None:
        print("Критерии не выбраны.")
        return

    criteria_name, criteria = selected
    print(f"\nЗапуск подбора по критериям: {criteria_name}")
    result = candidate_pool.collect_candidates(criteria_name, criteria)

    print("\nСбор пула кандидатов завершён.")
    print(f"Набор критериев: {result['criteria_name']}")
    print(f"Нужно было собрать: {result['target_count']}")
    print(f"Новых кандидатов добавлено: {result['added']}")
    print(f"Совпадений уже в JSON: {result['duplicates']}")
    print(f"Уже есть в основном датасете: {result['watched_skipped']}")
    print(f"Проверено объектов API: {result['scanned']}")
    print(f"Последняя страница: {result['last_page']}")
    print(f"Текущий размер пула: {result['pool_size']}")

    if result.get("api_unavailable"):
        print("API сейчас недоступен. Общий пул сохранён без изменений.")

    if result["reached_end"]:
        print("Выдача API закончилась раньше, чем набралось нужное количество.")

    if len(result["errors"]) > 0:
        print("Ошибки API/сети:")
        for error in result["errors"]:
            print(f"- {error}")


def show_candidate_pool() -> None:
    """Показывает кандидатов выбранного пула в консоли."""
    ui.clean_terminal()
    selected = candidate_pool.choose_existing_criteria()
    if selected is None:
        return

    criteria_name, criteria = selected
    candidates = candidate_pool.get_candidates_by_criteria(criteria_name)

    print(f"\nПул кандидатов: {criteria_name}")
    print(f"Страна: {criteria.get('country')}")
    print(f"Кандидатов: {len(candidates)}\n")

    if len(candidates) == 0:
        print("Для этого набора критериев кандидатов пока нет.")
        return

    for idx, candidate in enumerate(candidates, start=1):
        title = candidate.get("title") or "Без названия"
        year = candidate.get("year") or "?"
        kp_score = candidate.get("kp_score")
        imdb_score = candidate.get("imdb_score")
        kp_votes = candidate.get("kp_votes") or 0
        genres = ", ".join(candidate.get("genres", [])) or "нет"
        description = request.short_text(candidate.get("description"), 80) or "без описания"

        print(f"{idx}) {title} ({year})")
        print(f"   KP: {kp_score} | IMDb: {imdb_score} | KP votes: {kp_votes}")
        print(f"   Жанры: {genres}")
        print(f"   Описание: {description}\n")


def show_global_candidate_top() -> None:
    """Показывает топ кандидатов из общего пула по предикту без вайб-тегов."""
    ui.clean_terminal()
    candidates = candidate_pool.get_all_candidates()
    if len(candidates) == 0:
        print("Общий пул кандидатов пуст.")
        return

    top_n_value = request.loop_input(
        text="Топ N из общего пула >> ",
        funcs_list=[valid.is_correct_top_n]
    )
    top_n = min(int(top_n_value), len(candidates))

    weights = storage.load_weights()
    no_vibe_features = [
        feature for feature in constant.FEATURES
        if feature not in constant.TAGS_VIBE
    ]
    prediction_weights = model.make_group_weights(weights, no_vibe_features)

    scored_candidates = []
    for candidate in candidates:
        features = candidate_pool.build_candidate_features(candidate)
        predict = model.predict_score(features, prediction_weights)
        scored_candidates.append({
            "title": candidate.get("title") or "Без названия",
            "year": candidate.get("year") or "?",
            "predict": predict,
        })

    scored_candidates.sort(key=lambda item: item["predict"], reverse=True)

    print(f"\nТоп {top_n} из общего пула:\n")
    for row in scored_candidates[:top_n]:
        print(f"{row['title']} ({row['year']}): {row['predict']:.2f}")


def delete_candidate_pool() -> None:
    """Удаляет набор критериев и связанные с ним объекты из общего пула."""
    ui.clean_terminal()
    selected = candidate_pool.choose_existing_criteria()
    if selected is None:
        return

    criteria_name, _ = selected
    answer = input(f"\nУдалить пулл '{criteria_name}'? yes >> ").strip().lower()
    if answer != "yes":
        print("Удаление отменено.")
        return

    result = candidate_pool.delete_criteria_and_candidates(criteria_name)
    if result["deleted_criteria"] is False:
        print("Пулл не найден.")
        return

    print("Пулл удалён.")
    print(f"Удалено кандидатов из общего пула: {result['deleted_candidates']}")


def show_suspicious_candidate_duplicates() -> None:
    """Показывает подозрительно похожие дубли в общем пуле."""
    ui.clean_terminal()
    pairs = candidate_pool.find_suspicious_duplicates()
    if len(pairs) == 0:
        print("Подозрительных дублей в общем пуле не найдено.")
        return

    print("Подозрительные дубли в общем пуле:\n")
    for idx, pair in enumerate(pairs, start=1):
        left = pair["left"]
        right = pair["right"]
        print(f"{idx}) Похожесть: {pair['ratio']:.2f}")
        print(
            f"   A: {left.get('title')} ({left.get('year')}) "
            f"| критерий: {left.get('criteria_name')}"
        )
        print(
            f"   B: {right.get('title')} ({right.get('year')}) "
            f"| критерий: {right.get('criteria_name')}"
        )
        print("")
