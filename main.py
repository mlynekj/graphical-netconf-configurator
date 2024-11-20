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
        self.toolbar = QToolBar("Toolbar", self)
        self.toolbar.setVisible(True)
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # "Add a device" button
        plus_icon_img = QIcon(QPixmap("graphics/icons/plus.png")) #https://www.freepik.com/icon/add_1082378#fromView=family&page=1&position=1&uuid=d639dba2-0441-47bb-a400-3b47c2034665
        action_connectToDevice = QAction(plus_icon_img, "Connect to a device", self)
        action_connectToDevice.triggered.connect(self.show_DeviceConnectionDialog)
        self.toolbar.addAction(action_connectToDevice)

        # "Cable mode" button
        cable_mode_img = QIcon(QPixmap("graphics/icons/cable_mode.png")) #https://www.freepik.com/icon/ethernet_9693285
        action_cableMode = QAction(cable_mode_img, "Cable mode", self)
        action_cableMode.setCheckable(True)
        action_cableMode.triggered.connect(self.toggleCableMode)
        self.toolbar.addAction(action_cableMode)

        # Debug" button
        #DEBUG: 
        if __debug__:
            action_debug = QAction("DEBUG", self)
            action_debug.triggered.connect(self.show_DebugDialog)
            self.toolbar.addAction(action_debug)

        self.addToolBar(self.toolbar)                

    def cableModeButtonIsChecked(self):
        return self.toolbar.actions()[1].isChecked()

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

    def toggleCableMode(self):
        if self.cableModeButtonIsChecked():
            self.cable_mode = CableMode(self)
        else:
            self.cable_mode.restoreMouseEventHandlers(self.cable_mode.normal_mode_handlers)
            QApplication.restoreOverrideCursor()
            del self.cable_mode


class CableMode(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.view = parent.view
        self.scene = parent.view.scene

        self.cable_mode_cursor = QCursor(QPixmap("graphics/icons/cable_mode_cursor.png"))

        self.device1 = None
        self.device2 = None
        self.device1_interface = None
        self.device2_interface = None

        self.normal_mode_handlers = self.saveMouseEventHandlers()
        self.view.scene.mousePressEvent = self.device1SelectionMode

    @property
    def buttonIsChecked(self):
        return self.parent.toolbar.actions()[1].isChecked()

    def saveMouseEventHandlers(self):
        original_mousePressEvent = self.view.scene.mousePressEvent
        original_mouseMoveEvent = self.view.scene.mouseMoveEvent
        return(original_mousePressEvent, original_mouseMoveEvent)

    def restoreMouseEventHandlers(self, mouse_event_handlers):
        self.view.scene.mousePressEvent = mouse_event_handlers[0]
        self.view.scene.mouseMoveEvent = mouse_event_handlers[1]

    # ----------------- DEVICE1 -----------------
    def device1SelectionMode(self, event):
        self.device1 = self.view.scene.itemAt(event.scenePos(), QTransform())
        self.device1InterfaceSelectionMode(event)

    def device1InterfaceSelectionMode(self, event):
        menu = QMenu()

        for interface in self.device1.interfaces:
            interface_action = QAction(interface[0], menu)
            interface_action.triggered.connect(lambda checked, intf=interface[0]: self.device1InterfaceSelectionModeConfirm(intf))
            menu.addAction(interface_action)
        menu.exec(event.screenPos())

    def device1InterfaceSelectionModeConfirm(self, interface):
        self.device1_interface = interface
        
        
        QApplication.setOverrideCursor(self.cable_mode_cursor)
        self.device1_selection_mode_handlers = self.saveMouseEventHandlers()
        self.view.scene.mousePressEvent = self.device2SelectionMode

    # ----------------- DEVICE2 -----------------
    def device2SelectionMode(self, event):
        self.device2 = self.view.scene.itemAt(event.scenePos(), QTransform())
        if self.device2 == self.device1: # Dont allow connecting a device to itself
            self.restoreMouseEventHandlers(self.device1_selection_mode_handlers)
            QApplication.restoreOverrideCursor()
            return
        else:
            self.restoreMouseEventHandlers(self.device1_selection_mode_handlers)
            self.device2InterfaceSelectionMode(event)
            QApplication.restoreOverrideCursor()

    def device2InterfaceSelectionMode(self, event):
        menu = QMenu()

        for interface in self.device2.interfaces:
            interface_action = QAction(interface[0], menu)
            interface_action.triggered.connect(lambda checked, intf=interface[0]: self.device2InterfaceSelectionModeConfirm(intf))
            menu.addAction(interface_action)
        menu.exec(event.screenPos())

    def device2InterfaceSelectionModeConfirm(self, interface):
        self.device2_interface = interface
        self.addCable(self.device1, self.device1_interface, self.device2, self.device2_interface)

    # ----------------- MANAGEMENT OF THE CABLES -----------------
    def addCable(self, device1, device1_interface, device2, device2_interface):
        cable = Cable(device1, device1_interface, device2, device2_interface)
        cable.setZValue(-1) #All cables to the background
        self.view.scene.addItem(cable)
        return(cable)
    
    def removeCable(self, device1, device2):        
        cable_to_be_removed = [cable for cable in device1.cables if cable in device2.cables]
        cable_to_be_removed[0].removeCable()

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
    