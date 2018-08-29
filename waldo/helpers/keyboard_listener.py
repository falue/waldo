#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function

import logging
import os
from time import sleep

from evdev import InputDevice, ecodes

from shutdown_button import rg_led
from waldo.audio import AudioPlayer
from waldo.player import preload_players
from waldo.utils import read_main_config

logger = logging.getLogger(__name__)


def run_listener(autostart=None):
    config = read_main_config()

    dev = InputDevice('/dev/input/event1')

    players = preload_players()
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
                    players[command].play(pre_loaded=True)

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
    FORMAT = '%(asctime)s - %(name)-12s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)  # DEBUG / INFO / WARNING

    run_listener()

    while True:
        sleep(1)
