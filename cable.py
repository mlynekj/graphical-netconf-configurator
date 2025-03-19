# ---------- IMPORTS: ----------
# Standard library
import math

# Custom modules
import utils
from devices import Device

# Qt
from PySide6.QtWidgets import (
    QGraphicsLineItem, 
    QGraphicsRectItem, 
    QGraphicsTextItem,
    QMenu,
    QToolTip)
from PySide6.QtGui import (
    QPen,
    QColor,
    QAction,
    QFont,
    QCursor,
    QTransform)
from PySide6.QtCore import (
    Qt,
    QPointF,
    QTimer,
    QObject)

# ---------- CABLE CLASSES: ----------
class Cable(QGraphicsLineItem):
    def __init__(self, device1: object, device1_interface, device2: object, device2_interface):
        super().__init__()

        self.device1 = device1
        self.device2 = device2
        self.device1_interface = device1_interface
        self.device2_interface = device2_interface
        self.device1.id = device1.id
        self.device2.id = device2.id

        self.device1.cables.append(self)
        self.device1.cable_connected_interfaces.append(device1_interface)

        self.device2.cables.append(self)
        self.device2.cable_connected_interfaces.append(device2_interface)

        self.setPen(QPen(QColor(0, 0, 0), 3))

        self.device_interface_labels = []
        self.device_interface_labels.append(CableInterfaceLabel(interface_name = self.device1_interface, parent = self, device1 = device1))    
        self.device_interface_labels.append(CableInterfaceLabel(interface_name = self.device2_interface, parent = self, device2 = device2))

        self.updatePosition()

    def __str__(self):
        return(f"{self.device1.id}:({self.device1_interface}) - {self.device2.id}:({self.device2_interface})")

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

    def updateLabelsText(self):
        for interface_label in self.device_interface_labels:
            interface_label.setLabelText()

    def removeCable(self):
        if self in self.device1.cables:
            self.device1.cables.remove(self)
        
        if self in self.device2.cables:
            self.device2.cables.remove(self)

        self.scene().removeItem(self)


class CableInterfaceLabel(QGraphicsTextItem):
    def __init__(self, interface_name, parent, device1 = None, device2 = None, distance_offset=70):
        super().__init__(parent)
        
        self.interface_name = interface_name
        self.parent = parent
        self.device = device1 if device1 else device2
        self.device1 = device1
        self.device2 = device2
        self.distance_offset = distance_offset

        self.setFont(QFont('Arial', 8))
        self.setDefaultTextColor(Qt.white)

        # LABEL TEXT
        self.label_holder = QGraphicsRectItem(self.boundingRect(), self.parent)
        self.setLabelText()

        # TOOLTIP
        self.setAcceptHoverEvents(True)  # Enable mouse hover over events
        self.tooltip_text = self.text
        self.tooltip_timer = QTimer()
        self.tooltip_timer.setSingleShot(True) # only once per hover event
        self.tooltip_timer.timeout.connect(lambda: QToolTip.showText(self.hover_pos, self.tooltip_text))

        self.updatePosition()

    def _calculatePosition(self, distance_offset):
        line = self.parent.line()
        device1_point = line.p1() # where the line begins
        device2_point = line.p2() # where the line ends

        # Direction vector
        dx = device2_point.x() - device1_point.x()
        dy = device2_point.y() - device1_point.y()
        line_length = math.sqrt(dx**2 + dy**2)
        if line_length == 0:
            return device1_point if self.device1 else device2_point

        # Normalize the direction vector
        unit_dx = dx / line_length
        unit_dy = dy / line_length

        if self.device1:
            distance_offset = distance_offset
            device_point = device1_point
        elif self.device2:
            distance_offset = -distance_offset
            device_point = device2_point

        # Calculate the position of the label (move away from the device by distance offset)
        label_x = device_point.x() + unit_dx * distance_offset
        label_y = device_point.y() + unit_dy * distance_offset
        label_pos = QPointF(label_x, label_y)

        # Center the label
        label_pos_centered = label_pos - QPointF(self.boundingRect().width() / 2, self.boundingRect().height() / 2)
        
        return(label_pos_centered)
    
    def updatePosition(self):
        label_pos = self._calculatePosition(self.distance_offset)
        self.label_holder.setPos(label_pos)

    def hoverEnterEvent(self, event):
        # Tooltip
        self.tooltip_timer.start(1000) # shown after 1 second of hovering over the label, at the current mouse position
        self.hover_pos = event.screenPos()

    def hoverLeaveEvent(self, event):
        # Tooltip
        self.tooltip_timer.stop()
        QToolTip.hideText()
    
    def setLabelText(self):
        subinterfaces = self.device.interfaces[self.interface_name]['subinterfaces']
        ipv4_data, ipv6_data = utils.getFirstIPAddressesFromSubinterfaces(subinterfaces)

        self.text = str(f"{self.interface_name}")
        if ipv4_data:
            if not ipv4_data.get("flag", "") == "deleted":
                self.text += str(f"\n{ipv4_data['value']}")
        if ipv6_data:
            if not ipv4_data.get("flag", "") == "deleted":
                self.text += str(f"\n{ipv6_data['value']}")

        self.setPlainText(self.text)
        self.tooltip_text = self.text

        self.label_holder.setRect(self.boundingRect())
        self.label_holder.setBrush(QColor(0, 0, 0))
        self.label_holder.setPen(Qt.NoPen)
        self.setParentItem(self.label_holder)


class TempCable(QGraphicsLineItem):
    """ Temporary cable that is drawn in the process of creating a new cable """

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
    """
    Class that handles the cable editing mode in application.
    It allows users to add and delete cables between devices in a graphical scene.

    Important attributes:
        device1 (Device): The first device selected for cable connection.
        device2 (Device): The second device selected for cable connection.
        device1_interface (str): The interface of the first device.
        device2_interface (str): The interface of the second device.
    Public methods:
        exitMode():
            Exits the cable edit mode and restores normal mouse behavior.
        addCable(device1, device1_interface, device2, device2_interface):
            Adds a cable between two devices and returns the created cable.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.view = parent.view
        self.scene = parent.view.scene
        self.normal_mode_mouse_handlers = parent.normal_mode_mouse_handlers

        self.device1 = None # The first selected device
        self.device2 = None # The second selected device
        self.device1_interface = None
        self.device2_interface = None

        self.view.changeMouseBehaviour(
            cursor="device1_selection_mode",
            mouse_press_event=self._device1SelectionHandler,
            mouse_move_event=self._deleteCableMouseMoveHandler,
            tracking=True
        )

    def exitMode(self):
        self._deleteTempCable()
        self.view.changeMouseBehaviour(
            cursor="normal",
            mouse_press_event=self.normal_mode_mouse_handlers["mousePressEvent"],
            mouse_move_event=self.normal_mode_mouse_handlers["mouseMoveEvent"],
            mouse_release_event=self.normal_mode_mouse_handlers["mouseReleaseEvent"],
            tracking=False
        )
        del self

    def addCable(self, device1, device1_interface, device2, device2_interface):
        cable = Cable(device1, device1_interface, device2, device2_interface)
        cable.setZValue(-1) #All cables to the background
        self.scene.addItem(cable)
        return(cable)

    def _getItemClickedAtPos(self, event, item_type):
        item = self.scene.itemAt(event.scenePos(), QTransform())
        return item if isinstance(item, item_type) else None
    
    def _promptInterfaceSelection(self, device, callback):
        menu = QMenu()
        for interface in device.interfaces.keys():
            interface_action = QAction(interface, menu)
            interface_action.triggered.connect(lambda _, intf=interface: callback(intf)) # First argument (checked state of the button) is ignored
            menu.addAction(interface_action)
        menu.exec(QCursor.pos())

    # ----------------- CABLE DELETION -----------------
    def _deleteCableMouseMoveHandler(self, event):
        found_cable = self._getItemClickedAtPos(event, Cable)
        if found_cable:
            self.view.changeMouseBehaviour(
                cursor="delete_cable_mode",
                mouse_press_event=lambda _, cable=found_cable: self._deleteCableMousePressHandler(cable) # First argument (event) is ignored
            )
        else:
            self.view.changeMouseBehaviour(
                cursor="device1_selection_mode",
                mouse_press_event=self._device1SelectionHandler
            )

    def _deleteCableMousePressHandler(self, cable):
        cable.removeCable()
        self.view.changeMouseBehaviour(
            cursor="device1_selection_mode",
            mouse_press_event=self._device1SelectionHandler
        )

    # ----------------- TMP CABLE -----------------
    def _drawTempCable(self):
        self.tmp_cable = TempCable(self.device1.sceneBoundingRect().center())
        self.scene.addItem(self.tmp_cable)
        self.view.changeMouseBehaviour(mouse_move_event=lambda event: self.tmp_cable.updatePosition(event, self.device1.sceneBoundingRect().center()))

    def _deleteTempCable(self):
        if hasattr(self, 'tmp_cable'):
            self.scene.removeItem(self.tmp_cable)
            del self.tmp_cable
        self.view.changeMouseBehaviour(mouse_move_event=lambda event: self._deleteCableMouseMoveHandler(event))

    # ----------------- DEVICE1 -----------------
    def _device1SelectionHandler(self, event):
        """ Wait for the user to select the starting device """
        self.device1 = self._getItemClickedAtPos(event, Device) 
        if not self.device1: # Ignore clicks on anything else than a device
            return
        
        self._promptInterfaceSelection(self.device1, self._device1InterfaceSelected)

    def _device1InterfaceSelected(self, interface):
        self.device1_interface = interface
        self.view.changeMouseBehaviour(
            cursor="device2_selection_mode",
            mouse_press_event=self._device2SelectionHandler
        )
        self._drawTempCable()

    # ----------------- DEVICE2 -----------------
    def _device2SelectionHandler(self, event):
        """ Wait for the user to select the ending device """
        self.device2 = self._getItemClickedAtPos(event, Device) 
        if not self.device2 or self.device2 == self.device1: # Ignore clicks on anything else than a device, or connecting a device to itself
            return
        
        self._promptInterfaceSelection(self.device2, self._device2InterfaceSelected)
        self._deleteTempCable()
        self.view.changeMouseBehaviour(cursor="normal")

    def _device2InterfaceSelected(self, interface):
        self.device2_interface = interface
        self.addCable(self.device1, self.device1_interface, self.device2, self.device2_interface)
        self.view.changeMouseBehaviour(
            cursor="device1_selection_mode",
            mouse_press_event=self._device1SelectionHandler
        )

        