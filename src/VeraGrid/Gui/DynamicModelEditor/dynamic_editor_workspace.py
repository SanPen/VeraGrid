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
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QMainWindow, QSizePolicy, QTabWidget,
    QVBoxLayout, QWidget)

class Ui_DynamicEditorWorkspaceWindow(object):
    def setupUi(self, DynamicEditorWorkspaceWindow):
        if not DynamicEditorWorkspaceWindow.objectName():
            DynamicEditorWorkspaceWindow.setObjectName(u"DynamicEditorWorkspaceWindow")
        DynamicEditorWorkspaceWindow.resize(1180, 760)
        self.centralwidget = QWidget(DynamicEditorWorkspaceWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.editorTabs = QTabWidget(self.centralwidget)
        self.editorTabs.setObjectName(u"editorTabs")
        self.editorTabs.setTabsClosable(True)
        self.editorTabs.setMovable(True)
        self.editorTabs.setDocumentMode(True)

        self.verticalLayout.addWidget(self.editorTabs)

        DynamicEditorWorkspaceWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(DynamicEditorWorkspaceWindow)

        QMetaObject.connectSlotsByName(DynamicEditorWorkspaceWindow)
    # setupUi

    def retranslateUi(self, DynamicEditorWorkspaceWindow):
        DynamicEditorWorkspaceWindow.setWindowTitle(QCoreApplication.translate("DynamicEditorWorkspaceWindow", u"Dynamic Editor Workspace", None))
    # retranslateUi

