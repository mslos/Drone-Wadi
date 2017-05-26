import time
import argparse
from dronekit import connect, VehicleMode, LocationGlobal

#Callback definition for mode observer
def mode_callback(self, attr_name, msg):
	print "Vehicle Mode", self.mode
	if str(self.mode) == "VehicleMode:STABILIZE": # Quit program entirely to silence Raspberry Pi
		print "Quitting program..."
		exit()
		print "We should never get here! \nFUCK FUCK FUCK \nAHHHH"		

# From simple_goto.py example
def arm_and_takeoff(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """

    print("Basic pre-arm checks")
    # Don't try to arm until autopilot is ready
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)

    print("Arming motors")
    # Copter should arm in GUIDED mode
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    # Confirm vehicle armed before attempting to take off
    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print("Taking off!")
    vehicle.simple_takeoff(aTargetAltitude)  # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto
    #  (otherwise the command after Vehicle.simple_takeoff will execute
    #   immediately).
    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        # Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.95:
            print("Reached target altitude")
            break
        time.sleep(1)


## MISSION SETUP
print "SETTING UP MISSION"

# Connect to the Vehicle using "connection string" (in this case an address on network)
vehicle = connect('/dev/ttyS0', baud=57600, wait_ready=True)

# Set vehicle to GUIDED to ensure proper mission startup
vehicle.mode = VehicleMode("GUIDED")
while str(vehicle.mode.name) != "GUIDED": # Wait for async call to set vehicle mode
	print "Waiting for Wadi Drone to be set to GUIDED mode..."
	time.sleep(0.5)
print "Vehicle now in: " + vehicle.mode.name


# Parse file name from command line argument
parser = argparse.ArgumentParser(description='Process some.')
parser.add_argument('file', type=argparse.FileType('r'),
			help = "Points formatted as CSV (Format: <latitude>,<longitude>,<altitude>)" + 
				"Point 0: takeoff " + 
				"Point 1..(N-3): camera trap locations " +
				"Point (N-2): landing approach location 1" +
				"Point (N-1): landing approach location 2" +
				"Point N: landing touchdown location")
args = parser.parse_args()

# Read absolute GPS coordinates and altitude from CSV file into list of lists
numbers = [[i for i in line.strip().split(',')] for line in args.file.readlines()]

# Raw latitude, longitude, and altitude translated to LocationGlobals into `points` list
points = []
for line in range(len(numbers)-2):
	if not numbers[line][0].isalpha(): # Not data column descriptor
		lat = float(numbers[line][0])
		lon = float(numbers[line][1])
		alt = float(numbers[line][2])
		print 	"Point " + str(line) + ":" \
			"\tLatitude: " + str(lat) + \
			"\tLongitude: " + str(lon) + \
			"\tAltitude: " + str(alt)
		points.append(LocationGlobal(lat, lon, alt))

# Landing sequence - executed when vehicle enters 'RTL'
cmds = vehicle.commands
print "Clear any existing commands"
cmds.clear()

print "Set landing sequence"
landing_approach_1 = numbers[len(numbers)-2]
landing_approach_2 = numbers[len(numbers)-1]
touchdown = numbers[len(numbers)]
 
cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_DO_LAND_START, 0, 0, 0, 0, 0, 0, 0, 0, 0))
cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, landing_approach_1[0], landing_approach_1[1], landing_approach_1[2]))
cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, landing_approach_2[0], landing_approach_2[1], landing_approach_2[2]))
cmds.add(Command( 0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_LAND, 0, 0, 0, 0, 0, 0, touchdown[0], touchdown[1], touchdown[2]))

print "Upload new commands to vehicle"
cmds.upload()

## MISSION STARTUP
print "STARTING MISSION"

# Listens for mode changes and reliquishes drone control to remote control if mode is STABILIZE
vehicle.add_attribute_listener('mode', mode_callback)

# arm_and_takeoff(10)


## COVER ALL POINTS
for point in points:
	print "Going to next point"
	#vehicle.simple_goto(point, groundspeed=20) #check ground speed before uncommenting
	#while str(vehicle.mode.name) != "LOITER":
	#	pass
	print "Reached point. Loitering for 120 seconds..."
	time.sleep(1)


## RETURN HOME
print "Returning to runway..."
vehicle.mode = VehicleMode("RTL")


## MISSION TERMINATION
print "Closing vehicle object..."
vehicle.close()


## MISSION SUCCESSFULLY COMPLETED WITHOUT HARD INTERRUPT
print "MISSION COMPLETE"
