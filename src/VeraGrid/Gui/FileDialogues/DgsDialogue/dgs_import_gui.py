# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dgs_import_gui.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QMetaObject
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

class Ui_DgsImportDialog(object):
    def setupUi(self, DgsImportDialog):
        if not DgsImportDialog.objectName():
            DgsImportDialog.setObjectName(u"DgsImportDialog")
        DgsImportDialog.resize(380, 230)
        self.verticalLayout = QVBoxLayout(DgsImportDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(DgsImportDialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.formLayout = QFormLayout(self.frame)
        self.formLayout.setObjectName(u"formLayout")
        self.dgsUseVscForInjectionsCheckBox = QCheckBox(self.frame)
        self.dgsUseVscForInjectionsCheckBox.setObjectName(u"dgsUseVscForInjectionsCheckBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.SpanningRole, self.dgsUseVscForInjectionsCheckBox)

        self.dgsUseDynamicInformationCheckBox = QCheckBox(self.frame)
        self.dgsUseDynamicInformationCheckBox.setObjectName(u"dgsUseDynamicInformationCheckBox")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.SpanningRole, self.dgsUseDynamicInformationCheckBox)

        self.dgsDynamicSimulationModeLabel = QLabel(self.frame)
        self.dgsDynamicSimulationModeLabel.setObjectName(u"dgsDynamicSimulationModeLabel")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.dgsDynamicSimulationModeLabel)

        self.dgsDynamicSimulationModeComboBox = QComboBox(self.frame)
        self.dgsDynamicSimulationModeComboBox.setObjectName(u"dgsDynamicSimulationModeComboBox")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.dgsDynamicSimulationModeComboBox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout.setItem(3, QFormLayout.ItemRole.SpanningRole, self.verticalSpacer)

        self.importButton = QPushButton(self.frame)
        self.importButton.setObjectName(u"importButton")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.importButton)


        self.verticalLayout.addWidget(self.frame)


        self.retranslateUi(DgsImportDialog)

        QMetaObject.connectSlotsByName(DgsImportDialog)
    # setupUi

    def retranslateUi(self, DgsImportDialog):
        DgsImportDialog.setWindowTitle(QCoreApplication.translate("DgsImportDialog", u"DGS Import", None))
        self.dgsUseVscForInjectionsCheckBox.setText(QCoreApplication.translate("DgsImportDialog", u"Use VSC model for controllable injections", None))
        self.dgsUseDynamicInformationCheckBox.setText(QCoreApplication.translate("DgsImportDialog", u"Use dynamic information (when available)", None))
        self.dgsDynamicSimulationModeLabel.setText(
            QCoreApplication.translate(
                "DgsImportDialog",
                u"Dynamic simulation mode",
                None,
            )
        )
        self.importButton.setText(QCoreApplication.translate("DgsImportDialog", u"Import", None))
    # retranslateUi

