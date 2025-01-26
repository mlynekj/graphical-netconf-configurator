# Others
from lxml import etree as ET

# Custom
import helper as helper
from definitions import *

# Qt
from PySide6.QtWidgets import (
    QDialog, 
    QVBoxLayout,
    QDialogButtonBox,
    QLineEdit,
    QStyle,)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QGuiApplication

def getHostnameWithNetconf(device):
    """ Retrieves the device hostname of the specified device. """
    device_type = device.device_parameters['device_params']

    # FILTER
    if device_type == "iosxe":
        filter_xml = ET.parse(CISCO_XML_DIR + "system/get_config-hostname.xml") # For Cisco, use IOS-XE native models
        rpc_filter = ET.tostring(filter_xml).decode('utf-8') 
    elif device_type == "junos":
        filter_xml = ET.parse(OPENCONFIG_XML_DIR + "system/get_config-hostname.xml") # For Juniper, use OpenConfig models
        rpc_filter = ET.tostring(filter_xml).decode('utf-8') 
    
    # RPC    
    rpc_reply = device.mngr.get_config(source="running", filter=rpc_filter)
    rpc_reply_etree = helper.convertToEtree(rpc_reply, device_type)
    
    # XPATH
    hostname = rpc_reply_etree.find(".//hostname")
    if hostname is not None:
        return(hostname.text)
    else:
        return("N/A")

def setHostnameWithNetconf(device, new_hostname):
    """ Sets the device hostname of the specified device to the specified value. """
    device_type = device.device_parameters['device_params']

    # CONFIG FILTER
    if device_type == "iosxe":
        filter_xml = ET.parse(CISCO_XML_DIR + "system/edit_config-hostname.xml") # For Cisco, use IOS-XE native models
        namespaces = {'ns': 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
        hostname_element = filter_xml.find(".//ns:hostname", namespaces)
        hostname_element.text = new_hostname
        rpc_filter = ET.tostring(filter_xml).decode('utf-8') 
    elif device_type == "junos":
        filter_xml = ET.parse(OPENCONFIG_XML_DIR + "system/edit_config-hostname.xml") # For Juniper, use openconfig models
        namespaces = {'ns': 'http://openconfig.net/yang/system'}
        hostname_element = filter_xml.find(".//ns:hostname", namespaces)
        hostname_element.text = new_hostname
        rpc_filter = ET.tostring(filter_xml).decode('utf-8')
    
    # FLAG (needed to update the hostname label on canvas, when commiting changes later on)
    device.has_updated_hostname = True

    # RPC
    rpc_reply = device.mngr.edit_config(target=CONFIGURATION_TARGET_DATASTORE, config=rpc_filter)
    return(rpc_reply)

# ---------- QT: ----------
class HostnameDialog(QDialog):
    def __init__(self, device):
        super().__init__()

        self.device = device
        self.old_hostname = self.device.hostname

        self.setWindowTitle(f"Edit hostname: {self.old_hostname}")
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
        self.buttons.accepted.connect(self._confirmRename)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)

    def _confirmRename(self):
        self.new_hostname = self.hostname_input.text()

        if not self.new_hostname or (self.new_hostname == self.old_hostname):
            helper.showMessageBox(self, "Information", "No changes were made.")
        elif self.new_hostname and self.new_hostname != self.old_hostname:
            self.device.setHostname(self.new_hostname)
            self.device.refreshHostnameLabel()
        self.accept()
