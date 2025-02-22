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

from yang.filters import EditconfigFilter

from definitions import *
from lxml import etree as ET

# Other
import ipaddress
import sys
from PySide6.QtCore import QFile

# ---------- OPERATIONS: ----------
def configureOSPFWithNetconf(ospf_device, area, hello_interval, dead_interval, reference_bandwidth):
    """
    Configures OSPF on a network device using NETCONF. Called from the device's configureOSPF method.
    Parameters:
        ospf_device (object): The device object containing OSPF configuration parameters.
        area (str): The OSPF area to configure.
        hello_interval (int): The OSPF hello interval.
        dead_interval (int): The OSPF dead interval.
        reference_bandwidth (int): The OSPF reference bandwidth.
    Returns:
        rpc_reply (object): The RPC reply from the NETCONF edit-config operation.
        filter (str): The XML filter used in the NETCONF edit-config operation.
    """
    if ospf_device.device_parameters["device_params"] == "junos":
        # Create the filter
        filter = OpenconfigNetworkInstance_Editconfig_ConfigureOspf_Filter(area, hello_interval, dead_interval, reference_bandwidth, ospf_device.router_id, ospf_device.passive_interfaces, ospf_device.ospf_networks)
            
        # RPC                
        rpc_reply = ospf_device.original_device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE) # the mngr is not in the cloned device, but rather in the original device
        return(rpc_reply, filter)
    
    elif ospf_device.device_parameters["device_params"] == "iosxe":
        # Create the filter
        filter = CiscoIOSXEOspf_Editconfig_ConfigureOspf_Filter(area, hello_interval, dead_interval, reference_bandwidth, ospf_device.router_id, ospf_device.passive_interfaces, ospf_device.ospf_networks)
        
        # RPC                
        rpc_reply = ospf_device.original_device.mngr.edit_config(str(filter), target=CONFIGURATION_TARGET_DATASTORE) # the mngr is not in the cloned device, but rather in the original device
        return(rpc_reply, filter)



# ---------- FILTERS: ----------
class OpenconfigNetworkInstance_Editconfig_ConfigureOspf_Filter(EditconfigFilter):
    def __init__(self, area, hello_interval: int, dead_interval: int, reference_bandwidth: int, router_id, passive_interfaces: list, ospf_networks: dict):
        self.router_id = router_id
        self.area = area
        self.hello_interval = hello_interval
        self.dead_interval = dead_interval
        self.reference_bandwidth = reference_bandwidth
        self.passive_interfaces = passive_interfaces
        
        self.ospf_networks = ospf_networks
        self.interfaces = list(ospf_networks.keys())

        # Load the XML filter template
        self.filter_xml = ET.parse(ROUTING_YANG_DIR + "openconfig-network-instance_edit-config_configure-ospf.xml")
        self.namespaces = {'ns': 'http://openconfig.net/yang/network-instance'}

        # Set the router-id
        if self.router_id:
            ospfv2_global_config_element = self.filter_xml.find(".//ns:ospfv2/ns:global/ns:config", self.namespaces)
            router_id_element = ET.SubElement(ospfv2_global_config_element, "router-id")
            router_id_element.text = self.router_id
    
        # Set the area
        ospfv2_area_element = self.filter_xml.find(".//ns:ospfv2/ns:areas/ns:area/ns:identifier", self.namespaces)
        ospfv2_area_element.text = self.area
                
        # Add the interfaces
        for interface in self.interfaces:
            self._addInterface(interface)

    def _addInterface(self, interface_id):
        ospfv2_area_element = self.filter_xml.find(".//ns:ospfv2/ns:areas/ns:area", self.namespaces)
        interfaces_element = ospfv2_area_element.find("ns:interfaces", self.namespaces)

        interface_element = ET.SubElement(interfaces_element, "interface")
        id_element = ET.SubElement(interface_element, "id")
        id_element.text = interface_id

        config_element = ET.SubElement(interface_element, "config")
        config_id_element = ET.SubElement(config_element, "id")
        config_id_element.text = interface_id

        # Reference bandwidth
        # IMPORTANT: Openconfig does not have a reference bandwidth element, but only allows manullaly specifying the cost of a link. 
        # As a workaround, the cost is hence calculated manually based on the reference bandwidth (cost = reference_bandwidth / bandwidth (b/s)).
        if self.reference_bandwidth:
            reference_bandwidth_bps = int(self.reference_bandwidth) * int(1_000_000)
            if "fe" in interface_id: # FastEthernet
                cost = reference_bandwidth_bps / int(100_000_000)
            elif "ge" in interface_id: # GigabitEthernet
                cost = reference_bandwidth_bps / int(1_000_000_000)
            elif "xe" in interface_id: #10GigabitEthernet
                cost = reference_bandwidth_bps / int(10_000_000_000)
            else:
                cost = 1
                QMessageBox.warning(self, "Warning", f"Reference bandwidth is set, but the link speed of interface: {interface_id} on device with ID: {self.router_id} is not recognized. Default cost of 1 will be used.", QMessageBox.Ok)
            config_metric_element = ET.SubElement(config_element, "metric")
            config_metric_element.text = str(int(cost))

        # Mark as passive if in the passive_interfaces list
        if interface_id in self.passive_interfaces:
            passive_element = ET.SubElement(config_element, "passive")
            passive_element.text = "true"

        # Add the timers
        if self.hello_interval or self.dead_interval:
            timers_element = ET.SubElement(interface_element, "timers")
            timers_config_element = ET.SubElement(timers_element, "config")
            if self.hello_interval:
                hello_interval_element = ET.SubElement(timers_config_element, "hello-interval")
                hello_interval_element.text = str(self.hello_interval)
            if self.dead_interval:
                dead_interval_element = ET.SubElement(timers_config_element, "dead-interval")
                dead_interval_element.text = str(self.dead_interval)


class CiscoIOSXEOspf_Editconfig_ConfigureOspf_Filter(EditconfigFilter):
    def __init__(self, area, hello_interval: int, dead_interval: int, reference_bandwidth: int, router_id, passive_interfaces: list, ospf_networks: dict):
        self.router_id = router_id
        self.area = area
        self.hello_interval = hello_interval
        self.dead_interval = dead_interval
        self.reference_bandwidth = reference_bandwidth
        self.passive_interfaces = passive_interfaces
        
        self.ospf_networks = [network for networks in ospf_networks.values() for network in networks] # Flatten the list of lists
        self.ospf_interfaces = list(ospf_networks.keys())

        # Load the XML filter template
        self.filter_xml = ET.parse(ROUTING_YANG_DIR + "cisco-IOS-XE-ospf_edit-config_configure-ospf.xml")
        self.namespaces = {'native': 'http://cisco.com/ns/yang/Cisco-IOS-XE-native',
                           'ospf': 'http://cisco.com/ns/yang/Cisco-IOS-XE-ospf'}
        
        # Set the router-id
        if self.router_id:
            process_id_element = self.filter_xml.find(".//ospf:process-id", self.namespaces)
            router_id_element = ET.SubElement(process_id_element, "router-id")
            router_id_element.text = self.router_id

        # Set the auto-cost reference-bandwidth
        if self.reference_bandwidth:
            auto_cost_element = self.filter_xml.find(".//ospf:auto-cost", self.namespaces)
            reference_bandwidth_element = ET.SubElement(auto_cost_element, "reference-bandwidth")
            reference_bandwidth_element.text = str(self.reference_bandwidth)

        # Add networks
        for network in self.ospf_networks:
            self._addNetwork(network)

        # Add passive interfaces
        for interface in self.passive_interfaces:
            self._addPassiveInterface(interface)

        # Add the timers
        if self.hello_interval or self.dead_interval:
            for interface in self.ospf_interfaces:
                self._addTimers(interface)

    def _addNetwork(self, network):
        process_id_element = self.filter_xml.find(".//ospf:process-id", self.namespaces)
        network_element = ET.SubElement(process_id_element, "network")
        
        # IP
        network_ip_element = ET.SubElement(network_element, "ip")
        network_ip_element.text = network.network_address.exploded
        # Wildcard
        network_wildcard_element = ET.SubElement(network_element, "wildcard")
        network_wildcard_element.text = network.hostmask.exploded
        # Area
        network_area_element = ET.SubElement(network_element, "area")
        network_area_element.text = self.area

    def _addPassiveInterface(self, interface):
        passive_interface_container_element = self.filter_xml.find(".//ospf:passive-interface", self.namespaces)
        passive_interface_element = ET.SubElement(passive_interface_container_element, "interface")
        passive_interface_element.text = interface

    def _addTimers(self, interface):
        native_element = self.filter_xml.find(".//native:native", self.namespaces) #/native
        interface_container_element = ET.SubElement(native_element, "interface") #/native/interface
        
        # Split the interface name (e.g. GigabitEthernet1) into type and number (GigabitEthernet, 1)
        interface_type = ''.join(filter(str.isalpha, interface))
        interface_number = interface.replace(interface_type, '')

        # Create the interface elements
        interface_element = ET.SubElement(interface_container_element, interface_type) #../interface/GigabitEthernet
        interface_number_element = ET.SubElement(interface_element, "name") #../GigabitEthernet/name
        interface_number_element.text = interface_number #../GigabitEthernet/name[1]

        # Create the timers elements and their respective parent elements
        ip_element = ET.SubElement(interface_element, "ip") #../GigabitEthernet/ip
        ospf_namespace = "http://cisco.com/ns/yang/Cisco-IOS-XE-ospf"
        router_ospf_element = ET.SubElement(ip_element, f"{{{ospf_namespace}}}router-ospf", nsmap={None: ospf_namespace}) #../GigabitEthernet/ip/router-ospf
        ospf_element = ET.SubElement(router_ospf_element, "ospf") #../router-ospf/ospf
        if self.hello_interval:
            hello_interval_element = ET.SubElement(ospf_element, "hello-interval") #..ospf/hello-interval
            hello_interval_element.text = str(self.hello_interval)
        if self.dead_interval:
            dead_interval_element = ET.SubElement(ospf_element, "dead-interval") #..ospf/dead-interval       
            dead_interval_element.text = str(self.dead_interval)



# ---------- QT: ----------
class OSPFDialog(QDialog):
    """
    OSPFDialog is a QDialog subclass that provides a user interface for configuring OSPF settings on network devices.
    It allows users to configure OSPF on selected devices.
    When the dialog is opened, it creates a clone of the MainView scene (only the selected devices) and displays it in the dialog.
    UI components were created in QtCreator and converted to Python code using PySide6-uic.
    Attributes:
        selected_device (ClonedDevice): The currently selected device in the cloned scene.
        scene (QGraphicsScene): The graphical scene containing network devices. Created by cloning the MainView scene.
        ui (Ui_OSPFDialog): The user interface elements for the dialog.
    """
            
    def __init__(self, scene=None):
        super().__init__()

        self.selected_device = None
        self.scene = scene
        self.ui = Ui_OSPFDialog()
        self.ui.setupUi(self)

        self.ui.graphicsView.setScene(self.scene)

        for device in self.scene.items():
            if device.__class__.__name__ == 'OSPFDevice': # isInstance(item, OSPFDevice), without the need to import OSPFDevice (circular import)
                device.ospf_networks = device.getOSPFNetworks()

        # Configure the input fields
        self.ui.hello_input.setPlaceholderText("Optional")
        self.ui.dead_input.setPlaceholderText("Optional")
        self.ui.reference_bandwidth_input.setPlaceholderText("Optional")
        self.ui.routerid_input.setPlaceholderText("Optional")
        self.ui.routerid_input.setToolTip("If not specified, RID will be automatically assigned. The choice of RID is different for each vendor. \nCisco: Highest IP address of any loopback interface  / Highest IP address of any active interface. \nJuniper: Lowest IP address of any loopback interface / Lowest IP address of any active interface.")
        self.ui.routerid_input.setDisabled(True) # Disable the input field for the router ID from the start, because no device is selected

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
        self.ui.delete_network_button.clicked.connect(self._deleteNetworkButtonHandler) # "delete network" button
        self.ui.add_network_button.clicked.connect(self._addNetworkButtonHandler) # "add network" button

        # Connect signals
        self.scene.selectionChanged.connect(self._onSelectionChanged) # When a device is selected on the scene, connect the signal to the slot onSelectionChanged
        self.ui.routerid_input.editingFinished.connect(self._onRouterIDInputChanged) # When the router ID input is changed, connect the signal to the slot onRouterIDInputChanged

        # Connect the buttons
        self.ui.ok_cancel_buttons.button(QDialogButtonBox.Ok).clicked.connect(self._okButtonHandler)

    @Slot()
    def _onSelectionChanged(self):
        """
        Slot function that gets called when a device is clicked on in the cloned scene.
        Sets the selected device to the selected item and refreshes the passive interfaces, OSPF networks tables and the router ID input.
        """
        selected_items = self.scene.selectedItems()
        for device in selected_items:
            if device.__class__.__name__ == 'OSPFDevice': # isInstance(item, OSPFDevice), without the need to import OSPFDevice (circular import)
                self.selected_device = device
                self._refreshPassiveInterfacesTable()
                self._refreshOSPFNetworksTable()
                self._refreshRouterIDInput()

    def _refreshPassiveInterfacesTable(self):
        """
        Loads and refreshes the passive interfaces table in the UI.
        Information about the passive interfaces is taken from the selected device's list - "passive_interfaces".
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
                checkbox_item.clicked.connect(lambda state, row=row: self._onPassiveInterfaceCheckboxChange(row))
                self.ui.passive_interfaces_table.setCellWidget(row, 1, checkbox_item)
                self.ui.passive_interfaces_table.cellWidget(row, 1).setStyleSheet("QCheckBox { margin-left: auto; margin-right: auto; }") # Center horizontally
        else :
            self.ui.passive_interfaces_table.setRowCount(1)
            self.ui.passive_interfaces_table.setColumnCount(1)
            self.ui.passive_interfaces_table.setItem(0, 0, QTableWidgetItem("No interfaces found!"))
        
    def _onPassiveInterfaceCheckboxChange(self, row):
        """
        Checks for the state of the checkbox in the passive interfaces table (for each interface) and updates the selected device's "passive_interfaces" list.
        """

        if self.ui.passive_interfaces_table.cellWidget(row, 1).isChecked():
            self.selected_device.passive_interfaces.append(self.ui.passive_interfaces_table.item(row, 0).text())
        else:
            self.selected_device.passive_interfaces.remove(self.ui.passive_interfaces_table.item(row, 0).text())

    def _refreshOSPFNetworksTable(self):
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

    def _refreshRouterIDInput(self):
        if self.selected_device:
            self.ui.routerid_input.setDisabled(False)
            self.ui.routerid_input.setText(self.selected_device.router_id)
        else:
            self.ui.routerid_input.setDisabled(True)
            self.ui.routerid_input.clear()

    @Slot()
    def _onRouterIDInputChanged(self):
        """
        A slot function that gets called when the router ID input is changed (editingFinished signal). It updated the router_id parameter of the selected device.
        """

        if self.selected_device:
            self.ui.routerid_input.setDisabled(False)
            self.selected_device.router_id = self.ui.routerid_input.text()
        else:
            self.ui.routerid_input.setDisabled(True)
            self.ui.routerid_input.clear()

    def _deleteNetworkButtonHandler(self):
        """
        Handles the event when the "Delete Network" button is clicked.
        This method retrieves the selected rows from the networks table, extracts the network 
        and interface information, and calls the deleteNetwork method to remove the network 
        from the configuration. After deletion, it refreshes the OSPF networks table to reflect the changes.
        """

        selected_rows = self.ui.networks_table.selectionModel().selectedRows()
        if selected_rows:
            for row in selected_rows:  
                network_text = self.ui.networks_table.item(row.row(), 0).text()
                interface_name = self.ui.networks_table.item(row.row(), 1).text()
                self._deleteNetwork(ipaddress.ip_network(network_text), interface_name)
            self._refreshOSPFNetworksTable()
        else:
            QMessageBox.warning(self, "Warning", "Select networks to delete.", QMessageBox.Ok)

    def _deleteNetwork(self, network, interface_name):
        """
        Helper function to delete a network from the OSPF configuration. Should be called only from _deleteNetworkButtonHandler().
        """
        self.selected_device.removeOSPFNetwork(network, interface_name)

    def _addNetworkButtonHandler(self):
        """
        Handles the event when the "Add Network" button is clicked.
        This method checks if a device is selected. If a device is selected, it opens
        the AddOSPFNetworkDialog and refreshes the OSPF networks table after the dialog is closed. 
        """
        
        if self.selected_device:
            try:
                dialog = AddOSPFNetworkDialog(self.selected_device)
                dialog.exec()
            finally:
                self._refreshOSPFNetworksTable()
        else:
            QMessageBox.warning(self, "Warning", "Select a device.", QMessageBox.Ok)

    def _okButtonHandler(self):
        """
        Reads the input fields, validates them and initiates an OSPF configuration of OSPF on all devices in the scene.
        """

        area = self.ui.area_number_input.text()
        hello_interval = self.ui.hello_input.text()
        dead_interval = self.ui.dead_input.text()
        reference_bandwidth = self.ui.reference_bandwidth_input.text()

        if not area:
            QMessageBox.warning(self, "Warning", "OSPF area is required. Please fill in the area.", QMessageBox.Ok)
            return
    
        for device in self.scene.items():
            if device.__class__.__name__ == 'OSPFDevice': # isInstance(item, OSPFDevice), without the need to import OSPFDevice (circular import)
                device.configureOSPF(area, hello_interval, dead_interval, reference_bandwidth)
        self.accept()       


class AddOSPFNetworkDialog(QDialog):
    """
    A dialog for adding an OSPF network to a device. Is called when the "Add Network" button is clicked in the OSPFDialog.
    Attributes:
        device (Device): The device to which the OSPF network will be added.
        ui (Ui_AddOSPFNetworkDialog): The UI components of the dialog.  
    """

    def __init__(self, device):
        super().__init__()

        self.device = device
        self.ui = Ui_AddOSPFNetworkDialog()
        self.ui.setupUi(self)

        # Configure the UI components
        self.ui.interfaces_combo_box.addItems(self.device.interfaces.keys())
        self.ui.ok_cancel_buttons.button(QDialogButtonBox.Ok).clicked.connect(self._addNetwork)

    def _addNetwork(self):
        """
        Adds an OSPF network to the configuration.
        This method retrieves the network address and interface name from the UI,
        validates them, and adds the network to the OSPF configuration of the device.
        """

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