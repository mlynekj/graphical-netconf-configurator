# ---------- IMPORTS: ----------
# Standard library
import traceback
import ipaddress
from lxml import etree as ET

# Custom modules
import utils
import modules.netconf as netconf
import modules.interfaces as interfaces
import modules.system as system
import modules.ospf as ospf
import modules.security as security
import modules.vlan as vlan
from signals import signal_manager
from yang.filters import DispatchFilter, GetFilter
from definitions import ROUTING_YANG_DIR, CONFIGURATION_TARGET_DATASTORE

# Qt
from PySide6.QtWidgets import (
    QGraphicsPixmapItem, 
    QGraphicsItem,
    QLineEdit, 
    QMenu,
    QGraphicsTextItem,
    QToolTip,
    QVBoxLayout,
    QDialogButtonBox,
    QComboBox,
    QDialog,
    QVBoxLayout,
    QMessageBox)
from PySide6.QtGui import (
    QImage, 
    QPixmap,
    QAction,
    QFont,
    QAction,
    QIcon)
from PySide6.QtCore import QTimer

# QtCreator
from ui.ui_xmldatadialog import Ui_XMLDataDialog

# ---------- HELPER FUNCTIONS: ----------
def addRouter(device_parameters, scene, class_type) -> "Router":
    """Creates a router object and adds it to the scene."""

    if class_type == "IOSXERouter":
        router = IOSXERouter(device_parameters)
    elif class_type == "JUNOSRouter":
        router = JUNOSRouter(device_parameters)

    scene.addItem(router)
    return(router)

def addFirewall(device_parameters, scene, class_type) -> "Firewall":
    """Creates a firewall object and adds it to the scene."""

    if class_type == "JUNOSFirewall":
        firewall = JUNOSFirewall(device_parameters)

    scene.addItem(firewall)
    return(firewall)

def addSwitch(device_parameters, scene, class_type) -> "Switch":
    """Creates a switch object and adds it to the scene."""

    if class_type == "IOSXESwitch":
        switch = IOSXESwitch(device_parameters)

    scene.addItem(switch)
    return(switch)

# ---------- FILTERS: ----------
class JunosRpcRoute_Dispatch_GetRoutingInformation_Filter(DispatchFilter):
    def __init__(self) -> None:
        self.filter_xml = ET.parse(ROUTING_YANG_DIR + "junos-rpc-route_dispatch_get-routing-information.xml")
    
    
class IetfRouting_Get_GetRoutingState_Filter(GetFilter):
    def __init__(self) -> None:
        self.filter_xml = ET.parse(ROUTING_YANG_DIR + "ietf-routing_get_get-routing-state.xml")


# ---------- DEVICE CLASSES: ----------
# GENERAL CLASSES
class Device(QGraphicsPixmapItem):
    """
    Device Class
    This class represents a network device on a graphical canvas. It provides functionality for managing the device's 
    NETCONF connection, interfaces, hostname, and graphical representation. The class also supports interaction 
    through context menus, tooltips, and mouse events.
    Attributes:
        _registry (dict): A registry to store device instances.
        _device_type (str): The type of the device, used for ID generation.
        is_ospf_capable (bool): Indicates if the device supports OSPF.
        is_ipsec_capable (bool): Indicates if the device supports IPsec.
        is_vlan_capable (bool): Indicates if the device supports VLANs.
        device_parameters (dict): Parameters for the device, including connection details (IP, username, password, ...).
        mngr: The NETCONF connection manager for the device (ncclient).
        cables (list): A list of cables connected to the device on the canvas.
        cable_connected_interfaces (list): A list of interfaces connected to cables on the canvas.
        has_pending_changes (bool): Indicates if there are uncommitted changes on the device. Used when "commiting" the changes.
        has_updated_hostname (bool): Indicates if the hostname has been updated. Used to determine, whether it needs to be updated on the canvas.
        id (str): The unique identifier of the device.
        netconf_capabilities: The NETCONF capabilities of the device.
        interfaces (dict): A dictionary containing the device's interfaces.
        hostname (str): The hostname of the device.
        label (QGraphicsTextItem): The graphical label displaying the hostname and ID.
        tooltip_text (str): The text displayed in the tooltip.
        tooltip_timer (QTimer): A timer for showing the tooltip after a delay.
    Methods:
        __init__(device_parameters, x=0, y=0): Initializes the device with given parameters and position.
        getNetconfCapabilities(): Retrieves the NETCONF capabilities of the device.
        refreshHostnameLabel(new_hostname=None): Updates the hostname label on the canvas.
        deleteDevice(): Deletes the device from the canvas and disconnects it.
        updateCablePositions(): Updates the positions of connected cables.
        updateCableLabelsText(): Updates the labels of connected cables.
        hoverEnterEvent(event): Handles mouse hover enter events.
        hoverLeaveEvent(event): Handles mouse hover leave events.
        _getContextMenuItems(): Retrieves the context menu items for the device.
        contextMenuEvent(event): Handles the context menu event for the device.
        _showNetconfCapabilitiesDialog(): Displays the NETCONF capabilities dialog.
        _showDeviceInterfacesDialog(): Displays the device interfaces dialog.
        _showHostnameDialog(): Displays the hostname configuration dialog.
        getHostname(): Retrieves the hostname of the device using NETCONF.
        setHostname(new_hostname): Sets the hostname of the device using NETCONF.
        getInterfaces(): Retrieves the interfaces of the device using NETCONF.
        deleteInterfaceIP(interface_id, subinterface_index, old_ip): Deletes an IP address from an interface.
        setInterfaceIP(interface_id, subinterface_index, new_ip): Sets an IP address on an interface.
        addInterface(interface_id, interface_type): Adds a new interface to the device.
        configureInterfaceDescription(interface_id, description): Configures the description of an interface.
        cloneToOSPFDevice(): Clones the router to an `OSPFDevice` object for use in OSPF configuration dialogs.
        getRoutingTable(): Retrieves the routing table from the device based on its operating system.
        _showRoutingTable(): Displays the routing table in a dialog window by retrieving it and converting it to an XML tree.
        discardChanges(): Discards all pending changes on the device.
        commitChanges(confirmed=False, confirm_timeout=None): Commits all pending changes on the device.
        cancelCommit(): Cancels a confirmed commit operation.
        _generateID(): Generates a unique ID for the device.
        _getBaseClass(): Retrieves the base class of the current device class. Used for ID generation.
        getDeviceInstance(device_id): Retrieves a device instance by its ID.
        getAllDevicesInstancesKeys(): Retrieves all device instance keys.
        getAllDevicesInstances(): Retrieves all device instances.

    """
    
    _registry = {} # Used to store device instances
    _device_type = "dv"
    is_ospf_capable = False
    is_ipsec_capable = False
    is_vlan_capable = False
    
    def __init__(self, device_parameters, x=0, y=0) -> "Device":
        super().__init__()

        self.setAcceptHoverEvents(True) # Enable mouse hover over events

        self.device_parameters = device_parameters

        # NETCONF CONNECTION
        try:
            self.mngr = netconf.establishNetconfConnection(self.device_parameters)
            if CONFIGURATION_TARGET_DATASTORE == "running":
                assert(":writable-running" in self.mngr.server_capabilities)
            elif CONFIGURATION_TARGET_DATASTORE == "candidate":                
                assert(":candidate" in self.mngr.server_capabilities)
            self.mngr.lock(target=CONFIGURATION_TARGET_DATASTORE) # lock the datastore
        except Exception as e:
            utils.printGeneral(f"Error establishing NETCONF connection: {e}")
            utils.printGeneral(traceback.format_exc())
            QMessageBox.critical(None, "Error", f"Error establishing NETCONF connection: {e}")
            raise ConnectionError(f"Error establishing NETCONF connection: {e}")

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
        self.id = self._generateID()

        # DEVICE INFORMATION
        self.netconf_capabilities = self.getNetconfCapabilities()
        self.interfaces = self.getInterfaces() # Documented in doc/interfaces_dictionary.md
        self.hostname = self.getHostname()

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

    def getNetconfCapabilities(self) -> list:
        return(netconf.getNetconfCapabilities(self))

    def refreshHostnameLabel(self, new_hostname=None) -> None:
        """
        Refreshes the hostname label of the device.

        Parameters:
        hostname (str, optional): The new hostname to set. If not provided, the hostname will be retrieved using getHostname().
        """

        if new_hostname is not None:
            self.hostname = new_hostname
        else:
            self.hostname = self.getHostname()

        self.label.setPlainText(f"{str(self.hostname)} (ID: {self.id})")
        self.label_border = self.label.boundingRect()
        self.label.setPos((self.pixmap().width() - self.label_border.width()) / 2, self.pixmap().height())

    def deleteDevice(self) -> None:
        """Deletes the device from the canvas and disconnects it."""

        rpc_reply = netconf.demolishNetconfConnection(self) # Disconnect from NETCONF server

        self.scene().removeItem(self)
    
        for cable in self.cables.copy(): # cannot modify contents of a list, while iterating through it! => .copy()
            cable.removeCable()

        del type(self)._registry[self.id]
        utils.printRpc(rpc_reply, "Close NETCONF connection", self)
        utils.printGeneral(f"Connection to device: {self.device_parameters['address']} has been closed.")

    def updateCablePositions(self):
        """Updates the positions of all connected cables."""

        for cable in self.cables:
            cable.updatePosition()    

    def updateCableLabelsText(self):
        """Updates the labels of all connected cables."""

        for cable in self.cables:
            cable.updateLabelsText()

    # ---------- MOUSE EVENTS FUNCTIONS ---------- 
    def hoverEnterEvent(self, event) -> None:
        """Handles the mouse hover enter event."""

        # Tooltip
        self.tooltip_timer.start(1000)
        self.hover_pos = event.screenPos()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        """Handles the mouse hover leave event."""

        # Tooltip
        self.tooltip_timer.stop()
        QToolTip.hideText()
        super().hoverLeaveEvent(event)

    def _getContextMenuItems(self) -> list:
        """Returns the context menu items for the device."""
        
        items = []
        # Disconnect from device
        disconnect_action = QAction("Disconnect")
        disconnect_action.triggered.connect(self.deleteDevice)
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

        # Show runnning configuration
        show_running_config_action = QAction("Show Running Configuration")
        show_running_config_action.triggered.connect(self._showRunningConfig)
        show_running_config_action.setToolTip("Shows the running configuration of the device (in native YANG model).")
        items.append(show_running_config_action)

        # Discard all pending changes
        discard_changes_action = QAction("Discard all pending changes from candidate datastore")
        discard_changes_action.triggered.connect(self.discardChanges)
        discard_changes_action.setToolTip("Discards all changes uploaded to the candidate datastore of the device.")
        items.append(discard_changes_action)

        return(items)

    def contextMenuEvent(self, event) -> None:
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
    def _showNetconfCapabilitiesDialog(self) -> None:
        """Displays the NETCONF capabilities dialog."""

        dialog = netconf.NetconfCapabilitiesDialog(self)
        dialog.exec()

    def _showDeviceInterfacesDialog(self) -> None:
        """Displays the device interfaces dialog."""

        dialog = interfaces.DeviceInterfacesDialog(self)
        dialog.exec()

    def _showHostnameDialog(self) -> None:
        """Displays the hostname configuration dialog."""

        dialog = system.HostnameDialog(self)
        dialog.exec()
    
    # ---------- HOSTNAME MANIPULATION FUNCTIONS ---------- 
    def getHostname(self) -> str:
        """Retrieves the hostname of the device using NETCONF."""
        try:
            hostname, rpc_reply = system.getHostnameWithNetconf(self)
            utils.printRpc(rpc_reply, "Get Hostname", self)
            return(hostname)
        except Exception as e:
            utils.printGeneral(f"Error getting hostname: {e}")
            utils.printGeneral(traceback.format_exc())
            return None
    
    def setHostname(self, new_hostname) -> bool:
        """
        Sets the hostname of the device using NETCONF.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """

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
    def getInterfaces(self) -> dict:
        """
        Retrieves the interfaces of the device using NETCONF.
        Returns:
            dict: The interfaces data.
        """

        try:
            interfaces_data, rpc_reply = interfaces.getInterfacesWithNetconf(self)
            utils.printRpc(rpc_reply, "Get Interfaces", self)
            return(interfaces_data)
        except Exception as e:
            utils.printGeneral(f"Error getting interfaces: {e}")
            utils.printGeneral(traceback.format_exc())
            return None
    
    def deleteInterfaceIP(self, interface_id, subinterface_index, old_ip) -> bool:
        """
        Deletes an IP address from an interface using NETCONF.
        Updates the self.interfaces dictionary and the cable labels.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """

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
                    self.interfaces[interface_id]["flag"] = "deleted"
                elif old_ip.version == 6:
                    # find the entry to be deleted in the self.interfaces dictionary
                    all_entries = self.interfaces[interface_id]["subinterfaces"][subinterface_index]["ipv6_data"]
                    matching_entry = next((entry for entry in all_entries if entry["value"] == old_ip), None)
                    matching_entry["flag"] = "deleted"
                    self.interfaces[interface_id]["flag"] = "deleted"

                # update the cable labels
                if self.cables:
                    self.updateCableLabelsText()

                return True
        except Exception as e:
            utils.printGeneral(f"Error deleting IP: {e}")
            utils.printGeneral(traceback.format_exc())
            QMessageBox.critical(None, "Error", f"Error deleting IP: {e}")
            return False

    def setInterfaceIP(self, interface_id, subinterface_index, new_ip) -> bool:
        """
        Sets an IP address on an interface using NETCONF.
        Updates the self.interfaces dictionary and the cable labels.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """

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
                self.interfaces[interface_id]["flag"] = "uncommited"

                # Update the cable labels
                if self.cables:
                    self.updateCableLabelsText()

                return True
        except Exception as e:
            utils.printGeneral(f"Error setting IP: {e}")
            utils.printGeneral(traceback.format_exc())
            QMessageBox.critical(None, "Error", f"Error setting IP: {e}")
            return False

    def addInterface(self, interface_id, interface_type) -> bool:
        """
        Adds a new interface to the device using NETCONF.
        Updates the self.interfaces dictionary.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        
        try:
            rpc_reply, filter = interfaces.addInterfaceWithNetconf(self, interface_id, interface_type)
            if rpc_reply:
                utils.addPendingChange(self, f"Add interface: {interface_id}", rpc_reply, filter)
                utils.printRpc(rpc_reply, "Add Interface", self)
                self.interfaces[interface_id] = {
                    "flag": "uncommited",
                    "subinterfaces": {}
                }

                return True
        except Exception as e:
            utils.printGeneral(f"Error adding interface: {e}")
            utils.printGeneral(traceback.format_exc())
            QMessageBox.critical(None, "Error", f"Error adding interface: {e}")
            return False
    
    def configureInterfaceDescription(self, interface_id, description) -> bool:
        """
        Configures the description of an interface using NETCONF.
        Updates the self.interfaces dictionary.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        
        try:
            rpc_reply, filter = interfaces.editDescriptionWithNetconf(self, interface_id, description)
            if rpc_reply:
                utils.addPendingChange(self, f"Edit description on interface: {interface_id}", rpc_reply, filter)
                utils.printRpc(rpc_reply, "Edit description on interface", self)
                self.interfaces[interface_id]["description"] = description
                self.interfaces[interface_id]["flag"] = "uncommited"

                return True
        except Exception as e:
            utils.printGeneral(f"Error editing description: {e}")
            utils.printGeneral(traceback.format_exc())
            QMessageBox.critical(None, "Error", f"Error editing description: {e}")
            return False

    # ---------- OSPF FUNCTIONS ----------
    def cloneToOSPFDevice(self) -> "OSPFDevice":
        """
        Clones the device to an OSPFDevice object, which is used in the OSPF configuration dialog.
        The cloned device is used to display the device in the OSPF configuration dialog, without affecting the original device.
        After the OSPF configuration is done, the cloned device is deleted. 
        Must be externally checked, if the device is_ospf_capable == True, before calling this method.
        """
        return OSPFDevice(self)
    
    # ---------- ROUTING TABLE FUNCTIONS ---------- 
    def getRoutingTable(self) -> ET.Element:
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

    def _showRoutingTable(self) -> None:
        """
        Displays the routing table in a dialog window.
        This method retrieves the routing table using the `getRoutingTable` method,
        converts it to an XML tree using the `helper.convertToEtree` function, and
        then displays it in a `RoutingTableDialog` window.
        """

        routing_table = self.getRoutingTable()

        if routing_table is None:
            routing_table_dialog = ShowRoutingTableDialog(None, self)
            routing_table_dialog.exec()
            return

        if self.device_parameters["device_params"] == "iosxe":
            routing_table_dialog = ShowRoutingTableDialog(utils.convertToEtree(routing_table, "iosxe"), self)
        elif self.device_parameters["device_params"] == "junos":
            routing_table_dialog = ShowRoutingTableDialog(utils.convertToEtree(routing_table, "junos"), self)

        routing_table_dialog.exec()

    # ---------- RUNNING CONFIGARATION FUNCTIONS ----------
    def getRunningConfig(self) -> ET.Element:
        """
        Retrieves the running-configuration from the device.
        Returns:
            rpc_reply: The running config information.
        """

        try:
            rpc_reply = self.mngr.get_config(source="running")
            utils.printRpc(rpc_reply, "Get Running-Configuration", self)
            return (rpc_reply)
        except Exception as e:
            utils.printGeneral(f"Error getting running-config: {e}")
            utils.printGeneral(traceback.format_exc())

    def _showRunningConfig(self) -> None:
        """
        Displays the routing table in a dialog window.
        This method retrieves the routing table using the `getRoutingTable` method,
        converts it to an XML tree using the `helper.convertToEtree` function, and
        then displays it in a `RoutingTableDialog` window.
        """

        running_config = self.getRunningConfig()

        if running_config is None:
            running_config_dialog = ShowRunningConfigDialog(None, self)
            running_config_dialog.exec()
            return

        if self.device_parameters["device_params"] == "iosxe":
            running_config_dialog = ShowRoutingTableDialog(utils.convertToEtree(running_config, "iosxe"), self)
        elif self.device_parameters["device_params"] == "junos":
            running_config_dialog = ShowRoutingTableDialog(utils.convertToEtree(running_config, "junos"), self)

        running_config_dialog.exec()

    # ---------- CANDIDATE DATASTORE MANIPULATION FUNCTIONS ----------
    def discardChanges(self) -> bool:
        """
        Discards all pending changes on the device.
        Emits a signal to notify the main window that the device no longer has pending changes, clears flags, and updates cable labels.
        Also refreshes the self.interfaces dictionary.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        
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

    def commitChanges(self, confirmed=False, confirm_timeout=None) -> bool:
        """
        Commits all pending changes on the device.
        Emits a signal to notify the main window that the device no longer has pending changes, clears flags, and updates cable labels.
        """
        
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
        
    def cancelCommit(self) -> bool:
        """
        Cancels a confirmed commit operation. Handles the operation based on the device's operating system:
            - Cisco devices support the standard <cancel-commit> operation.
            - Juniper devices do not support the <cancel-commit> operation, so we have to use the <rollback> operation instead, followed by a <commit>.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        
        try:
            if self.device_parameters["device_params"] == "iosxe": # Cisco SUPPORTS the standard <cancel-commit> operation
                rpc_reply = netconf.cancelNetconfCommit(self) 
            elif self.device_parameters["device_params"] == "junos": # Juniper DOES NOT support the <cancel-commit> operation
                rpc_reply = netconf.rollbackNetconfChanges(self) 
                self.commitChanges()

            if rpc_reply:
                utils.printRpc(rpc_reply, "Cancel commit", self)
                self.interfaces = self.getInterfaces()
                self.has_pending_changes = False
                signal_manager.deviceNoLongerHasPendingChanges.emit(self.id)
                self.updateCableLabelsText()
                return True

        except Exception as e:
            utils.printGeneral(f"Error cancelling commit: {e}")
            utils.printGeneral(traceback.format_exc())
            QMessageBox.critical(None, "Error", f"Error cancelling commit: {e}")
            return False
    
    # ---------- REGISTRY FUNCTIONS ---------- 
    @classmethod
    def _generateID(cls) -> str:
        """
        Generates a unique ID for the device. The ID is generated based on the device type and a counter, meaning that each device type has its own counter.
        Devices inherited from the same base class share the same counter (Router -> IOSXERouter, JUNOSRouter; Switch -> IOSXESwitch; ...).
        Returns:
            str: The generated ID.
        """
        
        base_class = cls._getBaseClass()
        base_class._counter += 1
        return(f"{base_class._device_type}{base_class._counter}")
    
    @classmethod
    def _getBaseClass(cls) -> type:
        """Get the base class of the current class (e.g., Router, Switch, Firewall)."""

        for base in cls.__bases__:
            if issubclass(base, Device) and base is not Device:
                return base
        return cls
   
    @classmethod
    def getDeviceInstance(cls, device_id) -> "Device":
        """
        Retrieves a device instance by its ID.
        Returns:
            Device: The device instance
        """

        return cls._registry.get(device_id)
    
    @classmethod
    def getAllDevicesInstancesKeys(cls) -> list:
        """Retrieves all device instance keys."""

        return list(cls._registry.keys())
    
    @classmethod
    def getAllDevicesInstances(cls) -> list:
        """Retrieves all device instances."""

        return list(cls._registry.values())

    
class Router(Device):
    """
    Router Class
    The `Router` class represents a network router device and extends the `Device` class. 
    It includes specific attributes and methods for router functionality, such as OSPF 
    capabilities and routing table management.
    Attributes:
        _device_type (str): The type of the device, set to "rt" for routers.
        _counter (int): A counter for tracking instances of the class.
        is_ospf_capable (bool): Indicates whether the router supports OSPF.
        is_ipsec_capable (bool): Indicates whether the router supports IPsec.
        is_vlan_capable (bool): Indicates whether the router supports VLANs.
    Methods:
        __init__(device_parameters, x=0, y=0):
            Initializes a `Router` instance with the given parameters and sets up the router icon.
    """

    _device_type = "rt"
    _counter = 0
    is_ospf_capable = True
    is_ipsec_capable = False # Cisco routers are capable, Juniper routers are not
    is_vlan_capable = False

    def __init__(self, device_parameters, x=0, y=0) -> "Router":
        super().__init__(device_parameters, x, y)

        # ICON
        router_icon_img = QImage("graphics/devices/router.png")
        self.setPixmap(QPixmap.fromImage(router_icon_img))

    def _getContextMenuItems(self) -> list:
        """
        Router-specific context menu items.
        """

        items = super()._getContextMenuItems()

        # Show routing table
        show_routing_table_action = QAction("Show routing table")
        show_routing_table_action.triggered.connect(self._showRoutingTable)
        show_routing_table_action.setToolTip("Shows the routing table of the device.")
        items.append(show_routing_table_action)

        return items


class Switch(Device):
    """
    The `Switch` class represents a network switch device and extends the `Device` class. 
    It includes specific attributes and methods for switch functionality, such as VLAN
    capabilities.
    Attributes:
        _device_type (str): The type of the device, set to "sw" for switch.
        _counter (int): A counter for tracking instances or other purposes.
        is_ospf_capable (bool): Indicates if the switch supports OSPF (default: False).
        is_ipsec_capable (bool): Indicates if the switch supports IPsec (default: False).
        is_vlan_capable (bool): Indicates if the switch supports VLANs (default: True).
        vlans (dict): A dictionary containing VLAN information retrieved from the device.
    Methods:
        __init__(device_parameters, x=0, y=0):
            Initializes the Switch instance with device parameters and optional coordinates.
        getVlans():
            Retrieves VLAN information from the switch using NETCONF.
        addVlan(vlan_id, vlan_name):
            Adds a VLAN to the switch with the specified VLAN ID and name.
        deleteInterfaceVlan(interfaces):
            Deletes VLAN configurations on the specified interfaces.
        setInterfaceVlan(interfaces):
            Configures VLANs on the specified interfaces.
    """

    _device_type = "sw"
    _counter = 0
    is_ospf_capable = False
    is_ipsec_capable = False
    is_vlan_capable = True

    def __init__(self, device_parameters, x=0, y=0) -> "Switch":
        super().__init__(device_parameters, x, y)

        # ICON
        switch_icon_img = QImage("graphics/devices/switch.png")
        self.setPixmap(QPixmap.fromImage(switch_icon_img))

        self.vlans = self.getVlans()

    def _getContextMenuItems(self) -> list:
        """
        Switch-specific context menu items.
        """

        items = super()._getContextMenuItems()

        # Enable L3 functions
        enable_l3_functions_item = QAction("Enable L3 functions")
        enable_l3_functions_item.triggered.connect(self.enableL3Functions)
        enable_l3_functions_item.setToolTip("Enabled IP routing on the switch. The switch must support it.")
        items.append(enable_l3_functions_item)

        if self.is_ospf_capable:
            # Show routing table
            show_routing_table_action = QAction("Show routing table")
            show_routing_table_action.triggered.connect(self._showRoutingTable)
            show_routing_table_action.setToolTip("Shows the routing table of the device.")
            items.append(show_routing_table_action)

        return items

    def enableL3Functions(self) -> bool:
        """
        Enables L3 functions on the switch by configuring IP routing. Sets the
        `is_ospf_capable` attribute to True, which enables OSPF configuration and allows
        showing the routing table.
        This method is called from the context menu of the switch device.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """

        try:
            rpc_reply, filter = vlan.enableL3FunctionsWithNetconf(self)
            utils.addPendingChange(self, f"Enable L3 functions", rpc_reply, filter)
            utils.printRpc(rpc_reply, "Enable L3 functions", self)
            self.is_ospf_capable = True
            return True
        except Exception as e:
            utils.printGeneral(f"Error enabling L3 functions: {e}")
            utils.printGeneral(traceback.format_exc())
            return False

    def getVlans(self) -> dict:
        """
        Retrieves VLAN information from the switch using NETCONF.
        Returns:
            dict: The VLAN information
        """

        try:
            vlan_data, rpc_reply = vlan.getVlansWithNetconf(self)
            utils.printRpc(rpc_reply, "Get VLANs", self)
            return(vlan_data)
        except Exception as e:
            utils.printGeneral(f"Error getting VLANs: {e}")
            utils.printGeneral(traceback.format_exc())
            return None

    def addVlan(self, vlan_id, vlan_name) -> bool:
        """
        Adds a VLAN to the switch with the specified VLAN ID and name.
        Updates the self.vlans dictionary.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            rpc_reply, filter = vlan.addVlanWithNetconf(self, vlan_id, vlan_name)
            utils.addPendingChange(self, f"Add VLAN", rpc_reply, filter)
            utils.printRpc(rpc_reply, "Add VLAN", self)
            self.vlans[vlan_id] = {"name": vlan_name}
            return True
        except Exception as e:
            utils.printGeneral(f"Error addin VLAN: {e}")
            utils.printGeneral(traceback.format_exc())
            return False

    def deleteInterfaceVlan(self, interfaces) -> bool:
        """
        Deletes VLAN configurations on the specified interfaces.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """

        try:
            rpc_reply, filter = vlan.deleteInterfaceVlanWithNetconf(self, interfaces)
            utils.addPendingChange(self, f"Delete VLANs on interfaces", rpc_reply, filter)
            utils.printRpc(rpc_reply, "Delete VLANs on interfaces", self)
            return True
        except Exception as e:
            utils.printGeneral(f"Error deleting VLANs on device {self.id}: {e}")
            utils.printGeneral(traceback.format_exc())
            return False

    def setInterfaceVlan(self, interfaces) -> bool:
        """
        Configures VLANs on the specified interfaces.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """

        try:
            rpc_reply, filter = vlan.setInterfaceVlanWithNetconf(self, interfaces)
            utils.addPendingChange(self, f"Set VLANs on interfaces", rpc_reply, filter)
            utils.printRpc(rpc_reply, "Set VLANs on interfaces", self)
            return True
        except Exception as e:
            utils.printGeneral(f"Error setting VLANs on device {self.id}: {e}")
            utils.printGeneral(traceback.format_exc())
            return False


class Firewall(Router):
    """
    Represents a Firewall device, inheriting from the Router class.
    Attributes:
        _device_type (str): The type identifier for the device, set to "fw".
        _counter (int): A class-level counter for tracking instances (default is 0).
        is_security_zone_capable (bool): Indicates whether the firewall supports security zones (default is False).
    Methods:
        __init__(device_parameters, x=0, y=0):
            Initializes a Firewall instance with the given parameters and sets its icon.
    """
    
    _device_type = "fw"
    _counter = 0
    is_security_zone_capable = False

    def __init__(self, device_parameters, x=0, y=0) -> "Firewall":
        super().__init__(device_parameters, x, y)

        # ICON
        firewall_icon_img = QImage("graphics/devices/firewall.png")
        self.setPixmap(QPixmap.fromImage(firewall_icon_img))


# VENDOR-SPECIFIC CLASSES
class IOSXERouter(Router):
    """
    IOSXERouter is a subclass of the Router class, representing a Cisco IOS-XE router
    with additional capabilities, such as IPSec configuration.
    Attributes:
        is_ipsec_capable (bool): Indicates whether the router supports IPSec configuration.
    Methods:
        __init__(device_parameters, x=0, y=0):
            Initializes an instance of IOSXERouter with the given device parameters
            and optional x, y coordinates.
        configureIPSec(dev_parameters, ike_parameters, ipsec_parameters):
            Configures an IPSec tunnel on the router using the provided device, IKE,
            and IPSec parameters. Handles exceptions and logs errors if the configuration fails.
    """
    
    is_ipsec_capable = True

    def __init__(self, device_parameters, x=0, y=0):
        super().__init__(device_parameters, x, y)

    def configureIPSec(self, dev_parameters, ike_parameters, ipsec_parameters) -> bool:
        """
        Configures an IPSec tunnel on the router using the provided device, IKE, and IPSec parameters.
        Called from the IPSec configuration dialog when the user clicks the "Configure" button.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """

        try:
            rpc_reply, filter = security.configureIPSecWithNetconf(self, dev_parameters, ike_parameters, ipsec_parameters)
            utils.addPendingChange(self, f"Configure IPSec tunnel", rpc_reply, filter)
            utils.printRpc(rpc_reply, "Configure IPSec", self)
            return True
        except Exception as e:
            utils.printGeneral(f"Error configuring IPSec on device {self.id}: {e}")
            utils.printGeneral(traceback.format_exc())
            return False


class JUNOSRouter(Router):
    """
    Represents a JUNOS-based router device. Inherits from the Router class. Junos routers dont support IPSec.
    Attributes:
        is_ipsec_capable (bool): Indicates whether the router supports IPsec. Defaults to False.
    Methods:
        __init__(device_parameters, x=0, y=0):
            Initializes a JUNOSRouter instance with the given device parameters and optional coordinates.
    """

    is_ipsec_capable = False

    def __init__(self, device_parameters, x=0, y=0) -> "JUNOSRouter":
        super().__init__(device_parameters, x, y)


class IOSXESwitch(Switch):
    """
    IOSXESwitch is a subclass of the Switch class, representing a network switch
    running the Cisco IOS-XE operating system.
    Methods:
        __init__(device_parameters, x=0, y=0):
            Initializes an instance of the IOSXESwitch class with the given
            device parameters and optional position coordinates.
    """

    def __init__(self, device_parameters, x=0, y=0):
        super().__init__(device_parameters, x, y)


class JUNOSFirewall(Firewall):
    """
    JUNOSFirewall is a subclass of the Firewall class that provides additional functionality 
    specific to JUNOS devices, including support for security zones and IPSec configuration.
    Attributes:
        is_ipsec_capable (bool): Indicates whether the device supports IPSec configuration.
        is_security_zone_capable (bool): Indicates whether the device supports security zones.
    Methods:
        __init__(device_parameters, x=0, y=0):
            Initializes the JUNOSFirewall instance with device parameters and optional coordinates.
        getInterfaces():
            Retrieves the interfaces of the device and enriches the data with security zone information.
        addSecurityZoneDataToInterfacesDict(interfaces_dict: dict):
            Internal method to add security zone data to the provided interfaces dictionary.
        configureInterfacesSecurityZone(interface_id, security_zone, remove_interface_from_zone=False):
            Configures or removes a security zone on a specified interface.
        configureIPSec(dev_parameters, ike_parameters, ipsec_parameters):
            Configures an IPSec tunnel on the device using the provided parameters.
    """

    is_ipsec_capable = True
    is_security_zone_capable = True

    def __init__(self, device_parameters, x=0, y=0) -> "JUNOSFirewall":
        super().__init__(device_parameters, x, y)

    def getInterfaces(self) -> dict:
        """
        Retrieves the interfaces of the device and enriches them with security zone data.
        This method first calls the parent class's `getInterfaces` method to obtain
        the base interface information. It then adds additional security zone data
        to the interfaces dictionary. The security zone information is not present
        in the OpenConfig interfaces YANG model, so it has to be added externally.
        Returns:
            dict: A dictionary containing the interfaces with added security zone data.
        """

        interfaces = super().getInterfaces()
        interfaces_with_security_zone_data = self.addSecurityZoneDataToInterfacesDict(interfaces)
        return interfaces_with_security_zone_data

    def addSecurityZoneDataToInterfacesDict(self, interfaces_dict: dict) -> dict:
        """
        Adds security zone data to the provided interfaces dictionary.
        This method retrieves security zone information from the device using NETCONF,
        processes the data, and updates the given interfaces dictionary with the
        corresponding security zone for each interface.
        Args:
            interfaces_dict (dict): A dictionary containing interface data. The keys
                are interface names, and the values are dictionaries with interface
                attributes.
        Returns:
            dict: The updated interfaces dictionary with security zone information added.
        Raises:
            Exception: If an error occurs during the retrieval or processing of security
                zone data, an error message is logged, and the traceback is printed.
        Notes:
            - The method uses the `getSecurityZonesWithNetconf` function to retrieve
              security zone information from the device.
            - The `utils.convertToEtree` function is used to parse the NETCONF reply
              into an XML tree for easier data extraction.
            - Security zone names and their associated interfaces are extracted from
              the XML tree and added to the `interfaces_dict`.
            - Subinterface numbers are stripped from interface names before adding
              the security zone information, since the security zone is applied to
              the master interface, not the subinterface.
        """

        try:
            rpc_payload, rpc_reply = security.getSecurityZonesWithNetconf(self)
            utils.printRpc(rpc_reply, "Get Security Zones", self)
            
            # Extract security zones names
            rpc_reply_etree = utils.convertToEtree(rpc_reply, self.device_parameters["device_params"])
            security_zones_tags = rpc_reply_etree.findall(".//zones-information/zones-security/zones-security-zonename")
            self.security_zones = [zone.text for zone in security_zones_tags]
    
            # Add security zones data to the interfaces dictionary
            for zone in self.security_zones:
                interfaces_tags = rpc_reply_etree.findall(f".//zones-information/zones-security[zones-security-zonename='{zone}']/zones-security-interfaces/zones-security-interface-name")
                interfaces = [interface.text for interface in interfaces_tags]
                for interface in interfaces:
                    interface_stripped = interface.split(".")[0] # remove subinterface number
                    interfaces_dict[interface_stripped]["security_zone"] = zone

            return(interfaces_dict)

        except Exception as e:
            utils.printGeneral(f"Error getting security zones: {e}")
            utils.printGeneral(traceback.format_exc())
            return
        
    def configureInterfacesSecurityZone(self, interface_id, security_zone, remove_interface_from_zone=False) -> bool:
        """
        Configures or removes a security zone on a specified interface.
        This method calls the `security.configureSecurityZoneToInterfaceWithNetconf` function
        to configure or remove a security zone on the specified interface. The method then
        updates the `self.interfaces` dictionary with the new security zone information.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """

        try:
            if security_zone == " ":
                QMessageBox.critical(None, "Error", "Please select a security zone.")
                return False

            rpc_reply, filter = security.configureSecurityZoneToInterfaceWithNetconf(self, interface_id, security_zone, remove_interface_from_zone)
            if remove_interface_from_zone:
                utils.addPendingChange(self, f"Remove security zone: {security_zone} from interface: {interface_id}", rpc_reply, filter)
                utils.printRpc(rpc_reply, "Remove Security Zone", self)
                self.interfaces[interface_id].pop("security_zone", None) # Update the self.interfaces dictionary
            else:
                utils.addPendingChange(self, f"Set security zone: {security_zone} on interface: {interface_id}", rpc_reply, filter)
                utils.printRpc(rpc_reply, "Set Security Zone", self)
                self.interfaces[interface_id]["security_zone"] = security_zone # Update the self.interfaces dictionary

            return True
        except Exception as e:
            utils.printGeneral(f"Error setting security zone: {e}")
            utils.printGeneral(traceback.format_exc())
            QMessageBox.critical(None, "Error", f"Error setting security zone: {e}")
            return False
        
    # ---------- IPSEC FUNCTIONS ---------- 
    def configureIPSec(self, dev_parameters, ike_parameters, ipsec_parameters) -> bool:
        """
        Configures an IPSec tunnel on the device using the provided parameters.
        Called from the IPSec configuration dialog when the user clicks the "Configure" button.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """

        try:
            rpc_reply, filter = security.configureIPSecWithNetconf(self, dev_parameters, ike_parameters, ipsec_parameters)
            utils.addPendingChange(self, f"Configure IPSec tunnel", rpc_reply, filter)
            utils.printRpc(rpc_reply, "Configure IPSec", self)
            return True
        except Exception as e:
            utils.printGeneral(f"Error configuring IPSec on device {self.id}: {e}")
            utils.printGeneral(traceback.format_exc())
            return False


# ---------- CLONED DEVICE CLASSES: ----------
# This classes are meant to be used in batch configuration dialogs, where the user can configure multiple devices at once.
# The original devices are cloned to the new scene. After the configuration is done, the cloned devices are deleted. The original devices are not affected.
# The ClonedDevice class is a base class for all cloned devices. From this class, specific classes are meant to be inherited.
# - Currently, only OSPFDevice class is implemented, which is used in OSPF configuration dialog.  
class ClonedDevice(QGraphicsPixmapItem):
    """
    A class representing a cloned device in a graphical network configuration tool. 
    This class is used to create a visual and functional duplicate of an original device.
    Attributes:
        original_device (QGraphicsPixmapItem): The original device being cloned.
        device_parameters (dict): Parameters of the original device.
        label (QGraphicsTextItem): A text label displaying the hostname of the device.
        original_cables (list): A copy of the cables connected to the original device.
        cables (list): A list of cables connected to the cloned device.
        cable_connected_interfaces (list): A list of interfaces connected to cables.
        interfaces (list): A list of interfaces of the original device.
        id (int): The unique identifier of the device.
    """

    def __init__(self, original_device) -> "ClonedDevice":
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
    OSPFDevice is a subclass of ClonedDevice that represents a device supposed to be configured with OSPF protocol. 
    This class provides methods to manage OSPF-specific configurations, such as adding and removing OSPF networks, retrieving OSPF 
    networks for interfaces, and configuring OSPF parameters.
    Attributes:
        passive_interfaces (list): A list of interfaces configured as passive for OSPF.
        ospf_networks (dict): A dictionary mapping interface names to their respective OSPF networks.
        router_id (str or None): The OSPF router ID for the device.
    Methods:
        getOSPFNetworks():
            Retrieves a dictionary of OSPF networks for each interface that has a connected cable.
                dict: A dictionary where keys are interface names and values are lists of OSPF networks.
        addOSPFNetwork(network, interface_name):
            Adds an OSPF network to a specific interface.
                network: The network to add.
                interface_name (str): The name of the interface.
        removeOSPFNetwork(network, interface_name):
            Removes an OSPF network from a specific interface.
                network: The network to remove.
                interface_name (str): The name of the interface.
        configureOSPF(area, hello_interval, dead_interval, reference_bandwidth):
            Configures OSPF on the device with the specified parameters.
            Calls the `configureOSPFWithNetconf` function from the `ospf` module.
    """
    
    def __init__(self, original_device) -> "OSPFDevice":
        super().__init__(original_device)

        # OSPF SPECIFIC
        self.passive_interfaces = []
        self.ospf_networks = {} # filling the dictionary must be done externally (from OSPFDialog) after the whole scene is created, because it needs to know about connected cables in the scene
        self.router_id = None

    def getOSPFNetworks(self) -> dict:
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
    
    def addOSPFNetwork(self, network, interface_name) -> None:
        """
        Adds an OSPF network to a specific interface.
        Args:
            network: The network to add.
            interface_name (str): The name of the interface.
        """

        if interface_name not in self.ospf_networks:
            self.ospf_networks[interface_name] = []
        self.ospf_networks[interface_name].append(network)

    def removeOSPFNetwork(self, network, interface_name) -> None:
        """
        Removes an OSPF network from a specific interface.
        Args:
            network: The network to remove.
            interface_name (str): The name of the interface
        """
        self.ospf_networks[interface_name].remove(network)

    def configureOSPF(self, area, hello_interval, dead_interval, reference_bandwidth) -> bool:
        """
        Configures OSPF on the device with the specified parameters. Calls the configureOSPFWithNetconf function from the ospf module. 
        Called from the OSPFDialog, when the user clicks the "OK" button.
        Parameters:
            rpc_reply: The RPC reply from the NETCONF server.
            filter: The filter used in the NETCONF RPC.
        Args:
            area (int): The OSPF area to configure.
            hello_interval (int): The hello interval in seconds.
            dead_interval (int): The dead interval in seconds.
            reference_bandwidth (int): The reference bandwidth in Mbps.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        
        try:
            rpc_reply, filter = ospf.configureOSPFWithNetconf(self, area, hello_interval, dead_interval, reference_bandwidth)
            utils.addPendingChange(self.original_device, f"Configure OSPF area: {area}", rpc_reply, filter)
            utils.printRpc(rpc_reply, "Configure OSPF", self)
            return True
        except Exception as e:
            utils.printGeneral(f"Error configuring OSPF on device {self.original_device.id}: {e}")
            utils.printGeneral(traceback.format_exc())
            return False


# ---------- QT: ----------
class AddDeviceDialog(QDialog):
    """
    A dialog window for adding a network device to the scene. This dialog allows the user to input
    device details such as IP address, port, username, password, and device type.
    Attributes:
        view (QGraphicsView): The view containing the scene where devices are added.
        device_parameters (dict): A dictionary to store the parameters of the device being added.
        addressTextInput (QLineEdit): Input field for the device's IP address and port.
        usernameTextInput (QLineEdit): Input field for the device's username.
        passwordTextInput (QLineEdit): Input field for the device's password.
        deviceTypeComboInput (QComboBox): Dropdown menu for selecting the device type.
        buttons (QDialogButtonBox): OK and Cancel buttons for confirming or rejecting the dialog.
        layout (QVBoxLayout): The layout for arranging the dialog's widgets.
    Methods:
        __init__(view):
            Initializes the dialog, sets up the input fields, buttons, and layout.
        _confirmConnection():
            Validates the input fields, checks for duplicate devices in the scene, and adds the
            device to the scene based on the selected type.
    """

    def __init__(self, view) -> "AddDeviceDialog":
        super().__init__()

        gnc_icon = QPixmap("graphics/icons/gnc.png")
        self.setWindowIcon(QIcon(gnc_icon))

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
        self.deviceTypeComboInput.addItems(["Router - Cisco IOS XE", "Router - Juniper JunOS", "Switch - Cisco IOS XE", "Firewall - Juniper JunOS (SRX)"])
        self.layout.addWidget(self.deviceTypeComboInput)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._confirmConnection)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        # Layout
        self.setLayout(self.layout)

    def _confirmConnection(self) -> None:
        """
        Handles the OK button click event. Validates the input fields, checks for duplicate devices in the scene,
        and adds the device to the scene based on the selected type.
        """

        try:
            # Address + Port
            address_field = self.addressTextInput.text().split(":")
            if len(address_field) == 2:
                self.device_parameters["address"] = ipaddress.ip_address(address_field[0])
                if address_field[1].isdigit() and int(address_field[1]) in range(1, 65536):
                    self.device_parameters["port"] = address_field[1]
                else:
                    raise ValueError("Invalid port number")
            elif len(address_field) == 1:
                self.device_parameters["address"] = ipaddress.ip_address(self.addressTextInput.text())
                self.device_parameters["port"] = 830
            else:
                raise ValueError("Invalid IP address format")

            # Username + Password + Device vendor
            self.device_parameters["username"] = self.usernameTextInput.text()
            self.device_parameters["password"] = self.passwordTextInput.text()
            if "Cisco IOS XE" in self.deviceTypeComboInput.currentText():
                self.device_parameters["device_params"] = "iosxe"
            elif "Juniper JunOS" in self.deviceTypeComboInput.currentText():
                self.device_parameters["device_params"] = "junos"

            # Check if the device with the same address is not already in the scene
            for device in self.view.scene.items():
                if isinstance(device, Device):
                    if device.device_parameters["address"] == self.device_parameters["address"]:
                        QMessageBox.warning(self, "Device already exists", "The device with the same address is already in the scene.")
                        raise ValueError("Device already exists")

            # Add the device with the correct type               
            if self.deviceTypeComboInput.currentText() == "Router - Cisco IOS XE":
                addRouter(self.device_parameters, self.view.scene, "IOSXERouter")
            elif self.deviceTypeComboInput.currentText() == "Router - Juniper JunOS":
                addRouter(self.device_parameters, self.view.scene, "JUNOSRouter")
            elif self.deviceTypeComboInput.currentText() == "Switch - Cisco IOS XE":
                addSwitch(self.device_parameters, self.view.scene, "IOSXESwitch")
            elif self.deviceTypeComboInput.currentText() == "Firewall - Juniper JunOS (SRX)":
                addFirewall(self.device_parameters, self.view.scene, "JUNOSFirewall")

            self.accept()
            
        except ValueError as e:
            QMessageBox.critical(None, "Invalid input", f"Invalid input: {e}")
            utils.printGeneral(traceback.format_exc())
    

class ShowXMLDialog(QDialog):
    """
    A dialog for displaying general XML data in a tree form.
    """

    def __init__(self, data, device, data_type = "XML Data"):
        """
        Initializes the Dialog.
        Args:
            data: The XML data (XML root element, specifically).
            device (Device): The device object for which to display the data.
        Sets up the UI elements and connects the buttons to their respective functions.
        """
    
        super().__init__()

        self.xml_data = data

        self.ui = Ui_XMLDataDialog()
        self.ui.setupUi(self)

        # Setup UI elements
        self.ui.header.setText(f"{data_type} for device: {device.id}")
        self.ui.collapse_button.clicked.connect(self.ui.data_tree.collapseAll)
        self.ui.expand_button.clicked.connect(self.ui.data_tree.expandAll)
        self.ui.close_button_box.rejected.connect(self.reject)
        self.ui.refresh_button.setEnabled(False)
        # Fill the QTreeWidget with the data, takes the XML root element and the QTreeWidget as arguments
        utils.populateTreeWidget(self.ui.data_tree, self.xml_data)

class ShowRoutingTableDialog(ShowXMLDialog):
    def __init__(self, data, device, data_type = "Routing Table"):
        """
        Initializes the dialog for showing the routing table.
        Args:
            data: The XML data (XML root element, specifically).
            device (Device): The device object for which to display the data.
            data_type (str): The type of data being displayed (default is "Routing Table").
        """
        super().__init__(data, device, data_type)
        self.ui.refresh_button.setEnabled(True)
        self.ui.refresh_button.clicked.connect(lambda: self._refreshRoutingTable(device))

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

        utils.populateTreeWidget(self.ui.data_tree, routing_table_etree)

class ShowRunningConfigDialog(ShowXMLDialog):
    def __init__(self, data, device, data_type = "Running Configuration"):
        """
        Initializes the dialog for showing the running configuration.
        Args:
            data: The XML data (XML root element, specifically).
            device (Device): The device object for which to display the data.
            data_type (str): The type of data being displayed (default is "Running Configuration").
        """
        super().__init__(data, device, data_type)
        self.ui.refresh_button.setEnabled(True)
        self.ui.refresh_button.clicked.connect(lambda: self._refreshRunningConfig(device))

    def _refreshRunningConfig(self, device):
        """
        Refreshes the running configuration of the selected device. This method is called when the user clicks the "Refresh" button in the running configuration dialog.
        Args:
            device (Device): The device for which to refresh the running configuration.
        """

        running_config = device.getRunningConfig()
        if device.device_parameters["device_params"] == "iosxe":
            running_config_etree = utils.convertToEtree(running_config, "iosxe")
        elif device.device_parameters["device_params"] == "junos":
            running_config_etree = utils.convertToEtree(running_config, "junos")
        utils.populateTreeWidget(self.ui.data_tree, running_config_etree)