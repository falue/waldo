#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function

import logging
import os
import sys
from time import sleep

from evdev import InputDevice, ecodes

from shutdown_button import rg_led
from waldo.audio import AudioPlayer
from waldo.player import Player

# FIXME: Fix project structure
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from waldo.utils import read_config

# FIXME: Remove global variables!
# Read preferences and set project folder path
PREFERENCES = read_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
# do not expand user due to autostart user is 'root' not 'pi'
PROJECT_PATH = PREFERENCES["PROJECT_PATH"] if not os.path.isdir('projects') else 'projects'

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)  # DEBUG / INFO / WARNING

logger = logging.getLogger(__name__)


# FIXME: move where it belongs
def create_players():
    logger.info('Pre-loading players')
    players = {}
    song_names = sorted(
        [item for item in os.listdir(PROJECT_PATH) if not item.startswith('.') and not item == '_archive']
    )

    for name in song_names:
        players[name] = Player(song=name)

    return players


def run_listener(autostart=None):
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
    config = read_config(config_path)

    dev = InputDevice('/dev/input/event1')

    players = create_players()
    AudioPlayer(os.path.expanduser('~/Scripts/waldo/waldo/sounds/chime.mp3')).play()
    rg_led('green')

    if autostart:
        players[autostart].play()

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

            # KEY_NUMLOCK
            # KEY_RESERVED
            # KEY_EQUAL
            # KEY_KPSLASH
            # KEY_KPASTERISK
            # KEY_BACKSPACE
            # KEY_KPMINUS
            # KEY_KPPLUS
            # KEY_KPENTER
            # KEY_KPDOT
            # KEY_TAB

            # if(ecodes.KEY[event.code] == 'KEY_KPMINUS'):
            #     print('set MAP MIN')
            #
            # if(ecodes.KEY[event.code] == 'KEY_KPPLUS'):
            #     print('set MAP Max')
            #
            # if(ecodes.KEY[event.code] == 'KEY_KPASTERISK'):
            #     print('start recording and stop recording')

            # return ecodes.KEY[event.code]  # to control different things


if __name__ == '__main__':
    run_listener()

    while True:
        sleep(1)
