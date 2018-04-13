#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import RPi.GPIO as GPIO

os.system("sudo kill -9 `ps -aef | grep 'remote' | grep -v grep | awk '{print $2}'`")
os.system("sudo kill -9 `ps -aef | grep 'shutdown_button' | grep -v grep | awk '{print $2}'`")
os.system("sudo kill -9 `ps -aef | grep 'numpad_listener' | grep -v grep | awk '{print $2}'`")
os.system("sudo kill -9 `ps -aef | grep 'main' | grep -v grep | awk '{print $2}'`")
os.system("sudo kill -9 `ps -aef | grep 'audiotest' | grep -v grep | awk '{print $2}'`")

# Reset button LED from shutdown_button.py
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
led_pin_green = 20
led_pin_red = 21
GPIO.setup(led_pin_green, GPIO.OUT)
GPIO.output(led_pin_green, False)
GPIO.setup(led_pin_red, GPIO.OUT)
GPIO.output(led_pin_red, False)
