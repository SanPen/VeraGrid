# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDialogButtonBox)
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Substation.substation import Substation


class BusSelectorDialogue(QDialog):
    """
    NewMapLineDialogue
    """
    def __init__(self, grid: MultiCircuit, se: Substation, parent=None):
        """
        Constructor
        :param grid: MultiCircuit
        :param se: Substation
        :param parent: ?
        """
        QDialog.__init__(self, parent)
        self.setWindowTitle("Bus selection")

        # Create layout
        main_layout = QVBoxLayout()

        # Create horizontal layout for labels and combo-boxes
        combo_layout = QHBoxLayout()

        self.buses = grid.get_substation_buses(substation=se)
        self._is_valid = len(self.buses) > 0

        # Create labels and combo-boxes
        label1 = QLabel(se.name)
        self.combo_box = QComboBox()
        self.combo_box.addItems([bus.name for bus in self.buses])
        if len(self.buses) > 0:
            self.combo_box.setCurrentIndex(0)

        # Create vertical layout for first label and combobox
        vbox1 = QVBoxLayout()
        vbox1.addWidget(label1)
        vbox1.addWidget(self.combo_box)

        # Add vertical layouts to horizontal layout
        combo_layout.addLayout(vbox1)

        # Add horizontal layout to main layout
        main_layout.addLayout(combo_layout)

        # Create and add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Align the button box to the bottom-right
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(button_box)

        # Add button layout to main layout
        main_layout.addLayout(button_layout)

        # Set main layout
        self.setLayout(main_layout)

    def is_valid(self):
        """

        :return:
        """
        return self._is_valid

    def bus(self):
        """

        :return:
        """
        idx = self.combo_box.currentIndex()
        if idx > -1:
            return self.buses[idx]
        else:
            return None

    def accept(self):
        """
        accept
        """
        super().accept()

    def reject(self):
        """
        reject
        """
        self._is_valid = False
        super().reject()