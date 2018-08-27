# coding=utf-8
from __future__ import print_function

import logging
import os
import select
import sys
import time
from shutil import copyfile
from time import sleep

import RPi.GPIO as GPIO

from waldo.player import Player
from waldo.servo import Servo
from waldo.utils import read_main_config, read_project_config, map_value, write_project_config, bar, get_filesize

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

logger = logging.getLogger(__name__)


class Potentiometer(object):
    def __init__(self, analog_in=8):
        self.analog_in = analog_in
        self.mcp_chip = self.analog_in / 8
        self.mcp_in = self.analog_in % 8

        # MCP Analog in
        self.mcp = {
            0: {'clk': 4, 'cs': 27, 'miso': 17, 'mosi': 18},
            1: {'clk': 22, 'cs': 25, 'miso': 23, 'mosi': 24},
            2: {'clk': 5, 'cs': 13, 'miso': 6, 'mosi': 12},
        }

        for chip in self.mcp:
            # set up the SPI interface pins
            GPIO.setup(self.mcp[chip]['mosi'], GPIO.OUT)
            GPIO.setup(self.mcp[chip]['miso'], GPIO.IN)
            GPIO.setup(self.mcp[chip]['clk'], GPIO.OUT)
            GPIO.setup(self.mcp[chip]['cs'], GPIO.OUT)

    def read(self):
        passes = 80
        measurement = 0
        for i in range(passes):
            measurement += self._mcp_reading(self.mcp_in,
                                             self.mcp[self.mcp_chip]['clk'],
                                             self.mcp[self.mcp_chip]['mosi'],
                                             self.mcp[self.mcp_chip]['miso'],
                                             self.mcp[self.mcp_chip]['cs'],
                                             )
            sleep(0.0001)
        return measurement / passes

    @staticmethod
    def _mcp_reading(mcp_chip, clk, mosi, miso, cs):
        """"""
        if (mcp_chip > 7) or (mcp_chip < 0):
            return False
        GPIO.output(cs, True)
        GPIO.output(clk, False)  # start clock low
        GPIO.output(cs, False)  # bring CS low

        mcp_chip |= 0x18  # start bit + single-ended bit
        mcp_chip <<= 3  # we only need to send 5 bits here
        for i in range(5):
            if mcp_chip & 0x80:
                GPIO.output(mosi, True)
            else:
                GPIO.output(mosi, False)
            mcp_chip <<= 1
            GPIO.output(clk, True)
            GPIO.output(clk, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
            GPIO.output(clk, True)
            GPIO.output(clk, False)
            adcout <<= 1
            if GPIO.input(miso):
                adcout |= 0x1

        GPIO.output(cs, True)
        adcout >>= 1  # first bit is 'null' so drop it
        return adcout


def record_setup(project_name, channel_name):
    project_path = read_main_config()['project_path']

    # Project folder exist?
    if not os.path.isdir(os.path.join(project_path, project_name)):
        new_project(project_name)

    # Channel file exist?
    if os.path.isfile(os.path.join(project_path, project_name, channel_name)):
        # overwite?
        answer = raw_input("'%s' already exists. Replace? [Y/N]\n" % channel_name).lower()

        if answer == "y":
            # backup file in 'trash'
            try:
                os.makedirs(os.path.join(project_path, project_name, 'trash'))
            except OSError:
                pass

            copyfile(os.path.join(project_path, project_name, channel_name),
                     os.path.join(project_path, project_name, 'trash',
                                  channel_name + "_" + time.strftime('%Y-%m-%d_%H_%M_%S'))
                     )
        elif answer == "n":
            print("Abort.")
            return
        else:
            print("[Y/N] murmel, murmel")
            record_setup(project_name, channel_name)
            return  # sure?

    else:
        set_servo(project_name, channel_name)


def set_servo(project_name, channel_name):
    """
    Set config file for project - MCPin, servo_pin, map_min, map_max, start_pos.
    """
    # Read channel config data
    config = read_project_config(project_name)

    # Create key 'channels' if inexistent
    if 'channels' not in config:
        config.update({'channels': {}})

    # Set default answers
    if channel_name not in config['channels']:
        default_mcp_in = 14
        default_servo_pin = 0
        default_map_min = 100
        default_map_max = 600
        default_start_pos = False
    else:
        default_mcp_in = config['channels'][channel_name]['mcp_in']
        default_servo_pin = config['channels'][channel_name]['servo_pin']
        default_map_min = config['channels'][channel_name]['map_min']
        default_map_max = config['channels'][channel_name]['map_max']
        default_start_pos = config['channels'][channel_name]['start_pos']

    # Questions, questions, questions!
    mcp_in = int(raw_input('%s:\nSet MCP3008 in pin [0-23] '
                           '(Default: %s)\n' % (channel_name, default_mcp_in)) or default_mcp_in)

    servo_pin = int(raw_input('Set servo pin out pin [0-31]'
                              '(Default: %s)\n' % default_servo_pin) or default_servo_pin)

    map_min = raw_input('Set minimum position [100-600] '
                        '(Default: %s; \'m\' for manual detection)\n' % default_map_min) or default_map_min
    if map_min == 'm':
        map_min = get_dof(mcp_in, servo_pin)
        # FIXME: Catch pressing enter and prevent next raw_input to get executed
        raw_input('')

    map_max = raw_input('Set maximum position [100-600] '
                        '(Default: %s; \'m\' for manual detection)\n' % default_map_max) or default_map_max
    if map_max == 'm':
        map_max = get_dof(mcp_in, servo_pin)
        # FIXME: Catch pressing enter and prevent next raw_input to get executed
        raw_input('')
    if not default_start_pos:
        default_start_pos = map_min

    start_pos = int(raw_input('Set start position [100-600]'
                              '(Default: %s; map_min: %s)\n' % (default_start_pos, map_min)) or default_start_pos)

    # Update config list
    config['channels'].update(
        {
            channel_name: {
                'mcp_in': mcp_in,
                'servo_pin': servo_pin,
                'map_min': int(map_min),
                'map_max': int(map_max),
                'start_pos': start_pos,
            }
        }
    )

    # Write to config
    write_project_config(project_name, config)


def new_project(project_name):
    """
    Create new folder structure and setup config file.
    """
    # Get path
    project_path = read_main_config()['project_path']
    path = os.path.join(project_path, project_name)

    # Path not existent?
    if not os.path.exists(path):
        os.makedirs(path)
        os.makedirs(os.path.join(path, 'audio'))
        os.makedirs(os.path.join(path, 'trash'))

        answer = raw_input(
            "Copy config file from existing project? [Y/N] (For servo settings & recording connection type)\n").lower()
        if answer == "y":

            file_list = os.listdir(project_path)
            projects = sorted([a for a in file_list if not a.startswith(".")])
            if '_archive' in projects:
                projects.remove('_archive')
            if project_name in projects:
                projects.remove(project_name)

            if not projects:
                print("There are no project folders in '%s'." % project_path)
            else:
                project_list = list()
                print('Copy from where?')
                print('ID:\tProject:')
                # For each project to analyze
                for i, project in enumerate(projects):
                    print('%s\t%s' % (i, project))
                    project_list.append(i)

                answer = int(raw_input("Type your ID:\n").lower())

                if answer in project_list:
                    copy_from = os.path.join(project_path, projects[answer], 'config')
                    copy_to = os.path.join(path, 'config')
                    copyfile(copy_from, copy_to)
                    pass
                else:
                    print('By god, this is not an acceptable answer.')

        print('Created new project structure.')
    else:
        print('╳  Project already exists.')


def copy_channel(project_name, channel_old, channel_new, preserve_pin='pin_inc'):
    """
    Copies file channel_old to channel_new with matching config data. preserve pin copies
    servo pin 1:1 if true, if false increments the total amount of servo channels.
    """
    project_path = read_main_config()['project_path']
    config = read_project_config(project_name)

    # Check if new channel already exists
    if not os.path.isfile(os.path.join(project_path, project_name, channel_new)) \
            and channel_new not in config['channels']:
        # Copy old to new
        copyfile(os.path.join(project_path, project_name, channel_old),
                 os.path.join(project_path, project_name, channel_new))

        if preserve_pin == "pin_inc":
            # Write new servo_pin
            preserve_pin = len(config['channels'])

        elif preserve_pin == "pin_copy":
            # Copy servo_pin old to servo_pin new
            preserve_pin = config['channels'][channel_old]['servo_pin']
        else:
            # Write user defined integer as servo_pin
            preserve_pin = int(preserve_pin)

        # Update config list
        config['channels'].update(
            {
                channel_new: {
                    'mcp_in': config['channels'][channel_old]['mcp_in'],
                    'servo_pin': preserve_pin,
                    'map_min': config['channels'][channel_old]['map_min'],
                    'map_max': config['channels'][channel_old]['map_max'],
                    'start_pos': config['channels'][channel_old]['start_pos']
                }
            }
        )
        # Write in config file
        write_project_config(project_name, config)
        print("File and config data for new channel '%s' in project '%s' copied from '%s'." % (channel_new,
                                                                                               project_name,
                                                                                               channel_old))
    else:
        print("╳  File or config data for channel '%s' in project '%s' already exists." % (channel_new, project_name))


def get_dof(mcp_in, servo_pin):
    """
    Move servo, directly controlled via user input. Standard boundaries comply.
    On enter return of current value.
    """
    potentiometer = Potentiometer(mcp_in)
    servo = Servo(servo_pin)

    while True:
        reading = potentiometer.read()
        value = map_value(reading, 0, 1024, 600, 100)
        servo.set_pos(value)
        print("{}{}{}░".format(reading, ' ' * (5 - len(str(reading))), "█" * (reading / 5)))

        # Exit loop when enter is pressed
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            print("Defined: %s" % value)
            servo.turn_off()
            return value
        sleep(1 / 50.0)


def record_channel(project_name, channel_name):
    """
    Listen to analog input via MCP3008, follow with single servo and store data in file.
    :type project_name: str
    :type channel_name: str
    """
    # Read config data for channel
    config = read_project_config(project_name)
    servo_pin = config['channels'][channel_name]['servo_pin']
    map_min = config['channels'][channel_name]['map_min']
    map_max = config['channels'][channel_name]['map_max']
    mcp_in = config['channels'][channel_name]['mcp_in']

    servo = Servo(servo_pin)
    potentiometer = Potentiometer(mcp_in)
    player = Player(project_name)
    project_path = read_main_config()['project_path']

    data = []
    # Countdown for slow recordists
    print('Start recording in...')
    time.sleep(1)
    print('3')
    time.sleep(1)
    print('2')
    time.sleep(1)
    print('1')
    time.sleep(1)
    print('Go!')

    player._play_audio()

    # Open channel file, get start time of recording
    start_time = time.time()

    # Set up: first reading
    potentiometer_position = potentiometer.read()
    potentiometer_last_position = potentiometer_position
    data.append("%s: %s" % (0.0, potentiometer_position))

    # Record!
    while True:
        potentiometer_position = potentiometer.read()

        # Recording to file
        if potentiometer_position not in range(potentiometer_last_position - 8, potentiometer_last_position + 8):
            # Playback on servo
            servo_value = map_value(int(potentiometer_position), 0, 1024, map_min, map_max)
            servo.set_pos(servo_value)

            timecode = round(time.time() - start_time, 3)
            data.append("%s: %s" % (timecode, potentiometer_position))
            potentiometer_last_position = potentiometer_position
            logger.info('Servo %s:\t%s\t%s' % (servo_pin, potentiometer_position,
                                               bar(potentiometer_position)))
        else:
            logger.info('----- %s:\t%s\t%s' % (servo_pin, potentiometer_position,
                                               bar(potentiometer_position)))
        # Exit loop when enter is pressed
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            player.stop()
            servo.turn_off()
            break

        time.sleep(0.001)

    player.stop()
    GPIO.cleanup()

    with open(os.path.join(project_path, project_name, channel_name), 'w+') as record_file:
        record_file.write('\n'.join(data))

    logger.info("Recording ended.")

    # Get file size of recorded file
    file_size = get_filesize(os.path.getsize(os.path.join(project_path, project_name, channel_name)), 2)
    logger.info("Recorded file '%s' is %s." % (channel_name, file_size))


if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)  # DEBUG / INFO / WARNING

    record_channel('ohappyday_test', 'blaaaaaaaa')
