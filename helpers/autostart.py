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

bashcommando = 'play %s/waldo/sounds/autostart.mp3 -q' % main_path
os.system(bashcommando)  # invoke 'sox' in quiet mode

# os.system('%s/helpers/crash_recover.sh' % main_path)  # commented because it shuts down because autostart is running "now"

if measure_temp:
    # os.system('sudo python %s/helpers/monitor_temperature.py' % main_path)
    bashcommando = 'play %s/waldo/sounds/temp/monitore_temperature.mp3 -q' % main_path
    os.system(bashcommando)  # invoke 'sox' in quiet mode

    sp.Popen(['python', '%s/helpers/monitor_temperature.py' % main_path])

if autostart:
    # Notify about autostart
    bashcommando = 'play %s/waldo/sounds/temp/autostart_invoked.mp3 -q' % main_path  # sounds/chime.mp3
    os.system(bashcommando)  # invoke 'sox' in quiet mode

    # if autostart is number:
    if autostart is not True:
        autoplay = '-ap %s' % autostart
    else:
        autoplay = False

    sp.Popen(['python', '%s/helpers/shutdown_button.py' % main_path])
    sp.Popen('sudo python %s/helpers/remote.py %s' % (main_path, autoplay if autoplay else ''), shell=True)
    # os.system('sudo python %s/helpers/remote.py -ap %s' % (main_path, main_path, modifier))



    # os.system('sudo python %s/helpers/remote.py -ap %s' % (main_path, modifier))
    # os.system('python %s/helpers/numpad_listener.py' % main_path)
