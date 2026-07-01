"""Settings/Tools tab: pool stats, dedupe preview and maintenance actions."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from candidates import service as candidate_service
from desktop.settings.presenters import (
    KP_RETRY_BATCH_SIZE,
    format_clean_duplicates_status,
    format_clear_pool_status,
    format_dedupe_preview_lines,
    format_pool_kpi_items,
    format_retry_kp_preview_line,
    format_retry_kp_status,
    format_tmdb_files_empty_hint,
    format_tmdb_import_preview,
    format_tmdb_import_status,
)

StatusCallback = Callable[[str, int], None]
PoolChangedCallback = Callable[[], None]

SETTINGS_CONTENT_MAX_WIDTH = 720
SECTION_PADDING = 16
SECTION_SPACING = 10


class SettingsToolsView:
    """Rare pool maintenance actions with confirmation dialogs."""

    def __init__(
        self,
        *,
        on_status_message: StatusCallback | None = None,
        on_pool_changed: PoolChangedCallback | None = None,
    ) -> None:
        self._on_status_message = on_status_message
        self._on_pool_changed = on_pool_changed
        self._tmdb_files: list[Path] = []
        self._kpi_tiles: list[tuple[QLabel, QLabel]] = []

        self._widget = QWidget()
        self._widget.setObjectName("settingsToolsRoot")
        root_layout = QVBoxLayout(self._widget)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(14)

        header = QLabel("Сервис")
        header.setObjectName("settingsPageTitle")
        root_layout.addWidget(header)

        subtitle = QLabel("Редкие операции с candidate pool. Все изменения требуют подтверждения.")
        subtitle.setObjectName("settingsPageSubtitle")
        subtitle.setWordWrap(True)
        root_layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_host = QWidget()
        scroll_host_layout = QHBoxLayout(scroll_host)
        scroll_host_layout.setContentsMargins(0, 0, 0, 0)
        scroll_host_layout.setSpacing(0)

        content = QWidget()
        content.setMaximumWidth(SETTINGS_CONTENT_MAX_WIDTH)
        content.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        pool_section, pool_body = self._make_section("Состояние pool")
        self._kpi_row = QHBoxLayout()
        self._kpi_row.setSpacing(10)
        pool_body.addLayout(self._kpi_row)
        self._pool_empty_label = QLabel("")
        self._pool_empty_label.setObjectName("settingsEmptyText")
        self._pool_empty_label.setWordWrap(True)
        self._pool_empty_label.hide()
        pool_body.addWidget(self._pool_empty_label)
        content_layout.addWidget(pool_section)

        dedupe_section, dedupe_body = self._make_section(
            "Дубликаты",
            hint="Только просмотр. Очистка — в блоке «Обслуживание» ниже.",
        )
        self._dedupe_body = QLabel("")
        self._dedupe_body.setObjectName("settingsBodyText")
        self._dedupe_body.setWordWrap(True)
        dedupe_body.addWidget(self._dedupe_body)
        content_layout.addWidget(dedupe_section)

        kp_section, kp_body = self._make_section("Добор KP")
        self._kp_body = QLabel("")
        self._kp_body.setObjectName("settingsBodyText")
        self._kp_body.setWordWrap(True)
        kp_body.addWidget(self._kp_body)
        content_layout.addWidget(kp_section)

        tmdb_section, tmdb_body = self._make_section("Импорт TMDb")
        self._tmdb_file_combo = QComboBox()
        self._tmdb_file_combo.setObjectName("settingsTmdbImportFile")
        self._tmdb_file_combo.currentIndexChanged.connect(self._on_tmdb_file_changed)
        tmdb_body.addWidget(self._tmdb_file_combo)
        self._tmdb_preview = QLabel("")
        self._tmdb_preview.setObjectName("settingsSectionHint")
        self._tmdb_preview.setWordWrap(True)
        tmdb_body.addWidget(self._tmdb_preview)
        self._tmdb_import_button = QPushButton("Импортировать в pool")
        self._tmdb_import_button.setObjectName("candidateSearchApplyTopButton")
        self._tmdb_import_button.clicked.connect(self._run_tmdb_import)
        tmdb_body.addWidget(self._tmdb_import_button, alignment=Qt.AlignmentFlag.AlignLeft)
        content_layout.addWidget(tmdb_section)

        maintenance_section, maintenance_body = self._make_section("Обслуживание")
        maintenance_buttons = QHBoxLayout()
        maintenance_buttons.setSpacing(10)
        self._dedupe_button = QPushButton("Очистить дубли")
        self._dedupe_button.setObjectName("candidateSearchApplyTopButton")
        self._dedupe_button.clicked.connect(self._run_clean_duplicates)
        maintenance_buttons.addWidget(self._dedupe_button)
        self._retry_kp_button = QPushButton(f"Добрать KP ({KP_RETRY_BATCH_SIZE})")
        self._retry_kp_button.setObjectName("candidateSearchApplyTopButton")
        self._retry_kp_button.clicked.connect(self._run_retry_kp)
        maintenance_buttons.addWidget(self._retry_kp_button)
        maintenance_buttons.addStretch(1)
        maintenance_body.addLayout(maintenance_buttons)
        content_layout.addWidget(maintenance_section)

        danger_section, danger_body = self._make_section(
            "Опасная зона",
            hint="Необратимые действия с общим candidate pool.",
        )
        self._clear_pool_button = QPushButton("Очистить pool")
        self._clear_pool_button.setObjectName("settingsDangerButton")
        self._clear_pool_button.clicked.connect(self._run_clear_pool)
        danger_body.addWidget(self._clear_pool_button, alignment=Qt.AlignmentFlag.AlignLeft)
        content_layout.addWidget(danger_section)

        content_layout.addStretch(1)
        scroll_host_layout.addWidget(content)
        scroll_host_layout.addStretch(1)
        scroll.setWidget(scroll_host)
        root_layout.addWidget(scroll, stretch=1)

        self._init_kpi_tiles()
        self.refresh()

    @property
    def widget(self) -> QWidget:
        return self._widget

    def on_tab_activated(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        overview = candidate_service.get_search_overview_view()
        stats = (candidate_service.get_pool_stats_view().get("stats") or {})
        pool_empty = overview.get("is_empty")

        for index, (label, value, _icon) in enumerate(format_pool_kpi_items(stats)):
            if index < len(self._kpi_tiles):
                self._kpi_tiles[index][0].setText(value)
                self._kpi_tiles[index][1].setText(label)

        if pool_empty:
            self._pool_empty_label.setText("Candidate pool пуст. Импорт TMDb доступен ниже.")
            self._pool_empty_label.show()
            self._dedupe_body.setText("—")
            self._kp_body.setText("—")
            self._dedupe_button.setEnabled(False)
            self._retry_kp_button.setEnabled(False)
            self._clear_pool_button.setEnabled(False)
        else:
            self._pool_empty_label.hide()
            title_view = candidate_service.get_title_duplicates_view()
            suspicious_view = candidate_service.get_suspicious_duplicates_view()
            self._dedupe_body.setText("\n".join(format_dedupe_preview_lines(title_view, suspicious_view)))
            retry_view = candidate_service.get_retry_kp_view()
            self._kp_body.setText(format_retry_kp_preview_line(retry_view))
            self._dedupe_button.setEnabled(True)
            self._retry_kp_button.setEnabled(True)
            self._clear_pool_button.setEnabled(True)

        self._refresh_tmdb_import_section()

    def _init_kpi_tiles(self) -> None:
        for label_text, value_text, icon_text in format_pool_kpi_items({}):
            tile = self._make_metric_tile(label_text, value_text, icon_text)
            self._kpi_row.addWidget(tile, stretch=1)

    def _refresh_tmdb_import_section(self) -> None:
        files_view = candidate_service.get_tmdb_import_files_view()
        self._tmdb_files = list(files_view.get("files") or [])

        self._tmdb_file_combo.blockSignals(True)
        self._tmdb_file_combo.clear()
        if files_view.get("is_empty"):
            self._tmdb_file_combo.addItem("— файлов нет —")
            self._tmdb_preview.setText(format_tmdb_files_empty_hint())
            self._tmdb_import_button.setEnabled(False)
        else:
            for path in self._tmdb_files:
                self._tmdb_file_combo.addItem(path.name, path)
            self._tmdb_import_button.setEnabled(True)
            self._update_tmdb_preview()
        self._tmdb_file_combo.blockSignals(False)

    def _on_tmdb_file_changed(self, _index: int) -> None:
        self._update_tmdb_preview()

    def _selected_tmdb_file(self) -> Path | None:
        if not self._tmdb_files:
            return None
        index = self._tmdb_file_combo.currentIndex()
        if index < 0 or index >= len(self._tmdb_files):
            return None
        return self._tmdb_files[index]

    def _update_tmdb_preview(self) -> None:
        result_path = self._selected_tmdb_file()
        if result_path is None:
            self._tmdb_preview.setText(format_tmdb_files_empty_hint())
            return
        preview = candidate_service.load_tmdb_result_import_preview(result_path)
        self._tmdb_preview.setText(format_tmdb_import_preview(preview))

    @staticmethod
    def _make_section(title: str, *, hint: str | None = None) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("settingsSection")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SECTION_PADDING, SECTION_PADDING, SECTION_PADDING, SECTION_PADDING)
        layout.setSpacing(SECTION_SPACING)

        title_label = QLabel(title)
        title_label.setObjectName("settingsSectionTitle")
        layout.addWidget(title_label)

        if hint:
            hint_label = QLabel(hint)
            hint_label.setObjectName("settingsSectionHint")
            hint_label.setWordWrap(True)
            layout.addWidget(hint_label)

        body = QVBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(8)
        layout.addLayout(body)
        return frame, body

    def _make_metric_tile(self, label_text: str, value_text: str, icon_text: str) -> QFrame:
        from PyQt6.QtWidgets import QVBoxLayout as TileVBox

        frame = QFrame()
        frame.setObjectName("settingsMetricCard")
        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(10)

        icon = QLabel(icon_text)
        icon.setObjectName("settingsMetricIcon")
        icon.setFixedWidth(24)
        icon.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        text_column = TileVBox()
        text_column.setContentsMargins(0, 0, 0, 0)
        text_column.setSpacing(2)

        value = QLabel(value_text)
        value.setObjectName("settingsMetricValue")
        label = QLabel(label_text)
        label.setObjectName("settingsMetricLabel")
        text_column.addWidget(value)
        text_column.addWidget(label)

        row.addWidget(icon, alignment=Qt.AlignmentFlag.AlignTop)
        row.addLayout(text_column, stretch=1)
        self._kpi_tiles.append((value, label))
        return frame

    def _show_status(self, message: str, timeout_ms: int = 8000) -> None:
        if self._on_status_message is not None:
            self._on_status_message(message, timeout_ms)

    def _notify_pool_changed(self) -> None:
        if self._on_pool_changed is not None:
            self._on_pool_changed()

    def _run_tmdb_import(self) -> None:
        result_path = self._selected_tmdb_file()
        if result_path is None:
            self._show_status(format_tmdb_files_empty_hint(), 5000)
            return

        preview = candidate_service.load_tmdb_result_import_preview(result_path)
        if preview.get("ok") is False:
            self._show_status(format_tmdb_import_preview(preview, include_filename=True), 8000)
            self._update_tmdb_preview()
            return

        answer = QMessageBox.question(
            self._widget,
            "Импорт TMDb",
            f"{format_tmdb_import_preview(preview, include_filename=True)}\n\nИмпортировать в общий candidate pool?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        import_result = candidate_service.import_tmdb_result_to_pool(result_path)
        message = format_tmdb_import_status(import_result)
        self._show_status(message, 12000)
        self.refresh()
        if import_result.get("ok"):
            self._notify_pool_changed()

    def _run_clean_duplicates(self) -> None:
        answer = QMessageBox.question(
            self._widget,
            "Очистить дубли",
            "Удалить exact, похожие и cross-year дубли из общего candidate pool?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        result = candidate_service.clean_common_pool_duplicates()
        message = format_clean_duplicates_status(result)
        self._show_status(message)
        self.refresh()
        self._notify_pool_changed()

    def _run_retry_kp(self) -> None:
        retry_view = candidate_service.get_retry_kp_view()
        incomplete_count = int(retry_view.get("incomplete_count") or 0)
        if incomplete_count <= 0:
            self._show_status("Неполных карточек для KP retry нет.", 4000)
            return

        answer = QMessageBox.question(
            self._widget,
            "Добрать KP",
            f"Запустить KP retry для до {min(KP_RETRY_BATCH_SIZE, incomplete_count)} неполных карточек?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        result = candidate_service.retry_kp_enrichment_in_pool(limit=KP_RETRY_BATCH_SIZE)
        message = format_retry_kp_status(result)
        self._show_status(message, 10000)
        self.refresh()
        self._notify_pool_changed()

    def _run_clear_pool(self) -> None:
        answer = QMessageBox.warning(
            self._widget,
            "Очистить pool",
            "Удалить все записи из общего candidate pool? Действие необратимо.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        result = candidate_service.clear_common_candidate_pool()
        message = format_clear_pool_status(result)
        self._show_status(message)
        self.refresh()
        self._notify_pool_changed()
