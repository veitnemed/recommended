# Desktop GUI Roadmap

Roadmap описывает актуальный PyQt desktop для `Series List`: watched-база, карточка тайтла, аналитика и поиск кандидатов. Старые desktop-сценарии из `archive/legacy/` не возвращаются в активный GUI.

## Цель

Desktop должен быть рабочим интерфейсом для ежедневного сценария:

1. посмотреть watched-базу;
2. найти тайтл или кандидата;
3. проверить карточку, постер, рейтинги, жанры и описание;
4. добавить/обновить watched-запись через documented services;
5. использовать read-only аналитику для качества базы.

## Правила

- GUI не пишет JSON напрямую.
- Любой write идет через `dataset` или `candidates.service`.
- TMDb/KP/IMDb SQL вызываются через `apis` и сервисы.
- Generated JSON не добавляется в git.
- Desktop не содержит старых legacy-вкладок.

## Текущее состояние

| Область | Файлы | Статус |
| --- | --- | --- |
| Watched list + detail card | `desktop/app.py`, `desktop/watched_view.py` | done |
| Poster display/actions | `desktop/watched_view.py`, `posters/` | done |
| Edit `user_score` | `desktop/app.py`, `dataset.dataset_records` | done |
| Delete watched | `desktop/watched_delete.py`, `desktop/delete_dialog.py` | done |
| Add watched wizard | `desktop/add_title_dialog.py`, `dataset.storage_movie` | done |
| Analytics read-only | `desktop/analytics_view.py`, `dataset/score_analytics.py` | done |
| Plotly/fallback charts | `desktop/plotly_charts.py` | done |
| Candidate search in GUI | `candidates.service`, desktop wiring | planned |
| Candidate pool operations | `candidates.service` | planned |

## Этап 1. Polish текущей watched-базы

Статус: done.

- watched sidebar: поиск, сортировка, фильтры, thumbnails;
- detail card: poster, title, chips, ratings, overview;
- context actions: открыть локальный постер, удалить watched;
- стабильный layout при resize;
- helper-тесты в `tests/test_desktop.py`.

## Этап 2. Read-only аналитика

Статус: done.

Scope:

- dataset completeness;
- score distribution;
- genre distribution;
- average by year;
- gaps against IMDb/KP;
- suspicious records;
- fallback без WebEngine.

Правило: analytics читает dataset/meta и ничего не сохраняет.

## Этап 3. Watched write-сценарии

Статус: mostly done.

- добавление записи через wizard;
- редактирование `user_score`;
- удаление watched с preview и подтверждением;
- poster-cache side effects только через dataset/delete services.

Осталось:

- ручное редактирование жанров и raw scores в GUI;
- более понятные ошибки API/defaults;
- UX для неполных данных перед сохранением.

## Этап 4. Поиск кандидатов

Статус: planned.

Цель: перенести основной поиск из console в desktop без дублирования core-логики.

Задачи:

- criteria selector;
- runtime-фильтры по стране, году, рейтингу, жанрам;
- ready/incomplete split;
- карточка candidate preview;
- перенос candidate -> watched через существующий add flow;
- понятная пустая выдача и причины incomplete.

Запреты:

- не пересобирать pool при runtime-фильтре;
- не писать candidate pool напрямую из widgets;
- не вызывать KP/TMDb напрямую из desktop.

## Этап 5. Candidate pool operations

Статус: planned.

Read-only сначала:

- список criteria;
- stats по raw/watched/active/ready/incomplete;
- suspicious duplicates;
- incomplete candidates preview.

Write только с confirmation dialogs:

- mark watched;
- retry KP;
- delete criteria;
- import saved TMDb result.

TMDb build остается отдельным сложным сценарием и переносится позже.

## Этап 6. Metadata и posters

Статус: planned.

- показать состояние poster-cache: local/missing/remote;
- batch download missing posters;
- refresh TMDb metadata для выбранной записи;
- аккуратные сообщения по сети, SSL и отсутствию токена.

## Этап 7. Финальная структура GUI

После переноса поиска desktop должен иметь понятные зоны:

- `Watched`;
- `Search`;
- `Candidates`;
- `Analytics`;
- `Settings/Tools` для редких действий.

Console остается рабочим fallback и местом для редких maintenance-сценариев.

## Проверки

Для desktop-изменений:

```powershell
py -m compileall desktop dataset candidates apis storage ui tests
py -m pytest tests/test_desktop.py
```

Для структурных изменений:

```powershell
py -m compileall app apis candidates common config dataset desktop posters scripts storage ui web tests
py -m pytest
```
