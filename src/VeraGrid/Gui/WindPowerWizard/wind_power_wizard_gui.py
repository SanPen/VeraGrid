# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'wind_power_wizard_gui.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QDoubleSpinBox,
    QFrame, QGridLayout, QHeaderView, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QSplitter,
    QTableView, QToolBox, QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(836, 561)
        icon = QIcon()
        icon.addFile(u":/Icons/icons/wind_power.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        MainWindow.setWindowIcon(icon)
        self.actionCopy_to_clipboard = QAction(MainWindow)
        self.actionCopy_to_clipboard.setObjectName(u"actionCopy_to_clipboard")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/copy.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionCopy_to_clipboard.setIcon(icon1)
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        icon2 = QIcon()
        icon2.addFile(u":/Icons/icons/import_profiles.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionSave.setIcon(icon2)
        self.verticalLayout = QVBoxLayout(MainWindow)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(MainWindow)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.frame = QFrame(self.splitter)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.toolBox = QToolBox(self.frame)
        self.toolBox.setObjectName(u"toolBox")
        self.libraryPage = QWidget()
        self.libraryPage.setObjectName(u"libraryPage")
        self.libraryPage.setGeometry(QRect(0, 0, 386, 509))
        self.gridLayout_2 = QGridLayout(self.libraryPage)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_2 = QLabel(self.libraryPage)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_2.addWidget(self.label_2, 0, 0, 1, 1)

        self.templeteComboBox = QComboBox(self.libraryPage)
        self.templeteComboBox.setObjectName(u"templeteComboBox")

        self.gridLayout_2.addWidget(self.templeteComboBox, 0, 1, 1, 1)

        self.loadButton = QPushButton(self.libraryPage)
        self.loadButton.setObjectName(u"loadButton")

        self.gridLayout_2.addWidget(self.loadButton, 0, 2, 1, 1)

        self.plotDesignCurvesButton = QPushButton(self.libraryPage)
        self.plotDesignCurvesButton.setObjectName(u"plotDesignCurvesButton")

        self.gridLayout_2.addWidget(self.plotDesignCurvesButton, 1, 0, 1, 3)

        self.windTurbineTableView = QTableView(self.libraryPage)
        self.windTurbineTableView.setObjectName(u"windTurbineTableView")

        self.gridLayout_2.addWidget(self.windTurbineTableView, 2, 0, 1, 3)

        self.toolBox.addItem(self.libraryPage, u"Turbine library")
        self.sitePage = QWidget()
        self.sitePage.setObjectName(u"sitePage")
        self.sitePage.setGeometry(QRect(0, 0, 386, 509))
        self.gridLayout_3 = QGridLayout(self.sitePage)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_3 = QLabel(self.sitePage)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_3.addWidget(self.label_3, 0, 0, 1, 2)

        self.label_4 = QLabel(self.sitePage)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_3.addWidget(self.label_4, 1, 0, 1, 1)

        self.latitudeSpinBox = QDoubleSpinBox(self.sitePage)
        self.latitudeSpinBox.setObjectName(u"latitudeSpinBox")
        self.latitudeSpinBox.setDecimals(6)
        self.latitudeSpinBox.setMinimum(-90.000000000000000)
        self.latitudeSpinBox.setMaximum(90.000000000000000)

        self.gridLayout_3.addWidget(self.latitudeSpinBox, 1, 1, 1, 1)

        self.label_5 = QLabel(self.sitePage)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_3.addWidget(self.label_5, 2, 0, 1, 1)

        self.longitudeSpinBox = QDoubleSpinBox(self.sitePage)
        self.longitudeSpinBox.setObjectName(u"longitudeSpinBox")
        self.longitudeSpinBox.setDecimals(6)
        self.longitudeSpinBox.setMinimum(-180.000000000000000)
        self.longitudeSpinBox.setMaximum(180.000000000000000)

        self.gridLayout_3.addWidget(self.longitudeSpinBox, 2, 1, 1, 1)

        self.label = QLabel(self.sitePage)
        self.label.setObjectName(u"label")

        self.gridLayout_3.addWidget(self.label, 3, 0, 1, 1)

        self.powerSpinBox = QDoubleSpinBox(self.sitePage)
        self.powerSpinBox.setObjectName(u"powerSpinBox")
        self.powerSpinBox.setMinimum(0.000001000000000)
        self.powerSpinBox.setMaximum(99999.000000000000000)

        self.gridLayout_3.addWidget(self.powerSpinBox, 3, 1, 1, 1)

        self.label_6 = QLabel(self.sitePage)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_3.addWidget(self.label_6, 4, 0, 1, 1)

        self.hubHeightSpinBox = QDoubleSpinBox(self.sitePage)
        self.hubHeightSpinBox.setObjectName(u"hubHeightSpinBox")
        self.hubHeightSpinBox.setMinimum(1.000000000000000)
        self.hubHeightSpinBox.setMaximum(300.000000000000000)
        self.hubHeightSpinBox.setValue(100.000000000000000)

        self.gridLayout_3.addWidget(self.hubHeightSpinBox, 4, 1, 1, 1)

        self.label_7 = QLabel(self.sitePage)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_3.addWidget(self.label_7, 5, 0, 1, 1)

        self.roughnessLengthSpinBox = QDoubleSpinBox(self.sitePage)
        self.roughnessLengthSpinBox.setObjectName(u"roughnessLengthSpinBox")
        self.roughnessLengthSpinBox.setDecimals(3)
        self.roughnessLengthSpinBox.setMinimum(0.000000000000000)
        self.roughnessLengthSpinBox.setMaximum(5.000000000000000)
        self.roughnessLengthSpinBox.setValue(0.100000000000000)

        self.gridLayout_3.addWidget(self.roughnessLengthSpinBox, 5, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer, 6, 0, 1, 1)

        self.toolBox.addItem(self.sitePage, u"Site and model")

        self.verticalLayout_2.addWidget(self.toolBox)

        self.splitter.addWidget(self.frame)
        self.frame_4 = QFrame(self.splitter)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Raised)
        self.gridLayout = QGridLayout(self.frame_4)
        self.gridLayout.setObjectName(u"gridLayout")
        self.plotButton = QPushButton(self.frame_4)
        self.plotButton.setObjectName(u"plotButton")

        self.gridLayout.addWidget(self.plotButton, 1, 0, 1, 2)

        self.horizontalSpacer_2 = QSpacerItem(394, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 1, 2, 1, 1)

        self.acceptButton = QPushButton(self.frame_4)
        self.acceptButton.setObjectName(u"acceptButton")

        self.gridLayout.addWidget(self.acceptButton, 1, 3, 1, 1)

        self.tableView_2 = QTableView(self.frame_4)
        self.tableView_2.setObjectName(u"tableView_2")

        self.gridLayout.addWidget(self.tableView_2, 0, 0, 1, 4)

        self.splitter.addWidget(self.frame_4)

        self.verticalLayout.addWidget(self.splitter)


        self.retranslateUi(MainWindow)

        self.toolBox.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Wind power wizard", None))
        self.actionCopy_to_clipboard.setText(QCoreApplication.translate("MainWindow", u"Copy to clipboard", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Template", None))
        self.loadButton.setText(QCoreApplication.translate("MainWindow", u"Generate", None))
        self.plotDesignCurvesButton.setText(QCoreApplication.translate("MainWindow", u"Plot design curves", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.libraryPage), QCoreApplication.translate("MainWindow", u"Turbine library", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Wind turbine data", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Latitude", None))
        self.latitudeSpinBox.setSuffix(QCoreApplication.translate("MainWindow", u" deg", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Longitude", None))
        self.longitudeSpinBox.setSuffix(QCoreApplication.translate("MainWindow", u" deg", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Power", None))
        self.powerSpinBox.setSuffix(QCoreApplication.translate("MainWindow", u" MW", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Hub height", None))
        self.hubHeightSpinBox.setSuffix(QCoreApplication.translate("MainWindow", u" m", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Roughness", None))
        self.roughnessLengthSpinBox.setSuffix(QCoreApplication.translate("MainWindow", u" m", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.sitePage), QCoreApplication.translate("MainWindow", u"Site and model", None))
        self.plotButton.setText(QCoreApplication.translate("MainWindow", u"Plot", None))
        self.acceptButton.setText(QCoreApplication.translate("MainWindow", u"Accept", None))
    # retranslateUi
