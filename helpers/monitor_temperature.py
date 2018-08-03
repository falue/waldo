#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import time
import datetime

date = datetime.datetime.now().strftime('%Y-%m-%d_%a')

def measure_temp():
    temp = os.popen("vcgencmd measure_temp").readline()
    temp = temp.replace("temp=", "")
    temp = float(temp.replace("'C", ""))
    time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    visual = int(temp)/5 * "█"

    return time, "\t", str(temp) + '°C', "\t", visual


while True:
    data = ""
    for m in measure_temp():
         data += str(m)

    file = open("/home/pi/Scripts/waldo/logs/temperature/"+date+".log", "a")
    file.write(data + "\n")
    file.close()
    time.sleep(60)
