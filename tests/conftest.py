import pytest
import yaml

import yaml_extras


@pytest.fixture
def registered_yaml():
    yaml_extras.register(yaml)
    yield yaml
