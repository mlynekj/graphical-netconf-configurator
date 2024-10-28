# Other
import sys

# QT
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QGraphicsView, 
    QGraphicsScene,  
    QToolBar)
from PySide6.QtGui import ( 
    QBrush, 
    QColor, 
    QIcon, 
    QAction,
    QPixmap)

# Custom
from devices import Router, Cable
from dialogs import *


class MainView(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.scene.setBackgroundBrush(QBrush(QColor(255, 255, 255))) # White background

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Network Configurator")
        self.view = MainView()
        self.setCentralWidget(self.view)

        self.createToolBar()

    def createToolBar(self):
        toolbar = QToolBar("Toolbar", self)
        toolbar.setVisible(True)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # Add a device button
        plus_icon_img = QIcon(QPixmap("graphics/icons/plus.png")) #https://www.freepik.com/icon/add_1082378#fromView=family&page=1&position=1&uuid=d639dba2-0441-47bb-a400-3b47c2034665
        action1_connectToDevice = QAction(plus_icon_img, "Connect to a device", self)
        action1_connectToDevice.triggered.connect(self.showDeviceConnectionDialog)
        toolbar.addAction(action1_connectToDevice)

        #DEBUG: 
        if __debug__:
            action99_debug = QAction("DEBUG", self)
            action99_debug.triggered.connect(self.showDebugDialog)
            toolbar.addAction(action99_debug)

        self.addToolBar(toolbar)

    def showDeviceConnectionDialog(self):
        dialog = AddDeviceDialog(self.addRouter) # self.addRouter function callback
        dialog.exec()

    #DEBUG:
    def showDebugDialog(self):
        dialog = DebugDialog(self.addCable, self.removeCable) # self.addRouter and self.removeCable function callback
        dialog.exec()

    def addRouter(self, device_parameters, x, y):
        router = Router(device_parameters, x, y)
        self.view.scene.addItem(router)
        
        #DEBUG: Show border around router
        if __debug__:
            self.view.scene.addItem(router.border)
            router.border.setPos(router.scenePos())

        return router
        
    
    def addCable(self, device_1, device_2):
        cable = Cable(device_1, device_2)
        cable.setZValue(-1) #All cables to the background
        self.view.scene.addItem(cable)
        return cable
    
    def removeCable(self, device_1, device_2):        
        cable_to_be_removed = [cable for cable in device_1.cables if cable in device_2.cables]
        cable_to_be_removed[0].removeCable()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    window.resize(800, 600)

    sys.exit(app.exec())