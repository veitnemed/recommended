# Desktop Module Map

Карта PyQt desktop GUI: куда класть код, как добавлять вкладки и как не ломать границы слоёв.

Связанные документы:

- [DESKTOP_GUI_ROADMAP.md](DESKTOP_GUI_ROADMAP.md) — roadmap функций.
- [DESKTOP_STYLE_CONTRACT.md](DESKTOP_STYLE_CONTRACT.md) — визуальный контракт.
- [ARCHITECTURE_TARGET.md](ARCHITECTURE_TARGET.md) — общая архитектура проекта.

## Принцип

Desktop — **тонкий слой сценариев** поверх `dataset`, `candidates.service`, `posters`. UI не пишет JSON напрямую.

```text
start_app.py → desktop.app.main()
                 → shell/main_window.WatchedMoviesWindow
                      → WatchedTabView / Candidate*View / AnalyticsView
                           → presenters + shared widgets
                           → service layer (dataset, candidates)
```

## Структура пакетов

```text
desktop/
  app.py                         # thin entry: re-exports main + WatchedMoviesWindow

  shell/
    bootstrap.py                 # QApplication, WebEngine prep, main()
    main_window.py               # WatchedMoviesWindow: tabs, status bar
    tabs.py                      # MainTabRegistry, ShellTabSpec
  watched/
    model.py                     # load, filter, sort, format, writes (no Qt widgets)
    delete.py                    # delete preview/execute helpers
    tab.py                       # WatchedTabView
    dialogs/
      score_edit.py              # ScoreEditDialog
      delete_dialog.py           # WatchedDeleteDialog
    add_title/
      dialog.py                  # search/preview flow
      worker.py                  # AddTitleResolveWorker
  candidates/
    session.py                   # shared filter/sort state
    filters_view.py              # вкладка Фильтры
    list_view.py                 # вкладка Кандидаты
    presenters.py                # format/map candidate records
    workers/poster_worker.py
  analytics/
    view.py                      # AnalyticsView (read-only tab)
    charts.py                    # Plotly HTML builders
  shared/
    detail/
      card.py                    # WatchedDetailCard, delegate, layout profiles
    widgets/
      range_slider.py
      list_search.py
      collapsible_chip_helpers.py
      genre_chip_selector.py
      country_chip_selector.py
  theme/
    tokens.py                    # COLOR_*, FONT_*, spacing, radius
    styles/
      app.py                     # build_app_style
      dialogs.py                 # score/delete/add-title dialogs
      detail_card.py             # detail card, poster, bar fallbacks
      analytics.py               # build_analytics_style
```

| Модуль | Роль | Слой |
| --- | --- | --- |
| `app.py` | thin entry, re-exports `main` | shell |
| `shell/main_window.py` | главное окно, регистрация вкладок | shell |
| `shell/tabs.py` | tab registry, `on_tab_activated` dispatch | shell |
| `watched/tab.py` | вкладка Watched: sidebar, filters, list, detail, CRUD | feature view |
| `watched/model.py` | load/filter/format, poster paths, score save | model |
| `shared/detail/card.py` | `WatchedDetailCard`, list delegate | shared |
| `watched/dialogs/score_edit.py` | диалог редактирования user_score | dialog |
| `watched/add_title/` | wizard добавления / transfer из pool | dialog + worker |
| `candidates/session.py` | shared state Фильтры ↔ Кандидаты | session |
| `candidates/filters_view.py` | вкладка Фильтры | feature view |
| `candidates/list_view.py` | вкладка Кандидаты | feature view |
| `candidates/presenters.py` | format/map для UI | presenter |
| `analytics/view.py` | read-only вкладка Analytics | feature view |
| `analytics/charts.py` | Plotly chart builders | charts |
| `shared/widgets/` | range_slider, list_search, chip selectors | shared |
| `shared/detail/` | detail card reused across tabs | shared |
| `theme/tokens.py` | colors, fonts, spacing | theme |
| `theme/styles/*` | QSS builders per screen | theme |

## Контракт feature view

Каждая вкладка — класс с единым интерфейсом (как `CandidateListView`, `WatchedTabView`, `AnalyticsView`):

```python
class SomeTabView:
    @property
    def widget(self) -> QWidget: ...   # корневой виджет для QTabWidget

    def on_tab_activated(self) -> None: ...  # опционально: lazy refresh
```

Правила:

- view **не импортирует** другие feature views напрямую;
- cross-tab события идут через shell (`WatchedMoviesWindow`) или shared session (`CandidateSearchSession`);
- status bar — callback `on_status_message(msg, timeout_ms)` из shell;
- изменение watched-базы — callback `on_entries_changed(entries)` для analytics и др.

## Куда класть новый код

| Задача | Куда |
| --- | --- |
| Новая вкладка | `desktop/<feature>/` + регистрация в `shell/main_window.py` |
| Фильтр/сортировка watched (логика) | `watched/model.py` |
| Layout watched sidebar | `watched/tab.py` |
| Detail card / list delegate | `shared/detail/card.py` |
| Форматирование candidate list | `candidates/presenters.py` |
| Write-сценарий (save/delete) | `watched/delete.py` / `dataset` + dialog |
| Переиспользуемый виджет без domain | `shared/widgets/` |
| Новый цвет/spacing | `theme/tokens.py` |
| QSS нового экрана | `theme/styles/<screen>.py` |

## Запрещённые зависимости

```text
❌ desktop → storage (напрямую save/load JSON)
❌ feature view → feature view (Watched → Candidate)
❌ watched/model.py → PyQt6
❌ candidates/* → watched/tab.py
✅ candidate views → shared/detail (card reused across watched, candidates, add-title)
✅ все views → dataset / candidates.service
```

## Добавление вкладки (чеклист)

1. Создать view в `desktop/<feature>/` с `.widget`.
2. Бизнес-логику — в `dataset` / `candidates` / model без Qt.
3. QSS — через `desktop.theme` (`tokens.py` + `styles/`).
4. Зарегистрировать в `shell/main_window.py` через `MainTabRegistry`.
5. Callbacks в shell при cross-tab sync.
6. Тесты в `tests/test_desktop.py`.

## Порядок миграции

1. ~~`watched/model.py` + `detail_card.py`~~ done
2. ~~`watched/tab.py`~~ done
3. ~~`candidates/` — session, filters_view, list_view, presenters, workers~~ done
4. ~~`analytics/` — view, charts~~ done
5. ~~`shared/widgets/`~~ done
6. ~~`theme/` — tokens + styles~~ done
7. ~~Удалить shims~~ done
8. ~~Перенести flat-файлы (`app.py` → `shell/`, dialogs в feature-пакеты)~~ done
9. ~~`shell/tabs.py`, `shared/detail/`, `on_tab_activated`~~ done

## Проверки

```powershell
py -m compileall desktop dataset candidates storage ui tests
py -m pytest tests/test_desktop.py
```
