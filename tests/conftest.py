from pathlib import Path
from typing import Any
import pytest

from yaml_extras.file_utils import PathPattern


@pytest.fixture
def tmp_chdir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        yield tmp_path


@pytest.fixture
def loose_equality_for_lists():
    """When two objects contain one or more lists, compare the lists without order and return the
    resulting equality of the two objects.

    Args:
        data1 (Any): Loose-equality operand object which may contain one or more lists.
        data2 (Any): Loose-equality operand object which may contain one or more lists.

    Returns:
        bool: True if the two objects are loosely equal, False otherwise.
    """

    def _compare(data1: Any, data2: Any) -> bool:
        if data1 == data2:
            return True
        elif isinstance(data1, list) and isinstance(data2, list):
            sort_key = str
            sorted_data1 = sorted(data1, key=sort_key)
            sorted_data2 = sorted(data2, key=sort_key)
            return all(_compare(d1, d2) for d1, d2 in zip(sorted_data1, sorted_data2))
        elif isinstance(data1, dict) and isinstance(data2, dict):
            return all(key in data2 and _compare(data1[key], data2[key]) for key in data1)
        return False

    yield _compare


@pytest.fixture
def reset_caches():
    yield
    PathPattern.glob_results.cache_clear()
    PathPattern.results.cache_clear()
