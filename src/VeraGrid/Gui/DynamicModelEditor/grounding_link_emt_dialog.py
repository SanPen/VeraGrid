from __future__ import annotations

from PySide6 import QtWidgets


class GroundingLinkEmtDialog(QtWidgets.QDialog):
    """
    Modal dialog used to configure one EMT neutral-to-ground link block.
    """

    __slots__ = (
        "solid_connection_check",
        "include_r_check",
        "include_l_check",
        "include_c_check",
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
        Build the grounding-link configuration dialog.

        :param parent: Optional Qt parent.
        :param initial_config: Optional persisted modal configuration.
        :return: None.
        """
        super().__init__(parent)
        self.setWindowTitle("Configure EMT Grounding Link")
        self.resize(420, 260)

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        form_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout()
        main_layout.addLayout(form_layout)

        self.solid_connection_check = QtWidgets.QCheckBox("Solid bond to ground", self)
        form_layout.addRow("Connection", self.solid_connection_check)

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

        self.solid_connection_check.toggled.connect(self.update_parameter_widgets)
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
        solid_connection: bool = self.solid_connection_check.isChecked()
        self.inductive_value_label.setText("Inductance" if physical_mode else "Inductive Reactance")
        self.capacitive_value_label.setText("Capacitance" if physical_mode else "Capacitive Reactance")
        self.inductive_value_spin.setSuffix(" H" if physical_mode else " ohm")
        self.capacitive_value_spin.setSuffix(" F" if physical_mode else " ohm")
        self.include_r_check.setEnabled(not solid_connection)
        self.include_l_check.setEnabled(not solid_connection)
        self.include_c_check.setEnabled(not solid_connection)
        self.input_mode_combo.setEnabled(not solid_connection)
        self.resistance_spin.setEnabled((not solid_connection) and self.include_r_check.isChecked())
        self.inductive_value_spin.setEnabled((not solid_connection) and self.include_l_check.isChecked())
        self.capacitive_value_spin.setEnabled((not solid_connection) and self.include_c_check.isChecked())

    def accept_dialog(self) -> None:
        """
        Validate the modal state before accepting.

        :return: None.
        """
        if self.solid_connection_check.isChecked():
            self.accept()
            return
        elif self.include_r_check.isChecked() or self.include_l_check.isChecked() or self.include_c_check.isChecked():
            pass
        else:
            QtWidgets.QMessageBox.warning(self, "Grounding Link", "Enable at least one component (R, L, or C).")
            return

        if self.include_r_check.isChecked() and self.resistance_spin.value() <= 0.0:
            QtWidgets.QMessageBox.warning(self, "Grounding Link", "Resistance must be greater than zero.")
            return
        else:
            pass

        if self.include_l_check.isChecked() and self.inductive_value_spin.value() <= 0.0:
            label: str = "Inductive reactance" if self.input_mode_combo.currentData() == "reactance" else "Inductance"
            QtWidgets.QMessageBox.warning(self, "Grounding Link", f"{label} must be greater than zero.")
            return
        else:
            pass

        if self.include_c_check.isChecked() and self.capacitive_value_spin.value() <= 0.0:
            label = "Capacitive reactance" if self.input_mode_combo.currentData() == "reactance" else "Capacitance"
            QtWidgets.QMessageBox.warning(self, "Grounding Link", f"{label} must be greater than zero.")
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
            "solid_connection": self.solid_connection_check.isChecked(),
            "include_r": self.include_r_check.isChecked(),
            "include_l": self.include_l_check.isChecked(),
            "include_c": self.include_c_check.isChecked(),
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
        self.solid_connection_check.setChecked(bool(config.get("solid_connection", False)))
        self.include_r_check.setChecked(bool(config.get("include_r", True)))
        self.include_l_check.setChecked(bool(config.get("include_l", False)))
        self.include_c_check.setChecked(bool(config.get("include_c", False)))

        input_mode = config.get("input_mode", "physical")
        index = self.input_mode_combo.findData(input_mode)
        if index >= 0:
            self.input_mode_combo.setCurrentIndex(index)
        else:
            pass

        self.resistance_spin.setValue(float(config.get("resistance_ohm", 1.0)))
        self.inductive_value_spin.setValue(float(config.get("inductive_value", 0.01)))
        self.capacitive_value_spin.setValue(float(config.get("capacitive_value", 1.0e-6)))
        self.update_parameter_widgets()
