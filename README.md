# Wadi-Drone
Files necessary to set up your own version of Wadi Drone. 

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

