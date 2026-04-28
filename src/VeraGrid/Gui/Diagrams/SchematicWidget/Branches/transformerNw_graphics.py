# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import List, TYPE_CHECKING

import numpy as np
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QPen, QCursor, QColor
from PySide6.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsRectItem, QMenu, QGraphicsSceneMouseEvent

from VeraGrid.Gui.Diagrams.generic_graphics import ACTIVE, DEACTIVATED, GenericDiagramWidget
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.winding_graphics import WindingGraphicItem
from VeraGrid.Gui.Diagrams.SchematicWidget.terminal_item import RoundTerminalItem
from VeraGrid.Gui.gui_functions import add_menu_entry
from VeraGrid.Gui.messages import yes_no_question
from VeraGridEngine.Devices.Branches.transformerNw import TransformerNW
from VeraGridEngine.Devices.Branches.winding import Winding
from VeraGridEngine.Devices.Substation.bus import Bus

if TYPE_CHECKING:
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget


class TransformerNWGraphicItem(GenericDiagramWidget, QGraphicsRectItem):
    """
    Graphic representation of an N-winding transformer around a central star bus.
    """

    def __init__(self, editor: SchematicWidget,
                 elm: TransformerNW,
                 pos: QPoint = None,
                 parent=None,
                 index=0,
                 draw_labels: bool = True):
        self.h = 120
        self.w = 120
        GenericDiagramWidget.__init__(self, parent=parent, api_object=elm, editor=editor, draw_labels=True)
        QGraphicsRectItem.__init__(self, 0.0, 0.0, self.w, self.h, parent=parent)

        self.draw_labels = draw_labels
        self.index = index
        self.n_windings = self.api_object.winding_count

        if self.api_object is not None and self.api_object.active:
            self.color = ACTIVE['color']
            self.style = ACTIVE['style']
        elif self.api_object is not None:
            self.color = DEACTIVATED['color']
            self.style = DEACTIVATED['style']
        else:
            self.color = ACTIVE['color']
            self.style = ACTIVE['style']

        self.pen_width = 4
        self.setPen(QPen(Qt.GlobalColor.transparent, self.pen_width, self.style))
        self.setBrush(Qt.GlobalColor.transparent)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        if pos is not None:
            self.setPos(pos)

        winding_diameter = 36
        radius_small = 5
        angle_0 = -90.0
        d_angle = 360.0 / self.n_windings
        center = QPointF(self.w / 2.0, self.h / 2.0)
        # Keep the winding circles visually tight while still scaling with N.
        min_non_overlapping_radius = winding_diameter / (2.0 * max(np.sin(np.pi / self.n_windings), 1e-6))
        radius_large = max(winding_diameter * 0.5, min_non_overlapping_radius * 0.95)

        self.winding_circles: List[QGraphicsEllipseItem] = list()
        self.terminals: List[RoundTerminalItem] = list()
        self.connection_lines: List[WindingGraphicItem | None] = list()
        self.slot_windings: List[Winding | None] = list(self.api_object.windings[:self.n_windings])
        if len(self.slot_windings) < self.n_windings:
            self.slot_windings.extend([None] * (self.n_windings - len(self.slot_windings)))

        pen = QPen(self.color, self.pen_width, self.style)

        for i in range(self.n_windings):
            angle_rad = np.deg2rad(angle_0 + d_angle * i)
            dx = np.cos(angle_rad)
            dy = np.sin(angle_rad)

            winding_center_x = center.x() + dx * radius_large - winding_diameter * 0.5
            winding_center_y = center.y() + dy * radius_large - winding_diameter * 0.5

            winding_circle = QGraphicsEllipseItem(parent=self)
            winding_circle.setRect(winding_center_x, winding_center_y, winding_diameter, winding_diameter)

            tangent_center_distance = radius_large + winding_diameter * 0.5 + radius_small * 1.2
            terminal_center_x = center.x() + dx * tangent_center_distance - radius_small
            terminal_center_y = center.y() + dy * tangent_center_distance - radius_small

            terminal = RoundTerminalItem(name=f"t{i + 1}", parent=self, editor=self.editor, h=10, w=10)
            terminal.setPos(terminal_center_x, terminal_center_y)

            winding_circle.setPen(pen)
            terminal.setPen(pen)

            self.winding_circles.append(winding_circle)
            self.terminals.append(terminal)
            self.connection_lines.append(None)

        self.big_marker = None
        self.set_winding_tool_tips()

    @property
    def api_object(self) -> TransformerNW:
        return self._api_object

    @property
    def editor(self) -> SchematicWidget:
        return self._editor

    def get_associated_widgets(self) -> List[WindingGraphicItem | None]:
        return self.connection_lines

    def get_extra_graphics(self):
        return self.winding_circles + self.terminals

    def recolour_mode(self):
        if self.api_object is not None and self.api_object.active:
            self.color = ACTIVE['color']
            self.style = ACTIVE['style']
        elif self.api_object is not None:
            self.color = DEACTIVATED['color']
            self.style = DEACTIVATED['style']
        else:
            self.color = ACTIVE['color']
            self.style = ACTIVE['style']

        pen = QPen(self.color, self.pen_width, self.style)
        for i in range(self.n_windings):
            self.winding_circles[i].setPen(pen)
            self.terminals[i].setPen(pen)
            if self.connection_lines[i] is not None:
                self.connection_lines[i].recolour_mode()

    def set_enable(self, val=True):
        self.api_object.active = val
        for winding in self.api_object.windings:
            winding.active = val
        self.recolour_mode()

    def set_winding_tool_tips(self) -> None:
        for i, circle in enumerate(self.winding_circles):
            winding = self.slot_windings[i]
            if winding is None or winding.bus_to is None:
                circle.setToolTip(f"Winding {i + 1}: unassigned")
            else:
                circle.setToolTip(f"Winding {i + 1}: {winding.HV} kV")

    def set_label(self, val: str):
        pass

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        super().mouseMoveEvent(event)
        self.editor.update_diagram_element(device=self.api_object,
                                           x=self.pos().x(),
                                           y=self.pos().y(),
                                           w=self.w,
                                           h=self.h,
                                           r=self.rotation(),
                                           graphic_object=self)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if self.api_object is not None:
            self.editor.set_editor_model(api_object=self.api_object)

    def mouseDoubleClickEvent(self, event):
        return None

    def contextMenuEvent(self, event):
        if self.api_object is not None:
            menu = QMenu()
            menu.addSection("Transformer NW")

            add_menu_entry(menu=menu,
                           text="Active",
                           function_ptr=self.enable_disable_toggle,
                           checkeable=True,
                           checked_value=self.api_object.active)

            menu.addSeparator()

            add_menu_entry(menu=menu,
                           text="Delete",
                           function_ptr=self.delete,
                           icon_path=":/Icons/icons/delete_schematic.png")

            menu.exec_(event.screenPos())

    def enable_disable_toggle(self):
        if self.api_object is not None:
            self.set_enable(not self.api_object.active)
            if self._editor.circuit.get_time_number() > 0:
                ok = yes_no_question('Do you want to update the time series active status accordingly?',
                                     'Update time series active status')
                if ok:
                    self._editor.set_active_status_to_profile(self.api_object, override_question=True)
                    for winding in self.api_object.windings:
                        self._editor.set_active_status_to_profile(winding, override_question=True)

    def add_big_marker(self, color=Qt.GlobalColor.red, tool_tip_text=""):
        if self.big_marker is None:
            self.big_marker = QGraphicsEllipseItem(0, 0, 180, 180, parent=self)
            self.big_marker.setBrush(color)
            self.big_marker.setOpacity(0.5)
            self.big_marker.setToolTip(tool_tip_text)

    def delete_big_marker(self):
        if self.big_marker is not None:
            self.editor._remove_from_scene(self.big_marker)
            self.big_marker = None

    def change_size(self, w, h):
        self.editor.update_diagram_element(device=self.api_object,
                                           x=self.pos().x(),
                                           y=self.pos().y(),
                                           w=w,
                                           h=h,
                                           r=self.rotation(),
                                           graphic_object=self)

    def set_position(self, x: float, y: float) -> None:
        x = 0 if np.isnan(x) else int(x)
        y = 0 if np.isnan(y) else int(y)
        self.setPos(QPoint(int(x), int(y)))

    def get_connection_winding(self, from_port: RoundTerminalItem, to_port: RoundTerminalItem):
        for i, terminal in enumerate(self.terminals):
            if terminal in [from_port, to_port]:
                return i
        raise Exception("Unknown winding")

    def _get_or_create_slot_winding(self, i: int, bus: Bus | None) -> Winding:
        winding = self.slot_windings[i]
        if winding is None:
            winding = self.api_object.add_winding(bus=bus,
                                                  nominal_voltage=bus.Vnom if bus is not None else 1.0,
                                                  nominal_power=0.0)
            self.slot_windings[i] = winding
        return winding

    def set_connection(self, i: int, bus: Bus, conn: WindingGraphicItem, set_voltage: bool = True):
        winding = self._get_or_create_slot_winding(i=i, bus=bus)
        winding.bus_to = bus
        if set_voltage and bus is not None:
            winding.set_hv_and_lv(HV=bus.Vnom, LV=1.0)

        self.connection_lines[i] = conn
        self.terminals[i].setZValue(-1)
        conn.api_object = winding
        conn.winding_number = i
        conn.parent_tr3_graphics_item = self

        self.set_winding_tool_tips()
        self.mousePressEvent(None)

    def remove_winding(self, i: int):
        winding = self.slot_windings[i]
        if winding is not None:
            try:
                winding_index = list(self.api_object.windings).index(winding)
            except ValueError:
                winding_index = None

            if winding_index is not None:
                self.api_object.set_bus(winding_index, None)
            winding.bus_to = None

        self.connection_lines[i] = None
        self.terminals[i].setZValue(-1)
        self.set_winding_tool_tips()

    def arrange_children(self) -> None:
        pass

    def set_tile_color(self, brush: QColor):
        for winding_circle in self.winding_circles:
            winding_circle.setPen(QPen(brush, self.pen_width, self.style))

    def set_winding_color(self, i, color: QColor):
        self.winding_circles[i].setPen(QPen(color, self.pen_width, self.style))
        self.terminals[i].setPen(QPen(color, self.pen_width, self.style))

    def delete(self):
        self.editor.delete_with_dialogue(selected=[self], delete_from_db=False)
