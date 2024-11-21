from pathlib import Path

import pytest
import yaml

from yaml_extras import ExtrasLoader


@pytest.mark.parametrize(
    "doc,other_docs,expected",
    [
        pytest.param(
            """
data: !import.anchor other.yml &ptr
""",
            {"other.yml": "inner: &ptr\n  a: 1\n"},
            {"data": {"a": 1}},
            id="single anchor import",
        ),
        pytest.param(
            """
data: !import.anchor other.yml &ptr
""",
            {"other.yml": "inner: &ptr { a: 1 }\n"},
            {"data": {"a": 1}},
            id="single flow anchor import",
        ),
        pytest.param(
            """
content:
  child1: !import.anchor children.yml &child-1
  child2: !import.anchor children.yml &child-2
""",
            {
                "children.yml": """
child1: &child-1
  name: Alice
  age: 17
  
child2: &child-2
  name: Bob
  age: 30
  children:
    - !import.anchor grandchildren.yml &grandchild-1
""",
                "grandchildren.yml": """
grandchild1: &grandchild-1
  name: Charlie
  age: 7
""",
            },
            {
                "content": {
                    "child1": {"name": "Alice", "age": 17},
                    "child2": {
                        "name": "Bob",
                        "age": 30,
                        "children": [{"name": "Charlie", "age": 7}],
                    },
                }
            },
            id="nested deep anchor imports",
        ),
        pytest.param(
            """
data: !import.anchor dict_items.yml &list
""",
            {
                "dict_items.yml": """
dictionary:
  foo: bar
  baz: buzz
items: &list
  - foo
  - bar
  - baz
  - buzz
""",
            },
            {"data": ["foo", "bar", "baz", "buzz"]},
            id="single anchored sequence import",
        ),
        pytest.param(
            """
data: !import.anchor dict_items.yml &list
""",
            {
                "dict_items.yml": """
dictionary: {  foo: bar, baz: buzz }
items: &list [foo, bar, baz, buzz]
""",
            },
            {"data": ["foo", "bar", "baz", "buzz"]},
            id="single anchored flow sequence import",
        ),
    ],
)
def test_import_anchor(
    doc: str,
    other_docs: dict[str, str],
    expected: dict,
    tmp_chdir,
):
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
content1:
  <<: [!import.anchor other.yml &ptr2, !import.anchor another.yml &ptr1]
content2:
  <<:
    - !import.anchor other.yml &ptr2
    - !import.anchor another.yml &ptr1
content3:
  <<: !import.anchor other.yml &ptr2
  <<: !import.anchor another.yml &ptr1
""",
            {
                "other.yml": """
contents:
  a: &ptr1
    foo: bar
  b: &ptr2
    bar: baz
""",
                "another.yml": """
b: 2
contents:
  c: &ptr1
    bar: bor
    baz: bor
  d: &ptr2
    data: doo
""",
            },
            {f"content{i}": {"bar": "bor", "baz": "bor"} for i in "123"},
            id="multiple conflicting anchor imports, merged",
        ),
    ],
)
def test_merge_import_anchor(
    doc: str,
    other_docs: dict[str, str],
    expected: dict,
    tmp_chdir,
):
    for path, content in other_docs.items():
        with open(path, "w") as f:
            f.write(content)
    doc_yml = Path("doc.yml")
    doc_yml.write_text(doc)
    data = yaml.load(doc_yml.open("r"), ExtrasLoader)
    assert data == expected
