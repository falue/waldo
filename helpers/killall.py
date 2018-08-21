#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess

import RPi.GPIO as GPIO

from waldo.fn import playback_audio


def kill_our_scripts():
    subprocess.call("sudo kill -9 `ps -aef | grep 'keyboard_listener' | grep -v grep | awk '{print $2}'`", shell=True)
    subprocess.call("sudo kill -9 `ps -aef | grep 'shutdown_button' | grep -v grep | awk '{print $2}'`", shell=True)
    subprocess.call("sudo kill -9 `ps -aef | grep 'monitor_temperature' | grep -v grep | awk '{print $2}'`", shell=True)
    subprocess.call("sudo kill -9 `ps -aef | grep 'numpad_listener' | grep -v grep | awk '{print $2}'`", shell=True)
    subprocess.call("sudo kill -9 `ps -aef | grep 'main' | grep -v grep | awk '{print $2}'`", shell=True)
    subprocess.call("sudo kill -9 `ps -aef | grep 'audiotest' | grep -v grep | awk '{print $2}'`", shell=True)


def reset_gpio():
    # Reset button LED from shutdown_button.py
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    led_pin_green = 20
    led_pin_red = 21
    GPIO.setup(led_pin_green, GPIO.OUT)
    GPIO.output(led_pin_green, False)
    GPIO.setup(led_pin_red, GPIO.OUT)
    GPIO.output(led_pin_red, False)


if __name__ == '__main__':
    kill_our_scripts()
    reset_gpio()
    playback_audio('/home/pi/Scripts/waldo/waldo/sounds/terminated.wav')
