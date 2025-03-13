# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'editinterfacedialog.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_edit_interface_dialog(object):
    def setupUi(self, edit_interface_dialog):
        if not edit_interface_dialog.objectName():
            edit_interface_dialog.setObjectName(u"edit_interface_dialog")
        edit_interface_dialog.resize(636, 300)
        self.verticalLayout = QVBoxLayout(edit_interface_dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.interface_top_layout = QHBoxLayout()
        self.interface_top_layout.setObjectName(u"interface_top_layout")
        self.add_subinterface_button = QPushButton(edit_interface_dialog)
        self.add_subinterface_button.setObjectName(u"add_subinterface_button")

        self.interface_top_layout.addWidget(self.add_subinterface_button, 0, Qt.AlignmentFlag.AlignLeft)

        self.security_zone_frame = QFrame(edit_interface_dialog)
        self.security_zone_frame.setObjectName(u"security_zone_frame")
        self.security_zone_frame.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.security_zone_frame.sizePolicy().hasHeightForWidth())
        self.security_zone_frame.setSizePolicy(sizePolicy)
        self.security_zone_frame.setMinimumSize(QSize(0, 0))
        self.security_zone_layout = QHBoxLayout(self.security_zone_frame)
        self.security_zone_layout.setObjectName(u"security_zone_layout")
        self.interface_top_vertical_line = QFrame(self.security_zone_frame)
        self.interface_top_vertical_line.setObjectName(u"interface_top_vertical_line")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.interface_top_vertical_line.sizePolicy().hasHeightForWidth())
        self.interface_top_vertical_line.setSizePolicy(sizePolicy1)
        self.interface_top_vertical_line.setFrameShape(QFrame.Shape.VLine)
        self.interface_top_vertical_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.security_zone_layout.addWidget(self.interface_top_vertical_line)

        self.security_zone_label = QLabel(self.security_zone_frame)
        self.security_zone_label.setObjectName(u"security_zone_label")

        self.security_zone_layout.addWidget(self.security_zone_label)

        self.security_zone_combobox = QComboBox(self.security_zone_frame)
        self.security_zone_combobox.setObjectName(u"security_zone_combobox")

        self.security_zone_layout.addWidget(self.security_zone_combobox)

        self.change_security_zone_button = QPushButton(self.security_zone_frame)
        self.change_security_zone_button.setObjectName(u"change_security_zone_button")

        self.security_zone_layout.addWidget(self.change_security_zone_button)

        self.security_zone_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.security_zone_layout.addItem(self.security_zone_spacer)


        self.interface_top_layout.addWidget(self.security_zone_frame)


        self.verticalLayout.addLayout(self.interface_top_layout)

        self.horizontal_line = QFrame(edit_interface_dialog)
        self.horizontal_line.setObjectName(u"horizontal_line")
        self.horizontal_line.setFrameShape(QFrame.Shape.HLine)
        self.horizontal_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.horizontal_line)

        self.top_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.top_spacer)

        self.tables_layout = QVBoxLayout()
        self.tables_layout.setObjectName(u"tables_layout")

        self.verticalLayout.addLayout(self.tables_layout)

        self.bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.bottom_spacer)

        self.close_button_box = QDialogButtonBox(edit_interface_dialog)
        self.close_button_box.setObjectName(u"close_button_box")
        self.close_button_box.setStandardButtons(QDialogButtonBox.StandardButton.Close)

        self.verticalLayout.addWidget(self.close_button_box)


        self.retranslateUi(edit_interface_dialog)

        QMetaObject.connectSlotsByName(edit_interface_dialog)
    # setupUi

    def retranslateUi(self, edit_interface_dialog):
        edit_interface_dialog.setWindowTitle(QCoreApplication.translate("edit_interface_dialog", u"Edit interface: ", None))
        self.add_subinterface_button.setText(QCoreApplication.translate("edit_interface_dialog", u"Add subinterface", None))
        self.security_zone_label.setText(QCoreApplication.translate("edit_interface_dialog", u"Security zone:", None))
        self.change_security_zone_button.setText(QCoreApplication.translate("edit_interface_dialog", u"Change zone", None))
    # retranslateUi

