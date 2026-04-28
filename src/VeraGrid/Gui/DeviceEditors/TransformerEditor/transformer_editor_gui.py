# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'transformer_editor_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QDoubleSpinBox,
    QFrame, QLabel, QPushButton, QSizePolicy,
    QSpinBox, QVBoxLayout, QWidget)

class Ui_TransformerEditorDialog(object):
    def setupUi(self, TransformerEditorDialog):
        if not TransformerEditorDialog.objectName():
            TransformerEditorDialog.setObjectName(u"TransformerEditorDialog")
        TransformerEditorDialog.resize(430, 430)
        self.verticalLayout = QVBoxLayout(TransformerEditorDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.templatesLabel = QLabel(TransformerEditorDialog)
        self.templatesLabel.setObjectName(u"templatesLabel")

        self.verticalLayout.addWidget(self.templatesLabel)

        self.catalogueComboBox = QComboBox(TransformerEditorDialog)
        self.catalogueComboBox.setObjectName(u"catalogueComboBox")

        self.verticalLayout.addWidget(self.catalogueComboBox)

        self.loadTemplateButton = QPushButton(TransformerEditorDialog)
        self.loadTemplateButton.setObjectName(u"loadTemplateButton")

        self.verticalLayout.addWidget(self.loadTemplateButton)

        self.separator = QFrame(TransformerEditorDialog)
        self.separator.setObjectName(u"separator")
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.separator)

        self.snLabel = QLabel(TransformerEditorDialog)
        self.snLabel.setObjectName(u"snLabel")

        self.verticalLayout.addWidget(self.snLabel)

        self.snSpinBox = QDoubleSpinBox(TransformerEditorDialog)
        self.snSpinBox.setObjectName(u"snSpinBox")
        self.snSpinBox.setDecimals(6)
        self.snSpinBox.setMaximum(999999.000000000000000)

        self.verticalLayout.addWidget(self.snSpinBox)

        self.pcuLabel = QLabel(TransformerEditorDialog)
        self.pcuLabel.setObjectName(u"pcuLabel")

        self.verticalLayout.addWidget(self.pcuLabel)

        self.pcuSpinBox = QDoubleSpinBox(TransformerEditorDialog)
        self.pcuSpinBox.setObjectName(u"pcuSpinBox")
        self.pcuSpinBox.setDecimals(6)
        self.pcuSpinBox.setMaximum(999999.000000000000000)

        self.verticalLayout.addWidget(self.pcuSpinBox)

        self.pfeLabel = QLabel(TransformerEditorDialog)
        self.pfeLabel.setObjectName(u"pfeLabel")

        self.verticalLayout.addWidget(self.pfeLabel)

        self.pfeSpinBox = QDoubleSpinBox(TransformerEditorDialog)
        self.pfeSpinBox.setObjectName(u"pfeSpinBox")
        self.pfeSpinBox.setDecimals(6)
        self.pfeSpinBox.setMaximum(999999.000000000000000)

        self.verticalLayout.addWidget(self.pfeSpinBox)

        self.i0Label = QLabel(TransformerEditorDialog)
        self.i0Label.setObjectName(u"i0Label")

        self.verticalLayout.addWidget(self.i0Label)

        self.i0SpinBox = QDoubleSpinBox(TransformerEditorDialog)
        self.i0SpinBox.setObjectName(u"i0SpinBox")
        self.i0SpinBox.setDecimals(6)
        self.i0SpinBox.setMaximum(999999.000000000000000)

        self.verticalLayout.addWidget(self.i0SpinBox)

        self.vscLabel = QLabel(TransformerEditorDialog)
        self.vscLabel.setObjectName(u"vscLabel")

        self.verticalLayout.addWidget(self.vscLabel)

        self.vscSpinBox = QDoubleSpinBox(TransformerEditorDialog)
        self.vscSpinBox.setObjectName(u"vscSpinBox")
        self.vscSpinBox.setDecimals(6)
        self.vscSpinBox.setMaximum(999999.000000000000000)

        self.verticalLayout.addWidget(self.vscSpinBox)

        self.tapSeparator = QFrame(TransformerEditorDialog)
        self.tapSeparator.setObjectName(u"tapSeparator")
        self.tapSeparator.setFrameShape(QFrame.Shape.HLine)
        self.tapSeparator.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.tapSeparator)

        self.tapChangerTypeLabel = QLabel(TransformerEditorDialog)
        self.tapChangerTypeLabel.setObjectName(u"tapChangerTypeLabel")

        self.verticalLayout.addWidget(self.tapChangerTypeLabel)

        self.tapChangerTypeComboBox = QComboBox(TransformerEditorDialog)
        self.tapChangerTypeComboBox.setObjectName(u"tapChangerTypeComboBox")

        self.verticalLayout.addWidget(self.tapChangerTypeComboBox)

        self.asymmetryAngleLabel = QLabel(TransformerEditorDialog)
        self.asymmetryAngleLabel.setObjectName(u"asymmetryAngleLabel")

        self.verticalLayout.addWidget(self.asymmetryAngleLabel)

        self.asymmetryAngleSpinBox = QDoubleSpinBox(TransformerEditorDialog)
        self.asymmetryAngleSpinBox.setObjectName(u"asymmetryAngleSpinBox")
        self.asymmetryAngleSpinBox.setDecimals(6)
        self.asymmetryAngleSpinBox.setMaximum(999999.000000000000000)

        self.verticalLayout.addWidget(self.asymmetryAngleSpinBox)

        self.totalPositionsLabel = QLabel(TransformerEditorDialog)
        self.totalPositionsLabel.setObjectName(u"totalPositionsLabel")

        self.verticalLayout.addWidget(self.totalPositionsLabel)

        self.totalPositionsSpinBox = QSpinBox(TransformerEditorDialog)
        self.totalPositionsSpinBox.setObjectName(u"totalPositionsSpinBox")
        self.totalPositionsSpinBox.setMaximum(999999)

        self.verticalLayout.addWidget(self.totalPositionsSpinBox)

        self.neutralPositionLabel = QLabel(TransformerEditorDialog)
        self.neutralPositionLabel.setObjectName(u"neutralPositionLabel")

        self.verticalLayout.addWidget(self.neutralPositionLabel)

        self.neutralPositionSpinBox = QSpinBox(TransformerEditorDialog)
        self.neutralPositionSpinBox.setObjectName(u"neutralPositionSpinBox")
        self.neutralPositionSpinBox.setMaximum(999999)

        self.verticalLayout.addWidget(self.neutralPositionSpinBox)

        self.tapPositionLabel = QLabel(TransformerEditorDialog)
        self.tapPositionLabel.setObjectName(u"tapPositionLabel")

        self.verticalLayout.addWidget(self.tapPositionLabel)

        self.tapPositionSpinBox = QSpinBox(TransformerEditorDialog)
        self.tapPositionSpinBox.setObjectName(u"tapPositionSpinBox")
        self.tapPositionSpinBox.setMaximum(999999)

        self.verticalLayout.addWidget(self.tapPositionSpinBox)

        self.dvLabel = QLabel(TransformerEditorDialog)
        self.dvLabel.setObjectName(u"dvLabel")

        self.verticalLayout.addWidget(self.dvLabel)

        self.dvSpinBox = QDoubleSpinBox(TransformerEditorDialog)
        self.dvSpinBox.setObjectName(u"dvSpinBox")
        self.dvSpinBox.setDecimals(6)
        self.dvSpinBox.setMaximum(999999.000000000000000)

        self.verticalLayout.addWidget(self.dvSpinBox)

        self.acceptButton = QPushButton(TransformerEditorDialog)
        self.acceptButton.setObjectName(u"acceptButton")

        self.verticalLayout.addWidget(self.acceptButton)


        self.retranslateUi(TransformerEditorDialog)

        QMetaObject.connectSlotsByName(TransformerEditorDialog)
    # setupUi

    def retranslateUi(self, TransformerEditorDialog):
        TransformerEditorDialog.setWindowTitle(QCoreApplication.translate("TransformerEditorDialog", u"Transformer editor", None))
        self.templatesLabel.setText(QCoreApplication.translate("TransformerEditorDialog", u"Suitable templates", None))
        self.loadTemplateButton.setText(QCoreApplication.translate("TransformerEditorDialog", u"Load template values", None))
        self.snLabel.setText(QCoreApplication.translate("TransformerEditorDialog", u"Sn: Nominal power [MVA]", None))
        self.pcuLabel.setText(QCoreApplication.translate("TransformerEditorDialog", u"Pcu: Copper losses [kW]", None))
        self.pfeLabel.setText(QCoreApplication.translate("TransformerEditorDialog", u"Pfe: Iron losses [kW]", None))
        self.i0Label.setText(QCoreApplication.translate("TransformerEditorDialog", u"I0: No load current [%]", None))
        self.vscLabel.setText(QCoreApplication.translate("TransformerEditorDialog", u"Vsc: Short circuit voltage [%]", None))
        self.tapChangerTypeLabel.setText(QCoreApplication.translate("TransformerEditorDialog", u"Tap changer type", None))
        self.asymmetryAngleLabel.setText(QCoreApplication.translate("TransformerEditorDialog", u"Asymmetry angle (deg)", None))
        self.totalPositionsLabel.setText(QCoreApplication.translate("TransformerEditorDialog", u"Total positions", None))
        self.neutralPositionLabel.setText(QCoreApplication.translate("TransformerEditorDialog", u"Neutral position", None))
        self.tapPositionLabel.setText(QCoreApplication.translate("TransformerEditorDialog", u"Tap position", None))
        self.dvLabel.setText(QCoreApplication.translate("TransformerEditorDialog", u"Voltage increment per position", None))
        self.acceptButton.setText(QCoreApplication.translate("TransformerEditorDialog", u"Accept", None))
    # retranslateUi

