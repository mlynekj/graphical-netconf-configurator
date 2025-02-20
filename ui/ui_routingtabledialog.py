# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'routingtabledialog.ui'
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
    QHeaderView, QLabel, QSizePolicy, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget)

class Ui_RoutingTableDialog(object):
    def setupUi(self, RoutingTableDialog):
        if not RoutingTableDialog.objectName():
            RoutingTableDialog.setObjectName(u"RoutingTableDialog")
        RoutingTableDialog.resize(743, 408)
        self.verticalLayout = QVBoxLayout(RoutingTableDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.header = QLabel(RoutingTableDialog)
        self.header.setObjectName(u"header")

        self.verticalLayout.addWidget(self.header)

        self.routing_table_tree = QTreeWidget(RoutingTableDialog)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.routing_table_tree.setHeaderItem(__qtreewidgetitem)
        self.routing_table_tree.setObjectName(u"routing_table_tree")

        self.verticalLayout.addWidget(self.routing_table_tree)

        self.close_button_box = QDialogButtonBox(RoutingTableDialog)
        self.close_button_box.setObjectName(u"close_button_box")
        self.close_button_box.setStandardButtons(QDialogButtonBox.StandardButton.Close)

        self.verticalLayout.addWidget(self.close_button_box)


        self.retranslateUi(RoutingTableDialog)

        QMetaObject.connectSlotsByName(RoutingTableDialog)
    # setupUi

    def retranslateUi(self, RoutingTableDialog):
        RoutingTableDialog.setWindowTitle(QCoreApplication.translate("RoutingTableDialog", u"Dialog", None))
        self.header.setText(QCoreApplication.translate("RoutingTableDialog", u"routing_table", None))
    # retranslateUi

