# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'transformer3w_editor_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QDoubleSpinBox, QGroupBox,
    QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_Transformer3wEditorDialog(object):
    def setupUi(self, Transformer3wEditorDialog):
        if not Transformer3wEditorDialog.objectName():
            Transformer3wEditorDialog.setObjectName(u"Transformer3wEditorDialog")
        Transformer3wEditorDialog.resize(900, 420)
        self.verticalLayout = QVBoxLayout(Transformer3wEditorDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.nameLabel = QLabel(Transformer3wEditorDialog)
        self.nameLabel.setObjectName(u"nameLabel")

        self.verticalLayout.addWidget(self.nameLabel)

        self.pfeLabel = QLabel(Transformer3wEditorDialog)
        self.pfeLabel.setObjectName(u"pfeLabel")

        self.verticalLayout.addWidget(self.pfeLabel)

        self.pfeSpinBox = QDoubleSpinBox(Transformer3wEditorDialog)
        self.pfeSpinBox.setObjectName(u"pfeSpinBox")
        self.pfeSpinBox.setDecimals(6)
        self.pfeSpinBox.setMaximum(999999.000000000000000)

        self.verticalLayout.addWidget(self.pfeSpinBox)

        self.i0Label = QLabel(Transformer3wEditorDialog)
        self.i0Label.setObjectName(u"i0Label")

        self.verticalLayout.addWidget(self.i0Label)

        self.i0SpinBox = QDoubleSpinBox(Transformer3wEditorDialog)
        self.i0SpinBox.setObjectName(u"i0SpinBox")
        self.i0SpinBox.setDecimals(6)
        self.i0SpinBox.setMaximum(999999.000000000000000)

        self.verticalLayout.addWidget(self.i0SpinBox)

        self.windingsLayout = QHBoxLayout()
        self.windingsLayout.setObjectName(u"windingsLayout")
        self.winding1GroupBox = QGroupBox(Transformer3wEditorDialog)
        self.winding1GroupBox.setObjectName(u"winding1GroupBox")
        self.w1Layout = QVBoxLayout(self.winding1GroupBox)
        self.w1Layout.setObjectName(u"w1Layout")
        self.w1BusVoltageLabel = QLabel(self.winding1GroupBox)
        self.w1BusVoltageLabel.setObjectName(u"w1BusVoltageLabel")

        self.w1Layout.addWidget(self.w1BusVoltageLabel)

        self.w1VLabel = QLabel(self.winding1GroupBox)
        self.w1VLabel.setObjectName(u"w1VLabel")

        self.w1Layout.addWidget(self.w1VLabel)

        self.w1VnSpinBox = QDoubleSpinBox(self.winding1GroupBox)
        self.w1VnSpinBox.setObjectName(u"w1VnSpinBox")
        self.w1VnSpinBox.setDecimals(6)
        self.w1VnSpinBox.setMaximum(999999.000000000000000)

        self.w1Layout.addWidget(self.w1VnSpinBox)

        self.w1SnLabel = QLabel(self.winding1GroupBox)
        self.w1SnLabel.setObjectName(u"w1SnLabel")

        self.w1Layout.addWidget(self.w1SnLabel)

        self.w1SnSpinBox = QDoubleSpinBox(self.winding1GroupBox)
        self.w1SnSpinBox.setObjectName(u"w1SnSpinBox")
        self.w1SnSpinBox.setDecimals(6)
        self.w1SnSpinBox.setMaximum(999999.000000000000000)

        self.w1Layout.addWidget(self.w1SnSpinBox)

        self.w1PcuLabel = QLabel(self.winding1GroupBox)
        self.w1PcuLabel.setObjectName(u"w1PcuLabel")

        self.w1Layout.addWidget(self.w1PcuLabel)

        self.w1PcuSpinBox = QDoubleSpinBox(self.winding1GroupBox)
        self.w1PcuSpinBox.setObjectName(u"w1PcuSpinBox")
        self.w1PcuSpinBox.setDecimals(6)
        self.w1PcuSpinBox.setMaximum(999999.000000000000000)

        self.w1Layout.addWidget(self.w1PcuSpinBox)

        self.w1VscLabel = QLabel(self.winding1GroupBox)
        self.w1VscLabel.setObjectName(u"w1VscLabel")

        self.w1Layout.addWidget(self.w1VscLabel)

        self.w1VscSpinBox = QDoubleSpinBox(self.winding1GroupBox)
        self.w1VscSpinBox.setObjectName(u"w1VscSpinBox")
        self.w1VscSpinBox.setDecimals(6)
        self.w1VscSpinBox.setMaximum(999999.000000000000000)

        self.w1Layout.addWidget(self.w1VscSpinBox)


        self.windingsLayout.addWidget(self.winding1GroupBox)

        self.winding2GroupBox = QGroupBox(Transformer3wEditorDialog)
        self.winding2GroupBox.setObjectName(u"winding2GroupBox")
        self.w2Layout = QVBoxLayout(self.winding2GroupBox)
        self.w2Layout.setObjectName(u"w2Layout")
        self.w2BusVoltageLabel = QLabel(self.winding2GroupBox)
        self.w2BusVoltageLabel.setObjectName(u"w2BusVoltageLabel")

        self.w2Layout.addWidget(self.w2BusVoltageLabel)

        self.w2VLabel = QLabel(self.winding2GroupBox)
        self.w2VLabel.setObjectName(u"w2VLabel")

        self.w2Layout.addWidget(self.w2VLabel)

        self.w2VnSpinBox = QDoubleSpinBox(self.winding2GroupBox)
        self.w2VnSpinBox.setObjectName(u"w2VnSpinBox")
        self.w2VnSpinBox.setDecimals(6)
        self.w2VnSpinBox.setMaximum(999999.000000000000000)

        self.w2Layout.addWidget(self.w2VnSpinBox)

        self.w2SnLabel = QLabel(self.winding2GroupBox)
        self.w2SnLabel.setObjectName(u"w2SnLabel")

        self.w2Layout.addWidget(self.w2SnLabel)

        self.w2SnSpinBox = QDoubleSpinBox(self.winding2GroupBox)
        self.w2SnSpinBox.setObjectName(u"w2SnSpinBox")
        self.w2SnSpinBox.setDecimals(6)
        self.w2SnSpinBox.setMaximum(999999.000000000000000)

        self.w2Layout.addWidget(self.w2SnSpinBox)

        self.w2PcuLabel = QLabel(self.winding2GroupBox)
        self.w2PcuLabel.setObjectName(u"w2PcuLabel")

        self.w2Layout.addWidget(self.w2PcuLabel)

        self.w2PcuSpinBox = QDoubleSpinBox(self.winding2GroupBox)
        self.w2PcuSpinBox.setObjectName(u"w2PcuSpinBox")
        self.w2PcuSpinBox.setDecimals(6)
        self.w2PcuSpinBox.setMaximum(999999.000000000000000)

        self.w2Layout.addWidget(self.w2PcuSpinBox)

        self.w2VscLabel = QLabel(self.winding2GroupBox)
        self.w2VscLabel.setObjectName(u"w2VscLabel")

        self.w2Layout.addWidget(self.w2VscLabel)

        self.w2VscSpinBox = QDoubleSpinBox(self.winding2GroupBox)
        self.w2VscSpinBox.setObjectName(u"w2VscSpinBox")
        self.w2VscSpinBox.setDecimals(6)
        self.w2VscSpinBox.setMaximum(999999.000000000000000)

        self.w2Layout.addWidget(self.w2VscSpinBox)


        self.windingsLayout.addWidget(self.winding2GroupBox)

        self.winding3GroupBox = QGroupBox(Transformer3wEditorDialog)
        self.winding3GroupBox.setObjectName(u"winding3GroupBox")
        self.w3Layout = QVBoxLayout(self.winding3GroupBox)
        self.w3Layout.setObjectName(u"w3Layout")
        self.w3BusVoltageLabel = QLabel(self.winding3GroupBox)
        self.w3BusVoltageLabel.setObjectName(u"w3BusVoltageLabel")

        self.w3Layout.addWidget(self.w3BusVoltageLabel)

        self.w3VLabel = QLabel(self.winding3GroupBox)
        self.w3VLabel.setObjectName(u"w3VLabel")

        self.w3Layout.addWidget(self.w3VLabel)

        self.w3VnSpinBox = QDoubleSpinBox(self.winding3GroupBox)
        self.w3VnSpinBox.setObjectName(u"w3VnSpinBox")
        self.w3VnSpinBox.setDecimals(6)
        self.w3VnSpinBox.setMaximum(999999.000000000000000)

        self.w3Layout.addWidget(self.w3VnSpinBox)

        self.w3SnLabel = QLabel(self.winding3GroupBox)
        self.w3SnLabel.setObjectName(u"w3SnLabel")

        self.w3Layout.addWidget(self.w3SnLabel)

        self.w3SnSpinBox = QDoubleSpinBox(self.winding3GroupBox)
        self.w3SnSpinBox.setObjectName(u"w3SnSpinBox")
        self.w3SnSpinBox.setDecimals(6)
        self.w3SnSpinBox.setMaximum(999999.000000000000000)

        self.w3Layout.addWidget(self.w3SnSpinBox)

        self.w3PcuLabel = QLabel(self.winding3GroupBox)
        self.w3PcuLabel.setObjectName(u"w3PcuLabel")

        self.w3Layout.addWidget(self.w3PcuLabel)

        self.w3PcuSpinBox = QDoubleSpinBox(self.winding3GroupBox)
        self.w3PcuSpinBox.setObjectName(u"w3PcuSpinBox")
        self.w3PcuSpinBox.setDecimals(6)
        self.w3PcuSpinBox.setMaximum(999999.000000000000000)

        self.w3Layout.addWidget(self.w3PcuSpinBox)

        self.w3VscLabel = QLabel(self.winding3GroupBox)
        self.w3VscLabel.setObjectName(u"w3VscLabel")

        self.w3Layout.addWidget(self.w3VscLabel)

        self.w3VscSpinBox = QDoubleSpinBox(self.winding3GroupBox)
        self.w3VscSpinBox.setObjectName(u"w3VscSpinBox")
        self.w3VscSpinBox.setDecimals(6)
        self.w3VscSpinBox.setMaximum(999999.000000000000000)

        self.w3Layout.addWidget(self.w3VscSpinBox)


        self.windingsLayout.addWidget(self.winding3GroupBox)


        self.verticalLayout.addLayout(self.windingsLayout)

        self.acceptButton = QPushButton(Transformer3wEditorDialog)
        self.acceptButton.setObjectName(u"acceptButton")

        self.verticalLayout.addWidget(self.acceptButton)


        self.retranslateUi(Transformer3wEditorDialog)

        QMetaObject.connectSlotsByName(Transformer3wEditorDialog)
    # setupUi

    def retranslateUi(self, Transformer3wEditorDialog):
        Transformer3wEditorDialog.setWindowTitle(QCoreApplication.translate("Transformer3wEditorDialog", u"Transformer editor", None))
        self.nameLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Name:", None))
        self.pfeLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Pfe: Iron losses [kW]", None))
        self.i0Label.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"I0: No load current [%]", None))
        self.winding1GroupBox.setTitle(QCoreApplication.translate("Transformer3wEditorDialog", u"Winding 1", None))
        self.w1BusVoltageLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Bus voltage: N/A", None))
        self.w1VLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"V1: Nominal voltage [kV]", None))
        self.w1SnLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Sn1: Nominal power [MVA]", None))
        self.w1PcuLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Pcu 1-2: Copper losses [kW]", None))
        self.w1VscLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Vsc 1-2: Short circuit voltage [%]", None))
        self.winding2GroupBox.setTitle(QCoreApplication.translate("Transformer3wEditorDialog", u"Winding 2", None))
        self.w2BusVoltageLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Bus voltage: N/A", None))
        self.w2VLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"V2: Nominal voltage [kV]", None))
        self.w2SnLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Sn2: Nominal power [MVA]", None))
        self.w2PcuLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Pcu 2-3: Copper losses [kW]", None))
        self.w2VscLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Vsc 2-3: Short circuit voltage [%]", None))
        self.winding3GroupBox.setTitle(QCoreApplication.translate("Transformer3wEditorDialog", u"Winding 3", None))
        self.w3BusVoltageLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Bus voltage: N/A", None))
        self.w3VLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"V3: Nominal voltage [kV]", None))
        self.w3SnLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Sn3: Nominal power [MVA]", None))
        self.w3PcuLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Pcu 3-1: Copper losses [kW]", None))
        self.w3VscLabel.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Vsc 3-1: Short circuit voltage [%]", None))
        self.acceptButton.setText(QCoreApplication.translate("Transformer3wEditorDialog", u"Accept", None))
    # retranslateUi

