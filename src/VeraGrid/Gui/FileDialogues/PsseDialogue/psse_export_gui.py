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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFormLayout,
    QFrame, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *
from VeraGrid.Gui.Icons.icons_rc import *
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_PsseExportDialog(object):
    def setupUi(self, PsseExportDialog):
        if not PsseExportDialog.objectName():
            PsseExportDialog.setObjectName(u"PsseExportDialog")
        PsseExportDialog.resize(318, 153)
        self.verticalLayout_2 = QVBoxLayout(PsseExportDialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame_77 = QFrame(PsseExportDialog)
        self.frame_77.setObjectName(u"frame_77")
        self.frame_77.setMinimumSize(QSize(300, 0))
        self.frame_77.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_77.setFrameShadow(QFrame.Shadow.Raised)
        self.formLayout = QFormLayout(self.frame_77)
        self.formLayout.setObjectName(u"formLayout")
        self.label_112 = QLabel(self.frame_77)
        self.label_112.setObjectName(u"label_112")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_112)

        self.raw_export_version_comboBox = QComboBox(self.frame_77)
        self.raw_export_version_comboBox.setObjectName(u"raw_export_version_comboBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.raw_export_version_comboBox)

        self.exportButton = QPushButton(self.frame_77)
        self.exportButton.setObjectName(u"exportButton")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.exportButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout.setItem(1, QFormLayout.ItemRole.FieldRole, self.verticalSpacer)


        self.verticalLayout_2.addWidget(self.frame_77)


        self.retranslateUi(PsseExportDialog)

        QMetaObject.connectSlotsByName(PsseExportDialog)
    # setupUi

    def retranslateUi(self, PsseExportDialog):
        PsseExportDialog.setWindowTitle(QCoreApplication.translate("PsseExportDialog", u"PSS/e Export", None))
        self.label_112.setText(QCoreApplication.translate("PsseExportDialog", u"Export version", None))
        self.exportButton.setText(QCoreApplication.translate("PsseExportDialog", u"Export", None))
    # retranslateUi

