import sys
import base64
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QIcon, QPixmap

qtCreatorFile = "schedule.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        
        pixmap = QPixmap("earth.jpg")
        pixmap = pixmap.scaled(650, 400, QtCore.Qt.KeepAspectRatio, QtCore.Qt.FastTransformation)
        self.label = QLabel(self)
        self.label.setPixmap(pixmap)
        # Dimensions are probably not correct 
        self.label.setGeometry(20, 40, 650, 400)

        self.setupUi(self)

        self.scheduleSearch.clicked.connect(self.getAvailableSats)


    def getAvailableSats(self):
        date = self.scheduleDateEdit.date().toPyDate()
        # Call Andrew's script
        # Call populateTable when adding script to retrieve data

    def populateTable(self, data):
        self.availableSats.setRowCount(len(data))
        for row in range(len(data)):
            for column in range(7):
                self.availableSats.setItem(row, column, QtWidgets.QTableWidgetItem(data[row][column]))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())