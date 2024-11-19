import pytest
import yaml

import yaml_extras


def test_import_and_concat_dicts(registered_yaml, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    other_yml = tmp_path / "other.yml"
    other_yml.write_text("b: 2")
    another_yml = tmp_path / "another.yml"
    another_yml.write_text("inner: 'most'")
    doc_yml = tmp_path / "doc.yml"
    doc_yml.write_text(
        """
c: !++ [!import other.yml, !import another.yml]
"""
    )
    data = registered_yaml.load(doc_yml.open("r"), yaml.Loader)
    assert data == {"c": {"b": 2, "inner": "most"}}


def test_import_and_concat_lists(registered_yaml, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    other_yml = tmp_path / "other.yml"
    other_yml.write_text("- item1\n- item2\n")
    another_yml = tmp_path / "another.yml"
    another_yml.write_text("- name: innermost\n")
    doc_yml = tmp_path / "doc.yml"
    doc_yml.write_text("c: !++ [!import other.yml, !import another.yml]")
    data = registered_yaml.load(doc_yml.open("r"), yaml.Loader)
    assert data == {"c": ["item1", "item2", {"name": "innermost"}]}


def test_import_and_concat_errors(registered_yaml, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    other_yml = tmp_path / "other.yml"
    other_yml.write_text("b: 2")
    another_yml = tmp_path / "another.yml"
    another_yml.write_text("- inner: 'most'")
    doc_yml = tmp_path / "doc.yml"
    doc_yml.write_text(
        """
c: !++ [!import other.yml, !import another.yml]
"""
    )
    with pytest.raises(yaml.constructor.ConstructorError):
        data = registered_yaml.load(doc_yml.open("r"), yaml.Loader)
