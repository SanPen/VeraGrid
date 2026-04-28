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
    QDoubleSpinBox, QFrame, QLabel, QPushButton,
    QSizePolicy, QSpinBox, QVBoxLayout, QWidget)

class Ui_LineEditorDialog(object):
    def setupUi(self, LineEditorDialog):
        if not LineEditorDialog.objectName():
            LineEditorDialog.setObjectName(u"LineEditorDialog")
        LineEditorDialog.resize(420, 520)
        self.verticalLayout = QVBoxLayout(LineEditorDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.templatesLabel = QLabel(LineEditorDialog)
        self.templatesLabel.setObjectName(u"templatesLabel")

        self.verticalLayout.addWidget(self.templatesLabel)

        self.catalogueComboBox = QComboBox(LineEditorDialog)
        self.catalogueComboBox.setObjectName(u"catalogueComboBox")

        self.verticalLayout.addWidget(self.catalogueComboBox)

        self.circuitIndexLabel = QLabel(LineEditorDialog)
        self.circuitIndexLabel.setObjectName(u"circuitIndexLabel")

        self.verticalLayout.addWidget(self.circuitIndexLabel)

        self.circuitIndexSpinBox = QSpinBox(LineEditorDialog)
        self.circuitIndexSpinBox.setObjectName(u"circuitIndexSpinBox")
        self.circuitIndexSpinBox.setMinimum(1)
        self.circuitIndexSpinBox.setMaximum(1)

        self.verticalLayout.addWidget(self.circuitIndexSpinBox)

        self.loadTemplateButton = QPushButton(LineEditorDialog)
        self.loadTemplateButton.setObjectName(u"loadTemplateButton")

        self.verticalLayout.addWidget(self.loadTemplateButton)

        self.separator = QFrame(LineEditorDialog)
        self.separator.setObjectName(u"separator")
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.separator)

        self.lengthLabel = QLabel(LineEditorDialog)
        self.lengthLabel.setObjectName(u"lengthLabel")

        self.verticalLayout.addWidget(self.lengthLabel)

        self.lengthSpinBox = QDoubleSpinBox(LineEditorDialog)
        self.lengthSpinBox.setObjectName(u"lengthSpinBox")
        self.lengthSpinBox.setDecimals(6)
        self.lengthSpinBox.setMaximum(9999999.000000000000000)

        self.verticalLayout.addWidget(self.lengthSpinBox)

        self.currentLabel = QLabel(LineEditorDialog)
        self.currentLabel.setObjectName(u"currentLabel")

        self.verticalLayout.addWidget(self.currentLabel)

        self.currentSpinBox = QDoubleSpinBox(LineEditorDialog)
        self.currentSpinBox.setObjectName(u"currentSpinBox")
        self.currentSpinBox.setDecimals(6)
        self.currentSpinBox.setMaximum(9999999.000000000000000)

        self.verticalLayout.addWidget(self.currentSpinBox)

        self.resistanceLabel = QLabel(LineEditorDialog)
        self.resistanceLabel.setObjectName(u"resistanceLabel")

        self.verticalLayout.addWidget(self.resistanceLabel)

        self.resistanceSpinBox = QDoubleSpinBox(LineEditorDialog)
        self.resistanceSpinBox.setObjectName(u"resistanceSpinBox")
        self.resistanceSpinBox.setDecimals(6)
        self.resistanceSpinBox.setMaximum(9999999.000000000000000)

        self.verticalLayout.addWidget(self.resistanceSpinBox)

        self.reactanceLabel = QLabel(LineEditorDialog)
        self.reactanceLabel.setObjectName(u"reactanceLabel")

        self.verticalLayout.addWidget(self.reactanceLabel)

        self.reactanceSpinBox = QDoubleSpinBox(LineEditorDialog)
        self.reactanceSpinBox.setObjectName(u"reactanceSpinBox")
        self.reactanceSpinBox.setDecimals(6)
        self.reactanceSpinBox.setMaximum(9999999.000000000000000)

        self.verticalLayout.addWidget(self.reactanceSpinBox)

        self.susceptanceLabel = QLabel(LineEditorDialog)
        self.susceptanceLabel.setObjectName(u"susceptanceLabel")

        self.verticalLayout.addWidget(self.susceptanceLabel)

        self.susceptanceSpinBox = QDoubleSpinBox(LineEditorDialog)
        self.susceptanceSpinBox.setObjectName(u"susceptanceSpinBox")
        self.susceptanceSpinBox.setDecimals(6)
        self.susceptanceSpinBox.setMaximum(9999999.000000000000000)

        self.verticalLayout.addWidget(self.susceptanceSpinBox)

        self.applyToProfilesCheckBox = QCheckBox(LineEditorDialog)
        self.applyToProfilesCheckBox.setObjectName(u"applyToProfilesCheckBox")
        self.applyToProfilesCheckBox.setChecked(True)

        self.verticalLayout.addWidget(self.applyToProfilesCheckBox)

        self.acceptButton = QPushButton(LineEditorDialog)
        self.acceptButton.setObjectName(u"acceptButton")

        self.verticalLayout.addWidget(self.acceptButton)


        self.retranslateUi(LineEditorDialog)

        QMetaObject.connectSlotsByName(LineEditorDialog)
    # setupUi

    def retranslateUi(self, LineEditorDialog):
        LineEditorDialog.setWindowTitle(QCoreApplication.translate("LineEditorDialog", u"Line editor", None))
        self.templatesLabel.setText(QCoreApplication.translate("LineEditorDialog", u"Available templates", None))
        self.circuitIndexLabel.setText(QCoreApplication.translate("LineEditorDialog", u"Circuit index:", None))
        self.loadTemplateButton.setText(QCoreApplication.translate("LineEditorDialog", u"Load template values", None))
        self.lengthLabel.setText(QCoreApplication.translate("LineEditorDialog", u"L: Line length", None))
        self.lengthSpinBox.setSuffix(QCoreApplication.translate("LineEditorDialog", u" km", None))
        self.currentLabel.setText(QCoreApplication.translate("LineEditorDialog", u"Imax: Max. current", None))
        self.currentSpinBox.setSuffix(QCoreApplication.translate("LineEditorDialog", u" kA", None))
        self.resistanceLabel.setText(QCoreApplication.translate("LineEditorDialog", u"R: Resistance", None))
        self.resistanceSpinBox.setSuffix(QCoreApplication.translate("LineEditorDialog", u" \u03a9/km", None))
        self.reactanceLabel.setText(QCoreApplication.translate("LineEditorDialog", u"X: Inductance", None))
        self.reactanceSpinBox.setSuffix(QCoreApplication.translate("LineEditorDialog", u" \u03a9/km", None))
        self.susceptanceLabel.setText(QCoreApplication.translate("LineEditorDialog", u"S: Susceptance", None))
        self.susceptanceSpinBox.setSuffix(QCoreApplication.translate("LineEditorDialog", u" uS/Km", None))
        self.applyToProfilesCheckBox.setText(QCoreApplication.translate("LineEditorDialog", u"Apply to profiles", None))
        self.acceptButton.setText(QCoreApplication.translate("LineEditorDialog", u"Accept", None))
    # retranslateUi

