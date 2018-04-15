#!/bin/bash

# this was started by autostart.py, but that doesnt make sense because then autostart
# is always running and getting terminated by this script.
# initially this script also copied a backup config file to the main folder,
# to make sure REC_REPL is always False on startup. This does now autostart.py.

while true; do

	ps -ef | grep autostart | grep -v grep > /dev/null
	RUNNING=$?

	if [[ "$RUNNING" -eq 1 ]]; then
		echo "WALDO CRASHED: restarting..."
		play /home/pi/Scripts/waldo/waldo/sounds/unexpected_shutdown.wav -q
		python /home/pi/Scripts/waldo/helpers/killall.py
		python /home/pi/Scripts/waldo/helpers/autostart.py &
	fi

	sleep 1
done
