import os

import yaml

PROJECT_PATH = os.path.expanduser('~/waldo_projects')


def read_config(project_name, path=PROJECT_PATH):
    with open(os.path.join(path, project_name, 'config'), 'r') as c:
        config = yaml.load(c.read())
    return config


def write_config(project_name, config, path):
    with open(os.path.join(path, project_name, 'config'), 'w') as t:
        t.write(yaml.dump(config, default_flow_style=False))
