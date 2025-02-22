from lxml import etree as ET
from datetime import datetime
from signals import signal_manager

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTreeWidgetItem

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

    if element.tag.startswith('{'):  # If the tag has a namespace
        element.tag = element.tag.split('}', 1)[-1]  # Remove namespace from the tag
        # Recursively apply to child elements
        for child in element:
            removeXmlns(child)

def convertToEtree(rpc_reply, device_type, strip_namespaces=True):
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
    if strip_namespaces:
        removeXmlns(rpc_reply_etree) # Strip all XML Namespace declarations for easier parsing

    return(rpc_reply_etree) # returns the root node (https://lxml.de/apidoc/lxml.etree.html#lxml.etree.fromstring)

def prettyXml(input):
    """
    Converts an XML input into a pretty-printed XML string.
    
    Args:
        input (str or bytes): The XML input to be pretty-printed. It can be a string or bytes.
    
    Returns:
        str: A pretty-printed XML string.
    """

    string = str(input)
    try:
        xml_parser = ET.XMLParser(remove_blank_text=True)
        bytes_utf8 = bytes(string, 'utf8')
        xml_etree = ET.fromstring(bytes_utf8, xml_parser)
        xml_pretty = ET.tostring(xml_etree, pretty_print=True).decode()
    except ET.XMLSyntaxError:
        xml_pretty = input
        raise ValueError("Invalid XML input.")

    return (xml_pretty)

def printRpc(rpc_reply, action, device: object):
    """
    Prints the RPC reply in a formatted manner along with a timestamp, action, and device information.
    
    Args:
        rpc_reply (str): The RPC reply to be printed.
        action (str): The action associated with the RPC reply.
        device (Device): The device from which the RPC reply was received.
    """

    try:
        id = device.id
    except:
        id = "N/A"

    try:
        hostname = device.hostname
    except:
        hostname = "N/A"


    timestamp = datetime.now().strftime("%H:%M:%S")
    rpc_reply_pretty = prettyXml(rpc_reply)
    message = (
        f"{timestamp}\n"
        f"RPC reply for action: \"{action}\" on device with ID: {id} (Hostname: {hostname})\n"
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

def addPendingChange(device, pending_change_name, rpc_reply=None, filter=None):
    """
    This function marks the device as having pending changes and emits a signal
    to notify that a pending change has been added. The signal is then used to add the pending change to the PendingChangesWidget.
    
    Args:
        device (Device): The device object to which the pending change is to be added.
        pending_change (Any): The pending change to be added to the device.
    """

    signal_manager.pendingChangeAdded.emit(device.id, pending_change_name, prettyXml(rpc_reply), prettyXml(filter))
    device.has_pending_changes = True

def getBgColorFromFlag(flag):
    if flag == "commited":
        return "white"
    elif flag == "uncommited":
        return "yellow"
    elif flag == "deleted":
        return "red"

def getTooltipFromFlag(flag):
    if flag == "commited":
        return ""
    elif flag == "uncommited":
        return "This device has some IP addresses in the candidate datastore, which are not yet active. The changes will be put into effect after commit."
    elif flag == "deleted":
        return "This device has some IP addresses set for deletion. The deletion will be put into effect after commit."
    
def populateTreeWidget(tree_widget, xml_root):
        """
        Populates the QTreeWidget with items from the given XML root.
        This method clears the current items in the tree widget and 
        adds new items based on the provided XML root element.
        Args:
            xml_root: The root element of the XML structure containing the data to populate the tree widget.
        """

        tree_widget.clear()
        if xml_root is not None:
            addTreeItems(tree_widget.invisibleRootItem(), xml_root)
        else:
            tree_widget.setHeaderLabels(["No data found!"])

def addTreeItems(parent, element):
    """
    Recursively adds tree items to a QTreeWidget.
    Args:
        parent (QTreeWidgetItem): The parent tree widget item to which new items will be added.
        element (Element): The XML element whose data will be used to create tree items.
    """

    item = QTreeWidgetItem(parent, [element.tag])
    for key, value in element.attrib.items():
        QTreeWidgetItem(item, [f"{key}: {value}"])
    for child in element:
        addTreeItems(item, child)
    if element.text and element.text.strip():
        QTreeWidgetItem(item, [element.text.strip()])