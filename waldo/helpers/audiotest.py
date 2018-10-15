#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import time

left = '/home/pi/Scripts/waldo/waldo/sounds/audiotest_l.wav'
right = '/home/pi/Scripts/waldo/waldo/sounds/audiotest_r.wav'

while True:
    cmd = ['/usr/bin/play', '-v', '0.99', '-q', left]
    print('Left')
    subprocess.Popen(cmd)
    time.sleep(1)

    cmd = ['/usr/bin/play', '-v', '0.99', '-q', right]
    print('Right')
    subprocess.Popen(cmd)
    time.sleep(1)
