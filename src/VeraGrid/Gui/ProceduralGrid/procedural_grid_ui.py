# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'procedural_grid_ui.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
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
    QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(450, 451)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(1, 1, 1, 1)
        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 4, 0, 1, 1)

        self.targetSubstationListView = QListView(Dialog)
        self.targetSubstationListView.setObjectName(u"targetSubstationListView")

        self.gridLayout.addWidget(self.targetSubstationListView, 6, 0, 1, 3)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 9, 1, 1, 1)

        self.frame = QFrame(Dialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(1, 1, 1, 1)
        self.topClosestSpinBox = QSpinBox(self.frame)
        self.topClosestSpinBox.setObjectName(u"topClosestSpinBox")
        self.topClosestSpinBox.setMinimum(1)
        self.topClosestSpinBox.setMaximum(9999999)
        self.topClosestSpinBox.setValue(5)

        self.horizontalLayout.addWidget(self.topClosestSpinBox)

        self.computeCandidatesButton = QPushButton(self.frame)
        self.computeCandidatesButton.setObjectName(u"computeCandidatesButton")

        self.horizontalLayout.addWidget(self.computeCandidatesButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.computeButton = QPushButton(self.frame)
        self.computeButton.setObjectName(u"computeButton")

        self.horizontalLayout.addWidget(self.computeButton)


        self.gridLayout.addWidget(self.frame, 10, 0, 1, 3)

        self.methodComboBox = QComboBox(Dialog)
        self.methodComboBox.setObjectName(u"methodComboBox")

        self.gridLayout.addWidget(self.methodComboBox, 1, 1, 1, 2)

        self.label_5 = QLabel(Dialog)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 0, 0, 1, 1)

        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)

        self.candidateSubstationListView = QListView(Dialog)
        self.candidateSubstationListView.setObjectName(u"candidateSubstationListView")

        self.gridLayout.addWidget(self.candidateSubstationListView, 8, 0, 1, 3)

        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 7, 0, 1, 3)

        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 5, 0, 1, 3)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Procedural Grid", None))
        self.label_4.setText("")
        self.topClosestSpinBox.setSuffix(QCoreApplication.translate("Dialog", u" Substations", None))
#if QT_CONFIG(tooltip)
        self.computeCandidatesButton.setToolTip(QCoreApplication.translate("Dialog", u"Compute the N closest candiate substations", None))
#endif // QT_CONFIG(tooltip)
        self.computeCandidatesButton.setText(QCoreApplication.translate("Dialog", u"Get candiates", None))
        self.computeButton.setText(QCoreApplication.translate("Dialog", u"Compute", None))
        self.label_5.setText("")
        self.label.setText(QCoreApplication.translate("Dialog", u"Procedural grid method", None))
#if QT_CONFIG(tooltip)
        self.candidateSubstationListView.setToolTip(QCoreApplication.translate("Dialog", u"List of subations that can be connected to the selected substations", None))
#endif // QT_CONFIG(tooltip)
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Connection substation candidates", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Substation to connect", None))
    # retranslateUi

