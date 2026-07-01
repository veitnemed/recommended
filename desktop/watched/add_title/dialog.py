"""Add-title flow: backward-compatible re-exports."""

from desktop.watched.add_title.flow import AddTitleDialog, run_add_title_flow, run_candidate_transfer_flow
from desktop.watched.add_title.preview_dialog import AddTitlePreviewDialog
from desktop.watched.add_title.search_dialog import AddTitleSearchDialog

__all__ = [
    "AddTitleDialog",
    "AddTitlePreviewDialog",
    "AddTitleSearchDialog",
    "run_add_title_flow",
    "run_candidate_transfer_flow",
]
