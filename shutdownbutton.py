
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
GPIO.setup(14, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Power Led pin setup
GPIO.setup(15, GPIO.OUT)
GPIO.output(15, True)

signalValues = [True for i in range(numberOfMeasurements)]

while True:
    input_state = GPIO.input(14)
    signalValues.pop(0)
    signalValues.append(input_state)
    if signalValues.count(False) >= 3:
        print('Shutdown button pressed')
        os.system("shutdown now -h")
    time.sleep(waitingTime)

