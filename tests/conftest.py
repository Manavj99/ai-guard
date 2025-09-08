import pathlib
import random
import os
import pytest


@pytest.fixture(autouse=True)
def deterministic_env():
    os.environ["PYTHONHASHSEED"] = "0"
    random.seed(1337)


@pytest.fixture
def load_fixture():
    base = pathlib.Path(__file__).parent / "fixtures"

    def _loader(name: str) -> str:
        return (base / name).read_text(encoding="utf-8")

    return _loader
