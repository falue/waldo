#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time
import RPi.GPIO as GPIO

# FIXME: remove in production
GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)  # verwende GPIO pinbezeichnung: BOARD, ...andere BCM

buttons = {
    13: '-p timeit',
    16: '-p timeit 15',
    19: '-sp timeit 8er count.wav',
    20: 'asd',
    21: '-p timeit'
          }

for key in sorted(buttons):
    print "GPIO.setup(%s, GPIO.IN, pull_up_down=GPIO.PUD_UP)" % key
    GPIO.setup(key, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # set als eingang

main_path = os.path.dirname(os.path.realpath(__file__))
# button_state = GPIO.input(BUTTONpin) # getting input value from button

# state toggle button is pressed
while True:
    for key in buttons:
        if not GPIO.input(key):
            when_pressed = time.time()

            while not GPIO.input(key):
                if time.time() - when_pressed > 1.2:
                    print "cancel all functions"
                    time.sleep(2)
                time.sleep(0.005)

            when_released = time.time() - when_pressed

            if GPIO.input(key) and when_released <= 1.2:
                print "Button: %s\tFunction '%s'" % (key, buttons[key])
                bash_commando = 'cd %s && python waldo/main.py %s' % (main_path, buttons[key])
                print bash_commando
                # os.system(bash_commando)
                time.sleep(2)

                # how to...?
    time.sleep(0.005)

# setze gpio zurück - nach programm ende sonst online!
GPIO.cleanup()
