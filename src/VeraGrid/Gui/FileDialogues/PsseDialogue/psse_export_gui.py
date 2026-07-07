# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'psse_export_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QFormLayout, QFrame, QLabel, QPushButton,
    QSizePolicy, QSlider, QSpacerItem, QVBoxLayout,
    QWidget)
from VeraGrid.Gui.Icons.icons_rc import *
from VeraGrid.Gui.Icons.icons_rc import *
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_PsseExportDialog(object):
    def setupUi(self, PsseExportDialog):
        if not PsseExportDialog.objectName():
            PsseExportDialog.setObjectName(u"PsseExportDialog")
        PsseExportDialog.resize(431, 272)
        self.verticalLayout_2 = QVBoxLayout(PsseExportDialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame_77 = QFrame(PsseExportDialog)
        self.frame_77.setObjectName(u"frame_77")
        self.frame_77.setMinimumSize(QSize(300, 0))
        self.frame_77.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_77.setFrameShadow(QFrame.Shadow.Raised)
        self.formLayout = QFormLayout(self.frame_77)
        self.formLayout.setObjectName(u"formLayout")
        self.label_export_mode = QLabel(self.frame_77)
        self.label_export_mode.setObjectName(u"label_export_mode")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_export_mode)

        self.psse_export_mode_comboBox = QComboBox(self.frame_77)
        self.psse_export_mode_comboBox.setObjectName(u"psse_export_mode_comboBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.psse_export_mode_comboBox)

        self.label_file_format = QLabel(self.frame_77)
        self.label_file_format.setObjectName(u"label_file_format")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_file_format)

        self.psse_file_format_comboBox = QComboBox(self.frame_77)
        self.psse_file_format_comboBox.setObjectName(u"psse_file_format_comboBox")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.psse_file_format_comboBox)

        self.label_112 = QLabel(self.frame_77)
        self.label_112.setObjectName(u"label_112")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_112)

        self.raw_export_version_comboBox = QComboBox(self.frame_77)
        self.raw_export_version_comboBox.setObjectName(u"raw_export_version_comboBox")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.raw_export_version_comboBox)

        self.label_topology_mapping = QLabel(self.frame_77)
        self.label_topology_mapping.setObjectName(u"label_topology_mapping")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_topology_mapping)

        self.node_breaker_checkbox = QCheckBox(self.frame_77)
        self.node_breaker_checkbox.setObjectName(u"node_breaker_checkbox")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.node_breaker_checkbox)

        self.label_time_slot = QLabel(self.frame_77)
        self.label_time_slot.setObjectName(u"label_time_slot")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_time_slot)

        self.time_slot_slider = QSlider(self.frame_77)
        self.time_slot_slider.setObjectName(u"time_slot_slider")
        self.time_slot_slider.setMinimum(-1)
        self.time_slot_slider.setMaximum(-1)
        self.time_slot_slider.setOrientation(Qt.Orientation.Horizontal)

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.time_slot_slider)

        self.time_slot_label = QLabel(self.frame_77)
        self.time_slot_label.setObjectName(u"time_slot_label")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.time_slot_label)

        self.exportButton = QPushButton(self.frame_77)
        self.exportButton.setObjectName(u"exportButton")

        self.formLayout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.exportButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout.setItem(6, QFormLayout.ItemRole.FieldRole, self.verticalSpacer)


        self.verticalLayout_2.addWidget(self.frame_77)


        self.retranslateUi(PsseExportDialog)

        QMetaObject.connectSlotsByName(PsseExportDialog)
    # setupUi

    def retranslateUi(self, PsseExportDialog):
        PsseExportDialog.setWindowTitle(QCoreApplication.translate("PsseExportDialog", u"PSS/e Export", None))
        self.label_export_mode.setText(QCoreApplication.translate("PsseExportDialog", u"Export mode", None))
        self.label_file_format.setText(QCoreApplication.translate("PsseExportDialog", u"File format", None))
        self.label_112.setText(QCoreApplication.translate("PsseExportDialog", u"Export version", None))
        self.label_topology_mapping.setText(QCoreApplication.translate("PsseExportDialog", u"Topology mapping", None))
        self.node_breaker_checkbox.setText(QCoreApplication.translate("PsseExportDialog", u"Map substations to PSS/e nodes (34+ only)", None))
        self.label_time_slot.setText(QCoreApplication.translate("PsseExportDialog", u"Time slot", None))
        self.time_slot_label.setText(QCoreApplication.translate("PsseExportDialog", u"Snapshot", None))
        self.exportButton.setText(QCoreApplication.translate("PsseExportDialog", u"Export", None))
    # retranslateUi
