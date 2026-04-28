# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'map_warning_ui.ui'
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
        Dialog.resize(400, 300)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.MapWarningDialog = QLabel(Dialog)
        self.MapWarningDialog.setObjectName(u"MapWarningDialog")

        self.verticalLayout.addWidget(self.MapWarningDialog)

        self.okButton = QPushButton(Dialog)
        self.okButton.setObjectName(u"okButton")

        self.verticalLayout.addWidget(self.okButton)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.MapWarningDialog.setText(QCoreApplication.translate("Dialog", u"Please select a Map diagram before expanding the grid.", None))
        self.okButton.setText(QCoreApplication.translate("Dialog", u"OK", None))
    # retranslateUi

