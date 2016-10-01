import os

import yaml


def read_config(path):
    with open(os.path.join(path, 'config'), 'r') as c:
        config = yaml.load(c.read())
    return config


def write_config(path, config):
    with open(os.path.join(path, 'config'), 'w') as t:
        t.write(yaml.dump(config, default_flow_style=False))
