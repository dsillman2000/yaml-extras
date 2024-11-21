from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any, Type
import yaml


@dataclass
class ImportSpec:
    path: Path

    @classmethod
    def from_str(cls, path_str: str) -> "ImportSpec":
        return cls(Path(path_str))


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
        return cls(Path(path_str), anchor)


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
        level = 0
        events: list[yaml.Event] = []
        for event in yaml.parse(import_spec.path.open("r"), loader_type):
            if isinstance(event, yaml.events.ScalarEvent) and event.anchor == import_spec.anchor:
                events = [event]
                break
            elif (
                isinstance(event, yaml.events.MappingStartEvent)
                and event.anchor == import_spec.anchor
            ):
                events = [event]
                level = 1
            elif (
                isinstance(event, yaml.events.SequenceStartEvent)
                and event.anchor == import_spec.anchor
            ):
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
            raise ValueError(f"Anchor '{import_spec.anchor}' not found in {import_spec.path}")
        events = (
            [yaml.StreamStartEvent(), yaml.DocumentStartEvent()]
            + events
            + [yaml.DocumentEndEvent(), yaml.StreamEndEvent()]
        )
        return yaml.load(yaml.emit(evt for evt in events), loader_type)
