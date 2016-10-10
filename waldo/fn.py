#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import threading
import time

from shutil import copyfile

import serial

from utils import (read_config, write_config, mapvalue, getfilesize, usbdetection, get_servo_connection, get_mcp_connection)

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
# MAIN VARIABLES
# ===========================================================================

# set project folder path
preferences = read_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
PROJECT_PATH = os.path.expanduser(preferences["PROJECT_PATH"])

# set GPIO
GPIO.setmode(GPIO.BCM)

for mcps in preferences['mcp']:
    # set up the SPI interface pins
    GPIO.setup(preferences['mcp'][mcps]['MOSI'], GPIO.OUT)
    GPIO.setup(preferences['mcp'][mcps]['MISO'], GPIO.IN)
    GPIO.setup(preferences['mcp'][mcps]['CLK'], GPIO.OUT)
    GPIO.setup(preferences['mcp'][mcps]['CS'], GPIO.OUT)


if not os.path.isdir(PROJECT_PATH):
    os.makedirs(PROJECT_PATH)

STEP = 0.0352  # pause in record, smoothest 0.02 orig 0.0570 (16 servos * 0.0022 = 0.0352)

REC_REPL = False
SERVO_READY = {}


# ===========================================================================
# FUNCTIONS: PLAYBACKS
# ===========================================================================
def playback_audio(audiofile, play_from=0):
    """
    Playback audio
    :param audiofile:
    :param play_from:
    :return:
    """
    global REC_REPL

    wait_for_servos()

    print "Audio start:\t%s" % audiofile

    if play_from:
        bashcommando = 'play %s -q trim %s' % (audiofile, play_from)
    else:
        bashcommando = 'play %s -q' % (audiofile)
    os.system(bashcommando)  # invoke 'sox' in quiet mode

    REC_REPL = False
    print "Audio stopp:\t%s" % audiofile


def wait_for_servos():
    """
    Wait for servos to initiate and set REC_REPL to True if they do so.
    :return:
    """
    global REC_REPL

    # wait for every servo to catch up
    while not REC_REPL:
        print "Wait for all servos to be ready..."
        if all(value == True for value in SERVO_READY.values()):
            print "All servos ready."
            REC_REPL = True
        time.sleep(0.1)


def setServoPulse(channel, pulse):  # copypasta-überbleibsel...?
    # doesn't work because servoname.setPWMFreq(60) isn't set...?
    '''
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

    global SERVO_READY

    # read config data
    config = read_config(os.path.join(PROJECT_PATH, project))
    servo_pin = config['channels'][channel]['servo_pin']
    map_min = config['channels'][channel]['map_min']
    map_max = config['channels'][channel]['map_max']
    start_pos = config['channels'][channel]['start_pos']

    servo_connection = get_servo_connection(servo_pin)
    servo_pin = servo_connection['servo_pin']
    servo_obj = PWM(servo_connection['hat_adress'])

    print "Channelname:\t%s\tServopin:\t%s\tStart @\t%ss" % (channel, servo_pin, play_from)

    servo_obj.setPWMFreq(60)  # Set frequency to 60 Hz

    # fill list with file

    pulse_list = {}
    pulse_file = open(os.path.join(PROJECT_PATH, project, channel), 'r')
    for line in pulse_file.readlines():
        timestamp, value = line.split(": ")
        pulse_list[float(timestamp)] = int(value)

    """
    ^^faster than yaml
    with open(os.path.join(PROJECT_PATH, project, channel), 'r') as c:
        pulse_list = yaml.load(c.read())
    """

    tot_pulse_size = len(pulse_list)

    if play_from:
        play_from = float(play_from)
        for key in [p for p in pulse_list]:
            if key <= play_from:
                del pulse_list[key]

    print "Servo ready:\t%s\t%s frames\tstart @ %sth frame" % \
          (servo_pin, tot_pulse_size, tot_pulse_size - len(pulse_list))


    SERVO_READY.update({channel: True})

    # wait for all servos to catch on...
    while not REC_REPL:
        time.sleep(0.05)

    start_time = time.time()

    for rec_time, pulse in sorted(pulse_list.iteritems()):
        if REC_REPL:  # if project is without sound...
            # setServoPulse(servo_pin, pulse)
            cur_time = float("{0:.2f}".format(time.time()-start_time))
            rec_time_abr = float("{0:.2f}".format(rec_time))
            diff_time = rec_time_abr-cur_time
            # if float("{0:.2f}".format(rec_time)) - float("{0:.2f}".format(cur_time)) == 0:

            if diff_time >= -0.02 and diff_time <= 0.02:
                # print "\t\t\t" * servo_pin, servo_pin, rec_time_abr, cur_time, diff_time
                # print "Pin %d\t%d" % (servo_pin, pulse_map)
                print "\t\t\t\t\t\t\t\t" * servo_pin, "█" * mapvalue(pulse, 0, 1024, 1, 50)
                pulse_map = mapvalue(pulse, 0, 1024, map_min, map_max)
                servo_obj.setPWM(servo_pin, 0, pulse_map)
            #else:
            #    print "\t\t\t\t\t\t\t\t" * servo_pin, rec_time_abr, cur_time, diff_time, "not match"
            if STEP + diff_time >= 0 :
                sleeping = STEP + diff_time
            else:
                sleeping = 0
            time.sleep(sleeping)  # -(rec_time-diff_time)
        # else:
           # print "nothing"

    servo_obj.setPWM(servo_pin, 0, start_pos)  # <---- erster pulse = ruhepos.?
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
    global REC_REPL  # really totally necessary

    # listen to USB or mcp3008?
    config = read_config(os.path.join(PROJECT_PATH, project))
    servo_pin = config['channels'][channel]['servo_pin']
    map_min = config['channels'][channel]['map_min']
    map_max = config['channels'][channel]['map_max']

    servo_connection = get_servo_connection(servo_pin)
    servo_pin = servo_connection['servo_pin']
    servo_obj = PWM(servo_connection['hat_adress'])
    # servo_obj = PWM(servo_connection['hat_adress'])

    if(config['connection']['type'] == "usb"):
        usb_port = config['connection']['device']
        baudrate = config['connection']['baudrate']
        print "USB port: %s @ %d baud" % (usb_port, baudrate)
    else:
        mcp_in = config['channels'][channel]['mcp_in']
        mcp_connection = get_mcp_connection(mcp_in)
        CLK = mcp_connection['CLK']
        MOSI = mcp_connection['MOSI']
        MISO = mcp_connection['MISO']
        CS = mcp_connection['CS']
        mcp_in %= 8
        servo_obj.setPWMFreq(60)
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
        REC_REPL = True

    # record!
    record_file = open(os.path.join(PROJECT_PATH, project, channel), 'w+')
    start_time = time.time()

    while REC_REPL == True:
        # python: listen to usb port or MCP3008...
        if config['connection']['type'] == "usb":
            record = read_usb(usb_port, baudrate)
        else:
            record = read_mcp(mcp_in, CLK, MOSI, MISO, CS)

        # recording to file...
        record_file.write("%s: %s\n" % (time.time()-start_time, record))  # write timecode and 0-1024 in file...
        print "%s\t%s" % (time.time()-start_time, record),  # 0-1024

        # playback on servo...
        record = mapvalue(int(record), 0, 1024, map_min,
                          map_max)  # map value to sevo values
        servo_obj.setPWM(int(servo_pin), 0, record)  # move servo
        # setServoPulse(int(servo_pin), record)
        print "\t%s" % record  # servoMin <-> servoMax

        time.sleep(STEP)

    record_file.close()
    if config['connection']['type'] == "mcp3008":
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
        print "Connection set: MCP3008"
        config.update({'connection': {'type': 'mcp3008'
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
    config = read_config(os.path.join(PROJECT_PATH, project))

    if 'channels' not in config:
        config.update({'channels': {}})

    if channel not in config['channels']:
        default_mcp_in = 0
        default_servo_pin = 0
        default_map_min = 150
        default_map_max = 500
        default_start_pos = False
    else:
        default_mcp_in = config['channels'][channel]["mcp_in"]
        default_servo_pin = config['channels'][channel]["servo_pin"]
        default_map_min = config['channels'][channel]["map_min"]
        default_map_max = config['channels'][channel]["map_max"]
        default_start_pos =  config['channels'][channel]["start_pos"]

    mcp_in = int(raw_input("%s:\nSet MCP3008 in pin [0-7] (Default: %s)\n" % (channel, default_mcp_in)) or default_mcp_in)
    servo_pin = int(raw_input("Set servo pin out pin [0-15] (Default: %s)\n" % (default_servo_pin)) or default_servo_pin)
    map_min = raw_input("Set minimum position [150-500] (Default: %s; 'm' for manual detection)\n" % (default_map_min)) or default_map_min
    if map_min == 'm':
        map_min = get_dof(mcp_in, servo_pin)
    map_max = raw_input("Set maximum position [150-500] (Default: %s; 'm' for manual detection)\n" % (default_map_max)) or default_map_max
    if map_max == 'm':
        map_max = get_dof(mcp_in, servo_pin)
    if not default_start_pos:
        default_start_pos = map_min
    start_pos = int(raw_input("Set start position [150-500] (Default: %s; map_min: %s)\n" % (default_start_pos, map_min)) or default_start_pos)

    config['channels'].update({channel: {
                'mcp_in': mcp_in,
                'servo_pin': servo_pin,
                'map_min': int(map_min),
                'map_max': int(map_max),
                'start_pos': start_pos
            }
        }
    )

    write_config(os.path.join(PROJECT_PATH, project), config)


def get_dof(mcp_in, servo_pin):
    """
    playback live analog input -> servo_pin
    actually useful for direct replay?
    :param mcp_in:
    :param servo_pin:
    :return:
    """
    mcp_connection = get_mcp_connection(mcp_in)
    CLK = mcp_connection['CLK']
    MOSI = mcp_connection['MOSI']
    MISO = mcp_connection['MISO']
    CS = mcp_connection['CS']
    mcp_in %= 8

    servo_connection = get_servo_connection(servo_pin)
    servo_pin = servo_connection['servo_pin']
    servo_obj = PWM(servo_connection['hat_adress'])

    # FIXME: exit loop with return not ctrl+c

    print "Press ctrl + c for returning value."

    try:
        while True:
            value = read_mcp(mcp_in, CLK, MOSI, MISO, CS)
            value = mapvalue(value, 0, 1024, 150, 500)
            # print value,
            servo_obj.setPWM(servo_pin, 0, value)
            print "\r%s " % value,
            time.sleep(0.01)
    except KeyboardInterrupt:
        print "\nDefined: %s" % value
        return value


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
        new_project(project)

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
    global REC_REPL

    project = arg[2]
    channelname = arg[3]
    try:
        audiofile = arg[4]
    except IndexError:
        audiofile = False

    print "Play single servo."

    # play servo thread:
    process_thread_1 = threading.Thread(
        target=playback_servo,
        args=(project, channelname, )) # ^ note extra ','
    process_thread_1.start()

    wait_for_servos()

    if audiofile:
        process_thread_0 = threading.Thread(
            target=playback_audio,
            args=(os.path.join(PROJECT_PATH, project, 'audio', audiofile), )) # <- note extra ','
        process_thread_0.start()
    # else:
        # REC_REPL = True # if no audio


def play_all(project, play_from=0):
    """
    Play audio file and playback all servos there are
    :param project:
    :param play_from:
    :return:
    """

    global REC_REPL
    global SERVO_READY

    print "Play everything; start @ %ss" % play_from

    play_channels = read_config(os.path.join(PROJECT_PATH, project))
    # print play_channels
    for channel, data in play_channels['channels'].iteritems():
        #print "%s --- %s" % (channel, data)
        # threading.Thread(target=playback_servo, args=(project, channel, play_from,), name='channel').start()
        process_thread_1 = threading.Thread(
            target=playback_servo,
            args=(project, channel, play_from,)
        )
        # ^ note extra ','
        SERVO_READY.update({channel: False})
        process_thread_1.start()

    wait_for_servos()

    # play audio thread when set:
    filelist = os.listdir(os.path.join(PROJECT_PATH, project, 'audio'))
    audiofiles = [a for a in filelist if a.lower().endswith(('.wav', '.mp3', '.aiff'))]

    if audiofiles:
        process_thread_0 = threading.Thread(
            target=playback_audio,
            args=(os.path.join(PROJECT_PATH, project, 'audio', audiofiles[0]),
                  play_from, ))
        # <- note extra ','
        process_thread_0.start()
    # else:
        # REC_REPL = True



def new_project(project_name):
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


def list_projects(project=False):
    """
    List every channel in every project and point out difficulties.
    :return:
    """
    # read folder...
    # projects = os.listdir(PROJECT_PATH) # os.path.join()
    if project:
        projects = [project]
        print "List every channel in project '%s' and point out difficulties.\n\n" \
              "------------------------------------------------------------" % project
    else:
        filelist = os.listdir(PROJECT_PATH)
        projects = [a for a in filelist if not a.startswith(".")]
        print "List every channel in every project and point out difficulties.\n\n" \
              "------------------------------------------------------------"

    for project in projects:
        ch = ""
        error = ""
        disturbence = []
        play_channels = read_config(os.path.join(PROJECT_PATH, project))
        # print play_channels
        for channel, data in play_channels['channels'].iteritems():
            servo_dof_deg = 89
            if data['servo_pin'] in disturbence:
                error = "ERROR: MULTIPLE USE OF SERVOPIN %s" % data['servo_pin']
            disturbence = {data['servo_pin']}

            dof_prepend = mapvalue(data['map_min'], 150, 500, 0, servo_dof_deg)
            dof_append =  servo_dof_deg-mapvalue(data['map_max'], 150, 500, 0, servo_dof_deg)
            dof = servo_dof_deg-dof_append-dof_prepend
            ch += "\tchannel\tservo\tmcp_in\tmap_min\tmap_max\tst._pos\t°DOF\n"
            ch += "\t%s\t%s\t%s\t%s\t%s\t%s\t%s°\n" % (channel, data['servo_pin'], data['mcp_in'], data['map_min'],
                                                data['map_max'], data['start_pos'], dof)
            if dof < 0:
                ch += "REVERSE"
                dof *= -1
                dof_prepend_temp = dof_prepend
                dof_append_temp = dof_append
                dof_prepend = servo_dof_deg-dof_append_temp
                dof_append = servo_dof_deg-dof_prepend_temp
            #ch += "\t%s + %s + %s = %s (%s)\n" % (dof_prepend, dof,
            # dof_append, dof_prepend+dof+dof_append, servo_dof_deg)
            ch += "\t" +\
                  "▒" * mapvalue(dof_prepend, 0, servo_dof_deg, 0, 53) +\
                  "█" * mapvalue(dof, 0, servo_dof_deg, 0, 51) +\
                  "▒" * mapvalue(dof_append, 0, servo_dof_deg, 0, 53) +\
                  "\n"
        print "%s:\t%s\n%s" % (project, error, ch)
        print "------------------------------------------------------------"


def legal():
    print "done by me."
    print "2016."
    print "huehuehue."
