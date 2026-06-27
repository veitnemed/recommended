# Отчёт о проделанной работе на 2026-06-27

Основано на незакоммиченных изменениях после `2c3eabe` (poster auto-download, Model tab LOO training).

## Коротко

Два направления: **консольное меню жанров модели** и **desktop wizard «Добавить тайтл»** с двухэкранным UX (поиск → подтверждение на карточке). Save идёт через существующий service path (`add_movie` / `add_dataset_record`), без прямой записи JSON из PyQt.

---

## 1. Консоль: раздел «Жанры»

### Главное меню

Нумерация сдвинута:

| # | Пункт |
|---|--------|
| 4 | **Жанры** (новый) |
| 5 | Дополнительно |
| 6 | Пулл кандидатов |
| 7 | Выгрузить отчёт |

### Подменю «Жанры»

- **1 >> Показать все жанры** — каталог `has_*` из `config/genre_tags.json` с русскими подписями (`label`).

### Файлы

| Файл | Изменение |
|------|-----------|
| `ui/console/ui.py` | `show_genres_menu()`, обновлён `show_global_menu` |
| `ui/console/global_menu.py` | `open_genres_menu()` |
| `ui/console/console_app.py` | маршрутизация пункта 4 |
| `ui/console/genre_menu.py` | **новый** — вызов `genre_stats.show_model_genres()` |
| `dataset/genre_stats.py` | `build_model_genre_catalog()`, `show_model_genres()` |
| `config/genre_tags.json` | `has_romance` → label «Романтика» |
| `docs/README.md`, `docs/PROJECT_MAP.md` | структура меню |

### Тесты

- `tests_pytest/test_genre_stats.py`

---

## 2. Desktop: wizard «Добавить тайтл»

Заменена заглушка `QMessageBox` на полноценный сценарий добавления watched-тайтла.

### UX (два экрана, `QStackedWidget`)

**Экран A — поиск**

- Название, страна (по умолчанию **«Не важно»**), «Найти»
- Progress bar на 7 шагов resolve (IMDb SQL → KP → TMDb → сборка)
- Заголовок окна: «Добавить тайтл — поиск»

**Экран B — подтверждение**

- После успешного resolve экран поиска **скрыт**
- Шапка с title/year, статус источников
- Компактная `WatchedDetailCard` (постер ×0.5, меньшие круги IMDb/КП, без «моя оценка» на карточке)
- Scroll только для карточки; год, оценка и кнопки **вне scroll**
- «Искать другой» → возврат на экран A
- «Добавить тайтл» → `save_add_title_record()` → refresh списка watched

### Service-слой

| Файл | Роль |
|------|------|
| `dataset/add_title_service.py` | resolve bundle, preview card, `save_add_title_record()` |
| `dataset/title_resolve.py` | `on_progress` callback для GUI |
| `desktop/add_title_worker.py` | `QThread` → resolve |
| `desktop/add_title_dialog.py` | wizard UI |
| `desktop/app.py` | `_open_add_title_dialog()` |
| `candidates/tmdb_country_options.py` | «Не важно» + `add_title_country_combo_options()` |

### Карточка preview

- `DetailCardLayoutProfile` + `ADD_TITLE_PREVIEW_CARD_PROFILE`
- `include_bottom_stretch=False` для preview (меньше лишней высоты scroll)
- QSS: `#addTitlePreviewCard QLabel#detailTitle` → 18px

### Тесты

- `tests_pytest/test_add_title_service.py`
- `tests_pytest/test_desktop.py` — wizard wiring, `QStackedWidget`

### Roadmap

- `docs/DESKTOP_GUI_ROADMAP.md`: B1/B2 wizard — **done**

---

## 3. Что не входит / не коммитится

- `config/model_metrics.json` — локальный артефакт после LOO, не включается в коммит.

---

## 4. Проверки

```powershell
python -m pytest tests_pytest/test_genre_stats.py tests_pytest/test_add_title_service.py tests_pytest/test_desktop.py::test_add_title_button_opens_wizard_dialog -q
```

---

## 5. Следующие шаги (опционально)

- Редактирование vibe-тегов и жанров на экране preview
- Загрузка постера в preview по URL до save
- LLM-разметка vibe-тегов (см. обсуждение плана)
