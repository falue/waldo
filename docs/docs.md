![](images/Logo_Black_RGB.png)  

# o/Waldo
<!-- auto create table of contents: http://ecotrust-canada.github.io/markdown-toc --> 
- [General Setup](#general-setup)
  * [Powering raspberry Pi](#powering-raspberry-pi)
  * [Mount remote file system](#mount-remote-file-system)
  * [Raspberry Pi credentials](#raspberry-pi-credentials)
  * [Main config file](#main-config-file)
  * [Setup as independent unit](#setup-as-independent-unit)
- [Main functions / CLI](#main-functions---cli)
  * [Copy channel](#copy-channel)
  * [Create new project](#create-new-project)
  * [Deamon](#deamon)
  * [Help](#help)
  * [Legal information](#legal-information)
  * [Listing of project details](#listing-of-project-details)
  * [Play](#play)
  * [Record](#record)
  * [Setup project or servo](#setup-project-or-servo)
    + [Steps](#steps)
- [Helpers](#helpers)
  * [audiotest.py: Test R&L channels](#audiotestpy--test-r-l-channels)
  * [autostart.py: Files on startup](#autostartpy--files-on-startup)
  * [editor.py: Edit channel values](#editorpy--edit-channel-values)
    + [remover / adder](#remover---adder)
    + [Convenience functions](#convenience-functions)
  * [keyboard_listener.py: Listens to keystrokes](#keyboard-listenerpy--listens-to-keystrokes)
  * [monitor_temperature.py: Keep log of Core temperature](#monitor-temperaturepy--keep-log-of-core-temperature)
  * [shutdown_button.py: Button & LED indicator to soft shutdown](#shutdown-buttonpy--button---led-indicator-to-soft-shutdown)


# General Setup   

## Powering raspberry Pi
Use a 5V 2.5A power adaptor. 2.2A is too few and the yellow "flash" icon is displaying,
potentially corrupting SD cards or causing other problems.  


## Mount remote file system
```
mkdir  remote_waldo
sshfs pi@192.168.0.4:/home/pi/tmp_waldo_projects remote_waldo/
```

## Raspberry Pi credentials
pi / ...


## Main config file
The main configuration settings are stored in `~/.waldo/main_config.yml`
Button commands are stored, the following config for example defines the first 9 buttons.  

```yaml
project_path: /home/pi/waldo_projects   # define where your project folder is
buttons:                                # define buttons: key-identifier on USB numpad and name of project
  KEY_KP1: servo_test_4
  KEY_KP2: hatschi
  KEY_KP3: ohlala
  KEY_KP4: hey
  KEY_KP5: wow
  KEY_KP6: ohappyday
  KEY_KP7: nanana
  KEY_KP8: ohyea
  KEY_KP9: reset
  KEY_KPENTER: cancel                   # Name a function of any button 'cancel' and you have yourself a cancel button
measure_temp: true                      # starts on startup and measures temp every minute and logs it
autostart: true                         # Set to false if you don't want anything to start on startup.
                                        # ^Set to true if you want to start everything needed to start replaying
                                        # ^Set to project name to play automatically after startup
volume: 30                              # Set volume on startup (> 30 sound is clipping)
used_i2c_addresses: [0x40]              # [0x40] for 16 channels, [0x40, 0x41] for 32, etc
```


## Setup as independent unit
Add the library to the startup cycle of RasPi:
```
sudo nano /etc/rc.local
```
At the bottom (just before `exit 0`), note the following:
```
# Run WALDO
sudo -u pi /usr/local/bin/waldo daemon
```


# Main functions / CLI
You can [play](#play), [record](#record), [setup servos and projects](#-re-calibrate-a-servo),
[copy channel files](#copy-channel) (recorded PWM signals with a timestamp) and
[get a list](#listing-of-project-details) of all projects with all details.

## Copy channel
```
waldo copy project_name_from channel_name_old [project_name_to] channel_name_new --pin_mode pin_copy
```
Duplicate `project_name_from`/`channel_name_old` to `project_name_to`/`channel_name_new` and copy config data associated with
channel_name_old. project_name_to can be omitted, same project as project_name_from applies.
Servo_pin gets either incremented by total channels + 1 `pin_inc` (default), copied from old
`pin_copy`, or gets user defined by integer value `pin_new`.


## Create new project
```
waldo setup project_name
```  
You can choose to duplicate a config file from another project.  
Things you may want to do:
- Add audio file in path/to/project/audio (`.mp3`, `.wave`, `.aiff`)
    - Audio should be 32-bit sampled, 24-bit raises SOX's alsa driver error.
- Delete channels that are not needed anymore from the config file (manually)
- [Setup a new servo](#setup-project-or-servo)
- [Record](#Record-channel) inputs for servo movements


## Deamon
```
waldo deamon
```
Runs all things necessary for listening to keyboard strokes and replaying projects. This gets started if
autostart is `true` in [main-config-file](main config file).
See [Setup as independent unit](setup-as-independent-unit).

Kill running daemon with `killall -9 waldo`


## Help
```
waldo --help
```


## Legal information
```
waldo legal
```


## Listing of project details
```
waldo ls [project_name] [--bt_only]
```
Lists a specific project with [project_name] and every channel of it and their details.
Points out difficulties like multiple use of servo_pin, missing files or config data.
Omit [project_name] to get prompted var options.
Only prints projects which are defined as buttons with option [--bt_only]

```
waldo ls                # Go to prompt
waldo ls project_name   # Display project_name's details
waldo ls --bt_only      # Display projects which are button controlled
```

Example output:  
```
python waldo/main.py -ls
List every channel in every project and point out difficulties.
────────────────────────────────────────────────────────────────────────
test                                                      Button: KEY_P1
✖  No file 'sopran' for specs in config
✖  Multiple use of servo pin 3 (tenor)
✖  No specs in config for file
	channel file	servo	mcp_in	map_min	map_max	st._pos	°DOF
	bariton	    	3	    8	    233	    302	    233	    13°
	░░░░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
	bass		    6	    8	    390	    160	    160	    42°
	░░░░░░████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░ ↹
	sopran		    4	    8	    120	    410	    120	    52°
	░░██████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░
	tenor		    3	    8	    155	    444	    230	    52°
	░░░░░░██████████████████████████████████░░░░░░░░░░░░░░░░░░░

────────────────────────────────────────────────────────────────────────

empty_test:
✖  No channels in config file.
────────────────────────────────────────────────────────────────────────
```
`°DOF` is an attempt to calculate the physical 'degrees of freedom' of the servo, assuming maximal movement of 180°.  
The bar visualizes the 'degrees of freedom' of the servo (approximation).
Prints `↹` when map_min and map_max are reversed.
Displays button key on top right if project has set one in the main config file.


## Play
```
waldo play [project_name] [--start_from int]
```
Plays every channel of optional [project_name] and its sound file.
If [project_name] is omitted, a list of projects is displayed.
Optional argument [--start_from]: Start after n seconds.

Press `enter` to stop replaying.


## Record
```
waldo record project_name channel_name
```
This starts the setup/recording process for channel_name in project_name.
It records PWM signals with a timestamp to a file named channel_file.
If you record channel_name with a not existing project_name, you will be guided to [create a new project](#create-new-project).


## Setup project or servo
```
waldo setup project_name [channel_name]
```  
Omit [channel_name] and you setup a new empty project without any channel_files.
This functionality is used to store or change the settings of a certain servo for a certain
channel within a certain project.

### Steps
(Servo on Pin 2, Potentiometer on Pin 14)

```
waldo setup project_name channel_name
Set MCP3008 Pin [default 14] # In pin of potentiometer
Set Servo Pin [default 0]    # this is the servo out pin
Set minimum position:        # hit 'm' to set the min movement of the servo
Set maximum position:        # hit 'm' to set the max movement of the servo
Set start position:          # usually use the minimum position to start/stop closed
```


# Helpers
Use any of these helpers for your convenience.  


## audiotest.py: Test R&L channels
```
python helpers/audiotest.py
```
Plays test sounds ("left" and "right")indefinitely for testing your stereo channels.


## autostart.py: Files on startup
This file is used when the RasPi starts up, defined in `/etc/rc.local`, see [Setup as independent unit](#setup-as-independent-unit)
Checks if the variable `autostart` in main `config` file is true or an index number of buttons.


## editor.py: Edit channel values
```
python helpers/editor.py /path/to/project
```
Post-process channel files. Only works on Linux, neither Raspian nor OS X.


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


## keyboard_listener.py: Listens to keystrokes
Gets executed when autostart is `true` in [main-config-file](main config file).


## monitor_temperature.py: Keep log of Core temperature
```
python helpers/monitor_temperature.py
```
Stores every minute the temperature of the RasPi core in the file
`~/.waldo/logs/temperature/temperature-2018-08-28_Tue.log` if measure_temp is `true` in
[main-config-file](main config file). Files get deleted after 20 days. 


## shutdown_button.py: Button & LED indicator to soft shutdown
```
python helpers/shutdown_button.py
```
The button (pin 19) turns on an indicator LED when pressed,
a red LED (pin 21) lights up till the pi is fully save to cut power.
