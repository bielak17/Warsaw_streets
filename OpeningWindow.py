import os

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QMessageBox

#Class with first window opening to get the db name
class OpeningWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.pushButton.clicked.connect(self._on_submit)

     # Function for initializing UI from FirstWindow.ui file created in QtDesigner
    def init_ui(self):
        ui_path = os.path.join(os.path.dirname(__file__), "graphics", "FirstWindow.ui")
        uic.loadUi(ui_path, self)

    #Function getting the db_name and passing it to the main window. In case of wrong file name it shows warning window.
    def _on_submit(self):
        db_name = self.lineEdit.text()
        #print(db_name)
        if db_name == "" or db_name == "Streets_clean":
            warning = QMessageBox()
            warning.setIcon(QMessageBox.Warning)
            warning.setText("Please enter proper file name!")
            warning.setStandardButtons(QMessageBox.Ok)
            warning.exec_()
        else:
            self.db_name = db_name
            self.accept()