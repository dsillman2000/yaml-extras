# yaml-extras

Some extra scripting utilities written on top of PyYAML.

## Installation

Install with `pip` or `poetry`:
    
```bash
pip install yaml-extras
# or
poetry add yaml-extras
```

## Usage

```python
import yaml
from yaml_extras import ExtrasLoader
import json

with open('example.yml') as f:
    data = yaml.load(f, Loader=ExtrasLoader)

print(f"data = {json.dumps(data, indent=2)}")
```

## Features

### Modularity with "import"

`!import` tag: Import another whole YAML file. Supports multiple-import using the "<<" merge key, as well as aliasing the result of an import using an anchor.

> **Note:** There is no safeguard against cyclical imports. If you import a file that imports the original file, it will result in exceeding Python's maximum recursion depth.

**Syntax**

```
!import [&anchor ]<filepath>
```

**Examples**
<details><summary>Simple whole-file import</summary>

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
</details>

<details><summary>Nested whole-file imports</summary>

```yaml
# example.yml
my_children:
  child: !import child.yml
```

```yaml
# child.yml
name: child
age: 40
grandchild: !import grandchild.yml
```

```yaml
# grandchild.yml
name: grandchild
age: 10
```

Result when loading in Python:

```python
data = {
  "my_children": {
    "child": {
      "name": "child",
      "age": 40,
      "grandchild": {
        "name": "grandchild",
        "age": 10
      }
    }
  }
}
```
</details>

<details><summary>Multiple whole-file imports with merge</summary>

```yaml
# example.yml
all_animals:
  <<: 
    - !import animals/american.yml
    - !import animals/eurasian.yml
```
  
```yaml
# animals/american.yml
bear: wild
wolf: wild
fish: domestic
dog: domestic
```

```yaml
# animals/eurasian.yml
tiger: wild
lion: wild
cat: domestic
chicken: domestic
```

Result when loading in Python:

```python
data = {
  "all_animals": {
    "bear": "wild",
    "wolf": "wild",
    "fish": "domestic",
    "dog": "domestic",
    "tiger": "wild",
    "lion": "wild",
    "cat": "domestic",
    "chicken": "domestic"
  }
}
```
</details>

<details><summary>Anchored whole-file imports</summary>

```yaml
# example.yml
child: !import &child-anchor child.yml
again:
  child: *child-anchor
```

```yaml
# child.yml
name: child
age: 10
```

Result when loading in Python:

```python
data = {
  "child": {
    "name": "child",
    "age": 10
  },
  "again": {
    "child": {
      "name": "child",
      "age": 10
    }
  }
}
```
</details>

---

`!import.anchor` tag: Import a specific anchor from another YAML file. Supports multiple-import using the "<<" merge key, as well as aliasing the result of an import using an anchor.

> **Note:** There is no safeguard against cyclical imports. If you import an anchor that imports the original file (or anchor you define with this import), it will result in exceeding Python's maximum recursion depth.

**Syntax**

```
!import.anchor [&internal_anchor ]<filepath> &<external_anchor>
```

**Examples**

<details><summary>Simple anchor import</summary>

```yaml
# example.yml
my_children:
  child1: !import.anchor children.yml &child1
  child2: !import.anchor children.yml &child2
```

```yaml
# children.yml
child1: &child1
  name: child1
  age: 10
child2: &child2
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
</details>

<details><summary>Nested anchor imports</summary>

```yaml
# example.yml
my_children:
  child: !import.anchor child.yml &child
```

```yaml
# child.yml
name: child
age: 40
grandchild: !import.anchor grandchild.yml &grandchild
```

```yaml
# grandchild.yml
grandchild: &grandchild
  name: grandchild
  age: 10
```

Result when loading in Python:

```python
data = {
  "my_children": {
    "child": {
      "name": "child",
      "age": 40,
      "grandchild": {
        "name": "grandchild",
        "age": 10
      }
    }
  }
}
```
</details>

<details><summary>Multiple anchor imports with merge</summary>

```yaml
# example.yml
all_animals:
  <<: 
    - !import.anchor animals.yml &american
    - !import.anchor animals.yml &eurasian
```

```yaml
# animals.yml
american: &american
  bear: wild
  wolf: wild
  fish: domestic
  dog: domestic

eurasian: &eurasian
  tiger: wild
  lion: wild
  cat: domestic
  chicken: domestic
```

Result when loading in Python:

```python
data = {
  "all_animals": {
    "bear": "wild",
    "wolf": "wild",
    "fish": "domestic",
    "dog": "domestic",
    "tiger": "wild",
    "lion": "wild",
    "cat": "domestic",
    "chicken": "domestic"
  }
}
```
</details>

<details><summary>Anchored anchor imports</summary>

```yaml
# example.yml
child: !import.anchor &my-child child.yml &child-anchor
again:
  child: *my-child
```

```yaml
# child.yml
child: &child-anchor
  name: child
  age: 10
```

Result when loading in Python:

```python
data = {
  "child": {
    "name": "child",
    "age": 10
  },
  "again": {
    "child": {
      "name": "child",
      "age": 10
    }
  }
}
```
</details>

---

`!import-all` tag: Import a glob pattern of YAML files as a sequence. Supports merging the imports using the "<<" merge key, as well as aliasing the result of an import using an anchor.

The glob pattern system only supports two types of wildcards: `*` and `**`. `*` matches any character except for `/`, while `**` matches any character including `/`.

> **Note:** There is no safeguard against cyclical imports. If you import a file that imports the original file, it will result in exceeding Python's maximum recursion depth.

**Syntax**

```
!import-all [&anchor ]<glob_pattern>
```

**Examples**

<details><summary>Simple (*) sequence import</summary>

```yaml
# example.yml
all_children: !import-all children/*.yml
```

```yaml
# children/alice.yml
name: alice
age: 10
height: 1.2
```

```yaml
#children/bob.yml
name: bob
age: 7
height: 1.0
```

Result when loading in Python:

```python
data = {
  "all_children": [
    {
      "name": "alice",
      "age": 10,
      "height": 1.2
    },
    {
      "name": "bob",
      "age": 7,
      "height": 1.0
    }
  ]
}
```
</details>

<details><summary>Nested (*) sequence imports</summary>

```yaml
# example.yml
all_children: !import-all children/*.yml
```

```yaml
# children/bob.yml
name: bob
age: 28
```

```yaml
# children/alice.yml
name: alice
age: 40
children: !import-all children/alice/*.yml
```

```yaml
# children/alice/fred.yml
name: fred
age: 10
```

```yaml
# children/alice/jane.yml
name: jane
age: 7
```

Result when loading in Python:

```python
data = {
  "all_children": [
    {
      "name": "bob",
      "age": 28
    },
    {
      "name": "alice",
      "age": 40,
      "children": [
        {
          "name": "fred",
          "age": 10
        },
        {
          "name": "jane",
          "age": 7
        }
      ]
    }
  ]
}
```

</details>

<details><summary>Multiple (*) sequence imports with merge</summary>

```yaml
# example.yml
all_animals:
  <<: 
    - !import-all animals/american/*.yml
    - !import-all animals/eurasian/*.yml
```

```yaml
# animals/american/bear.yml
bear:
  type: wild
  size: large
```
  
```yaml
# animals/american/wolf.yml
wolf:
  type: wild
  size: medium
```

```yaml
# animals/eurasian/tiger.yml
tiger:
  type: wild
  size: large
```

```yaml
# animals/eurasian/lion.yml
lion:
  type: wild
  size: large
```

Result when loading in Python:

```python
data = {
  "all_animals": {
    "bear": {
      "type": "wild",
      "size": "large"
    },
    "wolf": {
      "type": "wild",
      "size": "medium"
    },
    "tiger": {
      "type": "wild",
      "size": "large"
    },
    "lion": {
      "type": "wild",
      "size": "large"
    }
  }
}
```
</details>

<details><summary>Anchored (*) sequence imports</summary>

```yaml
# example.yml
data: !import-all &my-children children/*.yml
again:
  data: *my-children
```

```yaml
# children/alice.yml
name: alice
age: 10
height: 1.2
```

```yaml
# children/bob.yml
name: bob
age: 7
height: 1.0
```

Result when loading in Python:

```python
data = {
  "data": [
    {
      "name": "alice",
      "age": 10,
      "height": 1.2
    },
    {
      "name": "bob",
      "age": 7,
      "height": 1.0
    }
  ],
  "again": {
    "data": [
      {
        "name": "alice",
        "age": 10,
        "height": 1.2
      },
      {
        "name": "bob",
        "age": 7,
        "height": 1.0
      }
    ]
  }
}
```
</details>

<details><summary>Simple (**) sequence import</summary>

```yaml
# example.yml
overarching: !import-all subfolders/**/*.yml
```

```yaml
# subfolders/child1.yml
name: child1
```

```yaml
# subfolders/child2.yml
name: child2
```

```yaml
# subfolders/subfolder1/grandchild1.yml
name: grandchild1
```

Result when loading in Python:

```python
data = {
  "overarching": [
    {
      "name": "child1"
    },
    {
      "name": "child2"
    },
    {
      "name": "grandchild1"
    }
  ]
}
```

</details>

---

`!import-all-parameterized` tag: Import a glob pattern of YAML files as a sequence, enriching the results with one or more metadata keys extracted from globs in the filepath. Supports merging the imports using the "<<" merge key, as well as aliasing the result of an import using an anchor.

The glob pattern system only supports two types of wildcards: `*` and `**`. `*` matches any character except for `/`, while `**` matches any character including `/`. Metadata keys can be extracted from zero or more globs in the path specification with syntax like this:

```yaml
# Import all YAML files in the `path/to/*.yml` glob as a sequence, attaching to each element the
# `basename` key extracted from the filename.
my_data: !import-all-parameterized path/to/{basename:*}.yml
#
# my_data:
#  - basename: file1
#    key1: value1
#  - basename: file2
#    key2: value2
#    key3: value3
# 

# Import all YAML files in the `path/to/**/meta.yml` glob as a sequence, attaching to each
# element the `subdirs` key extracted from the subdirectory structure.
my_subdirs: !import-all-parameterized path/to/{subdirs:**}/meta.yml
#
# my_subdirs:
#  - subdirs: subdir1
#    key1: value1
#  - subdirs: subdir1/subdir2/subdir3
#    key2: value2
#    key3: value3
#
```

> **Note (i):** There is no safeguard against cyclical imports. If you import a file that imports the original file, it will result in exceeding Python's maximum recursion depth.
>
> **Note (ii):** When the leaf files of an import contain mappings, then it is simple to "merge" the metadata keys from the path into the resulting imported mappings. However, when the leaf files are scalars or sequences, then the structure of the import results are slightly more contrived. The contents of the imports will be under a `content` key in each result, with the metadata keys extracted from the path added as additional key/value pairs in the mappings.

**Syntax**

```
!import-all-parameterized [&anchor ]<glob_pattern>
```

**Examples**

<details>
<summary>Simple parameterized import (*) with metadata</summary>

```yaml
# example.yml
grade_book: !import-all schools/{school_name:*}/grades/{student_name:*}.yml
```

```yaml
# schools/elementary/grades/David.yml
math: 95
science: 90
english: 80
```

```yaml
# schools/elementary/grades/Edward.yml
math: 100
science: 90
english: 100
```

```yaml
# schools/highschool/grades/Frank.yml
math: 85
science: 95
english: 90
```

Result when loading in Python:

```python
data = {
  "grade_book": [
    {
      "school_name": "elementary",
      "student_name": "David",
      "math": 95,
      "science": 90,
      "english": 80
    },
    {
      "school_name": "elementary",
      "student_name": "Edward",
      "math": 100,
      "science": 90,
      "english": 100
    },
    {
      "school_name": "highschool",
      "student_name": "Frank",
      "math": 85,
      "science": 95,
      "english": 90
    }
  ]
}
```

</details>
<details>
<summary>Simple parameterized import (**) with metadata</summary>

```yaml
# example.yml
translations: !import-all-parameterized words/{langspec:**}/words.yml
```

```yaml
# words/en/us/words.yml
- hello
- goodbye
- color
- thanks
```

```yaml
# words/en/uk/words.yml
- good morrow
- toodle-oo
- colour
- cheers
```

```yaml
# words/es/mx/words.yml
- hola
- adios
- color
- gracias
```

Result when loading in Python:

```python
data = {
  "translations": [
    {
      "langspec": "en/us",
      "content": ["hello", "goodbye", "color", "thanks"]
    },
    {
      "langspec": "en/uk",
      "content": ["good morrow", "toodle-oo", "colour", "cheers"]
    },
    {
      "langspec": "es/mx",
      "content": ["hola", "adios", "color", "gracias"]
    }
  ]
}
```

</details>

#### Customizing the import directory

By default, `!import` tags will search relative to the current working directory of the Python process. You can customize the base directory for imports by calling `yaml_import.set_import_relative_dir(...)` with the desired base directory.

```python
import yaml
from yaml_extras import ExtrasLoader, yaml_import

yaml_import.set_import_relative_dir('/path/to/imports')
data = yaml.load('!import somefile.yml', Loader=ExtrasLoader)
```

## Roadmap

### P1
- [x] Add support for `!import` to import other whole documents into a YAML document (general import).
- [x] Add support for `!import.anchor` to import specific anchors from other YAML documents (targeted import).
- [x] Add support for `!import-all` to import a glob pattern of YAML files as a sequence.
- [x] Add support for `!import-all.anchor` to import a specific anchor from a glob pattern of YAML files as a sequence.
- [x] Add support for `!import-all-parameterized` to import a glob pattern of YAML files as a sequence with some data extracted from the filepath.
- [ ] Add support for `!import-all-parameterized.anchor` to import a specific anchor from a glob pattern of YAML files as a sequence with some data extracted from the filepath.
- [x] Allow user to set relative import directory.

### P2
- [ ] Implement type specification system to validate YAML files against a schema using a `!yamlschema` tag system which mimics JSON Schema semantics and are validated upon construction.
- [ ] Add support for `!env` tag to import environment variables.

### P3
- [ ] VSCode / Intellisense plugin to navigate through imports using cmd + click

## Acknowledgements

- David Sillman <dsillman2000@gmail.com>
- [pyyaml-include](https://github.com/tanbro/pyyaml-include) author, [@tanbro](https://github.com/tanbro).
- [PyYAML](https://github.com/yaml/pyyaml)