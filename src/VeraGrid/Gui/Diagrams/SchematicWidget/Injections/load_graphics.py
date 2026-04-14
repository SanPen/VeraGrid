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
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.injections_template_graphics import InjectionTemplateGraphicItem
from VeraGrid.Gui.RmsModelEditor.rms_model_editor_engine import RmsModelEditorGUI
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.enumerations import DeviceType

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget


class LoadGraphicItem(InjectionTemplateGraphicItem):

    def __init__(self, parent, api_obj: Load, editor: SchematicWidget):
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
                                              h=20)

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
