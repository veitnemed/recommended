# Карта проекта

`Series List` - локальный Python-проект для ведения watched-базы и поиска сериалов/тайтлов через candidate pool, TMDb, IMDb SQL и KP enrichment.

Старая ML-модель перенесена в `archive/legacy/model/` и не является активной частью runtime.

## Быстрый вход

- [README.md](README.md) - пользовательское описание проекта.
- [STRUCTURE_PLAN.md](STRUCTURE_PLAN.md) - план структурной чистки.
- [DATA_STORAGE_PLAN.md](DATA_STORAGE_PLAN.md) - структура локального хранения данных.
- [add_functions.md](add_functions.md) - правила добавления и изменения функционала.
- [ADD_RECORD_RULES.md](ADD_RECORD_RULES.md) - контракт добавления и изменения записей.
- [DESKTOP_STYLE_CONTRACT.md](DESKTOP_STYLE_CONTRACT.md) - визуальный контракт desktop GUI.
- [DESKTOP_GUI_ROADMAP.md](DESKTOP_GUI_ROADMAP.md) - roadmap desktop GUI.

## Слои

```text
common <- config <- storage <- dataset / apis <- candidates <- ui
```

Правила:

- нижние слои не импортируют UI;
- `apis` только получают внешние данные и не пишут в dataset/pool;
- `candidates` не вызывает `input()` и `print()`, прогресс отдает наверх;
- UI не пишет JSON напрямую, а вызывает сервисы.

## Runtime-поток

1. `start_console.py` или `start_app.py` запускает приложение.
2. `storage` инициализирует базовые файлы и каталоги.
3. `ui.console` или `desktop` собирает пользовательский сценарий.
4. `dataset` работает с watched-записями, meta, жанрами, тегами и Excel.
5. `candidates` строит и фильтрует candidate pool.
6. `apis` отдает данные из KP, TMDb и IMDb SQL.
7. `posters` синхронизирует poster-cache и локальные изображения.

## Папки

### `app/`

Входные сценарии приложения и общая инициализация.

### `desktop/`

PyQt desktop GUI для watched-базы, карточки тайтла, поиска и аналитики.

- [desktop/app.py](../desktop/app.py) - главное окно.
- [desktop/watched_view.py](../desktop/watched_view.py) - watched-список и карточка выбранного тайтла.
- [desktop/candidate_filters_view.py](../desktop/candidate_filters_view.py) - runtime-фильтры общего pool.
- [desktop/candidate_list_view.py](../desktop/candidate_list_view.py) - sorted list и read-only карточка кандидата.
- [desktop/candidate_search_session.py](../desktop/candidate_search_session.py) - shared filter/sort state.
- [desktop/analytics_view.py](../desktop/analytics_view.py) - read-only аналитика.
- [desktop/theme.py](../desktop/theme.py) - QSS и style tokens.

### `ui/console/`

Консольный интерфейс, меню, prompts и сценарии пользователя.

- [ui/console/console_app.py](../ui/console/console_app.py) - запуск console UI.
- [ui/console/ui.py](../ui/console/ui.py) - отрисовка меню.
- [ui/console/global_menu.py](../ui/console/global_menu.py) - маршрутизация пунктов меню.
- [ui/console/interface_funcs.py](../ui/console/interface_funcs.py) - UI-сценарии.
- [ui/console/request.py](../ui/console/request.py) - формы и prompts.
- [ui/console/search_menu.py](../ui/console/search_menu.py) - поиск по candidate pool.
- [ui/console/candidate_pool_ui.py](../ui/console/candidate_pool_ui.py) - настройки сбора и defaults общего pool.
- [ui/console/tags_menu.py](../ui/console/tags_menu.py) - управление vibe-тегами.
- [ui/console/backup_menu.py](../ui/console/backup_menu.py) - backup и restore.

### `dataset/`

Watched dataset: добавление, обновление, удаление, meta, Excel, статистика, жанры и теги.

- [dataset/dataset_records.py](../dataset/dataset_records.py) - центральный add/update service.
- [dataset/storage_movie.py](../dataset/storage_movie.py) - сбор payload и сохранение записи.
- [dataset/delete_record.py](../dataset/delete_record.py) - безопасное удаление watched-записи.
- [dataset/title_resolve.py](../dataset/title_resolve.py) - defaults из SQL/API/TMDb и перенос кандидата.
- [dataset/dataset_stats.py](../dataset/dataset_stats.py) - сводка dataset.
- [dataset/genre_stats.py](../dataset/genre_stats.py) - просмотр жанров.
- [dataset/tags_work.py](../dataset/tags_work.py) - мутации тегов.

### `candidates/`

Поиск и обслуживание кандидатов к просмотру.

- [candidates/service.py](../candidates/service.py) - facade для UI.
- [candidates/candidate_pool.py](../candidates/candidate_pool.py) - общий candidate pool, фильтры, dedupe, retry KP.
- [candidates/tmdb_candidate_pool.py](../candidates/tmdb_candidate_pool.py) - TMDb Discover/Details build.
- [candidates/import_tmdb.py](../candidates/import_tmdb.py) - импорт saved TMDb result в общий pool.
- [candidates/kp_enrichment.py](../candidates/kp_enrichment.py) - KP lookup/enrichment.
- [candidates/schema.py](../candidates/schema.py) - нормализация candidate record.
- [candidates/keys.py](../candidates/keys.py) - ключи pool/dedupe.
- [candidates/genres.py](../candidates/genres.py) - runtime genre aliases.

Инварианты pool:

- один общий pool; `criteria_name` в записи = `"pool"`;
- `pool_entry_key = normalized_title|year`;
- `title_identity_key = normalized_title|year`;
- stats показывают `unique_total` и, при наличии, лишние записи в JSON;
- read-path не удаляет watched;
- write-path очищает watched-кандидатов из pool;
- runtime-фильтры не пересобирают сохраненный pool;
- явная очистка дублей: `clean_common_pool_duplicates()` (console: Управление pool).

### `apis/`

Внешние источники данных.

- [apis/kp_api.py](../apis/kp_api.py) - KP/внешний API.
- [apis/tmdb_api.py](../apis/tmdb_api.py) - TMDb Discover/Details.
- [apis/imdb_sql.py](../apis/imdb_sql.py) - локальная IMDb SQLite база.
- [apis/sql_title_aliases.json](../apis/sql_title_aliases.json) - alias-справочник для SQL-поиска.

### `storage/`

Низкоуровневое хранение и нормализация.

- [storage/data.py](../storage/data.py) - dataset/meta: load/save/init, rename title.
- [storage/files.py](../storage/files.py) - файлы, каталоги, backup.
- [storage/normalize.py](../storage/normalize.py) - нормализация `main_info`, `raw_scores`, `tags_vibe`, `genre`.

### `config/`

Константы, схемы и справочники.

- [config/constant.py](../config/constant.py) - пути и runtime-константы.
- [config/scheme.py](../config/scheme.py) - схема полей.
- [config/tags.json](../config/tags.json) - vibe-теги.
- [config/genre_tags.json](../config/genre_tags.json) - жанровые признаки.
- [config/tags_work.py](../config/tags_work.py) - чтение/валидация тегов.
- [config/genre_tags.py](../config/genre_tags.py) - чтение/валидация жанров.

### `posters/`

Poster-cache, загрузка и синхронизация постеров.

### `web/`

Read-only экспорт watched/add-title карточек.

### `scripts/`

Ручные diagnostic/build utilities.

### `tests/`

Активный pytest-набор.

### `archive/legacy/`

Старый код, оставленный только для истории. Runtime его не импортирует.

## Основные сценарии

### Добавление watched-записи

1. UI собирает title/year/user_score/raw_scores/genres/tags.
2. `dataset.title_resolve` подставляет defaults из доступных источников.
3. `dataset.storage_movie.add_movie()` собирает payload.
4. `dataset.dataset_records.add_dataset_record()` сохраняет dataset/meta и запускает связанные side effects.

### Поиск кандидатов

1. Пользователь задает runtime-фильтр (defaults из `criteria.json`, запись `"pool"`).
2. `candidates.service` готовит view для UI.
3. `candidates.candidate_pool` читает общий pool и применяет фильтры.
4. Incomplete-кандидаты можно добрать через KP enrichment.

### TMDb candidate pool

1. UI выбирает страну, режим и Discover-фильтры.
2. `tmdb_candidate_pool` получает TMDb Discover/Details.
3. IMDb SQL и KP enrichment дополняют данные.
4. Результат сохраняется в `data/exports/candidate_pool/`.
5. Saved result импортируется/мерджится в общий pool (auto-import или Управление pool).

### Перенос кандидата в watched

1. UI выбирает кандидата из pool.
2. `dataset.title_resolve.build_candidate_transfer_payload()` готовит defaults.
3. Пользователь подтверждает/редактирует форму.
4. `dataset.storage_movie.add_movie()` сохраняет запись.
5. `candidates.service.mark_candidate_watched_in_pool()` удаляет watched-кандидата из общего pool.

## Данные и артефакты

- `data/watched/titles.json` - watched dataset.
- `data/watched/meta.json` - meta/enrichment.
- `data/candidates/pool.json` - общий candidate pool.
- `data/candidates/criteria.json` - defaults сбора и search-фильтров (запись `"pool"`).
- `data/exports/candidate_pool/*.json|*.csv` - generated TMDb candidate pool results.
- `data/diagnostics/*.json` - generated diagnostics.
- `data/cache/` - локальные кэши.
- `datasets/dataset_sql_light/imdb_light.sqlite3` - локальная IMDb SQLite база.

Активные JSON в репозитории:

- `config/tags.json`;
- `config/genre_tags.json`;
- `apis/sql_title_aliases.json`.

## Проверки

```powershell
py -m compileall app apis candidates common config dataset desktop posters scripts storage ui web tests
py -m pytest
```
