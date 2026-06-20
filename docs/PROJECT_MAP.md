# Карта проекта

`Terminal Movies Learn` - консольная система для ведения личного dataset оценок и обучения простой рекомендательной модели.

Ниже карта проекта в текущем состоянии после рефакторинга слоёв. Целевая архитектура и правила зависимостей описаны в [ARCHITECTURE_TARGET.md](ARCHITECTURE_TARGET.md), правила добавления нового функционала - в [add_functions.md](add_functions.md).

## Быстрый вход

- [main.py](../main.py) - вход в приложение.
- [README.md](README.md) - пользовательское описание.
- [PROJECT_MAP.md](PROJECT_MAP.md) - карта проекта.
- [add_functions.md](add_functions.md) - правила добавления/изменения функционала.
- [ADD_RECORD_RULES.md](ADD_RECORD_RULES.md) - контракт добавления и изменения записей.

## Слои и направление зависимостей

```
common  <-  config  <-  storage  <-  dataset / apis  <-  candidates / model  <-  ui/console
```

Нижние слои не знают о верхних. Запреты: `model` не импортирует `ui`; `dataset` не импортирует `ui`; `apis` не импортирует dataset/candidates/model/ui; `candidates` не вызывает `print()/input()`; `config`/`common` не зависят от верхних слоёв; UI не сохраняет данные и не вызывает API напрямую - только через сервисы.

## Основной runtime-поток

1. `main.py` инициализирует storage и регистрирует progress-reporter для candidates.
2. `ui.console.menu_state` собирает текущий state: dataset, weights, счётчики, ошибки модели.
3. `ui.console.ui` печатает меню.
4. `ui.console.global_menu` маршрутизирует пользователя по разделам.
5. `ui.console.interface_funcs` запускает конкретные сценарии UI (input/print, prompts, подтверждения).
6. Для candidate pool console flows UI вызывает `candidates/service.py` (facade), который делегирует в core.
7. `storage` / `dataset` / `candidates` выполняют работу с данными.
8. `apis` отдаёт внешние данные (KP, TMDb, IMDb SQL).
9. `model` строит признаки, считает предикт, ошибки и обучение.

## Папки и роли

### `common/`

Чистые утилиты без привязки к данным и меню.

- [common/valid.py](../common/valid.py) - валидация ввода и payload.
- [common/format_score.py](../common/format_score.py) - преобразование `raw_scores` в вычисляемые признаки.

### `config/`

Базовые константы, схемы и каталоги признаков.

- [config/constant.py](../config/constant.py) - пути, названия секций, наборы признаков.
- [config/scheme.py](../config/scheme.py) - схема `main_info`, `raw_scores`, `tags_vibe`, `genre`.
- [config/tags_work.py](../config/tags_work.py) - чистое чтение/валидация каталога тегов `config/tags.json`.
- [config/tags.json](../config/tags.json) - vibe-теги.
- [config/genre_tags.json](../config/genre_tags.json) - жанровые признаки.
- [config/genre_tags.py](../config/genre_tags.py) - нормализация и генерация `has_*` жанров.

### `storage/`

Низкоуровневое файловое хранилище. Знает, как сохранить файл, но не решает, зачем.

- [storage/data.py](../storage/data.py) - dataset/meta/weights/metrics: load/save/init, rename title, LOO MAE.
- [storage/files.py](../storage/files.py) - файлы, каталоги, backup, стартовая инициализация.
- [storage/normalize.py](../storage/normalize.py) - нормализация `main_info`, `raw_scores`, `tags_vibe`, `genre`.

### `dataset/`

Пользовательский dataset: записи, meta, Excel, статистика, теги, резолв тайтлов.

- [dataset/dataset_records.py](../dataset/dataset_records.py) - центральный add/update service.
- [dataset/storage_movie.py](../dataset/storage_movie.py) - `add_movie()`, Excel row -> movie payload, пересчёт computed.
- [dataset/excel_work.py](../dataset/excel_work.py) - Excel export/import.
- [dataset/dataset_stats.py](../dataset/dataset_stats.py) - сводка dataset.
- [dataset/genre_import.py](../dataset/genre_import.py) - массовая жанровая разметка.
- [dataset/genre_stats.py](../dataset/genre_stats.py) - просмотр жанров dataset.
- [dataset/tags_work.py](../dataset/tags_work.py) - мутации тегов в данных (`add_tag`, `delete_tag`, `delete_all_tags`, backup).
- [dataset/title_resolve.py](../dataset/title_resolve.py) - сбор defaults из SQL/API/TMDb, payload переноса кандидата, сервисные обёртки над apis.

### `candidates/`

Пулы кандидатов к просмотру. Core-модули не вызывают `print()/input()` — прогресс отдаётся наверх через reporter.

**Console facade (после J1–J5):**

- [candidates/service.py](../candidates/service.py) — тонкий facade между `ui/console` и candidates core для console flows. Не содержит `input()/print()`, не должен разрастаться в god-module: orchestration + делегирование, без model scoring.

**Core:**

- [candidates/candidate_pool.py](../candidates/candidate_pool.py) — общий candidate pool: storage, filters, dedupe, collect (KP API), retry KP, ranking helpers, delete, suspicious duplicates.
- [candidates/import_tmdb.py](../candidates/import_tmdb.py) — import saved TMDb result JSON в общий pool + merge criteria metadata.
- [candidates/tmdb_candidate_pool.py](../candidates/tmdb_candidate_pool.py) — TMDb candidate pool v1 (discover/details/build/save); `set_progress_reporter()`, `build_summary_lines()`, genre diagnostics.
- [candidates/kp_enrichment.py](../candidates/kp_enrichment.py) — shared KP lookup/enrichment для pool и TMDb build.
- [candidates/schema.py](../candidates/schema.py) — нормализация candidate record, completeness, readiness.
- [candidates/keys.py](../candidates/keys.py) — `pool_entry_key`, `title_identity_key`, criteria defaults.
- [candidates/genres.py](../candidates/genres.py) — runtime genre aliases для фильтров (JSON не мигрируется).

**Через `candidates/service.py` (console):** pool read/stats, top prediction read/filter/defaults, contributions readiness split, mark watched write, retry KP, manual TMDb import, TMDb build/save/auto-import, delete criteria, suspicious duplicates view.

**Намеренно вне service:** model scoring/ranking (`rank_candidates_by_predict`, contribution reports), legacy `collect_candidates` (KP API), `candidate_pool_ui.py` (criteria input), TMDb genre diagnostics, standalone CLI (`build_candidate_pool.py`).

**Инварианты pool:**

- `pool_entry_key = criteria_name|normalized_title|year`
- `title_identity_key = normalized_title|year` (watched remove / import skip)
- read-path не purge watched; write-path purge watched
- genre filters — runtime-only; `candidate_criteria` filters — defaults для top prediction, pool не пересобирают

### `apis/`

Внешние источники данных. Только получают данные и возвращают результат наверх.

- [apis/kp_api.py](../apis/kp_api.py) - KP/внешний API для рейтингов, описаний и candidate-поиска.
- [apis/tmdb_api.py](../apis/tmdb_api.py) - TMDb Discover, Details и нормализация ответов.
- [apis/imdb_sql.py](../apis/imdb_sql.py) - поиск в локальной IMDb SQLite базе.

### `model/`

Модель и обучение. Не импортирует `ui`.

- [model/model.py](../model/model.py) - предикт, MAE, feature logic, `reset_weights()`, save-if-improved.
- [model/linear_regression_train.py](../model/linear_regression_train.py) - линейное обучение, LOO, метрики, отчёты.
- [model/train_report.py](../model/train_report.py) - отчёт по модели.
- [model/noise_experiment.py](../model/noise_experiment.py) - шумовая устойчивость (чистая логика).

### `ui/`

Интерфейсные слои приложения. Сейчас реализован консольный UI, GUI оставлен как место под будущий интерфейс.

- [ui/console/console_app.py](../ui/console/console_app.py) - запуск консольного приложения.
- [ui/console/ui.py](../ui/console/ui.py) - печать экранов и меню.
- [ui/console/global_menu.py](../ui/console/global_menu.py) - циклы меню и переходы между разделами.
- [ui/console/interface_funcs.py](../ui/console/interface_funcs.py) - UI-оркестрация сценариев (input/print, prompts); candidate pool flows → `candidates/service.py`.
- [ui/console/request.py](../ui/console/request.py) - формы, prompts, сбор `movie_request`.
- [ui/console/title_presenters.py](../ui/console/title_presenters.py) - карточки SQL/API/defaults.
- [ui/console/candidate_pool_ui.py](../ui/console/candidate_pool_ui.py) - input-layer для criteria; напрямую в `candidate_pool`, не через service.
- [ui/console/tags_menu.py](../ui/console/tags_menu.py) - управление vibe-тегами.
- [ui/console/backup_menu.py](../ui/console/backup_menu.py) - backup и restore.
- [ui/console/train_menu.py](../ui/console/train_menu.py) - интерактивные режимы обучения и шумовой эксперимент.
- [ui/console/rating_comparison.py](../ui/console/rating_comparison.py) - попарное сравнение оценок.
- [ui/console/menu_state.py](../ui/console/menu_state.py) - сбор состояния меню.
- [ui/gui/](../ui/gui) - место под будущий GUI.

### `tests/`

Тесты проекта. Точка входа - [tests/test.py](../tests/test.py).

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

Пункт `Собрать новый пулл` сразу запускает основной сценарий:

- `TMDb -> IMDb SQL -> KP API`

Подменю `Управление пуллами`:

- `Удалить пулл`
- `Фильтрация / редактирование критериев`
- `Импортировать TMDb result в общий пул`

Подменю `Диагностика и обслуживание`:

- `Показать подозрительные дубли`
- `Добрать KP для неполных кандидатов`
- `Показать вклады для кандидатов`
- `Показать TMDb жанры по dataset`

## Ключевые потоки

### 1. Ручное добавление записи

1. `ui.console.interface_funcs.request_object()`
2. `ui.console.request.request_api_defaults(confirm_genres=True)`
3. `dataset.title_resolve.resolve_title_for_training()`
4. `ui.console.request.request_all_scores(defaults)`
5. `dataset.storage_movie.add_movie(print_message=False)`
6. `dataset.dataset_records.add_dataset_record()`

UI печатает финальное сообщение сам. Service возвращает `AddRecordResult`.

### 2. Перенос кандидата из пула в dataset

1. `ui.console.interface_funcs.mark_candidate_as_watched()`
2. выбор `criteria_name` и кандидата через `candidate_pool_ui` + `candidates.service.get_mark_watched_view()`;
3. `dataset.title_resolve.build_candidate_transfer_payload(candidate)`;
4. предупреждение для incomplete через `candidates.service.is_pool_candidate_incomplete()`;
5. `ui.console.request.request_all_scores(defaults)`;
6. `dataset.storage_movie.add_movie(meta_payload=..., pool_candidate=..., print_message=False)`;
7. `add_dataset_record()` сохраняет запись;
8. `dataset.dataset_records._cleanup_candidate_pool()` → `candidates.service.mark_candidate_watched_in_pool()` удаляет кандидата из общего пула (fuzzy by title+year).

### 3. Top prediction из общего пула

1. `ui.console.interface_funcs.show_global_candidate_top()`
2. read/filter через `candidates.service` (`get_global_top_prediction_view`, `get_prediction_filter_view`, `get_prediction_filter_defaults_view`);
3. runtime-фильтр и ready/incomplete split — в service (делегирует в `candidate_pool`);
4. ranking через `candidate_pool.rank_candidates_by_predict()` — **намеренно в UI/core**, не в service.

### 4. Retry KP для incomplete-кандидатов

1. `ui.console.interface_funcs.retry_kp_for_incomplete_candidates()`
2. preview через `candidates.service.get_retry_kp_view()`;
3. выбор scope и подтверждение — в UI;
4. write через `candidates.service.retry_kp_enrichment_in_pool()` → `candidate_pool.retry_kp_enrichment_for_pool()`.

### 5. TMDb candidate pool v1

1. `ui.console.interface_funcs.run_tmdb_candidate_pool_flow()`
2. выбор страны, режима, `criteria_name`, Discover-фильтров — в UI;
3. build/save через `candidates.service` (`build_tmdb_candidate_pool`, `save_tmdb_build_result`);
4. прогресс TMDb — через `set_progress_reporter` (регистрируется в `console_app.py`), итог — `build_summary_lines`;
5. после обычного save UI предлагает auto-import → `maybe_auto_import_tmdb_result()` → `candidates.service.import_tmdb_result_to_pool()`;
6. ручной import saved result — `import_tmdb_result_to_common_pool_flow()` через тот же service import path.

### 5a. Manual TMDb result import

1. `ui.console.interface_funcs.import_tmdb_result_to_common_pool_flow()`
2. выбор result file, preview, `criteria_name`, подтверждение — в UI;
3. import через `candidates.service.import_tmdb_result_to_pool()` → `import_tmdb.import_tmdb_result_to_common_pool()`.

### 5b. Удаление criteria / suspicious duplicates

- delete: `delete_candidate_pool()` → `candidates.service.delete_candidate_pool_criteria()`
- duplicates: `show_suspicious_candidate_duplicates()` → `candidates.service.get_suspicious_duplicates_view()`

### 5c. Contributions (readiness gate через service, scoring в UI)

1. `show_candidate_contributions()` — split ready/incomplete через `get_contribution_ready_view()`;
2. отчёты вкладов — `candidate_pool.build_contribution_reports_for_ready_candidates()` (model scoring, вне service).

### 6. Обучение модели

- линейные режимы и шумовой эксперимент: `ui.console.train_menu.train_linear_model()`, `ui.console.train_menu.run_noise_sensitivity()` (UI-обёртки над `model.linear_regression_train` и `model.noise_experiment`);
- LOO-обучение: `model.linear_regression_train.run_loo_training()`;
- сброс весов: `ui.console.interface_funcs.reset_weights_model()` -> `model.reset_weights()`.

## Где менять поведение

- меню и маршрутизацию: `ui/console/ui.py`, `ui/console/global_menu.py`
- prompts и UI-сценарии: `ui/console/interface_funcs.py`, `ui/console/request.py`, `ui/console/train_menu.py`
- console facade candidate pool: `candidates/service.py` (новые console flows добавлять сюда, не раздувать)
- criteria input (forms): `ui/console/candidate_pool_ui.py`
- правила сохранения записи: `dataset/storage_movie.py`, `dataset/dataset_records.py`
- defaults и перенос кандидата: `dataset/title_resolve.py`
- core candidate pool (алгоритмы, keys, purge): `candidates/candidate_pool.py`, `candidates/schema.py`, `candidates/keys.py`
- TMDb import merge: `candidates/import_tmdb.py`
- TMDb build pipeline: `apis/tmdb_api.py`, `candidates/tmdb_candidate_pool.py`
- SQL-поиск: `apis/imdb_sql.py`
- обучение и предикт: `model/model.py`, `model/linear_regression_train.py`
- низкоуровневое сохранение: `storage/data.py`, `storage/files.py`

## Данные и артефакты

- `C:/DATA/movies-learn/dataset.json` - dataset.
- `C:/META/meta-movies-learn/meta_data.json` - meta.
- `C:/DATA/movies-learn/weights.json` - веса модели.
- `C:/DATA/movies-learn/candidate_pool.json` - общий candidate pool.
- `C:/DATA/movies-learn/candidate_criteria.json` - сохранённые criteria (filters + TMDb metadata).
- `data/candidate_pool/*.json|*.csv` - TMDb candidate pool result.
- `data/diagnostics/tmdb_genre_distribution_*.json` - диагностические отчёты TMDb-жанров по dataset.
- `data/cache/tmdb/` - локальный кэш TMDb Discover/Details.
- `datasets/dataset_sql_light/imdb_light.sqlite3` - локальная IMDb SQLite база.

## Проверки

```powershell
py -m compileall common config storage dataset candidates model apis ui tests
py tests\test.py
py main.py
```

Актуально для TMDb flow: после обычного build и сохранения snapshot UI сразу предлагает auto-import этого result в общий candidate pool. Для `test-run` auto-import не предлагается, а ручной import остаётся доступен через меню управления пулами.

Для меню `candidate_pool` полезно отдельно проверять: возврат по `0` из подменю, TMDb flow, import TMDb result, top prediction с runtime-фильтрами, retry KP с preview, перенос кандидата в dataset через форму.
