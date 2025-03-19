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
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_edit_interface_dialog(object):
    def setupUi(self, edit_interface_dialog):
        if not edit_interface_dialog.objectName():
            edit_interface_dialog.setObjectName(u"edit_interface_dialog")
        edit_interface_dialog.resize(683, 299)
        self.verticalLayout = QVBoxLayout(edit_interface_dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.add_subinterface_button = QPushButton(edit_interface_dialog)
        self.add_subinterface_button.setObjectName(u"add_subinterface_button")

        self.horizontalLayout.addWidget(self.add_subinterface_button)

        self.description_frame = QFrame(edit_interface_dialog)
        self.description_frame.setObjectName(u"description_frame")
        self.description_frame.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.description_frame.sizePolicy().hasHeightForWidth())
        self.description_frame.setSizePolicy(sizePolicy)
        self.description_frame.setMinimumSize(QSize(0, 0))
        self.security_zone_layout_2 = QHBoxLayout(self.description_frame)
        self.security_zone_layout_2.setObjectName(u"security_zone_layout_2")
        self.interface_top_vertical_line_2 = QFrame(self.description_frame)
        self.interface_top_vertical_line_2.setObjectName(u"interface_top_vertical_line_2")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.interface_top_vertical_line_2.sizePolicy().hasHeightForWidth())
        self.interface_top_vertical_line_2.setSizePolicy(sizePolicy1)
        self.interface_top_vertical_line_2.setFrameShape(QFrame.Shape.VLine)
        self.interface_top_vertical_line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.security_zone_layout_2.addWidget(self.interface_top_vertical_line_2)

        self.description_label = QLabel(self.description_frame)
        self.description_label.setObjectName(u"description_label")

        self.security_zone_layout_2.addWidget(self.description_label)

        self.description_input = QLineEdit(self.description_frame)
        self.description_input.setObjectName(u"description_input")
        self.description_input.setMaximumSize(QSize(200, 16777215))

        self.security_zone_layout_2.addWidget(self.description_input)

        self.change_description_button = QPushButton(self.description_frame)
        self.change_description_button.setObjectName(u"change_description_button")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.change_description_button.sizePolicy().hasHeightForWidth())
        self.change_description_button.setSizePolicy(sizePolicy2)

        self.security_zone_layout_2.addWidget(self.change_description_button)


        self.horizontalLayout.addWidget(self.description_frame)

        self.security_zone_frame = QFrame(edit_interface_dialog)
        self.security_zone_frame.setObjectName(u"security_zone_frame")
        self.security_zone_frame.setEnabled(True)
        sizePolicy.setHeightForWidth(self.security_zone_frame.sizePolicy().hasHeightForWidth())
        self.security_zone_frame.setSizePolicy(sizePolicy)
        self.security_zone_frame.setMinimumSize(QSize(0, 0))
        self.security_zone_layout = QHBoxLayout(self.security_zone_frame)
        self.security_zone_layout.setObjectName(u"security_zone_layout")
        self.interface_top_vertical_line = QFrame(self.security_zone_frame)
        self.interface_top_vertical_line.setObjectName(u"interface_top_vertical_line")
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


        self.horizontalLayout.addWidget(self.security_zone_frame)


        self.verticalLayout.addLayout(self.horizontalLayout)

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
        self.description_label.setText(QCoreApplication.translate("edit_interface_dialog", u"Description:", None))
        self.change_description_button.setText(QCoreApplication.translate("edit_interface_dialog", u"Change", None))
        self.security_zone_label.setText(QCoreApplication.translate("edit_interface_dialog", u"Security zone:", None))
        self.change_security_zone_button.setText(QCoreApplication.translate("edit_interface_dialog", u"Change", None))
    # retranslateUi

