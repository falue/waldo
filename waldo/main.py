#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ===========================================================================
# WALDO
# ===========================================================================

import os
import sys


from fn import (helpfile, set_connection, set_servo, record_setup, singleplay,
                play_all, newproject, listprojects, legal, GPIO)


# path to main dir



# ===========================================================================
# MAIN
# ===========================================================================

# if primay/first executed file from bash is waldo.py
if __name__ == '__main__':
    # keyboard interrupt fallback
    try:
        if sys.argv[1] == "-h" or sys.argv[1] == "--help":
            # HELP
            helpfile()

        elif sys.argv[1] == "-c" or sys.argv[1] == "--connection":
            # SET CONNECTION FOR RECORDING
            set_connection(sys.argv[2])

        elif sys.argv[1] == "-r" or sys.argv[1] == "--record":
            # RECORD
            record_setup(sys.argv)

        elif sys.argv[1] == "-ss" or sys.argv[1] == "--setservo":
            # RECORD
            set_servo(sys.argv[2], sys.argv[3])

        elif sys.argv[1] == "-sp" or sys.argv[1] == "--singleplay":
            # SINGLE PLAY
            singleplay(sys.argv)

        elif sys.argv[1] == "-p" or sys.argv[1] == "--play":
            # PLAY ALL
            try:
                play_all(sys.argv[2], sys.argv[3])
            except IndexError:
                play_all(sys.argv[2])

        elif sys.argv[1] == "-n" or sys.argv[1] == "--new":
            # CREATE NEW FOLDER SYSTEM
            newproject(sys.argv[2])


        elif sys.argv[1] == "-ls" or sys.argv[1] == "--list":
            # LIST PROJECTS AND CHANNELS
            try:
                listprojects(sys.argv[2])
            except IndexError:
                listprojects()

        elif sys.argv[1] == "-cc" or sys.argv[1] == "--copy":
            # COPYRIGHT
            legal()

        else:
            helpfile()

    except IndexError:
       helpfile()

    except KeyboardInterrupt:
        print "\nExit by user."
        # Set GPIO to default
        GPIO.cleanup()
