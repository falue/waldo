#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import signal
import sys
import time
import RPi.GPIO as GPIO
import subprocess as sp

from waldo.utils import (read_config, write_config, get_mcp_connection)
from waldo.fn import (read_mcp)

# FIXME: remove in production
GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)  # verwende GPIO pinbezeichnung: BOARD, ...andere BCM

# set project folder path
config = read_config(os.path.dirname(os.path.realpath(__file__)))
PROJECT_PATH = os.path.expanduser(config["PROJECT_PATH"])

# set GPIO
GPIO.setmode(GPIO.BCM)

for mcps in config['mcp']:
    # set up the SPI interface pins
    GPIO.setup(config['mcp'][mcps]['MOSI'], GPIO.OUT)
    GPIO.setup(config['mcp'][mcps]['MISO'], GPIO.IN)
    GPIO.setup(config['mcp'][mcps]['CLK'], GPIO.OUT)
    GPIO.setup(config['mcp'][mcps]['CS'], GPIO.OUT)

if not os.path.isdir(PROJECT_PATH):
    os.makedirs(PROJECT_PATH)
"""
buttons = {
    1: '-p dummy',
    2: '-p dummy',
    3: '-p dummy',
    4: '-p dummy',
    5: '-p dummy',
    6: '-p dummy',
    7: '-p dummy',
    8: '-p dummy',
    9: '-p dummy',
    10: '-p dummy',
    11: '-p dummy',
    12: '-p dummy',
    13: '-p dummy',
    14: '-p dummy',
    15: '-p dummy',
    16: '-p dummy',
    17: '-p dummy',
    18: '-p dummy',
    19: '-p dummy',
    20: '-p dummy',
    21: '-p dummy',
    22: '-p dummy',
    23: '-p dummy',
    24: '-p dummy',
    25: '-p dummy',
    26: '-p dummy',
    27: '-p dummy',
    28: '-p dummy',
    29: '-p song',
    30: 'cancel'
          }
"""

mcp_pin = 17  # pin nr. 1 on mcp3008 IC nr. 3
LIVE_ZONE = 22  # +/- analog read = button x

mcp_connection = get_mcp_connection(mcp_pin)
CLK = mcp_connection['CLK']
MOSI = mcp_connection['MOSI']
MISO = mcp_connection['MISO']
CS = mcp_connection['CS']

PLAY = False

buttons = config['buttons'].copy()


def calibrate():
    i = 1
    cal = False
    null_average = average()
    last_average = null_average
    button = {0: null_average,
              1: False,
              2: False,
              3: False,
              4: False,
              5: False
              }
    while not cal:
        # while i < len(button)-1:
        while not button[i]:
            curr_average = average()
            if last_average-LIVE_ZONE <= curr_average <= last_average+LIVE_ZONE and \
                    null_average-LIVE_ZONE <= curr_average <= null_average+LIVE_ZONE:
                # print "pass %s: %s - %s (%s)" % (i, curr_average, last_average, null_average)
                pass
            else:
                button[i] = average()
                print "Button %s: set @ %s [%s ... %s]" % (i, button[i], button[i]-LIVE_ZONE, button[i]+LIVE_ZONE)

            if not button[i]:
                last_average = curr_average
            else:
                last_average = null_average
                if i < 5:
                    i += 1
                    time.sleep(1)
                else:
                    time.sleep(0.2)
                    cal = True
                play_sound("beep")
    play_sound("buttons_cal")
    return button


def play_sound(audiofile):
    bashcommando = 'play waldo/sounds/%s.mp3 -q' % audiofile
    os.system(bashcommando)  # invoke 'sox' in quiet mode


def average():
    i = 0
    value = 0
    while i < 10:
        value += read_mcp(0, CLK, MOSI, MISO, CS)
        time.sleep(0.05)
        i += 1
    return value/10


def play(args):
    """
     But be wary: subprocess.Popen() only runs a process in the background if nothing in the python script depends on
     the output of the command being run !!!
    """
    global PLAY
    PLAY = sp.Popen(['python', 'waldo/main.py'] + args,
                    stdout=sp.PIPE,  # hide prints from function
                    preexec_fn=os.setsid
                    )


def cancel():
    global PLAY
    if PLAY:
        print "cancel PLAY"
        os.killpg(os.getpgid(PLAY.pid), signal.SIGTERM)
        PLAY = False
    else:
        print "nothing to cancel"
        pass


print "==============================="
print " _ _ _ _____ __    ____  _____ "
print "| | | |  [] |  |  |    \|     | analog"
print "| | | |     |  |__|  [] |  [] | digital"
print "|_____|__||_|_____|____/|_____| pupeteering"
print "_______________________________"


if 'button_value' not in config or len(sys.argv) > 1:
    print "Calibrate wire controls: Press first 5 buttons for 1 sec each."
    ranges = calibrate()

    config.update({'button_value': {
        0: ranges[0],
        1: ranges[5],
        2: ranges[4],
        3: ranges[3],
        4: ranges[2],
        5: ranges[1]
    }})
    write_config(os.path.dirname(os.path.realpath(__file__)), config)
    print "Buttons calibrated."

button_value = config['button_value'].copy()

print "Waiting for input via MCP3008..."

# change to home directory
bashcommando = 'cd %s' % PROJECT_PATH
os.system(bashcommando)

# set max volume
bashcommando = 'sudo amixer cset numid=1 -- 100% > /dev/null'
os.system(bashcommando)


while True:
    for mcp_in in range(len(buttons)/5):
        value = read_mcp(mcp_in, CLK, MOSI, MISO, CS)
        button = mcp_in*5
        print "mcp_in %s: %s %s\t|\t" % (mcp_in, button / 5, value)
        if value <= button_value[0]+LIVE_ZONE:
            pass
        elif button_value[1]-LIVE_ZONE <= value <= button_value[1]+LIVE_ZONE:
            if button+5 == 30:
                print "Button '30'!"
                cancel()
            else:
                cancel()
                play(buttons[button+5].split(" "))
                print "Button %s: waldo/main.py %s %s" % (button+5, buttons[button+5], value)
            time.sleep(1)
        elif button_value[2]-LIVE_ZONE <= value <= button_value[2]+LIVE_ZONE:
            cancel()
            play(buttons[button+4].split(" "))
            print "Button %s: waldo/main.py %s %s" % (button+4, buttons[button+4], value)
            time.sleep(1)
        elif button_value[3]-LIVE_ZONE <= value <= button_value[3]+LIVE_ZONE:
            cancel()
            play(buttons[button+3].split(" "))
            print "Button %s: waldo/main.py %s %s" % (button+3, buttons[button+3], value)
            time.sleep(1)
        elif button_value[4]-LIVE_ZONE <= value <= button_value[4]+LIVE_ZONE:
            cancel()
            play(buttons[button+2].split(" "))
            print "Button %s: waldo/main.py %s %s" % (button+2, buttons[button+2], value)
            time.sleep(1)
        elif button_value[5]-LIVE_ZONE <= value <= button_value[5]+LIVE_ZONE:
            cancel()
            play(buttons[button+1].split(" "))
            print "Button %s: waldo/main.py %s %s" % (button+1, buttons[button+1], value)
            time.sleep(1)

    time.sleep(0.05)
    # print "\r"

"""

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
                play = sp.Popen(['python', 'waldo/main.py'] + buttons[key].split(" "), stdout=sp.PIPE,
                               preexec_fn=os.setsid)
                time.sleep(2)
    """

# setze gpio zurück - nach programm ende sonst online!
GPIO.cleanup()
