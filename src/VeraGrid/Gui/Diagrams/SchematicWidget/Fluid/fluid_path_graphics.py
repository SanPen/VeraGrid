# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Union, TYPE_CHECKING
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor
from PySide6.QtWidgets import QMenu
from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGrid.Gui.Diagrams.SchematicWidget.terminal_item import BarTerminalItem, RoundTerminalItem
from VeraGrid.Gui.Diagrams.generic_graphics import GenericDiagramWidget, ACTIVE
from VeraGrid.Gui.messages import yes_no_question
from VeraGrid.Gui.gui_functions import add_menu_entry, translate_context_menu_text
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.line_graphics_template import LineGraphicTemplateItem
from VeraGridEngine.Devices.Fluid.fluid_path import FluidPath
from VeraGridEngine.enumerations import DeviceType

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget


class FluidPathGraphicItem(LineGraphicTemplateItem):
    """
    LineGraphicItem
    """

    def __init__(self,
                 from_port: Union[BarTerminalItem, RoundTerminalItem],
                 to_port: Union[BarTerminalItem, RoundTerminalItem, None],
                 editor: SchematicWidget,
                 width=10,
                 api_object: FluidPath = None,
                 arrow_size=15,
                 draw_labels: bool = True):
        """
        
        :param from_port:
        :param to_port:
        :param editor:
        :param width:
        :param api_object:
        :param arrow_size:
        """
        GenericDiagramWidget.__init__(self, parent=None, api_object=api_object, editor=editor, draw_labels=draw_labels)
        LineGraphicTemplateItem.__init__(self,
                                         from_port=from_port,
                                         to_port=to_port,
                                         editor=editor,
                                         width=width,
                                         api_object=api_object,
                                         arrow_size=arrow_size,
                                         arrow_f_pos=0.5,
                                         arrow_t_pos=0.5)

        # self.style = Qt.CustomDashLine
        self.style = ACTIVE['style']
        self.color = QColor(api_object.color) if api_object is not None else ACTIVE['fluid']

        self.set_colour(color=self.color,
                        w=self.width,
                        style=self.style)

    @property
    def api_object(self) -> FluidPath:
        return self._api_object

    def open_device_editor(self) -> bool:
        """
        Open the generic device editor for this fluid path.

        :return: ``True`` when the editor was opened.
        """
        dialog = TemplateDeviceEditor(api_object=self.api_object, circuit=self.editor.circuit)
        dialog.exec()
        return True

    def set_api_object_color(self):
        """
        Gather the color from the api object and apply
        :return:
        """
        self.color = QColor(self.api_object.color) if self.api_object is not None else ACTIVE['fluid']
        self.set_colour(color=self.color,
                        w=self.width,
                        style=self.style)

    def set_colour(self, color: QColor, w, style: Qt.PenStyle):
        """
        Set color and style
        :param color: QColor instance
        :param w: width
        :param style: PenStyle instance
        :return:
        """
        pen = QPen(color, w, style, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        self.set_pen(pen)
        self.arrow_p_from.set_colour(color)
        self.arrow_q_from.set_colour(color)
        self.arrow_p_to.set_colour(color)
        self.arrow_q_to.set_colour(color)

    def recolour_mode(self) -> None:
        """
        Change the colour according to the system theme
        """
        # super().recolour_mode()
        self.set_colour(self.color, self.width, self.style)

    def mouseDoubleClickEvent(self, event):
        """
        On double-click, edit
        :param event:
        :return:
        """
        if self.api_object is not None:
            self.edit()
        else:
            pass

    def contextMenuEvent(self, event):
        """
        Show context menu
        @param event:
        @return:
        """
        if self.api_object is not None:
            menu = QMenu()
            menu.addSection(translate_context_menu_text("FluidPath"))

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Editor"),
                           icon_path=":/Icons/icons/edit.png",
                           function_ptr=self.edit)

            menu.addSeparator()

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Plot profiles"),
                           icon_path=":/Icons/icons/plot.png",
                           function_ptr=self.plot_profiles)

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Delete"),
                           icon_path=":/Icons/icons/delete3.png",
                           function_ptr=self.delete)

            menu.addSeparator()
            self.add_auto_route_style_menu(menu=menu)
            menu.addSection(translate_context_menu_text("Convert to"))
            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Convert to line"),
                           icon_path=":/Icons/icons/assign_to_profile.png",
                           function_ptr=self.to_line)

            menu.exec_(event.screenPos())
        else:
            pass

    def plot_profiles(self):
        """
        Plot the time series profiles
        @return:
        """
        # get the index of this object
        # i = self.editor.circuit.get_fluid_paths().index(self.api_object)
        # self.editor.diagramScene.plot_branch(i, self.api_object)
        pass

    def edit(self):
        """
        Open the appropriate editor dialogue
        :return:
        """
        self.open_device_editor()

    def to_line(self):
        """
        Convert this object to transformer
        :return:
        """
        ok = yes_no_question(self.tr('Are you sure that you want to convert this fluid path into a line?'),
                             self.tr('Convert fluid path'))
        if ok:
            self._editor.convert_fluid_path_to_line(element=self.api_object, item_graphic=self)
