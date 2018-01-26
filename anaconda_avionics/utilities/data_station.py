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
        retr_string = "Camera ID: " + self.iden + "\n"
        retr_string += "    Lat: %s Lon: %s Alt: %s\n" % (self.lat, self.lon, self.alt)
        retr_string += "    Timeout:           %s\n" % self.timeout
        retr_string += "    Drone_Arrived:     %s\n" % self.drone_arrived
        retr_string += "    Download_Started:  %s\n" % self.download_started
        retr_string += "    Download_Complete: %s\n" % self.download_complete
        return retr_string