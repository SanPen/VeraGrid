# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dynamic_block_properties.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QTabWidget,
    QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_DynamicBlockPropertiesDialog(object):
    def setupUi(self, DynamicBlockPropertiesDialog):
        if not DynamicBlockPropertiesDialog.objectName():
            DynamicBlockPropertiesDialog.setObjectName(u"DynamicBlockPropertiesDialog")
        DynamicBlockPropertiesDialog.resize(1200, 700)
        self.main_layout = QVBoxLayout(DynamicBlockPropertiesDialog)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.tab_widget = QTabWidget(DynamicBlockPropertiesDialog)
        self.tab_widget.setObjectName(u"tab_widget")

        self.main_layout.addWidget(self.tab_widget)

        self.status_label = QLabel(DynamicBlockPropertiesDialog)
        self.status_label.setObjectName(u"status_label")
        self.status_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.status_label.setWordWrap(True)

        self.main_layout.addWidget(self.status_label)

        self.button_layout = QHBoxLayout()
        self.button_layout.setObjectName(u"button_layout")
        self.button_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.button_layout.addItem(self.button_spacer)

        self.apply_button = QPushButton(DynamicBlockPropertiesDialog)
        self.apply_button.setObjectName(u"apply_button")
        icon = QIcon()
        icon.addFile(u":/Icons/icons/accept.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.apply_button.setIcon(icon)

        self.button_layout.addWidget(self.apply_button)


        self.main_layout.addLayout(self.button_layout)


        self.retranslateUi(DynamicBlockPropertiesDialog)

        self.tab_widget.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(DynamicBlockPropertiesDialog)
    # setupUi

    def retranslateUi(self, DynamicBlockPropertiesDialog):
        DynamicBlockPropertiesDialog.setWindowTitle(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Block properties", None))
        self.status_label.setText("")
        self.apply_button.setText(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Apply changes", None))
    # retranslateUi
