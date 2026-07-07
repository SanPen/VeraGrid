# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtGui import QPen
from PySide6.QtWidgets import (QMenu)
from VeraGridEngine.Devices.Fluid.fluid_pump import FluidPump
from VeraGrid.Gui.Diagrams.generic_graphics import ACTIVE, Circle
from VeraGrid.Gui.gui_functions import add_menu_entry
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.injections_template_graphics import InjectionTemplateGraphicItem

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget


class FluidPumpGraphicItem(InjectionTemplateGraphicItem):
    """
    FluidPumpGraphicItem
    """

    def __init__(self, parent, api_obj: FluidPump, editor: "SchematicWidget"):
        """

        :param parent:
        :param api_obj:
        :param editor:
        """
        InjectionTemplateGraphicItem.__init__(self,
                                              parent=parent,
                                              api_obj=api_obj,
                                              editor=editor,
                                              device_type_name='fluid_pump',
                                              w=40,
                                              h=40)

        self.set_glyph(
            glyph=Circle(self, 40, 40, "P", self.update_nexus)
        )

    def recolour_mode(self):
        """
        Change the colour according to the system theme
        """
        self.color = ACTIVE['color']
        self.style = ACTIVE['style']

        pen = QPen(self.color, self.width, self.style)
        self.glyph.setPen(pen)
        self.nexus.setPen(pen)

    def contextMenuEvent(self, event):
        """
        Display context menu
        @param event:
        @return:
        """
        menu = QMenu()
        menu.addSection("Pump")

        add_menu_entry(menu=menu,
                       text="Plot fluid profiles",
                       icon_path=":/Icons/icons/plot.png",
                       function_ptr=self.plot)

        menu.addSeparator()

        add_menu_entry(menu=menu,
                       text="Delete",
                       icon_path=":/Icons/icons/delete3.png",
                       function_ptr=self.delete)

        add_menu_entry(menu=menu,
                       text="Change bus",
                       icon_path=":/Icons/icons/move_bus.png",
                       function_ptr=self.change_bus)

        menu.exec_(event.screenPos())
