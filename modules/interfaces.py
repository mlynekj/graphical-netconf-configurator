# YANG Bindings
from modules.yang_models.openconfig_interfaces import openconfig_interfaces

# Other
from pyangbind.lib.serialise import pybindIETFXMLEncoder
from ipaddress import IPv4Address, IPv6Address, IPv4Interface, IPv6Interface

# Custom
from modules.netconf import *
from modules.helper import *

def buildGetInterfacesFilter():
    # TODO: Clean up naming
    ocinterfaces_model = openconfig_interfaces()
    ocinterfaces = ocinterfaces_model.interfaces
    filter = '<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">' + pybindIETFXMLEncoder.serialise(ocinterfaces) + '</filter>'
    del ocinterfaces_model
    return (filter)

def buildGetSubinterfacesFilter(interface_name):
    """
    format:
    <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><interfaces xmlns="http://openconfig.net/yang/interfaces">
        <interface>
            <name>GI1</name>
        </interface>
    </interfaces>
    </filter>
    """

    # TODO: Clean up naming (this doesnt get subinterfaces, but rather a specific interface)
    ocinterfaces_model = openconfig_interfaces()
    ocinterfaces = ocinterfaces_model.interfaces
    ocinterfaces.interface.add(interface_name)
    
    filter = '<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">' + pybindIETFXMLEncoder.serialise(ocinterfaces) + '</filter>'
    del ocinterfaces_model
    return(filter)

def buildEditSubinterfaceFilter(interface_name, subinterface_index, ip, delete_ip=False):
    ocinterfaces_model = openconfig_interfaces()
    ocinterfaces = ocinterfaces_model.interfaces
    
    interface = ocinterfaces.interface.add(interface_name)
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

    edit_config_filter = '<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">' + pybindIETFXMLEncoder.serialise(ocinterfaces) + '</config>'
    del ocinterfaces_model

    if delete_ip:
        root = ET.fromstring(edit_config_filter)
        namespaces = {
            'oc-intf': 'http://openconfig.net/yang/interfaces',
            'oc-ip': 'http://openconfig.net/yang/interfaces/ip'
        }
        address_element = root.find('.//oc-ip:address', namespaces)
        address_element.set("operation", "delete")
        return(ET.tostring(root).decode('utf-8'))
    else:
        return(edit_config_filter)


def getInterfaces(mngr, device_id, getIPs=False):
    cursor = db_handler.connection.cursor()
    cursor.execute("SELECT device_params FROM Device WHERE device_id = ?", (device_id, ))
    device_params = cursor.fetchone()
    
    filter = buildGetInterfacesFilter()
    rpc_reply = mngr.get(filter)

    # Juniper returns <class 'ncclient.xml_.NCElement'> object, while Cisco returns <class 'ncclient.operations.retrieve.GetReply'>
    # Issue: https://github.com/ncclient/ncclient/issues/593
    # After the issue is resolved, this part can be simplified
    if device_params[0] == "iosxe": # TODO: maybe this can be donw without db
        # RPC REPLY -> XML -> BYTES
        rpc_reply_xml = rpc_reply.xml
        rpc_reply_bytes = rpc_reply_xml.encode('utf-8')
    elif device_params[0] == "junos":
        # NCElement -> STRING -> BYTES
        rpc_reply_str = str(rpc_reply)
        rpc_reply_bytes = rpc_reply_str.encode('utf-8')

    # BYTES -> ETREE
    rpc_reply_etree = ET.fromstring(rpc_reply_bytes)
    removeXmlns(rpc_reply_etree)
    
    interfaces = []
    interface_names = rpc_reply_etree.xpath('//interfaces/interface/name')
    
    if getIPs:
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
        for interface_name in interface_names:
            name = interface_name.text
            admin_status = interface_name.xpath('../state/admin-status')[0].text
            oper_status = interface_name.xpath('../state/oper-status')[0].text

            interfaces.append((name, admin_status, oper_status))
            
            #interface_id = db_handler.insertInterface(db_handler.connection, name, device_id, admin_status, oper_status) # do i need this? TODO: check
        
    """
    return format: # TODO: update this (after implmenting ipaddress library)
    interfaces = (name, admin_status, oper_status)
    [('ge-0/0/0', 'UP', 'UP'), ('ge-0/0/1', 'UP', 'UP'), ('ge-0/0/2', 'UP', 'UP')]
    """
    return(interfaces)

def getSubinterfaces(mngr, device_id, interface_name):
    cursor = db_handler.connection.cursor()
    cursor.execute("SELECT device_params FROM Device WHERE device_id = ?", (device_id, ))
    device_params = cursor.fetchone() # TODO: maybe this can be done without db
    
    filter = buildGetSubinterfacesFilter(interface_name)
    rpc_reply = mngr.get(filter)

    # Juniper returns <class 'ncclient.xml_.NCElement'> object, while Cisco returns <class 'ncclient.operations.retrieve.GetReply'>
    # Issue: https://github.com/ncclient/ncclient/issues/593
    # After the issue is resolved, this part can be simplified
    if device_params[0] == "iosxe": # TODO: maybe this can be done without db
        # RPC REPLY -> XML -> BYTES
        rpc_reply_xml = rpc_reply.xml
        rpc_reply_bytes = rpc_reply_xml.encode('utf-8')
    elif device_params[0] == "junos":
        # NCElement -> STRING -> BYTES
        rpc_reply_str = str(rpc_reply)
        rpc_reply_bytes = rpc_reply_str.encode('utf-8')

    # BYTES -> ETREE
    rpc_reply_etree = ET.fromstring(rpc_reply_bytes)
    removeXmlns(rpc_reply_etree)

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
        
        subinterfaces.append({
            "subinterface_index": subinterface_index,
            "ipv4": ipv4_data,
            "ipv6": ipv6_data
        })

    """
    return format: # TODO: update this (after implmenting ipaddress library)
    [{'subinterface_index': '16384', 'ipv4': [('127.0.0.1', '32')], 'ipv6': []}, {'subinterface_index': '16385', 'ipv4': [], 'ipv6': []}]
    """
    return(subinterfaces)

def deleteIp(mngr, device_id, interface_name, subinterface_index, old_ip=None, new_ip=None):  
    delete_filter = buildEditSubinterfaceFilter(interface_name, subinterface_index, old_ip, delete_ip=True)
    rpc_reply = mngr.edit_config(delete_filter, target='running')
    return(rpc_reply)

def setIp(mngr, device_id, interface_name, subinterface_index, old_ip=None, new_ip=None):   
    config_filter = buildEditSubinterfaceFilter(interface_name, subinterface_index, new_ip)
    rpc_reply = mngr.edit_config(config_filter, target='running')
    return(rpc_reply)
            
            
    
