# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dynamic_editor_workspace.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QHeaderView,
    QLineEdit, QMainWindow, QSizePolicy, QSplitter,
    QToolBar, QTreeView, QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_DynamicEditorWorkspaceWindow(object):
    def setupUi(self, DynamicEditorWorkspaceWindow):
        if not DynamicEditorWorkspaceWindow.objectName():
            DynamicEditorWorkspaceWindow.setObjectName(u"DynamicEditorWorkspaceWindow")
        DynamicEditorWorkspaceWindow.resize(1094, 603)
        self.block_editor_actionCheckModel = QAction(DynamicEditorWorkspaceWindow)
        self.block_editor_actionCheckModel.setObjectName(u"block_editor_actionCheckModel")
        icon = QIcon()
        icon.addFile(u":/Icons/icons/magnifying_glass2.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.block_editor_actionCheckModel.setIcon(icon)
        self.block_editor_actionCheckModel.setMenuRole(QAction.MenuRole.NoRole)
        self.actionCenter = QAction(DynamicEditorWorkspaceWindow)
        self.actionCenter.setObjectName(u"actionCenter")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/resize.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionCenter.setIcon(icon1)
        self.actionCenter.setMenuRole(QAction.MenuRole.NoRole)
        self.actionZoom_in = QAction(DynamicEditorWorkspaceWindow)
        self.actionZoom_in.setObjectName(u"actionZoom_in")
        icon2 = QIcon()
        icon2.addFile(u":/Icons/icons/zoom_in.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionZoom_in.setIcon(icon2)
        self.actionZoom_in.setMenuRole(QAction.MenuRole.NoRole)
        self.actionZoom_out = QAction(DynamicEditorWorkspaceWindow)
        self.actionZoom_out.setObjectName(u"actionZoom_out")
        icon3 = QIcon()
        icon3.addFile(u":/Icons/icons/zoom_out.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionZoom_out.setIcon(icon3)
        self.actionZoom_out.setMenuRole(QAction.MenuRole.NoRole)
        self.action_delete_all = QAction(DynamicEditorWorkspaceWindow)
        self.action_delete_all.setObjectName(u"action_delete_all")
        self.action_delete_all.setEnabled(True)
        icon4 = QIcon()
        icon4.addFile(u":/Icons/icons/new.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.action_delete_all.setIcon(icon4)
        self.action_delete_all.setMenuRole(QAction.MenuRole.NoRole)
        self.actionValidate = QAction(DynamicEditorWorkspaceWindow)
        self.actionValidate.setObjectName(u"actionValidate")
        icon5 = QIcon()
        icon5.addFile(u":/Icons/icons/check_all.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionValidate.setIcon(icon5)
        self.actionValidate.setMenuRole(QAction.MenuRole.NoRole)
        self.actionview_tree = QAction(DynamicEditorWorkspaceWindow)
        self.actionview_tree.setObjectName(u"actionview_tree")
        icon6 = QIcon()
        icon6.addFile(u":/Icons/icons/tree.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionview_tree.setIcon(icon6)
        self.actionview_tree.setMenuRole(QAction.MenuRole.NoRole)
        self.centralwidget = QWidget(DynamicEditorWorkspaceWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.treeFrame = QFrame(self.splitter)
        self.treeFrame.setObjectName(u"treeFrame")
        self.treeFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.treeFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.treeFrame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 4, 6, 0)
        self.frame_2 = QFrame(self.treeFrame)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(6, 0, 0, 0)
        self.searchInTreeLineEdit = QLineEdit(self.frame_2)
        self.searchInTreeLineEdit.setObjectName(u"searchInTreeLineEdit")

        self.horizontalLayout_2.addWidget(self.searchInTreeLineEdit)


        self.verticalLayout_2.addWidget(self.frame_2)

        self.treeView = QTreeView(self.treeFrame)
        self.treeView.setObjectName(u"treeView")
        self.treeView.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout_2.addWidget(self.treeView)

        self.splitter.addWidget(self.treeFrame)
        self.editorFrame = QFrame(self.splitter)
        self.editorFrame.setObjectName(u"editorFrame")
        self.editorFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.editorFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.editorFrame)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(6, 0, 0, 0)
        self.editorFrameLayout = QVBoxLayout()
        self.editorFrameLayout.setObjectName(u"editorFrameLayout")

        self.verticalLayout_3.addLayout(self.editorFrameLayout)

        self.splitter.addWidget(self.editorFrame)

        self.verticalLayout.addWidget(self.splitter)

        DynamicEditorWorkspaceWindow.setCentralWidget(self.centralwidget)
        self.toolBar = QToolBar(DynamicEditorWorkspaceWindow)
        self.toolBar.setObjectName(u"toolBar")
        self.toolBar.setMovable(False)
        self.toolBar.setFloatable(False)
        DynamicEditorWorkspaceWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar)

        self.toolBar.addAction(self.actionview_tree)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.action_delete_all)
        self.toolBar.addAction(self.block_editor_actionCheckModel)
        self.toolBar.addAction(self.actionValidate)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionZoom_out)
        self.toolBar.addAction(self.actionZoom_in)
        self.toolBar.addAction(self.actionCenter)
        self.toolBar.addSeparator()

        self.retranslateUi(DynamicEditorWorkspaceWindow)

        QMetaObject.connectSlotsByName(DynamicEditorWorkspaceWindow)
    # setupUi

    def retranslateUi(self, DynamicEditorWorkspaceWindow):
        DynamicEditorWorkspaceWindow.setWindowTitle(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"Dynamic Editor Workspace", None))
        self.block_editor_actionCheckModel.setText(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"CheckModel", None))
#if QT_CONFIG(tooltip)
        self.block_editor_actionCheckModel.setToolTip(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"Inspect model", None))
#endif // QT_CONFIG(tooltip)
        self.actionCenter.setText(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"Center", None))
        self.actionZoom_in.setText(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"Zoom in", None))
        self.actionZoom_out.setText(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"Zoom out", None))
        self.action_delete_all.setText(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"Delete all", None))
#if QT_CONFIG(tooltip)
        self.action_delete_all.setToolTip(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"Delete all blocks to start from scratch.", None))
#endif // QT_CONFIG(tooltip)
        self.actionValidate.setText(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"Validate", None))
        self.actionview_tree.setText(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"view tree", None))
        self.searchInTreeLineEdit.setPlaceholderText(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"Type to search the device", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"toolBar", None))
    # retranslateUi

