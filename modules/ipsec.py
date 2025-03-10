from ui.ui_ipsecdialog import Ui_IPSECDialog

import utils

# QT
from PySide6.QtWidgets import (
    QGraphicsPixmapItem, 
    QGraphicsItem,
    QGraphicsLineItem,
    QLineEdit, 
    QGraphicsRectItem, 
    QGraphicsSceneMouseEvent,
    QGraphicsProxyWidget,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QWidget,
    QGraphicsTextItem,
    QToolTip,
    QPushButton,
    QVBoxLayout,
    QDialogButtonBox,
    QComboBox,
    QDialog,
    QVBoxLayout,
    QMessageBox,
    QTreeWidgetItem)
from PySide6.QtGui import (
    QImage, 
    QPixmap,
    QPen,
    QColor,
    QAction,
    QFont,
    QIcon,
    QAction)
from PySide6.QtCore import (
    Qt,
    QLineF,
    QPointF,
    QPoint,
    QSize,
    QTimer)

from PySide6.QtWidgets import QDialog, QGraphicsScene, QGraphicsPixmapItem, QGraphicsLineItem, QGraphicsEllipseItem
from PySide6.QtGui import QPixmap, QPen, QColor

from lxml import etree as ET
from definitions import SECURITY_YANG_DIR, CONFIGURATION_TARGET_DATASTORE

from yang.filters import EditconfigFilter


import ipaddress

# ---------- OPERATIONS: ----------
def configureIPSecWithNetconf(device, dev_parameters, ike_parameters, ipsec_parameters):
    if device.device_parameters["device_params"] == "junos":
        # Create the filter
        raise NotImplementedError("Junos is not supported for IPSec configuration.")
        filter = ""    
        
        # RPC                
        rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
        return(rpc_reply, filter)
    
    elif device.device_parameters["device_params"] == "iosxe":
        # Create the filter
        filter = CiscoIOSXENative_Editconfig_ConfigureIPSec_Filter(dev_parameters, ike_parameters, ipsec_parameters)
        
        # RPC                
        #rpc_reply = device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE)
        rpc_reply = ""
        return(rpc_reply, filter)


# ---------- FILTERS: ----------
class CiscoIOSXENative_Editconfig_ConfigureIPSec_Filter(EditconfigFilter):
    def __init__(self, dev_parameters: dict, ike_parameters: dict, ipsec_parameters: dict):  
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

    def _createAccessListFilter(self, dev_parameters):
        # Store the values for later use
        self.access_list_values = {
            "name": "100", # TODO: add an user input field in the advanced tab
            "sequence": "10",
            "source_network": dev_parameters["local_private_network"],
            "destination_network": dev_parameters["remote_private_network"],
        }
        
        # Create the filter
        extended_acl_element = self.filter_xml.find(".//native:ip/native:access-list/acl:extended", self.namespaces)
        extended_acl_element.find(".//acl:name", self.namespaces).text = self.access_list_values["name"]
        extended_acl_element.find(".//acl:sequence", self.namespaces).text = self.access_list_values["sequence"]
        extended_acl_element.find(".//acl:ace-rule/acl:ipv4-address", self.namespaces).text = str(self.access_list_values["source_network"].network_address)
        extended_acl_element.find(".//acl:ace-rule/acl:mask", self.namespaces).text = str(self.access_list_values["source_network"].hostmask)
        extended_acl_element.find(".//acl:ace-rule/acl:dest-ipv4-address", self.namespaces).text = str(self.access_list_values["destination_network"].network_address)
        extended_acl_element.find(".//acl:ace-rule/acl:dest-mask", self.namespaces).text = str(self.access_list_values["destination_network"].hostmask)

    def _createTransformSetFilter(self, ipsec_parameters):
        # Preprocessing
        esp_hmac_element = f"esp-{ipsec_parameters["authentication"]}" # Set the IPSec authentication element (ESP-HMAC)
        if ipsec_parameters["encryption"] == "3des": # Set the IPSec encryption element (ESP-AES + length in bits, or ESP-3DES)
            esp_element = "esp-3des"
        elif ipsec_parameters["encryption"].startswith("aes"):
            esp_element = "esp-aes"
            key_bit_element = ipsec_parameters["encryption"].split("-")[1] if len(ipsec_parameters["encryption"].split()) == 2 else None
        tag_element = f"{ipsec_parameters['authentication']}_{ipsec_parameters['encryption']}" # Create name of the transform-set based on the authentication and encryption algorithms

        # Store the values for later use
        self.transform_set_values = {
            "tag": tag_element,
            "esp": esp_element,
            "key_bit": key_bit_element,
            "esp_hmac": esp_hmac_element,
            "lifetime": ipsec_parameters["lifetime"]
        }
        
        # Create the filter
        ipsec_element = self.filter_xml.find(".//crypto:ipsec", self.namespaces)
        ipsec_element.find(".//crypto:transform-set/crypto:tag", self.namespaces).text = self.transform_set_values["tag"]
        ipsec_element.find(".//crypto:transform-set/crypto:esp", self.namespaces).text = self.transform_set_values["esp"]
        ipsec_element.find(".//crypto:transform-set/crypto:esp-hmac", self.namespaces).text = self.transform_set_values["esp_hmac"]
        ipsec_element.find(".//crypto:seconds", self.namespaces).text = self.transform_set_values["lifetime"]
        if self.transform_set_values["key_bit"]: # If the encryption is AES - set the length in bits in a child element
            key_bit_element = ET.SubElement(ipsec_element, "key-bit")
            key_bit_element.text = self.transform_set_values["key_bit"]

    def _createIsakmpFilter(self, ike_parameters, dev_parameters):
        # Preprocessing
        key = ike_parameters["psk"] #Pre-shared key element
        address = dev_parameters["remote_peer_ip"] #Remote peer element
        policy_number = "1" #Policy number # TODO: add an user input field in the advanced tab 
        if ike_parameters["encryption"] == "3des": # Encryption elements
            encryption = "a3des"
        elif ike_parameters["encryption"].startswith("aes"):
            encryption = "aes"
            key_bit = ike_parameters["encryption"].split("-")[1]
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
        isakmp_element.find(".//crypto:key/crypto:key-address/crypto:key", self.namespaces).text = isakmp_values["key"]
        isakmp_element.find(".//crypto:key/crypto:key-address/crypto:addr4-container/crypto:address", self.namespaces).text = str(isakmp_values["address"])
        isakmp_element.find(".//crypto:policy/crypto:number", self.namespaces).text = isakmp_values["policy_number"]
        isakmp_element.find(".//crypto:policy/crypto:group", self.namespaces).text = isakmp_values["dh_group"]
        isakmp_element.find(".//crypto:policy/crypto:hash", self.namespaces).text = isakmp_values["hash"]
        isakmp_element.find(".//crypto:policy/crypto:lifetime", self.namespaces).text = isakmp_values["lifetime"]
        
        encryption_element = isakmp_element.find(".//crypto:policy/crypto:encryption", self.namespaces)
        encryption_type_element = ET.SubElement(encryption_element, isakmp_values["encryption"]) 
        if isakmp_values["encryption"] == "aes": # If the encryption is AES - set the length in bits in a child element
            key_bit_element = ET.SubElement(encryption_type_element, "key")
            key_bit_element.text = isakmp_values["key_bit"]
    
    def _createCryptoMapFilter(self, dev_parameters):
        # Preprocessing
        crypto_map_name = str(dev_parameters["remote_peer_ip"]).replace(".", "_") # Create a crypto map name based on the remote peer IP address
        crypto_map_sequence = 1 # TODO: pridat user input field v advanced tabu

        # Store the values for later use
        self.crypto_map_values = {
            "name": crypto_map_name,
            "sequence": crypto_map_sequence,
            "peer_address": dev_parameters["remote_peer_ip"],
        }
        
        # Create the filter
        crypto_map_element = self.filter_xml.find(".//crypto:map", self.namespaces)
        crypto_map_element.find(".//crypto:map-seq/crypto:map/crypto:name", self.namespaces).text = str(self.crypto_map_values["name"])
        crypto_map_element.find(".//crypto:map-seq/crypto:map/crypto:seq", self.namespaces).text = str(self.crypto_map_values["sequence"])
        crypto_map_element.find(".//crypto:map-seq/crypto:map/crypto:match/crypto:address", self.namespaces).text = self.access_list_values["name"]
        crypto_map_element.find(".//crypto:map-seq/crypto:map/crypto:set/crypto:peer/crypto:address", self.namespaces).text = str(self.crypto_map_values["peer_address"])
        crypto_map_element.find(".//crypto:map-seq/crypto:map/crypto:set/crypto:transform-set", self.namespaces).text = self.transform_set_values["tag"]
        
    def _applyCryptoMapToInteface(self, dev_parameters):
        # Split the interface name (e.g. GigabitEthernet1) into type and number (GigabitEthernet, 1)
        interface = dev_parameters["WAN_interface"]
        interface_type = ''.join(filter(str.isalpha, interface))
        interface_number = interface.replace(interface_type, '')

        interface_element = self.filter_xml.find(".//native:native/native:interface", self.namespaces)
        interface_type_element = ET.SubElement(interface_element, interface_type)
        interface_number_element = ET.SubElement(interface_type_element, "name")
        interface_number_element.text = interface_number
        
        crypto_element = ET.SubElement(interface_type_element, "crypto")
        map_element = ET.SubElement(crypto_element, "map")
        tag_element = ET.SubElement(map_element, "tag")
        tag_element.text = self.crypto_map_values["name"]




# ---------- QT: ----------
class IPSECDialog(QDialog):
    def __init__(self, devices):
        super().__init__()

        self.ui = Ui_IPSECDialog()
        self.ui.setupUi(self)

        self.ipsec_scene = QGraphicsScene()
        self.dev1 = devices[0]
        self.dev2 = devices[1]

        self.ipsec_scheme_background = QPixmap("graphics/ipsec_scheme.png")
        self.ipsec_scene.addPixmap(self.ipsec_scheme_background)

        self._fillIPSECScene()
        self.ui.graphicsView.setScene(self.ipsec_scene)

        self.ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self._okButtonHandler)
        self.ui.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)

        self.ui.ike_auth_combobox.addItems(["md5", "sha1", "sha256", "sha384", "sha512"])
        self.ui.ike_enc_combobox.addItems(["aes-128", "aes-192", "aes-256", "3des"])
        self.ui.ike_dh_combobox.addItems(["group1", "group2", "group5", "group14", "group15", "group16", "group19", "group20", "group21", "group24"])

        self.ui.ipsec_auth_combobox.addItems(["sha-hmac", "sha256-hmac", "sha384-hmac", "sha512-hmac"])
        self.ui.ipsec_enc_combobox.addItems(["aes-128", "aes-192", "aes-256", "3des"])

        self.ui.ike_lifetime_input.setText("3600") # TODO: only for testing purposes
        self.ui.ipsec_lifetime_input.setText("3600") # TODO: only for testing purposes
        self.ui.ike_psk_input.setText("cisco") # TODO: only for testing purposes
        

    def _fillIPSECScene(self):
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

    def _dev1_LAN_interface_selected(self, selected_intf):
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

    def _dev2_LAN_interface_selected(self, selected_intf):
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

    def _dev1_WAN_interface_selected(self, selected_intf):
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

    def _dev2_WAN_interface_selected(self, selected_intf):
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

    def _alignToCenter(self, element_to_center, starting_pos):
        elements_bounding_rect = element_to_center.boundingRect().width()
        element_to_center.setPos(starting_pos.x() - elements_bounding_rect / 2, starting_pos.y())

    def _alignToRight(self, element_to_align, starting_pos):
        elements_bounding_rect = element_to_align.boundingRect().width()
        element_to_align.setPos(starting_pos.x() - elements_bounding_rect, starting_pos.y())

    def _okButtonHandler(self):
        """
        Reads the input fields, validates them and initiates an IPSEC configuration on both devices.
        """

        dev1_parameters = {
            "LAN_interface": self.ui.dev1_LAN_interface_combobox.currentText() if self.ui.dev1_LAN_interface_combobox.currentText() else None,
            "WAN_interface": self.ui.dev1_WAN_interface_combobox.currentText() if self.ui.dev1_WAN_interface_combobox.currentText() else None,
            "local_private_network": ipaddress.IPv4Network(self.ui.dev1_LAN_network_lineedit.text()) if self.ui.dev1_LAN_network_lineedit.text() else None,
            "remote_private_network": ipaddress.IPv4Network(self.ui.dev2_LAN_network_lineedit.text()) if self.ui.dev2_LAN_network_lineedit.text() else None,
            "remote_peer_ip": ipaddress.IPv4Address(self.ui.dev2_WAN_ip_lineedit.text()) if self.ui.dev2_WAN_ip_lineedit.text() else None
        }

        dev2_parameters = {
            "LAN_interface": self.ui.dev2_LAN_interface_combobox.currentText() if self.ui.dev2_LAN_interface_combobox.currentText() else None,
            "WAN_interface": self.ui.dev2_WAN_interface_combobox.currentText() if self.ui.dev2_WAN_interface_combobox.currentText() else None,
            "local_private_network": ipaddress.IPv4Network(self.ui.dev2_LAN_network_lineedit.text()) if self.ui.dev2_LAN_network_lineedit.text() else None,
            "remote_private_network": ipaddress.IPv4Network(self.ui.dev1_LAN_network_lineedit.text()) if self.ui.dev1_LAN_network_lineedit.text() else None,
            "remote_peer_ip": ipaddress.IPv4Address(self.ui.dev1_WAN_ip_lineedit.text()) if self.ui.dev1_WAN_ip_lineedit.text() else None
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