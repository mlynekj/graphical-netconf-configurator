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

# Other
import ipaddress

class OSPFDialog(QDialog):
    # TODO: potom rozdelit do tridy asi "ProtocolDialog" a pak z ni dedit OSPFDialog, BGPDialog, ...
    def __init__(self, scene=None):
        super().__init__()

        self.setWindowTitle("OSPF Configuration")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()
        self.graphics_view = QGraphicsView()
        self.scene = scene if scene else QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        self.layout.addWidget(self.graphics_view)

        self.setLayout(self.layout)