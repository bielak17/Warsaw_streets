import sqlite3
import sys
import os
import webbrowser

from PyQt5.QtCore import Qt
from geopy.geocoders import Nominatim
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPainterPath, QPen, QBrush
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QGraphicsScene, QGraphicsPixmapItem, QGraphicsPathItem
from PyQt5 import uic, QtWidgets

import xml.etree.ElementTree as ET
from svg.path import parse_path, Move, Line, Close


def open_map(street_name):
    query = f"{street_name}, Warsaw"
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
    webbrowser.open(url)

def test():
    con = sqlite3.connect("Streets_clean.db")
    cursor = con.cursor()
    program = True
    while program:
        print("Testowe pokazywanie w konsoli:\n")
        cursor.execute("SELECT id,district FROM districts ORDER BY id ASC")
        dist_help = cursor.fetchall()
        for r in dist_help:
            print(f"{r[0]}-{r[1]}\n")
        print(f"0-Wyjscie z programu\n")
        dist_choice = int(input("Wybierz opcje z powyższych "))
        if dist_choice == 0:
            program = False
            con.close()
            sys.exit()
        cursor.execute("SELECT id, neighborhood FROM neighborhoods WHERE district_id = ? ORDER BY id ASC",(dist_choice,))
        neigh_help = cursor.fetchall()
        for r in neigh_help:
            print(f"{r[0]}-{r[1]}\n")
        print("0-Cała dzielnica\n")
        neigh_choice = int(input("Wybierz opcje z powyższych "))
        if neigh_choice == 0:
            cursor.execute("""SELECT streets.street, districts.district FROM streets
                           INNER JOIN street_district ON street_district.street_id=streets.id
                           INNER JOIN districts ON street_district.district_id=districts.id
                           WHERE districts.id = ?
                           ORDER BY streets.id ASC """,(dist_choice,))
            print_help = cursor.fetchall()
            for r in print_help:
                print(r)
        else:
            cursor.execute("""SELECT streets.street, districts.district, neighborhoods.neighborhood, streets.seen FROM streets
                           INNER JOIN street_neighborhoods ON street_neighborhoods.street_id=streets.id
                           INNER JOIN neighborhoods ON street_neighborhoods.neighborhood_id=neighborhoods.id
                           INNER JOIN districts ON neighborhoods.district_id=districts.id
                           WHERE districts.id = ? AND neighborhoods.id = ?
                           ORDER BY streets.id ASC""",(dist_choice,neigh_choice))
            print_help = cursor.fetchall()
            for r in print_help:
                if r[3]:
                    print(f"Seen: {r[0]} - {r[1]} - {r[2]}")
                else:
                    print(f"NOT seen: {r[0]} - {r[1]} - {r[2]}")
        print("\n---------------------------------------------\n\n\n")



    #Nominatim (OpenStreetMap) 1req/s
    geolocator = Nominatim(user_agent="geoapi_example")
    #location_bem = geolocator.reverse("52.26274105520976, 20.898388821074537", language="pl")
    #print("Dzielnica: ")
    #print(loc.raw.get("address", {}).get('suburb', None) or loc.raw.get("address", {}).get('city_district',None) or loc.raw.get("address", {}).get('borough', None)+"\n")
    #print("Skwer/Rondo:")
    #print(loc.address)

#Class for creating district buttons on the interactive map. It adds color on hover based on if the district
#was fully visited or not and on click changes to map of this district
class DistrictPathItem(QGraphicsPathItem):
    def __init__(self, path, district_id):
        super().__init__(path)
        self.district_id = district_id
        self.default_brush = QBrush(QColor(255,255,255,25))
        self.hover_red_brush = QBrush(QColor(255,0,0,35))
        self.hover_green_brush = QBrush(QColor(255,0,0,35))
        self.setBrush(self.default_brush)
        #No outline on the districts because the map has the outlines already
        self.setPen(QPen(QColor(0,0,0,0)))
        self.setAcceptHoverEvents(True)
    #check if all streets in the district were visited
    def is_visited(self):
        con = sqlite3.connect("Streets_clean.db")
        cursor = con.cursor()
        cursor.execute("""SELECT COUNT(street) FROM streets
             INNER JOIN street_district ON streets.id = street_district.street_id
             WHERE street_district.district_id=? AND seen = 0""",(self.district_id,))
        info = cursor.fetchall()[0]
        con.close()
        if info:
            return False
        else:
            return True
    #Hover and click logic of each district
    def hoverEnterEvent(self, event):
        if self.is_visited():
            self.setBrush(self.hover_green_brush)
        else:
            self.setBrush(self.hover_red_brush)
    def hoverLeaveEvent(self, event):
        self.setBrush(self.default_brush)
    def mousePressEvent(self, event):
        print(f"Clicked: {self.district_id}")

#Main class of the app
class MainWindow(QMainWindow):
    def __init__(self):
        #Loading UI from .ui file
        super().__init__()
        self.init_ui()
        #Updating table on the right with number of streets left to visit
        self.update_visited_table()
        #Load map of the whole city
        self.load_svg()
        #Connecting buttons
        self.Instruction_button.clicked.connect(self._on_click_instruction_button)
        self.Back_to_right_menu_1.clicked.connect(self._on_click_back_to_right_menu_button)
        self.Back_to_right_menu_2.clicked.connect(self._on_click_back_to_right_menu_button)
        self.GPX_button.clicked.connect(self._on_click_GPX_button)

# Function for initializing UI from Mainmenuui.ui file created in QtDesigner
    def init_ui(self):
        ui_path = os.path.join(os.path.dirname(__file__), "graphics", "Mainmenuui.ui")
        uic.loadUi(ui_path, self)

    #Function that updates the visited table on the main screen with the number of left streets to visit
    def update_visited_table(self):
        con = sqlite3.connect("Streets_clean.db")
        cursor = con.cursor()
        # Filling table on main window with number of not visited streets per district.
        for i in range(18):
            cursor.execute("""SELECT COUNT(street) FROM streets
                     INNER JOIN street_district ON streets.id = street_district.street_id
                     WHERE street_district.district_id=? AND seen = 0""", (i + 1,))
            value = cursor.fetchone()[0]
            self.visited_table.setItem(i, 1, QTableWidgetItem(str(value)))
        # Caluclating all not visited street for SUM row and updating it.
        cursor.execute("""SELECT COUNT(DISTINCT street) FROM streets WHERE seen = 0""")
        value_all = cursor.fetchone()[0]
        self.visited_table.setItem(18, 1, QTableWidgetItem(str(value_all)))
        #Prevension from editing the contents and size of the table by the user
        self.visited_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.visited_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        con.close()

    #Function that loads main map and interactive buttons from .png and .svg files
    def load_svg(self):
        #Adding main map of the whole city
        Warsaw_scene = QGraphicsScene()
        warsaw_map_path = os.path.join(os.path.dirname(__file__),"graphics","district_map.png")
        district_svg_path = os.path.join(os.path.dirname(__file__),"graphics","district_map.svg")
        pixmap = QPixmap(warsaw_map_path)
        map_item = QGraphicsPixmapItem(pixmap)
        map_item.setZValue(0)
        map_item.setAcceptedMouseButtons(Qt.NoButton)
        map_item.setAcceptHoverEvents(Qt.NoButton)
        Warsaw_scene.addItem(map_item)
        #Decoding .svg into separate paths for each district
        tree = ET.parse(district_svg_path)
        root = tree.getroot()
        namespace = {'svg': 'http://www.w3.org/2000/svg'}
        for path_elem in root.findall(".//svg:path", namespace):
            path_data = path_elem.attrib['d']
            district_id = path_elem.attrib.get('id', 'unknown')
            svg_path = parse_path(path_data)
            # Convert SVG path to QPainterPath
            qp_path = QPainterPath()
            for segment in svg_path:
                if isinstance(segment, Move):
                    qp_path.moveTo(segment.end.real, segment.end.imag)
                    started = True
                elif isinstance(segment, Line):
                    if not started:
                        qp_path.moveTo(segment.start.real, segment.start.imag)
                        started = True
                    qp_path.lineTo(segment.end.real, segment.end.imag)
                elif isinstance(segment, Close):
                    qp_path.closeSubpath()
            if not qp_path.isEmpty() and not qp_path.currentPosition() == qp_path.elementAt(0):
                qp_path.closeSubpath()
            #Creating DistrictPathItem from the created path
            item = DistrictPathItem(qp_path,district_id)
            item.setZValue(1)
            Warsaw_scene.addItem(item)
        #Adding everything on to the map
        self.Map.setRenderHint(QPainter.Antialiasing)
        self.Map.setScene(Warsaw_scene)
        self.Map.setInteractive(True)

    #3 buttons to change the page on the smaller right StackedWidget
    def _on_click_instruction_button(self):
        self.tabORinstORgpx.setCurrentIndex(1)

    def _on_click_back_to_right_menu_button(self):
        self.tabORinstORgpx.setCurrentIndex(0)

    def _on_click_GPX_button(self):
        self.tabORinstORgpx.setCurrentIndex(2)


#Main - showing the application and running it until close is pressed
if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()