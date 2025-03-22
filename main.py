# ---------- IMPORTS: ----------
# Standard library
import sys
import json
import time
import traceback
from io import StringIO
from contextlib import contextmanager
from threading import Thread, Event

# Custom modules
from devices import Device, AddDeviceDialog, addFirewall, addRouter, addSwitch
from cable import Cable, CableEditMode
from signals import signal_manager
import utils
import modules.ospf as ospf
import modules.security as security
import modules.vlan as vlan
from definitions import STDOUT_TO_CONSOLE, STDERR_TO_CONSOLE, DARK_MODE

# Qt
from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QGraphicsView, 
    QGraphicsScene,  
    QToolBar,
    QPlainTextEdit,
    QDockWidget,
    QGraphicsRectItem,
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QPushButton,
    QHeaderView,
    QLabel,
    QMessageBox,
    QDialog,
    QComboBox)
from PySide6.QtGui import ( 
    QIcon, 
    QAction,
    QPixmap,
    QCursor,
    QPen)
from PySide6.QtCore import Qt, QRectF

# QtCreator
from ui.ui_pendingchangedetailsdialog import Ui_PendingChangeDetailsDialog


sys.argv += ['-platform', 'windows:darkmode=2'] if DARK_MODE else ['-platform', 'windows:darkmode=1']


# ---------- QT CLASSES----------
class MainView(QGraphicsView):
    CURSOR_MODES = {
        "device1_selection_mode": "graphics/cursors/device1_selection_mode.png",
        "device2_selection_mode": "graphics/cursors/device2_selection_mode.png",
        "delete_cable_mode": "graphics/cursors/delete_cable_mode.png", # https://www.freepik.com/icon/close_14440511#fromView=search&page=2&position=40&uuid=6e978c49-dea0-4abd-bc85-7785d1bd8f7f
        "normal": None
    }

    def __init__(self) -> QGraphicsView:
        super().__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.rubber_band = None
        self.start_pos = None

        self._loadCursors()

    @contextmanager
    def generateClonedScene(self, used_for = "OSPF") -> QGraphicsScene: # type: ignore
        """
        Generates a cloned QGraphicsScene containing selected devices and their connections.
        This method clones the selected items from the current scene into a new QGraphicsScene.
        It supports cloning devices and their associated cables, ensuring that only connections
        between the cloned devices are included. The cloned scene is designed to be used in
        specific contexts, such as OSPF configuration.
        Args:
            used_for (str): Specifies the purpose of the cloned scene. Defaults to "OSPF".
                            Currently, it determines the type of cloned devices to create.
        Yields:
            QGraphicsScene: A new scene containing the cloned devices and their connections.
        Notes:
            - The method uses a context manager to ensure that the cloned scene is properly
                cleared and all items are removed when the context is exited.
        """

        selected_items = self.scene.selectedItems()
        if not selected_items:
            yield(None)
            return
        
        cloned_scene = QGraphicsScene()
        cloned_devices = []
        cloned_devices_ids = []
        device_id_map = {}

        # Create cloned devices, based on selection
        for item in selected_items:
            if isinstance(item, Device):
                if used_for == "OSPF":
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
    def _loadCursors(self) -> None:
        """Loads custom cursors for different modes defined in the CURSOR_MODES dictionary."""

        self.cursors = {
            mode: QCursor(QPixmap(cursor_path)) if cursor_path else None
            for mode, cursor_path in self.CURSOR_MODES.items()
        }

    def _changeCursor(self, mode) -> None:
        """
        Changes the cursor of the application based on the specified mode.
        Args:
            mode (str): The mode for which the cursor should be changed. 
                        It should be a key in the `self.cursors` dictionary.
        Behavior:
            - If the specified mode exists in `self.cursors` and has a valid cursor, 
              the cursor is set to the corresponding value.
            - If the mode is not found or has no valid cursor, the cursor defaults 
              to the standard arrow cursor (Qt.ArrowCursor).
        """

        if mode in self.cursors and self.cursors[mode]:
            self.setCursor(self.cursors[mode])
        else:
            self.setCursor(Qt.ArrowCursor)

    def changeMouseBehaviour(self, cursor=None, mouse_press_event=None, mouse_move_event=None, mouse_release_event=None, tracking: bool = None) -> None:
        """
        Modifies the behavior of the mouse within the scene by updating the cursor, 
        mouse event handlers, and mouse tracking settings.
        Args:
            cursor (QCursor, optional): The cursor to be displayed. If provided, 
                it updates the current cursor.
            mouse_press_event (function, optional): A custom function to handle 
                mouse press events. If provided, it replaces the default handler.
            mouse_move_event (function, optional): A custom function to handle 
                mouse move events. If provided, it replaces the default handler.
            mouse_release_event (function, optional): A custom function to handle 
                mouse release events. If provided, it replaces the default handler.
            tracking (bool, optional): Enables or disables mouse tracking. If True, 
                mouse tracking is enabled; otherwise, it is disabled.
        """

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

    def mousePressEvent(self, event) -> None:
        """
        Handles the mouse press event for the widget.
        This method is triggered when a mouse button is pressed within the widget.
        If the left mouse button is pressed, it removes any existing rubber band
        selection and creates a new rubber band starting at the mouse event's position.
        """

        if event.button() == Qt.LeftButton:
            self._removeRubberBand()
            self._createRubberBand(event)    

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """
        Handles the mouse release event.
        This method is triggered when the mouse button is released. If a rubber band
        selection is active, it processes the selection using the `_makeSelectionWithRubberBand`
        method. It also resets the starting position of the mouse drag and ensures
        the parent class's `mouseReleaseEvent` is called.
        """

        if self.rubber_band:
            self._makeSelectionWithRubberBand(event)

        self.start_pos = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """
        Handles the mouse move event within the application.
        This method performs the following actions:
        1. Updates the rubber band selection rectangle if it exists, the starting position is set,
           no items are selected in the scene, and the cable mode button is not checked.
        2. Updates the cable positions for all selected items in the scene that are instances of the `Device` class.
        3. Calls the parent class's `mouseMoveEvent` to ensure default behavior is preserved.
        """

        if self.rubber_band and self.start_pos:
            if not self.scene.selectedItems() and not self.window()._cableModeButtonIsChecked():
                self._updateRubberBand(event)
        
        for item in self.scene.selectedItems():
            if isinstance(item, Device):
                item.updateCablePositions()

        super().mouseMoveEvent(event)
        
    # ---------- RUBBER BAND FUNCTIONS ---------- 
    def _createRubberBand(self, event) -> None:
        """
        Initializes and creates a rubber band selection rectangle on the scene.
        This method is triggered by a mouse event and is used to create a 
        rectangular selection area (rubber band) on the scene. It sets the 
        starting position of the selection based on the mouse event, creates 
        a QGraphicsRectItem to represent the rubber band, and adds it to the scene.
        """
        
        self.start_pos = self.mapToScene(event.position().toPoint())
        self.rubber_band = QGraphicsRectItem()
        self.rubber_band.setPen(QPen(Qt.DashLine))
        self.scene.addItem(self.rubber_band)
    
    def _removeRubberBand(self) -> None:
        """
        Removes the rubber band item from the scene if it exists.
        This method checks if a rubber band item is currently present.
        If it exists, the method removes it from the scene and sets
        the `rubber_band` attribute to None.
        """

        if self.rubber_band:
            self.scene.removeItem(self.rubber_band)
            self.rubber_band = None

    def _updateRubberBand(self, event) -> None:
        """
        Updates the rubber band rectangle based on the current mouse position.
        This method is typically called during a mouse drag event to dynamically
        adjust the size and position of the rubber band selection rectangle.
        """

        current_pos = self.mapToScene(event.position().toPoint())
        rect = QRectF(self.start_pos, current_pos).normalized()
        self.rubber_band.setRect(rect)

    def _makeSelectionWithRubberBand(self, event) -> None:
        """
        Handles the selection of items within a rectangular area defined by a rubber band.
        This method finalizes the selection process by determining the rectangular area
        created by the rubber band, removing the rubber band from the scene, and selecting
        all items within the rectangle.
        """
        
        rect = self.rubber_band.rect()
        self.scene.removeItem(self.rubber_band)
        self.rubber_band = None

        # Select all items within the rectangle
        items = self.scene.items(rect, Qt.IntersectsItemShape)
        for item in items:
            item.setSelected(True)


class MainWindow(QMainWindow):
    def __init__(self) -> QMainWindow:
        super().__init__()

        self.setWindowTitle("GNC - Graphical NETCONF configurator")
        gnc_icon = QPixmap("graphics/icons/gnc.png")
        self.setWindowIcon(QIcon(gnc_icon))
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
        self.batchConfigurationWidget = BatchConfigurationWidget(self.view)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.batchConfigurationWidget)

        # Pending changes dock
        self.pendigChangesDockWidget = PendingChangesWidget()
        self.addDockWidget(Qt.RightDockWidgetArea, self.pendigChangesDockWidget)

    def _createToolBar(self) -> None:
        """Creates a toolbar with buttons for adding devices, toggling cable edit mode, and saving/loading devices."""
        self.toolbar = QToolBar("Toolbar", self)
        self.toolbar.setVisible(True)
        self.toolbar.setMovable(False)
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # "Add a device" button
        plus_icon_img = QIcon(QPixmap("graphics/icons/plus.png")) # https://www.freepik.com/icon/add_1082378#fromView=family&page=1&position=1&uuid=d639dba2-0441-47bb-a400-3b47c2034665
        action_connectToDevice = QAction(plus_icon_img, "Connect to a device", self)
        action_connectToDevice.triggered.connect(self._showDeviceConnectionDialog)
        self.toolbar.addAction(action_connectToDevice)

        # "Cable edit mode" button
        cable_mode_img = QIcon(QPixmap("graphics/icons/cable_mode.png")) # https://www.freepik.com/icon/ethernet_9693285
        action_cableEditMode = QAction(cable_mode_img, "Cable edit mode", self)
        action_cableEditMode.setCheckable(True)
        action_cableEditMode.triggered.connect(self._toggleCableMode)
        self.toolbar.addAction(action_cableEditMode)

        # "Save devices to file" button
        save_device_img = QIcon(QPixmap("graphics/icons/save.png")) # https://www.freepik.com/icon/floppy-disk_12153581#fromView=search&page=1&position=71&uuid=fc4114bf-cd3d-45c7-8ce4-1daf851f9308
        action_saveDevices = QAction(save_device_img, "Save devices to file", self)
        action_saveDevices.setToolTip("Save devices to a JSON file \"saved_devices.json\"")
        action_saveDevices.triggered.connect(self._saveDevicesToFile)
        self.toolbar.addAction(action_saveDevices)

        # "Load devices from file" button
        load_devices_img = QIcon(QPixmap("graphics/icons/load.png")) # https://www.freepik.com/icon/file-upload_12153583#fromView=resource_detail&position=0
        action_loadDevices = QAction(load_devices_img, "Load devices from file", self)
        action_loadDevices.setToolTip("Load devices from a JSON file \"saved_devices.json\"")
        action_loadDevices.triggered.connect(self._loadDevicesFromFile)
        self.toolbar.addAction(action_loadDevices)

        self.addToolBar(self.toolbar)                
  
    def _showDeviceConnectionDialog(self) -> None:
        """Shows the dialog for adding a new device to the scene."""
        dialog = AddDeviceDialog(self.view)
        dialog.exec()
    
    def _cableModeButtonIsChecked(self) -> bool:
        """Returns True if the cable edit mode button is checked, False otherwise."""
        return self.toolbar.actions()[1].isChecked()

    def _toggleCableMode(self) -> None:
        """Toggles the cable edit mode on and off."""
        if self._cableModeButtonIsChecked():
            self.cable_edit_mode = CableEditMode(self)
        else:
            self.cable_edit_mode.exitMode()

    def _saveDevicesToFile(self) -> None:
        """
        Saves the devices present in the scene to a JSON file named 'saved_devices.json'.
        This method iterates through the devices in the scene, collects their parameters, 
        and writes them to a JSON file. The passwords are stored in a plain-text format.
        The saved data includes:
        - Device type
        - IP address and port
        - Username and password
        - Vendor information
        - Device location (x, y coordinates)
        """

        if not self.view.scene.items():
            QMessageBox.warning(self, "No devices", "There are no devices in the scene to save.", QMessageBox.Ok)
            return
        
        with open("saved_devices.json", mode="w") as f:
            data = {
                "devices": []
            }

            for device in self.view.scene.items():
                if isinstance(device, Device): # ignore cables
                    device_data = {
                        "type": type(device).__name__,
                        "ip_address": f"{device.device_parameters['address']}:{device.device_parameters['port']}",
                        "username": device.device_parameters["username"],
                        "password": device.device_parameters["password"],
                        "vendor": device.device_parameters["device_params"],
                        "location": {
                            "x": device.pos().x(),
                            "y": device.pos().y()
                        }
                    }
                    data["devices"].append(device_data)
            
            json.dump(data, f, indent=4)

    def _loadDevicesFromFile(self) -> None:
        """Loads device configurations from a JSON file and creates device instances."""

        try:
            with open("saved_devices.json") as f:
                data = json.load(f)
                if not data["devices"]:
                    QMessageBox.warning(self, "No devices", "There are no devices in the file to load.", QMessageBox.Ok)
                    return

                for device in data["devices"]:
                    # Create the "device_parameters" dictionary used for creating the device instance
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
       
                    # Create the device instance
                    self._createDeviceFromSave(device_parameters, device["type"], x=device["location"]["x"], y=device["location"]["y"])

        except FileNotFoundError:
            QMessageBox.warning(self, "File not found", "File \"saved_devices.json\" not found.", QMessageBox.Ok)
            utils.printGeneral(traceback.format_exc())
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occured while loading devices from file: {e}", QMessageBox.Ok)
            utils.printGeneral(traceback.format_exc())

    def _createDeviceFromSave(self, device_parameters, device_type, x, y) -> None:
        """
        Creates a device in the scene based on the provided parameters if a device with the same address
        does not already exist.
        """

        # Check if the device with the same address is not already in the scene
        for device in self.view.scene.items():
            if isinstance(device, Device):
                if device.device_parameters["address"] == device_parameters["address"]:
                    QMessageBox.warning(self, "Device already exists", f"The device with the address: {device_parameters["address"]} is already in the scene.")
                    return
        
        if "Router" in device_type:
            addRouter(device_parameters, self.view.scene, device_type)
        elif "Switch" in device_type:
            addSwitch(device_parameters, self.view.scene, device_type)
        elif "Firewall" in device_type:
            addFirewall(device_parameters, self.view.scene, device_type)


class ConsoleWidget(QDockWidget):
    """Widget in the bottom area of the main window that displays the console output."""

    def __init__(self) -> QDockWidget:
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


class BatchConfigurationWidget(QDockWidget):
    """
    Widget in the left area of the main window that contains buttons for configuring devices in bulk.
    Holds buttons for configuring OSPF, IPSEC, and VLANs on selected devices.
    """

    def __init__(self, main_view) -> QDockWidget:
        super().__init__("Batch configuration")

        self.main_view = main_view

        title_label = QLabel("Batch configuration")
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

        # IPSEC button
        ipsec_button = QPushButton("IPSEC")
        ipsec_button.clicked.connect(self._showIPSECDialog)
        layout.addWidget(ipsec_button)

        # VLAN button
        vlan_button = QPushButton("VLAN")
        vlan_button.clicked.connect(self._showVLANDialog)
        layout.addWidget(vlan_button)

        button_holder.setLayout(layout)
        self.setWidget(button_holder)

    def _showOSPFDialog(self) -> None:
        """
        Displays the OSPF configuration dialog.
        This method generates a cloned scene for OSPF configuration and opens
        the OSPF dialog if the cloned scene is successfully created.
        """

        selected_items = self.main_view.scene.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Select devices to configure OSPF on!", QMessageBox.Ok)
            return
        
        for device in selected_items:
            if hasattr(device, "is_ospf_capable") and device.is_ospf_capable == False:
                QMessageBox.critical(None, "Error", "One or both of the devices do not support OSPF configuration.")
                return

        with self.main_view.generateClonedScene("OSPF") as cloned_scene:
            dialog = ospf.OSPFDialog(cloned_scene)
            dialog.exec()

    def _showIPSECDialog(self) -> None:
        """Displays a dialog for configuring IPSEC on selected devices."""

        selected_items = self.main_view.scene.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Select devices to configure IPSEC on!", QMessageBox.Ok)
            return
        
        if len(selected_items) != 2:
            QMessageBox.warning(self, "Warning", "Select exactly two devices to configure IPSEC on!", QMessageBox.Ok)
            return
        
        for device in selected_items:
            if hasattr(device, "is_ipsec_capable") and device.is_ipsec_capable == False:
                QMessageBox.critical(None, "Error", "One or both of the devices do not support IPsec configuration.")
                return
            
        dialog = security.IPSECDialog(selected_items)
        dialog.exec()
            
    def _showVLANDialog(self) -> None:
        """Displays a VLAN configuration dialog for selected devices."""

        selected_items = self.main_view.scene.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Select devices to configure VLANs on!", QMessageBox.Ok)
            return

        vlan_supported_switches = []
        for device in selected_items:
            if hasattr(device, "is_vlan_capable") and device.is_vlan_capable == False:
                QMessageBox.critical(None, "Error", "One or more of the devices do not support VLAN configuration.")
                return
            else:
                vlan_supported_switches.append(device)

        dialog = vlan.EditVlansDialog(vlan_supported_switches)
        dialog.exec()


class PendingChangesWidget(QDockWidget):
    """
    Widget in the right area of the main window that contains elements for displaying changes made to devices, which have not yet been committed.
    It includes a table to display pending changes, buttons for committing, confirming, and discarding changes, and a timer for confirmed commits.
    Methods:
        addPendingChangeToTable(device_id, change_name, rpc_reply, filter):
            Adds a pending change to the table with details such as device ID, change name, and additional data.
        clearPendingChangesFromTable(device_id):
            Removes all pending changes for a specific device from the table.
        _showPendingChangeDetails(item):
            Displays detailed information about a pending change when a table item is double-clicked.
        _confirmedCommitPendingChanges():
            Initiates a confirmed commit with a timeout, updating the UI and starting a countdown timer.
        _confirmCommit():
            Confirms the confirmed commit, finalizing the changes and resetting the UI.
        _commitPendingChanges():
            Commits all pending changes without a timeout or confirmation.
        _discardAllPendingChanges():
            Discards all pending changes on all devices and updates the UI.
        _cancelConfirmedCommit():
            Cancels a confirmed commit, reverting changes and resetting the UI.
        _revertButtonsToDefaultState():
            Resets the buttons and UI elements to their default state after a commit or cancellation.
        _stopCountdown():
            Stops the countdown timer for a confirmed commit.
    """
            
    def __init__(self) -> QDockWidget:
        super().__init__("Pending changes")

        self.confirmed_commit_thread = None
        self.stop_countdown_event = Event()

        title_label = QLabel("Pending changes")
        title_label.setAlignment(Qt.AlignCenter)
        self.setTitleBarWidget(title_label)

        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.setFixedWidth(250)
        self.setContentsMargins(0, 0, 0, 0)

        # Table with pending changes
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["ID", "Change"])
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # First column
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Second column
        self.table_widget.setSortingEnabled(True)

        # Commit button
        self.commit_button = QPushButton("Commit")
        self.commit_button.clicked.connect(self._commitPendingChanges)

        # Confirmed commit button
        self.confirmed_commit_button = QPushButton("Confirmed commit")
        self.confirmed_commit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.confirmed_commit_button.clicked.connect(self._confirmedCommitPendingChanges)
        self.confirmed_commit_timer_combobox = QComboBox()
        self.confirmed_commit_timer_combobox.addItems(["1 min.", "2 min.", "5 min.", "10 min."])

        # Discard all changes button
        self.discard_button = QPushButton("Discard all")
        self.discard_button.clicked.connect(self._discardAllPendingChanges)

        # Layout
        self.layout = QVBoxLayout()
        self.confirmed_commit_buttons_layout = QHBoxLayout()
        self.confirmed_commit_buttons_layout.addWidget(self.confirmed_commit_button, stretch=1)
        self.confirmed_commit_buttons_layout.addStretch()
        self.confirmed_commit_buttons_layout.addWidget(self.confirmed_commit_timer_combobox)
        self.layout.addWidget(self.table_widget)
        self.layout.addLayout(self.confirmed_commit_buttons_layout)
        self.layout.addWidget(self.commit_button)
        self.layout.addWidget(self.discard_button)
        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setWidget(self.container)

        # Signals
        signal_manager.pendingChangeAdded.connect(self.addPendingChangeToTable)
        signal_manager.deviceNoLongerHasPendingChanges.connect(self.clearPendingChangesFromTable)
        self.table_widget.itemDoubleClicked.connect(self._showPendingChangeDetails)

    def addPendingChangeToTable(self, device_id, change_name, rpc_reply, filter) -> None:
        """
        Adds a pending change to the table widget with details about the device and change.
        The change can be double-clicked to show additional details.
        Args:
            device_id (str): The identifier of the device associated with the change.
            change_name (str): The name or description of the change.
            rpc_reply (Any): The RPC reply object containing details of the change.
            filter (Any): The filter object associated with the change.
        """

        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)

        device_item = QTableWidgetItem(device_id)
        device_item.setFlags(device_item.flags() ^ Qt.ItemIsEditable)  # Non-editable cells
        device_item.setToolTip("Double click for details")
        self.table_widget.setItem(row_position, 0, device_item)

        change_item = QTableWidgetItem(change_name)
        change_item.setFlags(change_item.flags() ^ Qt.ItemIsEditable)  # Non-editable cells
        change_item.setData(Qt.UserRole, (rpc_reply, filter)) # Store the RPC reply and filter in the item, so it can be accessed when the item is double-clicked
        change_item.setToolTip("Double click for details")
        self.table_widget.setItem(row_position, 1, change_item)

    def clearPendingChangesFromTable(self, device_id) -> None:
        """Clears all pending changes for a specific device from the table."""
        for row in range(self.table_widget.rowCount() - 1, -1, -1): # Iterate backwards to avoid skipping rows
            if self.table_widget.item(row, 0).text() == device_id:
                self.table_widget.removeRow(row)

    def _showPendingChangeDetails(self, item) -> None:
        """
        Handles showing the details of a pending change when the user double-clicks on a pending change in the table.
        It creates a PendingChangeDetails dialog and displays the details of the pending change.
        """
        device_id = self.table_widget.item(item.row(), 0).text()
        change_name = self.table_widget.item(item.row(), 1).text()

        rpc_reply, filter = self.table_widget.item(item.row(), 1).data(Qt.UserRole)

        dialog = PendingChangeDetailsDialog(device_id, change_name, rpc_reply, filter)
        dialog.exec()

    # ---------- COMMIT FUNCTIONS ----------
    # (And functions related - cancel, discard, countdown timer, etc.)
    def _confirmedCommitPendingChanges(self) -> None:
        """
        (1/2) Handles the confirmed commit of pending changes on devices.

        This method is performing a "confirmed commit" defined in NETCONF RFC6241. It commits the pending changes to the devices with a specific timeout.
        If second commit is not performed within the timeout, the changes are reverted and all pending changes are discarded.
        
        The method performs the following steps:
        1. Retrieves the timeout value from the combobox and converts it to seconds.
        2. Iterates over all device instances and commits changes (with the confirmed parameter set to True) on devices with pending changes.
        3. Starts a countdown timer in a separate thread, that dynaminacally updates the commit button text to show the remaining time.
        4. Updates the UI elements and device states accordingly after the countdown.
        """

        # Get the timeout in seconds from the combobox
        timeout_minutes = self.confirmed_commit_timer_combobox.currentText()
        timeout_seconds = int(timeout_minutes.split()[0]) * 60

        commited_devices = []
        devices = Device.getAllDevicesInstances()
        try:
            for device in devices:
                if device.has_pending_changes:
                    device.commitChanges(confirmed=True, confirm_timeout=timeout_seconds)
                    commited_devices.append(device.id)

            def _countdown() -> None:
                """
                Simple countdown timer that updates the commit button text to show the remaining time. Launched in a separate thread to avoid blocking of the application.
                """
                
                for i in range(timeout_seconds, 0, -1):
                    if self.stop_countdown_event.is_set():
                        return
                    self.commit_button.setText(f"Confirm ({i} sec.)")
                    QApplication.processEvents()
                    time.sleep(1)

                # After the countdown:
                self._revertButtonsToDefaultState() # Revert the buttons to their default state
                for device_id in commited_devices: # Reset the flags and labels for devices that had pending changes
                    device = Device.getDeviceInstance(device_id)
                    device.has_pending_changes = False
                    signal_manager.deviceNoLongerHasPendingChanges.emit(device.id)
                    device.updateCableLabelsText()

            # When at least one device has pending changes - print and begin the confirmed commit procedure
            if commited_devices:
                utils.printGeneral(f"Performed confirmed commit on devices with ID: {', '.join(commited_devices)}\nTo preserve the changes, commit again within {timeout_seconds} seconds.")
                # Disable buttons
                self.confirmed_commit_button.setEnabled(False)
                self.confirmed_commit_timer_combobox.setEnabled(False)
                # Start countdown in a separate thread
                self.stop_countdown_event.clear()
                self.confirmed_commit_thread = Thread(target=_countdown)
                self.confirmed_commit_thread.start()
                # Change the "Commit" button to "Confirm" button
                self.commit_button.setText(f"Confirm ({timeout_seconds} sec.)")
                self.commit_button.clicked.disconnect()
                self.commit_button.clicked.connect(self._confirmCommit)
                # Change the "Discard all" button to "Cancel commit" button
                self.discard_button.setText("Cancel commit")
                self.discard_button.clicked.disconnect()
                self.discard_button.clicked.connect(self._cancelConfirmedCommit)
            else:
                QMessageBox.information(self, "No pending changes", "No pending changes to commit.")

        except Exception as e:
            QMessageBox.critical(self, "Commit failed", f"Failed to commit changes on one or more devices: {e}")
            utils.printGeneral(traceback.format_exc())

    def _confirmCommit(self) -> None:
        """
        (2/2) Handles the CONFIRMATION of the confirmed commit of pending changes on devices.
        """
                
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

                self._stopCountdown()
                self._revertButtonsToDefaultState()

        except Exception as e:
            QMessageBox.critical(self, "Commit failed", f"Failed to commit changes on one or more devices: {e}")
            utils.printGeneral(traceback.format_exc())

    def _commitPendingChanges(self) -> None:
        """
        Handles the commit of pending changes on devices. This commit is NOT confirmed and does not have a timeout.
        This method is performing "commit" defined in NETCONF RFC6241.
        """

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
                utils.printGeneral(f"Performed commit on devices with ID: {', '.join(commited_devices)}")
            else:
                QMessageBox.information(self, "No pending changes", "No pending changes to commit.")

        except Exception as e:
            QMessageBox.critical(self, "Commit failed", f"Failed to commit changes on one or more devices: {e}")
            utils.printGeneral(traceback.format_exc())

    def _discardAllPendingChanges(self) -> None:
        """
        Discards all pending changes on all device instances.
        This method retrieves all device instances and checks if they have any pending changes.
        If a device has pending changes, it discards those changes, marks the device as having no pending changes,
        and clears the pending changes from the table for that device.
        """

        devices = Device.getAllDevicesInstances()
        discarded_devices = []
        try:
            for device in devices:
                if device.has_pending_changes:
                    device.discardChanges()
                    self.clearPendingChangesFromTable(device.id)
                    discarded_devices.append(device.id)

            if discarded_devices:
                utils.printGeneral(f"Discarded changes on devices with ID: {', '.join(discarded_devices)}")
            else:
                QMessageBox.information(self, "No pending changes", "No pending changes to discard.")

        except Exception as e:
            QMessageBox.critical(self, "Discard failed", f"Failed to discard changes on one or more devices: {e}")
            utils.printGeneral(traceback.format_exc())

    def _cancelConfirmedCommit(self) -> None:
        """Cancels the confirmed commit of pending changes on devices."""

        devices = Device.getAllDevicesInstances()
        try:
            for device in devices:
                if device.has_pending_changes:
                    device.cancelCommit()
                    self.clearPendingChangesFromTable(device.id)

            self._stopCountdown()
            self._revertButtonsToDefaultState()

        except Exception as e:
            QMessageBox.critical(self, "Cancel failed", f"Failed to cancel commit on one or more devices: {e}")
            utils.printGeneral(traceback.format_exc())

    def _revertButtonsToDefaultState(self) -> None:
        """
        Resets the state of UI buttons to their default configuration.
        This method performs the following actions:
        - Resets the "Commit" button text to "Commit", disconnects any existing signals,
          and reconnects it to the `_commitPendingChanges` method.
        - Enables the "Confirmed commit" button and the associated timer combobox.
        - Resets the "Discard all" button text to "Discard all", disconnects any existing signals,
          and reconnects it to the `_discardAllPendingChanges` method.
        """

        # "Commit" button
        self.commit_button.setText("Commit")
        self.commit_button.clicked.disconnect()
        self.commit_button.clicked.connect(self._commitPendingChanges)
        # "Confirmed commit" button
        self.confirmed_commit_button.setEnabled(True)
        self.confirmed_commit_timer_combobox.setEnabled(True)
        # "Discard all" button
        self.discard_button.setText("Discard all")
        self.discard_button.clicked.disconnect()
        self.discard_button.clicked.connect(self._discardAllPendingChanges)

    def _stopCountdown(self) -> None:
        """Stops the countdown timer."""

        self.stop_countdown_event.set()
        
        if self.confirmed_commit_thread and self.confirmed_commit_thread.is_alive():
            self.confirmed_commit_thread.join()


class PendingChangeDetailsDialog(QDialog):
    """
    QDialog that displays the details of a pending change when the user double-clicks on a pending change in the table.
    It shows the RPC filter that was used to make the change and the RPC reply received after the change was made.
    """

    def __init__(self, device_id, change_name, rpc_reply, filter) -> QDialog:
        super().__init__()

        self.ui = Ui_PendingChangeDetailsDialog()
        self.ui.setupUi(self)
    
        self.device_id = device_id
        self.change = change_name
        self.rpc_reply = rpc_reply
        self.filter = filter

        self.ui.header.setText(f"{device_id} - {change_name}")
        self.ui.filter_text_browser.setPlainText(self.filter)
        self.ui.rpc_reply_text_browser.setPlainText(self.rpc_reply)
        

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