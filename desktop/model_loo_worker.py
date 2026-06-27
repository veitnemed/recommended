"""Background worker for explicit LOO training in the desktop GUI."""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal


class LooTrainingWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished_with_result = pyqtSignal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._cancel_requested = False

    def request_cancel(self) -> None:
        self._cancel_requested = True

    def run(self) -> None:
        from model import linear_regression_train
        from storage import data as storage_data

        data = storage_data.load_dataset()
        weights = storage_data.load_weights()

        def on_progress(current: int, total: int, message: str) -> None:
            self.progress.emit(current, total, message)

        result = linear_regression_train.execute_explicit_loo_training(
            data=data,
            weights=weights,
            on_progress=on_progress,
            should_cancel=lambda: self._cancel_requested,
            verbose=False,
        )
        self.finished_with_result.emit(result)
