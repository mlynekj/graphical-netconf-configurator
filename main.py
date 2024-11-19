# Other
import sys
from io import StringIO

# QT
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QGraphicsView, 
    QGraphicsScene,  
    QToolBar,
    QPlainTextEdit,
    QDockWidget)
from PySide6.QtGui import ( 
    QBrush, 
    QColor, 
    QIcon, 
    QAction,
    QPixmap)

# Custom
from devices import Router, Cable
from dialogs import *
from definitions import STDOUT_TO_CONSOLE, STDERR_TO_CONSOLE, DARK_MODE

sys.argv += ['-platform', 'windows:darkmode=2'] if DARK_MODE else ['-platform', 'windows:darkmode=1']

class MainView(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Network Configurator")
        self.view = MainView()
        self.setCentralWidget(self.view)

        self.createToolBar()
        self.consoleDockWidget = self.createConsoleWidget()
        self.addDockWidget(Qt.BottomDockWidgetArea, self.consoleDockWidget)

    def createToolBar(self):
        toolbar = QToolBar("Toolbar", self)
        toolbar.setVisible(True)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # "Add a device" button
        plus_icon_img = QIcon(QPixmap("graphics/icons/plus.png")) #https://www.freepik.com/icon/add_1082378#fromView=family&page=1&position=1&uuid=d639dba2-0441-47bb-a400-3b47c2034665
        action_connectToDevice = QAction(plus_icon_img, "Connect to a device", self)
        action_connectToDevice.triggered.connect(self.show_DeviceConnectionDialog)
        toolbar.addAction(action_connectToDevice)

        #DEBUG: 
        if __debug__:
            action_debug = QAction("DEBUG", self)
            action_debug.triggered.connect(self.show_DebugDialog)
            toolbar.addAction(action_debug)

        self.addToolBar(toolbar)

    def createConsoleWidget(self):
        console = QPlainTextEdit()
        console.setReadOnly(True)

        if STDOUT_TO_CONSOLE:
            sys.stdout = ConsoleStream(console)
        if STDERR_TO_CONSOLE:
            sys.stderr = ConsoleStream(console)

        dock = QDockWidget("Console", self)
        dock.setWidget(console)
        dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        return dock
        
    def show_DeviceConnectionDialog(self):
        dialog = AddDeviceDialog(self.addRouter) # self.addRouter function callback
        dialog.exec()

    #DEBUG:
    def show_DebugDialog(self):
        dialog = DebugDialog(self.addCable, self.removeCable) # self.addRouter and self.removeCable function callback
        dialog.exec()

    def addRouter(self, device_parameters, x, y):
        router = Router(device_parameters, x, y)
        self.view.scene.addItem(router)

        return(router)
    
    def addCable(self, device_1, device_2):
        cable = Cable(device_1, device_2)
        cable.setZValue(-1) #All cables to the background
        self.view.scene.addItem(cable)
        return(cable)
    
    def removeCable(self, device_1, device_2):        
        cable_to_be_removed = [cable for cable in device_1.cables if cable in device_2.cables]
        cable_to_be_removed[0].removeCable()


class ConsoleStream(StringIO):
    # Redirects stdout and stderr to the integrated console widget
    def __init__(self, console_widget):
        super().__init__()
        self.console_widget = console_widget

    def write(self, text):
        self.console_widget.appendPlainText(text)
        self.console_widget.ensureCursorVisible()

    def flush(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    window.resize(800, 600)

    sys.exit(app.exec())
    