#!/usr/bin/python
# -*- coding: utf-8 -*-

import time

i = 0
play = True

while play:
    print i
    time.sleep(.25)
    i += 1
    if i == 20:
        play = False