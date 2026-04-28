# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dc_line_editor_gui.ui'
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
    QVBoxLayout, QWidget)

class Ui_DcLineEditorDialog(object):
    def setupUi(self, DcLineEditorDialog):
        if not DcLineEditorDialog.objectName():
            DcLineEditorDialog.setObjectName(u"DcLineEditorDialog")
        DcLineEditorDialog.resize(420, 340)
        self.verticalLayout = QVBoxLayout(DcLineEditorDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.templatesLabel = QLabel(DcLineEditorDialog)
        self.templatesLabel.setObjectName(u"templatesLabel")

        self.verticalLayout.addWidget(self.templatesLabel)

        self.catalogueComboBox = QComboBox(DcLineEditorDialog)
        self.catalogueComboBox.setObjectName(u"catalogueComboBox")

        self.verticalLayout.addWidget(self.catalogueComboBox)

        self.loadTemplateButton = QPushButton(DcLineEditorDialog)
        self.loadTemplateButton.setObjectName(u"loadTemplateButton")

        self.verticalLayout.addWidget(self.loadTemplateButton)

        self.lineSeparator = QFrame(DcLineEditorDialog)
        self.lineSeparator.setObjectName(u"lineSeparator")
        self.lineSeparator.setFrameShape(QFrame.Shape.HLine)
        self.lineSeparator.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.lineSeparator)

        self.lengthLabel = QLabel(DcLineEditorDialog)
        self.lengthLabel.setObjectName(u"lengthLabel")

        self.verticalLayout.addWidget(self.lengthLabel)

        self.lengthSpinBox = QDoubleSpinBox(DcLineEditorDialog)
        self.lengthSpinBox.setObjectName(u"lengthSpinBox")
        self.lengthSpinBox.setDecimals(6)
        self.lengthSpinBox.setMaximum(9999999.000000000000000)
        self.lengthSpinBox.setValue(1.000000000000000)

        self.verticalLayout.addWidget(self.lengthSpinBox)

        self.currentLabel = QLabel(DcLineEditorDialog)
        self.currentLabel.setObjectName(u"currentLabel")

        self.verticalLayout.addWidget(self.currentLabel)

        self.currentSpinBox = QDoubleSpinBox(DcLineEditorDialog)
        self.currentSpinBox.setObjectName(u"currentSpinBox")
        self.currentSpinBox.setDecimals(2)
        self.currentSpinBox.setMaximum(9999999.000000000000000)

        self.verticalLayout.addWidget(self.currentSpinBox)

        self.resistanceLabel = QLabel(DcLineEditorDialog)
        self.resistanceLabel.setObjectName(u"resistanceLabel")

        self.verticalLayout.addWidget(self.resistanceLabel)

        self.resistanceSpinBox = QDoubleSpinBox(DcLineEditorDialog)
        self.resistanceSpinBox.setObjectName(u"resistanceSpinBox")
        self.resistanceSpinBox.setDecimals(6)
        self.resistanceSpinBox.setMaximum(9999999.000000000000000)

        self.verticalLayout.addWidget(self.resistanceSpinBox)

        self.acceptButton = QPushButton(DcLineEditorDialog)
        self.acceptButton.setObjectName(u"acceptButton")

        self.verticalLayout.addWidget(self.acceptButton)


        self.retranslateUi(DcLineEditorDialog)

        QMetaObject.connectSlotsByName(DcLineEditorDialog)
    # setupUi

    def retranslateUi(self, DcLineEditorDialog):
        DcLineEditorDialog.setWindowTitle(QCoreApplication.translate("DcLineEditorDialog", u"Line editor", None))
        self.templatesLabel.setText(QCoreApplication.translate("DcLineEditorDialog", u"Available templates", None))
        self.loadTemplateButton.setText(QCoreApplication.translate("DcLineEditorDialog", u"Load template values", None))
        self.lengthLabel.setText(QCoreApplication.translate("DcLineEditorDialog", u"L: Line length [km]", None))
        self.currentLabel.setText(QCoreApplication.translate("DcLineEditorDialog", u"Imax: Max. current [kA]", None))
        self.resistanceLabel.setText(QCoreApplication.translate("DcLineEditorDialog", u"R: Resistance [Ohm/km]", None))
        self.acceptButton.setText(QCoreApplication.translate("DcLineEditorDialog", u"Accept", None))
    # retranslateUi

