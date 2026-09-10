# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dynamic_events_page_ui.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QTableView, QToolBar,
    QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_DynamicEventsPage(object):
    def setupUi(self, DynamicEventsPage):
        if not DynamicEventsPage.objectName():
            DynamicEventsPage.setObjectName(u"DynamicEventsPage")
        DynamicEventsPage.resize(900, 560)
        self.actionSwitchSequence = QAction(DynamicEventsPage)
        self.actionSwitchSequence.setObjectName(u"actionSwitchSequence")
        self.actionAddEvent = QAction(DynamicEventsPage)
        self.actionAddEvent.setObjectName(u"actionAddEvent")
        icon = QIcon()
        icon.addFile(u":/Icons/icons/plus.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionAddEvent.setIcon(icon)
        self.actionRemove = QAction(DynamicEventsPage)
        self.actionRemove.setObjectName(u"actionRemove")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/minus.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionRemove.setIcon(icon1)
        self.actionNewGroup = QAction(DynamicEventsPage)
        self.actionNewGroup.setObjectName(u"actionNewGroup")
        self.actionNewGroup.setIcon(icon)
        self.mainLayout = QVBoxLayout(DynamicEventsPage)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.eventsToolBar = QToolBar(DynamicEventsPage)
        self.eventsToolBar.setObjectName(u"eventsToolBar")
        self.eventsToolBar.setMovable(False)
        self.eventsToolBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.eventsToolBar.setFloatable(False)

        self.mainLayout.addWidget(self.eventsToolBar)

        self.eventsTreeFrame = QFrame(DynamicEventsPage)
        self.eventsTreeFrame.setObjectName(u"eventsTreeFrame")
        self.eventsTreeFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.eventsTreeLayout = QGridLayout(self.eventsTreeFrame)
        self.eventsTreeLayout.setObjectName(u"eventsTreeLayout")
        self.eventsTreeLayout.setContentsMargins(0, 0, 0, 0)
        self.eventsTableView = QTableView(self.eventsTreeFrame)
        self.eventsTableView.setObjectName(u"eventsTableView")
        self.eventsTableView.setAlternatingRowColors(True)
        self.eventsTableView.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.eventsTableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.eventsTreeLayout.addWidget(self.eventsTableView, 0, 0, 1, 1)

        self.emptyModelMessage = QLabel(self.eventsTreeFrame)
        self.emptyModelMessage.setObjectName(u"emptyModelMessage")
        self.emptyModelMessage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.emptyModelMessage.setWordWrap(True)

        self.eventsTreeLayout.addWidget(self.emptyModelMessage, 0, 0, 1, 1)


        self.mainLayout.addWidget(self.eventsTreeFrame)

        self.saveLayout = QHBoxLayout()
        self.saveLayout.setObjectName(u"saveLayout")
        self.saveSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.saveLayout.addItem(self.saveSpacer)

        self.saveButton = QPushButton(DynamicEventsPage)
        self.saveButton.setObjectName(u"saveButton")
        icon2 = QIcon()
        icon2.addFile(u":/Icons/icons/accept.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.saveButton.setIcon(icon2)

        self.saveLayout.addWidget(self.saveButton)


        self.mainLayout.addLayout(self.saveLayout)


        self.eventsToolBar.addAction(self.actionSwitchSequence)
        self.eventsToolBar.addSeparator()
        self.eventsToolBar.addAction(self.actionAddEvent)
        self.eventsToolBar.addAction(self.actionNewGroup)
        self.eventsToolBar.addAction(self.actionRemove)

        self.retranslateUi(DynamicEventsPage)

        QMetaObject.connectSlotsByName(DynamicEventsPage)
    # setupUi

    def retranslateUi(self, DynamicEventsPage):
        DynamicEventsPage.setWindowTitle(QCoreApplication.translate("DynamicEventsPage", u"Dynamic Events", None))
        self.actionSwitchSequence.setText(QCoreApplication.translate("DynamicEventsPage", u"Switch Sequence Wizard", None))
#if QT_CONFIG(tooltip)
        self.actionSwitchSequence.setToolTip(QCoreApplication.translate("DynamicEventsPage", u"Create an EMT switch opening and reclosing event sequence", None))
#endif // QT_CONFIG(tooltip)
        self.actionAddEvent.setText(QCoreApplication.translate("DynamicEventsPage", u"Add Event", None))
#if QT_CONFIG(tooltip)
        self.actionAddEvent.setToolTip(QCoreApplication.translate("DynamicEventsPage", u"Add an event to the selected event group", None))
#endif // QT_CONFIG(tooltip)
        self.actionRemove.setText(QCoreApplication.translate("DynamicEventsPage", u"Remove Selected", None))
#if QT_CONFIG(tooltip)
        self.actionRemove.setToolTip(QCoreApplication.translate("DynamicEventsPage", u"Remove the selected event or event group", None))
#endif // QT_CONFIG(tooltip)
        self.actionNewGroup.setText(QCoreApplication.translate("DynamicEventsPage", u"Add Event Group", None))
#if QT_CONFIG(tooltip)
        self.actionNewGroup.setToolTip(QCoreApplication.translate("DynamicEventsPage", u"Create an event group for this simulation mode", None))
#endif // QT_CONFIG(tooltip)
        self.emptyModelMessage.setText(QCoreApplication.translate("DynamicEventsPage", u"This dynamic model is empty. New events cannot be added until the model is built.", None))
#if QT_CONFIG(tooltip)
        self.saveButton.setToolTip(QCoreApplication.translate("DynamicEventsPage", u"Save events", None))
#endif // QT_CONFIG(tooltip)
        self.saveButton.setText("")
    # retranslateUi
