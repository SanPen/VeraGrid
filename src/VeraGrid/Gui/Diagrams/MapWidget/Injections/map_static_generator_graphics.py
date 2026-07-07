# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtGui import QPen, QIcon, QPixmap
from PySide6.QtWidgets import QMenu, QGraphicsTextItem
from VeraGridEngine.Devices.Injections.static_generator import StaticGenerator
from VeraGrid.Gui.Diagrams.generic_graphics import ACTIVE, DEACTIVATED, OTHER, Square, Condenser
from VeraGrid.Gui.Diagrams.MapWidget.Injections.map_injections_template_graphics import MapInjectionTemplateGraphicItem
from VeraGrid.Gui.messages import yes_no_question

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.MapWidget.grid_map_widget import GridMapWidget


class MapStaticGeneratorGraphicItem(MapInjectionTemplateGraphicItem):

    def __init__(self, api_object: StaticGenerator,
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
    def api_object(self) -> StaticGenerator:
        return self._api_object
