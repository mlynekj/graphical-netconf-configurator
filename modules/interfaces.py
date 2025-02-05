# Other
from pyangbind.lib.serialise import pybindIETFXMLEncoder
from ipaddress import IPv4Address, IPv6Address, IPv4Interface, IPv6Interface
from lxml import etree as ET

# Custom
import modules.netconf as netconf
import helper as helper
from definitions import *

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
    QMessageBox,)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QGuiApplication, QAction, QBrush, QColor
import ipaddress

# ---------- FILTERS: ----------
class GetInterfacesOpenconfigFilter:
    def __init__(self):
        self.filter_xml = ET.parse(OPENCONFIG_XML_DIR + "/interfaces/get-all_interfaces.xml")

    def __str__(self):
        """
        This method converts the filter_xml attribute to a string using the
        ElementTree tostring method and decodes it to UTF-8.
        This is needed for dispatching RPCs with ncclient.

        Returns:
            str: The string representation of the filter_xml attribute.
        """
        return(ET.tostring(self.filter_xml).decode('utf-8'))

class EditIPAddressOpenconfigFilter:
    def __init__(self, interface, subinterface_index, ip, delete_ip=False):
        self.interface = interface
        self.subinterface_index = subinterface_index
        self.ip = ip
        self.delete_ip = delete_ip

        # Load the XML filter template
        self.filter_xml = ET.parse(OPENCONFIG_XML_DIR + "/interfaces/edit_config-ip_address.xml")
        self.namespaces = {'ns': 'http://openconfig.net/yang/interfaces',
                           'oc-ip': 'http://openconfig.net/yang/interfaces/ip'}

        # Set the interface name and subinterface index
        interface_name_element = self.filter_xml.find(".//ns:name", self.namespaces)
        interface_name_element.text = interface

        subinterface_index_element = self.filter_xml.find(".//ns:index", self.namespaces)
        subinterface_index_element.text = str(subinterface_index)

        if self.ip.version == 4:
            self.createIPV4Filter()
        elif self.ip.version == 6:
            self.createIPV6Filter()

    def __str__(self):
        """
        This method converts the filter_xml attribute to a string using the
        ElementTree tostring method and decodes it to UTF-8.
        This is needed for dispatching RPCs with ncclient.

        Returns:
            str: The string representation of the filter_xml attribute.
        """
        return(ET.tostring(self.filter_xml).decode('utf-8'))

    def createIPV4Filter(self):
        ipvX_element = self.filter_xml.findall(".//oc-ip:ipvX", self.namespaces)
        for ipvX in ipvX_element: # Opening and closing tags
            ipvX.tag = ipvX.tag.replace("ipvX", "ipv4")

        ipv4_element = self.filter_xml.find(".//oc-ip:ipv4", self.namespaces)
        address_element = ipv4_element.find(".//oc-ip:address", self.namespaces)
        address_element.set("operation", "delete") if self.delete_ip else None
        
        ip_elements = address_element.findall(".//oc-ip:ip", self.namespaces) # The IP address element is stored in TWO places in the XML
        for ip_element in ip_elements:
            ip_element.text = str(self.ip.ip)
        
        prefix_length_element = address_element.find(".//oc-ip:prefix-length", self.namespaces)
        prefix_length_element.text = str(self.ip.network.prefixlen)

    def createIPV6Filter(self):
        ipvX_element = self.filter_xml.findall(".//oc-ip:ipvX", self.namespaces)
        for ipvX in ipvX_element: # Opening and closing tags
            ipvX.tag = ipvX.tag.replace("ipvX", "ipv6")

        ipv4_element = self.filter_xml.find(".//oc-ip:ipv6", self.namespaces)
        address_element = ipv4_element.find(".//oc-ip:address", self.namespaces)
        address_element.set("operation", "delete") if self.delete_ip else None
        
        ip_elements = address_element.findall(".//oc-ip:ip", self.namespaces) # The IP address element is stored in TWO places in the XML
        for ip_element in ip_elements:
            ip_element.text = str(self.ip.ip)
        
        prefix_length_element = address_element.find(".//oc-ip:prefix-length", self.namespaces)
        prefix_length_element.text = str(self.ip.network.prefixlen)


# ---------- OPERATIONS: ----------
# -- Retrieval --
def getInterfacesWithNetconf(device):
    """
    TODO:
    """

    device_type = device.device_parameters['device_params']

    # FILTER
    filter = GetInterfacesOpenconfigFilter()

    # RPC
    rpc_reply = device.mngr.get(str(filter))
    rpc_reply_etree = helper.convertToEtree(rpc_reply, device_type)

    interfaces = {}
    interface_elements = rpc_reply_etree.xpath('//interfaces/interface/name')
    
    for interface_element in interface_elements:
        name = interface_element.text
        admin_status = interface_element.xpath('../state/admin-status')[0].text
        oper_status = interface_element.xpath('../state/oper-status')[0].text

        subinterfaces = {}
        subinterface_indexes = interface_element.xpath('../subinterfaces/subinterface/index')
        for subinterface_index in subinterface_indexes:
            subinterface_element = subinterface_index.getparent()
            
            ipv4_data = extractIPDataFromSubinterface(subinterface_element, version="ipv4")
            ipv6_data = extractIPDataFromSubinterface(subinterface_element, version="ipv6")
            subinterfaces[subinterface_index.text] = {
                'ipv4_data': ipv4_data,
                'ipv6_data': ipv6_data
            }

        interfaces[name] = {
            'admin_status': admin_status,
            'oper_status': oper_status,
            'subinterfaces': subinterfaces
        }

    return(interfaces)

def extractIPDataFromSubinterface(subinterface_element, version="ipv4"):
    ipvX_object_tag = (f".//{version}/addresses/address")
    ipvX_objects = subinterface_element.findall(ipvX_object_tag)

    ipvX_data = []
    for ipvX_object in ipvX_objects:
        ipvX_address = ipvX_object.find('state/ip')
        ipvX_prefix_length = ipvX_object.find('state/prefix-length')
        if ipvX_address is not None and ipvX_prefix_length is not None: 
            # cannot use "if ipvX_address and ipvX_prefix_length"
            # because "FutureWarning: The behavior of this method will change in future versions. Use specific 'len(elem)' or 'elem is not None' test instead"
            ip_interface = IPv4Interface(f"{ipvX_address.text}/{ipvX_prefix_length.text}") if version == "ipv4" else IPv6Interface(f"{ipvX_address.text}/{ipvX_prefix_length.text}")
            ipvX_data.append({'value': ip_interface, 'flag': 'commited'})
    return(ipvX_data)

# -- Manipulation with IPs --
def deleteIpWithNetconf(device, interface_element, subinterface_index, old_ip):
    """
    Delete an IP address from a specified interface.
    Args:
        device: The network device object which contains ncclient manager.
        interface_element (str): The name of the interface from which the IP address will be deleted.
        subinterface_index (int): The index of the subinterface.
        old_ip (str): The IP address to be deleted.
    Returns:
        rpc_reply: The response from the device after attempting to delete the IP address.
    """

    # FILTER
    filter = EditIPAddressOpenconfigFilter(interface_element, subinterface_index, old_ip, delete_ip=True)

    # RPC
    rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
    return(rpc_reply)

def setIpWithNetconf(device, interface_element, subinterface_index, new_ip):
    """
    Set an IP address on a specified interface.
    Args:
        device: The network device object which contains ncclient manager.
        interface_element (str): The name of the interface on which the IP address will be added.
        subinterface_index (int): The index of the subinterface.
        old_ip (str): The IP address to be added.
    Returns:
        rpc_reply: The response from the device after attempting to set the IP address.
    """   

    # FILTER
    filter = EditIPAddressOpenconfigFilter(interface_element, subinterface_index, new_ip)
    
    # RPC
    rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
    return(rpc_reply)


# ---------- QT: ----------
def checkFlag(flag):
    if flag == "commited":
        return "white"
    elif flag == "uncommited":
        return "yellow"
    elif flag == "deleted":
        return "red"
    

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

        # Retrieve the interfaces from the device
        try:
            self.interfaces = self.device.interfaces
        except Exception as e:
            self.interfaces = {}
            self.error_label = QLabel(f"Failed to retrieve self.interfaces: {e}")
            self.table_layout.addWidget(self.error_label)

        # Populate the table with the interfaces
        if self.interfaces:
            self.interfaces_table.setRowCount(len(self.interfaces))
            for row, (interface_element, interface_data) in enumerate(self.interfaces.items()):      
                admin_state = interface_data['admin_status']
                oper_state = interface_data['oper_status']
                ipv4_data, ipv6_data = self.getFirstIPAddresses(interface_data['subinterfaces'])

                # Flag: commited, uncommited, deleted
                bg_color = "white"
                if ipv4_data:
                    bg_color = checkFlag(ipv4_data['flag'])
                if ipv6_data:
                    bg_color = checkFlag(ipv6_data['flag'])

                # Interface name
                interface_item = QTableWidgetItem(interface_element)
                interface_item.setFlags(interface_item.flags() ^ Qt.ItemIsEditable)  # Non-editable cells
                interface_item.setBackground(QBrush(QColor(bg_color)))
                self.interfaces_table.setItem(row, 0, interface_item)
                # Administrative state
                admin_state_item = QTableWidgetItem(admin_state)
                admin_state_item.setFlags(admin_state_item.flags() ^ Qt.ItemIsEditable)
                admin_state_item.setBackground(QBrush(QColor(bg_color)))
                self.interfaces_table.setItem(row, 1, admin_state_item)
                # Operational state
                oper_state_item = QTableWidgetItem(oper_state)
                oper_state_item.setFlags(oper_state_item.flags() ^ Qt.ItemIsEditable)
                oper_state_item.setBackground(QBrush(QColor(bg_color)))
                self.interfaces_table.setItem(row, 2, oper_state_item)
                # IPv4 
                ipv4_item = QTableWidgetItem(str(ipv4_data['value']) if ipv4_data else "")
                ipv4_item.setFlags(ipv4_item.flags() ^ Qt.ItemIsEditable)
                ipv4_item.setBackground(QBrush(QColor(bg_color)))
                self.interfaces_table.setItem(row, 3, ipv4_item)
                # IPv6
                ipv6_item = QTableWidgetItem(str(ipv6_data['value']) if ipv6_data else "")
                ipv6_item.setFlags(ipv6_item.flags() ^ Qt.ItemIsEditable)
                ipv6_item.setBackground(QBrush(QColor(bg_color)))
                self.interfaces_table.setItem(row, 4, ipv6_item)
                # Edit button
                button_item = QPushButton("Edit")
                button_item.clicked.connect(self.showDialog)
                self.interfaces_table.setCellWidget(row, 5, button_item)      
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

    def getFirstIPAddresses(self, subinterfaces):
        """
        TODO:
        """

        ipv4_data = ""
        ipv6_data = ""
        for subinterface in subinterfaces.values():
            if subinterface['ipv4_data'] and not ipv4_data:
                ipv4_data = subinterface['ipv4_data'][0]
            if subinterface['ipv6_data'] and not ipv6_data:
                ipv6_data = subinterface['ipv6_data'][0]
            if ipv4_data and ipv6_data:
                break
        return ipv4_data, ipv6_data

    def showDialog(self):
        button = self.sender()

        row_index = self.interfaces_table.indexAt(button.pos()) # Get the index of the row, in which was the button clicked
        interface_id = self.interfaces_table.item(row_index.row(), 0).text() # Get the interface ID of the clicked row
            
        dialog = EditInterfaceDialog(self, self.device, interface_id)
        dialog.exec()

    def refreshDialog(self):
        helper.clearLayout(self.layout)
        self.fillLayout()
        self.setLayout(self.layout)


class EditInterfaceDialog(QDialog):
    def __init__(self, instance, device, interface_id):
        super().__init__()

        self.instance = instance
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

    def fillLayout(self):
        # Toolbar
        self.toolbar = QToolBar("Edit interface", self)
        self.action_addSubinterface = QAction("Add subinterface", self)
        self.action_addSubinterface.triggered.connect(lambda _, index=None : self.showDialog(index))
        self.toolbar.addAction(self.action_addSubinterface)
        self.layout.addWidget(self.toolbar)

        # Get subinterfaces, create a layout for each subinterface containg: Header, Table
        self.subinterfaces = self.device.interfaces[self.interface_id]['subinterfaces']
        for subinterface_index, subinterface_data in self.subinterfaces.items():
            subinterface_layout = QVBoxLayout()
            
            # Header ("Subinterface: x | [Add IP address]")
            subinterface_label = QLabel(f"Subinterface: {subinterface_index}")
            subinterface_label.setFont(QFont("Arial", 16))
            add_ip_button = QPushButton("Add IP address")
            add_ip_button.clicked.connect(lambda _, index=subinterface_index : self.showDialog(index))
            header_layout = QHBoxLayout()
            header_layout.addWidget(subinterface_label)
            header_layout.addWidget(add_ip_button)
            subinterface_layout.addLayout(header_layout)

            # Table
            subinterface_layout.addWidget(self.createSubinterfaceTable(subinterface_index, subinterface_data))
            
            self.layout.addLayout(subinterface_layout)

    def createSubinterfaceTable(self, subinterface_index, subinterface_data):
        """
        TODO:
        """

        # Create the table, set basic properties
        subinterface_table = QTableWidget()
        subinterface_table.setColumnCount(3)
        subinterface_table.setRowCount(len(subinterface_data['ipv4_data']) + len(subinterface_data['ipv6_data']))
        subinterface_table.setHorizontalHeaderLabels(["Address", "", ""])
        subinterface_table.horizontalHeader().setStretchLastSection(True)
        subinterface_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        row = 0
        for ipv4_data in subinterface_data['ipv4_data']:
            # Flag: commited, uncommited, deleted
            bg_color = "white"
            if ipv4_data:
                bg_color = checkFlag(ipv4_data['flag'])

            # IPv4 address
            ip_item = QTableWidgetItem(f"{ipv4_data['value'].ip}/{ipv4_data['value'].network.prefixlen}")
            ip_item.setBackground(QBrush(QColor(bg_color)))
            subinterface_table.setItem(row, 0, ip_item)
            # Edit button
            edit_ip_button_item = QPushButton("Edit")
            edit_ip_button_item.clicked.connect(lambda _, index=subinterface_index, ip = ipv4_data['value'] : self.showDialog(index, ip)) # _ = unused argument
            subinterface_table.setCellWidget(row, 1, edit_ip_button_item)
            # Delete button
            delete_ip_button_item = QPushButton("Delete")
            delete_ip_button_item.clicked.connect(lambda _, index=subinterface_index, ip = ipv4_data['value'] : self.deleteIP(index, ip))
            subinterface_table.setCellWidget(row, 2, delete_ip_button_item)
            
            row += 1
        
        for ipv6_data in subinterface_data['ipv6_data']:
            # Flag: commited, uncommited, deleted
            bg_color = "white"
            if ipv6_data:
                bg_color = checkFlag(ipv6_data['flag'])

            # IPv6 address
            subinterface_table.setItem(row, 0, QTableWidgetItem(f"{ipv6_data['value'].ip}/{ipv6_data['value'].network.prefixlen}"))
            # Edit button
            edit_ip_button_item = QPushButton("Edit")
            edit_ip_button_item.clicked.connect(lambda _, index=subinterface_index, ip = ipv6_data['value'] : self.showDialog(index, ip)) # _ = unused argument
            subinterface_table.setCellWidget(row, 1, edit_ip_button_item)
            # Delete button
            delete_ip_button_item = QPushButton("Delete")
            delete_ip_button_item.clicked.connect(lambda _, index=subinterface_index, ip = ipv6_data['value'] : self.deleteIP(index, ip))
            subinterface_table.setCellWidget(row, 2, delete_ip_button_item)

            row += 1
        return subinterface_table
    
    def deleteIP(self, subinterface_index, old_ip):
        self.device.deleteInterfaceIP(self.interface_id, subinterface_index, old_ip)
        #self.refreshDialog()

    def closeEvent(self, event):
        """ Refresh the parent dialog when this dialog is closed. """
        self.instance.refreshDialog()
        super().closeEvent(event)

    def showDialog(self, subinterface_index, ip = None):       
        self.editSubinterfaceDialog = EditSubinterfaceDialog(self, self.device, self.interface_id, subinterface_index, ip)
        self.editSubinterfaceDialog.exec()

    def refreshDialog(self):
        helper.clearLayout(self.layout)
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
                self.device.replaceInterfaceIP(self.interface_id, self.subinterface_id, self.old_ip, self.new_ip)
                self.editInterfaceDialog_instance.refreshDialog()
            elif self.old_ip and self.old_ip == self.new_ip:
                # If old_ip was entered and the new_ip is the same, do nothing
                helper.showMessageBox(self, "Information", "No changes were made.")
            elif not self.old_ip:
                # If old_ip was not entered, set new ip address
                self.device.setInterfaceIP(self.interface_id, self.subinterface_id, self.new_ip)
                self.editInterfaceDialog_instance.refreshDialog()
        else:
            self.device.setInterfaceIP(self.interface_id, self.subinterface_input.text(), self.new_ip)
            self.editInterfaceDialog_instance.refreshDialog()
        self.accept()