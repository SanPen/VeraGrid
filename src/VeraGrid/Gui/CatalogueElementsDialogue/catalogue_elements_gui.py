# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'catalogue_elements_gui.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QDialog, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QTreeView, QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_CatalogueElementsDialog(object):
    def setupUi(self, CatalogueElementsDialog):
        if not CatalogueElementsDialog.objectName():
            CatalogueElementsDialog.setObjectName(u"CatalogueElementsDialog")
        CatalogueElementsDialog.resize(541, 385)
        self.verticalLayout = QVBoxLayout(CatalogueElementsDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.titleLabel = QLabel(CatalogueElementsDialog)
        self.titleLabel.setObjectName(u"titleLabel")

        self.verticalLayout.addWidget(self.titleLabel)

        self.treeView = QTreeView(CatalogueElementsDialog)
        self.treeView.setObjectName(u"treeView")
        self.treeView.setAlternatingRowColors(True)
        self.treeView.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.treeView.setUniformRowHeights(True)
        self.treeView.setItemsExpandable(True)
        self.treeView.setSortingEnabled(False)

        self.verticalLayout.addWidget(self.treeView)

        self.toolsLayout = QHBoxLayout()
        self.toolsLayout.setObjectName(u"toolsLayout")
        self.selectAllButton = QPushButton(CatalogueElementsDialog)
        self.selectAllButton.setObjectName(u"selectAllButton")
        icon = QIcon()
        icon.addFile(u":/Icons/icons/check_all.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.selectAllButton.setIcon(icon)

        self.toolsLayout.addWidget(self.selectAllButton)

        self.selectNoneButton = QPushButton(CatalogueElementsDialog)
        self.selectNoneButton.setObjectName(u"selectNoneButton")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/uncheck_all.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.selectNoneButton.setIcon(icon1)

        self.toolsLayout.addWidget(self.selectNoneButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.toolsLayout.addItem(self.horizontalSpacer)

        self.acceptButton = QPushButton(CatalogueElementsDialog)
        self.acceptButton.setObjectName(u"acceptButton")
        icon2 = QIcon()
        icon2.addFile(u":/Icons/icons/accept.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.acceptButton.setIcon(icon2)

        self.toolsLayout.addWidget(self.acceptButton)


        self.verticalLayout.addLayout(self.toolsLayout)


        self.retranslateUi(CatalogueElementsDialog)

        QMetaObject.connectSlotsByName(CatalogueElementsDialog)
    # setupUi

    def retranslateUi(self, CatalogueElementsDialog):
        CatalogueElementsDialog.setWindowTitle(QCoreApplication.translate("CatalogueElementsDialog", u"Add catalogue elements", None))
        self.titleLabel.setText(QCoreApplication.translate("CatalogueElementsDialog", u"Select the catalogue elements to add", None))
#if QT_CONFIG(tooltip)
        self.selectAllButton.setToolTip(QCoreApplication.translate("CatalogueElementsDialog", u"Select all", None))
#endif // QT_CONFIG(tooltip)
        self.selectAllButton.setText("")
#if QT_CONFIG(tooltip)
        self.selectNoneButton.setToolTip(QCoreApplication.translate("CatalogueElementsDialog", u"Select none", None))
#endif // QT_CONFIG(tooltip)
        self.selectNoneButton.setText("")
#if QT_CONFIG(tooltip)
        self.acceptButton.setToolTip(QCoreApplication.translate("CatalogueElementsDialog", u"Import selected models", None))
#endif // QT_CONFIG(tooltip)
        self.acceptButton.setText(QCoreApplication.translate("CatalogueElementsDialog", u"Import models", None))
    # retranslateUi

