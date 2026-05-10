from __future__ import annotations

from PySide6 import QtWidgets

from VeraGridEngine.enumerations import BlockType


class BalancedSourceEmtDialog(QtWidgets.QDialog):
    """
    Modal dialog used to configure one balanced three-phase EMT source block.
    """

    __slots__ = ("_block_type", "_amplitude_spin", "_frequency_spin", "_phase_a_deg_spin", "_offset_spin", "_conductance_spin", "_conductance_group", "_info_label")

    def __init__(self,
                 block_type: BlockType,
                 parent: QtWidgets.QWidget | None = None,
                 initial_config: dict[str, object] | None = None) -> None:
        super().__init__(parent)
        self._block_type: BlockType = block_type
        self.setWindowTitle(self._build_dialog_title())
        self.resize(460, 320)

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        description_label: QtWidgets.QLabel = QtWidgets.QLabel(self._build_description_text(), self)
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)

        form_group = QtWidgets.QGroupBox("Balanced Wave Parameters", self)
        form_layout = QtWidgets.QFormLayout(form_group)

        self._amplitude_spin = QtWidgets.QDoubleSpinBox(form_group)
        self._amplitude_spin.setRange(-1.0e6, 1.0e6)
        self._amplitude_spin.setDecimals(8)
        self._amplitude_spin.setSingleStep(0.1)
        self._amplitude_spin.setAccelerated(True)
        form_layout.addRow("Amplitude", self._amplitude_spin)

        self._frequency_spin = QtWidgets.QDoubleSpinBox(form_group)
        self._frequency_spin.setRange(0.0, 1.0e6)
        self._frequency_spin.setDecimals(6)
        self._frequency_spin.setSingleStep(1.0)
        self._frequency_spin.setAccelerated(True)
        form_layout.addRow("Frequency [Hz]", self._frequency_spin)

        self._phase_a_deg_spin = QtWidgets.QDoubleSpinBox(form_group)
        self._phase_a_deg_spin.setRange(-3600.0, 3600.0)
        self._phase_a_deg_spin.setDecimals(6)
        self._phase_a_deg_spin.setSingleStep(1.0)
        self._phase_a_deg_spin.setAccelerated(True)
        form_layout.addRow("Phase A [deg]", self._phase_a_deg_spin)

        self._offset_spin = QtWidgets.QDoubleSpinBox(form_group)
        self._offset_spin.setRange(-1.0e6, 1.0e6)
        self._offset_spin.setDecimals(8)
        self._offset_spin.setSingleStep(0.1)
        self._offset_spin.setAccelerated(True)
        form_layout.addRow("Common offset", self._offset_spin)
        main_layout.addWidget(form_group)

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
        if self._block_type == BlockType.BALANCED_3PH_VOLTAGE_SOURCE_EMT:
            return "Configure Balanced 3-Phase EMT Voltage Source"
        elif self._block_type == BlockType.BALANCED_3PH_CURRENT_SOURCE_EMT:
            return "Configure Balanced 3-Phase EMT Current Source"
        elif self._block_type == BlockType.CONTROLLED_BALANCED_3PH_VOLTAGE_SOURCE_EMT:
            return "Configure Controlled Balanced 3-Phase EMT Voltage Source"
        else:
            return "Configure Controlled Balanced 3-Phase EMT Current Source"

    def _build_description_text(self) -> str:
        if self._block_type == BlockType.BALANCED_3PH_VOLTAGE_SOURCE_EMT:
            return "Define one balanced three-phase sinusoidal voltage source. Phases B and C are generated automatically from phase A with +/-120 degree shifts."
        elif self._block_type == BlockType.BALANCED_3PH_CURRENT_SOURCE_EMT:
            return "Define one balanced three-phase sinusoidal current source. Phases B and C are generated automatically from phase A with +/-120 degree shifts."
        elif self._block_type == BlockType.CONTROLLED_BALANCED_3PH_VOLTAGE_SOURCE_EMT:
            return "Define one balanced three-phase controlled voltage source. The command input sets the common sinusoidal amplitude."
        else:
            return "Define one balanced three-phase controlled current source. The command input sets the common sinusoidal amplitude."

    def _uses_fixed_amplitude(self) -> bool:
        return self._block_type in {BlockType.BALANCED_3PH_VOLTAGE_SOURCE_EMT, BlockType.BALANCED_3PH_CURRENT_SOURCE_EMT}

    def _uses_conductance(self) -> bool:
        return self._block_type in {BlockType.BALANCED_3PH_VOLTAGE_SOURCE_EMT, BlockType.CONTROLLED_BALANCED_3PH_VOLTAGE_SOURCE_EMT}

    def _apply_default_values(self) -> None:
        self._amplitude_spin.setValue(1.0)
        self._frequency_spin.setValue(50.0)
        self._phase_a_deg_spin.setValue(0.0)
        self._offset_spin.setValue(0.0)
        self._conductance_spin.setValue(100.0)

        if self._block_type == BlockType.CONTROLLED_BALANCED_3PH_VOLTAGE_SOURCE_EMT:
            self._info_label.setText("The command input sets the common three-phase voltage amplitude.")
        elif self._block_type == BlockType.CONTROLLED_BALANCED_3PH_CURRENT_SOURCE_EMT:
            self._info_label.setText("The command input sets the common three-phase current amplitude.")
        else:
            self._info_label.setText("")

    def _refresh_visibility(self) -> None:
        self._amplitude_spin.setVisible(self._uses_fixed_amplitude())
        amplitude_label = self._amplitude_spin.parent().layout().labelForField(self._amplitude_spin)
        if amplitude_label is not None:
            amplitude_label.setVisible(self._uses_fixed_amplitude())
        self._conductance_group.setVisible(self._uses_conductance())

    def accept_dialog(self) -> None:
        if self._frequency_spin.value() > 0.0:
            pass
        else:
            QtWidgets.QMessageBox.warning(self, "EMT Balanced Source", "The sinusoidal frequency must be greater than zero.")
            return
        self.accept()

    def get_configuration(self) -> dict[str, object]:
        return dict({
            "source_amplitude": float(self._amplitude_spin.value()),
            "source_frequency_hz": float(self._frequency_spin.value()),
            "source_phase_a_deg": float(self._phase_a_deg_spin.value()),
            "source_offset": float(self._offset_spin.value()),
            "source_conductance_value": float(self._conductance_spin.value()),
        })

    def apply_initial_configuration(self, config: dict[str, object]) -> None:
        if "source_amplitude" in config:
            self._amplitude_spin.setValue(float(config["source_amplitude"]))
        if "source_frequency_hz" in config:
            self._frequency_spin.setValue(float(config["source_frequency_hz"]))
        if "source_phase_a_deg" in config:
            self._phase_a_deg_spin.setValue(float(config["source_phase_a_deg"]))
        if "source_offset" in config:
            self._offset_spin.setValue(float(config["source_offset"]))
        if "source_conductance_value" in config:
            self._conductance_spin.setValue(float(config["source_conductance_value"]))
        self._refresh_visibility()
