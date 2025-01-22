from lxml import etree as ET
from datetime import datetime
from signals import signal_manager

def removeXmlns(element):
    """ Removes all namespace declarations from xml """
    element.tag = element.tag.split('}', 1)[-1]  # Remove namespace from the tag
    # Recursively apply to child elements
    for child in element:
        removeXmlns(child)

def convertToEtree(rpc_reply, device_type):
    """ Converts the RPC reply to an ElementTree object. """
    # Juniper returns <class 'ncclient.xml_.NCElement'> object, while Cisco returns <class 'ncclient.operations.retrieve.GetReply'>
    # Issue: https://github.com/ncclient/ncclient/issues/593
    # After the issue is resolved, this part can be simplified
    if device_type == "iosxe":
        # RPC REPLY -> XML -> BYTES
        rpc_reply_xml = rpc_reply.xml
        rpc_reply_bytes = rpc_reply_xml.encode('utf-8')
    elif device_type == "junos":
        # NCElement -> STRING -> BYTES
        rpc_reply_str = str(rpc_reply)
        rpc_reply_bytes = rpc_reply_str.encode('utf-8')

    # BYTES -> ETREE
    rpc_reply_etree = ET.fromstring(rpc_reply_bytes)
    removeXmlns(rpc_reply_etree) # Strip all XML Namespace declarations for easier parsing

    return(rpc_reply_etree)

def prettyXml(input):
    string = str(input)
    bytes_utf8 = bytes(string, 'utf8')
    xml_etree = ET.fromstring(bytes_utf8)
    xml_pretty = ET.tostring(xml_etree, pretty_print=True).decode()
    return (xml_pretty)

def printRpc(rpc_reply, action, device):
    timestamp = datetime.now().strftime("%H:%M:%S")
    rpc_reply_pretty = prettyXml(rpc_reply)
    message = (
        f"{timestamp}\n"
        f"RPC reply for action: \"{action}\" on device \"{device}\":\n"
        f"{rpc_reply}"
    )
    print(message)

def printGeneral(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    message = (
        f"{timestamp}\n"
        f"{message}"
    )
    print(message)

def addPendingChange(device, pending_change):
    signal_manager.pendingChangeAdded.emit(device.id, pending_change)
    device.has_pending_changes = True
