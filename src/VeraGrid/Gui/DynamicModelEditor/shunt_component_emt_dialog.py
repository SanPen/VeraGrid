from __future__ import annotations

from PySide6 import QtWidgets

from VeraGridEngine.enumerations import ShuntConnectionType


class ShuntComponentEmtDialog(QtWidgets.QDialog):
    """
    Modal dialog used to configure one single-component EMT shunt block.
    """

    __slots__ = (
        "_component_kind",
        "_allow_static_load_values",
        "_static_connection_type",
        "phase_a_check",
        "phase_b_check",
        "phase_c_check",
        "connection_combo",
        "static_connection_label",
        "use_static_load_values_check",
        "value_label",
        "value_spin",
        "base_info_label",
    )

    def __init__(self,
                 component_kind: str,
                 parent: QtWidgets.QWidget | None = None,
                 initial_config: dict[str, object] | None = None,
                 allow_static_load_values: bool = False,
                 static_connection_type: ShuntConnectionType | None = None,
                 nominal_voltage_kv: float | None = None,
                 base_power_mva: float | None = None,
                 base_frequency_hz: float | None = None) -> None:
        """
        Build the single-component EMT shunt configuration dialog.

        :param component_kind: ``R``, ``L`` or ``C``.
        :param parent: Optional Qt parent.
        :param initial_config: Optional persisted modal configuration.
        :return: None.
        """
        super().__init__(parent)
        if component_kind in {"R", "L", "C"}:
            self._component_kind = component_kind
        else:
            raise ValueError(f"Unsupported EMT shunt component kind '{component_kind}'")
        self._allow_static_load_values = allow_static_load_values
        self._static_connection_type = static_connection_type

        self.setWindowTitle(f"Configure EMT {component_kind} Shunt")
        self.resize(420, 240)

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        form_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout()
        main_layout.addLayout(form_layout)

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

        self.static_connection_label = QtWidgets.QLabel(self)
        self.static_connection_label.setWordWrap(True)
        form_layout.addRow("Static connection", self.static_connection_label)

        self.use_static_load_values_check = QtWidgets.QCheckBox("Use load static object values", self)
        self.use_static_load_values_check.setEnabled(self._allow_static_load_values)
        self.use_static_load_values_check.setChecked(False)
        form_layout.addRow("Value Source", self.use_static_load_values_check)

        self.value_label = QtWidgets.QLabel(self)
        self.value_spin = QtWidgets.QDoubleSpinBox(self)
        self.value_spin.setRange(0.0, 1.0e12)
        form_layout.addRow(self.value_label, self.value_spin)

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

        self.use_static_load_values_check.toggled.connect(self.update_parameter_widgets)

        self.update_parameter_widgets()

        if initial_config is not None:
            self.apply_initial_configuration(initial_config)
        else:
            pass

        self._apply_static_connection_state()

    @staticmethod
    def _get_connection_type_label(connection_type: ShuntConnectionType) -> str:
        """
        Return the user-facing label for one shunt connection type.

        :param connection_type: Static or modal shunt connection type.
        :return: Human-readable label.
        """
        if connection_type == ShuntConnectionType.GroundedStar:
            return "Grounded Star (Yg)"
        elif connection_type == ShuntConnectionType.NeutralStar:
            return "Neutral Star (Yn)"
        elif connection_type == ShuntConnectionType.FloatingStar:
            return "Floating Star (Y)"
        elif connection_type == ShuntConnectionType.Delta:
            return "Delta"
        else:
            return str(connection_type)

    def _apply_static_connection_state(self) -> None:
        """
        Enforce the static connection contract in the dialog widgets.

        :return: None.
        """
        if self._static_connection_type is None:
            self.static_connection_label.setText("No static connection override was resolved for this device.")
            self.connection_combo.setEnabled(True)
        else:
            self.static_connection_label.setText(
                "Taken from static object: " + self._get_connection_type_label(self._static_connection_type)
            )
            index: int = self.connection_combo.findData(self._static_connection_type)
            if index >= 0:
                self.connection_combo.setCurrentIndex(index)
            else:
                pass
            self.connection_combo.setEnabled(False)

    def update_parameter_widgets(self) -> None:
        """
        Refresh the visible label and units for the selected component.

        :return: None.
        """
        use_static_load_values: bool = self.use_static_load_values_check.isChecked()

        # Static-value mode binds the EMT block parameter to the host load API
        # mapping, so the manual R/L/C editor must be disabled to prevent mixed
        # ownership of the same parameter.
        self.value_spin.setEnabled(not use_static_load_values)

        if self._component_kind == "R":
            self.value_label.setText("Resistance")
            self.value_spin.setDecimals(8)
            self.value_spin.setSuffix(" ohm")
            self.value_spin.setValue(max(float(self.value_spin.value()), 1.0))
        elif self._component_kind == "L":
            self.value_label.setText("Inductance")
            self.value_spin.setDecimals(10)
            self.value_spin.setSuffix(" H")
        else:
            self.value_label.setText("Capacitance")
            self.value_spin.setDecimals(12)
            self.value_spin.setSuffix(" F")

        if self._component_kind == "R" and self.value_spin.value() == 0.0:
            self.value_spin.setValue(1.0)
        elif self._component_kind == "L" and self.value_spin.value() == 0.0:
            self.value_spin.setValue(0.01)
        elif self._component_kind == "C" and self.value_spin.value() == 0.0:
            self.value_spin.setValue(1.0e-6)
        else:
            pass

    def accept_dialog(self) -> None:
        """
        Validate the modal state before accepting.

        :return: None.
        """
        if self.phase_a_check.isChecked() or self.phase_b_check.isChecked() or self.phase_c_check.isChecked():
            pass
        else:
            QtWidgets.QMessageBox.warning(self, "EMT Shunt", "Enable at least one phase.")
            return

        if self.use_static_load_values_check.isChecked():
            pass
        else:
            if self.value_spin.value() <= 0.0:
                QtWidgets.QMessageBox.warning(self, "EMT Shunt", f"{self.value_label.text()} must be greater than zero.")
                return
            else:
                pass

        self.accept()

    def get_configuration(self) -> dict[str, object]:
        """
        Return the current modal configuration.

        :return: Configuration dictionary.
        """
        config: dict[str, object] = dict({
            "phA": self.phase_a_check.isChecked(),
            "phB": self.phase_b_check.isChecked(),
            "phC": self.phase_c_check.isChecked(),
            "connection_type": self.connection_combo.currentData(),
            "input_mode": "physical",
            "use_static_load_values": self.use_static_load_values_check.isChecked(),
            "include_r": self._component_kind == "R",
            "include_l": self._component_kind == "L",
            "include_c": self._component_kind == "C",
            "resistance_ohm": 1.0,
            "inductive_value": 0.01,
            "capacitive_value": 1.0e-6,
        })

        if self._component_kind == "R":
            config["resistance_ohm"] = float(self.value_spin.value())
        elif self._component_kind == "L":
            config["inductive_value"] = float(self.value_spin.value())
        else:
            config["capacitive_value"] = float(self.value_spin.value())

        return config

    def apply_initial_configuration(self, config: dict[str, object]) -> None:
        """
        Load one persisted configuration into the dialog widgets.

        :param config: Persisted configuration.
        :return: None.
        """
        self.phase_a_check.setChecked(bool(config.get("phA", True)))
        self.phase_b_check.setChecked(bool(config.get("phB", True)))
        self.phase_c_check.setChecked(bool(config.get("phC", True)))
        self.use_static_load_values_check.setChecked(
            bool(config.get("use_static_load_values", False)) and self._allow_static_load_values
        )

        connection_type = config.get("connection_type", ShuntConnectionType.GroundedStar)
        index = self.connection_combo.findData(connection_type)
        if index >= 0:
            self.connection_combo.setCurrentIndex(index)
        else:
            pass

        if self._component_kind == "R":
            self.value_spin.setValue(float(config.get("resistance_ohm", 1.0)))
        elif self._component_kind == "L":
            self.value_spin.setValue(float(config.get("inductive_value", 0.01)))
        else:
            self.value_spin.setValue(float(config.get("capacitive_value", 1.0e-6)))

        self._apply_static_connection_state()
        self.update_parameter_widgets()
