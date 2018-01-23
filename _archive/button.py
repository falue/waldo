#!/usr/bin/env python
import time

from waldo.fn import read_mcp

CLK = 4
CS = 27
MISO = 17
MOSI = 18


def average():
    value = 0
    for i in range(10):
        value += read_mcp(0, CLK, MOSI, MISO, CS)
        time.sleep(0.05)
    return value / 10


def average_new():
    values = [read_mcp(0, CLK, MOSI, MISO, CS) for _ in range(9)]
    print sorted(values)
    return sorted(values)[4]


if __name__ == '__main__':

    while True:
        print average_new()
        time.sleep(1)