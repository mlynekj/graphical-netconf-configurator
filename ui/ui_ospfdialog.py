# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ospfdialog.ui'
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
    QGraphicsView, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_OSPFDialog(object):
    def setupUi(self, OSPFDialog):
        if not OSPFDialog.objectName():
            OSPFDialog.setObjectName(u"OSPFDialog")
        OSPFDialog.resize(1024, 768)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(OSPFDialog.sizePolicy().hasHeightForWidth())
        OSPFDialog.setSizePolicy(sizePolicy)
        OSPFDialog.setMinimumSize(QSize(800, 500))
        OSPFDialog.setMaximumSize(QSize(1440, 900))
        OSPFDialog.setAutoFillBackground(False)
        self.horizontalLayout = QHBoxLayout(OSPFDialog)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.global_parameters_groupbox = QGroupBox(OSPFDialog)
        self.global_parameters_groupbox.setObjectName(u"global_parameters_groupbox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.global_parameters_groupbox.sizePolicy().hasHeightForWidth())
        self.global_parameters_groupbox.setSizePolicy(sizePolicy1)
        self.global_parameters_groupbox.setMinimumSize(QSize(180, 0))
        self.global_parameters_groupbox.setBaseSize(QSize(200, 200))
        self.verticalLayout_7 = QVBoxLayout(self.global_parameters_groupbox)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.area_number_label = QLabel(self.global_parameters_groupbox)
        self.area_number_label.setObjectName(u"area_number_label")
        sizePolicy.setHeightForWidth(self.area_number_label.sizePolicy().hasHeightForWidth())
        self.area_number_label.setSizePolicy(sizePolicy)

        self.verticalLayout_7.addWidget(self.area_number_label, 0, Qt.AlignmentFlag.AlignLeft)

        self.area_number_input = QLineEdit(self.global_parameters_groupbox)
        self.area_number_input.setObjectName(u"area_number_input")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.area_number_input.sizePolicy().hasHeightForWidth())
        self.area_number_input.setSizePolicy(sizePolicy2)

        self.verticalLayout_7.addWidget(self.area_number_input)

        self.reference_bandwidth_label = QLabel(self.global_parameters_groupbox)
        self.reference_bandwidth_label.setObjectName(u"reference_bandwidth_label")
        sizePolicy.setHeightForWidth(self.reference_bandwidth_label.sizePolicy().hasHeightForWidth())
        self.reference_bandwidth_label.setSizePolicy(sizePolicy)

        self.verticalLayout_7.addWidget(self.reference_bandwidth_label, 0, Qt.AlignmentFlag.AlignLeft)

        self.reference_bandwidth_input = QLineEdit(self.global_parameters_groupbox)
        self.reference_bandwidth_input.setObjectName(u"reference_bandwidth_input")
        sizePolicy2.setHeightForWidth(self.reference_bandwidth_input.sizePolicy().hasHeightForWidth())
        self.reference_bandwidth_input.setSizePolicy(sizePolicy2)

        self.verticalLayout_7.addWidget(self.reference_bandwidth_input)

        self.timers_groupbox = QGroupBox(self.global_parameters_groupbox)
        self.timers_groupbox.setObjectName(u"timers_groupbox")
        sizePolicy.setHeightForWidth(self.timers_groupbox.sizePolicy().hasHeightForWidth())
        self.timers_groupbox.setSizePolicy(sizePolicy)
        self.timers_groupbox.setMinimumSize(QSize(0, 0))
        self.verticalLayout_8 = QVBoxLayout(self.timers_groupbox)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.hello_label = QLabel(self.timers_groupbox)
        self.hello_label.setObjectName(u"hello_label")
        sizePolicy.setHeightForWidth(self.hello_label.sizePolicy().hasHeightForWidth())
        self.hello_label.setSizePolicy(sizePolicy)

        self.verticalLayout_8.addWidget(self.hello_label, 0, Qt.AlignmentFlag.AlignLeft)

        self.hello_input = QLineEdit(self.timers_groupbox)
        self.hello_input.setObjectName(u"hello_input")
        sizePolicy.setHeightForWidth(self.hello_input.sizePolicy().hasHeightForWidth())
        self.hello_input.setSizePolicy(sizePolicy)

        self.verticalLayout_8.addWidget(self.hello_input)

        self.dead_label = QLabel(self.timers_groupbox)
        self.dead_label.setObjectName(u"dead_label")
        sizePolicy.setHeightForWidth(self.dead_label.sizePolicy().hasHeightForWidth())
        self.dead_label.setSizePolicy(sizePolicy)

        self.verticalLayout_8.addWidget(self.dead_label, 0, Qt.AlignmentFlag.AlignLeft)

        self.dead_input = QLineEdit(self.timers_groupbox)
        self.dead_input.setObjectName(u"dead_input")
        sizePolicy.setHeightForWidth(self.dead_input.sizePolicy().hasHeightForWidth())
        self.dead_input.setSizePolicy(sizePolicy)

        self.verticalLayout_8.addWidget(self.dead_input)


        self.verticalLayout_7.addWidget(self.timers_groupbox)


        self.verticalLayout_2.addWidget(self.global_parameters_groupbox, 0, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.per_device_parameters_groupbox = QGroupBox(OSPFDialog)
        self.per_device_parameters_groupbox.setObjectName(u"per_device_parameters_groupbox")
        sizePolicy1.setHeightForWidth(self.per_device_parameters_groupbox.sizePolicy().hasHeightForWidth())
        self.per_device_parameters_groupbox.setSizePolicy(sizePolicy1)
        self.per_device_parameters_groupbox.setMinimumSize(QSize(180, 0))
        self.verticalLayout = QVBoxLayout(self.per_device_parameters_groupbox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.routerid_label = QLabel(self.per_device_parameters_groupbox)
        self.routerid_label.setObjectName(u"routerid_label")

        self.verticalLayout.addWidget(self.routerid_label)

        self.routerid_input = QLineEdit(self.per_device_parameters_groupbox)
        self.routerid_input.setObjectName(u"routerid_input")

        self.verticalLayout.addWidget(self.routerid_input)


        self.verticalLayout_2.addWidget(self.per_device_parameters_groupbox, 0, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.ok_cancel_buttons = QDialogButtonBox(OSPFDialog)
        self.ok_cancel_buttons.setObjectName(u"ok_cancel_buttons")
        sizePolicy.setHeightForWidth(self.ok_cancel_buttons.sizePolicy().hasHeightForWidth())
        self.ok_cancel_buttons.setSizePolicy(sizePolicy)
        self.ok_cancel_buttons.setMinimumSize(QSize(0, 0))
        self.ok_cancel_buttons.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout_2.addWidget(self.ok_cancel_buttons, 0, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignBottom)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.graphicsView = QGraphicsView(OSPFDialog)
        self.graphicsView.setObjectName(u"graphicsView")
        sizePolicy.setHeightForWidth(self.graphicsView.sizePolicy().hasHeightForWidth())
        self.graphicsView.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.graphicsView)

        self.right_layout = QVBoxLayout()
        self.right_layout.setObjectName(u"right_layout")
        self.networks_groupbox = QGroupBox(OSPFDialog)
        self.networks_groupbox.setObjectName(u"networks_groupbox")
        sizePolicy.setHeightForWidth(self.networks_groupbox.sizePolicy().hasHeightForWidth())
        self.networks_groupbox.setSizePolicy(sizePolicy)
        self.verticalLayout_5 = QVBoxLayout(self.networks_groupbox)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.networks_table = QTableWidget(self.networks_groupbox)
        self.networks_table.setObjectName(u"networks_table")
        sizePolicy.setHeightForWidth(self.networks_table.sizePolicy().hasHeightForWidth())
        self.networks_table.setSizePolicy(sizePolicy)

        self.verticalLayout_5.addWidget(self.networks_table)

        self.network_buttons_layout = QHBoxLayout()
        self.network_buttons_layout.setObjectName(u"network_buttons_layout")
        self.add_network_button = QPushButton(self.networks_groupbox)
        self.add_network_button.setObjectName(u"add_network_button")
        sizePolicy2.setHeightForWidth(self.add_network_button.sizePolicy().hasHeightForWidth())
        self.add_network_button.setSizePolicy(sizePolicy2)

        self.network_buttons_layout.addWidget(self.add_network_button)

        self.delete_network_button = QPushButton(self.networks_groupbox)
        self.delete_network_button.setObjectName(u"delete_network_button")
        sizePolicy2.setHeightForWidth(self.delete_network_button.sizePolicy().hasHeightForWidth())
        self.delete_network_button.setSizePolicy(sizePolicy2)

        self.network_buttons_layout.addWidget(self.delete_network_button)


        self.verticalLayout_5.addLayout(self.network_buttons_layout)


        self.right_layout.addWidget(self.networks_groupbox, 0, Qt.AlignmentFlag.AlignRight)

        self.passive_interfaces_groupbox = QGroupBox(OSPFDialog)
        self.passive_interfaces_groupbox.setObjectName(u"passive_interfaces_groupbox")
        sizePolicy.setHeightForWidth(self.passive_interfaces_groupbox.sizePolicy().hasHeightForWidth())
        self.passive_interfaces_groupbox.setSizePolicy(sizePolicy)
        self.verticalLayout_9 = QVBoxLayout(self.passive_interfaces_groupbox)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.passive_interfaces_table = QTableWidget(self.passive_interfaces_groupbox)
        self.passive_interfaces_table.setObjectName(u"passive_interfaces_table")
        sizePolicy.setHeightForWidth(self.passive_interfaces_table.sizePolicy().hasHeightForWidth())
        self.passive_interfaces_table.setSizePolicy(sizePolicy)

        self.verticalLayout_9.addWidget(self.passive_interfaces_table)


        self.right_layout.addWidget(self.passive_interfaces_groupbox, 0, Qt.AlignmentFlag.AlignRight)


        self.horizontalLayout.addLayout(self.right_layout)

#if QT_CONFIG(shortcut)
        self.area_number_label.setBuddy(self.area_number_input)
        self.reference_bandwidth_label.setBuddy(self.reference_bandwidth_input)
        self.hello_label.setBuddy(self.hello_input)
        self.dead_label.setBuddy(self.dead_input)
#endif // QT_CONFIG(shortcut)

        self.retranslateUi(OSPFDialog)

        QMetaObject.connectSlotsByName(OSPFDialog)
    # setupUi

    def retranslateUi(self, OSPFDialog):
        OSPFDialog.setWindowTitle(QCoreApplication.translate("OSPFDialog", u"OSPF configuration", None))
        self.global_parameters_groupbox.setTitle(QCoreApplication.translate("OSPFDialog", u"Global parameters:", None))
#if QT_CONFIG(tooltip)
        self.area_number_label.setToolTip(QCoreApplication.translate("OSPFDialog", u"Specifiy OSPF area number. Defaults to 0.", None))
#endif // QT_CONFIG(tooltip)
        self.area_number_label.setText(QCoreApplication.translate("OSPFDialog", u"Area number:", None))
#if QT_CONFIG(tooltip)
        self.area_number_input.setToolTip(QCoreApplication.translate("OSPFDialog", u"Specifiy OSPF area number. Defaults to 0.0.0.0", None))
#endif // QT_CONFIG(tooltip)
        self.area_number_input.setText(QCoreApplication.translate("OSPFDialog", u"0.0.0.0", None))
        self.area_number_input.setPlaceholderText(QCoreApplication.translate("OSPFDialog", u"0.0.0.0", None))
#if QT_CONFIG(tooltip)
        self.reference_bandwidth_label.setToolTip(QCoreApplication.translate("OSPFDialog", u"Specifiy reference bandwidth. Used for calculating cost.", None))
#endif // QT_CONFIG(tooltip)
        self.reference_bandwidth_label.setText(QCoreApplication.translate("OSPFDialog", u"Reference bandwidth (Mb/s):", None))
#if QT_CONFIG(tooltip)
        self.reference_bandwidth_input.setToolTip(QCoreApplication.translate("OSPFDialog", u"Specifiy reference bandwidth in megabits per second. Used for calculating cost.", None))
#endif // QT_CONFIG(tooltip)
        self.timers_groupbox.setTitle(QCoreApplication.translate("OSPFDialog", u"Timers:", None))
#if QT_CONFIG(tooltip)
        self.hello_label.setToolTip(QCoreApplication.translate("OSPFDialog", u"Specify OSPF hello timer.", None))
#endif // QT_CONFIG(tooltip)
        self.hello_label.setText(QCoreApplication.translate("OSPFDialog", u"Hello timer:", None))
#if QT_CONFIG(tooltip)
        self.hello_input.setToolTip(QCoreApplication.translate("OSPFDialog", u"Specify OSPF hello timer.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.dead_label.setToolTip(QCoreApplication.translate("OSPFDialog", u"Specify OSPF dead timer.", None))
#endif // QT_CONFIG(tooltip)
        self.dead_label.setText(QCoreApplication.translate("OSPFDialog", u"Dead timer:", None))
#if QT_CONFIG(tooltip)
        self.dead_input.setToolTip(QCoreApplication.translate("OSPFDialog", u"Specify OSPF dead timer.", None))
#endif // QT_CONFIG(tooltip)
        self.per_device_parameters_groupbox.setTitle(QCoreApplication.translate("OSPFDialog", u"Per-device parameters:", None))
        self.routerid_label.setText(QCoreApplication.translate("OSPFDialog", u"Router-ID", None))
#if QT_CONFIG(tooltip)
        self.networks_groupbox.setToolTip(QCoreApplication.translate("OSPFDialog", u"List of configured OSPF networks.", None))
#endif // QT_CONFIG(tooltip)
        self.networks_groupbox.setTitle(QCoreApplication.translate("OSPFDialog", u"Networks:", None))
#if QT_CONFIG(tooltip)
        self.add_network_button.setToolTip(QCoreApplication.translate("OSPFDialog", u"Add another network", None))
#endif // QT_CONFIG(tooltip)
        self.add_network_button.setText(QCoreApplication.translate("OSPFDialog", u"Add network", None))
#if QT_CONFIG(tooltip)
        self.delete_network_button.setToolTip(QCoreApplication.translate("OSPFDialog", u"Delete selected network", None))
#endif // QT_CONFIG(tooltip)
        self.delete_network_button.setText(QCoreApplication.translate("OSPFDialog", u"Delete network", None))
#if QT_CONFIG(tooltip)
        self.passive_interfaces_groupbox.setToolTip(QCoreApplication.translate("OSPFDialog", u"Select passive interfaces.", None))
#endif // QT_CONFIG(tooltip)
        self.passive_interfaces_groupbox.setTitle(QCoreApplication.translate("OSPFDialog", u"Passive interfaces:", None))
    # retranslateUi

