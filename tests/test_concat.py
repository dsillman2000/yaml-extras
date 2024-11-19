import pytest
import yaml

import yaml_extras


@pytest.mark.parametrize(
    "doc,expected",
    [
        (
            """
all: !++ [[1, 2], [3, 4]]
""",
            {"all": [1, 2, 3, 4]},
        ),
        (
            """
.data1: &data1
  a: 1
  b: 2
.data2: &data2
  c: "see"
  d: "dee"
all: !++ [*data1, *data2, {key: "value"}]
""",
            {
                ".data1": {"a": 1, "b": 2},
                ".data2": {"c": "see", "d": "dee"},
                "all": {"a": 1, "b": 2, "c": "see", "d": "dee", "key": "value"},
            },
        ),
    ],
)
def test_concat(doc: str, expected: dict, registered_yaml):
    data = registered_yaml.load(doc, yaml.Loader)
    assert data == expected


@pytest.mark.parametrize(
    "invalid_doc",
    [
        """
all: !++ 1
""",
        """
all: !++ [1, 2]
""",
        """
all: !++ {a: 1}
""",
        """
all: !++ [[1, 2], {a: 1}]
""",
    ],
)
def test_concat_error(invalid_doc: str, registered_yaml):
    with pytest.raises(yaml.constructor.ConstructorError):
        registered_yaml.load(invalid_doc, yaml.Loader)
