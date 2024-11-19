# yaml-extras

Some extra scripting utilities written on top of PyYAML.

## Installation

If you're using Poetry, use this repo directly:
    
```bash
# poetry add git+<clone url>
poetry add git+https://github.com/dsillman2000/yaml-extras.git
# or
poetry add git+ssh://git@github.com:dsillman2000/yaml-extras.git
```

## Usage

```python
from yaml_extras import ExtrasLoader
import json

with open('example.yaml') as f:
    data = yaml.load(f, Loader=ExtrasLoader)

print(f"data = {json.dumps(data, indent=2)}")
```

## Features

- `!import` tag: Import another YAML file. Supports multiple-import using the "<<" merge key.

```yaml
# example.yml
my_children:
  child1: !import child1.yml
  child2: !import child2.yml
```

```yaml
# child1.yml
name: child1
age: 10
```

```yaml
# child2.yml
name: child2
age: 7
```

Result when loading in Python:

```python
data = {
  "my_children": {
    "child1": {
      "name": "child1",
      "age": 10
    },
    "child2": {
      "name": "child2",
      "age": 7
    }
  }
}
```

## Roadmap

### P1
- [x] Add support for `!import` to import other documents into a YAML document.
- [ ] Utilize this project in a downstream project to generate code and documentation.

### P2
- [ ] Add support for `!env` tag to import environment variables.
- [ ] VSCode / Intellisense plugin to navigate through imports using cmd + click

## Acknowledgements

- David Sillman <dsillman2000@gmail.com>
- [pyyaml-include](https://github.com/tanbro/pyyaml-include) author, [@tanbro](https://github.com/tanbro).
- [PyYAML](https://github.com/yaml/pyyaml)