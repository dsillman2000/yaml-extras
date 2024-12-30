# Module: `yaml_import`

## Overview

There are five variants of the `!import` tag, each with a different behavior:

| Variant |  Purpose | Constructed type |
| --- | --- | --- |
| `!import` | Import an entire file into a specified YAML node. | `Any` |
| `!import.anchor` | Import an anchor from a file into a specified YAML node. | `Any` |
| `!import-all` | Import zero or more YAML files matching a glob pattern into a specified YAML node. | `list[Any]` |
| `!import-all.anchor` | Import a specific anchor from zero or more files matching a glob pattern into a specified YAML node. | `list[Any]` |
| `!import-all-parameterized` | Import zero or more YAML files matching a glob pattern into a specified YAML node, with zero or more metadata parameters extracted from components in the filepath. | `list[Any]` |

Each of the variants above are identified by their tag, which determines which PyYAML 
[Constructor](https://pyyaml.org/wiki/PyYAMLDocumentation) is used to process the tag and construct 
the result as a Python object during loading.

## The `yaml_import` module

::: yaml_extras.yaml_import
    options:
      members: []
      show_root_toc_entry: false

Specific breakdowns of the constructors and utility dataclasses are provided in the following
sections.

1. [!import](./1_import.md)
2. [!import.anchor](./2_import.anchor.md)
3. [!import-all](./3_import-all.md)   
4. [!import-all.anchor](./4_import-all.anchor.md)
5. [!import-all-parameterized](./5_import-all-parameterized.md)

## Customizations and utilities

For further information about customizing the import behavior, see:

- [Customizations: relative import directory](./6_customize_relative_dir.md)

For further information about how to use the specialized "path patterns" which are important for the
`!import-all`, `!import-all.anchor`, and `!import-all-parameterized` tags, see:

- [Utilities > Path patterns](../../utilities/path_patterns.md)
