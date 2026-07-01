"""Settings/Tools tab: pool stats, dedupe preview and maintenance actions."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from candidates import service as candidate_service
from desktop.settings.presenters import (
    KP_RETRY_BATCH_SIZE,
    format_clean_duplicates_status,
    format_clear_pool_status,
    format_dedupe_preview_lines,
    format_pool_stats_block,
    format_retry_kp_preview_line,
    format_retry_kp_status,
)

StatusCallback = Callable[[str, int], None]
PoolChangedCallback = Callable[[], None]


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

        self._widget = QWidget()
        self._widget.setObjectName("settingsToolsRoot")
        root_layout = QVBoxLayout(self._widget)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        header = QLabel("Сервис")
        header.setObjectName("candidateSearchHeader")
        root_layout.addWidget(header)

        subtitle = QLabel("Редкие операции с candidate pool. Все write-действия требуют подтверждения.")
        subtitle.setObjectName("candidateFiltersIntroLead")
        subtitle.setWordWrap(True)
        root_layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        self._stats_card = self._make_card()
        self._stats_layout = QVBoxLayout(self._stats_card)
        self._stats_layout.setContentsMargins(14, 12, 14, 12)
        self._stats_layout.setSpacing(6)
        stats_title = QLabel("Состояние pool")
        stats_title.setObjectName("candidateSearchFieldLabel")
        self._stats_layout.addWidget(stats_title)
        self._stats_body = QLabel("")
        self._stats_body.setObjectName("candidateFiltersIntroStats")
        self._stats_body.setWordWrap(True)
        self._stats_layout.addWidget(self._stats_body)
        content_layout.addWidget(self._stats_card)

        self._dedupe_card = self._make_card()
        self._dedupe_layout = QVBoxLayout(self._dedupe_card)
        self._dedupe_layout.setContentsMargins(14, 12, 14, 12)
        self._dedupe_layout.setSpacing(6)
        dedupe_title = QLabel("Предпросмотр дублей")
        dedupe_title.setObjectName("candidateSearchFieldLabel")
        self._dedupe_layout.addWidget(dedupe_title)
        self._dedupe_body = QLabel("")
        self._dedupe_body.setObjectName("candidateFiltersIntroLead")
        self._dedupe_body.setWordWrap(True)
        self._dedupe_layout.addWidget(self._dedupe_body)
        self._retry_preview = QLabel("")
        self._retry_preview.setObjectName("candidateFiltersIntroLead")
        self._retry_preview.setWordWrap(True)
        self._dedupe_layout.addWidget(self._retry_preview)
        content_layout.addWidget(self._dedupe_card)

        actions_row = QHBoxLayout()
        actions_row.setContentsMargins(0, 0, 0, 0)
        actions_row.setSpacing(10)

        self._dedupe_button = QPushButton("Очистить дубли")
        self._dedupe_button.setObjectName("candidateSearchApplyTopButton")
        self._dedupe_button.clicked.connect(self._run_clean_duplicates)
        actions_row.addWidget(self._dedupe_button)

        self._retry_kp_button = QPushButton(f"Добрать KP ({KP_RETRY_BATCH_SIZE})")
        self._retry_kp_button.setObjectName("candidateSearchApplyTopButton")
        self._retry_kp_button.clicked.connect(self._run_retry_kp)
        actions_row.addWidget(self._retry_kp_button)

        self._clear_pool_button = QPushButton("Очистить pool")
        self._clear_pool_button.setObjectName("candidateSearchWatchlist")
        self._clear_pool_button.clicked.connect(self._run_clear_pool)
        actions_row.addWidget(self._clear_pool_button)
        actions_row.addStretch(1)
        content_layout.addLayout(actions_row)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        root_layout.addWidget(scroll, stretch=1)

        self.refresh()

    @property
    def widget(self) -> QWidget:
        return self._widget

    def on_tab_activated(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        overview = candidate_service.get_search_overview_view()
        stats_view = candidate_service.get_pool_stats_view()
        stats_lines = format_pool_stats_block(stats_view)
        if overview.get("is_empty"):
            self._stats_body.setText("Candidate pool пуст.")
            self._dedupe_body.setText("Нет данных для предпросмотра дублей.")
            self._retry_preview.setText(format_retry_kp_preview_line({"incomplete_count": 0}))
            self._set_actions_enabled(False)
            return

        self._set_actions_enabled(True)
        self._stats_body.setText("\n".join(stats_lines))
        title_view = candidate_service.get_title_duplicates_view()
        suspicious_view = candidate_service.get_suspicious_duplicates_view()
        self._dedupe_body.setText("\n".join(format_dedupe_preview_lines(title_view, suspicious_view)))
        retry_view = candidate_service.get_retry_kp_view()
        self._retry_preview.setText(format_retry_kp_preview_line(retry_view))

    @staticmethod
    def _make_card() -> QFrame:
        frame = QFrame()
        frame.setObjectName("candidateFiltersIntro")
        return frame

    def _set_actions_enabled(self, enabled: bool) -> None:
        self._dedupe_button.setEnabled(enabled)
        self._retry_kp_button.setEnabled(enabled)
        self._clear_pool_button.setEnabled(enabled)

    def _show_status(self, message: str, timeout_ms: int = 8000) -> None:
        if self._on_status_message is not None:
            self._on_status_message(message, timeout_ms)

    def _notify_pool_changed(self) -> None:
        if self._on_pool_changed is not None:
            self._on_pool_changed()

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
