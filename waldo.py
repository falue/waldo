#!/usr/bin/python
# -*- coding: utf-8 -*-

from Adafruit_PWM_Servo_Driver import PWM
import time
import sys
from os import system
import os
import threading
from threading import Thread
import serial
from shutil import copyfile

# ===========================================================================
# WALDO
# ===========================================================================

# pfad zu verzeichnis
mainpath = os.path.dirname(os.path.realpath(__file__))

# Initialise the PWM device using the default address
servoname = PWM(0x40)
# Note if you'd like more debug output you can instead run:
#pwm = PWM(0x40, debug=True)

servoMin = 250  # Min pulse length out of 4096 (150)
servoMax = 350  # Max pulse length out of 4096(600)
ruheposition = servoMin
# 0.0585 recording
step = 0.0570	# replaying time sleep zwischen schritte >5ms weil recording-step >5ms

recording = False

# ===========================================================================
# FUNKTIONEN ALLGEMEIN
# ===========================================================================
def mapvalue(x, in_min, in_max, out_min, out_max):
  return (x-in_min) * (out_max+1-out_min) / ( in_max-in_min) + out_min

def getfilesize(size,precision=2):
  # http://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
  suffixes=['b','kb','mb','gb','tb']
  suffixIndex = 0
  if size < 1024 :
      return "%.*f%s"%(precision,size,suffixes[suffixIndex])
  else :
    while size >= 1024 and suffixIndex < 4:
      suffixIndex += 1 #increment the index of the suffix
      size = size/1024.0 #apply the division
      return "%.*f%s"%(precision,size,suffixes[suffixIndex])
      #return str(size) + suffixes[suffixIndex]

def usbdetection() :
    print "Please unplug and replug desired usb device."
    print "Listening to USB ports..."
    usb_detected = False
    usbdevices = os.popen("ls /dev/tty*").read().strip().split("\n")
    #print "start: ",
    #print len(usbdevices)

    while usb_detected == False :
       if len(usbdevices)+1 == len(os.popen("ls /dev/tty*").read().strip().split("\n")) :
           usbdevice = "".join(set(os.popen("ls /dev/tty*").read().strip().split("\n")).symmetric_difference(usbdevices))
           print "USB device detected; yours is @ '" + usbdevice + "'."
           print "Set baudrate:"
           print "[300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200] & [return]"
           baudrate = raw_input()
           usb_detected = True
           return usbdevice + " " + baudrate
       else :
           usbdevices = os.popen("ls /dev/tty*").read().strip().split("\n")
           #print len(usbdevices)
       
       time.sleep(0.25)

# ===========================================================================
# PLAYBACKS
# ===========================================================================
def playback_audio(audiofile):
  global recording
  recording = True
  #global mainpath # path als global deklarieren
  # song abspielen
  #print "funktion file: "+audiofile
  system('play '+audiofile+' -q') # invoke 'sox' in quiet mode
  recording = False
  print "Audio stopped:\t"+audiofile

def playback_servo(projectname, channelname):
  global mainpath # path als global deklarieren
  global step
  global recording
  print "Channelname:\t"+channelname
  #print servopin
  
  # files open
  pulses_list = open(mainpath+"/projects/"+ projectname + "/" + channelname, "r") # datei zum lesen öffnen
  pulses = []

  # fill list with file
  for line in pulses_list:
    # pulses.append(int(line))
    if line.strip().isdigit() :
      pulses.append(mapvalue(int(line), 0, 1024, servoMin, servoMax))
    else :
      #print line
      getservopin = line.split("\t")
      servopin = int(getservopin[1])
      
  pulses_list.close()

  print "Servopin:\t",
  #getservopin = pulses_list[0] #.split("\t")
  #servopin = getservopin[1]
  print servopin
  print "Pulses:"
  print pulses

  def setServoPulse(channel, pulse):
    pulseLength = 1000000                   # 1,000,000 us per second
    pulseLength /= 60                       # 60 Hz
    print "%d us per period" % pulseLength
    pulseLength /= 4096                     # 12 bits of resolution
    print "%d us per bit" % pulseLength
    pulse *= 1000
    pulse /= pulseLength
    servoname.setPWM(channel, 0, pulse)

  servoname.setPWMFreq(60)                        # Set frequency to 60 Hz

  # servo bewegen
  print "Servo start:"
  for pulse in pulses:
    if recording : # an sich safety für wenn sound nicht läuft...
      servoname.setPWM(servopin, 0, pulse)
      print "Pin "+str(servopin) +":\t" + str(pulse)
      time.sleep(step)
    #else :
    #  print "Not recording."
  servoname.setPWM(servopin, 0, ruheposition)
  print "Servo playback stopped:\t"+ channelname
  #time.sleep(1)

# ===========================================================================
# RECORD
# ===========================================================================
def record(projectname, channelname, servopin, path_song) :
  global recording
  global mainpath # path als global deklarieren
  global step
  global servoMin
  global servoMax

  # listen to USB
  with open(mainpath + "/config", 'r') as usbconfig:
    connection=usbconfig.read().replace('\n', '\t')

  usbdevice = connection.split("\t")
  usbport = usbdevice[1]
  baudrate = int(usbdevice[3])
  #print usbdevice
  
  #ser = serial.Serial(usbdevice[0], int(usbdevice[1]))
  print "USB port: '" + usbport + "' @",
  print baudrate,
  print "baud"

  print "start recording in..."
  time.sleep(1)
  print "3"
  time.sleep(1)
  print "2"
  time.sleep(1)
  print "1"
  time.sleep(1)
  print "Start!"

  #play audio...
  if path_song :
    processThread0 = threading.Thread(target=playback_audio, args=(path_song,)); # <- note extra ','
    processThread0.start();
  else :
    recording = True
  
  # record!
  recordfile = open(mainpath + "/projects/"+projectname+"/"+channelname, 'w+')
  recordfile.write("Pin:\t"+servopin+"\n")
  last_record = "0"
  while recording == True :
    millis = time.time()
    # python: listen to usb port...? ---> MCP3008...
    ser = serial.Serial(usbport, baudrate)
    serial_line = str(ser.readline().strip()).split("#") # read serial input by arduino, delete carriage return and errors while transmitting
    #print serial_line
    if len(serial_line) == 3 :
      record = serial_line[1]
    else :
      record = last_record
      print ''.join(serial_line)+"\t[interpolated "+str(record)+"]"

    if record.isdigit() :
      recordfile.write(record+"\n") # write 0-1024 in file...
      print record, # 0-1024
      last_record = record
      record = mapvalue(int(record), 0, 1024, servoMin, servoMax) # map value to sevo values
      servoname.setPWM(int(servopin), 0, record) # move servo
      print "\t",
      print record # servoMin - servoMax
    millis = time.time()-millis
    if millis > step :
      millis = 0
    #print millis
    time.sleep(step-millis)

  recordfile.close()
  print "Recording ended."
  print "Recorded file '"+ channelname +"' is " + getfilesize(os.path.getsize(mainpath + "/projects/"+projectname+"/"+channelname), 2) + " heavy."


# ===========================================================================
# MAIN
# ===========================================================================

# get arguments from bash command line
arg = []
for arguments in sys.argv:
  arg.append(arguments)

if arg[1] == "h" :
  # HELP
  with open(mainpath + "/help", 'r') as helpfile:
    print helpfile.read() #.replace('\n', '')
  helpfile.close()
  
elif arg[1] == "usb":
  # CHANGE USB CONNECTION
  connection = usbdetection().split()
  usbdevice = connection[0]
  baudrate = connection[1]
  usb = open(mainpath + "/config", 'w+') #------------------------------- w+?
  usb.write("usb port:\t"+usbdevice+"\nbaudrate:\t"+baudrate)
  usb.close()
  print "New USB connection saved."
  
elif arg[1] == "r":
  # RECORD
  if not os.path.exists(mainpath + "/projects/"+arg[2]):
    os.mkdir (mainpath + "/projects/"+arg[2])
    os.mkdir (mainpath + "/projects/"+arg[2]+"/audio")
    os.mkdir (mainpath + "/projects/"+arg[2]+"/trash")
    
  # check file
  if os.path.isfile(mainpath + "/projects/"+arg[2]+"/"+arg[3]) == True :
    # überschreiben?
    print "'"+arg[3]+"' existiert bereits. Überschreiben? [Y/N]"
    answer = raw_input().lower()

    if answer == "y" :
      # mache backup von zu überschreibender datei...
      copyfile(mainpath + "/projects/"+arg[2]+"/"+arg[3], mainpath+"/projects/"+arg[2]+"/trash/"+time.strftime("%y-%m-%d_%H:%M:%S")+"_"+arg[3])
      if len(arg) > 5 :
        record(arg[2], arg[3], arg[4], mainpath+"/projects/"+arg[2]+"/audio/"+arg[5])
      else :
        record(arg[2], arg[3], arg[4], "")
    elif answer == "n" :
      print "Abbruch."
    else :
      print "[Y/N] motherfucker."
  else :
      if len(arg) > 5 :
        record(arg[2], arg[3], arg[4], mainpath+"/projects/"+arg[2]+"/audio/"+arg[5])
      else :
        record(arg[2], arg[3], arg[4], "")
        


elif arg[1] == "sp" :
  # SINGLE PLAY
  print "Play single servo."
  print "Projektname:\t"+arg[2]
  #print arg
  if __name__ == '__main__':
    # play audio thread when set: 
    if len(arg) > 4 :
      processThread0 = threading.Thread(target=playback_audio, args=(mainpath+"/projects/"+arg[2]+"/audio/"+ arg[4],)); # <- note extra ','
      processThread0.start();
    #else :
    #  recording = True
    # play servo thread:
    processThread1 = threading.Thread(target=playback_servo, args=(arg[2], arg[3],)); # <- note extra ','
    processThread1.start();

elif arg[1] == "p" :
  # PLAY ALL
  # arg[2] == projektfoldername
  print "Play everything."
  # play audio thread when set:

  audiofile = os.listdir(mainpath+"/projects/"+arg[2]+"/audio/")  
  
  if audiofile[0] :
    processThread0 = threading.Thread(target=playback_audio, args=(mainpath+"/projects/"+arg[2]+"/audio/"+ audiofile[0],)); # <- note extra ','
    processThread0.start();

  # read folder...
  playchannels = os.listdir(mainpath+"/projects/"+arg[2]+"/")

  for channel in playchannels :
    if channel != "audio" and channel != "trash" :
      #with open(mainpath+"/projects/"+arg[2]+"/"+channel, "r") as f :
      #  firstline = f.readline().strip().split("\t")
      #servopin = firstline[1]
      #print channel +":\t Servopin: "+ servopin
      print channel
      # play servo thread:
      processThread1 = threading.Thread(target=playback_servo, args=(arg[2], channel,)); # <- note extra ','
      processThread1.start();

elif arg[1] == "ls" :
  # LIST POJECTS AND CHANNELS
  print "List every channel in every project.\n"
  # read folder...
  projects = os.listdir(mainpath+"/projects/")
  
  for project in projects :
    print project+":"
    playchannels = os.listdir(mainpath+"/projects/"+project+"/")

    for channel in playchannels :
      #print "\t->"+channel
      if channel != "audio" and channel != "trash" :
        with open(mainpath+"/projects/"+project+"/"+channel, "r") as f :
          firstline = f.readline().strip().split("\t")
        if len(firstline) > 1 :
          servopin = firstline[1]
        else :
          servopin = "?"
        print "  ↳ "+channel +"\t[Pin "+ servopin+"]"
      elif channel == "audio" :
        audios = os.listdir(mainpath+"/projects/"+project+"/audio")
    firstline = []

    for audio in audios :
      print "  audio: "+audio
    print ""
    
elif arg[1] == "c":
  # COPYRIGHT
  print "done by me."
  print "2016."
  print "huehuehue."
    
else :
  # what?
  print "How did you do that? Type 'python waldo.py h' for help."





      
