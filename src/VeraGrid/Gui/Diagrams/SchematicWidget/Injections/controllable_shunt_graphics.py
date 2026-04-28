# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6 import QtWidgets

from VeraGrid.Gui.Diagrams.generic_graphics import Square
from VeraGridEngine.Devices.Injections.controllable_shunt import ControllableShunt
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.injections_template_graphics import InjectionTemplateGraphicItem
from VeraGrid.Gui.DeviceEditors.ControllableShuntEditor.controllable_shunt_editor import ControllableShuntEditor
from VeraGrid.Gui.gui_functions import add_menu_entry

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget


class ControllableShuntGraphicItem(InjectionTemplateGraphicItem):
    """
    ExternalGrid graphic item
    """

    def __init__(self, parent, api_obj: ControllableShunt, editor: SchematicWidget):
        """

        :param parent:
        :param api_obj:
        :param editor:
        """
        InjectionTemplateGraphicItem.__init__(self,
                                              parent=parent,
                                              api_obj=api_obj,
                                              editor=editor,
                                              device_type_name='external grid',
                                              w=40,
                                              h=40)
        self.set_glyph(glyph=Square(self, 40, 40, "C", self.update_nexus))

    @property
    def api_object(self) -> ControllableShunt:
        return self._api_object

    def contextMenuEvent(self, event):
        """
        Display context menu
        @param event:
        @return:
        """
        if self.api_object is not None:
            menu = self.get_base_context_menu()
            menu.addSection("Controllable shunt")

            add_menu_entry(menu=menu,
                           text="Editor",
                           function_ptr=self.edit,
                           icon_path=":/Icons/icons/edit.png")

            menu.exec(event.screenPos())

        else:
            self.editor.gui.show_error_toast("The graphic has no API object!")


    def edit(self):
        """
        Call the edit dialogue
        :return:
        """
        dlg = ControllableShuntEditor(api_object=self.api_object)
        if dlg.exec():
            pass
