# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'interfacesdialog.ui'
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
    QHBoxLayout, QHeaderView, QPushButton, QSizePolicy,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_Interfaces(object):
    def setupUi(self, Interfaces):
        if not Interfaces.objectName():
            Interfaces.setObjectName(u"Interfaces")
        Interfaces.resize(718, 300)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Interfaces.sizePolicy().hasHeightForWidth())
        Interfaces.setSizePolicy(sizePolicy)
        Interfaces.setMinimumSize(QSize(700, 300))
        Interfaces.setBaseSize(QSize(700, 300))
        self.verticalLayout = QVBoxLayout(Interfaces)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.interfaces_table = QTableWidget(Interfaces)
        self.interfaces_table.setObjectName(u"interfaces_table")
        sizePolicy.setHeightForWidth(self.interfaces_table.sizePolicy().hasHeightForWidth())
        self.interfaces_table.setSizePolicy(sizePolicy)
        self.interfaces_table.setMinimumSize(QSize(700, 100))

        self.verticalLayout.addWidget(self.interfaces_table)

        self.button_layout = QHBoxLayout()
        self.button_layout.setObjectName(u"button_layout")
        self.add_interface_button = QPushButton(Interfaces)
        self.add_interface_button.setObjectName(u"add_interface_button")

        self.button_layout.addWidget(self.add_interface_button)

        self.refresh_button = QPushButton(Interfaces)
        self.refresh_button.setObjectName(u"refresh_button")

        self.button_layout.addWidget(self.refresh_button)

        self.close_button_box = QDialogButtonBox(Interfaces)
        self.close_button_box.setObjectName(u"close_button_box")
        self.close_button_box.setStandardButtons(QDialogButtonBox.StandardButton.Close)

        self.button_layout.addWidget(self.close_button_box)


        self.verticalLayout.addLayout(self.button_layout)


        self.retranslateUi(Interfaces)

        QMetaObject.connectSlotsByName(Interfaces)
    # setupUi

    def retranslateUi(self, Interfaces):
        Interfaces.setWindowTitle(QCoreApplication.translate("Interfaces", u"Dialog", None))
        self.add_interface_button.setText(QCoreApplication.translate("Interfaces", u"Add new interface", None))
#if QT_CONFIG(tooltip)
        self.refresh_button.setToolTip(QCoreApplication.translate("Interfaces", u"<html><head/><body><p>Refresh interface information by pulling the latest data from the device. Available only when no pending changes are waiting for commiting.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.refresh_button.setText(QCoreApplication.translate("Interfaces", u"Refresh interfaces", None))
    # retranslateUi

