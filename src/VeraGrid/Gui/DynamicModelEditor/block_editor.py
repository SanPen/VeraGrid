# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'block_editor.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
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
    QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMenuBar, QPushButton, QSizePolicy, QSpacerItem,
    QSplitter, QTableView, QToolBar, QToolBox,
    QToolButton, QTreeView, QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_BlockEditorWindow(object):
    def setupUi(self, BlockEditorWindow):
        if not BlockEditorWindow.objectName():
            BlockEditorWindow.setObjectName(u"BlockEditorWindow")
        BlockEditorWindow.resize(957, 572)
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
        self.verticalLayout.setContentsMargins(6, 0, 6, 6)
        self.frame_3 = QFrame(self.centralwidget)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame_3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(self.frame_3)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.frame = QFrame(self.splitter)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.frame)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 6, 0)
        self.toolBox = QToolBox(self.frame)
        self.toolBox.setObjectName(u"toolBox")
        self.page_7 = QWidget()
        self.page_7.setObjectName(u"page_7")
        self.page_7.setGeometry(QRect(0, 0, 459, 318))
        self.verticalLayout_13 = QVBoxLayout(self.page_7)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.libraryHeaderFrame = QFrame(self.page_7)
        self.libraryHeaderFrame.setObjectName(u"libraryHeaderFrame")
        self.libraryHeaderFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.libraryHeaderFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.libraryHeaderFrame)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.librarySearchButton = QToolButton(self.libraryHeaderFrame)
        self.librarySearchButton.setObjectName(u"librarySearchButton")

        self.horizontalLayout_5.addWidget(self.librarySearchButton)

        self.librarySearchLineEdit = QLineEdit(self.libraryHeaderFrame)
        self.librarySearchLineEdit.setObjectName(u"librarySearchLineEdit")

        self.horizontalLayout_5.addWidget(self.librarySearchLineEdit)


        self.verticalLayout_13.addWidget(self.libraryHeaderFrame)

        self.libraryTreeView = QTreeView(self.page_7)
        self.libraryTreeView.setObjectName(u"libraryTreeView")
        self.libraryTreeView.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout_13.addWidget(self.libraryTreeView)

        self.toolBox.addItem(self.page_7, u"Library")
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.page.setGeometry(QRect(0, 0, 98, 68))
        self.verticalLayout_7 = QVBoxLayout(self.page)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.variablesTableView = QTableView(self.page)
        self.variablesTableView.setObjectName(u"variablesTableView")
        self.variablesTableView.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout_7.addWidget(self.variablesTableView)

        self.toolBox.addItem(self.page, u"Variables")
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.page_2.setGeometry(QRect(0, 0, 98, 68))
        self.verticalLayout_8 = QVBoxLayout(self.page_2)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.parametersTableView = QTableView(self.page_2)
        self.parametersTableView.setObjectName(u"parametersTableView")
        self.parametersTableView.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout_8.addWidget(self.parametersTableView)

        self.toolBox.addItem(self.page_2, u"Parameters")
        self.page_3 = QWidget()
        self.page_3.setObjectName(u"page_3")
        self.page_3.setGeometry(QRect(0, 0, 98, 68))
        self.verticalLayout_9 = QVBoxLayout(self.page_3)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.equationsTableView = QTableView(self.page_3)
        self.equationsTableView.setObjectName(u"equationsTableView")
        self.equationsTableView.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout_9.addWidget(self.equationsTableView)

        self.toolBox.addItem(self.page_3, u"Equations")

        self.verticalLayout_6.addWidget(self.toolBox)

        self.splitter.addWidget(self.frame)
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

        self.verticalLayout_2.addWidget(self.splitter)


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

        self.validateConsistencyButton = QPushButton(self.frame_2)
        self.validateConsistencyButton.setObjectName(u"validateConsistencyButton")

        self.horizontalLayout_2.addWidget(self.validateConsistencyButton)

        self.doItButton = QPushButton(self.frame_2)
        self.doItButton.setObjectName(u"doItButton")

        self.horizontalLayout_2.addWidget(self.doItButton)


        self.verticalLayout.addWidget(self.frame_2)

        BlockEditorWindow.setCentralWidget(self.centralwidget)
        self.menuBar = QMenuBar(BlockEditorWindow)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 957, 23))
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

        self.toolBox.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(BlockEditorWindow)
    # setupUi

    def retranslateUi(self, BlockEditorWindow):
        BlockEditorWindow.setWindowTitle(QCoreApplication.translate("BlockEditorWindow", u"BlockEditorWindow", None))
        self.block_editor_actionCheckModel.setText(QCoreApplication.translate("BlockEditorWindow", u"CheckModel", None))
        self.actionCenter.setText(QCoreApplication.translate("BlockEditorWindow", u"Center", None))
        self.actionZoom_in.setText(QCoreApplication.translate("BlockEditorWindow", u"Zoom in", None))
        self.actionZoom_out.setText(QCoreApplication.translate("BlockEditorWindow", u"Zoom out", None))
        self.librarySearchButton.setText(QCoreApplication.translate("BlockEditorWindow", u"...", None))
        self.librarySearchLineEdit.setPlaceholderText(QCoreApplication.translate("BlockEditorWindow", u"Search basic blocks", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_7), QCoreApplication.translate("BlockEditorWindow", u"Library", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page), QCoreApplication.translate("BlockEditorWindow", u"Variables", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_2), QCoreApplication.translate("BlockEditorWindow", u"Parameters", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_3), QCoreApplication.translate("BlockEditorWindow", u"Equations", None))
        self.currently_editing_object_label.setText(QCoreApplication.translate("BlockEditorWindow", u"Device:", None))
        self.deviceLabel.setText(QCoreApplication.translate("BlockEditorWindow", u"dev", None))
#if QT_CONFIG(tooltip)
        self.validateConsistencyButton.setToolTip(QCoreApplication.translate("BlockEditorWindow", u"<html><head/><body><p><span style=\" font-weight:700;\">Model consistency validation</span></p><p>Run an informational validation of the edited model structure, mappings, initialization, and port connectivity. This check reports issues but does not block saving the model.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.validateConsistencyButton.setText(QCoreApplication.translate("BlockEditorWindow", u"Validate model consistency", None))
        self.doItButton.setText(QCoreApplication.translate("BlockEditorWindow", u"Do it!", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("BlockEditorWindow", u"toolBar", None))
    # retranslateUi

