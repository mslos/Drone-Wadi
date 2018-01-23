from dronekit import LocationGlobalRelative

class DataStation(LocationGlobalRelative): # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """
    Class that stores information relevant to navigation for each data station
    """

    def __init__(self, latitude, longitude, altitude, iden):
        super(DataStation, self).__init__(latitude, longitude,)
        self.lon = longitude
        self.lat = latitude
        self.alt = altitude
        self.iden = iden
        self.timeout = False
        self.drone_arrived = False
        self.download_started = False
        self.download_complete = False

    def summary(self):
        """
        Returns a summary (string) of the status of the camera.
        """
        ret_string = "Camera ID: " + self.iden + "\n"
        ret_string += "    Lat: %s Lon: %s Alt: %s\n" % (self.lat, self.lon, self.alt)
        ret_string += "    Timeout:           %s\n" % self.timeout
        ret_string += "    Drone_Arrived:     %s\n" % self.drone_arrived
        ret_string += "    Download_Started:  %s\n" % self.download_started
        ret_string += "    Download_Complete: %s\n" % self.download_complete
        return ret_string