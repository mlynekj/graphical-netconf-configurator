# YANG Bindings
from modules.yang_models.openconfig_interfaces import openconfig_interfaces

# Other
from pyangbind.lib.serialise import pybindIETFXMLEncoder

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
    return (filter)


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
                else:
                    ipv4_address = None
                    ipv4_prefix_length = None

                if len(interface_name.xpath('../subinterfaces/subinterface/ipv6/addresses/address/state/ip')) > 0:
                    ipv6_address = interface_name.xpath('../subinterfaces/subinterface/ipv6/addresses/address/state/ip')[0].text
                    ipv6_prefix_length = interface_name.xpath('../subinterfaces/subinterface/ipv6/addresses/address/state/prefix-length')[0].text
                else:
                    ipv6_address = None
                    ipv6_prefix_length = None

                interfaces.append((name, 
                                   admin_status, 
                                   oper_status, 
                                   ipv4_address, 
                                   ipv4_prefix_length, 
                                   ipv6_address, 
                                   ipv6_prefix_length))
            else:
                interfaces.append((name, admin_status, oper_status, None, None, None, None))
    else:
        for interface_name in interface_names:
            name = interface_name.text
            admin_status = interface_name.xpath('../state/admin-status')[0].text
            oper_status = interface_name.xpath('../state/oper-status')[0].text

            interfaces.append((name, admin_status, oper_status))
            
            #interface_id = db_handler.insertInterface(db_handler.connection, name, device_id, admin_status, oper_status) # do i need this? TODO: check
        
    """
    return format:
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
                ipv4_data.append((ipv4_address.text, ipv4_prefix_length.text))

        ipv6_data = []
        for ipv6_object in subinterface.findall('.//ipv6/addresses/address'):
            ipv6_address = ipv6_object.find('state/ip')
            ipv6_prefix_length = ipv6_object.find('state/prefix-length')
            if ipv6_address is not None and ipv6_prefix_length is not None:
                ipv6_data.append((ipv6_address.text, ipv6_prefix_length.text))
        
        subinterfaces.append({
            "subinterface_index": subinterface_index,
            "ipv4": ipv4_data,
            "ipv6": ipv6_data
        })

    """
    return format:
    [{'subinterface_index': '16384', 'ipv4': [('127.0.0.1', '32')], 'ipv6': []}, {'subinterface_index': '16385', 'ipv4': [], 'ipv6': []}]
    """
    return(subinterfaces)
            
            
            
    
