"""Desktop Candidates tab: card list and read-only detail card."""

from __future__ import annotations

import logging
from time import perf_counter

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from candidates import service as candidate_service
from desktop.candidate_poster_worker import CandidatePosterDownloadWorker
from desktop.candidate_search_session import CandidateSearchSession, DEFAULT_TOP_N
from desktop.candidate_search_view import (
    build_candidate_readonly_detail_entry,
    candidate_detail_identity,
    candidate_poster_url_for_download,
    format_candidate_metric_value,
    resolve_local_poster_path_for_candidate,
)
from desktop.watched_view import (
    CANDIDATE_DETAIL_CARD_PROFILE,
    LIST_ITEM_HEIGHT,
    LIST_ITEM_H_PADDING,
    LIST_ITEM_V_PADDING,
    LIST_TEXT_GAP,
    LIST_THUMB_HEIGHT,
    LIST_THUMB_WIDTH,
    WatchedDetailCard,
    _elide_text,
    _load_list_thumb_pixmap,
)

logger = logging.getLogger(__name__)


def build_candidate_list_item_delegate(parent, sort_mode: str):
    """Card-style list row like Watched: thumbnail, title, year and sort metric."""
    from PyQt6.QtCore import QRect, QSize, Qt
    from PyQt6.QtGui import QColor, QFont, QPainter, QPen
    from PyQt6.QtWidgets import QStyledItemDelegate, QStyle

    from desktop.theme import (
        COLOR_ACCENT,
        COLOR_ACCENT_SOFT,
        COLOR_BORDER,
        COLOR_CARD,
        COLOR_CARD_ALT,
        COLOR_TEXT,
        COLOR_TEXT_SECONDARY,
        FONT_FAMILY,
    )

    mode = sort_mode

    class CandidateListItemDelegate(QStyledItemDelegate):
        def sizeHint(self, option, index):
            width = option.rect.width() if option.rect.width() > 0 else 280
            return QSize(width, LIST_ITEM_HEIGHT)

        def paint(self, painter, option, index) -> None:
            candidate = index.data(Qt.ItemDataRole.UserRole)
            if not isinstance(candidate, dict):
                super().paint(painter, option, index)
                return

            rect = option.rect.adjusted(2, 1, -2, -1)
            is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
            is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)

            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

            if is_selected:
                painter.setPen(QPen(QColor(COLOR_ACCENT), 2))
                painter.setBrush(QColor(COLOR_ACCENT_SOFT))
            elif is_hovered:
                painter.setPen(QPen(QColor(COLOR_BORDER), 1))
                painter.setBrush(QColor(COLOR_CARD_ALT))
            else:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(Qt.BrushStyle.NoBrush)

            if is_selected or is_hovered:
                painter.drawRoundedRect(rect, 10, 10)

            thumb_left = rect.left() + LIST_ITEM_H_PADDING
            thumb_top = rect.top() + (rect.height() - LIST_THUMB_HEIGHT) // 2
            thumb_rect = QRect(thumb_left, thumb_top, LIST_THUMB_WIDTH, LIST_THUMB_HEIGHT)

            poster_path = resolve_local_poster_path_for_candidate(candidate)
            thumb = _load_list_thumb_pixmap(poster_path)
            if thumb is not None:
                clip = thumb_rect.adjusted(1, 1, -1, -1)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(COLOR_CARD))
                painter.drawRoundedRect(clip, 6, 6)
                painter.drawPixmap(clip, thumb)
            else:
                painter.setPen(QPen(QColor(COLOR_BORDER), 1))
                painter.setBrush(QColor(COLOR_CARD))
                painter.drawRoundedRect(thumb_rect, 6, 6)
                placeholder_font = QFont(FONT_FAMILY, 8)
                painter.setFont(placeholder_font)
                painter.setPen(QColor(COLOR_TEXT_SECONDARY))
                painter.drawText(thumb_rect, Qt.AlignmentFlag.AlignCenter, "—")

            text_left = thumb_rect.right() + LIST_TEXT_GAP
            text_right = rect.right() - LIST_ITEM_H_PADDING
            text_width = max(40, text_right - text_left)

            title = str(candidate.get("title") or candidate.get("name") or "Без названия")
            year = candidate.get("year")
            year_text = str(year) if year not in (None, "") else ""
            metric_text = format_candidate_metric_value(candidate, mode)
            meta_parts = [part for part in (year_text, metric_text if metric_text != "—" else "") if part]
            meta_text = " · ".join(meta_parts)

            title_font = QFont(FONT_FAMILY)
            title_font.setPointSize(10)
            title_font.setBold(True)
            meta_font = QFont(FONT_FAMILY)
            meta_font.setPointSize(9)

            title_rect = QRect(text_left, rect.top() + LIST_ITEM_V_PADDING, text_width, 28)
            meta_rect = QRect(text_left, title_rect.bottom(), text_width, 20)

            painter.setFont(title_font)
            painter.setPen(QColor(COLOR_TEXT))
            painter.drawText(
                title_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                _elide_text(painter, title, title_rect.width()),
            )

            if meta_text:
                painter.setFont(meta_font)
                painter.setPen(QColor(COLOR_ACCENT if is_selected else COLOR_TEXT_SECONDARY))
                painter.drawText(
                    meta_rect,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    meta_text,
                )

            painter.restore()

    return CandidateListItemDelegate(parent)


class CandidateListView:
    """Candidates tab: sort controls, card list, read-only detail card."""

    def __init__(self, session: CandidateSearchSession) -> None:
        self._session = session
        self._candidates: list[dict] = []
        self._detail_entries: dict[str, tuple] = {}
        self._poster_request_seq = 0
        self._poster_worker: CandidatePosterDownloadWorker | None = None
        self._delegate = build_candidate_list_item_delegate(None, session.sort_mode)

        self._widget = QWidget()
        self._widget.setObjectName("candidateListRoot")
        root_layout = QVBoxLayout(self._widget)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        controls = QVBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(6)

        sort_row = QHBoxLayout()
        sort_row.setSpacing(10)

        sort_label = QLabel("Сортировка")
        sort_label.setObjectName("candidateSearchFieldLabel")
        self._sort_combo = QComboBox()
        self._sort_combo.setObjectName("candidateListSort")
        for mode in candidate_service.SEARCH_SORT_MODES:
            self._sort_combo.addItem(
                candidate_service.SEARCH_SORT_MODE_LABELS[mode],
                mode,
            )
        self._sort_combo.setCurrentIndex(0)
        self._sort_combo.currentIndexChanged.connect(self._on_sort_changed)

        top_n_label = QLabel("Топ N")
        top_n_label.setObjectName("candidateSearchFieldLabel")
        self._top_n_spin = QSpinBox()
        self._top_n_spin.setObjectName("candidateSearchTopN")
        self._top_n_spin.setRange(1, 500)
        self._top_n_spin.setValue(DEFAULT_TOP_N)
        self._top_n_spin.valueChanged.connect(self._on_top_n_changed)

        sort_row.addWidget(sort_label)
        sort_row.addWidget(self._sort_combo, stretch=1)
        sort_row.addSpacing(12)
        sort_row.addWidget(top_n_label)
        sort_row.addWidget(self._top_n_spin)
        controls.addLayout(sort_row)

        self._counter_label = QLabel("")
        self._counter_label.setObjectName("candidateListCounter")
        controls.addWidget(self._counter_label)
        root_layout.addLayout(controls)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter, stretch=1)

        list_panel = QWidget()
        list_panel.setObjectName("candidateSearchResultsPanel")
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        self._results_list = QListWidget()
        self._results_list.setObjectName("candidateListWidget")
        self._results_list.setSpacing(2)
        self._results_list.setUniformItemSizes(True)
        self._results_list.setItemDelegate(self._delegate)
        self._results_list.currentRowChanged.connect(self._on_result_selected)
        list_layout.addWidget(self._results_list)
        splitter.addWidget(list_panel)

        detail_panel = QWidget()
        detail_panel.setObjectName("candidateSearchDetailPanel")
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(0)

        self._detail_placeholder = QLabel("Сначала примените фильтры на вкладке «Фильтры»")
        self._detail_placeholder.setObjectName("candidateSearchDetailPlaceholder")
        self._detail_placeholder.setWordWrap(True)
        self._detail_placeholder.setAlignment(Qt.AlignmentFlag.AlignTop)
        detail_layout.addWidget(self._detail_placeholder)

        scroll = QScrollArea()
        scroll.setObjectName("candidateSearchDetailScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self._detail_card = WatchedDetailCard(profile=CANDIDATE_DETAIL_CARD_PROFILE)
        scroll.setWidget(self._detail_card.widget)
        scroll.hide()
        self._detail_scroll = scroll
        detail_layout.addWidget(scroll, stretch=1)

        splitter.addWidget(detail_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([560, 560])

        session.add_listener(self.refresh)
        self.refresh()

    @property
    def widget(self) -> QWidget:
        return self._widget

    def _on_sort_changed(self, _index: int) -> None:
        mode = self._sort_combo.currentData()
        if mode in candidate_service.SEARCH_SORT_MODES:
            self._session.set_sort_mode(str(mode))
            self._delegate = build_candidate_list_item_delegate(self._results_list, self._session.sort_mode)
            self._results_list.setItemDelegate(self._delegate)
            self._results_list.viewport().update()

    def _on_top_n_changed(self, value: int) -> None:
        self._session.set_top_n(value)

    def refresh(self) -> None:
        self._poster_request_seq += 1
        if not self._session.has_results:
            self._candidates = []
            self._detail_entries = {}
            self._results_list.clear()
            self._counter_label.setText("")
            self._clear_detail(show_filters_hint=True)
            return

        self._candidates = self._session.sorted_candidates()
        total = self._session.sorted_total_count()
        pool_stats = candidate_service.get_pool_stats_view()["stats"]
        unique_total = pool_stats.get("unique_total", pool_stats.get("storage_total", 0))
        self._detail_entries = {
            candidate_detail_identity(candidate): build_candidate_readonly_detail_entry(candidate)
            for candidate in self._candidates
        }

        self._results_list.blockSignals(True)
        self._results_list.clear()
        if len(self._candidates) == 0:
            self._counter_label.setText("Показано 0")
            self._clear_detail(show_filters_hint=False)
        else:
            dup_note = ""
            if self._session.hidden_duplicates > 0:
                dup_note = f" · дублей скрыто: {self._session.hidden_duplicates}"
            self._counter_label.setText(
                f"Показано {len(self._candidates)} из {total} · уникальных в pool: {unique_total}{dup_note}"
            )
            for candidate in self._candidates:
                from PyQt6.QtWidgets import QListWidgetItem

                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, candidate)
                self._results_list.addItem(item)
            self._clear_detail(show_filters_hint=False)
        self._results_list.blockSignals(False)

        if self._results_list.count() > 0:
            self._results_list.setCurrentRow(0)
        elif not self._session.has_results:
            self._clear_detail(show_filters_hint=True)

    def _on_result_selected(self, row: int) -> None:
        started = perf_counter()
        if row < 0 or row >= len(self._candidates):
            if self._session.has_results and len(self._candidates) == 0:
                self._clear_detail(show_filters_hint=False)
            else:
                self._clear_detail(show_filters_hint=not self._session.has_results)
            return

        candidate = self._candidates[row]
        lookup_done = perf_counter()

        identity = candidate_detail_identity(candidate)
        self._poster_request_seq += 1
        request_seq = self._poster_request_seq
        entry = self._detail_entries.get(identity)
        if entry is None:
            entry = build_candidate_readonly_detail_entry(candidate)
            self._detail_entries[identity] = entry
        build_done = perf_counter()

        self._detail_placeholder.hide()
        self._detail_scroll.show()
        self._detail_card.show_entry(entry)
        render_done = perf_counter()

        poster_url = candidate_poster_url_for_download(candidate)
        if poster_url not in (None, ""):
            self._start_poster_download(poster_url, identity, request_seq)

        total_ms = (render_done - started) * 1000
        if total_ms >= 50:
            logger.info(
                "candidate selection row=%s: lookup=%.1fms card=%.1fms render=%.1fms total=%.1fms",
                row,
                (lookup_done - started) * 1000,
                (build_done - lookup_done) * 1000,
                (render_done - build_done) * 1000,
                total_ms,
            )

    def _start_poster_download(self, poster_url: str, identity: str, request_seq: int) -> None:
        worker = CandidatePosterDownloadWorker(poster_url, parent=self._widget)
        worker.finished_with_path.connect(
            lambda local_path, seq=request_seq, ident=identity: self._on_poster_download_finished(
                seq,
                ident,
                local_path,
            )
        )
        worker.finished.connect(worker.deleteLater)
        self._poster_worker = worker
        worker.start()

    def _on_poster_download_finished(self, request_seq: int, identity: str, local_path: str) -> None:
        if request_seq != self._poster_request_seq:
            return

        entry = self._detail_entries.get(identity)
        if entry is not None:
            entry_key, movie, card = entry
            updated_card = dict(card)
            updated_card["poster_path"] = local_path
            updated_card["poster_src"] = local_path
            self._detail_entries[identity] = (entry_key, movie, updated_card)

        self._detail_card.apply_local_poster_path(local_path)
        self._results_list.viewport().update()

    def _clear_detail(self, *, show_filters_hint: bool) -> None:
        self._poster_request_seq += 1
        self._detail_scroll.hide()
        if show_filters_hint:
            self._detail_placeholder.setText("Сначала примените фильтры на вкладке «Фильтры»")
            self._detail_placeholder.show()
        elif self._session.has_results and len(self._candidates) == 0:
            self._detail_placeholder.setText("Нет кандидатов после фильтра.")
            self._detail_placeholder.show()
        else:
            self._detail_placeholder.setText("Выберите кандидата из списка")
            self._detail_placeholder.show()
