#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import subprocess
from time import sleep

from waldo.helpers.keyboard_listener import run_listener
from waldo.helpers.monitor_temperature import monitor_temperature
from waldo.helpers.shutdown_button import shutdown_on_button_press, rg_led
from waldo.utils import read_config


def run_daemon():
    # Read preferences
    preferences = read_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

    autostart = preferences['autostart']
    measure_temp = preferences['measure_temp']

    shutdown_on_button_press()

    # Set volume to 30%
    subprocess.call(['amixer', '-q', 'set', 'Speaker', '30%'])  # amixer set PCM -- 100% amixer sset 'Master' 50%

    if measure_temp:
        monitor_temperature()

    if autostart:
        run_listener(autostart=autostart if type(autostart) is str else None)
    else:
        rg_led('green')

    while True:
        sleep(1)
