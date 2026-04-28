# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'voltage_warning_ui.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(480, 200)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.headerLabel = QLabel(Dialog)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.offendersLabel = QLabel(Dialog)
        self.offendersLabel.setObjectName(u"offendersLabel")

        self.verticalLayout.addWidget(self.offendersLabel)

        self.validVoltagesLabel = QLabel(Dialog)
        self.validVoltagesLabel.setObjectName(u"validVoltagesLabel")

        self.verticalLayout.addWidget(self.validVoltagesLabel)

        self.okButton = QPushButton(Dialog)
        self.okButton.setObjectName(u"okButton")

        self.verticalLayout.addWidget(self.okButton)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.headerLabel.setText(QCoreApplication.translate("Dialog", u"The following substations have voltage levels not present in the grid:", None))
        self.offendersLabel.setText("")
        self.validVoltagesLabel.setText("")
        self.okButton.setText(QCoreApplication.translate("Dialog", u"OK", None))
    # retranslateUi

