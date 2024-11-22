# QT
from PySide6.QtWidgets import (
    QGraphicsLineItem, 
    QGraphicsRectItem, 
    QGraphicsTextItem,
    QMenu,
    QApplication)
from PySide6.QtGui import (
    QImage, 
    QPixmap,
    QPen,
    QColor,
    QAction,
    QFont,
    QIcon,
    QCursor,
    QTransform)
from PySide6.QtCore import (
    Qt,
    QLineF,
    QPointF,
    QPoint,
    QSize,
    QTimer,
    QObject)

# Other
import math

class Cable(QGraphicsLineItem):
    def __init__(self, device1, device1_interface, device2: object, device2_interface):
        super().__init__()

        self.device1 = device1
        self.device2 = device2
        self.device1_interface = device1_interface
        self.device2_interface = device2_interface

        self.device1.cables.append(self)
        self.device2.cables.append(self)

        self.setPen(QPen(QColor(0, 0, 0), 3))

        self.device_interface_labels = []
        self.device_interface_labels.append(CableInterfaceLabel(self.device1_interface, "device1", self))    
        self.device_interface_labels.append(CableInterfaceLabel(self.device2_interface, "device2", self))

        self.updatePosition()
        self.updateLabelsPosition()

    def updatePosition(self):
        device_1_center = self.device1.sceneBoundingRect().center()
        device_2_center = self.device2.sceneBoundingRect().center()

        self.setLine(device_1_center.x(), 
                     device_1_center.y(), 
                     device_2_center.x(), 
                     device_2_center.y())
        
        self.updateLabelsPosition()

    def updateLabelsPosition(self):
        for interface_label in self.device_interface_labels:
            interface_label.updatePosition()

    def removeCable(self):
        if self in self.device1.cables:
            self.device1.cables.remove(self)
        
        if self in self.device2.cables:
            self.device2.cables.remove(self)

        self.scene().removeItem(self)

class CableInterfaceLabel(QGraphicsTextItem):
    def __init__(self, text, device, parent, distance_offset=70):
        super().__init__(text, parent)
        
        self.parent = parent
        self.device = device
        self.distance_offset = distance_offset

        self.setFont(QFont('Arial', 8))
        self.setDefaultTextColor(Qt.white)

        self.label_holder = QGraphicsRectItem(self.boundingRect(), parent)
        self.label_holder.setBrush(QColor(0, 0, 0))
        self.label_holder.setPen(Qt.NoPen)

        self.setParentItem(self.label_holder)

        self.updatePosition()

    def calculatePosition(self, distance_offset):
        line = self.parent.line()

        device1_point = line.p1()
        device2_point = line.p2()

        # Direction vector
        dx = device2_point.x() - device1_point.x()
        dy = device2_point.y() - device1_point.y()
        line_length = math.sqrt(dx**2 + dy**2)
        if line_length == 0:
            return device1_point if self.device == 1 else device2_point

        # Normalize the direction vector
        unit_dx = dx / line_length
        unit_dy = dy / line_length

        if self.device == "device1":
            distance_offset = distance_offset
            device_point = device1_point
        elif self.device == "device2":
            distance_offset = -distance_offset
            device_point = device2_point

        # Move the label away from the device by distance offset, using the direction vector
        device_label_x = device_point.x() + unit_dx * distance_offset
        device_label_y = device_point.y() + unit_dy * distance_offset
        device_label_pos = QPointF(device_label_x, device_label_y)

        # Center the label
        device_label_pos_centered = device_label_pos - QPointF(self.boundingRect().width() / 2, self.boundingRect().height() / 2)

        return(device_label_pos_centered)
    
    def updatePosition(self):
        device_label_pos = self.calculatePosition(self.distance_offset)

        self.label_holder.setPos(device_label_pos)

class CableEditMode(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.view = parent.view
        self.scene = parent.view.scene

        self.cable_mode_cursor = QCursor(QPixmap("graphics/icons/cable_mode_cursor.png"))

        self.device1 = None
        self.device2 = None
        self.device1_interface = None
        self.device2_interface = None

        self.normal_mode_handlers = self.parent.saveMouseEventHandlers()
        self.view.scene.mousePressEvent = self.device1SelectionMode

    @property
    def buttonIsChecked(self):
        return self.parent.toolbar.actions()[1].isChecked()

    # ----------------- DEVICE1 -----------------
    def device1SelectionMode(self, event):
        self.device1 = self.view.scene.itemAt(event.scenePos(), QTransform())
        self.device1InterfaceSelectionMode(event)

    def device1InterfaceSelectionMode(self, event):
        menu = QMenu()

        for interface in self.device1.interfaces:
            interface_action = QAction(interface[0], menu)
            interface_action.triggered.connect(lambda checked, intf=interface[0]: self.device1InterfaceSelectionModeConfirm(intf))
            menu.addAction(interface_action)
        menu.exec(event.screenPos())

    def device1InterfaceSelectionModeConfirm(self, interface):
        self.device1_interface = interface
        
        
        QApplication.setOverrideCursor(self.cable_mode_cursor)
        self.device1_selection_mode_handlers = self.parent.saveMouseEventHandlers()
        self.view.scene.mousePressEvent = self.device2SelectionMode

    # ----------------- DEVICE2 -----------------
    def device2SelectionMode(self, event):
        self.device2 = self.view.scene.itemAt(event.scenePos(), QTransform())
        if self.device2 == self.device1: # Dont allow connecting a device to itself
            self.parent.restoreMouseEventHandlers(self.device1_selection_mode_handlers)
            QApplication.restoreOverrideCursor()
            return
        else:
            self.parent.restoreMouseEventHandlers(self.device1_selection_mode_handlers)
            self.device2InterfaceSelectionMode(event)
            QApplication.restoreOverrideCursor()

    def device2InterfaceSelectionMode(self, event):
        menu = QMenu()

        for interface in self.device2.interfaces:
            interface_action = QAction(interface[0], menu)
            interface_action.triggered.connect(lambda checked, intf=interface[0]: self.device2InterfaceSelectionModeConfirm(intf))
            menu.addAction(interface_action)
        menu.exec(event.screenPos())

    def device2InterfaceSelectionModeConfirm(self, interface):
        self.device2_interface = interface
        self.addCable(self.device1, self.device1_interface, self.device2, self.device2_interface)

    # ----------------- MANAGEMENT OF THE CABLES -----------------
    def addCable(self, device1, device1_interface, device2, device2_interface):
        cable = Cable(device1, device1_interface, device2, device2_interface)
        cable.setZValue(-1) #All cables to the background
        self.view.scene.addItem(cable)
        return(cable)
    
    def removeCable(self, device1, device2):        
        cable_to_be_removed = [cable for cable in device1.cables if cable in device2.cables]
        cable_to_be_removed[0].removeCable()