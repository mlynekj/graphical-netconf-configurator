from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QGraphicsLineItem, QGraphicsRectItem, QGraphicsSceneMouseEvent, QMenu
from PySide6.QtGui import QImage, QPixmap, QPen, QColor, QAction
from PySide6.QtCore import QLineF
from ncclient import manager
import sqlite3
import db_handler

class Device(QGraphicsPixmapItem):
    def __init__(self, device_parameters, x=0, y=0):
        super().__init__()

        general_image_file = QImage("graphics/icons/general.png") # TODO: CHANGE GENERAL ICON
        self.setPixmap(QPixmap.fromImage(general_image_file))

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setPos(x, y)
        
        self.cables = []

        self.establishNetconfConnection(device_parameters)
        
        #DEBUG: Show border around router
        if __debug__:
            self.border = QGraphicsRectItem(self.boundingRect())
        
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event) 

        for cable in self.cables:
            cable.updatePosition()
        
        #DEBUG: Show border around router
        if __debug__:
            self.border.setPos(self.scenePos())

    def contextMenuEvent(self, event):
        menu = QMenu()
        action1_disconnect = QAction("Disconnect from the device")
        action1_disconnect.triggered.connect(self.deleteDevice)
        menu.addAction(action1_disconnect)

        action2_rename = QAction("Rename")
        action2_rename.triggered.connect(self.rename)
        menu.addAction(action2_rename)

        action3_showNetconfCapabilities = QAction("Show NETCONF Capabilities")
        action3_showNetconfCapabilities.triggered.connect(self.showNetconfCapabilities)
        menu.addAction(action3_showNetconfCapabilities)

        menu.exec(event.screenPos())

    def establishNetconfConnection(self, device_parameters):
        self.mngr = manager.connect(
            host=device_parameters["address"],
            username=device_parameters["username"],
            password=device_parameters["password"],
            device_params={"name":device_parameters["device_params"]},
            hostkey_verify=False)
        
    def deleteDevice(self):
        self.mngr.close_session()

        if hasattr(self, 'border'): 
            self.scene().removeItem(self.border) #Delete the DEBUG border, if there is one

        self.scene().removeItem(self)
        #removeItem -> doesnt remove the item from memory, but gives the ownership of the item back to the Python interpreter,
        #which decides when to remove it from the memory. It is not necessary to call the "del" function for deleting the object from memory.

        if isinstance(self, Router):
            Router._counter -= 1
        #elif isinstance(self, Switch):
        #   Switch._counter -= 1
        #elif ...

        #Delete the device from DB
        #NEEDS TO BE IN THE APPROPRIATE SUBCLASS! (to keep track of the respective id's)

    def rename(self):
        print("rename")
        # TODO: Rename Device + show names on canvas
        # TODO: Pojmenovani zarizeni (R1, ...)

    def showNetconfCapabilities(self):
        print("show caps")
        # TODO: Show NETCONF Capabilities (+ store them before in DB)
        
    # TODO: Pohlidat timeout, kdyz se zarizeni po necinnosti odpoji

    # TODO: Pohlidat exceptiony: timeout pri connectovani, spatne heslo, atd...


class Router(Device):
    _counter = 0
    def __init__(self, device_parameters, x=0, y=0):
        super().__init__(device_parameters, x, y)

        #Router icon
        router_image_file = QImage("graphics/icons/router.png")
        self.setPixmap(QPixmap.fromImage(router_image_file))
        
        #ID
        Router._counter += 1
        self.id = f"R{Router._counter}"

        #DB
        db_handler.insertDevice(db_handler.connection, self.id, 1) # 1 = device_type_id = Router

    def deleteDevice(self):
        db_handler.deleteDevice(db_handler.connection, self.id) #TODO: use one shared connection, or create and tear down one-shot connections? If one shared, there needs to be a fail-safe in db_handler.py
        super().deleteDevice()


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
