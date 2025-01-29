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
    QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QGuiApplication, QAction
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

class GetSubinterfacesOpenconfigFilter:
    def __init__(self, interface_element):
        self.filter_xml = ET.parse(OPENCONFIG_XML_DIR + "/interfaces/get-interface.xml")
        self.namespaces = {'ns': 'http://openconfig.net/yang/interfaces'}

        interface_name_element = self.filter_xml.find(".//ns:name", self.namespaces)
        interface_name_element.text = interface_element

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
# -- Interface --
def getInterfacesWithNetconf(device, getIPs=False):
    """
    Retrieve the list of interfaces from a network device, optionally including IP address information.
    Args:
        device (object): The network device object which contains ncclient manager.
        getIPs (bool, optional): If True, include IP address information for each interface. Defaults to False.
    Returns:
        list: A list of tuples representing the interfaces.

        [(name, admin_status, oper_status, ipv4_data, ipv6_data), ...]
        [('ge-0/0/0', 'UP', 'UP', IPv4Interface('192.168.1.1/24'), IPv6Interface('2001:db8::1/64')), ('ge-0/0/1', 'UP', 'UP', None, None)]
    """

    device_type = device.device_parameters['device_params']

    # FILTER
    filter = GetInterfacesOpenconfigFilter()

    # RPC
    rpc_reply = device.mngr.get(str(filter))
    rpc_reply_etree = helper.convertToEtree(rpc_reply, device_type)

    interfaces = []
    interface_elements = rpc_reply_etree.xpath('//interfaces/interface/name')
    
    # If the getIPs flag is NOT set, retrieve only the interface names and states
    if not getIPs:
        for interface_element in interface_elements:
            name = interface_element.text
            admin_status = interface_element.xpath('../state/admin-status')[0].text
            oper_status = interface_element.xpath('../state/oper-status')[0].text
            interfaces.append((name, admin_status, oper_status))
            return(interfaces)
        
    # If the getIPs flag is set, retrieve the first IP address for each interface (used for DeviceInterfacesDialog)
    for interface_element in interface_elements:
        name = interface_element.text
        admin_status = interface_element.xpath('../state/admin-status')[0].text
        oper_status = interface_element.xpath('../state/oper-status')[0].text

        subinterface_indexes = interface_element.xpath('../subinterfaces/subinterface/index')
        if len(subinterface_indexes) < 0: # If there are no subinterfaces
            interfaces.append((name, admin_status, oper_status, None, None))
            continue # Skip to the next interface

        ipv4_data = extractIPDataFromInterface(interface_element, version="ipv4")
        ipv6_data = extractIPDataFromInterface(interface_element, version="ipv6")
        interfaces.append((name, admin_status, oper_status, ipv4_data, ipv6_data))

    return(interfaces)

def extractIPDataFromInterface(interface_element, version="ipv4"):
    # XML Tags
    ipvX_address_tag = (f"../subinterfaces/subinterface/{version}/addresses/address/state/ip")
    ipvX_prefix_length_tag = (f"../subinterfaces/subinterface/{version}/addresses/address/state/prefix-length")

    # Extraction using XPath
    ipvX_address_node = interface_element.xpath(ipvX_address_tag)
    ipvX_prefix_length_node = interface_element.xpath(ipvX_prefix_length_tag)

    # Get data from nodes
    if ipvX_address_node and ipvX_prefix_length_node:
        ipvX_address = ipvX_address_node[0].text
        ipvX_prefix_length = ipvX_prefix_length_node[0].text
        ipvX_data = IPv4Interface(f"{ipvX_address}/{ipvX_prefix_length}") if version == "ipv4" else IPv6Interface(f"{ipvX_address}/{ipvX_prefix_length}")
    else:
        ipvX_data = None

    return(ipvX_data)

# -- Subinterface --
def getSubinterfacesWithNetconf(device, interface_element):
    """
    Retrieve subinterfaces for a specific interface.
    Args:
        device (object): The network device object which contains ncclient manager.
        interface_element (str): The name of the interface for which details are to be retrieved.
    Returns:
        list: A list of dictionaries, each containing details of a subinterface.

        [{'subinterface_index': '0', 'ipv4': [IPv4Interface('1.1.1.2/24')], 'ipv6': [IPv6Interface('2001::1/64')]}]
    """

    device_type = device.device_parameters['device_params']
    
    # FILTER
    filter = GetSubinterfacesOpenconfigFilter(interface_element)

    # RPC
    rpc_reply = device.mngr.get(str(filter))
    rpc_reply_etree = helper.convertToEtree(rpc_reply, device_type)

    raw_subinterfaces = rpc_reply_etree.findall('.//interfaces/interface/subinterfaces/subinterface')
    extracted_subinterfaces = []

    for subinterface in raw_subinterfaces:
        subinterface_index = subinterface.find('.//index').text

        ipv4_data = extractIPDataFromSubinterface(subinterface, version="ipv4")
        ipv6_data = extractIPDataFromSubinterface(subinterface, version="ipv6")
        extracted_subinterfaces.append({"subinterface_index": subinterface_index, "ipv4": ipv4_data, "ipv6": ipv6_data})
    return(extracted_subinterfaces)

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
            ipvX_data.append(IPv4Interface(f"{ipvX_address.text}/{ipvX_prefix_length.text}") if version == "ipv4" else IPv6Interface(f"{ipvX_address.text}/{ipvX_prefix_length.text}"))
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
            self.interfaces = self.device.getInterfaces(getIPs=True)
        except Exception as e:
            self.interfaces = []
            self.error_label = QLabel(f"Failed to retrieve self.interfaces: {e}")
            self.table_layout.addWidget(self.error_label)

        # Populate the table with the interfaces
        if self.interfaces:
            self.interfaces_table.setRowCount(len(self.interfaces))
            for row, (interface_element, admin_state, oper_state, ipv4_data, ipv6_data) in enumerate(self.interfaces):      
                # Interface name
                self.interface_item = QTableWidgetItem(interface_element)
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
        self.device.deleteInterfaceIP(self.interface_id, subinterface_index, old_ip)
        #self.refreshDialog()

    def closeEvent(self, event):
        """ Refresh the parent dialog when this dialog is closed. """
        #self.instance.refreshDialog()
        # refresh of dialog no longer needed. When working with candidate datastore, the change is not immediately visible.
        super().closeEvent(event)

    def fillLayout(self):
        # Toolbar
        self.toolbar = QToolBar("Edit interface", self)
        self.action_addSubinterface = QAction("Add subinterface", self)
        self.action_addSubinterface.triggered.connect(lambda _, index=None : self.showDialog(index))
        self.toolbar.addAction(self.action_addSubinterface)
        self.layout.addWidget(self.toolbar)

        # Get subinterfaces, create a layout for each subinterface containg: Header, Table
        self.subinterfaces = self.device.getSubinterfaces(self.interface_id)
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