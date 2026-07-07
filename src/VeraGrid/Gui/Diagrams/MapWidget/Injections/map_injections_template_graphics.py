# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QCursor, QColor, QBrush
from PySide6.QtWidgets import (QGraphicsEllipseItem, QMenu,
                               QGraphicsSceneContextMenuEvent,
                               QGraphicsSceneMouseEvent)
from VeraGrid.Gui.gui_functions import add_menu_entry, translate_context_menu_text
from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGrid.Gui.Diagrams.generic_graphics import GenericDiagramWidget
from VeraGrid.Gui.Diagrams.MapWidget.Substation.node_template import NodeTemplate
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Devices.types import INJECTION_DEVICE_TYPES

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.MapWidget.grid_map_widget import GridMapWidget


class MapInjectionTemplateGraphicItem(NodeTemplate, QGraphicsEllipseItem):
    """
    InjectionTemplateGraphicItem
    """

    def __init__(self,
                 api_object: INJECTION_DEVICE_TYPES,
                 editor: GridMapWidget,
                 lat: float,
                 lon: float,
                 size: float = 0.8,
                 draw_labels: bool = True):
        """

        :param api_object:
        :param editor:
        :param lat:
        :param lon:
        :param size:
        :param draw_labels:
        """
        # Correct way to call multiple inheritance
        super().__init__()

        # Explicitly call QGraphicsRectItem initialization
        QGraphicsEllipseItem.__init__(self)

        # Explicitly call NodeTemplate initialization
        NodeTemplate.__init__(self,
                              api_object=api_object,
                              editor=editor,
                              draw_labels=draw_labels,
                              lat=lat,
                              lon=lon)

        r2 = size / 2.0
        x, y = editor.to_x_y(lat=lat, lon=lon)  # upper left corner
        self.size = size
        self.setRect(x - r2, y - r2, self.size, self.size)

        # Properties of the container:
        self.setFlags(self.GraphicsItemFlag.ItemIsSelectable | self.GraphicsItemFlag.ItemIsMovable)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.set_api_object_color()

    @property
    def api_object(self) -> INJECTION_DEVICE_TYPES:
        """

        :return:
        """
        return self._api_object

    @property
    def editor(self) -> GridMapWidget:
        """

        :return:
        """
        return self._editor

    def set_api_object_color(self) -> QColor:
        """
        Sets whatever colour is in the API object property
        """

        color = QColor(self.api_object.color)
        color.setAlpha(128)
        self.color = color

        brush = QBrush(color)
        self.setBrush(brush)

        pen = self.pen()
        pen.setColor(color)
        pen.setWidth(0)  # set the pen width to 0
        self.setPen(pen)

        return color

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Event handler for mouse press events.
        """
        super().mousePressEvent(event)
        # selected_items = self.editor.map.view.selected_items()
        # if len(selected_items) < 2:
        self.setSelected(True)

        event.setAccepted(True)
        self.editor.map.view.disable_move = True

        if self.api_object is not None:
            self.editor.set_editor_model(api_object=self.api_object)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """
        Event handler for mouse release events.
        """
        # super().mouseReleaseEvent(event)
        self.editor.disableMove = True
        self.update_position_at_the_diagram()  # always update

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Event handler for mouse move events.
        """

        pos = self.mapToScene(event.pos())
        self.refresh(pos=pos)

    def update_position_at_the_diagram(self) -> None:
        """
        Updates the element position in the diagram (to save)
        :return:
        """
        lat, long = self.editor.to_lat_lon(self.get_xc(), self.get_yc())

        self.lat = lat
        self.lon = long

        self.editor.update_diagram_element(device=self.api_object,
                                           latitude=lat,
                                           longitude=long,
                                           graphic_object=self)

    def refresh(self, pos: QPointF):
        """
        This function refreshes the x, y coordinates of the graphic item
        Returns:

        """

        x = pos.x() - self.rect().width() / 2
        y = pos.y() - self.rect().height() / 2
        self.setRect(x, y, self.rect().width(), self.rect().height())
        self.set_callbacks(pos.x(), pos.y())


        self.update_position_at_the_diagram()  # always update

    def set_size(self, r: float):
        """

        :param r: radius in pixels
        :return:
        """
        if r != self.size:
            rect = self.rect()
            rect.setWidth(r)
            rect.setHeight(r)

            # change the width and height while keeping the same center
            r2 = (self.size - r) / 2
            new_x = rect.x() + r2
            new_y = rect.y() + r2

            self.size = r

            # Set the new rectangle with the updated dimensions
            self.setRect(new_x, new_y, r, r)

    def recolour_mode(self):
        """
        Change the colour according to the system theme
        """
        super().recolour_mode()

        return self.set_api_object_color()

    def delete(self):
        """
        Remove this element
        @return:
        """

        deleted, delete_from_db_final = self.editor.delete_with_dialogue(selected=[self], delete_from_db=False)

    def plot(self):
        """
        Plot API objects profiles
        """
        # time series object from the last simulation
        ts = self.editor.circuit.time_profile

        # plot the profiles
        self.api_object.plot_profiles(time=ts)

    def open_device_editor(self) -> bool:
        """
        Open the default map-injection editor.

        :return: ``True`` when the editor was opened.
        """
        circuit = self._editor.circuit
        dialog = TemplateDeviceEditor(api_object=self.api_object, circuit=circuit)
        dialog.exec()
        return True


    def mouseDoubleClickEvent(self, event, /):
        """

        :param event:
        :return:
        """
        super().mouseDoubleClickEvent(event)
        self.set_api_object_color()
        self.open_device_editor()

    def get_base_context_menu(self) -> QMenu:
        """
        Generate the base menu for injections
        :return:
        """
        menu = QMenu()

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Plot profiles"),
                       function_ptr=self.plot,
                       icon_path=":/Icons/icons/plot.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Editor"),
                       function_ptr=self.open_device_editor,
                       icon_path=":/Icons/icons/edit.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Consolidate coordinates"),
                       function_ptr=self.editor.consolidate_object_coordinates,
                       icon_path=":/Icons/icons/assign_to_profile.png")


        menu.addSeparator()

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Delete"),
                       function_ptr=self.delete,
                       icon_path=":/Icons/icons/delete_schematic.png")


        ss_counter = 0
        gen_counter = 0

        for graphic_obj in self.editor.get_selected():
            if isinstance(graphic_obj, GenericDiagramWidget):
                if graphic_obj.api_object.device_type == DeviceType.SubstationDevice:
                    has_substation = True
                    ss_counter += 1
                elif graphic_obj.api_object.device_type == DeviceType.GeneratorDevice:
                    gen_counter += 1
                else:
                    pass
            else:
                pass
        if ss_counter == 1 and gen_counter > 0:
            menu.addSeparator()

            add_menu_entry(menu=menu,
                           text=translate_context_menu_text("Change bus connection for the generator"),
                           function_ptr=self.editor.change_generator_bus_connection,
                           icon_path=":/Icons/icons/move_bus.png")

        return menu

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        """
        Display context menu
        @param event:
        @return:
        """
        menu = self.get_base_context_menu()
        menu.exec(event.screenPos())

    def get_xc(self) -> float:
        return self.rect().x() + self.size/2

    def get_yc(self) -> float:
        return self.rect().y() + self.size/2

    def consolidate_coordinates(self):
        """
        Consolidate coordinates in to the DB
        """
        lat, long = self.editor.to_lat_lon(self.get_xc(), self.get_yc())
        self.api_object.latitude = lat
        self.api_object.longitude = long
        self.editor.gui.show_info_toast("Coordinates consolidated!")
