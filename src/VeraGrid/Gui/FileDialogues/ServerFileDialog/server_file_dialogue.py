# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'server_file_dialogue.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QAction, QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog,
    QFormLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QSizePolicy, QSplitter,
    QToolBar, QTreeView, QVBoxLayout, QWidget)

from VeraGrid.Gui.Icons.icons_rc import *

class Ui_ServerFileDialog(object):
    def setupUi(self, ServerFileDialog):
        if not ServerFileDialog.objectName():
            ServerFileDialog.setObjectName(u"ServerFileDialog")
        ServerFileDialog.resize(1040, 720)
        icon = QIcon()
        icon.addFile(u":/Icons/icons/server.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        ServerFileDialog.setWindowIcon(icon)
        self.actionRefresh = QAction(ServerFileDialog)
        self.actionRefresh.setObjectName(u"actionRefresh")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/sync.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionRefresh.setIcon(icon1)
        self.actionLoadFile = QAction(ServerFileDialog)
        self.actionLoadFile.setObjectName(u"actionLoadFile")
        icon2 = QIcon()
        icon2.addFile(u":/Icons/icons/server.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionLoadFile.setIcon(icon2)
        self.actionLoadBase = QAction(ServerFileDialog)
        self.actionLoadBase.setObjectName(u"actionLoadBase")
        icon3 = QIcon()
        icon3.addFile(u":/Icons/icons/grid_icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionLoadBase.setIcon(icon3)
        self.actionLoadModel = QAction(ServerFileDialog)
        self.actionLoadModel.setObjectName(u"actionLoadModel")
        icon4 = QIcon()
        icon4.addFile(u":/Icons/icons/schematic.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionLoadModel.setIcon(icon4)
        self.actionSaveCurrent = QAction(ServerFileDialog)
        self.actionSaveCurrent.setObjectName(u"actionSaveCurrent")
        icon5 = QIcon()
        icon5.addFile(u":/Icons/icons/save.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionSaveCurrent.setIcon(icon5)
        self.actionDeleteSelected = QAction(ServerFileDialog)
        self.actionDeleteSelected.setObjectName(u"actionDeleteSelected")
        icon6 = QIcon()
        icon6.addFile(u":/Icons/icons/delete_db.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionDeleteSelected.setIcon(icon6)
        self.verticalLayout = QVBoxLayout(ServerFileDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.toolBar = QToolBar(ServerFileDialog)
        self.toolBar.setObjectName(u"toolBar")
        self.toolBar.setIconSize(QSize(24, 24))
        self.toolBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toolBar.addAction(self.actionRefresh)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionLoadFile)
        self.toolBar.addAction(self.actionLoadBase)
        self.toolBar.addAction(self.actionLoadModel)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionSaveCurrent)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionDeleteSelected)

        self.verticalLayout.addWidget(self.toolBar)

        self.mainSplitter = QSplitter(ServerFileDialog)
        self.mainSplitter.setObjectName(u"mainSplitter")
        self.mainSplitter.setOrientation(Qt.Horizontal)
        self.filesTreeView = QTreeView(self.mainSplitter)
        self.filesTreeView.setObjectName(u"filesTreeView")
        self.filesTreeView.setAlternatingRowColors(True)
        self.filesTreeView.setUniformRowHeights(True)
        self.filesTreeView.setItemsExpandable(True)
        self.filesTreeView.setRootIsDecorated(True)
        self.filesTreeView.setMinimumWidth(640)
        self.mainSplitter.addWidget(self.filesTreeView)
        self.detailWidget = QWidget(self.mainSplitter)
        self.detailWidget.setObjectName(u"detailWidget")
        self.detailLayout = QVBoxLayout(self.detailWidget)
        self.detailLayout.setObjectName(u"detailLayout")
        self.detailLayout.setContentsMargins(0, 0, 0, 0)
        self.detailWidget.setMinimumWidth(280)
        self.selectionGroupBox = QGroupBox(self.detailWidget)
        self.selectionGroupBox.setObjectName(u"selectionGroupBox")
        self.formLayout = QFormLayout(self.selectionGroupBox)
        self.formLayout.setObjectName(u"formLayout")
        self.kindTitleLabel = QLabel(self.selectionGroupBox)
        self.kindTitleLabel.setObjectName(u"kindTitleLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.kindTitleLabel)

        self.kindValueLabel = QLabel(self.selectionGroupBox)
        self.kindValueLabel.setObjectName(u"kindValueLabel")
        self.kindValueLabel.setWordWrap(True)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.kindValueLabel)

        self.fileNameTitleLabel = QLabel(self.selectionGroupBox)
        self.fileNameTitleLabel.setObjectName(u"fileNameTitleLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.fileNameTitleLabel)

        self.fileNameValueLabel = QLabel(self.selectionGroupBox)
        self.fileNameValueLabel.setObjectName(u"fileNameValueLabel")
        self.fileNameValueLabel.setWordWrap(True)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.fileNameValueLabel)

        self.fileIdTitleLabel = QLabel(self.selectionGroupBox)
        self.fileIdTitleLabel.setObjectName(u"fileIdTitleLabel")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.fileIdTitleLabel)

        self.fileIdValueLabel = QLabel(self.selectionGroupBox)
        self.fileIdValueLabel.setObjectName(u"fileIdValueLabel")
        self.fileIdValueLabel.setWordWrap(True)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.fileIdValueLabel)

        self.modelNameTitleLabel = QLabel(self.selectionGroupBox)
        self.modelNameTitleLabel.setObjectName(u"modelNameTitleLabel")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.modelNameTitleLabel)

        self.modelNameValueLabel = QLabel(self.selectionGroupBox)
        self.modelNameValueLabel.setObjectName(u"modelNameValueLabel")
        self.modelNameValueLabel.setWordWrap(True)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.modelNameValueLabel)

        self.modelIdTitleLabel = QLabel(self.selectionGroupBox)
        self.modelIdTitleLabel.setObjectName(u"modelIdTitleLabel")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.modelIdTitleLabel)

        self.modelIdValueLabel = QLabel(self.selectionGroupBox)
        self.modelIdValueLabel.setObjectName(u"modelIdValueLabel")
        self.modelIdValueLabel.setWordWrap(True)

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.modelIdValueLabel)

        self.ownerTitleLabel = QLabel(self.selectionGroupBox)
        self.ownerTitleLabel.setObjectName(u"ownerTitleLabel")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.ownerTitleLabel)

        self.ownerValueLabel = QLabel(self.selectionGroupBox)
        self.ownerValueLabel.setObjectName(u"ownerValueLabel")
        self.ownerValueLabel.setWordWrap(True)

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.ownerValueLabel)

        self.createdTitleLabel = QLabel(self.selectionGroupBox)
        self.createdTitleLabel.setObjectName(u"createdTitleLabel")

        self.formLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.createdTitleLabel)

        self.createdValueLabel = QLabel(self.selectionGroupBox)
        self.createdValueLabel.setObjectName(u"createdValueLabel")
        self.createdValueLabel.setWordWrap(True)

        self.formLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.createdValueLabel)


        self.detailLayout.addWidget(self.selectionGroupBox)

        self.helpGroupBox = QGroupBox(self.detailWidget)
        self.helpGroupBox.setObjectName(u"helpGroupBox")
        self.verticalLayout_2 = QVBoxLayout(self.helpGroupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.helpLabel = QLabel(self.helpGroupBox)
        self.helpLabel.setObjectName(u"helpLabel")
        self.helpLabel.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.helpLabel)


        self.detailLayout.addWidget(self.helpGroupBox)

        self.mainSplitter.addWidget(self.detailWidget)

        self.verticalLayout.addWidget(self.mainSplitter)
        self.mainSplitter.setStretchFactor(0, 5)
        self.mainSplitter.setStretchFactor(1, 2)


        self.retranslateUi(ServerFileDialog)

        QMetaObject.connectSlotsByName(ServerFileDialog)
    # setupUi

    def retranslateUi(self, ServerFileDialog):
        ServerFileDialog.setWindowTitle(QCoreApplication.translate("ServerFileDialog", u"Server Files", None))
        self.actionRefresh.setText(QCoreApplication.translate("ServerFileDialog", u"Refresh", None))
        self.actionRefresh.setToolTip(QCoreApplication.translate("ServerFileDialog", u"Reload the server file tree", None))
        self.actionLoadFile.setText(QCoreApplication.translate("ServerFileDialog", u"Load File", None))
        self.actionLoadFile.setToolTip(QCoreApplication.translate("ServerFileDialog", u"Load the full selected multiverse", None))
        self.actionLoadBase.setText(QCoreApplication.translate("ServerFileDialog", u"Load Base Model", None))
        self.actionLoadBase.setToolTip(QCoreApplication.translate("ServerFileDialog", u"Load only the selected file base model", None))
        self.actionLoadModel.setText(QCoreApplication.translate("ServerFileDialog", u"Load Selected Model", None))
        self.actionLoadModel.setToolTip(QCoreApplication.translate("ServerFileDialog", u"Load the selected scenario branch as one flat circuit", None))
        self.actionSaveCurrent.setText(QCoreApplication.translate("ServerFileDialog", u"Save Current Project", None))
        self.actionSaveCurrent.setToolTip(QCoreApplication.translate("ServerFileDialog", u"Upload the current project into the selected server file or model", None))
        self.actionDeleteSelected.setText(QCoreApplication.translate("ServerFileDialog", u"Delete Selected", None))
        self.actionDeleteSelected.setToolTip(QCoreApplication.translate("ServerFileDialog", u"Delete the selected file or model from the server database", None))
        self.selectionGroupBox.setTitle(QCoreApplication.translate("ServerFileDialog", u"Selection", None))
        self.kindTitleLabel.setText(QCoreApplication.translate("ServerFileDialog", u"Type", None))
        self.kindValueLabel.setText(QCoreApplication.translate("ServerFileDialog", u"-", None))
        self.fileNameTitleLabel.setText(QCoreApplication.translate("ServerFileDialog", u"File name", None))
        self.fileNameValueLabel.setText(QCoreApplication.translate("ServerFileDialog", u"-", None))
        self.fileIdTitleLabel.setText(QCoreApplication.translate("ServerFileDialog", u"File idtag", None))
        self.fileIdValueLabel.setText(QCoreApplication.translate("ServerFileDialog", u"-", None))
        self.modelNameTitleLabel.setText(QCoreApplication.translate("ServerFileDialog", u"Model name", None))
        self.modelNameValueLabel.setText(QCoreApplication.translate("ServerFileDialog", u"-", None))
        self.modelIdTitleLabel.setText(QCoreApplication.translate("ServerFileDialog", u"Model idtag", None))
        self.modelIdValueLabel.setText(QCoreApplication.translate("ServerFileDialog", u"-", None))
        self.ownerTitleLabel.setText(QCoreApplication.translate("ServerFileDialog", u"Owner user", None))
        self.ownerValueLabel.setText(QCoreApplication.translate("ServerFileDialog", u"-", None))
        self.createdTitleLabel.setText(QCoreApplication.translate("ServerFileDialog", u"Created at", None))
        self.createdValueLabel.setText(QCoreApplication.translate("ServerFileDialog", u"-", None))
        self.helpGroupBox.setTitle(QCoreApplication.translate("ServerFileDialog", u"Actions", None))
        self.helpLabel.setText(QCoreApplication.translate("ServerFileDialog", u"Delete removes the selected file or the selected model branch from the server database after confirmation.", None))
    # retranslateUi
