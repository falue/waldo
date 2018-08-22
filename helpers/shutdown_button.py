#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import time

import RPi.GPIO as GPIO

from waldo.utils import threaded


@threaded
def shutdown_on_button_press():
    # Time between measurements
    waiting_time = 0.1

    # Number of measurements
    number_of_measurements = 5

    print('Shutdown button active.')

    # Button pin setup
    button_pin = 19
    GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    signal_values = [True for _ in range(number_of_measurements)]

    shutdown_started = False  # has the shutdown already been initiated? To prevent multiple shutdown commands

    while True:
        input_state = GPIO.input(button_pin)
        signal_values.pop(0)
        signal_values.append(input_state)
        if signal_values.count(False) >= 3 and not shutdown_started:
            rg_led('red')
            shutdown_started = True
            print('Shutdown button pressed. Shutdown: Now.')
            subprocess.call(['sudo', 'shutdown', 'now', '-h'])
        time.sleep(waiting_time)


def rg_led(mode):
    if mode == 'red':
        GPIO.output(led_pin_green, False)
        GPIO.output(led_pin_red, True)
    elif mode == 'green':
        GPIO.output(led_pin_green, True)
        GPIO.output(led_pin_red, False)

# SETUP
led_pin_green = 20
led_pin_red = 21

# Bi-Color LED pins setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(led_pin_green, GPIO.OUT)
GPIO.setup(led_pin_red, GPIO.OUT)
rg_led('red')

if __name__ == '__main__':
    rg_led('green')
    shutdown_on_button_press()
    while True:
        time.sleep(60)
