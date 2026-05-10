from __future__ import annotations

from PySide6 import QtWidgets

from VeraGridEngine.enumerations import BlockType


class DcSourceEmtDialog(QtWidgets.QDialog):
    """
    Modal dialog used to configure one EMT DC source block.
    """

    __slots__ = ("_block_type", "_value_spin", "_conductance_spin", "_conductance_group", "_info_label")

    def __init__(self,
                 block_type: BlockType,
                 parent: QtWidgets.QWidget | None = None,
                 initial_config: dict[str, object] | None = None) -> None:
        super().__init__(parent)
        self._block_type: BlockType = block_type
        self.setWindowTitle(self._build_dialog_title())
        self.resize(420, 240)

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        description_label: QtWidgets.QLabel = QtWidgets.QLabel(self._build_description_text(), self)
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)

        value_group = QtWidgets.QGroupBox("Source Value", self)
        value_form = QtWidgets.QFormLayout(value_group)
        self._value_spin = QtWidgets.QDoubleSpinBox(value_group)
        self._value_spin.setRange(-1.0e6, 1.0e6)
        self._value_spin.setDecimals(8)
        self._value_spin.setSingleStep(0.1)
        self._value_spin.setAccelerated(True)
        value_form.addRow(self._build_value_label(), self._value_spin)
        main_layout.addWidget(value_group)

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
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self._apply_default_values()

        if initial_config is not None:
            self.apply_initial_configuration(initial_config)
        else:
            pass

        self._refresh_visibility()

    def _build_dialog_title(self) -> str:
        if self._block_type == BlockType.DC_VOLTAGE_SOURCE_EMT:
            return "Configure EMT DC Voltage Source"
        elif self._block_type == BlockType.DC_CURRENT_SOURCE_EMT:
            return "Configure EMT DC Current Source"
        elif self._block_type == BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT:
            return "Configure EMT Controlled DC Voltage Source"
        else:
            return "Configure EMT Controlled DC Current Source"

    def _build_description_text(self) -> str:
        if self._block_type == BlockType.DC_VOLTAGE_SOURCE_EMT:
            return "Define one DC voltage source using a Norton equivalent against the EMT DC bus."
        elif self._block_type == BlockType.DC_CURRENT_SOURCE_EMT:
            return "Define one fixed injected DC current source."
        elif self._block_type == BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT:
            return "Define one controlled DC voltage source. The command input is the source DC voltage used by the Norton equivalent."
        else:
            return "Define one controlled DC current source. The command input is the injected DC current."

    def _build_value_label(self) -> str:
        if self._block_type in {BlockType.DC_VOLTAGE_SOURCE_EMT, BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT}:
            return "Voltage"
        else:
            return "Current"

    def _uses_fixed_value(self) -> bool:
        return self._block_type in {BlockType.DC_VOLTAGE_SOURCE_EMT, BlockType.DC_CURRENT_SOURCE_EMT}

    def _uses_conductance(self) -> bool:
        return self._block_type in {BlockType.DC_VOLTAGE_SOURCE_EMT, BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT}

    def _apply_default_values(self) -> None:
        if self._block_type in {BlockType.DC_VOLTAGE_SOURCE_EMT, BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT}:
            self._value_spin.setValue(1.0)
        else:
            self._value_spin.setValue(0.0)

        self._conductance_spin.setValue(100.0)

        if self._block_type == BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT:
            self._info_label.setText("The command input sets the DC source voltage.")
        elif self._block_type == BlockType.CONTROLLED_DC_CURRENT_SOURCE_EMT:
            self._info_label.setText("The command input sets the injected DC current.")
        else:
            self._info_label.setText("")

    def _refresh_visibility(self) -> None:
        self._value_spin.setVisible(self._uses_fixed_value())
        value_label = self.parent()  # no-op placeholder to keep structure flat
        _unused = value_label
        self._conductance_group.setVisible(self._uses_conductance())

    def get_configuration(self) -> dict[str, object]:
        return dict({
            "source_value": float(self._value_spin.value()),
            "source_conductance_value": float(self._conductance_spin.value()),
        })

    def apply_initial_configuration(self, config: dict[str, object]) -> None:
        if "source_value" in config:
            self._value_spin.setValue(float(config["source_value"]))
        if "source_conductance_value" in config:
            self._conductance_spin.setValue(float(config["source_conductance_value"]))
        self._refresh_visibility()
