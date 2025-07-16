import os
import webbrowser

from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPainterPath, QPen, QBrush, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QGraphicsScene, QGraphicsPixmapItem, \
    QGraphicsPathItem, QPushButton, QWidget, QHBoxLayout
from PyQt5 import uic, QtWidgets

import xml.etree.ElementTree as ET
from svg.path import parse_path, Move, Line, Close

import database_searches as db


#Function that opens google maps with specific street_name search
def open_map(street_name):
    query = f"{street_name}, Warsaw"
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
    webbrowser.open(url)

#Class for creating district buttons on the interactive map. It adds color on hover based on if the district
#was fully visited or not and on click changes to map of this district
class DistrictPathItem(QGraphicsPathItem):
    def __init__(self, path, district_id, db):
        super().__init__(path)
        self.database = db
        self.district_id = district_id
        self.default_brush = QBrush(QColor(255,255,255,25))
        self.hover_red_brush = QBrush(QColor(255,0,0,35))
        self.hover_green_brush = QBrush(QColor(0,255,0,35))
        self.setBrush(self.default_brush)
        #No outline on the districts because the map has the outlines already
        self.setPen(QPen(QColor(0,0,0,0)))
        self.setAcceptHoverEvents(True)

    #check if all streets in the district were visited
    def is_visited(self):
        info = self.database.how_many_not_seen_in_district(self.district_id)
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
    def __init__(self, path, neighborhood_id, db):
        super().__init__(path)
        self.database = db
        self.neighborhood_id = neighborhood_id
        self.default_brush = QBrush(QColor(255,255,255,0))
        self.hover_red_brush = QBrush(QColor(255,0,0,55))
        self.hover_green_brush = QBrush(QColor(0,255,0,55))
        self.hover_info_brush = QBrush(QColor(155,155,155,75))
        self.setBrush(self.default_brush)
        #No outline on the districts because the map has the outlines already
        self.setPen(QPen(QColor(0,0,0,0)))
        self.setAcceptHoverEvents(True)
    #check if all streets in the neighborhood were visited
    def is_visited(self):
        info = self.database.how_many_not_seen_in_neighborhood(self.neighborhood_id)
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

#Class with main window of the app
class MainWindow(QMainWindow):
    def __init__(self,db_name):
        #Help variables
        self.current_district = 0
        self.current_neighborhood = 0
        #Loading UI from .ui file
        super().__init__()
        self.init_ui()
        #object of class database used to make SQL queries
        db_name += ".db"
        self.database = db.Database(db_name)
        #Updating table on the right with number of streets left to visit
        self._update_visited_table()
        #Load map of the whole city
        self.load_WarsawMap_svg()
        #Load all 18 maps of districts with neighborhoods
        self.loadDistricts_svgs()
        # make the app cover the windows toolbar (it needs full 1080 so on smaller screens it needs to cover the toolbar)
        #self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        #Connecting buttons
        self.Instruction_button.clicked.connect(self._on_click_instruction_button)
        self.Back_to_right_menu_1.clicked.connect(self._on_click_back_to_right_menu_button)
        self.Back_to_right_menu_2.clicked.connect(self._on_click_back_to_right_menu_button)
        self.GPX_button.clicked.connect(self._on_click_GPX_button)
        self.back_to_map_button.clicked.connect(self._on_click_back_to_maps)
        self.sort_button.toggled.connect(self._on_toggle_sort_by)
        self.Search_button.clicked.connect(lambda: self._on_click_search_button("name"))
        #also connecting enter in searchbar to searching
        self.SearchBar.returnPressed.connect(lambda: self._on_click_search_button("name"))

# Function for initializing UI from Mainmenuui.ui file created in QtDesigner
    def init_ui(self):
        ui_path = os.path.join(os.path.dirname(__file__), "graphics", "Mainmenuui.ui")
        uic.loadUi(ui_path, self)

    #Function that updates the visited table on the main screen with the number of left streets to visit
    def _update_visited_table(self):
        # Filling table on main window with number of not visited streets per district.
        for i in range(18):
            value = self.database.how_many_not_seen_in_district(i+1)
            self.visited_table.setItem(i, 1, QTableWidgetItem(str(value)))
        # Caluclating all not visited street for SUM row and updating it.
        value_all = self.database.how_many_not_seen_in_whole_city()
        self.visited_table.setItem(18, 1, QTableWidgetItem(str(value_all)))
        #Prevension from editing the contents and size of the table by the user
        self.visited_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.visited_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.visited_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

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
            item = DistrictPathItem(qp_path,district_id,self.database)
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
        for d,m in zip(dis,maps):
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
                item = NeighborhoodPathItem(qp_path, neighborhood_id, self.database)
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
            m.setRenderHint(QPainter.Antialiasing)
            m.setScene(district_scene)
            m.setInteractive(True)

    #function to populate main table with streets given via info argument which contains all data fetched from SQL query
    def _populate_table_with_data(self,info):
        self.main_table.setRowCount(len(info))
        for row_id, row_data in enumerate(info):
            for col_id, value in enumerate(row_data):
                #getting street id
                if col_id == 0:
                    s_id = value
                #getting street name
                if col_id == 1:
                    street_name = value
                # Setting graphics for the column is_visited
                if col_id == 4:
                    visited = value
                    if value:
                        icon = QIcon("graphics/green_tick.png")
                    else:
                        icon = QIcon("graphics/red_x.png")
                    item = QTableWidgetItem()
                    item.setIcon(icon)
                    self.main_table.setIconSize(QSize(24, 24))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setText("")
                else:
                    item = QTableWidgetItem(str(value))
                self.main_table.setItem(row_id, col_id, item)
            # adding buttons to change the visited/seen value of each street in database
            button_change_visit = QPushButton()
            if visited:
                button_change_visit.setText("Change to not seen")
                button_change_visit.clicked.connect(lambda _, id=s_id,row=row_id,name=street_name: self._change_seen_value(row,id,1,name))
            else:
                button_change_visit.setText("Change to seen")
                button_change_visit.clicked.connect(lambda _, id=s_id,row=row_id,name=street_name: self._change_seen_value(row,id,0,name))
            cell_widget_change_visit = QWidget()
            layout_change_visit = QHBoxLayout(cell_widget_change_visit)
            layout_change_visit.addWidget(button_change_visit)
            layout_change_visit.setContentsMargins(0, 0, 0, 0)  # no extra padding
            layout_change_visit.setAlignment(button_change_visit, Qt.AlignCenter)
            button_change_visit.setProperty("street_id", s_id)
            button_change_visit.setProperty("street_name", street_name)
            self.main_table.setCellWidget(row_id, 5, cell_widget_change_visit)
            # adding buttons to google maps page of each street to the table in the last column
            button_to_map = QPushButton("Check street on map")
            button_to_map.clicked.connect(lambda _, name=street_name: open_map(name))
            cell_widget_to_map = QWidget()
            layout_to_map = QHBoxLayout(cell_widget_to_map)
            layout_to_map.addWidget(button_to_map)
            layout_to_map.setContentsMargins(0, 0, 0, 0)
            layout_to_map.setAlignment(button_to_map, Qt.AlignCenter)
            self.main_table.setCellWidget(row_id, 6, cell_widget_to_map)
        self.main_table.resizeColumnsToContents()
        self.main_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.main_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.main_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

    #4 buttons on map while clicking district/neighborhoods or back/whole_district
    def _on_district_clicked(self,d_id):
        self.current_district = int(d_id)
        self.Map_stack.setCurrentIndex(self.current_district)
        #print(f"District with {self.current_district} clicked.")

    def _on_neighborhood_clicked(self,n_id,sort="name"):
        self.current_neighborhood = int(n_id)
        #print(f"Neighborhood with {self.current_neighborhood} clicked.")
        self.mainORtable.setCurrentIndex(1)
        info = self.database.all_streets_in_neighborhood(self.current_neighborhood,sort)
        self._populate_table_with_data(info)
        self.last_query = "neighborhood"

    def _on_back_to_full_map_clicked(self):
        self.current_district = 0
        self.current_neighborhood = 0
        self.Map_stack.setCurrentIndex(self.current_district)
        #print("Going back to main map")

    def _on_whole_district_clicked(self,sort="name"):
        self.current_neighborhood = 0
        #print("Whole district clicked")
        self.mainORtable.setCurrentIndex(1)
        info = self.database.all_streets_in_district(self.current_district,sort)
        self._populate_table_with_data(info)
        self.last_query = "district"

    #3 buttons to change the page on the smaller right StackedWidget
    def _on_click_instruction_button(self):
        self.tabORinstORgpx.setCurrentIndex(1)

    def _on_click_back_to_right_menu_button(self):
        self.tabORinstORgpx.setCurrentIndex(0)

    def _on_click_GPX_button(self):
        self.tabORinstORgpx.setCurrentIndex(2)

    #button to go back from table to main map
    def _on_click_back_to_maps(self):
        self.sort_button.blockSignals(True)
        self.sort_button.setChecked(False)
        self.sort_button.blockSignals(False)
        self.SearchBar.setText("")
        self.mainORtable.setCurrentIndex(0)
        self.current_neighborhood = 0
        self._update_visited_table()

    #button for sorting by name or seen it calls last used function but with different sorting order
    def _on_toggle_sort_by(self):
        if self.sort_button.isChecked():
            match self.last_query:
                case "search":
                    self._on_click_search_button("visit")
                case "district":
                    self._on_whole_district_clicked("visit")
                case "neighborhood":
                    self._on_neighborhood_clicked(self.current_neighborhood,"visit")
            self.sort_button.setText("Street ID")
        else:
            match self.last_query:
                case "search":
                    self._on_click_search_button("name")
                case "district":
                    self._on_whole_district_clicked("name")
                case "neighborhood":
                    self._on_neighborhood_clicked(self.current_neighborhood,"name")
            self.sort_button.setText("Visited")

    #button working with search bar. It captures the string from user and searches for streets that contain this string in its name
    def _on_click_search_button(self,sort):
        street_name = self.SearchBar.text()
        self.mainORtable.setCurrentIndex(1)
        info = self.database.search_for_street_name(street_name,sort)
        self._populate_table_with_data(info)
        self.last_query = "search"

    #function assigned to the change_value button in table it changes the value and refreshes row in table
    def _change_seen_value(self,row,street_id,is_visited,street_name):
        #getting the button to disable it for a second and change its functionality
        button_change_visit = self.main_table.cellWidget(row, 5).findChild(QPushButton)
        button_change_visit.setEnabled(False)
        self.database.change_seen_value(street_id,is_visited)
        #getting the changed data
        info = self.database.search_for_street_name(street_name,"name")
        #based on new value in seen column change the image and button in the table
        if info[0][4]:
            icon = QIcon("graphics/green_tick.png")
            QTimer.singleShot(0, lambda: button_change_visit.setText("Change to not seen"))
            button_change_visit.clicked.disconnect()
            button_change_visit.clicked.connect(lambda _, id = street_id, name=street_name, r=row: self._change_seen_value(r, id, 1, name))
        else:
            icon = QIcon("graphics/red_x.png")
            QTimer.singleShot(0, lambda: button_change_visit.setText("Change to seen"))
            button_change_visit.clicked.disconnect()
            button_change_visit.clicked.connect(lambda _, id = street_id, name=street_name, r=row: self._change_seen_value(r, id, 0, name))
        item = QTableWidgetItem()
        item.setIcon(icon)
        self.main_table.setIconSize(QSize(24, 24))
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("")
        self.main_table.setItem(row, 4, item)
        # enabling the button again after 0.2s and resizing the column to new button
        QTimer.singleShot(200, lambda: self.main_table.resizeColumnsToContents())
        QTimer.singleShot(200, lambda: button_change_visit.setEnabled(True))
