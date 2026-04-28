# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6 import QtWidgets
from VeraGridEngine.Devices.Injections.static_generator import StaticGenerator
from VeraGrid.Gui.gui_functions import add_menu_entry
from VeraGrid.Gui.Diagrams.MapWidget.Injections.map_injections_template_graphics import MapInjectionTemplateGraphicItem
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_workspace_manager import open_dynamic_editor
from VeraGridEngine.enumerations import DynamicSimulationMode

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.MapWidget.grid_map_widget import GridMapWidget


class MapStaticGeneratorGraphicItem(MapInjectionTemplateGraphicItem):

    def __init__(self, api_object: StaticGenerator,
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
    def api_object(self) -> StaticGenerator:
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
                           text="RMS Editor",
                           function_ptr=self.edit_rms,
                           icon_path=":/Icons/icons/dyn_edit.png")

            add_menu_entry(menu=menu,
                           text="EMT Editor",
                           function_ptr=self.edit_emt,
                           icon_path=":/Icons/icons/dyn_emt_edit.png")

            menu.exec(event.screenPos())
        else:
            self.editor.gui.show_error_toast("The graphic has no API object!")

    def edit_rms(self):
        """

        :return:
        """
        open_dynamic_editor(api_object=self.api_object, circuit=self.editor.circuit,
                            preferred_mode=DynamicSimulationMode.RMS)

    def edit_emt(self):
        """
        Open the EMT dynamic model editor for this generator.

        :return: None.
        """

        open_dynamic_editor(api_object=self.api_object, circuit=self.editor.circuit,
                            preferred_mode=DynamicSimulationMode.EMT)