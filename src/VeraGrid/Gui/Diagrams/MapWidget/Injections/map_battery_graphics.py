# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
from PySide6.QtWidgets import QGraphicsSceneContextMenuEvent
from VeraGridEngine.Devices.Injections.battery import Battery
from VeraGrid.Gui.gui_functions import add_menu_entry, translate_context_menu_text
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.generator_editor import GeneratorEditorDialog
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.generator_editor import GeneratorQCurveEditor
from VeraGrid.Gui.Diagrams.MapWidget.Injections.map_injections_template_graphics import MapInjectionTemplateGraphicItem
from VeraGridEngine.enumerations import DynamicSimulationMode

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.MapWidget.grid_map_widget import GridMapWidget


class MapBatteryGraphicItem(MapInjectionTemplateGraphicItem):

    def __init__(self, api_object: Battery,
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

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        """
        Display context menu
        @param event:
        @return:
        """
        menu = self.get_base_context_menu()

        menu.addSection(translate_context_menu_text("Battery"))

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("RMS Editor"),
                       function_ptr=self.edit_rms,
                       icon_path=":/Icons/icons/dyn_edit.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("EMT Editor"),
                       function_ptr=self.edit_emt,
                       icon_path=":/Icons/icons/dyn_emt_edit.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Qcurve edit"),
                       function_ptr=self.edit_q_curve,
                       icon_path=":/Icons/icons/edit.png")

    def edit_rms(self):
        """

        :return:
        """
        self.editor.gui.open_dynamic_editor(api_object=self.api_object, circuit=self.editor.circuit,
                                            preferred_mode=DynamicSimulationMode.RMS)

    def edit_emt(self):
        """
        Open the EMT dynamic model editor for this generator.

        :return: None.
        """

        self.editor.gui.open_dynamic_editor(api_object=self.api_object, circuit=self.editor.circuit,
                                            preferred_mode=DynamicSimulationMode.EMT)

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
