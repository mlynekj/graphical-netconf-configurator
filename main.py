import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene
from devices import Router

class MainView(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        self.view = MainView()
        self.setCentralWidget(self.view)

        self.router = Router()
        self.view.scene.addItem(self.router)

        self.router2 = Router()
        self.view.scene.addItem(self.router2)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    window.resize(800, 600)
    sys.exit(app.exec())