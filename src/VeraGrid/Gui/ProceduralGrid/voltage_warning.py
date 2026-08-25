# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import List, Tuple
from PySide6 import QtWidgets
from VeraGrid.Gui.ProceduralGrid.voltage_warning_ui import Ui_Dialog


class VoltageWarningDialog(QtWidgets.QDialog):
    """
    Warning dialog shown when selected substations have voltage levels
    not present in the existing grid.
    """

    def __init__(self, offenders: List[Tuple[str, float]], valid_voltages: List[float], parent=None):
        """
        :param offenders: List of (substation_name, invalid_voltage) pairs
        :param valid_voltages: Sorted list of valid voltages from the existing grid
        """
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr('Invalid Voltage Levels'))

        offenders_text = "\n".join(f"  • {name}: {v} kV" for name, v in offenders)
        self.ui.offendersLabel.setText(offenders_text)

        valid_str = ", ".join(f"{v} kV" for v in valid_voltages)
        self.ui.validVoltagesLabel.setText(f"Please change them to one of the existing voltages: {valid_str}")

        self.ui.okButton.clicked.connect(self.accept)
