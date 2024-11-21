import os
from pathlib import Path
import pytest

from yaml_extras.file_utils import PathPattern, PathWithMetadata


DirTree = dict[str, "DirTree | str"]


@pytest.fixture
def reset_caches():
    yield
    PathPattern.glob_results.cache_clear()
    PathPattern.results.cache_clear()


def materialize_dir_tree(dir_tree: DirTree, base_dir: Path | None = None) -> None:
    if base_dir is None:
        base_dir = Path.cwd()
    if not base_dir.exists():
        base_dir.mkdir()
    for key, value in dir_tree.items():
        if isinstance(value, str):
            (base_dir / key).write_text(value)
        else:
            materialize_dir_tree(value, base_dir / key)


def test_path_pattern_glob_results(tmp_path: Path, tmp_chdir, reset_caches):
    tree: DirTree = {
        "a": {
            "b": "b",
            "c": "c",
        },
        "d": {
            "e": "e",
            "f": "f",
        },
    }
    materialize_dir_tree(tree)
    assert set(PathPattern("a/*").glob_results()) == {tmp_path / "a" / "b", tmp_path / "a" / "c"}
    assert set(PathPattern("d/*").glob_results()) == {tmp_path / "d" / "e", tmp_path / "d" / "f"}
    assert set(PathPattern("*/b").glob_results()) == {tmp_path / "a" / "b"}


def test_path_pattern_results_unnamed(tmp_path: Path, tmp_chdir, reset_caches):
    tree: DirTree = {
        "a": {
            "b.l": "b",
            "c.l": "c",
        },
        "d": {
            "e.l": "e",
            "f.l": "f",
        },
        "g": {
            "hi": {
                "j.l": "j",
                "k.l": "k",
            },
            "ho": {
                "l.l": "l",
                "m.l": "m",
            },
            "ku": {
                "n.l": "n",
                "o": {
                    "oh.l": "oh",
                    "0.l": "0",
                },
            },
        },
    }
    materialize_dir_tree(tree)
    assert set(PathPattern("a/*.l").results()) == {
        PathWithMetadata(tmp_path / "a" / "b.l", None),
        PathWithMetadata(tmp_path / "a" / "c.l", None),
    }
    assert set(PathPattern("d/*.l").results()) == {
        PathWithMetadata(tmp_path / "d" / "e.l", None),
        PathWithMetadata(tmp_path / "d" / "f.l", None),
    }
    assert set(PathPattern("*/b.l").results()) == {PathWithMetadata(tmp_path / "a" / "b.l", None)}
    assert set(PathPattern("g/*o/*.l").results()) == {
        PathWithMetadata(tmp_path / "g" / "ho" / "l.l", None),
        PathWithMetadata(tmp_path / "g" / "ho" / "m.l", None),
    }
    assert set(PathPattern("g/**/*.l").results()) == {
        PathWithMetadata(tmp_path / "g" / "hi" / "j.l", None),
        PathWithMetadata(tmp_path / "g" / "hi" / "k.l", None),
        PathWithMetadata(tmp_path / "g" / "ho" / "l.l", None),
        PathWithMetadata(tmp_path / "g" / "ho" / "m.l", None),
        PathWithMetadata(tmp_path / "g" / "ku" / "n.l", None),
        PathWithMetadata(tmp_path / "g" / "ku" / "o" / "oh.l", None),
        PathWithMetadata(tmp_path / "g" / "ku" / "o" / "0.l", None),
    }


def test_path_pattern_results_named(tmp_path: Path, tmp_chdir, reset_caches):
    tree: DirTree = {
        "a": {
            "b.l": "b",
            "c.l": "c",
        },
        "d": {
            "e.l": "e",
            "f.l": "f",
        },
        "g": {
            "hi": {
                "j.l": "j",
                "k.l": "k",
            },
            "ho": {
                "l.l": "l",
                "m.l": "m",
            },
            "ku": {
                "n.l": "n",
                "o": {
                    "oh.l": "oh",
                    "0.l": "0",
                },
            },
        },
    }
    materialize_dir_tree(tree)
    assert set(PathPattern("a/{inner:*}.l").results()) == {
        PathWithMetadata(tmp_path / "a" / "b.l", {"inner": "b"}),
        PathWithMetadata(tmp_path / "a" / "c.l", {"inner": "c"}),
    }
    assert set(PathPattern("d/{second:*}.l").results()) == {
        PathWithMetadata(tmp_path / "d" / "e.l", {"second": "e"}),
        PathWithMetadata(tmp_path / "d" / "f.l", {"second": "f"}),
    }
    assert set(PathPattern("{root:*}/b.l").results()) == {
        PathWithMetadata(tmp_path / "a" / "b.l", {"root": "a"})
    }
    assert set(PathPattern("g/{pre_o:*}o/{second:*}.l").results()) == {
        PathWithMetadata(tmp_path / "g" / "ho" / "l.l", {"pre_o": "h", "second": "l"}),
        PathWithMetadata(tmp_path / "g" / "ho" / "m.l", {"pre_o": "h", "second": "m"}),
    }
    assert set(PathPattern("g/{subpath:**}/{leaf:*}.l").results()) == {
        PathWithMetadata(tmp_path / "g" / "hi" / "j", {"subpath": "hi", "leaf": "j.l"}),
        PathWithMetadata(tmp_path / "g" / "hi" / "k", {"subpath": "hi", "leaf": "k.l"}),
        PathWithMetadata(tmp_path / "g" / "ho" / "l", {"subpath": "ho", "leaf": "l.l"}),
        PathWithMetadata(tmp_path / "g" / "ho" / "m", {"subpath": "ho", "leaf": "m.l"}),
        PathWithMetadata(tmp_path / "g" / "ku" / "n", {"subpath": "ku", "leaf": "n.l"}),
        PathWithMetadata(tmp_path / "g" / "ku" / "o" / "oh", {"subpath": "ku/o", "leaf": "oh.l"}),
        PathWithMetadata(tmp_path / "g" / "ku" / "o" / "0", {"subpath": "ku/o", "leaf": "0.l"}),
    }
