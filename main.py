# Other
import sys
from io import StringIO

# QT
from PySide6.QtCore import Qt, Signal, QObject, QRectF
from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QGraphicsView, 
    QGraphicsScene,  
    QToolBar,
    QPlainTextEdit,
    QDockWidget,
    QMenu,
    QGraphicsRectItem)
from PySide6.QtGui import ( 
    QBrush, 
    QColor, 
    QIcon, 
    QAction,
    QPixmap,
    QTransform,
    QCursor,
    QPen)

# Custom
from devices import Device, Router
from cable import Cable, CableEditMode
from dialogs import *
from definitions import STDOUT_TO_CONSOLE, STDERR_TO_CONSOLE, DARK_MODE

sys.argv += ['-platform', 'windows:darkmode=2'] if DARK_MODE else ['-platform', 'windows:darkmode=1']

class MainView(QGraphicsView):
    CURSOR_MODES = {
        "device1_selection_mode": "graphics/cursors/device1_selection_mode.png",
        "device2_selection_mode": "graphics/cursors/device2_selection_mode.png",
        "delete_cable_mode": "graphics/cursors/delete_cable_mode.png", # https://www.freepik.com/icon/close_14440511#fromView=search&page=2&position=40&uuid=6e978c49-dea0-4abd-bc85-7785d1bd8f7f
        "normal": None
    }
        
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.rubber_band = None
        self.start_pos = None

        self._loadCursors()
        
    def _loadCursors(self):
        self.cursors = {
            mode: QCursor(QPixmap(cursor_path)) if cursor_path else None
            for mode, cursor_path in self.CURSOR_MODES.items()
        }

    def _changeCursor(self, mode):
        if mode in self.cursors and self.cursors[mode]:
            self.setCursor(self.cursors[mode])
        else:
            self.setCursor(Qt.ArrowCursor)

    def changeMouseBehaviour(self, cursor=None, mouse_press_event=None, mouse_move_event=None, mouse_release_event=None, tracking: bool = None):
        if cursor: 
            self._changeCursor(cursor)
        if mouse_press_event: 
            self.scene.mousePressEvent = mouse_press_event
        if mouse_move_event: 
            self.scene.mouseMoveEvent = mouse_move_event
        if mouse_release_event:
            self.scene.mouseReleaseEvent = mouse_release_event
        if tracking:
            self.setMouseTracking(tracking)

    def _createRubberBand(self, event):
        self.start_pos = self.mapToScene(event.position().toPoint())
        self.rubber_band = QGraphicsRectItem()
        self.rubber_band.setPen(QPen(Qt.DashLine))
        self.scene.addItem(self.rubber_band)
    
    def _removeRubberBand(self):
        if self.rubber_band:
            self.scene.removeItem(self.rubber_band)
            self.rubber_band = None

    def _updateRubberBand(self, event):
        current_pos = self.mapToScene(event.position().toPoint())
        rect = QRectF(self.start_pos, current_pos).normalized()
        self.rubber_band.setRect(rect)

    def _makeSelectionWithRubberBand(self, event):
        rect = self.rubber_band.rect()
        self.scene.removeItem(self.rubber_band)
        self.rubber_band = None

        # Select all items within the rectangle
        items = self.scene.items(rect, Qt.IntersectsItemShape)
        for item in items:
            item.setSelected(True)
 
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._removeRubberBand()
            self._createRubberBand(event)    

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.rubber_band and self.start_pos:
            if not self.scene.selectedItems() and not self.window().cableModeButtonIsChecked():
                self._updateRubberBand(event)
        
        for item in self.scene.selectedItems():
            if isinstance(item, Device):
                item.updateCablePositions()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.rubber_band:
            self._makeSelectionWithRubberBand(event)

        self.start_pos = None
        super().mouseReleaseEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Netconf Configurator")
        self.view = MainView()
        self.setCentralWidget(self.view)

        self.createToolBar()
        self.consoleDockWidget = self.createConsoleWidget()
        self.addDockWidget(Qt.BottomDockWidgetArea, self.consoleDockWidget)

        self.normal_mode_mouse_handlers = {
            "mousePressEvent": self.view.scene.mousePressEvent, 
            "mouseMoveEvent": self.view.scene.mouseMoveEvent,
            "mouseReleaseEvent": self.view.scene.mouseReleaseEvent
            }


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
            self.cable_edit_mode.exitMode()


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
    