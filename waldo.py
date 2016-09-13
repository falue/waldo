#!/usr/bin/python
# -*- coding: utf-8 -*-

# ===========================================================================
# WALDO
# ===========================================================================

import os
# from os import system
import serial
import sys
import threading
# from threading import Thread
import time
from Adafruit_MotorHAT.Adafruit_PWM_Servo_Driver import PWM # from Adafruit_PWM_Servo_Driver import PWM
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
    arg = []
    for arguments in sys.argv:
        arg.append(arguments)


    if arg[1] == "-h" or arg[1] == "--help":
        # HELP
        helpfile(mainpath)
        
    elif arg[1] == "-c" or arg[1] == "--connection":
        # SET CONNECTION FOR RECORDING
        setconnection()
        
    elif arg[1] == "-r" or arg[1] == "--record":
        # RECORD
        record_setup(mainpath, arg)
        
    elif arg[1] == "-sp" or arg[1] == "--singleplay":
        # SINGLE PLAY
        singleplay(mainpath, arg)
        
    elif arg[1] == "-p" or arg[1] == "--play":
        # PLAY ALL
        playall(mainpath, arg)
        
    elif arg[1] == "-ls" or arg[1] == "--list":
        # LIST PROJECTS AND CHANNELS
        listprojects(mainpath)

    elif arg[1] == "-cc" or arg[1] == "--copy":
        # COPYRIGHT
        legal()

    else:
        # SAY WHAT?
        print "How did you do that? Type 'waldo.py -h' for help."
