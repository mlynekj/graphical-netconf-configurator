# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'addospfnetworkdialog.ui'
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
    QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_AddOSPFNetworkDialog(object):
    def setupUi(self, AddOSPFNetworkDialog):
        if not AddOSPFNetworkDialog.objectName():
            AddOSPFNetworkDialog.setObjectName(u"AddOSPFNetworkDialog")
        AddOSPFNetworkDialog.resize(300, 104)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(AddOSPFNetworkDialog.sizePolicy().hasHeightForWidth())
        AddOSPFNetworkDialog.setSizePolicy(sizePolicy)
        AddOSPFNetworkDialog.setMinimumSize(QSize(250, 0))
        AddOSPFNetworkDialog.setMaximumSize(QSize(300, 104))
        self.verticalLayout = QVBoxLayout(AddOSPFNetworkDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.network_layout = QHBoxLayout()
        self.network_layout.setObjectName(u"network_layout")
        self.network_label = QLabel(AddOSPFNetworkDialog)
        self.network_label.setObjectName(u"network_label")

        self.network_layout.addWidget(self.network_label, 0, Qt.AlignmentFlag.AlignLeft)

        self.network_input = QLineEdit(AddOSPFNetworkDialog)
        self.network_input.setObjectName(u"network_input")

        self.network_layout.addWidget(self.network_input)


        self.verticalLayout.addLayout(self.network_layout)

        self.interface_layout = QHBoxLayout()
        self.interface_layout.setObjectName(u"interface_layout")
        self.interfaces_label = QLabel(AddOSPFNetworkDialog)
        self.interfaces_label.setObjectName(u"interfaces_label")

        self.interface_layout.addWidget(self.interfaces_label, 0, Qt.AlignmentFlag.AlignLeft)

        self.interfaces_combo_box = QComboBox(AddOSPFNetworkDialog)
        self.interfaces_combo_box.setObjectName(u"interfaces_combo_box")

        self.interface_layout.addWidget(self.interfaces_combo_box)


        self.verticalLayout.addLayout(self.interface_layout)

        self.ok_cancel_buttons = QDialogButtonBox(AddOSPFNetworkDialog)
        self.ok_cancel_buttons.setObjectName(u"ok_cancel_buttons")
        self.ok_cancel_buttons.setOrientation(Qt.Orientation.Horizontal)
        self.ok_cancel_buttons.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.ok_cancel_buttons)


        self.retranslateUi(AddOSPFNetworkDialog)
        self.ok_cancel_buttons.accepted.connect(AddOSPFNetworkDialog.accept)
        self.ok_cancel_buttons.rejected.connect(AddOSPFNetworkDialog.reject)

        QMetaObject.connectSlotsByName(AddOSPFNetworkDialog)
    # setupUi

    def retranslateUi(self, AddOSPFNetworkDialog):
        AddOSPFNetworkDialog.setWindowTitle(QCoreApplication.translate("AddOSPFNetworkDialog", u"Dialog", None))
        self.network_label.setText(QCoreApplication.translate("AddOSPFNetworkDialog", u"New network:", None))
        self.network_input.setPlaceholderText(QCoreApplication.translate("AddOSPFNetworkDialog", u"e.g. 10.0.0.0/24 or 2001::/64", None))
        self.interfaces_label.setText(QCoreApplication.translate("AddOSPFNetworkDialog", u"Interface:", None))
    # retranslateUi

