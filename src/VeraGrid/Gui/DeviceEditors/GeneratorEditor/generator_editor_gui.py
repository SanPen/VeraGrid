# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'generator_editor_gui.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
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
    QHeaderView, QPushButton, QSizePolicy, QSpacerItem,
    QSplitter, QTableView, QVBoxLayout, QWidget)

from VeraGrid.Gui.Widgets.matplotlibwidget import MatplotlibWidget

class Ui_GeneratorQCurveEditorDialog(object):
    def setupUi(self, GeneratorQCurveEditorDialog):
        if not GeneratorQCurveEditorDialog.objectName():
            GeneratorQCurveEditorDialog.setObjectName(u"GeneratorQCurveEditorDialog")
        GeneratorQCurveEditorDialog.resize(900, 520)
        self.verticalLayout = QVBoxLayout(GeneratorQCurveEditorDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(GeneratorQCurveEditorDialog)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.leftFrame = QFrame(self.splitter)
        self.leftFrame.setObjectName(u"leftFrame")
        self.leftLayout = QVBoxLayout(self.leftFrame)
        self.leftLayout.setObjectName(u"leftLayout")
        self.leftLayout.setContentsMargins(0, 0, 0, 0)
        self.tableView = QTableView(self.leftFrame)
        self.tableView.setObjectName(u"tableView")

        self.leftLayout.addWidget(self.tableView)

        self.buttonsFrame = QFrame(self.leftFrame)
        self.buttonsFrame.setObjectName(u"buttonsFrame")
        self.buttonsFrame.setMaximumSize(QSize(16777215, 40))
        self.buttonsLayout = QHBoxLayout(self.buttonsFrame)
        self.buttonsLayout.setObjectName(u"buttonsLayout")
        self.buttonsLayout.setContentsMargins(0, 0, 0, 0)
        self.addRowButton = QPushButton(self.buttonsFrame)
        self.addRowButton.setObjectName(u"addRowButton")

        self.buttonsLayout.addWidget(self.addRowButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttonsLayout.addItem(self.horizontalSpacer)

        self.delRowButton = QPushButton(self.buttonsFrame)
        self.delRowButton.setObjectName(u"delRowButton")

        self.buttonsLayout.addWidget(self.delRowButton)


        self.leftLayout.addWidget(self.buttonsFrame)

        self.splitter.addWidget(self.leftFrame)
        self.rightFrame = QFrame(self.splitter)
        self.rightFrame.setObjectName(u"rightFrame")
        self.rightLayout = QVBoxLayout(self.rightFrame)
        self.rightLayout.setObjectName(u"rightLayout")
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        self.plotter = MatplotlibWidget(self.rightFrame)
        self.plotter.setObjectName(u"plotter")

        self.rightLayout.addWidget(self.plotter)

        self.splitter.addWidget(self.rightFrame)

        self.verticalLayout.addWidget(self.splitter)


        self.retranslateUi(GeneratorQCurveEditorDialog)

        QMetaObject.connectSlotsByName(GeneratorQCurveEditorDialog)
    # setupUi

    def retranslateUi(self, GeneratorQCurveEditorDialog):
        GeneratorQCurveEditorDialog.setWindowTitle(QCoreApplication.translate("GeneratorQCurveEditorDialog", u"Reactive power curve editor", None))
        self.addRowButton.setText(QCoreApplication.translate("GeneratorQCurveEditorDialog", u"Add", None))
        self.delRowButton.setText(QCoreApplication.translate("GeneratorQCurveEditorDialog", u"Del", None))
    # retranslateUi

