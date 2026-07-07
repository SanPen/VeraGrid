# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cgmes_import_gui.ui'
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
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_CgmesImportDialog(object):
    def setupUi(self, CgmesImportDialog):
        if not CgmesImportDialog.objectName():
            CgmesImportDialog.setObjectName(u"CgmesImportDialog")
        CgmesImportDialog.resize(420, 340)
        self.verticalLayout = QVBoxLayout(CgmesImportDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(CgmesImportDialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.formLayout = QFormLayout(self.frame)
        self.formLayout.setObjectName(u"formLayout")
        self.versionLabel = QLabel(self.frame)
        self.versionLabel.setObjectName(u"versionLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.versionLabel)

        self.cgmesVersionComboBox = QComboBox(self.frame)
        self.cgmesVersionComboBox.setObjectName(u"cgmesVersionComboBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.cgmesVersionComboBox)

        self.topologyLabel = QLabel(self.frame)
        self.topologyLabel.setObjectName(u"topologyLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.topologyLabel)

        self.cgmesTopologyComboBox = QComboBox(self.frame)
        self.cgmesTopologyComboBox.setObjectName(u"cgmesTopologyComboBox")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.cgmesTopologyComboBox)

        self.recoveryLabel = QLabel(self.frame)
        self.recoveryLabel.setObjectName(u"recoveryLabel")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.recoveryLabel)

        self.cgmesRecoveryComboBox = QComboBox(self.frame)
        self.cgmesRecoveryComboBox.setObjectName(u"cgmesRecoveryComboBox")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.cgmesRecoveryComboBox)

        self.cgmesMapAreasLikeRawCheckBox = QCheckBox(self.frame)
        self.cgmesMapAreasLikeRawCheckBox.setObjectName(u"cgmesMapAreasLikeRawCheckBox")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.SpanningRole, self.cgmesMapAreasLikeRawCheckBox)

        self.cgmesTryMapDcToHvdcCheckBox = QCheckBox(self.frame)
        self.cgmesTryMapDcToHvdcCheckBox.setObjectName(u"cgmesTryMapDcToHvdcCheckBox")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.SpanningRole, self.cgmesTryMapDcToHvdcCheckBox)

        self.cgmesCreateBusbarPerCnCheckBox = QCheckBox(self.frame)
        self.cgmesCreateBusbarPerCnCheckBox.setObjectName(u"cgmesCreateBusbarPerCnCheckBox")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.SpanningRole, self.cgmesCreateBusbarPerCnCheckBox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout.setItem(6, QFormLayout.ItemRole.SpanningRole, self.verticalSpacer)

        self.importButton = QPushButton(self.frame)
        self.importButton.setObjectName(u"importButton")

        self.formLayout.setWidget(7, QFormLayout.ItemRole.SpanningRole, self.importButton)


        self.verticalLayout.addWidget(self.frame)


        self.retranslateUi(CgmesImportDialog)

        QMetaObject.connectSlotsByName(CgmesImportDialog)
    # setupUi

    def retranslateUi(self, CgmesImportDialog):
        CgmesImportDialog.setWindowTitle(QCoreApplication.translate("CgmesImportDialog", u"CGMES Import", None))
        self.versionLabel.setText(QCoreApplication.translate("CgmesImportDialog", u"CGMES Version", None))
        self.topologyLabel.setText(QCoreApplication.translate("CgmesImportDialog", u"Topology Mode", None))
        self.recoveryLabel.setText(QCoreApplication.translate("CgmesImportDialog", u"Recovery Mode", None))
        self.cgmesMapAreasLikeRawCheckBox.setText(QCoreApplication.translate("CgmesImportDialog", u"Map areas like RAW (Region\u2192Area, SubRegion\u2192Zone)", None))
        self.cgmesTryMapDcToHvdcCheckBox.setText(QCoreApplication.translate("CgmesImportDialog", u"Try mapping DC network to HVDC line devices", None))
        self.cgmesCreateBusbarPerCnCheckBox.setText(QCoreApplication.translate("CgmesImportDialog", u"Create one busbar section per connectivity node", None))
        self.importButton.setText(QCoreApplication.translate("CgmesImportDialog", u"Import", None))
    # retranslateUi

