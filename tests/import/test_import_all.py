from pathlib import Path

import pytest
import yaml


@pytest.mark.parametrize(
    "doc,other_docs,expected",
    [
        pytest.param(
            """
hello: world
children: !import-all children/*.yml
""",
            {
                "children/child1.yml": "name: Alice\nage: 17\n",
                "children/child2.yml": "name: Bob\nage: 30\n",
                "children/grands/grandchildren.yml": "name: Charlie\nage: 7\n",
            },
            {
                "hello": "world",
                "children": [
                    {"name": "Alice", "age": 17},
                    {"name": "Bob", "age": 30},
                ],
            },
            id="single import-all (*)",
        ),
        pytest.param(
            """
hello: world
children: !import-all children/**/*.yml
""",
            {
                "children/child1.yml": "name: Alice\nage: 17\n",
                "children/child2.yml": "name: Bob\nage: 30\n",
                "children/grands/grandchildren.yml": "name: Charlie\nage: 7\n",
            },
            {
                "hello": "world",
                "children": [
                    {"name": "Alice", "age": 17},
                    {"name": "Bob", "age": 30},
                    {"name": "Charlie", "age": 7},
                ],
            },
            id="single import-all (**)",
        ),
        pytest.param(
            """
cases:
  <<: !import-all cases-v1/*.yml
  <<: !import-all cases-v2/*yml
""",
            {
                "cases-v1/case1.yml": "case_1:\n  name: case1\n",
                "cases-v1/case2.yml": "case_2:\n  name: case2\n",
                "cases-v2/case3.yml": "case_3:\n  name: case3\n",
                "cases-v2/case4.yml": "case_4:\n  name: case4\n",
            },
            {
                "cases": {
                    "case_1": {"name": "case1"},
                    "case_2": {"name": "case2"},
                    "case_3": {"name": "case3"},
                    "case_4": {"name": "case4"},
                },
            },
            id="multiple import-all (*), merged",
        ),
        pytest.param(
            """
cases:
  <<: !import-all cases-v1/**/*.yml
  <<: !import-all cases-v2/**/*.yml
""",
            {
                "cases-v1/case1.yml": "case_1:\n  name: case1\n",
                "cases-v1/case2.yml": "case_2:\n  name: case2\n",
                "cases-v1/extra/case_extra1.yml": "case_extra_1:\n  name: case_extra1\n",
                "cases-v2/case3.yml": "case_3:\n  name: case3\n",
                "cases-v2/case4.yml": "case_4:\n  name: case4\n",
                "cases-v2/extra/case_extra2.yml": "case_extra_2:\n  name: case_extra2\n",
                "cases-v2/extra/case_extra3.yml": "case_extra_3:\n  name: case_extra3\n",
            },
            {
                "cases": {
                    "case_1": {"name": "case1"},
                    "case_2": {"name": "case2"},
                    "case_3": {"name": "case3"},
                    "case_4": {"name": "case4"},
                    "case_extra_1": {"name": "case_extra1"},
                    "case_extra_2": {"name": "case_extra2"},
                    "case_extra_3": {"name": "case_extra3"},
                },
            },
            id="multiple import-all (**), merged",
        ),
        pytest.param(
            """
overarching: !import-all data/*.yml
""",
            {
                "data/one.yml": "a: 1\n",
                "data/two.yml": "b: 2\n",
                "data/extensions/three.yml": "c: 3\n",
                "data/extensions/four.yml": "d: 4\n",
                "data/omitted/extensions/five.yml": "e: 5\n",
                "data/extensions.yml": "ext: !import-all data/extensions/*.yml\n",
            },
            {
                "overarching": [
                    {"a": 1},
                    {"b": 2},
                    {
                        "ext": [
                            {"c": 3},
                            {"d": 4},
                        ]
                    },
                ],
            },
            id="nested import-all (*)",
        ),
    ],
)
def test_import_all(
    doc: str,
    other_docs: dict[str, str],
    expected: dict,
    tmp_chdir,
    loose_equality_for_lists,
    reset_caches,
):
    from yaml_extras import ExtrasLoader

    for path, content in other_docs.items():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
    doc_yml = Path("doc.yml")
    doc_yml.write_text(doc)
    data = yaml.load(doc_yml.open("r"), ExtrasLoader)
    assert loose_equality_for_lists(data, expected)


def test_import_all__relative_dir(tmp_path, reset_caches, loose_equality_for_lists):
    from yaml_extras import ExtrasLoader, yaml_import

    doc = """
data: !import-all data/*.yml
"""
    tmpdir: Path = tmp_path / "my" / "contrived" / "subdirectory"
    tmpdir.mkdir(parents=True)
    doc_yml = Path(tmpdir) / "doc.yml"
    doc_yml.write_text(doc)
    yaml_import.set_import_relative_dir(tmpdir)
    data_dir = Path(tmpdir) / "data"
    data_dir.mkdir(parents=True)
    data1_yml = data_dir / "one.yml"
    data1_yml.write_text("a: 1\n")
    data2_yml = data_dir / "two.yml"
    data2_yml.write_text("b: 2\n")
    data = yaml.load(doc_yml.open("r"), ExtrasLoader)
    assert loose_equality_for_lists(data, {"data": [{"a": 1}, {"b": 2}]})
    yaml_import._reset_import_relative_dir()
