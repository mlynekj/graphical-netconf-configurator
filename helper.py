from lxml import etree as ET
from datetime import datetime
from signals import signal_manager

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

def showMessageBox(parent, title, message):
    """
    Displays a message box with a given title and message.
    
    Parameters:
        parent (QWidget): The parent widget of the message box.
        title (str): The title of the message box.
        message (str): The message to be displayed in the message box.
    """
    
    info_dialog = QDialog(parent)
    info_dialog.setWindowTitle(title)
    info_layout = QVBoxLayout()
    info_label = QLabel(message)
    info_layout.addWidget(info_label)
    info_button = QPushButton("OK")
    info_button.clicked.connect(info_dialog.accept)
    info_layout.addWidget(info_button)
    info_dialog.setLayout(info_layout)
    info_dialog.exec()

def clearLayout(layout):
    """
    Recursively clears all widgets and layouts from the given layout.
    
    Args:
        layout (QLayout): The layout to be cleared. This can be any type of QLayout, 
                          such as QVBoxLayout, QHBoxLayout, QGridLayout, etc.
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        else:
            sub_layout = item.layout()
            if sub_layout is not None:
                clearLayout(sub_layout)

def removeXmlns(element):
    """
    Removes all namespace declarations from an XML element and its children.

    Args:
        element (xml.etree.ElementTree.Element): The XML element from which to remove namespaces.
    """

    element.tag = element.tag.split('}', 1)[-1]  # Remove namespace from the tag
    # Recursively apply to child elements
    for child in element:
        removeXmlns(child)

def convertToEtree(rpc_reply, device_type):
    """
    Converts the RPC reply to an ElementTree object.

    Parameters:
        rpc_reply (ncclient.xml_.NCElement or ncclient.operations.retrieve.GetReply): The RPC reply object from the network device.
        device_type (str): The type of network device (e.g., "iosxe" or "junos").
    
    Returns:
        xml.etree.ElementTree.Element: The converted ElementTree object.
    
    Notes:
    - For Cisco IOS XE devices, the RPC reply is converted from XML to bytes.
    - For Juniper devices, the RPC reply is converted from NCElement to string to bytes.
    - All XML Namespace declarations are stripped for easier parsing.
    References:
    - Issue: https://github.com/ncclient/ncclient/issues/593
    """

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
    """
    Converts an XML input into a pretty-printed XML string.
    
    Args:
        input (str or bytes): The XML input to be pretty-printed. It can be a string or bytes.
    
    Returns:
        str: A pretty-printed XML string.
    """

    string = str(input)
    bytes_utf8 = bytes(string, 'utf8')
    xml_etree = ET.fromstring(bytes_utf8)
    xml_pretty = ET.tostring(xml_etree, pretty_print=True).decode()
    return (xml_pretty)

def printRpc(rpc_reply, action, device):
    """
    Prints the RPC reply in a formatted manner along with a timestamp, action, and device information.
    
    Args:
        rpc_reply (str): The RPC reply to be printed.
        action (str): The action associated with the RPC reply.
        device (str): The device from which the RPC reply was received.
    """

    timestamp = datetime.now().strftime("%H:%M:%S")
    rpc_reply_pretty = prettyXml(rpc_reply)
    message = (
        f"{timestamp}\n"
        f"RPC reply for action: \"{action}\" on device \"{device}\":\n"
        f"{rpc_reply_pretty}"
    )
    print(message)

def printGeneral(message):
    """
    Prints a message with a timestamp.
    
    Args:
        message (str): The message to be printed.
    """

    timestamp = datetime.now().strftime("%H:%M:%S")
    message = (
        f"{timestamp}\n"
        f"{message}"
    )
    print(message)

def addPendingChange(device, pending_change):
    """
    This function marks the device as having pending changes and emits a signal
    to notify that a pending change has been added.
    
    Args:
        device (Device): The device object to which the pending change is to be added.
        pending_change (Any): The pending change to be added to the device.
    """

    signal_manager.pendingChangeAdded.emit(device.id, pending_change)
    device.has_pending_changes = True
