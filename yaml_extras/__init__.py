import os

import yaml
import yaml_include

from yaml_extras import yaml_concat


def register(yaml):
    # Register the constructor for the `!import` tag
    yaml.add_constructor("!import", yaml_include.Constructor(), Loader=yaml.Loader)
    # Register the constructor for the `!++` tag
    yaml.add_constructor("!++", yaml_concat.Constructor(), Loader=yaml.Loader)
