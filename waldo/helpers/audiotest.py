#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time

from waldo.audio import AudioPlayer

AudioPlayer('/home/pi/Scripts/waldo/waldo/sounds/chime.mp3').play()

while True:
    AudioPlayer('/home/pi/Scripts/waldo/waldo/sounds/audiotest_l.wav').play()
    time.sleep(1)

    AudioPlayer('/home/pi/Scripts/waldo/waldo/sounds/audiotest_r.wav').play()
    time.sleep(1)
