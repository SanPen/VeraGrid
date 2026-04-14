# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import numpy as np
from typing import TYPE_CHECKING, List, Union, cast, Any
from PySide6.QtCore import Qt, QPoint, QRectF, QPointF
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QBrush, QColor, QCursor, QTransform, QFont
from PySide6.QtWidgets import QMenu, QGraphicsItem, QGraphicsRectItem, QGraphicsSceneMouseEvent

from VeraGrid.Gui.gui_functions import add_menu_entry
from VeraGrid.Gui.Diagrams.SchematicWidget.terminal_item import RoundTerminalItem
from VeraGrid.Gui.Diagrams.generic_graphics import GenericDiagramWidget, ACTIVE, DEACTIVATED
from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import (DeviceType,
                                         ConverterControlType,
                                         SchematicAutoRouteStyle,
                                         SchematicRouteKind,
                                         TerminalType)  # Assuming VSC controls might be relevant later

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget
    from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.line_graphics_template import \
        LineGraphicTemplateItem  # For type hints if needed later
    from VeraGrid.Gui.Diagrams.SchematicWidget.terminal_item import RoundTerminalItem, BarTerminalItem


class VscGraphicItem3Term(GenericDiagramWidget, QGraphicsRectItem):
    """
    Graphics item for the 3-Terminal VSC converter
    """

    def __init__(self,
                 editor: SchematicWidget,
                 api_object: VSC,
                 pos: QPoint = None,
                 parent=None,
                 draw_labels: bool = True):
        """
        Constructor for the 3-Terminal VSC Graphic Item.

        :param editor: SchematicWidget instance
        :param api_object: VSC API object
        :param pos: Initial position
        :param parent: Parent item
        :param draw_labels: Whether to draw labels
        """
        GenericDiagramWidget.__init__(self, parent=parent, api_object=api_object, editor=editor,
                                      draw_labels=draw_labels)
        QGraphicsRectItem.__init__(self, parent=parent)

        # Make it a square
        self.w = 68  # Width of the VSC symbol (match 2-terminal size)
        self.h = self.w  # Height of the VSC symbol
        self.setRect(0.0, 0.0, self.w, self.h)

        self.draw_labels = draw_labels

        # Color and style based on active state
        self.pen_width = 2.2
        self.r: float = 0.0
        if self.api_object.active:
            self.color = ACTIVE['color']
            self.style = ACTIVE['style']
        else:
            self.color = DEACTIVATED['color']
            self.style = DEACTIVATED['style']

        # Setup pen, brush, flags and cursor
        self.setPen(QPen(self.color, self.pen_width, self.style))
        self.setBrush(QBrush(self._body_fill_color()))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setTransformOriginPoint(self.get_rotation_origin_local_point())

        if pos is not None:
            self.setPos(pos)
        else:
            self.setPos(QPoint(0, 0))

        # --- Create Terminals ---
        self.terminal_size = 11.0
        r = self.terminal_size / 2.0
        # Terminal positions (top-left of the round marker)
        t_ac_pos = QPointF(self.w + 6.0 - r, self.h * 0.5 - r)
        t_dc_p_pos = QPointF(-6.0 - r, self.h * 0.34 - r)
        t_dc_n_pos = QPointF(-6.0 - r, self.h * 0.66 - r)

        # self.terminals: List[RoundTerminalItem] = list()
        self.terminal_ac: RoundTerminalItem | None = None
        self.terminal_dc_p: RoundTerminalItem | None = None
        self.terminal_dc_n: RoundTerminalItem | None = None
        self.conn_line_ac: LineGraphicTemplateItem | None = None
        self.conn_line_dc_p: LineGraphicTemplateItem | None = None
        self.conn_line_dc_n: LineGraphicTemplateItem | None = None

        # AC Terminal (Index 0)
        self.terminal_ac = RoundTerminalItem("ac", parent=self, editor=self.editor, terminal_type=TerminalType.AC,
                                             h=self.terminal_size, w=self.terminal_size)
        self.terminal_ac.setPos(t_ac_pos)
        self.terminal_ac.setRotation(0)  # Points right
        self.terminal_ac.setPen(QPen(self.color, self.pen_width, self.style))

        # DC+ Terminal (Index 1)
        self.terminal_dc_p = RoundTerminalItem("dc_p", parent=self, editor=self.editor, terminal_type=TerminalType.DC_P,
                                               h=self.terminal_size, w=self.terminal_size)
        self.terminal_dc_p.setPos(t_dc_p_pos)
        self.terminal_dc_p.setRotation(0)  # Points left
        self.terminal_dc_p.setPen(QPen(self.color, self.pen_width, self.style))

        # DC- Terminal (Index 2)
        self.terminal_dc_n = RoundTerminalItem("dc_n", parent=self, editor=self.editor, terminal_type=TerminalType.DC_N,
                                               h=self.terminal_size, w=self.terminal_size)
        self.terminal_dc_n.setPos(t_dc_n_pos)
        self.terminal_dc_n.setRotation(0)  # Points left
        self.terminal_dc_n.setPen(QPen(self.color, self.pen_width, self.style))
        self._style_terminals()

        self.set_terminal_tooltips()

        # self.setRotation(180)

    def get_rotation_origin_local_point(self) -> QPointF:
        """
        Return the local rotation origin used for this three-terminal VSC.

        The symbol and its three round terminals must rotate as one rigid body
        around the geometric center of the square.

        :return: Local rotation origin.
        """
        return self.rect().center()

    def apply_rotation_state(self, refresh_connections: bool) -> None:
        """
        Apply the persisted rotation angle to the live graphics item.

        :param refresh_connections: Refresh connected routes afterwards.
        :return: ``None``.
        """
        self.setTransformOriginPoint(self.get_rotation_origin_local_point())
        self.setRotation(self.r)

        if refresh_connections:
            self.update_conn()
        else:
            pass

    def set_rotation_angle(self, angle_degrees: float, persist: bool) -> None:
        """
        Set one persisted rotation angle for this VSC symbol.

        :param angle_degrees: Rotation angle in degrees.
        :param persist: Update the backing diagram element.
        :return: ``None``.
        """
        normalized_angle: float = float(angle_degrees) % 360.0
        self.r = normalized_angle
        self.apply_rotation_state(refresh_connections=True)

        if persist:
            self.editor.update_diagram_element(device=self.api_object,
                                               x=self.pos().x(),
                                               y=self.pos().y(),
                                               w=self.w,
                                               h=self.h,
                                               r=self.r,
                                               draw_labels=self.draw_labels,
                                               graphic_object=self)
        else:
            pass

    def rotate_90(self) -> None:
        """
        Rotate the VSC by ninety degrees and persist the change.

        :return: ``None``.
        """
        self.set_rotation_angle(angle_degrees=self.r + 90.0, persist=True)

    def _body_fill_color(self) -> QColor:
        """
        Body fill with strong contrast in dark/light themes.
        """
        if self.color.lightness() > 127:
            return QColor(35, 35, 35, 220)
        else:
            return QColor(245, 245, 245, 220)

    def _style_terminals(self) -> None:
        """
        Keep terminal points readable and consistent with current color/style.
        """
        terminal_fill = QColor(self.color)
        terminal_fill.setAlpha(220)
        for terminal in (self.terminal_ac, self.terminal_dc_p, self.terminal_dc_n):
            terminal.setBrush(QBrush(terminal_fill))
            terminal.setPen(QPen(self.color, self.pen_width, self.style))

    @property
    def api_object(self) -> VSC:
        return self._api_object

    @property
    def editor(self) -> SchematicWidget:
        return self._editor

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """Paint the VSC symbol."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # Draw the main rectangle (square)
        painter.setPen(QPen(self.color, self.pen_width, self.style))
        painter.setBrush(QBrush(self._body_fill_color()))
        painter.drawRect(self.rect())

        # Draw a diagonal line from top-right to bottom-left
        pen = QPen(self.color, self.pen_width)
        painter.setPen(pen)
        inset = max(1.0, self.pen_width * 0.7)
        painter.drawLine(QPointF(self.w - inset, inset), QPointF(inset, self.h - inset))

        # Draw AC/DC symbols inside the box near terminals
        txt_font = QFont(painter.font())
        txt_font.setBold(True)
        txt_font.setPointSizeF(self.h * 0.34)
        painter.setFont(txt_font)

        # Align each symbol center to the corresponding terminal centerline, shifted up slightly.
        up_shift = 2.0
        ac_y = self.terminal_ac.pos().y() + self.terminal_size * 0.5 - up_shift
        dc_p_y = self.terminal_dc_p.pos().y() + self.terminal_size * 0.5 - up_shift
        dc_n_y = self.terminal_dc_n.pos().y() + self.terminal_size * 0.5 - up_shift

        text_rect_size = self.h * 0.34
        ac_x = self.w * 0.82
        dc_x = self.w * 0.13
        painter.drawText(
            QRectF(ac_x - text_rect_size / 2, ac_y - text_rect_size / 2, text_rect_size,
                   text_rect_size), Qt.AlignmentFlag.AlignCenter, "~")
        painter.drawText(QRectF(dc_x - text_rect_size / 2, dc_p_y - text_rect_size / 2, text_rect_size,
                                text_rect_size), Qt.AlignmentFlag.AlignCenter, "+")
        painter.drawText(QRectF(dc_x - text_rect_size / 2, dc_n_y - text_rect_size / 2, text_rect_size,
                                text_rect_size), Qt.AlignmentFlag.AlignCenter, "-")

    def set_terminal_tooltips(self):
        """Set tooltips for the terminals."""
        if self.api_object:
            self.terminal_ac.setToolTip(
                f"AC Terminal ({self.api_object.bus_to.name if self.api_object.bus_to else 'Unconnected'})")
            self.terminal_dc_p.setToolTip(
                f"DC+ Terminal ({self.api_object.bus_from.name if self.api_object.bus_from else 'Unconnected'})")
            self.terminal_dc_n.setToolTip(
                f"DC- Terminal ({self.api_object.bus_dc_n.name if self.api_object.bus_dc_n else 'Unconnected'})")

    def update_conn(self):
        """Update the connection lines attached to this item."""
        if self.conn_line_ac is not None:
            self.conn_line_ac.update_ports()
        if self.conn_line_dc_p is not None:
            self.conn_line_dc_p.update_ports()
        if self.conn_line_dc_n is not None:
            self.conn_line_dc_n.update_ports()

    def get_associated_widgets(self) -> List[LineGraphicTemplateItem]:
        """Return the graphical line items connected to this VSC."""
        return [self.conn_line_ac, self.conn_line_dc_p, self.conn_line_dc_n]

    def get_connection_layout_key(self, conn_line: "LineGraphicTemplateItem") -> str | None:
        """
        Resolve one persisted terminal-connection key for a connector line.

        :param conn_line: Connector line item.
        :return: Connection key or ``None`` when the line is unrelated.
        """
        terminal_item: RoundTerminalItem | None = None

        if conn_line.get_terminal_from_parent() is self:
            terminal_item = cast(RoundTerminalItem | None, conn_line.get_terminal_from())
        elif conn_line.get_terminal_to_parent() is self:
            terminal_item = cast(RoundTerminalItem | None, conn_line.get_terminal_to())
        else:
            return None

        if terminal_item is None:
            return None
        elif terminal_item.terminal_type == TerminalType.AC:
            return "ac"
        elif terminal_item.terminal_type == TerminalType.DC_P:
            return "dc_p"
        elif terminal_item.terminal_type == TerminalType.DC_N:
            return "dc_n"
        else:
            return None

    def _get_or_create_connection_layout_metadata(self, connection_key: str) -> dict[str, Any]:
        """
        Return one mutable persisted metadata record for a terminal connector.

        :param connection_key: Connection key.
        :return: Connector metadata dictionary.
        """
        location = self.editor.diagram.query_point(self.api_object)

        if location is None:
            location = self.editor.diagram.update_graphic_location(api_object=self.api_object,
                                                                   x=self.pos().x(),
                                                                   y=self.pos().y(),
                                                                   w=self.w,
                                                                   h=self.h,
                                                                   r=self.r,
                                                                   draw_labels=self.draw_labels)
        else:
            pass

        terminal_connections: Any = location.layout_metadata.get("vsc_terminal_connections", None)

        if isinstance(terminal_connections, dict):
            pass
        else:
            terminal_connections = dict()
            location.layout_metadata["vsc_terminal_connections"] = terminal_connections

        connection_metadata: Any = terminal_connections.get(connection_key, None)

        if isinstance(connection_metadata, dict):
            return connection_metadata
        else:
            connection_metadata = dict()
            terminal_connections[connection_key] = connection_metadata
            return connection_metadata

    def get_connection_route_points(self, conn_line: "LineGraphicTemplateItem") -> list[tuple[float, float]]:
        """
        Return persisted route points for one VSC terminal connector.

        :param conn_line: Connector line item.
        :return: Route points.
        """
        connection_key = self.get_connection_layout_key(conn_line=conn_line)

        if connection_key is None:
            return list()
        else:
            pass

        connection_metadata = self._get_or_create_connection_layout_metadata(connection_key=connection_key)
        route_points: Any = connection_metadata.get("points", list())

        if isinstance(route_points, list):
            return list(route_points)
        else:
            return list()

    def should_preserve_connection_route_shape(self, conn_line: "LineGraphicTemplateItem") -> bool:
        """
        Return whether one VSC terminal connector should preserve saved elbows.

        :param conn_line: Connector line item.
        :return: Preservation flag.
        """
        connection_key = self.get_connection_layout_key(conn_line=conn_line)

        if connection_key is None:
            return False
        else:
            pass

        connection_metadata = self._get_or_create_connection_layout_metadata(connection_key=connection_key)
        route_kind_text: str = str(connection_metadata.get("kind", ""))
        locked: bool = bool(connection_metadata.get("locked", False))

        if locked:
            return True
        elif route_kind_text == SchematicRouteKind.MANUAL_POLYLINE.value:
            return True
        elif route_kind_text == SchematicRouteKind.MANUAL_ORTHOGONAL.value:
            return True
        else:
            return False

    def get_connection_auto_route_style(self, conn_line: "LineGraphicTemplateItem") -> SchematicAutoRouteStyle:
        """
        Return the automatic route style for one VSC terminal connector.

        :param conn_line: Connector line item.
        :return: Route-style enum.
        """
        connection_key = self.get_connection_layout_key(conn_line=conn_line)

        if connection_key is None:
            return SchematicAutoRouteStyle.RETICULAR
        else:
            pass

        connection_metadata = self._get_or_create_connection_layout_metadata(connection_key=connection_key)
        route_style_text: str = str(connection_metadata.get("route_style", SchematicAutoRouteStyle.RETICULAR.value))

        if route_style_text == SchematicAutoRouteStyle.STRAIGHT.value:
            return SchematicAutoRouteStyle.STRAIGHT
        else:
            return SchematicAutoRouteStyle.RETICULAR

    def set_connection_auto_route_style(self,
                                        conn_line: "LineGraphicTemplateItem",
                                        route_style: SchematicAutoRouteStyle) -> None:
        """
        Persist one automatic route style for a VSC terminal connector.

        :param conn_line: Connector line item.
        :param route_style: Requested route style.
        :return: ``None``.
        """
        connection_key = self.get_connection_layout_key(conn_line=conn_line)

        if connection_key is None:
            return
        else:
            pass

        connection_metadata = self._get_or_create_connection_layout_metadata(connection_key=connection_key)
        connection_metadata["route_style"] = route_style.value
        connection_metadata["kind"] = SchematicRouteKind.AUTO_POLYLINE.value
        connection_metadata["locked"] = False

    def set_connection_route_points(self,
                                    conn_line: "LineGraphicTemplateItem",
                                    points: list[tuple[float, float]],
                                    kind: SchematicRouteKind,
                                    locked: bool = False) -> None:
        """
        Persist one manual or automatic route for a VSC terminal connector.

        :param conn_line: Connector line item.
        :param points: Route points.
        :param kind: Route kind.
        :param locked: Lock flag.
        :return: ``None``.
        """
        connection_key = self.get_connection_layout_key(conn_line=conn_line)

        if connection_key is None:
            return
        else:
            pass

        connection_metadata = self._get_or_create_connection_layout_metadata(connection_key=connection_key)
        connection_metadata["points"] = list(points)
        connection_metadata["kind"] = kind.value
        connection_metadata["locked"] = bool(locked)

        if "route_style" not in connection_metadata:
            connection_metadata["route_style"] = SchematicAutoRouteStyle.RETICULAR.value
        else:
            pass

    def get_connection_attachment(self,
                                  conn_line: "LineGraphicTemplateItem",
                                  endpoint: str) -> dict[str, Any]:
        """
        Return persisted endpoint-anchor metadata for one connector endpoint.

        :param conn_line: Connector line item.
        :param endpoint: Endpoint key.
        :return: Attachment metadata.
        """
        connection_key = self.get_connection_layout_key(conn_line=conn_line)

        if connection_key is None:
            return dict()
        else:
            pass

        connection_metadata = self._get_or_create_connection_layout_metadata(connection_key=connection_key)
        attachments: Any = connection_metadata.get("attachments", None)

        if isinstance(attachments, dict):
            pass
        else:
            attachments = dict()
            connection_metadata["attachments"] = attachments

        attachment: Any = attachments.get(endpoint, None)

        if isinstance(attachment, dict):
            return dict(attachment)
        else:
            return dict()

    def set_connection_attachment(self,
                                  conn_line: "LineGraphicTemplateItem",
                                  endpoint: str,
                                  attachment: dict[str, Any]) -> None:
        """
        Persist endpoint-anchor metadata for one connector endpoint.

        :param conn_line: Connector line item.
        :param endpoint: Endpoint key.
        :param attachment: Attachment metadata.
        :return: ``None``.
        """
        connection_key = self.get_connection_layout_key(conn_line=conn_line)

        if connection_key is None:
            return
        else:
            pass

        connection_metadata = self._get_or_create_connection_layout_metadata(connection_key=connection_key)
        attachments: Any = connection_metadata.get("attachments", None)

        if isinstance(attachments, dict):
            pass
        else:
            attachments = dict()
            connection_metadata["attachments"] = attachments

        attachments[endpoint] = dict(attachment)

    def get_extra_graphics(self):
        """Return terminals associated with this widget."""
        return [self.terminal_ac, self.terminal_dc_p, self.terminal_dc_n]

    def recolour_mode(self):
        """Change the colour according to the system theme and active state."""
        if self.api_object is None:
            return

        if self.api_object.active:
            self.color = ACTIVE['color']
            self.style = ACTIVE['style']
        else:
            self.color = DEACTIVATED['color']
            self.style = DEACTIVATED['style']

        pen = QPen(self.color, self.pen_width, self.style)
        self.setPen(pen)
        self.setBrush(QBrush(self._body_fill_color()))

        self._style_terminals()

        if self.conn_line_ac is not None:
            self.conn_line_ac.recolour_mode()
        if self.conn_line_dc_p is not None:
            self.conn_line_dc_p.recolour_mode()
        if self.conn_line_dc_n is not None:
            self.conn_line_dc_n.recolour_mode()

        self.update()  # Request repaint

    def set_enable(self, val=True):
        """Set the enable value, graphically and in the API."""
        self.api_object.active = val
        self.recolour_mode()

    def mouseMoveEvent(self, event: 'QGraphicsSceneMouseEvent'):
        """Handle mouse move event."""
        super().mouseMoveEvent(event)
        self.editor.update_diagram_element(device=self.api_object,
                                           x=self.pos().x(),
                                           y=self.pos().y(),
                                           w=self.w,
                                           h=self.h,
                                           r=self.rotation(),
                                           graphic_object=self)
        self.update_conn()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """Handle mouse press: select item and show in editor."""
        super().mousePressEvent(event)  # Handle selection
        if self.api_object is not None:
            self.editor.set_editor_model(api_object=self.api_object)

    def mouseDoubleClickEvent(self, event):
        """ On double-click, potentially open an editor (optional)."""
        # Currently no specific editor for VSC, but could be added.
        # self.edit()
        pass

    def delete(self):
        """Delete the VSC and its connections."""
        # Remove connections first
        self.remove_connection(self.conn_line_ac)
        self.remove_connection(self.conn_line_dc_p)
        self.remove_connection(self.conn_line_dc_n)

        # Remove the item itself
        self.editor.diagram_scene.removeItem(self)

    def set_connection(self, terminal_type: TerminalType, bus: Bus, conn_line: LineGraphicTemplateItem):
        """Set a connection to a specific terminal."""

        success = False
        # Check type compatibility and update API / store line
        if terminal_type == TerminalType.OTHER:
            print(f"Error: Invalid terminal type {terminal_type} for VSC {self.api_object.name}")

        elif terminal_type == TerminalType.AC:
            if bus.is_dc:
                self.editor.gui.show_error_toast(
                    f"Connecting AC terminal of VSC '{self.api_object.name}' to DC bus '{bus.name}'")
            elif self.conn_line_ac is not None:
                self.editor.gui.show_error_toast(f"AC terminal of VSC {self.api_object.name} is already connected.")
            else:
                self.api_object.bus_to = bus
                self.conn_line_ac = conn_line
                self.set_terminal_tooltips()
                success = True

        elif terminal_type == TerminalType.DC_P:
            if not bus.is_dc:
                self.editor.gui.show_error_toast(
                    f"Connecting DC+ terminal of VSC '{self.api_object.name}' to AC bus '{bus.name}'")
            elif self.conn_line_dc_p is not None:
                self.editor.gui.show_error_toast(f"DC+ terminal of VSC {self.api_object.name} is already connected.")
            else:
                self.api_object.bus_from = bus
                self.conn_line_dc_p = conn_line
                self.set_terminal_tooltips()
                success = True

        elif terminal_type == TerminalType.DC_N:
            if not bus.is_dc:
                self.editor.gui.show_error_toast(
                    f"Connecting DC- terminal of VSC '{self.api_object.name}' to AC bus '{bus.name}'")
            elif self.conn_line_dc_n is not None:
                self.editor.gui.show_error_toast(f"DC- terminal of VSC {self.api_object.name} is already connected.")
            else:
                self.api_object.bus_dc_n = bus
                self.conn_line_dc_n = conn_line
                self.set_terminal_tooltips()
                success = True

        return success

    def redraw(self):
        """
        Redraw method - only recalculate position if VSC doesn't have saved coordinates
        :return:
        """
        # Only recalculate position if the VSC is at the default position (close to 0, 0)
        # This preserves saved positions when loading from file
        current_pos = self.pos()
        # Use small tolerance to handle floating-point precision issues
        if abs(current_pos.x()) < 1.0 and abs(current_pos.y()) < 1.0:
            # Only do automatic positioning if we're near the origin
            h1 = self.terminal_ac.pos().y() - (self.terminal_dc_p.pos().y() + self.terminal_dc_n.pos().y()) / 2.0
            b1 = self.terminal_ac.pos().x() - (self.terminal_dc_p.pos().x() + self.terminal_dc_n.pos().x()) / 2.0
            ang = np.arctan2(h1, b1)
            h2 = self.rect().height() / 2.0
            w2 = self.rect().width() / 2.0
            a = h2 * np.cos(ang) - w2 * np.sin(ang)
            b = w2 * np.sin(ang) + h2 * np.cos(ang)

            center = (self.terminal_ac.pos() + (
                        self.terminal_dc_p.pos() + self.terminal_dc_n.pos()) * 0.5) * 0.5 - QPointF(a, b)

            # Keep auto-placement separate from user-editable rotation so redraw
            # never wipes a saved orientation restored from the diagram.
            self.setPos(center)
            self.set_rotation_angle(angle_degrees=self.r + np.rad2deg(ang), persist=False)
        # If we're not near the origin, preserve the current position (likely loaded from file)
        self.update_conn()

    def remove_connection(self, conn_line: LineGraphicTemplateItem):
        """Remove a connection from a specific terminal."""
        if conn_line is None:
            return
        else:
            line = conn_line
            # Remove the line from the scene
            if line.scene():
                line.scene().removeItem(line)
            # Optionally clear the bus/cn reference in the api_object
            if line == self.conn_line_ac:
                self.api_object.bus_to = None
            elif line == self.conn_line_dc_p:
                self.api_object.bus_from = None
            elif line == self.conn_line_dc_n:
                self.api_object.bus_dc_n = None
            self.set_terminal_tooltips()

    def contextMenuEvent(self, event):
        """Show context menu."""
        if self.api_object is not None:
            menu = QMenu()

            # Enable/Disable
            pe = menu.addAction('Enable/Disable')
            pe_icon = QIcon()
            if self.api_object.active:
                pe_icon.addPixmap(QPixmap(":/Icons/icons/uncheck_all.png"))
            else:
                pe_icon.addPixmap(QPixmap(":/Icons/icons/check_all.png"))
            pe.setIcon(pe_icon)
            pe.triggered.connect(lambda: self.set_enable(not self.api_object.active))

            # Draw Labels (if applicable)
            # add_menu_entry(menu=menu,
            #                text="Draw labels",
            #                function_ptr=self.enable_disable_label_drawing, # Needs implementation if label drawing is kept
            #                checkeable=True,
            #                checked_value=self.draw_labels)

            # Delete
            menu.addSeparator()
            ra2 = menu.addAction('Delete')
            del_icon = QIcon()
            del_icon.addPixmap(QPixmap(":/Icons/icons/delete3.png"))
            ra2.setIcon(del_icon)
            ra2.triggered.connect(self.delete)

            # --- Add back original control/profile actions ---
            menu.addSeparator()

            add_menu_entry(menu=menu,
                           text="Control V AC from DC+",
                           function_ptr=self.control_v_from,
                           icon_path=":/Icons/icons/edit.png")

            add_menu_entry(menu=menu,
                           text="Control V AC from AC",
                           function_ptr=self.control_v_to,
                           icon_path=":/Icons/icons/edit.png")

            menu.addSeparator()

            add_menu_entry(menu=menu,
                           text="Rotate 90",
                           function_ptr=self.rotate_90,
                           icon_path=":/Icons/icons/rotate.svg")

            ra6 = menu.addAction('Plot profiles')
            plot_icon = QIcon()
            plot_icon.addPixmap(QPixmap(":/Icons/icons/plot.png"))
            ra6.setIcon(plot_icon)
            ra6.triggered.connect(self.plot_profiles)

            ra4 = menu.addAction('Assign rate to profile')
            ra4_icon = QIcon()
            ra4_icon.addPixmap(QPixmap(":/Icons/icons/assign_to_profile.png"))
            ra4.setIcon(ra4_icon)
            ra4.triggered.connect(self.assign_rate_to_profile)

            ra5 = menu.addAction('Assign active state to profile')
            ra5_icon = QIcon()
            ra5_icon.addPixmap(QPixmap(":/Icons/icons/assign_to_profile.png"))
            ra5.setIcon(ra5_icon)
            ra5.triggered.connect(self.assign_status_to_profile)

            menu.exec_(event.screenPos())
        else:
            pass

    def control_v_from(self):
        """
        Set control mode to regulate DC voltage based on DC+ side (Interpretation).
        Sets control1 to Vm_dcp.
        """
        if self.api_object.bus_to and self.api_object.bus_from:
            self.api_object.control1 = ConverterControlType.Vm_dc
            self.api_object.control1_dev = self.api_object.bus_from
            self.api_object.control1_val = 1.0  # Default to 1.0 pu

            print(f"VSC {self.api_object.name} control set: Control1=Vm_dcp (Bus: {self.api_object.bus_from.name})")
            self.editor.set_editor_model(api_object=self.api_object)  # Refresh editor view
        else:
            print("Error: Cannot set control_v_from, DC+ bus not connected.")

    def control_v_to(self):
        """
        Set control mode to regulate AC voltage based on AC side itself.
        Sets control1 to Vm_ac (controlling AC bus).
        Leaves control2 as is, or sets it to something default like Pac if necessary.
        """
        if self.api_object.bus_to:
            self.api_object.control1 = ConverterControlType.Vm_ac
            self.api_object.control1_dev = self.api_object.bus_to
            self.api_object.control1_val = 1.0  # Default to 1.0 pu

            print(f"VSC {self.api_object.name} control set: Control1=Vm_ac (Bus: {self.api_object.bus_to.name})")
            self.editor.set_editor_model(api_object=self.api_object)  # Refresh editor view
        else:
            print("Error: Cannot set control_v_to, AC bus not connected.")

    def assign_rate_to_profile(self):
        """
        Assign the snapshot rate to the profile
        """
        self._editor.set_rate_to_profile(self.api_object)

    def assign_status_to_profile(self):
        """
        Assign the snapshot rate to the profile
        """
        self._editor.set_active_status_to_profile(self.api_object)

    def plot_profiles(self) -> None:
        """
        Plot the time series profiles
        @return:
        """
        pass

    def assign_bus_to_vsc(self, terminal_vsc: RoundTerminalItem, bus_vsc:  RoundTerminalItem | BarTerminalItem) -> bool:
        """
        Assign the connected bus to a three-terminal VSC
        :return: if the connection was successful
        """
        if terminal_vsc.terminal_type == TerminalType.AC:
            if not bus_vsc.parent.api_object.is_dc:
                self.api_object.bus_to = bus_vsc.parent.api_object
                return True
            else:
                return False

        elif terminal_vsc.terminal_type == TerminalType.DC_P:
            if bus_vsc.parent.api_object.is_dc:
                self.api_object.bus_from = bus_vsc.parent.api_object
                return True
            else:
                return False

        elif terminal_vsc.terminal_type == TerminalType.DC_N:
            if bus_vsc.parent.api_object.is_dc:
                self.api_object.bus_dc_n = bus_vsc.parent.api_object
                return True
            else:
                return False

        else:
            print('Error in the VSC connection!')
            return False
