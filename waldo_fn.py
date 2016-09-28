#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from os import system
import RPi.GPIO as GPIO
import serial
import sys
import threading
# from threading import Thread
import time
from Adafruit_MotorHAT.Adafruit_PWM_Servo_Driver import PWM
# from Adafruit_PWM_Servo_Driver import PWM
from shutil import copyfile
from waldo_fn import *

# ===========================================================================
# MCP3008 CONFIG
# ===========================================================================

# set GPIO
GPIO.setmode(GPIO.BCM)

# standard mcp3008 connection pins
CLK = 18
MISO = 23
MOSI = 24
CS = 25

# set up the SPI interface pins
GPIO.setup(MOSI, GPIO.OUT)
GPIO.setup(MISO, GPIO.IN)
GPIO.setup(CLK, GPIO.OUT)
GPIO.setup(CS, GPIO.OUT)
# GPIO.setwarnings(False) # doesn't work

#mcp_connection = "CLK\t"+CLK+"\tMISO\t"+MISO+"\tMOSI\t"+MOSI+"\tCS\t"+CS
mcp_connection = "CLK\t%d\tMISO\t%d\tMOSI\t%d\tCS\t%d" % (CLK, MISO, MOSI, CS)

# ===========================================================================
# MAIN VARIABLES
# ===========================================================================

# PROBABLY DELETE ALL THIS AFTER GETTING RID OF GLOBALS

servoname = PWM(0x40)  # ServoHat no. 1
servoMin = 150  # Min pulse length out of 4096 (150)
servoMax = 275 # Max pulse length out of 4096(600)
# startposition = servoMin # defined in function by pulse[1]

# count_servo = 16  # just for step correction?! -> read channel =>count_servo

step = 0.0352  # pause in record, smoothest 0.02 orig 0.0570 (16*0.0022=0.0352)
step_playback = 0.032 # 1 servo @ 0.0022 # step - float(count_servo)/0.8 * 0.0022 # orig 0.0178 # recording takes longer than playback...  step - 0.00155

# @ 1  servo:  0.0022
# @ 3  servos: 0.032
# @ 8  servos: 0.0504~
# @ 16 servos: 0.05162


recording = False


# ===========================================================================
# FUNCTIONS: GENERAL
# ===========================================================================
def mapvalue(x, in_min, in_max, out_min, out_max):
    # map values fom one range into another
    return (x - in_min) * (out_max + 1 - out_min) / (in_max - in_min) + out_min


def getfilesize(size, precision=2):
    # human readable filesizes
    # http://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
    suffixes = ['b', 'kb', 'mb', 'gb', 'tb']
    suffixIndex = 0
    if size < 1024:
        return "%.*f%s" % (precision, size, suffixes[suffixIndex])
    else:
        while size >= 1024 and suffixIndex < 4:
            suffixIndex += 1
            size = size / 1024.0
            return "%.*f%s" % (precision, size, suffixes[suffixIndex])


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
            print "USB device detected; yours is @", usbdevice, "."
            print "Set baudrate:"
            print "[300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200] & [return]"
            baudrate = raw_input()
            usb_detected = True
            return "%s %s" % (usbdevice, baudrate)
        else:
            usbdevices = os.popen("ls /dev/tty*").read().strip().split("\n")
            # print len(usbdevices)
        time.sleep(0.25)


# ===========================================================================
# FUNCTIONS: PLAYBACKS
# ===========================================================================
def playback_audio(audiofile, play_from=0):
    # Playback audio
    global recording
    recording = True
    # print "funktion file: "+audiofile
    if play_from > 0:
        bashcommando = 'play %s -q trim %s' % (audiofile, play_from)
    else:
        bashcommando = 'play %s -q' % (audiofile)
    system(bashcommando)  # invoke 'sox' in quiet mode
    recording = False
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


def playback_servo(mainpath, projectname, channelname, play_from=0):
    # Playback single servo
    # global mainpath
    global step_playback  # wichtig
    global recording  # wichtig
    #print servopin

    # Open files with pulse data
    pulses_list = open(
        mainpath + "/projects/" + projectname + "/" + channelname,
        "r")  # open to read
    pulses = []

    # fill list with file
    for line in pulses_list:
        if line.strip().isdigit():
            pulses.append(mapvalue(int(line), 0, 1024, servoMin, servoMax))
        else:
            # print line
            getservopin = line.split("\t")
            servopin = int(getservopin[1])

    pulses_list.close()
    startposition = pulses[1]
    print "Channelname:\t%s\tServopin:\t%s\tStat @\t%s" % (channelname,
                                                           servopin, play_from)

    # getservopin = pulses_list[0] #.split("\t")
    # servopin = getservopin[1]
    # print servopin
    # print "Pulses:"
    # print pulses

    servoname.setPWMFreq(60)  # Set frequency to 60 Hz

    play_from_index = int(1.0 / step * float(play_from))  # steps to n seconds
    # Move servo
    print "Servo start:\t%s frames, start @ %s. frame" % (len(pulses),
                                                          play_from_index)
    # cut off beginning instants of list
    if play_from_index > 0:
        pulses = pulses[play_from_index:]

    for pulse in pulses:
        if recording:  # if poject is without sound...
            servoname.setPWM(servopin, 0, pulse)
            # setServoPulse(servopin, pulse)
            print "Pin %d\t%d" % (servopin, pulse)
            time.sleep(step_playback)  # compensation fo slow recording...
        # else :
        # print "Not recording."
    servoname.setPWM(servopin, 0,
                     startposition)  # <---- erster pulse = ruhepos.?
    # setServoPulse(servopin, startposition)
    print "Servo playback stopped: %s\tStart position: %d" % (channelname,
                                                              startposition)
    # Set GPIO to default
    GPIO.cleanup()


# ===========================================================================
# FUNCTIONS: RECORD
# ===========================================================================
def record(mainpath, projectname, channelname, servopin, path_song):
    # Listen to USB port and wite data into file
    global recording  # really totally necessary
    global step  # will get lost -> will be timed by default
    global servoMin  # will get lost -> will be defined in config file per project
    global servoMax  # will get lost -> will be defined in config file per project

    # listen to USB o mcp3008?
    with open(mainpath + "/projects/" + projectname + "/config",
              'r') as config:
        #connection = usbconfig.read().replace('\n', '\t')
        config_data = config.read()
    # print config_data
    config_rows = config_data.split("\n")
    connection = config_rows[0].split("\t")
    # print connection
    if connection[1] == "USB":
        usbport = connection[2]
        baudrate = int(connection[4])
        #print usbdevice
        #ser = serial.Serial(usbdevice[0], int(usbdevice[1]))
        print "USB port:", usbport, "@", baudrate, "baud"
    else:
        CLK = int(connection[3])
        MISO = int(connection[5])
        MOSI = int(connection[7])
        CS = int(connection[9])
        servoname.setPWMFreq(60)
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
    if path_song:
        processThread0 = threading.Thread(
            target=playback_audio, args=(path_song, ))
        # <- note extra ','
        processThread0.start()
    else:
        recording = True

    # record!
    recordfile = open(
        mainpath + "/projects/" + projectname + "/" + channelname, 'w+')
    recordfile.write("Pin:\t" + servopin + "\n")
    last_record = "0"

    while recording == True:
        millis = time.time()

        # python: listen to usb port or MCP3008...
        if connection[1] == "USB":
            record = read_usb(usbport, baudrate)
        else:
            record = read_mcp(0, CLK, MOSI, MISO, CS)
            #                 ^ channel 0-7 on Chip MCP3008!

        # recording to file...
        recordfile.write(str(record) + "\n")  # write 0-1024 in file...
        print record,  # 0-1024

        # playback on servo...
        record = mapvalue(int(record), 0, 1024, servoMin,
                          servoMax)  # map value to sevo values
        servoname.setPWM(int(servopin), 0, record)  # move servo
        # setServoPulse(int(servopin), record)
        print "\t%s" % record  # servoMin <-> servoMax

        millis = time.time() - millis
        if millis > step:
            millis = 0
        #print millis
        time.sleep(step - millis)

    recordfile.close()
    if connection[1] == "MCP":
        GPIO.cleanup()
    print "Recording ended."
    heavyness = getfilesize(
        os.path.getsize(mainpath + "/projects/" + projectname + "/" +
                        channelname), 2)
    print "Recorded file '%s' is %s heavy." % (channelname, heavyness)


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


def helpfile(mainpath):
    # Read/print help file
    with open(mainpath + "/help", 'r') as helpfile:
        print helpfile.read()  # .replace('\n', '')
    helpfile.close()


def setconnection(mainpath, project):
    global mcp_connection
    # Listen to USB port and write it in config file
    print "Set up connection with USB or analog input via MCP3008? [USB/MCP]"
    answer = raw_input().lower()

    config_list = open(mainpath + "/projects/" + project + "/config",
                       "r")  # open to read
    config_data = []

    # fill list with file
    for line in config_list:
        config_data.append(line.strip())
    # print config_data
    if len(config_data) <= 2:
        config_data = ["", ""]

    if answer == "usb":
        print "Connection set: USB"
        connection = usbdetection().split()
        usbdevice = connection[0]
        baudrate = connection[1]
        config_data[0] = "Connection:\tUSB\t%s\t@\t%s" % (usbdevice, baudrate)
        print "New connection saved."
    elif answer == "mcp":
        print "Connection set: MCP3008 %s" % (mcp_connection)
        config_data[0] = "Connection:\tMCP3008\t" + mcp_connection
        print "New connection saved."
    else:
        print "Either enter USB or MCP, pretty please."
    config_data[
        1] = "Name:\tGPIOin:\t->\tServopin:\tMapMin:\tMapMax:\tStartpoint:"
    configfile = open(mainpath + "/projects/" + project + "/config", 'w+')
    configfile.write("\n".join(config_data))
    configfile.close()


def record_setup(mainpath, arg):
    # print arg
    # play audio, listen to USB port, follow with single servo and store data in file
    newproject(mainpath, arg)

    # file exists?
    if os.path.isfile(mainpath + "/projects/" + arg[2] + "/" + arg[3]) == True:
        # overwite?
        print "'%s' already exists. Replace? [Y/N]" % arg[3]
        answer = raw_input().lower()

        if answer == "y":
            # backup file in 'trash'
            copyfile(mainpath + "/projects/" + arg[2] + "/" + arg[3],
                     mainpath + "/projects/" + arg[2] + "/trash/" +
                     time.strftime("%y-%m-%d_%H:%M:%S") + "_" + arg[3])
            # Audiofile-arg submitted?
            if len(arg) > 5:
                # overwrite and record with playing audio
                record(mainpath, arg[2], arg[3], arg[4],
                       mainpath + "/projects/" + arg[2] + "/audio/" + arg[5])
            else:
                # overwrite and record without playing audio
                record(mainpath, arg[2], arg[3], arg[4], "")
        elif answer == "n":
            print "Abort."
        else:
            print "[Y/N] murmel, murmel"
    else:
        if len(arg) > 5:
            # record with playing audio
            record(mainpath, arg[2], arg[3], arg[4],
                   mainpath + "/projects/" + arg[2] + "/audio/" + arg[5])
        else:
            # record without playing audio
            record(mainpath, arg[2], arg[3], arg[4], "")


def singleplay(mainpath, arg):
    # Play audio file and single servo
    print "Play single servo."
    global recording
    # print "Projektname:\t",arg[2]
    # print arg
    # play audio thread when set:
    if len(arg) > 4:
        processThread0 = threading.Thread(
            target=playback_audio,
            args=(mainpath + "/projects/" + arg[2] + "/audio/" + arg[4], ))
        # <- note extra ','
        processThread0.start()
    else :
      recording = True # if no audio
   
    # play servo thread:
    processThread1 = threading.Thread(
        target=playback_servo, args=(mainpath,
                                     arg[2],
                                     arg[3], ))
    # ^ note extra ','
    processThread1.start()


def playall(mainpath, arg):
    # Play audio file and playback all servos there are
    # arg[2] == projektfoldername

    if len(arg) == 4:
        play_from = arg[3]
    else:
        play_from = 0

    print "Play everything; start @ %ss" % play_from

    # play audio thread when set:
    audiofile = os.listdir(mainpath + "/projects/" + arg[2] + "/audio/")
    if len(audiofile) > 0:
        processThread0 = threading.Thread(
            target=playback_audio,
            args=(mainpath + "/projects/" + arg[2] + "/audio/" + audiofile[0],
                  play_from, ))
        # <- note extra ','
        processThread0.start()

    # read folder...
    playchannels = os.listdir(mainpath + "/projects/" + arg[2] + "/")

    # 'detect' servo pulse files
    for channel in playchannels:
        if channel != "audio" and channel != "trash" and channel != "config":
            #with open(mainpath+"/projects/"+arg[2]+"/"+channel, "r") as f :
            #  firstline = f.readline().strip().split("\t")
            #servopin = firstline[1]
            #print channel +":\t Servopin: "+ servopin
            #print "arg[2]:\t",
            #print arg[2]
            #print "\tchannel:\t"
            #print channel
            # play servo thread:
            processThread1 = threading.Thread(
                target=playback_servo,
                args=(mainpath,
                      arg[2],
                      channel,
                      play_from, ))
            # ^ note extra ','
            processThread1.start()


def newproject(mainpath, arg):
    if not os.path.exists(mainpath + "/projects/" + arg[2]):
        os.mkdir(mainpath + "/projects/" + arg[2])
        os.mkdir(mainpath + "/projects/" + arg[2] + "/audio")
        os.mkdir(mainpath + "/projects/" + arg[2] + "/trash")
        os.mknod(mainpath + "/projects/" + arg[2] + "/config")
        '''
        configfile = open(mainpath + "/projects/" + arg[2] + "/config", 'w+')
        configfile.write("standard")
        configfile.close()
        '''
        print "Created new project structure."
        setconnection(mainpath, arg[2])
    else:
        print "Project already exists."


def listprojects(mainpath):
    # print overview for all pojects including channels/servoPin connection
    print "List every channel in every project.\n------------------------------"

    # read folder...
    projects = os.listdir(mainpath + "/projects/")

    for project in projects:
        print "%s:" % project
        playchannels = os.listdir(mainpath + "/projects/" + project + "/")
        for channel in playchannels:
            #print "\t->"+channel
            if channel != "audio" and channel != "trash":
                with open(mainpath + "/projects/" + project + "/" + channel,
                          "r") as f:
                    firstline = f.readline().strip().split("\t")
                if len(firstline) > 1:
                    servopin = firstline[1]
                else:
                    servopin = "?"
                print "    ↳ %s\t[ %s ]" % (channel, servopin)
            elif channel == "audio":
                audios = os.listdir(mainpath + "/projects/" + project +
                                    "/audio")
        firstline = []
        for audio in audios:
            print "    ↳ audio:\t%s" % audio
        print "------------------------------"


def legal():
    print "done by me."
    print "2016."
    print "huehuehue."
