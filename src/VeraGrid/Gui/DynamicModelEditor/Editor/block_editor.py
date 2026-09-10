# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'block_editor.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
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
    QHeaderView, QLineEdit, QMainWindow, QSizePolicy,
    QSplitter, QToolBar, QToolBox, QTreeView,
    QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_BlockEditorWindow(object):
    def setupUi(self, BlockEditorWindow):
        if not BlockEditorWindow.objectName():
            BlockEditorWindow.setObjectName(u"BlockEditorWindow")
        BlockEditorWindow.resize(864, 446)
        self.block_editor_actionCheckModel = QAction(BlockEditorWindow)
        self.block_editor_actionCheckModel.setObjectName(u"block_editor_actionCheckModel")
        icon = QIcon()
        icon.addFile(u":/Icons/icons/magnifying_glass2.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
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
        self.action_delete_all = QAction(BlockEditorWindow)
        self.action_delete_all.setObjectName(u"action_delete_all")
        self.action_delete_all.setEnabled(True)
        icon4 = QIcon()
        icon4.addFile(u":/Icons/icons/new.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.action_delete_all.setIcon(icon4)
        self.action_delete_all.setMenuRole(QAction.MenuRole.NoRole)
        self.actionValidate = QAction(BlockEditorWindow)
        self.actionValidate.setObjectName(u"actionValidate")
        icon5 = QIcon()
        icon5.addFile(u":/Icons/icons/check_all.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionValidate.setIcon(icon5)
        self.actionValidate.setMenuRole(QAction.MenuRole.NoRole)
        self.actionSave = QAction(BlockEditorWindow)
        self.actionSave.setObjectName(u"actionSave")
        icon6 = QIcon()
        icon6.addFile(u":/Icons/icons/savec.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionSave.setIcon(icon6)
        self.actionSave.setMenuRole(QAction.MenuRole.NoRole)
        self.centralwidget = QWidget(BlockEditorWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame_3 = QFrame(self.centralwidget)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame_3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(self.frame_3)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.frame_7 = QFrame(self.splitter)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_7.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame_7)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 6, 0)
        self.graphicsView = QGraphicsView(self.frame_7)
        self.graphicsView.setObjectName(u"graphicsView")

        self.verticalLayout_3.addWidget(self.graphicsView)

        self.splitter.addWidget(self.frame_7)
        self.frame = QFrame(self.splitter)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.frame)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(6, 0, 0, 0)
        self.toolBox = QToolBox(self.frame)
        self.toolBox.setObjectName(u"toolBox")
        self.page_7 = QWidget()
        self.page_7.setObjectName(u"page_7")
        self.page_7.setGeometry(QRect(0, 0, 424, 369))
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
        self.librarySearchLineEdit = QLineEdit(self.libraryHeaderFrame)
        self.librarySearchLineEdit.setObjectName(u"librarySearchLineEdit")

        self.horizontalLayout_5.addWidget(self.librarySearchLineEdit)


        self.verticalLayout_13.addWidget(self.libraryHeaderFrame)

        self.libraryTreeView = QTreeView(self.page_7)
        self.libraryTreeView.setObjectName(u"libraryTreeView")
        self.libraryTreeView.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout_13.addWidget(self.libraryTreeView)

        self.toolBox.addItem(self.page_7, u"Library")

        self.verticalLayout_6.addWidget(self.toolBox)

        self.frame_4 = QFrame(self.frame)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_4)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_6.addWidget(self.frame_4)

        self.splitter.addWidget(self.frame)

        self.verticalLayout_2.addWidget(self.splitter)


        self.verticalLayout.addWidget(self.frame_3)

        BlockEditorWindow.setCentralWidget(self.centralwidget)
        self.toolBar = QToolBar(BlockEditorWindow)
        self.toolBar.setObjectName(u"toolBar")
        self.toolBar.setMovable(False)
        self.toolBar.setFloatable(False)
        BlockEditorWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar)

        self.toolBar.addAction(self.action_delete_all)
        self.toolBar.addAction(self.actionSave)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionCenter)
        self.toolBar.addAction(self.actionZoom_out)
        self.toolBar.addAction(self.actionZoom_in)
        self.toolBar.addAction(self.actionValidate)
        self.toolBar.addAction(self.block_editor_actionCheckModel)

        self.retranslateUi(BlockEditorWindow)

        self.toolBox.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(BlockEditorWindow)
    # setupUi

    def retranslateUi(self, BlockEditorWindow):
        BlockEditorWindow.setWindowTitle(QCoreApplication.translate("BlockEditorWindow", u"BlockEditorWindow", None))
        self.block_editor_actionCheckModel.setText(QCoreApplication.translate("BlockEditorWindow", u"CheckModel", None))
#if QT_CONFIG(tooltip)
        self.block_editor_actionCheckModel.setToolTip(QCoreApplication.translate("BlockEditorWindow", u"Inspect model", None))
#endif // QT_CONFIG(tooltip)
        self.actionCenter.setText(QCoreApplication.translate("BlockEditorWindow", u"Center", None))
        self.actionZoom_in.setText(QCoreApplication.translate("BlockEditorWindow", u"Zoom in", None))
        self.actionZoom_out.setText(QCoreApplication.translate("BlockEditorWindow", u"Zoom out", None))
        self.action_delete_all.setText(QCoreApplication.translate("BlockEditorWindow", u"Delete all", None))
#if QT_CONFIG(tooltip)
        self.action_delete_all.setToolTip(QCoreApplication.translate("BlockEditorWindow", u"Delete all blocks to start from scratch.", None))
#endif // QT_CONFIG(tooltip)
        self.actionValidate.setText(QCoreApplication.translate("BlockEditorWindow", u"Validate", None))
        self.actionSave.setText(QCoreApplication.translate("BlockEditorWindow", u"Save", None))
#if QT_CONFIG(shortcut)
        self.actionSave.setShortcut(QCoreApplication.translate("BlockEditorWindow", u"Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
        self.librarySearchLineEdit.setPlaceholderText(QCoreApplication.translate("BlockEditorWindow", u"Search basic blocks", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_7), QCoreApplication.translate("BlockEditorWindow", u"Library", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("BlockEditorWindow", u"toolBar", None))
    # retranslateUi

