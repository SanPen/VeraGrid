# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dynamic_editor_picker_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QComboBox,
    QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

class Ui_DynamicEditorPickerDialog(object):
    def setupUi(self, DynamicEditorPickerDialog):
        if not DynamicEditorPickerDialog.objectName():
            DynamicEditorPickerDialog.setObjectName(u"DynamicEditorPickerDialog")
        DynamicEditorPickerDialog.resize(720, 520)
        self.verticalLayout = QVBoxLayout(DynamicEditorPickerDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(12, 12, 12, 12)
        self.quickOpenGroupBox = QGroupBox(DynamicEditorPickerDialog)
        self.quickOpenGroupBox.setObjectName(u"quickOpenGroupBox")
        self.horizontalLayoutQuick = QHBoxLayout(self.quickOpenGroupBox)
        self.horizontalLayoutQuick.setObjectName(u"horizontalLayoutQuick")
        self.quickOpenLabel = QLabel(self.quickOpenGroupBox)
        self.quickOpenLabel.setObjectName(u"quickOpenLabel")
        self.quickOpenLabel.setWordWrap(True)

        self.horizontalLayoutQuick.addWidget(self.quickOpenLabel)

        self.quickOpenButton = QPushButton(self.quickOpenGroupBox)
        self.quickOpenButton.setObjectName(u"quickOpenButton")

        self.horizontalLayoutQuick.addWidget(self.quickOpenButton)


        self.verticalLayout.addWidget(self.quickOpenGroupBox)

        self.searchLineEdit = QLineEdit(DynamicEditorPickerDialog)
        self.searchLineEdit.setObjectName(u"searchLineEdit")
        self.searchLineEdit.setClearButtonEnabled(True)

        self.verticalLayout.addWidget(self.searchLineEdit)

        self.entriesTableWidget = QTableWidget(DynamicEditorPickerDialog)
        if (self.entriesTableWidget.columnCount() < 3):
            self.entriesTableWidget.setColumnCount(3)
        __qtablewidgetitem = QTableWidgetItem()
        self.entriesTableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.entriesTableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.entriesTableWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        self.entriesTableWidget.setObjectName(u"entriesTableWidget")
        self.entriesTableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.entriesTableWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.entriesTableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.verticalLayout.addWidget(self.entriesTableWidget)

        self.horizontalLayoutMode = QHBoxLayout()
        self.horizontalLayoutMode.setObjectName(u"horizontalLayoutMode")
        self.modeLabel = QLabel(DynamicEditorPickerDialog)
        self.modeLabel.setObjectName(u"modeLabel")

        self.horizontalLayoutMode.addWidget(self.modeLabel)

        self.modeComboBox = QComboBox(DynamicEditorPickerDialog)
        self.modeComboBox.setObjectName(u"modeComboBox")

        self.horizontalLayoutMode.addWidget(self.modeComboBox)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutMode.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayoutMode)

        self.buttonBox = QDialogButtonBox(DynamicEditorPickerDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Open)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(DynamicEditorPickerDialog)

        QMetaObject.connectSlotsByName(DynamicEditorPickerDialog)
    # setupUi

    def retranslateUi(self, DynamicEditorPickerDialog):
        DynamicEditorPickerDialog.setWindowTitle(QCoreApplication.translate("DynamicEditorPickerDialog", u"Open Dynamic Editor", None))
        self.quickOpenGroupBox.setTitle(QCoreApplication.translate("DynamicEditorPickerDialog", u"Quick Open", None))
        self.quickOpenLabel.setText(QCoreApplication.translate("DynamicEditorPickerDialog", u"Open the current block in the other mode.", None))
        self.quickOpenButton.setText(QCoreApplication.translate("DynamicEditorPickerDialog", u"Open", None))
        self.searchLineEdit.setPlaceholderText(QCoreApplication.translate("DynamicEditorPickerDialog", u"Search dynamic editors", None))
        ___qtablewidgetitem = self.entriesTableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("DynamicEditorPickerDialog", u"Name", None))
        ___qtablewidgetitem1 = self.entriesTableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("DynamicEditorPickerDialog", u"Type", None))
        ___qtablewidgetitem2 = self.entriesTableWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("DynamicEditorPickerDialog", u"Modes", None))
        self.modeLabel.setText(QCoreApplication.translate("DynamicEditorPickerDialog", u"Mode", None))
    # retranslateUi

