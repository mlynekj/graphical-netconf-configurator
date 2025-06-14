# ---------- IMPORTS: ----------
# Standard library
import os
from lxml import etree as ET
import ipaddress

# Custom modules
import utils
from yang.filters import EditconfigFilter, DispatchFilter
from definitions import ROOT_DIR, SECURITY_YANG_DIR, CONFIGURATION_TARGET_DATASTORE

# QT
from PySide6.QtWidgets import (
    QLineEdit, 
    QGraphicsRectItem, 
    QGraphicsTextItem,
    QGridLayout,
    QDialogButtonBox,
    QDialog,
    QLabel,
    QMessageBox,
    QGraphicsScene)
from PySide6.QtGui import QPixmap, QColor, QFont, QIcon
from PySide6.QtCore import Qt, QPointF

# QtCreator
from ui.ui_ipsecdialog import Ui_IPSECDialog

# ---------- OPERATIONS: ----------
def configureIPSecWithNetconf(device, dev_parameters, ike_parameters, ipsec_parameters) -> tuple:
    """
    Configures IPSec on a network device using NETCONF.
    It generates the appropriate configuration filter based on
    the device type, and applies the configuration using NETCONF.
    Args:
        device: An object representing the network device, which includes
                device parameters and a NETCONF manager instance.
        dev_parameters (dict): A dictionary containing device-specific parameters,
                               such as interface names and other configuration details.
        ike_parameters (dict): A dictionary containing IKE (Internet Key Exchange)
                               configuration parameters.
        ipsec_parameters (dict): A dictionary containing IPSec configuration parameters.
    Returns:
        tuple: A tuple containing:
            - rpc_reply: The NETCONF RPC reply object after applying the configuration.
            - filter: The configuration filter used for the NETCONF operation.
    Notes:
        - For Junos devices, a reminder is displayed to verify that the interfaces
          are assigned to the correct security zones (e.g., "trust" and "untrust").
          This couldn't be automated, because it could break other configurations.
    """

    if device.device_parameters["device_params"] == "junos":
        # Create the filter
        filter = JunosConf_Editconfig_ConfigureIPSec_Filter(dev_parameters, ike_parameters, ipsec_parameters)   
        print(filter)

        # RPC                
        rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)

        # Show reminder to check the security zones
        message = (
            "Make sure that the interfaces are assigned to the correct security zones.\n"
            f"{dev_parameters['LAN_interface']} -> LAN interface (e.g. \"trust\")\n"
            f"{dev_parameters['WAN_interface']} -> WAN interface (e.g \"untrust\")"
        )
        QMessageBox.information(None, f"Warning: Check security zones on device {device.hostname}", message)

        return(rpc_reply, filter)
    
    elif device.device_parameters["device_params"] == "iosxe":
        # Create the filter
        filter = CiscoIOSXENative_Editconfig_ConfigureIPSec_Filter(dev_parameters, ike_parameters, ipsec_parameters)
        
        # RPC
        rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
        return(rpc_reply, filter)

def getSecurityZonesWithNetconf(device) -> tuple:
    """
    Retrieves security zones from a network device using NETCONF. Currently, used only for Junos (SRX).
    Args:
        device: The network device object that provides a NETCONF manager 
                for executing RPC calls.
    Returns:
        tuple: A tuple containing:
            - rpc_payload: The RPC payload object used for the request.
            - rpc_reply: The RPC reply object containing the response from the device.
    """
    
    rpc_payload = JunosRpcZones_Dispatch_GetZones_Filter()
    rpc_reply = device.mngr.dispatch(rpc_payload.__ele__())
    return (rpc_payload, rpc_reply)

def configureSecurityZoneToInterfaceWithNetconf(device, interface, zone, remove_interface_from_zone=False):
    filter = JunosConfSecurity_EditConfig_ConfigureInterfacesZone_Filter(interface, zone, remove_interface_from_zone)
    rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
    return (rpc_reply, filter)


# ---------- FILTERS: ----------
class JunosRpcZones_Dispatch_GetZones_Filter(DispatchFilter):
    def __init__(self) -> None:
        self.filter_xml = ET.parse(SECURITY_YANG_DIR + "junos-rpc-zones_dispatch_get-zones.xml")


class CiscoIOSXENative_Editconfig_ConfigureIPSec_Filter(EditconfigFilter):
    def __init__(self, dev_parameters: dict, ike_parameters: dict, ipsec_parameters: dict) -> None:  
        # Load the XML filter template
        self.filter_xml = ET.parse(SECURITY_YANG_DIR + "Cisco-IOS-XE-native_edit-config_configure-ipsec.xml")
        self.namespaces = {'native': 'http://cisco.com/ns/yang/Cisco-IOS-XE-native',
                           "acl": "http://cisco.com/ns/yang/Cisco-IOS-XE-acl",
                           "crypto": "http://cisco.com/ns/yang/Cisco-IOS-XE-crypto"
                           }
        
        self._createAccessListFilter(dev_parameters)
        self._createTransformSetFilter(ipsec_parameters)
        self._createIsakmpFilter(ike_parameters, dev_parameters)
        self._createCryptoMapFilter(dev_parameters)
        self._applyCryptoMapToInteface(dev_parameters)

    def _createAccessListFilter(self, dev_parameters) -> None:
        # Store the values for later use
        self.access_list_values = {
            "name": dev_parameters["cisco_specific"]["acl_number"],
            "sequence": "10", # hardcoded - only one rule in the ACL
            "source_network": dev_parameters["local_private_network"],
            "destination_network": dev_parameters["remote_private_network"],
        }
        
        # Create the filter
        extended_acl_element = self.filter_xml.find(".//native:ip/native:access-list/acl:extended", self.namespaces)
        extended_acl_element.find(".//acl:name", self.namespaces).text = str(self.access_list_values["name"])
        extended_acl_element.find(".//acl:sequence", self.namespaces).text = str(self.access_list_values["sequence"])
        extended_acl_element.find(".//acl:ace-rule/acl:ipv4-address", self.namespaces).text = str(self.access_list_values["source_network"].network_address)
        extended_acl_element.find(".//acl:ace-rule/acl:mask", self.namespaces).text = str(self.access_list_values["source_network"].hostmask)
        extended_acl_element.find(".//acl:ace-rule/acl:dest-ipv4-address", self.namespaces).text = str(self.access_list_values["destination_network"].network_address)
        extended_acl_element.find(".//acl:ace-rule/acl:dest-mask", self.namespaces).text = str(self.access_list_values["destination_network"].hostmask)

    def _createTransformSetFilter(self, ipsec_parameters) -> None:
        # Preprocessing
        esp_hmac = f"esp-{ipsec_parameters["authentication"]}" # Set the IPSec authentication element (ESP-HMAC)
        if ipsec_parameters["encryption"] == "3des": # Set the IPSec encryption element (ESP-AES + length in bits, or ESP-3DES)
            esp = "esp-3des"
        elif "aes" in str(ipsec_parameters["encryption"]):
            esp = "esp-aes"
        key_bit = ipsec_parameters["encryption"].split("-")[1] if len(ipsec_parameters["encryption"].split("-")) == 2 else None
        tag = f"{ipsec_parameters['authentication']}_{ipsec_parameters['encryption']}".replace("-", "_") # Create name of the transform-set based on the authentication and encryption algorithms

        # Store the values for later use
        self.transform_set_values = {
            "tag": tag,
            "esp": esp,
            "key_bit": key_bit if key_bit else None,
            "esp_hmac": esp_hmac,
            "lifetime": ipsec_parameters["lifetime"]
        }
        
        # Create the filter
        ipsec_element = self.filter_xml.find(".//crypto:ipsec", self.namespaces)
        ipsec_element.find(".//crypto:transform-set/crypto:tag", self.namespaces).text = str(self.transform_set_values["tag"])
        ipsec_element.find(".//crypto:transform-set/crypto:esp", self.namespaces).text = str(self.transform_set_values["esp"])
        ipsec_element.find(".//crypto:transform-set/crypto:esp-hmac", self.namespaces).text = str(self.transform_set_values["esp_hmac"])
        ipsec_element.find(".//crypto:seconds", self.namespaces).text = str(self.transform_set_values["lifetime"])
        transform_set_element = ipsec_element.find(".//crypto:transform-set", self.namespaces)
        if self.transform_set_values["key_bit"]: # If the encryption is AES - set the length in bits in a child element
            key_bit_element = ET.SubElement(transform_set_element, "key-bit")
            key_bit_element.text = self.transform_set_values["key_bit"]

    def _createIsakmpFilter(self, ike_parameters, dev_parameters) -> None:
        # Preprocessing
        key = ike_parameters["psk"] #Pre-shared key element
        address = dev_parameters["remote_peer_ip"] #Remote peer element
        policy_number = dev_parameters["cisco_specific"]["isakmp_policy_number"] # ISAKMP policy number element
        if ike_parameters["encryption"] == "3des": # Encryption elements
            encryption = "a3des"
        elif ike_parameters["encryption"].startswith("aes"):
            encryption = "aes"
        key_bit = ike_parameters["encryption"].split("-")[1] if len(ike_parameters["encryption"].split("-")) == 2 else ""
        dh_group = str(ike_parameters["dh"]).replace("group", "") # "group5" -> "5"

        # Store the values for later use
        isakmp_values = {
            "key": key,
            "address": address,
            "policy_number": policy_number,
            "encryption": encryption,
            "key_bit": key_bit if key_bit else None,
            "hash": ike_parameters["authentication"],
            "dh_group": dh_group,
            "lifetime": ike_parameters["lifetime"]
        }
        
        # Create the filter
        isakmp_element = self.filter_xml.find(".//crypto:isakmp", self.namespaces)
        isakmp_element.find(".//crypto:key/crypto:key-address/crypto:key", self.namespaces).text = str(isakmp_values["key"])
        isakmp_element.find(".//crypto:key/crypto:key-address/crypto:addr4-container/crypto:address", self.namespaces).text = str(isakmp_values["address"])
        isakmp_element.find(".//crypto:policy/crypto:number", self.namespaces).text = str(isakmp_values["policy_number"])
        isakmp_element.find(".//crypto:policy/crypto:group", self.namespaces).text = str(isakmp_values["dh_group"])
        isakmp_element.find(".//crypto:policy/crypto:hash", self.namespaces).text = str(isakmp_values["hash"])
        isakmp_element.find(".//crypto:policy/crypto:lifetime", self.namespaces).text = str(isakmp_values["lifetime"])
        
        encryption_element = isakmp_element.find(".//crypto:policy/crypto:encryption", self.namespaces)
        encryption_type_element = ET.SubElement(encryption_element, isakmp_values["encryption"]) 
        if isakmp_values["encryption"] == "aes": # If the encryption is AES - set the length in bits in a child element
            key_bit_element = ET.SubElement(encryption_type_element, "key")
            key_bit_element.text = isakmp_values["key_bit"]
    
    def _createCryptoMapFilter(self, dev_parameters) -> None:
        # Preprocessing
        crypto_map_sequence = dev_parameters["cisco_specific"]["crypto_map_sequence"] # Crypto map sequence number element

        # Store the values for later use
        self.crypto_map_values = {
            "name": "netconf_cm",
            "sequence": crypto_map_sequence,
            "peer_address": dev_parameters["remote_peer_ip"],
        }
        
        # Create the filter
        crypto_map_element = self.filter_xml.find(".//crypto:map", self.namespaces)
        crypto_map_element.find(".//crypto:map-seq/crypto:map/crypto:name", self.namespaces).text = str(self.crypto_map_values["name"])
        crypto_map_element.find(".//crypto:map-seq/crypto:map/crypto:seq", self.namespaces).text = str(self.crypto_map_values["sequence"])
        crypto_map_element.find(".//crypto:map-seq/crypto:map/crypto:match/crypto:address", self.namespaces).text = str(self.access_list_values["name"])
        crypto_map_element.find(".//crypto:map-seq/crypto:map/crypto:set/crypto:peer/crypto:address", self.namespaces).text = str(self.crypto_map_values["peer_address"])
        crypto_map_element.find(".//crypto:map-seq/crypto:map/crypto:set/crypto:transform-set", self.namespaces).text = str(self.transform_set_values["tag"])
        
    def _applyCryptoMapToInteface(self, dev_parameters) -> None:
        # Split the interface name (e.g. GigabitEthernet1) into type and number (GigabitEthernet, 1)
        interface = dev_parameters["WAN_interface"]
        interface_type = ''.join(filter(str.isalpha, interface))
        interface_number = interface.replace(interface_type, '')

        interface_element = self.filter_xml.find(".//native:native/native:interface", self.namespaces)
        interface_type_element = ET.SubElement(interface_element, interface_type)
        interface_number_element = ET.SubElement(interface_type_element, "name")
        interface_number_element.text = interface_number
        
        crypto_namespace = "http://cisco.com/ns/yang/Cisco-IOS-XE-crypto"
        crypto_element = ET.SubElement(interface_type_element, f"{{{crypto_namespace}}}crypto", nsmap={None: crypto_namespace})
        map_element = ET.SubElement(crypto_element, "map")
        tag_element = ET.SubElement(map_element, "tag")
        tag_element.text = self.crypto_map_values["name"]


class JunosConf_Editconfig_ConfigureIPSec_Filter(EditconfigFilter):
    def __init__(self, dev_parameters: dict, ike_parameters: dict, ipsec_parameters: dict) -> None:
        self.filter_xml = ET.parse(SECURITY_YANG_DIR + "junos-conf_edit-config_configure-ipsec.xml")
        self.namespaces = {"conf": "http://yang.juniper.net/junos"}

        self._createIkeFilter(ike_parameters, dev_parameters)
        self._createIPSecFilter(ipsec_parameters, dev_parameters)
        self._createAddressBooksFilter(dev_parameters)
        self._createPoliciesFilter(dev_parameters)

    def _createIkeFilter(self, ike_parameters, dev_parameters) -> None:
        # Preprocessing
        proposal_name = f"pro_{ike_parameters["dh"]}_{ike_parameters["authentication"]}_{ike_parameters["encryption"]}_{ike_parameters["lifetime"]}"
        policy_name = f"pol_{dev_parameters["remote_peer_ip"]}".replace(".", "_")
        gateway_name = f"gat_{dev_parameters["remote_peer_ip"]}".replace(".", "_")
        encryption = f"{ike_parameters["encryption"]}-cbc"
        if ike_parameters["authentication"] == "sha1":
            authentication = "sha1"
        elif ike_parameters["authentication"] == "sha256":
            authentication = "sha-256"
        elif ike_parameters["authentication"] == "sha384":
            authentication = "sha-384"
        elif ike_parameters["authentication"] == "md5":
            authentication = "md5"

        # Store the values for later use
        self.ike_values = {
            "proposal_name": proposal_name,
            "policy_name": policy_name,
            "gateway_name": gateway_name,
            "authentication": authentication,
            "encryption": encryption,
            "dh": ike_parameters["dh"],
            "lifetime": ike_parameters["lifetime"],
            "psk": ike_parameters["psk"],
            "remote_peer_ip": dev_parameters["remote_peer_ip"],
            "external_interface": dev_parameters["WAN_interface"]
        }

        # Create the filter
        ike_element = self.filter_xml.find(".//conf:ike", self.namespaces)
        # IKE Proposal
        ike_element.find(".//conf:proposal/conf:name", self.namespaces).text = str(self.ike_values["proposal_name"])
        ike_element.find(".//conf:proposal/conf:dh-group", self.namespaces).text = str(self.ike_values["dh"])
        ike_element.find(".//conf:proposal/conf:authentication-algorithm", self.namespaces).text = str(self.ike_values["authentication"])
        ike_element.find(".//conf:proposal/conf:encryption-algorithm", self.namespaces).text = str(self.ike_values["encryption"])
        ike_element.find(".//conf:proposal/conf:lifetime-seconds", self.namespaces).text = str(self.ike_values["lifetime"])
        # IKE Policy
        ike_element.find(".//conf:policy/conf:name", self.namespaces).text = str(self.ike_values["policy_name"])
        ike_element.find(".//conf:policy/conf:proposals", self.namespaces).text = str(self.ike_values["proposal_name"])
        ike_element.find(".//conf:policy/conf:pre-shared-key/conf:ascii-text", self.namespaces).text = str(self.ike_values["psk"])
        # IKE Gateway
        ike_element.find(".//conf:gateway/conf:name", self.namespaces).text = str(self.ike_values["gateway_name"])
        ike_element.find(".//conf:gateway/conf:ike-policy", self.namespaces).text = str(self.ike_values["policy_name"])
        ike_element.find(".//conf:gateway/conf:address", self.namespaces).text = str(self.ike_values["remote_peer_ip"])
        ike_element.find(".//conf:gateway/conf:external-interface", self.namespaces).text = str(self.ike_values["external_interface"])

    def _createIPSecFilter(self, ipsec_parameters, dev_parameters) -> None:
        # Preprocessing
        proposal_name = f"pro_{ipsec_parameters["authentication"]}_{ipsec_parameters["encryption"]}_{ipsec_parameters["lifetime"]}"
        policy_name = f"pol_{dev_parameters["remote_peer_ip"]}".replace(".", "_")
        vpn_name = f"vpn_{dev_parameters["remote_peer_ip"]}".replace(".", "_")
        if ipsec_parameters["authentication"] == "sha-hmac":
            authentication = "hmac-sha1-96"
        elif ipsec_parameters["authentication"] == "sha256-hmac":
            authentication = "hmac-sha-256-128"
        encryption = f"{ipsec_parameters["encryption"]}-cbc"

        # Store the values for later use
        self.ipsec_values = {
            "proposal_name": proposal_name,
            "policy_name": policy_name,
            "vpn_name": vpn_name,
            "authentication": authentication,
            "encryption": encryption,
            "lifetime": ipsec_parameters["lifetime"]
        }

        # Create the filter
        ipsec_element = self.filter_xml.find(".//conf:ipsec", self.namespaces)
        # IPSec Proposal
        ipsec_element.find(".//conf:proposal/conf:name", self.namespaces).text = str(self.ipsec_values["proposal_name"])
        ipsec_element.find(".//conf:proposal/conf:authentication-algorithm", self.namespaces).text = str(self.ipsec_values["authentication"])
        ipsec_element.find(".//conf:proposal/conf:encryption-algorithm", self.namespaces).text = str(self.ipsec_values["encryption"])
        ipsec_element.find(".//conf:proposal/conf:lifetime-seconds", self.namespaces).text = str(self.ipsec_values["lifetime"])
        # IPSec Policy
        ipsec_element.find(".//conf:policy/conf:name", self.namespaces).text = str(self.ipsec_values["policy_name"]) 
        ipsec_element.find(".//conf:policy/conf:proposals", self.namespaces).text = str(self.ipsec_values["proposal_name"])
        # VPN
        ipsec_element.find(".//conf:vpn/conf:name", self.namespaces).text = str(self.ipsec_values["vpn_name"])
        ipsec_element.find(".//conf:vpn/conf:ike/conf:gateway", self.namespaces).text = str(self.ike_values["gateway_name"])
        ipsec_element.find(".//conf:vpn/conf:ike/conf:ipsec-policy", self.namespaces).text = str(self.ipsec_values["policy_name"])

    def _createAddressBooksFilter(self, dev_parameters) -> None:
        # Preprocessing
        trusted_address_name = f"{dev_parameters["local_private_network"]}_local_private_network".replace("/", "_").replace(".", "_")
        untrusted_address_name = f"{dev_parameters["remote_peer_ip"]}s_remote_private_network".replace("/", "_").replace(".", "_")
        
        # Store the values for later use
        self.address_books_values = {
            "trusted_address_name": trusted_address_name,
            "untrusted_address_name": untrusted_address_name
        }

        # Create the filter
        # "Trusted"
        trusted_address_book_element = self.filter_xml.find(".//conf:address-book[conf:name='trusted']", self.namespaces)
        trusted_address_book_element.find(".//conf:address/conf:name", self.namespaces).text = str(self.address_books_values["trusted_address_name"])
        trusted_address_book_element.find(".//conf:address/conf:ip-prefix", self.namespaces).text = str(dev_parameters["local_private_network"])        
        # "Untrusted"
        untrusted_address_book_element = self.filter_xml.find(".//conf:address-book[conf:name='untrusted']", self.namespaces)
        untrusted_address_book_element.find(".//conf:address/conf:name", self.namespaces).text = str(self.address_books_values["untrusted_address_name"])
        untrusted_address_book_element.find(".//conf:address/conf:ip-prefix", self.namespaces).text = str(dev_parameters["remote_private_network"])

    def _createPoliciesFilter(self, dev_parameters) -> None:
        # Preprocessing
        policy_trust_to_untrust_name = f"{dev_parameters["local_peer_ip"]}_to_{dev_parameters["remote_peer_ip"]}_out".replace(".", "_")
        policy_untrust_to_trust_name = f"{dev_parameters["remote_peer_ip"]}_to_{dev_parameters["local_peer_ip"]}_in".replace(".", "_")

        # Store the values for later use
        self.policies_values = {
            "policy_trust_to_untrust_name": policy_trust_to_untrust_name,
            "policy_untrust_to_trust_name": policy_untrust_to_trust_name
        }
        
        # Create the filter
        # "Trust to Untrust"
        policy_trust_to_untrust_element = self.filter_xml.find(".//conf:policies/conf:policy[conf:from-zone-name='trust'][conf:to-zone-name='untrust']", self.namespaces)
        policy_trust_to_untrust_element.find(".//conf:name", self.namespaces).text = str(self.policies_values["policy_trust_to_untrust_name"])
        policy_trust_to_untrust_element.find(".//conf:match/conf:source-address", self.namespaces).text = str(self.address_books_values["trusted_address_name"])
        policy_trust_to_untrust_element.find(".//conf:match/conf:destination-address", self.namespaces).text = str(self.address_books_values["untrusted_address_name"])
        policy_trust_to_untrust_element.find(".//conf:then/conf:permit/conf:tunnel/conf:ipsec-vpn", self.namespaces).text = str(self.ipsec_values["vpn_name"])

        # "Untrust to Trust"
        policy_untrust_to_trust_element = self.filter_xml.find(".//conf:policies/conf:policy[conf:from-zone-name='untrust'][conf:to-zone-name='trust']", self.namespaces)
        policy_untrust_to_trust_element.find(".//conf:name", self.namespaces).text = str(self.policies_values["policy_untrust_to_trust_name"])
        policy_untrust_to_trust_element.find(".//conf:match/conf:source-address", self.namespaces).text = str(self.address_books_values["untrusted_address_name"])
        policy_untrust_to_trust_element.find(".//conf:match/conf:destination-address", self.namespaces).text = str(self.address_books_values["trusted_address_name"])
        policy_untrust_to_trust_element.find(".//conf:then/conf:permit/conf:tunnel/conf:ipsec-vpn", self.namespaces).text = str(self.ipsec_values["vpn_name"])

class JunosConfSecurity_EditConfig_ConfigureInterfacesZone_Filter(EditconfigFilter):
    def __init__(self, interface, zone, remove_interface_from_zone=False) -> None:
        self.filter_xml = ET.parse(SECURITY_YANG_DIR + "junos-conf-security_edit-config_configure-interfaces-zone.xml")
        self.namespaces = {"conf": "http://yang.juniper.net/junos"}

        self._createFilter(interface, zone, remove_interface_from_zone)

    def _createFilter(self, interface, zone, remove_interface_from_zone) -> None:
        security_zone_element = self.filter_xml.find(".//conf:security-zone", self.namespaces)
        security_zone_element.find(".//conf:name", self.namespaces).text = str(zone)
        security_zone_element.find(".//conf:interfaces/conf:name", self.namespaces).text = str(interface)
        if remove_interface_from_zone:
            interface_element = security_zone_element.find(".//conf:interfaces", self.namespaces)
            interface_element.set("operation", "delete")


# ---------- QT: ----------
class IPSECDialog(QDialog):
    """
    IPSECDialog is a dialog for configuring IPSEC settings between two network devices.
    This class provides a graphical interface for selecting interfaces, configuring IKE and IPSEC parameters, 
    and setting advanced options specific to Cisco IOS-XE or Junos devices. It validates user input and 
    initiates the IPSEC configuration process on the selected devices.
    Attributes:
        ui (Ui_IPSECDialog): The user interface object for the dialog.
        ipsec_scene (QGraphicsScene): The graphics scene used to display the IPSEC scheme.
        dev1 (Device): The first network device to configure.
        dev2 (Device): The second network device to configure.
        ipsec_scheme_background (QPixmap): The background image for the IPSEC scheme.
    Methods:
        __init__(devices):
            Initializes the dialog with the given devices and sets up the UI components.
        _fillAdvancedTab():
            Populates the "Advanced" tab with device-specific settings based on the device type.
        _fillIPSECScene():
            Populates the IPSEC graphics scene with device-specific information and labels.
        _dev1_LAN_interface_selected(selected_intf):
            Handles the selection of a LAN interface for the first device and updates related fields.
        _dev2_LAN_interface_selected(selected_intf):
            Handles the selection of a LAN interface for the second device and updates related fields.
        _dev1_WAN_interface_selected(selected_intf):
            Handles the selection of a WAN interface for the first device and updates related fields.
        _dev2_WAN_interface_selected(selected_intf):
            Handles the selection of a WAN interface for the second device and updates related fields.
        _alignToCenter(element_to_center, starting_pos):
            Aligns a graphical element to the center of a specified position.
        _alignToRight(element_to_align, starting_pos):
            Aligns a graphical element to the right of a specified position.
        _okButtonHandler():
            Validates user input, reads configuration parameters, and initiates the IPSEC configuration 
            process on both devices.
    """
            
    def __init__(self, devices) -> None:
        super().__init__()

        self.dev1 = devices[0]
        self.dev2 = devices[1]

        # Set up the UI
        self.ui = Ui_IPSECDialog()
        self.ui.setupUi(self)
        gnc_icon = QPixmap(os.path.join(ROOT_DIR, "graphics/icons/gnc.png"))
        self.setWindowIcon(QIcon(gnc_icon))
        self.ipsec_scene = QGraphicsScene()
        self.ipsec_scheme_background = QPixmap(os.path.join(ROOT_DIR, "graphics/ipsec_scheme.png"))
        self.ipsec_scene.addPixmap(self.ipsec_scheme_background)
        self._fillIPSECScene()
        self._fillAdvancedTab()
        self.ui.graphicsView.setScene(self.ipsec_scene)

        # Connect buttons
        self.ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self._okButtonHandler)
        self.ui.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)

        # Add parameters to the comboboxes
        # IKE/ISAKMP
        self.ui.ike_auth_combobox.addItems(["md5", "sha1", "sha256", "sha384"]) # Supported both by Cisco and Juniper
        self.ui.ike_enc_combobox.addItems(["aes-128", "aes-192", "aes-256", "3des"]) # Supported both by Cisco and Juniper (Juniper: aes-128-cbc, aes-192-cbc, aes-256-cbc, 3des-cbc)
        self.ui.ike_dh_combobox.addItems(["group1", "group2", "group5", "group14", "group19", "group20", "group24"]) # Supported both by Cisco and Juniper (Juniper: group1, group2, group5, group14, group19, group20, group24)
        # IPSEC
        self.ui.ipsec_auth_combobox.addItems(["sha-hmac", "sha256-hmac"]) # Supported both by Cisco and Juniper (Juniper: hmac-sha1-96, hmac-sha256-128)
        self.ui.ipsec_enc_combobox.addItems(["aes-128", "aes-192", "aes-256", "3des"])

    def _fillAdvancedTab(self) -> None:
        """
        Populates the advanced settings tab in the user interface based on the 
        device parameters for two devices (dev1 and dev2).
        Needed for Cisco, to specify numbers of ACL, ISAKMP policy, and crypto map sequence.
        """

        if self.dev1.device_parameters["device_params"] == "junos":
            self.ui.dev1_advanced_groupbox.setTitle(f"{self.dev1.hostname} (Junos)")
            self.dev1_junos_layout = QGridLayout(self.ui.dev1_advanced_groupbox)
            self.dev1_junos_label = QLabel("No advanced settings available for Junos devices.")
            self.dev1_junos_layout.addWidget(self.dev1_junos_label, 0, 0)

        elif self.dev1.device_parameters["device_params"] == "iosxe":
            self.ui.dev1_advanced_groupbox.setTitle(f"{self.dev1.hostname} (IOS-XE)")
            self.dev1_layout = QGridLayout(self.ui.dev1_advanced_groupbox)
            self.dev1_acl_number_label = QLabel("ACL number:")
            self.dev1_acl_number_input = QLineEdit()
            self.dev1_acl_number_input.setPlaceholderText("100")
            self.dev1_acl_number_input.setToolTip("Enter a number in the extended range (100-199).")
            self.dev1_layout.addWidget(self.dev1_acl_number_label, 0, 0)
            self.dev1_layout.addWidget(self.dev1_acl_number_input, 0, 1)

            self.dev1_isakmp_policy_number_label = QLabel("ISAKMP policy number:")
            self.dev1_isakmp_policy_number_input = QLineEdit()
            self.dev1_isakmp_policy_number_input.setPlaceholderText("1")
            self.dev1_layout.addWidget(self.dev1_isakmp_policy_number_label, 1, 0)
            self.dev1_layout.addWidget(self.dev1_isakmp_policy_number_input, 1, 1)

            self.dev1_crypto_map_sequence_label = QLabel("Crypto map sequence number:")
            self.dev1_crypto_map_sequence_input = QLineEdit()
            self.dev1_crypto_map_sequence_input.setPlaceholderText("1")
            self.dev1_layout.addWidget(self.dev1_crypto_map_sequence_label, 2, 0)
            self.dev1_layout.addWidget(self.dev1_crypto_map_sequence_input, 2, 1)

        if self.dev2.device_parameters["device_params"] == "junos":
            self.ui.dev2_advanced_groupbox.setTitle(f"{self.dev2.hostname} (Junos)")
            self.dev2_junos_layout = QGridLayout(self.ui.dev2_advanced_groupbox)
            self.dev2_junos_label = QLabel("No advanced settings available for Junos devices.")
            self.dev2_junos_layout.addWidget(self.dev2_junos_label, 0, 0)

        elif self.dev2.device_parameters["device_params"] == "iosxe":
            self.ui.dev2_advanced_groupbox.setTitle(f"{self.dev2.hostname} (IOS-XE)")
            self.dev2_layout = QGridLayout(self.ui.dev2_advanced_groupbox)
            self.dev2_acl_number_label = QLabel("ACL number:")
            self.dev2_acl_number_input = QLineEdit()
            self.dev2_acl_number_input.setPlaceholderText("100")
            self.dev2_acl_number_input.setToolTip("Enter a number in the extended range (100-199).")
            self.dev2_layout.addWidget(self.dev2_acl_number_label, 0, 0)
            self.dev2_layout.addWidget(self.dev2_acl_number_input, 0, 1)

            self.dev2_isakmp_policy_number_label = QLabel("ISAKMP policy number:")
            self.dev2_isakmp_policy_number_input = QLineEdit()
            self.dev2_isakmp_policy_number_input.setPlaceholderText("1")
            self.dev2_layout.addWidget(self.dev2_isakmp_policy_number_label, 1, 0)
            self.dev2_layout.addWidget(self.dev2_isakmp_policy_number_input, 1, 1)

            self.dev2_crypto_map_sequence_label = QLabel("Crypto map sequence number:")
            self.dev2_crypto_map_sequence_input = QLineEdit()
            self.dev2_crypto_map_sequence_input.setPlaceholderText("1")
            self.dev2_layout.addWidget(self.dev2_crypto_map_sequence_label, 2, 0)
            self.dev2_layout.addWidget(self.dev2_crypto_map_sequence_input, 2, 1)

    def _fillIPSECScene(self) -> None:
        """
        Initializes and populates the IPSEC scene with graphical elements and UI components 
        for two devices (DEVICE1 and DEVICE2). This includes setting up labels, group boxes, 
        combo boxes, and read-only line edits for displaying and selecting device interfaces 
        and network information.
        Notes:
            - The combo boxes for LAN and WAN interfaces are populated with the keys of the 
              `interfaces` dictionary for each device.
            - The LAN and WAN interface combo boxes trigger respective selection handlers 
              when their values change.
            - Read-only line edits are used for displaying LAN network and WAN IP address.
              In the future, this could be editable.
            - Graphical elements are added to the `ipsec_scene` for visualization.
        """

        # DEVICE1
        # Hostname
        self.dev1_label_holder = QGraphicsRectItem()
        self.dev1_label = QGraphicsTextItem()
        self.dev1_label.setFont(QFont('Arial', 10))
        self.dev1_label.setPlainText(str(self.dev1.hostname))
        self.dev1_label_holder.setRect(self.dev1_label.boundingRect())
        self.dev1_label_holder.setBrush(QColor(255, 255, 255))
        self.dev1_label_holder.setPen(Qt.NoPen)
        self.dev1_label_holder.setPos(75, 90)
        self.dev1_label.setParentItem(self.dev1_label_holder)
        self.ipsec_scene.addItem(self.dev1_label_holder)
        # Interfaces tab - groupbox
        self.ui.dev1_groupbox.setTitle(self.dev1.hostname)
        self.ui.dev1_LAN_interface_combobox.addItems(self.dev1.interfaces.keys())
        self.ui.dev1_WAN_interface_combobox.addItems(self.dev1.interfaces.keys())
        self.ui.dev1_LAN_interface_combobox.setCurrentIndex(-1)
        self.ui.dev1_WAN_interface_combobox.setCurrentIndex(-1)
        self.ui.dev1_LAN_interface_combobox.currentTextChanged.connect(lambda selected_intf = self.ui.dev1_LAN_interface_combobox.currentText: self._dev1_LAN_interface_selected(selected_intf))
        self.ui.dev1_WAN_interface_combobox.currentTextChanged.connect(lambda selected_intf = self.ui.dev1_LAN_interface_combobox.currentText: self._dev1_WAN_interface_selected(selected_intf))
        # Labels in the IPSECScene - LAN Network
        self.ui.dev1_LAN_network_lineedit.setReadOnly(True)
        self.dev1_lan_network_label = QGraphicsTextItem()
        self.dev1_lan_network_label.setFont(QFont("Arial", 10))
        self.dev1_lan_network_label.setPos(125, 250)
        self.ipsec_scene.addItem(self.dev1_lan_network_label)
        # Labels in the IPSECScene - LAN Interface
        self.dev1_lan_interface_label = QGraphicsTextItem()
        self.dev1_lan_interface_label.setFont(QFont("Arial", 10))
        self.ipsec_scene.addItem(self.dev1_lan_interface_label)
        # Labels in the IPSECScene - WAN Interface
        self.dev1_wan_interface_label = QGraphicsTextItem()
        self.dev1_wan_interface_label.setFont(QFont("Arial", 10))
        self.dev1_wan_interface_label.setPos(130, 80)
        self.ipsec_scene.addItem(self.dev1_wan_interface_label)
        # Labels in the IPSECScene - WAN IP Address
        self.ui.dev1_WAN_ip_lineedit.setReadOnly(True)
        self.dev1_wan_ip_label = QGraphicsTextItem()
        self.dev1_wan_ip_label.setFont(QFont("Arial", 10))
        self.dev1_wan_ip_label.setPos(130, 100)
        self.ipsec_scene.addItem(self.dev1_wan_ip_label)

        # DEVICE2
        # Hostname
        self.dev2_label_holder = QGraphicsRectItem()
        self.dev2_label = QGraphicsTextItem()
        self.dev2_label.setFont(QFont('Arial', 10))
        self.dev2_label.setPlainText(str(self.dev2.hostname))
        self.dev2_label_holder.setRect(self.dev2_label.boundingRect())
        self.dev2_label_holder.setBrush(QColor(255, 255, 255))
        self.dev2_label_holder.setPen(Qt.NoPen)
        self.dev2_label_holder.setPos(505, 90)
        self.dev2_label.setParentItem(self.dev2_label_holder)
        self.ipsec_scene.addItem(self.dev2_label_holder)
        # Interfaces tab - groupbox
        self.ui.dev2_groupbox.setTitle(self.dev2.hostname)
        self.ui.dev2_LAN_interface_combobox.addItems(self.dev2.interfaces.keys())
        self.ui.dev2_WAN_interface_combobox.addItems(self.dev2.interfaces.keys())
        self.ui.dev2_LAN_interface_combobox.setCurrentIndex(-1)
        self.ui.dev2_WAN_interface_combobox.setCurrentIndex(-1)
        self.ui.dev2_LAN_interface_combobox.currentTextChanged.connect(lambda selected_intf = self.ui.dev2_LAN_interface_combobox.currentText: self._dev2_LAN_interface_selected(selected_intf))
        self.ui.dev2_WAN_interface_combobox.currentTextChanged.connect(lambda selected_intf = self.ui.dev2_LAN_interface_combobox.currentText: self._dev2_WAN_interface_selected(selected_intf))
        # Labels in the IPSECScene - LAN Network
        self.ui.dev2_LAN_network_lineedit.setReadOnly(True)
        self.dev2_lan_network_label = QGraphicsTextItem()
        self.dev2_lan_network_label.setFont(QFont("Arial", 10))
        self.dev2_lan_network_label.setPos(385, 250)
        self.ipsec_scene.addItem(self.dev2_lan_network_label)
        # Labels in the IPSECScene - LAN Interface
        self.dev2_lan_interface_label = QGraphicsTextItem()
        self.dev2_lan_interface_label.setFont(QFont("Arial", 10))
        self.ipsec_scene.addItem(self.dev2_lan_interface_label)
        # Labels in the IPSECScene - WAN Interface
        self.dev2_wan_interface_label = QGraphicsTextItem()
        self.dev2_wan_interface_label.setFont(QFont("Arial", 10))
        self.ipsec_scene.addItem(self.dev2_wan_interface_label)
        # Labels in the IPSECScene - WAN IP Address
        self.ui.dev2_WAN_ip_lineedit.setReadOnly(True)
        self.dev2_wan_ip_label = QGraphicsTextItem()
        self.dev2_wan_ip_label.setFont(QFont("Arial", 10))
        self.ipsec_scene.addItem(self.dev2_wan_ip_label)

    def _dev1_LAN_interface_selected(self, selected_intf) -> None:
        """Handles the selection of a LAN interface for the first device and updates related fields."""

        interface_data = self.dev1.interfaces[selected_intf]
        self.dev1_lan_interface_label.setPlainText(selected_intf)
        self._alignToCenter(self.dev1_lan_interface_label, QPointF(80, 120))
        ipv4_data, ipv6_data = utils.getFirstIPAddressesFromSubinterfaces(interface_data['subinterfaces'])
        if ipv4_data:
            self.ui.dev1_LAN_network_lineedit.setText(str(ipv4_data["value"].network))
            self.dev1_lan_network_label.setPlainText(f"Local network:\n{str(ipv4_data["value"].network)}")
        elif ipv6_data:
            self.ui.dev1_LAN_network_lineedit.setText(str(ipv6_data["value"].network))
            self.dev1_lan_network_label.setPlainText(f"Local network:\n{str(ipv6_data["value"].network)}")
        else:
            self.ui.dev1_LAN_network_lineedit.clear()
            self.dev1_lan_network_label.setPlainText("")

    def _dev2_LAN_interface_selected(self, selected_intf) -> None:
        """Handles the selection of a LAN interface for the second device and updates related fields."""

        interface_data = self.dev2.interfaces[selected_intf]
        self.dev2_lan_interface_label.setPlainText(selected_intf)
        self._alignToCenter(self.dev2_lan_interface_label, QPointF(500, 120))
        ipv4_data, ipv6_data = utils.getFirstIPAddressesFromSubinterfaces(interface_data['subinterfaces'])
        if ipv4_data:
            self.ui.dev2_LAN_network_lineedit.setText(str(ipv4_data["value"].network))
            self.dev2_lan_network_label.setPlainText(f"Local network:\n{str(ipv4_data["value"].network)}")
        elif ipv6_data:
            self.ui.dev2_LAN_network_lineedit.setText(str(ipv6_data["value"].network))
            self.dev2_lan_network_label.setPlainText(f"Local network:\n{str(ipv6_data["value"].network)}")
        else:
            self.ui.dev2_LAN_network_lineedit.clear()
            self.dev2_lan_network_label.setPlainText("")

    def _dev1_WAN_interface_selected(self, selected_intf) -> None:
        """Handles the selection of a WAN interface for the first device and updates related fields."""

        interface_data = self.dev1.interfaces[selected_intf]
        self.dev1_wan_interface_label.setPlainText(selected_intf)
        ipv4_data, ipv6_data = utils.getFirstIPAddressesFromSubinterfaces(interface_data['subinterfaces'])
        if ipv4_data:
            self.ui.dev1_WAN_ip_lineedit.setText(str(ipv4_data["value"].ip))
            self.dev1_wan_ip_label.setPlainText(str(ipv4_data["value"].ip))
        elif ipv6_data:
            self.ui.dev1_WAN_ip_lineedit.setText(str(ipv6_data["value"].ip))
            self.dev1_wan_ip_label.setPlainText(str(ipv6_data["value"].ip))
        else:
            self.ui.dev1_WAN_ip_lineedit.clear()
            self.ui.dev1_WAN_ip_lineedit.setText("")

    def _dev2_WAN_interface_selected(self, selected_intf) -> None:
        """Handles the selection of a WAN interface for the second device and updates related fields."""

        interface_data = self.dev2.interfaces[selected_intf]
        self.dev2_wan_interface_label.setPlainText(selected_intf)
        self._alignToRight(self.dev2_wan_interface_label, QPointF(470, 80))
        ipv4_data, ipv6_data = utils.getFirstIPAddressesFromSubinterfaces(interface_data['subinterfaces'])
        if ipv4_data:
            self.ui.dev2_WAN_ip_lineedit.setText(str(ipv4_data["value"].ip))
            self.dev2_wan_ip_label.setPlainText(str(ipv4_data["value"].ip))
            self._alignToRight(self.dev2_wan_ip_label, QPointF(470, 100))
        elif ipv6_data:
            self.ui.dev2_WAN_ip_lineedit.setText(str(ipv6_data["value"].ip))
            self.dev2_wan_ip_label.setPlainText(str(ipv6_data["value"].ip))
        else:
            self.ui.dev2_WAN_ip_lineedit.clear()
            self.ui.dev2_WAN_ip_lineedit.setText("")

    def _alignToCenter(self, element_to_center, starting_pos) -> None:
        """Aligns a graphical element to the center of a specified position."""

        elements_bounding_rect = element_to_center.boundingRect().width()
        element_to_center.setPos(starting_pos.x() - elements_bounding_rect / 2, starting_pos.y())

    def _alignToRight(self, element_to_align, starting_pos) -> None:
        """Aligns a graphical element to the right of a specified position."""

        elements_bounding_rect = element_to_align.boundingRect().width()
        element_to_align.setPos(starting_pos.x() - elements_bounding_rect, starting_pos.y())

    def _okButtonHandler(self) -> None:
        """Reads the input fields, validates them and initiates an IPSEC configuration on both devices."""

        # CREATE DICTIONARIES WITH THE VALUES FOR BOTH DEVICES, AND IKE/IPSEC PARAMETERS (WHICH ARE SAME FOR BOTH DEVICES)
        dev1_parameters = {
            "LAN_interface": self.ui.dev1_LAN_interface_combobox.currentText() if self.ui.dev1_LAN_interface_combobox.currentText() else None,
            "WAN_interface": self.ui.dev1_WAN_interface_combobox.currentText() if self.ui.dev1_WAN_interface_combobox.currentText() else None,
            "local_private_network": ipaddress.IPv4Network(self.ui.dev1_LAN_network_lineedit.text()) if self.ui.dev1_LAN_network_lineedit.text() else None,
            "remote_private_network": ipaddress.IPv4Network(self.ui.dev2_LAN_network_lineedit.text()) if self.ui.dev2_LAN_network_lineedit.text() else None,
            "remote_peer_ip": ipaddress.IPv4Address(self.ui.dev2_WAN_ip_lineedit.text()) if self.ui.dev2_WAN_ip_lineedit.text() else None,
            "local_peer_ip": ipaddress.IPv4Address(self.ui.dev1_WAN_ip_lineedit.text()) if self.ui.dev1_WAN_ip_lineedit.text() else None
        }

        dev2_parameters = {
            "LAN_interface": self.ui.dev2_LAN_interface_combobox.currentText() if self.ui.dev2_LAN_interface_combobox.currentText() else None,
            "WAN_interface": self.ui.dev2_WAN_interface_combobox.currentText() if self.ui.dev2_WAN_interface_combobox.currentText() else None,
            "local_private_network": ipaddress.IPv4Network(self.ui.dev2_LAN_network_lineedit.text()) if self.ui.dev2_LAN_network_lineedit.text() else None,
            "remote_private_network": ipaddress.IPv4Network(self.ui.dev1_LAN_network_lineedit.text()) if self.ui.dev1_LAN_network_lineedit.text() else None,
            "remote_peer_ip": ipaddress.IPv4Address(self.ui.dev1_WAN_ip_lineedit.text()) if self.ui.dev1_WAN_ip_lineedit.text() else None,
            "local_peer_ip": ipaddress.IPv4Address(self.ui.dev2_WAN_ip_lineedit.text()) if self.ui.dev2_WAN_ip_lineedit.text() else None
        }

        ike_parameters = {
            "authentication": self.ui.ike_auth_combobox.currentText() if self.ui.ike_auth_combobox.currentText() else None,
            "encryption": self.ui.ike_enc_combobox.currentText() if self.ui.ike_enc_combobox.currentText() else None,
            "dh": self.ui.ike_dh_combobox.currentText() if self.ui.ike_dh_combobox.currentText() else None,
            "lifetime": self.ui.ike_lifetime_input.text() if self.ui.ike_lifetime_input.text() else None,
            "psk": self.ui.ike_psk_input.text() if self.ui.ike_psk_input.text() else None
        }

        ipsec_parameters = {
            "authentication": self.ui.ipsec_auth_combobox.currentText() if self.ui.ipsec_auth_combobox.currentText() else None,
            "encryption": self.ui.ipsec_enc_combobox.currentText() if self.ui.ipsec_enc_combobox.currentText() else None,
            "lifetime": self.ui.ipsec_lifetime_input.text() if self.ui.ipsec_lifetime_input.text() else None
        }

        # Handle the "Advanced" tab for Cisco IOS-XE device1
        if self.dev1.device_parameters["device_params"] == "iosxe":
            dev1_parameters["cisco_specific"] = {
                "acl_number": int(self.dev1_acl_number_input.text()) if self.dev1_acl_number_input.text() else None,
                "isakmp_policy_number": int(self.dev1_isakmp_policy_number_input.text()) if self.dev1_isakmp_policy_number_input.text() else None,
                "crypto_map_sequence": int(self.dev1_crypto_map_sequence_input.text()) if self.dev1_crypto_map_sequence_input.text() else None
            }
            if None in dev1_parameters["cisco_specific"].values():
                QMessageBox.critical(self, "Error", f"Fill in all values in the \"Advanced\" tab for the device {self.dev1.hostname}.")
                return
            if dev1_parameters["cisco_specific"]["acl_number"] not in range(100, 200):
                QMessageBox.critical(self, "Error", "The ACL number must be in the range 100-199.")
                return
        elif self.dev1.device_parameters["device_params"] == "junos":
            pass

        # Handle the "Advanced" tab for Cisco IOS-XE device2
        if self.dev2.device_parameters["device_params"] == "iosxe":
            dev2_parameters["cisco_specific"] = {
                "acl_number": int(self.dev2_acl_number_input.text()) if self.dev2_acl_number_input.text() else None,
                "isakmp_policy_number": int(self.dev2_isakmp_policy_number_input.text()) if self.dev2_isakmp_policy_number_input.text() else None,
                "crypto_map_sequence": int(self.dev2_crypto_map_sequence_input.text()) if self.dev2_crypto_map_sequence_input.text() else None
            }
            if None in dev2_parameters["cisco_specific"].values():
                QMessageBox.critical(self, "Error", f"Fill in all values in the \"Advanced\" tab for the device {self.dev2.hostname}.")
                return
            if dev2_parameters["cisco_specific"]["acl_number"] not in range(100, 200):
                QMessageBox.critical(self, "Error", "The ACL number must be in the range 100-199.")
                return
        elif self.dev2.device_parameters["device_params"] == "junos":
            pass

        # Input validation
        if None in dev1_parameters.values() or None in dev2_parameters.values():
            QMessageBox.critical(self, "Error", "Fill in all fields in the \"Interfaces\" tab.")
            return
        elif None in ike_parameters.values():
            QMessageBox.critical(self, "Error", "Fill in all fields in the \"IKE\" tab.")
            return
        elif None in ipsec_parameters.values():
            QMessageBox.critical(self, "Error", "Fill in all fields in the \"IPSec\" tab.")
            return

        self.dev1.configureIPSec(dev1_parameters, ike_parameters, ipsec_parameters)
        self.dev2.configureIPSec(dev2_parameters, ike_parameters, ipsec_parameters)

        self.accept()