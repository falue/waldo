# Waldo and Rigby
1. [General Setup (using pi and waldo via SSH)](#general-setup-using-pi-and-waldo-via-ssh)
    - [Powering raspberry pi](#powering-raspberry-pi)
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
    1. [audiotest.py: Test R&L channels](#audiotestpy-test-rl-channels)
    2. [autostart.py: Files on startup](#autostartpy-files-on-startup)
    3. [clean_channelfile.py: Compress old channelfiles](#clean_channelfilepy-compress-old-channelfiles)
    4. [crash_recover.sh: Quit & restart everything](#crash_recoversh-quit-restart-everything)
    5. [editor.py: Edit channel values](#editorpy-edit-channel-values)
        - [remover / adder](#remover-adder)
        - [Convenience functions](#convenience-functions)
    6. [killall.py: Exit every python script](#killallpy-exit-every-python-script)
    7. [monitor_temperature.py: Keep log of Core temperature](#monitor_temperaturepy-keep-log-of-core-temperature)
    8. [notify.sh: GUI alert](#notifysh-gui-alert)
    9. [remote.py: Remote commands](#remotepy-remote-commands)
        - [Use keyboard remote control](#use-keyboard-remote-control)
        - [Autoplay track on startup](#autoplay-track-on-startup)
        - [(Re-)calibrate](#re-calibrate)
        - [Help for remote.py](#help-for-remotepy)
    10. [shutdown_button.py: Button & LED indicator to soft shutdown](#shutdown_buttonpy-button-led-indicator-to-soft-shutdown)
4. [Rigby (remote keyboard)](#rigby-remote-keyboard)
    - [Setup](#setup)
    - [Main config file](#main-config-file)
5. [Setup as independent unit](#setup-as-independent-unit)
6. [Photos](#photos)


# General Setup (using pi and waldo via SSH)    

## Powering raspberry Pi
Use a 5V 2.5A power adaptor. 2.2A is too few and the yellow "flash" icon is displaying,
potentially corrupting SD cards or causing other problems.  


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
    - Audio should be 32-bit sampled, 24-bit raises SOX's alsa driver error.
- Delete channels that are not needed anymore from the config file
- Call setservo for all channels if the servos are not calibrated

## Play an entire project
Play every channel of projectName
```
python waldo/main.py -p projectName [start_offset_in_seconds, repeat]
```
Optional argument: If integer: Start after n seconds. If "repeat": repeat track forever.

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
Honestly, i don't know exactly.


## audiotest.py: Test R&L channels
```
python helpers/audiotest.py
```
Plays test sounds indefinitely for testing your stereo channels.


## autostart.py: Files on startup
```
python helpers/autostart.py
```
This file gets started in the RasPi startup sequence, defined in `/etc/rc.local`, see [Setup as independent unit](#setup-as-independent-unit)
Checks if the variable `autostart` in main `config` file is true or an index number of buttons. Starts all scripts needed if so.


## clean_channelfile.py: Compress old channelfiles
```
python helpers/clean_channelfile.py /path/to/project
```
Remove repetitive values in all channelfiles in a project as the new concept already does while recording.


## crash_recover.sh: Quit & restart everything
***ARCHIVED***
```
bash helpers/crash_recover.sh
```
At the moment this is in folder `_archive/`. It was executed by `rc.local` (like autostart). Probably useful again sometime.
Checks if `autostart.py` is running and if so, `REC_REPL` is set to `False`, `killall.py` and other files are being
executed to compensate for cutting power while playing without shutting down.


## editor.py: Edit channel values
```
python helpers/editor.py /path/to/project
```
Post-process channel files. Only works on Linux, not Raspian nor OS X.

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
Does not kill temperature monitoring started by `autostart.py`


## monitor_temperature.py: Keep log of Core temperature
```
python helpers/monitor_temperature.py
```
Saves every minute the temperature of the Core of the RasPi in the file `logs/temperature.log`.
Soon this can also measure different temperature sensors for eg. surveilling servo-hats. 


## notify.sh: GUI alert
```
bash helpers/notify.sh
```
First sketch of GUI alert for RasPi display. Probably gets replaced by native GUI.


## remote.py: Remote commands

### Use keyboard remote control
To start using the analog keyboard Rigby or an USB (numpad) keyboard as a remote for playing or stopping any track, type
```
python helpers/remote.py
```
If you defined `numpad: true` in the main config file, you can use any regular computer keyboard
whereas the key numbers represent the button numbers defined in the main config file.

**Hint:** See [Rigby (remote keyboard)](#rigby-remote-keyboard) for setup analog keyboard Rigby.

### Autoplay track on startup
```
python helpers/remote.py -ap [buttonNumber]
```
buttonNumber represents the button definition integer from the main config file.

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


## shutdown_button.py: Button & LED indicator to soft shutdown
```
python helpers/shutdown_button.py
```
When pressing the button (pin 19), it resets `REC_REPL` to `False` and executes `killall.py`.  
Also it turns on an indicator green LED (pin 20), and when pressed,
a red LED (pin 21) lights up till the pi is fully save to cut power.


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
  KEY_KP1: servo_test_4
  KEY_KP2: hatschi
  KEY_KP3: ohlala
  KEY_KP4: hey
  KEY_KP5: wow
  KEY_KP6: ohappyday
  KEY_KP7: nanana
  KEY_KP8: ohyea
  KEY_KP9: reset
  KEY_KPENTER: cancel # Name a function of any button 'cancel' and you have yourself a cancel button
mcp:                  # Leave alone if you use Mortekay as analog-digital transformer
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
numpad: true       # Set to true if you use USB keyboard to play tracks instead of Rigby
measure_temp: true # starts on startup and measures temp every minute and logs it
autostart: true    # Set to false if you dont want anything to start on startup.
                   # ^Set to true if you want to start keyboard_listener.py, shutdown_button.py to start on RasPi startup
                   # ^Set to track name to play after startup

```
Naked:  
```json
PROJECT_PATH: /home/pi/waldo_projects
REC_REPL: false
autostart: 1
button_value:
  0: 58
  1: 962
  2: 798
  3: 685
  4: 600
  5: 290
buttons:
  KEY_KP1: servo_test_4
  KEY_KP2: hatschi
  KEY_KP3: ohlala
  KEY_KP4: hey
  KEY_KP5: wow
  KEY_KP6: ohappyday
  KEY_KP7: nanana
  KEY_KP8: ohyea
  KEY_KP9: reset
  KEY_KPENTER: cancel
mcp:
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
measure_temp: true
numpad: true
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

It executes the following scripts if `autostart` is set to `true` in config:
- `helpers/remote.py`
    - Listens to numpad or analog play buttons
    - Use modifier '(...)scripts/remote.py -ap tracknumber &' to autoplay when startup RasPi (? functionality should be: set `autostart` to a tracknumber in config)
- `helpers/shutdown_button.py`
    - displays 'ready' indicator LED (pin 16) and listens to pushbutton (pin 19) 
- `helpers/monitor_temperature.py`
    - saves core temperature once a minute in `logs/temperature/[today].log` if `measure_temp` is set to `true` in config


# Photos
![](images/poti.jpg)  
^ Connecting the Potentiometer on Pin 8  

![](images/servos.jpg)  
^ Connecting servos on (pin 0 and 1)  

![](images/ethernet.jpg)  
^ Rigby (Ethernet on Pin 0-5)  
