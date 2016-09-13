#!/usr/bin/python
# -*- coding: utf-8 -*-

# ===========================================================================
# WALDO
# ===========================================================================

# from Adafruit_PWM_Servo_Driver import PWM
from Adafruit_MotorHAT.Adafruit_PWM_Servo_Driver import PWM
import time
import sys
# from os import system
import os
import threading
# from threading import Thread
import serial
from shutil import copyfile
from waldo_fn import *

# ===========================================================================
# MAIN VARIABLES
# ===========================================================================

# path to main dir
mainpath = os.path.dirname(os.path.realpath(__file__))

servoname = PWM(0x40)  # Initialise the PWM device using the default address
servoMin = 250  # Min pulse length out of 4096 (150)
servoMax = 350  # Max pulse length out of 4096(600)
ruheposition = servoMin

step = 0.0570  # time.sleep between sevo steps
# step_recording =  0.0585 # recording takes longer than playback...

recording = False


# ===========================================================================
# MAIN
# ===========================================================================

# if primay/first executed file from bash is waldo.py
if __name__ == '__main__':
    # get arguments from bash command line
    # pobably use 'click' for that
    # -----> every statement to seperate function
    arg = []
    for arguments in sys.argv:
        arg.append(arguments)

    if arg[1] == "h":
        # HELP
        # Read/print help file
        with open(mainpath + "/help", 'r') as helpfile:
            print helpfile.read()  # .replace('\n', '')
        helpfile.close()

    elif arg[1] == "usb":
        # CHANGE USB CONNECTION
        # Listen to USB port and write it in config file
        connection = usbdetection().split()
        usbdevice = connection[0]
        baudrate = connection[1]
        usb = open(mainpath + "/config",
                   'w+')
        usb.write("usb port:\t" + usbdevice + "\nbaudrate:\t" + baudrate)
        usb.close()
        print "New USB connection saved."

    elif arg[1] == "r":
        # RECORD
        # play audio, listen to USB port, follow with single servo and store data in file
        if not os.path.exists(mainpath + "/projects/" + arg[2]):
            os.mkdir(mainpath + "/projects/" + arg[2])
            os.mkdir(mainpath + "/projects/" + arg[2] + "/audio")
            os.mkdir(mainpath + "/projects/" + arg[2] + "/trash")

        # file exists?
        if os.path.isfile(mainpath + "/projects/" + arg[2] + "/" + arg[3]) == True:
            # overwite?
            print "'" + arg[3] + "' existiert bereits. Überschreiben? [Y/N]"
            answer = raw_input().lower()

            if answer == "y":
                # backup file in 'trash'
                copyfile(mainpath + "/projects/" + arg[2] + "/" + arg[3],
                         mainpath + "/projects/" + arg[2] + "/trash/" +
                         time.strftime("%y-%m-%d_%H:%M:%S") + "_" + arg[3])
                # Audiofile-arg submitted?
                if len(arg) > 5:
                    # overwrite and record with playing audio
                    record(arg[2], arg[3], arg[4],
                           mainpath + "/projects/" + arg[2] + "/audio/" + arg[5])
                else:
                    # overwrite and record without playing audio
                    record(arg[2], arg[3], arg[4], "")
            elif answer == "n":
                print "Abbruch."
            else:
                print "[Y/N] motherfucker."
        else:
            if len(arg) > 5:
                # record with playing audio
                record(arg[2], arg[3], arg[4],
                       mainpath + "/projects/" + arg[2] + "/audio/" + arg[5])
            else:
                # record without playing audio
                record(arg[2], arg[3], arg[4], "")

    elif arg[1] == "sp":
        # SINGLE PLAY
        # Play audio file and single servo
        print "Play single servo."
        print "Projektname:\t" + arg[2]
        #print arg
        # play audio thread when set:
        if len(arg) > 4:
            processThread0 = threading.Thread(
                target=playback_audio,
                args=(mainpath + "/projects/" + arg[2] + "/audio/" + arg[4], ))
            # <- note extra ','
            processThread0.start()
        #else :
        #  recording = True
        # play servo thread:
        processThread1 = threading.Thread(
            target=playback_servo, args=(arg[2],
                                         arg[3], ))
        # <- note extra ','
        processThread1.start()

    elif arg[1] == "p":
        # PLAY ALL
        # Play audio file and playback all servos there are
        # arg[2] == projektfoldername
        print "Play everything."

        # play audio thread when set:
        audiofile = os.listdir(mainpath + "/projects/" + arg[2] + "/audio/")
        if audiofile[0]:
            processThread0 = threading.Thread(
                target=playback_audio,
                args=(
                    mainpath + "/projects/" + arg[2] + "/audio/" + audiofile[0], ))
            # <- note extra ','
            processThread0.start()

        # read folder...
        playchannels = os.listdir(mainpath + "/projects/" + arg[2] + "/")

        # 'detect' servo pulse files
        for channel in playchannels:
            if channel != "audio" and channel != "trash":
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
                    target=playback_servo, args=(arg[2],
                                                 channel, ))
                # <- note extra ','
                processThread1.start()

    elif arg[1] == "ls":
        # LIST POJECTS AND CHANNELS
        # print overview for all pojects including channels/servoPin connection
        print "List every channel in every project.\n"

        # read folder...
        projects = os.listdir(mainpath + "/projects/")

        for project in projects:
            print project + ":"
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
                    print "  ↳ " + channel + "\t[Pin " + servopin + "]"
                elif channel == "audio":
                    audios = os.listdir(mainpath + "/projects/" + project +
                                        "/audio")
            firstline = []
            for audio in audios:
                print "  audio: " + audio
            print ""

    elif arg[1] == "c":
        # COPYRIGHT
        print "done by me."
        print "2016."
        print "huehuehue."

    else:
        # what?
        print "How did you do that? Type 'waldo.py h' for help."
