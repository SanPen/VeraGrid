from __future__ import annotations

from PySide6 import QtWidgets

from VeraGrid.Gui.DynamicModelEditor.lookup_table_dialog import LookupArrayLinearDialog
from VeraGridEngine.enumerations import BlockType


class ArbitrarySourceEmtDialog(QtWidgets.QDialog):
    """
    Modal dialog used to configure one arbitrary-waveform EMT source block.
    """

    __slots__ = (
        "_block_type",
        "_phase_checks",
        "_time_points",
        "_value_points",
        "_waveform_summary_label",
        "_conductance_spin",
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
        self._time_points: list[float] = [0.0, 0.02, 0.04]
        self._value_points: list[float] = [0.0, 1.0, 0.0]
        self.setWindowTitle(self._build_dialog_title())
        self.resize(520, 360)

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

        waveform_group = QtWidgets.QGroupBox("Waveform Table", self)
        waveform_layout = QtWidgets.QVBoxLayout(waveform_group)
        self._waveform_summary_label = QtWidgets.QLabel(waveform_group)
        self._waveform_summary_label.setWordWrap(True)
        waveform_layout.addWidget(self._waveform_summary_label)
        edit_waveform_button = QtWidgets.QPushButton("Edit Waveform", waveform_group)
        edit_waveform_button.clicked.connect(self.edit_waveform_points)
        waveform_layout.addWidget(edit_waveform_button)
        main_layout.addWidget(waveform_group)

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
        self._refresh_waveform_summary()

    def _build_dialog_title(self) -> str:
        if self._block_type == BlockType.ARBITRARY_WAVEFORM_VOLTAGE_SOURCE_EMT:
            return "Configure Arbitrary Waveform EMT Voltage Source"
        else:
            return "Configure Arbitrary Waveform EMT Current Source"

    def _build_description_text(self) -> str:
        if self._block_type == BlockType.ARBITRARY_WAVEFORM_VOLTAGE_SOURCE_EMT:
            return "Define one arbitrary time waveform shared by the active phases. The source is injected through a Norton equivalent against the connected EMT bus voltages."
        else:
            return "Define one arbitrary time waveform shared by the active phases. The waveform is injected directly as phase currents."

    def _uses_conductance(self) -> bool:
        return self._block_type == BlockType.ARBITRARY_WAVEFORM_VOLTAGE_SOURCE_EMT

    def _apply_default_values(self) -> None:
        self._phase_checks["N"].setChecked(False)
        self._phase_checks["A"].setChecked(True)
        self._phase_checks["B"].setChecked(False)
        self._phase_checks["C"].setChecked(False)
        self._conductance_spin.setValue(100.0)

        if self._block_type == BlockType.ARBITRARY_WAVEFORM_VOLTAGE_SOURCE_EMT:
            self._info_label.setText("The same waveform is applied to every active phase as one source voltage. Conductance controls how stiff the source behaves against the bus.")
        else:
            self._info_label.setText("The same waveform is applied to every active phase as an injected current.")

    def _refresh_visibility(self) -> None:
        self._conductance_group.setVisible(self._uses_conductance())

    def _refresh_waveform_summary(self) -> None:
        self._waveform_summary_label.setText(
            f"{len(self._time_points)} points from {self._time_points[0]:.6g} s to {self._time_points[-1]:.6g} s."
        )

    def edit_waveform_points(self) -> None:
        dialog = LookupArrayLinearDialog(
            block_label="Arbitrary Source Waveform",
            initial_points=list(zip(self._time_points, self._value_points)),
            parent=self,
            x_label="t [s]",
            y_label="value",
            preview_enabled=True,
            preview_title="Arbitrary Source Waveform",
        )

        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self._time_points, self._value_points = dialog.get_points()
            self._refresh_waveform_summary()
        else:
            pass

    def accept_dialog(self) -> None:
        if any(checkbox.isChecked() for checkbox in self._phase_checks.values()):
            pass
        else:
            QtWidgets.QMessageBox.warning(self, "EMT Arbitrary Source", "Enable at least one terminal.")
            return

        if len(self._time_points) >= 2:
            pass
        else:
            QtWidgets.QMessageBox.warning(self, "EMT Arbitrary Source", "The waveform table requires at least two points.")
            return

        self.accept()

    def get_configuration(self) -> dict[str, object]:
        return dict({
            "phase_n": bool(self._phase_checks["N"].isChecked()),
            "phase_a": bool(self._phase_checks["A"].isChecked()),
            "phase_b": bool(self._phase_checks["B"].isChecked()),
            "phase_c": bool(self._phase_checks["C"].isChecked()),
            "time_points": list(self._time_points),
            "value_points": list(self._value_points),
            "source_conductance_value": float(self._conductance_spin.value()),
        })

    def apply_initial_configuration(self, config: dict[str, object]) -> None:
        phase_key_map = {"N": "phase_n", "A": "phase_a", "B": "phase_b", "C": "phase_c"}
        phase_label: str

        for phase_label, config_key in phase_key_map.items():
            if config_key in config:
                self._phase_checks[phase_label].setChecked(bool(config[config_key]))

        if isinstance(config.get("time_points", None), list):
            self._time_points = [float(value) for value in config["time_points"]]
        if isinstance(config.get("value_points", None), list):
            self._value_points = [float(value) for value in config["value_points"]]
        if "source_conductance_value" in config:
            self._conductance_spin.setValue(float(config["source_conductance_value"]))

        self._refresh_waveform_summary()
        self._refresh_visibility()
