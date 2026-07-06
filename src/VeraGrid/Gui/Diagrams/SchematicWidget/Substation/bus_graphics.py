# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import numpy as np
from typing import Union, TYPE_CHECKING, List, Dict, Tuple, Any
import webbrowser
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QRectF, QRect, QPointF
from PySide6.QtGui import QPen, QCursor, QBrush, QColor, QPainterPath
from PySide6.QtWidgets import QMenu, QGraphicsSceneMouseEvent, QGraphicsItem, QGraphicsPathItem

from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.injections_template_graphics import InjectionTemplateGraphicItem
from VeraGrid.Gui.messages import yes_no_question, warning_msg
from VeraGrid.Gui.gui_functions import add_menu_entry, translate_context_menu_text
from VeraGrid.Gui.ShortCircuitEditor.short_circuit_selector import ShortCircuitSelector
from VeraGrid.Gui.Diagrams.generic_graphics import (GenericDiagramWidget, ACTIVE, DEACTIVATED,
                                                    FONT_SCALE, TRANSPARENT, DraggableLabelItem)
from VeraGrid.Gui.Diagrams.SchematicWidget.terminal_item import BarTerminalItem, HandleItem, RoundTerminalItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.load_graphics import LoadGraphicItem, Load
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.generator_graphics import GeneratorGraphicItem, Generator
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.static_generator_graphics import (StaticGeneratorGraphicItem,
                                                                                        StaticGenerator)
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.battery_graphics import (BatteryGraphicItem, Battery)
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.shunt_graphics import (ShuntGraphicItem, Shunt)
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.external_grid_graphics import (ExternalGridGraphicItem,
                                                                                     ExternalGrid)
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.current_injection_graphics import (
    CurrentInjectionGraphicItem,
    CurrentInjection)
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.controllable_shunt_graphics import (
    ControllableShuntGraphicItem,
    ControllableShunt)
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.slot_geometry import (SchematicAttachmentSlot,
                                                                          build_explicit_slot_key,
                                                                          clamp_attachment_alignment,
                                                                          get_distributed_anchor,
                                                                          get_bar_slot_anchor,
                                                                          project_point_to_bar_terminal,
                                                                          infer_attachment_side_from_points,
                                                                          parse_attachment_slot,
                                                                          parse_explicit_slot_key)
from VeraGridEngine.enumerations import DeviceType, BusGraphicType, SchematicBranchEndpoint
from VeraGridEngine.Devices.types import INJECTION_DEVICE_TYPES
from VeraGridEngine.Devices.Substation import Bus
from VeraGridEngine.Devices.Events.short_cirtcuit_event import ShortCircuitEvent

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.line_graphics_template import LineGraphicTemplateItem
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget

INJECTION_GRAPHICS = Union[
    BatteryGraphicItem,
    ShuntGraphicItem,
    ExternalGridGraphicItem,
    ControllableShuntGraphicItem,
    LoadGraphicItem,
    GeneratorGraphicItem,
    StaticGeneratorGraphicItem,
    CurrentInjectionGraphicItem
]


def get_dock_sort_key(entry: Tuple[int, int, float, float | None, bool, INJECTION_GRAPHICS]) -> Tuple[bool, int, int]:
    """
    Build the ordering key for docked child graphics.
    """
    return entry[0] == 0, entry[0], entry[1]


class ShortCircuitFlags:
    """
    Short circuit flags
    """

    def __init__(self, sc_3p: bool = False, sc_lg: bool = False, sc_ll: bool = False, sc_llg: bool = False):
        self.sc_3p = sc_3p
        self.sc_lg = sc_lg
        self.sc_ll = sc_ll
        self.sc_llg = sc_llg

    def disable_all(self):
        """

        :return:
        """
        self.sc_3p = False
        self.sc_lg = False
        self.sc_ll = False
        self.sc_llg = False


class BusGraphicItem(GenericDiagramWidget, QtWidgets.QGraphicsRectItem):
    """
      Represents a block in the diagram
      Has an x and y and width and height
      width and height can only be adjusted with a tip in the lower right corner.

      - in and output ports
      - parameters
      - description
    """

    def __init__(self,
                 editor: SchematicWidget,
                 bus: Bus ,
                 parent=None,
                 h: float = 40,
                 w: float = 80,
                 x: float = 0,
                 y: float = 0,
                 draw_labels: bool = True,
                 r: float = 0):
        """

        :param editor:
        :param bus:
        :param parent:
        :param h:
        :param w:
        :param x:
        :param y:
        :param draw_labels:
        :param r:
        """
        GenericDiagramWidget.__init__(self, parent=parent, api_object=bus, editor=editor, draw_labels=draw_labels)
        QtWidgets.QGraphicsRectItem.__init__(self, parent)

        # Label:
        self.label = DraggableLabelItem(self, moved_callback=self.refresh_label_badge_geometry)
        self.label.setDefaultTextColor(ACTIVE['text'])
        self.label.document().setDocumentMargin(0.0)
        self.label.setScale(1.0)
        self.label_badge = QGraphicsPathItem(self)
        self.label_badge.setPen(QPen(QColor(ACTIVE['text']), 1.0))
        self.label_badge.setBrush(QBrush(QColor(ACTIVE['background'])))
        self.label_badge.setZValue(-1)

        # loads, shunts, generators, etc...
        self._child_graphics: List[INJECTION_GRAPHICS] = list()

        # index
        # self.index = index

        self.big_marker = None

        self.connectivity_graph = False

        # connection terminals the block
        if self.api_object.graphic_type == BusGraphicType.BusBar:
            self._terminal = BarTerminalItem('s', parent=self, editor=self.editor)
            self.min_w = 180.0
            self.min_h = 40.0
            self.offset = 20

            self.h = h if h >= self.min_h else self.min_h
            self.w = w if w >= self.min_w else self.min_w
            self.r = r

            # square
            self.tile = QtWidgets.QGraphicsRectItem(0, 0, 20, 20, self)
            self.tile.setOpacity(0.7)

            # Create corner for resize:
            self.sizer = HandleItem(self._terminal, callback=self.change_size)
            self.sizer.setPos(self.w, self.h)
            self.sizer.setFlag(self.GraphicsItemFlag.ItemIsMovable)

        elif self.api_object.graphic_type == BusGraphicType.Connectivity:
            self._terminal = RoundTerminalItem('s', parent=self, editor=self.editor, h=20, w=20)  # , h=self.h))
            self.min_w = 50.0
            self.min_h = 50.0
            self.offset = 20

            self.h = h if h >= self.min_h else self.min_h
            self.w = w if w >= self.min_w else self.min_w
            self.r = r

            self._terminal.setPos(self.w / 2 - self._terminal.w / 2, self.h / 2 - self._terminal.h / 2)
            # self._terminal.setPos(self.w / 2 + 10, self.h / 2 + 10)

            # square
            self.tile = QtWidgets.QGraphicsRectItem(0, 0, 5, 5, self)
            self.tile.setOpacity(1.0)

            # Create corner for resize:
            self.sizer = None

            self.connectivity_graph = True

        else:
            self._terminal = BarTerminalItem('s', parent=self, editor=editor)
            self.min_w = 180.0
            self.min_h = 40.0
            self.offset = 20

            self.h = h if h >= self.min_h else self.min_h
            self.w = w if w >= self.min_w else self.min_w
            self.r = r

            # square
            self.tile = QtWidgets.QGraphicsRectItem(0, 0, 20, 20, self)
            self.tile.setOpacity(0.7)

            # Create corner for resize:
            self.sizer = HandleItem(self._terminal, callback=self.change_size)
            self.sizer.setPos(self.w, self.h)
            self.sizer.setFlag(self.GraphicsItemFlag.ItemIsMovable)

        self.y0 = self.h + 40  # y position of the shunt element icons

        # Enabled for short circuit
        self.pen_width = 4

        self._terminal.setPen(QPen(TRANSPARENT, self.pen_width, self.style,
                                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))

        self.update_color()

        self.setPen(QPen(TRANSPARENT, self.pen_width, self.style))
        self.setBrush(TRANSPARENT)
        self.setFlags(self.GraphicsItemFlag.ItemIsSelectable | self.GraphicsItemFlag.ItemIsMovable)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Update size:
        self.change_size(w=self.w)
        title: str = self._api_object.name if self._api_object is not None else ""
        self.set_label_content(title=title, msg="")

        self.set_position(x, y)
        self.apply_rotation_state(refresh_geometry=False)

    @property
    def api_object(self) -> Bus:
        """

        :return:
        """
        return self._api_object

    @property
    def editor(self) -> SchematicWidget:
        """

        :return:
        """
        return self._editor

    @property
    def terminal(self):
        """

        :return:
        """
        return self._terminal

    def get_associated_branch_graphics(self) -> List[LineGraphicTemplateItem]:
        """
        Get a list of all associated branch graphics
        :return:
        """
        conn: List[LineGraphicTemplateItem] = self._terminal.get_hosted_graphics()

        return conn

    def get_associated_shunt_graphics(self) -> List[INJECTION_GRAPHICS]:
        """
        List of associated shunt graphics
        :return:
        """
        return self._child_graphics

    def get_associated_widgets(self) -> List[LineGraphicTemplateItem | INJECTION_GRAPHICS | QGraphicsItem]:
        """
        Get a list of all associated graphics
        :return:
        """
        conn: List[LineGraphicTemplateItem | INJECTION_GRAPHICS | QGraphicsItem] = self.get_associated_branch_graphics()

        for graphics in self._child_graphics:
            conn.append(graphics)
            conn.append(graphics.nexus)

        return conn

    def get_extra_graphics(self) -> List[QGraphicsItem]:
        return self.get_associated_widgets()

    def get_nexus_point(self) -> QPointF:
        """
        Get the connection point for the children nexus line
        (connection points for loads, shunts, generators, etc.)
        :return: QPointF
        """
        return self.get_connection_scene_point_from_local_point(self.get_default_connection_local_point())

    def get_nexus_point_for_child(self, child_graphic: INJECTION_GRAPHICS) -> QPointF:
        """
        Get the connection point for one docked child graphic.
        """
        dock = self._editor.diagram.get_dock(child_graphic.api_object)
        anchor_x = dock.get("anchor_x", None)
        anchor_y = dock.get("anchor_y", None)

        if anchor_x is None or anchor_y is None:
            child_center_local_x: float = child_graphic.pos().x() + child_graphic.w * 0.5
            child_center_local_y: float = child_graphic.pos().y() + child_graphic.h * 0.5
            local_anchor: QPointF = self.get_connection_local_point_from_local_point(QPointF(child_center_local_x,
                                                                                             child_center_local_y))
        else:
            local_anchor = self.get_connection_local_point_from_local_point(QPointF(float(anchor_x),
                                                                                    float(anchor_y)))

        return self.get_connection_scene_point_from_local_point(local_anchor)

    def recolour_mode(self) -> None:
        """
        Change the color according to the system theme
        """
        super().recolour_mode()

        self.label.setDefaultTextColor(ACTIVE['text'])
        badge_fill: QColor = QColor(ACTIVE['background'])
        badge_fill.setAlpha(215)
        badge_stroke: QColor = QColor(ACTIVE['text'])
        badge_stroke.setAlpha(150)
        self.label_badge.setPen(QPen(badge_stroke, 1.0))
        self.label_badge.setBrush(QBrush(badge_fill))
        self.update_color()

        for e in self._child_graphics:
            if e is not None:
                e.recolour_mode()

    def _get_base_bus_brush(self) -> QBrush:
        """
        Resolve the default bus brush outside study-result colouring.

        :return: Brush used for the idle bus appearance.
        """
        if not self.api_object.active:
            return QBrush(DEACTIVATED['color'])
        else:
            pass

        # The bus idle colour must follow the active GUI theme unless the user has
        # explicitly requested API/device colours for the whole diagram.
        if self.editor.diagram.use_api_colors:
            color_hex: str = str(self.api_object.color)
            return QBrush(QColor(color_hex))
        else:
            return QBrush(QColor(ACTIVE['color']))

    def enable_label_drawing(self) -> None:
        """
        Enable the bus label badge immediately.

        :return: ``None``.
        """
        super().enable_label_drawing()
        self.label.setVisible(True)
        self.label_badge.setVisible(True)
        self.refresh_label_badge_geometry()

    def disable_label_drawing(self) -> None:
        """
        Disable the bus label badge immediately.

        :return: ``None``.
        """
        super().disable_label_drawing()
        self.label.setVisible(False)
        self.label_badge.setVisible(False)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        """
        On mouse move of this object...
        Args:
            event: QGraphicsSceneMouseEvent inherited
        """
        super().mouseMoveEvent(event)
        self._editor.update_diagram_element(device=self.api_object,
                                            x=self.pos().x(),
                                            y=self.pos().y(),
                                            w=self.w,
                                            h=self.h,
                                            r=self.rotation(),
                                            draw_labels=self.draw_labels,
                                            graphic_object=self)

    def add_big_marker(self, color: Union[None, QColor] = QColor(255, 0, 0, 255), tool_tip_text: str = ""):
        """
        Add a big marker to the bus
        :param color: Qt Color ot the marker
        :param tool_tip_text: tool tip text to display
        """
        if color is not None:
            if self.big_marker is None:
                self.big_marker = QtWidgets.QGraphicsEllipseItem(0, 0, 180, 180, parent=self)

            self.big_marker.setBrush(color)
            self.big_marker.setOpacity(0.5)
            self.big_marker.setToolTip(tool_tip_text)

    def delete_big_marker(self) -> None:
        """
        Delete the big marker
        """
        if self.big_marker is not None:
            self._editor._remove_from_scene(self.big_marker)
            self.big_marker = None

    def set_position(self, x: float, y: float) -> None:
        """
        Set the bus x, y position
        :param x: x in pixels
        :param y: y in pixels
        """
        if np.isnan(x):
            x = 0.0
        if np.isnan(y):
            y = 0.0
        self.setPos(QPointF(x, y))

    def set_tile_color(self, brush: QBrush | QColor) -> None:
        """
        Set the color of the bus
        Args:
            brush:  Qt Color
        """
        if self.tile is not None:
            self.tile.setBrush(brush)
        self._terminal.setBrush(brush)

    def merge(self, other_bus_graphic: "BusGraphicItem") -> None:
        """
        Merge another BusGraphicItem into this
        :param other_bus_graphic: BusGraphicItem
        """
        self._child_graphics += other_bus_graphic._child_graphics

    def update(self, rect: Union[QRectF, QRect] = ...):
        """
        Update the object
        :return:
        """
        self.change_size(w=self.w)

    def set_height(self, h: int):
        """
        Set the height of the
        :param h:
        :return:
        """
        self.setRect(0.0, 0.0, self.w, h)
        self.h = h

    def get_terminal_center(self, val: QPointF) -> QPointF:
        """
        Get the center of the terminal
        :param val: position of a branch point
        :return:
        """
        return self._terminal.get_center_pos(val)

    def change_size(self, w: int | float, dummy: float = 0.0):
        """
        Resize block function
        :param w:
        :param dummy:
        :return:
        """
        # Limit the block size to the minimum size:
        self.w = w if w > self.min_w else self.min_w
        self.setRect(0.0, 0.0, self.w, self.min_h)
        y0 = self.offset
        x0 = 0

        # center label:
        self.label.set_anchor_position(QPointF(self.w + 5.0, -6.0))
        self.refresh_label_badge_geometry()

        # lower
        if not self.connectivity_graph:
            self._terminal.setPos(x0, y0)
            self._terminal.setRect(0, 20, self.w, 10)
        else:
            pass

        # Keep the rotation pivot aligned with the electrical connection bar.
        self.setTransformOriginPoint(self.get_rotation_origin_local_point())
        self.setRotation(self.r)

        # rearrange children
        if self.editor.is_loading_diagram():
            pass
        else:
            self.arrange_children()

        # update editor diagram position
        if self.editor.is_loading_diagram():
            pass
        else:
            self._editor.update_diagram_element(device=self.api_object,
                                                x=self.pos().x(),
                                                y=self.pos().y(),
                                                w=self.w,
                                                h=int(self.min_h),
                                                r=self.rotation(),
                                                draw_labels=self.draw_labels,
                                                graphic_object=self)

        return self.w, self.min_h

    def get_rotation_origin_local_point(self) -> QPointF:
        """
        Return the local rotation origin used for saved/loadable bus orientation.

        All bus rotation now happens around the widget geometric center so the
        whole symbol behaves as one rigid body during interactive rotation and
        when restored from persisted schematic coordinates.

        :return: Local rotation origin.
        """
        return self.rect().center()

    def get_default_connection_local_point(self) -> QPointF:
        """
        Return the default local anchor used for bar-style branch attachments.

        :return: Local attachment point.
        """
        terminal_y: float = self._terminal.pos().y() + self._terminal.rect().y()
        terminal_h: float = self._terminal.rect().height()
        local_x: float = self.rect().width() * 0.5
        local_y: float = terminal_y + terminal_h * 0.5
        return QPointF(local_x, local_y)

    def get_connection_local_point_from_local_point(self, local_point: QPointF) -> QPointF:
        """
        Project one local point to the valid electrical connection locus.

        :param local_point: Requested local point.
        :return: Projected local attachment point.
        """
        if self.connectivity_graph:
            center_point: QPointF = self.rect().center()
            projected_x = float(center_point.x())
            projected_y = float(center_point.y())
        else:
            terminal_y: float = self._terminal.pos().y() + self._terminal.rect().y()
            terminal_h: float = self._terminal.rect().height()
            projected_x, projected_y = project_point_to_bar_terminal(width=float(self.rect().width()),
                                                                     terminal_y=terminal_y,
                                                                     terminal_h=terminal_h,
                                                                     point_x=float(local_point.x()))

        return QPointF(projected_x, projected_y)

    def get_connection_local_point_from_scene_point(self, scene_point: QPointF) -> QPointF:
        """
        Project one scene point to the valid electrical connection locus.

        :param scene_point: Requested scene point.
        :return: Projected local attachment point.
        """
        local_point: QPointF = self.mapFromScene(scene_point)
        return self.get_connection_local_point_from_local_point(local_point)

    def get_connection_scene_point_from_local_point(self, local_point: QPointF) -> QPointF:
        """
        Map one local connection point to the scene after clamping it to the host geometry.

        :param local_point: Requested local point.
        :return: Scene attachment point.
        """
        projected_local_point: QPointF = self.get_connection_local_point_from_local_point(local_point)
        return self.mapToScene(projected_local_point)

    def apply_rotation_state(self, refresh_geometry: bool) -> None:
        """
        Apply the persisted rotation state to the live graphics item.

        :param refresh_geometry: Refresh attached routes and docked children afterwards.
        :return: ``None``.
        """
        self.setTransformOriginPoint(self.get_rotation_origin_local_point())
        self.setRotation(self.r)

        if refresh_geometry:
            self.refresh_connected_geometry_after_rotation()
        else:
            pass

    def refresh_connected_geometry_after_rotation(self) -> None:
        """
        Refresh docked children and attached branches after one rotation change.

        :return: ``None``.
        """
        self.arrange_children()
        self._terminal.update()
        self._terminal.process_callbacks(self._terminal.scenePos())
        self.auto_assign_branch_slots()

        branch_graphic: LineGraphicTemplateItem

        for branch_graphic in self.get_associated_branch_graphics():
            branch_graphic.update_ports()
            branch_graphic.load_route_points_from_diagram()
            branch_graphic.redraw()

    def set_rotation_angle(self, angle_degrees: float, persist: bool) -> None:
        """
        Set one persisted bus rotation angle.

        :param angle_degrees: Rotation angle in degrees.
        :param persist: Update the backing diagram location.
        :return: ``None``.
        """
        normalized_angle: float = float(angle_degrees) % 360.0
        self.r = normalized_angle
        self.apply_rotation_state(refresh_geometry=True)

        if persist:
            self._editor.update_diagram_element(device=self._api_object,
                                                x=self.pos().x(),
                                                y=self.pos().y(),
                                                w=self.w,
                                                h=self.h,
                                                r=self.r,
                                                draw_labels=self.draw_labels,
                                                graphic_object=self)
        else:
            pass

    def arrange_children(self) -> None:
        """
        This function sorts the load and generators icons
        Returns:
            Nothing
        """
        dock_groups: Dict[
            SchematicAttachmentSlot, List[Tuple[int, int, float, float | None, bool, INJECTION_GRAPHICS]]] = {
            SchematicAttachmentSlot.TOP: list(),
            SchematicAttachmentSlot.BOTTOM: list(),
            SchematicAttachmentSlot.LEFT: list(),
            SchematicAttachmentSlot.RIGHT: list(),
        }
        child_index: int

        for child_index, elm in enumerate(self._child_graphics):
            dock = self._editor.diagram.sync_injection_dock(api_object=elm.api_object,
                                                            owner_device=self.api_object,
                                                            side=SchematicAttachmentSlot.BOTTOM)
            side = parse_attachment_slot(str(dock.get("side", SchematicAttachmentSlot.BOTTOM.value)))
            order = int(dock.get("order", 0))
            offset = float(dock.get("offset", 0.0))
            alignment = dock.get("alignment", None)
            auto_layout = bool(dock.get("auto_layout", True))

            if side not in dock_groups:
                side = SchematicAttachmentSlot.BOTTOM
            else:
                pass

            dock_groups[side].append((order, child_index, offset, alignment, auto_layout, elm))

        self._arrange_child_group(side=SchematicAttachmentSlot.TOP,
                                  dock_entries=dock_groups[SchematicAttachmentSlot.TOP])
        self._arrange_child_group(side=SchematicAttachmentSlot.BOTTOM,
                                  dock_entries=dock_groups[SchematicAttachmentSlot.BOTTOM])
        self._arrange_child_group(side=SchematicAttachmentSlot.LEFT,
                                  dock_entries=dock_groups[SchematicAttachmentSlot.LEFT])
        self._arrange_child_group(side=SchematicAttachmentSlot.RIGHT,
                                  dock_entries=dock_groups[SchematicAttachmentSlot.RIGHT])

        # Arrange line positions
        if self.editor.is_loading_diagram():
            pass
        else:
            self._terminal.process_callbacks(self.pos() + self._terminal.pos())

    def _arrange_child_group(self,
                             side: SchematicAttachmentSlot,
                             dock_entries: List[
                                 Tuple[int, int, float, float | None, bool, INJECTION_GRAPHICS]]) -> None:
        """
        Arrange one dock side of child graphics.
        """
        if len(dock_entries) == 0:
            return
        else:
            pass

        sorted_entries = sorted(dock_entries, key=get_dock_sort_key)
        slot_count: int = len(sorted_entries)
        slot_index: int

        for slot_index, (_, _, offset, alignment, auto_layout, elm) in enumerate(sorted_entries, start=1):
            if auto_layout:
                span_fraction: float = float(slot_index) / float(slot_count + 1)
                if side == SchematicAttachmentSlot.TOP:
                    x_pos = self.w * span_fraction - elm.w * 0.5
                    y_pos = -elm.h - 40.0 - offset
                elif side == SchematicAttachmentSlot.LEFT:
                    x_pos = -elm.w - 40.0 - offset
                    y_pos = self.rect().height() * span_fraction - elm.h * 0.5
                elif side == SchematicAttachmentSlot.RIGHT:
                    x_pos = self.w + 40.0 + offset
                    y_pos = self.rect().height() * span_fraction - elm.h * 0.5
                else:
                    x_pos = self.w * span_fraction - elm.w * 0.5
                    y_pos = self.y0 + offset
            else:
                location = self.editor.diagram.query_point(elm.api_object)

                if location is None:
                    span_fraction = clamp_attachment_alignment(alignment)

                    if side == SchematicAttachmentSlot.TOP:
                        x_pos = self.w * span_fraction - elm.w * 0.5
                        y_pos = -elm.h - 40.0 - offset
                    elif side == SchematicAttachmentSlot.LEFT:
                        x_pos = -elm.w - 40.0 - offset
                        y_pos = self.rect().height() * span_fraction - elm.h * 0.5
                    elif side == SchematicAttachmentSlot.RIGHT:
                        x_pos = self.w + 40.0 + offset
                        y_pos = self.rect().height() * span_fraction - elm.h * 0.5
                    else:
                        x_pos = self.w * span_fraction - elm.w * 0.5
                        y_pos = self.y0 + offset
                else:
                    local_position: QPointF = self.mapFromScene(QPointF(float(location.x), float(location.y)))
                    x_pos = float(local_position.x())
                    y_pos = float(local_position.y())

            elm.setPos(x_pos, y_pos)

            if self.editor.is_loading_diagram():
                pass
            else:
                elm.update_nexus(elm.pos())

    def get_bottom_dock_baseline(self) -> float:
        """
        Return the baseline local Y coordinate used for bottom-docked children.

        :return: Bottom dock baseline.
        """
        return float(self.y0)

    def create_children_widgets(self, injections_by_tpe: Dict[DeviceType, List[INJECTION_DEVICE_TYPES]]):
        """
        Create the icons of the elements that are attached to the API bus object
        Returns: Nothing
        """

        for tpe, dev_list in injections_by_tpe.items():

            if tpe == DeviceType.LoadDevice:
                for elm in dev_list:
                    self.add_load(elm)

            elif tpe == DeviceType.StaticGeneratorDevice:
                for elm in dev_list:
                    self.add_static_generator(elm)

            elif tpe == DeviceType.GeneratorDevice:
                for elm in dev_list:
                    self.add_generator(elm)

            elif tpe == DeviceType.ShuntDevice:
                for elm in dev_list:
                    self.add_shunt(elm)

            elif tpe == DeviceType.BatteryDevice:
                for elm in dev_list:
                    self.add_battery(elm)

            elif tpe == DeviceType.ExternalGridDevice:
                for elm in dev_list:
                    self.add_external_grid(elm)

            elif tpe == DeviceType.CurrentInjectionDevice:
                for elm in dev_list:
                    self.add_current_injection(elm)

            elif tpe == DeviceType.ControllableShuntDevice:
                for elm in dev_list:
                    self.add_controllable_shunt(elm)

            else:
                raise Exception("Unknown device type:" + str(tpe))

        if self.editor.is_loading_diagram():
            pass
        else:
            self.arrange_children()

    def contextMenuEvent(self, event: QtWidgets.QGraphicsSceneContextMenuEvent):
        """
        Display the context menu
        @param event:
        @return:
        """
        menu = QMenu()
        menu.addSection(translate_context_menu_text("Bus"))

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Editor"),
                       icon_path=":/Icons/icons/edit.png",
                       function_ptr=self.edit)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Active"),
                       icon_path="",
                       function_ptr=self.enable_disable_toggle,
                       checkeable=True,
                       checked_value=self.api_object.active)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Draw labels"),
                       icon_path="",
                       function_ptr=self.enable_disable_label_drawing,
                       checkeable=True,
                       checked_value=self.draw_labels)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("add Short circuit"),
                       icon_path=":/Icons/icons/short_circuit_plus.png",
                       function_ptr=self.add_short_circuit)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Is a DC bus"),
                       icon_path=":/Icons/icons/dc.png",
                       function_ptr=self.enable_disable_dc,
                       checkeable=True,
                       checked_value=self.api_object.is_dc)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Plot profiles"),
                       icon_path=":/Icons/icons/plot.png",
                       function_ptr=self.plot_profiles)

        add_menu_entry(menu,
                       text=translate_context_menu_text("Arrange"),
                       icon_path=":/Icons/icons/automatic_layout.png",
                       function_ptr=self.arrange_children)

        add_menu_entry(menu,
                       text=translate_context_menu_text("Rotate 90"),
                       icon_path=":/Icons/icons/rotate.svg",
                       function_ptr=self.rotate)

        add_menu_entry(menu,
                       text=translate_context_menu_text("Assign active state to profile"),
                       icon_path=":/Icons/icons/assign_to_profile.png",
                       function_ptr=self.assign_status_to_profile)

        add_menu_entry(menu, text=translate_context_menu_text("Delete"),
                       icon_path=":/Icons/icons/delete_schematic.png",
                       function_ptr=self.delete)

        add_menu_entry(menu, text=translate_context_menu_text("Convert to voltage level"),
                       icon_path=":/Icons/icons/voltage_level.png",
                       function_ptr=self.convert_to_voltage_level)

        add_menu_entry(menu, text=translate_context_menu_text("Convert to impedances circuit"),
                       icon_path=":/Icons/icons/voltage_level.png",
                       function_ptr=self.convert_to_connectivity_grid)

        add_menu_entry(menu, text=translate_context_menu_text("Expand schematic"),
                       icon_path=":/Icons/icons/grid_icon.png",
                       function_ptr=self.expand_diagram_from_bus)

        add_menu_entry(menu, text=translate_context_menu_text("Vicinity diagram from here"),
                       icon_path=":/Icons/icons/grid_icon.png",
                       function_ptr=self.new_vicinity_diagram_from_here)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Open in street view"),
                       icon_path=":/Icons/icons/map.png",
                       function_ptr=self.open_street_view)

        menu.addSection(translate_context_menu_text("Add"))

        # Actions under the "Add" section
        add_menu_entry(menu, text=translate_context_menu_text("Load"),
                       icon_path=":/Icons/icons/add_load.png",
                       function_ptr=self.add_load)

        add_menu_entry(menu, text=translate_context_menu_text("Current injection"),
                       icon_path=":/Icons/icons/add_load.png",
                       function_ptr=self.add_current_injection)

        add_menu_entry(menu, text=translate_context_menu_text("Shunt"),
                       icon_path=":/Icons/icons/add_shunt.png",
                       function_ptr=self.add_shunt)

        add_menu_entry(menu,
                       text=translate_context_menu_text("Controllable shunt"),
                       icon_path=":/Icons/icons/add_shunt.png",
                       function_ptr=self.add_controllable_shunt)

        add_menu_entry(menu, text=translate_context_menu_text("Generator"),
                       icon_path=":/Icons/icons/add_gen.png",
                       function_ptr=self.add_generator)

        add_menu_entry(menu, text=translate_context_menu_text("Static generator"),
                       icon_path=":/Icons/icons/add_stagen.png",
                       function_ptr=self.add_static_generator)

        add_menu_entry(menu, text=translate_context_menu_text("Battery"),
                       icon_path=":/Icons/icons/add_batt.png",
                       function_ptr=self.add_battery)

        add_menu_entry(menu,
                       text=translate_context_menu_text("External grid"),
                       icon_path=":/Icons/icons/add_external_grid.png",
                       function_ptr=self.add_external_grid)

        menu.exec_(event.screenPos())

    def assign_status_to_profile(self):
        """
        Assign the snapshot rate to the profile
        """
        self._editor.set_active_status_to_profile(self.api_object)

    def delete(self) -> None:
        """
        Remove this element
        @return:
        """
        deleted, delete_from_db_final = self.editor.delete_with_dialogue(selected=[self], delete_from_db=False)
        if deleted:
            self._terminal.clear()

    def delete_child(self, obj: INJECTION_GRAPHICS | InjectionTemplateGraphicItem):
        """
        Delete a child object
        :param obj:
        """
        self._child_graphics.remove(obj)

    def update_color(self):
        """
        Update the colour
        """
        self.set_tile_color(self._get_base_bus_brush())

    def convert_to_voltage_level(self) -> None:
        """
        Open the voltage level conversion wizard
        """
        self.editor.convert_busbar_to_voltage_level(bus_graphics=self)

    def convert_to_connectivity_grid(self) -> None:
        """
        Transform this bus into a grid of buses to be able to compute the bus currents
        and delete this bus afterward
        """
        self.editor.transform_busbar_to_connectivity_grid(bus_graphics=self)

    def expand_diagram_from_bus(self) -> None:
        """
        Expands the diagram from this bus
        """
        self._editor.expand_diagram_from_bus(root_bus=self.api_object)

    def new_vicinity_diagram_from_here(self):
        """
        Create new vicinity diagram
        :return:
        """
        if self.api_object is not None:
            self.editor.gui.new_bus_branch_diagram_from_bus(root_bus=self.api_object)
        else:
            warning_msg("The api object is none :(")

    def enable_disable_toggle(self):
        """
        Toggle bus element state
        @return:
        """
        if self.api_object is not None:

            # change the bus state (snapshot)
            self.api_object.active = not self.api_object.active

            # change the Branches state (snapshot)
            for host in self._terminal.hosting_connections:
                if host.api_object is not None:
                    host.set_enable(val=self.api_object.active)

            if not self.api_object.active:
                self.clear_label()

            self.update_color()

            if self._editor.circuit.has_time_series:
                ok = yes_no_question('Do you want to update the time series active status accordingly?',
                                     'Update time series active status')

                if ok:
                    # change the bus state (time series)
                    self._editor.set_active_status_to_profile(self.api_object, override_question=True)

                    # change the Branches state (time series)
                    for host in self._terminal.hosting_connections:
                        if host.api_object is not None:
                            self._editor.set_active_status_to_profile(host.api_object, override_question=True)

    def add_short_circuit(self) -> None:
        """
        Enable 3-phase short circuit
        """
        self.w = ShortCircuitSelector()
        self.w.exec()

        if self.w.was_accepted:
            z_pu: complex = self.w.get_impedance_pu(Sbase=self.editor.circuit.Sbase,
                                                    Vbase=self.api_object.Vnom)
            sc = ShortCircuitEvent(
                name=f"{self.api_object.name} {self.w.fault.value}",
                device=self.api_object,
                fault_type=self.w.fault,
                method=self.w.method,
                phases=self.w.phases,
                r_fault=z_pu.real,
                x_fault=z_pu.imag
            )

            self.editor.circuit.add_short_circuit_event(sc)

    def enable_disable_dc(self):
        """
        Activates or deactivates the bus as a DC bus
        """
        if self._api_object.is_dc:
            self._api_object.is_dc = False
        else:
            self._api_object.is_dc = True

    def rotate(self):
        """

        :return:
        """
        self.set_rotation_angle(angle_degrees=self.r + 90.0,
                                persist=True)

    def plot_profiles(self) -> None:
        """
        Plot profiles
        """
        # get the index of this object
        i = self._editor.circuit.get_buses().index(self._api_object)
        self._editor.plot_bus(i, self._api_object)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        """
        mouse press: display the editor
        :param event: QGraphicsSceneMouseEvent
        """

        if self._api_object.device_type == DeviceType.BusDevice:
            self._editor.set_editor_model(api_object=self._api_object)

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        """
        Mouse double click
        :param event: event object
        """
        if self._api_object is not None:
            self.open_device_editor()
        else:
            pass

    def open_device_editor(self) -> bool:
        """
        Open the generic device editor for this bus.

        :return: ``True`` when the editor was opened.
        """
        dialog = TemplateDeviceEditor(api_object=self.api_object, circuit=self.editor.circuit)
        dialog.exec()
        return True

    def edit(self) -> None:
        """
        Open the appropriate editor dialogue.

        :return: ``None``.
        """
        self.open_device_editor()

    def get_terminal(self) -> BarTerminalItem:
        """
        Get the hosting terminal of this bus object
        :return: TerminalItem
        """
        return self._terminal

    def get_terminal_slots(self) -> Dict[str, Dict[str, str]]:
        """
        Compatibility catalog for named bus attachment slots.
        """
        slots: Dict[str, Dict[str, str]] = {
            SchematicAttachmentSlot.DEFAULT.value: {"terminal_key": SchematicAttachmentSlot.DEFAULT.value,
                                                    "side": SchematicAttachmentSlot.DEFAULT.value},
            SchematicAttachmentSlot.LEFT.value: {"terminal_key": SchematicAttachmentSlot.LEFT.value,
                                                 "side": SchematicAttachmentSlot.LEFT.value},
            SchematicAttachmentSlot.RIGHT.value: {"terminal_key": SchematicAttachmentSlot.RIGHT.value,
                                                  "side": SchematicAttachmentSlot.RIGHT.value},
            SchematicAttachmentSlot.TOP.value: {"terminal_key": SchematicAttachmentSlot.TOP.value,
                                                "side": SchematicAttachmentSlot.TOP.value},
            SchematicAttachmentSlot.BOTTOM.value: {"terminal_key": SchematicAttachmentSlot.BOTTOM.value,
                                                   "side": SchematicAttachmentSlot.BOTTOM.value},
        }

        explicit_slots: Dict[str, Dict[str, str]] = self.get_explicit_terminal_slots()
        slot_key: str

        for slot_key, slot_data in explicit_slots.items():
            slots[slot_key] = slot_data

        return slots

    def get_explicit_terminal_slots(self) -> Dict[str, Dict[str, str]]:
        """
        Build the explicit slot catalog currently attached to this bus.
        """
        slots: Dict[str, Dict[str, str]] = dict()
        side_key: SchematicAttachmentSlot

        for side_key in (
                SchematicAttachmentSlot.LEFT,
                SchematicAttachmentSlot.RIGHT,
                SchematicAttachmentSlot.TOP,
                SchematicAttachmentSlot.BOTTOM,
        ):
            order: int

            for order in self.get_explicit_slot_orders(side_key=side_key):
                slot_key: str = build_explicit_slot_key(owner_kind="bus", side=side_key, order=order)
                slots[slot_key] = {"terminal_key": slot_key, "side": side_key.value}

        return slots

    def get_terminal_anchor_by_key(self,
                                   terminal_key: str = "default",
                                   graphic_object: LineGraphicTemplateItem | None = None,
                                   alignment: float | None = None) -> QPointF:
        """
        Resolve the scene anchor point for a named attachment slot.
        """
        local_x: float
        local_y: float
        terminal_y: float = self._terminal.pos().y() + self._terminal.rect().y()
        terminal_h: float = self._terminal.rect().height()
        explicit_slot = parse_explicit_slot_key(slot_key=terminal_key)

        if explicit_slot is not None:
            _, side_key, order = explicit_slot
            explicit_entries = self.get_explicit_slot_entries(side_key=side_key)

            if graphic_object is not None:
                if not any(entry[2] is graphic_object for entry in explicit_entries):
                    explicit_entries.append((order, str(id(graphic_object.api_object)), graphic_object))
                else:
                    pass
            else:
                pass

            explicit_entries.sort(key=lambda entry: (entry[0], entry[1]))
            slot_count: int = len(explicit_entries)

            if graphic_object is not None and slot_count > 0:
                order_index = next(
                    index + 1 for index, entry in enumerate(explicit_entries) if entry[2] is graphic_object)
            else:
                ordered_slots: List[int] = [entry[0] for entry in explicit_entries]
                order_index = ordered_slots.index(order) + 1

            local_x, local_y = get_distributed_anchor(side=side_key,
                                                      width=self.rect().width(),
                                                      height=self.rect().height(),
                                                      terminal_y=terminal_y,
                                                      terminal_h=terminal_h,
                                                      order_index=order_index,
                                                      slot_count=slot_count,
                                                      alignment=alignment)
            return self.mapToScene(QPointF(local_x, local_y))
        else:
            pass

        if self.connectivity_graph:
            center_point: QPointF = self.rect().center()
            local_x = float(center_point.x())
            local_y = float(center_point.y())
        else:
            local_x, local_y = get_bar_slot_anchor(width=self.w,
                                                   terminal_y=terminal_y,
                                                   terminal_h=terminal_h,
                                                   slot_key=terminal_key,
                                                   alignment=alignment)

        return self.mapToScene(QPointF(local_x, local_y))

    def get_terminal_alignment_from_scene_point(self, side_key: str | SchematicAttachmentSlot,
                                                scene_point: QPointF) -> float:
        """
        Convert one scene point to a normalized alignment value on the requested side.

        :param side_key: Attachment side.
        :param scene_point: Scene point selected by the user.
        :return: Normalized alignment factor.
        """
        local_point: QPointF = self.mapFromScene(scene_point)

        normalized_side_key: SchematicAttachmentSlot = parse_attachment_slot(str(side_key))

        if normalized_side_key in (SchematicAttachmentSlot.TOP,
                                   SchematicAttachmentSlot.BOTTOM,
                                   SchematicAttachmentSlot.DEFAULT):
            span_value = self.rect().width()
            coordinate = local_point.x()
        else:
            span_value = self.rect().height()
            coordinate = local_point.y()

        if span_value <= 0.0:
            return 0.5
        else:
            pass

        alignment = coordinate / span_value

        if alignment < 0.0:
            return 0.0
        elif alignment > 1.0:
            return 1.0
        else:
            return float(alignment)

    def get_explicit_slot_orders(self, side_key: SchematicAttachmentSlot) -> List[int]:
        """
        Collect persisted explicit slot orders for this graphic on one side.
        """
        orders: List[int] = list()
        explicit_entries = self.get_explicit_slot_entries(side_key=side_key)
        entry: Tuple[int, str, LineGraphicTemplateItem]

        for entry in explicit_entries:
            orders.append(entry[0])

        return orders

    def get_explicit_slot_entries(self,
                                  side_key: SchematicAttachmentSlot
                                  ) -> List[Tuple[int, str, LineGraphicTemplateItem]]:
        """
        Collect persisted explicit slot entries for this graphic on one side.
        """
        entries: List[Tuple[int, str, LineGraphicTemplateItem]] = list()
        branch_graphics: List[LineGraphicTemplateItem] = self.get_associated_branch_graphics()
        graphic_object: LineGraphicTemplateItem

        for graphic_object in branch_graphics:
            endpoint: SchematicBranchEndpoint | None = self.get_branch_endpoint_for_graphic(graphic_object)

            if endpoint is None:
                pass
            else:
                attachment = self.editor.get_persisted_attachment(api_object=graphic_object.api_object,
                                                                  endpoint=endpoint.value)
                terminal_key = str(attachment.get("terminal_key", ""))
                explicit_slot = parse_explicit_slot_key(slot_key=terminal_key)

                if explicit_slot is None:
                    pass
                elif explicit_slot[1] != side_key:
                    pass
                else:
                    entries.append((explicit_slot[2], str(id(graphic_object.api_object)), graphic_object))

        return entries

    def has_duplicate_explicit_slot_order(self, side_key: SchematicAttachmentSlot, order: int) -> bool:
        """
        Check whether an explicit slot order is duplicated on one side.
        """
        count: int = 0
        entry: Tuple[int, str, LineGraphicTemplateItem]

        for entry in self.get_explicit_slot_entries(side_key=side_key):
            if entry[0] == order:
                count += 1
            else:
                pass

        return count > 1

    def get_branch_endpoint_for_graphic(
            self,
            graphic_object: LineGraphicTemplateItem
    ) -> SchematicBranchEndpoint | None:
        """
        Determine which endpoint of a branch graphic is attached to this node.
        """
        from_parent = graphic_object.get_terminal_from_parent()
        to_parent = graphic_object.get_terminal_to_parent()

        if from_parent is self:
            return SchematicBranchEndpoint.FROM
        elif to_parent is self:
            return SchematicBranchEndpoint.TO
        else:
            return None

    def get_branch_attachment_center(self) -> QPointF:
        """
        Get the scene center used to infer branch attachment sides.
        """
        if self.connectivity_graph:
            local_point = QPointF(self.rect().width() * 0.5, self.rect().height() * 0.5)
        else:
            terminal_y: float = self._terminal.pos().y() + self._terminal.rect().y()
            terminal_h: float = self._terminal.rect().height()
            local_point = QPointF(self.w * 0.5, terminal_y + terminal_h * 0.5)

        return self.mapToScene(local_point)

    def infer_branch_slot_side_and_sort_value(self, other_point: QPointF) -> Tuple[SchematicAttachmentSlot, float]:
        """
        Infer the attachment side and sorting coordinate for one connected branch.

        Bar-style buses are routed as vertical feeders by default, so they only use
        ``top`` and ``bottom`` during automatic legacy migration. Connectivity nodes
        still use all four sides.
        """
        local_other_point: QPointF = self.mapFromScene(other_point)
        local_center_x: float = self.rect().width() * 0.5
        terminal_y: float = self._terminal.pos().y() + self._terminal.rect().y()
        terminal_h: float = self._terminal.rect().height()
        local_center_y: float = terminal_y + terminal_h * 0.5
        side_key: SchematicAttachmentSlot
        sort_value: float

        if self.connectivity_graph:
            side_key = infer_attachment_side_from_points(origin=(local_center_x, local_center_y),
                                                         other=(local_other_point.x(), local_other_point.y()),
                                                         vertical_bias=1.0)

            if side_key in (SchematicAttachmentSlot.TOP, SchematicAttachmentSlot.BOTTOM):
                sort_value = float(local_other_point.x())
            else:
                sort_value = float(local_other_point.y())
        else:
            if local_other_point.y() < local_center_y:
                side_key = SchematicAttachmentSlot.TOP
            else:
                side_key = SchematicAttachmentSlot.BOTTOM

            sort_value = float(local_other_point.x())

        return side_key, sort_value

    def auto_assign_branch_slots(self) -> None:
        """
        Assign coordinate-based branch anchors from current geometry.
        """
        grouped_entries: Dict[
            SchematicAttachmentSlot, List[
                Tuple[float, str, LineGraphicTemplateItem, SchematicBranchEndpoint, Dict[str, Any]]
            ]] = {
            SchematicAttachmentSlot.LEFT: list(),
            SchematicAttachmentSlot.RIGHT: list(),
            SchematicAttachmentSlot.TOP: list(),
            SchematicAttachmentSlot.BOTTOM: list(),
        }
        branch_graphic: LineGraphicTemplateItem

        for branch_graphic in self.get_associated_branch_graphics():
            endpoint: SchematicBranchEndpoint | None = self.get_branch_endpoint_for_graphic(branch_graphic)
            branch_api_object = branch_graphic.api_object
            should_process_branch: bool = True

            if endpoint is None:
                should_process_branch = False
            elif branch_api_object is None:
                should_process_branch = False
            else:
                pass

            if should_process_branch:
                attachment = self.editor.get_persisted_attachment(api_object=branch_api_object,
                                                                  endpoint=endpoint.value)
                has_saved_endpoint_state = any(key in attachment for key in ("side",
                                                                             "slot",
                                                                             "terminal_key",
                                                                             "alignment",
                                                                             "order",
                                                                             "anchor_x",
                                                                             "anchor_y"))

                if self.editor.is_loading_diagram():
                    if has_saved_endpoint_state:
                        should_process_branch = False
                    else:
                        pass
                else:
                    pass

                if should_process_branch:
                    existing_slot = str(attachment.get("slot", ""))
                    auto_slot = bool(
                        attachment.get("auto_slot", existing_slot in ("", "default", "left", "right", "top", "bottom")))
                    anchor_auto = bool(attachment.get("anchor_auto", True))

                    if not auto_slot or not anchor_auto:
                        should_process_branch = False
                    else:
                        pass
                else:
                    pass

                if should_process_branch:
                    if endpoint == SchematicBranchEndpoint.FROM:
                        other_point = branch_graphic.pos2
                    else:
                        other_point = branch_graphic.pos1

                    side_key, sort_value = self.infer_branch_slot_side_and_sort_value(other_point=other_point)
                    local_anchor: QPointF = self.get_connection_local_point_from_scene_point(other_point)
                    attachment["anchor_x"] = float(local_anchor.x())
                    attachment["anchor_y"] = float(local_anchor.y())
                    attachment["anchor_auto"] = True

                    grouped_entries[side_key].append((sort_value,
                                                      str(id(branch_api_object)),
                                                      branch_graphic,
                                                      endpoint,
                                                      attachment))
                else:
                    pass
            else:
                pass

        side_key: SchematicAttachmentSlot

        for side_key, entries in grouped_entries.items():
            entries.sort(key=lambda entry: (entry[0], entry[1]))

            for order_index, (_, _, branch_graphic, endpoint, attachment) in enumerate(entries, start=1):
                branch_api_object = branch_graphic.api_object

                if branch_api_object is None:
                    pass
                else:
                    slot_key = build_explicit_slot_key(owner_kind="bus", side=side_key, order=order_index)
                    attachment["side"] = side_key.value
                    attachment["order"] = order_index
                    attachment["slot"] = slot_key
                    attachment["terminal_key"] = slot_key
                    attachment["auto_slot"] = True
                    self.editor.diagram.set_attachment(api_object=branch_api_object,
                                                       endpoint=endpoint.value,
                                                       attachment=attachment)

    def add_object(self, api_obj: INJECTION_DEVICE_TYPES):
        """
        Add any recognized object
        :param api_obj: EditableDevice
        """

        if api_obj.device_type == DeviceType.GeneratorDevice:
            self.add_generator(api_obj=api_obj)

        elif api_obj.device_type == DeviceType.LoadDevice:
            self.add_load(api_obj=api_obj)

        elif api_obj.device_type == DeviceType.StaticGeneratorDevice:
            self.add_static_generator(api_obj=api_obj)

        elif api_obj.device_type == DeviceType.ShuntDevice:
            self.add_shunt(api_obj=api_obj)

        elif api_obj.device_type == DeviceType.BatteryDevice:
            self.add_battery(api_obj=api_obj)

        elif api_obj.device_type == DeviceType.ExternalGridDevice:
            self.add_external_grid(api_obj=api_obj)

        elif api_obj.device_type == DeviceType.CurrentInjectionDevice:
            self.add_current_injection(api_obj=api_obj)

        elif api_obj.device_type == DeviceType.ControllableShuntDevice:
            self.add_controllable_shunt(api_obj=api_obj)

        else:
            raise Exception("Cannot add device of type {}".format(api_obj.device_type.value))

    def add_child_graphic(self, elm: INJECTION_DEVICE_TYPES, graphic: INJECTION_GRAPHICS):
        """
        Add an api object and its graphic to this bus graphics domain
        :param elm:
        :param graphic:
        :return:
        """
        location = self.editor.diagram.query_point(elm)

        if location is None:
            if self.draw_labels:
                graphic.enable_label_drawing()
            else:
                graphic.disable_label_drawing()
        else:
            graphic.apply_rotation_state(angle_degrees=float(location.r))

            if location.draw_labels:
                graphic.enable_label_drawing()
            else:
                graphic.disable_label_drawing()

            if self.editor.is_loading_diagram():
                pass
            else:
                graphic.update_nexus(graphic.scenePos())

        # Child graphics inherit the bus scene item, so they bypass the editor
        # add_to_scene() hook and must normalize their active/theme styling here.
        graphic.recolour_mode()
        self._child_graphics.append(graphic)
        if self.editor.is_loading_diagram():
            pass
        else:
            self.arrange_children()
        self.editor.graphics_manager.add_device(elm=elm, graphic=graphic)

    def add_load(self, api_obj: Union[Load, None] = None):
        """
        Add a load object to this bus
        :param api_obj:
        :return:
        """
        if api_obj is None or type(api_obj) is bool:
            api_obj = self._editor.circuit.add_load(bus=self._api_object)

        _grph = LoadGraphicItem(parent=self, api_obj=api_obj, editor=self._editor, draw_labels=self.draw_labels)
        self.add_child_graphic(elm=api_obj, graphic=_grph)
        return _grph

    def add_shunt(self, api_obj: Union[Shunt, None] = None):
        """
        Add a shunt device to this bus
        :param api_obj: If None, a new shunt is created
        """
        if api_obj is None or type(api_obj) is bool:
            api_obj = self._editor.circuit.add_shunt(bus=self._api_object)

        _grph = ShuntGraphicItem(parent=self, api_obj=api_obj, editor=self._editor, draw_labels=self.draw_labels)
        self.add_child_graphic(elm=api_obj, graphic=_grph)
        return _grph

    def add_generator(self, api_obj: Union[Generator, None] = None):
        """
        Add a generator to this bus
        :param api_obj: if None, a new generator is created
        """
        if api_obj is None or type(api_obj) is bool:
            api_obj = self._editor.circuit.add_generator(bus=self._api_object)

        _grph = GeneratorGraphicItem(parent=self, api_obj=api_obj, editor=self._editor, draw_labels=self.draw_labels)
        self.add_child_graphic(elm=api_obj, graphic=_grph)
        return _grph

    def add_static_generator(self, api_obj: Union[StaticGenerator, None] = None):
        """
        Add a static generator to this bus
        :param api_obj: If none, a new static generator is created
        :return:
        """
        if api_obj is None or type(api_obj) is bool:
            api_obj = self._editor.circuit.add_static_generator(bus=self._api_object)

        _grph = StaticGeneratorGraphicItem(parent=self,
                                           api_obj=api_obj,
                                           editor=self._editor,
                                           draw_labels=self.draw_labels)
        self.add_child_graphic(elm=api_obj, graphic=_grph)

        return _grph

    def add_battery(self, api_obj: Union[Battery, None] = None):
        """

        :param api_obj:
        :return:
        """
        if api_obj is None or type(api_obj) is bool:
            api_obj = self._editor.circuit.add_battery(bus=self._api_object)

        _grph = BatteryGraphicItem(parent=self, api_obj=api_obj, editor=self._editor, draw_labels=self.draw_labels)
        self.add_child_graphic(elm=api_obj, graphic=_grph)

        return _grph

    def add_external_grid(self, api_obj: Union[ExternalGrid, None] = None):
        """

        :param api_obj:
        :return:
        """
        if api_obj is None or type(api_obj) is bool:
            api_obj = self._editor.circuit.add_external_grid(bus=self._api_object)

        _grph = ExternalGridGraphicItem(parent=self,
                                        api_obj=api_obj,
                                        editor=self._editor,
                                        draw_labels=self.draw_labels)
        self.add_child_graphic(elm=api_obj, graphic=_grph)
        return _grph

    def add_current_injection(self, api_obj: Union[CurrentInjection, None] = None):
        """

        :param api_obj:
        :return:
        """
        if api_obj is None or type(api_obj) is bool:
            api_obj = self._editor.circuit.add_current_injection(bus=self._api_object)

        _grph = CurrentInjectionGraphicItem(parent=self,
                                            api_obj=api_obj,
                                            editor=self._editor,
                                            draw_labels=self.draw_labels)
        self.add_child_graphic(elm=api_obj, graphic=_grph)
        return _grph

    def add_controllable_shunt(self, api_obj: Union[ControllableShunt, None] = None):
        """

        :param api_obj:
        :return:
        """
        if api_obj is None or type(api_obj) is bool:
            api_obj = self._editor.circuit.add_controllable_shunt(bus=self._api_object)

        _grph = ControllableShuntGraphicItem(parent=self,
                                             api_obj=api_obj,
                                             editor=self._editor,
                                             draw_labels=self.draw_labels)
        self.add_child_graphic(elm=api_obj, graphic=_grph)

        return _grph

    def set_values(self, i: int, Vm: float, Va: float, P: float | None, Q: float | None,
                   tpe: str, format_str="{:10.2f}", vm_fmt: str = "{:10.4f}"):
        """

        :param i:
        :param Vm:
        :param Va:
        :param P:
        :param Q:
        :param tpe:
        :param format_str:
        :return:
        """
        if self.draw_labels:
            msg: str = str()

            if tpe is None:
                pass
            else:
                msg += f"[{tpe}]<br>"

            vm = vm_fmt.format(Vm)
            vm_kv = format_str.format(Vm * self._api_object.Vnom)
            va = format_str.format(Va)
            msg += f"V={vm_kv} kV<br>  {vm}&lt;{va}º p.u.<br>"

            if P is not None:
                p = format_str.format(P)
                q = format_str.format(Q)
                msg += f"P={p} MW<br>Q={q} MVAr"

        else:
            msg = ""

        if self._api_object is None:
            title = f"Bus {i}"
        else:
            title = f"{i}: {self._api_object.name}"
        self.set_label_content(title=title, msg=msg)

        self.setToolTip(msg)

    def set_values_3ph(self, i: int,
                       VmA: float, VmB: float, VmC: float,
                       VaA: float, VaB: float, VaC: float,
                       tpe: str, format_str="{:10.2f}"):
        """
        Set the three-phase tags
        :param i: Bus index
        :param VmA:
        :param VmB:
        :param VmC:
        :param VaA:
        :param VaB:
        :param VaC:
        :param tpe: Bus type
        :param format_str: number formatting string
        """
        if self.draw_labels:
            msg: str = str()

            if tpe is None:
                pass
            else:
                msg += f"[{tpe}]<br>"

            for Vm_i, Va_i, ph in zip([VmA, VmB, VmC], [VaA, VaB, VaC], ["a", "b", "c"]):
                if not (Vm_i == 0.0 and Va_i == 0.0):
                    vm = format_str.format(Vm_i)
                    vm_kv = format_str.format(Vm_i * self._api_object.Vnom)
                    va = format_str.format(Va_i)
                    msg += f"V{ph}={vm_kv} kV / {vm}&lt;{va}º p.u.<br>"

        else:
            msg = ""

        if self._api_object is None:
            title = f"Bus {i}"
        else:
            title = f"{i}: {self._api_object.name}"
        self.set_label_content(title=title, msg=msg)

        self.setToolTip(msg)

    def clear_label(self):
        """
        Clear the result label
        """
        msg = ""
        title = self._api_object.name if self._api_object is not None else ""
        self.set_label_content(title=title, msg=msg)

        self.setToolTip(msg)

    def set_label_content(self, title: str, msg: str) -> None:
        """
        Apply the bus label HTML using the compact result-badge style.

        :param title: Bus name.
        :param msg: Result text body.
        :return: ``None``.
        """
        body_html: str

        if len(msg) == 0:
            body_html = f'<div style="font-size:9pt; font-weight:600; text-align:center;">{title}</div>'
        else:
            body_html = f'<div style="font-size:9pt; font-weight:600; text-align:center;">{title}<br/>{msg}</div>'

        self.label.setHtml(body_html)
        self.label.setVisible(self.draw_labels)
        self.label_badge.setVisible(self.draw_labels)
        self.refresh_label_badge_geometry()

    def refresh_label_badge_geometry(self) -> None:
        """
        Refresh the rounded badge around the current bus label.

        :return: ``None``.
        """
        label_rect = self.label.boundingRect()
        badge_rect = self.label.mapRectToParent(label_rect).adjusted(-4.0, -2.0, 4.0, 2.0)
        badge_path = QPainterPath()
        badge_path.addRoundedRect(badge_rect, 4.0, 4.0)
        self.label_badge.setPath(badge_path)

    def open_street_view(self):
        """
        Call open street maps
        :return:
        """
        # https://maps.google.com/?q=<lat>,<lng>
        if self._api_object is not None:
            url = f"https://www.google.com/maps/?q={self._api_object.latitude},{self._api_object.longitude}"
            webbrowser.open(url)
        else:
            warning_msg(f"No API object available :(")

    def __str__(self):

        if self._api_object is None:
            return f"Bus graphics {hex(id(self))}"
        else:
            return f"Graphics of {self._api_object.name} [{hex(id(self))}]"

    def __repr__(self):
        return str(self)
