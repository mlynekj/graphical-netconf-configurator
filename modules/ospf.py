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
    QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QGuiApplication, QAction

# Other
import ipaddress

class OSPFDialog(QDialog):
    def __init__(self):
        super().__init__()