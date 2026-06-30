"""Desktop Filters tab for runtime candidate pool filtering."""

from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from candidates import service as candidate_service
from candidates import tmdb_country_options
from config import constant
from desktop.candidate_search_session import CandidateSearchSession
from desktop.genre_chip_selector import GenreChipSelector
from desktop.range_slider import RangeSlider

CANDIDATE_YEAR_MIN = 2000
COUNTRY_ALL_ROW = 0


class CandidateFiltersView:
    """Filters tab: configure runtime pool filters and apply."""

    def __init__(
        self,
        session: CandidateSearchSession,
        *,
        on_applied: Callable[[], None] | None = None,
    ) -> None:
        self._session = session
        self._on_applied = on_applied
        self._genre_options: list[str] = []
        self._year_max = constant.NOW_YEAR

        self._widget = QWidget()
        self._widget.setObjectName("candidateFiltersRoot")
        root_layout = QVBoxLayout(self._widget)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        header = QLabel("Фильтры pool")
        header.setObjectName("candidateSearchHeader")
        root_layout.addWidget(header)

        hint = QLabel(
            "Runtime-фильтры по сохранённому pool. Не пересобирает pool и не делает TMDb-запрос."
        )
        hint.setObjectName("candidateSearchHint")
        hint.setWordWrap(True)
        root_layout.addWidget(hint)

        self._status_label = QLabel("")
        self._status_label.setObjectName("candidateSearchResultsSummary")
        self._status_label.setWordWrap(True)
        root_layout.addWidget(self._status_label)

        scroll = QScrollArea()
        scroll.setObjectName("candidateSearchFiltersScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        form_host = QWidget()
        form_host.setObjectName("candidateSearchFiltersHost")
        form = QVBoxLayout(form_host)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(12)

        self._country_list = QListWidget()
        self._country_list.setObjectName("candidateSearchCountryList")
        self._country_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self._country_list.setMaximumHeight(120)
        all_item = QListWidgetItem("Все")
        all_item.setData(Qt.ItemDataRole.UserRole, None)
        self._country_list.addItem(all_item)
        for option in tmdb_country_options.country_options():
            item = QListWidgetItem(option["label"])
            item.setData(Qt.ItemDataRole.UserRole, option["code"])
            self._country_list.addItem(item)
        self._country_list.itemSelectionChanged.connect(self._on_country_selection_changed)
        form.addWidget(self._label("Страна"))
        form.addWidget(self._country_list)

        year_header = QHBoxLayout()
        year_header.setContentsMargins(0, 0, 0, 0)
        year_header.addWidget(self._label("Год"))
        year_header.addStretch()
        self._year_range_label = QLabel("")
        self._year_range_label.setObjectName("candidateSearchYearRangeLabel")
        year_header.addWidget(self._year_range_label)
        form.addLayout(year_header)

        self._year_slider = RangeSlider(
            CANDIDATE_YEAR_MIN,
            self._year_max,
            CANDIDATE_YEAR_MIN,
            self._year_max,
        )
        self._year_slider.setObjectName("candidateSearchYearRange")
        self._year_slider.rangeChanged.connect(self._on_year_range_changed)
        form.addWidget(self._year_slider)

        self._include_genre_selector = GenreChipSelector(object_name="candidateSearchIncludeGenres")
        self._exclude_genre_selector = GenreChipSelector(object_name="candidateSearchExcludeGenres")
        form.addWidget(self._label("Включить жанры"))
        form.addWidget(self._include_genre_selector)
        form.addWidget(self._label("Исключить жанры"))
        form.addWidget(self._exclude_genre_selector)

        self._min_kp_score = self._make_score_spin("candidateSearchMinKp")
        self._min_imdb_score = self._make_score_spin("candidateSearchMinImdb")
        self._min_kp_votes = self._make_votes_spin("candidateSearchMinKpVotes")
        self._min_imdb_votes = self._make_votes_spin("candidateSearchMinImdbVotes")
        form.addWidget(self._label("Мин. KP"))
        form.addWidget(self._min_kp_score)
        form.addWidget(self._label("Мин. IMDb"))
        form.addWidget(self._min_imdb_score)
        form.addWidget(self._label("Мин. голосов KP"))
        form.addWidget(self._min_kp_votes)
        form.addWidget(self._label("Мин. голосов IMDb"))
        form.addWidget(self._min_imdb_votes)

        self._only_complete_check = QCheckBox("Только complete")
        self._only_complete_check.setObjectName("candidateSearchOnlyComplete")
        self._only_complete_check.setChecked(True)
        self._only_unwatched_check = QCheckBox("Скрывать просмотренные")
        self._only_unwatched_check.setObjectName("candidateSearchOnlyUnwatched")
        self._only_unwatched_check.setChecked(True)
        self._hide_hidden_check = QCheckBox("Скрывать hidden")
        self._hide_hidden_check.setObjectName("candidateSearchHideHidden")
        self._hide_hidden_check.setChecked(True)
        form.addWidget(self._only_complete_check)
        form.addWidget(self._only_unwatched_check)
        form.addWidget(self._hide_hidden_check)

        self._apply_button = QPushButton("Применить фильтры")
        self._apply_button.setObjectName("candidateSearchButton")
        self._apply_button.clicked.connect(self._apply_filters)
        form.addWidget(self._apply_button)

        scroll.setWidget(form_host)
        root_layout.addWidget(scroll, stretch=1)

        self._select_country_all()
        self._update_year_range_label()
        self._apply_filter_defaults()
        self._refresh_status()

    @property
    def widget(self) -> QWidget:
        return self._widget

    @staticmethod
    def _label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("candidateSearchFieldLabel")
        return label

    @staticmethod
    def _make_score_spin(object_name: str) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setObjectName(object_name)
        spin.setRange(0.0, 10.0)
        spin.setDecimals(1)
        spin.setSingleStep(0.1)
        spin.setSpecialValueText("—")
        spin.setValue(0.0)
        return spin

    @staticmethod
    def _make_votes_spin(object_name: str) -> QSpinBox:
        spin = QSpinBox()
        spin.setObjectName(object_name)
        spin.setRange(0, 10_000_000)
        spin.setSingleStep(100)
        spin.setSpecialValueText("—")
        spin.setValue(0)
        return spin

    def _select_country_all(self) -> None:
        self._country_list.blockSignals(True)
        self._country_list.clearSelection()
        self._country_list.item(COUNTRY_ALL_ROW).setSelected(True)
        self._country_list.blockSignals(False)

    def _on_country_selection_changed(self) -> None:
        all_item = self._country_list.item(COUNTRY_ALL_ROW)
        selected = self._country_list.selectedItems()
        if len(selected) == 0:
            self._select_country_all()
            return

        real_selected = [
            item
            for item in selected
            if item.data(Qt.ItemDataRole.UserRole) not in (None, "")
        ]
        if len(real_selected) == 0:
            if all_item not in selected:
                self._select_country_all()
            return

        if all_item in selected:
            self._country_list.blockSignals(True)
            all_item.setSelected(False)
            self._country_list.blockSignals(False)

    def _on_year_range_changed(self, _lower: int, _upper: int) -> None:
        self._update_year_range_label()

    def _update_year_range_label(self) -> None:
        year_from, year_to = self._year_slider.values()
        self._year_range_label.setText(f"{year_from}–{year_to}")

    def _set_year_slider_from_defaults(self, year_min, year_max) -> None:
        lower = CANDIDATE_YEAR_MIN
        upper = self._year_max
        if year_min not in (None, ""):
            try:
                lower = int(year_min)
            except (TypeError, ValueError):
                lower = CANDIDATE_YEAR_MIN
        if year_max not in (None, ""):
            try:
                upper = int(year_max)
            except (TypeError, ValueError):
                upper = self._year_max
        lower = max(CANDIDATE_YEAR_MIN, min(self._year_max, lower))
        upper = max(CANDIDATE_YEAR_MIN, min(self._year_max, upper))
        if lower > upper:
            lower, upper = upper, lower
        self._year_slider.blockSignals(True)
        self._year_slider.setValues(lower, upper)
        self._year_slider.blockSignals(False)
        self._update_year_range_label()

    def _year_filter_bounds(self) -> tuple[int | None, int | None]:
        year_from, year_to = self._year_slider.values()
        year_min = None if year_from <= CANDIDATE_YEAR_MIN else year_from
        year_max = None if year_to >= self._year_max else year_to
        return year_min, year_max

    def _apply_filter_defaults(self) -> None:
        defaults_view = candidate_service.get_search_filter_defaults_view()
        defaults = defaults_view.get("defaults") or {}
        genre_view = candidate_service.get_search_genre_options_view()
        self._genre_options = list(genre_view.get("genres") or [])
        self._include_genre_selector.set_options(self._genre_options, defaults.get("include_genres") or [])
        self._exclude_genre_selector.set_options(self._genre_options, defaults.get("exclude_genres") or [])

        self._set_year_slider_from_defaults(defaults.get("year_min"), defaults.get("year_max"))
        self._set_optional_float(self._min_kp_score, defaults.get("min_kp_score"))
        self._set_optional_float(self._min_imdb_score, defaults.get("min_imdb_score"))
        self._set_optional_int(self._min_kp_votes, defaults.get("min_kp_votes"))
        self._set_optional_int(self._min_imdb_votes, defaults.get("min_imdb_votes"))
        self._only_complete_check.setChecked(defaults.get("only_complete", True) is True)

        self._country_list.blockSignals(True)
        self._country_list.clearSelection()
        default_country = defaults.get("country")
        if default_country not in (None, ""):
            matched = False
            for row in range(1, self._country_list.count()):
                item = self._country_list.item(row)
                if item.data(Qt.ItemDataRole.UserRole) == default_country:
                    item.setSelected(True)
                    matched = True
                    break
            if matched is False:
                self._country_list.item(COUNTRY_ALL_ROW).setSelected(True)
        else:
            self._country_list.item(COUNTRY_ALL_ROW).setSelected(True)
        self._country_list.blockSignals(False)

    @staticmethod
    def _set_optional_float(spin: QDoubleSpinBox, value) -> None:
        if value in (None, ""):
            spin.setValue(0.0)
            return
        try:
            spin.setValue(float(value))
        except (TypeError, ValueError):
            spin.setValue(0.0)

    @staticmethod
    def _set_optional_int(spin: QSpinBox, value) -> None:
        if value in (None, ""):
            spin.setValue(0)
            return
        try:
            spin.setValue(int(value))
        except (TypeError, ValueError):
            spin.setValue(0)

    def _collect_filters(self) -> dict:
        countries = []
        for item in self._country_list.selectedItems():
            code = item.data(Qt.ItemDataRole.UserRole)
            if code not in (None, ""):
                countries.append(str(code))

        year_min, year_max = self._year_filter_bounds()

        def optional_float(spin: QDoubleSpinBox):
            if spin.value() <= 0.0 and spin.specialValueText():
                return None
            return spin.value()

        def optional_int(spin: QSpinBox):
            if spin.value() <= 0 and spin.specialValueText():
                return None
            return spin.value()

        return {
            "criteria_name": None,
            "source": None,
            "country": countries,
            "year_min": year_min,
            "year_max": year_max,
            "include_genres": self._include_genre_selector.selected_genres(),
            "exclude_genres": self._exclude_genre_selector.selected_genres(),
            "min_kp_score": optional_float(self._min_kp_score),
            "min_kp_votes": optional_int(self._min_kp_votes),
            "min_imdb_score": optional_float(self._min_imdb_score),
            "min_imdb_votes": optional_int(self._min_imdb_votes),
            "only_complete": self._only_complete_check.isChecked(),
            "only_unwatched": self._only_unwatched_check.isChecked(),
            "hide_hidden": self._hide_hidden_check.isChecked(),
        }

    def _refresh_status(self) -> None:
        overview = candidate_service.get_search_overview_view()
        if overview.get("is_empty"):
            self._status_label.setText(
                "Общий candidate pool пуст.\n"
                "Соберите pool через console: TMDb build или import saved result."
            )
            self._apply_button.setEnabled(False)
            return

        self._apply_button.setEnabled(True)
        stats = overview.get("stats") or {}
        unique_total = stats.get("unique_total", stats.get("storage_total", 0))
        pool_note = f"Уникальных в pool: {unique_total}."
        if self._session.has_results:
            self._status_label.setText(
                f"{pool_note} Последний фильтр: {self._session.filtered_count}. "
                f"Откройте вкладку «Кандидаты» для просмотра."
            )
        else:
            summary = overview.get("summary") or "Настройте фильтры и нажмите «Применить фильтры»."
            self._status_label.setText(f"{pool_note}\n{summary}")

    def _apply_filters(self) -> None:
        result = self._session.apply_filters(self._collect_filters())
        if result.get("is_empty_pool"):
            self._refresh_status()
            return

        if result.get("filtered_count", 0) == 0:
            self._status_label.setText(
                "После фильтра: 0 кандидатов.\n"
                "Ослабьте фильтры или включите incomplete-кандидатов."
            )
        else:
            self._status_label.setText(result.get("message") or f"После фильтра: {result['filtered_count']}")

        if self._on_applied is not None:
            self._on_applied()
