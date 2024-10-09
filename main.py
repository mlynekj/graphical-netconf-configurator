# Other
import sys

# QT
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QGraphicsView, 
    QGraphicsScene, 
    QGraphicsLineItem, 
    QGraphicsItem, 
    QGraphicsRectItem, 
    QToolBar, 
    QPushButton, 
    QDialog, 
    QVBoxLayout, 
    QLineEdit, 
    QDialogButtonBox, 
    QComboBox, 
    QWidget)
from PySide6.QtGui import (
    QPen, 
    QBrush, 
    QColor, 
    QIcon, 
    QAction,
    QPixmap)

# Custom
from devices import Router, Cable
import db_handler


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

        #router = self.addRouter(100, 100)
        #router2 = self.addRouter(300, 300)
        #router3 = self.addRouter(500, 500)

        #cable = self.addCable(router, router2)
        #cable2 = self.addCable(router2, router3)
        #cable3 = self.addCable(router3, router)

    def createToolBar(self):
        toolbar = QToolBar("Toolbar", self)
        toolbar.setVisible(True)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setMovable(False)

        #Connect to a device
        plus_icon_img = QIcon(QPixmap("graphics/icons/plus.png")) #https://www.freepik.com/icon/add_1082378#fromView=family&page=1&position=1&uuid=d639dba2-0441-47bb-a400-3b47c2034665
        action1_connectToDevice = QAction(plus_icon_img, "Connect to a device", self)
        action1_connectToDevice.triggered.connect(self.showDeviceConnectionDialog)
        toolbar.addAction(action1_connectToDevice)

        #DEBUG BUTTON
        if __debug__:
            action99_debug = QAction("DEBUG", self)
            action99_debug.triggered.connect(self.showDebugDialog)
            toolbar.addAction(action99_debug)

        self.addToolBar(toolbar)

    def showDeviceConnectionDialog(self):
        dialog = AddDeviceDialog(self.addRouter)
        dialog.exec()

    #DEBUG:
    def showDebugDialog(self):
        dialog = DebugDialog(self.addCable, self.removeCable)
        dialog.exec()

    def addRouter(self, device_parameters, x, y):
        router = Router(device_parameters, x, y)
        self.view.scene.addItem(router)
        
        #DEBUG: Show border around router
        if __debug__:
            self.view.scene.addItem(router.border)
            router.border.setPos(router.scenePos())
            
        return router
        
    
    def addCable(self, device_1, device_2):
        cable = Cable(device_1, device_2)
        cable.setZValue(-1) #All cables to the background
        self.view.scene.addItem(cable)

        return cable
    
    def removeCable(self, device_1, device_2):        
        cable_to_be_removed = [cable for cable in device_1.cables if cable in device_2.cables]
        cable_to_be_removed[0].deleteCable()

class AddDeviceDialog(QDialog):
    device_parameters = {}

    def __init__(self, addRouter_callback):
        super().__init__()

        self.setWindowTitle("Add a device")
        self.addRouter_callback = addRouter_callback
        self.setModal(True)
        layout = QVBoxLayout()

        #Input fields
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("IP address")
        layout.addWidget(self.address_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        layout.addWidget(self.password_input)

        self.deviceType_combo = QComboBox()
        self.deviceType_combo.addItems(["Cisco IOS XE", "Juniper"])
        layout.addWidget(self.deviceType_combo)

        #DEBUG: Testing connection for debugging
        if __debug__:
            self.address_input.setText("10.0.0.201")
            self.username_input.setText("jakub")
            self.password_input.setText("cisco")

        #Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.confirmConnection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def confirmConnection(self):
        self.device_parameters["address"] = self.address_input.text()
        self.device_parameters["username"] = self.username_input.text()
        self.device_parameters["password"] = self.password_input.text()
        if self.deviceType_combo.currentText() == "Cisco IOS XE":
            self.device_parameters["device_params"] = "iosxe"
        elif self.deviceType_combo.currentText() == "Juniper":
            self.device_parameters["device_params"] = "junos"

        self.addRouter_callback(device_parameters = self.device_parameters, x=0, y=0)
        self.accept()


class DebugDialog(QDialog):
    def __init__(self, addCable_callback, removeCable_callback):
        super().__init__()

        self.addCable_callback = addCable_callback
        self.removeCable_callback = removeCable_callback

        self.setWindowTitle("Debug")
        layout = QVBoxLayout()

        #Input fields
        cursor = db_handler.connection.cursor()
        cursor.execute("SELECT Name FROM Device")
        devices = cursor.fetchall()
        devices_processed = []
        for device in devices:
            devices_processed.append(device[0])

        self.device1_combo = QComboBox()
        self.device1_combo.addItems(devices_processed)
        layout.addWidget(self.device1_combo)

        self.device2_combo = QComboBox()
        self.device2_combo.addItems(devices_processed)
        layout.addWidget(self.device2_combo)

        #Buttons
        self.button_box = QDialogButtonBox()
        button1_addCable = QPushButton("ADD CABLE")
        button2_removeCable = QPushButton("REMOVE CABLE")
        self.button_box.addButton(button1_addCable, QDialogButtonBox.AcceptRole)
        self.button_box.addButton(button2_removeCable, QDialogButtonBox.AcceptRole)
        button1_addCable.clicked.connect(self.addCableDebug)
        button2_removeCable.clicked.connect(self.removeCableDebug)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def addCableDebug(self):
        self.addCable_callback(Router.getRouterInstance(self.device1_combo.currentText()), Router.getRouterInstance(self.device2_combo.currentText()))
        self.accept()

    def removeCableDebug(self):
        self.removeCable_callback(Router.getRouterInstance(self.device1_combo.currentText()), Router.getRouterInstance(self.device2_combo.currentText()))
        self.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    window.resize(800, 600)

    sys.exit(app.exec())