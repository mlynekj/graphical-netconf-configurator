# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'xmldatadialog.ui'
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
    QFrame, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QSizePolicy, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget)

class Ui_XMLDataDialog(object):
    def setupUi(self, XMLDataDialog):
        if not XMLDataDialog.objectName():
            XMLDataDialog.setObjectName(u"XMLDataDialog")
        XMLDataDialog.resize(743, 408)
        self.verticalLayout = QVBoxLayout(XMLDataDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.top_laout = QHBoxLayout()
        self.top_laout.setObjectName(u"top_laout")
        self.header = QLabel(XMLDataDialog)
        self.header.setObjectName(u"header")

        self.top_laout.addWidget(self.header, 0, Qt.AlignmentFlag.AlignLeft)

        self.refresh_button = QPushButton(XMLDataDialog)
        self.refresh_button.setObjectName(u"refresh_button")
        self.refresh_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.top_laout.addWidget(self.refresh_button, 0, Qt.AlignmentFlag.AlignRight)

        self.separator = QFrame(XMLDataDialog)
        self.separator.setObjectName(u"separator")
        self.separator.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.separator.setAutoFillBackground(False)
        self.separator.setFrameShape(QFrame.Shape.VLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)

        self.top_laout.addWidget(self.separator, 0, Qt.AlignmentFlag.AlignRight)

        self.expand_button = QPushButton(XMLDataDialog)
        self.expand_button.setObjectName(u"expand_button")
        self.expand_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.top_laout.addWidget(self.expand_button, 0, Qt.AlignmentFlag.AlignRight)

        self.collapse_button = QPushButton(XMLDataDialog)
        self.collapse_button.setObjectName(u"collapse_button")
        self.collapse_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.top_laout.addWidget(self.collapse_button, 0, Qt.AlignmentFlag.AlignRight)

        self.top_laout.setStretch(0, 1)

        self.verticalLayout.addLayout(self.top_laout)

        self.data_tree = QTreeWidget(XMLDataDialog)
        self.data_tree.setObjectName(u"data_tree")

        self.verticalLayout.addWidget(self.data_tree)

        self.close_button_box = QDialogButtonBox(XMLDataDialog)
        self.close_button_box.setObjectName(u"close_button_box")
        self.close_button_box.setStandardButtons(QDialogButtonBox.StandardButton.Close)

        self.verticalLayout.addWidget(self.close_button_box)


        self.retranslateUi(XMLDataDialog)

        QMetaObject.connectSlotsByName(XMLDataDialog)
    # setupUi

    def retranslateUi(self, XMLDataDialog):
        XMLDataDialog.setWindowTitle(QCoreApplication.translate("XMLDataDialog", u"Dialog", None))
        self.header.setText(QCoreApplication.translate("XMLDataDialog", u"xml_data", None))
        self.refresh_button.setText(QCoreApplication.translate("XMLDataDialog", u"Refresh", None))
        self.expand_button.setText(QCoreApplication.translate("XMLDataDialog", u"Expand all", None))
        self.collapse_button.setText(QCoreApplication.translate("XMLDataDialog", u"Collapse all", None))
        ___qtreewidgetitem = self.data_tree.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("XMLDataDialog", u"Element", None));
    # retranslateUi

