from pathlib import Path

import pytest
import yaml


@pytest.mark.parametrize(
    "doc,other_docs,expected",
    [
        pytest.param(
            """
child_ages: !import-all.anchor children/*.yml &age
""",
            {
                "children/child1.yml": "name: Alice\nage: &age 17\n",
                "children/child2.yml": "name: Bob\nage: &age 30\n",
                "children/grands/grandchildren.yml": "name: Charlie\nage: &age 7\n",
            },
            {
                "child_ages": [17, 30],
            },
            id="single import-all.anchor (*)",
        ),
        pytest.param(
            """
child_ages: !import-all.anchor children/**/*.yml &age
""",
            {
                "children/child1.yml": "name: Alice\nage: &age 17\n",
                "children/child2.yml": "name: Bob\nage: &age 30\n",
                "children/grands/grandchildren.yml": "name: Charlie\nage: &age 7\n",
            },
            {
                "child_ages": [17, 30, 7],
            },
            id="single import-all.anchor (**)",
        ),
        pytest.param(
            """
all_resolutions:
  <<: !import-all.anchor cases-v1/*.yml &resolution
  <<: !import-all.anchor cases-v2/*.yml &resolution
""",
            {
                "cases-v1/case1.yml": "case_1:\n  resolution: &resolution { resolution_1: hi }\n",
                "cases-v1/case2.yml": "case_2:\n  resolution: &resolution { resolution_2: hello }\n",
                "cases-v2/case3.yml": "case_3:\n  resolution: &resolution { resolution_3: hey }\n",
                "cases-v2/case4.yml": "case_4:\n  resolution: &resolution { resolution_4: hola }\n",
                "cases-v3/case5.yml": "case_5:\n  resolution: &resolution { resolution_5: bonjour }\n",
            },
            {
                "all_resolutions": {
                    "resolution_1": "hi",
                    "resolution_2": "hello",
                    "resolution_3": "hey",
                    "resolution_4": "hola",
                }
            },
            id="multiple import-all.anchor (*), merged",
        ),
        pytest.param(
            """
all_resolutions:
  <<: !import-all.anchor cases-v1/**/*.yml &resolution
  <<: !import-all.anchor cases-v2/**/*.yml &resolution
""",
            {
                "cases-v1/case1.yml": "case_1:\n  resolution: &resolution { resolution_1: hi }\n",
                "cases-v1/case2.yml": "case_2:\n  resolution: &resolution { resolution_2: hello }\n",
                "cases-v1/extra/case_extra1.yml": "case_extra_1:\n  resolution: &resolution { resolution_extra1: hella }\n",
                "cases-v2/case3.yml": "case_3:\n  resolution: &resolution { resolution_3: hey }\n",
                "cases-v2/case4.yml": "case_4:\n  resolution: &resolution { resolution_4: hola }\n",
                "cases-v2/extra/case_extra2.yml": "case_extra_2:\n  resolution: &resolution { resolution_extra2: holla }\n",
                "cases-v2/extra/case_extra3.yml": "case_extra_3:\n  resolution: &resolution { resolution_extra3: hullo }\n",
                "cases-v3/case5.yml": "case_5:\n  resolution: &resolution { resolution_5: bonjour }\n",
            },
            {
                "all_resolutions": {
                    "resolution_1": "hi",
                    "resolution_2": "hello",
                    "resolution_3": "hey",
                    "resolution_4": "hola",
                    "resolution_extra1": "hella",
                    "resolution_extra2": "holla",
                    "resolution_extra3": "hullo",
                }
            },
            id="multiple import-all (**), merged",
        ),
        pytest.param(
            """
all_sums: !import-all.anchor data/*.yml &sum
""",
            {
                "data/one.yml": "operands: [1, 2]\nsum: &sum 3\n",
                "data/two.yml": "operands: [3, 4]\nsum: &sum 7\n",
                "data/extensions/three.yml": "operands: [5, 6]\nsum: &sum 11\nproduct: &product 30\n",
                "data/extensions/four.yml": "operands: [7, 8]\nsum: &sum 15\nproduct: &product 56\n",
                "data/omitted/extensions/five.yml": "operands: [9, 10]\nsum: &sum 19\nquotient: &quotient 0.9\n",
                "data/extensions.yml": "sum: &sum\n  ext: !import-all.anchor data/extensions/*.yml &sum\nproduct: &product\n  ext: !import-all.anchor data/extensions/*.yml &product\n",
            },
            {
                "all_sums": [3, 7, {"ext": [11, 15]}],
            },
            id="nested import-all.anchor (*)",
        ),
    ],
)
def test_import_anchor(
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
        Path(path).write_text(content)
    doc_yml = Path("doc.yml")
    doc_yml.write_text(doc)
    data = yaml.load(doc_yml.open("r"), ExtrasLoader)
    assert loose_equality_for_lists(data, expected)


def test_import_all_anchor__relative_dir(tmp_path, reset_caches, loose_equality_for_lists):
    from yaml_extras import ExtrasLoader, yaml_import

    doc = """
data: !import-all.anchor data/*.yml &sum
"""
    tmpdir: Path = tmp_path / "my" / "contrived" / "subdirectory"
    tmpdir.mkdir(parents=True)
    doc_yml = Path(tmpdir) / "doc.yml"
    doc_yml.write_text(doc)
    yaml_import.set_import_relative_dir(tmpdir)
    data_dir = Path(tmpdir) / "data"
    data_dir.mkdir(parents=True)
    data1_yml = data_dir / "one.yml"
    data1_yml.write_text("operands: [1, 2]\nsum: &sum 3\n")
    data2_yml = data_dir / "two.yml"
    data2_yml.write_text("operands: [3, 4]\nsum: &sum 7\n")

    data = yaml.load(doc_yml.open("r"), ExtrasLoader)
    assert loose_equality_for_lists(data, {"data": [3, 7]})
    yaml_import._reset_import_relative_dir()
