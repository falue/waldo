#!/bin/bash
sudo -u pi cp /home/pi/Scripts/waldo/config_backup /home/pi/Scripts/waldo/config
sudo -u pi /home/pi/Scripts/waldo/waldo.py -ap 0 &
sudo -u pi /home/pi/Scripts/waldo/shutdown_button.py &
sudo -u pi /home/pi/Scripts/waldo/numpad_listener.py