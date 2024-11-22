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