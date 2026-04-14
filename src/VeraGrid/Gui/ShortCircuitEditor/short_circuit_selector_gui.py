# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'short_circuit_selector_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QDoubleSpinBox,
    QFrame, QGridLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *
from VeraGrid.Gui.Icons.icons_rc import *
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_ShortCircuitSelectorDialog(object):
    def setupUi(self, ShortCircuitSelectorDialog):
        if not ShortCircuitSelectorDialog.objectName():
            ShortCircuitSelectorDialog.setObjectName(u"ShortCircuitSelectorDialog")
        ShortCircuitSelectorDialog.resize(417, 365)
        self.verticalLayout_2 = QVBoxLayout(ShortCircuitSelectorDialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame_77 = QFrame(ShortCircuitSelectorDialog)
        self.frame_77.setObjectName(u"frame_77")
        self.frame_77.setMinimumSize(QSize(300, 0))
        self.frame_77.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_77.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout = QGridLayout(self.frame_77)
        self.gridLayout.setObjectName(u"gridLayout")
        self.btn_accept = QPushButton(self.frame_77)
        self.btn_accept.setObjectName(u"btn_accept")

        self.gridLayout.addWidget(self.btn_accept, 11, 2, 1, 1)

        self.x_doubleSpinBox = QDoubleSpinBox(self.frame_77)
        self.x_doubleSpinBox.setObjectName(u"x_doubleSpinBox")
        self.x_doubleSpinBox.setDecimals(4)
        self.x_doubleSpinBox.setMaximum(10000000000000000.000000000000000)

        self.gridLayout.addWidget(self.x_doubleSpinBox, 7, 1, 1, 2)

        self.cb_type = QComboBox(self.frame_77)
        self.cb_type.setObjectName(u"cb_type")

        self.gridLayout.addWidget(self.cb_type, 5, 1, 1, 2)

        self.typeLabel = QLabel(self.frame_77)
        self.typeLabel.setObjectName(u"typeLabel")
        self.typeLabel.setTextFormat(Qt.TextFormat.PlainText)
        self.typeLabel.setWordWrap(True)

        self.gridLayout.addWidget(self.typeLabel, 8, 1, 1, 2)

        self.phases_label = QLabel(self.frame_77)
        self.phases_label.setObjectName(u"phases_label")

        self.gridLayout.addWidget(self.phases_label, 4, 1, 1, 2)

        self.cb_method = QComboBox(self.frame_77)
        self.cb_method.setObjectName(u"cb_method")

        self.gridLayout.addWidget(self.cb_method, 0, 1, 1, 2)

        self.r_doubleSpinBox = QDoubleSpinBox(self.frame_77)
        self.r_doubleSpinBox.setObjectName(u"r_doubleSpinBox")
        self.r_doubleSpinBox.setDecimals(4)
        self.r_doubleSpinBox.setMaximum(9999999999.000000000000000)

        self.gridLayout.addWidget(self.r_doubleSpinBox, 6, 1, 1, 2)

        self.label_4 = QLabel(self.frame_77)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 5, 0, 1, 1)

        self.label_2 = QLabel(self.frame_77)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 85, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 10, 2, 1, 1)

        self.cb_fault = QComboBox(self.frame_77)
        self.cb_fault.setObjectName(u"cb_fault")

        self.gridLayout.addWidget(self.cb_fault, 1, 1, 1, 2)

        self.cb_phases = QComboBox(self.frame_77)
        self.cb_phases.setObjectName(u"cb_phases")

        self.gridLayout.addWidget(self.cb_phases, 3, 1, 1, 2)

        self.label = QLabel(self.frame_77)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)

        self.label_3 = QLabel(self.frame_77)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)

        self.label_5 = QLabel(self.frame_77)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 6, 0, 1, 1)

        self.label_6 = QLabel(self.frame_77)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 7, 0, 1, 1)


        self.verticalLayout_2.addWidget(self.frame_77)


        self.retranslateUi(ShortCircuitSelectorDialog)

        QMetaObject.connectSlotsByName(ShortCircuitSelectorDialog)
    # setupUi

    def retranslateUi(self, ShortCircuitSelectorDialog):
        ShortCircuitSelectorDialog.setWindowTitle(QCoreApplication.translate("ShortCircuitSelectorDialog", u"Short circuit definition", None))
        self.btn_accept.setText(QCoreApplication.translate("ShortCircuitSelectorDialog", u"Accept", None))
#if QT_CONFIG(tooltip)
        self.x_doubleSpinBox.setToolTip(QCoreApplication.translate("ShortCircuitSelectorDialog", u"Fault reactance (often dismissed)", None))
#endif // QT_CONFIG(tooltip)
        self.x_doubleSpinBox.setSuffix(QCoreApplication.translate("ShortCircuitSelectorDialog", u" Ohm", None))
        self.typeLabel.setText(QCoreApplication.translate("ShortCircuitSelectorDialog", u"...", None))
        self.phases_label.setText(QCoreApplication.translate("ShortCircuitSelectorDialog", u"...", None))
#if QT_CONFIG(tooltip)
        self.r_doubleSpinBox.setToolTip(QCoreApplication.translate("ShortCircuitSelectorDialog", u"Fault resistance", None))
#endif // QT_CONFIG(tooltip)
        self.r_doubleSpinBox.setSuffix(QCoreApplication.translate("ShortCircuitSelectorDialog", u" Ohm", None))
        self.label_4.setText(QCoreApplication.translate("ShortCircuitSelectorDialog", u"Fault type", None))
        self.label_2.setText(QCoreApplication.translate("ShortCircuitSelectorDialog", u"Method", None))
        self.label.setText(QCoreApplication.translate("ShortCircuitSelectorDialog", u"Fault method", None))
        self.label_3.setText(QCoreApplication.translate("ShortCircuitSelectorDialog", u"Phases", None))
        self.label_5.setText(QCoreApplication.translate("ShortCircuitSelectorDialog", u"R", None))
        self.label_6.setText(QCoreApplication.translate("ShortCircuitSelectorDialog", u"X", None))
    # retranslateUi

