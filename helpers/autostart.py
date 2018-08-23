#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Start scripts if startup is true in main config file.
Play defined track
"""
import os
import subprocess
import sys
from os import path

from keyboard_listener import run_listener

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from waldo.utils import read_config
from waldo.fn import change_glob_rec_repl
from shutdown_button import shutdown_on_button_press, rg_led
from monitor_temperature import monitor_temperature

# Read preferences
PREFERENCES = read_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
# do not expand user due to autostart user is 'root' not 'pi'
PROJECT_PATH = PREFERENCES["PROJECT_PATH"] if not os.path.isdir('projects') else 'projects'

autostart = PREFERENCES['autostart']
measure_temp = PREFERENCES['measure_temp']

# reset config file value recrepl (in case waldo is shut off unexpected):
change_glob_rec_repl(False)

shutdown_on_button_press()

# set volume to 80%
subprocess.call(['amixer', '-q', 'set', 'Speaker', '20%'])  # amixer set PCM -- 100% amixer sset 'Master' 50%

if measure_temp:
    monitor_temperature()

if autostart:
    run_listener(autostart=autostart if type(autostart) is str else None)
else:
    rg_led('green')
