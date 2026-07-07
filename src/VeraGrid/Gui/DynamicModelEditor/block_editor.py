# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'block_editor.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGraphicsView, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QSpacerItem, QSplitter,
    QTabWidget, QTableView, QToolBar, QTreeView,
    QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_BlockEditorWindow(object):
    def setupUi(self, BlockEditorWindow):
        if not BlockEditorWindow.objectName():
            BlockEditorWindow.setObjectName(u"BlockEditorWindow")
        BlockEditorWindow.resize(1122, 610)
        self.block_editor_actionCheckModel = QAction(BlockEditorWindow)
        self.block_editor_actionCheckModel.setObjectName(u"block_editor_actionCheckModel")
        icon = QIcon()
        icon.addFile(u":/Icons/icons/calculator.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.block_editor_actionCheckModel.setIcon(icon)
        self.block_editor_actionCheckModel.setMenuRole(QAction.MenuRole.NoRole)
        self.actionCenter = QAction(BlockEditorWindow)
        self.actionCenter.setObjectName(u"actionCenter")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/resize.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionCenter.setIcon(icon1)
        self.actionCenter.setMenuRole(QAction.MenuRole.NoRole)
        self.actionZoom_in = QAction(BlockEditorWindow)
        self.actionZoom_in.setObjectName(u"actionZoom_in")
        icon2 = QIcon()
        icon2.addFile(u":/Icons/icons/zoom_in.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionZoom_in.setIcon(icon2)
        self.actionZoom_in.setMenuRole(QAction.MenuRole.NoRole)
        self.actionZoom_out = QAction(BlockEditorWindow)
        self.actionZoom_out.setObjectName(u"actionZoom_out")
        icon3 = QIcon()
        icon3.addFile(u":/Icons/icons/zoom_out.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionZoom_out.setIcon(icon3)
        self.actionZoom_out.setMenuRole(QAction.MenuRole.NoRole)
        self.centralwidget = QWidget(BlockEditorWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 0, 6, 0)
        self.frame_3 = QFrame(self.centralwidget)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.frame_3)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 6, 0, 0)
        self.splitter = QSplitter(self.frame_3)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.frame_6 = QFrame(self.splitter)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_6.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_6)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 6, 0)
        self.tabWidget = QTabWidget(self.frame_6)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.North)
        self.tabWidget.setDocumentMode(True)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_5 = QVBoxLayout(self.tab)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.libraryTreeView = QTreeView(self.tab)
        self.libraryTreeView.setObjectName(u"libraryTreeView")
        self.libraryTreeView.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout_5.addWidget(self.libraryTreeView)

        icon4 = QIcon()
        icon4.addFile(u":/Icons/icons/link-to-all.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tabWidget.addTab(self.tab, icon4, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_2 = QVBoxLayout(self.tab_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.variablesLabel = QLabel(self.tab_2)
        self.variablesLabel.setObjectName(u"variablesLabel")

        self.verticalLayout_2.addWidget(self.variablesLabel)

        self.variablesTableView = QTableView(self.tab_2)
        self.variablesTableView.setObjectName(u"variablesTableView")
        self.variablesTableView.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout_2.addWidget(self.variablesTableView)

        self.parametersLabel = QLabel(self.tab_2)
        self.parametersLabel.setObjectName(u"parametersLabel")

        self.verticalLayout_2.addWidget(self.parametersLabel)

        self.parametersTableView = QTableView(self.tab_2)
        self.parametersTableView.setObjectName(u"parametersTableView")
        self.parametersTableView.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout_2.addWidget(self.parametersTableView)

        self.equationsLabel = QLabel(self.tab_2)
        self.equationsLabel.setObjectName(u"equationsLabel")

        self.verticalLayout_2.addWidget(self.equationsLabel)

        self.equationsTableView = QTableView(self.tab_2)
        self.equationsTableView.setObjectName(u"equationsTableView")
        self.equationsTableView.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout_2.addWidget(self.equationsTableView)

        icon5 = QIcon()
        icon5.addFile(u":/Icons/icons/edit.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tabWidget.addTab(self.tab_2, icon5, "")

        self.verticalLayout_4.addWidget(self.tabWidget)

        self.splitter.addWidget(self.frame_6)
        self.frame_7 = QFrame(self.splitter)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_7.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame_7)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(6, 0, 0, 0)
        self.graphicsView = QGraphicsView(self.frame_7)
        self.graphicsView.setObjectName(u"graphicsView")

        self.verticalLayout_3.addWidget(self.graphicsView)

        self.splitter.addWidget(self.frame_7)

        self.verticalLayout_6.addWidget(self.splitter)


        self.verticalLayout.addWidget(self.frame_3)

        self.frame_2 = QFrame(self.centralwidget)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setMaximumSize(QSize(16777215, 40))
        self.frame_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.currently_editing_object_label = QLabel(self.frame_2)
        self.currently_editing_object_label.setObjectName(u"currently_editing_object_label")

        self.horizontalLayout_2.addWidget(self.currently_editing_object_label)

        self.deviceLabel = QLabel(self.frame_2)
        self.deviceLabel.setObjectName(u"deviceLabel")

        self.horizontalLayout_2.addWidget(self.deviceLabel)

        self.horizontalSpacer_3 = QSpacerItem(859, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.doItButton = QPushButton(self.frame_2)
        self.doItButton.setObjectName(u"doItButton")

        self.horizontalLayout_2.addWidget(self.doItButton)


        self.verticalLayout.addWidget(self.frame_2)

        BlockEditorWindow.setCentralWidget(self.centralwidget)
        self.menuBar = QMenuBar(BlockEditorWindow)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 1122, 23))
        BlockEditorWindow.setMenuBar(self.menuBar)
        self.toolBar = QToolBar(BlockEditorWindow)
        self.toolBar.setObjectName(u"toolBar")
        self.toolBar.setMovable(False)
        self.toolBar.setFloatable(False)
        BlockEditorWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar)

        self.toolBar.addAction(self.block_editor_actionCheckModel)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionCenter)
        self.toolBar.addAction(self.actionZoom_out)
        self.toolBar.addAction(self.actionZoom_in)

        self.retranslateUi(BlockEditorWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(BlockEditorWindow)
    # setupUi

    def retranslateUi(self, BlockEditorWindow):
        BlockEditorWindow.setWindowTitle(QCoreApplication.translate("BlockEditorWindow", u"BlockEditorWindow", None))
        self.block_editor_actionCheckModel.setText(QCoreApplication.translate("BlockEditorWindow", u"CheckModel", None))
        self.actionCenter.setText(QCoreApplication.translate("BlockEditorWindow", u"Center", None))
        self.actionZoom_in.setText(QCoreApplication.translate("BlockEditorWindow", u"Zoom in", None))
        self.actionZoom_out.setText(QCoreApplication.translate("BlockEditorWindow", u"Zoom out", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("BlockEditorWindow", u"Library", None))
#if QT_CONFIG(tooltip)
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("BlockEditorWindow", u"Drag and drop models into the scene", None))
#endif // QT_CONFIG(tooltip)
        self.variablesLabel.setStyleSheet(QCoreApplication.translate("BlockEditorWindow", u"font-weight: bold; padding: 4px;", None))
        self.variablesLabel.setText(QCoreApplication.translate("BlockEditorWindow", u"Variables", None))
        self.parametersLabel.setStyleSheet(QCoreApplication.translate("BlockEditorWindow", u"font-weight: bold; padding: 4px;", None))
        self.parametersLabel.setText(QCoreApplication.translate("BlockEditorWindow", u"Parameters", None))
        self.equationsLabel.setStyleSheet(QCoreApplication.translate("BlockEditorWindow", u"font-weight: bold; padding: 4px;", None))
        self.equationsLabel.setText(QCoreApplication.translate("BlockEditorWindow", u"Equations", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("BlockEditorWindow", u"Edit Selected", None))
#if QT_CONFIG(tooltip)
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("BlockEditorWindow", u"Select one block to edit its variables and equations", None))
#endif // QT_CONFIG(tooltip)
        self.currently_editing_object_label.setText(QCoreApplication.translate("BlockEditorWindow", u"Device:", None))
        self.deviceLabel.setText(QCoreApplication.translate("BlockEditorWindow", u"dev", None))
        self.doItButton.setText(QCoreApplication.translate("BlockEditorWindow", u"Do it!", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("BlockEditorWindow", u"toolBar", None))
    # retranslateUi

