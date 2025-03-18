# Other
from pyangbind.lib.serialise import pybindIETFXMLEncoder
from ipaddress import IPv4Address, IPv6Address, IPv4Interface, IPv6Interface
from lxml import etree as ET

from ncclient import operations

# Custom
import modules.netconf as netconf
import utils as utils
from definitions import *
from yang.filters import EditconfigFilter, GetFilter

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
import copy


from ui.ui_editvlansdialog import Ui_edit_vlans_dialog

# ---------- OPERATIONS: ----------
def getVlansWithNetconf(device) -> dict:
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

    if device.device_parameters['device_params'] == 'junos':
        raise NotImplementedError("Junos VLANs not implemented")

    return(vlans, rpc_reply)

def configureInterfaceVlanWithNetconf(device, interfaces: dict):
    pass

# ---------- FILTERS: ----------
class CiscoIOSXEVlan_Get_GetVlanList_Filter(GetFilter):
    def __init__(self):
        self.filter_xml = ET.parse(VLAN_YANG_DIR + "Cisco-IOS-XE-vlan_get_get-vlan-list.xml")


# ---------- QT: ----------
class EditVlansDialog(QDialog):
    def __init__(self, devices):
        super().__init__()

        self.devices = devices
        self.edited_devices = {}

        self.ui = Ui_edit_vlans_dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit VLANs")
        self.ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.confirmEdit)
        self.ui.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.close)

        for device in self.devices:
            #self.edited_devices[device.id] = device.interfaces.copy()
            self.edited_devices[device.id] = copy.deepcopy(device.interfaces)
            self.ui.devices_tab_widget.addTab(self.createDeviceTab(device), device.hostname)
            
            
            print(self.edited_devices)

    def createDeviceTab(self, device):
        tab = QWidget()
        tab_layout = QVBoxLayout()
        
        # UPPER PART
        vlan_list_groupbox = QGroupBox("VLANs")
        vlan_list_groupbox_layout = QHBoxLayout()
        # Groupbox for widgets used for adding a new VLAN
        add_vlan_groupbox = QGroupBox("Add a VLAN")
        add_vlan_groupbox_layout = QVBoxLayout()
        add_vlan_label = QLabel("Add a new VLAN:")
        add_vlan_input = QLineEdit()
        add_vlan_button = QPushButton("Add")
        add_vlan_button.clicked.connect(lambda: self.addVlan(device, add_vlan_input.text()))
        add_vlan_groupbox_layout.addWidget(add_vlan_label)
        add_vlan_groupbox_layout.addWidget(add_vlan_input)
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
        
    def _createVlanListTable(self, device):
        vlan_list_table = QTableWidget()
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
    
    def _createVlanInterfacesTable(self, device):
        
        vlan_interface_table = QTableWidget()
        vlan_interface_table.setColumnCount(6)
        vlan_interface_table.setRowCount(len(device.interfaces))
        vlan_interface_table.setHorizontalHeaderLabels(['Interface', 
                                                        'Admin state',
                                                        'Operational state',
                                                        'Description',
                                                        'Switchport mode',
                                                        'VLAN/s'])
        vlan_interface_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for row, (interface_element, interface_data) in enumerate(self.edited_devices[device.id].items()):      
                admin_state = interface_data.get('admin_status', "N/A")
                oper_state = interface_data.get('oper_status', "N/A")
                description = interface_data.get('description', "N/A")

                # Interface name
                interface_item = QTableWidgetItem(interface_element)
                interface_item.setFlags(interface_item.flags() ^ Qt.ItemIsEditable)  # Non-editable cells
                #interface_item.setBackground(QBrush(QColor(bg_color)))
                #interface_item.setToolTip(tooltip)
                vlan_interface_table.setItem(row, 0, interface_item)
                # Administrative state
                admin_state_item = QTableWidgetItem(admin_state)
                admin_state_item.setFlags(admin_state_item.flags() ^ Qt.ItemIsEditable)
                #admin_state_item.setBackground(QBrush(QColor(bg_color)))
                #admin_state_item.setToolTip(tooltip)
                vlan_interface_table.setItem(row, 1, admin_state_item)
                # Operational state
                oper_state_item = QTableWidgetItem(oper_state)
                oper_state_item.setFlags(oper_state_item.flags() ^ Qt.ItemIsEditable)
                #oper_state_item.setBackground(QBrush(QColor(bg_color)))
                #oper_state_item.setToolTip(tooltip)
                vlan_interface_table.setItem(row, 2, oper_state_item)
                # Description
                description_item = QTableWidgetItem(self.edited_devices[device.id][interface_element]["description"])
                description_item.setFlags(oper_state_item.flags() ^ Qt.ItemIsEditable)
                #description_item.setBackground(QBrush(QColor(bg_color)))
                #description_item.setToolTip(tooltip)
                vlan_interface_table.setItem(row, 3, description_item)
                # Switchport mode
                switchport_mode = interface_data["vlan_data"].get('switchport_mode', None)
                switchport_mode_item = QComboBox()
                switchport_mode_item.activated.connect(lambda index, row=row, switchport_item=switchport_mode_item: self.switchportModeChanged(device, row, switchport_item))
                switchport_mode_item.addItems(["access", "trunk", " "])
                if switchport_mode == None:
                    switchport_mode_item.setCurrentText(" ")
                else:
                    switchport_mode_item.setCurrentText(switchport_mode)
                #switchport_mode_item.setBackground(QBrush(QColor(bg_color)))
                #switchport_mode_item.setToolTip(tooltip)
                vlan_interface_table.setCellWidget(row, 4, switchport_mode_item)
                # VLANs
                vlan = interface_data["vlan_data"].get('vlan', None)
                vlan_item = QLineEdit()
                vlan_item.editingFinished.connect(lambda row=row, vlan_item=vlan_item: self.vlanChanged(device, row, vlan_item))
                
                if switchport_mode == None:
                    vlan = ""
                    vlan_item.setEnabled(False)
                elif switchport_mode == "access":
                    vlan = vlan
                    vlan_item.setEnabled(True)
                elif switchport_mode == "trunk":
                    vlan = ", ".join(vlan)
                    vlan_item.setEnabled(True)
                vlan_item.setText(vlan)
                #vlans_item.setBackground(QBrush(QColor(bg_color)))
                #vlans_item.setToolTip(tooltip)
                vlan_interface_table.setCellWidget(row, 5, vlan_item)

        return(vlan_interface_table)

    def switchportModeChanged(self, device, row, switchport_mode_item):
        interface_item = self.ui.devices_tab_widget.currentWidget().findChild(QTableWidget).item(row, 0)
        interface = interface_item.text()
        old_mode = device.interfaces[interface]['vlan_data'].get('switchport_mode', None)
        new_mode = switchport_mode_item.currentText()

        if old_mode == new_mode:
            return
        
        if new_mode == "access" or new_mode == "trunk":
            self.ui.devices_tab_widget.currentWidget().findChild(QTableWidget).cellWidget(row, 5).setEnabled(True)
            self.edited_devices[device.id][interface]['vlan_data']['switchport_mode'] = new_mode
        else:
            self.ui.devices_tab_widget.currentWidget().findChild(QTableWidget).cellWidget(row, 5).setEnabled(False)
            self.edited_devices[device.id][interface]['vlan_data']['switchport_mode'] = None
        self.edited_devices[device.id][interface]['flag'] = "uncommited"
        self.edited_devices[device.id][interface]['vlan_data']['vlan'] = "" # when changing mode, clear the VLANs field
        self.ui.devices_tab_widget.currentWidget().findChild(QTableWidget).cellWidget(row, 5).setText(" ") # when changing mode, clear the VLANs field

    def vlanChanged(self, device, row, vlan_item):
        interface_item = self.ui.devices_tab_widget.currentWidget().findChild(QTableWidget).item(row, 0)
        interface = interface_item.text()
        old_vlans = device.interfaces[interface]['vlan_data'].get('vlan', None)
        new_vlans = vlan_item.text()

        if old_vlans == new_vlans:
            return

        self.edited_devices[device.id][interface]['vlan_data']['vlan'] = new_vlans
        self.edited_devices[device.id][interface]['flag'] = "uncommited"

    def addVlan(self, device, vlan_id):
        pass

    def confirmEdit(self):
        for device in self.devices:
            uncommited_interfaces = {k: v for k, v in self.edited_devices[device.id].items() if v['flag'] == "uncommited"}
            device.configureInterfaceVlan(uncommited_interfaces)
