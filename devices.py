from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QGraphicsLineItem, QGraphicsRectItem, QGraphicsSceneMouseEvent
from PySide6.QtGui import QImage, QPixmap, QPen, QColor
from PySide6.QtCore import QLineF
from ncclient import manager

class Device(QGraphicsPixmapItem):
    def __init__(self, device_parameters, x=0, y=0):
        super().__init__()

        #General ICON, used only if different icon not specified
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

    def establishNetconfConnection(self, device_parameters):
        self.mngr = manager.connect(
            host=device_parameters["address"],
            username=device_parameters["username"],
            password=device_parameters["password"],
            device_params={"name":device_parameters["device_params"]},
            hostkey_verify=False)
        
    # TODO: Pohlidat timeout, kdyz se zarizeni po necinnosti odpoji

    # TODO: Pohlidat exceptiony: timeout pri connectovani, spatne heslo, atd...

    # TODO: Udelat right-click menu

    # TODO: Pojmenovani zarizeni (R1, ...)

    # TODO: Right-click menu:
    #           prejmenovat
    #           odpojit
    #           zobrazit capabilities

class Router(Device):
    def __init__(self, device_parameters, x=0, y=0):
        super().__init__(device_parameters, x, y)

        #Router icon
        router_image_file = QImage("graphics/icons/router.png")
        self.setPixmap(QPixmap.fromImage(router_image_file))
    
        
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
