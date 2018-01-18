#!/bin/bash
sudo -u pi /home/pi/Scripts/waldo/waldo.py -ap 0 &
sudo -u pi /home/pi/Scripts/waldo/shutdown_button.py &
sudo -u pi /home/pi/Scripts/waldo/numpad_listener.py