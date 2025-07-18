from PyQt5.QtWidgets import QApplication, QDialog

from MainWindow import MainWindow
from OpeningWindow import OpeningWindow

#Main - showing the First window and after it being accepted showing the main window and running it until close is pressed
if __name__ == '__main__':
    app = QApplication([])
    start_dialog = OpeningWindow()
    if start_dialog.exec_() == QDialog.Accepted:
        db_name = start_dialog.db_name
        window = MainWindow(db_name)
        window.show()
        app.exec_()