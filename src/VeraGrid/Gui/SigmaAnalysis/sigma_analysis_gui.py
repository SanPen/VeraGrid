# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sigma_analysis_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QMainWindow,
    QMenu, QMenuBar, QPushButton, QSizePolicy,
    QSlider, QSpacerItem, QSplitter, QStatusBar,
    QTabWidget, QTableView, QVBoxLayout, QWidget)

from VeraGrid.Gui.Widgets.matplotlibwidget import MatplotlibWidget
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1078, 643)
        icon = QIcon()
        icon.addFile(u":/Icons/icons/sigma.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
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
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.splitter_3 = QSplitter(self.centralwidget)
        self.splitter_3.setObjectName(u"splitter_3")
        self.splitter_3.setOrientation(Qt.Orientation.Horizontal)
        self.frame_8 = QFrame(self.splitter_3)
        self.frame_8.setObjectName(u"frame_8")
        self.frame_8.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_8.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_8)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(-1, 0, -1, -1)
        self.sigmaMethodLabel = QLabel(self.frame_8)
        self.sigmaMethodLabel.setObjectName(u"sigmaMethodLabel")

        self.verticalLayout_4.addWidget(self.sigmaMethodLabel)

        self.sigmaMethodComboBox = QComboBox(self.frame_8)
        self.sigmaMethodComboBox.addItem("")
        self.sigmaMethodComboBox.addItem("")
        self.sigmaMethodComboBox.setObjectName(u"sigmaMethodComboBox")

        self.verticalLayout_4.addWidget(self.sigmaMethodComboBox)

        self.sigmaStartingPointLabel = QLabel(self.frame_8)
        self.sigmaStartingPointLabel.setObjectName(u"sigmaStartingPointLabel")

        self.verticalLayout_4.addWidget(self.sigmaStartingPointLabel)

        self.sigmaStartingPointComboBox = QComboBox(self.frame_8)
        self.sigmaStartingPointComboBox.addItem("")
        self.sigmaStartingPointComboBox.addItem("")
        self.sigmaStartingPointComboBox.setObjectName(u"sigmaStartingPointComboBox")

        self.verticalLayout_4.addWidget(self.sigmaStartingPointComboBox)

        self.sigmaControlQCheckBox = QCheckBox(self.frame_8)
        self.sigmaControlQCheckBox.setObjectName(u"sigmaControlQCheckBox")

        self.verticalLayout_4.addWidget(self.sigmaControlQCheckBox)

        self.sigmaDiscreteShuntsCheckBox = QCheckBox(self.frame_8)
        self.sigmaDiscreteShuntsCheckBox.setObjectName(u"sigmaDiscreteShuntsCheckBox")
        self.sigmaDiscreteShuntsCheckBox.setChecked(True)

        self.verticalLayout_4.addWidget(self.sigmaDiscreteShuntsCheckBox)

        self.sigmaQvDroopCheckBox = QCheckBox(self.frame_8)
        self.sigmaQvDroopCheckBox.setObjectName(u"sigmaQvDroopCheckBox")
        self.sigmaQvDroopCheckBox.setChecked(True)

        self.verticalLayout_4.addWidget(self.sigmaQvDroopCheckBox)

        self.sigmaDistributedSlackCheckBox = QCheckBox(self.frame_8)
        self.sigmaDistributedSlackCheckBox.setObjectName(u"sigmaDistributedSlackCheckBox")

        self.verticalLayout_4.addWidget(self.sigmaDistributedSlackCheckBox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer)

        self.timeLabel = QLabel(self.frame_8)
        self.timeLabel.setObjectName(u"timeLabel")

        self.verticalLayout_4.addWidget(self.timeLabel)

        self.timeSlider = QSlider(self.frame_8)
        self.timeSlider.setObjectName(u"timeSlider")
        self.timeSlider.setOrientation(Qt.Orientation.Horizontal)

        self.verticalLayout_4.addWidget(self.timeSlider)

        self.sigmaRerunButton = QPushButton(self.frame_8)
        self.sigmaRerunButton.setObjectName(u"sigmaRerunButton")
        self.sigmaRerunButton.setIcon(icon)

        self.verticalLayout_4.addWidget(self.sigmaRerunButton)

        self.splitter_3.addWidget(self.frame_8)
        self.PlotFrame = QFrame(self.splitter_3)
        self.PlotFrame.setObjectName(u"PlotFrame")
        self.PlotFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.PlotFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.PlotFrame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.tabWidget = QTabWidget(self.PlotFrame)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_2 = QVBoxLayout(self.tab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.plotwidget = MatplotlibWidget(self.tab)
        self.plotwidget.setObjectName(u"plotwidget")

        self.verticalLayout_2.addWidget(self.plotwidget)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_3 = QVBoxLayout(self.tab_2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.tableView = QTableView(self.tab_2)
        self.tableView.setObjectName(u"tableView")

        self.verticalLayout_3.addWidget(self.tableView)

        self.tabWidget.addTab(self.tab_2, "")

        self.horizontalLayout.addWidget(self.tabWidget)

        self.splitter_3.addWidget(self.PlotFrame)

        self.verticalLayout.addWidget(self.splitter_3)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1078, 23))
        self.menuActions = QMenu(self.menubar)
        self.menuActions.setObjectName(u"menuActions")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuActions.menuAction())
        self.menuActions.addAction(self.actionCopy_to_clipboard)
        self.menuActions.addAction(self.actionSave)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionCopy_to_clipboard.setText(QCoreApplication.translate("MainWindow", u"Copy to clipboard", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.sigmaMethodLabel.setText(QCoreApplication.translate("MainWindow", u"Method", None))
        self.sigmaMethodComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"DPR HELM", None))
        self.sigmaMethodComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"Classical HELM", None))

        self.sigmaStartingPointLabel.setText(QCoreApplication.translate("MainWindow", u"DPR start", None))
        self.sigmaStartingPointComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"Stored guess", None))
        self.sigmaStartingPointComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"Classical no-load", None))

        self.sigmaControlQCheckBox.setText(QCoreApplication.translate("MainWindow", u"Q limits", None))
        self.sigmaDiscreteShuntsCheckBox.setText(QCoreApplication.translate("MainWindow", u"Discrete shunts", None))
        self.sigmaQvDroopCheckBox.setText(QCoreApplication.translate("MainWindow", u"QV droop", None))
        self.sigmaDistributedSlackCheckBox.setText(QCoreApplication.translate("MainWindow", u"Distributed slack", None))
        self.timeLabel.setText(QCoreApplication.translate("MainWindow", u"...", None))
        self.sigmaRerunButton.setText(QCoreApplication.translate("MainWindow", u"Re-run", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Plot", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Data", None))
        self.menuActions.setTitle(QCoreApplication.translate("MainWindow", u"Actions", None))
    # retranslateUi

