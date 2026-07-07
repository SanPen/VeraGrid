# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from PySide6 import QtWidgets
from VeraGrid.Gui.ShortCircuitEditor.short_circuit_selector_gui import Ui_ShortCircuitSelectorDialog
from VeraGridEngine.enumerations import FaultType, MethodShortCircuit, PhasesShortCircuit


def valid_methods_for_fault(fault: FaultType):
    """
    :param fault:
    :return:
    """
    # all other faults allow both
    return list(MethodShortCircuit)


def valid_phases_for_fault(fault: FaultType):
    """

    :param fault:
    :return:
    """
    if fault in (FaultType.LLLG, FaultType.LLL):
        return [PhasesShortCircuit.abc]

    if fault == FaultType.LG:
        return [PhasesShortCircuit.a, PhasesShortCircuit.b, PhasesShortCircuit.c]

    if fault in (FaultType.LL, FaultType.LLG):
        return [PhasesShortCircuit.ab, PhasesShortCircuit.bc, PhasesShortCircuit.ca]

    return []


class ShortCircuitSelector(QtWidgets.QDialog):
    """
    GridMergeDialogue
    """

    def __init__(self):
        """
        GridMergeDialogue
        :param App: App pointer
        """
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_ShortCircuitSelectorDialog()
        self.ui.setupUi(self)
        self.setWindowTitle('Short Circuit Configuration')
        self.setModal(True)

        # self.app = app

        self.fault_info_dict = {
            "Custom": {
                "R_ohm": 0.01,
                "X_ohm": 0.00,
                "description": "Typical value",
            },
            "Solid 3ph fault": {
                "R_ohm": 0.01,
                "X_ohm": 0.00,
                "description": "Near-bolted three-phase fault",
            },
            "Solid phase ground fault": {
                "R_ohm": 0.01,
                "X_ohm": 0.00,
                "description": "Near-bolted phase-to-ground fault",
            },
            "Metallic conductor conductor contact": {
                "R_ohm": 0.02,
                "X_ohm": 0.01,
                "description": "Low-impedance metallic conductor-to-conductor short",
            },
            "Excavator touching underground cable": {
                "R_ohm": 0.05,
                "X_ohm": 0.01,
                "description": "Direct mechanical strike on underground cable",
            },
            "Excavator damaging cable partial arc": {
                "R_ohm": 0.50,
                "X_ohm": 0.05,
                "description": "Cable damage with partial contact and arcing",
            },
            "Crane or machinery overhead arc": {
                "R_ohm": 10.0,
                "X_ohm": 0.00,
                "description": "Arc from machinery approaching overhead line",
            },
            "Tree branch touching overhead line": {
                "R_ohm": 500.0,
                "X_ohm": 0.00,
                "description": "Typical vegetation high-impedance fault",
            },
            "Wet tree or wet vegetation contact": {
                "R_ohm": 200.0,
                "X_ohm": 0.00,
                "description": "Vegetation contact with lower resistance due to moisture",
            },
            "Dry tree or dry branch contact": {
                "R_ohm": 1000.0,
                "X_ohm": 0.00,
                "description": "Dry vegetation high-impedance fault",
            },
            "Downed conductor on wet soil": {
                "R_ohm": 100.0,
                "X_ohm": 0.00,
                "description": "Downed conductor on relatively conductive ground",
            },
            "Downed conductor on gravel": {
                "R_ohm": 500.0,
                "X_ohm": 0.00,
                "description": "Downed conductor on gravel or ballast",
            },
            "Downed conductor on asphalt or concrete": {
                "R_ohm": 2000.0,
                "X_ohm": 0.00,
                "description": "Downed conductor on poorly conductive surface",
            },
            "Insulator contamination or leakage fault": {
                "R_ohm": 300.0,
                "X_ohm": 0.00,
                "description": "Leakage-type high-impedance fault",
            },
            "Generic arcing phase ground fault": {
                "R_ohm": 5.0,
                "X_ohm": 0.00,
                "description": "Simple resistive arc approximation",
            },
            "Severe high resistance transmission fault": {
                "R_ohm": 300.0,
                "X_ohm": 0.00,
                "description": "High-resistance EHV fault scenario",
            },
        }

        self.ui.cb_fault.addItems([e.value for e in FaultType])
        self.ui.cb_method.addItems([e.value for e in MethodShortCircuit])
        self.ui.cb_phases.addItems([e.value for e in PhasesShortCircuit])
        self.ui.cb_type.addItems([k for k, _ in self.fault_info_dict.items()])

        self.update_logic()
        self.fault = FaultType(self.ui.cb_fault.currentText())
        self.method = MethodShortCircuit(self.ui.cb_method.currentText())
        self.phases = PhasesShortCircuit(self.ui.cb_phases.currentText())
        self.r_ohm = self.ui.r_doubleSpinBox.value()
        self.x_ohm = self.ui.x_doubleSpinBox.value()
        self.was_accepted = False

        self.ui.btn_accept.clicked.connect(self.accept_clicked)
        self.ui.cb_method.currentTextChanged.connect(self.update_view)
        self.ui.cb_fault.currentIndexChanged.connect(self.update_logic)
        self.ui.cb_type.currentIndexChanged.connect(self.update_r_x)

    def update_view(self):
        """

        :return:
        """

        fault = FaultType(self.ui.cb_fault.currentText())

        # -------- UPDATE PHASES --------
        if self.ui.cb_method.currentText() == MethodShortCircuit.sequences.value:
            self.ui.cb_phases.setVisible(False)
            self.ui.phases_label.setVisible(False)
        else:
            self.ui.cb_phases.setVisible(True)
            self.ui.phases_label.setVisible(True)
            allowed_phases = valid_phases_for_fault(fault)
            current_phase = self.ui.cb_phases.currentText()

            self.ui.cb_phases.clear()
            for p in allowed_phases:
                self.ui.cb_phases.addItem(p.value)

            if current_phase in [p.value for p in allowed_phases]:
                self.ui.cb_phases.setCurrentText(current_phase)

    def update_logic(self):
        """Update available method and phase options based on the fault type."""

        fault = FaultType(self.ui.cb_fault.currentText())

        # -------- UPDATE METHOD --------
        allowed_methods = valid_methods_for_fault(fault)
        current_method = self.ui.cb_method.currentText()

        self.ui.cb_method.clear()
        for m in allowed_methods:
            self.ui.cb_method.addItem(m.value)

        if current_method in [m.value for m in allowed_methods]:
            self.ui.cb_method.setCurrentText(current_method)

        # -------- UPDATE PHASES --------
        if current_method == MethodShortCircuit.sequences.value:
            self.ui.cb_phases.setVisible(False)
            self.ui.phases_label.setVisible(False)
        else:
            self.ui.cb_phases.setVisible(True)
            self.ui.phases_label.setVisible(True)
            allowed_phases = valid_phases_for_fault(fault)
            current_phase = self.ui.cb_phases.currentText()

            self.ui.cb_phases.clear()
            for p in allowed_phases:
                self.ui.cb_phases.addItem(p.value)

            if current_phase in [p.value for p in allowed_phases]:
                self.ui.cb_phases.setCurrentText(current_phase)

        self.fault = FaultType(self.ui.cb_fault.currentText())
        self.method = MethodShortCircuit(self.ui.cb_method.currentText())
        self.phases = PhasesShortCircuit(self.ui.cb_phases.currentText())

    def get_selection(self):
        """Return the selected configuration as enums."""
        return (
            FaultType(self.ui.cb_fault.currentText()),
            MethodShortCircuit(self.ui.cb_method.currentText()),
            PhasesShortCircuit(self.ui.cb_phases.currentText()),
        )

    def update_r_x(self):
        """

        :return:
        """
        sel = self.ui.cb_type.currentText()

        data = self.fault_info_dict.get(sel, None)

        if data is not None:
            self.ui.r_doubleSpinBox.setValue(data["R_ohm"])
            self.ui.x_doubleSpinBox.setValue(data["X_ohm"])
            self.ui.typeLabel.setText(data["description"])
        else:
            self.ui.r_doubleSpinBox.setValue(0)
            self.ui.x_doubleSpinBox.setValue(0)
            self.ui.typeLabel.setText("")

    def get_impedance_pu(self, Sbase: float, Vbase: float) -> complex:
        """
        Get the per-unit impedance
        :param Sbase: Base power (MVA)
        :param Vbase: Base voltage (kV)
        :return: per unit fault impedance
        """
        z_ohm = complex(self.r_ohm, self.x_ohm)
        z_base = (Vbase * Vbase) / Sbase
        z_pu = z_ohm / z_base

        return z_pu

    def accept_clicked(self):
        """Check if values are valid and close dialog."""
        self.fault = FaultType(self.ui.cb_fault.currentText())
        self.method = MethodShortCircuit(self.ui.cb_method.currentText())
        self.phases = PhasesShortCircuit(self.ui.cb_phases.currentText())
        self.r_ohm = self.ui.r_doubleSpinBox.value()
        self.x_ohm = self.ui.x_doubleSpinBox.value()
        self.was_accepted = True
        self.close()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = ShortCircuitSelector()
    w.show()
    sys.exit(app.exec())