# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'block_editor.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGraphicsView, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow,
    QPushButton, QSizePolicy, QSpacerItem, QSplitter,
    QTableView, QToolBox, QTreeView, QVBoxLayout,
    QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_BlockEditorWindow(object):
    def setupUi(self, BlockEditorWindow):
        if not BlockEditorWindow.objectName():
            BlockEditorWindow.setObjectName(u"BlockEditorWindow")
        BlockEditorWindow.resize(864, 446)
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
        self.verticalLayout_3.setContentsMargins(0, 10, 6, 0)
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
        self.page_7.setGeometry(QRect(0, 0, 424, 288))
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
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.page.setGeometry(QRect(0, 0, 424, 288))
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
        self.page_2.setGeometry(QRect(0, 0, 424, 288))
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
        self.page_3.setGeometry(QRect(0, 0, 424, 288))
        self.verticalLayout_9 = QVBoxLayout(self.page_3)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.equationsTableView = QTableView(self.page_3)
        self.equationsTableView.setObjectName(u"equationsTableView")
        self.equationsTableView.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout_9.addWidget(self.equationsTableView)

        self.toolBox.addItem(self.page_3, u"Equations")

        self.verticalLayout_6.addWidget(self.toolBox)

        self.frame_4 = QFrame(self.frame)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_4)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.deviceLabel = QLabel(self.frame_4)
        self.deviceLabel.setObjectName(u"deviceLabel")

        self.horizontalLayout.addWidget(self.deviceLabel)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.doItButton = QPushButton(self.frame_4)
        self.doItButton.setObjectName(u"doItButton")
        icon = QIcon()
        icon.addFile(u":/Icons/icons/accept.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.doItButton.setIcon(icon)

        self.horizontalLayout.addWidget(self.doItButton)


        self.verticalLayout_6.addWidget(self.frame_4)

        self.splitter.addWidget(self.frame)

        self.verticalLayout_2.addWidget(self.splitter)


        self.verticalLayout.addWidget(self.frame_3)

        BlockEditorWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(BlockEditorWindow)

        self.toolBox.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(BlockEditorWindow)
    # setupUi

    def retranslateUi(self, BlockEditorWindow):
        BlockEditorWindow.setWindowTitle(QCoreApplication.translate("BlockEditorWindow", u"BlockEditorWindow", None))
        self.librarySearchLineEdit.setPlaceholderText(QCoreApplication.translate("BlockEditorWindow", u"Search basic blocks", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_7), QCoreApplication.translate("BlockEditorWindow", u"Library", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page), QCoreApplication.translate("BlockEditorWindow", u"Variables", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_2), QCoreApplication.translate("BlockEditorWindow", u"Parameters", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_3), QCoreApplication.translate("BlockEditorWindow", u"Equations", None))
        self.deviceLabel.setText("")
        self.doItButton.setText("")
    # retranslateUi

