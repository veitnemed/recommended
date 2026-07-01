"""Desktop Watched tab: sidebar list, filters, detail card and write actions."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from desktop.shared.widgets.list_search import DebouncedLineEditSearch, resolve_selection_row
from desktop.shared.widgets.range_slider import RangeSlider
from desktop.watched.delete import (
    execute_watched_delete,
    format_delete_status_message,
    load_delete_preview,
)
from desktop.watched.dialogs.delete_dialog import WatchedDeleteDialog
from desktop.watched.dialogs.score_edit import ScoreEditDialog
from desktop.shared.detail.card import WatchedDetailCard, WatchedListItemDelegate
from desktop.watched.model import (
    GENRE_FILTER_ALL,
    SORT_OPTIONS,
    USER_SCORE_MAX,
    USER_SCORE_MIN,
    USER_SCORE_STEP,
    YEAR_FILTER_DEFAULT_FROM,
    YEAR_FILTER_DEFAULT_TO,
    YEAR_FILTER_MAX,
    YEAR_FILTER_MIN,
    WatchedEntry,
    apply_view,
    build_watched_search_index,
    format_list_label,
    format_save_user_score_status,
    format_watched_filters_label,
    format_watched_list_counter,
    format_watched_list_status,
    genre_filter_is_active,
    get_available_genres,
    load_watched_entries,
    save_watched_user_score,
    score_filter_is_active,
    validate_score_edit_entry,
    watched_filters_are_active,
    year_filter_is_active,
)

StatusCallback = Callable[[str, int], None]
EntriesCallback = Callable[[list[WatchedEntry]], None]


class WatchedTabView:
    """Watched tab: list sidebar, collapsible filters, detail card, CRUD actions."""

    def __init__(
        self,
        *,
        parent: QWidget | None = None,
        on_status_message: StatusCallback | None = None,
        on_entries_changed: EntriesCallback | None = None,
    ) -> None:
        self._parent = parent
        self._on_status_message = on_status_message
        self._on_entries_changed = on_entries_changed

        self._entries: list[WatchedEntry] = load_watched_entries()
        self._watched_search_index = build_watched_search_index(self._entries)
        self._visible_entries: list[WatchedEntry] = list(self._entries)
        self._sort_key = SORT_OPTIONS[0][0]

        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        left_panel = self._build_left_panel()
        right_panel = self._build_right_panel()
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([340, 840])

        self._widget = tab

        self._refresh_list()
        if self._list_widget.count() > 0:
            self._list_widget.setCurrentRow(0)

    @property
    def widget(self) -> QWidget:
        return self._widget

    @property
    def entries(self) -> list[WatchedEntry]:
        return self._entries

    def reload_entries(self, added_key: str | None = None) -> None:
        """Refresh watched list after an external add (e.g. candidate transfer)."""
        previous_key = None
        current_row = self._list_widget.currentRow()
        if 0 <= current_row < len(self._visible_entries):
            previous_key = self._visible_entries[current_row][0]

        self._entries = load_watched_entries()
        self._reload_watched_search_index()
        self._reload_genre_filter_options()
        self._refresh_list()
        self._notify_entries_changed()

        if self._list_widget.count() == 0:
            self._show_empty_details()
            return

        select_key = added_key or previous_key
        row_to_select = resolve_selection_row(
            select_key,
            self._visible_entries,
            key_getter=lambda entry: entry[0],
        )
        if row_to_select < 0:
            self._show_empty_details()
            return

        self._list_widget.blockSignals(True)
        self._list_widget.setCurrentRow(row_to_select)
        self._list_widget.blockSignals(False)
        self._detail_card.show_entry(self._visible_entries[row_to_select])

    def _notify_entries_changed(self) -> None:
        if self._on_entries_changed is not None:
            self._on_entries_changed(self._entries)

    def _show_status(self, message: str, timeout_ms: int = 4000) -> None:
        if self._on_status_message is not None:
            self._on_status_message(message, timeout_ms)

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("watchedSidebar")
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(400)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self._add_title_button = QPushButton("+ Добавить тайтл")
        self._add_title_button.setObjectName("watchedAddTitle")
        self._add_title_button.clicked.connect(self._open_add_title_dialog)
        layout.addWidget(self._add_title_button)

        self._search_input = QLineEdit()
        self._search_input.setObjectName("watchedSearch")
        self._search_input.setPlaceholderText("Поиск по названию")
        self._search_input.setClearButtonEnabled(True)
        self._debounced_watched_search = DebouncedLineEditSearch(
            self._search_input,
            self._on_filters_changed,
            parent=panel,
        )
        layout.addWidget(self._search_input)

        sort_row = QWidget()
        sort_row.setObjectName("watchedSortRow")
        sort_layout = QHBoxLayout(sort_row)
        sort_layout.setContentsMargins(0, 0, 0, 0)
        sort_layout.setSpacing(10)

        sort_label = QLabel("Сортировка")
        sort_label.setObjectName("watchedSortLabel")

        self._sort_combo = QComboBox()
        self._sort_combo.setObjectName("watchedSort")
        for sort_key, label in SORT_OPTIONS:
            self._sort_combo.addItem(label, sort_key)
        self._sort_combo.currentIndexChanged.connect(self._on_filters_changed)

        sort_layout.addWidget(sort_label)
        sort_layout.addWidget(self._sort_combo, stretch=1)
        layout.addWidget(sort_row)

        self._filters_expanded = False
        self._filter_toggle = QPushButton("▸ Фильтры")
        self._filter_toggle.setObjectName("watchedFilterToggle")
        self._filter_toggle.clicked.connect(self._toggle_filters_panel)
        layout.addWidget(self._filter_toggle)

        self._filters_panel = self._build_filters_panel()
        self._filters_panel.setVisible(False)
        layout.addWidget(self._filters_panel)

        self._list_counter_label = QLabel("")
        self._list_counter_label.setObjectName("watchedListCounter")
        layout.addWidget(self._list_counter_label)

        self._list_widget = QListWidget()
        self._list_widget.setObjectName("watchedList")
        self._list_widget.setSpacing(2)
        self._list_widget.setUniformItemSizes(True)
        self._list_widget.setItemDelegate(WatchedListItemDelegate(self._list_widget))
        self._list_widget.currentRowChanged.connect(self._on_selection_changed)
        self._list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list_widget.customContextMenuRequested.connect(self._open_list_context_menu)
        layout.addWidget(self._list_widget, stretch=1)

        return panel

    def _build_filters_panel(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("watchedFiltersPanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        layout.addWidget(self._build_score_filter_panel())
        layout.addWidget(self._build_year_filter_panel())
        layout.addWidget(self._build_genre_filter_panel())

        reset_all_button = QPushButton("Сбросить фильтры")
        reset_all_button.setObjectName("watchedFilterResetAll")
        reset_all_button.clicked.connect(self._reset_all_filters)
        layout.addWidget(reset_all_button)
        return frame

    def _toggle_filters_panel(self) -> None:
        self._filters_expanded = not self._filters_expanded
        self._filters_panel.setVisible(self._filters_expanded)
        self._update_filter_toggle_label()

    def _update_filter_toggle_label(self) -> None:
        score_active = self._score_filter_active()
        year_active = self._year_filter_active()
        genre_active = self._genre_filter_active()
        filters_active = watched_filters_are_active(score_active, year_active, genre_active)
        self._filter_toggle.setText(
            format_watched_filters_label(
                score_active,
                year_active,
                genre_active,
                self._filters_expanded,
            )
        )
        self._filter_toggle.setProperty("watchedFiltersActive", "true" if filters_active else "false")
        self._filter_toggle.style().unpolish(self._filter_toggle)
        self._filter_toggle.style().polish(self._filter_toggle)

    def _reset_all_filters(self) -> None:
        self._score_slider.blockSignals(True)
        self._score_slider.setValues(
            self._score_to_slider_value(USER_SCORE_MIN),
            self._score_to_slider_value(USER_SCORE_MAX),
        )
        self._score_slider.blockSignals(False)

        self._year_slider.blockSignals(True)
        self._year_slider.setValues(YEAR_FILTER_DEFAULT_FROM, YEAR_FILTER_DEFAULT_TO)
        self._year_slider.blockSignals(False)

        self._genre_combo.blockSignals(True)
        self._genre_combo.setCurrentIndex(0)
        self._genre_combo.blockSignals(False)

        self._update_score_range_label()
        self._update_year_range_label()
        self._on_filters_changed()

    def _build_score_filter_panel(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("watchedScoreFilter")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Оценка")
        title.setObjectName("watchedScoreFilterTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self._score_range_label = QLabel()
        self._score_range_label.setObjectName("watchedFilterValue")
        header_row.addWidget(self._score_range_label)
        layout.addLayout(header_row)

        self._score_slider = RangeSlider(
            self._score_to_slider_value(USER_SCORE_MIN),
            self._score_to_slider_value(USER_SCORE_MAX),
            self._score_to_slider_value(USER_SCORE_MIN),
            self._score_to_slider_value(USER_SCORE_MAX),
        )
        self._score_slider.setObjectName("watchedScoreRange")
        self._score_slider.rangeChanged.connect(self._on_score_range_changed)
        layout.addWidget(self._score_slider)
        self._update_score_range_label()
        return frame

    def _score_to_slider_value(self, score: float) -> int:
        return int(round(float(score) / USER_SCORE_STEP))

    def _score_from_slider_value(self, value: int) -> float:
        return round(value * USER_SCORE_STEP, 1)

    def _score_filter_range(self) -> tuple[float, float]:
        lower, upper = self._score_slider.values()
        return (self._score_from_slider_value(lower), self._score_from_slider_value(upper))

    def _score_filter_active(self) -> bool:
        min_score, max_score = self._score_filter_range()
        return score_filter_is_active(min_score, max_score)

    def _update_score_range_label(self) -> None:
        min_score, max_score = self._score_filter_range()
        self._score_range_label.setText(f"{min_score:.1f}-{max_score:.1f}")

    def _on_score_range_changed(self, _lower: int, _upper: int) -> None:
        self._update_score_range_label()
        self._on_filters_changed()

    def _build_year_filter_panel(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("watchedYearFilter")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Год")
        title.setObjectName("watchedYearFilterTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self._year_range_label = QLabel()
        self._year_range_label.setObjectName("watchedFilterValue")
        header_row.addWidget(self._year_range_label)
        layout.addLayout(header_row)

        self._year_slider = RangeSlider(
            YEAR_FILTER_MIN,
            YEAR_FILTER_MAX,
            YEAR_FILTER_DEFAULT_FROM,
            YEAR_FILTER_DEFAULT_TO,
        )
        self._year_slider.setObjectName("watchedYearRange")
        self._year_slider.rangeChanged.connect(self._on_year_range_changed)
        layout.addWidget(self._year_slider)
        self._update_year_range_label()
        return frame

    def _year_filter_range(self) -> tuple[int, int]:
        return self._year_slider.values()

    def _year_filter_active(self) -> bool:
        year_from, year_to = self._year_filter_range()
        return year_filter_is_active(year_from, year_to)

    def _update_year_range_label(self) -> None:
        year_from, year_to = self._year_filter_range()
        self._year_range_label.setText(f"{year_from}-{year_to}")

    def _on_year_range_changed(self, _lower: int, _upper: int) -> None:
        self._update_year_range_label()
        self._on_filters_changed()

    def _build_genre_filter_panel(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("watchedGenreFilter")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)

        title = QLabel("Жанр")
        title.setObjectName("watchedGenreFilterTitle")
        layout.addWidget(title)

        self._genre_combo = QComboBox()
        self._genre_combo.setObjectName("watchedGenre")
        self._genre_combo.addItem(GENRE_FILTER_ALL, None)
        for genre in get_available_genres(self._entries):
            self._genre_combo.addItem(genre, genre)
        self._genre_combo.currentIndexChanged.connect(self._on_filters_changed)
        layout.addWidget(self._genre_combo)
        return frame

    def _open_add_title_dialog(self) -> None:
        from desktop.watched.add_title import run_add_title_flow

        result = run_add_title_flow(self._parent)
        if result is None or result.ok is False:
            return

        added_key = result.title
        self.reload_entries(added_key=added_key)
        self._show_status(result.message or "Новая запись добавлена!", 5000)

    def _reload_watched_search_index(self) -> None:
        self._watched_search_index = build_watched_search_index(self._entries)

    def _selected_genre_filter(self) -> str | None:
        genre = self._genre_combo.currentData()
        return genre if isinstance(genre, str) else None

    def _genre_filter_active(self) -> bool:
        return genre_filter_is_active(self._selected_genre_filter())

    def _build_right_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self._detail_card = WatchedDetailCard()
        scroll.setWidget(self._detail_card.widget)
        return scroll

    def _current_entry_key(self) -> str | None:
        row = self._list_widget.currentRow()
        if row < 0 or row >= len(self._visible_entries):
            return None
        return self._visible_entries[row][0]

    def _refresh_after_user_score_save(self, current_key: str, result) -> None:
        self._entries = load_watched_entries()
        self._reload_watched_search_index()
        self._refresh_list()
        self._notify_entries_changed()

        row_to_select = resolve_selection_row(
            current_key,
            self._visible_entries,
            key_getter=lambda entry: entry[0],
        )
        if row_to_select >= 0:
            self._list_widget.blockSignals(True)
            self._list_widget.setCurrentRow(row_to_select)
            self._list_widget.blockSignals(False)
            self._detail_card.show_entry(self._visible_entries[row_to_select])

        self._show_status(format_save_user_score_status(result), 4000)

    def _entry_from_item(self, item) -> WatchedEntry | None:
        if item is None:
            return None
        entry = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(entry, tuple) and len(entry) == 3:
            return entry
        return None

    def _open_list_context_menu(self, position) -> None:
        item = self._list_widget.itemAt(position)
        entry = self._entry_from_item(item)
        is_valid, _message = validate_score_edit_entry(entry)
        if is_valid is False:
            return

        self._list_widget.setCurrentItem(item)
        menu = QMenu(self._list_widget)
        edit_action = menu.addAction("Изменить оценку")
        delete_action = menu.addAction("Удалить запись")
        chosen_action = menu.exec(self._list_widget.viewport().mapToGlobal(position))
        if chosen_action is edit_action:
            self._edit_user_score(entry)
        elif chosen_action is delete_action:
            self._delete_watched_entry(entry)

    def _delete_watched_entry(self, entry: WatchedEntry | None) -> None:
        is_valid, message = validate_score_edit_entry(entry)
        if is_valid is False:
            self._show_status(message, 4000)
            return

        dataset_key, _movie, _card = entry
        preview = load_delete_preview(dataset_key)
        if preview is None:
            self._show_status("Запись не найдена", 4000)
            return

        dialog = WatchedDeleteDialog(preview, parent=self._parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        result = execute_watched_delete(dataset_key)
        if result.get("ok"):
            self._refresh_after_delete(result)
            return

        self._show_status(format_delete_status_message(result), 4000)

    def _reload_genre_filter_options(self) -> None:
        current = self._selected_genre_filter()
        self._genre_combo.blockSignals(True)
        self._genre_combo.clear()
        self._genre_combo.addItem(GENRE_FILTER_ALL, None)
        for genre in get_available_genres(self._entries):
            self._genre_combo.addItem(genre, genre)
        if current is not None:
            index = self._genre_combo.findData(current)
            self._genre_combo.setCurrentIndex(index if index >= 0 else 0)
        else:
            self._genre_combo.setCurrentIndex(0)
        self._genre_combo.blockSignals(False)

    def _refresh_after_delete(self, result: dict) -> None:
        previous_key = self._current_entry_key()
        self._entries = load_watched_entries()
        self._reload_watched_search_index()
        self._reload_genre_filter_options()
        self._refresh_list()
        self._notify_entries_changed()

        if self._list_widget.count() > 0:
            row_to_select = resolve_selection_row(
                previous_key,
                self._visible_entries,
                key_getter=lambda entry: entry[0],
            )
            if row_to_select < 0:
                row_to_select = 0
            self._list_widget.blockSignals(True)
            self._list_widget.setCurrentRow(row_to_select)
            self._list_widget.blockSignals(False)
            self._detail_card.show_entry(self._visible_entries[row_to_select])
        else:
            self._show_empty_details()

        self._show_status(format_delete_status_message(result), 4000)

    def _edit_user_score(self, entry: WatchedEntry | None) -> None:
        is_valid, message = validate_score_edit_entry(entry)
        if is_valid is False:
            self._show_status(message, 4000)
            return

        score = self._show_user_score_dialog(entry)
        if score is None:
            return

        dataset_key, _movie, _card = entry
        result = save_watched_user_score(dataset_key, score)
        if result.ok and result.reason in ("updated", "nothing_changed"):
            self._refresh_after_user_score_save(dataset_key, result)
            return

        self._show_status(format_save_user_score_status(result), 4000)

    def _show_user_score_dialog(self, entry: WatchedEntry) -> float | None:
        dialog = ScoreEditDialog(entry, parent=self._parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialog.score_value()

    def _on_filters_changed(self) -> None:
        self._sort_key = self._sort_combo.currentData()
        previous_key = self._current_entry_key()
        self._refresh_list()

        row_to_select = resolve_selection_row(
            previous_key,
            self._visible_entries,
            key_getter=lambda entry: entry[0],
        )
        if row_to_select >= 0:
            self._list_widget.setCurrentRow(row_to_select)

    def _refresh_list(self) -> None:
        query = self._search_input.text()
        min_score, max_score = self._score_filter_range()
        year_from, year_to = self._year_filter_range()
        genre = self._selected_genre_filter()
        self._visible_entries = apply_view(
            self._entries,
            query,
            self._sort_key,
            min_score,
            max_score,
            year_from,
            year_to,
            genre,
            title_index=self._watched_search_index,
        )

        self._list_widget.blockSignals(True)
        self._list_widget.clear()
        for entry in self._visible_entries:
            _, _, card = entry
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, entry)
            item.setToolTip(format_list_label(card))
            self._list_widget.addItem(item)
        self._list_widget.blockSignals(False)

        if self._list_widget.count() == 0:
            self._show_empty_details()
        self._update_list_status()

    def _update_list_status(self) -> None:
        visible = len(self._visible_entries)
        total = len(self._entries)
        query = self._search_input.text()
        score_active = self._score_filter_active()
        year_active = self._year_filter_active()
        genre_active = self._genre_filter_active()
        self._list_counter_label.setText(
            format_watched_list_counter(
                visible,
                total,
                query,
                score_active,
                year_active,
                genre_active,
            )
        )
        self._show_status(
            format_watched_list_status(
                visible,
                total,
                query,
                score_active,
                year_active,
                genre_active,
            )
        )
        self._update_filter_toggle_label()

    def _on_selection_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._visible_entries):
            self._show_empty_details()
            return
        self._detail_card.show_entry(self._visible_entries[row])

    def _show_empty_details(self) -> None:
        if self._search_input.text().strip():
            title = "Ничего не найдено"
        else:
            title = "Выберите тайтл слева"
        self._detail_card.show_empty(title)
