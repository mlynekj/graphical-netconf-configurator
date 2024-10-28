# Other
from ncclient import manager, transport, operations
from ncclient.operations import RaiseMode
from lxml import etree as ET
from PySide6.QtWidgets import QLabel, QMessageBox

# Custom
import db_handler

def establishNetconfConnection(device_parameters):
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

    
def demolishNetconfConnection(mngr):
    mngr.close_session()
    # TODO: catch exceptions

def commitChanges(mngr):
    rpc_reply = mngr.commit()
    return(rpc_reply)

def getNetconfCapabilities(mngr, device_id):
    capabilities_response = mngr.server_capabilities
    db_handler.insertNetconfCapabilities(db_handler.connection, capabilities_response, device_id)
    return(capabilities_response)