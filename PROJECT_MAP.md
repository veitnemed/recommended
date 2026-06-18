# Карта проекта

`Terminal Movies Learn` - консольная система для ведения личного dataset оценок и обучения простой рекомендательной модели.

Ниже карта проекта в текущем состоянии: какие папки за что отвечают и через какие точки проходит основная логика.

## Быстрый вход

- [main.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/main.py:1) - вход в приложение.
- [README.md](/d:/VS%20PROJJJ/vscode%20projects/recommended/README.md:1) - пользовательское описание.
- [PROJECT_MAP.md](/d:/VS%20PROJJJ/vscode%20projects/recommended/PROJECT_MAP.md:1) - карта проекта.
- [ADD_RECORD_RULES.md](/d:/VS%20PROJJJ/vscode%20projects/recommended/ADD_RECORD_RULES.md:1) - контракт добавления и изменения записей.

## Основной runtime-поток

1. `main.py` вызывает инициализацию storage.
2. `interface.menu_state` собирает текущий state: dataset, weights, счётчики, ошибки модели.
3. `interface.ui` печатает меню.
4. `interface.global_menu` маршрутизирует пользователя по разделам.
5. `interface.interface_funcs` запускает конкретные сценарии UI.
6. `data_work` выполняет бизнес-логику: dataset, pool, SQL, TMDb, Excel.
7. `model_work` строит признаки, считает предикт, ошибки и обучение.

## Папки и роли

### `config/`

Базовые константы, схемы и каталоги признаков.

- [config/constant.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/config/constant.py:1) - пути, названия секций, наборы признаков.
- [config/scheme.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/config/scheme.py:1) - схема `main_info`, `raw_scores`, `tags_vibe`, `genre`.
- [config/tags.json](/d:/VS%20PROJJJ/vscode%20projects/recommended/config/tags.json:1) - vibe-теги.
- [config/genre_tags.json](/d:/VS%20PROJJJ/vscode%20projects/recommended/config/genre_tags.json:1) - жанровые признаки.
- [config/genre_tags.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/config/genre_tags.py:1) - нормализация и генерация `has_*` жанров.

### `core/`

Низкоуровневая логика без привязки к меню.

- [core/valid.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/core/valid.py:1) - валидация ввода и payload.
- [core/format_score.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/core/format_score.py:1) - преобразование `raw_scores` в вычисляемые признаки.

### `interface/`

Консольный UI и маршрутизация.

- [interface/ui.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/ui.py:1) - печать экранов и меню.
- [interface/global_menu.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/global_menu.py:1) - циклы меню и переходы между разделами.
- [interface/interface_funcs.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/interface_funcs.py:1) - UI-оркестрация сценариев.
- [interface/request.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/request.py:1) - формы, prompts, сбор `movie_request`.
- [interface/title_presenters.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/title_presenters.py:1) - карточки SQL/API/defaults.
- [interface/candidate_pool_ui.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/candidate_pool_ui.py:1) - интерактивная работа с criteria.
- [interface/tags_menu.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/tags_menu.py:1) - управление vibe-тегами.
- [interface/backup_menu.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/backup_menu.py:1) - backup и restore.

### `data_work/`

Основная прикладная логика данных.

- [data_work/storage.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/storage.py:1) - фасад для storage-сервисов.
- [data_work/storage_files.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/storage_files.py:1) - файлы, каталоги, backup.
- [data_work/storage_data.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/storage_data.py:1) - dataset/meta/weights, rename title.
- [data_work/storage_movie.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/storage_movie.py:1) - `add_movie()`, Excel row -> movie payload, пересчёт computed.
- [data_work/dataset_records.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/dataset_records.py:1) - центральный add/update service.
- [data_work/storage_normalize.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/storage_normalize.py:1) - нормализация `main_info`, `raw_scores`, `tags_vibe`, `genre`.
- [data_work/excel_work.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/excel_work.py:1) - Excel export/import.
- [data_work/candidate_pool.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/candidate_pool.py:1) - общий candidate pool: сбор, фильтры, ranking, retry KP, import/remove.
- [data_work/tmdb_candidate_pool.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/tmdb_candidate_pool.py:1) - TMDb candidate pool v1.
- [data_work/sql_search.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/sql_search.py:1) - поиск в локальной IMDb SQLite базе.
- [data_work/title_resolve.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/title_resolve.py:1) - сбор defaults из SQL/API/TMDb и payload для переноса кандидата.
- [data_work/genre_import.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/genre_import.py:1) - массовая жанровая разметка.
- [data_work/dataset_stats.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/dataset_stats.py:1) - сводка dataset.
- [data_work/genre_stats.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/genre_stats.py:1) - просмотр жанров dataset.

### `integrations/`

Внешние источники данных.

- [integrations/api.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/integrations/api.py:1) - KP/внешний API для рейтингов, описаний и candidate-поиска.
- [integrations/api_tmdb.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/integrations/api_tmdb.py:1) - TMDb Discover, Details и нормализация ответов.

### `model_work/`

Модель и обучение.

- [model_work/model.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/model_work/model.py:1) - предикт, MAE, feature logic.
- [model_work/linear_regression_train.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/model_work/linear_regression_train.py:1) - линейное обучение.
- [model_work/train_modes.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/model_work/train_modes.py:1) - дополнительные режимы обучения и диагностики.
- [model_work/train_report.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/model_work/train_report.py:1) - отчёт по модели.
- [model_work/noise_experiment.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/model_work/noise_experiment.py:1) - шумовая устойчивость.

## Текущее меню

### Главное меню

1. `Данные`
2. `Обучение`
3. `Модель`
4. `Дополнительно`
5. `Пулл кандидатов`
6. `Выгрузить отчёт`

### `Пулл кандидатов`

Главный экран:

1. `Собрать новый пулл`
2. `Посмотреть пуллы кандидатов`
3. `Собрать топ из общего пула`
4. `Отметить просмотренные из пулла`
5. `Управление пуллами`
6. `Диагностика и обслуживание`
0. `Главное меню`

Подменю `Собрать новый пулл`:

- `TMDb -> IMDb SQL -> KP API`
- `Legacy IMDb SQL -> KP API`
- `TMDb test-run`

Подменю `Управление пуллами`:

- `Удалить пулл`
- `Фильтрация / редактирование критериев`
- `Импортировать TMDb result в общий пул`

Подменю `Диагностика и обслуживание`:

- `Показать подозрительные дубли`
- `Добрать KP для неполных кандидатов`
- `Показать вклады для кандидатов`

## Ключевые потоки

### 1. Ручное добавление записи

1. `interface.interface_funcs.request_object()`
2. `interface.request.request_api_defaults(confirm_genres=True)`
3. `data_work.title_resolve.resolve_title_for_training()`
4. `interface.request.request_all_scores(defaults)`
5. `data_work.storage_movie.add_movie(print_message=False)`
6. `data_work.dataset_records.add_dataset_record()`

UI печатает финальное сообщение сам. Storage возвращает `AddRecordResult`.

### 2. Перенос кандидата из пула в dataset

1. `interface.interface_funcs.mark_candidate_as_watched()`
2. выбор `criteria_name` и кандидата;
3. `data_work.title_resolve.build_candidate_transfer_payload(candidate)`;
4. предупреждение для incomplete-кандидата, если нужно;
5. `interface.request.request_all_scores(defaults)`;
6. `storage.add_movie(meta_payload=..., pool_candidate=..., print_message=False)`;
7. `add_dataset_record()` сохраняет запись;
8. после успеха связанный кандидат удаляется из общего пула.

### 3. Top prediction из общего пула

1. `interface.interface_funcs.show_global_candidate_top()`
2. загрузка всех кандидатов;
3. runtime-фильтр через `filter_saved_candidates_for_prediction()`;
4. ready-filter через `is_candidate_ready_for_prediction()`;
5. ranking через `rank_candidates_by_predict()`.

Поддерживаемые runtime-фильтры:

- `criteria_name`;
- `source`;
- `country`;
- `year_min`, `year_max`;
- `include_genres`, `exclude_genres`;
- `min_kp_score`, `min_kp_votes`;
- `min_imdb_score`, `min_imdb_votes`;
- `min_tmdb_score`, `min_tmdb_votes`;
- `only_complete`.

Если есть incomplete-кандидаты, UI показывает:

- сколько их пропущено;
- preview первых incomplete;
- подсказку про `Добрать KP для неполных кандидатов`.

### 4. Retry KP для incomplete-кандидатов

1. `interface.interface_funcs.retry_kp_for_incomplete_candidates()`
2. выбор scope: все или конкретный `criteria_name`;
3. preview кандидатов на добор;
4. подтверждение перед API-запросами;
5. запуск `candidate_pool.retry_kp_enrichment_for_pool(...)`.

### 5. TMDb candidate pool v1

1. `interface.interface_funcs.run_tmdb_candidate_pool_flow()`
2. выбор страны, режима и обычного запуска или test-run;
3. ввод ранних Discover-фильтров:
   - `year_min`;
   - `year_max`;
   - `min_tmdb_score`;
   - `min_tmdb_votes`;
4. `data_work.tmdb_candidate_pool.build_candidate_pool(...)`;
5. сохранение отдельного TMDb result;
6. при необходимости импорт через `import_tmdb_result_to_common_pool_flow()`.

## Где менять поведение

- меню и маршрутизацию: `interface/ui.py`, `interface/global_menu.py`
- prompts и UI-сценарии: `interface/interface_funcs.py`, `interface/request.py`
- правила сохранения записи: `data_work/storage_movie.py`, `data_work/dataset_records.py`
- defaults и перенос кандидата: `data_work/title_resolve.py`
- общий candidate pool: `data_work/candidate_pool.py`
- TMDb pipeline: `integrations/api_tmdb.py`, `data_work/tmdb_candidate_pool.py`
- SQL-поиск: `data_work/sql_search.py`
- обучение и предикт: `model_work/model.py`, `model_work/linear_regression_train.py`

## Данные и артефакты

- `C:/DATA/movies-learn/dataset.json` - dataset.
- `C:/META/meta-movies-learn/meta_data.json` - meta.
- `C:/DATA/movies-learn/weights.json` - веса модели.
- `C:/DATA/movies-learn/candidate_pool.json` - общий candidate pool.
- `data/candidate_pool/*.json|*.csv` - TMDb candidate pool result.
- `data/cache/tmdb/` - локальный кэш TMDb Discover/Details.
- `datasets/dataset_sql_light/imdb_light.sqlite3` - локальная IMDb SQLite база.

## Проверки

Базовые:

```powershell
py tests\test.py
py -c "import tests.test_encoding as t; t.run_tests()"
```

Для меню `candidate_pool` полезно отдельно проверять:

- возврат по `0` из каждого подменю;
- старый legacy flow;
- TMDb flow;
- import TMDb result;
- top prediction с runtime-фильтрами;
- retry KP с preview и подтверждением;
- перенос кандидата в dataset через форму.
