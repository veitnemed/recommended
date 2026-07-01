"""Add-title and candidate-transfer flow orchestration."""

from __future__ import annotations

from PyQt6.QtWidgets import QDialog

from dataset import service
from desktop.watched.add_title.preview_dialog import AddTitlePreviewDialog
from desktop.watched.add_title.search_dialog import AddTitleSearchDialog


def run_candidate_transfer_flow(parent, candidate: dict):
    """Open preview dialog for pool candidate transfer; returns save result or None."""
    if not isinstance(candidate, dict):
        return None
    bundle = service.build_candidate_transfer_bundle(candidate)
    preview_dialog = AddTitlePreviewDialog(bundle, parent, transfer_mode=True)
    if preview_dialog.exec() == QDialog.DialogCode.Accepted:
        return preview_dialog.save_result
    return None


def run_add_title_flow(parent=None):
    """Open search dialog, then preview dialog; loop back on «Искать другой»."""
    initial_title = ""
    initial_country = ""

    while True:
        search_dialog = AddTitleSearchDialog(
            parent,
            initial_title=initial_title,
            initial_country=initial_country,
        )
        if search_dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        bundle = search_dialog.resolve_bundle
        if bundle is None:
            return None

        preview_dialog = AddTitlePreviewDialog(bundle, parent)
        if preview_dialog.exec() == QDialog.DialogCode.Accepted:
            return preview_dialog.save_result

        if preview_dialog.search_again is False:
            return None

        initial_title = search_dialog.last_title
        initial_country = search_dialog.last_country


class AddTitleDialog:
    """Backward-compatible entry: runs the two-dialog flow."""

    def __init__(self, parent=None) -> None:
        self._parent = parent
        self._save_result = None

    @property
    def save_result(self):
        return self._save_result

    def exec(self) -> int:
        result = run_add_title_flow(self._parent)
        if result is None:
            return QDialog.DialogCode.Rejected
        self._save_result = result
        return QDialog.DialogCode.Accepted
