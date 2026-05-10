from __future__ import annotations

from PySide6 import QtWidgets

from VeraGridEngine.enumerations import BlockType


class TransientSourceEmtDialog(QtWidgets.QDialog):
    """
    Modal dialog used to configure one transient EMT source block.
    """

    __slots__ = ("_block_type", "_phase_checks", "_field_widgets")

    def __init__(self,
                 block_type: BlockType,
                 parent: QtWidgets.QWidget | None = None,
                 initial_config: dict[str, object] | None = None) -> None:
        super().__init__(parent)
        self._block_type: BlockType = block_type
        self._phase_checks: dict[str, QtWidgets.QCheckBox] = dict()
        self._field_widgets: dict[str, QtWidgets.QDoubleSpinBox] = dict()
        self.setWindowTitle(self._build_dialog_title())
        self.resize(500, 540)

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        description_label: QtWidgets.QLabel = QtWidgets.QLabel(self._build_description_text(), self)
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)

        phase_group = QtWidgets.QGroupBox("Active Phases", self)
        phase_layout = QtWidgets.QHBoxLayout(phase_group)
        for phase_label in ("N", "A", "B", "C"):
            checkbox = QtWidgets.QCheckBox(phase_label, phase_group)
            self._phase_checks[phase_label] = checkbox
            phase_layout.addWidget(checkbox)
        phase_layout.addStretch()
        main_layout.addWidget(phase_group)

        parameter_group = QtWidgets.QGroupBox("Waveform Parameters", self)
        parameter_form = QtWidgets.QFormLayout(parameter_group)
        for field_name, label_text in self._get_field_labels().items():
            spin = QtWidgets.QDoubleSpinBox(parameter_group)
            spin.setRange(-1.0e9, 1.0e9)
            spin.setDecimals(8)
            spin.setSingleStep(0.1)
            spin.setAccelerated(True)
            self._field_widgets[field_name] = spin
            parameter_form.addRow(label_text, spin)
        main_layout.addWidget(parameter_group)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self._apply_default_values()

        if initial_config is not None:
            self.apply_initial_configuration(initial_config)
        else:
            pass

    def _build_dialog_title(self) -> str:
        return str(self._block_type.name).replace("_", " ").title()

    def _build_description_text(self) -> str:
        if self._block_type in {BlockType.STEP_VOLTAGE_SOURCE_EMT, BlockType.STEP_CURRENT_SOURCE_EMT}:
            return "Define one step waveform source shared by the active phases."
        elif self._block_type in {BlockType.RAMP_VOLTAGE_SOURCE_EMT, BlockType.RAMP_CURRENT_SOURCE_EMT}:
            return "Define one ramp waveform source shared by the active phases."
        elif self._block_type == BlockType.DOUBLE_EXPONENTIAL_CURRENT_SOURCE_EMT:
            return "Define one double-exponential current source shared by the active phases."
        elif self._block_type == BlockType.HEIDLER_CURRENT_SOURCE_EMT:
            return "Define one Heidler current source shared by the active phases."
        else:
            return "Define one CIGRE surge current source shared by the active phases."

    def _get_field_labels(self) -> dict[str, str]:
        if self._block_type in {BlockType.STEP_VOLTAGE_SOURCE_EMT, BlockType.STEP_CURRENT_SOURCE_EMT}:
            return {
                "initial_value": "Initial value",
                "final_value": "Final value",
                "step_time_s": "Step time [s]",
                "source_conductance_value": "Conductance",
            }
        elif self._block_type in {BlockType.RAMP_VOLTAGE_SOURCE_EMT, BlockType.RAMP_CURRENT_SOURCE_EMT}:
            return {
                "initial_value": "Initial value",
                "final_value": "Final value",
                "start_time_s": "Start time [s]",
                "end_time_s": "End time [s]",
                "source_conductance_value": "Conductance",
            }
        elif self._block_type == BlockType.DOUBLE_EXPONENTIAL_CURRENT_SOURCE_EMT:
            return {
                "amplitude_value": "Amplitude",
                "alpha_value": "Alpha",
                "beta_value": "Beta",
                "delay_s": "Delay [s]",
            }
        elif self._block_type == BlockType.HEIDLER_CURRENT_SOURCE_EMT:
            return {
                "peak_value": "Peak",
                "front_time_s": "Front time [s]",
                "tail_time_s": "Tail time [s]",
                "order_value": "Order n",
                "delay_s": "Delay [s]",
            }
        else:
            return {
                "a_value": "A",
                "b_value": "B",
                "n_value": "n",
                "tn_s": "tn [s]",
                "i1_value": "I1",
                "t1_s": "t1 [s]",
                "i2_value": "I2",
                "t2_s": "t2 [s]",
                "delay_s": "Delay [s]",
            }

    def _apply_default_values(self) -> None:
        self._phase_checks["N"].setChecked(False)
        self._phase_checks["A"].setChecked(True)
        self._phase_checks["B"].setChecked(False)
        self._phase_checks["C"].setChecked(False)

        default_values = {
            "initial_value": 0.0,
            "final_value": 1.0,
            "step_time_s": 0.02,
            "start_time_s": 0.01,
            "end_time_s": 0.03,
            "source_conductance_value": 100.0,
            "amplitude_value": 1.0,
            "alpha_value": 100.0,
            "beta_value": 5000.0,
            "delay_s": 0.0,
            "peak_value": 1.0,
            "front_time_s": 1.0e-4,
            "tail_time_s": 5.0e-4,
            "order_value": 4.0,
            "a_value": 1000.0,
            "b_value": 10000.0,
            "n_value": 2.0,
            "tn_s": 1.0e-4,
            "i1_value": 1.0,
            "t1_s": 5.0e-4,
            "i2_value": 0.5,
            "t2_s": 2.0e-4,
        }

        for field_name, widget in self._field_widgets.items():
            widget.setValue(float(default_values[field_name]))

    def accept_dialog(self) -> None:
        if any(checkbox.isChecked() for checkbox in self._phase_checks.values()):
            pass
        else:
            QtWidgets.QMessageBox.warning(self, "EMT Transient Source", "Enable at least one terminal.")
            return

        if "step_time_s" in self._field_widgets and self._field_widgets["step_time_s"].value() < 0.0:
            QtWidgets.QMessageBox.warning(self, "EMT Transient Source", "The step time must be non-negative.")
            return

        if "end_time_s" in self._field_widgets:
            if self._field_widgets["end_time_s"].value() > self._field_widgets["start_time_s"].value():
                pass
            else:
                QtWidgets.QMessageBox.warning(self, "EMT Transient Source", "The ramp end time must be greater than the ramp start time.")
                return

        self.accept()

    def get_configuration(self) -> dict[str, object]:
        config: dict[str, object] = {
            "phase_n": bool(self._phase_checks["N"].isChecked()),
            "phase_a": bool(self._phase_checks["A"].isChecked()),
            "phase_b": bool(self._phase_checks["B"].isChecked()),
            "phase_c": bool(self._phase_checks["C"].isChecked()),
        }

        for field_name, widget in self._field_widgets.items():
            config[field_name] = float(widget.value())

        return config

    def apply_initial_configuration(self, config: dict[str, object]) -> None:
        phase_key_map = {"N": "phase_n", "A": "phase_a", "B": "phase_b", "C": "phase_c"}
        phase_label: str

        for phase_label, config_key in phase_key_map.items():
            if config_key in config:
                self._phase_checks[phase_label].setChecked(bool(config[config_key]))

        for field_name, widget in self._field_widgets.items():
            if field_name in config:
                widget.setValue(float(config[field_name]))
