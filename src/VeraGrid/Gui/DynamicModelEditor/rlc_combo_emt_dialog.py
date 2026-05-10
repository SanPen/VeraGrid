# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from PySide6 import QtWidgets

from VeraGridEngine.enumerations import ShuntConnectionType


class RlcComboEmtDialog(QtWidgets.QDialog):
    """
    Modal dialog used to configure the first combined EMT RLC shunt block.
    """

    __slots__ = (
        "phase_a_check",
        "phase_b_check",
        "phase_c_check",
        "include_r_check",
        "include_l_check",
        "include_c_check",
        "connection_combo",
        "connection_help_label",
        "input_mode_combo",
        "resistance_spin",
        "inductive_value_label",
        "inductive_value_spin",
        "capacitive_value_label",
        "capacitive_value_spin",
        "base_info_label",
    )

    def __init__(self,
                 parent: QtWidgets.QWidget | None = None,
                 initial_config: dict[str, object] | None = None,
                 nominal_voltage_kv: float | None = None,
                 base_power_mva: float | None = None,
                 base_frequency_hz: float | None = None) -> None:
        """
        Build the RLC combo configuration dialog.

        :param parent: Optional Qt parent.
        :param initial_config: Optional persisted modal configuration.
        :return: None.
        """
        super().__init__(parent)
        self.setWindowTitle("Configure EMT RLC Combo")
        self.resize(420, 300)

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        form_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout()
        main_layout.addLayout(form_layout)

        component_widget = QtWidgets.QWidget(self)
        component_layout = QtWidgets.QHBoxLayout(component_widget)
        component_layout.setContentsMargins(0, 0, 0, 0)
        self.include_r_check = QtWidgets.QCheckBox("R", component_widget)
        self.include_l_check = QtWidgets.QCheckBox("L", component_widget)
        self.include_c_check = QtWidgets.QCheckBox("C", component_widget)
        self.include_r_check.setChecked(True)
        component_layout.addWidget(self.include_r_check)
        component_layout.addWidget(self.include_l_check)
        component_layout.addWidget(self.include_c_check)
        component_layout.addStretch()
        form_layout.addRow("Components", component_widget)

        phase_widget = QtWidgets.QWidget(self)
        phase_layout = QtWidgets.QHBoxLayout(phase_widget)
        phase_layout.setContentsMargins(0, 0, 0, 0)
        self.phase_a_check = QtWidgets.QCheckBox("A", phase_widget)
        self.phase_b_check = QtWidgets.QCheckBox("B", phase_widget)
        self.phase_c_check = QtWidgets.QCheckBox("C", phase_widget)
        self.phase_a_check.setChecked(True)
        self.phase_b_check.setChecked(True)
        self.phase_c_check.setChecked(True)
        phase_layout.addWidget(self.phase_a_check)
        phase_layout.addWidget(self.phase_b_check)
        phase_layout.addWidget(self.phase_c_check)
        phase_layout.addStretch()
        form_layout.addRow("Phases", phase_widget)

        self.connection_combo = QtWidgets.QComboBox(self)
        self.connection_combo.addItem("Grounded Star (Yg)", ShuntConnectionType.GroundedStar)
        self.connection_combo.addItem("Neutral Star (Yn)", ShuntConnectionType.NeutralStar)
        self.connection_combo.addItem("Floating Star (Y)", ShuntConnectionType.FloatingStar)
        self.connection_combo.addItem("Delta", ShuntConnectionType.Delta)
        form_layout.addRow("Connection", self.connection_combo)

        self.input_mode_combo = QtWidgets.QComboBox(self)
        self.input_mode_combo.addItem("Physical R/L/C", "physical")
        self.input_mode_combo.addItem("R + Reactances", "reactance")
        form_layout.addRow("Input Mode", self.input_mode_combo)

        self.resistance_spin = QtWidgets.QDoubleSpinBox(self)
        self.resistance_spin.setDecimals(8)
        self.resistance_spin.setRange(0.0, 1.0e12)
        self.resistance_spin.setValue(1.0)
        self.resistance_spin.setSuffix(" ohm")
        form_layout.addRow("Resistance", self.resistance_spin)

        self.inductive_value_label = QtWidgets.QLabel("Inductance", self)
        self.inductive_value_spin = QtWidgets.QDoubleSpinBox(self)
        self.inductive_value_spin.setDecimals(10)
        self.inductive_value_spin.setRange(0.0, 1.0e12)
        self.inductive_value_spin.setValue(0.01)
        form_layout.addRow(self.inductive_value_label, self.inductive_value_spin)

        self.capacitive_value_label = QtWidgets.QLabel("Capacitance", self)
        self.capacitive_value_spin = QtWidgets.QDoubleSpinBox(self)
        self.capacitive_value_spin.setDecimals(12)
        self.capacitive_value_spin.setRange(0.0, 1.0e12)
        self.capacitive_value_spin.setValue(1.0e-6)
        form_layout.addRow(self.capacitive_value_label, self.capacitive_value_spin)

        self.connection_help_label = QtWidgets.QLabel(self)
        self.connection_help_label.setWordWrap(True)
        self.connection_help_label.setText(
            "Star variants expose neutral/ground explicitly. Delta is available in the direct-value EMT workflow."
        )
        main_layout.addWidget(self.connection_help_label)

        self.base_info_label = QtWidgets.QLabel(self)
        self.base_info_label.setWordWrap(True)
        if nominal_voltage_kv is not None and base_power_mva is not None and base_frequency_hz is not None:
            self.base_info_label.setText(
                f"Base conversion uses Vnom={float(nominal_voltage_kv):.4f} kV, Sbase={float(base_power_mva):.4f} MVA, fbase={float(base_frequency_hz):.4f} Hz."
            )
        else:
            self.base_info_label.setText(
                "Base conversion uses fallback values because the host device base information is not available."
            )
        main_layout.addWidget(self.base_info_label)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self.include_r_check.toggled.connect(self.update_parameter_widgets)
        self.include_l_check.toggled.connect(self.update_parameter_widgets)
        self.include_c_check.toggled.connect(self.update_parameter_widgets)
        self.input_mode_combo.currentIndexChanged.connect(self.update_parameter_widgets)

        self.update_parameter_widgets()

        if initial_config is not None:
            self.apply_initial_configuration(initial_config)
        else:
            pass

    def update_parameter_widgets(self) -> None:
        """
        Refresh labels and enabled states for the electrical parameter inputs.

        :return: None.
        """
        physical_mode: bool = self.input_mode_combo.currentData() == "physical"
        self.inductive_value_label.setText("Inductance" if physical_mode else "Inductive Reactance")
        self.capacitive_value_label.setText("Capacitance" if physical_mode else "Capacitive Reactance")
        self.inductive_value_spin.setSuffix(" H" if physical_mode else " ohm")
        self.capacitive_value_spin.setSuffix(" F" if physical_mode else " ohm")
        self.resistance_spin.setEnabled(self.include_r_check.isChecked())
        self.inductive_value_spin.setEnabled(self.include_l_check.isChecked())
        self.capacitive_value_spin.setEnabled(self.include_c_check.isChecked())

    def accept_dialog(self) -> None:
        """
        Validate the modal state before accepting.

        :return: None.
        """
        if self.include_r_check.isChecked() or self.include_l_check.isChecked() or self.include_c_check.isChecked():
            pass
        else:
            QtWidgets.QMessageBox.warning(self, "RLC Combo", "Enable at least one component (R, L, or C).")
            return

        if self.phase_a_check.isChecked() or self.phase_b_check.isChecked() or self.phase_c_check.isChecked():
            pass
        else:
            QtWidgets.QMessageBox.warning(self, "RLC Combo", "Enable at least one phase.")
            return

        if self.include_r_check.isChecked() and self.resistance_spin.value() <= 0.0:
            QtWidgets.QMessageBox.warning(self, "RLC Combo", "Resistance must be greater than zero.")
            return
        else:
            pass

        if self.include_l_check.isChecked() and self.inductive_value_spin.value() <= 0.0:
            label: str = "Inductive reactance" if self.input_mode_combo.currentData() == "reactance" else "Inductance"
            QtWidgets.QMessageBox.warning(self, "RLC Combo", f"{label} must be greater than zero.")
            return
        else:
            pass

        if self.include_c_check.isChecked() and self.capacitive_value_spin.value() <= 0.0:
            label = "Capacitive reactance" if self.input_mode_combo.currentData() == "reactance" else "Capacitance"
            QtWidgets.QMessageBox.warning(self, "RLC Combo", f"{label} must be greater than zero.")
            return
        else:
            pass

        self.accept()

    def get_configuration(self) -> dict[str, object]:
        """
        Return the current modal configuration.

        :return: Configuration dictionary.
        """
        return dict({
            "include_r": self.include_r_check.isChecked(),
            "include_l": self.include_l_check.isChecked(),
            "include_c": self.include_c_check.isChecked(),
            "phA": self.phase_a_check.isChecked(),
            "phB": self.phase_b_check.isChecked(),
            "phC": self.phase_c_check.isChecked(),
            "connection_type": self.connection_combo.currentData(),
            "input_mode": self.input_mode_combo.currentData(),
            "resistance_ohm": float(self.resistance_spin.value()),
            "inductive_value": float(self.inductive_value_spin.value()),
            "capacitive_value": float(self.capacitive_value_spin.value()),
        })

    def apply_initial_configuration(self, config: dict[str, object]) -> None:
        """
        Load one persisted configuration into the dialog widgets.

        :param config: Persisted configuration.
        :return: None.
        """
        self.include_r_check.setChecked(bool(config.get("include_r", True)))
        self.include_l_check.setChecked(bool(config.get("include_l", False)))
        self.include_c_check.setChecked(bool(config.get("include_c", False)))
        self.phase_a_check.setChecked(bool(config.get("phA", True)))
        self.phase_b_check.setChecked(bool(config.get("phB", True)))
        self.phase_c_check.setChecked(bool(config.get("phC", True)))

        input_mode = config.get("input_mode", "physical")
        index = self.input_mode_combo.findData(input_mode)
        if index >= 0:
            self.input_mode_combo.setCurrentIndex(index)
        else:
            pass

        connection_type = config.get("connection_type", ShuntConnectionType.GroundedStar)
        index = self.connection_combo.findData(connection_type)
        if index >= 0:
            self.connection_combo.setCurrentIndex(index)
        else:
            pass

        self.resistance_spin.setValue(float(config.get("resistance_ohm", 1.0)))
        self.inductive_value_spin.setValue(float(config.get("inductive_value", 0.01)))
        self.capacitive_value_spin.setValue(float(config.get("capacitive_value", 1.0e-6)))
        self.update_parameter_widgets()
