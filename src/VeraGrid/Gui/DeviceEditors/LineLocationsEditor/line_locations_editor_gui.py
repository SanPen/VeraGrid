# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'line_locations_editor_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QPushButton,
    QSizePolicy, QSpacerItem, QTableView, QVBoxLayout,
    QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_LineLocationsEditorWidget(object):
    def setupUi(self, LineLocationsEditorWidget):
        if not LineLocationsEditorWidget.objectName():
            LineLocationsEditorWidget.setObjectName(u"LineLocationsEditorWidget")
        LineLocationsEditorWidget.resize(720, 420)
        self.mainLayout = QVBoxLayout(LineLocationsEditorWidget)
        self.mainLayout.setObjectName(u"mainLayout")
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.addButton = QPushButton(LineLocationsEditorWidget)
        self.addButton.setObjectName(u"addButton")
        icon = QIcon()
        icon.addFile(u":/Icons/icons/plus.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.addButton.setIcon(icon)

        self.buttonLayout.addWidget(self.addButton)

        self.removeButton = QPushButton(LineLocationsEditorWidget)
        self.removeButton.setObjectName(u"removeButton")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/delete3.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.removeButton.setIcon(icon1)

        self.buttonLayout.addWidget(self.removeButton)

        self.importButton = QPushButton(LineLocationsEditorWidget)
        self.importButton.setObjectName(u"importButton")
        icon2 = QIcon()
        icon2.addFile(u":/Icons/icons/load.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.importButton.setIcon(icon2)

        self.buttonLayout.addWidget(self.importButton)

        self.exportButton = QPushButton(LineLocationsEditorWidget)
        self.exportButton.setObjectName(u"exportButton")
        icon3 = QIcon()
        icon3.addFile(u":/Icons/icons/save.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.exportButton.setIcon(icon3)

        self.buttonLayout.addWidget(self.exportButton)

        self.copyButton = QPushButton(LineLocationsEditorWidget)
        self.copyButton.setObjectName(u"copyButton")
        icon4 = QIcon()
        icon4.addFile(u":/Icons/icons/copy.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.copyButton.setIcon(icon4)

        self.buttonLayout.addWidget(self.copyButton)

        self.pasteButton = QPushButton(LineLocationsEditorWidget)
        self.pasteButton.setObjectName(u"pasteButton")
        icon5 = QIcon()
        icon5.addFile(u":/Icons/icons/paste.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pasteButton.setIcon(icon5)

        self.buttonLayout.addWidget(self.pasteButton)

        self.buttonSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttonLayout.addItem(self.buttonSpacer)


        self.mainLayout.addLayout(self.buttonLayout)

        self.tableView = QTableView(LineLocationsEditorWidget)
        self.tableView.setObjectName(u"tableView")

        self.mainLayout.addWidget(self.tableView)


        self.retranslateUi(LineLocationsEditorWidget)

        QMetaObject.connectSlotsByName(LineLocationsEditorWidget)
    # setupUi

    def retranslateUi(self, LineLocationsEditorWidget):
#if QT_CONFIG(tooltip)
        self.addButton.setToolTip(QCoreApplication.translate("LineLocationsEditorWidget", u"Add point", None))
#endif // QT_CONFIG(tooltip)
        self.addButton.setText("")
#if QT_CONFIG(tooltip)
        self.removeButton.setToolTip(QCoreApplication.translate("LineLocationsEditorWidget", u"Remove selected", None))
#endif // QT_CONFIG(tooltip)
        self.removeButton.setText("")
#if QT_CONFIG(tooltip)
        self.importButton.setToolTip(QCoreApplication.translate("LineLocationsEditorWidget", u"Import CSV", None))
#endif // QT_CONFIG(tooltip)
        self.importButton.setText("")
#if QT_CONFIG(tooltip)
        self.exportButton.setToolTip(QCoreApplication.translate("LineLocationsEditorWidget", u"Export CSV", None))
#endif // QT_CONFIG(tooltip)
        self.exportButton.setText("")
#if QT_CONFIG(tooltip)
        self.copyButton.setToolTip(QCoreApplication.translate("LineLocationsEditorWidget", u"Copy", None))
#endif // QT_CONFIG(tooltip)
        self.copyButton.setText("")
#if QT_CONFIG(tooltip)
        self.pasteButton.setToolTip(QCoreApplication.translate("LineLocationsEditorWidget", u"Paste", None))
#endif // QT_CONFIG(tooltip)
        self.pasteButton.setText("")
        pass
    # retranslateUi

