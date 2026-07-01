from storage import data as storage_data


def _patch_storage_paths(monkeypatch, tmp_path) -> None:
    watched_dir = tmp_path / "watched"
    titles_json = watched_dir / "titles.json"
    meta_json = watched_dir / "meta.json"

    monkeypatch.setattr(storage_data.constant, "DATA_DIR", str(watched_dir))
    monkeypatch.setattr(storage_data.constant, "DIR_META", str(watched_dir))
    monkeypatch.setattr(storage_data.constant, "FILE_NAME", str(titles_json))
    monkeypatch.setattr(storage_data.constant, "META_JSON", str(meta_json))


def test_add_movies_to_meta_returns_false_without_printing(monkeypatch, tmp_path, capsys) -> None:
    _patch_storage_paths(monkeypatch, tmp_path)

    result = storage_data.add_movies_to_meta(
        {"title": "", "user_score": 8.0, "year": 2020},
        {},
    )

    assert result is False
    assert capsys.readouterr().out == ""


def test_rename_movie_title_returns_false_without_printing(monkeypatch, tmp_path, capsys) -> None:
    _patch_storage_paths(monkeypatch, tmp_path)

    result = storage_data.rename_movie_title("Missing", "New Title")

    assert result is False
    assert capsys.readouterr().out == ""
