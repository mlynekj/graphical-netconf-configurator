# Qt
from PySide6.QtWidgets import (
    QDialog, 
    QVBoxLayout,
    QHBoxLayout, 
    QScrollArea, 
    QWidget, 
    QLabel, 
    QPushButton,
    QComboBox,
    QDialogButtonBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QStyle,
    QToolBar,
    QMessageBox,
    QGraphicsView,
    QGraphicsScene,
    QCheckBox,
    QAbstractItemView)
from PySide6.QtCore import Qt, QSize, Slot
from PySide6.QtGui import QFont, QGuiApplication, QAction

from ui.ui_ospfdialog import Ui_OSPFDialog

# Other
import ipaddress
from devices import ClonedDevice
import sys
from PySide6.QtCore import QFile

class OSPFDialog(QDialog):
    def __init__(self, scene=None):
        super().__init__()

        self.scene = scene
        self.ui = Ui_OSPFDialog()
        self.ui.setupUi(self)

        self.ui.graphicsView.setScene(self.scene)

        # Passive interfaces
        self.ui.passive_interfaces_table.setColumnCount(2)
        self.ui.passive_interfaces_table.setHorizontalHeaderLabels(["Interface", "Passive"])
        self.ui.passive_interfaces_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.passive_interfaces_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.ui.passive_interfaces_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.passive_interfaces_table.setSortingEnabled(True)

        # Networks
        self.ui.networks_table.setColumnCount(2)
        self.ui.networks_table.setHorizontalHeaderLabels(["Network", "Interface"])
        self.ui.networks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.networks_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.ui.networks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.networks_table.setSortingEnabled(True)

        # When a device is selected on the scene, connect the signal to the slot onSelectionChanged
        self.scene.selectionChanged.connect(self.onSelectionChanged)

    @Slot()
    def onSelectionChanged(self):
        selected_items = self.scene.selectedItems()
        for item in selected_items:
            if isinstance(item, ClonedDevice):
                self.fillPassiveInterfacesTable(item)
                self.fillNetworksTable(item)

    def fillPassiveInterfacesTable(self, device):
        interfaces = device.interfaces
        passive_interfaces = device.passive_interfaces
        if interfaces:
            self.ui.passive_interfaces_table.setRowCount(len(interfaces))
            for row, (interface) in enumerate(interfaces.items()):      
                # Interface name
                interface_item = QTableWidgetItem(interface[0])
                interface_item.setFlags(interface_item.flags() ^ Qt.ItemIsEditable)  # Non-editable cells
                self.ui.passive_interfaces_table.setItem(row, 0, interface_item)
                
                # Checkbox
                checkbox_item = QCheckBox()
                if interface[0] in passive_interfaces:
                    checkbox_item.setChecked(True)
                else:
                    checkbox_item.setChecked(False)
                checkbox_item.clicked.connect(lambda state, row=row: self.onPassiveInterfaceCheckboxChange(row, device))
                self.ui.passive_interfaces_table.setCellWidget(row, 1, checkbox_item)
                self.ui.passive_interfaces_table.cellWidget(row, 1).setStyleSheet("QCheckBox { margin-left: auto; margin-right: auto; }") # Center horizontally
        else :
            self.ui.passive_interfaces_table.setRowCount(1)
            self.ui.passive_interfaces_table.setColumnCount(1)
            self.ui.passive_interfaces_table.setItem(0, 0, QTableWidgetItem("No interfaces found!"))
        
    def onPassiveInterfaceCheckboxChange(self, row, device):
        if self.ui.passive_interfaces_table.cellWidget(row, 1).isChecked():
            device.passive_interfaces.append(self.ui.passive_interfaces_table.item(row, 0).text())
        else:
            device.passive_interfaces.remove(self.ui.passive_interfaces_table.item(row, 0).text())

    def fillNetworksTable(self, device):
        self.ui.networks_table.setRowCount(0)
        
        networks = device.ospf_networks
        for interface_name, interface_networks in networks.items():
            for network in interface_networks:
                self.addNetworkToTable(network, interface_name)
    
    def addNetworkToTable(self, network, interface_name):
        rowPosition = self.ui.networks_table.rowCount()
        self.ui.networks_table.insertRow(rowPosition)
        self.ui.networks_table.setItem(rowPosition, 0, QTableWidgetItem(str(network)))
        self.ui.networks_table.setItem(rowPosition, 1, QTableWidgetItem(interface_name))
