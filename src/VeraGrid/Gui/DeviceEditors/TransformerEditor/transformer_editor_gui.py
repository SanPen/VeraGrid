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
    QFormLayout, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QWidget)

class Ui_TransformerEditorDialog(object):
    def setupUi(self, TransformerEditorDialog):
        if not TransformerEditorDialog.objectName():
            TransformerEditorDialog.setObjectName(u"TransformerEditorDialog")
        TransformerEditorDialog.resize(581, 598)
        self.formLayout = QFormLayout(TransformerEditorDialog)
        self.formLayout.setObjectName(u"formLayout")
        self.templatesLabel = QLabel(TransformerEditorDialog)
        self.templatesLabel.setObjectName(u"templatesLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.templatesLabel)

        self.separator = QFrame(TransformerEditorDialog)
        self.separator.setObjectName(u"separator")
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.SpanningRole, self.separator)

        self.snLabel = QLabel(TransformerEditorDialog)
        self.snLabel.setObjectName(u"snLabel")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.snLabel)

        self.snSpinBox = QDoubleSpinBox(TransformerEditorDialog)
        self.snSpinBox.setObjectName(u"snSpinBox")
        self.snSpinBox.setDecimals(6)
        self.snSpinBox.setMaximum(999999.000000000000000)

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.snSpinBox)

        self.pcuLabel = QLabel(TransformerEditorDialog)
        self.pcuLabel.setObjectName(u"pcuLabel")

        self.formLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.pcuLabel)

        self.pcuSpinBox = QDoubleSpinBox(TransformerEditorDialog)
        self.pcuSpinBox.setObjectName(u"pcuSpinBox")
        self.pcuSpinBox.setDecimals(6)
        self.pcuSpinBox.setMaximum(999999.000000000000000)

        self.formLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.pcuSpinBox)

        self.pfeLabel = QLabel(TransformerEditorDialog)
        self.pfeLabel.setObjectName(u"pfeLabel")

        self.formLayout.setWidget(8, QFormLayout.ItemRole.LabelRole, self.pfeLabel)

        self.pfeSpinBox = QDoubleSpinBox(TransformerEditorDialog)
        self.pfeSpinBox.setObjectName(u"pfeSpinBox")
        self.pfeSpinBox.setDecimals(6)
        self.pfeSpinBox.setMaximum(999999.000000000000000)

        self.formLayout.setWidget(8, QFormLayout.ItemRole.FieldRole, self.pfeSpinBox)

        self.i0Label = QLabel(TransformerEditorDialog)
        self.i0Label.setObjectName(u"i0Label")

        self.formLayout.setWidget(10, QFormLayout.ItemRole.LabelRole, self.i0Label)

        self.i0SpinBox = QDoubleSpinBox(TransformerEditorDialog)
        self.i0SpinBox.setObjectName(u"i0SpinBox")
        self.i0SpinBox.setDecimals(6)
        self.i0SpinBox.setMaximum(999999.000000000000000)

        self.formLayout.setWidget(10, QFormLayout.ItemRole.FieldRole, self.i0SpinBox)

        self.vscLabel = QLabel(TransformerEditorDialog)
        self.vscLabel.setObjectName(u"vscLabel")

        self.formLayout.setWidget(12, QFormLayout.ItemRole.LabelRole, self.vscLabel)

        self.vscSpinBox = QDoubleSpinBox(TransformerEditorDialog)
        self.vscSpinBox.setObjectName(u"vscSpinBox")
        self.vscSpinBox.setDecimals(6)
        self.vscSpinBox.setMaximum(999999.000000000000000)

        self.formLayout.setWidget(12, QFormLayout.ItemRole.FieldRole, self.vscSpinBox)

        self.tapSeparator = QFrame(TransformerEditorDialog)
        self.tapSeparator.setObjectName(u"tapSeparator")
        self.tapSeparator.setFrameShape(QFrame.Shape.HLine)
        self.tapSeparator.setFrameShadow(QFrame.Shadow.Sunken)

        self.formLayout.setWidget(14, QFormLayout.ItemRole.LabelRole, self.tapSeparator)

        self.tapChangerTypeLabel = QLabel(TransformerEditorDialog)
        self.tapChangerTypeLabel.setObjectName(u"tapChangerTypeLabel")

        self.formLayout.setWidget(15, QFormLayout.ItemRole.LabelRole, self.tapChangerTypeLabel)

        self.tapChangerTypeComboBox = QComboBox(TransformerEditorDialog)
        self.tapChangerTypeComboBox.setObjectName(u"tapChangerTypeComboBox")

        self.formLayout.setWidget(15, QFormLayout.ItemRole.FieldRole, self.tapChangerTypeComboBox)

        self.asymmetryAngleLabel = QLabel(TransformerEditorDialog)
        self.asymmetryAngleLabel.setObjectName(u"asymmetryAngleLabel")

        self.formLayout.setWidget(17, QFormLayout.ItemRole.LabelRole, self.asymmetryAngleLabel)

        self.asymmetryAngleSpinBox = QDoubleSpinBox(TransformerEditorDialog)
        self.asymmetryAngleSpinBox.setObjectName(u"asymmetryAngleSpinBox")
        self.asymmetryAngleSpinBox.setDecimals(6)
        self.asymmetryAngleSpinBox.setMaximum(999999.000000000000000)

        self.formLayout.setWidget(17, QFormLayout.ItemRole.FieldRole, self.asymmetryAngleSpinBox)

        self.totalPositionsLabel = QLabel(TransformerEditorDialog)
        self.totalPositionsLabel.setObjectName(u"totalPositionsLabel")

        self.formLayout.setWidget(19, QFormLayout.ItemRole.LabelRole, self.totalPositionsLabel)

        self.totalPositionsSpinBox = QSpinBox(TransformerEditorDialog)
        self.totalPositionsSpinBox.setObjectName(u"totalPositionsSpinBox")
        self.totalPositionsSpinBox.setMaximum(999999)

        self.formLayout.setWidget(19, QFormLayout.ItemRole.FieldRole, self.totalPositionsSpinBox)

        self.neutralPositionLabel = QLabel(TransformerEditorDialog)
        self.neutralPositionLabel.setObjectName(u"neutralPositionLabel")

        self.formLayout.setWidget(21, QFormLayout.ItemRole.LabelRole, self.neutralPositionLabel)

        self.neutralPositionSpinBox = QSpinBox(TransformerEditorDialog)
        self.neutralPositionSpinBox.setObjectName(u"neutralPositionSpinBox")
        self.neutralPositionSpinBox.setMaximum(999999)

        self.formLayout.setWidget(21, QFormLayout.ItemRole.FieldRole, self.neutralPositionSpinBox)

        self.tapPositionLabel = QLabel(TransformerEditorDialog)
        self.tapPositionLabel.setObjectName(u"tapPositionLabel")

        self.formLayout.setWidget(23, QFormLayout.ItemRole.LabelRole, self.tapPositionLabel)

        self.tapPositionSpinBox = QSpinBox(TransformerEditorDialog)
        self.tapPositionSpinBox.setObjectName(u"tapPositionSpinBox")
        self.tapPositionSpinBox.setMaximum(999999)

        self.formLayout.setWidget(23, QFormLayout.ItemRole.FieldRole, self.tapPositionSpinBox)

        self.dvLabel = QLabel(TransformerEditorDialog)
        self.dvLabel.setObjectName(u"dvLabel")

        self.formLayout.setWidget(25, QFormLayout.ItemRole.LabelRole, self.dvLabel)

        self.dvSpinBox = QDoubleSpinBox(TransformerEditorDialog)
        self.dvSpinBox.setObjectName(u"dvSpinBox")
        self.dvSpinBox.setDecimals(6)
        self.dvSpinBox.setMaximum(999999.000000000000000)

        self.formLayout.setWidget(25, QFormLayout.ItemRole.FieldRole, self.dvSpinBox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout.setItem(27, QFormLayout.ItemRole.FieldRole, self.verticalSpacer)

        self.frame = QFrame(TransformerEditorDialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.catalogueComboBox = QComboBox(self.frame)
        self.catalogueComboBox.setObjectName(u"catalogueComboBox")

        self.horizontalLayout.addWidget(self.catalogueComboBox)

        self.loadTemplateButton = QPushButton(self.frame)
        self.loadTemplateButton.setObjectName(u"loadTemplateButton")
        self.loadTemplateButton.setMaximumSize(QSize(180, 16777215))

        self.horizontalLayout.addWidget(self.loadTemplateButton)


        self.formLayout.setWidget(1, QFormLayout.ItemRole.SpanningRole, self.frame)

        self.frame_2 = QFrame(TransformerEditorDialog)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer = QSpacerItem(474, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.acceptButton = QPushButton(self.frame_2)
        self.acceptButton.setObjectName(u"acceptButton")

        self.horizontalLayout_2.addWidget(self.acceptButton)


        self.formLayout.setWidget(28, QFormLayout.ItemRole.SpanningRole, self.frame_2)


        self.retranslateUi(TransformerEditorDialog)

        QMetaObject.connectSlotsByName(TransformerEditorDialog)
    # setupUi

    def retranslateUi(self, TransformerEditorDialog):
        TransformerEditorDialog.setWindowTitle(QCoreApplication.translate("TransformerEditorDialog", u"Transformer editor", None))
        self.templatesLabel.setText(QCoreApplication.translate("TransformerEditorDialog", u"Suitable templates", None))
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
        self.loadTemplateButton.setText(QCoreApplication.translate("TransformerEditorDialog", u"Load template values", None))
        self.acceptButton.setText(QCoreApplication.translate("TransformerEditorDialog", u"Accept", None))
    # retranslateUi

