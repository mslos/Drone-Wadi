# Anaconda Avionics

This codebase contains the full companion computer software for autonomous drone missions and data retrieval from
remote data stations. Currently, this is optimized for camera traps and image transfer, but can be easily generalized
for any file type from any data station so long as the data station adheres to the standard file locations.

Data transfer is achieved over SFTP which uses SSH2 as the application layer protocol. This takes advantage of the security
and encryption capabilities of SSH2 while maintaining the simple, robust file transfer capabilities of SFTP. All of this
uses TCP as the transport layer protocol so data integrity is guaranteed.


## Set up

To install the necessary packages for this software, run the following command:

```
    make init
```

## Testing

For software tests, run the following command:

```
    make test
```

## Running a Mission

From inside the `wadi-drone` directory on the UAS, execute:

```python
    python . PATH_TO_CAMERA_TRAP_COORDINATES PATH_TO_LANDING_COORDINATES
```

For example:

```python
    python . cameras_slovakia_field1.0.csv landing_slovakia_field1.0.csv
```

## Format for CSV waypoint coordinate files

The camera trap file contains coordinates in the format `latitude,longitude,three-digit-camera-id`, separated by newlines.

The landing file contains coordinates in the format `latitude,longitude,altitude-at-point`, separated by newlines.

Altitude is specified in meters. Latitude and longitude coordinates are specified in decimal format. For example, 48.425158 is the correct format. 48° 25' 30.5688'' is incorrect.
