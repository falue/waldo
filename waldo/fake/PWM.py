import math


class PWM(object):
    def __init__(self, address=0x40, debug=False):
        self.address = address
        self.debug = debug

    def setPWMFreq(self, freq):
        prescaleval = 25000000.0  # 25MHz
        prescaleval /= 4096.0  # 12-bit
        prescaleval /= float(freq)
        prescaleval -= 1.0
        if self.debug:
            print "Setting PWM frequency to %d Hz" % freq
            print "Estimated pre-scale: %d" % prescaleval
        prescale = math.floor(prescaleval + 0.5)
        if self.debug:
            print "Final pre-scale: %d" % prescale

    def setPWM(self, channel, on, off):
        if self.debug:
            print "Channel: %s on: %s of: %s" % channel, on, off

    def setAllPWM(self, on, off):
        if self.debug:
            print "All channels on: %s of: %s" % on, off
