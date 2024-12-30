"""
This module implements the custom Constructor behaviors for the ExtrasLoader to allow for importing
external YAML modules and anchors from within them into the current YAML document.

The following tags are supported:

- `!import`: Import the entire contents of a file into the current document.
- `!import.anchor`: Import a specific anchor from within a file.
- `!import-all`: Import all files that match a pattern as a sequence of objects.
- `!import-all.anchor`: Import a specific anchor from all files that match a pattern as a sequence 
  of objects.
- `!import-all-parameterized`: Import all files that match a pattern as a sequence of objects, 
  including merging the named wildcards into the results.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any, Callable, Type
import yaml

from yaml_extras.file_utils import PathPattern, PathWithMetadata


IMPORT_RELATIVE_DIR: Callable[[], Path] = Path.cwd


def _reset_import_relative_dir() -> None:
    global IMPORT_RELATIVE_DIR
    IMPORT_RELATIVE_DIR = Path.cwd


def get_import_relative_dir() -> Path:
    """Read a global variable to get the current relative directory for imports.

    Returns:
        Path: Current relative directory for imports.
    """
    global IMPORT_RELATIVE_DIR
    return IMPORT_RELATIVE_DIR()


def set_import_relative_dir(path: Path) -> None:
    """Set a global variable to change the current relative directory for imports.

    Args:
        path (Path): New relative directory for imports.
    """
    global IMPORT_RELATIVE_DIR
    IMPORT_RELATIVE_DIR = lambda: path


def load_yaml_anchor(file_stream: IO, anchor: str, loader_type: Type[yaml.Loader]) -> Any:
    """Load an anchor from a YAML file.

    Args:
        file_stream (IO): YAML file stream to load from.
        anchor (str): Anchor to load.

    Returns:
        Any: Content from the yaml file which the anchor marks.
    """
    level = 0
    events: list[yaml.Event] = []
    for event in yaml.parse(file_stream, loader_type):
        if isinstance(event, yaml.events.ScalarEvent) and event.anchor == anchor:
            events = [event]
            break
        elif isinstance(event, yaml.events.MappingStartEvent) and event.anchor == anchor:
            events = [event]
            level = 1
        elif isinstance(event, yaml.events.SequenceStartEvent) and event.anchor == anchor:
            events = [event]
            level = 1
        elif level > 0:
            events.append(event)
            if isinstance(event, (yaml.MappingStartEvent, yaml.SequenceStartEvent)):
                level += 1
            elif isinstance(event, (yaml.MappingEndEvent, yaml.SequenceEndEvent)):
                level -= 1
            if level == 0:
                break
    if not events:
        raise ValueError(f"Anchor '{anchor}' not found in {file_stream.name}")
    events = (
        [yaml.StreamStartEvent(), yaml.DocumentStartEvent()]
        + events
        + [yaml.DocumentEndEvent(), yaml.StreamEndEvent()]
    )
    return yaml.load(yaml.emit(evt for evt in events), loader_type)


@dataclass
class ImportSpec:
    """Small utility dataclass for typing the parsed argument to the `!import` tag. E.g.,

    ```yaml
    my-data: !import path/to/file.yml
    ```

    Shall be parsed as,

    ```python
    ImportSpec(Path("path/to/file.yml"))
    ```

    Attributes:
        path (Path): Relative path to the file to be imported

    Methods:
        from_str: Parse a string into an `ImportSpec` dataclass.
    """

    path: Path

    @classmethod
    def from_str(cls, path_str: str) -> "ImportSpec":
        """Parse a string into an `ImportSpec` dataclass.

        Args:
            path_str (str): Relative path to the file to be imported

        Returns:
            ImportSpec: Dataclass containing the path to the file to be imported.
        """
        return cls(Path(get_import_relative_dir() / path_str))


@dataclass
class ImportConstructor:
    """Custom PyYAML constructor for the `!import` tag, which loads an entire file into the current
    document.

    As a Constructor, it can be called with a `yaml.Loader` and a `yaml.Node` to attempt to
    construct a given node tagged as `!import` into a Python object. In any valid use of the tag,
    this node should always be a scalar string, e.g.:

    ```yaml
    my-data: !import path/to/my/file.yml
    ```

    To standardize the parsing of the tag's argument, the Constructor uses an
    [`ImportSpec`](./#yaml_extras.yaml_import.ImportSpec)
    dataclass to hold the path to the file to be imported, as a relative path.

    Methods:
        __call__: Construct a node tagged as `!import` into a Python object.
        load: Using a specified loader type, load the contents of the file specified in the
            `ImportSpec` dataclass.
    """

    def __call__(self, loader: yaml.Loader, node: yaml.Node) -> Any:
        """Using the specified loader, attempt to construct a node tagged as `!import` into a Python
        object.

        For any valid use of the tag, the node should always be a scalar string in the form of
        a relative file path.

        Heavily inspired by [@tanbro](https://github.com/tanbro)'s
        [pyyaml-include](https://github.com/tanbro/pyyaml-include) library.

        Args:
            loader (yaml.Loader): YAML loader
            node (yaml.Node): `!import`-tagged node

        Returns:
            Any: Result of loading the file's contents using the specified loader.
        """
        import_spec: ImportSpec
        if isinstance(node, yaml.ScalarNode):
            val = loader.construct_scalar(node)
            if isinstance(val, str):
                import_spec = ImportSpec.from_str(val)
            else:
                raise TypeError(f"!import Expected a string, got {type(val)}")
        else:
            raise TypeError(f"!import Expected a string scalar, got {type(node)}")
        return self.load(type(loader), import_spec)

    def load(self, loader_type: Type[yaml.Loader], import_spec: ImportSpec) -> Any:
        """Utility function to load the contents of the file specified in the `ImportSpec`
        dataclass.

        Args:
            loader_type (Type[yaml.Loader]): YAML loader type
            import_spec (ImportSpec): Dataclass containing the path to the file to be imported.

        Returns:
            Any: Result of loading the file's contents using the specified loader type.
        """
        # Just load the contents of the file
        return yaml.load(import_spec.path.open("r"), loader_type)


@dataclass
class ImportAnchorSpec:
    """Small utility dataclass for typing the parsed arguments to the `!import.anchor` tag. E.g.,

    ```yaml
    my-data: !import.anchor path/to/file.yml &my-anchor
    ```

    Shall be parsed as,

    ```python
    ImportAnchorSpec(Path("path/to/file.yml"), "my-anchor")
    ```

    Attributes:
        path (Path): Relative path to the file to be imported
        anchor (str): Anchor to be loaded

    Methods:
        from_str: Parse a string into an `ImportAnchorSpec` dataclass.
    """

    path: Path
    anchor: str

    @classmethod
    def from_str(cls, spec_str: str) -> "ImportAnchorSpec":
        """Parse the string into an `ImportAnchorSpec` dataclass. It is expected that the string
        will be in the form of `path/to/file.yml &anchor`.

        Args:
            spec_str (str): String to be parsed

        Returns:
            ImportAnchorSpec: Dataclass containing the path to the file to be imported and the
                anchor to be loaded.
        """
        path_str, anchor = spec_str.split(" &", 1)
        return cls(Path(get_import_relative_dir() / path_str), anchor)


@dataclass
class ImportAnchorConstructor:
    """Custom PyYAML constructor for the `!import.anchor` tag, which loads a specific anchor from a
    file into the current document.

    As a Constructor, it can be called with a `yaml.Loader` and a `yaml.Node` to attempt to
    construct a given node tagged as `!import.anchor` into a Python object. In any valid use of the
    tag, this node should always be a scalar string.

    It is expected that the first token of the string is the path to the file to be imported, and
    the second token is the anchor to be imported (leading with `&`), e.g.:

    ```yaml
    my-data: !import.anchor path/to/my/file.yml &my-anchor
    ```

    To standardize the parsing of the tag's argument, the Constructor uses an
    [`ImportAnchorSpec`](./#yaml_extras.yaml_import.ImportAnchorSpec)
    dataclass to hold the path to the file to be imported and the anchor to be loaded.

    Methods:
        __call__: Construct a node tagged as `!import.anchor` into a Python object.
        load: Using a specified loader type, load the anchor from the specified file by scanning the
            file for the anchor and extracting the node it marks.
    """

    def __call__(self, loader: yaml.Loader, node: yaml.Node) -> Any:
        """Using the specified loader, attempt to construct a node tagged as `!import.anchor` into a
        Python object.

        For any valid use of the tag, the node should always be a scalar string. It
        is expected that the first token of the string is the path to the file to be imported, and
        the second token is the anchor to be imported (leading with `&`).

        Args:
            loader (yaml.Loader): YAML loader.
            node (yaml.Node): `!import.anchor`-tagged node.

        Returns:
            Any: Result of loading the anchor from the file using the specified loader.
        """
        import_spec: ImportAnchorSpec
        if isinstance(node, yaml.ScalarNode):
            val = loader.construct_scalar(node)
            if isinstance(val, str):
                import_spec = ImportAnchorSpec.from_str(val)
            else:
                raise TypeError(f"!import.anchor Expected a string, got {type(val)}")
        else:
            raise TypeError(f"!import.anchor Expected a string scalar, got {type(node)}")
        return self.load(type(loader), import_spec)

    def load(self, loader_type: Type[yaml.Loader], import_spec: ImportAnchorSpec) -> Any:
        """Utility function which, using the specified loader type and the `ImportAnchorSpec`,
        attempts to load the anchor from the specified file by scanning the file for the anchor and
        extracting the node it marks.

        Args:
            loader_type (Type[yaml.Loader]): YAML loader type.
            import_spec (ImportAnchorSpec): Dataclass containing the path to the file to be imported
                and the anchor to be loaded.

        Returns:
            Any: Result of loading the anchor from the file using the specified loader type.
        """
        return load_yaml_anchor(import_spec.path.open("r"), import_spec.anchor, loader_type)


@dataclass
class ImportAllSpec:
    """Small utility dataclass for typing the parsed argument to the `!import-all` tag as a
    specialized `PathPattern` type. E.g.,

    ```yaml
    my-data: !import-all data/*.yml
    ```

    Shall be parsed as,

    ```python
    ImportAllSpec(PathPattern("data/*.yml", ...))
    ```

    Attributes:
        path_pattern (PathPattern): Pattern for matching files to be imported.

    Methods:
        from_str: Parse a string into an `ImportAllSpec` dataclass.
    """

    path_pattern: PathPattern

    @classmethod
    def from_str(cls, path_pattern_str: str) -> "ImportAllSpec":
        """Parse a string into an `ImportAllSpec` dataclass. It is expected that the string is a
        valid path pattern with no named wildcards.

        Args:
            path_pattern_str (str): String containing a path pattern to be parsed.

        Raises:
            ValueError: If the user supplies named wildcards in the path pattern, which should only
                be used in `!import-all-parameterized`.

        Returns:
            ImportAllSpec: Dataclass containing the path pattern to be matched.
        """
        path_pattern = PathPattern(path_pattern_str, get_import_relative_dir())
        if path_pattern.names != []:
            raise ValueError(
                "Named wildcards are not supported in !import-all. Use !import-all-parameterized "
                "instead."
            )
        return cls(PathPattern(path_pattern_str, get_import_relative_dir()))


@dataclass
class ImportAllConstructor:
    """Custom PyYAML constructor for the `!import-all` tag, which loads all files that match a
    glob pattern into the current document.

    As a Constructor, it can be called with a `yaml.Loader` and a `yaml.Node` to attempt to
    construct a given node tagged as `!import-all` into a Python object. In any valid use of the
    tag, this node should always be a scalar string, and it should be in the form of a path glob
    _with no named wildcards_, e.g.:

    ```yaml
    my-data: !import-all data/*.yml
    ```

    To standardize the parsing of the tag's argument, the Constructor uses an
    [`ImportAllSpec`](./#yaml_extras.yaml_import.ImportAllSpec) dataclass to hold the path pattern
    object to be matched after it's been parsed from the string in the YAML document.
    """

    def __call__(self, loader: yaml.Loader, node: yaml.Node) -> list[Any]:
        """Using the specified loader, attempt to construct a node tagged as `!import-all` into a
        sequence of Python objects.

        For any valid use of the tag, the node should always be a scalar string, and it should be in
        the form of a path glob _with no named wildcards_.

        Args:
            loader (yaml.Loader): YAML loader
            node (yaml.Node): `!import-all`-tagged node

        Returns:
            list[Any]: List of objects loaded from the files that match the pattern.
        """
        import_spec: ImportAllSpec
        if isinstance(node, yaml.ScalarNode):
            val = loader.construct_scalar(node)
            if isinstance(val, str):
                import_spec = ImportAllSpec.from_str(val)
            else:
                raise TypeError(f"!import-all Expected a string, got {type(val)}")
        else:
            raise TypeError(f"!import-all Expected a string scalar, got {type(node)}")
        return self.load(type(loader), import_spec)

    def load(self, loader_type: Type[yaml.Loader], import_spec: ImportAllSpec) -> list[Any]:
        """Utility function which, using the specified loader type and the `ImportAllSpec`, attempts
        to load all files that match the pattern into a list of objects (one per each file matched).

        Args:
            loader_type (Type[yaml.Loader]): YAML loader type
            import_spec (ImportAllSpec): Dataclass containing the path pattern to be matched.

        Returns:
            list[Any]: List of objects loaded from the files that match the pattern.
        """
        # Find and load all files that match the pattern into a sequence of objects
        return [
            yaml.load(path_w_metadata.path.open("r"), loader_type)
            for path_w_metadata in import_spec.path_pattern.results()
        ]


@dataclass
class ImportAllAnchorSpec:
    """Small utility dataclass for typing the parsed argument to the `!import-all.anchor` tag as a
    specialized `PathPattern` type. E.g.,

    ```yaml
    my-data: !import-all.anchor data/*.yml &my-anchor
    ```

    Shall be parsed as,

    ```python
    ImportAllAnchorSpec(PathPattern("data/*.yml", ...), "my-anchor")
    ```

    Attributes:
        path_pattern (PathPattern): Pattern for matching files to be imported.
        anchor (str): Anchor to be loaded from each file.

    Methods:
        from_str: Parse a string into an `ImportAllAnchorSpec` dataclass.
    """

    path_pattern: PathPattern
    anchor: str

    @classmethod
    def from_str(cls, path_pattern_str_w_anchor: str) -> "ImportAllAnchorSpec":
        """Parse a string into an `ImportAllAnchorSpec` dataclass. It is expected that the string
        contains a valid path pattern with no named wildcards, followed by an anchor to be loaded
        from each file.

        Args:
            path_pattern_str_w_anchor (str): String containing a path pattern and an anchor to be
                loaded from each file.

        Raises:
            ValueError: If the user supplies named wildcards in the path pattern, which should only
                be used in `!import-all-parameterized`.

        Returns:
            ImportAllAnchorSpec: Dataclass containing the path pattern to be matched and the anchor
                to be loaded from each file.
        """
        path_pattern_str, anchor = path_pattern_str_w_anchor.split(" &", 1)
        path_pattern = PathPattern(path_pattern_str, get_import_relative_dir())
        if path_pattern.names != []:
            raise ValueError(
                "Named wildcards are not supported in !import-all. Use !import-all-parameterized "
                "instead."
            )
        return cls(PathPattern(path_pattern_str, get_import_relative_dir()), anchor)


@dataclass
class ImportAllAnchorConstructor:
    """Custom PyYAML constructor for the `!import-all.anchor` tag, which loads a specific anchor
    from each of the files that match a glob pattern into the current document as a sequence of
    objects.

    As a Constructor, it can be called with a `yaml.Loader` and a `yaml.Node` to attempt to
    construct a given node tagged as `!import-all.anchor` into a Python object. In any valid use of
    the tag, this node should always be a scalar string, and it should be in the form of a path glob
    _with no named wildcards_, followed by an anchor to be loaded from each file, e.g.:

    ```yaml
    my-data: !import-all.anchor data/*.yml &my-anchor
    ```

    To standardize the parsing of the tag's argument, the Constructor uses an
    [`ImportAllAnchorSpec`](./#yaml_extras.yaml_import.ImportAllAnchorSpec) dataclass to hold the
    path pattern object to be matched and the anchor to be loaded from each file.
    """

    def __call__(self, loader: yaml.Loader, node: yaml.Node) -> list[Any]:
        """Using the specified loader, attempt to construct a node tagged as `!import-all.anchor`
        into a sequence of Python objects.

        For any valid use of the tag, the node should always be a scalar string, and it should be in
        the form of a path glob _with no named wildcards_, followed by an anchor to be loaded from
        each file.

        Args:
            loader (yaml.Loader): YAML loader
            node (yaml.Node): `!import-all.anchor`-tagged node

        Returns:
            list[Any]: List of anchored objects loaded from the files that match the pattern.
        """
        import_spec: ImportAllAnchorSpec
        if isinstance(node, yaml.ScalarNode):
            val = loader.construct_scalar(node)
            if isinstance(val, str):
                import_spec = ImportAllAnchorSpec.from_str(val)
            else:
                raise TypeError(f"!import-all.anchor Expected a string, got {type(val)}")
        else:
            raise TypeError(f"!import-all.anchor Expected a string scalar, got {type(node)}")
        return self.load(type(loader), import_spec)

    def load(self, loader_type: Type[yaml.Loader], import_spec: ImportAllAnchorSpec) -> list[Any]:
        """Utility function which, using the specified loader type and the `ImportAllAnchorSpec`,
        attempts to load a specific anchor from each of the files that match the pattern into a
        sequence of objects.

        Args:
            loader_type (Type[yaml.Loader]): YAML loader type
            import_spec (ImportAllAnchorSpec): Dataclass containing the path pattern to be matched
                and the anchor to be loaded from each file.

        Returns:
            list[Any]: List of anchored objects loaded from the files that match the pattern.
        """
        # Find and load all files that match the pattern into a sequence of objects
        return [
            load_yaml_anchor(path_w_metadata.path.open("r"), import_spec.anchor, loader_type)
            for path_w_metadata in import_spec.path_pattern.results()
        ]


@dataclass
class ImportAllParameterizedSpec:
    """Small utility dataclass for typing the parsed argument to the `!import-all-parameterized` tag
    as a specialized `PathPattern` type. E.g.,

    ```yaml
    my-data: !import-all-parameterized data/{file_name:*}.yml
    ```

    Shall be parsed as,

    ```python
    ImportAllParameterizedSpec(PathPattern("data/{file_name:*}.yml", ...))
    ```

    Attributes:
        path_pattern (PathPattern): Pattern for matching files to be imported, optionally using
            named wildcards.

    Methods:
        from_str: Parse a string into an `ImportAllParameterizedSpec` dataclass.

    """

    path_pattern: PathPattern

    @classmethod
    def from_str(cls, path_pattern_str: str) -> "ImportAllParameterizedSpec":
        """Parse a string into an `ImportAllParameterizedSpec` dataclass. It is expected that the
        string contains a valid path pattern, optionally with named wildcards for extracting
        some metadata strings from the matched file paths.

        Args:
            path_pattern_str (str): String containing a path pattern to be parsed.

        Raises:
            ValueError: If the PathPattern fails to be parsed from the provided string.

        Returns:
            ImportAllParameterizedSpec: Dataclass containing the path pattern to be matched.
        """
        try:
            return cls(PathPattern(path_pattern_str, get_import_relative_dir()))
        except Exception as e:
            raise ValueError(f"Failed to form path pattern: {path_pattern_str}") from e


@dataclass
class ImportAllParameterizedConstructor:
    """Custom PyYAML constructor for the `!import-all-parameterized` tag, which loads all files that
    match a glob pattern into the current document, including merging the named wildcards into each
    result.

    As a Constructor, it can be called with a `yaml.Loader` and a `yaml.Node` to attempt to
    construct a given node tagged as `!import-all-parameterized` into a Python object. In any valid
    use of the tag, this node should always be a scalar string, and it should be in the form of a
    valid path pattern, optionally with named wildcards, e.g.:

    ```yaml
    my-data: !import-all-parameterized data/{file_name:*}.yml
    more-data: !import-all-parameterized data/{sub_dirs:**}/info.yml
    ```

    To standardize the parsing of the tag's argument, the Constructor uses an
    [`ImportAllParameterizedSpec`](./#yaml_extras.yaml_import.ImportAllParameterizedSpec) dataclass
    to hold the path pattern object to be matched after it's been parsed from the string in the YAML
    document.

    Methods:
        __call__: Construct a node tagged as `!import-all-parameterized` into a Python object.
        load: Using a specified loader type, load the contents of the files that match the pattern
            into a sequence of objects, including merging the named wildcards into each result.

    """

    def __call__(self, loader: yaml.Loader, node: yaml.Node) -> list[Any]:
        """Using the specified loader, attempt to construct a node tagged as
        `!import-all-parameterized` into a sequence of Python objects. For any valid use of the tag,
        the node should always be a scalar string, and it should be in the form of a valid path
        pattern, optionally with named wildcards.

        Args:
            loader (yaml.Loader): YAML loader
            node (yaml.Node): `!import-all-parameterized`-tagged node

        Returns:
            list[Any]: List of objects loaded from the files that match the pattern, including
                merging the named wildcards into each result.
        """
        import_spec: ImportAllParameterizedSpec
        if isinstance(node, yaml.ScalarNode):
            val = loader.construct_scalar(node)
            if isinstance(val, str):
                import_spec = ImportAllParameterizedSpec.from_str(val)
            else:
                raise TypeError(f"!import-all Expected a string, got {type(val)}")
        else:
            raise TypeError(f"!import-all Expected a string scalar, got {type(node)}")
        return self.load(type(loader), import_spec)

    def load(
        self, loader_type: Type[yaml.Loader], import_spec: ImportAllParameterizedSpec
    ) -> list[Any]:
        """Utility function which, using the specified loader type and the
        `ImportAllParameterizedSpec`, attempts to load the contents of the files that match the
        pattern into a sequence of objects, including merging the named wildcards into the results.

        Args:
            loader_type (Type[yaml.Loader]): YAML loader type
            import_spec (ImportAllParameterizedSpec): Dataclass containing the path pattern to be
                matched.

        Returns:
            list[Any]: List of objects loaded from the files that match the pattern, including
                merging the named wildcards into each result.
        """
        # Find and load all files that match the pattern into a sequence of objects, including
        # merging the named wildcards into the results.
        import_results: dict[PathWithMetadata, Any] = {
            path_w_metadata: yaml.load(path_w_metadata.path.open("r"), loader_type)
            for path_w_metadata in import_spec.path_pattern.results()
        }
        _to_object = lambda content: content if isinstance(content, dict) else {"content": content}
        return [
            _to_object(content) | (path_w_metadata.metadata or {})
            for path_w_metadata, content in import_results.items()
        ]


_Constructor = yaml.constructor.Constructor | Any
RESERVED_TAGS: dict[str, Type[_Constructor]] = {
    "!import": ImportConstructor,
    "!import.anchor": ImportAnchorConstructor,
    "!import-all": ImportAllConstructor,
    "!import-all.anchor": ImportAllAnchorConstructor,
    "!import-all-parameterized": ImportAllParameterizedConstructor,
}
