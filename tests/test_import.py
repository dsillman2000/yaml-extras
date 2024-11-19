from pathlib import Path

import pytest
import yaml

import yaml_extras


@pytest.mark.parametrize(
    "doc,other_docs,expected",
    [
        (
            """
a: !import other.yml
""",
            {"other.yml": "b: 2"},
            {"a": {"b": 2}},
        ),
        (
            """
a: !import other.yml
""",
            {"other.yml": "b: 2\nc: !import another.yml", "another.yml": "inner: 'most'"},
            {"a": {"b": 2, "c": {"inner": "most"}}},
        ),
    ],
)
def test_import(
    doc: str,
    other_docs: dict[str, str],
    expected: dict,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    registered_yaml,
):
    monkeypatch.chdir(tmp_path)
    print(tmp_path)
    for path, content in other_docs.items():
        with open(path, "w") as f:
            f.write(content)
    doc_yml = Path("doc.yml")
    doc_yml.write_text(doc)
    data = registered_yaml.load(doc_yml.open("r"), yaml.Loader)
    assert data == expected
