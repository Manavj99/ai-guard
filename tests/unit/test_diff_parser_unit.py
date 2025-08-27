from pathlib import Path
import json

from src.ai_guard.diff_parser import parse_github_event, _get_base_head_from_event


def test_parse_github_event_roundtrip(tmp_path: Path):
    event = {
        "pull_request": {
            "base": {"sha": "base123"},
            "head": {"sha": "head456"},
        }
    }
    p = tmp_path / "event.json"
    p.write_text(json.dumps(event), encoding="utf-8")
    parsed = parse_github_event(str(p))
    assert parsed["pull_request"]["base"]["sha"] == "base123"
    assert _get_base_head_from_event(str(p)) == ("base123", "head456")


