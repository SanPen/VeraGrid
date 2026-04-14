# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import TYPE_CHECKING
import numpy as np

from PySide6.QtWidgets import QGraphicsSceneContextMenuEvent
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGrid.Gui.Diagrams.Editors.generator_editor import GeneratorQCurveEditor
from VeraGrid.Gui.messages import yes_no_question, info_msg
from VeraGrid.Gui.Diagrams.MapWidget.Injections.map_injections_template_graphics import MapInjectionTemplateGraphicItem
from VeraGrid.Gui.SolarPowerWizard.solar_power_wizzard import SolarPvWizard
from VeraGrid.Gui.WindPowerWizard.wind_power_wizzard import WindFarmWizard
from VeraGrid.Gui.gui_functions import add_menu_entry
from VeraGrid.Gui.RmsModelEditor.rms_model_editor_engine import RmsModelEditorGUI
from VeraGridEngine.enumerations import DeviceType

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.MapWidget.grid_map_widget import GridMapWidget


class MapGeneratorGraphicItem(MapInjectionTemplateGraphicItem):
    """
    GeneratorGraphicItem
    """

    def __init__(self, api_object: Generator,
                 editor: GridMapWidget,
                 lat: float,
                 lon: float,
                 size: float = 0.8,
                 draw_labels: bool = True):
        """

        :param api_object:
        :param editor:
        """
        MapInjectionTemplateGraphicItem.__init__(self,
                                                 api_object=api_object,
                                                 editor=editor,
                                                 lat=lat,
                                                 lon=lon,
                                                 size=size,
                                                 draw_labels=draw_labels)

    @property
    def api_object(self) -> Generator:
        return self._api_object

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        """
        Display context menu
        @param event:
        @return:
        """
        menu = self.get_base_context_menu()

        menu.addSection("Generator")

        add_menu_entry(menu=menu,
                       text="Voltage control",
                       icon_path="",
                       function_ptr=self.enable_disable_control_toggle,
                       checkeable=True,
                       checked_value=self.api_object.is_controlled)

        add_menu_entry(menu=menu,
                       text="Rms Editor",
                       function_ptr=self.edit_rms,
                       icon_path=":/Icons/icons/edit.png")

        add_menu_entry(menu=menu,
                       text="Qcurve edit",
                       function_ptr=self.edit_q_curve,
                       icon_path=":/Icons/icons/edit.png")

        menu.addSeparator()

        add_menu_entry(menu=menu,
                       text="Solar photovoltaic wizard",
                       icon_path=":/Icons/icons/solar_power.png",
                       function_ptr=self.solar_pv_wizard)

        add_menu_entry(menu=menu,
                       text="Wind farm wizard",
                       icon_path=":/Icons/icons/wind_power.png",
                       function_ptr=self.wind_farm_wizard)

        menu.addSeparator()

        add_menu_entry(menu=menu,
                       text="Convert to battery",
                       icon_path=":/Icons/icons/add_batt.png",
                       function_ptr=self.to_battery)

        menu.exec(event.screenPos())

    def edit_rms(self):
        """

        :return:
        """
        # load templates
        templates = self.editor.circuit.rms_models

        # select line templates
        templ_catalogue = dict()
        templ_list = []
        for templ in templates:
            if templ.tpe == DeviceType.GeneratorDevice:
                templ_list.append(templ.name)
                templ_catalogue[templ.name] = templ

        # prompt RmsModelEditorGUI

        rms_model_editor = RmsModelEditorGUI(api_object_model_host=self.api_object.rms_model, templates_list=templ_list,
                                             templates_catalogue=templ_catalogue, api_object_name=self.api_object.name,
                                             api_object=self.api_object, main_editor=True, parent=self.editor)
        rms_model_editor.show()

    def to_battery(self):
        """
        Convert this generator to a battery
        """
        ok = yes_no_question('Are you sure that you want to convert this generator into a battery?',
                             'Convert generator')
        if ok:
            self._editor.convert_generator_to_battery(gen=self.api_object, graphic_object=self)

    def enable_disable_control_toggle(self):
        """
        Enable / Disable device voltage control
        """
        if self.api_object is not None:
            self.api_object.is_controlled = not self.api_object.is_controlled

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

    def solar_pv_wizard(self):
        """
        Open the appropriate editor dialogue
        :return:
        """

        if self._editor.circuit.has_time_series:

            dlg = SolarPvWizard(time_array=self._editor.circuit.time_profile.strftime("%Y-%m-%d %H:%M").tolist(),
                                peak_power=self.api_object.Pmax,
                                latitude=self.api_object.bus.latitude,
                                longitude=self.api_object.bus.longitude,
                                gen_name=self.api_object.name,
                                bus_name=self.api_object.bus.name)
            if dlg.exec():
                if dlg.is_accepted:
                    if len(dlg.P) == self.api_object.P_prof.size():
                        self.api_object.P_prof.set(dlg.P)

                        self.plot()
                    else:
                        raise Exception("Wrong length from the solar photovoltaic wizard")
        else:
            info_msg("You need to have time profiles for this function")

    def wind_farm_wizard(self):
        """
        Open the appropriate editor dialogue
        :return:
        """

        if self._editor.circuit.has_time_series:

            dlg = WindFarmWizard(time_array=self._editor.circuit.time_profile.strftime("%Y-%m-%d %H:%M").tolist(),
                                 peak_power=self.api_object.Pmax,
                                 latitude=self.api_object.bus.latitude,
                                 longitude=self.api_object.bus.longitude,
                                 gen_name=self.api_object.name,
                                 bus_name=self.api_object.bus.name)
            if dlg.exec():
                if dlg.is_accepted:
                    if len(dlg.P) == self.api_object.P_prof.size():
                        self.api_object.P_prof.set(dlg.P)
                        self.plot()
                    else:
                        raise Exception("Wrong length from the solar photovoltaic wizard")
        else:
            info_msg("You need to have time profiles for this function")
