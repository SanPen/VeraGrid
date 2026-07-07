# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Union
import sys

import numpy as np
from PySide6 import QtWidgets

from VeraGrid.Gui.DeviceEditors.LineEditor.line_editor_gui import Ui_LineEditorDialog
from VeraGrid.Gui.gui_functions import get_list_model
from VeraGrid.Gui.messages import error_msg, warning_msg, yes_no_question
from VeraGridEngine.Devices.Branches.line import Line, OverheadLineType, SequenceLineType, UndergroundLineType
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Substation.bus import Bus

LineTemplate = Union[SequenceLineType, OverheadLineType, UndergroundLineType]


class LineEditor(QtWidgets.QDialog):
    """
    Line editor controller backed by a Qt Designer `.ui` file.
    """

    def __init__(self, line: Line, grid: MultiCircuit) -> None:
        """
        Build the line editor view/controller.

        :param line: Branch object to update.
        :param grid: Grid model with system base and template catalogues.
        """
        super().__init__()
        self.ui = Ui_LineEditorDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("Line editor")

        self.line: Line = line
        self.sbase: float = grid.Sbase
        self.frequency: float = grid.fBase
        self.templates: list[LineTemplate] = self._collect_templates(grid=grid)
        self.current_template: LineTemplate | None = line.template
        self.selected_template: LineTemplate | None = None

        self._configure_initial_values()
        self._configure_template_widgets()
        self._connect_signals()

    def _collect_templates(self, grid: MultiCircuit) -> list[LineTemplate]:
        """
        Filter line templates that match the branch nominal voltage.

        :param grid: Grid model containing template catalogues.
        :return: Matching template list.
        """
        nominal_voltage: float = self.line.get_max_bus_nominal_voltage()
        templates: list[LineTemplate] = list()

        for template_list in [grid.sequence_line_types, grid.underground_cable_types, grid.overhead_line_types]:
            for template in template_list:
                if nominal_voltage == template.Vnom:
                    templates.append(template)
                else:
                    pass

        return templates

    def _configure_initial_values(self) -> None:
        """
        Initialize all widget values from the current line state.
        """
        voltage_from: float = self.line.bus_from.Vnom
        self.ui.currentLabel.setText(f"Imax: Max. current @ {int(voltage_from)} [kV]")

        if voltage_from <= 0.0:
            error_msg(
                text=f"Vnom in bus {self.line.bus_from} is {voltage_from}\n"
                "That causes an infinite base admittance.\n"
                "The process has been aborted.\n"
                "Please correct the data and try again.",
                title="Line editor initialization",
            )
        else:
            zbase: float = (voltage_from * voltage_from) / self.sbase
            ybase: float = 1.0 / zbase
            length: float = self.line.length
            if length == 0.0:
                length = 1.0
            else:
                pass

            resistance_ohm_km: float = self.line.R * zbase / length
            reactance_ohm_km: float = self.line.X * zbase / length
            susceptance_us_km: float = self.line.B * ybase / length * 1e6
            current_ka: float = float(np.round(self.line.rate / (voltage_from * 1.73205080757), 6))

            self.ui.lengthSpinBox.setValue(length)
            self.ui.currentSpinBox.setValue(current_ka)
            self.ui.resistanceSpinBox.setValue(resistance_ohm_km)
            self.ui.reactanceSpinBox.setValue(reactance_ohm_km)
            self.ui.susceptanceSpinBox.setValue(susceptance_us_km)
            self.ui.circuitIndexSpinBox.setValue(max(1, int(self.line.circuit_idx)))
            self._try_apply_current_template_defaults()

    def _try_apply_current_template_defaults(self) -> None:
        """
        Prefill electrical values using the currently assigned template when available.
        """
        if self.current_template is None:
            return
        else:
            pass

        if self.current_template in self.templates:
            if isinstance(self.current_template, SequenceLineType) or isinstance(self.current_template, UndergroundLineType):
                self.ui.currentSpinBox.setValue(self.current_template.Imax)
                self.ui.resistanceSpinBox.setValue(self.current_template.R)
                self.ui.reactanceSpinBox.setValue(self.current_template.X)
                self.ui.susceptanceSpinBox.setValue(self.current_template.B)
            elif isinstance(self.current_template, OverheadLineType):
                if self.current_template.check():
                    sequence_values = self.current_template.get_sequence_values(
                        circuit_idx=self.line.circuit_idx,
                        seq=1,
                    )
                    self.ui.resistanceSpinBox.setValue(sequence_values[0])
                    self.ui.reactanceSpinBox.setValue(sequence_values[1])
                    self.ui.susceptanceSpinBox.setValue(sequence_values[2])
                    self.ui.currentSpinBox.setValue(sequence_values[3])
                    self.ui.circuitIndexSpinBox.setMaximum(max(1, int(self.current_template.n_circuits)))
                else:
                    warning_msg(
                        text=f"The template {self.current_template.name} contains errors",
                        title="Load template",
                    )
            else:
                pass
        else:
            pass

    def _configure_template_widgets(self) -> None:
        """
        Configure template-related widgets and defaults.
        """
        if len(self.templates) > 0:
            self.ui.catalogueComboBox.setModel(get_list_model(self.templates))
            if self.current_template in self.templates:
                template_index: int = self.templates.index(self.current_template)
                self.ui.catalogueComboBox.setCurrentIndex(template_index)
            else:
                pass
        else:
            self.ui.catalogueComboBox.setEnabled(False)
            self.ui.loadTemplateButton.setEnabled(False)

        if isinstance(self.current_template, OverheadLineType):
            self.ui.circuitIndexSpinBox.setMaximum(max(1, int(self.current_template.n_circuits)))
        else:
            self.ui.circuitIndexSpinBox.setMaximum(1)

    def _connect_signals(self) -> None:
        """
        Bind GUI signals to controller slots.
        """
        self.ui.acceptButton.clicked.connect(self.accept_click)
        self.ui.loadTemplateButton.clicked.connect(self.load_template_btn_click)
        self.ui.catalogueComboBox.currentIndexChanged.connect(self.update_max_circuits)

    def accept_click(self) -> None:
        """
        Persist the current line design values into the model and close the dialog.
        """
        length: float = self.ui.lengthSpinBox.value()
        if length == 0.0:
            error_msg(text="The length cannot be 0!", title="Accept line design values")
            return
        else:
            pass

        if self.selected_template is not None:
            self.line.disable_auto_updates()
            self.line.set_length(val=length)
            self.line.set_circuit_idx(val=int(self.ui.circuitIndexSpinBox.value()), obj=self.selected_template)
            self.line.apply_template(obj=self.selected_template, Sbase=self.sbase, freq=self.frequency)
            self.line.enable_auto_updates()
            self.accept()
        else:
            response: bool = yes_no_question(
                text="Warning: You did not load template values. The circuit index will not be updated. "
                "Line parameters will be based on the provided values for Length, Max Current, Resistance, "
                "Reactance, and Susceptance.\n\nDo you want to continue without a template?",
                title="No Template Selected",
            )

            if response:
                angular_frequency: float = 2.0 * np.pi * self.frequency
                self.line.fill_design_properties(
                    r_ohm=self.ui.resistanceSpinBox.value(),
                    x_ohm=self.ui.reactanceSpinBox.value(),
                    c_nf=self.ui.susceptanceSpinBox.value() * 1e3 / angular_frequency,
                    length=length,
                    Imax=self.ui.currentSpinBox.value(),
                    freq=self.frequency,
                    Sbase=self.sbase,
                    apply_to_profile=self.ui.applyToProfilesCheckBox.isChecked(),
                )
                self.accept()
            else:
                return

    def load_template(self, template: LineTemplate) -> None:
        """
        Apply the selected template values to the editor widgets.

        :param template: Template instance selected by the user.
        """
        if isinstance(template, SequenceLineType) or isinstance(template, UndergroundLineType):
            self.ui.currentSpinBox.setValue(template.Imax)
            self.ui.resistanceSpinBox.setValue(template.R)
            self.ui.reactanceSpinBox.setValue(template.X)
            self.ui.susceptanceSpinBox.setValue(template.B)
            self.selected_template = template
            self.ui.circuitIndexSpinBox.setMaximum(1)
        elif isinstance(template, OverheadLineType):
            if template.check():
                sequence_values = template.get_sequence_values(
                    circuit_idx=int(self.ui.circuitIndexSpinBox.value()),
                    seq=1,
                )
                self.ui.currentSpinBox.setValue(sequence_values[3])
                self.ui.resistanceSpinBox.setValue(sequence_values[0])
                self.ui.reactanceSpinBox.setValue(sequence_values[1])
                self.ui.susceptanceSpinBox.setValue(sequence_values[2])
                self.ui.circuitIndexSpinBox.setMaximum(max(1, int(template.n_circuits)))
                self.selected_template = template
            else:
                warning_msg(text=f"The template {template.name} contains errors", title="Load template")
        else:
            pass

    def load_template_btn_click(self) -> None:
        """
        Load the currently selected catalogue template into the form.
        """
        current_index: int = self.ui.catalogueComboBox.currentIndex()
        if -1 < current_index < len(self.templates):
            self.load_template(template=self.templates[current_index])
        else:
            pass

    def update_max_circuits(self) -> None:
        """
        Update circuit index bounds according to the current template selection.
        """
        current_index: int = self.ui.catalogueComboBox.currentIndex()
        if -1 < current_index < len(self.templates):
            template: LineTemplate = self.templates[current_index]
            if isinstance(template, OverheadLineType):
                self.ui.circuitIndexSpinBox.setMaximum(max(1, int(template.n_circuits)))
            else:
                self.ui.circuitIndexSpinBox.setMaximum(1)
        else:
            self.ui.circuitIndexSpinBox.setMaximum(1)


if __name__ == "__main__":
    qt_app = QtWidgets.QApplication(sys.argv)
    bus_from_demo = Bus(name="Bus from", Vnom=110.0)
    bus_to_demo = Bus(name="Bus to", Vnom=110.0)
    line_demo = Line(
        bus_from=bus_from_demo,
        bus_to=bus_to_demo,
        name="Demo line",
        length=15.0,
        r=0.01,
        x=0.08,
        b=0.001,
        rate=120.0,
        circuit_idx=1,
    )
    grid_demo = MultiCircuit(name="Line Editor Demo", Sbase=100.0, fbase=50.0)
    dialog_demo = LineEditor(line=line_demo, grid=grid_demo)
    dialog_demo.show()
    sys.exit(qt_app.exec())
