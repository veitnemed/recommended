"""Add-title search dialog: title, country and async resolve."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from candidates.sources.tmdb.country_options import add_title_country_combo_options
from common import valid
from dataset import service
from desktop.watched.add_title.constants import (
    ADD_TITLE_DIALOG_STYLE,
    SEARCH_DIALOG_HEIGHT,
    SEARCH_DIALOG_HEIGHT_ACTIVE,
    SEARCH_DIALOG_WIDTH,
)
from desktop.watched.add_title.worker import AddTitleResolveWorker


class AddTitleSearchDialog(QDialog):
    """Compact dialog: title, country, progress. Closes when resolve succeeds."""

    def __init__(
        self,
        parent=None,
        *,
        initial_title: str = "",
        initial_country: str = "",
    ) -> None:
        super().__init__(parent)
        self._bundle: service.AddTitleResolveBundle | None = None
        self._worker: AddTitleResolveWorker | None = None
        self.last_title = initial_title.strip()
        self.last_country = initial_country

        self.setObjectName("addTitleSearchDialog")
        self.setWindowTitle("Добавить тайтл — поиск")
        self.setModal(True)
        self.setFixedSize(SEARCH_DIALOG_WIDTH, SEARCH_DIALOG_HEIGHT)
        self.setStyleSheet(ADD_TITLE_DIALOG_STYLE)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 12, 14, 12)
        root_layout.setSpacing(8)

        header = QLabel("Добавить тайтл")
        header.setObjectName("addTitleHeader")
        root_layout.addWidget(header)

        subtitle = QLabel("Введите название и нажмите «Найти»")
        subtitle.setObjectName("addTitleSubtitle")
        subtitle.setWordWrap(True)
        root_layout.addWidget(subtitle)

        search_frame = QFrame()
        search_frame.setObjectName("addTitleSearchPanel")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 10, 12, 10)
        search_layout.setSpacing(8)

        self._title_input = QLineEdit()
        self._title_input.setObjectName("addTitleSearchInput")
        self._title_input.setPlaceholderText("Название сериала")
        self._title_input.setText(self.last_title)
        self._title_input.returnPressed.connect(self._start_search)

        self._country_combo = QComboBox()
        self._country_combo.setObjectName("addTitleCountryCombo")
        for label, value in add_title_country_combo_options():
            self._country_combo.addItem(label, value)
        self._set_country_selection(initial_country)

        self._search_button = QPushButton("Найти")
        self._search_button.setObjectName("addTitleSearchButton")
        self._search_button.clicked.connect(self._start_search)

        search_layout.addWidget(self._title_input, stretch=3)
        search_layout.addWidget(self._country_combo, stretch=1)
        search_layout.addWidget(self._search_button)
        root_layout.addWidget(search_frame)

        self._progress = QProgressBar()
        self._progress.setObjectName("addTitleProgress")
        self._progress.setTextVisible(True)
        self._progress.hide()
        root_layout.addWidget(self._progress)

        self._status_label = QLabel("")
        self._status_label.setObjectName("addTitleStatus")
        self._status_label.setWordWrap(True)
        self._status_label.hide()
        root_layout.addWidget(self._status_label)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 4, 0, 0)
        footer.addStretch()
        cancel_button = QPushButton("Отмена")
        cancel_button.setObjectName("addTitleSecondaryButton")
        cancel_button.clicked.connect(self.reject)
        footer.addWidget(cancel_button)
        root_layout.addLayout(footer)

        self._title_input.setFocus(Qt.FocusReason.OtherFocusReason)
        if self.last_title:
            self._title_input.selectAll()

    @property
    def resolve_bundle(self) -> service.AddTitleResolveBundle | None:
        return self._bundle

    def _set_country_selection(self, country: str) -> None:
        normalized = str(country or "").strip()
        if normalized == "":
            self._country_combo.setCurrentIndex(0)
            return
        for index in range(self._country_combo.count()):
            if self._country_combo.itemData(index) == normalized:
                self._country_combo.setCurrentIndex(index)
                return

    def _selected_country(self) -> str:
        country = self._country_combo.currentData()
        if country is None:
            return ""
        return str(country).strip()

    def _set_search_active(self, active: bool) -> None:
        self._title_input.setEnabled(not active)
        self._country_combo.setEnabled(not active)
        self._search_button.setEnabled(not active)
        self._progress.setVisible(active)
        self._status_label.setVisible(active)
        self.setFixedHeight(SEARCH_DIALOG_HEIGHT_ACTIVE if active else SEARCH_DIALOG_HEIGHT)
        if active is False:
            self._progress.reset()

    def _start_search(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return

        title = self._title_input.text().strip()
        if valid.is_correct_title(title) is False:
            QMessageBox.warning(self, "Добавить тайтл", "Введите корректное название.")
            return

        self.last_title = title
        self.last_country = self._selected_country()
        self._bundle = None
        self._set_search_active(True)
        self._status_label.setText("Поиск…")
        self._progress.setValue(0)
        self._progress.setMaximum(7)

        worker = AddTitleResolveWorker(title, self.last_country, self)
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

    def _on_resolve_finished(self, bundle: service.AddTitleResolveBundle) -> None:
        self._worker = None
        self._set_search_active(False)
        self._bundle = bundle
        self.accept()

    def closeEvent(self, event) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.requestInterruption()
        super().closeEvent(event)
