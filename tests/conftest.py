import pathlib
import random
import os
import sys
import pytest

# Add src directory to Python path for imports
_project_root = pathlib.Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))


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
