#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import subprocess
import time
from threading import Thread

import yaml
from RPi import GPIO

GPIO.setwarnings(False)


def read_config(path):
    """
    Read and convert config files.
    :param path:
    :return:
    """
    filepath = os.path.join(path, 'config')
    if os.path.isfile(filepath):
        with open(filepath, 'r') as c:
            config = yaml.safe_load(c.read())
        return config
    else:
        print("There is no such project or no config file in %s" % path)
        exit()


def read_main_config():
    try:
        return read_config(os.path.expanduser('~/.config/waldo/main_config.yml'))
    except:
        # create config
        pass


def write_config(path, config):
    """
    Write in config file.
    :param path:
    :param config:
    :return:
    """
    with open(os.path.join(path, 'config'), 'w') as t:
        t.write(yaml.dump(config, default_flow_style=False))


def mapvalue(x, in_min, in_max, out_min, out_max):
    """
    Map values from one range to another.
    :param x:
    :param in_min:
    :param in_max:
    :param out_min:
    :param out_max:
    :return:
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def get_filesize(size, precision=2):
    """
    Get human readable filesizes of file.
    :param size:
    :param precision:
    :return:
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
    :return:
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
    preferences = read_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
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
        return "█" * (mapvalue(value, 100, 500, 0, max_bar) - 1) + "░"
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


if __name__ == '__main__':
    print(detect_usb_device())
