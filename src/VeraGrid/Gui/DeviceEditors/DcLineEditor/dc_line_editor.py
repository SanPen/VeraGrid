# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys

import numpy as np
from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.DeviceEditors.DcLineEditor.dc_line_editor_gui import Ui_DcLineEditorDialog
from VeraGrid.Gui.gui_functions import get_list_model
from VeraGrid.Gui.messages import warning_msg
from VeraGridEngine.Devices.Branches.dc_line import DcLine
from VeraGridEngine.Devices.Branches.line import OverheadLineType, SequenceLineType, UndergroundLineType
from VeraGridEngine.Devices.Substation.bus import Bus

DcLineTemplate = SequenceLineType | OverheadLineType | UndergroundLineType


class DcLineEditor(QtWidgets.QDialog):
    """
    DC line editor backed by a Qt Designer `.ui` file.
    """

    def __init__(
        self,
        branch: DcLine,
        Sbase: float = 100.0,
        templates: list[DcLineTemplate] | None = None,
        current_template: DcLineTemplate | None = None,
    ) -> None:
        """
        Build DC line editor controller.

        :param branch: Branch object to update.
        :param Sbase: Base power in MVA.
        :param templates: Compatible templates.
        :param current_template: Current selected template.
        """
        super().__init__()
        self.ui = Ui_DcLineEditorDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr("Line editor"))

        self.branch: DcLine = branch
        self.sbase: float = Sbase
        self.templates: list[DcLineTemplate] | None = templates
        self.current_template: DcLineTemplate | None = current_template
        self.selected_template: DcLineTemplate | None = None

        self._configure_initial_values()
        self._connect_signals()

    def _configure_initial_values(self) -> None:
        """
        Initialize widgets from branch values and current template.
        """
        voltage_from: float = self.branch.bus_from.Vnom
        self.ui.currentLabel.setText(f"Imax: Max. current [kA] @ {int(voltage_from)} [kV]")

        zbase: float = self.sbase / (voltage_from * voltage_from)
        resistance_ohm: float = self.branch.R * zbase
        current_ka: float = self.branch.rate / voltage_from

        self.ui.lengthSpinBox.setValue(1.0)
        self.ui.currentSpinBox.setValue(current_ka)
        self.ui.resistanceSpinBox.setValue(resistance_ohm)

        self._configure_templates(initial_resistance=resistance_ohm, initial_current=current_ka)

    def _configure_templates(self, initial_resistance: float, initial_current: float) -> None:
        """
        Configure template widgets and optional initial value overrides.

        :param initial_resistance: Resistance fallback value.
        :param initial_current: Current fallback value.
        """
        resistance_value: float = initial_resistance
        current_value: float = initial_current

        if self.templates is not None and len(self.templates) > 0:
            self.ui.catalogueComboBox.setModel(get_list_model(self.templates))

            if self.current_template is not None and self.current_template in self.templates:
                template_index: int = self.templates.index(self.current_template)
                self.ui.catalogueComboBox.setCurrentIndex(template_index)

                if isinstance(self.current_template, SequenceLineType):
                    current_value = self.current_template.Imax
                    resistance_value = self.current_template.R
                elif isinstance(self.current_template, UndergroundLineType):
                    current_value = self.current_template.Imax
                    resistance_value = self.current_template.R
                elif isinstance(self.current_template, OverheadLineType):
                    if self.current_template.check():
                        sequence_values = self.current_template.get_sequence_values(circuit_idx=0, seq=1)
                        current_value = sequence_values[3]
                        resistance_value = sequence_values[0]
                    else:
                        warning_msg(
                            text=self.tr("The template {template_name} contains errors").format(
                                template_name=self.current_template.name,
                            ),
                            title=self.tr("Load template"),
                        )
                else:
                    pass
            else:
                pass
        else:
            self.ui.templatesLabel.setVisible(False)
            self.ui.catalogueComboBox.setVisible(False)
            self.ui.loadTemplateButton.setVisible(False)
            self.ui.lineSeparator.setVisible(False)

        self.ui.currentSpinBox.setValue(current_value)
        self.ui.resistanceSpinBox.setValue(resistance_value)

    def _connect_signals(self) -> None:
        """
        Connect GUI signals to controller methods.
        """
        self.ui.loadTemplateButton.clicked.connect(self.load_template_btn_click)
        self.ui.acceptButton.clicked.connect(self.accept_click)

    def accept_click(self) -> None:
        """
        Apply edited line parameters into the model and accept dialog.
        """
        length_value: float = self.ui.lengthSpinBox.value()
        current_value: float = self.ui.currentSpinBox.value()
        resistance_ohm: float = self.ui.resistanceSpinBox.value() * length_value

        voltage_from: float = self.branch.bus_from.Vnom
        nominal_power: float = float(np.round(current_value * voltage_from, 2))
        zbase: float = self.sbase / (voltage_from * voltage_from)

        self.branch.R = float(np.round(resistance_ohm / zbase, 6))
        self.branch.rate = nominal_power

        if self.selected_template is not None:
            self.branch.template = self.selected_template
        else:
            pass

        self.accept()

    def load_template(self, template: DcLineTemplate) -> None:
        """
        Load template values into the form controls.

        :param template: Selected template.
        """
        if isinstance(template, SequenceLineType):
            self.ui.currentSpinBox.setValue(template.Imax)
            self.ui.resistanceSpinBox.setValue(template.R)
            self.selected_template = template
        elif isinstance(template, UndergroundLineType):
            self.ui.currentSpinBox.setValue(template.Imax)
            self.ui.resistanceSpinBox.setValue(template.R)
            self.selected_template = template
        elif isinstance(template, OverheadLineType):
            if template.check():
                sequence_values = template.get_sequence_values(circuit_idx=0, seq=1)
                self.ui.currentSpinBox.setValue(sequence_values[3])
                self.ui.resistanceSpinBox.setValue(sequence_values[0])
                self.selected_template = template
            else:
                warning_msg(
                    text=self.tr("The template {template_name} contains errors").format(template_name=template.name),
                    title=self.tr("Load template"),
                )
        else:
            pass

    def load_template_btn_click(self) -> None:
        """
        Load currently selected template from catalogue.
        """
        if self.templates is not None and len(self.templates) > 0:
            template_index: int = self.ui.catalogueComboBox.currentIndex()
            if -1 < template_index < len(self.templates):
                self.load_template(template=self.templates[template_index])
            else:
                pass
        else:
            pass


if __name__ == "__main__":
    qt_app = QtWidgets.QApplication(sys.argv)
    bus_from_demo = Bus(name="DC from", Vnom=320.0, is_dc=True)
    bus_to_demo = Bus(name="DC to", Vnom=320.0, is_dc=True)
    dc_line_demo = DcLine(
        bus_from=bus_from_demo,
        bus_to=bus_to_demo,
        name="Demo DC line",
        r=0.02,
        rate=500.0,
    )
    dialog_demo = DcLineEditor(branch=dc_line_demo, Sbase=100.0, templates=None, current_template=None)
    dialog_demo.show()
    sys.exit(qt_app.exec())
