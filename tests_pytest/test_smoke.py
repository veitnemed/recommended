import json
import tempfile
from pathlib import Path


def test_tmp_path_can_write_utf8_json() -> None:
    payload = {"title": "Во все тяжкие"}

    with tempfile.TemporaryDirectory() as temp_root:
        path = Path(temp_root) / "test.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        raw_text = path.read_text(encoding="utf-8")

    assert "Во все тяжкие" in raw_text
    assert "\\u0412" not in raw_text
