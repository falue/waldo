#!/usr/bin/python
# -*- coding: utf-8 -*-

from Adafruit_MotorHAT.Adafruit_PWM_Servo_Driver import PWM
import os
import time
import serial


# ===========================================================================
# MAIN VARIABLES
# ===========================================================================

# PROBABLY DELETE ALL THIS AFTER GETTING RID OF GLOBALS

# path to main dir
mainpath = os.path.dirname(os.path.realpath(__file__))

servoname = PWM(0x40)  # Initialise the PWM device using the default address
servoMin = 250  # Min pulse length out of 4096 (150)
servoMax = 350  # Max pulse length out of 4096(600)
ruheposition = servoMin

step = 0.0570  # time.sleep between sevo steps
# step_recording =  0.0585 # recording takes longer than playback...


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
            return "%.*f%s" % (precision, size, suffixes[suffixIndex]
                               )  # return str(size) + suffixes[suffixIndex]


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
            print "USB device detected; yours is @ '" + usbdevice + "'."
            print "Set baudrate:"
            print "[300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200] & [return]"
            baudrate = raw_input()
            usb_detected = True
            return usbdevice + " " + baudrate
        else:
            usbdevices = os.popen("ls /dev/tty*").read().strip().split("\n")
            # print len(usbdevices)
        time.sleep(0.25)


# ===========================================================================
# FUNCTIONS: PLAYBACKS
# ===========================================================================
def playback_audio(audiofile):
    # Playback audio
    global recording
    recording = True
    # print "funktion file: "+audiofile
    system('play ' + audiofile + ' -q')  # invoke 'sox' in quiet mode
    recording = False
    print "Audio stopped:\t" + audiofile


def playback_servo(projectname, channelname):
    # Playback single servo
    global mainpath
    global step
    global recording
    #print servopin

    # Open files with pulse data
    pulses_list = open(mainpath + "/projects/" + projectname + "/" +
                       channelname, "r")  # open to read
    pulses = []

    # fill list with file
    for line in pulses_list:
        # pulses.append(int(line))
        if line.strip().isdigit():
            pulses.append(mapvalue(int(line), 0, 1024, servoMin, servoMax))
        else:
            # print line
            getservopin = line.split("\t")
            servopin = int(getservopin[1])

    pulses_list.close()

    print "Channelname:\t" + channelname + "\tServopin:\t" + str(servopin)

    # getservopin = pulses_list[0] #.split("\t")
    # servopin = getservopin[1]
    # print servopin
    # print "Pulses:"
    # print pulses

    def setServoPulse(channel, pulse):  # copypasta-überbleibsel...?
        pulseLength = 1000000  # 1,000,000 us per second
        pulseLength /= 60  # 60 Hz
        print "%d us per period" % pulseLength
        pulseLength /= 4096  # 12 bits of resolution
        print "%d us per bit" % pulseLength
        pulse *= 1000
        pulse /= pulseLength
        servoname.setPWM(channel, 0, pulse)

    servoname.setPWMFreq(60)  # Set frequency to 60 Hz

    # Move servo
    print "Servo start:"
    for pulse in pulses:
        if recording:  # if poject is without sound...
            servoname.setPWM(servopin, 0,
                             pulse)  # probably use function above...?
            print "Pin " + str(servopin) + ":\t" + str(pulse)
            time.sleep(step)
        #else :
        #  print "Not recording."
    servoname.setPWM(servopin, 0, ruheposition)
    print "Servo playback stopped:\t" + channelname
    #time.sleep(1)


# ===========================================================================
# FUNCTIONS: RECORD
# ===========================================================================
def record(projectname, channelname, servopin, path_song):
    # Listen to USB port and wite data into file
    global recording
    global mainpath  # path als global deklarieren
    global step
    global servoMin
    global servoMax

    # listen to USB
    with open(mainpath + "/config", 'r') as usbconfig:
        connection = usbconfig.read().replace('\n', '\t')
    usbdevice = connection.split("\t")
    usbport = usbdevice[1]
    baudrate = int(usbdevice[3])
    #print usbdevice

    #ser = serial.Serial(usbdevice[0], int(usbdevice[1]))
    print "USB port: '" + usbport + "' @",
    print baudrate,
    print "baud"

    # countdown for slow recordists
    print "start recording in..."
    time.sleep(1)
    print "3",
    time.sleep(1)
    print "\r2",
    time.sleep(1)
    print "\r1"
    time.sleep(1)
    print "Start!"

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
        # python: listen to usb port...? ---> MCP3008...
        ser = serial.Serial(usbport, baudrate)
        serial_line = str(ser.readline().strip()).split(
            "#")  # read serial input by arduino, delete carriage return and errors while transmitting
        #print serial_line
        if len(serial_line) == 3:
            record = serial_line[1]
        else:
            record = last_record
            print ''.join(serial_line) + "\t[interpolated " + str(record) + "]"

        if record.isdigit():
            recordfile.write(record + "\n")  # write 0-1024 in file...
            print record,  # 0-1024
            last_record = record
            record = mapvalue(int(record), 0, 1024, servoMin,
                              servoMax)  # map value to sevo values
            servoname.setPWM(int(servopin), 0, record)  # move servo
            print "\t",
            print record  # servoMin - servoMax
        millis = time.time() - millis
        if millis > step:
            millis = 0
        #print millis
        time.sleep(step - millis)

    recordfile.close()
    print "Recording ended."
    print "Recorded file '" + channelname + "' is " + getfilesize(
        os.path.getsize(mainpath + "/projects/" + projectname + "/" +
                        channelname), 2) + " heavy."
