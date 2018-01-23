#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import signal
import time
import RPi.GPIO as GPIO
import subprocess as sp

# FIXME: remove in production
GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)  # verwende GPIO pinbezeichnung: BOARD, ...andere BCM

buttons = {
    13: '-p timeit',
    16: '-p timeit 15',
    19: '-sp timeit 8er count.wav',
    20: '-p timeit',
    21: '-p vali'
          }

for key in sorted(buttons):
    print "GPIO.setup(%s, GPIO.IN, pull_up_down=GPIO.PUD_UP)" % key
    GPIO.setup(key, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # set als eingang

main_path = os.path.dirname(os.path.realpath(__file__))
play = False

# FIXME: on startup:
# bash_commando = 'cd %s' % main_path
# set volume to max

while True:
    for key in buttons:
        if not GPIO.input(key):
            when_pressed = time.time()

            while not GPIO.input(key):
                if time.time() - when_pressed > 1:
                    print "Stop: All projects"
                    if play:
                        os.killpg(os.getpgid(play.pid), signal.SIGTERM)
                        play = False
                    time.sleep(2)
                time.sleep(0.001)

            when_released = time.time() - when_pressed

            if GPIO.input(key) and when_released <= 1:
                if play:
                    print "Stop before play; ",
                    os.killpg(os.getpgid(play.pid), signal.SIGTERM)
                print "Start: 'python waldo/main.py %s'" % buttons[key]
                play = sp.Popen(['python', 'waldo/main.py'] + buttons[key].split(" "),
                                stdout=sp.PIPE,
                                preexec_fn=os.setsid)
                time.sleep(2)

    time.sleep(0.01)

# setze gpio zurück - nach programm ende sonst online!
GPIO.cleanup()
