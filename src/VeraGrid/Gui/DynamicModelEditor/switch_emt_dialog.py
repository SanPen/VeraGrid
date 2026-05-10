# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from PySide6 import QtWidgets


class SwitchEmtDialog(QtWidgets.QDialog):
    """
    Modal dialog used to configure one EMT switch template.
    """

    __slots__ = (
        "phase_a_check",
        "phase_b_check",
        "phase_c_check",
        "control_mode_combo",
        "control_mode_help_label",
        "initial_state_combo",
        "closed_conductance_mode_combo",
        "manual_closed_conductance_spin",
        "open_conductance_spin",
        "time_constant_spin",
        "command_threshold_spin",
    )

    def __init__(self,
                 parent: QtWidgets.QWidget | None = None,
                 initial_config: dict[str, object] | None = None) -> None:
        """
        Build the switch EMT configuration dialog.

        :param parent: Optional Qt parent.
        :return: None.
        """
        super().__init__(parent)
        self.setWindowTitle("Configure EMT Switch")
        self.resize(420, 340)

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

        self.control_mode_combo = QtWidgets.QComboBox(self)
        self.control_mode_combo.addItem("Timed / Events", "event_mode")
        self.control_mode_combo.addItem("Signal Controlled", "signal_controlled")
        form_layout.addRow("Control Mode", self.control_mode_combo)

        self.control_mode_help_label = QtWidgets.QLabel(self)
        self.control_mode_help_label.setWordWrap(True)
        main_layout.addWidget(self.control_mode_help_label)

        self.initial_state_combo = QtWidgets.QComboBox(self)
        self.initial_state_combo.addItem("Use PF active", "use_pf_active")
        self.initial_state_combo.addItem("Force closed", "force_closed")
        self.initial_state_combo.addItem("Force open", "force_open")
        form_layout.addRow("Initial State", self.initial_state_combo)

        self.closed_conductance_mode_combo = QtWidgets.QComboBox(self)
        self.closed_conductance_mode_combo.addItem("Use switch R/X", "use_device_g")
        self.closed_conductance_mode_combo.addItem("Manual conductance", "manual_g")
        form_layout.addRow("Closed Branch", self.closed_conductance_mode_combo)

        self.manual_closed_conductance_spin = QtWidgets.QDoubleSpinBox(self)
        self.manual_closed_conductance_spin.setDecimals(8)
        self.manual_closed_conductance_spin.setRange(0.0, 1.0e12)
        self.manual_closed_conductance_spin.setValue(1.0e4)
        self.manual_closed_conductance_spin.setEnabled(False)
        form_layout.addRow("Manual Closed G", self.manual_closed_conductance_spin)

        self.open_conductance_spin = QtWidgets.QDoubleSpinBox(self)
        self.open_conductance_spin.setDecimals(12)
        self.open_conductance_spin.setRange(0.0, 1.0e3)
        self.open_conductance_spin.setValue(1.0e-8)
        form_layout.addRow("Open G", self.open_conductance_spin)

        self.time_constant_spin = QtWidgets.QDoubleSpinBox(self)
        self.time_constant_spin.setDecimals(8)
        self.time_constant_spin.setRange(1.0e-8, 10.0)
        self.time_constant_spin.setValue(1.0e-4)
        self.time_constant_spin.setSuffix(" s")
        form_layout.addRow("Time Constant", self.time_constant_spin)

        self.command_threshold_spin = QtWidgets.QDoubleSpinBox(self)
        self.command_threshold_spin.setDecimals(6)
        self.command_threshold_spin.setRange(-1.0e9, 1.0e9)
        self.command_threshold_spin.setValue(0.5)
        self.command_threshold_spin.setEnabled(False)
        form_layout.addRow("Command Threshold", self.command_threshold_spin)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        main_layout.addWidget(buttons)

        self.control_mode_combo.currentIndexChanged.connect(self.on_control_mode_changed)
        self.closed_conductance_mode_combo.currentIndexChanged.connect(self.on_conductance_mode_changed)
        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)

        self.on_control_mode_changed()
        self.on_conductance_mode_changed()

        if initial_config is not None:
            self.apply_initial_configuration(initial_config)
        else:
            pass

    def on_control_mode_changed(self) -> None:
        """
        Update signal-control-specific widgets.

        :return: None.
        """
        signal_controlled: bool = self.get_control_mode() == "signal_controlled"
        self.command_threshold_spin.setEnabled(signal_controlled)

        if signal_controlled:
            self.control_mode_help_label.setText(
                "Signal Controlled: the switch exposes a command input. Values above the threshold close the switch and values below the threshold open it."
            )
        else:
            self.control_mode_help_label.setText(
                "Timed / Events: control the retained mode with EMT events on `switch_closed_mode_*`. Use value `1` to close and `0` to open. Reclose and reopen are implemented by adding multiple EMT mode events over time."
            )

    def on_conductance_mode_changed(self) -> None:
        """
        Update manual-conductance widgets.

        :return: None.
        """
        self.manual_closed_conductance_spin.setEnabled(self.get_closed_conductance_mode() == "manual_g")

    def accept_dialog(self) -> None:
        """
        Validate the modal data before accepting.

        :return: None.
        """
        if self.phase_a_check.isChecked() or self.phase_b_check.isChecked() or self.phase_c_check.isChecked():
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "Switch EMT", "Enable at least one phase.")

    def get_control_mode(self) -> str:
        return str(self.control_mode_combo.currentData())

    def get_closed_conductance_mode(self) -> str:
        return str(self.closed_conductance_mode_combo.currentData())

    def get_switch_configuration(self) -> dict[str, object]:
        """
        Return the current switch dialog configuration.

        :return: Configuration dictionary.
        """
        initial_state_mode: str = str(self.initial_state_combo.currentData())
        return dict({
            "phA": self.phase_a_check.isChecked(),
            "phB": self.phase_b_check.isChecked(),
            "phC": self.phase_c_check.isChecked(),
            "signal_controlled": self.get_control_mode() == "signal_controlled",
            "seed_from_pf_active": initial_state_mode == "use_pf_active",
            "initial_closed": initial_state_mode != "force_open",
            "use_device_conductance": self.get_closed_conductance_mode() == "use_device_g",
            "manual_closed_conductance": float(self.manual_closed_conductance_spin.value()),
            "open_conductance": float(self.open_conductance_spin.value()),
            "switch_time_constant": float(self.time_constant_spin.value()),
            "command_threshold": float(self.command_threshold_spin.value()),
        })

    def apply_initial_configuration(self, config: dict[str, object]) -> None:
        """
        Load one persisted switch configuration into the modal widgets.

        :param config: Stored switch configuration.
        :return: None.
        """
        self.phase_a_check.setChecked(bool(config.get("phA", True)))
        self.phase_b_check.setChecked(bool(config.get("phB", True)))
        self.phase_c_check.setChecked(bool(config.get("phC", True)))

        if bool(config.get("signal_controlled", False)):
            self.control_mode_combo.setCurrentIndex(1)
        else:
            self.control_mode_combo.setCurrentIndex(0)

        if bool(config.get("seed_from_pf_active", True)):
            self.initial_state_combo.setCurrentIndex(0)
        else:
            if bool(config.get("initial_closed", True)):
                self.initial_state_combo.setCurrentIndex(1)
            else:
                self.initial_state_combo.setCurrentIndex(2)

        if bool(config.get("use_device_conductance", True)):
            self.closed_conductance_mode_combo.setCurrentIndex(0)
        else:
            self.closed_conductance_mode_combo.setCurrentIndex(1)

        self.manual_closed_conductance_spin.setValue(float(config.get("manual_closed_conductance", 1.0e4)))
        self.open_conductance_spin.setValue(float(config.get("open_conductance", 1.0e-8)))
        self.time_constant_spin.setValue(float(config.get("switch_time_constant", 1.0e-4)))
        self.command_threshold_spin.setValue(float(config.get("command_threshold", 0.5)))
        self.on_control_mode_changed()
        self.on_conductance_mode_changed()
