"""Read-only desktop analytics view for watched scores."""

from __future__ import annotations

import os
import sys
import tempfile

from dataset.score_analytics import build_score_analytics


ANALYTICS_STYLE = """
QWidget#analyticsRoot {
    background-color: #0f0f10;
    color: #f4f4f5;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}
QWidget#analyticsBarRow {
    background: transparent;
}
QLabel#analyticsTitle {
    background: transparent;
    color: #f4f4f5;
    font-size: 24px;
    font-weight: 700;
}
QLabel#analyticsSubtitle {
    background: transparent;
    color: #a1a1aa;
    font-size: 13px;
}
QFrame#summaryCard,
QFrame#analyticsSection,
QFrame#insightCard,
QFrame#sameScoreCard {
    background-color: #171719;
    border: 1px solid #2a2a2e;
    border-radius: 16px;
}
QLabel#summaryLabel,
QLabel#barLabel,
QLabel#denseLabel,
QLabel#denseTitles,
QLabel#insightText {
    background: transparent;
    color: #a1a1aa;
    font-size: 12px;
}
QLabel#summaryValue {
    background: transparent;
    color: #f4f4f5;
    font-size: 22px;
    font-weight: 700;
}
QLabel#sectionTitle {
    background: transparent;
    color: #f4f4f5;
    font-size: 15px;
    font-weight: 700;
}
QFrame#barTrack {
    background-color: #1c1c1f;
    border-radius: 6px;
}
QFrame#barFill {
    background-color: #10a37f;
    border-radius: 6px;
}
QLabel#barCount,
QLabel#denseCount {
    background: transparent;
    color: #f4f4f5;
    font-size: 13px;
    font-weight: 600;
}
QLabel#denseScore {
    background: transparent;
    color: #10a37f;
    font-size: 18px;
    font-weight: 700;
}
QLabel#sameScoreTitles {
    background: transparent;
    color: #d4d4d8;
    font-size: 12px;
}
QLabel#analyticsFallback {
    background: transparent;
    color: #d4d4d8;
    font-size: 13px;
    padding: 10px 2px;
}
"""

BAR_TRACK_WIDTH = 330
BAR_HEIGHT = 12
PLOTLY_VIEW_HEIGHT = 318
BAR_TRACK_STYLE = "background-color: #1c1c1f; border-radius: 6px;"
BAR_FILL_STYLE = "background-color: #10a37f; border-radius: 6px;"


def _format_metric(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, int):
        return str(value)
    return f"{float(value):.1f}"


def _entries_to_records(entries: list[tuple[str, dict, dict]]) -> dict:
    return {key: movie for key, movie, _card in entries}


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


class AnalyticsView:
    """Widget wrapper for read-only score analytics."""

    def __init__(self, entries: list[tuple[str, dict, dict]] | None = None) -> None:
        from PyQt6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

        self._plotly_html_paths: list[str] = []

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(ANALYTICS_STYLE)

        self._root = QWidget()
        self._root.setObjectName("analyticsRoot")
        self._root.setStyleSheet(ANALYTICS_STYLE)
        self._scroll.setWidget(self._root)

        root_layout = QVBoxLayout(self._root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        title = QLabel("Аналитика")
        title.setObjectName("analyticsTitle")
        root_layout.addWidget(title)

        subtitle = QLabel("Распределение моих оценок в watched-базе")
        subtitle.setObjectName("analyticsSubtitle")
        root_layout.addWidget(subtitle)

        self._summary_layout = QHBoxLayout()
        self._summary_layout.setSpacing(8)
        root_layout.addLayout(self._summary_layout)

        self._insights_layout = QVBoxLayout()
        root_layout.addWidget(self._make_section("Коротко", self._insights_layout))

        self._distribution_layout = QVBoxLayout()
        root_layout.addWidget(self._make_section("Распределение оценок", self._distribution_layout))

        self._dense_layout = QVBoxLayout()
        root_layout.addWidget(self._make_section("Одинаковые оценки", self._dense_layout))

        root_layout.addStretch()
        self.update_entries(entries or [])

    @property
    def widget(self):
        return self._scroll

    def update_entries(self, entries: list[tuple[str, dict, dict]]) -> None:
        analytics = build_score_analytics(_entries_to_records(entries))
        self._fill_summary(analytics["summary"])
        self._fill_insights(analytics["insights"])
        self._fill_distribution(analytics["score_count_points"])
        self._fill_dense_scores(analytics["dense_scores"])

    def _clear_plotly_html_files(self) -> None:
        while self._plotly_html_paths:
            path = self._plotly_html_paths.pop()
            try:
                os.remove(path)
            except OSError:
                pass

    def _write_plotly_html_file(self, html: str) -> str:
        handle = tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            suffix=".html",
            prefix="recommended_plotly_",
            delete=False,
        )
        with handle:
            handle.write(html)
        self._plotly_html_paths.append(handle.name)
        return handle.name

    def _make_section(self, title_text: str, content_layout):
        from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout

        frame = QFrame()
        frame.setObjectName("analyticsSection")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QLabel(title_text)
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        layout.addLayout(content_layout)
        return frame

    def _fill_summary(self, summary: dict) -> None:
        _clear_layout(self._summary_layout)
        items = (
            ("Всего", summary["count"]),
            ("Средняя", summary["average"]),
            ("Медиана", summary["median"]),
            ("Минимум", summary["minimum"]),
            ("Максимум", summary["maximum"]),
        )
        for label, value in items:
            self._summary_layout.addWidget(self._make_summary_card(label, _format_metric(value)))
        self._summary_layout.addStretch()

    def _make_summary_card(self, label_text: str, value_text: str):
        from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout

        frame = QFrame()
        frame.setObjectName("summaryCard")
        frame.setFixedWidth(124)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(3)

        label = QLabel(label_text)
        label.setObjectName("summaryLabel")
        value = QLabel(value_text)
        value.setObjectName("summaryValue")
        layout.addWidget(label)
        layout.addWidget(value)
        return frame

    def _fill_insights(self, insights: list[str]) -> None:
        _clear_layout(self._insights_layout)
        for text in insights:
            self._insights_layout.addWidget(self._make_insight_line(text))

    def _make_insight_line(self, text: str):
        from PyQt6.QtWidgets import QLabel

        label = QLabel(text)
        label.setObjectName("insightText")
        label.setWordWrap(True)
        return label

    def _fill_distribution(self, distribution: list[dict]) -> None:
        _clear_layout(self._distribution_layout)
        self._clear_plotly_html_files()
        try:
            from PyQt6.QtCore import QUrl
            from PyQt6.QtWebEngineWidgets import QWebEngineView
        except ImportError as error:
            self._distribution_layout.addWidget(
                self._make_fallback_message(
                    "Интерактивные графики требуют PyQt6-WebEngine\n"
                    f"Python: {sys.executable}\n"
                    f"Ошибка: {error}"
                )
            )
            return

        try:
            from desktop.plotly_charts import build_score_count_html

            html = build_score_count_html(distribution)
        except ImportError as error:
            self._distribution_layout.addWidget(
                self._make_fallback_message(
                    "Интерактивные графики требуют plotly\n"
                    f"Python: {sys.executable}\n"
                    f"Ошибка: {error}"
                )
            )
            return

        try:
            from PyQt6.QtWidgets import QSizePolicy

            view = QWebEngineView()
            view.setFixedHeight(PLOTLY_VIEW_HEIGHT)
            view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            view.setStyleSheet("background-color: #171719;")
            html_path = self._write_plotly_html_file(html)
            view.setUrl(QUrl.fromLocalFile(html_path))
            self._distribution_layout.addWidget(view)
        except Exception as error:
            self._distribution_layout.addWidget(
                self._make_fallback_message(
                    "Не удалось открыть интерактивный график\n"
                    f"Python: {sys.executable}\n"
                    f"Ошибка: {error}"
                )
            )

    def _make_fallback_message(self, text: str):
        from PyQt6.QtWidgets import QLabel

        label = QLabel(text)
        label.setObjectName("analyticsFallback")
        label.setWordWrap(True)
        return label

    def _make_bar_row(self, item: dict, max_count: int):
        from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

        row = QWidget()
        row.setObjectName("analyticsBarRow")
        row.setFixedHeight(24)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel(item["label"])
        label.setObjectName("barLabel")
        label.setFixedWidth(76)
        layout.addWidget(label)

        track = QFrame()
        track.setObjectName("barTrack")
        track.setStyleSheet(BAR_TRACK_STYLE)
        track.setFixedHeight(BAR_HEIGHT)
        track.setFixedWidth(BAR_TRACK_WIDTH)
        track_layout = QHBoxLayout(track)
        track_layout.setContentsMargins(0, 0, 0, 0)
        track_layout.setSpacing(0)
        fill = QFrame()
        fill.setObjectName("barFill")
        fill.setStyleSheet(BAR_FILL_STYLE)
        fill.setFixedHeight(BAR_HEIGHT)
        fill_width = (
            0
            if max_count == 0 or item["count"] == 0
            else max(8, int(BAR_TRACK_WIDTH * item["count"] / max_count))
        )
        fill.setFixedWidth(fill_width)
        track_layout.addWidget(fill)
        track_layout.addStretch()
        layout.addWidget(track)

        count = QLabel(f"{item['count']} · {item['percent']:.1f}%")
        count.setObjectName("barCount")
        count.setFixedWidth(92)
        layout.addWidget(count)
        layout.addStretch()
        return row

    def _fill_dense_scores(self, dense_scores: list[dict]) -> None:
        _clear_layout(self._dense_layout)
        if len(dense_scores) == 0:
            self._dense_layout.addWidget(self._make_dense_row({"score": None, "count": 0, "titles": [], "extra_count": 0}))
            return
        for row in dense_scores:
            self._dense_layout.addWidget(self._make_dense_row(row))

    def _make_dense_row(self, dense_row: dict):
        from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

        row = QFrame()
        row.setObjectName("sameScoreCard")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        score_text = "-" if dense_row.get("score") is None else _format_metric(dense_row["score"])
        count_text = "Нет оценок" if dense_row.get("count", 0) == 0 else f"{dense_row['count']} тайтлов"
        titles = dense_row.get("titles", [])
        extra_count = dense_row.get("extra_count", 0)
        if titles:
            titles_text = " · ".join(titles)
            if extra_count > 0:
                titles_text = f"{titles_text} · ещё {extra_count}"
        else:
            titles_text = "Нет тайтлов для отображения"

        score = QLabel(score_text)
        score.setObjectName("denseScore")
        score.setFixedWidth(58)
        layout.addWidget(score)

        text_column = QVBoxLayout()
        text_column.setSpacing(2)
        count = QLabel(count_text)
        count.setObjectName("denseCount")
        title_label = QLabel(titles_text)
        title_label.setObjectName("sameScoreTitles")
        title_label.setWordWrap(True)
        text_column.addWidget(count)
        text_column.addWidget(title_label)
        layout.addLayout(text_column)
        layout.addStretch()
        return row
