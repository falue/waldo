#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time

from waldo.fn import playback_audio

playback_audio('/home/pi/Scripts/waldo/waldo/sounds/chime.mp3')
while True:
    playback_audio('/home/pi/Scripts/waldo/waldo/sounds/audiotest_l.wav')
    time.sleep(1)

    playback_audio('/home/pi/Scripts/waldo/waldo/sounds/audiotest_r.wav')
    time.sleep(1)
