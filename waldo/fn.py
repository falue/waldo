#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import threading
import time

from shutil import copyfile

import serial
from utils import (read_config, write_config, mapvalue, getfilesize, usbdetection)

# install fakeRPiGPIO when not on a raspberry pi
import RPi.GPIO as GPIO
GPIO.VERBOSE = False

# FIXME: remove in production
GPIO.setwarnings(False)

try:
    from Adafruit_MotorHAT.Adafruit_PWM_Servo_Driver import PWM
except ImportError:
    from fake import PWM

# ===========================================================================
# MCP3008 CONFIG
# ===========================================================================

# set GPIO
GPIO.setmode(GPIO.BCM)

# standard mcp3008 connection pins
MCP_CONNECTION = {'CLK': 18,
                  'MISO': 23,
                  'MOSI': 24,
                  'CS': 25
                  }


# set up the SPI interface pins
GPIO.setup(MCP_CONNECTION['MOSI'], GPIO.OUT)
GPIO.setup(MCP_CONNECTION['MISO'], GPIO.IN)
GPIO.setup(MCP_CONNECTION['CLK'], GPIO.OUT)
GPIO.setup(MCP_CONNECTION['CS'], GPIO.OUT)
# GPIO.setwarnings(False) # doesn't work

# ===========================================================================
# MAIN VARIABLES
# ===========================================================================

# PROBABLY DELETE ALL THIS AFTER GETTING RID OF GLOBALS

# set project folder path
preferences = read_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
PROJECT_PATH = os.path.expanduser(preferences["PROJECT_PATH"])
# PROJECT_PATH = os.path.expanduser('~/waldo_projects')

if not os.path.isdir(PROJECT_PATH):
    os.makedirs(PROJECT_PATH)

SERVO_NAME = PWM(0x40)  # ServoHat no. 1

# count_servo = 16  # just for step correction?! -> read channel =>count_servo

STEP = 0.0352  # pause in record, smoothest 0.02 orig 0.0570 (16*0.0022=0.0352)
STEP_PLAYBACK = 0.032 # 1 servo @ 0.0022 # step - float(count_servo)/0.8 * 0.0022 # orig 0.0178 # recording takes longer than playback...  step - 0.00155

# @ 1  servo:  0.0022
# @ 3  servos: 0.032
# @ 8  servos: 0.0504~
# @ 16 servos: 0.05162


RECORDING = False


# ===========================================================================
# FUNCTIONS: GENERAL
# ===========================================================================



# ===========================================================================
# FUNCTIONS: PLAYBACKS
# ===========================================================================
def playback_audio(audiofile, play_from=0):
    # Playback audio
    global RECORDING
    RECORDING = True
    # print "funktion file: "+audiofile

    if play_from > 0:
        bashcommando = 'play %s -q trim %s' % (audiofile, play_from)
    else:
        bashcommando = 'play %s -q' % (audiofile)
    os.system(bashcommando)  # invoke 'sox' in quiet mode

    RECORDING = False
    print "Audio stopped:\t", audiofile


'''
# doesn't work because servoname.setPWMFreq(60) isn't set...?
def setServoPulse(channel, pulse):  # copypasta-überbleibsel...?
    pulseLength = 1000000  # 1,000,000 us per second
    pulseLength /= 60  # 60 Hz
    # print "%d us per period" % pulseLength
    pulseLength /= 4096  # 12 bits of resolution
    # print "%d us per bit" % pulseLength
    pulse *= 1000
    pulse /= pulseLength
    servoname.setPWM(channel, 0, pulse)
    '''


def playback_servo(project, channel, play_from=0):
    """
    Playback single servo
    :param project:
    :param channel:
    :param play_from:
    :return:
    """

    # read config data
    config = read_config(os.path.join(PROJECT_PATH, project))
    servo_pin = config['channels'][channel]['servo_pin']
    map_min = config['channels'][channel]['map_min']
    map_max = config['channels'][channel]['map_max']
    start_pos = config['channels'][channel]['start_pos']


    # fill list with file
    pulse_list = open(os.path.join(PROJECT_PATH, project, channel), 'r')
    pulses = [mapvalue(int(line.strip()), 0, 1024, map_min, map_max) for line in pulse_list]

    print "Channelname:\t%s\tServopin:\t%s\tStat @\t%s" % (channel, servo_pin, play_from)

    SERVO_NAME.setPWMFreq(60)  # Set frequency to 60 Hz

    play_from_index = int(1.0 / STEP * float(play_from))  # steps to n seconds
    # Move servo
    print "Servo start:\t%s frames, start @ %s. frame" % (len(pulses),
                                                          play_from_index)
    # cut off beginning instants of list
    if play_from_index:
        pulses = pulses[play_from_index:]

    for pulse in pulses:
        if RECORDING:  # if project is without sound...
            SERVO_NAME.setPWM(servo_pin, 0, pulse)
            # setServoPulse(servo_pin, pulse)
            print "Pin %d\t%d" % (servo_pin, pulse)
            time.sleep(STEP_PLAYBACK)  # compensation fo slow recording...
        # else :
            # print "Not recording."

    SERVO_NAME.setPWM(servo_pin, 0, start_pos)  # <---- erster pulse = ruhepos.?
    # setServoPulse(servo_pin, startposition)
    print "Servo playback stopped: %s\tStart position: %d" % (channel, start_pos)
    # Set GPIO to default
    GPIO.cleanup()


# ===========================================================================
# FUNCTIONS: RECORD
# ===========================================================================
def record(project, channel, audiofile):
    """
    Listen to USB port and write data into file
    :param project:
    :param channel:
    :param audiofile:
    :return:
    """
    global RECORDING  # really totally necessary

    # listen to USB o mcp3008?
    config = read_config(os.path.join(PROJECT_PATH, project))

    if(config['connection']['type'] == "usb"):
        usb_port = config['connection']['device']
        baudrate = config['connection']['baudrate']
        print "USB port: %s @ %d baud" % (usb_port, baudrate)
    else:
        CLK = config['connection']['CLK']
        MOSI = config['connection']['MOSI']
        MISO = config['connection']['MISO']
        CS = config['connection']['CS']
        SERVO_NAME.setPWMFreq(60)
        print "Connection via MCP3008 (%d %d %d %d)" % (CLK, MISO, MOSI, CS)

    # countdown for slow recordists
    print "Start recording in..."
    print "3"
    time.sleep(1)
    print "2"
    time.sleep(1)
    print "1"
    time.sleep(1)
    print "Go!"
    time.sleep(1)

    # play audio file
    if audiofile:
        processThread0 = threading.Thread(
            target=playback_audio,
            args=(os.path.join(PROJECT_PATH, project, 'audio', audiofile), ))
        # <- note extra ','
        processThread0.start()
    else:
        RECORDING = True

    # set definitions
    # recordfile.write("Pin:\t%s\n" % servopin)
    config = read_config(os.path.join(PROJECT_PATH, project))
    servo_pin = config['channels'][channel]['servo_pin']
    map_min = config['channels'][channel]['map_min']
    map_max = config['channels'][channel]['map_max']

    # record!
    record_file = open(os.path.join(PROJECT_PATH, project, channel), 'w+')

    while RECORDING == True:
        millis = time.time()

        # python: listen to usb port or MCP3008...
        if config['connection']['type'] == "usb":
            record = read_usb(usb_port, baudrate)
        else:
            record = read_mcp(0, CLK, MOSI, MISO, CS)
            #                 ^ channel 0-7 on Chip MCP3008!

        # recording to file...
        record_file.write(str(record) + "\n")  # write 0-1024 in file...
        print record,  # 0-1024

        # playback on servo...
        record = mapvalue(int(record), 0, 1024, map_min,
                          map_max)  # map value to sevo values
        SERVO_NAME.setPWM(int(servo_pin), 0, record)  # move servo
        # setServoPulse(int(servo_pin), record)
        print "\t%s" % record  # servoMin <-> servoMax

        millis = time.time() - millis
        if millis > STEP:
            millis = 0
        # print millis
        time.sleep(STEP - millis)

    record_file.close()
    if config['connection']['type'] == "MCP":
        GPIO.cleanup()
    print "Recording ended."
    heavyness = getfilesize(os.path.getsize(os.path.join(PROJECT_PATH, project, channel)), 2)
    print "Recorded file '%s' is %s heavy." % (channel, heavyness)


def read_usb(usbport, baudrate):
    ser = serial.Serial(usbport, baudrate)
    serial_line = str(ser.readline().strip()).split("#")
    # ^ read serial input by arduino, delete carriage return and errors while transmitting
    #print serial_line
    if len(serial_line) == 3:
        record = serial_line[1]
    else:
        record = last_record
        print ''.join(serial_line), "\t[interpolated", record, "]"
    if record.isdigit():
        return record
    last_record = record


'''
def read_mcp(channel):
    #############
    record = analogread(channel, CLK, MOSI, MISO, CS)
    return record
'''


def read_mcp(adcnum, clockpin, mosipin, misopin, cspin):
    if ((adcnum > 7) or (adcnum < 0)):
        return -1
    GPIO.output(cspin, True)

    GPIO.output(clockpin, False)  # start clock low
    GPIO.output(cspin, False)  # bring CS low

    commandout = adcnum
    commandout |= 0x18  # start bit + single-ended bit
    commandout <<= 3  # we only need to send 5 bits here
    for i in range(5):
        if (commandout & 0x80):
            GPIO.output(mosipin, True)
        else:
            GPIO.output(mosipin, False)
        commandout <<= 1
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)

    adcout = 0
    # read in one empty bit, one null bit and 10 ADC bits
    for i in range(12):
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)
        adcout <<= 1
        if (GPIO.input(misopin)):
            adcout |= 0x1

    GPIO.output(cspin, True)

    adcout >>= 1  # first bit is 'null' so drop it
    return adcout

# ===========================================================================
# FUNCTIONS: ARGUMENTS
# ===========================================================================


def helpfile():
    """
    Read/print help file
    """
    with open(os.path.join(os.path.dirname(__file__), '../help'), 'r') as f:
        print f.read()


def set_connection(project):
    """
    Listen to USB port and write it in config file
    """


    """
    config_path = os.path.join(PROJECT_PATH, project, 'config')


    with open(config_path) as c:
        config_data = c.readlines()

    # print config_data
    if len(config_data) <= 2:
        config_data = ["", ""]
    """
    # if config exists, do append
    config = read_config(os.path.join(PROJECT_PATH, project))
    if not config:
        config = {}

    answer = raw_input("Set up connection with USB or analog input via MCP3008? [USB/MCP]\n").lower()
    if answer == "usb":
        print "Connection set: USB"
        connection = usbdetection().split()
        config.update({'connection': {'type': 'usb',
                                      'device': connection[0],
                                      'baudrate': int(connection[1])
                                      }
                       }
                      )
    elif answer == "mcp":
        print "Connection set: MCP3008 %s" % '-'.join(MCP_CONNECTION)
        config.update({'connection': {'type': 'mcp3008',
                                      'CLK': MCP_CONNECTION['CLK'],
                                      'MISO': MCP_CONNECTION['MISO'],
                                      'MOSI': MCP_CONNECTION['MOSI'],
                                      'CS': MCP_CONNECTION['CS']
                                      }
                       }
                      )
    else:
        print "Either enter USB or MCP, pretty please."
        set_connection(project)
        return

    path = os.path.join(PROJECT_PATH, project)
    write_config(path, config)
    print "New connection saved."


def set_servo(project, channel):
    """
    Set config file for project - MCPin, servo_pin, map_min, map_max, start_pos
    :param project:
    :param channel:
    :param servo_pin:
    :return:
    """
    mcp_in = int(raw_input("%s:\nSet MCP3008 in pin [0-7]\n" % channel))
    servo_pin = int(raw_input("Set servo pin out pin [0-15]\n"))
    map_min = int(raw_input("Set minimum position [150-600]\n"))
    map_max = int(raw_input("Set maximum position [150-600]\n"))
    start_pos = int(raw_input("Set start position [150-600]\n"))

    config = read_config(os.path.join(PROJECT_PATH, project))

    config['channels'].update({channel: {
                'mcp_in': mcp_in,
                'servo_pin': servo_pin,
                'map_min': map_min,
                'map_max': map_max,
                'start_pos': start_pos
            }
        }
    )

    write_config(os.path.join(PROJECT_PATH, project), config)


def record_setup(arg):
    """
    play audio, listen to USB port, follow with single servo and store data in file
    :param arg:
    :return:
    """
    project = arg[2]
    channel = arg[3]
    try:
        audio_file = arg[4]
    except IndexError:
        audio_file = False

    if not os.path.isdir(os.path.join(PROJECT_PATH, project)):
        newproject(project)

    # file exists?
    if os.path.isfile(os.path.join(PROJECT_PATH, project, channel)):
        # overwite?
        answer = raw_input("'%s' already exists. Replace? [Y/N]\n" % channel).lower()

        if answer == "y":
            # backup file in 'trash'
            copyfile(os.path.join(PROJECT_PATH, project, channel),
                     os.path.join(PROJECT_PATH, project, "trash",
                     time.strftime("%y-%m-%d_%H-%M-%S") + "_" + channel))
        elif answer == "n":
            print "Abort."
            return
        else:
            print "[Y/N] murmel, murmel"
            record_setup(arg)
            return # sure?
    else:
        set_servo(project, channel)

    record(project, channel, audio_file)


def singleplay(arg):
    """
    Play single servo @ specific pin and occasional audio file
    :param arg:
    :return:
    """
    global RECORDING

    project = arg[2]
    channelname = arg[3]
    try:
        audiofile = arg[4]
    except IndexError:
        audiofile = False

    print "Play single servo."

    if audiofile:
        processThread0 = threading.Thread(
            target=playback_audio,
            args=(os.path.join(PROJECT_PATH, project, 'audio', audiofile), )) # <- note extra ','
        processThread0.start()
    else :
      RECORDING = True # if no audio

    # play servo thread:
    processThread1 = threading.Thread(
        target=playback_servo, args=(project, channelname, )) # ^ note extra ','
    processThread1.start()


def play_all(project, play_from=0):
    """
    Play audio file and playback all servos there are
    :param project:
    :param play_from:
    :return:
    """

    global RECORDING

    print "Play everything; start @ %ss" % play_from

    # play audio thread when set:
    filelist = os.listdir(os.path.join(PROJECT_PATH, project, 'audio'))
    audiofiles = [a for a in filelist if a.lower().endswith(('.wav', '.mp3', '.aiff'))]

    if audiofiles:
        processThread0 = threading.Thread(
            target=playback_audio,
            args=(os.path.join(PROJECT_PATH, project, 'audio', audiofiles[0]),
                  play_from, ))
        # <- note extra ','
        processThread0.start()
    else:
        RECORDING = True

    play_channels = read_config(os.path.join(PROJECT_PATH, project))
    # print play_channels
    for channel, data in play_channels['channels'].iteritems():
        #print "%s --- %s" % (channel, data)
        processThread1 = threading.Thread(
            target=playback_servo,
            args=(project, channel, play_from,)
        )
        # ^ note extra ','
        processThread1.start()


def newproject(project_name):
    path = os.path.join(PROJECT_PATH, project_name)
    if not os.path.exists(path):
        os.makedirs(path)
        os.makedirs(os.path.join(path, 'audio'))
        os.makedirs(os.path.join(path, 'trash'))
        os.mknod(os.path.join(path, 'config'))

        print "Created new project structure."
        set_connection(project_name)
    else:
        print "Project already exists."


def listprojects():
    """
    print overview for all pojects including channels/servoPin connection
    :return:
    """

    print "List every channel in every project.\n------------------------------"

    # read folder...
    # projects = os.listdir(PROJECT_PATH) # os.path.join()

    filelist = os.listdir(PROJECT_PATH)
    projects = [a for a in filelist if not a.startswith(".")]

    for project in projects:
        print "%s:" % project
        with open(os.path.join(PROJECT_PATH, project, 'config'), 'r') as myfile:
            data = myfile.read()
        print data
        print "------------------------------"


    """
    filelist = os.listdir(PROJECT_PATH)
    projects = [a for a in filelist if not a.startswith(".")]

    for project in projects:
        print "%s:" % project
        playchannels = os.listdir(os.path.join(PROJECT_PATH, project))
        for channel in playchannels:
            # print "\t->"+channel
            if channel != "audio" and channel != "trash" and not channel.startswith("."):
                with open(os.path.join(PROJECT_PATH, project, channel), "r") as f:
                    firstline = f.readline().strip().split("\t")
                if len(firstline) > 1:
                    servopin = firstline[1]
                else:
                    servopin = "?"
                print "    ↳ %s\t%s" % (channel, servopin)
            elif channel == "audio":
                audiolist = os.listdir(os.path.join(PROJECT_PATH, project, "audio"))
                audios = [a for a in audiolist if not a.startswith(".")]
        for audio in audios:
            print "    ↳ audio:\t%s" % audio
        print "------------------------------"
    """

def legal():
    print "done by me."
    print "2016."
    print "huehuehue."
