#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import time
import datetime


def measure_temp():
    temp = os.popen("vcgencmd measure_temp").readline()
    temp = temp.replace("temp=", "")
    temp = float(temp.replace("'C", ""))
    time = datetime.datetime.now().strftime('%a, %Y-%m-%d %H:%M:%S')
    visual = int(temp)/10 * "█"

    return time, "\t", str(temp) + '°C', "\t", visual


while True:
    data = ""
    for m in measure_temp():
         data += str(m)

    print data
    data += "\n"
    file = open("/home/pi/Scripts/waldo/logs/temperature.log", "a")
    file.write(data)
    file.close()
    time.sleep(60)
