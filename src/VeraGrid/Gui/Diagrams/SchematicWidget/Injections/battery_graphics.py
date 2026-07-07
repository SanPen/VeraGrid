# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGrid.Gui.Diagrams.generic_graphics import BatterySymbol
from VeraGridEngine.Devices.Injections.battery import Battery
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.injections_template_graphics import InjectionTemplateGraphicItem
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.generator_editor import GeneratorEditorDialog


if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget


class BatteryGraphicItem(InjectionTemplateGraphicItem):

    def __init__(self, parent, api_obj: Battery, editor: SchematicWidget, draw_labels: bool = True):
        """

        :param parent:
        :param api_obj:
        :param editor:
        """
        InjectionTemplateGraphicItem.__init__(self,
                                              parent=parent,
                                              api_obj=api_obj,
                                              editor=editor,
                                              device_type_name='battery',
                                              w=40,
                                              h=40,
                                              draw_labels=draw_labels,
                                              )
        self.set_glyph(glyph=BatterySymbol(self, 40, 40))

    @property
    def api_object(self) -> Battery:
        """

        :return:
        """
        return self._api_object

    def open_device_editor(self) -> bool:
        """
        Open the battery editor using the generator editor implementation.

        :return: ``True`` when the editor was opened.
        """
        dlg = GeneratorEditorDialog(api_object=self.api_object, circuit=self.editor.circuit)
        if dlg.exec():
            return True
        else:
            return True
