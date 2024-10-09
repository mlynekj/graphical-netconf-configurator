# Qt
from PySide6.QtWidgets import (
    QDialog, 
    QVBoxLayout, 
    QScrollArea, 
    QWidget, 
    QLabel, 
    QPushButton)

# Custom
import db_handler


class CapabilitiesDialog(QDialog):
    def __init__(self, device_id):
        super().__init__()

        self.setWindowTitle("Device Capabilities")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create a widget to hold the capabilities
        capabilities_widget = QWidget()
        capabilities_layout = QVBoxLayout()

        capabilities = db_handler.queryNetconfCapabilities(db_handler.connection, device_id)

        for capability in capabilities:
            capabilities_layout.addWidget(QLabel(capability))
        

        capabilities_widget.setLayout(capabilities_layout)
        scroll_area.setWidget(capabilities_widget)

        layout.addWidget(scroll_area)

        # Add a close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

        #TODO: nejak to funguje, ale je to nejake divne. Az nebudu prejety, tady pokracovat a upravit/predelat/vylepsit
        #radky asi dat do nejake tabulky, volani mezi soubory je nejaka posahane
        #vsechny dialogy prestehovat do dialogs.py