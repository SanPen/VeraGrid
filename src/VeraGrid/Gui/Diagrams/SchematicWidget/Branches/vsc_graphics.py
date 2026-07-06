# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING, Union
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QMenu
from VeraGrid.Gui.gui_functions import add_menu_entry, translate_context_menu_text
from VeraGrid.Gui.Diagrams.SchematicWidget.terminal_item import BarTerminalItem, RoundTerminalItem
from VeraGrid.Gui.DeviceEditors.VscEditor.vsc_device_editor import VscDeviceEditorDialog
from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.enumerations import TapModuleControl, DynamicSimulationMode
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.line_graphics_template import LineGraphicTemplateItem

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget


class VscGraphicItem(LineGraphicTemplateItem):
    """
    Graphics item for the VSC converter
    """

    def __init__(self,
                 from_port: Union[BarTerminalItem, RoundTerminalItem],
                 to_port: Union[BarTerminalItem, RoundTerminalItem],
                 editor: SchematicWidget,
                 width=5,
                 api_object: VSC = None,
                 draw_labels: bool = True):
        """

        :param from_port:
        :param to_port:
        :param editor:
        :param width:
        :param api_object:
        """

        if from_port.parent.api_object.is_dc and not to_port.parent.api_object.is_dc:  # this is the correct sense
            # do nothing as the ports are in the correct sense
            LineGraphicTemplateItem.__init__(self=self,
                                             from_port=from_port,
                                             to_port=to_port,
                                             editor=editor,
                                             width=width,
                                             api_object=api_object,
                                             draw_labels=draw_labels)
        elif not from_port.parent.api_object.is_dc and to_port.parent.api_object.is_dc:  # opposite sense, revert
            # flip the ports
            LineGraphicTemplateItem.__init__(self=self,
                                             from_port=to_port,
                                             to_port=from_port,
                                             editor=editor,
                                             width=width,
                                             api_object=api_object,
                                             draw_labels=draw_labels)
            print("had to flip VSC graphic ports!")
        else:
            raise Exception('VscGraphics: Impossible connecting a VSC device here. '
                            'VSC devices must be connected between AC and DC buses')



    @property
    def api_object(self) -> VSC:
        return self._api_object

    def open_device_editor(self) -> bool:
        """
        Open the VSC editor.

        :return: ``True`` when the editor was opened.
        """
        dlg = VscDeviceEditorDialog(api_object=self.api_object, circuit=self.editor.circuit, main_gui=self.editor.gui)
        if dlg.exec():
            return True
        else:
            return True

    def contextMenuEvent(self, event):
        """
        Show context menu
        @param event:
        @return:
        """
        if self.api_object is not None:
            menu = QMenu()

            pe = menu.addAction(translate_context_menu_text("Enable/Disable"))
            pe_icon = QIcon()
            if self.api_object.active:
                pe_icon.addPixmap(QPixmap(":/Icons/icons/uncheck_all.png"))
            else:
                pe_icon.addPixmap(QPixmap(":/Icons/icons/check_all.png"))
            pe.setIcon(pe_icon)
            pe.triggered.connect(self.enable_disable_toggle)

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Draw labels"),
                           function_ptr=self.enable_disable_label_drawing,
                           checkeable=True,
                           checked_value=self.draw_labels)

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Change bus"),
                           function_ptr=self.change_bus,
                           icon_path=":/Icons/icons/move_bus.png")

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Set Control dev 1"),
                           function_ptr=self.set_control_dev_1,
                           icon_path=":/Icons/icons/move_bus.png")

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Set Control dev 2"),
                           function_ptr=self.set_control_dev_2,
                           icon_path=":/Icons/icons/move_bus.png")

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

            menu.addSeparator()
            self.add_auto_route_style_menu(menu=menu)
            menu.addSeparator()

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Delete"),
                           function_ptr=self.delete,
                           icon_path=":/Icons/icons/delete3.png")

            menu.addSeparator()

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Control V from"),
                           function_ptr=self.control_v_from,
                           icon_path=":/Icons/icons/edit.png")

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Control V to"),
                           function_ptr=self.control_v_to,
                           icon_path=":/Icons/icons/edit.png")

            menu.addSeparator()

            ra6 = menu.addAction(translate_context_menu_text("Plot profiles"))
            plot_icon = QIcon()
            plot_icon.addPixmap(QPixmap(":/Icons/icons/plot.png"))
            ra6.setIcon(plot_icon)
            ra6.triggered.connect(self.plot_profiles)

            ra4 = menu.addAction(translate_context_menu_text("Assign rate to profile"))
            ra4_icon = QIcon()
            ra4_icon.addPixmap(QPixmap(":/Icons/icons/assign_to_profile.png"))
            ra4.setIcon(ra4_icon)
            ra4.triggered.connect(self.assign_rate_to_profile)

            ra5 = menu.addAction(translate_context_menu_text("Assign active state to profile"))
            ra5_icon = QIcon()
            ra5_icon.addPixmap(QPixmap(":/Icons/icons/assign_to_profile.png"))
            ra5.setIcon(ra5_icon)
            ra5.triggered.connect(self.assign_status_to_profile)

            menu.exec_(event.screenPos())
        else:
            pass


    def edit_dynamic_rms(self):
        """
        Open the unified dynamic editor workspace for this generator.
        """

        self.editor.gui.open_dynamic_editor(api_object=self.api_object, circuit=self.editor.circuit,
                                            preferred_mode=DynamicSimulationMode.RMS)

    def edit_dynamic_emt(self):
        """
        Open the unified dynamic editor workspace for this generator.
        """

        self.editor.gui.open_dynamic_editor(api_object=self.api_object, circuit=self.editor.circuit,
                                            preferred_mode=DynamicSimulationMode.EMT)

    def mouseDoubleClickEvent(self, event):
        """
        On double click, edit
        :param event:
        :return:
        """
        self.open_device_editor()

    def edit(self) -> None:
        """
        Open the VSC device editor.
        """
        self.open_device_editor()

    def control_v_from(self):
        """

        :return:
        """
        self.api_object.regulation_bus = self.api_object.bus_from
        self.api_object.tap_module_control_mode = TapModuleControl.Vm

    def control_v_to(self):
        """

        :return:
        """
        self.api_object.regulation_bus = self.api_object.bus_to
        self.api_object.tap_module_control_mode = TapModuleControl.Vm

    def set_control_dev_1(self):
        """

        :return:
        """
        self.editor.set_vsc_control_dev(graphic=self, control_idx=1)

    def set_control_dev_2(self):
        """

        :return:
        """
        self.editor.set_vsc_control_dev(graphic=self, control_idx=2)

    def set_arrows_with_power_vsc(self, Pf: float | None, Pt: complex | None, Qt: complex | None) -> None:
        """
        Set the arrow directions
        :param Pf: DC actrive power from
        :param Pt: AC active power to
        :param Qt: AC reactive power
        """

        if Pf is not None:

            if Pt is None:
                Pt = -Pf

            if Qt is None:
                Qt = 0

            # from -> DC
            # to   -> AC

            # AC side
            self.arrow_p_to.set_value(Pt, True, Pt > 0, name="Pac", units="MW", draw_label=self.draw_labels)
            self.arrow_q_to.set_value(Qt, True, Qt > 0, name="Qac", units="MVAr", draw_label=self.draw_labels)

            # DC side
            self.arrow_p_from.set_value(Pf, True, Pf < 0, name="Pdc", units="MW", draw_label=self.draw_labels)
            self.arrow_q_from.setVisible(False)
        else:
            if Pt is None:
                self.arrow_p_from.setVisible(False)
                self.arrow_q_from.setVisible(False)
                self.arrow_p_to.setVisible(False)
                self.arrow_q_to.setVisible(False)
