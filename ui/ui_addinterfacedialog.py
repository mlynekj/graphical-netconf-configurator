# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'addinterfacedialog.ui'
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
    QDialogButtonBox, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QSizePolicy, QVBoxLayout, QWidget)

class Ui_add_interface_dialog(object):
    def setupUi(self, add_interface_dialog):
        if not add_interface_dialog.objectName():
            add_interface_dialog.setObjectName(u"add_interface_dialog")
        add_interface_dialog.resize(250, 140)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(add_interface_dialog.sizePolicy().hasHeightForWidth())
        add_interface_dialog.setSizePolicy(sizePolicy)
        add_interface_dialog.setMinimumSize(QSize(250, 0))
        add_interface_dialog.setMaximumSize(QSize(350, 140))
        self.verticalLayout_2 = QVBoxLayout(add_interface_dialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.add_new_interface_groupbox = QGroupBox(add_interface_dialog)
        self.add_new_interface_groupbox.setObjectName(u"add_new_interface_groupbox")
        self.verticalLayout = QVBoxLayout(self.add_new_interface_groupbox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.interface_name_layout = QHBoxLayout()
        self.interface_name_layout.setObjectName(u"interface_name_layout")
        self.interface_name_label = QLabel(self.add_new_interface_groupbox)
        self.interface_name_label.setObjectName(u"interface_name_label")

        self.interface_name_layout.addWidget(self.interface_name_label, 0, Qt.AlignmentFlag.AlignTop)

        self.interface_name_input = QLineEdit(self.add_new_interface_groupbox)
        self.interface_name_input.setObjectName(u"interface_name_input")

        self.interface_name_layout.addWidget(self.interface_name_input, 0, Qt.AlignmentFlag.AlignTop)


        self.verticalLayout.addLayout(self.interface_name_layout)

        self.interface_type_layout = QHBoxLayout()
        self.interface_type_layout.setObjectName(u"interface_type_layout")
        self.interface_type_label = QLabel(self.add_new_interface_groupbox)
        self.interface_type_label.setObjectName(u"interface_type_label")

        self.interface_type_layout.addWidget(self.interface_type_label, 0, Qt.AlignmentFlag.AlignTop)

        self.interface_type_combobox = QComboBox(self.add_new_interface_groupbox)
        self.interface_type_combobox.setObjectName(u"interface_type_combobox")

        self.interface_type_layout.addWidget(self.interface_type_combobox, 0, Qt.AlignmentFlag.AlignTop)


        self.verticalLayout.addLayout(self.interface_type_layout)


        self.verticalLayout_2.addWidget(self.add_new_interface_groupbox)

        self.ok_cancel_button_box = QDialogButtonBox(add_interface_dialog)
        self.ok_cancel_button_box.setObjectName(u"ok_cancel_button_box")
        self.ok_cancel_button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout_2.addWidget(self.ok_cancel_button_box)


        self.retranslateUi(add_interface_dialog)

        QMetaObject.connectSlotsByName(add_interface_dialog)
    # setupUi

    def retranslateUi(self, add_interface_dialog):
        add_interface_dialog.setWindowTitle(QCoreApplication.translate("add_interface_dialog", u"Dialog", None))
        self.add_new_interface_groupbox.setTitle(QCoreApplication.translate("add_interface_dialog", u"Add a new interface", None))
        self.interface_name_label.setText(QCoreApplication.translate("add_interface_dialog", u"Interface name:", None))
        self.interface_type_label.setText(QCoreApplication.translate("add_interface_dialog", u"Interface type:", None))
    # retranslateUi

