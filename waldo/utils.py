#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import time
import yaml
from RPi import GPIO as GPIO

GPIO.setwarnings(False)

def read_config(path):
    """
    Read and convert config files.
    :param path:
    :return:
    """
    filepath = os.path.join(path, 'config')
    if(os.path.isfile(filepath)):
        with open(filepath, 'r') as c:
            config = yaml.load(c.read())
        return config
    else:
        print "There is no such project or no config file in project '%s'" % path.split("/")[::1]
        exit()


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


def getfilesize(size, precision=2):
    """
    Get human readable filesizes of file.
    :param size:
    :param precision:
    :return:
    """
    suffixes = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
    suffixIndex = 0
    if size < 1024:
        return "%.*f%s" % (precision, size, suffixes[suffixIndex])
    else:
        while size >= 1024 and suffixIndex < 4:
            suffixIndex += 1
            size /= 1024.0
        return "%.*f %s" % (precision, size, suffixes[suffixIndex])


def usbdetection():
    """
    Detect and write usb connection in file 'config'
    :return:
    """
    print "Please unplug and replug desired usb device."
    print "Listening to USB ports..."
    usb_detected = False
    usbdevices = os.popen("ls /dev/tty*").read().strip().split("\n")
    # print "start: ",
    # print len(usbdevices)

    while not usb_detected:
        if len(usbdevices) + 1 == len(
                os.popen("ls /dev/tty*").read().strip().split("\n")):
            usbdevice = "".join(
                set(os.popen("ls /dev/tty*").read().strip().split("\n"))
                    .symmetric_difference(usbdevices))
            print "USB device detected; yours is @ %s." % usbdevice
            baudrate = raw_input(
                "Set baudrate:\n[300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200] & "
                "[return] (Default: 9600)\n") or 9600
            usb_detected = True
            return "%s %s" % (usbdevice, baudrate)
        else:
            usbdevices = os.popen("ls /dev/tty*").read().strip().split("\n")
            # print len(usbdevices)
        time.sleep(0.25)


def get_servo_connection(servo_pin):
    """
    Returns servo pins as int and servo hat board adress as hex.
    :param servo:
    """
    hat_adress = servo_pin / 16
    servo_pin %= 16

    hat_adress = int(hex(64+hat_adress), 16)

    connection = {'servo_pin': servo_pin,
                  'hat_adress': hat_adress
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
        return "█" * (mapvalue(value, 100, 500, 0, max_bar)-1) + "░"
    else:
        return "░"


def get_first_file(path, suffix=False):
    if not suffix:
        suffix = ''
    filelist = os.listdir(path)
    audiofiles = [a for a in filelist if a.lower().endswith(suffix) and not a.startswith('.')]
    if len(audiofiles):
        return audiofiles[0]
    else:
        return False
