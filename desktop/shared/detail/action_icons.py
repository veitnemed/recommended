"""Small painted icons for title detail-card action buttons."""

from __future__ import annotations


def make_detail_action_icon(kind: str, color: str, disabled_color: str | None = None):
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

    icon = QIcon()
    for mode, item_color in (
        (QIcon.Mode.Normal, color),
        (QIcon.Mode.Disabled, disabled_color or color),
    ):
        pixmap = QPixmap(28, 28)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen()
        pen.setColor(Qt.GlobalColor.transparent)
        painter.setPen(pen)

        draw_pen = QPen()
        draw_pen.setColor(QColor(item_color))
        draw_pen.setWidthF(2.0)
        draw_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        draw_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(draw_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if kind == "eye":
            path = QPainterPath()
            path.moveTo(4, 14)
            path.cubicTo(8, 7, 20, 7, 24, 14)
            path.cubicTo(20, 21, 8, 21, 4, 14)
            painter.drawPath(path)
            painter.drawEllipse(10, 10, 8, 8)
            painter.setBrush(QColor(item_color))
            painter.drawEllipse(13, 13, 2, 2)
        elif kind == "hide":
            painter.drawEllipse(6, 6, 16, 16)
            painter.drawLine(9, 19, 19, 9)

        painter.end()
        icon.addPixmap(pixmap, mode)
    return icon
