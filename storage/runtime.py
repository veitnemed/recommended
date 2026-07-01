"""Runtime data layout initialization."""

from __future__ import annotations

import os

from config import constant


RUNTIME_DIRECTORIES = (
    constant.APP_DATA_DIR,
    constant.WATCHED_DIR,
    constant.CANDIDATES_DIR,
    constant.CACHE_DIR,
    constant.EXPORTS_DIR,
    constant.LOGS_DIR,
    constant.BACKUP_DIR,
)


def ensure_runtime_directories() -> list[str]:
    """Create standard runtime directories and return their paths."""
    created_or_existing = []
    for directory in RUNTIME_DIRECTORIES:
        os.makedirs(directory, exist_ok=True)
        created_or_existing.append(directory)
    return created_or_existing


def ensure_runtime_data_layout(*, create_initial_backup: bool = False) -> dict:
    """Initialize runtime JSON files and directories through one public entrypoint."""
    from app.core.storage import init_search_lists
    from candidates.repositories.criteria_repository import init_candidate_criteria
    from candidates.repositories.pool_repository import init_candidate_pool
    from storage.data import init_dataset, init_meta

    directories = ensure_runtime_directories()
    init_meta()
    init_dataset()
    init_candidate_criteria()
    init_candidate_pool()
    init_search_lists()

    backup_created = False
    if create_initial_backup:
        from storage.files import create_backup

        create_backup()
        backup_created = True

    return {
        "ok": True,
        "directories": directories,
        "backup_created": backup_created,
    }
