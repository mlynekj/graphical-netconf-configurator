# QT
from PySide6.QtWidgets import (
    QGraphicsPixmapItem, 
    QGraphicsItem,
    QGraphicsLineItem, 
    QGraphicsRectItem, 
    QGraphicsSceneMouseEvent, 
    QMenu,
    QGraphicsTextItem)
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
import dialogs

from PySide6.QtWidgets import QMessageBox

class Device(QGraphicsPixmapItem):
    _counter = 0 # Used to generate device IDs
    _registry = {} # Used to store device instances
    _device_type = "D"
    
    def __init__(self, device_parameters, x=0, y=0):
        super().__init__()

        self.device_parameters = device_parameters

        # NETCONF CONNECTION
        self.mngr = netconf.establishNetconfConnection(device_parameters) # TODO: Handle timeout, when the device disconnects after some time

        # ICON + CANVAS PLACEMENT
        device_icon_img = QImage("graphics/icons/general.png") # TODO: CHANGE GENERAL ICON
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

        # LABEL
        self.label = QGraphicsTextItem(str(self.id), self)
        self.label.setDefaultTextColor(QColor(0, 0, 0))
        self.label.setFont(QFont('Arial', 10))
        self.label.setPos(0, self.pixmap().height())
        self.label_border = self.label.boundingRect()
        self.label.setPos((self.pixmap().width() - self.label_border.width()) / 2, self.pixmap().height())

        # REGISTRY
        type(self)._registry[self.id] = self

        # DEVICE INFORMATION
        self.netconf_capabilities = self.dev_GetNetconfCapabilites()
        self.interfaces = self.dev_GetInterfaces(self)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event) 

        for cable in self.cables:
            cable.updatePosition()
        
        # DEBUG: Show border around device
        if __debug__:
            self.border.setPos(self.scenePos())

    def generateID(self):
        return(type(self)._device_type + str(type(self)._counter))

    def contextMenuEvent(self, event):
        # Right-click menu
        menu = QMenu()

        # Disconnect from device
        disconnect_action = QAction("Disconnect from the device")
        disconnect_action.triggered.connect(self.deleteDevice)
        menu.addAction(disconnect_action)

        # Show NETCONF capabilites
        show_netconf_capabilities_action = QAction("Show NETCONF Capabilities")
        show_netconf_capabilities_action.triggered.connect(self.showNetconfCapabilities)
        menu.addAction(show_netconf_capabilities_action)

        # Show interfaces
        show_interfaces_action = QAction("Show Interfaces")
        show_interfaces_action.triggered.connect(self.showInterfaces)
        menu.addAction(show_interfaces_action)

        menu.exec(event.screenPos())
        
    def deleteDevice(self):
        netconf.demolishNetconfConnection(self.mngr) # Disconnect from NETCONF

        if hasattr(self, 'border'): 
            self.scene().removeItem(self.border) # Delete the DEBUG border, if there is one

        self.scene().removeItem(self)
    
        # Cables
        for cable in self.cables.copy(): # CANNOT MODIFY CONTENTS OF A LIST, WHILE ITERATING THROUGH IT! => .copy()
            cable.removeCable()

        del type(self)._registry[self.id]

    def showNetconfCapabilities(self):
        dialog = dialogs.CapabilitiesDialog(self)
        dialog.exec()

    def showInterfaces(self):
        dialog = dialogs.ListInterfacesDialog(self)
        dialog.exec()

    def dev_GetNetconfCapabilites(self):
        return(netconf.getNetconfCapabilities(self.mngr))

    # INTERFACE MANIPULATION FUNCTIONS
    def dev_GetInterfaces(self, getIPs=False):
        return(interfaces.getInterfaceList(self, getIPs))

    def dev_GetSubinterfaces(self, interface_id):
        return(interfaces.getSubinterfaces(self, interface_id))
    
    def dev_DeleteInterfaceIP(self, interface_id, subinterface_index, old_ip):
        rpc_reply = interfaces.deleteIp(self, interface_id, subinterface_index, old_ip)
        rpc_reply = netconf.commitChanges(self.mngr)

    def dev_SetInterfaceIP(self, interface_id, subinterface_index, new_ip):
        rpc_reply = interfaces.setIp(self, interface_id, subinterface_index, new_ip)
        rpc_reply = netconf.commitChanges(self.mngr)

    def dev_ReplaceInterfaceIP(self, interface_id, subinterface_index, old_ip, new_ip):
        rpc_reply = interfaces.deleteIp(self, interface_id, subinterface_index, old_ip)
        rpc_reply = interfaces.setIp(self, interface_id, subinterface_index, new_ip)
        rpc_reply = netconf.commitChanges(self.mngr)
    
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
        router_icon_img = QImage("graphics/icons/router.png")
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
