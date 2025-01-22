# Other
from ncclient import manager, transport, operations
from ncclient.operations import RaiseMode
from lxml import etree as ET
from PySide6.QtWidgets import QLabel, QMessageBox
from pyangbind.lib.serialise import pybindIETFXMLEncoder

# Custom
import modules.helper as helper

def establishNetconfConnection(device_parameters):
    # TODO: pass the device, not the device_parameters ?
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
        helper.printGeneral(f"Successfully established NETCONF connection to: {device_parameters['address']} on port {device_parameters['port']}")
        return mngr
    except transport.errors.SSHError as e:
        QMessageBox.critical(None, "Connection Error", f"Unable to connect: {e}")
        raise ConnectionError(f"Unable to connect: {e}")
    except transport.errors.AuthenticationError as e:
        QMessageBox.critical(None, "Authentication Error", f"Authentication error: {e}")
        raise ConnectionError(f"Authentication error: {e}")
    except operations.errors.TimeoutExpiredError as e:
        QMessageBox.critical(None, "Timeout Error", f"Timeout during connecting expired: {e}")
        raise ConnectionError(f"Timeout during connecting expired: {e}")
    except Exception as e:
        QMessageBox.critical(None, "General Error", f"General error: {e}")
        raise ConnectionError(f"General error: {e}")
 
def demolishNetconfConnection(device):
    # TODO: pass the device, not the mngr ?
    """ Tears down the spcified ncclient connection, by deleting the mng object. """
    device.mngr.close_session()
    # TODO: catch exceptions

def commitNetconfChanges(device):
    # TODO: pass the device, not the mngr ?
    """ Performs the "commit" operation using the specified ncclient connection. """
    rpc_reply = device.mngr.commit()
    helper.printRpc(rpc_reply, "Commit changes", device.hostname)
    return(rpc_reply)

def discardChanges(device):
    # TODO: pass the device, not the mngr ?
    """ Performs the "discard-changes" operation using the specified ncclient connection. """
    rpc_reply = device.mngr.discard_changes()
    helper.printRpc(rpc_reply, "Discard changes", device.hostname)
    return(rpc_reply)

def getNetconfCapabilities(device):
    # TODO: pass the device, not the mngr ?
    """ Retrieves the capabilities of the specified ncclient connection. """
    capabilities = device.mngr.server_capabilities
    return(capabilities)

 