# Running a mission
Find the file `~/Anaconda_Avionics/Raspi/data_mule_mission.py` on the UAS. The file is likely to be in the `~` folder. You can SSH into the drone over Command Line or use [RealVNC](https://www.realvnc.com/en/raspberrypi/).

Run the file in python 2.7. The coordinates passed are in the CSV format.
`python data_mule_mission.py CAMERA_TRAPS_COORDINATES LANDING_COORDINATES`

For example:
`python data_mule_mission.py cameras_slovakia_field1.0.csv landing_slovakia_field1.0.csv`

# Format for .csv files with coordinates

The camera trap file contains coordinates in the format `latitude,longitude,three-digit-camera-id`, separated by newlines.

The landing file contains coordinates in the format `latitude,longitude,altitude-at-point` separated by newlines.

Altitude is specified in meters. Latitude and longitude coordinates are specified in decimal format. For example, 48.425158 is the correct format. 48° 25' 30.5688'' is incorrect.

# Uploading new SleepyPi firmware to camera trap

The goal is to automate SleepyPi firmware upload in the future, but it is manual now.

1. The IP of the camera trap is `192.168.42.11+CAMERA_ID`. Therefore, for camera trap ID 001, the IP address is 192.168.42.11.12. For camera trap ID 002, the IP address is 192.168.42.11.13.

2. Camera trap SleepyPi firmware is located in /home/pi/sketchbook/. Because Arduino sketchbook is iffy (e.g. Arduino breaks when there are dashes in file names, while git loves to put dashes everywhere). You must copy the SleepyPi firmware manually into the sketchbook folder using scp. The command is `scp SOURCE_FILE IP_ADDR:/home/pi/sketchbook/` For example, `scp ./firmware.ino 192.168.42.11.13:/home/pi/sketchbook/`

3. To upload firmware onto SleepyPi you will have to connect to the camera trap over RealVNC. Both you and the camera trap must be connected to the Wadi Drone network. You use the Raspberry Pi UNIX login, which is `pi` as user name and `raspberry` as password.




# Tips
- SleepyPi compiler does not like dashes in the names of files
- you can create a soft link with `ln -s` from sketchbook to git folder

# Libraries necessary for Sleepy Pi 2
    git clone https://github.com/PaulStoffregen/Time.git
    git clone https://github.com/rocketscream/Low-Power.git
    # rename the directory as Arduino doesn't like the dash
    mv /home/pi/sketchbook/libraries/Low-Power /home/pi/sketchbook/libraries/LowPower
    git clone https://github.com/SpellFoundry/PCF8523.git
    git clone https://github.com/GreyGnome/PinChangeInt.git
