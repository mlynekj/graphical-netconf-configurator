# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'pendingchangedetailsdialog.ui'
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
    QLabel, QSizePolicy, QTextBrowser, QVBoxLayout,
    QWidget)

class Ui_PendingChangeDetailsDialog(object):
    def setupUi(self, PendingChangeDetailsDialog):
        if not PendingChangeDetailsDialog.objectName():
            PendingChangeDetailsDialog.setObjectName(u"PendingChangeDetailsDialog")
        PendingChangeDetailsDialog.resize(690, 300)
        self.verticalLayout_3 = QVBoxLayout(PendingChangeDetailsDialog)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.header = QLabel(PendingChangeDetailsDialog)
        self.header.setObjectName(u"header")

        self.verticalLayout_3.addWidget(self.header)

        self.groupboxes_layout = QHBoxLayout()
        self.groupboxes_layout.setObjectName(u"groupboxes_layout")
        self.filter_groupbox = QGroupBox(PendingChangeDetailsDialog)
        self.filter_groupbox.setObjectName(u"filter_groupbox")
        self.verticalLayout_2 = QVBoxLayout(self.filter_groupbox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.filter_text_browser = QTextBrowser(self.filter_groupbox)
        self.filter_text_browser.setObjectName(u"filter_text_browser")

        self.verticalLayout_2.addWidget(self.filter_text_browser)


        self.groupboxes_layout.addWidget(self.filter_groupbox)

        self.rpc_reply_groupbox = QGroupBox(PendingChangeDetailsDialog)
        self.rpc_reply_groupbox.setObjectName(u"rpc_reply_groupbox")
        self.verticalLayout = QVBoxLayout(self.rpc_reply_groupbox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.rpc_reply_text_browser = QTextBrowser(self.rpc_reply_groupbox)
        self.rpc_reply_text_browser.setObjectName(u"rpc_reply_text_browser")

        self.verticalLayout.addWidget(self.rpc_reply_text_browser)


        self.groupboxes_layout.addWidget(self.rpc_reply_groupbox)


        self.verticalLayout_3.addLayout(self.groupboxes_layout)


        self.retranslateUi(PendingChangeDetailsDialog)

        QMetaObject.connectSlotsByName(PendingChangeDetailsDialog)
    # setupUi

    def retranslateUi(self, PendingChangeDetailsDialog):
        PendingChangeDetailsDialog.setWindowTitle(QCoreApplication.translate("PendingChangeDetailsDialog", u"Dialog", None))
        self.header.setText(QCoreApplication.translate("PendingChangeDetailsDialog", u"device_id:change", None))
        self.filter_groupbox.setTitle(QCoreApplication.translate("PendingChangeDetailsDialog", u"Filter", None))
        self.rpc_reply_groupbox.setTitle(QCoreApplication.translate("PendingChangeDetailsDialog", u"RPC Reply", None))
    # retranslateUi

