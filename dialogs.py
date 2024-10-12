# Qt
from PySide6.QtWidgets import (
    QDialog, 
    QVBoxLayout, 
    QScrollArea, 
    QWidget, 
    QLabel, 
    QPushButton,
    QComboBox,
    QDialogButtonBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView)
from PySide6.QtCore import Qt

# Custom
import db_handler
import devices

class AddDeviceDialog(QDialog):
    device_parameters = {}

    def __init__(self, addRouter_callback):
        super().__init__()

        self.setWindowTitle("Add a device")
        self.addRouter_callback = addRouter_callback
        self.setModal(True)
        layout = QVBoxLayout()

        # Input fields
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("IP address:port")
        layout.addWidget(self.address_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        layout.addWidget(self.password_input)

        self.deviceType_combo = QComboBox()
        self.deviceType_combo.addItems(["Cisco IOS XE", "Juniper"])
        layout.addWidget(self.deviceType_combo)

        #DEBUG: Testing connection for debugging
        if __debug__:
            self.address_input.setText("10.0.0.201")
            self.username_input.setText("jakub")
            self.password_input.setText("cisco")

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.confirmConnection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def confirmConnection(self):
        addr_field = self.address_input.text().split(":")
        if len(addr_field) == 2:
            self.device_parameters["address"] = addr_field[0]
            self.device_parameters["port"] = addr_field[1]
        elif len(addr_field) == 1:
            self.device_parameters["address"] = self.address_input.text()
            self.device_parameters["port"] = 830
        else:
            raise ValueError("Invalid IP address format")

        self.device_parameters["username"] = self.username_input.text()
        self.device_parameters["password"] = self.password_input.text()
        if self.deviceType_combo.currentText() == "Cisco IOS XE":
            self.device_parameters["device_params"] = "iosxe"
        elif self.deviceType_combo.currentText() == "Juniper":
            self.device_parameters["device_params"] = "junos"

        self.addRouter_callback(device_parameters = self.device_parameters, x=0, y=0)
        self.accept()


class CapabilitiesDialog(QDialog):
    def __init__(self, device_id):
        super().__init__()

        self.setWindowTitle("Device Capabilities")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create a widget to hold the capabilities
        table_widget = QWidget()
        table_layout = QVBoxLayout()

        capabilities_table = QTableWidget()
        capabilities_table.setColumnCount(1)
        capabilities_table.setHorizontalHeaderLabels(["Capability"])

        try:
            capabilities = db_handler.queryNetconfCapabilities(db_handler.connection, device_id)
        except Exception as e:
            capabilities = []
            error_label = QLabel(f"Failed to retrieve capabilities: {e}")
            table_layout.addWidget(error_label)

        if capabilities:
            capabilities_table.setRowCount(len(capabilities))

            for row, capability in enumerate(capabilities):
                capability_item = QTableWidgetItem(capability)
                capability_item.setFlags(capability_item.flags() ^ Qt.ItemIsEditable) # Non-editable cells
                capabilities_table.setItem(row, 0, capability_item) # 0 = first column

        else :
            capabilities_table.setRowCount(1)
            capabilities_table.setItem(0, 0, QTableWidgetItem("No capabilities found"))

        capabilities_table.horizontalHeader().setStretchLastSection(True)
        capabilities_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        capabilities_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        
        table_layout.addWidget(capabilities_table)
        table_widget.setLayout(table_layout)
        scroll_area.setWidget(table_widget)

        layout.addWidget(scroll_area)

        # Add a close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

        #TODO: nejak to funguje, ale je to nejake divne. Az nebudu prejety, tady pokracovat a upravit/predelat/vylepsit
        #radky asi dat do nejake tabulky, volani mezi soubory je nejaka posahane

class DebugDialog(QDialog):
    def __init__(self, addCable_callback, removeCable_callback):
        super().__init__()

        self.addCable_callback = addCable_callback
        self.removeCable_callback = removeCable_callback

        self.setWindowTitle("Debug")
        layout = QVBoxLayout()

        #Input fields
        cursor = db_handler.connection.cursor()
        cursor.execute("SELECT device_id FROM Device") # TODO: does this need to be from a DB? Does this project need a DB at all?
        devices = cursor.fetchall()
        devices_processed = []
        for device in devices:
            devices_processed.append(device[0])

        self.device1_combo = QComboBox()
        self.device1_combo.addItems(devices_processed)
        layout.addWidget(self.device1_combo)

        self.device2_combo = QComboBox()
        self.device2_combo.addItems(devices_processed)
        layout.addWidget(self.device2_combo)

        #Buttons
        self.button_box = QDialogButtonBox()

        button1_addCable = QPushButton("ADD CABLE")
        button1_addCable.clicked.connect(self.addCableDebug)
        self.button_box.addButton(button1_addCable, QDialogButtonBox.AcceptRole)

        button2_removeCable = QPushButton("REMOVE CABLE")
        button2_removeCable.clicked.connect(self.removeCableDebug)
        self.button_box.addButton(button2_removeCable, QDialogButtonBox.AcceptRole)        
        
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def addCableDebug(self):
        device_1 = devices.Router.getDeviceInstance(self.device1_combo.currentText())
        device_2 = devices.Router.getDeviceInstance(self.device2_combo.currentText())
        self.addCable_callback(device_1, device_2)
        self.accept()

    def removeCableDebug(self):
        device_1 = devices.Router.getDeviceInstance(self.device1_combo.currentText())
        device_2 = devices.Router.getDeviceInstance(self.device2_combo.currentText())
        self.removeCable_callback(device_1, device_2)
        self.accept()