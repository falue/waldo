#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import signal
import sys
import time
import RPi.GPIO as GPIO
import subprocess as sp

from waldo.utils import read_config, write_config, get_mcp_connection, set_gpio_pins
from waldo.fn import read_mcp, servo_start_pos


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

PLAY = [False, False]  # thread, projectname
activity = 0

# read all buttons from config file
BUTTONS = config['buttons'].copy()

# If primay/first executed file from bash is waldo.py
# keyboard interrupt fallback
try:
    if sys.argv[1] == "-ap" or sys.argv[1] == "--autoplay":
        print 'autoplay active!'
    pass

except IndexError:
    pass


def calibrate():
    """
    (Re-) Calibrate buttons. Necessary because different lengths of ethernet cables have different resistances.
    :return:
    """
    print "Calibrate wire controls: Press first 5 buttons for approx. 1 sec each. Wait for 'beep' to release."
    # Define "zero"-button (eg., nothing is pressed)
    null_average = average(20)
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
                curr_average = average(10)
		print curr_average

                # Check if button is pressed
                if curr_average > null_average + LIVE_ZONE:

                    # Measure again to hit correct start of measuring
                    curr_average = average(10)

                    # Check if new button not the same as last time
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
                        time.sleep(0.75)

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


def average(count):
    """
    Leveling out 10 MCP3008 readings of analog values.
    :return:
    """
    value = 0
    for i in range(count):
        value += read_mcp(0, CLK, MOSI, MISO, CS)
        time.sleep(0.05)
    return value / count


def play(args):
    """
    Run waldo/main.py with args in the background, hidden.
    """
    global PLAY
    # set to thread
    PLAY[0] = sp.Popen(['python', 'waldo/main.py'] + args,
                    stdout=sp.PIPE,  # hide prints from function
                    preexec_fn=os.setsid
                    )
    # set to project name
    PLAY[1] = args[1]


def cancel():
    """
    Cancel ongoing 'play' instance.
    :return:
    """
    global PLAY

    # is actual playing?
    config = read_config(os.path.dirname(os.path.realpath(__file__)))
    is_replaying = config["REC_REPL"]

    if is_replaying or PLAY[0]:  # if PLAY[0]
        print "\nCancel PLAY '%s'" % PLAY[1]
        os.killpg(os.getpgid(PLAY[0].pid), signal.SIGTERM)
        servo_start_pos(PLAY[1])
        PLAY[0] = False
        PLAY[1] = False
        time.sleep(0.25)
        print "Waiting for input via control panel 'rigby'..."
    else:
        # print "Nothing to cancel"
        time.sleep(0.25)
        pass


# Main loop
if __name__ == '__main__':
    try:
        # Set GPIO pins as used by mcp read/write pins
        set_gpio_pins(config)

        print "==============================="
        print " _ _ _ _____ __    ____  _____ "
        print "| | | |  [] |  |  |    \|     | analog"
        print "| | | |     |  |__|  [] |  [] | digital"
        print "|_____|__||_|_____|____/|_____| pupeteering"
        print "_______________________________"

        # If arg is submitted
        if len(sys.argv) > 1:
            arg = sys.argv[1]
        else:
            arg = False

        # Print helpfile
        if arg == "-h" or arg == "--help":
            with open(os.path.join(os.path.dirname(__file__), 'help'), 'r') as f:
                print f.read()
            GPIO.cleanup()
            raise SystemExit

        # Start calibration
        elif arg == "-cal" or arg == "--calibrate" or 'button_value' not in config:
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

        print "Waiting for input via control panel 'rigby'..."

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
                        time.sleep(0.75)

            # Read if project is ongoing
            config = None
            while config == None:
                config = read_config(os.path.dirname(os.path.realpath(__file__)))
                time.sleep(0.05)
            REC_REPL = config["REC_REPL"]

            # show activity
            if REC_REPL:
                if activity <= 40:
                    sys.stdout.write('.')
                    activity += 1
                else:
                    sys.stdout.write('\x1b[2K\r')  # delete line (\x1b[2K)and go to beginning of line (\r)
                    activity = 0
                sys.stdout.flush()

            time.sleep(0.05)

    except KeyboardInterrupt:
        GPIO.cleanup()
        print "\nExit by user."


