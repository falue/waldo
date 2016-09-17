#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ===========================================================================
# WALDO
# ===========================================================================

import os
import sys

import click

from fn import (helpfile, setconnection, record_setup, singleplay,
                playall, newproject, listprojects, legal, GPIO)


# path to main dir
mainpath = os.path.dirname(os.path.realpath(__file__))

# ===========================================================================
# MAIN
# ===========================================================================

# if primay/first executed file from bash is waldo.py
if __name__ == '__main__':
    # keyboard interrupt fallback
    try:
        # get arguments from bash command line
        arg = []
        for arguments in sys.argv:
            arg.append(arguments)

        if arg[1] == "-h" or arg[1] == "--help":
            # HELP
            helpfile(mainpath)

        elif arg[1] == "-c" or arg[1] == "--connection":
            # SET CONNECTION FOR RECORDING
            setconnection(mainpath, arg[2])

        elif arg[1] == "-r" or arg[1] == "--record":
            # RECORD
            record_setup(mainpath, arg)

        elif arg[1] == "-sp" or arg[1] == "--singleplay":
            # SINGLE PLAY
            singleplay(mainpath, arg)

        elif arg[1] == "-p" or arg[1] == "--play":
            # PLAY ALL
            playall(mainpath, arg)

        elif arg[1] == "-n" or arg[1] == "--new":
            # CREATE NEW FOLDER SYSTEM
            newproject(mainpath, arg)

        elif arg[1] == "-ls" or arg[1] == "--list":
            # LIST PROJECTS AND CHANNELS
            listprojects(mainpath)

        elif arg[1] == "-cc" or arg[1] == "--copy":
            # COPYRIGHT
            legal()

        else:
            # SAY WHAT?
            print "How did you do that? Type 'waldo.py -h' for help."

    except KeyboardInterrupt:
        print "\nExit by user."
        # Set GPIO to default
        GPIO.cleanup()
