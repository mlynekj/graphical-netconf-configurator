# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'vlandialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QTabWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

class Ui_vlan_dialog(object):
    def setupUi(self, vlan_dialog):
        if not vlan_dialog.objectName():
            vlan_dialog.setObjectName(u"vlan_dialog")
        vlan_dialog.resize(742, 507)
        self.verticalLayout_2 = QVBoxLayout(vlan_dialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.vlan_list_groupbox = QGroupBox(vlan_dialog)
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

        self.devices_tab_widget = QTabWidget(vlan_dialog)
        self.devices_tab_widget.setObjectName(u"devices_tab_widget")

        self.verticalLayout_2.addWidget(self.devices_tab_widget)


        self.retranslateUi(vlan_dialog)

        QMetaObject.connectSlotsByName(vlan_dialog)
    # setupUi

    def retranslateUi(self, vlan_dialog):
        vlan_dialog.setWindowTitle(QCoreApplication.translate("vlan_dialog", u"Dialog", None))
        self.vlan_list_groupbox.setTitle(QCoreApplication.translate("vlan_dialog", u"VLANs", None))
        self.add_vlan_groupbox.setTitle(QCoreApplication.translate("vlan_dialog", u"Add a VLAN", None))
        self.label.setText(QCoreApplication.translate("vlan_dialog", u"Add a new VLAN", None))
        self.add_vlan_lineedit.setText("")
        self.add_vlan_button.setText(QCoreApplication.translate("vlan_dialog", u"Add", None))
    # retranslateUi

