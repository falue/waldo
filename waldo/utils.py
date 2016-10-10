import os
import time
import yaml


def read_config(path):
    with open(os.path.join(path, 'config'), 'r') as c:
        config = yaml.load(c.read())
    return config


def write_config(path, config):
    with open(os.path.join(path, 'config'), 'w') as t:
        t.write(yaml.dump(config, default_flow_style=False))


def mapvalue(x, in_min, in_max, out_min, out_max):
    """
    map values fom one range into another
    :param x:
    :param in_min:
    :param in_max:
    :param out_min:
    :param out_max:
    :return:
    """
    # FIXME: + 1?
    return (x - in_min) * (out_max + 1 - out_min) / (in_max - in_min) + out_min


def getfilesize(size, precision=2):
    # human readable filesizes
    # http://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
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
    # detect and write usb connection in file 'config'
    print "Please unplug and replug desired usb device."
    print "Listening to USB ports..."
    usb_detected = False
    usbdevices = os.popen("ls /dev/tty*").read().strip().split("\n")
    # print "start: ",
    # print len(usbdevices)

    while usb_detected == False:
        if len(usbdevices) + 1 == len(
                os.popen("ls /dev/tty*").read().strip().split("\n")):
            usbdevice = "".join(
                set(os.popen("ls /dev/tty*").read().strip().split("\n"))
                .symmetric_difference(usbdevices))
            print "USB device detected; yours is @ %s." % usbdevice
            baudrate = raw_input("Set baudrate:\n[300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200] & [return] ")
            usb_detected = True
            return "%s %s" % (usbdevice, baudrate)
        else:
            usbdevices = os.popen("ls /dev/tty*").read().strip().split("\n")
            # print len(usbdevices)
        time.sleep(0.25)


def get_servo_connection(servo_pin):
    """
    returns servo pins as int and Servo hat board adress as hex
    :param servo:
    """
    hat_adress = servo_pin / 16
    servo_pin = servo_pin % 16

    hat_adress = hex(64+hat_adress)

    connection = {'servo_pin': servo_pin,
                  'hat_adress': hat_adress
                 }

    return connection

# print set_servo_connection(66)


def get_mcp_connection(mcp_pin):
    """
    returns connection pin numbers based on input pin
    :param mcp_pin:
    :return:
    """
    ic = mcp_pin / 8
    preferences = read_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
    return preferences['mcp'][ic]

# print get_mcp_connection(8)
