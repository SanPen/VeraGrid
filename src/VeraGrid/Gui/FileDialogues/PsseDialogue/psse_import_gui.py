# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'psse_import_gui.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QFormLayout,
    QFrame, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *
from VeraGrid.Gui.Icons.icons_rc import *
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_PsseImportDialog(object):
    def setupUi(self, PsseImportDialog):
        if not PsseImportDialog.objectName():
            PsseImportDialog.setObjectName(u"PsseImportDialog")
        PsseImportDialog.resize(318, 202)
        self.verticalLayout_2 = QVBoxLayout(PsseImportDialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame_77 = QFrame(PsseImportDialog)
        self.frame_77.setObjectName(u"frame_77")
        self.frame_77.setMinimumSize(QSize(300, 0))
        self.frame_77.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_77.setFrameShadow(QFrame.Shadow.Raised)
        self.formLayout = QFormLayout(self.frame_77)
        self.formLayout.setObjectName(u"formLayout")
        self.use_short_names_checkBox = QCheckBox(self.frame_77)
        self.use_short_names_checkBox.setObjectName(u"use_short_names_checkBox")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.SpanningRole, self.use_short_names_checkBox)

        self.adjust_taps_to_discrete_positions_checkBox = QCheckBox(self.frame_77)
        self.adjust_taps_to_discrete_positions_checkBox.setObjectName(u"adjust_taps_to_discrete_positions_checkBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.SpanningRole, self.adjust_taps_to_discrete_positions_checkBox)

        self.importButton = QPushButton(self.frame_77)
        self.importButton.setObjectName(u"importButton")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.importButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout.setItem(3, QFormLayout.ItemRole.LabelRole, self.verticalSpacer)

        self.flatten_virtual_taps_checkBox = QCheckBox(self.frame_77)
        self.flatten_virtual_taps_checkBox.setObjectName(u"flatten_virtual_taps_checkBox")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.SpanningRole, self.flatten_virtual_taps_checkBox)


        self.verticalLayout_2.addWidget(self.frame_77)


        self.retranslateUi(PsseImportDialog)

        QMetaObject.connectSlotsByName(PsseImportDialog)
    # setupUi

    def retranslateUi(self, PsseImportDialog):
        PsseImportDialog.setWindowTitle(QCoreApplication.translate("PsseImportDialog", u"PSS/e Import", None))
#if QT_CONFIG(tooltip)
        self.use_short_names_checkBox.setToolTip(QCoreApplication.translate("PsseImportDialog", u"<html><head/><body><p>Use &quot;I_J_ckt&quot; insetad of </p><p>&quot;I_Iname_VI_J_Jname_VJ_ckt&quot;</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.use_short_names_checkBox.setText(QCoreApplication.translate("PsseImportDialog", u"Use short branch names", None))
#if QT_CONFIG(tooltip)
        self.adjust_taps_to_discrete_positions_checkBox.setToolTip(QCoreApplication.translate("PsseImportDialog", u"<html><head/><body><p>PSS/e taps might not come adjusted </p><p>to the specified tap positions, </p><p>Do you want to adjust them?</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.adjust_taps_to_discrete_positions_checkBox.setText(QCoreApplication.translate("PsseImportDialog", u"Adjust taps to integer positios", None))
        self.importButton.setText(QCoreApplication.translate("PsseImportDialog", u"Import", None))
#if QT_CONFIG(tooltip)
        self.flatten_virtual_taps_checkBox.setToolTip(QCoreApplication.translate("PsseImportDialog", u"<html><head/><body><p>PSS/e does not handle the difference of nominal </p><p>voltage between the bus and the transformer (the vitual tap) </p><p>If checked, this will make the transformer nominal voltages </p><p>equal to the buses nominal voltage to behave like PSS/e</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.flatten_virtual_taps_checkBox.setText(QCoreApplication.translate("PsseImportDialog", u"Flatten viatual taps", None))
    # retranslateUi

