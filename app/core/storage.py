"""Small JSON lists for local search actions: watchlist and hidden candidates."""

from __future__ import annotations

import json
import os
from datetime import datetime

from candidates.keys import title_identity_key
from candidates.schema import normalize_candidate_record
from config import constant
from storage import data as storage_data


WATCHLIST_JSON = os.path.join(constant.CANDIDATES_DIR, "watchlist.json")
HIDDEN_JSON = os.path.join(constant.CANDIDATES_DIR, "hidden.json")


def _init_json(path: str) -> None:
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump({}, file, ensure_ascii=False, indent=4)


def init_search_lists() -> None:
    """Creates local search list JSON files when missing."""
    _init_json(WATCHLIST_JSON)
    _init_json(HIDDEN_JSON)


def _load_mapping(path: str) -> dict:
    _init_json(path)
    with open(path, "r", encoding="utf-8-sig") as file:
        data = json.load(file)
    return data if isinstance(data, dict) else {}


def _save_mapping(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def _entry(candidate: dict, action: str) -> dict:
    normalized = normalize_candidate_record(candidate)
    return {
        "candidate": normalized,
        f"{action}_at": datetime.now().isoformat(timespec="seconds"),
    }


def add_to_watchlist(candidate: dict) -> dict:
    """Adds a candidate to the local watchlist."""
    data = _load_mapping(WATCHLIST_JSON)
    identity = title_identity_key(candidate)
    data[identity] = _entry(candidate, "added")
    _save_mapping(WATCHLIST_JSON, data)
    return {"ok": True, "identity": identity, "count": len(data)}


def add_to_hidden(candidate: dict) -> dict:
    """Adds a candidate to the hidden list."""
    data = _load_mapping(HIDDEN_JSON)
    identity = title_identity_key(candidate)
    data[identity] = _entry(candidate, "hidden")
    _save_mapping(HIDDEN_JSON, data)
    return {"ok": True, "identity": identity, "count": len(data)}


def load_hidden_identities() -> set[str]:
    return set(_load_mapping(HIDDEN_JSON).keys())


def load_watchlist_identities() -> set[str]:
    return set(_load_mapping(WATCHLIST_JSON).keys())


def load_watched_identities() -> set[str]:
    dataset = storage_data.load_dataset()
    identities = set()
    for dataset_key, movie in dataset.items():
        main_info = movie.get("main_info", {}) if isinstance(movie, dict) else {}
        identity = title_identity_key({
            "title": main_info.get("title") or dataset_key,
            "year": main_info.get("year"),
        })
        if identity != "|":
            identities.add(identity)
    return identities
