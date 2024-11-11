# Other
from pyangbind.lib.serialise import pybindIETFXMLEncoder
from ipaddress import IPv4Address, IPv6Address, IPv4Interface, IPv6Interface
from lxml import etree as ET

# Custom
import modules.netconf as netconf
import modules.helper as helper

# YANG Bindings
from modules.yang_models.openconfig_interfaces import openconfig_interfaces

TARGET_DATASTORE = 'candidate'

# ---------- FILTERS: ----------
# TODO: predelat asi cele na XML soubory
def createFilter_GetAllInterfaces():
    """
    Creates a NETCONF filter to retrieve all interfaces.
    Returns:
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><interfaces xmlns="http://openconfig.net/yang/interfaces"/>
        </filter>
    """

    ocinterfaces_model = openconfig_interfaces()
    
    ocinterfaces = ocinterfaces_model.interfaces

    filter = '<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">' + pybindIETFXMLEncoder.serialise(ocinterfaces) + '</filter>'
    del ocinterfaces_model
    return (filter)

def createFilter_GetInterface(interface):
    """
    Creates a NETCONF filter to retrieve specific interface.
    Args:
        interface (str): The name of the network interface to be added to the filter.
    Returns:
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><interfaces xmlns="http://openconfig.net/yang/interfaces">
            <interface>
                <name>interface</name>
            </interface>
        </interfaces>
        </filter>
    """

    ocinterfaces_model = openconfig_interfaces()
    
    ocinterfaces = ocinterfaces_model.interfaces
    ocinterfaces.interface.add(interface)
    
    filter = '<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">' + pybindIETFXMLEncoder.serialise(ocinterfaces) + '</filter>'
    del ocinterfaces_model
    return(filter)

def createFilter_EditIPAddress(interface, subinterface_index, ip, delete_ip=False):
    """
    Creates a NETCONF filter to edit or delete a subinterface IP address.
    Args:
        interface (str): The name of the interface.
        subinterface_index (int): The index of the subinterface.
        ip (IPv4Interface of IPv6Interface): An IPvXInterface object containing the IP address and network information.
        delete_ip (bool, optional): If True, the IP address will be marked for deletion. Defaults to False.
    Returns:
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><interfaces xmlns="http://openconfig.net/yang/interfaces">
        <interface>
            <name>interface</name>
            <subinterfaces>
            <subinterface>
                <index>subinterface_index</index>
                <ipv4 xmlns="http://openconfig.net/yang/interfaces/ip">
                <addresses>
                    <address(operation="delete")>
                    <ip>ip.ip</ip>
                    <config>
                        <ip>ip.ip</ip>
                        <prefix-length>ip.network.prefixlen</prefix-length>
                    </config>
                    </address>
                </addresses>
                </ipv4>
            </subinterface>
            </subinterfaces>
        </interface>
        </interfaces>
        </config>
    """

    ocinterfaces_model = openconfig_interfaces()
    
    ocinterfaces = ocinterfaces_model.interfaces
    interface = ocinterfaces.interface.add(interface)
    interface.subinterfaces.subinterface.add(subinterface_index)
    subinterface = interface.subinterfaces.subinterface[subinterface_index]
    if ip.version == 4:
        subinterface.ipv4.addresses.address.add(str(ip.ip)) # Only sets the reference to the address, not the address itself!
        ipv4 = subinterface.ipv4.addresses.address[str(ip.ip)]
        ipv4.config.ip = str(ip.ip)
        ipv4.config.prefix_length = str(ip.network.prefixlen)
    elif ip.version == 6:
        subinterface.ipv6.addresses.address.add(str(ip.ip)) # Only sets the reference to the address, not the address itself!
        ipv6 = subinterface.ipv6.addresses.address[str(ip.ip)] 
        ipv6.config.ip = str(ip.ip)
        ipv6.config.prefix_length = str(ip.network.prefixlen)

    filter = '<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">' + pybindIETFXMLEncoder.serialise(ocinterfaces) + '</config>'
    del ocinterfaces_model

    if delete_ip:
        # If the delete flag is set, add operation="delete" to the address element
        root = ET.fromstring(filter)
        namespaces = {
            'oc-intf': 'http://openconfig.net/yang/interfaces',
            'oc-ip': 'http://openconfig.net/yang/interfaces/ip'
        }
        address_element = root.find('.//oc-ip:address', namespaces)
        address_element.set("operation", "delete")
        return(ET.tostring(root).decode('utf-8'))
    else:
        return(filter)

# ---------- OPERATIONS: ----------
def getInterfaceList(device, getIPs=False):
    """
    Retrieve the list of interfaces from a network device, optionally including IP address information.
    Args:
        device (object): The network device object which contains ncclient manager.
        getIPs (bool, optional): If True, include IP address information for each interface. Defaults to False.
    Returns:
        list: A list of tuples representing the interfaces.

        [(name, admin_status, oper_status, ipv4_data, ipv6_data), ...]
        [('ge-0/0/0', 'UP', 'UP', IPv4Interface('192.168.1.1/24'), IPv6Interface('2001:db8::1/64')), ('ge-0/0/1', 'UP', 'UP', None, None)]
    """
    
    device_type = device.device_parameters['device_params']

    filter = createFilter_GetAllInterfaces()
    rpc_reply = device.mngr.get(filter)

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
    helper.removeXmlns(rpc_reply_etree) # Strip all XML Namespace declarations for easier parsing
    
    interfaces = []
    interface_names = rpc_reply_etree.xpath('//interfaces/interface/name')
    
    if getIPs:
        # If the getIPs flag is set, retrieve the first IP address for each interface (used for ListInterfacesDialog)
        for interface_name in interface_names:
            name = interface_name.text
            admin_status = interface_name.xpath('../state/admin-status')[0].text
            oper_status = interface_name.xpath('../state/oper-status')[0].text

            subinterface_indexes = interface_name.xpath('../subinterfaces/subinterface/index')
            if len(subinterface_indexes) > 0:
                if len(interface_name.xpath('../subinterfaces/subinterface/ipv4/addresses/address/state/ip')) > 0:
                    ipv4_address = interface_name.xpath('../subinterfaces/subinterface/ipv4/addresses/address/state/ip')[0].text
                    ipv4_prefix_length = interface_name.xpath('../subinterfaces/subinterface/ipv4/addresses/address/state/prefix-length')[0].text
                    ipv4_data = IPv4Interface(ipv4_address + '/' + ipv4_prefix_length)
                else:
                    ipv4_data = None

                if len(interface_name.xpath('../subinterfaces/subinterface/ipv6/addresses/address/state/ip')) > 0:
                    ipv6_address = interface_name.xpath('../subinterfaces/subinterface/ipv6/addresses/address/state/ip')[0].text
                    ipv6_prefix_length = interface_name.xpath('../subinterfaces/subinterface/ipv6/addresses/address/state/prefix-length')[0].text
                    ipv6_data = IPv6Interface(ipv6_address + '/' + ipv6_prefix_length)
                else:
                    ipv6_data = None

                interfaces.append((name, admin_status, oper_status, ipv4_data, ipv6_data))
            else:
                interfaces.append((name, admin_status, oper_status, None, None))
    else:
        # If the getIPs flag is not set, retrieve only the interface names
        for interface_name in interface_names:
            name = interface_name.text
            admin_status = interface_name.xpath('../state/admin-status')[0].text
            oper_status = interface_name.xpath('../state/oper-status')[0].text
            interfaces.append(name, admin_status, oper_status)
    return(interfaces)

def getSubinterfaces(device, interface_name):
    """
    Retrieve subinterfaces for a specific interface.
    Args:
        device (object): The network device object which contains ncclient manager.
        interface_name (str): The name of the interface for which details are to be retrieved.
    Returns:
        list: A list of dictionaries, each containing details of a subinterface.

        [{'subinterface_index': '0', 'ipv4': [IPv4Interface('1.1.1.2/24')], 'ipv6': [IPv6Interface('2001::1/64')]}]
    """

    device_type = device.device_parameters['device_params']
    
    filter = createFilter_GetInterface(interface_name)
    rpc_reply = device.mngr.get(filter)

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
    helper.removeXmlns(rpc_reply_etree)

    subinterfaces = []
    for subinterface in rpc_reply_etree.findall('.//interfaces/interface/subinterfaces/subinterface'):
        subinterface_index = subinterface.find('.//index').text

        ipv4_data = []
        for ipv4_object in subinterface.findall('.//ipv4/addresses/address'):
            ipv4_address = ipv4_object.find('state/ip')
            ipv4_prefix_length = ipv4_object.find('state/prefix-length')
            if ipv4_address is not None and ipv4_prefix_length is not None:
                ipv4_data.append((IPv4Interface(ipv4_address.text + '/' + ipv4_prefix_length.text)))

        ipv6_data = []
        for ipv6_object in subinterface.findall('.//ipv6/addresses/address'):
            ipv6_address = ipv6_object.find('state/ip')
            ipv6_prefix_length = ipv6_object.find('state/prefix-length')
            if ipv6_address is not None and ipv6_prefix_length is not None:
                ipv6_data.append((IPv6Interface(ipv6_address.text + '/' + ipv6_prefix_length.text)))
        
        subinterfaces.append({"subinterface_index": subinterface_index, "ipv4": ipv4_data, "ipv6": ipv6_data})
    return(subinterfaces)

def deleteIp(device, interface_name, subinterface_index, old_ip):
    """
    Delete an IP address from a specified interface.
    Args:
        device: The network device object which contains ncclient manager.
        interface_name (str): The name of the interface from which the IP address will be deleted.
        subinterface_index (int): The index of the subinterface.
        old_ip (str): The IP address to be deleted.
    Returns:
        rpc_reply: The response from the device after attempting to delete the IP address.
    """
    
    filter = createFilter_EditIPAddress(interface_name, subinterface_index, old_ip, delete_ip=True)
    rpc_reply = device.mngr.edit_config(filter, target=TARGET_DATASTORE)
    return(rpc_reply)

def setIp(device, interface_name, subinterface_index, new_ip):
    """
    Set an IP address on a specified interface.
    Args:
        device: The network device object which contains ncclient manager.
        interface_name (str): The name of the interface on which the IP address will be added.
        subinterface_index (int): The index of the subinterface.
        old_ip (str): The IP address to be added.
    Returns:
        rpc_reply: The response from the device after attempting to set the IP address.
    """   

    filter = createFilter_EditIPAddress(interface_name, subinterface_index, new_ip)
    rpc_reply = device.mngr.edit_config(filter, target=TARGET_DATASTORE)
    return(rpc_reply)
            
    
