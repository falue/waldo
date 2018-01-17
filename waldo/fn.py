#!/usr/bin/python
# -*- coding: utf-8 -*-
import bisect
import logging
import os
import threading
import time
import select
import sys
from shutil import copyfile

import RPi.GPIO as GPIO
import serial

from utils import (set_gpio_pins, read_config, write_config, mapvalue,
                   getfilesize, usbdetection, get_servo_connection,
                   get_mcp_connection, bar, get_first_file)

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.WARNING)  # DEBUG / INFO / WARNING
logger = logging.getLogger()





# Import fake library if not @ RaspberryPi
try:
    from Adafruit_MotorHAT.Adafruit_PWM_Servo_Driver import PWM
except ImportError:
    from fake import PWM

# Read preferences and set project folder path
PREFERENCES = read_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
PROJECT_PATH = os.path.expanduser(PREFERENCES["PROJECT_PATH"]) if not os.path.isdir('projects') else 'projects'

# Make project folder if inexistent
if not os.path.isdir(PROJECT_PATH):
    os.makedirs(PROJECT_PATH)

# Globals
REC_REPL = False
SERVO_READY = {}
SERVO_FREQ = 60


def playback_audio(audiofile, play_from=0):
    """
    Start audio playback.
    :param audiofile:
    :param play_from:
    :return:
    """
    global REC_REPL

    print "Audio start:\t%s" % audiofile

    # Play from beginning or play_from
    if play_from:
        bashcommando = 'play %s -q trim %s' % (audiofile, play_from)
    else:
        bashcommando = 'play %s -q' % (audiofile)

    os.system(bashcommando)  # invoke 'sox' in quiet mode

    REC_REPL = False
    print "Audio stop:\t%s" % audiofile


def wait_for_servos():
    """
    Wait for servos to initiate and set REC_REPL to True if they do so.
    :return:
    """
    global REC_REPL
    print 'Wait for all servos to be ready',

    # Wait for every servo to catch up
    while not REC_REPL:
        sys.stdout.write('.')
        sys.stdout.flush()
        if all(value == True for value in SERVO_READY.values()):
            print "\nAll servos ready."
            change_glob_rec_repl(True)
            REC_REPL = True
            return
        time.sleep(0.05)

def getValue(l, t):
    x = bisect.bisect(l, (t, None))
    if x < len(l) and l[x][0] == t:
        pass
    elif x > 0:
        x -= 1

    return l[x]


def playback_servo(project, channel, play_from=0):
    """
    Playback a single servo.
    :param project:
    :param channel:
    :param play_from:
    :return:
    """

    global SERVO_READY
    play_from = float(play_from)

    # TODO: function servo init?
    # servo_init(project, channel)

    # Read config data for channel
    config = read_config(os.path.join(PROJECT_PATH, project))
    servo_pin = config['channels'][channel]['servo_pin']
    map_min = config['channels'][channel]['map_min']
    map_max = config['channels'][channel]['map_max']
    start_pos = config['channels'][channel]['start_pos']

    # Get servo pin and set servo hat adress
    servo_connection = get_servo_connection(servo_pin)
    servo_pin = servo_connection['servo_pin']
    servo_obj = PWM(servo_connection['hat_adress'])
    servo_obj.setPWMFreq(SERVO_FREQ)  # Set frequency to 60 Hz

    logger.info("Channelname:\t%s\tServopin:\t%s\tStart @\t%ss" % (channel, servo_pin, play_from))

    # Fill pulse_list with pulses
    with open(os.path.join(PROJECT_PATH, project, channel), 'r') as pulse_file:
        pulse_list = []
        for line in pulse_file.readlines():
            timestamp, value = line.split(": ")
            pulse_list.append((float(timestamp), int(value)))

    # Cut beginning of tuple list when play_from is set
    # if play_from:
    #     play_from = float(play_from)
    #     del_before = bisect.bisect_left(pulse_list, (play_from, None))
    #     pulse_list = pulse_list[del_before:]

    logger.info("Servo ready:\t%s\t%s frames" %
                (servo_pin, len(pulse_list)))

    # Signal: this channel is ready to go!
    SERVO_READY.update({channel: True})

    # Wait for all other servos to catch on
    while not REC_REPL:
        time.sleep(0.05)

    start_time = time.time()

    # Replay
    while REC_REPL:
        try:
            now = time.time()
            # XXX
            #timestamp, pulse = pulse_list[bisect.bisect_right(pulse_list, (now - start_time + play_from, None))]
            timestamp, pulse = getValue(pulse_list, now - start_time + play_from)
            pulse_map = mapvalue(pulse, 0, 1024, map_min, map_max)
            servo_obj.setPWM(servo_pin, 0, pulse_map)
            logger.debug("{}\t{}\t{}\t{}\t{}{}".format(timestamp,
                                                       now - start_time - timestamp,
                                                       pulse,
                                                       servo_pin,
                                                       "\t" * servo_pin,
                                                       bar(pulse))
                         )
            time.sleep(0.005)  # TODO: Research
        except IndexError:
            pass

    # Finisehd playing, go to startpositions and cut connection to servo
    servo_start_pos(project, {channel})


def servo_init():
    # # Read config data for channel
    # config = read_config(os.path.join(PROJECT_PATH, project))
    # servo_pin = config['channels'][channel]['servo_pin']
    # map_min = config['channels'][channel]['map_min']
    # map_max = config['channels'][channel]['map_max']
    # start_pos = config['channels'][channel]['start_pos']
    #
    # # Get servo pin and set servo hat adress
    # servo_connection = get_servo_connection(servo_pin)
    # servo_pin = servo_connection['servo_pin']
    # servo_obj = PWM(servo_connection['hat_adress'])
    # servo_obj.setPWMFreq(SERVO_FREQ)  # Set frequency to 60 Hz
    pass


def servo_start_pos(project, channels=False):
    """
    Go to startpositions and cut connection to servo
    :param project:
    :param channels:
    :return:
    """

    # Read config data for channel
    config = read_config(os.path.join(PROJECT_PATH, project))

    # If channel is not submitted
    if not channels:
        channels = config['channels']

    # go to start and stop channels split because time.sleep is needed just once
    # go to start position
    for channel in channels:
        servo_pin = config['channels'][channel]['servo_pin']
        start_pos = config['channels'][channel]['start_pos']

        # Get servo pin and set servo hat adress
        servo_connection = get_servo_connection(servo_pin)
        servo_pin = servo_connection['servo_pin']
        servo_obj = PWM(servo_connection['hat_adress'])
        # servo_obj.setPWMFreq(SERVO_FREQ)  # Set frequency to 60 Hz

        servo_obj.setPWM(servo_pin, 0, start_pos)  # Go to start position
        logger.info('Servo playback to start: %s\tStart position: %d' % (channel, start_pos))
        # print 'Servo playback to start: %s\tStart position: %d' % (channel, start_pos)
    print "All servos moved to start_pos."

    time.sleep(0.35)

    # stop channels
    for channel in channels:
        servo_pin = config['channels'][channel]['servo_pin']

        # Get servo pin and set servo hat adress
        servo_connection = get_servo_connection(servo_pin)
        servo_pin = servo_connection['servo_pin']
        servo_obj = PWM(servo_connection['hat_adress'])
        # servo_obj.setPWMFreq(SERVO_FREQ)  # Set frequency to 60 Hz

        # Time for moving servo
        # servo_obj.setPWM(servo_pin, 4096, 0)  # completly off
        logger.info('Servo playback to start: %s' % (channel))
        # print 'Servo playback to die: %s' % (channel)
    print "All servos cut off."

    change_glob_rec_repl(False)


def change_glob_rec_repl(on_off):
    # set general global var to false
    PREFERENCES.update({'REC_REPL': on_off})
    write_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."), PREFERENCES)

def record(project, channel, audiofile):
    """
    Listen to USB port or analog input via MCP3008, follow with single servo and store data in file.
    :param project:
    :param channel:
    :param audiofile:
    :return:
    """
    # Set GPIO pins as used by mcp read/write pins
    set_gpio_pins(PREFERENCES)

    global REC_REPL  # really totally necessary

    # Read config data for channel
    config = read_config(os.path.join(PROJECT_PATH, project))
    servo_pin = config['channels'][channel]['servo_pin']
    map_min = config['channels'][channel]['map_min']
    map_max = config['channels'][channel]['map_max']

    # Get servo pin and set servo hat adress
    servo_connection = get_servo_connection(servo_pin)
    servo_pin = servo_connection['servo_pin']
    servo_obj = PWM(servo_connection['hat_adress'])

    # Define type of user-input
    if config['connection']['type'] == "usb":
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
        servo_obj.setPWMFreq(SERVO_FREQ)
        print "Connection via MCP3008 (%d %d %d %d)" % (CLK, MISO, MOSI, CS)

    # Countdown for slow recordists
    print "Start recording in..."
    time.sleep(1)
    print "3"
    time.sleep(1)
    print "2"
    time.sleep(1)
    print "1"
    time.sleep(1)
    print "Go!"
    time.sleep(0.1)

    # Get audio file name if existent
    if not audiofile:
        suffix = ('.wav', '.mp3', '.aiff')
        audiofile = get_first_file(os.path.join(PROJECT_PATH, project, 'audio'), suffix)


    # Play audio file
    if audiofile:
        processThread0 = threading.Thread(
            target=playback_audio,
            args=(os.path.join(PROJECT_PATH, project, 'audio', audiofile), ))
        processThread0.start()

    REC_REPL = True

    # Open channel file, get start time of recording
    record_file = open(os.path.join(PROJECT_PATH, project, channel), 'w+')
    start_time = time.time()

    # Record!
    while REC_REPL:
        # Listen to usb port or MCP3008
        if config['connection']['type'] == "usb":
            record = read_usb(usb_port, baudrate)
        else:
            record = read_mcp(mcp_in, CLK, MOSI, MISO, CS)

        # Playback on servo
        servo_value = mapvalue(int(record), 0, 1024, map_min,
                          map_max)  # map value to servo values
        servo_obj.setPWM(int(servo_pin), 0, servo_value)  # move servo
        # setServoPulse(int(servo_pin), record)

        # Recording to file
        record_file.write("%s: %s\n" % (time.time()-start_time, record))  # write timecode and 0-1024 in file...
        print "Servo %s:\t%s\t%s" % (servo_pin, record, bar(record))  # 0-1024

        # time.sleep(STEP)

    record_file.close()

    # Clean used GPIO pins
    if config['connection']['type'] == "mcp3008":
        GPIO.cleanup()

    print "Recording ended."

    # Get filesize of recorded file
    heavyness = getfilesize(os.path.getsize(os.path.join(PROJECT_PATH, project, channel)), 2)
    print "Recorded file '%s' is %s heavy." % (channel, heavyness)


# FIXME: USB Interface useful? functional?
def read_usb(usbport, baudrate):
    """
    Listen to USB port @ baudrate line by line from arduino with potentiometer.
    :param usbport:
    :param baudrate:
    :return:
    """
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
    """
    Read and return analog values of MCP3008 IC.
    :param adcnum:
    :param clockpin:
    :param mosipin:
    :param misopin:
    :param cspin:
    :return:
    """
    if (adcnum > 7) or (adcnum < 0):
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


def helpfile():
    """
    Read and print help file.
    """
    with open(os.path.join(os.path.dirname(__file__), 'help'), 'r') as f:
        print f.read()


def set_connection(project):
    """
    Pick USB port or MCP3008 as user interface and write it in config file.
    :param project:
    :return:
    """
    # If config exists, do append
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
    Set config file for project - MCPin, servo_pin, map_min, map_max, start_pos.
    :param project:
    :param channel:
    :param servo_pin:
    :return:
    """
    # Read channel config data
    config = read_config(os.path.join(PROJECT_PATH, project))

    # Create key 'channels' if inexistent
    if 'channels' not in config:
        config.update({'channels': {}})

    # Set default answers
    if channel not in config['channels']:
        default_mcp_in = 8
        default_servo_pin = 0
        default_map_min = 100
        default_map_max = 600
        default_start_pos = False
    else:
        default_mcp_in = config['channels'][channel]["mcp_in"]
        default_servo_pin = config['channels'][channel]["servo_pin"]
        default_map_min = config['channels'][channel]["map_min"]
        default_map_max = config['channels'][channel]["map_max"]
        default_start_pos =  config['channels'][channel]["start_pos"]

    # Questions, questions, questions!
    mcp_in = int(raw_input("%s:\nSet MCP3008 in pin [0-23] (Default: %s)\n" % (channel, default_mcp_in))
                 or default_mcp_in)

    servo_pin = int(raw_input("Set servo pin out pin [0-15] (Default: %s)\n" % (default_servo_pin))
                    or default_servo_pin)

    map_min = raw_input("Set minimum position [100-600] (Default: %s; 'm' for manual detection)\n" % (default_map_min))\
              or default_map_min
    if map_min == 'm':
        map_min = get_dof(mcp_in, servo_pin)
        # FIXME: Catch pressing enter and prevent next raw_input to get executed
        raw_input("")

    map_max = raw_input("Set maximum position [100-600] (Default: %s; 'm' for manual detection)\n" % (default_map_max))\
              or default_map_max
    if map_max == 'm':
        map_max = get_dof(mcp_in, servo_pin)
        # FIXME: Catch pressing enter and prevent next raw_input to get executed
        raw_input("")
    if not default_start_pos:
        default_start_pos = map_min

    start_pos = int(raw_input("Set start position [100-600] (Default: %s; map_min: %s)\n"
                              % (default_start_pos, map_min)) or default_start_pos)

    # Update config list
    config['channels'].update({channel: {
                'mcp_in': mcp_in,
                'servo_pin': servo_pin,
                'map_min': int(map_min),
                'map_max': int(map_max),
                'start_pos': start_pos
            }
        }
    )

    # Write to config
    write_config(os.path.join(PROJECT_PATH, project), config)


def get_dof(mcp_in, servo_pin):
    """
    Move servo, directly controlled via user input. Standard boundaries comply.
    On enter return of current value.
    :param mcp_in:
    :param servo_pin:
    :return:
    """

    # FIXME: USB connection should also work
    # FIXME: Actually useful for direct replay?

    mcp_connection = get_mcp_connection(mcp_in)
    CLK = mcp_connection['CLK']
    MOSI = mcp_connection['MOSI']
    MISO = mcp_connection['MISO']
    CS = mcp_connection['CS']
    mcp_in %= 8

    set_gpio_pins(PREFERENCES)

    servo_connection = get_servo_connection(servo_pin)
    servo_pin = servo_connection['servo_pin']
    servo_obj = PWM(servo_connection['hat_adress'])
    servo_obj.setPWMFreq(SERVO_FREQ)  # Set frequency to 60 Hz

    print "Press enter for returning value."

    while True:
        value = read_mcp(mcp_in, CLK, MOSI, MISO, CS)
        value = mapvalue(value, 0, 1024, 600, 100)
        # print value,
        servo_obj.setPWM(servo_pin, 0, value)
        # print "servo_obj.setPWM(%s, 0, %s)" % (servo_pin, value)
        # print "\r%s " % bar(value),
        print "%s %s" % (value, bar(value))
        time.sleep(0.05)

        # Exit loop when enter is pressed
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            print "Defined: %s" % value
            servo_obj.setPWM(servo_pin, 4096, 0)  # completly off
            GPIO.cleanup()
            return value
            break


def record_setup(arg):
    """
    Setup recording, check to copy/trash and overwrite existing files.
    :param arg:
    :return:
    """
    project = arg[2]
    channel = arg[3]

    # Audio file as argument?
    try:
        audio_file = arg[4]
    except IndexError:
        audio_file = False

    # Project folder exist?
    if not os.path.isdir(os.path.join(PROJECT_PATH, project)):
        new_project(project)

    # Channel file exist?
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
    Play single servo @ specific pin and occasional audio file.
    :param arg:
    :return:
    """
    # FIXME: Function can be integrated in 'playall()'

    global REC_REPL

    project = arg[2]
    channelname = arg[3]

    # Audiofile exists?
    try:
        audiofile = arg[4]
    except IndexError:
        audiofile = False

    print "Play single servo."

    # Play servo thread:
    process_thread_1 = threading.Thread(
        target=playback_servo,
        args=(project, channelname, )) # ^ note extra ','
    process_thread_1.start()

    wait_for_servos()

    if not audiofile:
        audiofile = get_first_file(os.path.join(PROJECT_PATH, project, 'audio'), ('.wav', '.mp3', '.aiff'))

    # Play audiofile
    if audiofile:
        process_thread_0 = threading.Thread(
            target=playback_audio,
            args=(os.path.join(PROJECT_PATH, project, 'audio', audiofile), )) # <- note extra ','
        process_thread_0.start()
    # else:
        # REC_REPL = True # if no audio


def play_all(project, play_from=0):
    """
    Setup play whole project: Start threads for audiofile and all servos.
    :param project:
    :param play_from:
    :return:
    """

    global SERVO_READY

    print "Play everything; start @ %ss" % play_from

    # Get data from channel config
    play_channels = read_config(os.path.join(PROJECT_PATH, project))
    # print play_channels

    # Start threads for playback all servos
    for channel, data in play_channels['channels'].iteritems():
        # print "%s --- %s" % (channel, data)
        # threading.Thread(target=playback_servo, args=(project, channel, play_from,), name='channel').start()
        process_thread_1 = threading.Thread(
            target=playback_servo,
            args=(project, channel, play_from,)
        )
        # ^ note extra ','
        SERVO_READY.update({channel: False})
        process_thread_1.start()

    wait_for_servos()

    # Get audiofile
    audiofile = get_first_file(os.path.join(PROJECT_PATH, project, 'audio'), ('.wav', '.mp3', '.aiff'))

    # Play audio thread when set:
    if audiofile:
        process_thread_0 = threading.Thread(
            target=playback_audio,
            args=(os.path.join(PROJECT_PATH, project, 'audio', audiofile),
                  play_from, ))
        # <- note extra ','
        process_thread_0.start()
    # else:
        # REC_REPL = True


def new_project(project_name):
    """
    Create new folder structure and setup congig file.
    :param project_name:
    :return:
    """
    # Get path
    path = os.path.join(PROJECT_PATH, project_name)

    # Path not existent?
    if not os.path.exists(path):
        os.makedirs(path)
        os.makedirs(os.path.join(path, 'audio'))
        os.makedirs(os.path.join(path, 'trash'))
        os.mknod(os.path.join(path, 'config'))

        print "Created new project structure."
        set_connection(project_name)
    else:
        print "╳  Project already exists."


def copy_channel(project, channel_old, channel_new, preserve_pin="pin_inc"):
    """
    Copies file channel_old to channel_new with matching config data. preserve pin copies
    servo pin 1:1 if true, if false increments the total amount of servo channels.
    :param project:
    :param channel_old:
    :param channel_new:
    :param preserve_pin:
    :return:
    """
    # Read config data for project
    config = read_config(os.path.join(PROJECT_PATH, project))

    # Check if new channel already exists
    if not os.path.isfile(os.path.join(PROJECT_PATH, project, channel_new)) \
            and not channel_new in config['channels']:
        # Copy old to new
        copyfile(os.path.join(PROJECT_PATH, project, channel_old),
                 os.path.join(PROJECT_PATH, project, channel_new))

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
        write_config(os.path.join(PROJECT_PATH, project), config)
        print "File and config data for new channel '%s' in project '%s' copied from '%s'." % (channel_new,
                                                                                               project,
                                                                                               channel_old)
    else:
        print "╳  File or config data for channel '%s' in project '%s' already exists." % (channel_new, project)


def list_projects(project=False):
    """
    List every or a single channel in every project and point out difficulties.
    :return:
    """
    # Read every folder or define specific
    if project:
        projects = [project]
        print "List every channel in project '%s' and point out difficulties.\n" \
              "-------------------------------------------------------------" % project
    else:
        filelist = os.listdir(PROJECT_PATH)
        projects = [a for a in filelist if not a.startswith(".")]
        print "List every channel in every project and point out difficulties.\n" \
              "-------------------------------------------------------------"
        print "There are no project folders in '%s'." % PROJECT_PATH

    # TODO: md5 hashing content of channels, find and mark duplicates

    # ignore archive
    if '_archive' in projects:
        projects.remove('_archive')
    pass

    # For each project to analyze
    for project in sorted(projects):
        ch = ""
        error = ""
        disturbence = []
        channelfiles_spec = []

        # Read config of channel
        play_channels = read_config(os.path.join(PROJECT_PATH, project))
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
                if not os.path.isfile(os.path.join(PROJECT_PATH, project, channel)):
                    error += "╳  No file '%s' for specs in config\n" % channel

                # Store channelname for later use
                channelfiles_spec.append(channel)

                # Calculate visual representation for max degrees of angular freedom
                dof_prepend = mapvalue(data['map_min'], 100, 600, 0, servo_dof_deg)
                dof_append =  servo_dof_deg-mapvalue(data['map_max'], 100, 600, 0, servo_dof_deg)
                dof = servo_dof_deg-dof_append-dof_prepend

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
                graph_rep = "░" * mapvalue(dof_prepend, 0, servo_dof_deg, 0, 60) + \
                            "█" * mapvalue(dof, 0, servo_dof_deg, 0, 60) + \
                            "░" * mapvalue(dof_append, 0, servo_dof_deg, 0, 60)

                # Correct table layout if long channel name
                if len(channel) < 8:
                    name_space = "\t"
                else:
                    name_space = ""

                # Sum up channel content
                ch += "%s\t%s%s\t%s\t%s\t%s\t%s\t%s°\n%s%s\n" % (channel, name_space, data['servo_pin'],
                                                                 data['mcp_in'], data['map_min'],
                                                                 data['map_max'], data['start_pos'], dof,
                                                                 graph_rep, reversed_channel)

            # Check if all channel files have corresponding config data specified
            channel_list = os.listdir(os.path.join(PROJECT_PATH, project))
            channelfiles = [a for a in channel_list if not a.startswith(".") and
                            not a == 'config' and
                            not a == 'trash' and
                            not a == 'audio']
            no_specs = "'\n╳  No specs in config for file '".join([item for item in channelfiles if item
                                                                  not in channelfiles_spec])
            if no_specs:
                error += "╳  No specs in config for file '%s'\n" % no_specs

            # Print table header
            thead = "channel\t\tservo\tmcp_in\tmap_min\tmap_max\tst._pos\t°DOF"
            print "%s:\n%s\n%s\n%s" % (project, error, thead, ch)

        else:
            print "%s\n╳  No channels in config file.\n" % project

        print "-------------------------------------------------------------\n"


def legal():
    print "==============================="
    print " _ _ _ _____ __    ____  _____ "
    print "| | | |  [] |  |  |    \|     | analog"
    print "| | | |     |  |__|  [] |  [] | digital"
    print "|_____|__||_|_____|____/|_____| pupeteering"
    print "_______________________________"
    print "By Fabian Lüscher 2016."
    print "http://www.filmkulissen.ch"
    print "With generous help of Ben Hagen. Thanks a bunch!"

