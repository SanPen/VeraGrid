# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from PySide6 import QtCore, QtWidgets


class Ui_DynamicEventDialogue(object):
    """
    UI builder for the dynamic-events editor dialog.
    """

    def setupUi(self, dialog: QtWidgets.QDialog) -> None:
        """
        Create the static widget tree for the dialog.

        :param dialog: Target dialog instance.
        :return: None.
        """
        dialog.setObjectName("DynamicEventEditor")
        dialog.resize(720, 520)
        self.mainLayout = QtWidgets.QVBoxLayout(dialog)
        self.mainLayout.setObjectName("mainLayout")

        self.targetDeviceLabel = QtWidgets.QLabel(dialog)
        self.targetDeviceLabel.setObjectName("targetDeviceLabel")
        self.mainLayout.addWidget(self.targetDeviceLabel)

        self.eventsTableWidget = QtWidgets.QTableWidget(dialog)
        self.eventsTableWidget.setObjectName("eventsTableWidget")
        self.eventsTableWidget.setRowCount(0)
        self.eventsTableWidget.setColumnCount(0)
        self.eventsTableWidget.verticalHeader().setVisible(False)
        self.eventsTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.mainLayout.addWidget(self.eventsTableWidget)

        self.groupsLayout = QtWidgets.QHBoxLayout()
        self.groupsLayout.setObjectName("groupsLayout")
        spacer_item = QtWidgets.QSpacerItem(
            40,
            20,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self.groupsLayout.addItem(spacer_item)

        self.newGroupButton = QtWidgets.QPushButton(dialog)
        self.newGroupButton.setObjectName("newGroupButton")
        self.groupsLayout.addWidget(self.newGroupButton)
        self.mainLayout.addLayout(self.groupsLayout)

        self.tableButtonsLayout = QtWidgets.QHBoxLayout()
        self.tableButtonsLayout.setObjectName("tableButtonsLayout")

        self.addRowButton = QtWidgets.QPushButton(dialog)
        self.addRowButton.setObjectName("addRowButton")
        self.tableButtonsLayout.addWidget(self.addRowButton)

        self.removeRowButton = QtWidgets.QPushButton(dialog)
        self.removeRowButton.setObjectName("removeRowButton")
        self.tableButtonsLayout.addWidget(self.removeRowButton)

        self.mainLayout.addLayout(self.tableButtonsLayout)

        self.switchSequenceButton = QtWidgets.QPushButton(dialog)
        self.switchSequenceButton.setObjectName("switchSequenceButton")
        self.mainLayout.addWidget(self.switchSequenceButton)

        self.dialogButtonBox = QtWidgets.QDialogButtonBox(dialog)
        self.dialogButtonBox.setObjectName("dialogButtonBox")
        self.dialogButtonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self.mainLayout.addWidget(self.dialogButtonBox)

        self.retranslateUi(dialog)
        QtCore.QMetaObject.connectSlotsByName(dialog)

    def retranslateUi(self, dialog: QtWidgets.QDialog) -> None:
        """
        Apply translated texts to the dialog widgets.

        :param dialog: Target dialog instance.
        :return: None.
        """
        dialog.setWindowTitle(QtCore.QCoreApplication.translate("DynamicEventEditor", "Dynamic Event Editor"))
        self.targetDeviceLabel.setText(QtCore.QCoreApplication.translate("DynamicEventEditor", "<b>Target device:</b>"))
        self.newGroupButton.setText(QtCore.QCoreApplication.translate("DynamicEventEditor", "➕ New Event Group"))
        self.addRowButton.setText(QtCore.QCoreApplication.translate("DynamicEventEditor", "➕ Add New Event"))
        self.removeRowButton.setText(QtCore.QCoreApplication.translate("DynamicEventEditor", "❌ Remove Selected Rows"))
        self.switchSequenceButton.setText(QtCore.QCoreApplication.translate("DynamicEventEditor", "Switch Sequence Wizard"))
