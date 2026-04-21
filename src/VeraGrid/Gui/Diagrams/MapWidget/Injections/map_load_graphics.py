# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6 import QtWidgets
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPolygonF
from VeraGrid.Gui.gui_functions import add_menu_entry
from VeraGrid.Gui.messages import info_msg
from VeraGrid.Gui.profile_wizard_utils import fill_substation_weather_profiles
from VeraGrid.Gui.Diagrams.generic_graphics import Polygon
from VeraGrid.Gui.Diagrams.MapWidget.Injections.map_injections_template_graphics import MapInjectionTemplateGraphicItem
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_workspace_manager import open_dynamic_editor
from VeraGrid.Gui.LoadDesigner.load_designer import LoadDesigner
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.enumerations import DeviceType, FmuTemplateDomain, DynamicSimulationMode

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.MapWidget.grid_map_widget import GridMapWidget


class MapLoadGraphicItem(MapInjectionTemplateGraphicItem):

    def __init__(self, api_object: Load,
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
    def api_object(self) -> Load:
        return self._api_object

    def contextMenuEvent(self, event: QtWidgets.QGraphicsSceneContextMenuEvent):
        """
        Display context menu
        @param event:
        @return:
        """
        if self.api_object is not None:
            menu = self.get_base_context_menu()
            menu.addSection("Load")

            add_menu_entry(menu=menu,
                           text="Load profile wizard",
                           function_ptr=self.load_profile_wizard,
                           icon_path=":/Icons/icons/gear.png")

            add_menu_entry(menu=menu,
                           text="Dynamic Editor",
                           function_ptr=self.edit_dynamic,
                           icon_path=":/Icons/icons/edit.png")

            menu.exec(event.screenPos())
        else:
            self.editor.gui.show_error_toast("The graphic has no API object!")

    def edit_rms(self):
        open_dynamic_editor(api_object=self.api_object, circuit=self.editor.circuit,
                            preferred_mode=DynamicSimulationMode.RMS)

    def edit_emt(self):
        """
        Open the EMT dynamic model editor for this load.

        :return: None.
        """

        open_dynamic_editor(api_object=self.api_object, circuit=self.editor.circuit,
                            preferred_mode=DynamicSimulationMode.EMT)

    def edit_dynamic(self):
        """
        Open the unified dynamic editor workspace for this map load.
        """

        open_dynamic_editor(api_object=self.api_object, circuit=self.editor.circuit)

    def load_profile_wizard(self) -> None:
        """
        Open the load profile composition wizard and apply the generated profiles.

        :return: None.
        """
        if self._editor.circuit.has_time_series:
            if self.api_object.bus is not None:
                bus_name: str = self.api_object.bus.name
                latitude: float | None = self.api_object.bus.latitude
                longitude: float | None = self.api_object.bus.longitude
            else:
                bus_name = ""
                latitude = None
                longitude = None

            dlg: LoadDesigner = LoadDesigner(time_array=self._editor.circuit.time_profile,
                                             active_power=self.api_object.P,
                                             reactive_power=self.api_object.Q,
                                             latitude=latitude,
                                             longitude=longitude,
                                             load_name=self.api_object.name,
                                             bus_name=bus_name)

            if dlg.exec():
                if dlg.is_accepted:
                    if len(dlg.P) == self.api_object.P_prof.size() and len(dlg.Q) == self.api_object.Q_prof.size():
                        self.api_object.P_prof.set(dlg.P)
                        self.api_object.Q_prof.set(dlg.Q)
                        if self.api_object.bus is not None:
                            fill_substation_weather_profiles(bus=self.api_object.bus,
                                                             temperature=dlg.temperature,
                                                             wind_speed=dlg.wind_speed,
                                                             irradiation=None,
                                                             expected_size=self.api_object.P_prof.size())
                        else:
                            pass
                        self.plot()
                    else:
                        raise Exception("Wrong length from the load profile wizard")
                else:
                    pass
            else:
                pass
        else:
            info_msg("You need to have time profiles for this function")
