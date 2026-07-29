# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'admittance_matrix_editor_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QTableView, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_AdmittanceMatrixEditorWidget(object):
    def setupUi(self, AdmittanceMatrixEditorWidget):
        if not AdmittanceMatrixEditorWidget.objectName():
            AdmittanceMatrixEditorWidget.setObjectName(u"AdmittanceMatrixEditorWidget")
        AdmittanceMatrixEditorWidget.resize(785, 454)
        self.gridLayout = QGridLayout(AdmittanceMatrixEditorWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.phaseLayout = QHBoxLayout()
        self.phaseLayout.setObjectName(u"phaseLayout")
        self.phasesLabel = QLabel(AdmittanceMatrixEditorWidget)
        self.phasesLabel.setObjectName(u"phasesLabel")

        self.phaseLayout.addWidget(self.phasesLabel)

        self.phaseNCheckBox = QCheckBox(AdmittanceMatrixEditorWidget)
        self.phaseNCheckBox.setObjectName(u"phaseNCheckBox")

        self.phaseLayout.addWidget(self.phaseNCheckBox)

        self.phaseACheckBox = QCheckBox(AdmittanceMatrixEditorWidget)
        self.phaseACheckBox.setObjectName(u"phaseACheckBox")

        self.phaseLayout.addWidget(self.phaseACheckBox)

        self.phaseBCheckBox = QCheckBox(AdmittanceMatrixEditorWidget)
        self.phaseBCheckBox.setObjectName(u"phaseBCheckBox")

        self.phaseLayout.addWidget(self.phaseBCheckBox)

        self.phaseCCheckBox = QCheckBox(AdmittanceMatrixEditorWidget)
        self.phaseCCheckBox.setObjectName(u"phaseCCheckBox")

        self.phaseLayout.addWidget(self.phaseCCheckBox)

        self.phaseSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.phaseLayout.addItem(self.phaseSpacer)


        self.gridLayout.addLayout(self.phaseLayout, 2, 0, 1, 2)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 6, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 7, 0, 1, 1)

        self.yshTableView = QTableView(AdmittanceMatrixEditorWidget)
        self.yshTableView.setObjectName(u"yshTableView")

        self.gridLayout.addWidget(self.yshTableView, 6, 0, 1, 1)

        self.matrixTableView = QTableView(AdmittanceMatrixEditorWidget)
        self.matrixTableView.setObjectName(u"matrixTableView")

        self.gridLayout.addWidget(self.matrixTableView, 4, 0, 1, 1)

        self.actionsLayout = QHBoxLayout()
        self.actionsLayout.setObjectName(u"actionsLayout")
        self.computeButton = QPushButton(AdmittanceMatrixEditorWidget)
        self.computeButton.setObjectName(u"computeButton")
        icon = QIcon()
        icon.addFile(u":/Icons/icons/calculator.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.computeButton.setIcon(icon)

        self.actionsLayout.addWidget(self.computeButton)

        self.actionsSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.actionsLayout.addItem(self.actionsSpacer)

        self.acceptButton = QPushButton(AdmittanceMatrixEditorWidget)
        self.acceptButton.setObjectName(u"acceptButton")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/accept.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.acceptButton.setIcon(icon1)

        self.actionsLayout.addWidget(self.acceptButton)


        self.gridLayout.addLayout(self.actionsLayout, 8, 0, 1, 2)

        self.titleLabel = QLabel(AdmittanceMatrixEditorWidget)
        self.titleLabel.setObjectName(u"titleLabel")
        font = QFont()
        font.setBold(True)
        self.titleLabel.setFont(font)
        self.titleLabel.setWordWrap(True)

        self.gridLayout.addWidget(self.titleLabel, 0, 0, 1, 2)

        self.descriptionLabel = QLabel(AdmittanceMatrixEditorWidget)
        self.descriptionLabel.setObjectName(u"descriptionLabel")
        self.descriptionLabel.setWordWrap(True)

        self.gridLayout.addWidget(self.descriptionLabel, 1, 0, 1, 2)

        self.yshLabel = QLabel(AdmittanceMatrixEditorWidget)
        self.yshLabel.setObjectName(u"yshLabel")
        self.yshLabel.setFont(font)

        self.gridLayout.addWidget(self.yshLabel, 5, 0, 1, 2)

        self.yshLabel_2 = QLabel(AdmittanceMatrixEditorWidget)
        self.yshLabel_2.setObjectName(u"yshLabel_2")
        self.yshLabel_2.setFont(font)

        self.gridLayout.addWidget(self.yshLabel_2, 3, 0, 1, 1)


        self.retranslateUi(AdmittanceMatrixEditorWidget)

        QMetaObject.connectSlotsByName(AdmittanceMatrixEditorWidget)
    # setupUi

    def retranslateUi(self, AdmittanceMatrixEditorWidget):
        self.phasesLabel.setText(QCoreApplication.translate("AdmittanceMatrixEditorWidget", u"Phases:", None))
        self.phaseNCheckBox.setText(QCoreApplication.translate("AdmittanceMatrixEditorWidget", u"N", None))
        self.phaseACheckBox.setText(QCoreApplication.translate("AdmittanceMatrixEditorWidget", u"A", None))
        self.phaseBCheckBox.setText(QCoreApplication.translate("AdmittanceMatrixEditorWidget", u"B", None))
        self.phaseCCheckBox.setText(QCoreApplication.translate("AdmittanceMatrixEditorWidget", u"C", None))
#if QT_CONFIG(tooltip)
        self.computeButton.setToolTip(QCoreApplication.translate("AdmittanceMatrixEditorWidget", u"Compute from sequence values", None))
#endif // QT_CONFIG(tooltip)
        self.computeButton.setText("")
        self.acceptButton.setText(QCoreApplication.translate("AdmittanceMatrixEditorWidget", u"Accept", None))
        self.titleLabel.setText(QCoreApplication.translate("AdmittanceMatrixEditorWidget", u"Admittance matrix", None))
        self.descriptionLabel.setText(QCoreApplication.translate("AdmittanceMatrixEditorWidget", u"Dense complex admittance matrix.", None))
        self.yshLabel.setText(QCoreApplication.translate("AdmittanceMatrixEditorWidget", u"Shunt admittance", None))
        self.yshLabel_2.setText(QCoreApplication.translate("AdmittanceMatrixEditorWidget", u"Series admittance", None))
        pass
    # retranslateUi

