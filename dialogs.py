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
    QHeaderView,
    QStyle,
    QToolBar,
    QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QGuiApplication, QAction

# Other
from ipaddress import IPv4Address, IPv6Address, IPv4Interface, IPv6Interface

# Custom
import db_handler
import devices
import modules.interfaces

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
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                QSize(800, 500),
                QGuiApplication.primaryScreen().availableGeometry()
            )
        )

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


class InterfacesDialog(QDialog):
    def __init__(self, device_id):
        super().__init__()

        self.device_id = device_id

        self.setWindowTitle("Device Interfaces")
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                QSize(800, 500),
                QGuiApplication.primaryScreen().availableGeometry()
            )
        )

        layout = QVBoxLayout()

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create a widget to hold the interfaces
        table_widget = QWidget()
        table_layout = QVBoxLayout()

        self.interfaces_table = QTableWidget()
        self.interfaces_table.setColumnCount(6)
        self.interfaces_table.setHorizontalHeaderLabels(["Interface", 
                                                    "Admin state", 
                                                    "Operational state", 
                                                    "IPv4", 
                                                    "IPv6",
                                                    ""])

        try:
            #interfaces = db_handler.queryInterfaces(db_handler.connection, self.device_id)
            device = devices.Device.getDeviceInstance(device_id)
            interfaces = devices.Device.getDeviceInterfaces(device, getIPs=True)
        except Exception as e:
            interfaces = []
            error_label = QLabel(f"Failed to retrieve interfaces: {e}")
            table_layout.addWidget(error_label)

        
        if interfaces:
            self.interfaces_table.setRowCount(len(interfaces))

            for row, (interface_name, 
                      admin_state, 
                      oper_state, 
                      ipv4_data, ipv6_data) in enumerate(interfaces):
                
                # Interface name
                interface_item = QTableWidgetItem(interface_name)
                interface_item.setFlags(interface_item.flags() ^ Qt.ItemIsEditable)  # Non-editable cells
                self.interfaces_table.setItem(row, 0, interface_item)  # 0 = first column

                # Administrative state
                admin_state_item = QTableWidgetItem(admin_state)
                admin_state_item.setFlags(admin_state_item.flags() ^ Qt.ItemIsEditable)
                self.interfaces_table.setItem(row, 1, admin_state_item)

                # Operational state
                oper_state_item = QTableWidgetItem(oper_state)
                oper_state_item.setFlags(oper_state_item.flags() ^ Qt.ItemIsEditable)
                self.interfaces_table.setItem(row, 2, oper_state_item)

                # IPv4 
                ipv4_item = QTableWidgetItem(str(ipv4_data) if ipv4_data is not None else "")
                ipv4_item.setFlags(ipv4_item.flags() ^ Qt.ItemIsEditable)
                self.interfaces_table.setItem(row, 3, ipv4_item)

                # IPv6
                ipv6_item = QTableWidgetItem(str(ipv6_data) if ipv6_data is not None else "")
                ipv6_item.setFlags(ipv6_item.flags() ^ Qt.ItemIsEditable)
                self.interfaces_table.setItem(row, 4, ipv6_item)

                # Edit button
                button_item = QPushButton("Edit")
                button_item.clicked.connect(self.showEditInterfaceDialog)
                self.interfaces_table.setCellWidget(row, 5, button_item)

        else :
            self.interfaces_table.setRowCount(1)
            self.interfaces_table.setColumnCount(1)
            self.interfaces_table.setItem(0, 0, QTableWidgetItem("No interfaces found"))

        self.interfaces_table.horizontalHeader().setStretchLastSection(True)
        self.interfaces_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        table_layout.addWidget(self.interfaces_table)
        table_widget.setLayout(table_layout)
        scroll_area.setWidget(table_widget)

        layout.addWidget(scroll_area)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def showEditInterfaceDialog(self):
        button = self.sender()
        if button:
            row_index = self.interfaces_table.indexAt(button.pos()) # Get the index of the row, in which was the button clicked
            interface_id = self.interfaces_table.item(row_index.row(), 0).text() # Get the interface ID of the clicked row
            
            dialog = EditInterfaceDialog(self.device_id, interface_id)
            dialog.exec()

class EditInterfaceDialog(QDialog):

    def __init__(self, device_id, interface_id):
        super().__init__()

        self.device_id = device_id
        self.interface_id = interface_id

        self.setWindowTitle("Edit interface: " + interface_id)
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                QSize(300, 400),
                QGuiApplication.primaryScreen().availableGeometry()
            )
        )

        self.layout = QVBoxLayout()

        toolbar = QToolBar("Edit interface", self)
        action1_addSubinterface = QAction("Add subinterface", self)
        action1_addSubinterface.triggered.connect(self.addSubinterface)
        toolbar.addAction(action1_addSubinterface)
        self.layout.addWidget(toolbar)

        device = devices.Device.getDeviceInstance(device_id)

        subinterfaces = devices.Device.getDeviceSubinterfaces(device, interface_id)
        for subinterface in subinterfaces:
            subinterface_layout = QVBoxLayout()
            subinterface_label = QLabel("Subinterface: " + subinterface['subinterface_index'])
            subinterface_label.setFont(QFont("Arial", 16))
            subinterface_layout.addWidget(subinterface_label)
            subinterface_layout.addWidget(self.createSubinterfaceTable(interface_id, subinterface))
            
            self.layout.addLayout(subinterface_layout)
        
        self.setLayout(self.layout)

    def createSubinterfaceTable(self, interface_id, subinterface):
        subinterface_table = QTableWidget()
        subinterface_table.setColumnCount(3)
        subinterface_table.setRowCount(len(subinterface['ipv4']) + len(subinterface['ipv6']))
        subinterface_table.setHorizontalHeaderLabels(["Address", "Prefix length", ""])
        subinterface_table.horizontalHeader().setStretchLastSection(True)
        subinterface_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        row = 0
        for ipv4_data in subinterface['ipv4']:
            subinterface_table.setItem(row, 0, QTableWidgetItem(str(ipv4_data.ip)))
            subinterface_table.setItem(row, 1, QTableWidgetItem(str(ipv4_data.network.prefixlen)))
            
            button_item = QPushButton("Edit")
            button_item.clicked.connect(lambda _, interface=interface_id, index=subinterface['subinterface_index'], ip = ipv4_data : self.showEditSubinterfaceDialog(interface, index, ip)) # _ = unused argument
            subinterface_table.setCellWidget(row, 2, button_item)
            
            row += 1
        
        for ipv6_data in subinterface['ipv6']:
            subinterface_table.setItem(row, 0, QTableWidgetItem(str(ipv6_data.ip)))
            subinterface_table.setItem(row, 1, QTableWidgetItem(str(ipv6_data.network.prefixlen)))

            button_item = QPushButton("Edit")
            button_item.clicked.connect(lambda _, interface=interface_id, index=subinterface['subinterface_index'], ip = ipv6_data : self.showEditSubinterfaceDialog(interface, index, ip)) # _ = unused argument
            subinterface_table.setCellWidget(row, 2, button_item)

            row += 1

        return subinterface_table
    
    def showEditSubinterfaceDialog(self, interface, subinterface_index, ip):       
        dialog = EditSubinterfaceDialog(self, self.device_id, interface, subinterface_index, ip)
        dialog.exec()

    def addSubinterface(self):
        pass

    def confirmEdit(self):
        # TODO: later
        self.accept()

    def refreshTables(self):
        # TODO: on close of editInterface dialog, refresh InterfaceDialog
        # Clear the layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        # Toolbar
        toolbar = QToolBar("Edit interface", self)
        action1_addSubinterface = QAction("Add subinterface", self)
        action1_addSubinterface.triggered.connect(self.addSubinterface)
        toolbar.addAction(action1_addSubinterface)
        self.layout.addWidget(toolbar)

        # Device
        device = devices.Device.getDeviceInstance(self.device_id)
        subinterfaces = devices.Device.getDeviceSubinterfaces(device, self.interface_id)

        # Subinterfaces
        for subinterface in subinterfaces:
            subinterface_layout = QVBoxLayout()
            subinterface_label = QLabel("Subinterface: " + subinterface['subinterface_index'])
            subinterface_label.setFont(QFont("Arial", 16))
            subinterface_layout.addWidget(subinterface_label)
            subinterface_layout.addWidget(self.createSubinterfaceTable(self.interface_id, subinterface))  

            self.layout.addLayout(subinterface_layout)

        self.setLayout(self.layout)

class EditSubinterfaceDialog(QDialog):
    def __init__(self, editInterfaceDialogInstance, device_id, interface, subinterface_id, ip):
        super().__init__()

        self.editInterfaceDialogInstance = editInterfaceDialogInstance
        self.device_id = device_id
        self.interface_id = interface
        self.subinterface_id = subinterface_id
        self.old_ip = ip

        self.layout = QVBoxLayout()
        
        self.setWindowTitle("Edit subinterface: " + subinterface_id)
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                QSize(300, 200),
                QGuiApplication.primaryScreen().availableGeometry()
            )
        )

        self.ip_input = QLineEdit()
        self.ip_input.setText(str(self.old_ip))
        self.layout.addWidget(self.ip_input)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.confirmEdit)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

        self.setLayout(self.layout)

    def confirmEdit(self):
        if self.old_ip.version == 4:
            self.new_ip = IPv4Interface(self.ip_input.text())
        elif self.old_ip.version == 6:
            self.new_ip = IPv6Interface(self.ip_input.text())

        if self.new_ip != self.old_ip:
            device = devices.Device.getDeviceInstance(self.device_id)
            devices.Device.replaceInterfaceIp(device, self.interface_id, self.subinterface_id, self.old_ip, self.new_ip)
            self.editInterfaceDialogInstance.refreshTables()
        else:
            info_dialog = QDialog(self)
            info_dialog.setWindowTitle("Information")
            info_layout = QVBoxLayout()
            info_label = QLabel("No changes were made.")
            info_layout.addWidget(info_label)
            info_button = QPushButton("OK")
            info_button.clicked.connect(info_dialog.accept)
            info_layout.addWidget(info_button)
            info_dialog.setLayout(info_layout)
            info_dialog.exec()
        self.accept()



class DebugDialog(QDialog):
    def __init__(self, addCable_callback, removeCable_callback):
        super().__init__()

        self.addCable_callback = addCable_callback
        self.removeCable_callback = removeCable_callback

        self.setWindowTitle("Debug")
        layout = QVBoxLayout()

        #Input fields
        cursor = db_handler.connection.cursor()
        cursor.execute("SELECT device_id FROM Device")
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