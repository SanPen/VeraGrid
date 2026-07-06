# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'line_editor_gui.ui'
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
    QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QSpinBox, QWidget)

class Ui_LineEditorDialog(object):
    def setupUi(self, LineEditorDialog):
        if not LineEditorDialog.objectName():
            LineEditorDialog.setObjectName(u"LineEditorDialog")
        LineEditorDialog.resize(494, 428)
        self.formLayout = QFormLayout(LineEditorDialog)
        self.formLayout.setObjectName(u"formLayout")
        self.templatesLabel = QLabel(LineEditorDialog)
        self.templatesLabel.setObjectName(u"templatesLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.SpanningRole, self.templatesLabel)

        self.frame_2 = QFrame(LineEditorDialog)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.catalogueComboBox = QComboBox(self.frame_2)
        self.catalogueComboBox.setObjectName(u"catalogueComboBox")

        self.horizontalLayout_2.addWidget(self.catalogueComboBox)

        self.loadTemplateButton = QPushButton(self.frame_2)
        self.loadTemplateButton.setObjectName(u"loadTemplateButton")
        self.loadTemplateButton.setMaximumSize(QSize(180, 16777215))

        self.horizontalLayout_2.addWidget(self.loadTemplateButton)


        self.formLayout.setWidget(1, QFormLayout.ItemRole.SpanningRole, self.frame_2)

        self.separator = QFrame(LineEditorDialog)
        self.separator.setObjectName(u"separator")
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.SpanningRole, self.separator)

        self.circuitIndexLabel = QLabel(LineEditorDialog)
        self.circuitIndexLabel.setObjectName(u"circuitIndexLabel")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.circuitIndexLabel)

        self.circuitIndexSpinBox = QSpinBox(LineEditorDialog)
        self.circuitIndexSpinBox.setObjectName(u"circuitIndexSpinBox")
        self.circuitIndexSpinBox.setMinimum(1)
        self.circuitIndexSpinBox.setMaximum(1)

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.circuitIndexSpinBox)

        self.lengthLabel = QLabel(LineEditorDialog)
        self.lengthLabel.setObjectName(u"lengthLabel")

        self.formLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.lengthLabel)

        self.lengthSpinBox = QDoubleSpinBox(LineEditorDialog)
        self.lengthSpinBox.setObjectName(u"lengthSpinBox")
        self.lengthSpinBox.setDecimals(6)
        self.lengthSpinBox.setMaximum(9999999.000000000000000)

        self.formLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.lengthSpinBox)

        self.resistanceLabel = QLabel(LineEditorDialog)
        self.resistanceLabel.setObjectName(u"resistanceLabel")

        self.formLayout.setWidget(7, QFormLayout.ItemRole.LabelRole, self.resistanceLabel)

        self.resistanceSpinBox = QDoubleSpinBox(LineEditorDialog)
        self.resistanceSpinBox.setObjectName(u"resistanceSpinBox")
        self.resistanceSpinBox.setDecimals(6)
        self.resistanceSpinBox.setMaximum(9999999.000000000000000)

        self.formLayout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.resistanceSpinBox)

        self.currentLabel = QLabel(LineEditorDialog)
        self.currentLabel.setObjectName(u"currentLabel")

        self.formLayout.setWidget(8, QFormLayout.ItemRole.LabelRole, self.currentLabel)

        self.currentSpinBox = QDoubleSpinBox(LineEditorDialog)
        self.currentSpinBox.setObjectName(u"currentSpinBox")
        self.currentSpinBox.setDecimals(6)
        self.currentSpinBox.setMaximum(9999999.000000000000000)

        self.formLayout.setWidget(8, QFormLayout.ItemRole.FieldRole, self.currentSpinBox)

        self.reactanceLabel = QLabel(LineEditorDialog)
        self.reactanceLabel.setObjectName(u"reactanceLabel")

        self.formLayout.setWidget(9, QFormLayout.ItemRole.LabelRole, self.reactanceLabel)

        self.reactanceSpinBox = QDoubleSpinBox(LineEditorDialog)
        self.reactanceSpinBox.setObjectName(u"reactanceSpinBox")
        self.reactanceSpinBox.setDecimals(6)
        self.reactanceSpinBox.setMaximum(9999999.000000000000000)

        self.formLayout.setWidget(9, QFormLayout.ItemRole.FieldRole, self.reactanceSpinBox)

        self.susceptanceLabel = QLabel(LineEditorDialog)
        self.susceptanceLabel.setObjectName(u"susceptanceLabel")

        self.formLayout.setWidget(10, QFormLayout.ItemRole.LabelRole, self.susceptanceLabel)

        self.susceptanceSpinBox = QDoubleSpinBox(LineEditorDialog)
        self.susceptanceSpinBox.setObjectName(u"susceptanceSpinBox")
        self.susceptanceSpinBox.setDecimals(6)
        self.susceptanceSpinBox.setMaximum(9999999.000000000000000)

        self.formLayout.setWidget(10, QFormLayout.ItemRole.FieldRole, self.susceptanceSpinBox)

        self.frame = QFrame(LineEditorDialog)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.applyToProfilesCheckBox = QCheckBox(self.frame)
        self.applyToProfilesCheckBox.setObjectName(u"applyToProfilesCheckBox")
        self.applyToProfilesCheckBox.setChecked(True)

        self.horizontalLayout.addWidget(self.applyToProfilesCheckBox)

        self.horizontalSpacer = QSpacerItem(259, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.acceptButton = QPushButton(self.frame)
        self.acceptButton.setObjectName(u"acceptButton")

        self.horizontalLayout.addWidget(self.acceptButton)


        self.formLayout.setWidget(24, QFormLayout.ItemRole.SpanningRole, self.frame)


        self.retranslateUi(LineEditorDialog)

        QMetaObject.connectSlotsByName(LineEditorDialog)
    # setupUi

    def retranslateUi(self, LineEditorDialog):
        LineEditorDialog.setWindowTitle(QCoreApplication.translate("LineEditorDialog", u"Line editor", None))
        self.templatesLabel.setText(QCoreApplication.translate("LineEditorDialog", u"Available templates", None))
        self.loadTemplateButton.setText(QCoreApplication.translate("LineEditorDialog", u"Load template values", None))
        self.circuitIndexLabel.setText(QCoreApplication.translate("LineEditorDialog", u"Circuit index:", None))
        self.lengthLabel.setText(QCoreApplication.translate("LineEditorDialog", u"L: Line length", None))
        self.lengthSpinBox.setSuffix(QCoreApplication.translate("LineEditorDialog", u" km", None))
        self.resistanceLabel.setText(QCoreApplication.translate("LineEditorDialog", u"R: Resistance", None))
        self.resistanceSpinBox.setSuffix(QCoreApplication.translate("LineEditorDialog", u" \u03a9/km", None))
        self.currentLabel.setText(QCoreApplication.translate("LineEditorDialog", u"Imax: Max. current", None))
        self.currentSpinBox.setSuffix(QCoreApplication.translate("LineEditorDialog", u" kA", None))
        self.reactanceLabel.setText(QCoreApplication.translate("LineEditorDialog", u"X: Inductance", None))
        self.reactanceSpinBox.setSuffix(QCoreApplication.translate("LineEditorDialog", u" \u03a9/km", None))
        self.susceptanceLabel.setText(QCoreApplication.translate("LineEditorDialog", u"S: Susceptance", None))
        self.susceptanceSpinBox.setSuffix(QCoreApplication.translate("LineEditorDialog", u" uS/km", None))
        self.applyToProfilesCheckBox.setText(QCoreApplication.translate("LineEditorDialog", u"Apply to profiles", None))
        self.acceptButton.setText(QCoreApplication.translate("LineEditorDialog", u"Accept", None))
    # retranslateUi

