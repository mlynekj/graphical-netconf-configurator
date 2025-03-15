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


from ui.ui_editvlansdialog import Ui_edit_vlans_dialog

# ---------- OPERATIONS: ----------
def getVlansWithNetconf(device):
    device_type = device.device_parameters['device_params']

    if device_type == 'iosxe':
        # FILTER
        filter = CiscoIOSXEVlan_Get_GetVlanList_Filter()

        # RPC
        rpc_reply = device.mngr.get(str(filter))
        rpc_reply_etree = utils.convertToEtree(rpc_reply, device_type)

        # PARSE
        vlans = {}
        vlans_elements = rpc_reply_etree.findall('.//vlan-list')

        for vlan_element in vlans_elements:
            vlan_id = vlan_element.find('id')
            name = vlan_element.find('name')
            vlans[vlan_id.text] = {
                'name': name.text if name is not None else '',
            }

    if device_type == 'junos':
        raise NotImplementedError("Junos VLANs not implemented")

    return(vlans, rpc_reply)


# ---------- FILTERS: ----------
class CiscoIOSXEVlan_Get_GetVlanList_Filter(GetFilter):
    def __init__(self):
        self.filter_xml = ET.parse(VLAN_YANG_DIR + "Cisco-IOS-XE-vlan_get_get-vlan-list.xml")


# ---------- QT: ----------
class EditVlansDialog(QDialog):
    def __init__(self, devices):
        super().__init__()

        self.devices = devices

        self.ui = Ui_edit_vlans_dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Edit VLANs")
        self.ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.confirmEdit)
        self.ui.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.close)

        

    def confirmEdit(self):
        pass