#!/bin/bash
# use modifier '(...)scripts/remote.py -ap tracknumber &' to autoplay when startup RasPi
python /home/pi/Scripts/waldo/scripts/remote.py -ap 1 &
python /home/pi/Scripts/waldo/scripts/shutdown_button.py &
python /home/pi/Scripts/waldo/scripts/numpad_listener.py &
