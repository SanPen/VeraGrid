# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from PySide6 import QtWidgets

from VeraGridEngine.enumerations import EmtFaultPlacementSide, FaultType


def _get_fault_phase_count(fault_tpe: FaultType) -> int:
    """
    Return the number of enabled phases required by one fault type.

    :param fault_tpe: Requested fault type.
    :return: Required number of enabled phases.
    """
    if fault_tpe == FaultType.LG:
        return 1
    else:
        if fault_tpe in {FaultType.LL, FaultType.LLG}:
            return 2
        else:
            if fault_tpe in {FaultType.LLL, FaultType.LLLG}:
                return 3
            else:
                return 1


def _fault_uses_ground(fault_tpe: FaultType) -> bool:
    """
    Return whether one fault type includes a ground branch.

    :param fault_tpe: Requested fault type.
    :return: True when the fault uses ground.
    """
    if fault_tpe in {FaultType.LG, FaultType.LLG, FaultType.LLLG}:
        return True
    else:
        return False


class FaultEmtDialog(QtWidgets.QDialog):
    """
    Modal dialog used to configure one EMT fault template.
    """

    __slots__ = (
        "fault_type_combo",
        "phase_a_check",
        "phase_b_check",
        "phase_c_check",
        "placement_side_combo",
        "placement_help_label",
        "control_mode_combo",
        "control_mode_help_label",
        "initial_closed_check",
        "fault_resistance_spin",
        "ground_resistance_spin",
        "open_conductance_spin",
        "time_constant_spin",
        "command_threshold_spin",
    )

    def __init__(self,
                 parent: QtWidgets.QWidget | None = None,
                 initial_config: dict[str, object] | None = None) -> None:
        """
        Build the EMT fault configuration dialog.

        :param parent: Optional Qt parent.
        :param initial_config: Optional persisted modal configuration.
        :return: None.
        """
        super().__init__(parent)
        self.setWindowTitle("Configure EMT Fault")
        self.resize(440, 360)

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        form_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout()
        main_layout.addLayout(form_layout)

        self.fault_type_combo = QtWidgets.QComboBox(self)
        self.fault_type_combo.addItem("Line to Ground (LG)", FaultType.LG)
        self.fault_type_combo.addItem("Line to Line (LL)", FaultType.LL)
        self.fault_type_combo.addItem("Line-Line-Ground (LLG)", FaultType.LLG)
        self.fault_type_combo.addItem("Three-Phase (LLL)", FaultType.LLL)
        self.fault_type_combo.addItem("Three-Phase-Ground (LLLG)", FaultType.LLLG)
        form_layout.addRow("Fault Type", self.fault_type_combo)

        self.placement_side_combo = QtWidgets.QComboBox(self)
        self.placement_side_combo.addItem("From Side", EmtFaultPlacementSide.FromSide)
        self.placement_side_combo.addItem("To Side", EmtFaultPlacementSide.ToSide)
        form_layout.addRow("Placement", self.placement_side_combo)

        self.placement_help_label = QtWidgets.QLabel(self)
        self.placement_help_label.setWordWrap(True)
        main_layout.addWidget(self.placement_help_label)

        phase_widget = QtWidgets.QWidget(self)
        phase_layout = QtWidgets.QHBoxLayout(phase_widget)
        phase_layout.setContentsMargins(0, 0, 0, 0)
        self.phase_a_check = QtWidgets.QCheckBox("A", phase_widget)
        self.phase_b_check = QtWidgets.QCheckBox("B", phase_widget)
        self.phase_c_check = QtWidgets.QCheckBox("C", phase_widget)
        self.phase_a_check.setChecked(True)
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

        self.initial_closed_check = QtWidgets.QCheckBox("Fault initially applied", self)
        form_layout.addRow("Initial State", self.initial_closed_check)

        self.fault_resistance_spin = QtWidgets.QDoubleSpinBox(self)
        self.fault_resistance_spin.setDecimals(10)
        self.fault_resistance_spin.setRange(1.0e-12, 1.0e12)
        self.fault_resistance_spin.setValue(1.0e-4)
        form_layout.addRow("Phase Fault R", self.fault_resistance_spin)

        self.ground_resistance_spin = QtWidgets.QDoubleSpinBox(self)
        self.ground_resistance_spin.setDecimals(10)
        self.ground_resistance_spin.setRange(1.0e-12, 1.0e12)
        self.ground_resistance_spin.setValue(1.0e-4)
        form_layout.addRow("Ground Fault R", self.ground_resistance_spin)

        self.open_conductance_spin = QtWidgets.QDoubleSpinBox(self)
        self.open_conductance_spin.setDecimals(12)
        self.open_conductance_spin.setRange(0.0, 1.0e3)
        self.open_conductance_spin.setValue(1.0e-8)
        form_layout.addRow("Open G", self.open_conductance_spin)

        self.time_constant_spin = QtWidgets.QDoubleSpinBox(self)
        self.time_constant_spin.setDecimals(10)
        self.time_constant_spin.setRange(1.0e-8, 10.0)
        self.time_constant_spin.setValue(1.0e-6)
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

        self.fault_type_combo.currentIndexChanged.connect(self.on_fault_type_changed)
        self.placement_side_combo.currentIndexChanged.connect(self.on_placement_side_changed)
        self.control_mode_combo.currentIndexChanged.connect(self.on_control_mode_changed)
        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)

        if initial_config is not None:
            self.apply_initial_configuration(initial_config)
        else:
            self.on_fault_type_changed()
            self.on_placement_side_changed()
            self.on_control_mode_changed()

    def on_fault_type_changed(self) -> None:
        """
        Update the phase selectors and grounding fields for the selected fault shape.

        :return: None.
        """
        fault_tpe: FaultType = self.get_fault_type()
        required_phase_count: int = _get_fault_phase_count(fault_tpe)

        # The dialog first unlocks all phase toggles so the algorithm can decide
        # whether the current fault shape allows manual phase selection or must
        # force a fixed three-phase shape.
        self.phase_a_check.setEnabled(True)
        self.phase_b_check.setEnabled(True)
        self.phase_c_check.setEnabled(True)

        # Single-line-to-ground faults must collapse to exactly one selected phase.
        if required_phase_count == 1:
            self.phase_a_check.setChecked(True)
            self.phase_b_check.setChecked(False)
            self.phase_c_check.setChecked(False)
        else:
            # Two-phase faults keep manual selection flexibility but must never
            # start from an invalid empty/one-phase state.
            if required_phase_count == 2:
                selected_phase_count: int = self.get_selected_phase_count()

                if selected_phase_count < 2:
                    self.phase_a_check.setChecked(True)
                    self.phase_b_check.setChecked(True)
                    self.phase_c_check.setChecked(False)
                else:
                    pass
            else:
                # Three-phase faults must always expose the complete ABC set, so
                # the dialog forces and locks that state to prevent invalid builds.
                self.phase_a_check.setChecked(True)
                self.phase_b_check.setChecked(True)
                self.phase_c_check.setChecked(True)
                self.phase_a_check.setEnabled(False)
                self.phase_b_check.setEnabled(False)
                self.phase_c_check.setEnabled(False)

        uses_ground: bool = _fault_uses_ground(fault_tpe)
        self.ground_resistance_spin.setEnabled(uses_ground)

    def on_control_mode_changed(self) -> None:
        """
        Update the command-threshold widgets for the selected control mode.

        :return: None.
        """
        signal_controlled: bool = self.get_control_mode()
        self.command_threshold_spin.setEnabled(signal_controlled)

        if signal_controlled:
            self.control_mode_help_label.setText(
                "Signal Controlled: the fault exposes a command input. Values above the threshold apply the fault and values below the threshold clear it."
            )
        else:
            self.control_mode_help_label.setText(
                "Timed / Events: control the retained mode with EMT events on `fault_closed_mode_*`. Use value `1` to apply the fault and `0` to clear it."
            )

    def on_placement_side_changed(self) -> None:
        """
        Update the placement help text describing how to wire the outer and inner ports.

        :return: None.
        """
        placement_side: EmtFaultPlacementSide = self.get_placement_side()

        if placement_side == EmtFaultPlacementSide.FromSide:
            self.placement_help_label.setText(
                "From Side: connect `v_outer_*` to the parent branch from-side voltage, connect `v_inner_*` to the downstream line from-side voltage input, connect the downstream line from-side current output to `i_inner_*`, and connect `i_outer_*` back to the parent branch from-side current output."
            )
        else:
            self.placement_help_label.setText(
                "To Side: connect `v_outer_*` to the parent branch to-side voltage, connect `v_inner_*` to the upstream line to-side voltage input, connect the upstream line to-side current output to `i_inner_*`, and connect `i_outer_*` back to the parent branch to-side current output."
            )

    def accept_dialog(self) -> None:
        """
        Validate the modal state before accepting.

        :return: None.
        """
        selected_phase_count: int = self.get_selected_phase_count()
        fault_tpe: FaultType = self.get_fault_type()
        required_phase_count: int = _get_fault_phase_count(fault_tpe)

        # The template builder validates topology too, but the dialog checks it
        # first so users get immediate feedback before the symbolic build starts.
        if required_phase_count == 1 and selected_phase_count != 1:
            QtWidgets.QMessageBox.warning(self, "Fault EMT", "LG faults require exactly one enabled phase.")
            return
        else:
            if required_phase_count == 2 and selected_phase_count != 2:
                QtWidgets.QMessageBox.warning(self, "Fault EMT", "LL and LLG faults require exactly two enabled phases.")
                return
            else:
                if required_phase_count == 3 and selected_phase_count != 3:
                    QtWidgets.QMessageBox.warning(self, "Fault EMT", "LLL and LLLG faults require phases A, B, and C.")
                    return
                else:
                    pass

        self.accept()

    def get_fault_type(self) -> FaultType:
        """
        Return the selected fault type.

        :return: Fault type enum.
        """
        current_data: object = self.fault_type_combo.currentData()

        if isinstance(current_data, FaultType):
            return current_data
        else:
            return FaultType.LG

    def get_control_mode(self) -> bool:
        """
        Return whether the fault is signal controlled.

        :return: True when signal control is enabled.
        """
        current_data: object = self.control_mode_combo.currentData()

        if current_data == "signal_controlled":
            return True
        else:
            return False

    def get_placement_side(self) -> EmtFaultPlacementSide:
        """
        Return the selected internal placement side.

        :return: Placement side enum.
        """
        current_data: object = self.placement_side_combo.currentData()

        if isinstance(current_data, EmtFaultPlacementSide):
            return current_data
        else:
            return EmtFaultPlacementSide.FromSide

    def get_selected_phase_count(self) -> int:
        """
        Count the enabled phase check boxes.

        :return: Number of selected phases.
        """
        selected_phase_count: int = 0

        if self.phase_a_check.isChecked():
            selected_phase_count += 1
        else:
            pass

        if self.phase_b_check.isChecked():
            selected_phase_count += 1
        else:
            pass

        if self.phase_c_check.isChecked():
            selected_phase_count += 1
        else:
            pass

        return selected_phase_count

    def get_configuration(self) -> dict[str, object]:
        """
        Return the current fault dialog configuration.

        :return: Configuration dictionary.
        """
        return dict({
            "fault_type": self.get_fault_type(),
            "placement_side": self.get_placement_side(),
            "phA": self.phase_a_check.isChecked(),
            "phB": self.phase_b_check.isChecked(),
            "phC": self.phase_c_check.isChecked(),
            "signal_controlled": self.get_control_mode(),
            "initial_closed": self.initial_closed_check.isChecked(),
            "fault_resistance": float(self.fault_resistance_spin.value()),
            "ground_resistance": float(self.ground_resistance_spin.value()),
            "open_conductance": float(self.open_conductance_spin.value()),
            "fault_time_constant": float(self.time_constant_spin.value()),
            "command_threshold": float(self.command_threshold_spin.value()),
        })

    def apply_initial_configuration(self, config: dict[str, object]) -> None:
        """
        Load one persisted configuration into the dialog widgets.

        :param config: Persisted fault configuration.
        :return: None.
        """
        fault_tpe_obj: object = config.get("fault_type", FaultType.LG)
        fault_tpe: FaultType

        if isinstance(fault_tpe_obj, FaultType):
            fault_tpe = fault_tpe_obj
        else:
            fault_tpe = FaultType.argparse(str(fault_tpe_obj))

        index: int = self.fault_type_combo.findData(fault_tpe)
        if index >= 0:
            self.fault_type_combo.setCurrentIndex(index)
        else:
            pass

        self.phase_a_check.setChecked(bool(config.get("phA", True)))
        self.phase_b_check.setChecked(bool(config.get("phB", False)))
        self.phase_c_check.setChecked(bool(config.get("phC", False)))

        placement_side_obj: object = config.get("placement_side", EmtFaultPlacementSide.FromSide)
        placement_side: EmtFaultPlacementSide

        if isinstance(placement_side_obj, EmtFaultPlacementSide):
            placement_side = placement_side_obj
        else:
            placement_side = EmtFaultPlacementSide.argparse(str(placement_side_obj))

        placement_index: int = self.placement_side_combo.findData(placement_side)
        if placement_index >= 0:
            self.placement_side_combo.setCurrentIndex(placement_index)
        else:
            pass

        if bool(config.get("signal_controlled", False)):
            self.control_mode_combo.setCurrentIndex(1)
        else:
            self.control_mode_combo.setCurrentIndex(0)

        self.initial_closed_check.setChecked(bool(config.get("initial_closed", False)))
        self.fault_resistance_spin.setValue(float(config.get("fault_resistance", 1.0e-4)))
        self.ground_resistance_spin.setValue(float(config.get("ground_resistance", 1.0e-4)))
        self.open_conductance_spin.setValue(float(config.get("open_conductance", 1.0e-8)))
        self.time_constant_spin.setValue(float(config.get("fault_time_constant", 1.0e-6)))
        self.command_threshold_spin.setValue(float(config.get("command_threshold", 0.5)))
        self.on_fault_type_changed()
        self.on_placement_side_changed()
        self.on_control_mode_changed()
