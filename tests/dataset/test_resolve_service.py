"""Tests for add-title resolve orchestration boundaries."""

from dataset.resolve import service as resolve_service


def test_resolve_title_data_for_add_is_quiet_without_progress_callback(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        resolve_service.sql_search,
        "search_title_in_sql",
        lambda title, country: {"ok": False, "data": None, "details": "not_found"},
    )
    monkeypatch.setattr(
        resolve_service.api,
        "find_series_raw",
        lambda query, country: {"ok": False, "error": "not_found", "details": "not_found"},
    )
    monkeypatch.setattr(
        resolve_service,
        "search_tmdb_defaults_data",
        lambda queries: {"data": None, "error": None, "status": "not_found"},
    )

    result = resolve_service.resolve_title_data_for_add("Missing", "RU")

    assert result["found"] is False
    assert capsys.readouterr().out == ""


def test_resolve_title_data_for_add_reports_progress_to_callback(monkeypatch) -> None:
    monkeypatch.setattr(
        resolve_service.sql_search,
        "search_title_in_sql",
        lambda title, country: {"ok": False, "data": None, "details": "not_found"},
    )
    monkeypatch.setattr(
        resolve_service.api,
        "find_series_raw",
        lambda query, country: {"ok": False, "error": "not_found", "details": "not_found"},
    )
    monkeypatch.setattr(
        resolve_service,
        "search_tmdb_defaults_data",
        lambda queries: {"data": None, "error": None, "status": "not_found"},
    )
    progress_messages = []

    resolve_service.resolve_title_data_for_add(
        "Missing",
        "RU",
        on_progress=lambda step, total, message: progress_messages.append((step, total, message)),
    )

    assert progress_messages
    assert progress_messages[-1][0] == resolve_service.ADD_TITLE_RESOLVE_PROGRESS_TOTAL
