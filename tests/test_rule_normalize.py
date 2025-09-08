import pytest
from ai_guard.parsers.common import normalize_rule


@pytest.mark.parametrize(
    "tool,raw,exp",
    [
        ("flake8", "E501", "flake8:E501"),
        ("mypy", "error[name-defined]", "mypy:name-defined"),
        ("mypy", "name-defined", "mypy:name-defined"),
        ("bandit", "B101", "bandit:B101"),
        ("eslint", "no-unused-vars", "eslint:no-unused-vars"),
        ("jest", "something", "jest:something"),
    ],
)
def test_normalize_rule(tool, raw, exp):
    assert normalize_rule(tool, raw) == exp
