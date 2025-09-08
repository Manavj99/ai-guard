"""Unit tests for SARIF parser helpers in analyzer."""

from ai_guard.analyzer import (
    _parse_flake8_output,
    _parse_mypy_output,
    _parse_bandit_json,
)


def _first_location_uri(result) -> str:
    return result.locations[0]["physicalLocation"]["artifactLocation"]["uri"]


def _first_location_region(result):
    return result.locations[0]["physicalLocation"].get("region", {})


def test_parse_flake8_output_basic():
    output = (
        "src/ai_guard/example.py:10:5: E999 SyntaxError: invalid syntax\n"
        "tests/unit/test_example.py:3:1: F401 'os' imported but unused\n"
    )
    results = _parse_flake8_output(output)
    assert len(results) == 2

    r0 = results[0]
    assert r0.rule_id.startswith("flake8:E999")
    assert r0.level == "warning"
    assert _first_location_uri(r0) == "src/ai_guard/example.py"
    region0 = _first_location_region(r0)
    assert region0.get("startLine") == 10
    assert region0.get("startColumn") == 5

    r1 = results[1]
    assert r1.rule_id.startswith("flake8:F401")
    assert _first_location_uri(r1) == "tests/unit/test_example.py"


def test_parse_mypy_output_basic():
    output = (
        "src/ai_guard/example.py:12: error: Incompatible return value type "
        "[return-value]\n"
        "src/ai_guard/other.py:22:7: warning: Name 'x' is not defined [name-defined]\n"
        "Note: Some notes here\n"
    )
    results = _parse_mypy_output(output)
    # Only lines matching our pattern produce results (notes are skipped)
    assert len(results) == 2

    r0 = results[0]
    assert r0.rule_id.startswith("mypy:return-value")
    assert r0.level == "error"
    assert _first_location_uri(r0) == "src/ai_guard/example.py"
    assert _first_location_region(r0).get("startLine") == 12

    r1 = results[1]
    assert r1.level in ("warning", "note")
    assert _first_location_uri(r1) == "src/ai_guard/other.py"
    assert _first_location_region(r1).get("startLine") == 22


def test_parse_bandit_json_basic():
    bandit_json = {
        "results": [
            {
                "filename": "src/ai_guard/secret.py",
                "line_number": 8,
                "issue_severity": "HIGH",
                "issue_text": "Use of insecure function",
                "test_id": "B102",
            },
            {
                "filename": "src/ai_guard/mid.py",
                "line_number": 20,
                "issue_severity": "MEDIUM",
                "issue_text": "Potential vulnerability",
                "test_id": "B301",
            },
        ]
    }

    import json as _json

    results = _parse_bandit_json(_json.dumps(bandit_json))
    assert len(results) == 2

    high = results[0]
    assert high.rule_id == "bandit:B102"
    assert high.level == "error"
    assert _first_location_uri(high) == "src/ai_guard/secret.py"
    assert _first_location_region(high).get("startLine") == 8

    med = results[1]
    assert med.rule_id == "bandit:B301"
    assert med.level == "warning"
    assert _first_location_uri(med) == "src/ai_guard/mid.py"
    assert _first_location_region(med).get("startLine") == 20
