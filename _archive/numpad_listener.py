#!/usr/bin/env python
# -*- coding: utf-8 -*-
import keyboard
import time
# listening to numpad keystrokes and send matching commands

# pseudocode
#  keystroke 'integer': send commend & enter to waldo window
#  keystroke 'q': quit this script (so one can debug on Pi) -> run killall.py

print 'listening to keystrokes now!'


# keyboard.press_and_release('shift+s, space')
#
# keyboard.write('The quick brown fox jumps over the lazy dog.')
#
# # Press PAGE UP then PAGE DOWN to type "foobar".
# keyboard.add_hotkey('page up, page down', lambda: keyboard.write('foobar'))
#
# # Blocks until you press esc.
# keyboard.wait('esc')
#
# # Record events until 'esc' is pressed.
# recorded = keyboard.record(until='esc')
# # Then replay back at three times the speed.
# keyboard.play(recorded, speed_factor=3)
#
# # Type @@ then press space to replace with abbreviation.
# keyboard.add_abbreviation('@@', 'my.long.email@example.com')
# # Block forever.
# keyboard.wait()


# keyboard.wait('9')
# def test():
#     if is_pressed(57):
#         print keyboard.read_key()  # filter=<lambda>
#
#     time.sleep(0.25)
#     test()
#
#
#
# test()

#
def print_pressed_keys(e):
    # KeyboardEvent.scan_code
    # KeyboardEvent.name
    # event_type
    # print keyboard._pressed_events
    if e.event_type == 'down' and e.name != 'num lock':
        print e.scan_code, e.name, e.event_type
    # line = ', '.join(str(code) for code in keyboard._pressed_events)
    # # '\r' and end='' overwrites the previous line.
    # # ' '*40 prints 40 spaces at the end to ensure the previous line is cleared.
    # if line != '69':
    #     print('\r' + line)
    # print str(code) for code in keyboard._pressed_events

keyboard.hook(print_pressed_keys)
keyboard.wait()

# #
# while 1:
#     # keyboard.press_and_release('a')
#     keyboard.write(144)
#     time.sleep(0.5)
#

