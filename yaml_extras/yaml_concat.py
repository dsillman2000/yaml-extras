from dataclasses import dataclass
from functools import reduce
from typing import Dict, List

import yaml


@dataclass
class Constructor:
    """A custom constructor which concatenates a list of mappings or sequences, including anchors and aliases."""

    def __call__(self, loader: yaml.Loader, node: yaml.Node):
        # Concatenate the mappings or sequences
        if not isinstance(node, yaml.SequenceNode):
            raise yaml.constructor.ConstructorError(
                None, None, "expected a sequence but found %s" % node.id, node.start_mark
            )
        member_type: type = None
        merged_result: dict | list | None = None
        for member in node.value:
            if isinstance(member, yaml.MappingNode):
                if member_type is None:
                    member_type = dict
                    merged_result = {}
                elif member_type is not dict:
                    raise yaml.constructor.ConstructorError(
                        None, None, "expected a mapping but found %s" % member.id, member.start_mark
                    )
                merged_result |= loader.construct_mapping(member)
            elif isinstance(member, yaml.SequenceNode):
                if member_type is None:
                    member_type = list
                    merged_result = []
                elif member_type is not list:
                    raise yaml.constructor.ConstructorError(
                        None, None, "expected a sequence but found %s" % member.id, member.start_mark
                    )
                merged_result += loader.construct_sequence(member)
            elif isinstance(member, yaml.ScalarNode):
                if member.tag == "!import":
                    imported_member = loader.construct_object(member)
                    if isinstance(imported_member, dict):
                        if member_type is None:
                            member_type = dict
                            merged_result = {}
                        elif member_type is not dict:
                            raise yaml.constructor.ConstructorError(
                                None, None, "expected a mapping but found %s" % member.id, member.start_mark
                            )
                        merged_result |= imported_member
                    elif isinstance(imported_member, list):
                        if member_type is None:
                            member_type = list
                            merged_result = []
                        elif member_type is not list:
                            raise yaml.constructor.ConstructorError(
                                None, None, "expected a sequence but found %s" % member.id, member.start_mark
                            )
                        merged_result += imported_member
                    else:
                        print(imported_member)
                        raise yaml.constructor.ConstructorError(
                            None, None, "expected a mapping or sequence but found %s" % member.id, member.start_mark
                        )
            else:
                raise yaml.constructor.ConstructorError(
                    None, None, "expected a mapping or sequence but found %s" % member.id, member.start_mark
                )
        if merged_result is None:
            raise yaml.constructor.ConstructorError(None, None, "expected a mapping or sequence", node.start_mark)
        return merged_result
