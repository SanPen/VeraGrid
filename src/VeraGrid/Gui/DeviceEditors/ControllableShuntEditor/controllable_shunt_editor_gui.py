# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'controllable_shunt_editor_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QHeaderView,
    QPushButton, QSizePolicy, QSpacerItem, QTableView,
    QVBoxLayout, QWidget)

class Ui_ControllableShuntEditorDialog(object):
    def setupUi(self, ControllableShuntEditorDialog):
        if not ControllableShuntEditorDialog.objectName():
            ControllableShuntEditorDialog.setObjectName(u"ControllableShuntEditorDialog")
        ControllableShuntEditorDialog.resize(640, 420)
        self.verticalLayout = QVBoxLayout(ControllableShuntEditorDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tableView = QTableView(ControllableShuntEditorDialog)
        self.tableView.setObjectName(u"tableView")

        self.verticalLayout.addWidget(self.tableView)

        self.buttonsLayout = QHBoxLayout()
        self.buttonsLayout.setObjectName(u"buttonsLayout")
        self.addButton = QPushButton(ControllableShuntEditorDialog)
        self.addButton.setObjectName(u"addButton")

        self.buttonsLayout.addWidget(self.addButton)

        self.deleteButton = QPushButton(ControllableShuntEditorDialog)
        self.deleteButton.setObjectName(u"deleteButton")

        self.buttonsLayout.addWidget(self.deleteButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttonsLayout.addItem(self.horizontalSpacer)

        self.doneButton = QPushButton(ControllableShuntEditorDialog)
        self.doneButton.setObjectName(u"doneButton")

        self.buttonsLayout.addWidget(self.doneButton)


        self.verticalLayout.addLayout(self.buttonsLayout)


        self.retranslateUi(ControllableShuntEditorDialog)

        QMetaObject.connectSlotsByName(ControllableShuntEditorDialog)
    # setupUi

    def retranslateUi(self, ControllableShuntEditorDialog):
        ControllableShuntEditorDialog.setWindowTitle(QCoreApplication.translate("ControllableShuntEditorDialog", u"Controllable shunt editor", None))
        self.addButton.setText(QCoreApplication.translate("ControllableShuntEditorDialog", u"Add", None))
        self.deleteButton.setText(QCoreApplication.translate("ControllableShuntEditorDialog", u"Delete", None))
        self.doneButton.setText(QCoreApplication.translate("ControllableShuntEditorDialog", u"Done", None))
    # retranslateUi

