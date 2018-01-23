#!/bin/bash
# TODO: if autoplay is defined in main config start these scripts
# TODO: get autoplay button number from main config
python /home/pi/Scripts/waldo/waldo.py -ap 2 &
python /home/pi/Scripts/waldo/shutdown_button.py &
python /home/pi/Scripts/waldo/numpad_listener.py &