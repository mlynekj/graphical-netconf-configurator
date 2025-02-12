# Other
import sys
from io import StringIO
from contextlib import contextmanager
import json

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
    QGraphicsRectItem,
    QSizePolicy,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QPushButton,
    QHeaderView,
    QLabel,
    QMessageBox)
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
from devices import Device, Router, Switch, AddDeviceDialog
from cable import Cable, CableEditMode
from signals import signal_manager
import modules.netconf as netconf
import helper as helper
import modules.ospf as ospf
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

    @contextmanager
    def generateClonedScene(self):
        selected_items = self.scene.selectedItems()
        if not selected_items:
            yield(None)
            return
        
        cloned_scene = QGraphicsScene()
        cloned_devices = []
        cloned_devices_ids = []
        device_id_map = {}

        # Create cloned devices, based selection
        for item in selected_items:
            if isinstance(item, Device):
                new_device = item.cloneToOSPFDevice()
                cloned_scene.addItem(new_device)
                cloned_devices.append(new_device)
                cloned_devices_ids.append(new_device.id)
                device_id_map[item.id] = new_device

        # Create cables between cloned devices, if the cables exist in the original scene
        connected_pairs = set()
        for cloned_device in cloned_devices:
            for cable in cloned_device.original_cables:
                # Check if both devices of the cable are in the cloned devices, if not, skip
                if cable.device1.id not in cloned_devices_ids or cable.device2.id not in cloned_devices_ids: 
                    continue

                # make sure that only one cable is created between two devices (not two cables in opposing directions)
                device_pair = tuple(sorted([cable.device1.id, cable.device2.id]))
                if device_pair not in connected_pairs:
                    device1_copy = device_id_map[cable.device1.id]
                    device2_copy = device_id_map[cable.device2.id]
                    cloned_cable = Cable(device1_copy, cable.device1_interface, device2_copy, cable.device2_interface) # The cable must be created with reference to the cloned devices
                    cloned_scene.addItem(cloned_cable)
                    connected_pairs.add(device_pair)

        # Needed for contextmanager (when the dialog is closed, the scene is cleared and all items are removed)
        try:
            yield(cloned_scene)
        finally:
            for item in cloned_scene.items():
                cloned_scene.removeItem(item)
            cloned_scene.clear()


    # ---------- MOUSE BEHAVIOUR AND APPEREANCE FUNCTIONS ----------         
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

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._removeRubberBand()
            self._createRubberBand(event)    

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.rubber_band:
            self._makeSelectionWithRubberBand(event)

        self.start_pos = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.rubber_band and self.start_pos:
            if not self.scene.selectedItems() and not self.window()._cableModeButtonIsChecked():
                self._updateRubberBand(event)
        
        for item in self.scene.selectedItems():
            if isinstance(item, Device):
                item.updateCablePositions()

        super().mouseMoveEvent(event)
        
    # ---------- RUBBER BAND FUNCTIONS ---------- 
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


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Netconf Configurator")
        self.view = MainView()
        self.setCentralWidget(self.view)

        self.normal_mode_mouse_handlers = {
            "mousePressEvent": self.view.scene.mousePressEvent, 
            "mouseMoveEvent": self.view.scene.mouseMoveEvent,
            "mouseReleaseEvent": self.view.scene.mouseReleaseEvent
            }

        # Toolbar
        self._createToolBar()

        # Console dock
        self.consoleDockWidget = ConsoleWidget()
        self.addDockWidget(Qt.BottomDockWidgetArea, self.consoleDockWidget)

        # Protocols configuration dock
        self.protocolsWidget = ProtocolsWidget(self.view)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.protocolsWidget)

        # Pending changes dock
        self.pendigChangesDockWidget = PendingChangesWidget()
        self.addDockWidget(Qt.RightDockWidgetArea, self.pendigChangesDockWidget)

    def _createToolBar(self):
        self.toolbar = QToolBar("Toolbar", self)
        self.toolbar.setVisible(True)
        self.toolbar.setMovable(False)
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # "Add a device" button
        plus_icon_img = QIcon(QPixmap("graphics/icons/plus.png")) #https://www.freepik.com/icon/add_1082378#fromView=family&page=1&position=1&uuid=d639dba2-0441-47bb-a400-3b47c2034665
        action_connectToDevice = QAction(plus_icon_img, "Connect to a device", self)
        action_connectToDevice.triggered.connect(self._showDeviceConnectionDialog)
        self.toolbar.addAction(action_connectToDevice)

        # "Cable edit mode" button
        cable_mode_img = QIcon(QPixmap("graphics/icons/cable_mode.png")) #https://www.freepik.com/icon/ethernet_9693285
        action_cableEditMode = QAction(cable_mode_img, "Cable edit mode", self)
        action_cableEditMode.setCheckable(True)
        action_cableEditMode.triggered.connect(self._toggleCableMode)
        self.toolbar.addAction(action_cableEditMode)

        # "Load devices from file" button
        load_devices_img = QIcon(QPixmap("graphics/icons/load.png")) # https://www.freepik.com/icon/file_892070#fromView=search&page=1&position=43&uuid=50ac52f8-baa0-416e-bdb5-fa1dde310592
        action_loadDevices = QAction(load_devices_img, "Load devices from file", self)
        action_loadDevices.setToolTip("Load devices from a JSON file \"saved_devices.json\"")
        action_loadDevices.triggered.connect(self._loadDevicesFromFile)
        self.toolbar.addAction(action_loadDevices)


        self.addToolBar(self.toolbar)                
  
    def _showDeviceConnectionDialog(self):
        dialog = AddDeviceDialog(self.view)
        dialog.exec()
    
    def _cableModeButtonIsChecked(self):
        return self.toolbar.actions()[1].isChecked()

    def _toggleCableMode(self):
        if self._cableModeButtonIsChecked():
            self.cable_edit_mode = CableEditMode(self)
        else:
            self.cable_edit_mode.exitMode()

    def _loadDevicesFromFile(self):
        try:
            with open("saved_devices.json") as f:
                data = json.load(f)
                for device in data["devices"]:
                    device_parameters = {}

                    address_field = device["ip_address"].split(":")
                    if len(address_field) == 2:
                        device_parameters["address"] = address_field[0]
                        device_parameters["port"] = address_field[1]
                    elif len(address_field) == 1:
                        device_parameters["address"] = device["ip_address"]
                        device_parameters["port"] = 830
                        
                    device_parameters["username"] = device["username"]
                    device_parameters["password"] = device["password"]
                    device_parameters["device_params"] = device["vendor"]

                    if device["type"] == "Router":
                        router = Router(device_parameters, x=device["location"]["x"], y=device["location"]["y"])
                        self.view.scene.addItem(router)
                    elif device["type"] == "Switch":
                        switch = Switch(device_parameters, x=device["location"]["x"], y=device["location"]["y"])
                        self.view.scene.addItem(switch)
        except FileNotFoundError:
            QMessageBox.warning(self, "File not found", "File \"saved_devices.json\" not found.", QMessageBox.Ok)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occured while loading devices from file: {e}", QMessageBox.Ok)

# Bottom dock widget
class ConsoleWidget(QDockWidget):
    def __init__(self):
        super().__init__("Console")

        self.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)

        self.consoleTextField = QPlainTextEdit()
        self.consoleTextField.setReadOnly(True)

        if STDOUT_TO_CONSOLE:
            sys.stdout = ConsoleStream(self.consoleTextField)
        if STDERR_TO_CONSOLE:
            sys.stderr = ConsoleStream(self.consoleTextField)

        self.setWidget(self.consoleTextField)


# Left dock widget
class ProtocolsWidget(QDockWidget):
    def __init__(self, main_view):
        super().__init__("Configure protocols")

        self.main_view = main_view

        title_label = QLabel("Configure protocols")
        title_label.setAlignment(Qt.AlignCenter)
        self.setTitleBarWidget(title_label)

        self.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.setFixedWidth(150)
    
        button_holder = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        # OSPF button
        ospf_button = QPushButton("OSPF")
        ospf_button.clicked.connect(self._showOSPFDialog)
        layout.addWidget(ospf_button)
        
        # MPLS button
        mpls_button = QPushButton("MPLS")
        layout.addWidget(mpls_button)

        button_holder.setLayout(layout)
        self.setWidget(button_holder)

    def _showOSPFDialog(self):
        with self.main_view.generateClonedScene() as cloned_scene:
            if cloned_scene:
                dialog = ospf.OSPFDialog(cloned_scene)
                dialog.exec()
            else:
                QMessageBox.warning(self, "Warning", "Select devices to configure OSPF on!", QMessageBox.Ok)


# Right dock widget
class PendingChangesWidget(QDockWidget):
    def __init__(self):
        super().__init__("Pending changes")

        title_label = QLabel("Pending changes")
        title_label.setAlignment(Qt.AlignCenter)
        self.setTitleBarWidget(title_label)

        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.setFixedWidth(250)
        self.setContentsMargins(0, 0, 0, 0)

        # Signals
        signal_manager.pendingChangeAdded.connect(self.addPendingChangeToTable)
        signal_manager.deviceNoLongerHasPendingChanges.connect(self.clearPendingChangesFromTable)

        # Table with pending changes
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["ID", "Change"])
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # First column
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Second column
        self.table_widget.setSortingEnabled(True)

        # Commit button
        self.commit_button = QPushButton("Commit all changes") # TODO: muze byt verify + commit, nebu muzu udelat dva button a druhy bude "confirmed commit" (nebo funkce confirmed commitu bude v "commit" tlacitku)
        self.commit_button.clicked.connect(self._commitPendingChanges)

        # Discard all changes button
        # TODO: self.discard_button = QPushButton("Discard all changes")

        # Layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.table_widget)
        self.layout.addWidget(self.commit_button)
        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setWidget(self.container)

    def addPendingChangeToTable(self, device_id, change):
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)

        device_item = QTableWidgetItem(device_id)
        device_item.setFlags(device_item.flags() ^ Qt.ItemIsEditable)  # Non-editable cells
        self.table_widget.setItem(row_position, 0, device_item)

        change_item = QTableWidgetItem(change)
        change_item.setFlags(change_item.flags() ^ Qt.ItemIsEditable)  # Non-editable cells
        self.table_widget.setItem(row_position, 1, change_item)

    def clearPendingChangesFromTable(self, device_id):
        for row in range(self.table_widget.rowCount() - 1, -1, -1): # Iterate backwards to avoid skipping rows
            if self.table_widget.item(row, 0).text() == device_id:
                self.table_widget.removeRow(row)

    def _commitPendingChanges(self):
        commited_devices = []
        devices = Device.getAllDevicesInstances()

        try:
            for device in devices:
                if device.has_pending_changes:
                    device.commitChanges()
                    self.clearPendingChangesFromTable(device.id)
                    commited_devices.append(device.id)
                if device.has_updated_hostname: # Refresh the hostname label on canvas, if it was updated
                    device.has_updated_hostname = False
                    device.refreshHostnameLabel()
        
            if commited_devices:
                helper.printGeneral(f"Performed commit on devices with ID: {', '.join(commited_devices)}")
            else:
                helper.showMessageBox(self, "No pending changes", "No pending changes to commit.")

        except Exception as e:
            helper.showMessageBox(self, "Commit failed", f"Failed to commit changes on one or more devices: {e}")


class ConsoleStream(StringIO):
    """
    Class that redirects stdout and/or stderr to an integrated console widget.
    """

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
    window.resize(1024, 768)

    sys.exit(app.exec())
    