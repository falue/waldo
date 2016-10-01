import os

from waldo.utils import read_config, write_config

TEST_PATH = os.path.join(os.path.dirname(__file__), 'data/projects')


def test_read_write_config():
    config = {'connection': '',
              'baudrate': '960011',
              'CLK': 18,
              'MISO': 23,
              'MOSI': 24,
              'CS': 25,
              'channel_1': {'in': 1,
                            'out': 2,
                            'max': 0,
                            'min': 1024},
              'channel_2': {'in': 1,
                            'out': 2,
                            'max': 0,
                            'min': 1024},
              }

    write_config(project_name='test', config=config, path=TEST_PATH)
    assert config == read_config(project_name='test', path=TEST_PATH)
