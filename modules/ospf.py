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
    QGraphicsScene)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QGuiApplication, QAction

from ui.ui_ospfdialog import Ui_OSPFDialog

# Other
import ipaddress

import sys
from PySide6.QtCore import QFile

class OSPFDialog(QDialog):
    def __init__(self, scene=None):
        super().__init__()

        self.scene = scene
        self.ui = Ui_OSPFDialog()
        self.ui.setupUi(self)

        self.ui.graphicsView.setScene(self.scene)

# class OSPFDialog(QDialog):
#     # TODO: potom rozdelit do tridy asi "ProtocolDialog" a pak z ni dedit OSPFDialog, BGPDialog, ...
#     def __init__(self, scene=None):
#         super().__init__()

#         self.setWindowTitle("OSPF Configuration")
#         self.setGeometry(100, 100, 800, 600)

#         self.main_layout = QHBoxLayout()

#         # Left side
#         self.left_widget = QWidget()
#         self.left_layout = QVBoxLayout()
#         self.left_widget.setLayout(self.left_layout)

#         self.process_id_group = QWidget()
#         self.process_id_layout = QVBoxLayout()
#         self.process_id_group.setLayout(self.process_id_layout)

#         self.process_id_label = QLabel("Process ID")
#         self.left_layout.addWidget(self.process_id_label)
#         self.process_id_input = QLineEdit()
#         self.left_layout.addWidget(self.process_id_input)

        
#         self.left_layout.addWidget(QPushButton("Button 1"))
#         self.main_layout.addWidget(self.left_widget)

#         # Center
#         self.graphics_view = QGraphicsView()
#         self.scene = scene if scene else QGraphicsScene()
#         self.graphics_view.setScene(self.scene)
#         self.main_layout.addWidget(self.graphics_view)


#         # Right side
#         self.right_widget = QWidget()
#         self.right_layout = QVBoxLayout()
#         self.right_widget.setLayout(self.right_layout)
#         self.right_layout.addWidget(QLabel("Right Widget"))
#         self.right_layout.addWidget(QPushButton("Button 2"))
#         self.main_layout.addWidget(self.right_widget)

#         self.setLayout(self.main_layout)