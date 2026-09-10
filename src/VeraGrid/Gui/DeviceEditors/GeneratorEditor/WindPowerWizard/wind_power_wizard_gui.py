# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'wind_power_wizard_gui.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QSplitter, QTabWidget, QTableView,
    QVBoxLayout, QWidget)
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
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.frame = QFrame(self.splitter)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_2 = QGridLayout(self.frame)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setWordWrap(True)

        self.gridLayout_2.addWidget(self.label_3, 0, 0, 1, 2)

        self.label_4 = QLabel(self.frame)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_2.addWidget(self.label_4, 1, 0, 1, 1)

        self.latitudeSpinBox = QDoubleSpinBox(self.frame)
        self.latitudeSpinBox.setObjectName(u"latitudeSpinBox")
        self.latitudeSpinBox.setDecimals(6)
        self.latitudeSpinBox.setMinimum(-90.000000000000000)
        self.latitudeSpinBox.setMaximum(90.000000000000000)

        self.gridLayout_2.addWidget(self.latitudeSpinBox, 1, 1, 1, 1)

        self.label_5 = QLabel(self.frame)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_2.addWidget(self.label_5, 2, 0, 1, 1)

        self.longitudeSpinBox = QDoubleSpinBox(self.frame)
        self.longitudeSpinBox.setObjectName(u"longitudeSpinBox")
        self.longitudeSpinBox.setDecimals(6)
        self.longitudeSpinBox.setMinimum(-180.000000000000000)
        self.longitudeSpinBox.setMaximum(180.000000000000000)

        self.gridLayout_2.addWidget(self.longitudeSpinBox, 2, 1, 1, 1)

        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.gridLayout_2.addWidget(self.label, 3, 0, 1, 1)

        self.powerSpinBox = QDoubleSpinBox(self.frame)
        self.powerSpinBox.setObjectName(u"powerSpinBox")
        self.powerSpinBox.setMinimum(0.000000000000000)
        self.powerSpinBox.setMaximum(99999.000000000000000)

        self.gridLayout_2.addWidget(self.powerSpinBox, 3, 1, 1, 1)

        self.label_6 = QLabel(self.frame)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_2.addWidget(self.label_6, 4, 0, 1, 1)

        self.hubHeightSpinBox = QDoubleSpinBox(self.frame)
        self.hubHeightSpinBox.setObjectName(u"hubHeightSpinBox")
        self.hubHeightSpinBox.setMinimum(1.000000000000000)
        self.hubHeightSpinBox.setMaximum(300.000000000000000)
        self.hubHeightSpinBox.setValue(100.000000000000000)

        self.gridLayout_2.addWidget(self.hubHeightSpinBox, 4, 1, 1, 1)

        self.label_7 = QLabel(self.frame)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_2.addWidget(self.label_7, 5, 0, 1, 1)

        self.roughnessLengthSpinBox = QDoubleSpinBox(self.frame)
        self.roughnessLengthSpinBox.setObjectName(u"roughnessLengthSpinBox")
        self.roughnessLengthSpinBox.setDecimals(3)
        self.roughnessLengthSpinBox.setMinimum(0.000000000000000)
        self.roughnessLengthSpinBox.setMaximum(5.000000000000000)
        self.roughnessLengthSpinBox.setValue(0.100000000000000)

        self.gridLayout_2.addWidget(self.roughnessLengthSpinBox, 5, 1, 1, 1)

        self.localTimeCheckBox = QCheckBox(self.frame)
        self.localTimeCheckBox.setObjectName(u"localTimeCheckBox")

        self.gridLayout_2.addWidget(self.localTimeCheckBox, 6, 0, 1, 2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 8, 0, 1, 1)

        self.loadButton = QPushButton(self.frame)
        self.loadButton.setObjectName(u"loadButton")
        icon3 = QIcon()
        icon3.addFile(u":/Icons/icons/calculator.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.loadButton.setIcon(icon3)

        self.gridLayout_2.addWidget(self.loadButton, 7, 0, 1, 2)

        self.splitter.addWidget(self.frame)
        self.frame_4 = QFrame(self.splitter)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout = QGridLayout(self.frame_4)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalSpacer_2 = QSpacerItem(394, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 1, 3, 1, 1)

        self.acceptButton = QPushButton(self.frame_4)
        self.acceptButton.setObjectName(u"acceptButton")
        icon4 = QIcon()
        icon4.addFile(u":/Icons/icons/accept.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.acceptButton.setIcon(icon4)

        self.gridLayout.addWidget(self.acceptButton, 1, 4, 1, 1)

        self.tabWidget = QTabWidget(self.frame_4)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_4 = QVBoxLayout(self.tab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.tableView_2 = QTableView(self.tab)
        self.tableView_2.setObjectName(u"tableView_2")
        self.tableView_2.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout_4.addWidget(self.tableView_2)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_5 = QVBoxLayout(self.tab_2)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.frame_2 = QFrame(self.tab_2)
        self.frame_2.setObjectName(u"frame_2")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.templeteComboBox = QComboBox(self.frame_2)
        self.templeteComboBox.setObjectName(u"templeteComboBox")

        self.horizontalLayout.addWidget(self.templeteComboBox)

        self.plotDesignCurvesButton = QPushButton(self.frame_2)
        self.plotDesignCurvesButton.setObjectName(u"plotDesignCurvesButton")
        self.plotDesignCurvesButton.setMaximumSize(QSize(32, 16777215))
        icon5 = QIcon()
        icon5.addFile(u":/Icons/icons/plot.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.plotDesignCurvesButton.setIcon(icon5)

        self.horizontalLayout.addWidget(self.plotDesignCurvesButton)


        self.verticalLayout_5.addWidget(self.frame_2)

        self.windTurbineTableView = QTableView(self.tab_2)
        self.windTurbineTableView.setObjectName(u"windTurbineTableView")
        self.windTurbineTableView.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout_5.addWidget(self.windTurbineTableView)

        self.tabWidget.addTab(self.tab_2, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 5)

        self.plotButton = QPushButton(self.frame_4)
        self.plotButton.setObjectName(u"plotButton")
        self.plotButton.setIcon(icon5)

        self.gridLayout.addWidget(self.plotButton, 1, 0, 1, 3)

        self.splitter.addWidget(self.frame_4)

        self.verticalLayout.addWidget(self.splitter)


        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Wind power wizard", None))
        self.actionCopy_to_clipboard.setText(QCoreApplication.translate("MainWindow", u"Copy to clipboard", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
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
#if QT_CONFIG(tooltip)
        self.localTimeCheckBox.setToolTip(QCoreApplication.translate("MainWindow", u"Shift Open-Meteo GMT timestamps by longitude so the generated power matches the circuit timestamps as local solar time.", None))
#endif // QT_CONFIG(tooltip)
        self.localTimeCheckBox.setText(QCoreApplication.translate("MainWindow", u"Use local solar time", None))
#if QT_CONFIG(tooltip)
        self.loadButton.setToolTip(QCoreApplication.translate("MainWindow", u"Generate time series", None))
#endif // QT_CONFIG(tooltip)
        self.loadButton.setText("")
#if QT_CONFIG(tooltip)
        self.acceptButton.setToolTip(QCoreApplication.translate("MainWindow", u"Accept and apply", None))
#endif // QT_CONFIG(tooltip)
        self.acceptButton.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Time series", None))
#if QT_CONFIG(tooltip)
        self.plotDesignCurvesButton.setToolTip(QCoreApplication.translate("MainWindow", u"Plot design curves", None))
#endif // QT_CONFIG(tooltip)
        self.plotDesignCurvesButton.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Turbine model", None))
        self.plotButton.setText("")
    # retranslateUi

