# ---------- IMPORTS: ----------
# Standard library 
import os
from lxml import etree as ET
import copy

# Custom modules
import utils
from definitions import ROOT_DIR, CONFIGURATION_TARGET_DATASTORE, VLAN_YANG_DIR
from yang.filters import EditconfigFilter, GetFilter

# Qt
from PySide6.QtWidgets import (
    QDialog, 
    QVBoxLayout,
    QHBoxLayout,
    QWidget, 
    QLabel, 
    QPushButton,
    QComboBox,
    QDialogButtonBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QMessageBox,)
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPixmap

# QtCreator
from ui.ui_editvlansdialog import Ui_edit_vlans_dialog

# ---------- OPERATIONS: ----------
def getVlansWithNetconf(device) -> dict:
    """
    Retrieve VLANs from a network device using NETCONF.
    This function fetches VLANs from a network device based on its
    device parameters. Currently, it supports devices with 'iosxe' parameters.
    For 'junos' devices, the functionality is not implemented.
    Args:
        device: An object representing the network device. It must have a 
                `device_parameters` attribute containing a dictionary with 
                the key 'device_params' to specify the device type.
    Returns:
        dict: A dictionary containing VLAN information where the keys are VLAN IDs
              and the values are dictionaries with VLAN details (name).
        rpc_reply: The raw RPC reply received from the device.
    Raises:
        NotImplementedError: If the device type is 'junos', as this functionality
                             is not implemented for Junos devices.
    """

    if device.device_parameters['device_params'] == 'iosxe':
        # FILTER
        filter = CiscoIOSXEVlan_Get_GetVlanList_Filter()

        # RPC
        rpc_reply = device.mngr.get(str(filter))
        rpc_reply_etree = utils.convertToEtree(rpc_reply, device.device_parameters['device_params'])

        # PARSE
        vlans = {}
        vlans_elements = rpc_reply_etree.findall('.//vlan-list')

        for vlan_element in vlans_elements:
            vlan_id = vlan_element.find('id')
            name = vlan_element.find('name')
            vlans[vlan_id.text] = {
                'name': name.text if name is not None else '',
            }

        return(vlans, rpc_reply)

    if device.device_parameters['device_params'] == 'junos':
        raise NotImplementedError("Junos VLANs not implemented")
    
def deleteInterfaceVlanWithNetconf(device, interfaces: dict) -> tuple:
    """
    Deletes VLAN configuration from network device interfaces using NETCONF.
    This function supports devices with 'iosxe' device parameters. For 'junos' 
    devices, the functionality is not implemented and raises a NotImplementedError.
    Args:
        device: An object representing the network device, which includes 
                device parameters and a NETCONF manager instance.
        interfaces (dict): A dictionary containing interface configuration details 
                           to identify which VLANs to delete.
    Returns:
        tuple: A tuple containing:
            - rpc_reply: The NETCONF RPC reply from the device after attempting 
                         to delete the VLAN configuration.
            - filter: The filter object used for the NETCONF edit-config operation.
    Raises:
        NotImplementedError: If the device parameters indicate a 'junos' device.
    """
    
    if device.device_parameters['device_params'] == 'iosxe':
        # FILTER
        filter = OpenconfigInterfaces_EditConfig_ConfigureInterfaceVlan_Filter(interfaces, delete=True)
        print(filter)
        # RPC
        rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
        #rpc_reply = ""
        return(rpc_reply, filter)

    if device.device_parameters['device_params'] == 'junos':
        raise NotImplementedError("Junos VLANs not implemented")
    
def setInterfaceVlanWithNetconf(device, interfaces: dict) -> tuple:
    """
    Configures VLAN settings on network device interfaces using NETCONF.
    This function applies VLAN configurations to the specified interfaces
    on a network device. It supports devices running IOS-XE and raises a
    `NotImplementedError` for Junos devices.
    Args:
        device: An object representing the network device, which includes
                device parameters and a NETCONF manager instance.
        interfaces (dict): A dictionary containing interface configuration
                           details. The structure of this dictionary should
                           match the requirements of the VLAN configuration.
    Returns:
        tuple: A tuple containing the RPC reply from the NETCONF operation
               and the filter used for the configuration.
    Raises:
        NotImplementedError: If the device is running Junos, as VLAN
                             configuration for Junos is not implemented.
    """
    
    if device.device_parameters['device_params'] == 'iosxe':
        # FILTER
        filter = OpenconfigInterfaces_EditConfig_ConfigureInterfaceVlan_Filter(interfaces, delete=False)

        # RPC
        rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
        return(rpc_reply, filter)

    if device.device_parameters['device_params'] == 'junos':
        raise NotImplementedError("Junos VLANs not implemented")

def addVlanWithNetconf(device, vlan_id, vlan_name) -> tuple:
    """
    Adds a VLAN to a network device using NETCONF.
    This function supports Cisco IOS-XE devices and uses the NETCONF protocol
    to configure VLANs. For unsupported device types, such as Junos, a 
    NotImplementedError is raised.
    Args:
        device: An object representing the network device. It must have a 
                `device_parameters` attribute with a 'device_params' key 
                indicating the device type (e.g., 'iosxe').
        vlan_id (int): The VLAN ID to be added.
        vlan_name (str): The name of the VLAN to be added.
    Returns:
        tuple: A tuple containing the RPC reply from the NETCONF operation 
               and the filter used for the configuration.
    Raises:
        NotImplementedError: If the device type is not supported (e.g., 'junos').
    """

    if device.device_parameters['device_params'] == 'iosxe':
        # FILTER
        filter = CiscoIOSXEVlan_EditConfig_AddVlan_Filter(vlan_id, vlan_name)

        # RPC
        rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
        return(rpc_reply, filter)

    if device.device_parameters['device_params'] == 'junos':
        raise NotImplementedError("Junos VLANs not implemented")

def enableL3FunctionsWithNetconf(device) -> tuple:
    if device.device_parameters['device_params'] == 'iosxe':
        # FILTER
        filter = CiscoIOSXENative_EditConfig_Enablel3Functions_Filter()

        # RPC
        rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
        return(rpc_reply, filter)

    if device.device_parameters['device_params'] == 'junos':
        raise NotImplementedError("Junos VLANs not implemented")


# ---------- FILTERS: ----------
class CiscoIOSXEVlan_Get_GetVlanList_Filter(GetFilter):
    def __init__(self):
        self.filter_xml = ET.parse(VLAN_YANG_DIR + "Cisco-IOS-XE-vlan_get_get-vlan-list.xml")


class OpenconfigInterfaces_EditConfig_ConfigureInterfaceVlan_Filter(EditconfigFilter):
    def __init__(self, interfaces: dict, delete=False):
        self.filter_xml = ET.parse(VLAN_YANG_DIR + "openconfig-interfaces_editconfig_configure-interface-vlan.xml")
        self.namespaces = {"oc-intf": "http://openconfig.net/yang/interfaces"}

        for interface_name, interface_data in interfaces.items():
            self._addInterface(interface_name, interface_data, delete)

    def _addInterface(self, interface_name, interface_data, delete):
        interfaces_element = self.filter_xml.find(".//oc-intf:interfaces", self.namespaces)
        interface_element = ET.SubElement(interfaces_element, "interface")
        name_element = ET.SubElement(interface_element, "name").text = interface_name
        ethernet_element = ET.SubElement(interface_element, "ethernet", xmlns="http://openconfig.net/yang/interfaces/ethernet")
        if delete:
            ethernet_element.set("operation", "delete")
            return

        # This will only be executed, if the operation is not "delete"
        ethernet_config_element = ET.SubElement(ethernet_element, "config")
        ethernet_switchport_element = ET.SubElement(ethernet_config_element, "switchport", xmlns="http://cisco.com/ns/yang/cisco-xe-openconfig-if-ethernet-ext")
        if interface_data["vlan_data"]["port_mode"] == "routed-port": # If the port is set to routed port, disable switchport
            ethernet_switchport_element.text = "false"
        else: # If the port is set to access or trunk, enable switchport and configure the VLANs
            switched_vlan_element = ET.SubElement(ethernet_element, "switched-vlan", xmlns="http://openconfig.net/yang/vlan")
            ethernet_switchport_element.text = "true"
            config_element = ET.SubElement(switched_vlan_element, "config")
            interface_mode_element = ET.SubElement(config_element, "interface-mode")
            if interface_data["vlan_data"]["port_mode"] == "access":
                interface_mode_element.text = "ACCESS"
                access_vlan_element = ET.SubElement(config_element, "access-vlan")
                access_vlan_element.text = interface_data["vlan_data"]["vlan"][0]
            elif interface_data["vlan_data"]["port_mode"] == "trunk":
                interface_mode_element.text = "TRUNK"
                for vlan in interface_data["vlan_data"]["vlan"]:
                    trunk_vlan_element = ET.SubElement(config_element, "trunk-vlans")
                    trunk_vlan_element.text = vlan.strip()


class CiscoIOSXEVlan_EditConfig_AddVlan_Filter(EditconfigFilter):
    def __init__(self, vlan_id, vlan_name):
        self.filter_xml = ET.parse(VLAN_YANG_DIR + "Cisco-IOS-XE-vlan_editconfig_add-vlan.xml")
        self.namespaces = {"native": "http://cisco.com/ns/yang/Cisco-IOS-XE-native",
                           "vlan": "http://cisco.com/ns/yang/Cisco-IOS-XE-vlan"}
        
        self.filter_xml.find(".//native:vlan/vlan:configuration/vlan:vlan-id", self.namespaces).text = vlan_id
        self.filter_xml.find(".//native:vlan/vlan:vlan-list/vlan:id", self.namespaces).text = vlan_id

        if vlan_name:
            self.filter_xml.find(".//native:vlan/vlan:vlan-list/vlan:name", self.namespaces).text = vlan_name


class CiscoIOSXENative_EditConfig_Enablel3Functions_Filter(EditconfigFilter):
    def __init__(self):
        self.filter_xml = ET.parse(VLAN_YANG_DIR + "Cisco-IOS-XE-native_editconfig_enable-l3-functions.xml")


# ---------- QT: ----------
class EditVlansDialog(QDialog):
    """
    EditVlansDialog is a dialog for editing VLAN configurations on network devices.
    This class provides a graphical interface for managing VLANs and their associated interfaces
    on multiple devices. Users can add new VLANs, modify VLAN configurations, and update interface
    settings such as port mode and VLAN assignments.
    Attributes:
        devices (list): A list of device objects to be edited.
        edited_devices (dict): A dictionary containing deep copies of device interfaces for editing.
        ui (Ui_edit_vlans_dialog): The UI object for setting up the dialog layout and widgets.
    Methods:
        __init__(devices):
            Initializes the dialog with the provided devices and sets up the UI.
        createDeviceTab(device):
            Creates a tab for a specific device, displaying its VLANs and interface configurations.
        _createVlanListTable(device):
            Creates a table widget to display the list of VLANs configured on a device.
        _addVlanToTable(vlan_id, vlan_name):
            Adds a new VLAN entry to the VLAN list table in the current device tab.
        _createVlanInterfacesTable(device):
            Creates a table widget to display the interface configurations for a device.
        portModeChanged(device, row, port_mode_item):
            Handles changes to the port mode of an interface and updates the corresponding data.
        vlanChanged(device, row, vlan_item):
            Handles changes to the VLAN assignment of an interface and updates the corresponding data.
        addVlan(device, vlan_id, vlan_name):
            Adds a new VLAN to the device and updates the VLAN list table.
        confirmEdit():
            Applies the changes made to the devices and commits the updated configurations.
    Usage:
        This class is intended to be used as part of a PyQt application for network configuration.
        It requires a list of device objects with attributes such as `id`, `hostname`, `vlans`, and `interfaces`.
    """

    def __init__(self, devices) -> None:
        super().__init__()

        self.devices = devices
        self.edited_devices = {}

        gnc_icon = QPixmap(os.path.join(ROOT_DIR, "graphics/icons/gnc.png"))
        self.setWindowIcon(QIcon(gnc_icon))

        self.ui = Ui_edit_vlans_dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit VLANs")
        self.ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.confirmEdit)
        self.ui.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.close)

        for device in self.devices:
            self.edited_devices[device.id] = copy.deepcopy(device.interfaces)
            self.ui.devices_tab_widget.addTab(self.createDeviceTab(device), device.hostname)

    def createDeviceTab(self, device) -> QWidget:
        """
        Creates a tab widget for a specific device, displaying VLAN configurations and interfaces.
        Args:
            device (Device): The network device for which the tab is being created.
        Returns:
            QWidget: A tab widget containing the VLAN and interface configuration for the device.
        """

        tab = QWidget()
        tab.setObjectName(device.id)
        tab_layout = QVBoxLayout()
        
        # UPPER PART
        vlan_list_groupbox = QGroupBox("VLANs")
        vlan_list_groupbox_layout = QHBoxLayout()
        # Groupbox for widgets used for adding a new VLAN
        add_vlan_groupbox = QGroupBox("Add a VLAN")
        add_vlan_groupbox_layout = QVBoxLayout()
        add_vlan_label = QLabel("Add a new VLAN:")
        add_vlan_id_label = QLabel("ID:")
        add_vlan_input_id = QLineEdit()
        add_vlan_name_label = QLabel("Name:")
        add_vlan_input_name = QLineEdit()
        add_vlan_button = QPushButton("Add")
        add_vlan_button.clicked.connect(lambda: self.addVlan(device, add_vlan_input_id.text(), add_vlan_input_name.text()))
        add_vlan_groupbox_layout.addWidget(add_vlan_label)
        add_vlan_groupbox_layout.addWidget(add_vlan_id_label)
        add_vlan_groupbox_layout.addWidget(add_vlan_input_id)
        add_vlan_groupbox_layout.addWidget(add_vlan_name_label)
        add_vlan_groupbox_layout.addWidget(add_vlan_input_name)
        add_vlan_groupbox_layout.addWidget(add_vlan_button)
        add_vlan_groupbox_layout.addStretch()
        add_vlan_groupbox.setLayout(add_vlan_groupbox_layout)
        # Groupbox for displaying VLANs configured on the device
        vlan_list_table = self._createVlanListTable(device)
        vlan_list_groupbox_layout.addWidget(vlan_list_table)
        vlan_list_groupbox_layout.addWidget(add_vlan_groupbox)
        vlan_list_groupbox.setLayout(vlan_list_groupbox_layout)
        
        # LOWER PART
        vlan_interface_table = self._createVlanInterfacesTable(device)
        
        # TAB LAYOUT
        tab_layout.addWidget(vlan_list_groupbox)
        tab_layout.addWidget(vlan_interface_table)
        tab.setLayout(tab_layout)
        return tab
        
    def _createVlanListTable(self, device) -> QTableWidget:
        """
        Creates a table widget to display the list of VLANs configured on a device.
        Args:
            device (Device): The network device for which the VLANs are being displayed.
        Returns:
            QTableWidget: A table widget displaying the VLANs and their names.
        """

        vlan_list_table = QTableWidget()
        vlan_list_table.setObjectName(f"vlan_list_table_{device.id}")
        vlan_list_table.setColumnCount(2)
        vlan_list_table.setRowCount(len(device.vlans))
        vlan_list_table.setHorizontalHeaderLabels(['ID', 'Name'])
        vlan_list_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for row, (vlan_id, vlan_data) in enumerate(device.vlans.items()):
            # VLAN ID
            vlan_id_item = QTableWidgetItem(vlan_id)
            vlan_id_item.setFlags(vlan_id_item.flags() ^ Qt.ItemIsEditable)
            vlan_list_table.setItem(row, 0, vlan_id_item)
            # VLAN name
            vlan_name = vlan_data.get('name', "N/A")
            vlan_name_item = QTableWidgetItem(vlan_name)
            vlan_name_item.setFlags(vlan_name_item.flags() ^ Qt.ItemIsEditable)
            vlan_list_table.setItem(row, 1, vlan_name_item)
        return(vlan_list_table)
    
    def _addVlanToTable(self, vlan_id, vlan_name) -> None:
        """
        Adds a new VLAN entry to the VLAN list table in the current device tab.
        Args:
            vlan_id (str): The ID of the VLAN to be added.
            vlan_name (str): The name of the VLAN to be added.
        """

        current_tab = self.ui.devices_tab_widget.currentWidget()
        vlan_list_table = current_tab.findChild(QTableWidget, f"vlan_list_table_{current_tab.objectName()}")
        row = vlan_list_table.rowCount()
        vlan_list_table.insertRow(row)
        vlan_list_table.setItem(row, 0, QTableWidgetItem(vlan_id))
        vlan_list_table.setItem(row, 1, QTableWidgetItem(vlan_name))
    
    def _createVlanInterfacesTable(self, device) -> QTableWidget:
        """
        Creates a table widget to display the interface configurations for a device.
        Args:
            device (Device): The network device for which the interface configurations are displayed.
        Returns:
            QTableWidget: A table widget displaying the interface configurations.
        """

        vlan_interface_table = QTableWidget()
        vlan_interface_table.setObjectName(f"vlan_interface_table_{device.id}")
        vlan_interface_table.setColumnCount(6)
        vlan_interface_table.setRowCount(len(self.edited_devices[device.id].items()))
        vlan_interface_table.setHorizontalHeaderLabels(['Interface', 
                                                        'Admin state',
                                                        'Operational state',
                                                        'Description',
                                                        'Port mode',
                                                        'VLAN/s'])
        vlan_interface_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for row, (interface_element, interface_data) in enumerate(self.edited_devices[device.id].items()):      
                admin_state = interface_data.get('admin_status', "N/A")
                oper_state = interface_data.get('oper_status', "N/A")
                description = interface_data.get('description', "N/A")

                bg_color = utils.getBgColorFromFlag(interface_data['flag'])
                tooltip = utils.getTooltipFromFlag(interface_data['flag'])

                # Interface name
                interface_item = QTableWidgetItem(interface_element)
                interface_item.setFlags(interface_item.flags() ^ Qt.ItemIsEditable)  # Non-editable cells
                interface_item.setBackground(QBrush(QColor(bg_color)))
                interface_item.setToolTip(tooltip)
                vlan_interface_table.setItem(row, 0, interface_item)
                # Administrative state
                admin_state_item = QTableWidgetItem(admin_state)
                admin_state_item.setFlags(admin_state_item.flags() ^ Qt.ItemIsEditable)
                admin_state_item.setBackground(QBrush(QColor(bg_color)))
                admin_state_item.setToolTip(tooltip)
                vlan_interface_table.setItem(row, 1, admin_state_item)
                # Operational state
                oper_state_item = QTableWidgetItem(oper_state)
                oper_state_item.setFlags(oper_state_item.flags() ^ Qt.ItemIsEditable)
                oper_state_item.setBackground(QBrush(QColor(bg_color)))
                oper_state_item.setToolTip(tooltip)
                vlan_interface_table.setItem(row, 2, oper_state_item)
                # Description
                description_item = QTableWidgetItem(description)
                description_item.setFlags(oper_state_item.flags() ^ Qt.ItemIsEditable)
                description_item.setBackground(QBrush(QColor(bg_color)))
                description_item.setToolTip(tooltip)
                vlan_interface_table.setItem(row, 3, description_item)
                # port mode
                port_mode = interface_data["vlan_data"].get('port_mode', None)
                port_mode_item = QComboBox()
                port_mode_item.activated.connect(lambda index, row=row, port_item=port_mode_item: self.portModeChanged(device, row, port_item))
                port_mode_item.addItems(["access", "trunk", "routed-port", " "])
                if port_mode == None:
                    port_mode_item.setCurrentText(" ")
                else:
                    port_mode_item.setCurrentText(port_mode)
                vlan_interface_table.setCellWidget(row, 4, port_mode_item)
                # VLANs
                vlan_from_dict = interface_data["vlan_data"].get('vlan', None)
                vlan_item = QLineEdit()
                vlan_item.editingFinished.connect(lambda row=row, vlan_item=vlan_item: self.vlanChanged(device, row, vlan_item))
                if port_mode == None:
                    vlan_text = ""
                    vlan_item.setEnabled(False)
                elif port_mode == "routed-port":
                    vlan_text = ""
                    vlan_item.setEnabled(False)
                elif port_mode == "access":
                    vlan_text = vlan_from_dict
                    vlan_item.setEnabled(True)
                elif port_mode == "trunk":
                    vlan_text = ",".join(vlan_from_dict)
                    vlan_item.setEnabled(True)
                vlan_item.setText(vlan_text)
                vlan_interface_table.setCellWidget(row, 5, vlan_item)

        return(vlan_interface_table)

    def portModeChanged(self, device, row, port_mode_item) -> None:
        """
        Handles events when the port mode of an interface is changed in the dialog table by the user.
        Updates the corresponding data in the edited_devices dictionary.
        Args:
            device (Device): The network device for which the interface configuration is being edited.
            row (int): The row index of the interface in the table.
            port_mode_item (QComboBox): The combobox widget containing the port mode options.
        """
        interface_item = self.ui.devices_tab_widget.currentWidget().findChild(QTableWidget).item(row, 0)
        interface = interface_item.text()
        old_mode = device.interfaces[interface]['vlan_data'].get('port_mode', None)
        new_mode = port_mode_item.currentText()

        if old_mode == new_mode:
            return
        
        if new_mode == "access" or new_mode == "trunk":
            self.ui.devices_tab_widget.currentWidget().findChild(QTableWidget).cellWidget(row, 5).setEnabled(True)
            self.edited_devices[device.id][interface]['vlan_data']['port_mode'] = new_mode
        elif new_mode == "routed-port":
            self.ui.devices_tab_widget.currentWidget().findChild(QTableWidget).cellWidget(row, 5).setEnabled(False)
            self.edited_devices[device.id][interface]['vlan_data']['port_mode'] = new_mode
        else:
            self.ui.devices_tab_widget.currentWidget().findChild(QTableWidget).cellWidget(row, 5).setEnabled(False)
            self.edited_devices[device.id][interface]['vlan_data']['port_mode'] = None
        self.edited_devices[device.id][interface]['flag'] = "uncommited"
        self.edited_devices[device.id][interface]['vlan_data']['vlan'] = "" # when changing mode, clear the VLANs number/s field
        self.ui.devices_tab_widget.currentWidget().findChild(QTableWidget).cellWidget(row, 5).setText(" ") # when changing mode, clear the VLANs number/s field

    def vlanChanged(self, device, row, vlan_item) -> None:
        """
        Handles events when the VLAN assignment of an interface is changed in the dialog table by the user.
        Updates the corresponding data in the edited_devices dictionary.
        Args:
            device (Device): The network device for which the interface configuration is being edited.
            row (int): The row index of the interface in the table.
            vlan_item (QLineEdit): The line edit widget containing the VLAN assignment.
        """

        interface_item = self.ui.devices_tab_widget.currentWidget().findChild(QTableWidget).item(row, 0)
        interface = interface_item.text()
        old_vlans = device.interfaces[interface]['vlan_data'].get('vlan', None)
        new_vlans = vlan_item.text().strip()

        if old_vlans == new_vlans:
            return

        new_vlans_list = new_vlans.split(",")
        self.edited_devices[device.id][interface]['vlan_data']['vlan'] = new_vlans_list
        self.edited_devices[device.id][interface]['flag'] = "uncommited"

    def addVlan(self, device, vlan_id, vlan_name) -> None:
        """
        Adds a new VLAN to the device and updates the VLAN list table.
        Args:
            device (Device): The network device to which the VLAN is being added.
            vlan_id (str): The ID of the new VLAN.
            vlan_name (str): The name of the new VLAN.
        """

        if not vlan_id:
            QMessageBox.warning(self, "Error", "VLAN ID cannot be empty.")
            return

        if vlan_id in device.vlans:
            QMessageBox.warning(self, "Error", f"VLAN {vlan_id} already exists.")
            return
        
        device.addVlan(vlan_id, vlan_name)
        self._addVlanToTable(vlan_id, vlan_name)

    def confirmEdit(self) -> None:
        """
        Handles the user's confirmation to apply the changes made in the dialog.
        Checks which interfaces have been edited on every device, and sends the changes to the devices (creates the filter, sends the RPC).
        """

        for device in self.devices:
            uncommited_interfaces = {k: v for k, v in self.edited_devices[device.id].items() if v['flag'] == "uncommited"}
            if not uncommited_interfaces:
                continue

            interfaces_to_delete = {}
            interfaces_to_set = {}
            for interface, data in uncommited_interfaces.items():
                if data['vlan_data']['port_mode'] == "" or data['vlan_data']['port_mode'] == None: # if the port mode is empty, delete the VLAN configuration
                    interfaces_to_delete[interface] = data

                if data['vlan_data']['port_mode'] == "access": # if the port mode is access, the VLAN number must be set
                    if data['vlan_data']['vlan'] == "" or data['vlan_data']['vlan'] == None:
                        QMessageBox.warning(self, "Error", f"Device {device.hostname} - Interface {interface} has an empty VLAN number/s.")
                        return
                    else:
                        interfaces_to_delete[interface] = data
                        interfaces_to_set[interface] = data
                elif data['vlan_data']['port_mode'] == "trunk": # if the port mode is trunk, the VLAN number/s is optionall
                    interfaces_to_delete[interface] = data
                    interfaces_to_set[interface] = data
                elif data['vlan_data']['port_mode'] == "routed-port":
                    interfaces_to_delete[interface] = data
                    interfaces_to_set[interface] = data

            if interfaces_to_delete:
                result_delete = device.deleteInterfaceVlan(interfaces_to_delete)
                if result_delete is False:
                    QMessageBox.critical(self, "Error", f"Failed to delete VLAN configuration on device {device.hostname}.")
                    continue
            
            if interfaces_to_set:
                result_set = device.setInterfaceVlan(interfaces_to_set)
                if result_set is False:
                    QMessageBox.critical(self, "Error", f"Failed to set VLAN configuration on device {device.hostname}.")
                    continue

            device.interfaces = copy.deepcopy(self.edited_devices[device.id]) # Copy the temporary dictionary to the device's interfaces dictionary
            
        self.accept()