#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import os
import subprocess
import time

from waldo.utils import threaded


@threaded
def monitor_temperature():
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
        temp = subprocess.check_output(['vcgencmd', 'measure_temp']).strip()
        temp = temp.replace('temp=', '')
        temp = float(temp.replace('\'C', ''))
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        visual = int(temp) / 5 * '█'

        output = '{}\t{}°C\t{}'.format(now, temp, visual)

        return output

    while True:
        data = measure_temp()
        with open('%s/../logs/temperature/%s.log' % (main_path, date), 'a') as f:
            f.write(data + '\n')
        time.sleep(60)


if __name__ == '__main__':
    monitor_temperature()
    while True:
        time.sleep(1)
