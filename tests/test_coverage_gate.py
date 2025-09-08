from ai_guard.gates.coverage_eval import evaluate_coverage_str


def test_coverage_fails_below_threshold(load_fixture):
    xml = load_fixture("coverage_low.xml")
    res = evaluate_coverage_str(xml, threshold=80.0)
    assert res.passed is False
    assert res.percent < 80.0


def test_coverage_passes_threshold(load_fixture):
    xml = load_fixture("coverage_ok.xml")
    res = evaluate_coverage_str(xml, threshold=80.0)
    assert res.passed is True
    assert res.percent >= 80.0
