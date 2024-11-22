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
    QDockWidget,
    QMenu)
from PySide6.QtGui import ( 
    QBrush, 
    QColor, 
    QIcon, 
    QAction,
    QPixmap,
    QTransform,
    QCursor)

# Custom
from devices import Router
from cable import Cable, CableEditMode
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

        self.setWindowTitle("Netconf Configurator")
        self.view = MainView()
        self.setCentralWidget(self.view)

        self.createToolBar()
        self.consoleDockWidget = self.createConsoleWidget()
        self.addDockWidget(Qt.BottomDockWidgetArea, self.consoleDockWidget)

        self.normal_mode_handlers = self.saveMouseEventHandlers()

    def saveMouseEventHandlers(self):
        original_mousePressEvent = self.view.scene.mousePressEvent
        original_mouseMoveEvent = self.view.scene.mouseMoveEvent
        return(original_mousePressEvent, original_mouseMoveEvent)

    def restoreMouseEventHandlers(self, mouse_event_handlers):
        self.view.scene.mousePressEvent = mouse_event_handlers[0]
        self.view.scene.mouseMoveEvent = mouse_event_handlers[1]

    def createToolBar(self):
        self.toolbar = QToolBar("Toolbar", self)
        self.toolbar.setVisible(True)
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # "Add a device" button
        plus_icon_img = QIcon(QPixmap("graphics/icons/plus.png")) #https://www.freepik.com/icon/add_1082378#fromView=family&page=1&position=1&uuid=d639dba2-0441-47bb-a400-3b47c2034665
        action_connectToDevice = QAction(plus_icon_img, "Connect to a device", self)
        action_connectToDevice.triggered.connect(self.show_DeviceConnectionDialog)
        self.toolbar.addAction(action_connectToDevice)

        # "Cable edit mode" button
        cable_mode_img = QIcon(QPixmap("graphics/icons/cable_mode.png")) #https://www.freepik.com/icon/ethernet_9693285
        action_cableEditMode = QAction(cable_mode_img, "Cable edit mode", self)
        action_cableEditMode.setCheckable(True)
        action_cableEditMode.triggered.connect(self.toggleCableMode)
        self.toolbar.addAction(action_cableEditMode)

        # Debug" button
        #DEBUG: 
        if __debug__:
            action_debug = QAction("DEBUG", self)
            action_debug.triggered.connect(self.show_DebugDialog)
            self.toolbar.addAction(action_debug)

        self.addToolBar(self.toolbar)                

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
    
    def cableModeButtonIsChecked(self):
        return self.toolbar.actions()[1].isChecked()

    def toggleCableMode(self):
        if self.cableModeButtonIsChecked():
            self.cable_edit_mode = CableEditMode(self)
        else:
            self.restoreMouseEventHandlers(self.normal_mode_handlers)
            self.cable_edit_mode.dontRenderTmpCable()
            self.cable_edit_mode.changeCursor("normal")
            del self.cable_edit_mode


class ConsoleStream(StringIO):
    # Redirects stdout and/or stderr to the integrated console widget
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
    