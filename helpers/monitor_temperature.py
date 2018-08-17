#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import time
import datetime

main_path = os.path.dirname(os.path.realpath(__file__))

date = datetime.datetime.now().strftime('%Y-%m-%d_%a')

# Delete old logs
current_time = time.time()

for f in os.listdir('%s/../logs/temperature' % main_path):
    filepath = '%s/../logs/temperature/%s' % (main_path, f)
    creation_time = os.path.getctime(filepath)
    if (current_time - creation_time) // (24 * 3600) >= 20:
        os.unlink(filepath)
        print('%s removed.' % f)


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

    file = open("%s/../logs/temperature/%s.log" % (main_path, date), "a")
    file.write(data + "\n")
    file.close()
    time.sleep(60)
