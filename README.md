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

with open('example.yml') as f:
    data = yaml.load(f, Loader=ExtrasLoader)

print(f"data = {json.dumps(data, indent=2)}")
```

## Features

### Modularity with "import"

`!import` tag: Import another whole YAML file. Supports multiple-import using the "<<" merge key, as well as aliasing the result of an import using an anchor.

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
grandchild: &grandhcild
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

## Roadmap

### P1
- [x] Add support for `!import` to import other whole documents into a YAML document (general import).
- [x] Add support for `!import.anchor` to import specific anchors from other YAML documents (targeted import).
- [ ] Utilize this project in a downstream project to generate code and documentation.

### P2
- [ ] Add support for `!env` tag to import environment variables.
- [ ] VSCode / Intellisense plugin to navigate through imports using cmd + click

## Acknowledgements

- David Sillman <dsillman2000@gmail.com>
- [pyyaml-include](https://github.com/tanbro/pyyaml-include) author, [@tanbro](https://github.com/tanbro).
- [PyYAML](https://github.com/yaml/pyyaml)