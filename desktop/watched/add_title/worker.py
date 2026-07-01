"""Background worker for add-title resolve in desktop GUI."""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from dataset.add_title_service import AddTitleResolveBundle, resolve_title_for_add


class AddTitleResolveWorker(QThread):
    """Resolve title metadata off the UI thread."""

    progress = pyqtSignal(int, int, str)
    finished_with_result = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, title: str, country: str, parent=None) -> None:
        super().__init__(parent)
        self._title = title
        self._country = country

    def run(self) -> None:
        try:
            bundle = resolve_title_for_add(
                self._title,
                self._country,
                on_progress=self._on_progress,
            )
        except Exception as error:  # noqa: BLE001 - surface to dialog
            self.failed.emit(str(error))
            return
        self.finished_with_result.emit(bundle)

    def _on_progress(self, current: int, total: int, message: str) -> None:
        self.progress.emit(current, total, message)
