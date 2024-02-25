from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QGraphicsLineItem, QGraphicsRectItem, QGraphicsSceneMouseEvent
from PySide6.QtGui import QImage, QPixmap, QPen, QColor
from PySide6.QtCore import QLineF

class Router(QGraphicsPixmapItem):
    def __init__(self, x=0, y=0):
        super().__init__()

        router_image_file = QImage("router.png")

        self.setPixmap(QPixmap.fromImage(router_image_file))
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setPos(x, y)
        
        self.cables = []

        #DEBUG: zobrazi ohraniceni kolem routeru
        if __debug__:
            self.border = QGraphicsRectItem(self.boundingRect())
        
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        
        for cable in self.cables:
            cable.updatePosition()
        
        #DEBUG: zobrazi ohraniceni kolem routeru
        if __debug__:
            self.updateBorderPosition()

    def updateBorderPosition(self):
        self.border.setPos(self.scenePos())

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
