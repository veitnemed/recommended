# Agent Notes

Короткий контекст проекта, чтобы не тратить токены на повторную разведку.

## Проект

Рекомендательная система сериалов/фильмов на Python. Основной UI консольный, вход через `main.py`.

Важные папки:

- `interface/` - консольные меню и действия UI.
- `data_work/` - работа с датасетом, SQL, candidate pools.
- `integrations/` - внешние API.
- `datasets/dataset_sql_light/imdb_light.sqlite3` - локальная IMDb SQLite база.
- `data/candidate_pool/` - новые TMDb candidate_pool JSON/CSV артефакты.
- `data/cache/tmdb/` - локальный кэш TMDb, игнорируется git.

## Секреты

TMDb токен читается из:

- переменной окружения `TMDB_TOKEN`;
- `.env.local`;
- `tmdb.env`.

Не выводить токен в консоль. `.env.local`, `tmdb.env`, `.env/`, `data/cache/` добавлены в `.gitignore`.

## Новый TMDb Candidate Pool V1

Добавлен новый поток, не смешивается со старым общим пулом кандидатов.

Файлы:

- `integrations/api_tmdb.py`
- `data_work/tmdb_candidate_pool.py`
- `build_candidate_pool.py`

CLI:

```powershell
python build_candidate_pool.py --country RU --pages 3 --details-limit 50 --mode quality
python build_candidate_pool.py --country KR --pages 3 --details-limit 50 --mode hidden_gems
```

Сохраняет:

- `data/candidate_pool/candidate_pool_RU_quality.json`
- `data/candidate_pool/candidate_pool_RU_quality.csv`
- аналогично для `KR` и `hidden_gems`.

TMDb ответы кэшируются:

- Discover: `data/cache/tmdb/discover/<hash>.json`
- Details: `data/cache/tmdb/details/<tmdb_id>_<language>.json`

KP API в v1 не вызывается. Есть только `enrich_from_kp_cache_only()`.

## Правило работы агента

Перед изменениями:
1. Найти нужные файлы.
2. Кратко написать план.
3. Указать, какие файлы будут изменены.
4. Только потом вносить правку.

Не делать массовые рефакторинги без отдельного разрешения.

## Меню

Меню `ПУЛЛ КАНДИДАТОВ`:

- старый пункт `1 >> Собрать пулл кандидатов` оставлен как есть;
- добавлен пункт `8 >> Собрать TMDb candidate_pool v1`.

Изменённые места:

- `interface/ui.py` - печать пункта 8.
- `interface/global_menu.py` - разрешён выбор до 8 и вызов нового flow.
- `interface/interface_funcs.py` - `run_tmdb_candidate_pool_flow()`.

Новый flow спрашивает:

- страна: `RU` / `KR`;
- режим в меню показывается по-русски: `Лучшие по качеству` / `Скрытые находки`;
- страницы TMDb Discover, default `3`, clamp `1..20`;
- details limit, default `50`, clamp `1..300`;
- подтверждение запуска.

## IMDb SQL

Локальная база: `datasets/dataset_sql_light/imdb_light.sqlite3`.

Схема компактная, используются таблицы:

- `titles`
- `akas`
- `credits`

В новом TMDb flow IMDb enrichment ищет по `candidate["imdb_id"] == titles.tconst`.

## Старый Candidate Pool

Старый flow живёт в:

- `data_work/candidate_pool.py`
- `interface/candidate_pool_ui.py`

Не смешивать с новым TMDb candidate_pool v1. Старый общий пул использует `C:/DATA/movies-learn/candidate_pool.json`.

## Полезные проверки

Компиляция новых/изменённых файлов:

```powershell
C:\Users\super\AppData\Local\Programs\Python\Python313\python.exe -m compileall integrations\api_tmdb.py data_work\tmdb_candidate_pool.py build_candidate_pool.py interface\ui.py interface\global_menu.py interface\interface_funcs.py
```

Проверка меню:

```powershell
C:\Users\super\AppData\Local\Programs\Python\Python313\python.exe -c "from interface import ui; ui.show_candidate_pool_menu(0,0,0)"
```

Проверка нового menu-flow с отменой:

```powershell
"`n`n`n`nn" | C:\Users\super\AppData\Local\Programs\Python\Python313\python.exe -c "from interface.interface_funcs import run_tmdb_candidate_pool_flow; run_tmdb_candidate_pool_flow()"
```

## Последний успешный ручной тест

Команда:

```powershell
python build_candidate_pool.py --country RU --pages 3 --details-limit 50 --mode quality
```

Результат:

- Discover results: `60`
- Details requested: `50`
- Has IMDb ID: `50`
- Found in IMDb SQL: `50`
- Final candidates: `50`

Top примеры:

- `Слово пацана. Кровь на асфальте`
- `Бригада`
- `Вампиры средней полосы`
- `Ликвидация`
- `Эпидемия`
- `Мажор`

## Важные правила

- Не трогать и не коммитить секреты.
- Не вызывать KP API в TMDb candidate_pool v1.
- Не зашивать IP TMDb/CloudFront.
- Не делать TMDb Details по всем ID подряд, только по ограниченному top-N.
- Не ломать старый candidate_pool flow и пункт меню 1.
- В рабочем дереве уже может быть много чужих изменений, не откатывать их.


