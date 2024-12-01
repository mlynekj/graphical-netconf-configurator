# Qt
from PySide6.QtWidgets import (
    QDialog, 
    QVBoxLayout,
    QHBoxLayout, 
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
import ipaddress

# Custom
import devices

def showMessageBox(parent, title, message):
    info_dialog = QDialog(parent)
    info_dialog.setWindowTitle(title)
    info_layout = QVBoxLayout()
    info_label = QLabel(message)
    info_layout.addWidget(info_label)
    info_button = QPushButton("OK")
    info_button.clicked.connect(info_dialog.accept)
    info_layout.addWidget(info_button)
    info_dialog.setLayout(info_layout)
    info_dialog.exec()

def clearLayout(layout):
    """ Recursively clear all widgets and layouts from the given layout. """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        else:
            sub_layout = item.layout()
            if sub_layout is not None:
                clearLayout(sub_layout)


class AddDeviceDialog(QDialog):
    def __init__(self, addRouter_callback):
        super().__init__()

        self.device_parameters = {}

        self.setWindowTitle("Add a device")
        self.addRouter_callback = addRouter_callback
        self.setModal(True)
        self.layout = QVBoxLayout()

        # Input fields
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("IP address:port")
        self.layout.addWidget(self.address_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.layout.addWidget(self.password_input)

        self.deviceType_combo = QComboBox()
        self.deviceType_combo.addItems(["Cisco IOS XE", "Juniper"])
        self.layout.addWidget(self.deviceType_combo)

        #DEBUG: Testing connection for debugging
        if __debug__:
            self.address_input.setText("10.0.0.201")
            self.username_input.setText("jakub")
            self.password_input.setText("cisco")

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.confirmConnection)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)

    def confirmConnection(self):
        address_field = self.address_input.text().split(":")
        if len(address_field) == 2:
            self.device_parameters["address"] = address_field[0]
            self.device_parameters["port"] = address_field[1]
        elif len(address_field) == 1:
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

        self.addRouter_callback(self.device_parameters, x=0, y=0)
        self.accept()


class CapabilitiesDialog(QDialog):
    def __init__(self, device):
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

        self.layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Initialize table for holding the capabilities
        self.table_widget = QWidget()
        self.table_layout = QVBoxLayout()
        self.capabilities_table = QTableWidget()
        self.capabilities_table.setColumnCount(1)
        self.capabilities_table.setHorizontalHeaderLabels(["Capability"])

        # Load capabilities
        try:
            self.capabilities = device.netconf_capabilities
        except Exception as e:
            self.capabilities = []
            self.error_label = QLabel(f"Failed to retrieve self.capabilities: {e}")
            self.table_layout.addWidget(self.error_label)

        # Populate the table with the capabilities
        if self.capabilities:
            self.capabilities_table.setRowCount(len(self.capabilities))
            for row, capability in enumerate(self.capabilities):
                capability_item = QTableWidgetItem(capability)
                capability_item.setFlags(capability_item.flags() ^ Qt.ItemIsEditable) # Non-editable cells
                self.capabilities_table.setItem(row, 0, capability_item)
        else :
            self.capabilities_table.setRowCount(1)
            self.capabilities_table.setItem(0, 0, QTableWidgetItem("No capabilities found"))

        # Set table properties
        self.capabilities_table.horizontalHeader().setStretchLastSection(True)
        self.capabilities_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.capabilities_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Add table to layout
        self.table_layout.addWidget(self.capabilities_table)
        self.table_widget.setLayout(self.table_layout)
        self.scroll_area.setWidget(self.table_widget)
        self.layout.addWidget(self.scroll_area)

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.layout.addWidget(self.close_button)

        self.setLayout(self.layout)


class DeviceInterfacesDialog(QDialog):
    def __init__(self, device):
        super().__init__()

        self.device = device

        self.setWindowTitle("Device Interfaces")
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                QSize(800, 500),
                QGuiApplication.primaryScreen().availableGeometry()
            )
        )

        self.layout = QVBoxLayout()
        self.fillLayout()
        self.setLayout(self.layout)

    def fillLayout(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Initialize table for holding the interfaces
        self.table_widget = QWidget()
        self.table_layout = QVBoxLayout()
        self.interfaces_table = QTableWidget()
        self.interfaces_table.setColumnCount(6)
        self.interfaces_table.setHorizontalHeaderLabels(["Interface", 
                                                         "Admin state", 
                                                         "Operational state", 
                                                         "IPv4", 
                                                         "IPv6",
                                                         ""])

        # Get interfaces
        try:
            self.interfaces = self.device.dev_GetInterfaces(getIPs=True)
        except Exception as e:
            self.interfaces = []
            self.error_label = QLabel(f"Failed to retrieve self.interfaces: {e}")
            self.table_layout.addWidget(self.error_label)

        # Populate the table with the interfaces
        if self.interfaces:
            self.interfaces_table.setRowCount(len(self.interfaces))
            for row, (interface_name, admin_state, oper_state, ipv4_data, ipv6_data) in enumerate(self.interfaces):      
                # Interface name
                self.interface_item = QTableWidgetItem(interface_name)
                self.interface_item.setFlags(self.interface_item.flags() ^ Qt.ItemIsEditable)  # Non-editable cells
                self.interfaces_table.setItem(row, 0, self.interface_item)
                # Administrative state
                self.admin_state_item = QTableWidgetItem(admin_state)
                self.admin_state_item.setFlags(self.admin_state_item.flags() ^ Qt.ItemIsEditable)
                self.interfaces_table.setItem(row, 1, self.admin_state_item)
                # Operational state
                self.oper_state_item = QTableWidgetItem(oper_state)
                self.oper_state_item.setFlags(self.oper_state_item.flags() ^ Qt.ItemIsEditable)
                self.interfaces_table.setItem(row, 2, self.oper_state_item)
                # IPv4 
                self.ipv4_item = QTableWidgetItem(str(ipv4_data) if ipv4_data is not None else "")
                self.ipv4_item.setFlags(self.ipv4_item.flags() ^ Qt.ItemIsEditable)
                self.interfaces_table.setItem(row, 3, self.ipv4_item)
                # IPv6
                self.ipv6_item = QTableWidgetItem(str(ipv6_data) if ipv6_data is not None else "")
                self.ipv6_item.setFlags(self.ipv6_item.flags() ^ Qt.ItemIsEditable)
                self.interfaces_table.setItem(row, 4, self.ipv6_item)
                # Edit button
                self.button_item = QPushButton("Edit")
                self.button_item.clicked.connect(self.showDialog)
                self.interfaces_table.setCellWidget(row, 5, self.button_item)      
        else :
            self.interfaces_table.setRowCount(1)
            self.interfaces_table.setColumnCount(1)
            self.interfaces_table.setItem(0, 0, QTableWidgetItem("No interfaces found!"))

        # Set table properties
        self.interfaces_table.horizontalHeader().setStretchLastSection(True)
        self.interfaces_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Add table to layout
        self.table_layout.addWidget(self.interfaces_table)
        self.table_widget.setLayout(self.table_layout)
        self.scroll_area.setWidget(self.table_widget)
        self.layout.addWidget(self.scroll_area)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        self.layout.addWidget(close_button)

    def showDialog(self):
        button = self.sender()
        if button:
            row_index = self.interfaces_table.indexAt(button.pos()) # Get the index of the row, in which was the button clicked
            interface_id = self.interfaces_table.item(row_index.row(), 0).text() # Get the interface ID of the clicked row
            
            dialog = EditInterfaceDialog(self, self.device, interface_id)
            dialog.exec()

    def refreshDialog(self):
        clearLayout(self.layout)
        self.fillLayout()
        self.setLayout(self.layout)


class EditInterfaceDialog(QDialog):
    def __init__(self, deviceInterfacesDialog_instance, device, interface_id):
        super().__init__()

        self.deviceInterfacesDialog_instance = deviceInterfacesDialog_instance
        self.device = device
        self.interface_id = interface_id

        self.setWindowTitle("Edit interface: " + self.interface_id)
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                QSize(300, 400),
                QGuiApplication.primaryScreen().availableGeometry()
            )
        )

        self.layout = QVBoxLayout()
        self.fillLayout()
        self.setLayout(self.layout)

    def createSubinterfaceTable(self, subinterface):
        """
        Create a table containing IPv4 and IPv6 addresses for specified subinterface + [Edit] and [Delete] buttons for each row.

        Args:
            interface_id (int): The ID of the interface to which the subinterface belongs.
            subinterface (dict): A dictionary containing subinterface details.
            - 'ipv4': A list of "IPv4Interface" objects
            - 'ipv6': A list of "IPv6Interface" objects
        Returns:
            QTableWidget: Table populated with subinterface information and buttons.
        """

        # Create the table, set basic properties
        subinterface_table = QTableWidget()
        subinterface_table.setColumnCount(3)
        subinterface_table.setRowCount(len(subinterface['ipv4']) + len(subinterface['ipv6']))
        subinterface_table.setHorizontalHeaderLabels(["Address", "", ""])
        subinterface_table.horizontalHeader().setStretchLastSection(True)
        subinterface_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        row = 0
        for ipv4_data in subinterface['ipv4']:
            # IPv4 address
            subinterface_table.setItem(row, 0, QTableWidgetItem(str(ipv4_data.ip)+"/"+str(ipv4_data.network.prefixlen)))
            # Edit button
            self.edit_ip_button_item = QPushButton("Edit")
            self.edit_ip_button_item.clicked.connect(lambda _, index=subinterface['subinterface_index'], ip = ipv4_data : self.showDialog(index, ip)) # _ = unused argument
            subinterface_table.setCellWidget(row, 1, self.edit_ip_button_item)
            # Delete button
            self.delete_ip_button_item = QPushButton("Delete")
            self.delete_ip_button_item.clicked.connect(lambda _, index=subinterface['subinterface_index'], ip = ipv4_data : self.deleteIP(index, ip))
            subinterface_table.setCellWidget(row, 2, self.delete_ip_button_item)
            
            row += 1
        
        for ipv6_data in subinterface['ipv6']:
            # IPv6 address
            subinterface_table.setItem(row, 0, QTableWidgetItem(str(ipv6_data.ip)+"/"+str(ipv6_data.network.prefixlen)))
            # Edit button
            self.edit_ip_button_item = QPushButton("Edit")
            self.edit_ip_button_item.clicked.connect(lambda _, index=subinterface['subinterface_index'], ip = ipv6_data : self.showDialog(index, ip)) # _ = unused argument
            subinterface_table.setCellWidget(row, 1, self.edit_ip_button_item)
            # Delete button
            self.delete_ip_button_item = QPushButton("Delete")
            self.delete_ip_button_item.clicked.connect(lambda _, index=subinterface['subinterface_index'], ip = ipv6_data : self.deleteIP(index, ip))
            subinterface_table.setCellWidget(row, 2, self.delete_ip_button_item)

            row += 1
        return subinterface_table
    
    def deleteIP(self, subinterface_index, old_ip):
        self.device.dev_DeleteInterfaceIP(self.interface_id, subinterface_index, old_ip)
        self.refreshDialog()

    def closeEvent(self, event):
        """ Refresh the parent dialog when this dialog is closed. """
        self.deviceInterfacesDialog_instance.refreshDialog()
        super().closeEvent(event)

    def fillLayout(self):
        # Toolbar
        self.toolbar = QToolBar("Edit interface", self)
        self.action_addSubinterface = QAction("Add subinterface", self)
        self.action_addSubinterface.triggered.connect(lambda _, index=None : self.showDialog(index))
        self.toolbar.addAction(self.action_addSubinterface)
        self.layout.addWidget(self.toolbar)

        # Get subinterfaces, create a layout for each subinterface containg: Header, Table
        self.subinterfaces = self.device.dev_GetSubinterfaces(self.interface_id)
        for subinterface in self.subinterfaces:
            self.subinterface_layout = QVBoxLayout()
            
            # Header ("Subinterface: x | [Add IP address]")
            self.subinterface_label = QLabel("Subinterface: " + subinterface['subinterface_index'])
            self.subinterface_label.setFont(QFont("Arial", 16))
            self.add_ip_button = QPushButton("Add IP address")
            self.add_ip_button.clicked.connect(lambda _, index=subinterface['subinterface_index'] : self.showDialog(index))
            self.header_layout = QHBoxLayout()
            self.header_layout.addWidget(self.subinterface_label)
            self.header_layout.addWidget(self.add_ip_button)
            self.subinterface_layout.addLayout(self.header_layout)

            # Table
            self.subinterface_layout.addWidget(self.createSubinterfaceTable(subinterface))
            
            self.layout.addLayout(self.subinterface_layout)

    def showDialog(self, subinterface_index, ip = None):       
        self.editSubinterfaceDialog = EditSubinterfaceDialog(self, self.device, self.interface_id, subinterface_index, ip)
        self.editSubinterfaceDialog.exec()

    def refreshDialog(self):
        clearLayout(self.layout)
        self.fillLayout()
        self.setLayout(self.layout)


class EditSubinterfaceDialog(QDialog):
    def __init__(self, editInterfaceDialog_instance, device, interface, subinterface_id, ip = None):
        super().__init__()

        self.editInterfaceDialog_instance = editInterfaceDialog_instance
        self.device = device
        self.interface_id = interface
        self.subinterface_id = subinterface_id
        self.old_ip = ip if ip is not None else None

        self.layout = QVBoxLayout()
        
        if self.subinterface_id:
             # Editing existing subinterface
            self.setWindowTitle("Edit subinterface: " + subinterface_id)
        else:
            # Creating new subinterface
            self.setWindowTitle("Add subinterface")

        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                QSize(300, 200),
                QGuiApplication.primaryScreen().availableGeometry()
            )
        )

        # Subinterface: [...]
        self.subinterface_header_layout = QHBoxLayout()
        self.subinterface_label = QLabel("Subinterface: ")
        self.subinterface_header_layout.addWidget(self.subinterface_label)
        self.subinterface_input = QLineEdit()
        self.subinterface_header_layout.addWidget(self.subinterface_input)
        if self.subinterface_id:
            # If editing existing subinterface, set the "subinterface ID" field and make it read-only
            self.subinterface_input.setText(self.subinterface_id)
            self.subinterface_input.setReadOnly(True)
        self.layout.addLayout(self.subinterface_header_layout)

        # IP: [...]
        self.ip_input = QLineEdit()
        if self.old_ip:
            # If replacing old IP, set the "IP address" field to the old one
            self.ip_input.setText(str(self.old_ip))
        else:
            self.ip_input.setPlaceholderText("Enter IP address")
        self.layout.addWidget(self.ip_input)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.confirmEdit)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)

    def confirmEdit(self):
        # Creating "new_ip" object (IPv4Interface or IPv6Interface)
        if self.old_ip:
            # If replacing old IP address, check the version of the old one and set the version of the new one accordingly
            if self.old_ip.version == 4:
                self.new_ip = ipaddress.IPv4Interface(self.ip_input.text())
            elif self.old_ip.version == 6:
                self.new_ip = ipaddress.IPv6Interface(self.ip_input.text())
        else:
            # If adding a new IP address, set the version of the newly entered IP address automatically (using the ipaddress library)
            self.new_ip = ipaddress.ip_interface(self.ip_input.text())

        if self.subinterface_id:
            # Editing existing subinterface
            if self.old_ip and self.old_ip != self.new_ip:
                # If old_ip was entered and the new_ip is different, replace the IP address
                self.device.dev_ReplaceInterfaceIP(self.interface_id, self.subinterface_id, self.old_ip, self.new_ip)
                self.editInterfaceDialog_instance.refreshDialog()
            elif self.old_ip and self.old_ip == self.new_ip:
                # If old_ip was entered and the new_ip is the same, do nothing
                showMessageBox(self, "Information", "No changes were made.")
            elif not self.old_ip:
                # If old_ip was not entered, set new ip address
                self.device.dev_SetInterfaceIP(self.interface_id, self.subinterface_id, self.new_ip)
                self.editInterfaceDialog_instance.refreshDialog()
        else:
            self.device.dev_SetInterfaceIP(self.interface_id, self.subinterface_input.text(), self.new_ip)
            self.editInterfaceDialog_instance.refreshDialog()
        self.accept()


class EditHostnameDialog(QDialog):
    def __init__(self, device):
        super().__init__()

        self.device = device
        self.old_hostname = self.device.hostname

        self.setWindowTitle("Edit hostname: " + self.old_hostname)
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                QSize(300, 100),
                QGuiApplication.primaryScreen().availableGeometry()
            )
        )
        
        self.layout = QVBoxLayout()

        # Input fields
        self.hostname_input = QLineEdit()
        self.hostname_input.setPlaceholderText(self.old_hostname)
        self.layout.addWidget(self.hostname_input)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.confirmRename)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)

    def confirmRename(self):
        new_hostname = self.hostname_input.text()

        if not new_hostname or (new_hostname and new_hostname == self.old_hostname):
            showMessageBox(self, "Information", "No changes were made.")
        elif new_hostname and new_hostname != self.old_hostname:
            self.device.dev_SetHostname(new_hostname)
            self.device.refreshHostnameLabel()
        self.accept()

class OSPFDialog(QDialog):
    def __init__(self):
        super().__init__()

class DebugDialog(QDialog):
    def __init__(self, addCable_callback, removeCable_callback):
        super().__init__()

        self.addCable_callback = addCable_callback
        self.removeCable_callback = removeCable_callback

        self.setWindowTitle("Debug")
        self.layout = QVBoxLayout()

        #Input fields
        self.devices = devices.Device.getAllDeviceInstances()

        self.device1_combo = QComboBox()
        self.device1_combo.addItems(self.devices)
        self.layout.addWidget(self.device1_combo)

        self.device2_combo = QComboBox()
        self.device2_combo.addItems(self.devices)
        self.layout.addWidget(self.device2_combo)

        #Buttons
        self.button_box = QDialogButtonBox()

        button1_addCable = QPushButton("ADD CABLE")
        button1_addCable.clicked.connect(self.addCableDebug)
        self.button_box.addButton(button1_addCable, QDialogButtonBox.AcceptRole)

        button2_removeCable = QPushButton("REMOVE CABLE")
        button2_removeCable.clicked.connect(self.removeCableDebug)
        self.button_box.addButton(button2_removeCable, QDialogButtonBox.AcceptRole)         
        
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

    def addCableDebug(self):
        device_1 = devices.Device.getDeviceInstance(self.device1_combo.currentText())
        device_2 = devices.Device.getDeviceInstance(self.device2_combo.currentText())
        self.addCable_callback(device_1, device_2)
        self.accept()

    def removeCableDebug(self):
        device_1 = devices.Device.getDeviceInstance(self.device1_combo.currentText())
        device_2 = devices.Device.getDeviceInstance(self.device2_combo.currentText())
        self.removeCable_callback(device_1, device_2)
        self.accept()