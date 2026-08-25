# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys
from PySide6 import QtWidgets

from VeraGrid.Gui.DeviceEditors.TransformerEditor.transformer_editor_gui import Ui_TransformerEditorDialog
import VeraGrid.Gui.gui_functions as gf
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Branches.transformer_type import TransformerType
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import TapChangerTypes


class TransformerEditor(QtWidgets.QDialog):
    """
    Transformer 2-winding editor controller backed by a Qt Designer `.ui`.
    """

    def __init__(self, branch: Transformer2W, grid: MultiCircuit, modify_on_accept: bool = True) -> None:
        """
        Build the transformer editor view/controller.

        :param branch: Transformer object being edited.
        :param grid: Grid model containing base values and template catalogue.
        :param modify_on_accept: Whether to apply changes directly when accepted.
        """
        super().__init__()
        self.ui = Ui_TransformerEditorDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr("Transformer editor"))

        self.transformer_obj: Transformer2W = branch
        self.sbase: float = grid.Sbase
        self.modify_on_accept: bool = modify_on_accept
        self.templates: list[TransformerType] = self.filter_valid_templates(grid.transformer_types)
        self.current_template: TransformerType | None = branch.template
        self.selected_template: TransformerType | None = None

        self._configure_initial_values()
        self._connect_signals()

    def _configure_initial_values(self) -> None:
        """
        Initialize catalogue and numerical fields from either template or current object values.
        """
        sn_value: float = self.transformer_obj.Sn
        pcu_value: float = self.transformer_obj.Pcu
        pfe_value: float = self.transformer_obj.Pfe
        i0_value: float = self.transformer_obj.I0
        vsc_value: float = self.transformer_obj.Vsc

        if len(self.templates) > 0:
            self.ui.catalogueComboBox.setModel(gf.get_list_model(self.templates))
            if self.current_template in self.templates:
                template_index: int = self.templates.index(self.current_template)
                self.ui.catalogueComboBox.setCurrentIndex(template_index)
                sn_value = self.current_template.Sn
                pcu_value = self.current_template.Pcu
                pfe_value = self.current_template.Pfe
                i0_value = self.current_template.I0
                vsc_value = self.current_template.Vsc
            else:
                pass
        else:
            self.ui.catalogueComboBox.setEnabled(False)
            self.ui.loadTemplateButton.setEnabled(False)

        self.ui.snSpinBox.setValue(sn_value)
        self.ui.pcuSpinBox.setValue(pcu_value)
        self.ui.pfeSpinBox.setValue(pfe_value)
        self.ui.i0SpinBox.setValue(i0_value)
        self.ui.vscSpinBox.setValue(vsc_value)

        tap_types: list[TapChangerTypes] = [
            TapChangerTypes.NoRegulation,
            TapChangerTypes.Symmetrical,
            TapChangerTypes.Asymmetrical,
            TapChangerTypes.VoltageRegulation,
        ]
        self.ui.tapChangerTypeComboBox.setModel(gf.ComboModel(enum_values=tap_types, translate=self.tr))
        tap_type_index: int = self.ui.tapChangerTypeComboBox.findData(self.transformer_obj.tap_changer.tc_type)
        if tap_type_index >= 0:
            self.ui.tapChangerTypeComboBox.setCurrentIndex(tap_type_index)
        else:
            self.ui.tapChangerTypeComboBox.setCurrentIndex(0)

        self.ui.asymmetryAngleSpinBox.setValue(self.transformer_obj.tap_changer.asymmetry_angle)
        self.ui.totalPositionsSpinBox.setValue(self.transformer_obj.tap_changer.total_positions)
        self.ui.neutralPositionSpinBox.setValue(self.transformer_obj.tap_changer.neutral_position)
        self.ui.tapPositionSpinBox.setValue(self.transformer_obj.tap_changer.tap_position)
        self.ui.dvSpinBox.setValue(self.transformer_obj.tap_changer.dV)

    def _connect_signals(self) -> None:
        """
        Bind GUI actions to controller slots.
        """
        self.ui.loadTemplateButton.clicked.connect(self.load_template_btn_click)
        self.ui.acceptButton.clicked.connect(self.accept_click)

    def filter_valid_templates(self, templates: list[TransformerType] | None, pu_range: float = 0.1) -> list[TransformerType]:
        """
        Keep templates that match current transformer nominal voltages within tolerance.

        :param templates: Candidate template list.
        :param pu_range: Relative voltage tolerance.
        :return: Filtered list.
        """
        if templates is None:
            return list()
        else:
            pass

        valid_templates: list[TransformerType] = list()
        voltage_from: float = self.transformer_obj.bus_from.Vnom
        voltage_to: float = self.transformer_obj.bus_to.Vnom
        upper: float = 1.0 + pu_range
        lower: float = 1.0 - pu_range

        for template in templates:
            hv_upper: float = template.HV * upper
            hv_lower: float = template.HV * lower
            lv_upper: float = template.LV * upper
            lv_lower: float = template.LV * lower

            voltage_from_matches: bool = (hv_lower < voltage_from < hv_upper) or (lv_lower < voltage_from < lv_upper)
            voltage_to_matches: bool = (hv_lower < voltage_to < hv_upper) or (lv_lower < voltage_to < lv_upper)

            if voltage_from_matches and voltage_to_matches:
                valid_templates.append(template)
            else:
                pass

        return valid_templates

    def get_template(self) -> TransformerType:
        """
        Build a temporary transformer template from current widget values.

        :return: Synthesized template instance.
        """
        epsilon: float = 1e-20
        voltage_from: float = self.transformer_obj.bus_from.Vnom
        voltage_to: float = self.transformer_obj.bus_to.Vnom
        nominal_power: float = self.ui.snSpinBox.value() + epsilon
        copper_losses: float = self.ui.pcuSpinBox.value() + epsilon
        iron_losses: float = self.ui.pfeSpinBox.value() + epsilon
        no_load_current: float = self.ui.i0SpinBox.value() + epsilon
        short_circuit_voltage: float = self.ui.vscSpinBox.value()

        if iron_losses == 0.0:
            iron_losses = epsilon
        else:
            pass
        if no_load_current == 0.0:
            no_load_current = epsilon
        else:
            pass

        template: TransformerType = TransformerType(
            hv_nominal_voltage=voltage_from,
            lv_nominal_voltage=voltage_to,
            nominal_power=nominal_power,
            copper_losses=copper_losses,
            iron_losses=iron_losses,
            no_load_current=no_load_current,
            short_circuit_voltage=short_circuit_voltage,
            gr_hv1=0.5,
            gx_hv1=0.5,
        )
        return template

    def accept_click(self) -> None:
        """
        Apply selected or synthesized template and accept dialog.
        """
        if self.modify_on_accept:
            if self.selected_template is None:
                template: TransformerType = self.get_template()
            else:
                template = self.selected_template
            self.transformer_obj.apply_template(obj=template, Sbase=self.sbase)
            self._apply_tap_changer_values()
        else:
            pass
        self.accept()

    def _apply_tap_changer_values(self) -> None:
        """
        Apply tap changer values from GUI controls to the transformer model.
        """
        tap_changer_obj = self.transformer_obj.tap_changer
        tap_changer_obj.asymmetry_angle = self.ui.asymmetryAngleSpinBox.value()
        tap_changer_obj.total_positions = self.ui.totalPositionsSpinBox.value()
        tap_changer_obj.tap_position = self.ui.tapPositionSpinBox.value()
        tap_changer_obj.dV = self.ui.dvSpinBox.value()
        tap_changer_obj.neutral_position = self.ui.neutralPositionSpinBox.value()

        tap_changer_obj.tc_type = self.ui.tapChangerTypeComboBox.currentData()

        tap_changer_obj.recalc()

    def load_template(self, template: TransformerType) -> None:
        """
        Load a template values into the form.

        :param template: Selected template.
        """
        self.ui.snSpinBox.setValue(template.Sn)
        self.ui.pcuSpinBox.setValue(template.Pcu)
        self.ui.pfeSpinBox.setValue(template.Pfe)
        self.ui.i0SpinBox.setValue(template.I0)
        self.ui.vscSpinBox.setValue(template.Vsc)
        self.selected_template = template

    def load_template_btn_click(self) -> None:
        """
        Load currently selected template into field controls.
        """
        current_index: int = self.ui.catalogueComboBox.currentIndex()
        if -1 < current_index < len(self.templates):
            selected_template: TransformerType = self.templates[current_index]
            self.load_template(template=selected_template)
        else:
            pass


if __name__ == "__main__":
    qt_app = QtWidgets.QApplication(sys.argv)
    bus_from_demo = Bus(name="HV bus", Vnom=132.0)
    bus_to_demo = Bus(name="MV bus", Vnom=33.0)
    transformer_demo = Transformer2W(
        bus_from=bus_from_demo,
        bus_to=bus_to_demo,
        name="Demo transformer",
        nominal_power=40.0,
        copper_losses=120.0,
        iron_losses=30.0,
        no_load_current=0.5,
        short_circuit_voltage=10.0,
    )
    grid_demo = MultiCircuit(name="Transformer Editor Demo", Sbase=100.0, fbase=50.0)
    dialog_demo = TransformerEditor(branch=transformer_demo, grid=grid_demo, modify_on_accept=True)
    dialog_demo.show()
    sys.exit(qt_app.exec())
