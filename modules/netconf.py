# Other
from ncclient import manager, transport, operations
from ncclient.operations import RaiseMode
from lxml import etree as ET
from PySide6.QtWidgets import QLabel, QMessageBox
from pyangbind.lib.serialise import pybindIETFXMLEncoder

# Custom
import utils as utils

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
from PySide6.QtGui import QGuiApplication

from yang.filters import DispatchFilter
from definitions import SYSTEM_YANG_DIR

# ---------- FILTERS: ----------
class JunosRpc_Dispatch_RollbackZero_Filter(DispatchFilter):
    def __init__(self):
        self.filter_xml = ET.parse(SYSTEM_YANG_DIR + "junos-rpc_dispatch_rollback_pending_changes.xml")



def establishNetconfConnection(device_parameters):
    """
    Establishes a NETCONF connection to a network device.
    Args:
        device_parameters (dict): A dictionary containing:
            - address (str): The IP address or hostname of the device.
            - username (str): The username for authentication.
            - password (str): The password for authentication.
            - port (int): The port number for the NETCONF connection.
            - device_params (str): The device-specific parameters for the NETCONF connection.
    Returns:
        ncclient.manager: An instance of the ncclient manager class representing the NETCONF connection.
    """
    
    try:
        mngr = manager.connect(
            host=device_parameters["address"],
            username=device_parameters["username"],
            password=device_parameters["password"],
            port=device_parameters["port"],
            device_params={"name": device_parameters["device_params"]},
            hostkey_verify=False
        )
        mngr.raise_mode = RaiseMode.ERRORS # Raise exceptions only on errors, not on warnings (https://github.com/ncclient/ncclient/issues/545)
        utils.printGeneral(f"Successfully established NETCONF connection to: {device_parameters['address']} on port {device_parameters['port']}")
        return mngr
    except transport.SSHError as e:
        QMessageBox.critical(None, "Connection Error", f"Unable to connect: {e}")
        raise ConnectionError(f"Unable to connect: {e}")
    except transport.AuthenticationError as e:
        QMessageBox.critical(None, "Authentication Error", f"Authentication error: {e}")
        raise ConnectionError(f"Authentication error: {e}")
    except operations.TimeoutExpiredError as e:
        QMessageBox.critical(None, "Timeout Error", f"Timeout during connecting expired: {e}")
        raise ConnectionError(f"Timeout during connecting expired: {e}")
    except Exception as e:
        QMessageBox.critical(None, "General Error", f"General error: {e}")
        raise ConnectionError(f"General error: {e}")
 
def demolishNetconfConnection(device):
    """ Tears down the spcified ncclient connection, by deleting the mng object. """
    try:
        rpc_reply = device.mngr.close_session()
        return(rpc_reply)
    except operations.RPCError as e:
        utils.printGeneral(f"Failed to close NETCONF connection: {e}")
        return (rpc_reply)
    except Exception as e:
        utils.printGeneral(f"Failed to close NETCONF connection: {e}")
        return None

def commitNetconfChanges(device, confirmed: bool=False, confirm_timeout=None):
    """ Performs the "commit" operation using the specified ncclient connection. """
    try:
        rpc_reply = device.mngr.commit(confirmed, timeout=str(confirm_timeout))
        return(rpc_reply)
    except operations.RPCError as e:
        utils.printGeneral(f"Failed to commit changes: {e}")
        return (rpc_reply)
    except Exception as e:
        utils.printGeneral(f"Failed to commit changes: {e}")
        return None

def discardNetconfChanges(device):
    """ Performs the "discard-changes" operation using the specified ncclient connection. """
    try:
        rpc_reply = device.mngr.discard_changes()
        return(rpc_reply)
    except operations.RPCError as e:
        utils.printGeneral(f"Failed to discard changes: {e}")
        return (rpc_reply)
    except Exception as e:
        utils.printGeneral(f"Failed to discard changes: {e}")
        return None
    
def cancelNetconfCommit(device):
    """ Performs the "cancel-commit" operation using the specified ncclient connection. """
    try:
        rpc_reply = device.mngr.cancel_commit()
        return(rpc_reply)
    except operations.RPCError as e:
        utils.printGeneral(f"Failed to cancel commit: {e}")
        return (rpc_reply)
    except Exception as e:
        utils.printGeneral(f"Failed to cancel commit: {e}")
        return None

def rollbackZeroNetconfChanges(device):
    """ Performs the "rollback" operation using the specified ncclient connection. """
    try:
        rpc_payload = JunosRpc_Dispatch_RollbackZero_Filter()
        rpc_reply = device.mngr.dispatch(rpc_payload.__ele__())
        return(rpc_reply)
    except operations.RPCError as e:
        utils.printGeneral(f"Failed to rollback changes: {e}")
        return (rpc_reply)
    except Exception as e:
        utils.printGeneral(f"Failed to rollback changes: {e}")
        return None

def getNetconfCapabilities(device):
    """ Retrieves the capabilities of the specified ncclient connection. """
    capabilities = device.mngr.server_capabilities
    return(capabilities)



# ---------- QT: ----------
class NetconfCapabilitiesDialog(QDialog):
    def __init__(self, device):
        super().__init__()

        self.setWindowTitle("Device Capabilities")
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                QSize(800, 500),
                QGuiApplication.primaryScreen().availableGeometry()
            )
        )

        self.layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Initialize table for holding the capabilities
        self.table_widget = QWidget()
        self.table_layout = QVBoxLayout()
        self.capabilities_table = QTableWidget()
        self.capabilities_table.setColumnCount(1)
        self.capabilities_table.setHorizontalHeaderLabels(["Capability"])

        # Load capabilities
        try:
            self.capabilities = device.netconf_capabilities
        except Exception as e:
            self.capabilities = []
            self.error_label = QLabel(f"Failed to retrieve self.capabilities: {e}")
            self.table_layout.addWidget(self.error_label)

        # Populate the table with the capabilities
        if self.capabilities:
            self.capabilities_table.setRowCount(len(self.capabilities))
            for row, capability in enumerate(self.capabilities):
                capability_item = QTableWidgetItem(capability)
                capability_item.setFlags(capability_item.flags() ^ Qt.ItemIsEditable) # Non-editable cells
                self.capabilities_table.setItem(row, 0, capability_item)
        else :
            self.capabilities_table.setRowCount(1)
            self.capabilities_table.setItem(0, 0, QTableWidgetItem("No capabilities found"))

        # Set table properties
        self.capabilities_table.horizontalHeader().setStretchLastSection(True)
        self.capabilities_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.capabilities_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Add table to layout
        self.table_layout.addWidget(self.capabilities_table)
        self.table_widget.setLayout(self.table_layout)
        self.scroll_area.setWidget(self.table_widget)
        self.layout.addWidget(self.scroll_area)

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.layout.addWidget(self.close_button)

        self.setLayout(self.layout)
 