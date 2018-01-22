#!/bin/bash
# use modifier '(...)waldo/waldo.py -ap tracknumber &' to autoplay when startup RasPi
sudo -u pi /home/pi/Scripts/waldo/waldo.py -ap 1 &
sudo -u pi /home/pi/Scripts/waldo/shutdown_button.py &
sudo -u pi /home/pi/Scripts/waldo/numpad_listener.py &