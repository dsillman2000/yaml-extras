import os
from io import StringIO

import yaml

from yaml_extras import yaml_import


class ExtrasLoader(yaml.SafeLoader):
    def __init__(self, stream):
        super().__init__(stream)
        self.add_constructor("!import", yaml_import.Constructor())

    def flatten_mapping(self, node: yaml.Node):
        """The `flatten_mapping` implementation, which handles the "<<" merge key logic in PyYAML,
        needs to be patched to account for when the value(s) of the "<<" merge key are an "!import"
        tag. The expected behavior is for the contents of the files to be loaded via import before
        merging the results.

        Args:
            node (yaml.Node): The node to flatten.
        """
        if isinstance(node, yaml.MappingNode):
            for i in range(len(node.value)):
                key_node, value_node = node.value[i]
                if key_node.tag == "tag:yaml.org,2002:merge":
                    if isinstance(value_node, yaml.ScalarNode) and value_node.tag == "!import":
                        imported_value = self.construct_object(value_node)
                        data_buffer = StringIO()
                        imported_repr = yaml.SafeDumper(data_buffer).represent_data(imported_value)
                        node.value[i] = (key_node, imported_repr)
                    if isinstance(value_node, yaml.SequenceNode):
                        for j in range(len(value_node.value)):
                            subnode = value_node.value[j]
                            if isinstance(subnode, yaml.ScalarNode) and subnode.tag == "!import":
                                imported_value = self.construct_object(subnode)
                                data_buffer = StringIO()
                                imported_repr = yaml.SafeDumper(data_buffer).represent_data(
                                    imported_value
                                )
                                value_node.value[j] = imported_repr
                        node.value[i] = (key_node, value_node)

        super().flatten_mapping(node)
