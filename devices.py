# QT
from PySide6.QtWidgets import (
    QGraphicsPixmapItem, 
    QGraphicsItem,
    QGraphicsLineItem, 
    QGraphicsRectItem, 
    QGraphicsSceneMouseEvent, 
    QMenu,
    QGraphicsTextItem,
    QToolTip)
from PySide6.QtGui import (
    QImage, 
    QPixmap,
    QPen,
    QColor,
    QAction,
    QFont)
from PySide6.QtCore import (
    QLineF,
    QPointF)

# Other
from ncclient import manager

# Custom
import modules.netconf as netconf
import modules.interfaces as interfaces
import modules.system as system
import modules.helper as helper
import dialogs

from PySide6.QtWidgets import QMessageBox

class Device(QGraphicsPixmapItem):
    _counter = 0 # Used to generate device IDs
    _registry = {} # Used to store device instances
    _device_type = "D"
    
    def __init__(self, device_parameters, x=0, y=0):
        super().__init__()

        self.setAcceptHoverEvents(True)  # Enable mouse hover over events

        self.device_parameters = device_parameters

        # NETCONF CONNECTION
        self.mngr = netconf.establishNetconfConnection(device_parameters) # TODO: Handle timeout, when the device disconnects after some time

        # ICON + CANVAS PLACEMENT
        device_icon_img = QImage("graphics/devices/general.png") # TODO: CHANGE GENERAL ICON
        self.setPixmap(QPixmap.fromImage(device_icon_img))
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setPos(x, y)
        #DEBUG: Show border around device
        if __debug__:
            self.border = QGraphicsRectItem(self.boundingRect())
        
        # CABLES LIST
        self.cables = []

        # ID
        type(self)._counter += 1
        self.id = self.generateID()

        # DEVICE INFORMATION
        self.netconf_capabilities = self.dev_GetNetconfCapabilites()
        self.interfaces = self.dev_GetInterfaces(self)
        self.hostname = self.dev_GetHostname()

        # LABEL (Hostname)
        self.label = QGraphicsTextItem(str(self.hostname), self)
        self.label.setDefaultTextColor(QColor(0, 0, 0))
        self.label.setFont(QFont('Arial', 10))
        self.label.setPos(0, self.pixmap().height())
        self.label_border = self.label.boundingRect()
        self.label.setPos((self.pixmap().width() - self.label_border.width()) / 2, self.pixmap().height())

        # REGISTRY
        type(self)._registry[self.id] = self

    def refreshHostnameLabel(self):
        self.hostname = self.dev_GetHostname()

        self.label.setPlainText(str(self.hostname))
        self.label_border = self.label.boundingRect()
        self.label.setPos((self.pixmap().width() - self.label_border.width()) / 2, self.pixmap().height())

    def generateID(self):
        return(type(self)._device_type + str(type(self)._counter))

    def deleteDevice(self):
        netconf.demolishNetconfConnection(self) # Disconnect from NETCONF

        if hasattr(self, 'border'): 
            self.scene().removeItem(self.border) # Delete the DEBUG border, if there is one

        self.scene().removeItem(self)
    
        # Cables
        for cable in self.cables.copy(): # CANNOT MODIFY CONTENTS OF A LIST, WHILE ITERATING THROUGH IT! => .copy()
            cable.removeCable()

        del type(self)._registry[self.id]

    # ---------- MOUSE EVENTS FUNCTIONS ---------- 
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event) 

        for cable in self.cables:
            cable.updatePosition()
        
        # DEBUG: Show border around device
        if __debug__:
            self.border.setPos(self.scenePos())

    def hoverEnterEvent(self, event):
        QToolTip.showText(event.screenPos(), f"Device ID: {self.id}")

    def hoverLeaveEvent(self, event):
        QToolTip.hideText()

    def contextMenuEvent(self, event):
        """ Right-click menu """
        menu = QMenu()

        # Disconnect from device
        disconnect_action = QAction("Disconnect from the device")
        disconnect_action.triggered.connect(self.deleteDevice)
        menu.addAction(disconnect_action)

        # Show NETCONF capabilites
        show_netconf_capabilities_action = QAction("Show NETCONF Capabilities")
        show_netconf_capabilities_action.triggered.connect(self.show_CapabilitiesDialog)
        menu.addAction(show_netconf_capabilities_action)

        # Show interfaces
        show_interfaces_action = QAction("Show Interfaces")
        show_interfaces_action.triggered.connect(self.show_ListInterfacesDialog)
        menu.addAction(show_interfaces_action)

        # Edit Hostname
        edit_hostname_action = QAction("Edit Hostname")
        edit_hostname_action.triggered.connect(self.show_EditHostnameDialog)
        menu.addAction(edit_hostname_action)

        # Discard all pending changes
        discard_changes_action = QAction("Discard all pending changes from candidate datastore")
        discard_changes_action.triggered.connect(lambda: netconf.discardChanges(self))
        menu.addAction(discard_changes_action)

        menu.exec(event.screenPos())

    # ---------- DIALOG SHOW FUNCTIONS ---------- 
    def show_CapabilitiesDialog(self):
        dialog = dialogs.CapabilitiesDialog(self)
        dialog.exec()

    def show_ListInterfacesDialog(self):
        dialog = dialogs.DeviceInterfacesDialog(self)
        dialog.exec()

    def show_EditHostnameDialog(self):
        dialog = dialogs.EditHostnameDialog(self)
        dialog.exec()

    def dev_GetNetconfCapabilites(self):
        return(netconf.getNetconfCapabilities(self))
    
    # ---------- HOSTNAME MANIPULATION FUNCTIONS ---------- 
    def dev_GetHostname(self):
        return(system.getHostname(self))
    
    def dev_SetHostname(self, new_hostname):
        rpc_reply = system.setHostname(self, new_hostname)
        rpc_reply = netconf.commitChanges(self)

    # ---------- INTERFACE MANIPULATION FUNCTIONS ---------- 
    def dev_GetInterfaces(self, getIPs=False):
        return(interfaces.getInterfaceList(self, getIPs))

    def dev_GetSubinterfaces(self, interface_id):
        return(interfaces.getSubinterfaces(self, interface_id))
    
    def dev_DeleteInterfaceIP(self, interface_id, subinterface_index, old_ip):
        rpc_reply = interfaces.deleteIp(self, interface_id, subinterface_index, old_ip)
        rpc_reply = netconf.commitChanges(self)

    def dev_SetInterfaceIP(self, interface_id, subinterface_index, new_ip):
        rpc_reply = interfaces.setIp(self, interface_id, subinterface_index, new_ip)
        rpc_reply = netconf.commitChanges(self)

    def dev_ReplaceInterfaceIP(self, interface_id, subinterface_index, old_ip, new_ip):
        rpc_reply = interfaces.deleteIp(self, interface_id, subinterface_index, old_ip)
        rpc_reply = interfaces.setIp(self, interface_id, subinterface_index, new_ip)
        rpc_reply = netconf.commitChanges(self)
    
    # ---------- REGISTRY FUNCTIONS ---------- 
    @classmethod
    def getDeviceInstance(cls, device_id):
        return cls._registry.get(device_id)
    
    @classmethod
    def getAllDeviceInstances(cls):
        return list(cls._registry.keys())

    
class Router(Device):
    _device_type = "R"

    def __init__(self, device_parameters, x=0, y=0):
        super().__init__(device_parameters, x, y)

        # ICON
        router_icon_img = QImage("graphics/devices/router.png")
        self.setPixmap(QPixmap.fromImage(router_icon_img))


class Cable(QGraphicsLineItem):
    def __init__(self, device_1, device_2):
        super().__init__()

        self.device_1 = device_1
        self.device_2 = device_2

        self.device_1.cables.append(self)
        self.device_2.cables.append(self)

        self.setPen(QPen(QColor(0, 0, 0), 3))

        self.updatePosition()

    def updatePosition(self):
        self.device_1_center = self.device_1.sceneBoundingRect().center()
        self.device_2_center = self.device_2.sceneBoundingRect().center()

        self.setLine(self.device_1_center.x(), 
                     self.device_1_center.y(), 
                     self.device_2_center.x(), 
                     self.device_2_center.y())

    def removeCable(self):
        if self in self.device_1.cables:
            self.device_1.cables.remove(self)
        
        if self in self.device_2.cables:
            self.device_2.cables.remove(self)

        self.scene().removeItem(self)
