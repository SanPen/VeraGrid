# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dynamic_editor_workspace.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QHeaderView,
    QLineEdit, QMainWindow, QSizePolicy, QSplitter,
    QToolBar, QTreeView, QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_DynamicEditorWorkspaceWindow(object):
    def setupUi(self, DynamicEditorWorkspaceWindow):
        if not DynamicEditorWorkspaceWindow.objectName():
            DynamicEditorWorkspaceWindow.setObjectName(u"DynamicEditorWorkspaceWindow")
        DynamicEditorWorkspaceWindow.resize(1094, 603)
        self.actionview_tree = QAction(DynamicEditorWorkspaceWindow)
        self.actionview_tree.setObjectName(u"actionview_tree")
        icon = QIcon()
        icon.addFile(u":/Icons/icons/tree.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionview_tree.setIcon(icon)
        self.actionview_tree.setMenuRole(QAction.MenuRole.NoRole)
        self.actionRMS_Editor = QAction(DynamicEditorWorkspaceWindow)
        self.actionRMS_Editor.setObjectName(u"actionRMS_Editor")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/dyn.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionRMS_Editor.setIcon(icon1)
        self.actionRMS_Editor.setMenuRole(QAction.MenuRole.NoRole)
        self.actionEMT_Editor = QAction(DynamicEditorWorkspaceWindow)
        self.actionEMT_Editor.setObjectName(u"actionEMT_Editor")
        icon2 = QIcon()
        icon2.addFile(u":/Icons/icons/dyn_emt.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionEMT_Editor.setIcon(icon2)
        self.actionEMT_Editor.setMenuRole(QAction.MenuRole.NoRole)
        self.actionRMS_Events = QAction(DynamicEditorWorkspaceWindow)
        self.actionRMS_Events.setObjectName(u"actionRMS_Events")
        icon3 = QIcon()
        icon3.addFile(u":/Icons/icons/dyn_edit.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionRMS_Events.setIcon(icon3)
        self.actionRMS_Events.setMenuRole(QAction.MenuRole.NoRole)
        self.actionEMT_Events = QAction(DynamicEditorWorkspaceWindow)
        self.actionEMT_Events.setObjectName(u"actionEMT_Events")
        icon4 = QIcon()
        icon4.addFile(u":/Icons/icons/dyn_emt_edit.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionEMT_Events.setIcon(icon4)
        self.actionEMT_Events.setMenuRole(QAction.MenuRole.NoRole)
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
        self.toolBar.setAllowedAreas(Qt.ToolBarArea.LeftToolBarArea)
        self.toolBar.setFloatable(False)
        DynamicEditorWorkspaceWindow.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolBar)

        self.toolBar.addAction(self.actionview_tree)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionRMS_Editor)
        self.toolBar.addAction(self.actionRMS_Events)
        self.toolBar.addAction(self.actionEMT_Editor)
        self.toolBar.addAction(self.actionEMT_Events)

        self.retranslateUi(DynamicEditorWorkspaceWindow)

        QMetaObject.connectSlotsByName(DynamicEditorWorkspaceWindow)
    # setupUi

    def retranslateUi(self, DynamicEditorWorkspaceWindow):
        DynamicEditorWorkspaceWindow.setWindowTitle(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"Dynamic Editor Workspace", None))
        self.actionview_tree.setText(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"view tree", None))
        self.actionRMS_Editor.setText(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"RMS Editor", None))
        self.actionEMT_Editor.setText(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"EMT Editor", None))
        self.actionRMS_Events.setText(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"RMS Events", None))
        self.actionEMT_Events.setText(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"EMT Events", None))
        self.searchInTreeLineEdit.setPlaceholderText(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"Type to search the device", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"toolBar", None))
    # retranslateUi

