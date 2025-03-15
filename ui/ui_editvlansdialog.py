# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'editvlansdialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_edit_vlans_dialog(object):
    def setupUi(self, edit_vlans_dialog):
        if not edit_vlans_dialog.objectName():
            edit_vlans_dialog.setObjectName(u"edit_vlans_dialog")
        edit_vlans_dialog.resize(742, 507)
        self.verticalLayout_2 = QVBoxLayout(edit_vlans_dialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.vlan_list_groupbox = QGroupBox(edit_vlans_dialog)
        self.vlan_list_groupbox.setObjectName(u"vlan_list_groupbox")
        self.horizontalLayout = QHBoxLayout(self.vlan_list_groupbox)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.vlan_list_table = QTableWidget(self.vlan_list_groupbox)
        self.vlan_list_table.setObjectName(u"vlan_list_table")

        self.horizontalLayout.addWidget(self.vlan_list_table)

        self.add_vlan_groupbox = QGroupBox(self.vlan_list_groupbox)
        self.add_vlan_groupbox.setObjectName(u"add_vlan_groupbox")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.add_vlan_groupbox.sizePolicy().hasHeightForWidth())
        self.add_vlan_groupbox.setSizePolicy(sizePolicy)
        self.add_vlan_groupbox.setMinimumSize(QSize(200, 0))
        self.verticalLayout = QVBoxLayout(self.add_vlan_groupbox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(self.add_vlan_groupbox)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.add_vlan_lineedit = QLineEdit(self.add_vlan_groupbox)
        self.add_vlan_lineedit.setObjectName(u"add_vlan_lineedit")

        self.verticalLayout.addWidget(self.add_vlan_lineedit)

        self.add_vlan_button = QPushButton(self.add_vlan_groupbox)
        self.add_vlan_button.setObjectName(u"add_vlan_button")

        self.verticalLayout.addWidget(self.add_vlan_button)


        self.horizontalLayout.addWidget(self.add_vlan_groupbox, 0, Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTop)


        self.verticalLayout_2.addWidget(self.vlan_list_groupbox, 0, Qt.AlignmentFlag.AlignTop)

        self.devices_tab_widget = QTabWidget(edit_vlans_dialog)
        self.devices_tab_widget.setObjectName(u"devices_tab_widget")

        self.verticalLayout_2.addWidget(self.devices_tab_widget)

        self.buttonBox = QDialogButtonBox(edit_vlans_dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout_2.addWidget(self.buttonBox)


        self.retranslateUi(edit_vlans_dialog)

        QMetaObject.connectSlotsByName(edit_vlans_dialog)
    # setupUi

    def retranslateUi(self, edit_vlans_dialog):
        edit_vlans_dialog.setWindowTitle(QCoreApplication.translate("edit_vlans_dialog", u"Dialog", None))
        self.vlan_list_groupbox.setTitle(QCoreApplication.translate("edit_vlans_dialog", u"VLANs", None))
        self.add_vlan_groupbox.setTitle(QCoreApplication.translate("edit_vlans_dialog", u"Add a VLAN", None))
        self.label.setText(QCoreApplication.translate("edit_vlans_dialog", u"Add a new VLAN", None))
        self.add_vlan_lineedit.setText("")
        self.add_vlan_button.setText(QCoreApplication.translate("edit_vlans_dialog", u"Add", None))
    # retranslateUi

