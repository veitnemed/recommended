"""Desktop application bootstrap and entry point."""

from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from desktop.shell.main_window import WatchedMoviesWindow
from desktop.theme import FONT_FAMILY


def _prepare_webengine() -> None:
    """Prepare Qt WebEngine before QApplication is created."""
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    try:
        from PyQt6 import QtWebEngineWidgets  # noqa: F401
    except ImportError:
        pass


def main() -> None:
    _prepare_webengine()
    app = QApplication(sys.argv)
    app.setFont(QFont(FONT_FAMILY, 10))
    window = WatchedMoviesWindow()
    window.show()
    sys.exit(app.exec())
