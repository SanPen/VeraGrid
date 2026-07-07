# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'matpower_export_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFormLayout,
    QFrame, QLabel, QPushButton, QSizePolicy,
    QSlider, QSpacerItem, QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *
from VeraGrid.Gui.Icons.icons_rc import *
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_MatpowerExportDialog(object):
    def setupUi(self, MatpowerExportDialog):
        if not MatpowerExportDialog.objectName():
            MatpowerExportDialog.setObjectName(u"MatpowerExportDialog")
        MatpowerExportDialog.resize(396, 230)
        self.verticalLayout_2 = QVBoxLayout(MatpowerExportDialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame_77 = QFrame(MatpowerExportDialog)
        self.frame_77.setObjectName(u"frame_77")
        self.frame_77.setMinimumSize(QSize(300, 0))
        self.frame_77.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_77.setFrameShadow(QFrame.Shadow.Raised)
        self.formLayout = QFormLayout(self.frame_77)
        self.formLayout.setObjectName(u"formLayout")
        self.label_export_mode = QLabel(self.frame_77)
        self.label_export_mode.setObjectName(u"label_export_mode")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_export_mode)

        self.matpower_export_mode_comboBox = QComboBox(self.frame_77)
        self.matpower_export_mode_comboBox.setObjectName(u"matpower_export_mode_comboBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.matpower_export_mode_comboBox)

        self.label_time_slot = QLabel(self.frame_77)
        self.label_time_slot.setObjectName(u"label_time_slot")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_time_slot)

        self.time_slot_slider = QSlider(self.frame_77)
        self.time_slot_slider.setObjectName(u"time_slot_slider")
        self.time_slot_slider.setMinimum(-1)
        self.time_slot_slider.setMaximum(-1)
        self.time_slot_slider.setOrientation(Qt.Orientation.Horizontal)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.time_slot_slider)

        self.time_slot_label = QLabel(self.frame_77)
        self.time_slot_label.setObjectName(u"time_slot_label")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.time_slot_label)

        self.exportButton = QPushButton(self.frame_77)
        self.exportButton.setObjectName(u"exportButton")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.exportButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout.setItem(3, QFormLayout.ItemRole.FieldRole, self.verticalSpacer)


        self.verticalLayout_2.addWidget(self.frame_77)


        self.retranslateUi(MatpowerExportDialog)

        QMetaObject.connectSlotsByName(MatpowerExportDialog)
    # setupUi

    def retranslateUi(self, MatpowerExportDialog):
        MatpowerExportDialog.setWindowTitle(QCoreApplication.translate("MatpowerExportDialog", u"MATPOWER Export", None))
        self.label_export_mode.setText(QCoreApplication.translate("MatpowerExportDialog", u"Export mode", None))
        self.label_time_slot.setText(QCoreApplication.translate("MatpowerExportDialog", u"Time slot", None))
        self.time_slot_label.setText(QCoreApplication.translate("MatpowerExportDialog", u"Snapshot", None))
        self.exportButton.setText(QCoreApplication.translate("MatpowerExportDialog", u"Export", None))
    # retranslateUi

