import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsLineItem, QGraphicsItem, QGraphicsRectItem, QToolBar, QPushButton, QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox, QComboBox
from PySide6.QtGui import QPen, QBrush, QColor, QIcon, QAction
from devices import Router, Cable

class MainView(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.scene.setBackgroundBrush(QBrush(QColor(255, 255, 255))) #White background

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Network Configurator")
        self.view = MainView()
        self.setCentralWidget(self.view)

        self.createToolBar()

        router = self.addRouter(100, 100)
        router2 = self.addRouter(300, 300)
        router3 = self.addRouter(500, 500)

        cable = self.addCable(router, router2)
        cable2 = self.addCable(router2, router3)
        cable3 = self.addCable(router3, router)

    def createToolBar(self):
        toolbar = QToolBar("Toolbar", self)
        toolbar.setVisible(True)

        action1_connectToDevice = QAction(QIcon(), "Connect to a device", self)
        toolbar.addAction(action1_connectToDevice)
        action1_connectToDevice.triggered.connect(self.addDevicePopup)

        self.addToolBar(toolbar)

    def addDevicePopup(self):
        dialog = QDialog()
        dialog.setWindowTitle("Connect to a device")
        #dialog.setModal()
        layout = QVBoxLayout()

        #Input fields
        address_input = QLineEdit()
        address_input.setPlaceholderText("IP address")
        layout.addWidget(address_input)

        username_input = QLineEdit()
        username_input.setPlaceholderText("Username")
        layout.addWidget(username_input)

        password_input = QLineEdit()
        password_input.setPlaceholderText("Password")
        layout.addWidget(password_input)

        deviceType_combo = QComboBox()
        deviceType_combo.addItems(["Cisco IOS XE", "Juniper"])
        layout.addWidget(deviceType_combo)
        
        #Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec():
            router_name = address_input.text()
            

    def addRouter(self, x, y):
        router = Router(x, y)
        self.view.scene.addItem(router)
        
        #DEBUG: Show border around router
        if __debug__:
            self.view.scene.addItem(router.border)
            router.border.setPos(router.scenePos())
            
        return router
    
    def addCable(self, device_1, device_2):
        cable = Cable(device_1, device_2)
        cable.setZValue(-1)                     #move object "Cable" under all other objects (to the background)
        self.view.scene.addItem(cable)

        return cable

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    window.resize(800, 600)
    sys.exit(app.exec())