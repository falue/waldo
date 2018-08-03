#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Start scripts if startup is true in main config file.
Play defined track
'''
import os
import sys
import subprocess as sp
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from waldo.utils import read_config
from waldo.fn import change_glob_rec_repl

# Read preferences
PREFERENCES = read_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
autostart = PREFERENCES['autostart']
measure_temp = PREFERENCES['measure_temp']

main_path = os.path.expanduser('~/Scripts/waldo')

# reset config file value recrepl (in case waldo is shut off unexpected):
change_glob_rec_repl(False)

# os.system('%s/helpers/crash_recover.sh' % main_path)  # commented because it shuts down because autostart is running "now"

if measure_temp:
    # os.system('sudo python %s/helpers/monitor_temperature.py' % main_path)
    sp.Popen(['python', '%s/helpers/monitor_temperature.py' % main_path])

if autostart:
    # Notify about autostart
    # bashcommando = 'play %s/waldo/sounds/chime.mp3 -q' % main_path
    # os.system(bashcommando)  # invoke 'sox' in quiet mode

    # if autostart is number:
    if autostart is not True:
        modifier = autostart
    else:
        modifier = ''

    sp.Popen(['python', '%s/helpers/shutdown_button.py' % main_path])
    os.system('sudo python %s/helpers/remote.py -ap %s' % (main_path, modifier))
    os.system('python %s/helpers/numpad_listener.py' % main_path)
