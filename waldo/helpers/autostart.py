#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))  # import modules from one level above
from utils import read_config

# Read preferences
PREFERENCES = read_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..'))
autostart = PREFERENCES['autostart']

print autostart

if autostart:
    # modifier = '-ap %s' % autostart if int(autostart) else ''
    if autostart is not True:
        modifier = '-ap %s' % int(autostart)
    else:
        modifier = ''

    print 'python /home/pi/Scripts/waldo/waldo/helpers/remote.py %s' % modifier
    # os.system('python /home/pi/Scripts/waldo/waldo/helpers/remote.py %s' % modifier)
    # os.system('/home/pi/Scripts/waldo/waldo/helpers/shutdown_button.py')
    # os.system('python /home/pi/Scripts/waldo/waldo/helpers/numpad_listener.py')
