# Others
from lxml import etree as ET

# Custom
import modules.helper as helper
from definitions import *

def getHostname(device):
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

def setHostname(device, new_hostname):
    """ Sets the device hostname of the specified device to the specified value. """
    device_type = device.device_parameters['device_params']

    # CONFIG
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
    
    # FLAG (needed to update the hostname label on canvas when commiting changes)
    device.has_updated_hostname = True

    # RPC
    rpc_reply = device.mngr.edit_config(target=CONFIGURATION_TARGET_DATASTORE, config=rpc_filter)
    return(rpc_reply)