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
            self.address_input.setText("10.0.0.142")
            self.username_input.setText("root")
            self.password_input.setText("Juniper123")

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

class InterfacesDialog(QDialog):
    def __init__(self, device_id):
        super().__init__()

        self.setWindowTitle("Device Interfaces")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create a widget to hold the interfaces
        table_widget = QWidget()
        table_layout = QVBoxLayout()

        interfaces_table = QTableWidget()
        interfaces_table.setColumnCount(8)
        interfaces_table.setHorizontalHeaderLabels(["Interface", 
                                                    "Admin state", 
                                                    "Operational state", 
                                                    "Subinterface index", 
                                                    "IPv4 address", 
                                                    "IPv4 prefix length", 
                                                    "IPv6 address", 
                                                    "IPv6 prefix length"])

        try:
            interfaces = db_handler.queryInterfaces(db_handler.connection, device_id)
        except Exception as e:
            interfaces = []
            error_label = QLabel(f"Failed to retrieve interfaces: {e}")
            table_layout.addWidget(error_label)

        
        if interfaces:
            interfaces_table.setRowCount(len(interfaces))

            for row, (interface_id,
                      interface_name, 
                      admin_state, 
                      oper_state, 
                      subinterface_index, 
                      ipv4_address, ipv4_prefix_length, 
                      ipv6_address, ipv6_prefix_length) in enumerate(interfaces):
                
                print(interface_id, interface_name, admin_state, oper_state, subinterface_index, ipv4_address, ipv4_prefix_length, ipv6_address, ipv6_prefix_length)
                # Interface name
                interface_item = QTableWidgetItem(interface_name)
                interface_item.setFlags(interface_item.flags() ^ Qt.ItemIsEditable)  # Non-editable cells
                interfaces_table.setItem(row, 0, interface_item)  # 0 = first column

                # Administrative state
                admin_state_item = QTableWidgetItem(admin_state)
                admin_state_item.setFlags(admin_state_item.flags() ^ Qt.ItemIsEditable)
                interfaces_table.setItem(row, 1, admin_state_item)

                # Operational state
                oper_state_item = QTableWidgetItem(oper_state)
                oper_state_item.setFlags(oper_state_item.flags() ^ Qt.ItemIsEditable)
                interfaces_table.setItem(row, 2, oper_state_item)

                # Subinterface index
                subinterface_index_item = QTableWidgetItem(str(subinterface_index) if subinterface_index is not None else "")
                subinterface_index_item.setFlags(subinterface_index_item.flags() ^ Qt.ItemIsEditable)
                interfaces_table.setItem(row, 3, subinterface_index_item)

                # IPv4 address
                ipv4_address_item = QTableWidgetItem(ipv4_address)
                ipv4_address_item.setFlags(ipv4_address_item.flags() ^ Qt.ItemIsEditable)
                interfaces_table.setItem(row, 4, ipv4_address_item)

                # IPv4 prefix length
                ipv4_prefix_length_item = QTableWidgetItem(str(ipv4_prefix_length) if ipv4_prefix_length is not None else "")
                ipv4_prefix_length_item.setFlags(ipv4_prefix_length_item.flags() ^ Qt.ItemIsEditable)
                interfaces_table.setItem(row, 5, ipv4_prefix_length_item)

                # IPv6 address
                ipv6_address_item = QTableWidgetItem(ipv6_address)
                ipv6_address_item.setFlags(ipv6_address_item.flags() ^ Qt.ItemIsEditable)
                interfaces_table.setItem(row, 6, ipv6_address_item)

                # IPv6 prefix length
                ipv6_prefix_length_item = QTableWidgetItem(str(ipv6_prefix_length) if ipv6_prefix_length is not None else "")
                ipv6_prefix_length_item.setFlags(ipv6_prefix_length_item.flags() ^ Qt.ItemIsEditable)
                interfaces_table.setItem(row, 7, ipv6_prefix_length_item)

        else :
            interfaces_table.setRowCount(1)
            interfaces_table.setColumnCount(1)
            interfaces_table.setItem(0, 0, QTableWidgetItem("No interfaces found"))

        interfaces_table.horizontalHeader().setStretchLastSection(True)
        interfaces_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        interfaces_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        
        table_layout.addWidget(interfaces_table)
        table_widget.setLayout(table_layout)
        scroll_area.setWidget(table_widget)

        layout.addWidget(scroll_area)

        # Add a close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

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