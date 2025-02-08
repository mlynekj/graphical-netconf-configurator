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
from ui.ui_addospfnetworkdialog import Ui_AddOSPFNetworkDialog

# Other
import ipaddress
from devices import ClonedDevice
import sys
from PySide6.QtCore import QFile

class OSPFDialog(QDialog):
    def __init__(self, scene=None):
        super().__init__()

        self.selected_device = None
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
        self.ui.delete_network_button.clicked.connect(self.deleteNetworkButtonHandler) # "delete network" button
        self.ui.add_network_button.clicked.connect(self.addNetworkButtonHandler) # "add network" button

        # When a device is selected on the scene, connect the signal to the slot onSelectionChanged
        self.scene.selectionChanged.connect(self.onSelectionChanged)

    @Slot()
    def onSelectionChanged(self):
        """
        Slot function that gets called when a device is clicked on in the cloned scene.
        Sets the selected device to the selected item and refreshes the passive interfaces and OSPF networks tables.
        """
        selected_items = self.scene.selectedItems()
        for item in selected_items:
            if isinstance(item, ClonedDevice):
                self.selected_device = item
                self.refreshPassiveInterfacesTable()
                self.refreshOSPFNetworksTable()

    def refreshPassiveInterfacesTable(self):
        """
        Loads and refreshes the passive interfaces table in the UI.
        Information about the passive interfaces is taken from the selected device list - "passive_interfaces".
        """

        interfaces = self.selected_device.interfaces
        passive_interfaces = self.selected_device.passive_interfaces
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
                checkbox_item.clicked.connect(lambda state, row=row: self.onPassiveInterfaceCheckboxChange(row))
                self.ui.passive_interfaces_table.setCellWidget(row, 1, checkbox_item)
                self.ui.passive_interfaces_table.cellWidget(row, 1).setStyleSheet("QCheckBox { margin-left: auto; margin-right: auto; }") # Center horizontally
        else :
            self.ui.passive_interfaces_table.setRowCount(1)
            self.ui.passive_interfaces_table.setColumnCount(1)
            self.ui.passive_interfaces_table.setItem(0, 0, QTableWidgetItem("No interfaces found!"))
        
    def onPassiveInterfaceCheckboxChange(self, row):
        """
        Checks for the state of the checkbox in the passive interfaces table (for each interface) and updates the selected device's "passive_interfaces" list.
        """

        if self.ui.passive_interfaces_table.cellWidget(row, 1).isChecked():
            self.selected_device.passive_interfaces.append(self.ui.passive_interfaces_table.item(row, 0).text())
        else:
            self.selected_device.passive_interfaces.remove(self.ui.passive_interfaces_table.item(row, 0).text())

    def refreshOSPFNetworksTable(self):
        """
        Loads and refreshes the OSPF networks in the UI.
        Information about the OSPF networks is taken from the selected device's list - "ospf_networks".
        """
                
        self.ui.networks_table.setRowCount(0)
        
        networks = self.selected_device.ospf_networks
        for interface_name, interface_networks in networks.items():
            for network in interface_networks:
                self._insertNetworkIntoTable(network, interface_name)
    
    def _insertNetworkIntoTable(self, network, interface_name):
        """
        Helper function to insert a network into the OSPF networks table. Should be called only from refreshOSPFNetworksTable().
        """

        rowPosition = self.ui.networks_table.rowCount()
        self.ui.networks_table.insertRow(rowPosition)
        self.ui.networks_table.setItem(rowPosition, 0, QTableWidgetItem(str(network)))
        self.ui.networks_table.setItem(rowPosition, 1, QTableWidgetItem(interface_name))

    def deleteNetworkButtonHandler(self):
        selected_rows = self.ui.networks_table.selectionModel().selectedRows()
        if selected_rows:
            for row in selected_rows:  
                network_text = self.ui.networks_table.item(row.row(), 0).text()
                interface_name = self.ui.networks_table.item(row.row(), 1).text()
                self.deleteNetwork(ipaddress.ip_network(network_text), interface_name)
            self.refreshOSPFNetworksTable()
        else:
            QMessageBox.warning(self, "Warning", "Select networks to delete.", QMessageBox.Ok)

    def deleteNetwork(self, network, interface_name):
        self.selected_device.removeOSPFNetwork(network, interface_name)

    def addNetworkButtonHandler(self):
            if self.selected_device:
                try:
                    dialog = AddOSPFNetworkDialog(self.selected_device)
                    dialog.exec()
                finally:
                    self.refreshOSPFNetworksTable()
            else:
                QMessageBox.warning(self, "Warning", "Select a device.", QMessageBox.Ok)


class AddOSPFNetworkDialog(QDialog):
    def __init__(self, device):
        super().__init__()

        self.device = device
        self.ui = Ui_AddOSPFNetworkDialog()
        self.ui.setupUi(self)

        self.ui.interfaces_combo_box.addItems(self.device.interfaces.keys())
        self.ui.interfaces_combo_box.addItems(["Not specified"])

        self.ui.ok_cancel_buttons.button(QDialogButtonBox.Ok).clicked.connect(self.addNetwork)

    def addNetwork(self):
        network = self.ui.network_input.text()
        interface_name = self.ui.interfaces_combo_box.currentText()
        if network and interface_name:
            try:
                if interface_name == "Not specified":
                    interface_name = None
                self.device.addOSPFNetwork(ipaddress.ip_network(network), interface_name)
                
                self.accept()
            except ValueError:
                QMessageBox.warning(self, "Warning", "Invalid network address.", QMessageBox.Ok)
        else:
            QMessageBox.warning(self, "Warning", "Fill in all fields.", QMessageBox.Ok)
