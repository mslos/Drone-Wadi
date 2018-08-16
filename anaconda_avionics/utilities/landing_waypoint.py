from dronekit import LocationGlobalRelative

class LandingWaypoint(LocationGlobalRelative): # pylint: disable=too-few-public-methods
    """
    Class that stores information relevant to navigation used for the landing approach.
    """

    def __init__(self, number, latitude, longitude, altitude, airspeed="N/A"): # pylint: disable=too-many-arguments
        super(LandingWaypoint, self).__init__(latitude, longitude,)
        self.waypoint_number = number
        self.lon = longitude
        self.lat = latitude
        self.alt = altitude
        self.airspeed = airspeed

    def summary(self):
        """
        Returns a summary (string) of the waypoint.
        """

        ret_string = "Landing Waypoint Number: %s\n" % self.waypoint_number
        ret_string += "    Lat: %s Lon: %s Alt: %s\n" % (self.lat, self.lon, self.alt)
        ret_string += "    Airspeed (m/s):           %s\n" % self.airspeed
        return ret_string