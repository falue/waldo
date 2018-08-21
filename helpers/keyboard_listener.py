#!/usr/bin/env python
from __future__ import print_function

import os
import sys

from evdev import InputDevice, ecodes

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from waldo.fn import play_all, REC_REPL, playback_audio
from waldo.utils import read_config


class Player(object):
    # NOT YET FUNCTIONAL!!
    threads = []

    def __init__(self, song):
        self.song = song
        self.play()

    def play(self):
        print('play {}'.format(self.song))
        self.threads = play_all(self.song)
        print(self.threads)

    def stop(self):
        print('stop {}'.format(self.song))
        for t in self.threads:
            t.stop()


def cancel():
    os.system('killall play -9')
    global REC_REPL
    REC_REPL = False


def run_listener():
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
    config = read_config(config_path)

    dev = InputDevice('/dev/input/event1')
    playback_audio(os.path.expanduser('~/Scripts/waldo/waldo/sounds/chime.mp3'))

    for event in dev.read_loop():
        if event.value == 1:

            try:
                command = config['buttons'][ecodes.KEY[event.code]]
                cancel()

                if command != 'cancel':
                    play_all(command)
            except KeyError:
                pass


if __name__ == '__main__':
    run_listener()
