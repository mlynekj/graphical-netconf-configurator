# Other
from pyangbind.lib.serialise import pybindIETFXMLEncoder
from ipaddress import IPv4Address, IPv6Address, IPv4Interface, IPv6Interface
from lxml import etree as ET

from ncclient import operations

# Custom
import modules.netconf as netconf
import utils as utils
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
    QGroupBox,
    QMessageBox,)
from PySide6.QtCore import Qt, QSize, Slot
from PySide6.QtGui import QFont, QGuiApplication, QAction, QBrush, QColor

import ipaddress

from ui.ui_interfacesdialog import Ui_Interfaces
from ui.ui_addinterfacedialog import Ui_add_interface_dialog
from ui.ui_editinterfacedialog import Ui_edit_interface_dialog

from yang.filters import GetFilter, EditconfigFilter

# ---------- OPERATIONS: ----------
# -- Retrieval --
def getInterfacesWithNetconf(device):
    """
    TODO: documentation
    """

    device_type = device.device_parameters['device_params']

    # FILTER
    filter = OpenconfigInterfaces_Get_GetAllInterfaces_Filter()

    # RPC
    rpc_reply = device.mngr.get(str(filter))
    rpc_reply_etree = utils.convertToEtree(rpc_reply, device_type)

    interfaces = {}
    interface_elements = rpc_reply_etree.xpath('//interfaces/interface/name')
    
    for interface_element in interface_elements:
        name = interface_element.text
        # After update of JUNOS (vRouter 24.2R1.S2) Juniper returns !THREE! <interfaces>...</interfaces> tags for each interface, 
        # so i need to skip the duplicate tags to avoid overwriting the data with empty values
        if name not in interfaces:
            admin_status_element = interface_element.find('../state/admin-status')
            admin_status = interface_element.find('../state/admin-status').text if admin_status_element is not None else None
            oper_status_element = interface_element.find('../state/oper-status')
            oper_status = interface_element.find('../state/oper-status').text if oper_status_element is not None else None
            description_element = interface_element.find('../config/description')
            description = interface_element.find('../config/description').text if description_element is not None else None

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
                'description': description,
                'subinterfaces': subinterfaces
            }

            # If the device has VLAN capabilites, get VLAN data
            if hasattr(device, "addVlan") and hasattr(device, "configureInterfaceVlan"):
                vlan_data = extractVlanDataFromInterface(interface_element)
                interfaces[name]["vlan_data"] = vlan_data

    return(interfaces, rpc_reply)

def extractIPDataFromSubinterface(subinterface_element, version="ipv4"):
    ipvX_object_tag = (f".//{version}/addresses/address")
    ipvX_objects = subinterface_element.findall(ipvX_object_tag)

    ipvX_data = []
    for ipvX_object in ipvX_objects:
        ipvX_address = ipvX_object.find('state/ip')
        ipvX_prefix_length = ipvX_object.find('state/prefix-length')
        if ipvX_address is not None and ipvX_prefix_length is not None: 
            ip_interface = IPv4Interface(f"{ipvX_address.text}/{ipvX_prefix_length.text}") if version == "ipv4" else IPv6Interface(f"{ipvX_address.text}/{ipvX_prefix_length.text}")
            ipvX_data.append({'value': ip_interface, 'flag': 'commited'})
    return(ipvX_data)

def extractVlanDataFromInterface(interface_element):
    vlan_data = {}
    vlan_element = interface_element.find('../ethernet/switched-vlan/config')
    if vlan_element is not None:
        interface_mode = vlan_element.find('interface-mode')
        if interface_mode is not None:
            vlan_data["switchport_mode"] = interface_mode.text.lower()
            if vlan_data["switchport_mode"] == "access":
                vlan = vlan_element.find('access-vlan')
                vlan_data["vlan"] = vlan.text if vlan is not None else None
            elif vlan_data["switchport_mode"] == "trunk":
                vlans = vlan_element.findall('trunk-vlans')
                vlan_data["vlan"] = [vlan.text for vlan in vlans] if vlans is not None else None

    return vlan_data

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
    filter = OpenconfigInterfaces_Editconfig_EditIpaddress_Filter(interface_element, subinterface_index, old_ip, delete_ip=True)

    # RPC
    rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
    return(rpc_reply, filter)

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

    try:
        # FILTER
        filter = OpenconfigInterfaces_Editconfig_EditIpaddress_Filter(interface_element, subinterface_index, new_ip)
        
        # RPC
        rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
        return(rpc_reply, filter)
    except operations.errors.RPCError as e:
        utils.printGeneral(f"Failed to set IP on device {device.id}: {e}")
        return (rpc_reply, filter)
    except Exception as e:
        utils.printGeneral(f"Failed to set IP on device {device.id}: {e}")
        return None

# -- Add new interfaces --
def addInterfaceWithNetconf(device, interface_id, interface_type):
    try:
        # FILTER
        filter = OpenconfigInterfaces_Editconfig_AddInterface_Filter(interface_id, interface_type)
        
        # RPC
        rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
        return(rpc_reply, filter)
    except operations.errors.RPCError as e:
        utils.printGeneral(f"Failed to add interface on device {device.id}: {e}")
        return (rpc_reply)
    except Exception as e:
        utils.printGeneral(f"Failed to add interface on device {device.id}: {e}")
        return None



# ---------- FILTERS: ----------
class OpenconfigInterfaces_Get_GetAllInterfaces_Filter(GetFilter):
    def __init__(self):
        self.filter_xml = ET.parse(INTERFACES_YANG_DIR + "openconfig-interfaces_get_get-all-interfaces.xml")


class OpenconfigInterfaces_Editconfig_EditIpaddress_Filter(EditconfigFilter):
    def __init__(self, interface, subinterface_index, ip, delete_ip=False):
        self.interface = interface
        self.subinterface_index = subinterface_index
        self.ip = ip
        self.delete_ip = delete_ip

        # Load the XML filter template
        self.filter_xml = ET.parse(INTERFACES_YANG_DIR + "openconfig-interfaces_editconfig_edit_ipaddress.xml")
        self.namespaces = {'ns': 'http://openconfig.net/yang/interfaces',
                           'oc-ip': 'http://openconfig.net/yang/interfaces/ip',
                           'iana-iftype': 'urn:ietf:params:xml:ns:yang:iana-if-type'}

        # Set the interface name
        interface_name_element = self.filter_xml.find(".//ns:name", self.namespaces)
        interface_name_element.text = interface

        # Set the interface type
        interface_type_element = self.filter_xml.find(".//ns:type", self.namespaces)
        if "loopback" in self.interface.lower() or "lo" in self.interface.lower():
            self.interface_type = "ianaift:softwareLoopback" # Loopback
        else:
            self.interface_type = "ianaift:ethernetCsmacd" # Default
        interface_type_element.text = self.interface_type

        # Set the subinterface index
        subinterface_index_element = self.filter_xml.find(".//ns:index", self.namespaces)
        subinterface_index_element.text = str(subinterface_index)

        # Set the IP address and prefix length
        if self.ip.version == 4:
            self.createIPV4Filter()
        elif self.ip.version == 6:
            self.createIPV6Filter()

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

        ipv6_element = self.filter_xml.find(".//oc-ip:ipv6", self.namespaces)
        address_element = ipv6_element.find(".//oc-ip:address", self.namespaces)
        address_element.set("operation", "delete") if self.delete_ip else None
        
        ip_elements = address_element.findall(".//oc-ip:ip", self.namespaces) # The IP address element is stored in TWO places in the XML
        for ip_element in ip_elements:
            ip_element.text = str(self.ip.ip)
        
        prefix_length_element = address_element.find(".//oc-ip:prefix-length", self.namespaces)
        prefix_length_element.text = str(self.ip.network.prefixlen)


class OpenconfigInterfaces_Editconfig_AddInterface_Filter(EditconfigFilter):
    def __init__(self, interface_id, interface_type):
        self.interface_id = interface_id
        self.interface_type = interface_type

        # Load the XML filter template
        self.filter_xml = ET.parse(INTERFACES_YANG_DIR + "openconfig-interfaces_editconfig_add_interface.xml")
        self.namespaces = {'ns': 'http://openconfig.net/yang/interfaces',
                            'iana-iftype': 'urn:ietf:params:xml:ns:yang:iana-if-type'}

        # Set the interface name
        interface_name_elements = self.filter_xml.findall(".//ns:name", self.namespaces)
        for element in interface_name_elements:
            element.text = interface_id
        
        # Set the interface type
        interface_type_element = self.filter_xml.find(".//ns:type", self.namespaces)
        if interface_type == "Loopback":
            interface_type_element.text = "ianaift:softwareLoopback"


# ---------- QT: ----------
class DeviceInterfacesDialog(QDialog):
    def __init__(self, device):
        super().__init__()

        self.device = device

        self.ui = Ui_Interfaces()
        self.ui.setupUi(self)

        self.setWindowTitle("Device Interfaces")
        self.ui.close_button_box.button(QDialogButtonBox.Close).clicked.connect(self.close)
        self.ui.add_interface_button.clicked.connect(self.showAddInterfaceDialog)
        self.ui.refresh_button.clicked.connect(self.refreshInterfaces)
        self.fillLayout()

    def fillLayout(self):
        # Retrieve the interfaces from the device
        try:
            self.interfaces = self.device.interfaces
        except Exception as e:
            self.interfaces = {}
            QMessageBox.critical(self, "Error", f"An error occured while retrieving the interfaces from the device: {e}")

        # Populate the table with the interfaces
        if self.interfaces:
            self.ui.interfaces_table.setRowCount(len(self.interfaces))
            self.ui.interfaces_table.setColumnCount(7)
            self.ui.interfaces_table.setHorizontalHeaderLabels(["Interface", 
                                        "Admin state", 
                                        "Operational state", 
                                        "IPv4", 
                                        "IPv6",
                                        "Description"
                                        ""])
            self.ui.interfaces_table.horizontalHeader().setStretchLastSection(True)
            self.ui.interfaces_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            for row, (interface_element, interface_data) in enumerate(self.interfaces.items()):      
                admin_state = interface_data.get('admin_status', "N/A")
                oper_state = interface_data.get('oper_status', "N/A")
                description = interface_data.get('description', "N/A")
                ipv4_data, ipv6_data = utils.getFirstIPAddressesFromSubinterfaces(interface_data['subinterfaces'])

                # Flag: commited, uncommited, deleted
                bg_color = "white"
                tooltip = ""
                if ipv4_data:
                    bg_color = utils.getBgColorFromFlag(ipv4_data['flag'])
                    tooltip = utils.getTooltipFromFlag(ipv4_data['flag'])
                if ipv6_data:
                    bg_color = utils.getBgColorFromFlag(ipv6_data['flag'])
                    tooltip = utils.getTooltipFromFlag(ipv6_data['flag'])


                # Interface name
                interface_item = QTableWidgetItem(interface_element)
                interface_item.setFlags(interface_item.flags() ^ Qt.ItemIsEditable)  # Non-editable cells
                interface_item.setBackground(QBrush(QColor(bg_color)))
                interface_item.setToolTip(tooltip)
                self.ui.interfaces_table.setItem(row, 0, interface_item)
                # Administrative state
                admin_state_item = QTableWidgetItem(admin_state)
                admin_state_item.setFlags(admin_state_item.flags() ^ Qt.ItemIsEditable)
                admin_state_item.setBackground(QBrush(QColor(bg_color)))
                admin_state_item.setToolTip(tooltip)
                self.ui.interfaces_table.setItem(row, 1, admin_state_item)
                # Operational state
                oper_state_item = QTableWidgetItem(oper_state)
                oper_state_item.setFlags(oper_state_item.flags() ^ Qt.ItemIsEditable)
                oper_state_item.setBackground(QBrush(QColor(bg_color)))
                oper_state_item.setToolTip(tooltip)
                self.ui.interfaces_table.setItem(row, 2, oper_state_item)
                # IPv4 
                ipv4_item = QTableWidgetItem(str(ipv4_data['value']) if ipv4_data else "")
                ipv4_item.setFlags(ipv4_item.flags() ^ Qt.ItemIsEditable)
                ipv4_item.setBackground(QBrush(QColor(bg_color)))
                ipv4_item.setToolTip(tooltip)
                self.ui.interfaces_table.setItem(row, 3, ipv4_item)
                # IPv6
                ipv6_item = QTableWidgetItem(str(ipv6_data['value']) if ipv6_data else "")
                ipv6_item.setFlags(ipv6_item.flags() ^ Qt.ItemIsEditable)
                ipv6_item.setBackground(QBrush(QColor(bg_color)))
                ipv6_item.setToolTip(tooltip)
                self.ui.interfaces_table.setItem(row, 4, ipv6_item)
                # Description
                description_item = QTableWidgetItem(description)
                description_item.setFlags(oper_state_item.flags() ^ Qt.ItemIsEditable)
                description_item.setBackground(QBrush(QColor(bg_color)))
                description_item.setToolTip(tooltip)
                self.ui.interfaces_table.setItem(row, 5, description_item)
                # Edit button
                button_item = QPushButton("Edit")
                button_item.clicked.connect(self.showDialog)
                self.ui.interfaces_table.setCellWidget(row, 6, button_item)      
        else :
            self.ui.interfaces_table.setRowCount(1)
            self.ui.interfaces_table.setColumnCount(1)
            self.ui.interfaces_table.setItem(0, 0, QTableWidgetItem("No interfaces found!"))

    def showDialog(self):
        button = self.sender()

        row_index = self.ui.interfaces_table.indexAt(button.pos()) # Get the index of the row, in which was the button clicked
        interface_id = self.ui.interfaces_table.item(row_index.row(), 0).text() # Get the interface ID of the clicked row
            
        dialog = EditInterfaceDialog(self, self.device, interface_id)
        dialog.exec()

    def refreshDialog(self):
        self.ui.interfaces_table.clear()
        self.fillLayout()

    def showAddInterfaceDialog(self):
        try:
            AddInterfaceDialog(self.device).exec()
        finally:
            self.refreshDialog()

    def refreshInterfaces(self):
        """
        Refresh the device.interfaces list by retrieving new list from the device. Usefull for refreshing the dialog when waiting for the interface to come up.
        Cannot be launched when the device has pending changes, because the changes would be lost.
        """

        if self.device.has_pending_changes:
            QMessageBox.warning(self, "Warning", "The device has some pending changes. Please commit or discard them first.")
            return
        else:
            self.device.interfaces = self.device.getInterfaces()
            self.refreshDialog()
            self.device.updateCableLabelsText()


class EditInterfaceDialog(QDialog):
    def __init__(self, instance, device, interface_id):
        super().__init__()

        self.ui = Ui_edit_interface_dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(f"Edit interface: {interface_id}")

        self.instance = instance
        self.device = device
        self.interface_id = interface_id

        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                QSize(300, 400),
                QGuiApplication.primaryScreen().availableGeometry()
            )
        )

        # If the device is of type Firewall, show UI elements for managing security zones
        if device.__class__.__name__ == 'Firewall': # isInstance(item, Firewall), without the need to import class Firewall
            self.ui.security_zone_frame.setVisible(True)
            self.ui.security_zone_combobox.addItems(device.security_zones)
            self.ui.security_zone_combobox.addItems(" ")
            self.ui.security_zone_combobox.setCurrentText(device.interfaces[interface_id].get('security_zone', " "))
            self.ui.change_security_zone_button.clicked.connect(lambda: self.changeSecurityZone(self.ui.security_zone_combobox.currentText()))
        else:
            self.ui.security_zone_frame.setVisible(False)

        self.fillLayout()

    def fillLayout(self):
        self.ui.add_subinterface_button.clicked.connect(lambda _, index=None : self.showDialog(index))

        # Get subinterfaces, create a layout for each subinterface containg: Header, Table
        self.subinterfaces = self.device.interfaces[self.interface_id]['subinterfaces']
        for subinterface_index, subinterface_data in self.subinterfaces.items():
            # Groupbox for each subinterface
            subinterface_groupbox = QGroupBox()
            subinterface_groupbox.setTitle(f"Subinterface: {subinterface_index}")
            subinterface_groupbox_layout = QVBoxLayout()
            
            # Sublayout for the buttons at the top ("Add IP address")
            subinterface_top_layout = QHBoxLayout()
            add_ip_button = QPushButton("Add IP address")
            add_ip_button.clicked.connect(lambda _, index=subinterface_index : self.showDialog(index))
            subinterface_top_layout.addWidget(add_ip_button)
            subinterface_top_layout.addStretch()
            subinterface_groupbox_layout.addLayout(subinterface_top_layout)

            # Table for each subinterface
            subinterface_groupbox_layout.addWidget(self.createSubinterfaceTable(subinterface_index, subinterface_data))
            subinterface_groupbox.setLayout(subinterface_groupbox_layout)
            self.ui.tables_layout.addWidget(subinterface_groupbox)

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
                bg_color = utils.getBgColorFromFlag(ipv4_data['flag'])

            # IPv4 address
            ip_item = QTableWidgetItem(f"{ipv4_data['value'].ip}/{ipv4_data['value'].network.prefixlen}")
            ip_item.setBackground(QBrush(QColor(bg_color)))
            subinterface_table.setItem(row, 0, ip_item)
            # Edit button
            edit_ip_button_item = QPushButton("Edit")
            edit_ip_button_item.clicked.connect(lambda _, index=subinterface_index, ip = ipv4_data['value'] : self.showDialog(index, ip)) # _ = unused argument
            if ipv4_data['flag'] == "deleted": # Dont allow to edit deleted IP addresses - prompt the user to create a new one instead
                edit_ip_button_item.setEnabled(False)
                edit_ip_button_item.setToolTip("Cannot edit deleted IP address. Create a new one instead.")
            else:
                edit_ip_button_item.setEnabled(True)
            subinterface_table.setCellWidget(row, 1, edit_ip_button_item)
            # Delete button
            delete_ip_button_item = QPushButton("Delete")
            delete_ip_button_item.clicked.connect(lambda _, index=subinterface_index, ip = ipv4_data['value'] : self.deleteIP(index, ip))
            if ipv4_data['flag'] == "deleted": # Dont allow to delete already deleted IP addresses - prompt the user to create a new one instead
                delete_ip_button_item.setEnabled(False)
                delete_ip_button_item.setToolTip("Cannot delete an already deleted IP address. Create a new one instead.")
            else:
                delete_ip_button_item.setEnabled(True)
            subinterface_table.setCellWidget(row, 2, delete_ip_button_item)
            
            row += 1
        
        for ipv6_data in subinterface_data['ipv6_data']:
            # Flag: commited, uncommited, deleted
            bg_color = "white"
            if ipv6_data:
                bg_color = utils.getBgColorFromFlag(ipv6_data['flag'])

            # IPv6 address
            ip_item = QTableWidgetItem(f"{ipv6_data['value'].ip}/{ipv6_data['value'].network.prefixlen}")
            ip_item.setBackground(QBrush(QColor(bg_color)))
            subinterface_table.setItem(row, 0, ip_item)
            # Edit button
            edit_ip_button_item = QPushButton("Edit")
            edit_ip_button_item.clicked.connect(lambda _, index=subinterface_index, ip = ipv6_data['value'] : self.showDialog(index, ip)) # _ = unused argument
            if ipv6_data['flag'] == "deleted": # Dont allow to edit deleted IP addresses - prompt the user to create a new one instead
                edit_ip_button_item.setEnabled(False)
                edit_ip_button_item.setToolTip("Cannot edit deleted IP address. Create a new one instead.")
            else:
                edit_ip_button_item.setEnabled(True)
            subinterface_table.setCellWidget(row, 1, edit_ip_button_item)
            # Delete button
            delete_ip_button_item = QPushButton("Delete")
            delete_ip_button_item.clicked.connect(lambda _, index=subinterface_index, ip = ipv6_data['value'] : self.deleteIP(index, ip))
            if ipv6_data['flag'] == "deleted": # Dont allow to delete already deleted IP addresses - prompt the user to create a new one instead
                delete_ip_button_item.setEnabled(False)
                delete_ip_button_item.setToolTip("Cannot edit deleted IP address. Create a new one instead.")
            else:
                delete_ip_button_item.setEnabled(True)
            subinterface_table.setCellWidget(row, 2, delete_ip_button_item)

            row += 1
        return subinterface_table
    
    def deleteIP(self, subinterface_index, old_ip):
        self.device.deleteInterfaceIP(self.interface_id, subinterface_index, old_ip)
        self.refreshDialog()

    def closeEvent(self, event):
        """ Refresh the parent dialog when this dialog is closed. """
        self.instance.refreshDialog()
        super().closeEvent(event)

    def changeSecurityZone(self, security_zone):
        if self.device.interfaces[self.interface_id].get("security_zone", None) is not None: # if the interface already has a security zone assigned
            result = self.device.configureInterfacesSecurityZone(self.interface_id, self.device.interfaces[self.interface_id]["security_zone"], remove_interface_from_zone=True) # remove the interface from the old zone
        result = self.device.configureInterfacesSecurityZone(self.interface_id, security_zone)

        if result == True:
            QMessageBox.information(self, "Information", f"Security zone for interface {self.interface_id} has been changed to {security_zone}.")
        elif result == False:
            QMessageBox.warning(self, "Warning", f"Failed to change the security zone for interface {self.interface_id}.")
        

    def showDialog(self, subinterface_index, ip = None):       
        self.editSubinterfaceDialog = EditSubinterfaceDialog(self, self.device, self.interface_id, subinterface_index, ip)
        self.editSubinterfaceDialog.exec()

    def refreshDialog(self):
        utils.clearLayout(self.ui.tables_layout)
        self.fillLayout()


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
                delete_success = self.device.deleteInterfaceIP(self.interface_id, self.subinterface_id, self.old_ip)
                if delete_success: # Dont set new IP if the old one was not deleted
                    self.device.setInterfaceIP(self.interface_id, self.subinterface_id, self.new_ip)
                self.editInterfaceDialog_instance.refreshDialog()
            elif self.old_ip and self.old_ip == self.new_ip:
                # If old_ip was entered and the new_ip is the same, do nothing
                QMessageBox.information(self, "Information", "No changes were made.")
            elif not self.old_ip:
                # If old_ip was not entered, set new ip address
                self.device.setInterfaceIP(self.interface_id, self.subinterface_id, self.new_ip)
                self.editInterfaceDialog_instance.refreshDialog()
        else:
            self.device.setInterfaceIP(self.interface_id, self.subinterface_input.text(), self.new_ip)
            self.editInterfaceDialog_instance.refreshDialog()
        self.accept()


class AddInterfaceDialog(QDialog):
    def __init__(self, device):
        super().__init__()

        self.device = device

        self.ui = Ui_add_interface_dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Add new interface")
        self.ui.ok_cancel_button_box.button(QDialogButtonBox.Ok).clicked.connect(self.confirmAdd)
        self.ui.ok_cancel_button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        self.ui.interface_type_combobox.currentIndexChanged.connect(self.changePlaceholderInterfaceName)

        if self.device.device_parameters['device_params'] == "junos":
            QMessageBox.information(self, "Information", "Juniper devices support only one loopback interface - lo0, which may already be present on the device. Procced with caution.")

        self.ui.interface_type_combobox.addItems(["Loopback"])

    @Slot()
    def changePlaceholderInterfaceName(self):
        """
        Give a hint to the user about the interface name format based on the selected interface type.
        """

        interface_type = self.ui.interface_type_combobox.currentText()
        if interface_type == "Loopback":
            if self.device.device_parameters['device_params'] == "junos":
                self.ui.interface_name_input.setPlaceholderText("lo0")
            elif self.device.device_parameters['device_params'] == "iosxe":
                self.ui.interface_name_input.setPlaceholderText("Loopback0")
        else:
            self.ui.interface_name_input.setPlaceholderText("-")

    def confirmAdd(self):
        interface_name = self.ui.interface_name_input.text()
        interface_type = self.ui.interface_type_combobox.currentText()

        if not interface_type == "Loopback":
            QMessageBox.warning(self, "Warning", "Select a valid interface type.")
            return
        
        if self.device.device_parameters['device_params'] == "junos":
            if self.checkValidInterfaceName(interface_name, "lo"):
                self.device.addInterface(interface_name, interface_type)
                self.accept()
            else:
                QMessageBox.warning(self, "Warning", "Invalid interface name!")
                return
        if self.device.device_parameters['device_params'] == "iosxe":
            if self.checkValidInterfaceName(interface_name, "Loopback"):
                self.device.addInterface(interface_name, interface_type)
                self.accept()
            else:
                QMessageBox.warning(self, "Warning", "Invalid interface name!")
                return

    def checkValidInterfaceName(self, name, checked_name):
        if name.startswith(checked_name):
            return True
        