# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'block_data_dialogue.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout,
    QHeaderView, QListWidget, QListWidgetItem, QSizePolicy,
    QSplitter, QTableView, QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(925, 514)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.splitter_3 = QSplitter(Dialog)
        self.splitter_3.setObjectName(u"splitter_3")
        self.splitter_3.setOrientation(Qt.Orientation.Horizontal)
        self.frame_8 = QFrame(self.splitter_3)
        self.frame_8.setObjectName(u"frame_8")
        self.frame_8.setMaximumSize(QSize(400, 16777215))
        self.frame_8.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_8.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_7 = QVBoxLayout(self.frame_8)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(-1, 8, -1, -1)
        self.datalistWidget = QListWidget(self.frame_8)
        brush = QBrush(QColor(64, 191, 83, 255))
        brush.setStyle(Qt.BrushStyle.NoBrush)
        __qlistwidgetitem = QListWidgetItem(self.datalistWidget)
        __qlistwidgetitem.setForeground(brush);
        brush1 = QBrush(QColor(64, 191, 83, 255))
        brush1.setStyle(Qt.BrushStyle.NoBrush)
        __qlistwidgetitem1 = QListWidgetItem(self.datalistWidget)
        __qlistwidgetitem1.setForeground(brush1);
        brush2 = QBrush(QColor(26, 95, 180, 255))
        brush2.setStyle(Qt.BrushStyle.NoBrush)
        __qlistwidgetitem2 = QListWidgetItem(self.datalistWidget)
        __qlistwidgetitem2.setForeground(brush2);
        brush3 = QBrush(QColor(26, 95, 180, 255))
        brush3.setStyle(Qt.BrushStyle.NoBrush)
        __qlistwidgetitem3 = QListWidgetItem(self.datalistWidget)
        __qlistwidgetitem3.setForeground(brush3);
        brush4 = QBrush(QColor(255, 120, 0, 255))
        brush4.setStyle(Qt.BrushStyle.NoBrush)
        __qlistwidgetitem4 = QListWidgetItem(self.datalistWidget)
        __qlistwidgetitem4.setForeground(brush4);
        self.datalistWidget.setObjectName(u"datalistWidget")

        self.verticalLayout_7.addWidget(self.datalistWidget)

        self.splitter_3.addWidget(self.frame_8)
        self.PlotFrame = QFrame(self.splitter_3)
        self.PlotFrame.setObjectName(u"PlotFrame")
        self.PlotFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.PlotFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.PlotFrame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.splitter = QSplitter(self.PlotFrame)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.tableView_variables_and_params = QTableView(self.splitter)
        self.tableView_variables_and_params.setObjectName(u"tableView_variables_and_params")
        self.splitter.addWidget(self.tableView_variables_and_params)
        self.tableView_equations = QTableView(self.splitter)
        self.tableView_equations.setObjectName(u"tableView_equations")
        self.splitter.addWidget(self.tableView_equations)

        self.horizontalLayout.addWidget(self.splitter)

        self.splitter_3.addWidget(self.PlotFrame)

        self.verticalLayout.addWidget(self.splitter_3)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))

        __sortingEnabled = self.datalistWidget.isSortingEnabled()
        self.datalistWidget.setSortingEnabled(False)
        ___qlistwidgetitem = self.datalistWidget.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("Dialog", u"State variables", None));
        ___qlistwidgetitem1 = self.datalistWidget.item(1)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("Dialog", u"State equations", None));
        ___qlistwidgetitem2 = self.datalistWidget.item(2)
        ___qlistwidgetitem2.setText(QCoreApplication.translate("Dialog", u"Algebraic variables", None));
        ___qlistwidgetitem3 = self.datalistWidget.item(3)
        ___qlistwidgetitem3.setText(QCoreApplication.translate("Dialog", u"Algebraic equations", None));
        ___qlistwidgetitem4 = self.datalistWidget.item(4)
        ___qlistwidgetitem4.setText(QCoreApplication.translate("Dialog", u"Parameters", None));
        self.datalistWidget.setSortingEnabled(__sortingEnabled)

    # retranslateUi

