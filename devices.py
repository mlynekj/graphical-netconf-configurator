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
    QVBoxLayout)
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
import helper as helper
from signals import signal_manager


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
            self.addressTextInput.setText("172.16.10.251")
            self.usernameTextInput.setText("jakub")
            self.passwordTextInput.setText("cisco")

    def _confirmConnection(self):
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

        # Device type
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

class Device(QGraphicsPixmapItem):
    _counter = 0 # Used to generate device IDs
    _registry = {} # Used to store device instances
    _device_type = "D"
    
    def __init__(self, device_parameters, x=0, y=0):
        super().__init__()

        self.setAcceptHoverEvents(True)  # Enable mouse hover over events

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

        # FLAGS
        self.has_pending_changes = False
        self.has_updated_hostname = False

        # ID
        type(self)._counter += 1
        self.id = self._generateID()

        # DEVICE INFORMATION
        self.netconf_capabilities = self._getNetconfCapabilites()
        self.interfaces = self._getInterfaces()
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
        netconf.demolishNetconfConnection(self) # Disconnect from NETCONF serve

        self.scene().removeItem(self)
    
        for cable in self.cables.copy(): # cannot modify contents of a list, while iterating through it! => .copy()
            cable.removeCable()

        del type(self)._registry[self.id]
        helper.printGeneral(f"Connection to device: {self.device_parameters['address']} has been closed.")

    def discardChanges(self):
        try:
            rpc_reply = netconf.discardNetconfChanges(self)
            helper.printRpc(rpc_reply, "Discard changes", self.hostname)
            self.has_pending_changes = False
            signal_manager.allPendingChangesDiscarded.emit(self.id)
        except Exception as e:
            helper.printGeneral(f"Error discarding changes: {e}")
            return

    def commitChanges(self, bulk_commit=False):
        try:
            if not bulk_commit:
                rpc_reply = netconf.commitNetconfChanges(self)
                helper.printRpc(rpc_reply, "Commit changes", self.hostname)
                self.has_pending_changes = False
                signal_manager.allPendingChangesCommitted.emit(self.id) # TODO:
            else:
                pass
                # TODO: udelat logiku hromadnych commit - nejake jednotne vypsani zmen, hromadne nulovani flagu, atd.
        except Exception as e:
            helper.printGeneral(f"Error committing changes: {e}")
            return

    def updateCablePositions(self):
        for cable in self.cables:
            cable.updatePosition()    

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

    def contextMenuEvent(self, event):
        """
        Context menu event for the device.
        This method creates a context menu with several actions:
        - Disconnect from the device
        - Show NETCONF Capabilities
        - Show Interfaces
        - Edit Hostname
        - Discard all pending changes from candidate datastore
        Each action is connected to its respective method to perform the desired operation.
        """
        
        menu = QMenu()
        menu.setToolTipsVisible(True)

        # Disconnect from device
        disconnect_action = QAction("Disconnect from the device")
        disconnect_action.triggered.connect(self._deleteDevice)
        disconnect_action.setToolTip("Disconnects from the device and removes it from the canvas.")
        menu.addAction(disconnect_action)

        # Show NETCONF capabilites
        show_netconf_capabilities_action = QAction("Show NETCONF Capabilities")
        show_netconf_capabilities_action.triggered.connect(self._showNetconfCapabilitiesDialog)
        show_netconf_capabilities_action.setToolTip("Shows the NETCONF capabilities of the device.")
        menu.addAction(show_netconf_capabilities_action)

        # Show interfaces
        show_interfaces_action = QAction("Show Interfaces")
        show_interfaces_action.triggered.connect(self._showDeviceInterfacesDialog)
        show_interfaces_action.setToolTip("Shows the configuration dialog for the device interfaces.")
        menu.addAction(show_interfaces_action)

        # Edit Hostname
        edit_hostname_action = QAction("Edit Hostname")
        edit_hostname_action.triggered.connect(self._showHostnameDialog)
        edit_hostname_action.setToolTip("Shows the configuration dialog for the hostname of the device.")
        menu.addAction(edit_hostname_action)

        # Discard all pending changes
        discard_changes_action = QAction("Discard all pending changes from candidate datastore")
        discrd_changes_action.triggered.connect(self._discardChanges)
        discard_changes_action.setToolTip("Discards all changes uploaded to the candidate datastore of the device.")
        menu.addAction(discard_changes_action)

        menu.exec(event.screenPos())

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
        return(system.getHostnameWithNetconf(self))
    
    def setHostname(self, new_hostname):
        rpc_reply = system.setHostnameWithNetconf(self, new_hostname)
        helper.addPendingChange(self, f"Set hostname: {new_hostname}")
        helper.printRpc(rpc_reply, "Set Hostname", self.hostname)

    # ---------- INTERFACE MANIPULATION FUNCTIONS ---------- 
    def _getInterfaces(self, getIPs=False):
        return(interfaces.getInterfaceListWithNetconf(self, getIPs))

    def getSubinterfaces(self, interface_id):
        return(interfaces.getSubinterfacesWithNetconf(self, interface_id))
    
    def deleteInterfaceIP(self, interface_id, subinterface_index, old_ip):
        rpc_reply = interfaces.deleteIpWithNetconf(self, interface_id, subinterface_index, old_ip)
        helper.addPendingChange(self, f"Delete IP: {old_ip} from interface: {interface_id}.{subinterface_index}")
        helper.printRpc(rpc_reply, "Delete IP", self.hostname)

    def setInterfaceIP(self, interface_id, subinterface_index, new_ip):
        rpc_reply = interfaces.setIpWithNetconf(self, interface_id, subinterface_index, new_ip)
        helper.addPendingChange(self, f"Set IP: {new_ip} on interface: {interface_id}.{subinterface_index}")
        helper.printRpc(rpc_reply, "Set IP", self.hostname)

    def replaceInterfaceIP(self, interface_id, subinterface_index, old_ip, new_ip):
        rpc_reply_delete = interfaces.deleteIpWithNetconf(self, interface_id, subinterface_index, old_ip)
        rpc_reply_set = interfaces.setIpWithNetconf(self, interface_id, subinterface_index, new_ip)
        helper.addPendingChange(self, f"Replace IP: {old_ip} with {new_ip} on interface: {interface_id}.{subinterface_index}")
        helper.printRpc(rpc_reply_delete, "Delete IP", self.hostname)
        helper.printRpc(rpc_reply_set, "Set IP", self.hostname)
    
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

        # Router specific functions go here

class Switch(Device):
    _device_type = "S"

    def __init__(self, device_parameters, x=0, y=0):
        super().__init__(device_parameters, x, y)

        # ICON
        switch_icon_img = QImage("graphics/devices/switch.png")
        self.setPixmap(QPixmap.fromImage(switch_icon_img))

        # Switch specific functions go here