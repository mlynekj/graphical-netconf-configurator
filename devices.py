# QT
from PySide6.QtWidgets import (
    QGraphicsPixmapItem, 
    QGraphicsItem,
    QGraphicsLineItem, 
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
    QVBoxLayout)
from PySide6.QtGui import (
    QImage, 
    QPixmap,
    QPen,
    QColor,
    QAction,
    QFont,
    QIcon)
from PySide6.QtCore import (
    Qt,
    QLineF,
    QPointF,
    QPoint,
    QSize,
    QTimer)

# Other
from ncclient import manager
import math

# Custom
import modules.netconf as netconf
import modules.interfaces as interfaces
import modules.system as system
import modules.helper as helper
import dialogs

from PySide6.QtWidgets import QMessageBox

class Device(QGraphicsPixmapItem):
    _counter = 0 # Used to generate device IDs
    _registry = {} # Used to store device instances
    _device_type = "D"
    
    def __init__(self, device_parameters, x=0, y=0):
        super().__init__()

        self.setAcceptHoverEvents(True)  # Enable mouse hover over events

        self.device_parameters = device_parameters

        # NETCONF CONNECTION
        self.mngr = netconf.establishNetconfConnection(device_parameters) # TODO: Handle timeout, when the device disconnects after some time

        # ICON + CANVAS PLACEMENT
        device_icon_img = QImage("graphics/devices/general.png") # TODO: CHANGE GENERAL ICON
        self.setPixmap(QPixmap.fromImage(device_icon_img))
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setPos(x, y)
        self.setZValue(1)
        
        # CABLES LIST
        self.cables = []

        # ID
        type(self)._counter += 1
        self.id = self.generateID()

        # DEVICE INFORMATION
        self.netconf_capabilities = self.dev_GetNetconfCapabilites()
        self.interfaces = self.dev_GetInterfaces(self)
        self.hostname = self.dev_GetHostname()

        # LABEL (Hostname)
        self.label = QGraphicsTextItem(str(self.hostname), self)
        self.label.setFont(QFont('Arial', 10))
        self.label.setPos(0, self.pixmap().height())
        self.label_border = self.label.boundingRect()
        self.label.setPos((self.pixmap().width() - self.label_border.width()) / 2, self.pixmap().height())

        # TOOLTIP
        self.tooltip_text = (
            f"Device ID: {self.id}\n"
            f"IP: {self.device_parameters['address']}\n"
            f"Device type: {self.device_parameters['device_params']}"
        )
        self.tooltip_timer = QTimer() # shown after 1 second of hovering over the device, at the current mouse position
        self.tooltip_timer.setSingleShot(True) # only once per hover event
        self.tooltip_timer.timeout.connect(lambda: QToolTip.showText(self.hover_pos, self.tooltip_text))

        # REGISTRY
        type(self)._registry[self.id] = self

    def refreshHostnameLabel(self):
        self.hostname = self.dev_GetHostname()

        self.label.setPlainText(str(self.hostname))
        self.label_border = self.label.boundingRect()
        self.label.setPos((self.pixmap().width() - self.label_border.width()) / 2, self.pixmap().height())

    def generateID(self):
        return(type(self)._device_type + str(type(self)._counter))

    def deleteDevice(self):
        netconf.demolishNetconfConnection(self) # Disconnect from NETCONF

        self.scene().removeItem(self)
    
        # Cables
        for cable in self.cables.copy(): # CANNOT MODIFY CONTENTS OF A LIST, WHILE ITERATING THROUGH IT! => .copy()
            cable.removeCable()

        del type(self)._registry[self.id]
        

    # ---------- MOUSE EVENTS FUNCTIONS ---------- 
    def mousePressEvent(self, event):
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event) 

        for cable in self.cables:
            cable.updatePosition()

    def hoverEnterEvent(self, event):
        # Tooltip
        self.tooltip_timer.start(1000)
        self.hover_pos = event.screenPos()

    def hoverLeaveEvent(self, event):
        # Tooltip
        self.tooltip_timer.stop()
        QToolTip.hideText()

    def contextMenuEvent(self, event):
        """ Right-click menu """
        menu = QMenu()

        # Disconnect from device
        disconnect_action = QAction("Disconnect from the device")
        disconnect_action.triggered.connect(self.deleteDevice)
        menu.addAction(disconnect_action)

        # Show NETCONF capabilites
        show_netconf_capabilities_action = QAction("Show NETCONF Capabilities")
        show_netconf_capabilities_action.triggered.connect(self.show_CapabilitiesDialog)
        menu.addAction(show_netconf_capabilities_action)

        # Show interfaces
        show_interfaces_action = QAction("Show Interfaces")
        show_interfaces_action.triggered.connect(self.show_ListInterfacesDialog)
        menu.addAction(show_interfaces_action)

        # Edit Hostname
        edit_hostname_action = QAction("Edit Hostname")
        edit_hostname_action.triggered.connect(self.show_EditHostnameDialog)
        menu.addAction(edit_hostname_action)

        # Discard all pending changes
        discard_changes_action = QAction("Discard all pending changes from candidate datastore")
        discard_changes_action.triggered.connect(lambda: netconf.discardChanges(self))
        menu.addAction(discard_changes_action)

        menu.exec(event.screenPos())

    # ---------- DIALOG SHOW FUNCTIONS ---------- 
    def show_CapabilitiesDialog(self):
        dialog = dialogs.CapabilitiesDialog(self)
        dialog.exec()

    def show_ListInterfacesDialog(self):
        dialog = dialogs.DeviceInterfacesDialog(self)
        dialog.exec()

    def show_EditHostnameDialog(self):
        dialog = dialogs.EditHostnameDialog(self)
        dialog.exec()

    def dev_GetNetconfCapabilites(self):
        return(netconf.getNetconfCapabilities(self))
    
    # ---------- HOSTNAME MANIPULATION FUNCTIONS ---------- 
    def dev_GetHostname(self):
        return(system.getHostname(self))
    
    def dev_SetHostname(self, new_hostname):
        rpc_reply = system.setHostname(self, new_hostname)
        rpc_reply = netconf.commitChanges(self)

    # ---------- INTERFACE MANIPULATION FUNCTIONS ---------- 
    def dev_GetInterfaces(self, getIPs=False):
        return(interfaces.getInterfaceList(self, getIPs))

    def dev_GetSubinterfaces(self, interface_id):
        return(interfaces.getSubinterfaces(self, interface_id))
    
    def dev_DeleteInterfaceIP(self, interface_id, subinterface_index, old_ip):
        rpc_reply = interfaces.deleteIp(self, interface_id, subinterface_index, old_ip)
        rpc_reply = netconf.commitChanges(self)

    def dev_SetInterfaceIP(self, interface_id, subinterface_index, new_ip):
        rpc_reply = interfaces.setIp(self, interface_id, subinterface_index, new_ip)
        rpc_reply = netconf.commitChanges(self)

    def dev_ReplaceInterfaceIP(self, interface_id, subinterface_index, old_ip, new_ip):
        rpc_reply = interfaces.deleteIp(self, interface_id, subinterface_index, old_ip)
        rpc_reply = interfaces.setIp(self, interface_id, subinterface_index, new_ip)
        rpc_reply = netconf.commitChanges(self)
    
    # ---------- REGISTRY FUNCTIONS ---------- 
    @classmethod
    def getDeviceInstance(cls, device_id):
        return cls._registry.get(device_id)
    
    @classmethod
    def getAllDeviceInstances(cls):
        return list(cls._registry.keys())

    
class Router(Device):
    _device_type = "R"

    def __init__(self, device_parameters, x=0, y=0):
        super().__init__(device_parameters, x, y)

        # ICON
        router_icon_img = QImage("graphics/devices/router.png")
        self.setPixmap(QPixmap.fromImage(router_icon_img))


class Cable(QGraphicsLineItem):
    def __init__(self, device1, device1_interface, device2, device2_interface):
        super().__init__()

        self.device1 = device1
        self.device2 = device2
        self.device1_interface = device1_interface
        self.device2_interface = device2_interface

        self.device1.cables.append(self)
        self.device2.cables.append(self)

        self.setPen(QPen(QColor(0, 0, 0), 3))

        self.device1_interface_label, self.device1_interface_label_holder = self.createLabel(self.device1_interface)
        self.device2_interface_label, self.device2_interface_label_holder = self.createLabel(self.device2_interface)
        
        self.updatePosition()
        self.updateLabelsPosition()

    def createLabel(self, text):
        label = QGraphicsTextItem(text, self)
        label.setFont(QFont('Arial', 8))
        label.setDefaultTextColor(Qt.white)

        label_holder = QGraphicsRectItem(label.boundingRect(), self)
        label_holder.setBrush(QColor(0, 0, 0))
        label_holder.setPen(Qt.NoPen)
        
        #TODO: move to the foreground (so it is not covered by the device)
        label.setParentItem(label_holder)

        return(label, label_holder)

    def calculateLabelPositions(self, distance_offset):
        line = self.line()

        start_point = line.p1()
        end_point = line.p2()

        # Direction vector
        dx = end_point.x() - start_point.x()
        dy = end_point.y() - start_point.y()
        line_length = math.sqrt(dx**2 + dy**2)

        if line_length == 0:
            return start_point, end_point

        # Normalize the direction vector
        unit_dx = dx / line_length
        unit_dy = dy / line_length

        # Move the label away from the device using the direction vector
        device1_label_x = start_point.x() + unit_dx * distance_offset
        device1_label_y = start_point.y() + unit_dy * distance_offset
        device1_label_pos = QPointF(device1_label_x, device1_label_y)

        device2_label_x = end_point.x() + unit_dx * (-distance_offset)
        device2_label_y = end_point.y() + unit_dy * (-distance_offset)
        device2_label_pos = QPointF(device2_label_x, device2_label_y)

        # Center the label
        device1_label_pos_centered = device1_label_pos - QPointF(self.device1_interface_label.boundingRect().width() / 2, self.device1_interface_label.boundingRect().height() / 2)
        device2_label_pos_centered = device2_label_pos - QPointF(self.device2_interface_label.boundingRect().width() / 2, self.device2_interface_label.boundingRect().height() / 2)

        return(device1_label_pos_centered, device2_label_pos_centered)

    def updateLabelsPosition(self):
        distance_offset = 70
        device1_label_pos, device2_label_pos = self.calculateLabelPositions(distance_offset)

        self.device1_interface_label_holder.setPos(device1_label_pos)
        self.device2_interface_label_holder.setPos(device2_label_pos)

    def updatePosition(self):
        device_1_center = self.device1.sceneBoundingRect().center()
        device_2_center = self.device2.sceneBoundingRect().center()

        self.setLine(device_1_center.x(), 
                     device_1_center.y(), 
                     device_2_center.x(), 
                     device_2_center.y())
        
        self.updateLabelsPosition()

    def removeCable(self):
        if self in self.device1.cables:
            self.device1.cables.remove(self)
        
        if self in self.device2.cables:
            self.device2.cables.remove(self)

        self.scene().removeItem(self)
