# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'procedural_grid_ui.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QListView,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(434, 485)
        self.verticalLayout_2 = QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame_2 = QFrame(Dialog)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout = QGridLayout(self.frame_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 7, 1, 1, 1)

        self.computeCandidatesButton = QPushButton(self.frame_2)
        self.computeCandidatesButton.setObjectName(u"computeCandidatesButton")

        self.gridLayout.addWidget(self.computeCandidatesButton, 6, 1, 1, 1)

        self.targetSubstationListView = QListView(self.frame_2)
        self.targetSubstationListView.setObjectName(u"targetSubstationListView")

        self.gridLayout.addWidget(self.targetSubstationListView, 3, 0, 1, 2)

        self.label = QLabel(self.frame_2)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.topClosestSpinBox = QSpinBox(self.frame_2)
        self.topClosestSpinBox.setObjectName(u"topClosestSpinBox")
        self.topClosestSpinBox.setMinimum(1)
        self.topClosestSpinBox.setMaximum(9999999)
        self.topClosestSpinBox.setValue(5)

        self.gridLayout.addWidget(self.topClosestSpinBox, 6, 0, 1, 1)

        self.candidateSubstationListView = QListView(self.frame_2)
        self.candidateSubstationListView.setObjectName(u"candidateSubstationListView")

        self.gridLayout.addWidget(self.candidateSubstationListView, 5, 0, 1, 2)

        self.methodComboBox = QComboBox(self.frame_2)
        self.methodComboBox.setObjectName(u"methodComboBox")

        self.gridLayout.addWidget(self.methodComboBox, 0, 1, 1, 1)

        self.label_3 = QLabel(self.frame_2)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)

        self.label_2 = QLabel(self.frame_2)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 4, 0, 1, 1)


        self.verticalLayout_2.addWidget(self.frame_2)

        self.frame = QFrame(Dialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(1, 1, 1, 1)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.computeButton = QPushButton(self.frame)
        self.computeButton.setObjectName(u"computeButton")
        icon = QIcon()
        icon.addFile(u":/Icons/icons/schematic.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.computeButton.setIcon(icon)

        self.horizontalLayout.addWidget(self.computeButton)


        self.verticalLayout_2.addWidget(self.frame)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Procedural Grid", None))
#if QT_CONFIG(tooltip)
        self.computeCandidatesButton.setToolTip(QCoreApplication.translate("Dialog", u"Compute the N closest candiate substations", None))
#endif // QT_CONFIG(tooltip)
        self.computeCandidatesButton.setText(QCoreApplication.translate("Dialog", u"Get candiates", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Procedural grid method", None))
        self.topClosestSpinBox.setSuffix(QCoreApplication.translate("Dialog", u" Substations", None))
#if QT_CONFIG(tooltip)
        self.candidateSubstationListView.setToolTip(QCoreApplication.translate("Dialog", u"List of subations that can be connected to the selected substations", None))
#endif // QT_CONFIG(tooltip)
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Substation to connect", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Connection substation candidates", None))
        self.computeButton.setText(QCoreApplication.translate("Dialog", u"Compute", None))
    # retranslateUi

