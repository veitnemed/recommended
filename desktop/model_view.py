"""Desktop Model tab: metrics summary and explicit LOO training."""

from PyQt6.QtCore import QObject, pyqtSignal

from desktop.analytics_view import (
    ANALYTICS_ROOT_MARGIN,
    ANALYTICS_ROOT_SPACING,
    ANALYTICS_SECTION_PADDING,
    ANALYTICS_SECTION_SPACING,
    ANALYTICS_SUMMARY_CARD_PADDING,
    ANALYTICS_SUMMARY_CARD_SPACING,
    ANALYTICS_SUMMARY_SPACING,
    SECTION_HEADER_ICON_BADGE_SIZE,
    SUMMARY_CARD_HEIGHT,
    SUMMARY_ICON_BADGE_SIZE,
)
from desktop.model_loo_worker import LooTrainingWorker
from desktop.model_summary import (
    build_model_tab_summary,
    build_weights_summary,
    format_training_result_message,
)
from desktop.theme import (
    FONT_BASE,
    FONT_KPI_VALUE,
    FONT_SECTION,
    FONT_SMALL,
    FONT_TITLE,
    build_analytics_style,
)
from model import linear_regression_train


MODEL_FONT_BASE = FONT_BASE
MODEL_FONT_PAGE_TITLE = FONT_TITLE
MODEL_FONT_SUBTITLE = FONT_BASE
MODEL_FONT_SUMMARY_LABEL = FONT_SMALL
MODEL_FONT_SUMMARY_VALUE = FONT_KPI_VALUE

MODEL_STYLE = build_analytics_style(
    font_base=MODEL_FONT_BASE,
    font_page_title=MODEL_FONT_PAGE_TITLE,
    font_subtitle=MODEL_FONT_SUBTITLE,
    font_summary_label=MODEL_FONT_SUMMARY_LABEL,
    font_summary_value=MODEL_FONT_SUMMARY_VALUE,
    font_section_title=FONT_SECTION,
)

SUMMARY_CARD_ICONS = {
    "LOO MAE": "◎",
    "IMDb baseline": "★",
    "КП baseline": "К",
    "Dataset size": "▦",
    "Статус metrics": "●",
}

TRAINING_CONTENT_SPACING = 8
WEIGHTS_PANEL_MAX_HEIGHT = 220


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        child_layout = item.layout()
        if child_layout is not None:
            _clear_layout(child_layout)
            continue
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


class ModelView(QObject):
    """Model metrics summary with explicit LOO training controls."""

    training_finished = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import (
            QFrame,
            QHBoxLayout,
            QLabel,
            QProgressBar,
            QPushButton,
            QScrollArea,
            QVBoxLayout,
            QWidget,
        )

        self._training_worker: LooTrainingWorker | None = None
        self._weights_details_visible = False

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(MODEL_STYLE)

        self._root = QWidget()
        self._root.setObjectName("modelRoot")
        self._root.setStyleSheet(MODEL_STYLE)
        self._scroll.setWidget(self._root)

        root_layout = QVBoxLayout(self._root)
        root_layout.setContentsMargins(
            ANALYTICS_ROOT_MARGIN,
            ANALYTICS_ROOT_MARGIN,
            ANALYTICS_ROOT_MARGIN,
            ANALYTICS_ROOT_MARGIN,
        )
        root_layout.setSpacing(ANALYTICS_ROOT_SPACING)

        title = QLabel("Модель")
        title.setObjectName("modelTitle")
        root_layout.addWidget(title)

        subtitle = QLabel("Метрики модели и явное LOO обучение на текущем dataset")
        subtitle.setObjectName("modelSubtitle")
        root_layout.addWidget(subtitle)

        self._stale_banner = QFrame()
        self._stale_banner.setObjectName("modelStaleBanner")
        stale_layout = QHBoxLayout(self._stale_banner)
        stale_layout.setContentsMargins(14, 12, 14, 12)
        self._stale_banner_text = QLabel("")
        self._stale_banner_text.setObjectName("modelStaleBannerText")
        self._stale_banner_text.setWordWrap(True)
        stale_layout.addWidget(self._stale_banner_text)
        self._stale_banner.hide()
        root_layout.addWidget(self._stale_banner)

        self._summary_layout = QHBoxLayout()
        self._summary_layout.setSpacing(ANALYTICS_SUMMARY_SPACING)
        self._summary_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        root_layout.addLayout(self._summary_layout)

        training_content = QVBoxLayout()
        training_content.setContentsMargins(0, 0, 0, 0)
        training_content.setSpacing(TRAINING_CONTENT_SPACING)

        training_hint = QLabel(
            "Ridge LOO: подбор alpha на текущем dataset, обучение финальной модели и сохранение weights/model_metrics."
        )
        training_hint.setObjectName("modelTrainingStatus")
        training_hint.setWordWrap(True)
        training_content.addWidget(training_hint)

        buttons_row = QHBoxLayout()
        buttons_row.setContentsMargins(0, 0, 0, 0)
        buttons_row.setSpacing(10)

        self._train_button = QPushButton("Запустить LOO обучение")
        self._train_button.setObjectName("modelTrainButton")
        self._train_button.clicked.connect(self._start_loo_training)
        buttons_row.addWidget(self._train_button)

        self._details_button = QPushButton("Подробнее")
        self._details_button.setObjectName("modelDetailsButton")
        self._details_button.clicked.connect(self._toggle_weights_details)
        buttons_row.addWidget(self._details_button)
        buttons_row.addStretch()
        training_content.addLayout(buttons_row)

        self._training_progress = QProgressBar()
        self._training_progress.setObjectName("modelTrainingProgress")
        self._training_progress.setTextVisible(True)
        self._training_progress.hide()
        training_content.addWidget(self._training_progress)

        self._training_status = QLabel("")
        self._training_status.setObjectName("modelTrainingStatus")
        self._training_status.setWordWrap(True)
        self._training_status.hide()
        training_content.addWidget(self._training_status)

        self._training_result = QLabel("")
        self._training_result.setObjectName("modelTrainingResult")
        self._training_result.setWordWrap(True)
        self._training_result.hide()
        training_content.addWidget(self._training_result)

        self._weights_panel = QFrame()
        self._weights_panel.setObjectName("modelWeightsPanel")
        self._weights_panel.hide()
        weights_panel_layout = QVBoxLayout(self._weights_panel)
        weights_panel_layout.setContentsMargins(12, 10, 12, 10)
        weights_panel_layout.setSpacing(0)

        self._weights_scroll = QScrollArea()
        self._weights_scroll.setWidgetResizable(True)
        self._weights_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._weights_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._weights_scroll.setMaximumHeight(WEIGHTS_PANEL_MAX_HEIGHT)

        self._weights_text = QLabel("")
        self._weights_text.setObjectName("modelWeightsText")
        self._weights_text.setWordWrap(True)
        self._weights_text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._weights_scroll.setWidget(self._weights_text)
        weights_panel_layout.addWidget(self._weights_scroll)
        training_content.addWidget(self._weights_panel)

        self._training_section = self._make_section("Обучение", training_content, "↻")
        from PyQt6.QtWidgets import QSizePolicy

        self._training_section.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )
        root_layout.addWidget(self._training_section)
        self.refresh()

    @property
    def widget(self):
        return self._scroll

    def refresh(self) -> None:
        summary = build_model_tab_summary()
        self._fill_summary(summary)
        self._update_stale_banner(summary)
        if self._weights_details_visible:
            self._refresh_weights_panel()

    def _toggle_weights_details(self) -> None:
        self._weights_details_visible = not self._weights_details_visible
        if self._weights_details_visible:
            self._refresh_weights_panel()
            self._weights_panel.show()
            self._details_button.setText("Свернуть")
            return
        self._weights_panel.hide()
        self._details_button.setText("Подробнее")

    def _refresh_weights_panel(self) -> None:
        from storage import data as storage_data

        weights = storage_data.load_weights()
        summary = build_weights_summary(weights)
        self._weights_text.setText(summary["text_block"])

    def _set_training_status_text(self, text: str) -> None:
        if text.strip() == "":
            self._training_status.hide()
            self._training_status.setText("")
            return
        self._training_status.setText(text)
        self._training_status.show()

    def _set_training_result_text(self, text: str) -> None:
        if text.strip() == "":
            self._training_result.hide()
            self._training_result.setText("")
            return
        self._training_result.setText(text)
        self._training_result.show()

    def _update_stale_banner(self, summary: dict) -> None:
        if summary.get("is_stale") is True:
            self._stale_banner_text.setText(summary.get("stale_retrain_message") or "")
            self._stale_banner.show()
            return
        self._stale_banner.hide()

    def _fill_summary(self, summary: dict) -> None:
        _clear_layout(self._summary_layout)
        items = (
            ("LOO MAE", summary["loo_mae_display"]),
            ("IMDb baseline", summary["imdb_baseline_display"]),
            ("КП baseline", summary["kp_baseline_display"]),
            ("Dataset size", summary["dataset_size_display"]),
            ("Статус metrics", summary["metrics_status_kpi"]),
        )
        for label, value in items:
            icon = SUMMARY_CARD_ICONS.get(label, "•")
            tooltip = ""
            object_name = "summaryCard"
            if label == "Статус metrics":
                tooltip = summary.get("metrics_status_display") or ""
                if summary.get("is_stale") is True:
                    object_name = "summaryCardStale"
            card = self._make_summary_card(label, value, icon, object_name=object_name, value_tooltip=tooltip)
            self._summary_layout.addWidget(card, stretch=1)

    def _make_summary_card(
        self,
        label_text: str,
        value_text: str,
        icon_text: str,
        *,
        object_name: str = "summaryCard",
        value_tooltip: str = "",
    ):
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

        frame = QFrame()
        frame.setObjectName(object_name)
        frame.setFixedHeight(SUMMARY_CARD_HEIGHT)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(
            ANALYTICS_SUMMARY_CARD_PADDING,
            ANALYTICS_SUMMARY_CARD_PADDING,
            ANALYTICS_SUMMARY_CARD_PADDING,
            ANALYTICS_SUMMARY_CARD_PADDING,
        )
        layout.setSpacing(10)

        icon_badge = QFrame()
        icon_badge.setObjectName("summaryIconBadge")
        icon_badge.setFixedSize(SUMMARY_ICON_BADGE_SIZE, SUMMARY_ICON_BADGE_SIZE)
        badge_layout = QVBoxLayout(icon_badge)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        icon = QLabel(icon_text)
        icon.setObjectName("summaryIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_layout.addWidget(icon)

        text_column = QVBoxLayout()
        text_column.setContentsMargins(0, 0, 0, 0)
        text_column.setSpacing(ANALYTICS_SUMMARY_CARD_SPACING)

        label = QLabel(label_text)
        label.setObjectName("summaryLabel")
        value = QLabel(value_text)
        value.setObjectName("summaryValue")
        value.setWordWrap(True)
        if value_tooltip:
            value.setToolTip(value_tooltip)
        text_column.addWidget(label)
        text_column.addWidget(value)
        text_column.addStretch()

        layout.addWidget(icon_badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(text_column, stretch=1)
        return frame

    def _make_section(self, title_text: str, content_layout, icon_text: str = ""):
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QFrame, QVBoxLayout

        frame = QFrame()
        frame.setObjectName("analyticsSection")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(
            ANALYTICS_SECTION_PADDING,
            ANALYTICS_SECTION_PADDING,
            ANALYTICS_SECTION_PADDING,
            ANALYTICS_SECTION_PADDING,
        )
        layout.setSpacing(ANALYTICS_SECTION_SPACING)
        layout.addWidget(self._make_section_header(title_text, icon_text))
        layout.addLayout(content_layout)
        return frame

    def _make_section_header(self, title_text: str, icon_text: str):
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

        header = QWidget()
        header.setObjectName("sectionHeader")
        row = QHBoxLayout(header)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        icon_badge = QFrame()
        icon_badge.setObjectName("sectionHeaderIconBadge")
        icon_badge.setFixedSize(SECTION_HEADER_ICON_BADGE_SIZE, SECTION_HEADER_ICON_BADGE_SIZE)
        icon_layout = QVBoxLayout(icon_badge)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon = QLabel(icon_text)
        icon.setObjectName("sectionHeaderIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon)

        title = QLabel(title_text)
        title.setObjectName("sectionTitle")

        row.addWidget(icon_badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(title, alignment=Qt.AlignmentFlag.AlignVCenter)
        row.addStretch()
        return header

    def _set_training_active(self, active: bool) -> None:
        self._train_button.setEnabled(not active)
        self._details_button.setEnabled(not active)
        self._training_progress.setVisible(active)
        if active is False:
            self._training_progress.reset()
            self._set_training_status_text("")

    def _start_loo_training(self) -> None:
        from PyQt6.QtWidgets import QMessageBox
        from storage import data as storage_data

        if self._training_worker is not None and self._training_worker.isRunning():
            return

        data = storage_data.load_dataset()
        weights = storage_data.load_weights()
        preflight = linear_regression_train.validate_explicit_loo_training(data)
        if preflight.get("ok") is not True:
            QMessageBox.warning(self._root, "LOO обучение", preflight.get("message", "Нельзя запустить обучение."))
            return

        self._set_training_result_text("")
        self._set_training_active(True)
        self._set_training_status_text("Подготовка LOO обучения…")

        worker = LooTrainingWorker(self._root)
        worker.progress.connect(self._on_training_progress)
        worker.finished_with_result.connect(self._on_training_finished)
        worker.finished.connect(worker.deleteLater)
        self._training_worker = worker
        worker.start()

    def _on_training_progress(self, current: int, total: int, message: str) -> None:
        total = max(total, 1)
        self._training_progress.setMaximum(total)
        self._training_progress.setValue(min(current, total))
        percent = int(round((min(current, total) / total) * 100))
        self._training_progress.setFormat(f"{percent}%")
        self._set_training_status_text(message)

    def _on_training_finished(self, result: dict) -> None:
        from PyQt6.QtWidgets import QMessageBox

        self._set_training_active(False)
        self._training_worker = None
        self._set_training_result_text(format_training_result_message(result))
        self.refresh()
        self.training_finished.emit()

        if result.get("ok") is True:
            return

        QMessageBox.warning(
            self._root,
            "LOO обучение",
            result.get("message", "LOO обучение не выполнено."),
        )
