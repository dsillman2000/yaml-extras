from pathlib import Path
from typing import Any

import pytest
import yaml

from yaml_extras import ExtrasLoader


def loose_equality_for_lists(data1: Any, data2: Any) -> bool:
    """When two objects contain one or more lists, compare the lists without order and return the
    resulting equality of the two objects.

    Args:
        data1 (Any): Loose-equality operand object which may contain one or more lists.
        data2 (Any): Loose-equality operand object which may contain one or more lists.

    Returns:
        bool: True if the two objects are loosely equal, False otherwise.
    """
    if data1 == data2:
        return True
    elif isinstance(data1, list) and isinstance(data2, list):
        sort_key = str
        sorted_data1 = sorted(data1, key=sort_key)
        sorted_data2 = sorted(data2, key=sort_key)
        return all(loose_equality_for_lists(d1, d2) for d1, d2 in zip(sorted_data1, sorted_data2))
    elif isinstance(data1, dict) and isinstance(data2, dict):
        return all(
            key in data2 and loose_equality_for_lists(data1[key], data2[key]) for key in data1
        )
    return False


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
def test_import_all(doc: str, other_docs: dict[str, str], expected: dict, tmp_chdir):
    for path, content in other_docs.items():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
    doc_yml = Path("doc.yml")
    doc_yml.write_text(doc)
    data = yaml.load(doc_yml.open("r"), ExtrasLoader)
    assert loose_equality_for_lists(data, expected)
