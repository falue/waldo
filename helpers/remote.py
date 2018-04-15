#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import signal
import sys
import time
import RPi.GPIO as GPIO
import subprocess as sp
import keyboard

from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from waldo.utils import read_config, write_config, get_mcp_connection, set_gpio_pins
from waldo.fn import read_mcp, servo_start_pos, change_glob_rec_repl

# FIXME: remove in production
# GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)  # verwende GPIO pinbezeichnung: BOARD, ...andere BCM

# Set project folder path
config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
config = read_config(config_path)
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
button_number = False

# reset config file value recrepl (in case waldo is shut off unexpected):
# change_glob_rec_repl(False)


def set_button_connection(new_config):
    answer = raw_input("Set up play button connection with USB (numpad) or analog input via MCP3008? [USB/MCP]\n").lower()
    if answer == "usb":
        print "Connect your USB keyboard. Number keys equal button key defined in main config."
        new_config.update({'numpad': True})
        return new_config

    elif answer == "mcp":
        ranges = calibrate()

        # Update config list
        # TODO: Change button_value to play_button_value so don't get confused
        new_config.update({'numpad': False})
        new_config.update({'button_value': {
            0: ranges[0],
            1: ranges[1],
            2: ranges[2],
            3: ranges[3],
            4: ranges[4],
            5: ranges[5]
        }})

        return new_config

    else:
        print "Either enter USB or MCP, pretty please."
        set_button_connection(new_config)


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
    bashcommando = 'play /home/pi/Scripts/waldo/waldo/sounds/%s.mp3 -q' % audiofile
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
    PLAY[0] = sp.Popen(['python', '/home/pi/Scripts/waldo/waldo/main.py'] + args,
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
    config = read_config(config_path)
    is_replaying = config["REC_REPL"]

    if is_replaying or PLAY[0]:  # if PLAY[0]
        print "\nCancel PLAY '%s'" % PLAY[1]
        os.killpg(os.getpgid(PLAY[0].pid), signal.SIGTERM)
        servo_start_pos(PLAY[1])
        PLAY[0] = False
        PLAY[1] = False
        change_glob_rec_repl(False)
        time.sleep(0.25)
        if not config['numpad']:
            print "Waiting for input via control panel 'rigby'..."
    else:
        # print "Nothing to cancel"
        time.sleep(0.25)
        pass


# Numpad keys
keys = {79: 1, 80: 2, 81: 3, 75: 4, 76: 5, 77: 6, 71: 7, 72: 8, 73: 9, 82: 0,  # numpad
        2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9, 11: 0,  # regular number keys
        16: 'q', 28: 'enter', 98: '/', 55: '*', 14: 'backspace', 74: '-', 78: '+', 96: 'enter', 83: '.'
        }


def get_pressed_keys(e):
    # KeyboardEvent.scan_code
    # KeyboardEvent.name
    # event_type
    # print keyboard._pressed_events

    # keycode = False
    # for code in e:
    #     keycode = code, keycode
    keycode = list([x for x in e])
    if len(keycode):
        keycode = int('\n'.join(str(p) for p in keycode))
        # exclude num lock
        try:
            return keys[keycode] if keycode != 69 else False
            time.sleep(0.25)
        except KeyError:
            print 'This button is not programmed to do a damn thing.'


def foo(e):
    # if e.event_type == 'down' and e.name != 'num lock':
    #     # print e.scan_code, e.name, e.event_type
    #     print e.name
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

        # If primay/first executed file from bash is scripts/remote.py
        # keyboard interrupt fallback
        elif arg == "-ap" or arg == "--autoplay":
            print 'Autoplay activated.'
            try:
                print 'Play button %s.' % sys.argv[2]
                button_number = int(sys.argv[2])
            except IndexError:
                print 'No autoplay startup track defined in config (use integer of button instead of "True").'

        # Start calibration
        elif arg == "-cal" or arg == "--calibrate" or 'button_value' not in config:
            new_config = set_button_connection(config)

            # Write data to main config
            write_config(os.path.dirname(os.path.realpath(__file__)), new_config)
            print "Buttons calibrated."

        button_value = config['button_value'].copy()

        if not config['numpad']:
            print "Waiting for input via control panel 'rigby'..."
        else:
            print 'Awaiting keyboard input (Press 1-30 & enter) with directly connected USB keyboard'
            # hook global keyboard presses to function
            keyboard.hook(foo)

        # Change to home directory
        os.chdir(os.path.dirname(os.path.realpath(__file__)))

        # Set max volume
        bashcommando = 'sudo amixer cset numid=1 -- 100% > /dev/null'
        os.system(bashcommando)

        # Wait for button presses...
        while True:
            # If USB is used, get button_number via Keyboard input:
            if not button_number:
                if config['numpad']:
                    # TODO: also raw input, but read keypress from library
                    # answer = raw_input("Awaiting keyboard input (Press 1-30 & enter)...\n").lower()
                    # try:
                    #     button_number = int(answer)
                    # except ValueError:
                    #     # Handle the exception
                    #     print 'Not an integer value.'

                    keystroke = get_pressed_keys(keyboard._pressed_events)
                    if keystroke is not None and keystroke is not False:
                        button_number = keystroke

                else:
                    # If MCP is used, get button_number via mcp:
                    for mcp_in in range(30):
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
                                button_number = button + i
                                time.sleep(0.75)

            # Get button_number from MCP or USB numpad
            if button_number:
                if button_number in BUTTONS:
                    # Cancel any ongoing 'play' instances
                    cancel()
                    # Check if special 'Cancel' button
                    if BUTTONS[button_number] == 'cancel':
                        button_number = False
                        continue

                    # Set commands as defined in main config file
                    play(BUTTONS[button_number].split(" "))
                    print "Button %s: waldo/main.py %s" % (button_number, BUTTONS[button_number])
                else:
                    print "The button '%s' is not defined in main config file." % (button_number)
                button_number = False

            # Read if project is ongoing
            config = None
            while config == None:
                if os.path.isfile(os.path.join(config_path, 'config')):
                    config = read_config(config_path)
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


