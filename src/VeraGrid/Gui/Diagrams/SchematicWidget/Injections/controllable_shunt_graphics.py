# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGrid.Gui.Diagrams.generic_graphics import Square
from VeraGridEngine.Devices.Injections.controllable_shunt import ControllableShunt
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.injections_template_graphics import InjectionTemplateGraphicItem
from VeraGrid.Gui.DeviceEditors.ControllableShuntEditor.controllable_shunt_device_editor import (
    ControllableShuntDeviceEditorDialog,
)

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

    def open_device_editor(self) -> bool:
        """
        Open the controllable shunt editor.

        :return: ``True`` when the editor was opened.
        """
        dlg = ControllableShuntDeviceEditorDialog(api_object=self.api_object, circuit=self.editor.circuit)
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
        if self.api_object is not None:
            menu = self.get_base_context_menu()
            menu.exec(event.screenPos())

        else:
            self.editor.gui.show_error_toast("The graphic has no API object!")
