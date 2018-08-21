#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function

import logging
import os
import sys

from evdev import InputDevice, ecodes

from waldo.player import Player


# FIXME: würg
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from waldo.fn import playback_audio
from waldo.utils import read_config

logger = logging.getLogger(__name__)


def create_players():
    logger.info('Pre-loading players')
    players = {}
    song_names = sorted([item for item in os.listdir(PROJECT_PATH) if not item.startswith('.')])

    for name in song_names:
        players[name] = Player(song=name)

    return players


def run_listener():
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
    config = read_config(config_path)

    dev = InputDevice('/dev/input/event1')

    players = create_players()
    playback_audio(os.path.expanduser('~/Scripts/waldo/waldo/sounds/chime.mp3'))

    for event in dev.read_loop():
        if event.value == 1:

            try:
                command = config['buttons'][ecodes.KEY[event.code]]

                for p in players.values():
                    if p.running:
                        p.stop()

                if command != 'cancel':
                    players[command].play()

            except KeyError:
                pass


if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)  # DEBUG / INFO / WARNING

    # Read preferences and set project folder path
    PREFERENCES = read_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
    # do not expand user due to autostart user is 'root' not 'pi'
    PROJECT_PATH = PREFERENCES["PROJECT_PATH"] if not os.path.isdir('projects') else 'projects'

    run_listener()
