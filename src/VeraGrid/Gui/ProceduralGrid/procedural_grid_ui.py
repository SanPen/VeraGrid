# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'procedural_grid_ui.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
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
    QSplitter, QVBoxLayout, QWidget)

from VeraGrid.Gui.Widgets.matplotlibwidget import MatplotlibWidget
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(900, 560)
        icon = QIcon()
        icon.addFile(u":/Icons/icons/automatic_layout.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        Dialog.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.splitter = QSplitter(Dialog)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.leftFrame = QFrame(self.splitter)
        self.leftFrame.setObjectName(u"leftFrame")
        self.leftFrame.setMaximumSize(QSize(400, 16777215))
        self.leftFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.leftFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.leftVerticalLayout = QVBoxLayout(self.leftFrame)
        self.leftVerticalLayout.setObjectName(u"leftVerticalLayout")
        self.leftVerticalLayout.setContentsMargins(-1, 0, -1, -1)
        self.parametersFrame = QFrame(self.leftFrame)
        self.parametersFrame.setObjectName(u"parametersFrame")
        self.parametersFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.parametersFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout = QGridLayout(self.parametersFrame)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label = QLabel(self.parametersFrame)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.methodComboBox = QComboBox(self.parametersFrame)
        self.methodComboBox.setObjectName(u"methodComboBox")

        self.gridLayout.addWidget(self.methodComboBox, 0, 1, 1, 1)

        self.label_3 = QLabel(self.parametersFrame)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 2)

        self.targetSubstationListView = QListView(self.parametersFrame)
        self.targetSubstationListView.setObjectName(u"targetSubstationListView")

        self.gridLayout.addWidget(self.targetSubstationListView, 2, 0, 1, 2)

        self.topClosestSpinBox = QSpinBox(self.parametersFrame)
        self.topClosestSpinBox.setObjectName(u"topClosestSpinBox")
        self.topClosestSpinBox.setMinimum(1)
        self.topClosestSpinBox.setMaximum(9999999)
        self.topClosestSpinBox.setValue(5)

        self.gridLayout.addWidget(self.topClosestSpinBox, 3, 0, 1, 1)

        self.computeCandidatesButton = QPushButton(self.parametersFrame)
        self.computeCandidatesButton.setObjectName(u"computeCandidatesButton")

        self.gridLayout.addWidget(self.computeCandidatesButton, 3, 1, 1, 1)

        self.label_2 = QLabel(self.parametersFrame)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 4, 0, 1, 2)

        self.candidateSubstationListView = QListView(self.parametersFrame)
        self.candidateSubstationListView.setObjectName(u"candidateSubstationListView")

        self.gridLayout.addWidget(self.candidateSubstationListView, 5, 0, 1, 2)


        self.leftVerticalLayout.addWidget(self.parametersFrame)

        self.splitter.addWidget(self.leftFrame)
        self.plotFrame = QFrame(self.splitter)
        self.plotFrame.setObjectName(u"plotFrame")
        self.plotFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.plotFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.plotVerticalLayout = QVBoxLayout(self.plotFrame)
        self.plotVerticalLayout.setObjectName(u"plotVerticalLayout")
        self.plotVerticalLayout.setContentsMargins(0, 0, 0, 0)
        self.summaryLabel = QLabel(self.plotFrame)
        self.summaryLabel.setObjectName(u"summaryLabel")
        self.summaryLabel.setWordWrap(True)

        self.plotVerticalLayout.addWidget(self.summaryLabel)

        self.plotWidget = MatplotlibWidget(self.plotFrame)
        self.plotWidget.setObjectName(u"plotWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.plotWidget.sizePolicy().hasHeightForWidth())
        self.plotWidget.setSizePolicy(sizePolicy)

        self.plotVerticalLayout.addWidget(self.plotWidget)

        self.splitter.addWidget(self.plotFrame)

        self.verticalLayout.addWidget(self.splitter)

        self.buttonsFrame = QFrame(Dialog)
        self.buttonsFrame.setObjectName(u"buttonsFrame")
        self.buttonsFrame.setMaximumSize(QSize(16777215, 36))
        self.buttonsFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.buttonsFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.buttonsHorizontalLayout = QHBoxLayout(self.buttonsFrame)
        self.buttonsHorizontalLayout.setObjectName(u"buttonsHorizontalLayout")
        self.buttonsHorizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.previewButton = QPushButton(self.buttonsFrame)
        self.previewButton.setObjectName(u"previewButton")
        self.previewButton.setMinimumSize(QSize(24, 24))
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/run_cascade_step.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.previewButton.setIcon(icon1)

        self.buttonsHorizontalLayout.addWidget(self.previewButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttonsHorizontalLayout.addItem(self.horizontalSpacer)

        self.acceptButton = QPushButton(self.buttonsFrame)
        self.acceptButton.setObjectName(u"acceptButton")
        self.acceptButton.setMinimumSize(QSize(24, 24))
        icon2 = QIcon()
        icon2.addFile(u":/Icons/icons/color_grid.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.acceptButton.setIcon(icon2)

        self.buttonsHorizontalLayout.addWidget(self.acceptButton)


        self.verticalLayout.addWidget(self.buttonsFrame)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Procedural grid expansion", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Procedural grid method", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Substation to connect", None))
        self.topClosestSpinBox.setSuffix(QCoreApplication.translate("Dialog", u" Substations", None))
#if QT_CONFIG(tooltip)
        self.computeCandidatesButton.setToolTip(QCoreApplication.translate("Dialog", u"Compute the N closest candiate substations", None))
#endif // QT_CONFIG(tooltip)
        self.computeCandidatesButton.setText(QCoreApplication.translate("Dialog", u"Get candiates", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Connection substation candidates", None))
#if QT_CONFIG(tooltip)
        self.candidateSubstationListView.setToolTip(QCoreApplication.translate("Dialog", u"List of subations that can be connected to the selected substations", None))
#endif // QT_CONFIG(tooltip)
        self.summaryLabel.setText("")
#if QT_CONFIG(tooltip)
        self.previewButton.setToolTip(QCoreApplication.translate("Dialog", u"Preview", None))
#endif // QT_CONFIG(tooltip)
        self.previewButton.setText(QCoreApplication.translate("Dialog", u"Preview", None))
#if QT_CONFIG(tooltip)
        self.acceptButton.setToolTip(QCoreApplication.translate("Dialog", u"Create Grid", None))
#endif // QT_CONFIG(tooltip)
        self.acceptButton.setText(QCoreApplication.translate("Dialog", u"Accept", None))
    # retranslateUi

