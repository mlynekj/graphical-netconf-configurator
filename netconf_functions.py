# Other
from ncclient import manager
import xml.etree.ElementTree as ET

# Custom
import db_handler

def establishNetconfConnection(device_parameters):
    try:
        mngr = manager.connect(
            host=device_parameters["address"],
            username=device_parameters["username"],
            password=device_parameters["password"],
            device_params={"name": device_parameters["device_params"]},
            hostkey_verify=False
        )
        return mngr
    except Exception as e:
        # TODO: Handle other exceptions
        print(f"Failed to connect to NETCONF server: {e}")
        return None
    
def demolishNetconfConnection(mngr):
    mngr.close_session()
    # TODO: catch exceptions

def getNetconfCapabilities(mngr, device_id):
    capabilities_response = mngr.server_capabilities
    db_handler.insertNetconfCapabilities(db_handler.connection, capabilities_response, device_id)