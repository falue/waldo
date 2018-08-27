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


def list_projects(project=False):
    """
    List every or a single channel in every project and point out difficulties.
    :return:
    """
    project_path = read_main_config()['project_path']

    # Read every folder or define specific
    if project:
        projects = [project]
        print("List every channel in project '%s' and point out difficulties.\n"
              "--------------------------------------------------------------------" % project)
    else:
        filelist = os.listdir(project_path)
        projects = [a for a in filelist if not a.startswith(".")]
        print("List every channel in every project and point out difficulties.\n"
              "--------------------------------------------------------------------")

    # TODO: md5 hashing content of channels, find and mark duplicates

    # ignore archive
    if '_archive' in projects:
        projects.remove('_archive')
    pass

    if not projects:
        print("There are no project folders in '%s'." % project_path)

    # For each project to analyze
    for project in sorted(projects):
        ch = ""
        error = ""
        disturbence = []
        channelfiles_spec = []

        # Read config of channel
        play_channels = read_project_config(project)
        if 'channels' in play_channels:
            # Iter every channel in project
            for channel, data in sorted(play_channels['channels'].iteritems()):
                servo_dof_deg = 90

                # Check if servo_pin was multiple used
                if data['servo_pin'] in disturbence:
                    error += "╳  Multiple use of servo pin %s (%s)\n" % (data['servo_pin'], channel)

                # Store servo pin for later use to check this^
                disturbence.append(data['servo_pin'])

                # Check if channel file exist as in config data specified
                if not os.path.isfile(os.path.join(project_path, project, channel)):
                    error += "╳  No file '%s' for specs in config\n" % channel

                # Store channelname for later use
                channelfiles_spec.append(channel)

                # Calculate visual representation for max degrees of angular freedom
                dof_prepend = map_value(data['map_min'], 100, 600, 0, servo_dof_deg)
                dof_append = servo_dof_deg - map_value(data['map_max'], 100, 600, 0, servo_dof_deg)
                dof = servo_dof_deg - dof_append - dof_prepend

                # Check if channel was reversed, change visual representation
                if dof < 0:
                    reversed_channel = " ⇆"  # ↩ REVERSED
                    dof *= -1
                    dof_prepend_temp = dof_prepend
                    dof_append_temp = dof_append
                    dof_prepend = servo_dof_deg - dof_append_temp
                    dof_append = servo_dof_deg - dof_prepend_temp
                else:
                    reversed_channel = ''
                # ch += "\t%s + %s + %s = %s (%s)\n" % (dof_prepend, dof,
                #                                      dof_append, dof_prepend+dof+dof_append, servo_dof_deg)

                # Create visual representation of max degrees of angular freedom
                graph_rep = "░" * map_value(dof_prepend, 0, servo_dof_deg, 0, 60) + \
                            "█" * map_value(dof, 0, servo_dof_deg, 0, 60) + \
                            "░" * map_value(dof_append, 0, servo_dof_deg, 0, 60)

                # Correct table layout if long channel name
                if len(channel) < 8:
                    name_space = "\t"
                else:
                    name_space = ""

                # Sum up channel content
                ch += "\t%s\t%s%s\t%s\t%s\t%s\t%s\t%s°\n\t%s%s\n" % (channel, name_space, data['servo_pin'],
                                                                     data['mcp_in'], data['map_min'],
                                                                     data['map_max'], data['start_pos'], dof,
                                                                     graph_rep, reversed_channel)

            # Check if all channel files have corresponding config data specified
            channel_list = os.listdir(os.path.join(project_path, project))
            channelfiles = [a for a in channel_list if not a.startswith(".") and
                            not a == 'config' and
                            not a == 'trash' and
                            not a == 'audio']
            no_specs = "'\n╳  No specs in config for file '".join([item for item in channelfiles if item
                                                                   not in channelfiles_spec])
            if no_specs:
                error += "╳  No specs in config for file '%s'\n" % no_specs

            # Print table header
            thead = "\tchannel\t\tservo\tmcp_in\tmap_min\tmap_max\tst._pos\t°DOF"
            print("%s:\n%s%s\n%s" % (project, error, thead, ch))

        else:
            print("%s\n╳  No channels in config file.\n" % project)

        print("--------------------------------------------------------------------\n")


def legal():
    print("===============================")
    print(" _ _ _ _____ __    ____  _____ ")
    print("| | | |  [] |  |  |    \|     | analog")
    print("| | | |     |  |__|  [] |  [] | digital")
    print("|_____|__||_|_____|____/|_____| pupeteering")
    print("_______________________________")
    print("By Fabian Lüscher 2016.")
    print("http://www.filmkulissen.ch")
    print("With generous help of Ben Hagen. Thanks a bunch!")


if __name__ == '__main__':
    print(detect_usb_device())
