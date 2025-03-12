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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_Ui_edit_interface_dialog(object):
    def setupUi(self, Ui_edit_interface_dialog):
        if not Ui_edit_interface_dialog.objectName():
            Ui_edit_interface_dialog.setObjectName(u"Ui_edit_interface_dialog")
        Ui_edit_interface_dialog.resize(637, 300)
        self.verticalLayout_2 = QVBoxLayout(Ui_edit_interface_dialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.add_subinterface_button = QPushButton(Ui_edit_interface_dialog)
        self.add_subinterface_button.setObjectName(u"add_subinterface_button")

        self.verticalLayout_2.addWidget(self.add_subinterface_button, 0, Qt.AlignmentFlag.AlignLeft)

        self.top_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.top_spacer)

        self.tables_layout = QVBoxLayout()
        self.tables_layout.setObjectName(u"tables_layout")

        self.verticalLayout_2.addLayout(self.tables_layout)

        self.bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.bottom_spacer)

        self.close_button_box = QDialogButtonBox(Ui_edit_interface_dialog)
        self.close_button_box.setObjectName(u"close_button_box")
        self.close_button_box.setStandardButtons(QDialogButtonBox.StandardButton.Close)

        self.verticalLayout_2.addWidget(self.close_button_box)


        self.retranslateUi(Ui_edit_interface_dialog)

        QMetaObject.connectSlotsByName(Ui_edit_interface_dialog)
    # setupUi

    def retranslateUi(self, Ui_edit_interface_dialog):
        Ui_edit_interface_dialog.setWindowTitle(QCoreApplication.translate("Ui_edit_interface_dialog", u"Edit interface: ", None))
        self.add_subinterface_button.setText(QCoreApplication.translate("Ui_edit_interface_dialog", u"Add subinterface", None))
    # retranslateUi

