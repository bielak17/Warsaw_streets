import sqlite3
import sys
import os
import webbrowser

from PyQt5.QtCore import Qt, pyqtSignal, QObject
from geopy.geocoders import Nominatim
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPainterPath, QPen, QBrush
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QGraphicsScene, QGraphicsPixmapItem, \
    QGraphicsPathItem, QGraphicsView
from PyQt5 import uic, QtWidgets

import xml.etree.ElementTree as ET
from svg.path import parse_path, Move, Line, Close

from creating_database import districts


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
    #Hover logic of each district
    def hoverEnterEvent(self, event):
        if self.is_visited():
            self.setBrush(self.hover_green_brush)
        else:
            self.setBrush(self.hover_red_brush)
    def hoverLeaveEvent(self, event):
        self.setBrush(self.default_brush)


# Class for creating neighborhoods buttons on the interactive map. It adds color on hover based on if the neighborhood
# was fully visited or not and on click opens tab with all streets running through it
class NeighborhoodPathItem(QGraphicsPathItem):
    def __init__(self, path, neighborhood_id):
        super().__init__(path)
        self.neighborhood_id = neighborhood_id
        self.default_brush = QBrush(QColor(255,255,255,0))
        self.hover_red_brush = QBrush(QColor(255,0,0,55))
        self.hover_green_brush = QBrush(QColor(255,0,0,55))
        self.hover_info_brush = QBrush(QColor(155,155,155,75))
        self.setBrush(self.default_brush)
        #No outline on the districts because the map has the outlines already
        self.setPen(QPen(QColor(0,0,0,0)))
        self.setAcceptHoverEvents(True)
    #check if all streets in the district were visited
    def is_visited(self):
        con = sqlite3.connect("Streets_clean.db")
        cursor = con.cursor()
        cursor.execute("""SELECT COUNT(street) FROM streets
             INNER JOIN street_neighborhoods ON streets.id = street_neighborhoods.street_id
             WHERE street_neighborhoods.neighborhood_id=? AND seen = 0""",(self.neighborhood_id,))
        info = cursor.fetchall()[0]
        con.close()
        if info:
            return False
        else:
            return True
    #Hover logic of each district
    def hoverEnterEvent(self, event):
        if self.neighborhood_id != '0' and self.neighborhood_id != 'back':
            if self.is_visited():
                self.setBrush(self.hover_green_brush)
            else:
                self.setBrush(self.hover_red_brush)
        else:
            self.setBrush(self.hover_info_brush)

    def hoverLeaveEvent(self, event):
        self.setBrush(self.default_brush)

#Main class of the app
class MainWindow(QMainWindow):
    def __init__(self):
        #Help variables
        self.current_district = 0
        self.current_neighborhood = 0
        #Loading UI from .ui file
        super().__init__()
        self.init_ui()
        #Updating table on the right with number of streets left to visit
        self.update_visited_table()
        #Load map of the whole city
        self.load_WarsawMap_svg()
        #Load all 18 maps of districts with neighborhoods
        self.loadDistricts_svgs()
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
        self.visited_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        con.close()

    #Function that loads main map and interactive buttons from .png and .svg files
    def load_WarsawMap_svg(self):
        #Adding main map of the whole city
        Warsaw_scene = QGraphicsScene()
        warsaw_map_path = os.path.join(os.path.dirname(__file__),"graphics","maps","district_map.png")
        district_svg_path = os.path.join(os.path.dirname(__file__),"graphics","maps","district_map.svg")
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
            item.mousePressEvent = lambda event, did=district_id: self._on_district_clicked(did)
            Warsaw_scene.addItem(item)
        #Adding everything on to the map
        self.Map.setRenderHint(QPainter.Antialiasing)
        self.Map.setScene(Warsaw_scene)
        self.Map.setInteractive(True)

    def loadDistricts_svgs(self):
        #lists of all districts and corresponding widgets
        dis = ["Bemowo","Bialoleka","Bielany","Mokotow","Ochota","Praga Poludnie", "Praga Polnoc", "Rembertow", "Srodmiescie", "Targowek", "Ursus", "Ursynow", "Wawer", "Wesola", "Wilanow", "Wlochy", "Wola", "Zoliborz"]
        maps = [self.Map_Bemowo,self.Map_Bialoleka,self.Map_Bielany,self.Map_Mokotow,self.Map_Ochota,self.Map_PragaPoludnie,self.Map_PragaPolnoc,self.Map_Rembertow,self.Map_Srodmiescie,self.Map_Targowek,self.Map_Ursus,self.Map_Ursynow,self.Map_Wawer,self.Map_Wesola,self.Map_Wilanow,self.Map_Wlochy,self.Map_Wola,self.Map_Zoliborz]
        #For each district add map and create path from .svg file and display it in appropriate Widgets
        for d,map in zip(dis,maps):
            district_scene = QGraphicsScene()
            district_map_path = os.path.join(os.path.dirname(__file__),"graphics","maps",f"{d}_map.png")
            district_svg_path = os.path.join(os.path.dirname(__file__), "graphics", "maps", f"{d}_map.svg")
            pixmap = QPixmap(district_map_path)
            map_item = QGraphicsPixmapItem(pixmap)
            map_item.setZValue(0)
            map_item.setAcceptedMouseButtons(Qt.NoButton)
            map_item.setAcceptHoverEvents(Qt.NoButton)
            district_scene.addItem(map_item)
            tree = ET.parse(district_svg_path)
            root = tree.getroot()
            namespace = {'svg': 'http://www.w3.org/2000/svg'}
            for path_elem in root.findall(".//svg:path", namespace):
                path_data = path_elem.attrib['d']
                neighborhood_id = path_elem.attrib.get('id', 'unknown')
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
                # Creating NeighborhoodPathItem from the created path
                item = NeighborhoodPathItem(qp_path, neighborhood_id)
                item.setZValue(1)
                #Assign functions based on the purpose of the path: if its back, whole district or separate neighborhoods
                if neighborhood_id == "0":
                    item.mousePressEvent = lambda event: self._on_whole_district_clicked()
                elif neighborhood_id == "back":
                    item.mousePressEvent = lambda event: self._on_back_to_full_map_clicked()
                else:
                    item.mousePressEvent = lambda event, nid=neighborhood_id: self._on_neighborhood_clicked(nid)
                district_scene.addItem(item)
            # Adding everything on to the map
            map.setRenderHint(QPainter.Antialiasing)
            map.setScene(district_scene)
            map.setInteractive(True)

    #buttons on map while clicking district/neighborhoods or back/whole_district
    def _on_district_clicked(self,d_id):
        self.current_district = int(d_id)
        self.Map_stack.setCurrentIndex(self.current_district)
        #print(f"District with {self.current_district} clicked.")

    def _on_neighborhood_clicked(self,n_id):
        self.current_neighborhood = int(n_id)
        print(f"Neighborhood with {self.current_neighborhood} clicked.")

    def _on_back_to_full_map_clicked(self):
        self.current_district = 0
        self.current_neighborhood = 0
        self.Map_stack.setCurrentIndex(self.current_district)
        #print("Going back to main map")

    def _on_whole_district_clicked(self):
        self.current_neighborhood = 0
        print("Whole district clicked")

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