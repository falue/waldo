#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import subprocess
import time

import RPi.GPIO as GPIO

from waldo.utils import threaded


@threaded
def shutdown_on_button_press():
    #######################
    #    Configuration    #
    #######################

    # Time between measurements
    waiting_time = 0.1

    # Number of measurements
    number_of_measurements = 5

    GPIO.setwarnings(False)

    #######################
    #     Code Starts     #
    #######################

    print('Shutdown button active.')

    # Button pin setup
    GPIO.setmode(GPIO.BCM)
    button_pin = 19
    GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Bi-Color LED pins setup
    led_pin_green = 20
    led_pin_red = 21
    GPIO.setup(led_pin_green, GPIO.OUT)
    GPIO.output(led_pin_green, True)
    GPIO.setup(led_pin_red, GPIO.OUT)
    GPIO.output(led_pin_red, False)

    signal_values = [True for _ in range(number_of_measurements)]

    shutdown_started = False  # has the shutdown already been initiated? To prevent multiple shutdown commands

    while True:
        input_state = GPIO.input(button_pin)
        signal_values.pop(0)
        signal_values.append(input_state)
        if signal_values.count(False) >= 3 and not shutdown_started:
            GPIO.output(led_pin_green, False)
            GPIO.output(led_pin_red, True)
            shutdown_started = True
            print('Shutdown button pressed. Shutdown: Now.')
            subprocess.call("sudo shutdown now -h")
        time.sleep(waiting_time)


if __name__ == '__main__':
    shutdown_on_button_press()
    while True:
        time.sleep(60)
