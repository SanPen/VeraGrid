# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING, Union
from PySide6.QtWidgets import QMenu
from VeraGrid.Gui.gui_functions import add_menu_entry, translate_context_menu_text
from VeraGrid.Gui.DeviceEditors.device_editor_factory import build_device_editor_dialog
from VeraGrid.Gui.Diagrams.SchematicWidget.terminal_item import BarTerminalItem, RoundTerminalItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.line_graphics_template import LineGraphicTemplateItem
from VeraGridEngine.Devices.Branches.hvdc_line import HvdcLine
from VeraGrid.Gui.messages import yes_no_question
from VeraGridEngine.enumerations import DynamicSimulationMode

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget


class HvdcGraphicItem(LineGraphicTemplateItem):

    def __init__(self,
                 from_port: Union[BarTerminalItem, RoundTerminalItem],
                 to_port: Union[BarTerminalItem, RoundTerminalItem],
                 editor: SchematicWidget,
                 width=5,
                 api_object: HvdcLine = None,
                 draw_labels: bool = True):
        """

        :param from_port:
        :param to_port:
        :param editor:
        :param width:
        :param api_object:
        """
        LineGraphicTemplateItem.__init__(self=self,
                                         from_port=from_port,
                                         to_port=to_port,
                                         editor=editor,
                                         width=width,
                                         api_object=api_object,
                                         draw_labels=draw_labels)

    @property
    def api_object(self) -> HvdcLine:
        return self._api_object

    def open_device_editor(self) -> bool:
        """
        Open the generic device editor for this HVDC line.

        :return: ``True`` when the editor was opened.
        """
        dialog = build_device_editor_dialog(api_object=self.api_object, circuit=self.editor.circuit)
        dialog.exec()
        return True

    def contextMenuEvent(self, event):
        """
        Show context menu
        @param event:
        @return:
        """
        if self.api_object is not None:
            menu = QMenu()
            menu.addSection(translate_context_menu_text("HVDC line"))

            pe = menu.addAction(translate_context_menu_text("Active"))
            pe.setCheckable(True)
            pe.setChecked(self.api_object.active)
            pe.triggered.connect(self.enable_disable_toggle)

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Draw labels"),
                           icon_path="",
                           function_ptr=self.enable_disable_label_drawing,
                           checkeable=True,
                           checked_value=self.draw_labels)

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Editor"),
                           function_ptr=self.edit,
                           icon_path=":/Icons/icons/edit.png")

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("RMS Editor"),
                           function_ptr=self.edit_dynamic_rms,
                           icon_path=":/Icons/icons/dyn_edit.png")

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("EMT Editor"),
                           function_ptr=self.edit_dynamic_emt,
                           icon_path=":/Icons/icons/dyn_emt_edit.png")

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Change bus"),
                           icon_path=":/Icons/icons/move_bus.png",
                           function_ptr=self.change_bus)

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Convert to VSC multi-terminal"),
                           icon_path=":/Icons/icons/vsc.png",
                           function_ptr=self.convert_to_multi_terminal)

            menu.addSeparator()

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Plot profiles"),
                           icon_path=":/Icons/icons/plot.png",
                           function_ptr=self.plot_profiles)

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Assign rate to profile"),
                           icon_path=":/Icons/icons/assign_to_profile.png",
                           function_ptr=self.assign_rate_to_profile)

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Assign active state to profile"),
                           icon_path=":/Icons/icons/assign_to_profile.png",
                           function_ptr=self.assign_status_to_profile)

            menu.addSeparator()
            self.add_auto_route_style_menu(menu=menu)
            menu.addSeparator()

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Delete"),
                           icon_path=":/Icons/icons/delete3.png",
                           function_ptr=self.delete)

            menu.exec_(event.screenPos())
        else:
            pass

    def mouseDoubleClickEvent(self, event) -> None:
        """
        Open the HVDC editor on double click.

        :param event: Mouse event.
        :return: ``None``.
        """
        if self.api_object is not None:
            self.open_device_editor()
        else:
            pass

    def edit(self) -> None:
        """
        Open the appropriate editor dialogue.

        :return: ``None``.
        """
        self.open_device_editor()

    def convert_to_multi_terminal(self):
        """
        Convert this HvdcLine to a vsc + DC line system
        """
        ok = yes_no_question('Do you want to change the HvdcLine by 2 VSC converters + 1 DC Line?',
                             'Change by a VSC system')

        if ok:
            self.editor.convert_hvdc_line_to_vsc_system(hvdc_line=self.api_object)

    def plot_profiles(self):
        """
        Plot the time series profiles
        @return:
        """
        # get the index of this object
        i = self.editor.circuit.get_hvdc().index(self.api_object)
        self.editor.plot_hvdc_branch(i, self.api_object)

    def edit_dynamic_rms(self):
        """
        Open the unified dynamic editor workspace for this generator.
        """

        self.editor.gui.open_dynamic_editor(api_object=self.api_object,
                                            circuit=self.editor.circuit,
                                            preferred_mode=DynamicSimulationMode.RMS)

    def edit_dynamic_emt(self):
        """
        Open the unified dynamic editor workspace for this generator.
        """

        self.editor.gui.open_dynamic_editor(api_object=self.api_object,
                                            circuit=self.editor.circuit,
                                            preferred_mode=DynamicSimulationMode.EMT)
