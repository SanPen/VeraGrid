# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'rms_model_editor.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
    QLabel, QMainWindow, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(966, 538)
        self.actionCheckModel = QAction(MainWindow)
        self.actionCheckModel.setObjectName(u"actionCheckModel")
        self.actionCheckModel.setMenuRole(QAction.MenuRole.NoRole)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setMaximumSize(QSize(16777215, 40))
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.model_selector_comboBox = QComboBox(self.frame)
        self.model_selector_comboBox.addItem("")
        self.model_selector_comboBox.addItem("")
        self.model_selector_comboBox.addItem("")
        self.model_selector_comboBox.setObjectName(u"model_selector_comboBox")

        self.horizontalLayout.addWidget(self.model_selector_comboBox)

        self.horizontalSpacer = QSpacerItem(856, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.currently_editing_block_label = QLabel(self.frame)
        self.currently_editing_block_label.setObjectName(u"currently_editing_block_label")

        self.horizontalLayout.addWidget(self.currently_editing_block_label)

        self.horizontalSpacer_2 = QSpacerItem(48, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.currently_editing_object_label = QLabel(self.frame)
        self.currently_editing_object_label.setObjectName(u"currently_editing_object_label")

        self.horizontalLayout.addWidget(self.currently_editing_object_label)


        self.verticalLayout.addWidget(self.frame)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setObjectName(u"mainLayout")

        self.verticalLayout.addLayout(self.mainLayout)

        self.frame_2 = QFrame(self.centralwidget)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setMaximumSize(QSize(16777215, 40))
        self.frame_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.InitGuessButton = QPushButton(self.frame_2)
        self.InitGuessButton.setObjectName(u"InitGuessButton")

        self.horizontalLayout_2.addWidget(self.InitGuessButton)

        self.horizontalSpacer_3 = QSpacerItem(859, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.doItButton = QPushButton(self.frame_2)
        self.doItButton.setObjectName(u"doItButton")

        self.horizontalLayout_2.addWidget(self.doItButton)


        self.verticalLayout.addWidget(self.frame_2)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionCheckModel.setText(QCoreApplication.translate("MainWindow", u"CheckModel", None))
        self.model_selector_comboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"Template model", None))
        self.model_selector_comboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"Block editor model", None))
        self.model_selector_comboBox.setItemText(2, QCoreApplication.translate("MainWindow", u"Equations editor model", None))

        self.model_selector_comboBox.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Select model to apply", None))
        self.currently_editing_block_label.setText(QCoreApplication.translate("MainWindow", u"Submodel:", None))
        self.currently_editing_object_label.setText(QCoreApplication.translate("MainWindow", u"Device:", None))
        self.InitGuessButton.setText(QCoreApplication.translate("MainWindow", u"Add Initial Values", None))
        self.doItButton.setText(QCoreApplication.translate("MainWindow", u"Do it!", None))
    # retranslateUi

