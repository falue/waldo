# Waldo and Rigby
1. [General Setup (using pi and waldo via SSH)](#general-setup-using-pi-and-waldo-via-ssh)
    - [Set fixed IP for raspberry pi](#set-fixed-ip-for-raspberry-pi)
    - [Set fixed IP for Laptop](#set-fixed-ip-for-laptop)
    - [Mount remote file system](#mount-remote-file-system)
    - [Raspberry Pi credentials](#raspberry-pi-credentials)
2. [Main commands](#main-commands)
    - [Set record connection type](#set-record-connection-type)
    - [Copyright](#copyright)
    - [Copy channel](#copy-channel)
    - [Help for main.py](#help-for-main.py)
    - [Listing of project folders](#listing-of-project-folders)
    - [Create new project](#create-new-project)
    - [Play an entire project](#play-an-entire-project)
    - [Record channel](#record-channel)
    - [Singleplay channel](#singleplay-channel)
    - [Recalibrate a servo](#recalibrate-a-servo) ([Requirements](#requirements)|[Steps](#steps))
3. [Helpers](#helpers)
    1. [remote.py: Remote commands](#remotepy-remote-commands)
        - [Use keyboard remote control](#use-keyboard-remote-control)
        - [Autostart](#autostart)
        - [(Re-)calibrate](#re-calibrate)
        - [Help for remote.py](#help-for-remotepy)
    2. [editor.py: Editor](#editorpy-editor)
        - [remover / adder](#remover-adder)
        - [Convenience functions](#convenience-functions)
    3. [killall.py: Exit every python script](#killallpy-exit-every-python-script)
4. [Rigby (remote keyboard)](#rigby-remote-keyboard)
    - [Setup](#setup)
    - [Main config file](#main-config-file)
5. [Setup as independent unit](#setup-as-independent-unit)
6. [Photos](#photos)


# General Setup (using pi and waldo via SSH)

## Set fixed IP for raspberry pi
1. Edit **/etc/dhcpcd.conf** , enable static ip config:
```
# Uncomment if you want to give static IP
interface eth0
static ip_address=192.168.0.4/24
static routers=192.168.0.1
static domain_name_servers=192.168.0.1
```
2. reboot

## Set fixed IP for Laptop
```
ifconfig enp0s25 192.168.0.5 netmask 255.255.255.0 up
```

## Mount remote file system
```
mkdir  remote_waldo
sshfs pi@192.168.0.4:/home/pi/tmp_waldo_projects remote_waldo/
```

## Raspberry Pi credentials
pi / 1234


# Main commands
Use the file `waldo/main.py` for recording, playing, analyzing a track, song or project.  
 
**Hint:** Some functionality may be broken if you don't `cd` in the main folder `waldo/`.
Honestly, i don't know exactly. Never tried.


## Set record connection type
```
python waldo/main.py -c projectname
```
Set potentiometer input type:  
Either via MCP chip (analog-digital translation to GPIO pins of RasPi) or
eg. an Arduino on a USB port which does the translation and can do other, more sophisticated calculations than a 
linear potentiometer could ever do.

## Copyright
```
python waldo/main.py -cc
```
Well, get copyright info.

## Copy channel
```
python waldo/main.py -cp projectName channelfilename_old channelfilename_new [pin_inc|pin_copy|pin_new]
```
Duplicate channel_old to channel_new in projectName and copy config data associated with
channel_old.  
Servo_pin gets either incremented by total channels + 1 `pin_inc` (default), copied from old
`pin_copy`, or gets user defined by integer value `pin_new`.
   
## Help for main.py
```
python waldo/main.py -h
```

## Listing of project folders
```
python waldo/main.py -ls [projectName]
```
List evey project (or a specific one with [projectname]) and every channel with their
servo-hat-pin-associations.  
Point out difficulties like multiple use of servo_pin or missing files or config data.  
Vizualize range of used servo degrees.  

Example output:  
```
python waldo/main.py -ls
List every channel in every project and point out difficulties.
-------------------------------------------------------------
test:
╳  No file 'sopran' for specs in config
╳  Multiple use of servo pin 3 (tenor)
╳  No specs in config for file
	channel		servo	mcp_in	map_min	map_max	st._pos	°DOF
	bariton		3	    8	    233	    302	    233	    13°
	░░░░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
	bass		6	    8	    160	    390	    160	    42°
	░░░░░░████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░
	sopran		4	    8	    120	    410	    120	    52°
	░░██████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░
	tenor		3	    8	    155	    444	    230	    52°
	░░░░░░██████████████████████████████████░░░░░░░░░░░░░░░░░░░

-------------------------------------------------------------

empty_test:
╳  No channels in config file.
-------------------------------------------------------------
```
Whereas `°DOF` is an attempt to calculate the physical 'degrees of freedom' of the servo.

## Create new project
```
python waldo/main.py -n projectName
```
Name your project what you want except 'cancel' - this cannot be replayed with Rigby keyboard.  
You can choose to duplicate an existing config file.  
Things you may want to do:
- Add audio file in path/to/project/audio (`.mp3`, `.wave`, `.aiff`)
- Delete channels that are not needed anymore from the config file
- Call setservo for all channels if the servos are not calibrated

## Play an entire project
Play every channel of projectName
```
python waldo/main.py -p projectName [start_offset_in_seconds]
```
Optional argument: Start after n seconds.

## Record channel
```
python waldo/main.py -r projectName channelName
```
If you record channelName with a not existing projectName, you will be guided to [create a new project](#create-new-project).

## Singleplay channel
```
python waldo/main.py -sp projectname channelfilename [audiofilename]
```
Playback of one specific servo in projectname through a specific servo. Optional specific audio
playback with [audiofilename] (if none is entered, alphabetical first in folder will play if
existent).

## Recalibrate a servo
This functionality is used to store the settings of a certain servo (e.g., of a box) for a certain channel within a certain project.

### Requirements:
1. Potentiometer is connected to the toprow of connectors (labelled 0-23), on Pin 8.
2. Servo to calibrate is connected to bottom-row, to one of the pins.

### Steps
(Servo on Pin 2, Potentiometer on Pin 8)

```
python waldo/main.py -ss /path/to/project channelName
Set MCP3008 Pin [default 8] # this is the potentiometer, you can just hit enter
Set Servo Pin [default 0]   # this is the servo pin, here use 2
Set minimum position:       # hit 'm' to set the value with the potentiometer
Set maximum position:       # hit 'm' to set the value with the potentiometer
Set start position:         # usually use the minimum position to start closed
```


# Helpers
Use any of these helpers for your convenience.  

**Hint:** Some functionality may be broken if you don't `cd` in the main folder `waldo/`.
Honestly, i don't know exactly. Never tried.

## remote.py: Remote commands
### Use keyboard remote control
To start using the analog keyboard Rigby or an USB (numpad) keyboard as a remote for playing or stopping any track, type
```
python helpers/remote.py
```
If you defined `numpad: true` in the main config file, you can use any regular computer keyboard
whereas the key numbers represent the button numbers defined in the main config file.

**Hint:** See [Rigby (remote keyboard)](#rigby-remote-keyboard) for setup analog keyboard Rigby.
### Autostart
```
python helpers/remote.py -ap [buttonNumber]
```
buttonNumber represents the button definition integer from the main config file. This track will start when the Pi starts up.

### (Re-)calibrate
Needs to be done when the cable connecting rigby and the pi has changed.
1. Kill running scripts/remote.py process
2. Calibrate:
```
python helpers/remote.py -cal
```
### Help for remote.py
```
python helpers/remote.py -h
```

## editor.py: Editor
```
python helpers/editor.py /path/to/project
```
### remover / adder
Switch between 'remover' and 'adder' mode.
* Adder (default after start of editor): clicking adds a point
* Remover: clicking removes the closest point
### Convenience functions
* Erase all: remove all added points from the editor.
* First/last to y = zero: changes the first and last point added by clicking to y = 0.
* add start/end: add a value at t = 0, and t = end_of_recording with y = 0 for both values.
* Save (needs to have channelName set in input field): write the new line to this channelName
* set same height (needs to have channelName set in input field): set last / first added point y value such, that they match the previously existing y value at that time.
* Merge (needs to have channelName set in input field): Merge the currently drawn line with the existing line (useful, if only a certain part of the curve needs to be changed).

## killall.py: Exit every python script
Handy after `autostart.py` startet some scripts and you want to kill them all. Also sets LED pins to false.

# Rigby (remote keyboard)
## Setup
1. Connect rigby with RJ-45 cable to special port on pi ('pin 0-5')
2. Boot pi


## Main config file
Button commands are stored in config file, the following config for example defines the first 10 buttons.  
Note the PROJECT_PATH on top: It gets ignored when the folder 'projects' in root exists - it will take 'projects' as Project path.

**Hint:** Any button can have the value 'cancel' to stop every ongoing track. Standard may be 30.  
Erase invalid comments in json file below when copy-pasting.

```json
PROJECT_PATH: /home/pi/waldo_projects   # define where your project folder is.
                                        # if folder 'waldo/projects' exists, this gets ignored.
                                        # DO NOT use '~' for user expanding; does not work when autostarting
REC_REPL: false   # Always false; just true if a track is being played. 
button_value:     # Calibrated values for analog keyboard Rigby (changes depending on the length of ethernet cable)
  0: 89
  1: 932
  2: 778
  3: 670
  4: 594
  5: 306
buttons:          # define buttons: key-number on USB numpad or button-number on Rigby, followed by bash commands to play songs
  1: -p s1_tonleiter_einzaehlen
  2: -p s23_teaser_variante_tonleiter
  3: -p s12_refrain_piano
  4: -p s4_variante_solostimmen
  5: -p s9_variante_lalala
  6: -p reset
  7: -p reset
  8: -p reset
  9: -p reset
  10: -p reset
  30: cancel      # Name a function of any button 'cancel' and you have yourself a cancel button
mcp:              # Leave alone if you use Mortekay as analog-digital transformer
  0:
    CLK: 4
    CS: 27
    MISO: 17
    MOSI: 18
  1:
    CLK: 22
    CS: 25
    MISO: 23
    MOSI: 24
  2:
    CLK: 5
    CS: 13
    MISO: 6
    MOSI: 12
numpad: true      # Set to true if you use USB keyboard to play tracks instead of Rigby
autostart: true   # Set to false if you dont want anything to start on startup.
                  # ^Set to true if you want to start remote.py, shutdown_button.py to start on RasPi startup
                  # ^Set to integer number of defined button to start any track on startup

```

# Setup as independent unit
Add the script `scripts/autostart.py` to the startup cycle of RasPi:
```
sudo nano /etc/rc.local
```
At the bottom (just before `exit 0`), note the following:
```
# Run WALDO
sudo -u pi python /home/pi/Scripts/waldo/helpers/autostart.py
```

It executes the following scripts:
- scripts/remote.py
    - Listens to numpad or analog play buttons
    - Use modifier '(...)scripts/remote.py -ap tracknumber &' to autoplay when startup RasPi
- scripts/shutdown_button.py
    - displays 'ready' indicator LED (pin 16) and listens to pushbutton (pin 19) 


# Photos
![](images/poti.jpg)  
^ Connecting the Potentiometer on Pin 8  

![](images/servos.jpg)  
^ Connecting servos on (pin 0 and 1)  

![](images/ethernet.jpg)  
^ Rigby (Ethernet on Pin 0-5)  
