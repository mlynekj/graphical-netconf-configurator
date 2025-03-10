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

# Custom
import modules.netconf as netconf
import modules.interfaces as interfaces
import modules.system as system
import modules.ospf as ospf
import modules.ipsec as ipsec
import utils as utils
from signals import signal_manager
from definitions import *

# Other
import ipaddress
import traceback

from ui.ui_routingtabledialog import Ui_RoutingTableDialog
from yang.filters import *

from lxml import etree as ET

# ---------- FILTERS: ----------
class JunosRpcRoute_Dispatch_GetRoutingInformation_Filter(DispatchFilter):
    def __init__(self):
        self.filter_xml = ET.parse(ROUTING_YANG_DIR + "junos-rpc-route_dispatch_get-routing-information.xml")
    
    
class IetfRouting_Get_GetRoutingState_Filter(GetFilter):
    def __init__(self):
        self.filter_xml = ET.parse(ROUTING_YANG_DIR + "ietf-routing_get_get-routing-state.xml")



# ---------- DEVICE CLASSES: ----------
class Device(QGraphicsPixmapItem):
    _counter = 0 # Used to generate device IDs
    _registry = {} # Used to store device instances
    _device_type = "D"
    
    def __init__(self, device_parameters, x=0, y=0):
        """
        TODO: document format of device_parameters + other stuff
        """
        super().__init__()

        self.setAcceptHoverEvents(True) # Enable mouse hover over events

        self.device_parameters = device_parameters

        # NETCONF CONNECTION
        self.mngr = netconf.establishNetconfConnection(self.device_parameters) # TODO: Handle timeout, when the device disconnects after some time

        # ICON + CANVAS PLACEMENT
        device_icon_img = QImage("graphics/devices/general.png")
        self.setPixmap(QPixmap.fromImage(device_icon_img))
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setPos(x, y)
        self.setZValue(1)
        
        # CABLES LIST
        self.cables = []
        self.cable_connected_interfaces = []

        # FLAGS
        self.has_pending_changes = False
        self.has_updated_hostname = False

        # ID
        type(self)._counter += 1
        self.id = self._generateID()

        # DEVICE INFORMATION
        self.netconf_capabilities = self._getNetconfCapabilites()
        self.interfaces = self.getInterfaces() # Documented in doc/interfaces_dictionary.md
        self.hostname = self._getHostname()

        # LABEL (Hostname)
        self.label = QGraphicsTextItem(self)
        self.label.setFont(QFont('Arial', 10))
        self.refreshHostnameLabel(self.hostname)

        # TOOLTIP
        self.tooltip_text = (
            f"Device ID: {self.id}\n"
            f"IP: {self.device_parameters['address']}\n"
            f"Device type: {self.device_parameters['device_params']}"
        )
        self.tooltip_timer = QTimer() # shown after 1 second of hovering over the device, at the current mouse position
        self.tooltip_timer.setSingleShot(True) # only once per hover event
        self.tooltip_timer.timeout.connect(lambda: QToolTip.showText(self.hover_pos, self.tooltip_text))

        # REGISTRY
        type(self)._registry[self.id] = self

    def _getNetconfCapabilites(self):
        return(netconf.getNetconfCapabilities(self))

    def refreshHostnameLabel(self, new_hostname=None):
        """
        Refreshes the hostname label of the device.

        Parameters:
        hostname (str, optional): The new hostname to set. If not provided, the hostname will be retrieved using getHostname().
        """

        if new_hostname is not None:
            self.hostname = new_hostname
        else:
            self.hostname = self._getHostname()

        self.label.setPlainText(str(self.hostname))
        self.label_border = self.label.boundingRect()
        self.label.setPos((self.pixmap().width() - self.label_border.width()) / 2, self.pixmap().height())
    
        return(netconf.getNetconfCapabilities(self))

    def _generateID(self):
        return(type(self)._device_type + str(type(self)._counter))

    def _deleteDevice(self):
        rpc_reply = netconf.demolishNetconfConnection(self) # Disconnect from NETCONF server

        self.scene().removeItem(self)
    
        for cable in self.cables.copy(): # cannot modify contents of a list, while iterating through it! => .copy()
            cable.removeCable()

        del type(self)._registry[self.id]
        utils.printRpc(rpc_reply, "Close NETCONF connection", self)
        utils.printGeneral(f"Connection to device: {self.device_parameters['address']} has been closed.")

    def updateCablePositions(self):
        for cable in self.cables:
            cable.updatePosition()    

    def updateCableLabelsText(self):
        for cable in self.cables:
            cable.updateLabelsText()

    # ---------- MOUSE EVENTS FUNCTIONS ---------- 
    def hoverEnterEvent(self, event):
        # Tooltip
        self.tooltip_timer.start(1000)
        self.hover_pos = event.screenPos()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        # Tooltip
        self.tooltip_timer.stop()
        QToolTip.hideText()
        super().hoverLeaveEvent(event)

    def _getContextMenuItems(self):
        items = []

        # Disconnect from device
        disconnect_action = QAction("Disconnect")
        disconnect_action.triggered.connect(self._deleteDevice)
        disconnect_action.setToolTip("Disconnects from the device and removes it from the canvas.")
        items.append(disconnect_action)

        # Show NETCONF capabilites
        show_netconf_capabilities_action = QAction("Show NETCONF Capabilities")
        show_netconf_capabilities_action.triggered.connect(self._showNetconfCapabilitiesDialog)
        show_netconf_capabilities_action.setToolTip("Shows the NETCONF capabilities of the device.")
        items.append(show_netconf_capabilities_action)

        # Show interfaces
        show_interfaces_action = QAction("Edit Interfaces")
        show_interfaces_action.triggered.connect(self._showDeviceInterfacesDialog)
        show_interfaces_action.setToolTip("Shows the configuration dialog for the device interfaces.")
        items.append(show_interfaces_action)

        # Edit Hostname
        edit_hostname_action = QAction("Edit Hostname")
        edit_hostname_action.triggered.connect(self._showHostnameDialog)
        edit_hostname_action.setToolTip("Shows the configuration dialog for the hostname of the device.")
        items.append(edit_hostname_action)

        # Discard all pending changes
        discard_changes_action = QAction("Discard all pending changes from candidate datastore")
        discard_changes_action.triggered.connect(self.discardChanges)
        discard_changes_action.setToolTip("Discards all changes uploaded to the candidate datastore of the device.")
        items.append(discard_changes_action)

        return items

    def contextMenuEvent(self, event):
        """
        Context menu event for the device.
        This method handles showing of the context menu.
        """

        self.menu = QMenu()

        context_menu_items = self._getContextMenuItems()
        for action in context_menu_items:
            self.menu.addAction(action)

        self.menu.setToolTipsVisible(True)
        self.menu.exec(event.screenPos())

    # ---------- DIALOG SHOW FUNCTIONS ---------- 
    def _showNetconfCapabilitiesDialog(self):
        dialog = netconf.NetconfCapabilitiesDialog(self)
        dialog.exec()

    def _showDeviceInterfacesDialog(self):
        dialog = interfaces.DeviceInterfacesDialog(self)
        dialog.exec()

    def _showHostnameDialog(self):
        dialog = system.HostnameDialog(self)
        dialog.exec()
    
    # ---------- HOSTNAME MANIPULATION FUNCTIONS ---------- 
    def _getHostname(self):
        try:
            hostname, rpc_reply = system.getHostnameWithNetconf(self)
            utils.printRpc(rpc_reply, "Get Hostname", self)
            return(hostname)
        except Exception as e:
            utils.printGeneral(f"Error getting hostname: {e}")
            utils.printGeneral(traceback.format_exc())
            return None
    
    def setHostname(self, new_hostname):
        try:
            rpc_reply, filter = system.setHostnameWithNetconf(self, new_hostname)
            utils.addPendingChange(self, f"Set hostname: {new_hostname}", rpc_reply, filter)
            utils.printRpc(rpc_reply, "Set Hostname", self)
            
            # FLAG (needed to update the hostname label on canvas, when commiting changes later on)
            self.has_updated_hostname = True

            return True
        except Exception as e:
            utils.printGeneral(f"Error setting hostname: {e}")
            utils.printGeneral(traceback.format_exc())
            QMessageBox.critical(None, "Error", f"Error setting hostname: {e}")
            return False

    # ---------- INTERFACE MANIPULATION FUNCTIONS ---------- 
    def getInterfaces(self):
        try:
            interfaces_data, rpc_reply = interfaces.getInterfacesWithNetconf(self)
            utils.printRpc(rpc_reply, "Get Interfaces", self)
            return(interfaces_data)
        except Exception as e:
            utils.printGeneral(f"Error getting interfaces: {e}")
            utils.printGeneral(traceback.format_exc())
            return None
    
    def deleteInterfaceIP(self, interface_id, subinterface_index, old_ip):
        try:
            rpc_reply, filter = interfaces.deleteIpWithNetconf(self, interface_id, subinterface_index, old_ip)
            if rpc_reply:
                utils.addPendingChange(self, f"Delete IP: {old_ip} from interface: {interface_id}.{subinterface_index}", rpc_reply, filter)
                utils.printRpc(rpc_reply, "Delete IP", self)

                # Delete the IP from the self.interfaces dictionary
                if old_ip.version == 4:
                    # find the entry to be deleted in the self.interfaces dictionary
                    all_entries = self.interfaces[interface_id]["subinterfaces"][subinterface_index]["ipv4_data"]
                    matching_entry = next((entry for entry in all_entries if entry["value"] == old_ip), None)
                    matching_entry["flag"] = "deleted"
                elif old_ip.version == 6:
                    # find the entry to be deleted in the self.interfaces dictionary
                    all_entries = self.interfaces[interface_id]["subinterfaces"][subinterface_index]["ipv6_data"]
                    matching_entry = next((entry for entry in all_entries if entry["value"] == old_ip), None)
                    matching_entry["flag"] = "deleted"

                # update the cable labels
                if self.cables:
                    self.updateCableLabelsText()

                return True
        except Exception as e:
            utils.printGeneral(f"Error deleting IP: {e}")
            utils.printGeneral(traceback.format_exc())
            QMessageBox.critical(None, "Error", f"Error deleting IP: {e}")
            return False

    def setInterfaceIP(self, interface_id, subinterface_index, new_ip):
        try:
            rpc_reply, filter = interfaces.setIpWithNetconf(self, interface_id, subinterface_index, new_ip)
            if rpc_reply:
                utils.addPendingChange(self, f"Set IP: {new_ip} on interface: {interface_id}.{subinterface_index}", rpc_reply, filter)
                utils.printRpc(rpc_reply, "Set IP", self)
                
                # Add the IP to the self.interfaces dictionary
                if subinterface_index not in self.interfaces[interface_id]["subinterfaces"]: # When adding IP to a new subinterface, create the subinterface first
                    self.interfaces[interface_id]["subinterfaces"][subinterface_index] = {
                        "ipv4_data": [],
                        "ipv6_data": []
                    }
                
                if new_ip.version == 4:
                    self.interfaces[interface_id]["subinterfaces"][subinterface_index]["ipv4_data"].append({"value": new_ip, "flag": "uncommited"})
                elif new_ip.version == 6:
                    self.interfaces[interface_id]["subinterfaces"][subinterface_index]["ipv6_data"].append({"value": new_ip, "flag": "uncommited"})

                # Update the cable labels
                if self.cables:
                    self.updateCableLabelsText()

                return True
        except Exception as e:
            utils.printGeneral(f"Error setting IP: {e}")
            utils.printGeneral(traceback.format_exc())
            QMessageBox.critical(None, "Error", f"Error setting IP: {e}")
            return False

    def addInterface(self, interface_id, interface_type):
        try:
            rpc_reply, filter = interfaces.addInterfaceWithNetconf(self, interface_id, interface_type)
            if rpc_reply:
                utils.addPendingChange(self, f"Add interface: {interface_id}", rpc_reply, filter)
                utils.printRpc(rpc_reply, "Add Interface", self)
                self.interfaces[interface_id] = {
                    "subinterfaces": {}
                }

                return True
        except Exception as e:
            utils.printGeneral(f"Error adding interface: {e}")
            utils.printGeneral(traceback.format_exc())
            QMessageBox.critical(None, "Error", f"Error adding interface: {e}")
            return False
    
    # ---------- CANDIDATE DATASTORE MANIPULATION FUNCTIONS ----------
    def discardChanges(self):
        try:
            rpc_reply = netconf.discardNetconfChanges(self)
            if rpc_reply:
                utils.printRpc(rpc_reply, "Discard changes", self)
                self.interfaces = self.getInterfaces() # Refresh interfaces after discard

                self.has_pending_changes = False
                signal_manager.deviceNoLongerHasPendingChanges.emit(self.id)

                self.updateCableLabelsText()
                return True
        except Exception as e:
            utils.printGeneral(f"Error discarding changes: {e}")
            utils.printGeneral(traceback.format_exc())
            QMessageBox.critical(None, "Error", f"Error discarding changes: {e}")
            return False

    def commitChanges(self, confirmed=False, confirm_timeout=None):
        try:
            rpc_reply = netconf.commitNetconfChanges(self, confirmed, confirm_timeout)
            if rpc_reply:
                utils.printRpc(rpc_reply, "Commit changes", self)
                self.interfaces = self.getInterfaces() # Refresh interfaces after commit

                if not confirmed: # Dont remove the pending changes flag, if the commit is of the confirmed type
                    self.has_pending_changes = False
                    signal_manager.deviceNoLongerHasPendingChanges.emit(self.id)
                    self.updateCableLabelsText()
                return True
        except Exception as e:
            utils.printGeneral(f"Error committing changes: {e}")
            utils.printGeneral(traceback.format_exc())
            QMessageBox.critical(None, "Error", f"Error committing changes: {e}")
            return False
    
    # ---------- REGISTRY FUNCTIONS ---------- 
    @classmethod
    def getDeviceInstance(cls, device_id):
        return cls._registry.get(device_id)
    
    @classmethod
    def getAllDevicesInstancesKeys(cls):
        return list(cls._registry.keys())
    
    @classmethod
    def getAllDevicesInstances(cls):
        return list(cls._registry.values())

    
class Router(Device):
    _device_type = "R"

    def __init__(self, device_parameters, x=0, y=0):
        super().__init__(device_parameters, x, y)

        # ICON
        router_icon_img = QImage("graphics/devices/router.png")
        self.setPixmap(QPixmap.fromImage(router_icon_img))

    def _getContextMenuItems(self):
        """
        Router-specific context menu items.
        """

        items = super()._getContextMenuItems()

        # Show routing table
        show_routing_table_action = QAction("Show routing table")
        show_routing_table_action.triggered.connect(self.showRoutingTable)
        show_routing_table_action.setToolTip("Shows the routing table of the device.")
        items.append(show_routing_table_action)

        return items

    def cloneToOSPFDevice(self):
        """
        Clones the device to an OSPFDevice object, which is used in the OSPF configuration dialog.
        The cloned device is used to display the device in the OSPF configuration dialog, without affecting the original device.
        After the OSPF configuration is done, the cloned device is deleted.
        """
        return OSPFDevice(self)
    
    # ---------- IPSEC FUNCTIONS ---------- 
    def configureIPSec(self, dev_parameters, ike_parameters, ipsec_parameters):
        try:
            rpc_reply, filter = ipsec.configureIPSecWithNetconf(self, dev_parameters, ike_parameters, ipsec_parameters)
            #utils.addPendingChange(self.original_device, f"Configure IPSec tunnel between: TODO", rpc_reply, filter)
            #utils.printRpc(rpc_reply, "Configure IPSec", self)
            print(filter)
        except Exception as e:
            utils.printGeneral(f"Error configuring IPSec on device {self.id}: {e}")
            utils.printGeneral(traceback.format_exc())
    
    # ---------- ROUTING TABLE FUNCTIONS ---------- 
    def getRoutingTable(self):
        """
        Retrieves the routing table from the device based on its operating system.
        Returns:
            rpc_reply: The routing table information.
        """
        try:
            if self.device_parameters["device_params"] == "iosxe":
                rpc_filter = IetfRouting_Get_GetRoutingState_Filter()
                rpc_reply = self.mngr.get(str(rpc_filter))
            elif self.device_parameters["device_params"] == "junos":
                rpc_payload = JunosRpcRoute_Dispatch_GetRoutingInformation_Filter()
                rpc_reply = self.mngr.dispatch(rpc_payload.__ele__())
            
            utils.printRpc(rpc_reply, "Get Routing Table", self)
            return (rpc_reply)
        except Exception as e:
            utils.printGeneral(f"Error getting routing table: {e}")
            utils.printGeneral(traceback.format_exc())

    def showRoutingTable(self):
        """
        Displays the routing table in a dialog window.
        This method retrieves the routing table using the `getRoutingTable` method,
        converts it to an XML tree using the `helper.convertToEtree` function, and
        then displays it in a `RoutingTableDialog` window.
        """

        routing_table = self.getRoutingTable()

        if routing_table is None:
            routingTableDialog = RoutingTableDialog(None, self)
            routingTableDialog.exec()
            return

        if self.device_parameters["device_params"] == "iosxe":
            routingTableDialog = RoutingTableDialog(utils.convertToEtree(routing_table, "iosxe"), self)
        elif self.device_parameters["device_params"] == "junos":
            routingTableDialog = RoutingTableDialog(utils.convertToEtree(routing_table, "junos"), self)

        routingTableDialog.exec()


class Switch(Device):
    _device_type = "S"

    def __init__(self, device_parameters, x=0, y=0):
        super().__init__(device_parameters, x, y)

        # ICON
        switch_icon_img = QImage("graphics/devices/switch.png")
        self.setPixmap(QPixmap.fromImage(switch_icon_img))

        # Switch specific functions go here


class ClonedDevice(QGraphicsPixmapItem):
    def __init__(self, original_device):
        super().__init__()

        self.original_device = original_device
        self.device_parameters = original_device.device_parameters

        # GRAPHICS
        self.setPixmap(original_device.pixmap())
        self.setFlag(QGraphicsItem.ItemIsMovable, False) # In order to allow moving the devices, the method for updating the cloned cables would have to be implemented.
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setPos(original_device.pos())
        self.setZValue(1)

        # LABEL (Hostname)
        self.label = QGraphicsTextItem(self)
        self.label.setFont(QFont('Arial', 10))
        self.label.setPlainText(original_device.label.toPlainText())
        self.label.setPos(original_device.label.pos())

        # CABLES LIST
        self.original_cables = original_device.cables.copy()
        self.cables = []
        self.cable_connected_interfaces = []

        # INTERFACES
        self.interfaces = original_device.interfaces

        # ID
        self.id = original_device.id


class OSPFDevice(ClonedDevice):
    """
    A class to represent a device, that was cloned from Router class. It is used in OSPF configuration dialog, where it serves as a QGraphicItem in the cloned scene.
    """
    def __init__(self, original_device):
        super().__init__(original_device)

        # OSPF SPECIFIC
        self.passive_interfaces = []
        self.ospf_networks = {} # filling the dictionary must be done externally (from OSPFDialog) after the whole scene is created, because it needs to know about connected cables in the scene
        self.router_id = None

    def getOSPFNetworks(self):
        """
        Returns a dictionary of OSPF networks for each interface.
        Example of return value: doc/ospf_networks.md
        """

        interfaces = self.interfaces
        
        device_ospf_networks = {} # {interface_name: [networks]}
        for interface_name, interface_data in interfaces.items(): # .items() because the key (interface name) is used as a key in the return dictionary
            if interface_name not in self.cable_connected_interfaces:
                continue # skip interfaces, that dont have a cable connected to it (or they have, but the other end wasnt cloned to the new scene)
            
            subinterfaces = interface_data.get("subinterfaces", {})
            if subinterfaces:
                for subinterface_data in subinterfaces.values(): # .values() because the key is not needed
                    interface_ospf_networks = []
                    for ipv4 in subinterface_data.get("ipv4_data", []):
                        interface_ospf_networks.append(ipv4["value"].network)
                    for ipv6 in subinterface_data.get("ipv6_data", []):
                        interface_ospf_networks.append(ipv6["value"].network)

                device_ospf_networks[interface_name] = interface_ospf_networks        
        return device_ospf_networks
    
    def addOSPFNetwork(self, network, interface_name):
        if interface_name not in self.ospf_networks:
            self.ospf_networks[interface_name] = []
        self.ospf_networks[interface_name].append(network)

    def removeOSPFNetwork(self, network, interface_name):
        self.ospf_networks[interface_name].remove(network)

    def configureOSPF(self, area, hello_interval, dead_interval, reference_bandwidth):
        """
        Configures OSPF on the device with the specified parameters. Calls the configureOSPFWithNetconf function from the ospf module. Called from the OSPFDialog, when the user clicks the "OK" button.
        Parameters:
            rpc_reply: The RPC reply from the NETCONF server.
            filter: The filter used in the NETCONF RPC.
        Args:
            area (int): The OSPF area to configure.
            hello_interval (int): The hello interval in seconds.
            dead_interval (int): The dead interval in seconds.
            reference_bandwidth (int): The reference bandwidth in Mbps.
        Returns:
            None
        """
        
        try:
            rpc_reply, filter = ospf.configureOSPFWithNetconf(self, area, hello_interval, dead_interval, reference_bandwidth)
            utils.addPendingChange(self.original_device, f"Configure OSPF area: {area}", rpc_reply, filter)
            utils.printRpc(rpc_reply, "Configure OSPF", self)
        except Exception as e:
            utils.printGeneral(f"Error configuring OSPF on device {self.original_device.id}: {e}")
            utils.printGeneral(traceback.format_exc())


# ---------- QT: ----------
class AddDeviceDialog(QDialog):
    def __init__(self, view):
        super().__init__()

        self.view = view
        self.device_parameters = {}
        self.setWindowTitle("Add a device")
        self.setModal(True)
        self.layout = QVBoxLayout()

        # Input fields
        self.addressTextInput = QLineEdit()
        self.addressTextInput.setPlaceholderText("IP address:port")
        self.layout.addWidget(self.addressTextInput)

        self.usernameTextInput = QLineEdit()
        self.usernameTextInput.setPlaceholderText("Username")
        self.layout.addWidget(self.usernameTextInput)

        self.passwordTextInput = QLineEdit()
        self.passwordTextInput.setPlaceholderText("Password")
        self.layout.addWidget(self.passwordTextInput)

        self.deviceTypeComboInput = QComboBox()
        self.deviceTypeComboInput.addItems(["Router", "Switch"])
        self.layout.addWidget(self.deviceTypeComboInput)

        self.deviceVendorComboInput = QComboBox()
        self.deviceVendorComboInput.addItems(["Cisco IOS XE", "Juniper"])
        self.layout.addWidget(self.deviceVendorComboInput)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._confirmConnection)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        # Layout
        self.setLayout(self.layout)

        #DEBUG: Testing connection for debugging
        if __debug__:
            self.addressTextInput.setText("172.16.10.81")
            self.usernameTextInput.setText("jakub")
            self.passwordTextInput.setText("cisco")

    def _confirmConnection(self):
        try:
            # Address + Port
            address_field = self.addressTextInput.text().split(":")
            if len(address_field) == 2:
                self.device_parameters["address"] = address_field[0]
                self.device_parameters["port"] = address_field[1]
            elif len(address_field) == 1:
                self.device_parameters["address"] = self.addressTextInput.text()
                self.device_parameters["port"] = 830
            else:
                raise ValueError("Invalid IP address format")

            # Username + Password + Device vendor
            self.device_parameters["username"] = self.usernameTextInput.text()
            self.device_parameters["password"] = self.passwordTextInput.text()
            if self.deviceVendorComboInput.currentText() == "Cisco IOS XE":
                self.device_parameters["device_params"] = "iosxe"
            elif self.deviceVendorComboInput.currentText() == "Juniper":
                self.device_parameters["device_params"] = "junos"
        except ValueError as e:
            QMessageBox.critical(None, "Invalid input", f"Invalid input: {e}")
            utils.printGeneral(traceback.format_exc())

        # Check if the device with the same address is not already in the scene
        for device in self.view.scene.items():
            if isinstance(device, Device):
                if device.device_parameters["address"] == self.device_parameters["address"]:
                    QMessageBox.warning(self, "Device already exists", "The device with the same address is already in the scene.")
                    return

        # Add the device with the correct type (exception handling is done in the _addRouter and _addSwitch methods)                
        if self.deviceTypeComboInput.currentText() == "Router":
            self._addRouter()
        elif self.deviceTypeComboInput.currentText() == "Switch":
            self._addSwitch()

        self.accept()

    def _addRouter(self):
        router = Router(self.device_parameters)
        self.view.scene.addItem(router)
        return(router)
    
    def _addSwitch(self):
        switch = Switch(self.device_parameters)
        self.view.scene.addItem(switch)
        return(switch)
    

class RoutingTableDialog(QDialog):
    """
    A dialog for displaying the routing table of a router (instance of class Router).
    """

    def __init__(self, routing_table, router):
        """
        Initializes the RoutingTableDialog.
        Args:
            routing_table: The routing table XML data (XML root element, specifically).
            router (Router): The router object for which to display the routing table.
        Sets up the UI elements and connects the buttons to their respective functions.
        """
    
        super().__init__()

        self.routing_table = routing_table

        self.ui = Ui_RoutingTableDialog()
        self.ui.setupUi(self)

        # Setup UI elements
        self.ui.header.setText(f"Routing table for device: {router.id}")
        self.ui.collapse_button.clicked.connect(self.ui.routing_table_tree.collapseAll)
        self.ui.expand_button.clicked.connect(self.ui.routing_table_tree.expandAll)
        self.ui.refresh_button.clicked.connect(lambda: self._refreshRoutingTable(router))
        self.ui.close_button_box.rejected.connect(self.reject)

        # Fill the QTreeWidget with the routing table data, takes the XML root element and the QTreeWidget as arguments
        utils.populateTreeWidget(self.ui.routing_table_tree, self.routing_table)

    def _refreshRoutingTable(self, router):
        """
        Refreshes the routing table of the selected router. This method is called when the user clicks the "Refresh" button in the routing table dialog.
        Args:
            router (Router): The router for which to refresh the routing table.
        """

        routing_table = router.getRoutingTable()
        if router.device_parameters["device_params"] == "iosxe":
            routing_table_etree = utils.convertToEtree(routing_table, "iosxe")
        elif router.device_parameters["device_params"] == "junos":
            routing_table_etree = utils.convertToEtree(routing_table, "junos")

        utils.populateTreeWidget(self.ui.routing_table_tree, routing_table_etree)
        