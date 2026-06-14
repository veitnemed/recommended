# Карта проекта

`Terminal Movies Learn` — консольная лаборатория для личной модели вкуса. Пользователь собирает свои оценки, программа подтягивает данные из API, хранит вайб-теги и жанровую разметку, обучает модель и отдельно поддерживает общий пул кандидатов.

## Быстрый вход

- [main.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/main.py:1) — точка входа.
- [README.md](/d:/VS%20PROJJJ/vscode%20projects/recommended/README.md:1) — пользовательское описание.
- [PROJECT_MAP.md](/d:/VS%20PROJJJ/vscode%20projects/recommended/PROJECT_MAP.md:1) — эта карта.
- [requirements.txt](/d:/VS%20PROJJJ/vscode%20projects/recommended/requirements.txt:1) — зависимости.

Запуск:

```powershell
py main.py
```

## Основной поток

1. `main.py` вызывает `storage.init_all_dates()`.
2. Инициализация создаёт рабочие JSON-файлы: датасет, meta, веса, критерии пула, общий пул кандидатов и API-лог.
3. `interface.menu_state.get_menu_state()` загружает датасет, веса, размер датасета и текущий `MAE`.
4. `interface.ui` печатает главное меню.
5. `interface.request` собирает и валидирует пользовательский ввод.
6. `interface.global_menu` переводит пользователя в нужный раздел.
7. `data_work` отвечает за хранение, Excel, backup, жанры, TST, переименование записи и общий пул кандидатов.
8. `model_work` считает признаки, прогнозы, ошибки и обучение.

## Текущее меню

### Главное

1. `Данные`
2. `Обучение`
3. `Модель`
4. `Дополнительно`
5. `Пулл кандидатов`
6. `Выгрузить отчёт`

### Данные

- открыть Excel
- загрузить Excel
- добавить запись
- показать мои оценки
- данные о датасете
- прочитать оценки TST
- бэкап
- переименовать запись

### Обучение

- быстрое обучение
- случайная оптимизация
- многошаговый координатный поиск
- гибридная оптимизация
- линейная регрессия
- параметры обучения

### Модель

- признаки:
  - вайб-тэги
  - жанровая разметка
  - показать веса модели
  - сбросить веса модели
- тесты эффективности
- сделать прогноз

### Дополнительно

- просмотр API признаков
- показать все жанры датасета
- показать влияние голосов
- пересчитать raw оценки

### Пулл кандидатов

- собрать пулл кандидатов
- посмотреть пуллы кандидатов
- собрать топ из общего пула
- удалить пулл
- показать подозрительные дубли

Сверху подменю выводится текущее число кандидатов в общем пуле.

## Папки и роли

### `config/`

Центр схем, динамических каталогов и констант.

- [config/constant.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/config/constant.py:1) — пути, списки признаков, `bias`, пути к JSON кандидатов и API-логу.
- [config/scheme.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/config/scheme.py:1) — схема секций `main_info`, `raw_scores`, `tags_vibe`, `genre`.
- [config/tags.json](/d:/VS%20PROJJJ/vscode%20projects/recommended/config/tags.json:1) — каталог вайб-тегов.
- [config/genre_tags.json](/d:/VS%20PROJJJ/vscode%20projects/recommended/config/genre_tags.json:1) — каталог жанровых признаков.
- [config/genre_tags.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/config/genre_tags.py:1) — генерация, нормализация и миграция жанровых ключей в стиль `has_*`.

### `core/`

Базовая логика без привязки к меню.

- [core/valid.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/core/valid.py:1) — валидация ввода.
- [core/format_score.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/core/format_score.py:1) — преобразование рейтингов, голосов и тегов в признаки модели.

### `data_work/`

Хранение и подготовка данных.

- [data_work/storage.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/storage.py:1) — фасад над `storage_*` и `candidate_pool`.
- [data_work/storage_files.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/storage_files.py:1) — файлы, каталоги, backup, стартовая инициализация.
- [data_work/storage_data.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/storage_data.py:1) — dataset, meta, weights, безопасное переименование записи.
- [data_work/storage_movie.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/storage_movie.py:1) — добавление записи, валидация и сбор из Excel.
- [data_work/storage_normalize.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/storage_normalize.py:1) — нормализация raw, vibe и genre.
- [data_work/excel_work.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/excel_work.py:1) — Excel-экспорт и импорт.
- [data_work/tags_work.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/tags_work.py:1) — операции с вайб-тегами.
- [data_work/genre_import.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/genre_import.py:1) — жанровая разметка из API с подтверждением.
- [data_work/genre_stats.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/genre_stats.py:1) — сводка жанров датасета через API.
- [data_work/dataset_stats.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/dataset_stats.py:1) — статистика датасета.
- [data_work/tst_scores.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/tst_scores.py:1) — импорт оценок из TST.
- [data_work/candidate_pool.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/data_work/candidate_pool.py:1) — критерии подбора, общий пул кандидатов, дедупликация, фильтрация просмотренного, удаление пуллов, диагностика подозрительных дублей и сбор признаков для топа без вайб-тегов.

### `interface/`

Консольный UI.

- [interface/ui.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/ui.py:1) — экраны и меню.
- [interface/request.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/request.py:1) — универсальный ввод, API-defaults, подтверждение или ручная правка жанров при добавлении.
- [interface/global_menu.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/global_menu.py:1) — маршрутизация по меню, включая отдельный раздел кандидатов.
- [interface/interface_funcs.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/interface_funcs.py:1) — действия меню.
- [interface/tags_menu.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/tags_menu.py:1) — управление вайб-тегами.
- [interface/backup_menu.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/backup_menu.py:1) — backup и восстановление.
- [interface/train_params.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/interface/train_params.py:1) — параметры эвристических режимов обучения.

### `model_work/`

Модель, обучение и диагностика.

- [model_work/model.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/model_work/model.py:1) — ядро модели: `bias`, признаки, прогноз, ошибки, эвристические алгоритмы.
- [model_work/train_modes.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/model_work/train_modes.py:1) — пользовательские режимы обучения поверх эвристик.
- [model_work/linear_regression_train.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/model_work/linear_regression_train.py:1) — `Ridge`, `Lasso`, `ElasticNet`, `SGDRegressor (MAE)`, `scipy minimize (MAE)`.
- [model_work/train_report.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/model_work/train_report.py:1) — текстовый отчёт по обучению.
- [model_work/noise_experiment.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/model_work/noise_experiment.py:1) — устойчивость к шуму.

### `integrations/`

Внешние источники данных.

- [integrations/api.py](/d:/VS%20PROJJJ/vscode%20projects/recommended/integrations/api.py:1) — поиск сериала, чтение рейтингов, голосов, стран, жанров, описаний, подбор кандидатов по фильтрам и запись API-лога.

## Признаки модели

Текущий вектор признаков собирается так:

1. `bias = 1.0`
2. `computed_scores` из `raw_scores`
3. `tags_vibe`
4. `genre`

`genre` динамический:

- известные жанры мапятся в осмысленные `has_*`;
- новые жанры тоже приводятся к стилю `has_english_name`;
- старые ключи `genre_*` мигрируют при чтении.

## Общий пул кандидатов

Главная идея:

- есть один общий `candidate_pool.json`;
- он считается единственным источником правды;
- новые наборы критериев добавляют записи именно туда;
- отдельный просмотр по набору критериев — это просто выборка по `criteria_name`;
- общий пул автоматически очищается от объектов, уже попавших в основной датасет.

### Дедупликация

Пул схлопывает дубли по нормализованному названию и году.

Дополнительно используется мягкое сравнение похожих названий:

- нижний регистр;
- `ё -> е`;
- удаление пунктуации;
- схлопывание пробелов;
- сравнение compact-строк без пробелов;
- similarity ratio;
- сравнение набора слов.

Если найдено несколько дублей, остаётся лучший вариант по:

- `kp_score`
- `kp_votes`
- `imdb_score`
- `imdb_votes`

## Топ из общего пула

Раздел `Пулл кандидатов -> Собрать топ из общего пула`:

- читает всех кандидатов из общего пула;
- собирает признаки без вайб-тегов;
- использует текущие веса модели;
- ранжирует по предикту;
- печатает `Название (год): предикт`.

## Добавление новой записи

Поток ручного добавления:

1. поиск сериала через API;
2. показ названия, года, страны и краткого описания;
3. показ жанров из API;
4. подтверждение жанров или ручная правка;
5. ввод оценки, вайб-тегов и жанровой разметки;
6. сохранение записи;
7. автоматическая очистка общего пула кандидатов от этого сериала.

## API-лог

Все запросы к API пишутся в:

`C:/DATA/movies-learn/api_requests.log`

Записываются события:

- `api_request_start`
- `api_request_attempt`
- `api_request_success`
- `api_request_http_error`
- `api_request_network_error`
- `api_request_timeout`
- `api_request_os_error`
- `api_request_failed`
- `api_json_ok`
- `api_bad_request_parameters`

## Где чаще всего менять поведение

- поменять меню: `interface/ui.py`, `interface/global_menu.py`
- поменять схему данных: `config/scheme.py`, затем проверить `storage_normalize.py`
- поменять правила жанров: `config/genre_tags.py`
- поменять формулу признаков: `core/format_score.py`, `model_work/model.py`
- поменять логику общего пула: `data_work/candidate_pool.py`
- поменять безопасное переименование записи: `data_work/storage_data.py`
- поменять API-интеграцию и логирование: `integrations/api.py`
- поменять эвристическое обучение: `model_work/model.py`, `model_work/train_modes.py`
- поменять линейное обучение: `model_work/linear_regression_train.py`
- поменять Excel: `data_work/excel_work.py`

## Проверки

Базовые:

```powershell
py tests\test.py
py -c "import tests.test_encoding as t; t.run_tests()"
```

После заметных изменений особенно полезно проверить:

- ручное добавление записи;
- переименование записи;
- Excel-экспорт и импорт;
- жанровую разметку;
- сбор кандидатов при рабочем API;
- удаление пулла;
- просмотр по конкретному набору критериев;
- топ из общего пула;
- диагностику подозрительных дублей;
- обучение и сохранение весов;
- восстановление из backup.
