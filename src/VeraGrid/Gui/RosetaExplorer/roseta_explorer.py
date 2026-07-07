# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'roseta_explorer.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListView, QMainWindow, QMenu, QMenuBar,
    QProgressBar, QPushButton, QSizePolicy, QSpacerItem,
    QSplitter, QTabWidget, QTableView, QTreeView,
    QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_RosetaExplorer(object):
    def setupUi(self, RosetaExplorer):
        if not RosetaExplorer.objectName():
            RosetaExplorer.setObjectName(u"RosetaExplorer")
        RosetaExplorer.resize(1267, 789)
        RosetaExplorer.setBaseSize(QSize(0, 0))
        RosetaExplorer.setAcceptDrops(True)
        icon = QIcon()
        icon.addFile(u":/Icons/icons/roseta.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        RosetaExplorer.setWindowIcon(icon)
        RosetaExplorer.setAutoFillBackground(False)
        RosetaExplorer.setIconSize(QSize(48, 48))
        RosetaExplorer.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        RosetaExplorer.setDocumentMode(False)
        RosetaExplorer.setTabShape(QTabWidget.TabShape.Rounded)
        RosetaExplorer.setDockNestingEnabled(False)
        RosetaExplorer.setUnifiedTitleAndToolBarOnMac(False)
        self.actionSave_logs = QAction(RosetaExplorer)
        self.actionSave_logs.setObjectName(u"actionSave_logs")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/save.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionSave_logs.setIcon(icon1)
        self.centralwidget = QWidget(RosetaExplorer)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.mainTabWidget = QTabWidget(self.frame)
        self.mainTabWidget.setObjectName(u"mainTabWidget")
        self.dataTabLayout = QWidget()
        self.dataTabLayout.setObjectName(u"dataTabLayout")
        self.verticalLayout_4 = QVBoxLayout(self.dataTabLayout)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(6, 6, 6, 6)
        self.modelTabWidget = QTabWidget(self.dataTabLayout)
        self.modelTabWidget.setObjectName(u"modelTabWidget")
        self.modelTabWidget.setTabPosition(QTabWidget.TabPosition.South)
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_5 = QVBoxLayout(self.tab_2)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.frame_5 = QFrame(self.tab_2)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_5.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.treeFilterLineEdit = QLineEdit(self.frame_5)
        self.treeFilterLineEdit.setObjectName(u"treeFilterLineEdit")

        self.horizontalLayout_3.addWidget(self.treeFilterLineEdit)

        self.treeFilterComboBox = QComboBox(self.frame_5)
        self.treeFilterComboBox.setObjectName(u"treeFilterComboBox")

        self.horizontalLayout_3.addWidget(self.treeFilterComboBox)

        self.treeFilterButton = QPushButton(self.frame_5)
        self.treeFilterButton.setObjectName(u"treeFilterButton")

        self.horizontalLayout_3.addWidget(self.treeFilterButton)


        self.verticalLayout_5.addWidget(self.frame_5)

        self.mainTreeView = QTreeView(self.tab_2)
        self.mainTreeView.setObjectName(u"mainTreeView")

        self.verticalLayout_5.addWidget(self.mainTreeView)

        icon2 = QIcon()
        icon2.addFile(u":/Icons/icons/array.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.modelTabWidget.addTab(self.tab_2, icon2, "")
        self.modelTab = QWidget()
        self.modelTab.setObjectName(u"modelTab")
        self.verticalLayout_10 = QVBoxLayout(self.modelTab)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.main_splitter = QSplitter(self.modelTab)
        self.main_splitter.setObjectName(u"main_splitter")
        self.main_splitter.setOrientation(Qt.Orientation.Horizontal)
        self.frame_2 = QFrame(self.main_splitter)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.frame_2)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.frame_7 = QFrame(self.frame_2)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setMinimumSize(QSize(0, 26))
        self.frame_7.setMaximumSize(QSize(16777215, 16777215))
        self.frame_7.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_7.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_7)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.modelTypeLabel = QLabel(self.frame_7)
        self.modelTypeLabel.setObjectName(u"modelTypeLabel")

        self.horizontalLayout_2.addWidget(self.modelTypeLabel)

        self.horizontalSpacer = QSpacerItem(529, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)


        self.verticalLayout_6.addWidget(self.frame_7)

        self.clasesListView = QListView(self.frame_2)
        self.clasesListView.setObjectName(u"clasesListView")

        self.verticalLayout_6.addWidget(self.clasesListView)

        self.main_splitter.addWidget(self.frame_2)
        self.frame_6 = QFrame(self.main_splitter)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_6.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame_6)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(1, 1, 1, 1)
        self.frame_4 = QFrame(self.frame_6)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setMaximumSize(QSize(16777215, 40))
        self.frame_4.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_4)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.filterLineEdit = QLineEdit(self.frame_4)
        self.filterLineEdit.setObjectName(u"filterLineEdit")

        self.horizontalLayout.addWidget(self.filterLineEdit)

        self.filterComboBox = QComboBox(self.frame_4)
        self.filterComboBox.setObjectName(u"filterComboBox")

        self.horizontalLayout.addWidget(self.filterComboBox)

        self.filterButton = QPushButton(self.frame_4)
        self.filterButton.setObjectName(u"filterButton")

        self.horizontalLayout.addWidget(self.filterButton)


        self.verticalLayout_3.addWidget(self.frame_4)

        self.propertiesTableView = QTableView(self.frame_6)
        self.propertiesTableView.setObjectName(u"propertiesTableView")

        self.verticalLayout_3.addWidget(self.propertiesTableView)

        self.main_splitter.addWidget(self.frame_6)

        self.verticalLayout_10.addWidget(self.main_splitter)

        self.modelTabWidget.addTab(self.modelTab, icon2, "")
        self.loggerTab = QWidget()
        self.loggerTab.setObjectName(u"loggerTab")
        self.verticalLayout_9 = QVBoxLayout(self.loggerTab)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.loggerTreeView = QTreeView(self.loggerTab)
        self.loggerTreeView.setObjectName(u"loggerTreeView")

        self.verticalLayout_9.addWidget(self.loggerTreeView)

        icon3 = QIcon()
        icon3.addFile(u":/Icons/icons/data.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.modelTabWidget.addTab(self.loggerTab, icon3, "")

        self.verticalLayout_4.addWidget(self.modelTabWidget)

        self.mainTabWidget.addTab(self.dataTabLayout, icon2, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.horizontalLayout_4 = QHBoxLayout(self.tab)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.consoleLayout = QVBoxLayout()
        self.consoleLayout.setObjectName(u"consoleLayout")

        self.horizontalLayout_4.addLayout(self.consoleLayout)

        icon4 = QIcon()
        icon4.addFile(u":/Icons/icons/console.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.mainTabWidget.addTab(self.tab, icon4, "")

        self.verticalLayout.addWidget(self.mainTabWidget)


        self.verticalLayout_2.addWidget(self.frame)

        self.progress_frame = QFrame(self.centralwidget)
        self.progress_frame.setObjectName(u"progress_frame")
        self.progress_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.progress_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_7 = QGridLayout(self.progress_frame)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.cancelButton = QPushButton(self.progress_frame)
        self.cancelButton.setObjectName(u"cancelButton")
        self.cancelButton.setMinimumSize(QSize(0, 24))
        icon5 = QIcon()
        icon5.addFile(u":/Icons/icons/delete.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.cancelButton.setIcon(icon5)

        self.gridLayout_7.addWidget(self.cancelButton, 1, 0, 1, 1)

        self.progressBar = QProgressBar(self.progress_frame)
        self.progressBar.setObjectName(u"progressBar")
        palette = QPalette()
        brush = QBrush(QColor(159, 159, 159, 255))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, brush)
        brush1 = QBrush(QColor(159, 159, 159, 128))
        brush1.setStyle(Qt.BrushStyle.SolidPattern)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.PlaceholderText, brush1)
#endif
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, brush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.PlaceholderText, brush1)
#endif
        brush2 = QBrush(QColor(120, 120, 120, 255))
        brush2.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, brush2)
        brush3 = QBrush(QColor(0, 0, 0, 128))
        brush3.setStyle(Qt.BrushStyle.SolidPattern)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.PlaceholderText, brush3)
#endif
        self.progressBar.setPalette(palette)
        self.progressBar.setAutoFillBackground(False)
        self.progressBar.setStyleSheet(u"QProgressBar {\n"
"	border: 1px solid rgb(186, 189, 182);\n"
"    border-radius: 5px;\n"
"	text-align: center;\n"
"}\n"
"QProgressBar::chunk{\n"
"	background-color: rgb(0, 34, 43);\n"
"    color: rgb(255, 255, 255)\n"
"}\n"
"")
        self.progressBar.setValue(50)
        self.progressBar.setTextVisible(True)
        self.progressBar.setInvertedAppearance(False)

        self.gridLayout_7.addWidget(self.progressBar, 1, 1, 1, 1)

        self.progressLabel = QLabel(self.progress_frame)
        self.progressLabel.setObjectName(u"progressLabel")

        self.gridLayout_7.addWidget(self.progressLabel, 0, 1, 1, 1)


        self.verticalLayout_2.addWidget(self.progress_frame)

        RosetaExplorer.setCentralWidget(self.centralwidget)
        self.menuBar = QMenuBar(RosetaExplorer)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 1267, 23))
        self.menuFile = QMenu(self.menuBar)
        self.menuFile.setObjectName(u"menuFile")
        RosetaExplorer.setMenuBar(self.menuBar)

        self.menuBar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionSave_logs)

        self.retranslateUi(RosetaExplorer)

        self.mainTabWidget.setCurrentIndex(0)
        self.modelTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(RosetaExplorer)
    # setupUi

    def retranslateUi(self, RosetaExplorer):
        RosetaExplorer.setWindowTitle(QCoreApplication.translate("RosetaExplorer", u"Cgmes Explorer", None))
        self.actionSave_logs.setText(QCoreApplication.translate("RosetaExplorer", u"Save logs", None))
        self.treeFilterButton.setText(QCoreApplication.translate("RosetaExplorer", u"Filter", None))
        self.modelTabWidget.setTabText(self.modelTabWidget.indexOf(self.tab_2), QCoreApplication.translate("RosetaExplorer", u"Tree view", None))
        self.modelTypeLabel.setText(QCoreApplication.translate("RosetaExplorer", u"...", None))
        self.filterButton.setText(QCoreApplication.translate("RosetaExplorer", u"Filter", None))
        self.modelTabWidget.setTabText(self.modelTabWidget.indexOf(self.modelTab), QCoreApplication.translate("RosetaExplorer", u"Table view", None))
        self.modelTabWidget.setTabText(self.modelTabWidget.indexOf(self.loggerTab), QCoreApplication.translate("RosetaExplorer", u"Logger", None))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.dataTabLayout), QCoreApplication.translate("RosetaExplorer", u"Data", None))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.tab), QCoreApplication.translate("RosetaExplorer", u"Python", None))
#if QT_CONFIG(tooltip)
        self.cancelButton.setToolTip(QCoreApplication.translate("RosetaExplorer", u"Cancel process", None))
#endif // QT_CONFIG(tooltip)
        self.cancelButton.setText("")
        self.progressLabel.setText("")
        self.menuFile.setTitle(QCoreApplication.translate("RosetaExplorer", u"File", None))
    # retranslateUi

