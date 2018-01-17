import RPi.GPIO as GPIO
import time, datetime, os

#######################
#    Configuration    #
#######################

# Time between measurements
waitingTime = 0.1

# Number of measurements
numberOfMeasurements = 5


#######################
#     Code Starts     #
#######################

# Button pin setup
GPIO.setmode(GPIO.BCM)
button_pin = 19
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Power Led pin setup
led_primary_pin = 16
GPIO.setup(led_primary_pin, GPIO.OUT)
GPIO.output(led_primary_pin, True)

signalValues = [True for i in range(numberOfMeasurements)]

while True:
    input_state = GPIO.input(button_pin)
    signalValues.pop(0)
    signalValues.append(input_state)
    if signalValues.count(False) >= 3:
        print('Shutdown button pressed')
        os.system("sudo shutdown now -h")
    time.sleep(waitingTime)
