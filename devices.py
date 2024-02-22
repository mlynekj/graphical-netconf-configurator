from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtGui import QImage, QPixmap

class Router(QGraphicsPixmapItem):
    def __init__(self):
        super().__init__()

        router_image_file = QImage("router.png")

        self.setPixmap(QPixmap.fromImage(router_image_file))
        self.setFlag(QGraphicsItem.ItemIsMovable, True)