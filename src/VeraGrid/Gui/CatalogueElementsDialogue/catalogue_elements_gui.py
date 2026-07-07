# -*- coding: utf-8 -*-
#
# Form generated from reading UI file 'catalogue_elements_gui.ui'
#
# This file is intentionally checked-in to keep UI compilation out of the runtime path.

from PySide6.QtCore import QCoreApplication, QMetaObject, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QTreeView,
    QVBoxLayout,
)


class Ui_CatalogueElementsDialog(object):
    """
    UI definition for the catalogue elements selection dialog.
    """

    def setupUi(self, CatalogueElementsDialog: QDialog) -> None:
        """
        Setup the UI.

        :param CatalogueElementsDialog: QDialog instance where the UI is installed.
        :return: None
        """
        if not CatalogueElementsDialog.objectName():
            CatalogueElementsDialog.setObjectName("CatalogueElementsDialog")
        else:
            # Explicit else per project coding rules.
            pass

        CatalogueElementsDialog.resize(760, 520)

        self.verticalLayout = QVBoxLayout(CatalogueElementsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)

        self.titleLabel = QLabel(CatalogueElementsDialog)
        self.titleLabel.setObjectName("titleLabel")
        self.verticalLayout.addWidget(self.titleLabel)

        self.treeView = QTreeView(CatalogueElementsDialog)
        self.treeView.setObjectName("treeView")
        self.treeView.setAlternatingRowColors(True)
        self.treeView.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.treeView.setUniformRowHeights(True)
        self.treeView.setSortingEnabled(False)
        self.verticalLayout.addWidget(self.treeView)

        self.toolsLayout = QHBoxLayout()
        self.toolsLayout.setObjectName("toolsLayout")

        self.selectAllButton = QPushButton(CatalogueElementsDialog)
        self.selectAllButton.setObjectName("selectAllButton")
        self.toolsLayout.addWidget(self.selectAllButton)

        self.selectNoneButton = QPushButton(CatalogueElementsDialog)
        self.selectNoneButton.setObjectName("selectNoneButton")
        self.toolsLayout.addWidget(self.selectNoneButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.toolsLayout.addItem(self.horizontalSpacer)

        self.verticalLayout.addLayout(self.toolsLayout)

        self.buttonBox = QDialogButtonBox(CatalogueElementsDialog)
        self.buttonBox.setObjectName("buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CatalogueElementsDialog)
        QMetaObject.connectSlotsByName(CatalogueElementsDialog)

    def retranslateUi(self, CatalogueElementsDialog: QDialog) -> None:
        """
        Set translated strings.

        :param CatalogueElementsDialog: QDialog instance.
        :return: None
        """
        CatalogueElementsDialog.setWindowTitle(
            QCoreApplication.translate("CatalogueElementsDialog", "Add catalogue elements", None)
        )
        self.titleLabel.setText(
            QCoreApplication.translate("CatalogueElementsDialog", "Select the catalogue elements to add", None)
        )
        self.selectAllButton.setText(QCoreApplication.translate("CatalogueElementsDialog", "Select all", None))
        self.selectNoneButton.setText(QCoreApplication.translate("CatalogueElementsDialog", "Select none", None))

