# ---------- IMPORTS: ----------
# Standard library
import ipaddress
from lxml import etree as ET
from ncclient import operations
from natsort import natsorted

# Custom modules
import utils
from yang.filters import GetFilter, EditconfigFilter
from definitions import INTERFACES_YANG_DIR, CONFIGURATION_TARGET_DATASTORE

# Qt
from PySide6.QtWidgets import (
    QDialog, 
    QVBoxLayout,
    QHBoxLayout, 
    QLabel, 
    QPushButton,
    QDialogButtonBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QStyle,
    QGroupBox,
    QMessageBox,)
from PySide6.QtCore import Qt, QSize, Slot
from PySide6.QtGui import QGuiApplication, QBrush, QColor, QIcon, QPixmap

# QtCreator
from ui.ui_interfacesdialog import Ui_Interfaces
from ui.ui_addinterfacedialog import Ui_add_interface_dialog
from ui.ui_editinterfacedialog import Ui_edit_interface_dialog



# ---------- OPERATIONS: ----------
def getInterfacesWithNetconf(device) -> tuple:
    """
    Retrieve interface information from a network device using NETCONF.
    This function fetches interface details, including administrative and operational
    statuses, descriptions, subinterface data, and VLAN information (if applicable),
    from a network device using the NETCONF protocol.
    Args:
        device (object): A device object that contains connection details and device-specific
                         parameters. The object must have a `device_parameters` dictionary
                         with a 'device_params' key and a `mngr` attribute for NETCONF operations.
    Returns:
        tuple: A tuple containing:
            - interfaces (dict): A dictionary where each key is an interface name, and the value
              is another dictionary with the following keys: (example in the /doc folder)
                - 'admin_status' (str or None): The administrative status of the interface.
                - 'oper_status' (str or None): The operational status of the interface.
                - 'description' (str or None): The description of the interface.
                - 'flag' (str): A flag indicating the state of the interface (e.g., "commited").
                - 'subinterfaces' (dict): A dictionary of subinterfaces, where each key is a
                  subinterface index, and the value is a dictionary containing:
                    - 'ipv4_data' (dict): IPv4-related data for the subinterface.
                    - 'ipv6_data' (dict): IPv6-related data for the subinterface.
                - 'vlan_data' (dict, optional): VLAN-related data for the interface, if the
                  device supports VLAN capabilities.
            - rpc_reply (object): The raw RPC reply object returned by the NETCONF operation.
    Notes:
        - This function handles duplicate `<interfaces>` tags returned by certain devices
          (e.g., Juniper vRouter 24.2R1.S2) by skipping duplicate entries.
        - The function assumes the presence of helper functions `extractIPDataFromSubinterface`
          and `extractVlanDataFromInterface` for extracting subinterface and VLAN data, respectively.
        - The `device` object should have an `is_vlan_capable` attribute to indicate VLAN support.
    Raises:
        Any exceptions raised by the NETCONF manager or helper functions will propagate.
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
 
            interfaces[name] = {
                'admin_status': admin_status,
                'oper_status': oper_status,
                'description': description,
                'flag': "commited"
            }
            
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
            interfaces[name]["subinterfaces"] = subinterfaces

            # if the device has VLAN capabilites
            if hasattr(device, "is_vlan_capable") and device.is_vlan_capable:
                vlan_data = extractVlanDataFromInterface(interface_element)
                interfaces[name]["vlan_data"] = vlan_data
            
            sorted_interfaces = {key: interfaces[key] for key in natsorted(interfaces)}
    return(sorted_interfaces, rpc_reply)

def extractIPDataFromSubinterface(subinterface_element, version="ipv4") -> list[dict]:
    """
    Extracts IP address data from a subinterface XML element.
    Args:
        subinterface_element (xml.etree.ElementTree.Element): 
            The XML element representing the subinterface from which IP data will be extracted.
        version (str, optional): 
            The IP version to extract data for. Defaults to "ipv4". 
            Acceptable values are "ipv4" or "ipv6".
    Returns:
        list[dict]: 
            A list of dictionaries containing extracted IP data. Each dictionary has:
            - 'value': An ipaddress.IPv4Interface or ipaddress.IPv6Interface object representing the IP address and prefix length.
            - 'flag': A string indicating the status of the IP data, set to 'commited'. Meant to allow setting the flag to "uncommited", when manipulating with the data.
    """

    ipvX_object_tag = (f".//{version}/addresses/address")
    ipvX_objects = subinterface_element.findall(ipvX_object_tag)

    ipvX_data = []
    for ipvX_object in ipvX_objects:
        ipvX_address = ipvX_object.find('state/ip')
        ipvX_prefix_length = ipvX_object.find('state/prefix-length')
        if ipvX_address is not None and ipvX_prefix_length is not None: 
            ip_interface = ipaddress.IPv4Interface(f"{ipvX_address.text}/{ipvX_prefix_length.text}") if version == "ipv4" else ipaddress.IPv6Interface(f"{ipvX_address.text}/{ipvX_prefix_length.text}")
            ipvX_data.append({'value': ip_interface, 'flag': 'commited'})
    return(ipvX_data)

def extractVlanDataFromInterface(interface_element) -> dict:
    """
    Extracts VLAN data from an interface element.
    This function parses an XML element representing a network interface and extracts
    VLAN configuration details, such as the switchport mode (access or trunk) and the
    associated VLAN(s).
    Args:
        interface_element (xml.etree.ElementTree.Element): The XML element representing
            the network interface.
    Returns:
        dict: A dictionary containing VLAN data with the following keys:
            - "port_mode" (str or None): The (switch)port mode of the interface
              ("access", "trunk", "router-port" or None if not specified).
            - "vlan" (str, list, or None): The VLAN(s) associated with the interface.
              For "access" mode, this is a single VLAN ID as a string. For "trunk" mode,
              this is a list of VLAN IDs as strings. If no VLAN is specified, this is None.
    """

    vlan_data = {}

    # Check if the interface is a routed port (not a switchport)
    switchport_state_element = interface_element.find('../ethernet/config/switchport')
    if switchport_state_element is not None:
        switchport_state = switchport_state_element.text
        if switchport_state is not None and switchport_state == "false":
            vlan_data["port_mode"] = "routed-port"
        else: # if not a routed port, check for VLAN configuration
            vlan_element = interface_element.find('../ethernet/switched-vlan/config')
            if vlan_element is not None:
                interface_mode = vlan_element.find('interface-mode')
                if interface_mode is not None:
                    vlan_data["port_mode"] = interface_mode.text.lower()
                    if vlan_data["port_mode"] == "access":
                        vlan = vlan_element.find('access-vlan')
                        vlan_data["vlan"] = vlan.text if vlan is not None else None
                    elif vlan_data["port_mode"] == "trunk":
                        vlans = vlan_element.findall('trunk-vlans')
                        vlan_data["vlan"] = [vlan.text for vlan in vlans] if vlans is not None else None
            else:
                vlan_data["port_mode"] = None
                vlan_data["vlan"] = None

    return vlan_data

def deleteIpWithNetconf(device, interface_element, subinterface_index, old_ip) -> tuple:
    """
    Deletes an IP address from a specified interface on a network device using NETCONF.
    Args:
        device: The network device object that provides the NETCONF manager.
        interface_element: The interface element identifier where the IP address is to be deleted.
        subinterface_index: The index of the subinterface from which the IP address is to be removed.
        old_ip: The IP address to be deleted.
    Returns:
        tuple: A tuple containing the RPC reply and the filter used for the operation if successful.
        None: If an exception occurs during the operation.
    """

    try:
        # FILTER
        filter = OpenconfigInterfaces_Editconfig_EditIpaddress_Filter(interface_element, subinterface_index, old_ip, delete_ip=True)

        # RPC
        rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
        return(rpc_reply, filter)
    except operations.RPCError as e:
        utils.printGeneral(f"Failed to delete IP on device {device.id}: {e}")
        return (rpc_reply, filter)
    except Exception as e:
        utils.printGeneral(f"Failed to set IP on device {device.id}: {e}")
        return None

def setIpWithNetconf(device, interface_element, subinterface_index, new_ip) -> tuple:
    """
    Sets a new IP address on a specified network interface using NETCONF.
    Args:
        device: The network device object that provides the NETCONF manager.
        interface_element: The identifier or configuration element of the interface to be updated.
        subinterface_index: The index of the subinterface to be updated.
        new_ip: The new IP address to be assigned to the interface.
    Returns:
        tuple: A tuple containing the RPC reply and the filter used for the operation if successful.
        None: If an exception occurs during the operation.
    """

    try:
        # FILTER
        filter = OpenconfigInterfaces_Editconfig_EditIpaddress_Filter(interface_element, subinterface_index, new_ip)
        # RPC
        rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
        return(rpc_reply, filter)
    except operations.RPCError as e:
        utils.printGeneral(f"Failed to set IP on device {device.id}: {e}")
        return (rpc_reply, filter)
    except Exception as e:
        utils.printGeneral(f"Failed to set IP on device {device.id}: {e}")
        return None

def addInterfaceWithNetconf(device, interface_id, interface_type) -> tuple:
    """
    Adds a network interface to a device using NETCONF.
    This function constructs a filter for adding an interface and sends an
    edit-config RPC request to the device's NETCONF manager. 
    Args:
        device (object): The device object representing the target device.
                         It must have a `mngr` attribute for NETCONF operations
                         and an `id` attribute for identification.
        interface_id (str): The identifier of the interface to be added.
        interface_type (str): The type of the interface to be added.
    Returns:
        tuple: A tuple containing the RPC reply and the filter used for the operation if successful.
        None: If an exception occurs during the operation.
    """

    try:
        # FILTER
        filter = OpenconfigInterfaces_Editconfig_AddInterface_Filter(interface_id, interface_type)
        
        # RPC
        rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
        return(rpc_reply, filter)
    except operations.RPCError as e:
        utils.printGeneral(f"Failed to add interface on device {device.id}: {e}")
        return (rpc_reply)
    except Exception as e:
        utils.printGeneral(f"Failed to add interface on device {device.id}: {e}")
        return None

def editDescriptionWithNetconf(device, interface_element, description) -> tuple:
    """
    Edits the description of a network interface on a device using NETCONF.
    Args:
        device: The network device object that supports NETCONF operations.
        interface_element: The specific interface element to be updated.
        description: The new description to set for the interface.
    Returns:
        tuple: A tuple containing the RPC reply and the filter used for the operation if successful.
        None: If an exception occurs during the operation.
    """

    try:
        # FILTER
        filter = OpenconfigInterfaces_Editconfig_EditDescription_Filter(interface_element, description)
        # RPC
        rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
        return(rpc_reply, filter)
    except operations.RPCError as e:
        utils.printGeneral(f"Failed to to edit interface description on device {device.id}: {e}")
        return (rpc_reply, filter)
    except Exception as e:
        utils.printGeneral(f"Failed to to edit interface description on device {device.id}: {e}")
        return None


# ---------- FILTERS: ----------
class OpenconfigInterfaces_Get_GetAllInterfaces_Filter(GetFilter):
    def __init__(self) -> None:
        self.filter_xml = ET.parse(INTERFACES_YANG_DIR + "openconfig-interfaces_get_get-all-interfaces.xml")


class OpenconfigInterfaces_Editconfig_EditIpaddress_Filter(EditconfigFilter):
    def __init__(self, interface, subinterface_index, ip, delete_ip=False) -> None:
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
        elif "vlan" in self.interface.lower():
            self.interface_type = "ianaift:l3ipvlan" # L3 VLAN
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

    def createIPV4Filter(self) -> None:
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

    def createIPV6Filter(self) -> None:
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
    def __init__(self, interface_id, interface_type) -> None:
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
        elif interface_type == "Vlan":
            interface_type_element.text = "ianaift:l3ipvlan"


class OpenconfigInterfaces_Editconfig_EditDescription_Filter(EditconfigFilter):
    def __init__(self, interface_element, description) -> None:
        self.filter_xml = ET.parse(INTERFACES_YANG_DIR + "openconfig-interfaces_editconfig_edit_description.xml")
        self.namespaces = {'ns': 'http://openconfig.net/yang/interfaces'}

        self.filter_xml.find(".//ns:name", self.namespaces).text = interface_element
        self.filter_xml.find(".//ns:description", self.namespaces).text = description


# ---------- QT: ----------
class DeviceInterfacesDialog(QDialog):
    """
    DeviceInterfacesDialog is a dialog window for managing and displaying the interfaces of a network device.
    This class provides a graphical interface for viewing, and editing the interfaces of a device. 
    It displays the interfaces in a table format, showing details such as administrative state, operational state, 
    IPv4 and IPv6 addresses, and descriptions. Users can also add new interfaces or edit existing ones.
    Methods:
        __init__(device):
            Initializes the dialog with the given device and sets up the user interface.
        fillLayout():
            Populates the table with the device's interfaces and their details.
        showDialog():
            Opens a dialog for editing the selected interface.
        refreshDialog():
            Clears and repopulates the interface table.
        showAddInterfaceDialog():
            Opens a dialog for adding a new interface and refreshes the table afterward.
        refreshInterfaces():
            Refreshes the device's interface list by retrieving the latest data from the device.
    """

    def __init__(self, device) -> QDialog:
        super().__init__()

        self.device = device
        self.ui = Ui_Interfaces()
        self.ui.setupUi(self)

        gnc_icon = QPixmap("graphics/icons/gnc.png")
        self.setWindowIcon(QIcon(gnc_icon))
        self.setWindowTitle("Device Interfaces")
        self.ui.close_button_box.button(QDialogButtonBox.Close).clicked.connect(self.close)
        self.ui.add_interface_button.clicked.connect(self.showAddInterfaceDialog)
        self.ui.refresh_button.clicked.connect(self.refreshInterfaces)
        self.fillLayout()

    def fillLayout(self) -> None:
        """Fills the layout of the dialog with the interfaces of the device."""

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
                                        "Description",
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
                bg_color = utils.getBgColorFromFlag(interface_data['flag'])
                tooltip = utils.getTooltipFromFlag(interface_data['flag'])

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

    def showDialog(self) -> None:
        """Opens a dialog for editing the selected interface."""

        button = self.sender()

        row_index = self.ui.interfaces_table.indexAt(button.pos()) # Get the index of the row, in which was the button clicked
        interface_id = self.ui.interfaces_table.item(row_index.row(), 0).text() # Get the interface ID of the clicked row
            
        dialog = EditInterfaceDialog(self, self.device, interface_id)
        dialog.exec()

    def refreshDialog(self) -> None:
        """Clears and repopulates the interface table."""

        self.ui.interfaces_table.clear()
        self.fillLayout()

    def showAddInterfaceDialog(self) -> None:
        """Opens a dialog for adding a new interface and refreshes the table afterward."""

        try:
            AddInterfaceDialog(self.device).exec()
        finally:
            self.refreshDialog()

    def refreshInterfaces(self) -> None:
        """
        Refreshes the device.interfaces list by retrieving new list from the device. Usefull for refreshing the dialog when waiting for the interface to come up.
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
    """
    EditInterfaceDialog is dialog for editing network interface configurations. 
    It provides functionality to manage subinterfaces, IP addresses, security zones, and descriptions.
    Methods:
        __init__(instance, device, interface_id):
            Initializes the dialog with the given instance, device, and interface ID.
        fillLayout():
            Populates the dialog layout with subinterface group boxes and tables.
        createSubinterfaceTable(subinterface_index, subinterface_data):
            Creates a QTableWidget for displaying IP addresses of a subinterface.
        deleteIP(subinterface_index, old_ip):
            Deletes an IP address from a subinterface and refreshes the dialog.
        closeEvent(event):
            Refreshes the parent dialog when this dialog is closed.
        changeSecurityZone(security_zone):
            Changes the security zone of the interface.
        changeDescription(description):
            Updates the description of the interface.
        showDialog(subinterface_index, ip=None):
            Opens a dialog for editing or adding a subinterface or IP address.
        refreshDialog():
            Clears and repopulates the layout to reflect updated data.
        """

    def __init__(self, instance, device, interface_id) -> QDialog:
        super().__init__()

        self.ui = Ui_edit_interface_dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(f"Edit interface: {interface_id}")
        gnc_icon = QPixmap("graphics/icons/gnc.png")
        self.setWindowIcon(QIcon(gnc_icon))

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

        # If the device has capabilites for configuring security zones, show UI elements for it
        if hasattr(device, "is_security_zone_capable") and device.is_security_zone_capable:
            self.ui.security_zone_frame.setVisible(True)
            self.ui.security_zone_combobox.addItems(device.security_zones)
            self.ui.security_zone_combobox.addItems(" ")
            self.ui.security_zone_combobox.setCurrentText(device.interfaces[interface_id].get('security_zone', " "))
            self.ui.change_security_zone_button.clicked.connect(lambda: self.changeSecurityZone(self.ui.security_zone_combobox.currentText()))
        else:
            self.ui.security_zone_frame.setVisible(False)

        # Connect buttons
        self.ui.add_subinterface_button.clicked.connect(lambda _, index=None : self.showDialog(index))
        self.ui.change_description_button.clicked.connect(lambda: self.changeDescription(self.ui.description_input.text()))
        self.ui.close_button_box.button(QDialogButtonBox.Close).clicked.connect(self.close)

        self.fillLayout()

    def fillLayout(self) -> None:
        """Populates the dialog layout with subinterface group boxes and tables."""

        # Get subinterfaces, create a layout for each subinterface containg: Header, Table
        self.subinterfaces = self.device.interfaces[self.interface_id]['subinterfaces']
        self.ui.description_input.setText(self.device.interfaces[self.interface_id].get('description', ""))
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

    def createSubinterfaceTable(self, subinterface_index, subinterface_data) -> None:
        """Creates a QTableWidget for displaying IP addresses of a subinterface."""

        # Create the table, set basic properties
        subinterface_table = QTableWidget()
        subinterface_table.setColumnCount(3)
        subinterface_table.setRowCount(len(subinterface_data['ipv4_data']) + len(subinterface_data['ipv6_data']))
        subinterface_table.setHorizontalHeaderLabels(["Address", "", ""])
        subinterface_table.horizontalHeader().setStretchLastSection(True)
        subinterface_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        row = 0
        for ipv4_data in subinterface_data['ipv4_data']:
            bg_color = "white"
            if ipv4_data:
                bg_color = utils.getBgColorFromFlag(ipv4_data['flag']) # Flag: commited, uncommited, deleted

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
            bg_color = "white"
            if ipv6_data:
                bg_color = utils.getBgColorFromFlag(ipv6_data['flag']) # Flag: commited, uncommited, deleted

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
    
    def deleteIP(self, subinterface_index, old_ip) -> None:
        """Deletes an IP address from a subinterface and refreshes the dialog."""
        
        self.device.deleteInterfaceIP(self.interface_id, subinterface_index, old_ip)
        self.refreshDialog()

    def closeEvent(self, event) -> None:
        """ Refresh the parent dialog when this dialog is closed. """
        
        self.instance.refreshDialog()
        super().closeEvent(event)

    def changeSecurityZone(self, security_zone) -> None:
        """Changes the security zone of the interface. Used for Juniper SRX."""

        if self.device.interfaces[self.interface_id].get("security_zone", None) is not None: # if the interface already has a security zone assigned, remove it first before assigning a new onw
            result = self.device.configureInterfacesSecurityZone(self.interface_id, self.device.interfaces[self.interface_id]["security_zone"], remove_interface_from_zone=True) # remove the interface from the old zone
        result = self.device.configureInterfacesSecurityZone(self.interface_id, security_zone)

        if result == True:
            QMessageBox.information(self, "Information", f"Security zone for interface {self.interface_id} has been changed to {security_zone}.")
        elif result == False:
            QMessageBox.warning(self, "Warning", f"Failed to change the security zone for interface {self.interface_id}.")  

    def changeDescription(self, description) -> None:
        """Updates the description of the interface."""

        old_description = self.device.interfaces[self.interface_id].get("description", None)

        if description == "":
            QMessageBox.warning(self, "Warning", "Description cannot be empty.")
            return

        if old_description is not None and old_description == description:
            QMessageBox.information(self, "Information", "No changes were made.")
            return
        
        result = self.device.configureInterfaceDescription(self.interface_id, description)
        
        if result == True:
            QMessageBox.information(self, "Information", f"Description for interface {self.interface_id} has been changed to {description}.")
        elif result == False:
            QMessageBox.warning(self, "Warning", f"Failed to change the description for interface {self.interface_id}.")

    def showDialog(self, subinterface_index, ip = None) -> None:
        """Opens a dialog for editing or adding a subinterface or IP address."""

        self.editSubinterfaceDialog = EditSubinterfaceDialog(self, self.device, self.interface_id, subinterface_index, ip)
        self.editSubinterfaceDialog.exec()

    def refreshDialog(self) -> None:
        """Clears and repopulates the layout to reflect updated data."""

        utils.clearLayout(self.ui.tables_layout)
        self.fillLayout()


class EditSubinterfaceDialog(QDialog):
    """
    A dialog for editing or adding a subinterface to a network device.
    This dialog allows the user to either edit an existing subinterface or create a new one.
    It provides fields for specifying the subinterface ID and its associated IP address.
    Methods:
        confirmEdit():
            Handles the confirmation of the edit or creation of the subinterface.
            Validates the IP address, updates the device configuration, and refreshes the parent dialog.
    """

    def __init__(self, editInterfaceDialog_instance, device, interface, subinterface_id, ip = None) -> QDialog:
        super().__init__()

        self.editInterfaceDialog_instance = editInterfaceDialog_instance
        self.device = device
        self.interface_id = interface
        self.subinterface_id = subinterface_id
        self.old_ip = ip if ip is not None else None

        gnc_icon = QPixmap("graphics/icons/gnc.png")
        self.setWindowIcon(QIcon(gnc_icon))

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

    def confirmEdit(self) -> None:
        """Handles the confirmation of the edit or creation of the subinterface."""

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
    """
    AddInterfaceDialog is a dialog window for adding a new network interface to a device.
    This class provides a user interface for selecting an interface type (currently, only loopback interfaces are supported),
    specifying an interface name, and validating the input based on the device's parameters. 
    It supports devices with "junos" and "iosxe" parameters and ensures
    that the interface name adheres to the expected format for the selected type.
    Methods:
        changePlaceholderInterfaceName():
            Gives a hint to the user about the interface name format based on the selected interface type.
        confirmAdd():
            Handles the confirmation of the addition of a new interface.
            Validates the input, adds the interface to the device configuration, and closes the dialog.
        checkValidInterfaceName(name, checked_name):
            Checks if the interface name adheres to the expected format for the selected type.
    """
    
    def __init__(self, device) -> QDialog:
        super().__init__()

        self.device = device

        self.ui = Ui_add_interface_dialog()
        self.ui.setupUi(self)

        gnc_icon = QPixmap("graphics/icons/gnc.png")
        self.setWindowIcon(QIcon(gnc_icon))
        self.setWindowTitle("Add new interface")
        self.ui.ok_cancel_button_box.button(QDialogButtonBox.Ok).clicked.connect(self.confirmAdd)
        self.ui.ok_cancel_button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        self.ui.interface_type_combobox.currentIndexChanged.connect(self.changePlaceholderInterfaceName)

        if self.device.device_parameters['device_params'] == "junos":
            QMessageBox.information(self, "Information", "Juniper devices support only one loopback interface - lo0, which may already be present on the device. Procced with caution.")

        self.ui.interface_type_combobox.addItems(["Loopback", "Vlan"])

    @Slot()
    def changePlaceholderInterfaceName(self):
        """Give a hint to the user about the interface name format based on the selected interface type."""

        interface_type = self.ui.interface_type_combobox.currentText()
        if interface_type == "Loopback":
            if self.device.device_parameters['device_params'] == "junos":
                self.ui.interface_name_input.setPlaceholderText("lo0")
            elif self.device.device_parameters['device_params'] == "iosxe":
                self.ui.interface_name_input.setPlaceholderText("Loopback0")
        elif interface_type == "Vlan":
            if self.device.device_parameters['device_params'] == "iosxe":
                self.ui.interface_name_input.setPlaceholderText("Vlan1")
            else:
                QMessageBox.warning(self, "Warning", "Vlan interfaces are not supported on this device.")
                self.ui.interface_name_input.setPlaceholderText("-")
        else:
            self.ui.interface_name_input.setPlaceholderText("-")

    def confirmAdd(self) -> None:
        """Handles the confirmation of the addition of a new interface."""

        interface_name = self.ui.interface_name_input.text()
        interface_type = self.ui.interface_type_combobox.currentText()

        if interface_type == "Loopback":
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
        elif interface_type == "Vlan":
            if self.device.device_parameters['device_params'] == "iosxe":
                if self.checkValidInterfaceName(interface_name, "Vlan"):
                    self.device.addInterface(interface_name, interface_type)
                    self.accept()
                else:
                    QMessageBox.warning(self, "Warning", "Invalid interface name!")
                    return
            else:
                QMessageBox.warning(self, "Warning", "Vlan interfaces are not supported on this device.")
                return

    def checkValidInterfaceName(self, name, checked_name):
        """Checks if the interface name adheres to the expected format for the selected type."""
        
        if name.startswith(checked_name):
            return True