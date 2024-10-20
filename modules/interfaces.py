# YANG Bindings
from modules.yang_models.openconfig_interfaces import openconfig_interfaces

# Other
from pyangbind.lib.serialise import pybindIETFXMLEncoder

# Custom
from modules.netconf import *
from modules.helper import *

ocinterfaces_model = openconfig_interfaces()

def buildGetInterfacesFilter():
    ocinterfaces = ocinterfaces_model.interfaces
    filter = '<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">' + pybindIETFXMLEncoder.serialise(ocinterfaces) + '</filter>'
    return (filter)

def getInterfaces(mngr, device_id):
    cursor = db_handler.connection.cursor()
    cursor.execute("SELECT device_params FROM Device WHERE device_id = ?", (device_id, ))
    device_params = cursor.fetchone()
    
    filter = buildGetInterfacesFilter()
    rpc_reply = mngr.get(filter)

    # Juniper returns <class 'ncclient.xml_.NCElement'> object, while Cisco returns <class 'ncclient.operations.retrieve.GetReply'>
    # Issue: https://github.com/ncclient/ncclient/issues/593
    # After the issue is resolved, this part can be simplified
    if device_params[0] == "iosxe":
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
    
    interface_names = rpc_reply_etree.xpath('//interfaces/interface/name')
    for interface_name in interface_names:
        name = interface_name.text
        admin_status = interface_name.xpath('../state/admin-status')[0].text
        oper_status = interface_name.xpath('../state/oper-status')[0].text
        interface_id = db_handler.insertInterface(db_handler.connection, name, device_id, admin_status, oper_status)

        subinterface_indexes = interface_name.xpath('../subinterfaces/subinterface/index')
        if len(subinterface_indexes) > 0:
            for index in subinterface_indexes:
                subinterface_index = index.text
                if len(index.xpath('../ipv4/addresses/address/state/ip')) > 0:
                    ipv4_address = index.xpath('../ipv4/addresses/address/state/ip')[0].text
                    ipv4_prefix_length = index.xpath('../ipv4/addresses/address/state/prefix-length')[0].text
                    db_handler.insertSubinterface(db_handler.connection, interface_id, subinterface_index, ipv4_address, ipv4_prefix_length)
            
            
            
            
    
