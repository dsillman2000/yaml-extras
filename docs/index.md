# yaml-extras

Some extra scripting utilities written on top of PyYAML. Written by
[David Sillman](https://github.com/dsillman2000).

## Installation

```bash
pip install yaml-extras
```

## Usage

```python
from yaml_extras import ExtrasLoader
import json

with open('example.yml') as f:
    data_dict = yaml.load(f, ExtrasLoader)

print(f"data = {json.dumps(data_dict, indent=2)}")
```

## Features

| Feature | Description |
| --- | --- |
| [import](tags/import/0_yaml_import.md) | Import other YAML files, or parts of them. |

## Utility interfaces

| Utility interface | Description |
| --- | --- |
| [Path patterns](utilities/path_patterns.md) | Utilities for working with paths and path patterns, i.e. for glob-based imports |