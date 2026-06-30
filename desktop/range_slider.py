"""Compact two-handle horizontal range slider for desktop filters."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from desktop.theme import (
    COLOR_ACCENT,
    COLOR_ACCENT_SOFT,
    COLOR_BORDER,
    COLOR_CARD_ALT,
    COLOR_TEXT,
)


class RangeSlider(QWidget):
    """Compact two-handle horizontal range slider."""

    rangeChanged = pyqtSignal(int, int)

    def __init__(self, minimum: int, maximum: int, lower: int, upper: int, parent=None) -> None:
        super().__init__(parent)
        self._minimum = minimum
        self._maximum = maximum
        self._lower = lower
        self._upper = upper
        self._active_handle = "lower"
        self._dragging = False
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumHeight(30)

    def sizeHint(self) -> QSize:
        return QSize(180, 30)

    def values(self) -> tuple[int, int]:
        return (self._lower, self._upper)

    def setValues(self, lower: int, upper: int) -> None:
        lower = self._clamp(lower)
        upper = self._clamp(upper)
        if lower > upper:
            lower, upper = upper, lower
        if (lower, upper) == (self._lower, self._upper):
            return
        self._lower = lower
        self._upper = upper
        self.update()
        self.rangeChanged.emit(self._lower, self._upper)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        handle_radius = 7
        track_height = 4
        left = handle_radius + 2
        right = self.width() - handle_radius - 2
        center_y = self.height() / 2

        track = QRectF(left, center_y - track_height / 2, right - left, track_height)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLOR_CARD_ALT))
        painter.drawRoundedRect(track, track_height / 2, track_height / 2)

        lower_x = self._x_from_value(self._lower)
        upper_x = self._x_from_value(self._upper)
        active = QRectF(lower_x, center_y - track_height / 2, upper_x - lower_x, track_height)
        painter.setBrush(QColor(COLOR_ACCENT_SOFT))
        painter.drawRoundedRect(active, track_height / 2, track_height / 2)

        handle_pen = QPen(QColor(COLOR_BORDER), 1)
        for x in (lower_x, upper_x):
            painter.setPen(handle_pen)
            painter.setBrush(QColor(COLOR_ACCENT))
            painter.drawEllipse(
                QRectF(x - handle_radius, center_y - handle_radius, handle_radius * 2, handle_radius * 2)
            )
            painter.setPen(QPen(QColor(COLOR_TEXT), 1))
            painter.drawEllipse(QRectF(x - 2, center_y - 2, 4, 4))

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        lower_distance = abs(event.position().x() - self._x_from_value(self._lower))
        upper_distance = abs(event.position().x() - self._x_from_value(self._upper))
        self._active_handle = "lower" if lower_distance <= upper_distance else "upper"
        self._dragging = True
        self._move_active_handle(event.position().x())

    def mouseMoveEvent(self, event) -> None:
        if self._dragging:
            self._move_active_handle(event.position().x())

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False

    def keyPressEvent(self, event) -> None:
        if event.key() not in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            super().keyPressEvent(event)
            return
        delta = -1 if event.key() == Qt.Key.Key_Left else 1
        if self._active_handle == "lower":
            self.setValues(min(self._lower + delta, self._upper), self._upper)
        else:
            self.setValues(self._lower, max(self._upper + delta, self._lower))

    def _move_active_handle(self, x: float) -> None:
        value = self._value_from_x(x)
        if self._active_handle == "lower":
            self.setValues(min(value, self._upper), self._upper)
        else:
            self.setValues(self._lower, max(value, self._lower))

    def _clamp(self, value: int) -> int:
        return max(self._minimum, min(self._maximum, int(value)))

    def _x_from_value(self, value: int) -> float:
        handle_radius = 7
        left = handle_radius + 2
        right = self.width() - handle_radius - 2
        if self._maximum == self._minimum:
            return left
        ratio = (value - self._minimum) / (self._maximum - self._minimum)
        return left + ratio * (right - left)

    def _value_from_x(self, x: float) -> int:
        handle_radius = 7
        left = handle_radius + 2
        right = self.width() - handle_radius - 2
        if right <= left:
            return self._minimum
        ratio = max(0.0, min(1.0, (x - left) / (right - left)))
        return round(self._minimum + ratio * (self._maximum - self._minimum))
