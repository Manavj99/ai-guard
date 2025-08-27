from pathlib import Path
import json

from src.ai_guard.report import GateResult, summarize
from src.ai_guard.sarif_report import make_location, write_sarif, SarifRun, SarifResult


def test_summarize_outputs_and_exit_code(capsys):
    results = [
        GateResult("Lint (flake8)", True, "ok"),
        GateResult("Static types (mypy)", False, "failed"),
    ]
    code = summarize(results)
    captured = capsys.readouterr().out
    assert "AI-Guard Quality Gates Summary" in captured
    assert "❌" in captured
    assert code == 1


def test_sarif_write_and_location(tmp_path: Path):
    loc = make_location("file.py", 10, 2)
    result = SarifResult(rule_id="flake8:E999", level="error", message="boom", locations=[loc])
    out = tmp_path / "out.sarif"
    write_sarif(str(out), SarifRun(tool_name="ai-guard", results=[result]))
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["version"] == "2.1.0"
    runs = data["runs"][0]
    assert runs["tool"]["driver"]["name"] == "ai-guard"
    res = runs["results"][0]
    assert res["ruleId"] == "flake8:E999"
    assert res["level"] == "error"
    assert res["message"]["text"] == "boom"
    region = res["locations"][0]["physicalLocation"]["region"]
    assert region["startLine"] == 10
    assert region["startColumn"] == 2
