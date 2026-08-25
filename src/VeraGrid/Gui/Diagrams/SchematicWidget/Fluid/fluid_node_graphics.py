# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import numpy as np
from typing import Union, TYPE_CHECKING, List, Dict, Tuple
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QPen, QCursor, QBrush, QColor
from PySide6.QtWidgets import QMenu, QGraphicsSceneMouseEvent

from VeraGridEngine.Devices.Fluid import FluidNode, FluidTurbine, FluidPump, FluidP2x
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import DeviceType, FaultType, SchematicBranchEndpoint
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.Devices.types import FLUID_TYPES

from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGrid.Gui.Diagrams.generic_graphics import ACTIVE, FONT_SCALE, GenericDiagramWidget, DraggableLabelItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.slot_geometry import (SchematicAttachmentSlot,
                                                                          build_explicit_slot_key,
                                                                          clamp_attachment_alignment,
                                                                          get_bar_slot_anchor,
                                                                          get_distributed_anchor,
                                                                          project_point_to_bar_terminal,
                                                                          infer_attachment_side_from_points,
                                                                          parse_attachment_slot,
                                                                          parse_explicit_slot_key)
from VeraGrid.Gui.Diagrams.SchematicWidget.terminal_item import BarTerminalItem, HandleItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Fluid.fluid_turbine_graphics import FluidTurbineGraphicItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Fluid.fluid_pump_graphics import FluidPumpGraphicItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Fluid.fluid_p2x_graphics import FluidP2xGraphicItem
from VeraGrid.Gui.messages import yes_no_question, error_msg
from VeraGrid.Gui.gui_functions import add_menu_entry, translate_context_menu_text

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.line_graphics_template import LineGraphicTemplateItem
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget

FLUID_CHILD_GRAPHICS = Union[FluidTurbineGraphicItem, FluidPumpGraphicItem, FluidP2xGraphicItem]


class FluidNodeGraphicItem(GenericDiagramWidget, QtWidgets.QGraphicsRectItem):
    """
      Represents a block in the diagram
      Has an x and y and width and height
      width and height can only be adjusted with a tip in the lower right corner.

      - in and output ports
      - parameters
      - description
    """

    def __init__(self, editor: SchematicWidget, fluid_node: FluidNode,
                 parent=None, index=0, h: float = 20, w: float = 80, x: float = 0, y: float = 0,
                 draw_labels: bool = True):

        GenericDiagramWidget.__init__(self, parent=parent, api_object=fluid_node, editor=editor,
                                      draw_labels=draw_labels)
        QtWidgets.QGraphicsRectItem.__init__(self, parent)

        self.min_w = 180.0
        self.min_h = 40.0
        self.offset = 20
        self.h = h if h >= self.min_h else self.min_h
        self.w = w if w >= self.min_w else self.min_w

        # loads, shunts, generators, etc...
        self._child_graphics: List[FLUID_CHILD_GRAPHICS] = list()

        # Enabled for short circuit
        self.sc_enabled = [False, False, False, False]
        self.sc_type = FaultType.LLLG
        self.pen_width = 4

        # index
        self.index = index

        self.color = QColor(fluid_node.color) if fluid_node is not None else ACTIVE['fluid']
        self.style = ACTIVE['style']

        # Label:
        self.label = DraggableLabelItem(self)
        self.label.setDefaultTextColor(ACTIVE['text'])
        self.label.document().setDocumentMargin(0.0)
        self.label.setScale(FONT_SCALE)
        self.label.setPlainText(self.api_object.name if self.api_object is not None else "")

        # square
        self.tile = QtWidgets.QGraphicsRectItem(0, 0, 20, 20, self)
        self.tile.setOpacity(0.7)

        # connection terminals the block
        self._terminal = BarTerminalItem('s', parent=self, editor=self.editor)  # , h=self.h))
        self._terminal.setPen(QPen(Qt.GlobalColor.transparent, self.pen_width, self.style,
                                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))

        # Create corner for resize:
        self.sizer = HandleItem(self._terminal, callback=self.change_size)
        self.sizer.setPos(self.w, self.h)
        self.sizer.setFlag(self.GraphicsItemFlag.ItemIsMovable)

        self.big_marker = None

        self.set_tile_color(self.color)

        self.setPen(QPen(Qt.GlobalColor.transparent, self.pen_width, self.style))
        self.setBrush(Qt.GlobalColor.transparent)
        self.setFlags(self.GraphicsItemFlag.ItemIsSelectable | self.GraphicsItemFlag.ItemIsMovable)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Update size:
        self.change_size(self.w, self.h)

        self.set_position(x, y)

    @property
    def api_object(self) -> FluidNode:
        return self._api_object

    @property
    def editor(self) -> SchematicWidget:
        return self._editor

    def get_associated_branch_graphics(self) -> List[LineGraphicTemplateItem]:
        """
        Get a list of all associated branch graphics
        :return:
        """
        conn: List[LineGraphicTemplateItem] = self._terminal.get_hosted_graphics()

        return conn

    def get_associated_widgets(self) -> List[LineGraphicTemplateItem | FLUID_CHILD_GRAPHICS]:
        """
        Get a list of all associated graphics
        :return:
        """
        conn: List[LineGraphicTemplateItem | FLUID_CHILD_GRAPHICS] = self.get_associated_branch_graphics()

        for graphics in self._child_graphics:
            conn.append(graphics)

        return conn

    def set_api_object_color(self) -> None:
        """
        Gather the color from the api object and apply
        :return:
        """
        self.color = QColor(self.api_object.color) if self.api_object is not None else ACTIVE['fluid']
        self.set_tile_color(self.color)

    def set_label(self, val: str) -> None:
        """
        Set the label content
        :param val:
        :return:
        """
        self.label.setPlainText(val)

    def open_device_editor(self) -> bool:
        """
        Open the generic device editor for this fluid node.

        :return: ``True`` when the editor was opened.
        """
        dialog = TemplateDeviceEditor(api_object=self.api_object, circuit=self.editor.circuit)
        dialog.exec()
        return True

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        mouse press: display the editor
        :param event:
        :return:
        """
        if self.api_object is not None:
            self.editor.set_editor_model(api_object=self.api_object)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Open the fluid-node editor on double click.

        :param event: Mouse event.
        :return: ``None``.
        """
        if self.api_object is not None:
            self.open_device_editor()
        else:
            pass

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        On mouse move of this object...
        Args:
            event: QGraphicsSceneMouseEvent inherited
        """
        super().mouseMoveEvent(event)

        self.editor.update_diagram_element(device=self.api_object,
                                            x=self.pos().x(),
                                            y=self.pos().y(),
                                            w=self.w,
                                            h=self.h,
                                            r=self.rotation(),
                                            draw_labels=self.draw_labels,
                                            graphic_object=self)

    def set_position(self, x: float, y: float) -> None:
        """
        Set the bus x, y position
        :param x: x in pixels
        :param y: y in pixels
        """
        if np.isnan(x):
            x = 0
        if np.isnan(y):
            y = 0
        self.setPos(QPoint(int(x), int(y)))

    def recolour_mode(self) -> None:
        """
        Change the colour according to the system theme
        """
        # self.color = ACTIVE['color']
        # self.style = ACTIVE['style']
        self.label.setDefaultTextColor(ACTIVE['text'])
        # self.set_tile_color(self.color)

        for e in self._child_graphics:
            if e is not None:
                e.recolour_mode()

    def get_nexus_point(self) -> QPointF:
        """
        Get the connection point for the chldren nexus line
        :return: QPointF
        """
        return QPointF(self.x() + self.rect().width() / 2.0,
                       self.y() + self.rect().height() + self._terminal.h / 2.0)

    def get_nexus_point_for_child(self, child_graphic: FLUID_CHILD_GRAPHICS) -> QPointF:
        """
        Compatibility connection point for docked child graphics.
        """
        return self.get_nexus_point()

    def set_tile_color(self, brush: QBrush | QColor) -> None:
        """
        Set the color of the title
        Args:
            brush:  Qt Color
        """
        self.tile.setBrush(brush)
        self._terminal.setBrush(brush)

    def redraw(self) -> None:
        """
        Update the object
        :return:
        """
        self.change_size(self.w, self.h)

    def set_height(self, h):
        """
        Set the object height
        :param h: height in pixels
        """
        self.setRect(0.0, 0.0, self.w, h)
        self.h = h

    def change_size(self, w: float, h: Union[None, float] = None):
        """
        Resize block function
        @param w:
        @param h:
        @return:
        """
        # Limit the block size to the minimum size:
        self.w = w if w > self.min_w else self.min_w
        self.setRect(0.0, 0.0, self.w, self.min_h)
        y0 = self.offset
        x0 = 0

        # center label:
        self.label.set_anchor_position(QPointF(self.w + 5.0, -20.0))

        # lower
        self._terminal.setPos(x0, y0)
        self._terminal.setRect(0, 20, self.w, 10)

        # rearrange children
        if self.editor.is_loading_diagram():
            pass
        else:
            self.arrange_children()

        # update editor diagram position
        if self.editor.is_loading_diagram():
            pass
        else:
            self.editor.update_diagram_element(device=self.api_object,
                                               x=self.pos().x(),
                                               y=self.pos().y(),
                                               w=self.w,
                                               h=int(self.min_h),
                                               r=self.rotation(),
                                               draw_labels=self.draw_labels,
                                               graphic_object=self)

        return self.w, self.min_h

    def arrange_children(self) -> None:
        """
        This function sorts the load and generators icons
        Returns:
            Nothing
        """
        dock_groups: Dict[SchematicAttachmentSlot, List[
            Tuple[int, int, float, float | None, bool, FLUID_CHILD_GRAPHICS]
        ]] = {
            SchematicAttachmentSlot.TOP: list(),
            SchematicAttachmentSlot.BOTTOM: list(),
            SchematicAttachmentSlot.LEFT: list(),
            SchematicAttachmentSlot.RIGHT: list(),
        }
        child_index: int

        for child_index, elm in enumerate(self._child_graphics):
            dock = self.editor.diagram.sync_injection_dock(api_object=elm.api_object,
                                                           owner_device=self.api_object,
                                                           side=SchematicAttachmentSlot.BOTTOM)
            side: SchematicAttachmentSlot = parse_attachment_slot(
                str(dock.get("side", SchematicAttachmentSlot.BOTTOM.value))
            )
            order = int(dock.get("order", 0))
            offset = float(dock.get("offset", 0.0))
            alignment = dock.get("alignment", None)
            auto_layout = bool(dock.get("auto_layout", True))

            if side not in dock_groups:
                side = SchematicAttachmentSlot.BOTTOM
            else:
                pass

            dock_groups[side].append((order, child_index, offset, alignment, auto_layout, elm))

        side_key: SchematicAttachmentSlot

        for side_key, dock_entries in dock_groups.items():
            sorted_entries = sorted(dock_entries, key=lambda entry: (entry[0] == 0, entry[0], entry[1]))
            slot_count = len(sorted_entries)
            slot_index: int

            for slot_index, (_, _, offset, alignment, auto_layout, elm) in enumerate(sorted_entries, start=1):
                if auto_layout:
                    span_fraction: float = float(slot_index) / float(slot_count + 1)
                    if side_key == SchematicAttachmentSlot.TOP:
                        x_pos = self.w * span_fraction - elm.w * 0.5
                        y_pos = -elm.h - 40.0 - offset
                    elif side_key == SchematicAttachmentSlot.LEFT:
                        x_pos = -elm.w - 40.0 - offset
                        y_pos = self.rect().height() * span_fraction - elm.h * 0.5
                    elif side_key == SchematicAttachmentSlot.RIGHT:
                        x_pos = self.w + 40.0 + offset
                        y_pos = self.rect().height() * span_fraction - elm.h * 0.5
                    else:
                        x_pos = self.w * span_fraction - elm.w * 0.5
                        y_pos = self.get_bottom_dock_baseline() + offset
                else:
                    location = self.editor.diagram.query_point(elm.api_object)

                    if location is None:
                        span_fraction = clamp_attachment_alignment(alignment)

                        if side_key == SchematicAttachmentSlot.TOP:
                            x_pos = self.w * span_fraction - elm.w * 0.5
                            y_pos = -elm.h - 40.0 - offset
                        elif side_key == SchematicAttachmentSlot.LEFT:
                            x_pos = -elm.w - 40.0 - offset
                            y_pos = self.rect().height() * span_fraction - elm.h * 0.5
                        elif side_key == SchematicAttachmentSlot.RIGHT:
                            x_pos = self.w + 40.0 + offset
                            y_pos = self.rect().height() * span_fraction - elm.h * 0.5
                        else:
                            x_pos = self.w * span_fraction - elm.w * 0.5
                            y_pos = self.get_bottom_dock_baseline() + offset
                    else:
                        local_position: QPointF = self.mapFromScene(QPointF(float(location.x), float(location.y)))
                        x_pos = float(local_position.x())
                        y_pos = float(local_position.y())

                elm.setPos(x_pos, y_pos)

                if self.editor.is_loading_diagram():
                    pass
                else:
                    elm.update_nexus(elm.pos())

        # Arrange line positions
        if self.editor.is_loading_diagram():
            pass
        else:
            self._terminal.process_callbacks(self.pos() + self._terminal.pos())

    def get_bottom_dock_baseline(self) -> float:
        """
        Return the baseline local Y coordinate used for bottom-docked children.

        :return: Bottom dock baseline.
        """
        return float(self.h + 40.0)

    def create_children_widgets(self, injections_by_tpe: Dict[DeviceType, List[FLUID_TYPES]]):
        """
        Create the icons of the elements that are attached to the API bus object
        Returns:
            Nothing
        """
        for tpe, dev_list in injections_by_tpe.items():

            if tpe == DeviceType.FluidPumpDevice:
                for elm in dev_list:
                    self.add_pump(elm)

            elif tpe == DeviceType.FluidTurbineDevice:
                for elm in dev_list:
                    self.add_turbine(elm)

            elif tpe == DeviceType.FluidP2XDevice:
                for elm in dev_list:
                    self.add_p2x(elm)

            else:
                raise Exception("Unknown device type:" + str(tpe))

        if self.editor.is_loading_diagram():
            pass
        else:
            self.arrange_children()

    def contextMenuEvent(self, event):
        """
        Display context menu
        @param event:
        @return:
        """
        menu = QMenu()
        menu.addSection(translate_context_menu_text("Fluid node"))

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Editor"),
                       icon_path=":/Icons/icons/edit.png",
                       function_ptr=self.edit)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Plot electrical profiles"),
                       icon_path=":/Icons/icons/plot.png",
                       function_ptr=self.plot_electrical_profiles)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Plot fluid profiles"),
                       icon_path=":/Icons/icons/plot.png",
                       function_ptr=self.plot_fluid_profiles)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Arrange"),
                       icon_path=":/Icons/icons/automatic_layout.png",
                       function_ptr=self.arrange_children)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Delete all the connections"),
                       icon_path=":/Icons/icons/delete_conn.png",
                       function_ptr=lambda: self.delete_all_connections(ask=True, delete_from_db=True))

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Delete"),
                       icon_path=":/Icons/icons/delete3.png",
                       function_ptr=self.remove)

        menu.addSection(translate_context_menu_text("Add"))

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Turbine"),
                       icon_path=":/Icons/icons/add_gen.png",
                       function_ptr=self.add_turbine)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Pump"),
                       icon_path=":/Icons/icons/add_gen.png",
                       function_ptr=self.add_pump)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("P2X"),
                       icon_path=":/Icons/icons/add_gen.png",
                       function_ptr=self.add_p2x)

        menu.exec_(event.screenPos())

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
        Compatibility catalog for named fluid-node attachment slots.
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
        Build the explicit slot catalog currently attached to this fluid node.
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
                slot_key: str = build_explicit_slot_key(owner_kind="fluid", side=side_key, order=order)
                slots[slot_key] = {"terminal_key": slot_key, "side": side_key.value}

        return slots

    def get_terminal_anchor_by_key(self,
                                   terminal_key: str = "default",
                                   graphic_object: GenericDiagramWidget | None = None,
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
                order_index = next(index + 1 for index, entry in enumerate(explicit_entries) if entry[2] is graphic_object)
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

        local_x, local_y = get_bar_slot_anchor(width=self.w,
                                               terminal_y=terminal_y,
                                               terminal_h=terminal_h,
                                               slot_key=terminal_key,
                                               alignment=alignment)

        return self.mapToScene(QPointF(local_x, local_y))

    def get_terminal_alignment_from_scene_point(self, side_key: str, scene_point: QPointF) -> float:
        """
        Convert one scene point to a normalized alignment value on the requested side.

        :param side_key: Attachment side.
        :param scene_point: Scene point selected by the user.
        :return: Normalized alignment factor.
        """
        local_point: QPointF = self.mapFromScene(scene_point)

        if side_key in (SchematicAttachmentSlot.TOP.value,
                        SchematicAttachmentSlot.BOTTOM.value,
                        SchematicAttachmentSlot.DEFAULT.value):
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
                                  side_key: SchematicAttachmentSlot) -> List[Tuple[int, str, LineGraphicTemplateItem]]:
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

    def get_branch_endpoint_for_graphic(self,
                                        graphic_object: LineGraphicTemplateItem) -> SchematicBranchEndpoint | None:
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
        terminal_y: float = self._terminal.pos().y() + self._terminal.rect().y()
        terminal_h: float = self._terminal.rect().height()
        local_point = QPointF(self.w * 0.5, terminal_y + terminal_h * 0.5)
        return self.mapToScene(local_point)

    def get_default_connection_local_point(self) -> QPointF:
        """
        Return the default local anchor used for fluid-path attachments.

        :return: Local attachment point.
        """
        terminal_y: float = self._terminal.pos().y() + self._terminal.rect().y()
        terminal_h: float = self._terminal.rect().height()
        local_x: float = self.w * 0.5
        local_y: float = terminal_y + terminal_h * 0.5
        return QPointF(local_x, local_y)

    def get_connection_local_point_from_local_point(self, local_point: QPointF) -> QPointF:
        """
        Project one local point to the fluid-node connection line.

        :param local_point: Requested local point.
        :return: Projected local attachment point.
        """
        terminal_y: float = self._terminal.pos().y() + self._terminal.rect().y()
        terminal_h: float = self._terminal.rect().height()
        projected_x, projected_y = project_point_to_bar_terminal(width=float(self.w),
                                                                 terminal_y=terminal_y,
                                                                 terminal_h=terminal_h,
                                                                 point_x=float(local_point.x()))
        return QPointF(projected_x, projected_y)

    def get_connection_local_point_from_scene_point(self, scene_point: QPointF) -> QPointF:
        """
        Project one scene point to the fluid-node connection line.

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

    def auto_assign_branch_slots(self) -> None:
        """
        Assign coordinate-based branch anchors to attached fluid paths from current geometry.
        """
        grouped_entries: Dict[SchematicAttachmentSlot, List[
            Tuple[float, str, LineGraphicTemplateItem, SchematicBranchEndpoint, Dict[str, Any]]
        ]] = {
            SchematicAttachmentSlot.LEFT: list(),
            SchematicAttachmentSlot.RIGHT: list(),
            SchematicAttachmentSlot.TOP: list(),
            SchematicAttachmentSlot.BOTTOM: list(),
        }
        local_center_x: float = self.w * 0.5
        terminal_y: float = self._terminal.pos().y() + self._terminal.rect().y()
        terminal_h: float = self._terminal.rect().height()
        local_center_y: float = terminal_y + terminal_h * 0.5
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
                    auto_slot = bool(attachment.get("auto_slot", existing_slot in ("", "default", "left", "right", "top", "bottom")))
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

                    local_other_point: QPointF = self.mapFromScene(other_point)
                    side_key: SchematicAttachmentSlot = infer_attachment_side_from_points(
                        origin=(local_center_x, local_center_y),
                        other=(local_other_point.x(), local_other_point.y()),
                        vertical_bias=1.0,
                    )
                    local_anchor: QPointF = self.get_connection_local_point_from_scene_point(other_point)
                    attachment["anchor_x"] = float(local_anchor.x())
                    attachment["anchor_y"] = float(local_anchor.y())
                    attachment["anchor_auto"] = True

                    if side_key in (SchematicAttachmentSlot.TOP, SchematicAttachmentSlot.BOTTOM):
                        sort_value = float(local_other_point.x())
                    else:
                        sort_value = float(local_other_point.y())

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
                    slot_key = build_explicit_slot_key(owner_kind="fluid", side=side_key, order=order_index)
                    attachment["side"] = side_key.value
                    attachment["order"] = order_index
                    attachment["slot"] = slot_key
                    attachment["terminal_key"] = slot_key
                    attachment["auto_slot"] = True
                    self.editor.diagram.set_attachment(api_object=branch_api_object,
                                                       endpoint=endpoint.value,
                                                       attachment=attachment)

    def add_object(self, api_obj: Union[None, EditableDevice] = None):
        """
        Add any recognized object
        :param api_obj: EditableDevice
        """

        if api_obj.device_type == DeviceType.FluidTurbineDevice:
            self.add_turbine(api_obj=api_obj)

        elif api_obj.device_type == DeviceType.FluidPumpDevice:
            self.add_pump(api_obj=api_obj)

        elif api_obj.device_type == DeviceType.FluidP2XDevice:
            self.add_p2x(api_obj=api_obj)

        else:
            raise Exception("Cannot add device of type {}".format(api_obj.device_type.value))

    def create_bus_if_necessary(self) -> Bus:
        """
        Create the internal electrical bus of the fluid node
        :return api_object.bus
        """

        if self.api_object.bus is None:
            # create the bus and assign it
            self.api_object.bus = self.editor.circuit.add_bus()

            # set the same name
            self.api_object.bus.name = "Bus of " + self.api_object.name

        return self.api_object.bus

    def add_turbine(self, api_obj: Union[None, FluidTurbine] = None):
        """

        :param api_obj:
        :return:
        """
        if api_obj is None or type(api_obj) is bool:
            api_obj = self.editor.circuit.add_fluid_turbine(node=self.api_object, api_obj=None)
            api_obj.generator = self.editor.circuit.add_generator(bus=self.create_bus_if_necessary())
            api_obj.generator.name = f"Turbine @{self.api_object.name}"

        _grph = FluidTurbineGraphicItem(parent=self, api_obj=api_obj, editor=self.editor)
        self._child_graphics.append(_grph)
        self.reset_child_to_auto_layout(child_graphic=_grph)
        if self.editor.is_loading_diagram():
            pass
        else:
            self.arrange_children()
        return _grph

    def add_pump(self, api_obj: Union[None, FluidPump] = None):
        """

        :param api_obj:
        :return:
        """
        if api_obj is None or type(api_obj) is bool:
            api_obj = self.editor.circuit.add_fluid_pump(node=self.api_object, api_obj=None)
            api_obj.generator = self.editor.circuit.add_generator(bus=self.create_bus_if_necessary())
            api_obj.generator.name = f"Pump @{self.api_object.name}"

        _grph = FluidPumpGraphicItem(parent=self, api_obj=api_obj, editor=self.editor)
        self._child_graphics.append(_grph)
        self.reset_child_to_auto_layout(child_graphic=_grph)
        if self.editor.is_loading_diagram():
            pass
        else:
            self.arrange_children()
        return _grph

    def add_p2x(self, api_obj: Union[None, FluidP2x] = None):
        """

        :param api_obj:
        :return:
        """
        if api_obj is None or type(api_obj) is bool:
            api_obj = self.editor.circuit.add_fluid_p2x(node=self.api_object, api_obj=None)
            api_obj.generator = self.editor.circuit.add_generator(bus=self.create_bus_if_necessary())
            api_obj.generator.name = f"P2X @{self.api_object.name}"

        _grph = FluidP2xGraphicItem(parent=self, api_obj=api_obj, editor=self.editor)
        self._child_graphics.append(_grph)
        self.reset_child_to_auto_layout(child_graphic=_grph)
        if self.editor.is_loading_diagram():
            pass
        else:
            self.arrange_children()
        return _grph

    def reset_child_to_auto_layout(self, child_graphic: FLUID_CHILD_GRAPHICS) -> None:
        """
        Reset one freshly created fluid child to automatic dock placement.

        The injection template seeds a temporary graphics position during construction.
        That position must not become persisted manual placement metadata for new
        fluid devices, otherwise every sibling keeps the same coordinates.

        :param child_graphic: Newly created child graphic.
        :return: ``None``.
        """
        dock = self.editor.diagram.get_dock(child_graphic.api_object)
        dock["side"] = str(dock.get("side", SchematicAttachmentSlot.BOTTOM.value))
        dock["order"] = self.get_next_child_dock_order(side_key=parse_attachment_slot(dock["side"]))
        dock["offset"] = 0.0
        dock["auto_layout"] = True
        dock.pop("alignment", None)
        dock.pop("anchor_x", None)
        dock.pop("anchor_y", None)
        dock.pop("child_anchor_x", None)
        dock.pop("child_anchor_y", None)
        self.editor.diagram.set_dock(child_graphic.api_object, dock)

    def get_next_child_dock_order(self, side_key: SchematicAttachmentSlot) -> int:
        """
        Compute the next automatic child order for one fluid-node side.

        :param side_key: Dock side.
        :return: One-based order value.
        """
        max_order: int = 0
        child_graphic: FLUID_CHILD_GRAPHICS

        for child_graphic in self._child_graphics:
            if child_graphic.api_object is None:
                pass
            else:
                dock = self.editor.diagram.get_dock(child_graphic.api_object)
                child_side = parse_attachment_slot(str(dock.get("side", SchematicAttachmentSlot.BOTTOM.value)))

                if child_side != side_key:
                    pass
                else:
                    child_order = int(dock.get("order", 0))

                    if child_order > max_order:
                        max_order = child_order
                    else:
                        pass

        return max_order + 1

    def delete_all_connections(self, ask: bool, delete_from_db: bool) -> None:
        """
        Delete all bus connections
        """
        if ask:
            ok = yes_no_question(self.tr('Are you sure that you want to delete this fluid node'),
                                 'Remove fluid node from schematic and DB' if delete_from_db else "Remove bus from schematic")
        else:
            ok = True

        if ok:
            self._terminal.remove_all_connections(delete_from_db=delete_from_db)

    def remove(self, ask=True):
        """
        Remove this element
        @return:
        """
        if ask:
            ok = yes_no_question(self.tr('Are you sure that you want to delete this fluid node'),
                                 self.tr('Remove fluid node'))
        else:
            ok = True

        if ok:
            self.editor.remove_element(device=self.api_object, graphic_object=self)

    def update_color(self):
        """
        Update the colour
        """
        self.set_tile_color(QBrush(ACTIVE['color']))

    def plot_electrical_profiles(self):
        """

        @return:
        """
        # get the index of this object
        if self.api_object is not None:
            if self.api_object.bus is not None:
                i = self.editor.circuit.fluid_nodes.index(self.api_object)
                self.editor.plot_bus(i, self.api_object.bus)
            else:
                error_msg(self.tr("No electrical bus attached :/"))
        else:
            error_msg(self.tr("No DB object attached :/"))

    def plot_fluid_profiles(self):
        """

        @return:
        """
        # get the index of this object
        if self.api_object is not None:
            i = self.editor.circuit.fluid_nodes.index(self.api_object)
            self.editor.plot_fluid_node(i, self.api_object)
        else:
            error_msg(self.tr("No DB object attached :/"))

    def set_values(self, i: int, Vm: float, Va: float, P: float, Q: float,
                   tpe: str, format_str="{:10.2f}"):
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
            vm = format_str.format(Vm)

            if self.api_object is not None:
                if self.api_object.bus is not None:
                    vm_kv = format_str.format(Vm * self.api_object.bus.Vnom)
                else:
                    vm_kv = "No electrical bus"
            else:
                vm_kv = ""
            va = format_str.format(Va)
            msg = f"Bus {i}"
            if tpe is not None:
                msg += f" [{tpe}]"
            msg += "<br>"
            msg += f"v={vm}&lt;{va}º pu<br>"
            msg += f"V={vm_kv} kV<br>"
            if P is not None:
                p = format_str.format(P)
                q = format_str.format(Q)
                msg += f"P={p} MW<br>Q={q} MVAr"
        else:
            msg = ""

        title = self.api_object.name if self.api_object is not None else ""
        self.label.setHtml(f'<html><head/><body><p><span style=" font-size:10pt;">{title}<br/></span>'
                           f'<span style=" font-size:6pt;">{msg}</span></p></body></html>')

        self.setToolTip(msg)

    def set_fluid_values(self, i: int, Vm: float, Va: float, P: float, Q: float,
                         tpe: str,
                         fluid_node_p2x_flow: float,
                         fluid_node_current_level: float,
                         fluid_node_spillage: float,
                         fluid_node_flow_in: float,
                         fluid_node_flow_out: float,
                         format_str="{:10.2f}"):
        """

        :param i:
        :param Vm:
        :param Va:
        :param P:
        :param Q:
        :param tpe:
        :param fluid_node_p2x_flow:
        :param fluid_node_current_level:
        :param fluid_node_spillage:
        :param fluid_node_flow_in:
        :param fluid_node_flow_out:
        :param format_str:
        :return:
        """
        if self.draw_labels:
            vm = format_str.format(Vm)

            if self.api_object is not None:
                if self.api_object.bus is not None:
                    vm_kv = format_str.format(Vm * self.api_object.bus.Vnom)
                else:
                    vm_kv = "No electrical bus"
            else:
                vm_kv = ""
            va = format_str.format(Va)
            msg = f"Bus {i}"
            if tpe is not None:
                msg += f" [{tpe}]"
            msg += "<br>"
            msg += f"v={vm}&lt;{va}º pu<br>"
            msg += f"V={vm_kv} kV<br>"
            if P is not None:
                p = format_str.format(P)
                q = format_str.format(Q)
                msg += f"P={p} MW<br>Q={q} MVAr<br>"

            if fluid_node_flow_in is not None:
                f_in = format_str.format(fluid_node_flow_in)
                msg += f"In={f_in} m3/s<br>"

            if fluid_node_flow_out is not None:
                f_out = format_str.format(fluid_node_flow_out)
                msg += f"Out={f_out} m3/s<br>"

            if fluid_node_spillage is not None:
                f_spill = format_str.format(fluid_node_spillage)
                msg += f"Spill={f_spill} m3/s<br>"

            if fluid_node_current_level is not None:
                f_lvl = format_str.format(fluid_node_current_level)
                msg += f"Lvl={f_lvl} m3<br>"

            if fluid_node_p2x_flow is not None:
                f_p2x = format_str.format(fluid_node_p2x_flow)
                msg += f"P2X={f_p2x} m3/s<br>"

        else:
            msg = ""

        title = self.api_object.name if self.api_object is not None else ""
        self.label.setHtml(f'<html><head/><body><p><span style=" font-size:10pt;">{title}<br/></span>'
                           f'<span style=" font-size:6pt;">{msg}</span></p></body></html>')

        self.setToolTip(msg)
