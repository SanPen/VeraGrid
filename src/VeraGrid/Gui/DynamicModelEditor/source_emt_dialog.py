from __future__ import annotations

from PySide6 import QtWidgets

from VeraGridEngine.enumerations import BlockType


class SourceEmtDialog(QtWidgets.QDialog):
    """
    Modal dialog used to configure one sinusoidal EMT source block.
    """

    __slots__ = (
        "_block_type",
        "_phase_checks",
        "_amplitude_spins",
        "_phase_deg_spins",
        "_offset_spins",
        "_frequency_spin",
        "_conductance_spin",
        "_amplitude_group",
        "_conductance_group",
        "_info_label",
    )

    def __init__(self,
                 block_type: BlockType,
                 parent: QtWidgets.QWidget | None = None,
                 initial_config: dict[str, object] | None = None) -> None:
        super().__init__(parent)
        self._block_type: BlockType = block_type
        self._phase_checks: dict[str, QtWidgets.QCheckBox] = dict()
        self._amplitude_spins: dict[str, QtWidgets.QDoubleSpinBox] = dict()
        self._phase_deg_spins: dict[str, QtWidgets.QDoubleSpinBox] = dict()
        self._offset_spins: dict[str, QtWidgets.QDoubleSpinBox] = dict()
        self.setWindowTitle(self._build_dialog_title())
        self.resize(520, 560)

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

        common_group = QtWidgets.QGroupBox("Wave Parameters", self)
        common_form = QtWidgets.QFormLayout(common_group)
        self._frequency_spin = QtWidgets.QDoubleSpinBox(common_group)
        self._frequency_spin.setRange(0.0, 1.0e6)
        self._frequency_spin.setDecimals(6)
        self._frequency_spin.setSingleStep(1.0)
        self._frequency_spin.setAccelerated(True)
        common_form.addRow("Frequency [Hz]", self._frequency_spin)
        main_layout.addWidget(common_group)

        self._amplitude_group = QtWidgets.QGroupBox(self._build_amplitude_group_title(), self)
        amplitude_form = QtWidgets.QFormLayout(self._amplitude_group)
        for phase_label in ("N", "A", "B", "C"):
            amplitude_spin = QtWidgets.QDoubleSpinBox(self._amplitude_group)
            amplitude_spin.setRange(-1.0e6, 1.0e6)
            amplitude_spin.setDecimals(8)
            amplitude_spin.setSingleStep(0.1)
            amplitude_spin.setAccelerated(True)
            self._amplitude_spins[phase_label] = amplitude_spin
            amplitude_form.addRow(f"{phase_label} amplitude", amplitude_spin)

            phase_spin = QtWidgets.QDoubleSpinBox(self._amplitude_group)
            phase_spin.setRange(-3600.0, 3600.0)
            phase_spin.setDecimals(6)
            phase_spin.setSingleStep(1.0)
            phase_spin.setAccelerated(True)
            self._phase_deg_spins[phase_label] = phase_spin
            amplitude_form.addRow(f"{phase_label} phase [deg]", phase_spin)

            offset_spin = QtWidgets.QDoubleSpinBox(self._amplitude_group)
            offset_spin.setRange(-1.0e6, 1.0e6)
            offset_spin.setDecimals(8)
            offset_spin.setSingleStep(0.1)
            offset_spin.setAccelerated(True)
            self._offset_spins[phase_label] = offset_spin
            amplitude_form.addRow(f"{phase_label} offset", offset_spin)
        main_layout.addWidget(self._amplitude_group)

        self._conductance_group = QtWidgets.QGroupBox("Norton Conductance", self)
        conductance_form = QtWidgets.QFormLayout(self._conductance_group)
        self._conductance_spin = QtWidgets.QDoubleSpinBox(self._conductance_group)
        self._conductance_spin.setRange(0.0, 1.0e9)
        self._conductance_spin.setDecimals(8)
        self._conductance_spin.setSingleStep(1.0)
        self._conductance_spin.setAccelerated(True)
        conductance_form.addRow("Conductance", self._conductance_spin)
        main_layout.addWidget(self._conductance_group)

        self._info_label = QtWidgets.QLabel(self)
        self._info_label.setWordWrap(True)
        main_layout.addWidget(self._info_label)

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

        self._refresh_visibility()

    def _build_dialog_title(self) -> str:
        if self._block_type == BlockType.VOLTAGE_SOURCE_EMT:
            return "Configure Sinusoidal EMT Voltage Source"
        elif self._block_type == BlockType.CURRENT_SOURCE_EMT:
            return "Configure Sinusoidal EMT Current Source"
        elif self._block_type == BlockType.CONTROLLED_VOLTAGE_SOURCE_EMT:
            return "Configure Controlled Sinusoidal EMT Voltage Source"
        else:
            return "Configure Controlled Sinusoidal EMT Current Source"

    def _build_description_text(self) -> str:
        if self._block_type == BlockType.VOLTAGE_SOURCE_EMT:
            return "Define one sinusoidal EMT voltage source. Each active phase uses amplitude, phase, frequency, and offset. The bus sees one Norton equivalent defined by the configured conductance."
        elif self._block_type == BlockType.CURRENT_SOURCE_EMT:
            return "Define one sinusoidal EMT current source. Each active phase injects one internally generated sine wave with amplitude, phase, frequency, and offset."
        elif self._block_type == BlockType.CONTROLLED_VOLTAGE_SOURCE_EMT:
            return "Define one controlled sinusoidal EMT voltage source. Each command input sets the sinusoidal amplitude of its phase, while frequency, phase offset, and DC offset stay fixed in the dialog."
        else:
            return "Define one controlled sinusoidal EMT current source. Each command input sets the sinusoidal amplitude of its phase, while frequency, phase offset, and DC offset stay fixed in the dialog."

    def _build_amplitude_group_title(self) -> str:
        if self._block_type in {BlockType.CONTROLLED_VOLTAGE_SOURCE_EMT, BlockType.CONTROLLED_CURRENT_SOURCE_EMT}:
            return "Fixed Phase Offsets"
        elif self._block_type == BlockType.VOLTAGE_SOURCE_EMT:
            return "Voltage Wave Values"
        else:
            return "Current Wave Values"

    def _uses_fixed_amplitudes(self) -> bool:
        return self._block_type in {BlockType.VOLTAGE_SOURCE_EMT, BlockType.CURRENT_SOURCE_EMT}

    def _uses_source_conductance(self) -> bool:
        return self._block_type in {BlockType.VOLTAGE_SOURCE_EMT, BlockType.CONTROLLED_VOLTAGE_SOURCE_EMT}

    def _apply_default_values(self) -> None:
        self._phase_checks["N"].setChecked(False)
        self._phase_checks["A"].setChecked(True)
        self._phase_checks["B"].setChecked(True)
        self._phase_checks["C"].setChecked(True)

        self._frequency_spin.setValue(50.0)
        self._conductance_spin.setValue(100.0)

        default_phase_deg = {"N": 0.0, "A": 0.0, "B": -120.0, "C": 120.0}
        for phase_label in ("N", "A", "B", "C"):
            self._phase_deg_spins[phase_label].setValue(default_phase_deg[phase_label])
            self._offset_spins[phase_label].setValue(0.0)

            if phase_label == "N":
                self._amplitude_spins[phase_label].setValue(0.0)
            else:
                self._amplitude_spins[phase_label].setValue(1.0)

        if self._block_type == BlockType.CONTROLLED_VOLTAGE_SOURCE_EMT:
            self._info_label.setText("The command inputs are per-phase sinusoidal voltage amplitudes. Conductance controls how stiff the source behaves against the bus voltage.")
        elif self._block_type == BlockType.CONTROLLED_CURRENT_SOURCE_EMT:
            self._info_label.setText("The command inputs are per-phase sinusoidal current amplitudes.")
        else:
            self._info_label.setText("")

    def _refresh_visibility(self) -> None:
        amplitude_visible: bool = self._uses_fixed_amplitudes()

        for phase_label in ("N", "A", "B", "C"):
            self._amplitude_spins[phase_label].setVisible(amplitude_visible)
            amplitude_label = self._amplitude_group.layout().labelForField(self._amplitude_spins[phase_label])
            if amplitude_label is not None:
                amplitude_label.setVisible(amplitude_visible)

        self._conductance_group.setVisible(self._uses_source_conductance())

    def accept_dialog(self) -> None:
        if any(checkbox.isChecked() for checkbox in self._phase_checks.values()):
            pass
        else:
            QtWidgets.QMessageBox.warning(self, "EMT Source", "Enable at least one terminal.")
            return

        if self._frequency_spin.value() > 0.0:
            pass
        else:
            QtWidgets.QMessageBox.warning(self, "EMT Source", "The sinusoidal frequency must be greater than zero.")
            return

        self.accept()

    def get_configuration(self) -> dict[str, object]:
        return dict({
            "phase_n": bool(self._phase_checks["N"].isChecked()),
            "phase_a": bool(self._phase_checks["A"].isChecked()),
            "phase_b": bool(self._phase_checks["B"].isChecked()),
            "phase_c": bool(self._phase_checks["C"].isChecked()),
            "source_frequency_hz": float(self._frequency_spin.value()),
            "source_phase_amplitudes": dict({phase_label: float(spin.value()) for phase_label, spin in self._amplitude_spins.items()}),
            "source_phase_angle_deg": dict({phase_label: float(spin.value()) for phase_label, spin in self._phase_deg_spins.items()}),
            "source_phase_offsets": dict({phase_label: float(spin.value()) for phase_label, spin in self._offset_spins.items()}),
            "source_conductance_value": float(self._conductance_spin.value()),
        })

    def apply_initial_configuration(self, config: dict[str, object]) -> None:
        phase_key_map = {"N": "phase_n", "A": "phase_a", "B": "phase_b", "C": "phase_c"}
        phase_label: str

        for phase_label, config_key in phase_key_map.items():
            if config_key in config:
                self._phase_checks[phase_label].setChecked(bool(config[config_key]))
            else:
                pass

        if "source_frequency_hz" in config:
            self._frequency_spin.setValue(float(config["source_frequency_hz"]))

        source_phase_amplitudes = config.get("source_phase_amplitudes", None)
        if isinstance(source_phase_amplitudes, dict):
            for phase_label, spin in self._amplitude_spins.items():
                if phase_label in source_phase_amplitudes:
                    spin.setValue(float(source_phase_amplitudes[phase_label]))

        source_phase_angle_deg = config.get("source_phase_angle_deg", None)
        if isinstance(source_phase_angle_deg, dict):
            for phase_label, spin in self._phase_deg_spins.items():
                if phase_label in source_phase_angle_deg:
                    spin.setValue(float(source_phase_angle_deg[phase_label]))

        source_phase_offsets = config.get("source_phase_offsets", None)
        if isinstance(source_phase_offsets, dict):
            for phase_label, spin in self._offset_spins.items():
                if phase_label in source_phase_offsets:
                    spin.setValue(float(source_phase_offsets[phase_label]))

        if "source_conductance_value" in config:
            self._conductance_spin.setValue(float(config["source_conductance_value"]))

        self._refresh_visibility()
