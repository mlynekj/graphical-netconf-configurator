# QT
from PySide6.QtWidgets import (
    QGraphicsLineItem, 
    QGraphicsRectItem, 
    QGraphicsTextItem,
    QMenu,
    QApplication,
    QToolTip)
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
    QObject,
    QEvent)

# Other
import math

# Custom
from devices import Device

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

        # TOOLTIP
        self.setAcceptHoverEvents(True)  # Enable mouse hover over events
        self.tooltip_text = text
        self.tooltip_timer = QTimer() # shown after 1 second of hovering over the label, at the current mouse position
        self.tooltip_timer.setSingleShot(True) # only once per hover event
        self.tooltip_timer.timeout.connect(lambda: QToolTip.showText(self.hover_pos, self.tooltip_text))

        self.updatePosition()

    def updatePosition(self):
        label_pos = self.calculatePosition(self.distance_offset)
        self.label_holder.setPos(label_pos)

    def calculatePosition(self, distance_offset):
        line = self.parent.line()
        device1_point = line.p1() # where the line begins
        device2_point = line.p2() # where the line ends

        # Direction vector
        dx = device2_point.x() - device1_point.x()
        dy = device2_point.y() - device1_point.y()
        line_length = math.sqrt(dx**2 + dy**2)
        if line_length == 0:
            return device1_point if self.device == "device1" else device2_point

        # Normalize the direction vector
        unit_dx = dx / line_length
        unit_dy = dy / line_length

        if self.device == "device1":
            distance_offset = distance_offset
            device_point = device1_point
        elif self.device == "device2":
            distance_offset = -distance_offset
            device_point = device2_point

        # Calculate the position of the label (move away from the device by distance offset)
        label_x = device_point.x() + unit_dx * distance_offset
        label_y = device_point.y() + unit_dy * distance_offset
        label_pos = QPointF(label_x, label_y)

        # Center the label
        label_pos_centered = label_pos - QPointF(self.boundingRect().width() / 2, self.boundingRect().height() / 2)
        
        return(label_pos_centered)
    
    def hoverEnterEvent(self, event):
        # Tooltip
        self.tooltip_timer.start(1000)
        self.hover_pos = event.screenPos()

    def hoverLeaveEvent(self, event):
        # Tooltip
        self.tooltip_timer.stop()
        QToolTip.hideText()
    

class TmpCable(QGraphicsLineItem):
    def __init__(self, starting_pos):
        super().__init__()

        self.starting_pos = starting_pos
        self.setPen(QPen(QColor(0, 0, 0), 3))

    def updatePosition(self, event, starting_pos):
        cursor_pos = event.scenePos()
        self.setLine(
            starting_pos.x(), 
            starting_pos.y(), 
            cursor_pos.x(), 
            cursor_pos.y()
        )
        

class CableEditMode(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.view = parent.view
        self.scene = parent.view.scene

        self.cable_mode_cursor_device1 = QCursor(QPixmap("graphics/cursors/cable_mode_cursor_device1.png"))
        self.cable_mode_cursor_device2 = QCursor(QPixmap("graphics/cursors/cable_mode_cursor_device2.png"))

        self.device1 = None
        self.device2 = None
        self.device1_interface = None
        self.device2_interface = None

        self.normal_mode_handlers = self.parent.saveMouseEventHandlers()
        self.changeCursor("device1_selection_mode")
        self.view.scene.mousePressEvent = self.device1SelectionMode

    def changeCursor(self, cursor):
        if cursor == "normal":
            QApplication.restoreOverrideCursor()
        elif cursor == "device1_selection_mode":
            QApplication.setOverrideCursor(self.cable_mode_cursor_device1)
        elif cursor == "device2_selection_mode":
            QApplication.setOverrideCursor(self.cable_mode_cursor_device2)
        

    # ----------------- TMP CABLE -----------------
    def renderTmpCable(self):
        self.tmp_cable = TmpCable(self.device1.sceneBoundingRect().center())
        self.view.scene.addItem(self.tmp_cable)
        self.view.setMouseTracking(True)
        self.view.scene.mouseMoveEvent = lambda event: self.tmp_cable.updatePosition(event, self.device1.sceneBoundingRect().center())

    def dontRenderTmpCable(self):
        self.view.scene.removeItem(self.tmp_cable)
        self.view.setMouseTracking(False)
        self.view.scene.mouseMoveEvent = self.normal_mode_handlers[1] # [1] = original_mouseMoveEvent

    # ----------------- DEVICE1 -----------------
    def device1SelectionMode(self, event):
        self.device1 = self.view.scene.itemAt(event.scenePos(), QTransform())
        if not isinstance(self.device1, Device):
            return
        
        self.changeCursor("normal")
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
        
        self.changeCursor("device2_selection_mode")
        self.view.scene.mousePressEvent = self.device2SelectionMode
        self.renderTmpCable()

    # ----------------- DEVICE2 -----------------
    def device2SelectionMode(self, event):
        self.device2 = self.view.scene.itemAt(event.scenePos(), QTransform())
        if not isinstance(self.device2, Device):
            return
        
        if self.device2 == self.device1: # Dont allow connecting a device to itself
            self.view.scene.mousePressEvent = self.device1SelectionMode
            self.changeCursor("device1_selection_mode")
            return
        else:
            self.device2InterfaceSelectionMode(event)
            self.dontRenderTmpCable()
            self.changeCursor("normal")

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
        self.view.scene.mousePressEvent = self.normal_mode_handlers[0] # [0] = original_mousePressEvent

    # ----------------- MANAGEMENT OF THE CABLES -----------------
    def addCable(self, device1, device1_interface, device2, device2_interface):
        cable = Cable(device1, device1_interface, device2, device2_interface)
        cable.setZValue(-1) #All cables to the background
        self.view.scene.addItem(cable)
        return(cable)
    
    def removeCable(self, device1, device2):        
        cable_to_be_removed = [cable for cable in device1.cables if cable in device2.cables]
        cable_to_be_removed[0].removeCable()