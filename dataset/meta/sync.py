"""Sync watched raw_scores/main_info into meta.json."""

from dataset.meta.lookup import find_meta_title
from storage.data import load_meta, save_meta
from storage.normalize import normalize_main_info, normalize_raw_scores


def sync_raw_scores_to_meta(title: str, main_info: dict, raw_scores: dict) -> None:
    """Update or create meta entry with normalized main_info and raw_scores."""
    meta = load_meta()
    meta_title = find_meta_title(meta, title)

    meta_obj = {
        "main_info": normalize_main_info(main_info),
        "raw_scores": normalize_raw_scores(raw_scores),
    }
    if meta_title is None:
        meta[title] = meta_obj
    else:
        current_meta = dict(meta[meta_title])
        current_meta["main_info"] = meta_obj["main_info"]
        current_meta["raw_scores"] = meta_obj["raw_scores"]
        meta[meta_title] = current_meta

    save_meta(meta)
