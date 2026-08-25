# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import TYPE_CHECKING
import numpy as np
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGrid.Gui.Diagrams.generic_graphics import GeneratorSymbol
from VeraGrid.Gui.messages import yes_no_question
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.injections_template_graphics import InjectionTemplateGraphicItem
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.generator_editor import GeneratorEditorDialog, GeneratorQCurveEditor
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.SolarPowerWizard.solar_power_wizzard import SolarPvWizard
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.WindPowerWizard.wind_power_wizzard import WindFarmWizard
from VeraGrid.Gui.profile_wizard_utils import fill_substation_weather_profiles
from VeraGrid.Gui.gui_functions import add_menu_entry, translate_context_menu_text
from VeraGridEngine.enumerations import DynamicSimulationMode


if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget


class GeneratorGraphicItem(InjectionTemplateGraphicItem):
    """
    GeneratorGraphicItem
    """

    def __init__(self, parent, api_obj: Generator, editor: SchematicWidget, draw_labels: bool = True):
        """

        :param parent:
        :param api_obj:
        :param editor:
        """
        InjectionTemplateGraphicItem.__init__(self,
                                              parent=parent,
                                              api_obj=api_obj,
                                              editor=editor,
                                              device_type_name='generator',
                                              w=40,
                                              h=40,
                                              draw_labels=draw_labels)
        self.set_glyph(glyph=GeneratorSymbol(self, 40, 40))

    @property
    def api_object(self) -> Generator:
        return self._api_object

    def open_device_editor(self) -> bool:
        """
        Open the generator editor.

        :return: ``True`` when the editor was opened.
        """
        dlg = GeneratorEditorDialog(api_object=self.api_object, circuit=self.editor.circuit)
        if dlg.exec():
            return True
        else:
            return True

    def contextMenuEvent(self, event):
        """
        Display context menu
        @param event:
        @return:
        """
        menu = self.get_base_context_menu()
        menu.addSection(translate_context_menu_text("Generator"))

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Set regulation bus"),
                       icon_path="",
                       function_ptr=self.set_regulation_bus)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Qcurve edit"),
                       function_ptr=self.edit_q_curve,
                       icon_path=":/Icons/icons/edit.png")

        menu.addSeparator()

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Solar photovoltaic wizard"),
                       icon_path=":/Icons/icons/solar_power.png",
                       function_ptr=self.solar_pv_wizard)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Wind farm wizard"),
                       icon_path=":/Icons/icons/wind_power.png",
                       function_ptr=self.wind_farm_wizard)

        menu.addSeparator()

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Convert to battery"),
                       icon_path=":/Icons/icons/add_batt.png",
                       function_ptr=self.to_battery)

        menu.exec_(event.screenPos())

    def mouseDoubleClickEvent(self, event):
        """
        Open the generator editor on double click.

        :param event: Mouse event.
        :return: None.
        """
        super().mouseDoubleClickEvent(event)

    def edit_dynamic_rms(self):
        """
        Open the unified dynamic editor workspace for this generator.
        """

        self.editor.gui.open_dynamic_editor(api_object=self.api_object,
                                            circuit=self.editor.circuit,
                                            preferred_mode=DynamicSimulationMode.RMS)

    def edit_dynamic_emt(self):
        """
        Open the unified dynamic editor workspace for this generator.
        """

        self.editor.gui.open_dynamic_editor(api_object=self.api_object,
                                            circuit=self.editor.circuit,
                                            preferred_mode=DynamicSimulationMode.EMT)

    def to_battery(self):
        """
        Convert this generator to a battery
        """
        ok = yes_no_question(self.tr('Are you sure that you want to convert this generator into a battery?'),
                             self.tr('Convert generator'))
        if ok:
            self._editor.convert_generator_to_battery(gen=self.api_object, graphic_object=self)

    def set_regulation_bus(self):
        """
        Set regulation bus
        :return:
        """
        self._editor.set_generator_control_bus(generator_graphics=self)

    def clear_regulation_bus(self):
        """

        :return:
        """
        self.api_object.control_bus = None

    def clear_regulation_cn(self):
        """

        :return:
        """
        self.api_object.control_cn = None

    def edit_q_curve(self):
        """
        Open the appropriate editor dialogue
        :return:
        """
        dlg = GeneratorQCurveEditor(q_curve=self.api_object.q_curve,
                                    Qmin=self.api_object.Qmin,
                                    Qmax=self.api_object.Qmax,
                                    Pmin=self.api_object.Pmin,
                                    Pmax=self.api_object.Pmax,
                                    Snom=self.api_object.Snom)
        if dlg.exec():
            pass

        self.api_object.Snom = np.round(dlg.Snom, 1) if dlg.Snom > 1 else dlg.Snom
        self.api_object.Qmin = dlg.Qmin
        self.api_object.Qmax = dlg.Qmax
        self.api_object.Pmin = dlg.Pmin
        self.api_object.Pmax = dlg.Pmax

    def edit_generator(self):
        """
        Open the full generator editor dialogue.

        :return: None.
        """
        self.open_device_editor()

    def solar_pv_wizard(self):
        """
        Open the appropriate editor dialogue
        :return:
        """

        if self._editor.circuit.has_time_series:

            dlg = SolarPvWizard(time_array=self._editor.circuit.time_profile,
                                peak_power=self.api_object.Pmax,
                                latitude=self.api_object.bus.latitude,
                                longitude=self.api_object.bus.longitude,
                                gen_name=self.api_object.name,
                                bus_name=self.api_object.bus.name)
            if dlg.exec():
                if dlg.is_accepted:
                    if len(dlg.P) == self.api_object.P_prof.size():
                        self.api_object.P_prof.set(dlg.P)
                        fill_substation_weather_profiles(bus=self.api_object.bus,
                                                         temperature=dlg.temperature,
                                                         wind_speed=dlg.wind_speed,
                                                         irradiation=dlg.irradiation,
                                                         expected_size=self.api_object.P_prof.size())

                        self.plot()
                    else:
                        self.editor.gui.show_error_toast("Wrong length from the solar photovoltaic wizard")
        else:
            self.editor.gui.show_error_toast("You need to have time profiles for this function")

    def wind_farm_wizard(self):
        """
        Open the appropriate editor dialogue
        :return:
        """

        if self._editor.circuit.has_time_series:

            dlg = WindFarmWizard(time_array=self._editor.circuit.time_profile,
                                 peak_power=self.api_object.Pmax,
                                 latitude=self.api_object.bus.latitude,
                                 longitude=self.api_object.bus.longitude,
                                 gen_name=self.api_object.name,
                                 bus_name=self.api_object.bus.name)
            if dlg.exec():
                if dlg.is_accepted:
                    if len(dlg.P) == self.api_object.P_prof.size():
                        self.api_object.P_prof.set(dlg.P)
                        fill_substation_weather_profiles(bus=self.api_object.bus,
                                                         temperature=dlg.temperature,
                                                         wind_speed=dlg.wind_speed,
                                                         irradiation=None,
                                                         expected_size=self.api_object.P_prof.size())
                        self.plot()
                    else:
                        self.editor.gui.show_error_toast("Wrong length from the wind farm wizard")
        else:
            self.editor.gui.show_error_toast("You need to have time profiles for this function")
