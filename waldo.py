#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import signal
import sys
import time
import RPi.GPIO as GPIO
import subprocess as sp

from waldo.utils import read_config, write_config, get_mcp_connection, set_gpio_pins
from waldo.fn import read_mcp

# FIXME: remove in production
# GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)  # verwende GPIO pinbezeichnung: BOARD, ...andere BCM

# Set project folder path
config = read_config(os.path.dirname(os.path.realpath(__file__)))
PROJECT_PATH = os.path.expanduser(config["PROJECT_PATH"])

# Make project folder if inexistent
if not os.path.isdir(PROJECT_PATH):
    os.makedirs(PROJECT_PATH)

# Globals
LIVE_ZONE = 22  # +/- analog read = button x

mcp_connection = get_mcp_connection(0)
CLK = mcp_connection['CLK']
MOSI = mcp_connection['MOSI']
MISO = mcp_connection['MISO']
CS = mcp_connection['CS']

PLAY = False

# read all buttons from config file
BUTTONS = config['buttons'].copy()


def calibrate():
    """
    (Re-) Calibrate buttons. Necessary because different lengths of ethernet cables have different resistances.
    :return:
    """
    # Define "zero"-button (eg., nothing is pressed)
    null_average = average()
    last_average = null_average
    print "Button 0: set @ %s [%s ... %s]" % (null_average,
                                              null_average - LIVE_ZONE,
                                              null_average + LIVE_ZONE)

    # Define 6 example buttons (incl. "zero"-button)
    button = {0: null_average,
              1: False,
              2: False,
              3: False,
              4: False,
              5: False
              }

    # Cycle all 5 example buttons
    for position in sorted(button):
        if position != 0:
            while not button[position]:
                curr_average = average()

                # Check if button is pressed
                if curr_average > null_average + LIVE_ZONE:

                    # Measure again to hit correct start of measuring
                    curr_average = average()

                    # Check of new button not the same as last time
                    if curr_average not in range(last_average - LIVE_ZONE,
                                                 last_average + LIVE_ZONE):
                        # Define new button setup
                        button[position] = curr_average
                        last_average = curr_average
                        system_sound("beep")
                        print "Button %s: set @ %s [%s ... %s]" % (position, button[position],
                                                                   button[position] - LIVE_ZONE,
                                                                   button[position] + LIVE_ZONE)

                        # Important - user lets go off button -> new reading!
                        time.sleep(1)

    # Finished calibrating
    system_sound("buttons_cal")
    time.sleep(1)

    return button


def system_sound(audiofile):
    """
    Playback my own system sounds.
    :param audiofile:
    :return:
    """
    bashcommando = 'play waldo/sounds/%s.mp3 -q' % audiofile
    os.system(bashcommando)  # invoke 'sox' in quiet mode


def average():
    """
    Leveling out 10 MCP3008 readings of analog values.
    :return:
    """
    value = 0
    for i in range(10):
        value += read_mcp(0, CLK, MOSI, MISO, CS)
        time.sleep(0.05)
    return value / 10


def play(args):
    """
    Run waldo/main.py with args in the background, hidden.
    """
    global PLAY
    PLAY = sp.Popen(['python', 'waldo/main.py'] + args,
                    stdout=sp.PIPE,  # hide prints from function
                    preexec_fn=os.setsid
                    )


def cancel():
    """
    Cancel ongoing 'play' instance.
    :return:
    """
    global PLAY

    if PLAY:
        print "Cancel PLAY"
        os.killpg(os.getpgid(PLAY.pid), signal.SIGTERM)
        PLAY = False
        time.sleep(1)
    else:
        # print "nothing to cancel"
        pass


# Main loop
if __name__ == '__main__':

    # Set GPIO pins as used by mcp read/write pins
    set_gpio_pins(config)

    print "==============================="
    print " _ _ _ _____ __    ____  _____ "
    print "| | | |  [] |  |  |    \|     | analog"
    print "| | | |     |  |__|  [] |  [] | digital"
    print "|_____|__||_|_____|____/|_____| pupeteering"
    print "_______________________________"

    # Buttons not yet calibrated
    if 'button_value' not in config or len(sys.argv) > 1:
        print "Calibrate wire controls: Press first 5 buttons for approx. 1 sec each."
        ranges = calibrate()

        # Update congig list
        config.update({'button_value': {
            0: ranges[0],
            1: ranges[1],
            2: ranges[2],
            3: ranges[3],
            4: ranges[4],
            5: ranges[5]
        }})

        # Write data to main config
        write_config(os.path.dirname(os.path.realpath(__file__)), config)
        print "Buttons calibrated."

    button_value = config['button_value'].copy()

    print "Waiting for input via control panel'rygby'..."

    # Change to home directory
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    # Set max volume
    bashcommando = 'sudo amixer cset numid=1 -- 100% > /dev/null'
    os.system(bashcommando)

    # Wait for button presses...
    while True:
        for mcp_in in range(len(BUTTONS) / 5):
            # Read analog value for first 5 buttons
            value = read_mcp(mcp_in, CLK, MOSI, MISO, CS)
            button = mcp_in * 5
            # print "mcp_in %s: %s %s\t|\t" % (mcp_in, button / 5, value)

            # If nothing is pressed ("zero"-button)
            if value <= button_value[0] + LIVE_ZONE:
                continue

            # Cycle all 5 buttons
            for i in range(1, 6):
                if button_value[i] - LIVE_ZONE <= value <= button_value[i] + LIVE_ZONE:
                    # Cancel any ongoing 'play' instances
                    cancel()
                    button_number = button + i

                    # Check if special 'Cancel' button
                    if button_number == 30:
                        # print "Button '30'!"
                        continue

                    # Set commands as defined in main config file
                    command = BUTTONS[button_number].split(" ")

                    play(command)

                    print "Button %s: waldo/main.py %s %s" % (button_number, BUTTONS[button_number], value)
                    time.sleep(1)

        time.sleep(0.05)

    # Set back GPIO pins
    GPIO.cleanup()
