# Other
from ncclient import manager
import sqlite3

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

# Custom
import db_handler
from netconf_functions import *
from dialogs import *

from PySide6.QtWidgets import QMessageBox

class Device(QGraphicsPixmapItem):
    def __init__(self, device_parameters, x=0, y=0):
        super().__init__()

        device_icon_img = QImage("graphics/icons/general.png") # TODO: CHANGE GENERAL ICON
        self.setPixmap(QPixmap.fromImage(device_icon_img))

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setPos(x, y)
        
        self.cables = []

        self.mngr = establishNetconfConnection(device_parameters)
        
        #DEBUG: Show border around device
        if __debug__:
            self.border = QGraphicsRectItem(self.boundingRect())
        
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event) 

        for cable in self.cables:
            cable.updatePosition()
        
        #DEBUG: Show border around device
        if __debug__:
            self.border.setPos(self.scenePos())

    def contextMenuEvent(self, event):
        menu = QMenu()

        # Disconnect from device
        action1_disconnect = QAction("Disconnect from the device")
        action1_disconnect.triggered.connect(self.deleteDevice)
        menu.addAction(action1_disconnect)

        # Rename the device
        action2_rename = QAction("Rename")
        action2_rename.triggered.connect(self.rename)
        menu.addAction(action2_rename)

        # Show NETCONF capabilites
        action3_showNetconfCapabilities = QAction("Show NETCONF Capabilities")
        action3_showNetconfCapabilities.triggered.connect(self.showNetconfCapabilities)
        menu.addAction(action3_showNetconfCapabilities)

        menu.exec(event.screenPos())
        
    def deleteDevice(self):
        demolishNetconfConnection(self.mngr) # Disconnect from NETCONF

        if hasattr(self, 'border'): 
            self.scene().removeItem(self.border) # Delete the DEBUG border, if there is one

        self.scene().removeItem(self)
        #removeItem -> doesnt remove the item from memory, but gives the ownership of the item back to the Python interpreter,
        #which decides when to remove it from the memory. It is not necessary to call the "del" function for deleting the object from memory.

    def rename(self):
        print("rename")
        # TODO: Rename Device

    def showNetconfCapabilities(self):
        pass

    # TODO: Pohlidat timeout, kdyz se zarizeni po necinnosti odpoji

    
class Router(Device):
    _counter = 0
    _registry = {} # To store router instances
    def __init__(self, device_parameters, x=0, y=0):
        super().__init__(device_parameters, x, y)

        #Router icon
        router_icon_img = QImage("graphics/icons/router.png")
        self.setPixmap(QPixmap.fromImage(router_icon_img))

        #ID
        Router._counter += 1
        self.id = f"R{Router._counter}"

        #Label
        self.label = QGraphicsTextItem(str(self.id), self)
        self.label.setDefaultTextColor(QColor(0, 0, 0))
        self.label.setFont(QFont('Arial', 10))
        self.label.setPos(0, self.pixmap().height())
        self.label_border = self.label.boundingRect()
        self.label.setPos((self.pixmap().width() - self.label_border.width()) / 2, self.pixmap().height())

        #DB
        db_handler.insertDevice(db_handler.connection, self.id, 1) # 1 = device_type_id = Router

        #Registry
        Router._registry[self.id] = self

        #NETCONF capabilities
        getNetconfCapabilities(self.mngr, self.id)

    def deleteDevice(self):
        # Delete from DB
        db_handler.deleteDevice(db_handler.connection, self.id) #TODO: use one shared connection, or create and tear down one-shot connections? If one shared, there needs to be a fail-safe in db_handler.py
        
        # Cables
        for cable in self.cables.copy(): # CANNOT MODIFY CONTENTS OF A LIST, WHILE ITERATING THROUGH IT! => .copy()
            cable.removeCable()

        del Router._registry[self.id]
        
        super().deleteDevice()

    def showNetconfCapabilities(self):
        super().showNetconfCapabilities()
        dialog = CapabilitiesDialog(self.id)
        dialog.exec()

        

    @classmethod
    def getRouterInstance(cls, router_id):
        return cls._registry.get(router_id)


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

        self.setLine(self.device_1_center.x(), self.device_1_center.y(), self.device_2_center.x(), self.device_2_center.y())

    def removeCable(self):
        if self in self.device_1.cables:
            self.device_1.cables.remove(self)
        
        if self in self.device_2.cables:
            self.device_2.cables.remove(self)

        self.scene().removeItem(self)
