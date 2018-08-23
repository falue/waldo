# -*- coding: utf-8 -*-
# Import fake library if not @ RaspberryPi
import bisect
import logging
from time import sleep, time

from waldo.utils import threaded

try:
    from Adafruit_MotorHAT.Adafruit_PWM_Servo_Driver import PWM
except ImportError:
    from fake import PWM

logger = logging.getLogger(__name__)


class Servo(object):
    def __init__(self, servo_number, start_pos=300):
        self.servo_number = servo_number
        self.start_pos = start_pos
        self.servo_pin, self.servo_hat_address = self._get_servo_connection(servo_number)
        self.servo_obj = PWM(self.servo_hat_address)
        self.servo_obj.setPWMFreq(50)  # 60hz = 16.666ms, 50hz = 20ms, 40hz = 25ms

    def turn_off(self):
        self.servo_obj.setPWM(self.servo_pin, 0, 4096)

    def set_pos(self, new_pos):
        logger.debug('Servo {}\tgoing to {}'.format(self.servo_pin, new_pos))
        self.servo_obj.setPWM(channel=self.servo_pin, on=0, off=new_pos)  # new generation servos check only total
                                                                          # length of duty cycle

    @staticmethod
    def _get_servo_connection(servo_pin):
        """
        Returns servo pins as int and servo hat board address as hex.
        """
        hat_address = servo_pin / 16
        servo_pin %= 16

        hat_address = int(hex(64 + hat_address), 16)

        return servo_pin, hat_address


class ServoChannel(object):
    def __init__(self, channel_file_path, servo_number, map_min, map_max, start_pos):
        self.pulse_list = None
        self.servo = None
        self.ready = False
        self.running = False
        self.servo_number = servo_number
        self.map_min = map_min
        self.map_max = map_max
        self.start_pos = start_pos
        self.channel_file_path = channel_file_path
        self.read_channel_file(channel_file_path)

    @threaded
    def read_channel_file(self, channel_file_path):
        with open(channel_file_path, 'r') as pulse_file:
            self.pulse_list = []
            for line in pulse_file.readlines():
                timestamp, value = line.split(': ')
                self.pulse_list.append((float(timestamp), int(value)))
        self.ready = True

    @threaded
    def play(self, play_from=0):
        self.servo = Servo(self.servo_number)

        start_time = time()
        self.running = True

        while self.running:
            try:
                now = time()
                timestamp, pulse = self._get_value(self.pulse_list, now - start_time + play_from)
                pulse_map = map_value(pulse, 0, 1024, self.map_min, self.map_max)
                self.servo.set_pos(pulse_map)
                logger.debug("Channel: {}\tTimestamp: {}\tPulse: {}\tPulse_map: {}\tServo pin: {}".format(self.channel_file_path,
                                                             timestamp,
                                                             pulse,
                                                             pulse_map,
                                                             self.servo.servo_pin,
                                                             )
                            )
                sleep(0.005)  # TODO: Research
            except IndexError:
                self.stop()

    def stop(self):
        if self.servo:
            self.running = False
            self.servo.set_pos(self.start_pos)
            self.servo.turn_off()

    @staticmethod
    def _get_value(l, t):
        x = bisect.bisect_left(l, (t, None))

        if x == len(l) - 1:
            # Stop at last entry
            raise IndexError
        elif x < len(l) and l[x][0] == t:
            pass
        elif x > 0:
            x -= 1

        return l[x]


def map_value(x, in_min, in_max, out_min, out_max):
    """
    Map values from one range to another.
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(name)-12s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)  # DEBUG / INFO / WARNING

    channel = '/home/pi/waldo_projects/sine_test/sine'
    s = ServoChannel(channel, 0, 326, 494, 326)
    s.stop()
    s.play()

    while True:
        sleep(1)
