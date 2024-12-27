from pathlib import Path

import pytest
import yaml

from yaml_extras import ExtrasLoader


@pytest.mark.parametrize(
    "doc,other_docs,expected",
    [
        pytest.param(
            """
leaves: !import-all-parameterized branches/**/{name:*}.yml
""",
            {
                "branches/branch1/leaf1.yml": "id: '001'\nage: 17\n",
                "branches/branch1/leaf2.yml": "id: '002'\nage: 30\n",
                "branches/branch2/leaf3.yml": "id: '003'\nage: 7\n",
                "branches/branch2/branch3/leaf4.yml": "id: '004'\nage: 10\n",
                "branches/branch2/branch3/branch4/branch5/leaf5.yml": "id: '005'\nage: 20\n",
            },
            {
                "leaves": [
                    {"name": "leaf1", "id": "001", "age": 17},
                    {"name": "leaf2", "id": "002", "age": 30},
                    {"name": "leaf3", "id": "003", "age": 7},
                    {"name": "leaf4", "id": "004", "age": 10},
                    {"name": "leaf5", "id": "005", "age": 20},
                ],
            },
            id="import-all-parameterized (parameterized leaves)",
        ),
        pytest.param(
            """
leaves: !import-all-parameterized branches/{path:**}/*.yml
""",
            {
                "branches/branch1/leaf1.yml": "id: '001'\nage: 17\n",
                "branches/branch1/leaf2.yml": "id: '002'\nage: 30\n",
                "branches/branch2/leaf3.yml": "id: '003'\nage: 7\n",
                "branches/branch2/branch3/leaf4.yml": "id: '004'\nage: 10\n",
                "branches/branch2/branch3/branch4/branch5/leaf5.yml": "id: '005'\nage: 20\n",
            },
            {
                "leaves": [
                    {"path": "branch1", "id": "001", "age": 17},
                    {"path": "branch1", "id": "002", "age": 30},
                    {"path": "branch2", "id": "003", "age": 7},
                    {"path": "branch2/branch3", "id": "004", "age": 10},
                    {"path": "branch2/branch3/branch4/branch5", "id": "005", "age": 20},
                ],
            },
            id="import-all-parameterized (parameterized branch paths)",
        ),
        pytest.param(
            """
leaves: !import-all-parameterized branches/{path:**}/{name:*}.yml
""",
            {
                "branches/branch1/leaf1.yml": "id: '001'\nage: 17\n",
                "branches/branch1/leaf2.yml": "id: '002'\nage: 30\n",
                "branches/branch2/leaf3.yml": "id: '003'\nage: 7\n",
                "branches/branch2/branch3/leaf4.yml": "id: '004'\nage: 10\n",
                "branches/branch2/branch3/branch4/branch5/leaf5.yml": "id: '005'\nage: 20\n",
            },
            {
                "leaves": [
                    {"path": "branch1", "name": "leaf1", "id": "001", "age": 17},
                    {"path": "branch1", "name": "leaf2", "id": "002", "age": 30},
                    {"path": "branch2", "name": "leaf3", "id": "003", "age": 7},
                    {"path": "branch2/branch3", "name": "leaf4", "id": "004", "age": 10},
                    {
                        "path": "branch2/branch3/branch4/branch5",
                        "name": "leaf5",
                        "id": "005",
                        "age": 20,
                    },
                ]
            },
            id="import-all-parameterized (parameterized branch paths and leaves)",
        ),
        pytest.param(
            """
definitions: !import-all-parameterized words/{word:*}.yml
""",
            {
                "words/hello.yml": "Greeting\n",
                "words/goodbye.yml": "Farewell\n",
                "words/hi.yml": "Informal greeting\n",
            },
            {
                "definitions": [
                    {"word": "hello", "content": "Greeting"},
                    {"word": "goodbye", "content": "Farewell"},
                    {"word": "hi", "content": "Informal greeting"},
                ]
            },
            id="import-all-parameterized (scalar leaves)",
        ),
        pytest.param(
            """
synonyms: !import-all-parameterized words/{word:*}.yml
""",
            {
                "words/hello.yml": "- hi\n- hey\n- howdy\n",
                "words/goodbye.yml": "- bye\n- farewell\n- see you\n",
            },
            {
                "synonyms": [
                    {"word": "hello", "content": ["hi", "hey", "howdy"]},
                    {"word": "goodbye", "content": ["bye", "farewell", "see you"]},
                ]
            },
            id="import-all-parameterized (sequence leaves)",
        ),
    ],
)
def test_import_all_parameterized(
    doc,
    other_docs,
    expected,
    reset_caches,
    loose_equality_for_lists,
    tmp_chdir,
):
    for path, content in other_docs.items():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
    doc_yml = Path("doc.yml")
    doc_yml.write_text(doc)
    data = yaml.load(doc_yml.open("r"), ExtrasLoader)
    assert loose_equality_for_lists(data, expected)
