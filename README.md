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
