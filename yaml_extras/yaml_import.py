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
    global IMPORT_RELATIVE_DIR
    return IMPORT_RELATIVE_DIR()


def set_import_relative_dir(path: Path) -> None:
    global IMPORT_RELATIVE_DIR
    old = IMPORT_RELATIVE_DIR()
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
    path: Path

    @classmethod
    def from_str(cls, path_str: str) -> "ImportSpec":
        return cls(Path(get_import_relative_dir() / path_str))


@dataclass
class ImportConstructor:

    def __call__(self, loader: yaml.Loader, node: yaml.Node):
        """Heavily inspired by @tanbro's pyyaml-include library.

        Args:
            loader (yaml.Loader): YAML loader
            node (yaml.Node): Import tagged node
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
        # Just load the contents of the file
        return yaml.load(import_spec.path.open("r"), loader_type)


@dataclass
class ImportAnchorSpec:
    path: Path
    anchor: str

    @classmethod
    def from_str(cls, spec_str: str) -> "ImportAnchorSpec":
        path_str, anchor = spec_str.split(" &", 1)
        return cls(Path(get_import_relative_dir() / path_str), anchor)


@dataclass
class ImportAnchorConstructor:

    def __call__(self, loader: yaml.Loader, node: yaml.Node):
        """Import a specific anchor from within a file.

        Args:
            loader (yaml.Loader): YAML loader
            node (yaml.Node): Import anchor tagged node
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
        # Find target node events by anchor
        return load_yaml_anchor(import_spec.path.open("r"), import_spec.anchor, loader_type)


@dataclass
class ImportAllSpec:
    path_pattern: PathPattern

    @classmethod
    def from_str(cls, path_pattern_str: str) -> "ImportAllSpec":
        path_pattern = PathPattern(path_pattern_str, get_import_relative_dir())
        if path_pattern.names != []:
            raise ValueError(
                "Named wildcards are not supported in !import-all. Use !import-all-parameterized instead."
            )
        return cls(PathPattern(path_pattern_str, get_import_relative_dir()))


@dataclass
class ImportAllConstructor:

    def __call__(self, loader: yaml.Loader, node: yaml.Node):
        """Import all files that match a pattern as a sequence of objects.

        Args:
            loader (yaml.Loader): YAML loader
            node (yaml.Node): Import-all tagged node
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

    def load(self, loader_type: Type[yaml.Loader], import_spec: ImportAllSpec) -> Any:
        # Find and load all files that match the pattern into a sequence of objects
        return [
            yaml.load(path_w_metadata.path.open("r"), loader_type)
            for path_w_metadata in import_spec.path_pattern.results()
        ]


@dataclass
class ImportAllAnchorSpec:
    path_pattern: PathPattern
    anchor: str

    @classmethod
    def from_str(cls, path_pattern_str_w_anchor: str) -> "ImportAllAnchorSpec":
        path_pattern_str, anchor = path_pattern_str_w_anchor.split(" &", 1)
        path_pattern = PathPattern(path_pattern_str, get_import_relative_dir())
        if path_pattern.names != []:
            raise ValueError(
                "Named wildcards are not supported in !import-all. Use !import-all-parameterized instead."
            )
        return cls(PathPattern(path_pattern_str, get_import_relative_dir()), anchor)


@dataclass
class ImportAllAnchorConstructor:
    def __call__(self, loader: yaml.Loader, node: yaml.Node):
        """Import all files that match a pattern as a sequence of objects.

        Args:
            loader (yaml.Loader): YAML loader
            node (yaml.Node): Import-all tagged node
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

    def load(self, loader_type: Type[yaml.Loader], import_spec: ImportAllAnchorSpec) -> Any:
        # Find and load all files that match the pattern into a sequence of objects
        return [
            load_yaml_anchor(path_w_metadata.path.open("r"), import_spec.anchor, loader_type)
            for path_w_metadata in import_spec.path_pattern.results()
        ]


@dataclass
class ImportAllParameterizedSpec:
    path_pattern: PathPattern

    @classmethod
    def from_str(cls, path_pattern_str: str) -> "ImportAllParameterizedSpec":
        try:
            return cls(PathPattern(path_pattern_str, get_import_relative_dir()))
        except Exception as e:
            raise ValueError(f"Failed to form path pattern: {path_pattern_str}") from e


@dataclass
class ImportAllParameterizedConstructor:
    def __call__(self, loader: yaml.Loader, node: yaml.Node):
        """Import all files that match a pattern as a sequence of objects.

        Args:
            loader (yaml.Loader): YAML loader
            node (yaml.Node): Import-all tagged node
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

    def load(self, loader_type: Type[yaml.Loader], import_spec: ImportAllParameterizedSpec) -> Any:
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
