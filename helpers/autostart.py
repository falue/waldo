#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Start scripts if startup is true in main config file.
Play defined track
'''
import os
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from waldo.utils import read_config

# Read preferences
PREFERENCES = read_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
autostart = PREFERENCES['autostart']

if autostart:
    # modifier = '-ap %s' % autostart if int(autostart) else ''
    if autostart is not True:
        modifier = autostart
    else:
        modifier = ''
    os.system('sudo python /home/pi/Scripts/waldo/helpers/remote.py -ap %s' % modifier)
    os.system('python /home/pi/Scripts/waldo/helpers/shutdown_button.py')
    # os.system('python /home/pi/Scripts/waldo/helpers/numpad_listener.py')
