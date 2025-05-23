from pathlib import Path

import pytest
import yaml


@pytest.mark.parametrize(
    "doc,other_docs,expected",
    [
        pytest.param(
            """
a: !import other.yml
""",
            {"other.yml": "b: 2"},
            {"a": {"b": 2}},
            id="single import case",
        ),
        pytest.param(
            """
a: !import other.yml
b: !import other.yml
""",
            {
                "other.yml": "b: 2\nc: !import another.yml",
                "another.yml": "inner: 'most'",
            },
            {
                "a": {"b": 2, "c": {"inner": "most"}},
                "b": {"b": 2, "c": {"inner": "most"}},
            },
            id="simple import twice",
        ),
        pytest.param(
            """
a: !import other.yml
b: !import another.yml
""",
            {"other.yml": "b: 2", "another.yml": "c: 3"},
            {"a": {"b": 2}, "b": {"c": 3}},
            id="two separate imports",
        ),
        pytest.param(
            """
a:
  child1: !import child1.yml
  child2: !import child2.yml
""",
            {
                "child1.yml": "- foo: 1\n- bar: 2",
                "child2.yml": "- foo: 3\n- bar: 4\n- !import grandchild.yml",
                "grandchild.yml": "baz: 5\nbuzz: 6",
            },
            {
                "a": {
                    "child1": [{"foo": 1}, {"bar": 2}],
                    "child2": [{"foo": 3}, {"bar": 4}, {"baz": 5, "buzz": 6}],
                },
            },
            id="nested deep imports",
        ),
    ],
)
def test_import(
    doc: str,
    other_docs: dict[str, str],
    expected: dict,
    tmp_chdir,
):
    from yaml_extras import ExtrasLoader

    for path, content in other_docs.items():
        with open(path, "w") as f:
            f.write(content)
    doc_yml = Path("doc.yml")
    doc_yml.write_text(doc)
    data = yaml.load(doc_yml.open("r"), ExtrasLoader)
    assert data == expected


@pytest.mark.parametrize(
    "doc,other_docs,expected",
    [
        pytest.param(
            """
data:
  <<: !import other.yml
""",
            {"other.yml": "a: 1"},
            {"data": {"a": 1}},
            id="single merged import",
        ),
        pytest.param(
            """
data1:
  <<: [!import other.yml, !import another.yml]
data2:
  <<:
    - !import other.yml
    - !import another.yml
data3:
  <<: !import other.yml
  <<: !import another.yml
""",
            {"other.yml": "a: 1", "another.yml": "b: 2"},
            {
                "data1": {"a": 1, "b": 2},
                "data2": {"a": 1, "b": 2},
                "data3": {"a": 1, "b": 2},
            },
            id="multiple disjoint merged imports",
        ),
        pytest.param(
            """
data1:
  <<: [!import another.yml, !import other.yml]
data2:
  <<:
    - !import another.yml
    - !import other.yml
data3:
  <<: !import other.yml
  <<: !import another.yml
""",
            {"other.yml": "a: 1\nc: 3", "another.yml": "a: 2\nb: 2"},
            {
                "data1": {"a": 1, "b": 2, "c": 3},
                "data2": {"a": 1, "b": 2, "c": 3},
                "data3": {"a": 2, "b": 2, "c": 3},
            },
            id="multiple conflicting merged imports",
        ),
    ],
)
def test_merge_import(
    doc: str,
    other_docs: dict[str, str],
    expected: dict,
    tmp_chdir,
):
    from yaml_extras import ExtrasLoader

    for path, content in other_docs.items():
        with open(path, "w") as f:
            f.write(content)
    doc_yml = Path("doc.yml")
    doc_yml.write_text(doc)
    data = yaml.load(doc_yml.open("r"), ExtrasLoader)
    assert data == expected


def test_import__relative_dir(tmp_path, reset_caches):
    from yaml_extras import ExtrasLoader, yaml_import

    doc = """
data: !import data.yml
"""
    tmpdir: Path = tmp_path / "my" / "contrived" / "subdirectory"
    tmpdir.mkdir(parents=True)
    doc_yml = Path(tmpdir) / "doc.yml"
    doc_yml.write_text(doc)
    yaml_import.set_import_relative_dir(tmpdir)
    data_yml = Path(tmpdir) / "data.yml"
    data_yml.write_text("a: 1\nb: 2\n")

    data = yaml.load(doc_yml.open("r"), ExtrasLoader)
    assert data == {"data": {"a": 1, "b": 2}}
    yaml_import._reset_import_relative_dir()
