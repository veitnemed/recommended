"""Background worker for candidate poster preview download in desktop GUI."""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from posters.download_images import download_poster_url_for_preview


class CandidatePosterDownloadWorker(QThread):
    """Download one candidate poster URL into preview cache off the UI thread."""

    finished_with_path = pyqtSignal(str)
    failed = pyqtSignal()

    def __init__(self, poster_url: str, parent=None) -> None:
        super().__init__(parent)
        self._poster_url = poster_url

    def run(self) -> None:
        local_path = download_poster_url_for_preview(self._poster_url)
        if local_path not in (None, ""):
            self.finished_with_path.emit(str(local_path))
            return
        self.failed.emit()
