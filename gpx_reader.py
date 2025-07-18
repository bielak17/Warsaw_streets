import time
import xml.etree.ElementTree as ET
from geopy.geocoders import Nominatim

from PyQt5.QtCore import QObject, pyqtSignal


class gpx_reader(QObject):
    progress = pyqtSignal(int)
    file_length = pyqtSignal(int)
    finished = pyqtSignal()
    result = pyqtSignal(list)
    time_left = pyqtSignal(str)

    def __init__(self,file_path):
        super().__init__()
        self.file = file_path

    #Function that gets all the streets from the gpx file
    def run(self):
        tree = ET.parse(self.file)
        root = tree.getroot()
        namespace = {'default': 'http://www.topografix.com/GPX/1/1'}
        trackpoints = root.findall('.//default:trkpt',namespace)
        coordinates = []
        #After parsing the gpx file coordinates are saved into coordinates[] list
        for tp in trackpoints:
            lat = float(tp.get('lat'))
            lon = float(tp.get('lon'))
            coordinates.append((lat,lon))
        #Using Nominatim (OpenStreetMap) to search coordinates into streets name it can only handle 1req per second
        geolocator = Nominatim(user_agent="my_reverse_geocoder_app")
        length = len(coordinates)
        i = 0
        street_list = []
        previous_street = ""
        current_street = ""
        self.file_length.emit(length)
        #Checking the street name from every 10 coordinates
        #because this app is for walking/cycling not a lot changes for 10 seconds so only every 10th point is being checked
        while i < length:
            #Updating progress bar
            time_l = (length//10 - i//10)+1
            self.time_left.emit(str(time_l))
            self.progress.emit(i)
            try:
                location = geolocator.reverse((coordinates[i][0],coordinates[i][1]),language="pl")
                #if the location is none we skip
                if location is None:
                    i += 10
                    continue
                address = location.raw.get("address", {})
            #Checking if the geo reverse worked properly
            except Exception as e:
                print(f"Error at point {i}: {e}")
                continue
            #print(address)
            #Checking only streets in Warsaw
            if address.get("city") == "Warszawa":
                #In Wesoła there are duplicates so in database all Wesoła streets has (Wesoła) added to them so we add it here as well
                if address.get("suburb") == "Wesoła":
                    current_street = address.get("road")+"(Wesoła)"
                else:
                    current_street = address.get("road")
                #Fixing the quotation marks
                if current_street is not None:
                    current_street = current_street.replace("„",'"')
                    current_street = current_street.replace("”", '"')
                #If the street is none (for example coordinates are on the bridge/park/...) it is skipped
                if current_street is None:
                    previous_street = ""
                    i += 10
                    continue
                #print(previous_street,current_street)
                #If the same street appears in 2 consecutive points we add it to the visited street_list
                #of course only if it is not added already
                if current_street == previous_street and current_street not in street_list:
                    street_list.append(current_street)
            #Setting previous street as the one that was just checked
            previous_street = current_street
            i+=10
            #Sleeping for 1.1 second because free model of this geolocator allows for 1 search per second only
            time.sleep(1.1)
        print(street_list)
        self.result.emit(street_list)
        self.finished.emit()
