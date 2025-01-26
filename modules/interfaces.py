# Other
from pyangbind.lib.serialise import pybindIETFXMLEncoder
from ipaddress import IPv4Address, IPv6Address, IPv4Interface, IPv6Interface
from lxml import etree as ET

# Custom
import modules.netconf as netconf
import helper as helper
from definitions import *


#TMP potom uklidit
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
# TODO: predelat asi cele na XML soubory

def createFilter_EditIPAddress(interface, subinterface_index, ip, delete_ip=False):
    """
    Creates a NETCONF filter to edit or delete a subinterface IP address.
    Args:
        interface (str): The name of the interface.
        subinterface_index (int): The index of the subinterface.
        ip (IPv4Interface of IPv6Interface): An IPvXInterface object containing the IP address and network information.
        delete_ip (bool, optional): If True, the IP address will be marked for deletion. Defaults to False.
    Returns (example):
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
            <interfaces xmlns="http://openconfig.net/yang/interfaces">
                <interface>
                    <name>interface</name>
                    <subinterfaces>
                    <subinterface>
                        <index>subinterface_index</index>
                        <ipv4(ipv6) xmlns="http://openconfig.net/yang/interfaces/ip">
                        <addresses>
                            <address(operation="delete")>
                            <ip>ip.ip</ip>
                            <config>
                                <ip>ip.ip</ip>
                                <prefix-length>ip.network.prefixlen</prefix-length>
                            </config>
                            </address>
                        </addresses>
                        </ipv4>
                    </subinterface>
                    </subinterfaces>
                </interface>
            </interfaces>
        </config>
    """

    filter_xml = ET.parse(OPENCONFIG_XML_DIR + "/interfaces/edit_config-ip_address.xml")
    namespaces = {'ns': 'http://openconfig.net/yang/interfaces',
                  'oc-ip': 'http://openconfig.net/yang/interfaces/ip'}
    
    interface_name_element = filter_xml.find(".//ns:name", namespaces)
    interface_name_element.text = interface

    subinterface_index_element = filter_xml.find(".//ns:index", namespaces)
    subinterface_index_element.text = str(subinterface_index)

    if ip.version == 4:
        ipvX_element = filter_xml.findall(".//oc-ip:ipvX", namespaces)
        for ipvX in ipvX_element: # Opening and closing tags
            ipvX.tag = ipvX.tag.replace("ipvX", "ipv4")

        ipv4_element = filter_xml.find(".//oc-ip:ipv4", namespaces)
        address_element = ipv4_element.find(".//oc-ip:address", namespaces)
        address_element.set("operation", "delete") if delete_ip else None
        
        ip_elements = address_element.findall(".//oc-ip:ip", namespaces) # The IP address element is stored in TWO places in the XML
        for ip_element in ip_elements:
            ip_element.text = str(ip.ip)
        
        prefix_length_element = address_element.find(".//oc-ip:prefix-length", namespaces)
        prefix_length_element.text = str(ip.network.prefixlen)
    elif ip.version == 6:
        ipvX_element = filter_xml.findall(".//oc-ip:ipvX", namespaces)
        for ipvX in ipvX_element: # Opening and closing tags
            ipvX.tag = ipvX.tag.replace("ipvX", "ipv6")

        ipv6_element = filter_xml.find(".//oc-ip:ipv6", namespaces)
        address_element = ipv6_element.find(".//oc-ip:address", namespaces)
        address_element.set("operation", "delete") if delete_ip else None
        
        ip_elements = address_element.findall(".//oc-ip:ip", namespaces) # The IP address element is stored in TWO places in the XML
        for ip_element in ip_elements:
            ip_element.text = str(ip.ip)
        
        prefix_length_element = address_element.find(".//oc-ip:prefix-length", namespaces)
        prefix_length_element.text = str(ip.network.prefixlen)

    return(ET.tostring(filter_xml).decode('utf-8'))

# ---------- OPERATIONS: ----------
def getInterfaceListWithNetconf(device, getIPs=False):
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
    filter_xml = ET.parse(OPENCONFIG_XML_DIR + "/interfaces/get-all_interfaces.xml")
    rpc_filter = ET.tostring(filter_xml).decode('utf-8')

    # RPC
    rpc_reply = device.mngr.get(rpc_filter)
    rpc_reply_etree = helper.convertToEtree(rpc_reply, device_type)

    interfaces = []
    interface_names = rpc_reply_etree.xpath('//interfaces/interface/name')
    
    if getIPs:
        # If the getIPs flag is set, retrieve the first IP address for each interface (used for ListInterfacesDialog)
        for interface_name in interface_names:
            name = interface_name.text
            admin_status = interface_name.xpath('../state/admin-status')[0].text
            oper_status = interface_name.xpath('../state/oper-status')[0].text

            subinterface_indexes = interface_name.xpath('../subinterfaces/subinterface/index')
            if len(subinterface_indexes) > 0:
                if len(interface_name.xpath('../subinterfaces/subinterface/ipv4/addresses/address/state/ip')) > 0:
                    ipv4_address = interface_name.xpath('../subinterfaces/subinterface/ipv4/addresses/address/state/ip')[0].text
                    ipv4_prefix_length = interface_name.xpath('../subinterfaces/subinterface/ipv4/addresses/address/state/prefix-length')[0].text
                    ipv4_data = IPv4Interface(ipv4_address + '/' + ipv4_prefix_length)
                else:
                    ipv4_data = None

                if len(interface_name.xpath('../subinterfaces/subinterface/ipv6/addresses/address/state/ip')) > 0:
                    ipv6_address = interface_name.xpath('../subinterfaces/subinterface/ipv6/addresses/address/state/ip')[0].text
                    ipv6_prefix_length = interface_name.xpath('../subinterfaces/subinterface/ipv6/addresses/address/state/prefix-length')[0].text
                    ipv6_data = IPv6Interface(ipv6_address + '/' + ipv6_prefix_length)
                else:
                    ipv6_data = None

                interfaces.append((name, admin_status, oper_status, ipv4_data, ipv6_data))
            else:
                interfaces.append((name, admin_status, oper_status, None, None))
    else:
        # If the getIPs flag is not set, retrieve only the interface names
        for interface_name in interface_names:
            name = interface_name.text
            admin_status = interface_name.xpath('../state/admin-status')[0].text
            oper_status = interface_name.xpath('../state/oper-status')[0].text
            interfaces.append((name, admin_status, oper_status))
    return(interfaces)

def getSubinterfacesWithNetconf(device, interface_name):
    """
    Retrieve subinterfaces for a specific interface.
    Args:
        device (object): The network device object which contains ncclient manager.
        interface_name (str): The name of the interface for which details are to be retrieved.
    Returns:
        list: A list of dictionaries, each containing details of a subinterface.

        [{'subinterface_index': '0', 'ipv4': [IPv4Interface('1.1.1.2/24')], 'ipv6': [IPv6Interface('2001::1/64')]}]
    """

    device_type = device.device_parameters['device_params']
    
    # FILTER
    filter_xml = ET.parse(OPENCONFIG_XML_DIR + "/interfaces/get-interface.xml")
    namespaces = {'ns': 'http://openconfig.net/yang/interfaces'}
    interface_name_element = filter_xml.find(".//ns:name", namespaces)
    interface_name_element.text = interface_name
    rpc_filter = ET.tostring(filter_xml).decode('utf-8') 

    # RPC
    rpc_reply = device.mngr.get(rpc_filter)
    rpc_reply_etree = helper.convertToEtree(rpc_reply, device_type)

    subinterfaces = []
    for subinterface in rpc_reply_etree.findall('.//interfaces/interface/subinterfaces/subinterface'):
        subinterface_index = subinterface.find('.//index').text

        ipv4_data = []
        for ipv4_object in subinterface.findall('.//ipv4/addresses/address'):
            ipv4_address = ipv4_object.find('state/ip')
            ipv4_prefix_length = ipv4_object.find('state/prefix-length')
            if ipv4_address is not None and ipv4_prefix_length is not None:
                ipv4_data.append((IPv4Interface(ipv4_address.text + '/' + ipv4_prefix_length.text)))

        ipv6_data = []
        for ipv6_object in subinterface.findall('.//ipv6/addresses/address'):
            ipv6_address = ipv6_object.find('state/ip')
            ipv6_prefix_length = ipv6_object.find('state/prefix-length')
            if ipv6_address is not None and ipv6_prefix_length is not None:
                ipv6_data.append((IPv6Interface(ipv6_address.text + '/' + ipv6_prefix_length.text)))
        
        subinterfaces.append({"subinterface_index": subinterface_index, "ipv4": ipv4_data, "ipv6": ipv6_data})
    return(subinterfaces)

def deleteIpWithNetconf(device, interface_name, subinterface_index, old_ip):
    """
    Delete an IP address from a specified interface.
    Args:
        device: The network device object which contains ncclient manager.
        interface_name (str): The name of the interface from which the IP address will be deleted.
        subinterface_index (int): The index of the subinterface.
        old_ip (str): The IP address to be deleted.
    Returns:
        rpc_reply: The response from the device after attempting to delete the IP address.
    """
    # FILTER
    filter = createFilter_EditIPAddress(interface_name, subinterface_index, old_ip, delete_ip=True)

    # RPC
    rpc_reply = device.mngr.edit_config(filter, target=CONFIGURATION_TARGET_DATASTORE)
    return(rpc_reply)

def setIpWithNetconf(device, interface_name, subinterface_index, new_ip):
    """
    Set an IP address on a specified interface.
    Args:
        device: The network device object which contains ncclient manager.
        interface_name (str): The name of the interface on which the IP address will be added.
        subinterface_index (int): The index of the subinterface.
        old_ip (str): The IP address to be added.
    Returns:
        rpc_reply: The response from the device after attempting to set the IP address.
    """   
    # FILTER
    filter = createFilter_EditIPAddress(interface_name, subinterface_index, new_ip)
    
    # RPC
    rpc_reply = device.mngr.edit_config(filter, target=CONFIGURATION_TARGET_DATASTORE)
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
            
    
