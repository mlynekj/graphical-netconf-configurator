import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsLineItem, QGraphicsItem, QGraphicsRectItem
from PySide6.QtGui import QPen
from devices import Router, Cable

class MainView(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Network Configurator")
        self.view = MainView()
        self.setCentralWidget(self.view)

        router = self.addRouter(100, 100)
        router2 = self.addRouter(300, 300)

        cable = self.addCable(router, router2)
        
    def addRouter(self, x, y):
        router = Router(x, y)
        self.view.scene.addItem(router)
        
        #DEBUG: zobrazi ohraniceni kolem routeru
        if __debug__:
            self.view.scene.addItem(router.border)
            router.border.setPos(router.scenePos())
            
        return router
    
    def addCable(self, device_1, device_2):
        cable = Cable(device_1, device_2)
        cable.setZValue(-1)                     #presunout objekt "cable" pod vsechny ostatni objekty
        self.view.scene.addItem(cable)

        return cable


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    window.resize(800, 600)
    sys.exit(app.exec())