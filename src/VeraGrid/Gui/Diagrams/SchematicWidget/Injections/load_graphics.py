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
from VeraGrid.Gui.profile_wizard_utils import fill_substation_weather_profiles
from VeraGrid.Gui.Diagrams.generic_graphics import Polygon
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.injections_template_graphics import InjectionTemplateGraphicItem
from VeraGridEngine.Devices.Injections.load import Load
from VeraGrid.Gui.DeviceEditors.LoadDesigner.load_designer import LoadDesigner
from VeraGrid.Gui.DeviceEditors.LoadDesigner.load_device_editor import LoadDeviceEditorDialog

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget


class LoadGraphicItem(InjectionTemplateGraphicItem):

    def __init__(self, parent, api_obj: Load, editor: SchematicWidget, draw_labels: bool = True):
        """

        :param parent:
        :param api_obj:
        :param editor:
        """
        InjectionTemplateGraphicItem.__init__(self,
                                              parent=parent,
                                              api_obj=api_obj,
                                              editor=editor,
                                              device_type_name='load',
                                              w=20,
                                              h=20,
                                              draw_labels=draw_labels)

        # triangle
        self.set_glyph(glyph=Polygon(
            self,
            polygon=QPolygonF([QPointF(0, 0),
                               QPointF(self.w, 0),
                               QPointF(self.w / 2, self.h)]),
            update_nexus_fcn=self.update_nexus)
        )

    @property
    def api_object(self) -> Load:
        return self._api_object

    def open_device_editor(self) -> bool:
        """
        Open the load editor.

        :return: ``True`` when the editor was opened.
        """
        dlg = LoadDeviceEditorDialog(api_object=self.api_object, circuit=self.editor.circuit)
        if dlg.exec():
            return True
        else:
            return True

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
                           icon_path=":/Icons/icons/load_wizard.png")

            menu.exec(event.screenPos())
        else:
            self.editor.gui.show_error_toast("The graphic has no API object!")

    def load_profile_wizard(self) -> None:
        """
        Open the load profile composition wizard and apply the generated profiles.

        :return: None.
        """
        if self._editor.circuit.has_time_series:
            if self.api_object.bus is not None:
                bus_name: str = self.api_object.bus.name
                latitude: float | None = self.api_object.bus.latitude
                longitude: float| None = self.api_object.bus.longitude
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
                        self.editor.gui.show_error_toast("Wrong length from the load profile wizard")
                else:
                    pass
            else:
                pass
        else:
            self.editor.gui.show_error_toast("You need to have time profiles for this function")
