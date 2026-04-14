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
from VeraGrid.Gui.Diagrams.generic_graphics import Polygon
from VeraGrid.Gui.Diagrams.MapWidget.Injections.map_injections_template_graphics import MapInjectionTemplateGraphicItem
from VeraGrid.Gui.RmsModelEditor.rms_model_editor_engine import RmsModelEditorGUI
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.enumerations import DeviceType

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
                           text="Rms Editor",
                           function_ptr=self.edit_rms,
                           icon_path=":/Icons/icons/edit.png")

            menu.exec(event.screenPos())
        else:
            self.editor.gui.show_error_toast("The graphic has no API object!")

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
            if templ.tpe == DeviceType.LoadDevice:
                templ_list.append(templ.name)
                templ_catalogue[templ.name] = templ

        # prompt RmsModelEditorGUI
        rms_model_editor = RmsModelEditorGUI(api_object_model_host=self.api_object.rms_model, templates_list=templ_list,
                                             templates_catalogue=templ_catalogue, api_object_name=self.api_object.name,
                                             api_object=self.api_object, main_editor= True, parent=self.editor)
        rms_model_editor.show()
