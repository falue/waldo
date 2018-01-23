#!/bin/bash
# use modifier '(...)waldo/waldo.py -ap tracknumber &' to autoplay when startup RasPi
sudo -u pi /home/pi/Scripts/waldo/scripts/remote.py -ap 1 &
sudo -u pi /home/pi/Scripts/waldo/scripts/shutdown_button.py &
sudo -u pi /home/pi/Scripts/waldo/scripts/numpad_listener.py &