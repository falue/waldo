# coding=utf-8
import logging
from time import sleep

import RPi.GPIO as GPIO

import servo

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

logger = logging.getLogger(__name__)


class Recorder(object):
    def __init__(self, analog_in=8):
        self.analog_in = analog_in
        self.mcp_chip = self.analog_in / 8
        self.mcp_in = self.analog_in % 8

        # MCP Analog in
        self.mcp = {
            0: {'clk': 4,  'cs': 27, 'miso': 17, 'mosi': 18},
            1: {'clk': 22, 'cs': 25, 'miso': 23, 'mosi': 24},
            2: {'clk': 5,  'cs': 13, 'miso': 6,  'mosi': 12},
        }

        for chip in self.mcp:
            # set up the SPI interface pins
            GPIO.setup(self.mcp[chip]['mosi'], GPIO.OUT)
            GPIO.setup(self.mcp[chip]['miso'], GPIO.IN)
            GPIO.setup(self.mcp[chip]['clk'], GPIO.OUT)
            GPIO.setup(self.mcp[chip]['cs'], GPIO.OUT)

    def read(self):
        passes = 80
        reading = 0
        for i in range(passes):
            reading += self._mcp_reading(self.mcp_in,
                                        self.mcp[self.mcp_chip]['clk'],
                                        self.mcp[self.mcp_chip]['mosi'],
                                        self.mcp[self.mcp_chip]['miso'],
                                        self.mcp[self.mcp_chip]['cs']
                                        )
            sleep(0.0001)
        return reading / passes

    def _mcp_reading(self, mcp_chip, clk, mosi, miso, cs):
        if (mcp_chip > 7) or (mcp_chip < 0):
            return False
        GPIO.output(cs, True)
        GPIO.output(clk, False)  # start clock low
        GPIO.output(cs, False)  # bring CS low

        mcp_chip |= 0x18  # start bit + single-ended bit
        mcp_chip <<= 3  # we only need to send 5 bits here
        for i in range(5):
            if mcp_chip & 0x80:
                GPIO.output(mosi, True)
            else:
                GPIO.output(mosi, False)
            mcp_chip <<= 1
            GPIO.output(clk, True)
            GPIO.output(clk, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
            GPIO.output(clk, True)
            GPIO.output(clk, False)
            adcout <<= 1
            if GPIO.input(miso):
                adcout |= 0x1

        GPIO.output(cs, True)
        adcout >>= 1  # first bit is 'null' so drop it
        return adcout


if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)  # DEBUG / INFO / WARNING

    r = Recorder(20)

    channel = '/home/pi/waldo_projects/sine_test/sine'
    # s = servo.ServoChannel(channel, 0, 0, 1024, 0)
    s = servo.Servo(0)
    # s.set_pos(512)

    while True:
        reading = r.read()
        # s.set_pos(reading)
        print("{}{}{}░".format(reading, ' ' * (5-len(str(reading))), "█" * (reading/5)))
        # sleep(0.001)  # 0.001
