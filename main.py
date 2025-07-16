from PyQt5.QtWidgets import QApplication, QDialog
from geopy.geocoders import Nominatim

from MainWindow import MainWindow
from OpeningWindow import OpeningWindow

#Nominatim (OpenStreetMap) 1req/s
#geolocator = Nominatim(user_agent="geoapi_example")
#location_bem = geolocator.reverse("52.26274105520976, 20.898388821074537", language="pl")
#print("Dzielnica: ")
#print(loc.raw.get("address", {}).get('suburb', None) or loc.raw.get("address", {}).get('city_district',None) or loc.raw.get("address", {}).get('borough', None)+"\n")
#print("Skwer/Rondo:")
#print(loc.address)

#Main - showing the application and running it until close is pressed
if __name__ == '__main__':
    app = QApplication([])
    start_dialog = OpeningWindow()
    if start_dialog.exec_() == QDialog.Accepted:
        db_name = start_dialog.db_name
        window = MainWindow(db_name)
        window.show()
        app.exec_()