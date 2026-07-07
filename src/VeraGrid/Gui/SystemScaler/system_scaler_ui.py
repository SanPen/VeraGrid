# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'system_scaler_ui.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout,
    QHeaderView, QPushButton, QSizePolicy, QSpacerItem,
    QSplitter, QTableView, QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(1149, 455)
        self.verticalLayout_4 = QVBoxLayout(Dialog)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.splitter_2 = QSplitter(Dialog)
        self.splitter_2.setObjectName(u"splitter_2")
        self.splitter_2.setOrientation(Qt.Orientation.Horizontal)
        self.splitter = QSplitter(self.splitter_2)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.frame_4 = QFrame(self.splitter)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.frame_4)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, -1, 0)
        self.checkpointsTableView = QTableView(self.frame_4)
        self.checkpointsTableView.setObjectName(u"checkpointsTableView")
        self.checkpointsTableView.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout.addWidget(self.checkpointsTableView)

        self.splitter.addWidget(self.frame_4)
        self.frame_5 = QFrame(self.splitter)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_5.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame_5)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, -1, 0)
        self.checkpointDataTableView = QTableView(self.frame_5)
        self.checkpointDataTableView.setObjectName(u"checkpointDataTableView")
        self.checkpointDataTableView.setFrameShape(QFrame.Shape.NoFrame)

        self.verticalLayout_3.addWidget(self.checkpointDataTableView)

        self.splitter.addWidget(self.frame_5)
        self.splitter_2.addWidget(self.splitter)
        self.plotFrame = QFrame(self.splitter_2)
        self.plotFrame.setObjectName(u"plotFrame")
        self.plotFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.plotFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.plotFrame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(9, 0, 0, 0)
        self.splitter_2.addWidget(self.plotFrame)

        self.verticalLayout_4.addWidget(self.splitter_2)

        self.frame_3 = QFrame(Dialog)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setMaximumSize(QSize(16777215, 36))
        self.frame_3.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.addButton = QPushButton(self.frame_3)
        self.addButton.setObjectName(u"addButton")
        icon = QIcon()
        icon.addFile(u":/Icons/icons/plus (gray).png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.addButton.setIcon(icon)

        self.horizontalLayout_2.addWidget(self.addButton)

        self.removeButton = QPushButton(self.frame_3)
        self.removeButton.setObjectName(u"removeButton")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/minus (gray).png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.removeButton.setIcon(icon1)

        self.horizontalLayout_2.addWidget(self.removeButton)

        self.horizontalSpacer_2 = QSpacerItem(250, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.plotButton = QPushButton(self.frame_3)
        self.plotButton.setObjectName(u"plotButton")
        icon2 = QIcon()
        icon2.addFile(u":/Icons/icons/plot.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.plotButton.setIcon(icon2)

        self.horizontalLayout_2.addWidget(self.plotButton)

        self.doit_button = QPushButton(self.frame_3)
        self.doit_button.setObjectName(u"doit_button")

        self.horizontalLayout_2.addWidget(self.doit_button)


        self.verticalLayout_4.addWidget(self.frame_3)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"System Scaler", None))
#if QT_CONFIG(tooltip)
        self.addButton.setToolTip(QCoreApplication.translate("Dialog", u"Add scaling checkpoint", None))
#endif // QT_CONFIG(tooltip)
        self.addButton.setText("")
#if QT_CONFIG(tooltip)
        self.removeButton.setToolTip(QCoreApplication.translate("Dialog", u"Remove scaling checkpoint", None))
#endif // QT_CONFIG(tooltip)
        self.removeButton.setText("")
#if QT_CONFIG(tooltip)
        self.plotButton.setToolTip(QCoreApplication.translate("Dialog", u"Plot the proposed scaling", None))
#endif // QT_CONFIG(tooltip)
        self.plotButton.setText("")
        self.doit_button.setText(QCoreApplication.translate("Dialog", u"Do it", None))
    # retranslateUi

