from dataclasses import dataclass
import yaml
import yaml_include


@dataclass
class Constructor(yaml_include.Constructor):

    def __call__(self, loader, node):
        return super().__call__(loader, node)
