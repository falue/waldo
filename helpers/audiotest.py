#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
chime
left
right
'''
import os
import time

bashcommando = 'play /home/pi/Scripts/waldo/waldo/sounds/chime.mp3 -q'
os.system(bashcommando)  # invoke 'sox' in quiet mode

while True:
    bashcommando = 'play /home/pi/Scripts/waldo/waldo/sounds/audiotest_l.wav -q'
    os.system(bashcommando)  # invoke 'sox' in quiet mode

    time.sleep(1)

    bashcommando = 'play /home/pi/Scripts/waldo/waldo/sounds/audiotest_r.wav -q'
    os.system(bashcommando)  # invoke 'sox' in quiet mode

    time.sleep(1)

