from ui.ui_ipsecdialog import Ui_IPSECDialog

import utils

# QT
from PySide6.QtWidgets import (
    QGraphicsPixmapItem, 
    QGraphicsItem,
    QGraphicsLineItem,
    QLineEdit, 
    QGraphicsRectItem, 
    QGraphicsSceneMouseEvent,
    QGraphicsProxyWidget,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QWidget,
    QGraphicsTextItem,
    QToolTip,
    QPushButton,
    QVBoxLayout,
    QDialogButtonBox,
    QComboBox,
    QDialog,
    QVBoxLayout,
    QMessageBox,
    QTreeWidgetItem)
from PySide6.QtGui import (
    QImage, 
    QPixmap,
    QPen,
    QColor,
    QAction,
    QFont,
    QIcon,
    QAction)
from PySide6.QtCore import (
    Qt,
    QLineF,
    QPointF,
    QPoint,
    QSize,
    QTimer)

from PySide6.QtWidgets import QDialog, QGraphicsScene, QGraphicsPixmapItem, QGraphicsLineItem, QGraphicsEllipseItem
from PySide6.QtGui import QPixmap, QPen, QColor

class IPSECDialog(QDialog):
    def __init__(self, cloned_devices):
        super().__init__()

        self.ui = Ui_IPSECDialog()
        self.ui.setupUi(self)

        self.ipsec_scene = QGraphicsScene()
        scene_height = self.ui.graphicsView.height()
        device_width = cloned_devices[0].boundingRect().width()
        spacing = 200
        vertical_position = 50
        self.dev1 = cloned_devices[0]
        self.dev2 = cloned_devices[1]

        ipsec_scheme = QPixmap("graphics/ipsec_scheme.png")
        self.ipsec_scene.addPixmap(ipsec_scheme)

        # AZ BUDE FUNKCNI NETCONF SPOJENI, CELE TOTO PREPSAT DO NECEHO CITELNEJSIHO
        # device1 hostname label
        self.dev1_label_holder = QGraphicsRectItem()
        self.dev1_label = QGraphicsTextItem()
        self.dev1_label.setFont(QFont('Arial', 10))
        self.dev1_label.setPlainText(str(self.dev1.original_device.hostname))
        self.dev1_label_holder.setRect(self.dev1_label.boundingRect())
        self.dev1_label_holder.setBrush(QColor(255, 255, 255))
        self.dev1_label_holder.setPen(Qt.NoPen)
        self.dev1_label_holder.setPos(75, 90)
        self.dev1_label.setParentItem(self.dev1_label_holder)
        self.ipsec_scene.addItem(self.dev1_label_holder)

        # device2 hostname label
        self.dev2_label_holder = QGraphicsRectItem()
        self.dev2_label = QGraphicsTextItem()
        self.dev2_label.setFont(QFont('Arial', 10))
        self.dev2_label.setPlainText(str(self.dev2.original_device.hostname))
        self.dev2_label_holder.setRect(self.dev2_label.boundingRect())
        self.dev2_label_holder.setBrush(QColor(255, 255, 255))
        self.dev2_label_holder.setPen(Qt.NoPen)
        self.dev2_label_holder.setPos(505, 90)
        self.dev2_label.setParentItem(self.dev2_label_holder)
        self.ipsec_scene.addItem(self.dev2_label_holder)

        self.ui.graphicsView.setScene(self.ipsec_scene)

        # device1 interface tab
        self.ui.dev1_groupbox.setTitle(self.dev1.original_device.hostname)
        self.ui.dev1_LAN_interface_combobox.addItems(self.dev1.original_device.interfaces.keys())
        self.ui.dev1_WAN_interface_combobox.addItems(self.dev1.original_device.interfaces.keys())
        self.ui.dev1_LAN_interface_combobox.currentTextChanged.connect(lambda selected_intf = self.ui.dev1_LAN_interface_combobox.currentText: self._dev1_LAN_interface_selected(selected_intf))
        self.ui.dev1_WAN_interface_combobox.currentTextChanged.connect(lambda selected_intf = self.ui.dev1_LAN_interface_combobox.currentText: self._dev1_WAN_interface_selected(selected_intf))

        self.dev1_lan_network_label = QGraphicsTextItem()
        self.dev1_lan_network_label.setFont(QFont("Arial", 10))
        self.dev1_lan_network_label.setPos(125, 250) #toto asi neni stred, ale levy kraj? vylepsit
        self.ipsec_scene.addItem(self.dev1_lan_network_label)

        self.dev1_lan_interface_label = QGraphicsTextItem()
        self.dev1_lan_interface_label.setFont(QFont("Arial", 10))
        self.dev1_lan_interface_label.setPos(80, 120) #toto asi neni stred, ale levy kraj? vylepsit
        self.ipsec_scene.addItem(self.dev1_lan_interface_label)

        self.dev1_wan_interface_label = QGraphicsTextItem()
        self.dev1_wan_interface_label.setFont(QFont("Arial", 10))
        self.dev1_wan_interface_label.setPos(130, 85) #toto asi neni stred, ale levy kraj? vylepsit
        self.ipsec_scene.addItem(self.dev1_wan_interface_label)

        self.dev1_wan_ip_label = QGraphicsTextItem()
        self.dev1_wan_ip_label.setFont(QFont("Arial", 10))
        self.dev1_wan_ip_label.setPos(130, 105) #toto asi neni stred, ale levy kraj? vylepsit
        self.ipsec_scene.addItem(self.dev1_wan_ip_label)

        # device2 interface tab
        self.ui.dev2_groupbox.setTitle(self.dev2.original_device.hostname)
        self.ui.dev2_LAN_interface_combobox.addItems(self.dev2.original_device.interfaces.keys())
        self.ui.dev2_WAN_interface_combobox.addItems(self.dev2.original_device.interfaces.keys())
        self.ui.dev2_LAN_interface_combobox.currentTextChanged.connect(lambda selected_intf = self.ui.dev1_LAN_interface_combobox.currentText: self._dev2_LAN_interface_selected(selected_intf))
        self.ui.dev2_WAN_interface_combobox.currentTextChanged.connect(lambda selected_intf = self.ui.dev1_LAN_interface_combobox.currentText: self._dev2_WAN_interface_selected(selected_intf))

        self.dev2_lan_network_label = QGraphicsTextItem()
        self.dev2_lan_network_label.setFont(QFont("Arial", 10))
        self.dev2_lan_network_label.setPos(385, 250) #toto asi neni stred, ale levy kraj? vylepsit
        self.ipsec_scene.addItem(self.dev2_lan_network_label)

        self.dev2_lan_interface_label = QGraphicsTextItem()
        self.dev2_lan_interface_label.setFont(QFont("Arial", 10))
        self.dev2_lan_interface_label.setPos(510, 120) #toto asi neni stred, ale levy kraj? vylepsit
        self.ipsec_scene.addItem(self.dev2_lan_interface_label)

        self.dev2_wan_interface_label = QGraphicsTextItem()
        self.dev2_wan_interface_label.setFont(QFont("Arial", 10))
        self.dev2_wan_interface_label.setPos(460, 85) #toto asi neni stred, ale levy kraj? vylepsit
        self.ipsec_scene.addItem(self.dev2_wan_interface_label)

        self.dev2_wan_ip_label = QGraphicsTextItem()
        self.dev2_wan_ip_label.setFont(QFont("Arial", 10))
        self.dev2_wan_ip_label.setPos(460, 105) #toto asi neni stred, ale levy kraj? vylepsit
        self.ipsec_scene.addItem(self.dev2_wan_ip_label)

    def _dev1_LAN_interface_selected(self, selected_intf):
        interface_data = self.dev1.original_device.interfaces[selected_intf]
        self.dev1_lan_interface_label.setPlainText(selected_intf)
        ipv4_data, ipv6_data = utils.getFirstIPAddressesFromSubinterfaces(interface_data['subinterfaces'])
        if ipv4_data:
            self.ui.dev1_LAN_network_lineedit.setText(str(ipv4_data["value"].network))
            self.dev1_lan_network_label.setPlainText(f"Local network:\n{str(ipv4_data["value"].network)}")
        elif ipv6_data:
            self.ui.dev1_LAN_network_lineedit.setText(str(ipv6_data["value"].network))
            self.dev1_lan_network_label.setPlainText(f"Local network:\n{str(ipv6_data["value"].network)}")
        else:
            self.ui.dev1_LAN_network_lineedit.clear()
            self.dev1_lan_network_label.setPlainText("")

    def _dev2_LAN_interface_selected(self, selected_intf):
        interface_data = self.dev1.original_device.interfaces[selected_intf]
        self.dev2_lan_interface_label.setPlainText(selected_intf)
        ipv4_data, ipv6_data = utils.getFirstIPAddressesFromSubinterfaces(interface_data['subinterfaces'])
        if ipv4_data:
            self.ui.dev2_LAN_network_lineedit.setText(str(ipv4_data["value"].network))
            self.dev2_lan_network_label.setPlainText(f"Local network:\n{str(ipv4_data["value"].network)}")
        elif ipv6_data:
            self.ui.dev2_LAN_network_lineedit.setText(str(ipv6_data["value"].network))
            self.dev2_lan_network_label.setPlainText(f"Local network:\n{str(ipv6_data["value"].network)}")
        else:
            self.ui.dev2_LAN_network_lineedit.clear()
            self.dev2_lan_network_label.setPlainText("")

    def _dev1_WAN_interface_selected(self, selected_intf):
        interface_data = self.dev1.original_device.interfaces[selected_intf]
        self.dev1_wan_interface_label.setPlainText(selected_intf)
        ipv4_data, ipv6_data = utils.getFirstIPAddressesFromSubinterfaces(interface_data['subinterfaces'])
        if ipv4_data:
            self.ui.dev1_WAN_ip_lineedit.setText(str(ipv4_data["value"]))
            self.dev1_wan_ip_label.setPlainText(str(ipv4_data["value"]))
        elif ipv6_data:
            self.ui.dev1_WAN_ip_lineedit.setText(str(ipv6_data["value"]))
            self.dev1_wan_ip_label.setPlainText(str(ipv6_data["value"]))
        else:
            self.ui.dev1_WAN_ip_lineedit.clear()
            self.ui.dev1_WAN_ip_lineedit.setText("")

    def _dev2_WAN_interface_selected(self, selected_intf):
        interface_data = self.dev2.original_device.interfaces[selected_intf]
        ipv4_data, ipv6_data = utils.getFirstIPAddressesFromSubinterfaces(interface_data['subinterfaces'])
        if ipv4_data:
            self.ui.dev2_WAN_ip_lineedit.setText(str(ipv4_data["value"]))
            self.dev2_wan_ip_label.setPlainText(str(ipv4_data["value"]))
        elif ipv6_data:
            self.ui.dev2_WAN_ip_lineedit.setText(str(ipv6_data["value"]))
            self.dev2_wan_ip_label.setPlainText(str(ipv6_data["value"]))
        else:
            self.ui.dev2_WAN_ip_lineedit.clear()
            self.ui.dev2_WAN_ip_lineedit.setText("")