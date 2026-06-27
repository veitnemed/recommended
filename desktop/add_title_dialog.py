"""Add-title wizard dialog with progress bar and card confirmation."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from candidates.tmdb_country_options import add_title_country_combo_options
from common import valid
from config import constant
from dataset.add_title_service import (
    AddTitleResolveBundle,
    format_resolve_status_lines,
    save_add_title_record,
)
from desktop.add_title_worker import AddTitleResolveWorker
from desktop.theme import build_add_title_dialog_style
from desktop.watched_view import (
    ADD_TITLE_PREVIEW_CARD_PROFILE,
    USER_SCORE_MAX,
    USER_SCORE_MIN,
    USER_SCORE_STEP,
    YEAR_FILTER_DEFAULT_FROM,
    YEAR_FILTER_MAX,
    YEAR_FILTER_MIN,
    WatchedDetailCard,
    normalize_user_score_value,
)

ADD_TITLE_DIALOG_STYLE = build_add_title_dialog_style()

PAGE_SEARCH = 0
PAGE_PREVIEW = 1

SEARCH_DIALOG_MIN_HEIGHT = 340
PREVIEW_DIALOG_MIN_HEIGHT = 620
PREVIEW_CARD_SCROLL_MIN_HEIGHT = 260


class AddTitleDialog(QDialog):
    """Two-step wizard: search page, then preview/confirm page."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._bundle: AddTitleResolveBundle | None = None
        self._save_result = None
        self._worker: AddTitleResolveWorker | None = None

        self.setObjectName("addTitleDialog")
        self.setWindowTitle("Добавить тайтл — поиск")
        self.setModal(True)
        self.setMinimumWidth(760)
        self.setMinimumHeight(SEARCH_DIALOG_MIN_HEIGHT)
        self.resize(760, SEARCH_DIALOG_MIN_HEIGHT)
        self.setStyleSheet(ADD_TITLE_DIALOG_STYLE)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        self._stack = QStackedWidget()
        self._stack.setObjectName("addTitleStack")
        root_layout.addWidget(self._stack, stretch=1)

        self._stack.addWidget(self._build_search_page())
        self._stack.addWidget(self._build_preview_page())

        footer = QHBoxLayout()
        footer.addStretch()
        cancel_button = QPushButton("Отмена")
        cancel_button.setObjectName("addTitleSecondaryButton")
        cancel_button.clicked.connect(self.reject)
        footer.addWidget(cancel_button)
        root_layout.addLayout(footer)

        self._show_search_page()
        self._title_input.setFocus(Qt.FocusReason.OtherFocusReason)

    def _build_search_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("addTitleSearchPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        header = QLabel("Добавить тайтл")
        header.setObjectName("addTitleHeader")
        layout.addWidget(header)

        subtitle = QLabel("Введите название и нажмите «Найти»")
        subtitle.setObjectName("addTitleSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        search_frame = QFrame()
        search_frame.setObjectName("addTitleSearchPanel")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(14, 12, 14, 12)
        search_layout.setSpacing(10)

        self._title_input = QLineEdit()
        self._title_input.setObjectName("addTitleSearchInput")
        self._title_input.setPlaceholderText("Название сериала")
        self._title_input.returnPressed.connect(self._start_search)

        self._country_combo = QComboBox()
        self._country_combo.setObjectName("addTitleCountryCombo")
        for label, value in add_title_country_combo_options():
            self._country_combo.addItem(label, value)

        self._search_button = QPushButton("Найти")
        self._search_button.setObjectName("addTitleSearchButton")
        self._search_button.clicked.connect(self._start_search)

        search_layout.addWidget(self._title_input, stretch=3)
        search_layout.addWidget(self._country_combo, stretch=1)
        search_layout.addWidget(self._search_button)
        layout.addWidget(search_frame)

        self._progress = QProgressBar()
        self._progress.setObjectName("addTitleProgress")
        self._progress.setTextVisible(True)
        self._progress.hide()
        layout.addWidget(self._progress)

        self._status_label = QLabel("")
        self._status_label.setObjectName("addTitleStatus")
        self._status_label.setWordWrap(True)
        self._status_label.hide()
        layout.addWidget(self._status_label)

        layout.addStretch(1)
        return page

    def _build_preview_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("addTitlePreviewPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._preview_header = QLabel("Подтверждение")
        self._preview_header.setObjectName("addTitleHeader")
        layout.addWidget(self._preview_header)

        self._warning_label = QLabel("")
        self._warning_label.setObjectName("addTitleWarning")
        self._warning_label.setWordWrap(True)
        self._warning_label.hide()
        layout.addWidget(self._warning_label)

        scroll = QScrollArea()
        scroll.setObjectName("addTitlePreviewScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumHeight(PREVIEW_CARD_SCROLL_MIN_HEIGHT)

        card_shell = QFrame()
        card_shell.setObjectName("addTitlePreviewCard")
        card_shell_layout = QVBoxLayout(card_shell)
        card_shell_layout.setContentsMargins(10, 10, 10, 10)
        card_shell_layout.setSpacing(0)

        self._detail_card = WatchedDetailCard(card_shell, profile=ADD_TITLE_PREVIEW_CARD_PROFILE)
        card_shell_layout.addWidget(self._detail_card.widget)
        scroll.setWidget(card_shell)
        layout.addWidget(scroll, stretch=1)

        confirm_hint = QLabel("Проверьте карточку и подтвердите добавление")
        confirm_hint.setObjectName("addTitleConfirmHint")
        confirm_hint.setWordWrap(True)
        layout.addWidget(confirm_hint)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)

        self._year_input = QSpinBox()
        self._year_input.setObjectName("addTitleYearSpin")
        self._year_input.setRange(YEAR_FILTER_MIN, max(YEAR_FILTER_MAX, constant.NOW_YEAR))
        self._year_input.setValue(YEAR_FILTER_DEFAULT_FROM)
        self._year_input.valueChanged.connect(self._update_confirm_state)

        self._score_input = QDoubleSpinBox()
        self._score_input.setObjectName("addTitleScoreSpin")
        self._score_input.setRange(USER_SCORE_MIN, USER_SCORE_MAX)
        self._score_input.setSingleStep(USER_SCORE_STEP)
        self._score_input.setDecimals(1)
        self._score_input.setValue(USER_SCORE_MIN)
        self._score_input.valueChanged.connect(self._update_confirm_state)

        year_label = QLabel("Год")
        year_label.setObjectName("addTitleFieldLabel")
        score_label = QLabel("Моя оценка")
        score_label.setObjectName("addTitleFieldLabel")
        form.addRow(year_label, self._year_input)
        form.addRow(score_label, self._score_input)
        layout.addLayout(form)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self._back_button = QPushButton("Искать другой")
        self._back_button.setObjectName("addTitleSecondaryButton")
        self._back_button.clicked.connect(self._reset_preview)
        self._confirm_button = QPushButton("Добавить тайтл")
        self._confirm_button.setObjectName("addTitleConfirmButton")
        self._confirm_button.clicked.connect(self._confirm_add)
        actions.addWidget(self._back_button)
        actions.addStretch()
        actions.addWidget(self._confirm_button)
        layout.addLayout(actions)

        return page

    @property
    def save_result(self):
        return self._save_result

    def _selected_country(self) -> str:
        country = self._country_combo.currentData()
        if country is None:
            return ""
        return str(country).strip()

    def _show_search_page(self) -> None:
        self._stack.setCurrentIndex(PAGE_SEARCH)
        self.setWindowTitle("Добавить тайтл — поиск")
        self.setMinimumHeight(SEARCH_DIALOG_MIN_HEIGHT)
        if self.height() < SEARCH_DIALOG_MIN_HEIGHT:
            self.resize(self.width(), SEARCH_DIALOG_MIN_HEIGHT)

    def _show_preview_page(self) -> None:
        self._stack.setCurrentIndex(PAGE_PREVIEW)
        self.setWindowTitle("Добавить тайтл — подтверждение")
        self.setMinimumHeight(PREVIEW_DIALOG_MIN_HEIGHT)
        if self.height() < PREVIEW_DIALOG_MIN_HEIGHT:
            self.resize(self.width(), PREVIEW_DIALOG_MIN_HEIGHT)

    def _set_search_active(self, active: bool) -> None:
        self._title_input.setEnabled(not active)
        self._country_combo.setEnabled(not active)
        self._search_button.setEnabled(not active)
        self._progress.setVisible(active)
        self._status_label.setVisible(active)
        if active is False:
            self._progress.reset()

    def _format_preview_header(self, card: dict) -> str:
        title = str(card.get("title") or "").strip() or "Без названия"
        year = card.get("year")
        if year not in (None, ""):
            return f"{title} ({year})"
        return title

    def _start_search(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return

        title = self._title_input.text().strip()
        if valid.is_correct_title(title) is False:
            QMessageBox.warning(self, "Добавить тайтл", "Введите корректное название.")
            return

        self._bundle = None
        self._show_search_page()
        self._set_search_active(True)
        self._status_label.setText("Поиск…")
        self._progress.setValue(0)
        self._progress.setMaximum(7)

        worker = AddTitleResolveWorker(title, self._selected_country(), self)
        worker.progress.connect(self._on_progress)
        worker.finished_with_result.connect(self._on_resolve_finished)
        worker.failed.connect(self._on_resolve_failed)
        worker.finished.connect(worker.deleteLater)
        self._worker = worker
        worker.start()

    def _on_progress(self, current: int, total: int, message: str) -> None:
        self._progress.setMaximum(max(total, 1))
        self._progress.setValue(min(current, total))
        percent = int(round(100 * current / max(total, 1)))
        self._progress.setFormat(f"{percent}%")
        self._status_label.setText(message)

    def _on_resolve_failed(self, message: str) -> None:
        self._worker = None
        self._set_search_active(False)
        QMessageBox.critical(self, "Добавить тайтл", f"Ошибка поиска:\n{message}")

    def _on_resolve_finished(self, bundle: AddTitleResolveBundle) -> None:
        self._worker = None
        self._set_search_active(False)
        self._bundle = bundle
        self._show_preview(bundle)

    def _show_preview(self, bundle: AddTitleResolveBundle) -> None:
        preview_entry = ("__preview__", bundle.preview_movie, bundle.preview_card)
        self._detail_card.show_entry(preview_entry)
        self._preview_header.setText(self._format_preview_header(bundle.preview_card))

        year = bundle.preview_card.get("year")
        if year not in (None, ""):
            try:
                self._year_input.setValue(int(year))
            except (TypeError, ValueError):
                self._year_input.setValue(YEAR_FILTER_DEFAULT_FROM)
        else:
            self._year_input.setValue(YEAR_FILTER_DEFAULT_FROM)

        status_lines = format_resolve_status_lines(bundle.statuses)
        if bundle.found is False:
            self._warning_label.setText(
                "Автоматически данные не найдены. Проверьте карточку и заполните год/оценку вручную."
            )
            self._warning_label.show()
        elif len(status_lines) > 0:
            self._warning_label.setText(" · ".join(status_lines))
            self._warning_label.show()
        else:
            self._warning_label.hide()

        self._score_input.setValue(USER_SCORE_MIN)
        self._show_preview_page()
        self._update_confirm_state()
        self._score_input.setFocus(Qt.FocusReason.OtherFocusReason)

    def _update_confirm_state(self) -> None:
        year_ok = valid.is_correct_year(str(self._year_input.value()))
        score_ok = valid.is_correct_score(str(self._score_input.value()))
        self._confirm_button.setEnabled(self._bundle is not None and year_ok and score_ok)

    def _reset_preview(self) -> None:
        self._bundle = None
        self._warning_label.hide()
        self._show_search_page()
        self._title_input.selectAll()
        self._title_input.setFocus(Qt.FocusReason.OtherFocusReason)

    def _confirm_add(self) -> None:
        if self._bundle is None:
            return

        user_score = normalize_user_score_value(self._score_input.value())
        year = int(self._year_input.value())
        if valid.is_correct_score(str(user_score)) is False:
            QMessageBox.warning(self, "Добавить тайтл", "Укажите корректную оценку (0–10).")
            return
        if valid.is_correct_year(str(year)) is False:
            QMessageBox.warning(self, "Добавить тайтл", f"Укажите корректный год ({YEAR_FILTER_MIN}–{constant.NOW_YEAR}).")
            return

        self._confirm_button.setEnabled(False)
        result = save_add_title_record(
            self._bundle.defaults,
            user_score,
            meta_payload=self._bundle.meta_payload,
            poster_hints=self._bundle.poster_hints,
            year=year,
        )
        if result.ok is False:
            self._confirm_button.setEnabled(True)
            QMessageBox.warning(self, "Добавить тайтл", result.message)
            return

        self._save_result = result
        self.accept()
