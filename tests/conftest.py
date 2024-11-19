from pathlib import Path
import pytest


@pytest.fixture
def tmp_chdir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    with monkeypatch.context() as m:
        m.chdir(tmp_path)
        yield tmp_path
