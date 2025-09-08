from ai_guard.parsers.typescript import parse_eslint, parse_jest


def test_parse_eslint_json():
    out = (
        '[{"filePath":"a.ts","messages":['
        '{"ruleId":"no-unused-vars","severity":2,"message":"x unused","line":3,"column":7}'
        "]}]"
    )
    res = parse_eslint(out)
    assert len(res) == 1
    f = res[0]
    assert f["rule"] == "eslint:no-unused-vars"
    assert f["severity"] == "error"
    assert f["file"].endswith("a.ts")
    assert f["line"] == 3 and f["col"] == 7


def test_parse_eslint_stylish():
    out = "/repo/a.ts:3:7  error  x unused  no-unused-vars"
    res = parse_eslint(out)
    assert len(res) == 1
    f = res[0]
    assert f["rule"] == "eslint:no-unused-vars"
    assert f["severity"] == "error"


def test_parse_jest_human():
    out = "Tests:       1 failed, 12 passed, 13 total"
    res = parse_jest(out)
    assert res["failed"] == 1
    assert res["passed"] == 12
    assert res["tests"] == 13
