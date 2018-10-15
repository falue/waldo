#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function

import logging
import os
import subprocess
from time import sleep

from evdev import InputDevice, ecodes

from shutdown_button import rg_led
from waldo.audio import AudioPlayer
from waldo.player import preload_players
from waldo.utils import read_main_config

logger = logging.getLogger(__name__)


def run_listener(autostart=None):
    config = read_main_config()

    dev = wait_for_keyboard()

    players = preload_players()
    print('All players loaded.')
    AudioPlayer(os.path.expanduser('~/Scripts/waldo/waldo/sounds/chime.mp3')).play()
    rg_led('green')

    if autostart:
        players[autostart].play()

    try:
        read_loop(dev, config, players)
    except IOError:
        print('Keyboard unplugged.')
        run_listener(autostart=autostart)


def wait_for_keyboard():
    print('Checking for keyboard..')
    dev = False
    while not dev:
        try:
            # TODO: /dev/input/event1 can also be the LCD-touchscreen
            dev = InputDevice('/dev/input/event1')
        except OSError:
            print('No keyboard found..')
            sleep(0.5)
            rg_led('green')
            sleep(0.15)
            rg_led('red')
            sleep(0.15)
            rg_led('green')
            sleep(0.15)
            rg_led('red')
    print('Keyboard found.')
    rg_led('red')
    return dev


def read_loop(dev, config, players):
    for event in dev.read_loop():
        if event.value == 1:
            try:
                command = config['buttons'][ecodes.KEY[event.code]]

                subprocess.call(['killall', '-9', 'play'])

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
