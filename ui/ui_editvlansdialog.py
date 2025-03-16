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
    QSizePolicy, QTabWidget, QVBoxLayout, QWidget)

class Ui_edit_vlans_dialog(object):
    def setupUi(self, edit_vlans_dialog):
        if not edit_vlans_dialog.objectName():
            edit_vlans_dialog.setObjectName(u"edit_vlans_dialog")
        edit_vlans_dialog.resize(742, 507)
        self.verticalLayout_3 = QVBoxLayout(edit_vlans_dialog)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.devices_tab_widget = QTabWidget(edit_vlans_dialog)
        self.devices_tab_widget.setObjectName(u"devices_tab_widget")

        self.verticalLayout_3.addWidget(self.devices_tab_widget)

        self.buttonBox = QDialogButtonBox(edit_vlans_dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout_3.addWidget(self.buttonBox)


        self.retranslateUi(edit_vlans_dialog)

        QMetaObject.connectSlotsByName(edit_vlans_dialog)
    # setupUi

    def retranslateUi(self, edit_vlans_dialog):
        edit_vlans_dialog.setWindowTitle(QCoreApplication.translate("edit_vlans_dialog", u"Dialog", None))
    # retranslateUi

