#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import subprocess
import time
from multiprocessing import Process
from threading import Thread

import yaml
from RPi import GPIO
from shutil import copyfile

GPIO.setwarnings(False)


def read_project_config(project_name):
    main_config = read_main_config()
    config_path = os.path.join(main_config['project_path'], project_name, 'config')

    try:
        with open(config_path, 'r') as c:
            config = yaml.safe_load(c.read())
        return config
    except IOError:
        return {}


def read_main_config():
    try:
        # FIXME: use exists_ok in Python3
        os.makedirs(os.path.expanduser('~/.waldo/'))
    except OSError:
        pass

    config_path = os.path.expanduser('~/.waldo/main_config.yml')

    try:
        with open(config_path, 'r') as c:
            config = yaml.safe_load(c.read())
    except IOError:
        config = {'project_path': '/home/pi/waldo_projects',
                  'autostart': True,
                  'buttons': [],
                  'measure_temp': True,
                  }
        with open(config_path, 'w') as f:
            f.write(yaml.safe_dump(config))

    return config


def write_project_config(project_name, config):
    """
    Write in config file.
    """
    project_path = read_main_config()['project_path']
    with open(os.path.join(project_path, project_name, 'config'), 'w') as t:
        t.write(yaml.safe_dump(config, default_flow_style=False))


def map_value(x, in_min, in_max, out_min, out_max):
    """
    Map values from one range to another.
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def get_filesize(size, precision=2):
    """
    Get human readable filesizes of file.
    """
    suffixes = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
    suffix_index = 0
    if size < 1024:
        return "%.*f%s" % (precision, size, suffixes[suffix_index])
    else:
        while size >= 1024 and suffix_index < 4:
            suffix_index += 1
            size /= 1024.0
        return "%.*f %s" % (precision, size, suffixes[suffix_index])


def detect_usb_device():
    """
    Detect and write usb connection in file 'config'
    """
    print("Please unplug and replug desired usb device.")
    print("Listening to USB ports...")
    usb_devices = get_usb_devices()

    while True:
        if len(usb_devices) + 1 == len(get_usb_devices()):
            usb_device = set(get_usb_devices()).symmetric_difference(usb_devices).pop()
            print("USB device detected; yours is @ %s." % usb_device)
            baud_rate = raw_input(
                "Set baud_rate:\n[300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200] & "
                "[return] (Default: 9600)\n") or 9600
            return usb_device, baud_rate
        else:
            usb_devices = get_usb_devices()
        time.sleep(0.25)


def get_usb_devices():
    return subprocess.check_output('ls /dev/tty*', shell=True).strip().splitlines()


def get_servo_connection(servo_pin):
    """
    Returns servo pins as int and servo hat board address as hex.
    :type servo_pin: int
    """
    hat_address = servo_pin / 16
    servo_pin %= 16

    hat_address = int(hex(64 + hat_address), 16)

    connection = {'servo_pin': servo_pin,
                  'hat_address': hat_address
                  }

    return connection


def get_mcp_connection(mcp_pin):
    """
    Returns connection pin numbers based on input pin.
    :param mcp_pin:
    :return:
    """
    ic = mcp_pin / 8
    preferences = read_main_config()
    return preferences['mcp'][ic]


def set_gpio_pins(preferences):
    """
    Set GPIO pins as used by mcp read/write pins.
    :param preferences:
    :return:
    """
    # set GPIO
    GPIO.VERBOSE = False
    GPIO.setmode(GPIO.BCM)

    for mcps in preferences['mcp']:
        # set up the SPI interface pins
        GPIO.setup(preferences['mcp'][mcps]['MOSI'], GPIO.OUT)
        GPIO.setup(preferences['mcp'][mcps]['MISO'], GPIO.IN)
        GPIO.setup(preferences['mcp'][mcps]['CLK'], GPIO.OUT)
        GPIO.setup(preferences['mcp'][mcps]['CS'], GPIO.OUT)


def bar(value, max_bar=30):
    """
    Visual representation for analog values.
    :param value:
    :param max_bar:
    :return:
    """
    if value > 0:
        return "█" * (map_value(value, 100, 500, 0, max_bar) - 1) + "░"
    else:
        return "░"


def get_first_file(path, suffix=False):
    if not suffix:
        suffix = ''
    if os.path.isdir(path):
        file_list = os.listdir(path)
        audio_files = [a for a in file_list if a.lower().endswith(suffix) and not a.startswith('.')]
        if len(audio_files):
            return audio_files[0]
        else:
            return None


def threaded(fn):
    def wrapper(*args, **kwargs):
        t = Thread(target=fn, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()

    return wrapper


def processed(fn):
    def wrapper(*args, **kwargs):
        t = Process(target=fn, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()

    return wrapper


def get_all_projects():
    project_path = read_main_config()['project_path']
    file_list = os.listdir(project_path)
    return [a for a in file_list if not a.startswith(".") and not a == '_archive']


def print_projects(project_name, bt_only=False):
    """
    List every or a single channel in every project and point out difficulties.
    """
    main_config = read_main_config()
    project_path = main_config['project_path']

    # Read every folder or define specific
    if project_name:
        if not os.path.isdir(os.path.join(project_path, project_name)):
            print('Project \'{}\' does not exist.'.format(project_name))
            exit()
        projects = [project_name]
        print('List project \'{}\' and show errors.\n'.format(project_name))
    elif bt_only:
        projects = main_config['buttons'].values()
        print('List button projects and show errors.\n')
    else:
        projects = get_all_projects()
        print('List every project and show errors.\n')

    print('────────────────────────────────────────────────────────────────────────')

    if not projects:
        print('There are no project folders in \'{}\'.'.format(project_path))

    # For each project to analyze
    for project_name in sorted(projects):
        ch = ''
        error = ''
        spacer = ''
        button_name = ''
        used_servo_pins = []
        channel_specs = []

        # Display button
        if project_name in main_config['buttons'].values():
            button_name = main_config['buttons'].keys()[main_config['buttons'].values().index(project_name)]
            button_name = ' Button: {} '.format(button_name)
            spacer = " " * (71 - len(project_name) - len(button_name))

        print('{}:{}\033[100m{}\033[41m\033[0m'.format(project_name, spacer, button_name))

        # Read config of channel
        project = read_project_config(project_name)
        if 'channels' in project:
            for channel, data in sorted(project['channels'].iteritems()):
                servo_dof_deg = 90

                # Check if servo_pin was used multiply
                if data['servo_pin'] in used_servo_pins:
                    error += '\033[41m ✖  Multiple use of servo pin {} ({}) \033[41m\033[0m\n'.format(
                        data['servo_pin'],
                        channel
                    )

                # Store servo pin for later use to check this^
                used_servo_pins.append(data['servo_pin'])

                # Check if channel file exist as in config data specified
                if not os.path.isfile(os.path.join(project_path, project_name, channel)):
                    error += '✖  No file \'{}\' for specs in config\n'.format(channel)

                # Store channel name for later use
                channel_specs.append(channel)

                # Calculate visual representation for max degrees of angular freedom
                dof_prepend = map_value(data['map_min'], 100, 600, 0, servo_dof_deg)
                dof_append = servo_dof_deg - map_value(data['map_max'], 100, 600, 0, servo_dof_deg)
                dof = servo_dof_deg - dof_append - dof_prepend

                # Check if channel was reversed, change visual representation
                if dof < 0:
                    reversed_channel = ' ↹'  # ↩ REVERSED
                    dof *= -1
                    dof_prepend_temp = dof_prepend
                    dof_append_temp = dof_append
                    dof_prepend = servo_dof_deg - dof_append_temp
                    dof_append = servo_dof_deg - dof_prepend_temp
                else:
                    reversed_channel = ''

                # Create visual representation of max degrees of angular freedom
                graph_rep = '\033[100m \033[0m\033[0m' * map_value(dof_prepend, 0, servo_dof_deg, 0, 60) + \
                            '█' * map_value(dof, 0, servo_dof_deg, 0, 60) + \
                            '\033[100m \033[0m\033[0m' * map_value(dof_append, 0, servo_dof_deg, 0, 60)

                # Correct table layout if long channel name
                if len(channel) < 8:
                    name_space = '\t'
                else:
                    name_space = ''

                # Sum up channel content
                ch += '\t{}\t{}{}\t{}\t{}\t{}\t{}\t{}°\n\t{}{}\n'.format(channel,
                                                                          name_space,
                                                                          data['servo_pin'],
                                                                          data['mcp_in'],
                                                                          data['map_min'],
                                                                          data['map_max'],
                                                                          data['start_pos'],
                                                                          dof,
                                                                          graph_rep,
                                                                          reversed_channel
                                                                          )

            # Check if all channel files have corresponding config data specified
            channel_list = os.listdir(os.path.join(project_path, project_name))
            channel_files = [a for a in channel_list if not a.startswith(".") and
                            not a == 'config' and
                            not a == 'trash' and
                            not a == 'audio']

            for item in channel_files:
                if item not in channel_specs:
                    error += '✖  No specs in config for file \'{}\'\n'.format(item)

            # Print table header and all channels
            thead = '\tchannel\t\tservo\tmcp_in\tmap_min\tmap_max\tst._pos\t°DOF'
            print('{}{}\n{}'.format(error, thead, ch))

        else:
            print('✖  No channels in config file.\n')

        print('────────────────────────────────────────────────────────────────────────\n')


def display_projects():
    project_path = read_main_config()['project_path']
    print('Projects location: {}'.format(project_path))
    projects = get_all_projects()
    print('Total {} projects.'.format(len(projects)))
    for project_name in projects:
        config = read_project_config(project_name)
        len_channels = len(config['channels']) if config else 0
        print('  {} {} {}{} channels'.format(project_name, ' ' * (15-len(project_name)), ' ' if len_channels < 10 else '', len_channels))


def copy_channel(project_name_from, channel_name_old, project_name_to, channel_name_new, pin_mode):
    """
    Copies file channel_name_old to channel_name_new with matching config data. preserve_pin increments the total
    amount of servo channels if 'pin_inc' (default), copies servo pin 1:1 if 'pin_copy', or sets integer if is integer.
    """
    project_path = read_main_config()['project_path']
    config_old = read_project_config(project_name_from)
    config_new = read_project_config(project_name_to)

    # Check if new channel already exists
    if not os.path.isfile(os.path.join(project_path, project_name_from, channel_name_old)):
        print('\033[31mx\033[0m\033[0m Channel file \'{}\' of project \'{}\' does not exist.'.format(channel_name_old, project_name_to))

    elif not os.path.isfile(os.path.join(project_path, project_name_to, channel_name_new)) \
            and not channel_name_new in config_old['channels']:
        copyfile(os.path.join(project_path, project_name_from, channel_name_old),
                 os.path.join(project_path, project_name_to, channel_name_new))

        if pin_mode == "pin_inc":
            # Write new servo_pin
            pin_mode = len(config_new['channels'])

        elif pin_mode == "pin_copy":
            # Copy servo_pin old to servo_pin new
            pin_mode = config_old['channels'][channel_name_old]['servo_pin']
        else:
            # Write user defined integer as servo_pin
            pin_mode = int(pin_mode)

        config_new['channels'].update(
            {
                channel_name_new: {
                    'mcp_in': config_old['channels'][channel_name_old]['mcp_in'],
                    'servo_pin': pin_mode,
                    'map_min': config_old['channels'][channel_name_old]['map_min'],
                    'map_max': config_old['channels'][channel_name_old]['map_max'],
                    'start_pos': config_old['channels'][channel_name_old]['start_pos']
                }
            }
        )
        write_project_config(project_name_to, config_new)
        print("File and config data for new channel '%s' in project '%s' copied from '%s'." % (channel_name_new,
                                                                                               project_name_to,
                                                                                               channel_name_old))
    else:
        print("\033[31mx\033[0m\033[0m File or config data for channel '%s' in project '%s' already exists." % (channel_name_new, project_name_to))


def empty_project_trash(project_name):
    project_path = read_main_config()['project_path']
    file_list = os.listdir(os.path.join(project_path, project_name, 'trash'))
    for file_name in file_list:
        os.remove(os.path.join(project_path, project_name, 'trash', file_name))
    len_files = len(file_list)
    if len_files > 0:
        print('Emptied trash in \'{}\': {} {}'.format(project_name, len_files, 'file' if len_files == 1 else 'files'))
    else:
        print('Trash is empty.')


def show_legal():
    print(""" _ _ _ _____ __    ____  _____ 
| | | |  [] |  |  |    \|     | analog
| | | |     |  |__|  [] |  [] | digital
|_____|__||_|_____|____/|_____| pupeteering

By OTTOMNATIC GmbH 2018.
http://www.ottomatic.io"""
          )


if __name__ == '__main__':
    print(detect_usb_device())
