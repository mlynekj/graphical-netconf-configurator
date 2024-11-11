# Other
from pyangbind.lib.serialise import pybindIETFXMLEncoder
from ipaddress import IPv4Address, IPv6Address, IPv4Interface, IPv6Interface
from lxml import etree as ET

# Custom
import modules.netconf as netconf
import modules.helper as helper
from definitions import *

CONFIGURATION_TARGET_DATASTORE = 'candidate'

# ---------- FILTERS: ----------
# TODO: predelat asi cele na XML soubory

def createFilter_EditIPAddress(interface, subinterface_index, ip, delete_ip=False):
    """
    Creates a NETCONF filter to edit or delete a subinterface IP address.
    Args:
        interface (str): The name of the interface.
        subinterface_index (int): The index of the subinterface.
        ip (IPv4Interface of IPv6Interface): An IPvXInterface object containing the IP address and network information.
        delete_ip (bool, optional): If True, the IP address will be marked for deletion. Defaults to False.
    Returns (example):
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
            <interfaces xmlns="http://openconfig.net/yang/interfaces">
                <interface>
                    <name>interface</name>
                    <subinterfaces>
                    <subinterface>
                        <index>subinterface_index</index>
                        <ipv4(ipv6) xmlns="http://openconfig.net/yang/interfaces/ip">
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

    filter_xml = ET.parse(OPENCONFIG_XML_DIR + "/interfaces/edit_config-ip_address.xml")
    namespaces = {'ns': 'http://openconfig.net/yang/interfaces',
                  'oc-ip': 'http://openconfig.net/yang/interfaces/ip'}
    
    interface_name_element = filter_xml.find(".//ns:name", namespaces)
    interface_name_element.text = interface

    subinterface_index_element = filter_xml.find(".//ns:index", namespaces)
    subinterface_index_element.text = str(subinterface_index)

    if ip.version == 4:
        ipv4_element = filter_xml.find(".//oc-ip:ipv4", namespaces)
        address_element = ipv4_element.find(".//oc-ip:address", namespaces)
        address_element.set("operation", "delete") if delete_ip else None
        
        ip_elements = address_element.findall(".//oc-ip:ip", namespaces) # The IP address element is stored in TWO places in the XML
        for ip_element in ip_elements:
            ip_element.text = str(ip.ip)
        
        prefix_length_element = address_element.find(".//oc-ip:prefix-length", namespaces)
        prefix_length_element.text = str(ip.network.prefixlen)
    elif ip.version == 6:
        ipv6_element = filter_xml.find(".//oc-ip:ipv6", namespaces)
        address_element = ipv6_element.find(".//oc-ip:address", namespaces)
        address_element.set("operation", "delete") if delete_ip else None
        
        ip_elements = address_element.findall(".//oc-ip:ip", namespaces) # The IP address element is stored in TWO places in the XML
        for ip_element in ip_elements:
            ip_element.text = str(ip.ip)
        
        prefix_length_element = address_element.find(".//oc-ip:prefix-length", namespaces)
        prefix_length_element.text = str(ip.network.prefixlen)

    return(ET.tostring(filter_xml).decode('utf-8'))

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

    # FILTER
    filter_xml = ET.parse(OPENCONFIG_XML_DIR + "/interfaces/get-all_interfaces.xml")
    rpc_filter = ET.tostring(filter_xml).decode('utf-8')

    # RPC
    rpc_reply = device.mngr.get(rpc_filter)
    rpc_reply_etree = helper.convertToEtree(rpc_reply, device_type)

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
    
    # FILTER
    filter_xml = ET.parse(OPENCONFIG_XML_DIR + "/interfaces/get-interface.xml")
    namespaces = {'ns': 'http://openconfig.net/yang/interfaces'}
    interface_name_element = filter_xml.find(".//ns:name", namespaces)
    interface_name_element.text = interface_name
    rpc_filter = ET.tostring(filter_xml).decode('utf-8') 

    # RPC
    rpc_reply = device.mngr.get(rpc_filter)
    rpc_reply_etree = helper.convertToEtree(rpc_reply, device_type)

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
    # FILTER
    filter = createFilter_EditIPAddress(interface_name, subinterface_index, old_ip, delete_ip=True)

    # RPC
    rpc_reply = device.mngr.edit_config(filter, target=CONFIGURATION_TARGET_DATASTORE)
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
    # FILTER
    filter = createFilter_EditIPAddress(interface_name, subinterface_index, new_ip)
    
    # RPC
    rpc_reply = device.mngr.edit_config(filter, target=CONFIGURATION_TARGET_DATASTORE)
    return(rpc_reply)
            
    
