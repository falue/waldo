#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Start scripts if startup is true in main config file.
Play defined track
"""
import os
import sys
from os import path

from keyboard_listener import run_listener

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from waldo.utils import read_config
from waldo.fn import change_glob_rec_repl, play_all
from shutdown_button import shutdown_on_button_press
from monitor_temperature import monitor_temperature

# Read preferences
PREFERENCES = read_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
autostart = PREFERENCES['autostart']
measure_temp = PREFERENCES['measure_temp']

main_path = os.path.expanduser('~/Scripts/waldo')

# reset config file value recrepl (in case waldo is shut off unexpected):
change_glob_rec_repl(False)

shutdown_on_button_press()

if measure_temp:
    monitor_temperature()

if autostart:
    run_listener(autostart=autostart if type(autostart) is str else None)
