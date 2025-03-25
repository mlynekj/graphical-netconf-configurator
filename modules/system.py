# ---------- IMPORTS: ----------
# Standard library
from lxml import etree as ET

# Custom modules
import utils as utils
from yang.filters import GetFilter, EditconfigFilter
from definitions import SYSTEM_YANG_DIR, CONFIGURATION_TARGET_DATASTORE

# Qt
from PySide6.QtWidgets import (
    QDialog, 
    QVBoxLayout,
    QDialogButtonBox,
    QLineEdit,
    QStyle,
    QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QGuiApplication, QIcon, QPixmap


# ---------- OPERATIONS: ----------
def getHostnameWithNetconf(device) -> tuple:
    """
    Retrieves the device hostname of the specified device.
    Returns:
        tuple:
            - hostname (str): The hostname of the device.
            - rpc_reply (str): The raw NETCONF RPC reply.
    """

    device_type = device.device_parameters['device_params']

    # FILTER
    if device_type == "iosxe":
        filter_xml = CiscoIOSXENative_Get_GetHostname_Filter() # For Cisco, use IOS-XE native models
    elif device_type == "junos":
        filter_xml = OpenconfigSystem_Get_GetHostname_Filter() # For Juniper, use OpenConfig models
    
    # RPC    
    rpc_reply = device.mngr.get_config(source="running", filter=str(filter_xml))
    rpc_reply_etree = utils.convertToEtree(rpc_reply, device_type)
    
    # XPATH
    hostname = rpc_reply_etree.find(".//hostname")
    if hostname is not None:
        return(hostname.text, rpc_reply)
    else:
        return("N/A", rpc_reply)

def setHostnameWithNetconf(device, new_hostname) -> tuple:
    """
    Sets the device hostname of the specified device to the specified value.
    Args:
        new_hostname (str): The new hostname to set.
    Returns:
        tuple:
            - rpc_reply (str): The raw NETCONF RPC reply.
            - filter_xml (str): The raw NETCONF filter XML.
    """

    device_type = device.device_parameters['device_params']

    # CONFIG FILTER
    if device_type == "iosxe":
        filter_xml = CiscoIOSXENative_Editconfig_EditHostname_Filter(new_hostname) # For Cisco, use IOS-XE native models
    elif device_type == "junos":
        filter_xml = OpenconfigSystem_Editconfig_EditHostname_Filter(new_hostname) # For Juniper, use OpenConfig models

    # RPC
    rpc_reply = device.mngr.edit_config(target=CONFIGURATION_TARGET_DATASTORE, config=str(filter_xml))
    return(rpc_reply, filter_xml)


# ---------- FILTERS: ----------
class CiscoIOSXENative_Get_GetHostname_Filter(GetFilter):
    def __init__(self):
        self.filter_xml = ET.parse(SYSTEM_YANG_DIR + "Cisco-IOS-XE-native_get_get-hostname.xml")


class OpenconfigSystem_Get_GetHostname_Filter(GetFilter):
    def __init__(self):
        self.filter_xml = ET.parse(SYSTEM_YANG_DIR + "openconfig-system_get_get-hostname.xml")


class CiscoIOSXENative_Editconfig_EditHostname_Filter(EditconfigFilter):
    def __init__(self, new_hostname):
        self.filter_xml = ET.parse(SYSTEM_YANG_DIR + "Cisco-IOS-XE-native_edit-config_edit-hostname.xml")
        namespaces = {'ns': 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
        
        hostname_element = self.filter_xml.find(".//ns:hostname", namespaces)
        hostname_element.text = new_hostname


class OpenconfigSystem_Editconfig_EditHostname_Filter(EditconfigFilter):
    def __init__(self, new_hostname):
        self.filter_xml = ET.parse(SYSTEM_YANG_DIR + "openconfig-system_edit-config_edit-hostname.xml") # For Juniper, use openconfig models
        namespaces = {'ns': 'http://openconfig.net/yang/system'}
        
        hostname_element = self.filter_xml.find(".//ns:hostname", namespaces)
        hostname_element.text = new_hostname


# ---------- QT: ----------
class HostnameDialog(QDialog):
    """
    A dialog window for editing the hostname of a device.
    This dialog allows the user to view the current hostname of a device,
    input a new hostname, and confirm or cancel the change.
    Attributes:
        device (object): The device object whose hostname is being edited.
        old_hostname (str): The current hostname of the device.
        new_hostname (str): The new hostname entered by the user.
        layout (QVBoxLayout): The layout manager for the dialog.
        hostname_input (QLineEdit): The input field for entering the new hostname.
        buttons (QDialogButtonBox): The dialog buttons for confirming or canceling the action.
    Methods:
        _confirmRename():
            Handles the logic for confirming the hostname change.
            Updates the device's hostname if a valid new hostname is provided.
    """

    def __init__(self, device) -> None:
        super().__init__()

        self.device = device
        self.old_hostname = self.device.hostname

        gnc_icon = QPixmap("graphics/icons/gnc.png")
        self.setWindowIcon(QIcon(gnc_icon))
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

    def _confirmRename(self) -> None:
        """Handles the logic for confirming the hostname change."""
        
        self.new_hostname = self.hostname_input.text()

        if not self.new_hostname or (self.new_hostname == self.old_hostname):
            QMessageBox.information(self, "Information", "No changes were made.")
        elif self.new_hostname and self.new_hostname != self.old_hostname:
            self.device.setHostname(self.new_hostname)
            self.device.refreshHostnameLabel()
        self.accept()