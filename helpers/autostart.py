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

# Read preferences
PREFERENCES = read_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
autostart = PREFERENCES['autostart']

if autostart:
    # if autostart is number:
    if autostart is not True:
        modifier = autostart
    else:
        modifier = ''
    main_path = os.path.expanduser('~/Scripts/waldo')
    sp.Popen(['python', '/home/pi/Scripts/waldo/helpers/shutdown_button.py'])
    os.system('sudo python /home/pi/Scripts/waldo/helpers/remote.py -ap %s' % modifier)
    os.system('python %s/helpers/numpad_listener.py' % main_path)
