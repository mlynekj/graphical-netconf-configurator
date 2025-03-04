# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ipsecdialog.ui'
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
    QDialogButtonBox, QGraphicsView, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QSizePolicy, QSpacerItem,
    QTabWidget, QVBoxLayout, QWidget)

class Ui_IPSECDialog(object):
    def setupUi(self, IPSECDialog):
        if not IPSECDialog.objectName():
            IPSECDialog.setObjectName(u"IPSECDialog")
        IPSECDialog.resize(618, 686)
        self.verticalLayout_2 = QVBoxLayout(IPSECDialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.graphicsView = QGraphicsView(IPSECDialog)
        self.graphicsView.setObjectName(u"graphicsView")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.graphicsView.sizePolicy().hasHeightForWidth())
        self.graphicsView.setSizePolicy(sizePolicy)
        self.graphicsView.setMinimumSize(QSize(605, 355))

        self.verticalLayout_2.addWidget(self.graphicsView, 0, Qt.AlignmentFlag.AlignHCenter)

        self.tabWidget = QTabWidget(IPSECDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.interfaces_tab = QWidget()
        self.interfaces_tab.setObjectName(u"interfaces_tab")
        self.verticalLayout = QVBoxLayout(self.interfaces_tab)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.dev1_groupbox = QGroupBox(self.interfaces_tab)
        self.dev1_groupbox.setObjectName(u"dev1_groupbox")
        self.gridLayout = QGridLayout(self.dev1_groupbox)
        self.gridLayout.setObjectName(u"gridLayout")
        self.dev1_LAN_network_lineedit = QLineEdit(self.dev1_groupbox)
        self.dev1_LAN_network_lineedit.setObjectName(u"dev1_LAN_network_lineedit")

        self.gridLayout.addWidget(self.dev1_LAN_network_lineedit, 0, 4, 1, 1)

        self.interface_label_2 = QLabel(self.dev1_groupbox)
        self.interface_label_2.setObjectName(u"interface_label_2")

        self.gridLayout.addWidget(self.interface_label_2, 1, 1, 1, 1)

        self.dev1_LAN_interface_combobox = QComboBox(self.dev1_groupbox)
        self.dev1_LAN_interface_combobox.setObjectName(u"dev1_LAN_interface_combobox")

        self.gridLayout.addWidget(self.dev1_LAN_interface_combobox, 0, 2, 1, 1)

        self.LAN_label_1 = QLabel(self.dev1_groupbox)
        self.LAN_label_1.setObjectName(u"LAN_label_1")

        self.gridLayout.addWidget(self.LAN_label_1, 0, 0, 1, 1)

        self.network_label_1 = QLabel(self.dev1_groupbox)
        self.network_label_1.setObjectName(u"network_label_1")

        self.gridLayout.addWidget(self.network_label_1, 0, 3, 1, 1)

        self.ip_label_1 = QLabel(self.dev1_groupbox)
        self.ip_label_1.setObjectName(u"ip_label_1")

        self.gridLayout.addWidget(self.ip_label_1, 1, 3, 1, 1)

        self.dev1_WAN_interface_combobox = QComboBox(self.dev1_groupbox)
        self.dev1_WAN_interface_combobox.setObjectName(u"dev1_WAN_interface_combobox")

        self.gridLayout.addWidget(self.dev1_WAN_interface_combobox, 1, 2, 1, 1)

        self.dev1_WAN_ip_lineedit = QLineEdit(self.dev1_groupbox)
        self.dev1_WAN_ip_lineedit.setObjectName(u"dev1_WAN_ip_lineedit")

        self.gridLayout.addWidget(self.dev1_WAN_ip_lineedit, 1, 4, 1, 1)

        self.interface_label_1 = QLabel(self.dev1_groupbox)
        self.interface_label_1.setObjectName(u"interface_label_1")

        self.gridLayout.addWidget(self.interface_label_1, 0, 1, 1, 1)

        self.WAN_label_1 = QLabel(self.dev1_groupbox)
        self.WAN_label_1.setObjectName(u"WAN_label_1")

        self.gridLayout.addWidget(self.WAN_label_1, 1, 0, 1, 1)


        self.verticalLayout.addWidget(self.dev1_groupbox)

        self.dev2_groupbox = QGroupBox(self.interfaces_tab)
        self.dev2_groupbox.setObjectName(u"dev2_groupbox")
        self.gridLayout_2 = QGridLayout(self.dev2_groupbox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.LAN_label_2 = QLabel(self.dev2_groupbox)
        self.LAN_label_2.setObjectName(u"LAN_label_2")

        self.gridLayout_2.addWidget(self.LAN_label_2, 0, 0, 1, 1)

        self.interface_label_3 = QLabel(self.dev2_groupbox)
        self.interface_label_3.setObjectName(u"interface_label_3")

        self.gridLayout_2.addWidget(self.interface_label_3, 0, 1, 1, 1)

        self.dev2_LAN_interface_combobox = QComboBox(self.dev2_groupbox)
        self.dev2_LAN_interface_combobox.setObjectName(u"dev2_LAN_interface_combobox")

        self.gridLayout_2.addWidget(self.dev2_LAN_interface_combobox, 0, 2, 1, 1)

        self.network_label_2 = QLabel(self.dev2_groupbox)
        self.network_label_2.setObjectName(u"network_label_2")

        self.gridLayout_2.addWidget(self.network_label_2, 0, 3, 1, 1)

        self.dev2_LAN_network_lineedit = QLineEdit(self.dev2_groupbox)
        self.dev2_LAN_network_lineedit.setObjectName(u"dev2_LAN_network_lineedit")

        self.gridLayout_2.addWidget(self.dev2_LAN_network_lineedit, 0, 4, 1, 1)

        self.WAN_label_2 = QLabel(self.dev2_groupbox)
        self.WAN_label_2.setObjectName(u"WAN_label_2")

        self.gridLayout_2.addWidget(self.WAN_label_2, 1, 0, 1, 1)

        self.interface_label_4 = QLabel(self.dev2_groupbox)
        self.interface_label_4.setObjectName(u"interface_label_4")

        self.gridLayout_2.addWidget(self.interface_label_4, 1, 1, 1, 1)

        self.dev2_WAN_interface_combobox = QComboBox(self.dev2_groupbox)
        self.dev2_WAN_interface_combobox.setObjectName(u"dev2_WAN_interface_combobox")

        self.gridLayout_2.addWidget(self.dev2_WAN_interface_combobox, 1, 2, 1, 1)

        self.ip_label_2 = QLabel(self.dev2_groupbox)
        self.ip_label_2.setObjectName(u"ip_label_2")

        self.gridLayout_2.addWidget(self.ip_label_2, 1, 3, 1, 1)

        self.dev2_WAN_ip_lineedit = QLineEdit(self.dev2_groupbox)
        self.dev2_WAN_ip_lineedit.setObjectName(u"dev2_WAN_ip_lineedit")

        self.gridLayout_2.addWidget(self.dev2_WAN_ip_lineedit, 1, 4, 1, 1)


        self.verticalLayout.addWidget(self.dev2_groupbox)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_3)

        self.tabWidget.addTab(self.interfaces_tab, "")
        self.ike_tab = QWidget()
        self.ike_tab.setObjectName(u"ike_tab")
        self.gridLayout_3 = QGridLayout(self.ike_tab)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.ike_auth_label = QLabel(self.ike_tab)
        self.ike_auth_label.setObjectName(u"ike_auth_label")

        self.gridLayout_3.addWidget(self.ike_auth_label, 0, 0, 1, 1)

        self.ike_enc_combobox = QComboBox(self.ike_tab)
        self.ike_enc_combobox.setObjectName(u"ike_enc_combobox")

        self.gridLayout_3.addWidget(self.ike_enc_combobox, 1, 1, 1, 1)

        self.ike_enc_label = QLabel(self.ike_tab)
        self.ike_enc_label.setObjectName(u"ike_enc_label")

        self.gridLayout_3.addWidget(self.ike_enc_label, 1, 0, 1, 1)

        self.ike_psk_input = QLineEdit(self.ike_tab)
        self.ike_psk_input.setObjectName(u"ike_psk_input")

        self.gridLayout_3.addWidget(self.ike_psk_input, 4, 1, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer_2, 5, 1, 1, 1)

        self.ike_auth_combobox = QComboBox(self.ike_tab)
        self.ike_auth_combobox.setObjectName(u"ike_auth_combobox")

        self.gridLayout_3.addWidget(self.ike_auth_combobox, 0, 1, 1, 1)

        self.ike_psk_label = QLabel(self.ike_tab)
        self.ike_psk_label.setObjectName(u"ike_psk_label")

        self.gridLayout_3.addWidget(self.ike_psk_label, 4, 0, 1, 1)

        self.ike_lifetime_label = QLabel(self.ike_tab)
        self.ike_lifetime_label.setObjectName(u"ike_lifetime_label")

        self.gridLayout_3.addWidget(self.ike_lifetime_label, 3, 0, 1, 1)

        self.ike_lifetime_input = QLineEdit(self.ike_tab)
        self.ike_lifetime_input.setObjectName(u"ike_lifetime_input")

        self.gridLayout_3.addWidget(self.ike_lifetime_input, 3, 1, 1, 1)

        self.ike_dh_label = QLabel(self.ike_tab)
        self.ike_dh_label.setObjectName(u"ike_dh_label")

        self.gridLayout_3.addWidget(self.ike_dh_label, 2, 0, 1, 1)

        self.ike_dh_combobox = QComboBox(self.ike_tab)
        self.ike_dh_combobox.setObjectName(u"ike_dh_combobox")

        self.gridLayout_3.addWidget(self.ike_dh_combobox, 2, 1, 1, 1)

        self.tabWidget.addTab(self.ike_tab, "")
        self.ipsec_tab = QWidget()
        self.ipsec_tab.setObjectName(u"ipsec_tab")
        self.gridLayout_4 = QGridLayout(self.ipsec_tab)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.ipsec_enc_label = QLabel(self.ipsec_tab)
        self.ipsec_enc_label.setObjectName(u"ipsec_enc_label")

        self.gridLayout_4.addWidget(self.ipsec_enc_label, 1, 0, 1, 1)

        self.ipsec_lifetime_input = QLineEdit(self.ipsec_tab)
        self.ipsec_lifetime_input.setObjectName(u"ipsec_lifetime_input")

        self.gridLayout_4.addWidget(self.ipsec_lifetime_input, 2, 1, 1, 1)

        self.ipsec_enc_combobox = QComboBox(self.ipsec_tab)
        self.ipsec_enc_combobox.setObjectName(u"ipsec_enc_combobox")

        self.gridLayout_4.addWidget(self.ipsec_enc_combobox, 1, 1, 1, 1)

        self.ipsec_auth_combobox = QComboBox(self.ipsec_tab)
        self.ipsec_auth_combobox.setObjectName(u"ipsec_auth_combobox")

        self.gridLayout_4.addWidget(self.ipsec_auth_combobox, 0, 1, 1, 1)

        self.ipsec_lifetime_label = QLabel(self.ipsec_tab)
        self.ipsec_lifetime_label.setObjectName(u"ipsec_lifetime_label")

        self.gridLayout_4.addWidget(self.ipsec_lifetime_label, 2, 0, 1, 1)

        self.ipsec_auth_label = QLabel(self.ipsec_tab)
        self.ipsec_auth_label.setObjectName(u"ipsec_auth_label")

        self.gridLayout_4.addWidget(self.ipsec_auth_label, 0, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_4.addItem(self.verticalSpacer, 3, 1, 1, 1)

        self.tabWidget.addTab(self.ipsec_tab, "")
        self.advanced_tab = QWidget()
        self.advanced_tab.setObjectName(u"advanced_tab")
        self.tabWidget.addTab(self.advanced_tab, "")

        self.verticalLayout_2.addWidget(self.tabWidget)

        self.buttonBox = QDialogButtonBox(IPSECDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout_2.addWidget(self.buttonBox)


        self.retranslateUi(IPSECDialog)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(IPSECDialog)
    # setupUi

    def retranslateUi(self, IPSECDialog):
        IPSECDialog.setWindowTitle(QCoreApplication.translate("IPSECDialog", u"Dialog", None))
        self.dev1_groupbox.setTitle(QCoreApplication.translate("IPSECDialog", u"dev1", None))
        self.interface_label_2.setText(QCoreApplication.translate("IPSECDialog", u"Interface", None))
        self.LAN_label_1.setText(QCoreApplication.translate("IPSECDialog", u"LAN", None))
        self.network_label_1.setText(QCoreApplication.translate("IPSECDialog", u"Network", None))
        self.ip_label_1.setText(QCoreApplication.translate("IPSECDialog", u"IP", None))
        self.interface_label_1.setText(QCoreApplication.translate("IPSECDialog", u"Interface", None))
        self.WAN_label_1.setText(QCoreApplication.translate("IPSECDialog", u"WAN", None))
        self.dev2_groupbox.setTitle(QCoreApplication.translate("IPSECDialog", u"dev2", None))
        self.LAN_label_2.setText(QCoreApplication.translate("IPSECDialog", u"LAN", None))
        self.interface_label_3.setText(QCoreApplication.translate("IPSECDialog", u"Interface", None))
        self.network_label_2.setText(QCoreApplication.translate("IPSECDialog", u"Network", None))
        self.WAN_label_2.setText(QCoreApplication.translate("IPSECDialog", u"WAN", None))
        self.interface_label_4.setText(QCoreApplication.translate("IPSECDialog", u"Interface", None))
        self.ip_label_2.setText(QCoreApplication.translate("IPSECDialog", u"IP", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.interfaces_tab), QCoreApplication.translate("IPSECDialog", u"Interfaces", None))
        self.ike_auth_label.setText(QCoreApplication.translate("IPSECDialog", u"Authentication algorithm", None))
        self.ike_enc_label.setText(QCoreApplication.translate("IPSECDialog", u"Encryption algorithm", None))
        self.ike_psk_label.setText(QCoreApplication.translate("IPSECDialog", u"Pre-shared key", None))
        self.ike_lifetime_label.setText(QCoreApplication.translate("IPSECDialog", u"Lifetime (seconds)", None))
        self.ike_dh_label.setText(QCoreApplication.translate("IPSECDialog", u"Diffie-Hellman group", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.ike_tab), QCoreApplication.translate("IPSECDialog", u"IKE", None))
        self.ipsec_enc_label.setText(QCoreApplication.translate("IPSECDialog", u"Encryption algorithm", None))
        self.ipsec_lifetime_label.setText(QCoreApplication.translate("IPSECDialog", u"Lifetime (seconds)", None))
        self.ipsec_auth_label.setText(QCoreApplication.translate("IPSECDialog", u"Authentication algorithm", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.ipsec_tab), QCoreApplication.translate("IPSECDialog", u"IPSec", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.advanced_tab), QCoreApplication.translate("IPSECDialog", u"Advanced", None))
    # retranslateUi

