# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import sys
import numpy as np
from typing import Union, TYPE_CHECKING
from PySide6.QtCore import Qt, QLineF, QPointF, QRectF
from PySide6.QtGui import (QPen, QCursor, QPixmap, QBrush, QColor, QTransform, QPolygonF, QFont,
                           QPainter, QPainterPath, QPainterPathStroker)
from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsRectItem, QGraphicsPolygonItem,
                               QGraphicsEllipseItem, QGraphicsSceneMouseEvent, QGraphicsTextItem,
                               QGraphicsPathItem, QStyleOptionGraphicsItem, QWidget, QMenu)
from VeraGrid.Gui.Diagrams.generic_graphics import (ACTIVE, DEACTIVATED, OTHER, GenericDiagramWidget, TRANSPARENT,
                                                    WHITE, DraggableLabelItem)
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.route_geometry import (merge_route_with_endpoints,
                                                                           move_polyline_route_segment,
                                                                           move_polyline_route_vertex,
                                                                           normalize_route_points,
                                                                           sample_route_segment)
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.slot_geometry import (SchematicAttachmentSlot,
                                                                          infer_attachment_slot_from_route,
                                                                          parse_attachment_slot,
                                                                          parse_explicit_slot_key,
                                                                          requires_explicit_attachment_anchor)
from VeraGrid.Gui.Diagrams.SchematicWidget.terminal_item import BarTerminalItem, RoundTerminalItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Substation.bus_graphics import BusGraphicItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Fluid.fluid_node_graphics import FluidNodeGraphicItem
from VeraGrid.Gui.messages import yes_no_question
from VeraGrid.Gui.gui_functions import translate_context_menu_text

from VeraGridEngine.Devices.Diagrams.schematic_layout import build_default_branch_route
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Substation.busbar import BusBar
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Branches.winding import Winding
from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Branches.upfc import UPFC
from VeraGridEngine.Devices.Branches.switch import Switch
from VeraGridEngine.Devices.Branches.dc_line import DcLine
from VeraGridEngine.Devices.Branches.series_reactance import SeriesReactance
from VeraGridEngine.Devices.Branches.hvdc_line import HvdcLine
from VeraGridEngine.Devices.Fluid.fluid_node import FluidNode
from VeraGridEngine.Devices.Fluid.fluid_path import FluidPath
from VeraGridEngine.Devices.types import BRANCH_TYPES
from VeraGridEngine.enumerations import SchematicAutoRouteStyle, SchematicRouteKind, SwitchGraphicType


if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget
    from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.transformer3w_graphics import Transformer3WGraphicItem
    from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.transformerNw_graphics import TransformerNWGraphicItem
    from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.vsc_graphics_3term import VscGraphicItem3Term

NODE_GRAPHIC = Union[BusGraphicItem, FluidNodeGraphicItem]


class TransformerSymbol(QGraphicsRectItem):
    """
    TransformerSymbol
    """

    def __init__(self, parent, pen_width: int, h=80, w=80):
        QGraphicsRectItem.__init__(self, parent=parent)

        d = w / 2

        self.parent = parent

        self.width = pen_width
        self.pen_width = pen_width
        self.color = ACTIVE['color']
        self.style = ACTIVE['style']
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        QGraphicsRectItem.setPen(self, QPen(TRANSPARENT))
        self.setRect(QRectF(0, 0, w, h))

        self.c0 = QGraphicsEllipseItem(0, 0, d, d, parent=self)
        self.c1 = QGraphicsEllipseItem(0, 0, d, d, parent=self)
        self.c2 = QGraphicsEllipseItem(0, 0, d, d, parent=self)
        self.c0.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.c1.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.c2.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        self.c0.setPen(QPen(TRANSPARENT, self.width, self.style))
        self.c2.setPen(QPen(self.color, self.width, self.style))
        self.c1.setPen(QPen(self.color, self.width, self.style))

        fill_brush = QBrush(Qt.BrushStyle.NoBrush)
        self.c0.setBrush(fill_brush)
        self.c2.setBrush(fill_brush)

        self.c0.setPos(w * 0.35 - d / 2, h * 0.5 - d / 2)
        self.c1.setPos(w * 0.35 - d / 2, h * 0.5 - d / 2)
        self.c2.setPos(w * 0.65 - d / 2, h * 0.5 - d / 2)

        self.c0.setZValue(0)
        self.c1.setZValue(2)
        self.c2.setZValue(1)

    def set_colour(self, color: QColor, w, style: Qt.PenStyle):
        """
        Set color and style
        :param color: QColor instance
        :param w: width
        :param style: PenStyle instance
        :return:
        """
        line_w = float(w)
        pen = QPen(color, line_w, style)
        self.c2.setPen(pen)
        self.c1.setPen(pen)
        self.c0.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.c2.setBrush(QBrush(Qt.BrushStyle.NoBrush))

    def set_pen(self, pen: QPen):
        """

        :param pen:
        :return:
        """
        self.set_colour(color=pen.color(),
                        w=max(1.2, pen.widthF()),
                        style=pen.style())

    def setBrush(self, brush: QBrush | QColor) -> None:
        """
        Keep transformer coils hollow regardless of external fill requests.

        :param brush: Brush or color.
        :return: ``None``.
        """
        self.c0.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.c2.setBrush(QBrush(Qt.BrushStyle.NoBrush))

    def setPen(self, pen: QPen) -> None:
        """
        Apply one pen to the visible transformer coils.

        :param pen: Pen to apply.
        :return: ``None``.
        """
        self.c1.setPen(pen)
        self.c2.setPen(pen)

    def setToolTipText(self, toolTip: str):
        """
        Set branch tool tip text
        Args:
            toolTip: text
        """
        self.setToolTip(toolTip)
        self.c0.setToolTip(toolTip)
        self.c1.setToolTip(toolTip)
        self.c2.setToolTip(toolTip)

    def redraw(self):
        """

        :return:
        """
        self.setTransform(self.parent.get_symbol_transform(self.rect()))


class VscSymbol(QGraphicsRectItem):
    """
    VscSymbol
    """

    def __init__(self, parent, pen_width, h=68, w=68, icon_route: str | None = None):
        QGraphicsRectItem.__init__(self, parent=parent)

        self.parent = parent

        self.width = pen_width
        self.pen_width = pen_width
        self.color = ACTIVE['color']
        self.style = ACTIVE['style']
        self.icon_route = icon_route
        self.icon_graphic = None
        self.body = None
        self.divider = None
        self.text_ac = None
        self.text_dc = None

        self.setPen(QPen(TRANSPARENT))
        self.setRect(QRectF(0, 0, w, h))

        if self.icon_route is None:
            self.body = QGraphicsRectItem(QRectF(0, 0, w, h), parent=self)
            self.divider = QGraphicsLineItem(QLineF(w, 0, 0, h), parent=self)

            self.text_ac = QGraphicsTextItem("~", parent=self)
            self.text_dc = QGraphicsTextItem("=", parent=self)
            self.text_ac.document().setDocumentMargin(0.0)
            self.text_dc.document().setDocumentMargin(0.0)

            txt_font = QFont()
            txt_font.setBold(True)
            txt_font.setPointSizeF(max(15.0, 0.34 * h))

            self.text_ac.setFont(txt_font)
            self.text_dc.setFont(txt_font)

            self._layout_vector_labels()
            self._apply_vector_style(color=self.color, w=self.width, style=self.style)
        else:
            self.icon_graphic = QGraphicsRectItem(QRectF(0, 0, w, h), parent=self)
            self.icon_graphic.setBrush(QBrush(QPixmap(self.icon_route)))
            self.icon_graphic.setPen(QPen(TRANSPARENT, self.width, self.style))

    @staticmethod
    def _contrast_fill(color: QColor) -> QColor:
        """
        Get a subtle fill that keeps contrast in dark and light mode.
        """
        if color.lightness() > 127:
            return QColor(30, 30, 30, 255)
        else:
            return QColor(245, 245, 245, 255)

    def _apply_vector_style(self, color: QColor, w: float, style: Qt.PenStyle) -> None:
        """
        Apply colors and stroke for the vector VSC symbol.
        """
        if self.body is None:
            return

        line_w = max(2.0, float(w) * 0.45)
        pen = QPen(color, line_w, style)
        self.body.setPen(pen)
        self.body.setBrush(QBrush(self._contrast_fill(color)))
        self.divider.setPen(pen)
        self._layout_diagonal(line_w=line_w)

        self.text_ac.setDefaultTextColor(color)
        self.text_dc.setDefaultTextColor(color)

    @staticmethod
    def _place_text_center(item: QGraphicsTextItem, x: float, y: float) -> None:
        """
        Place text item by center coordinates.
        """
        rect = item.boundingRect()
        item.setPos(x - (rect.x() + rect.width() * 0.5),
                    y - (rect.y() + rect.height() * 0.5))

    def _layout_vector_labels(self) -> None:
        """
        Center AC/DC text symbols in their visual zones.
        """
        w = self.rect().width()
        h = self.rect().height()
        y_center = h * 0.475
        self._place_text_center(self.text_ac, w * 0.84, y_center)
        self._place_text_center(self.text_dc, w * 0.18, y_center)

    def _layout_diagonal(self, line_w: float) -> None:
        """
        Inset diagonal so stroke never protrudes out of the box corners.
        """
        if self.divider is None:
            return
        w = self.rect().width()
        h = self.rect().height()
        inset = max(1.0, line_w * 0.6)
        self.divider.setLine(QLineF(w - inset, inset, inset, h - inset))

    def set_colour(self, color: QColor, w, style: Qt.PenStyle):
        """
        Set color and style
        :param color: QColor instance
        :param w: width
        :param style: PenStyle instance
        :return:
        """
        if self.icon_route is None:
            self._apply_vector_style(color=color, w=w, style=style)
        else:
            self.setBrush(color)
            self.setPen(QPen(color, w, style))

    def set_pen(self, pen: QPen):
        """

        :param pen:
        :return:
        """
        if self.icon_route is None:
            self._apply_vector_style(color=pen.color(),
                                     w=max(1.2, pen.widthF()),
                                     style=pen.style())
        else:
            self.setPen(pen)

    def setToolTipText(self, toolTip: str):
        """
        Set branch tool tip text
        Args:
            toolTip: text
        """
        self.setToolTip(toolTip)

    def redraw(self):
        """

        :return:
        """
        self.setTransform(self.parent.get_symbol_transform(self.rect()))


class UpfcSymbol(VscSymbol):
    """
    UpfcSymbol
    """

    def __init__(self, parent, pen_width, h=48, w=48):
        VscSymbol.__init__(self, parent=parent, pen_width=pen_width, h=h, w=w, icon_route=":/Icons/icons/upfc.png")


class SeriesReactanceSymbol(VscSymbol):
    """
    UpfcSymbol
    """

    def __init__(self, parent, pen_width, h=30, w=30):
        VscSymbol.__init__(self, parent=parent, pen_width=pen_width, h=h, w=w,
                           icon_route=":/Icons/icons/reactance.png")


class BranchVectorSymbolBase(QGraphicsRectItem):
    """
    Shared vector base for compact branch symbols.
    """

    def __init__(self, parent, pen_width: float | int, h: float, w: float) -> None:
        """
        Build one compact vector branch symbol.

        :param parent: Parent branch graphic.
        :param pen_width: Reference pen width.
        :param h: Symbol height.
        :param w: Symbol width.
        :return: ``None``.
        """
        QGraphicsRectItem.__init__(self, parent=parent)

        self.parent = parent
        self.width = pen_width
        self.pen_width = pen_width
        self.color = ACTIVE['color']
        self.style = ACTIVE['style']
        self._stroke_items: list[QGraphicsLineItem | QGraphicsEllipseItem | QGraphicsPathItem] = list()
        self._fill_items: list[QGraphicsEllipseItem | QGraphicsPathItem] = list()

        self.setPen(QPen(TRANSPARENT))
        self.setRect(QRectF(0, 0, w, h))

    def _register(self,
                  item: QGraphicsLineItem | QGraphicsEllipseItem | QGraphicsPathItem,
                  fill_item: bool = False) -> QGraphicsLineItem | QGraphicsEllipseItem | QGraphicsPathItem:
        """
        Track child items that follow the symbol stroke and fill.

        :param item: Registered primitive.
        :param fill_item: Register it for fill updates too.
        :return: The same registered item.
        """
        self._stroke_items.append(item)

        if fill_item:
            self._fill_items.append(item)
        else:
            pass

        return item

    @staticmethod
    def _contrast_fill(color: QColor) -> QColor:
        """
        Keep a readable body fill in light and dark themes.
        """
        if color.lightness() > 127:
            fill = QColor(32, 32, 32, 255)
        else:
            fill = QColor(245, 245, 245, 255)

        fill.setAlpha(210)
        return fill

    def set_colour(self, color: QColor, w: float | int, style: Qt.PenStyle) -> None:
        """
        Set the branch symbol stroke and fill.

        :param color: Target stroke color.
        :param w: Requested width.
        :param style: Requested line style.
        :return: ``None``.
        """
        pen = QPen(color, max(1.8, float(w) * 0.42), style, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        item: QGraphicsLineItem | QGraphicsEllipseItem | QGraphicsPathItem

        for item in self._stroke_items:
            item.setPen(pen)

        fill_brush = QBrush(self._contrast_fill(color))
        fill_item: QGraphicsEllipseItem | QGraphicsPathItem
        for fill_item in self._fill_items:
            fill_item.setBrush(fill_brush)

    def set_pen(self, pen: QPen) -> None:
        """
        Apply one pen without changing the fill intent.

        :param pen: Symbol pen.
        :return: ``None``.
        """
        self.set_colour(color=pen.color(),
                        w=max(1.2, pen.widthF()),
                        style=pen.style())

    def setBrush(self, brush: QBrush | QColor) -> None:
        """
        Allow external callers to refresh only the body fill.

        :param brush: Fill brush or color.
        :return: ``None``.
        """
        brush_obj: QBrush = brush if isinstance(brush, QBrush) else QBrush(brush)
        item: QGraphicsEllipseItem | QGraphicsPathItem

        for item in self._fill_items:
            item.setBrush(brush_obj)

    def setToolTipText(self, toolTip: str) -> None:
        """
        Set branch tool tip text.

        :param toolTip: Tooltip text.
        :return: ``None``.
        """
        self.setToolTip(toolTip)

    def redraw(self) -> None:
        """
        Redraw using the parent line transform.

        :return: ``None``.
        """
        self.setTransform(self.parent.get_symbol_transform(self.rect()))


class SwitchSymbol(BranchVectorSymbolBase):
    """
    SwitchSymbol
    """

    def __init__(self, parent, pen_width: float | int, h: float = 36, w: float = 44) -> None:
        """
        Build one vector switch symbol.

        :param parent: Parent branch graphic.
        :param pen_width: Reference pen width.
        :param h: Symbol height.
        :param w: Symbol width.
        :return: ``None``.
        """
        BranchVectorSymbolBase.__init__(self, parent=parent, pen_width=pen_width, h=h, w=w)

        mid_y = h * 0.5
        left_line = QGraphicsLineItem(0.0, mid_y, w * 0.12, mid_y, parent=self)
        right_line = QGraphicsLineItem(w * 0.88, mid_y, w, mid_y, parent=self)
        self._register(left_line)
        self._register(right_line)

        body_path = QPainterPath()
        body_path.addRoundedRect(w * 0.12, h * 0.18, w * 0.76, h * 0.64, 6.0, 6.0)
        body = QGraphicsPathItem(body_path, parent=self)
        self._register(body, fill_item=True)


class DisconnectorSymbol(BranchVectorSymbolBase):
    """
    DisconnectorSymbol
    """

    def __init__(self, parent, pen_width: float | int, h: float = 36, w: float = 44) -> None:
        """
        Build one vector disconnector symbol.

        :param parent: Parent branch graphic.
        :param pen_width: Reference pen width.
        :param h: Symbol height.
        :param w: Symbol width.
        :return: ``None``.
        """
        BranchVectorSymbolBase.__init__(self, parent=parent, pen_width=pen_width, h=h, w=w)

        mid_y = h * 0.5
        left_line = QGraphicsLineItem(0.0, mid_y, w * 0.36, mid_y, parent=self)
        right_line = QGraphicsLineItem(w * 0.64, mid_y, w, mid_y, parent=self)
        self._register(left_line)
        self._register(right_line)

        left_contact = QGraphicsEllipseItem(w * 0.28, h * 0.42, w * 0.08, h * 0.16, parent=self)
        right_contact = QGraphicsEllipseItem(w * 0.64, h * 0.42, w * 0.08, h * 0.16, parent=self)
        self._register(left_contact, fill_item=True)
        self._register(right_contact, fill_item=True)

        knife = QGraphicsLineItem(w * 0.34, h * 0.50, w * 0.66, h * 0.24, parent=self)
        self._register(knife)


class HvdcSymbol(QGraphicsRectItem):
    """
    HvdcSymbol
    """

    def __init__(self, parent, pen_width, h=30, w=30):
        QGraphicsRectItem.__init__(self, parent=parent)

        w2 = int(w / 2)
        self.parent = parent

        self.width = pen_width
        self.pen_width = pen_width
        self.color = ACTIVE['color']
        self.style = ACTIVE['style']

        self.setPen(QPen(TRANSPARENT))
        self.setRect(QRectF(0, 0, w, h))

        offset = 3
        t_points = QPolygonF()
        t_points.append(QPointF(0, offset))
        t_points.append(QPointF(w - offset, w2))
        t_points.append(QPointF(0, w - offset))

        triangle = QGraphicsPolygonItem(self)
        triangle.setPolygon(t_points)
        triangle.setPen(QPen(WHITE))
        triangle.setBrush(QBrush(WHITE))

        line = QGraphicsRectItem(QRectF(h - offset, offset, offset, w - 2 * offset), parent=self)
        line.setPen(QPen(WHITE))
        line.setBrush(QBrush(WHITE))

    def set_colour(self, color: QColor, w, style: Qt.PenStyle):
        """
        Set color and style
        :param color: QColor instance
        :param w: width
        :param style: PenStyle instance
        :return:
        """
        self.setBrush(color)
        self.setPen(QPen(color, w, style))

    def set_pen(self, pen: QPen):
        """

        :param pen:
        :return:
        """
        self.setPen(pen)

    def setToolTipText(self, toolTip: str):
        """
        Set branch tool tip text
        Args:
            toolTip: text
        """
        self.setToolTip(toolTip)

    def redraw(self):
        """
        Redraw the HVDC symbol
        """
        self.setTransform(self.parent.get_symbol_transform(self.rect()))


class ArrowHead(QGraphicsPolygonItem):
    """
    This is the arrow object
    """

    def __init__(self,
                 parent: QGraphicsLineItem,
                 arrow_size: float,
                 position: float = 0.9,
                 under: bool = False,
                 backwards: bool = False,
                 separation: int = 5,
                 show_text: bool = True,
                 text_scale: float = 1.0):
        """
        Constructor
        :param parent: Parent line
        :param arrow_size: Size of the arrow
        :param position: proportion of the line where to locate the arrow
        :param under: Is it under?
        :param backwards: Is it backwards?
        :param separation: Separation
        :param show_text: Show the label?
        :param text_scale: Text scale
        """
        QGraphicsPolygonItem.__init__(self, parent=parent)

        self.parent: QGraphicsLineItem = parent
        self.arrow_size: float = arrow_size
        self.position: float = position
        self.under: bool = under
        self.backwards: float = backwards
        self.sep = separation

        self.label = DraggableLabelItem(self)
        self.label.document().setDocumentMargin(0.0)
        self.label.setHtml('<div style="font-size:9pt; font-weight:600; text-align:center;"></div>')
        self.show_text = show_text

        self.setPen(Qt.PenStyle.NoPen)

        # self.setFlag(self.GraphicsItemFlag.ItemIgnoresTransformations, True)

    def setScale(self, scale):
        """

        :param scale:
        :return:
        """
        super().setScale(scale)
        self.label.setScale(scale)

    def set_size(self, size: float):
        self.arrow_size: float = size
        self.redraw()

    def set_colour(self, color: QColor):
        """
        Set color and style
        :param color: QColor instance
        """
        self.setBrush(color)
        self.label.setDefaultTextColor(color)
        # self.label.setScale(w)

    def set_value(self, value: float, redraw=True, backwards=False, name="", units="", format_str="{:10.2f}",
                  draw_label: bool = True, visibility_filter_value=1e-4):
        """
        Set the sign with a value
        :param value: any real value
        :param redraw: redraw after the sign update
        :param backwards: draw backwards
        :param name: name of the displayed magnitude (i.e. Pf)
        :param units: the units of the displayed magnitude (i.e MW)
        :param format_str: the formatting string of the displayed magnitude
        :param visibility_filter_value: threshold to determine if to show this widget
        :param draw_label: Draw label
        """
        self.setVisible(bool(abs(value) > visibility_filter_value))
        self.backwards = backwards

        self.label.setVisible(draw_label)
        if draw_label:
            x = format_str.format(value)
            msg = f'{name}:{x} {units}'
            self.label.setHtml(f'<div style="font-size:9pt; font-weight:600; text-align:center;">{msg}</div>')
            self.setToolTip(msg)

        if redraw:
            self.redraw()

    def redraw(self) -> None:
        """
        Redraw the arrow
        """
        if isinstance(self.parent, LineGraphicTemplateItem):
            base_pt, segment = self.parent.get_route_sample(self.position)
            line = QLineF(QPointF(segment[0][0], segment[0][1]), QPointF(segment[1][0], segment[1][1]))
        else:
            line = self.parent.line()
            base_pt = line.p1() + (line.p2() - line.p1()) * self.position

        # the angle is added 180º if the sign is negative
        angle = - line.angle()

        p1 = -self.arrow_size if self.backwards else self.arrow_size
        p2 = -self.arrow_size if self.under else self.arrow_size
        arrow_p1 = base_pt - QTransform().rotate(angle).map(QPointF(p1, 0))
        arrow_p2 = base_pt - QTransform().rotate(angle).map(QPointF(p1, p2))
        arrow_polygon = QPolygonF([base_pt, arrow_p1, arrow_p2])

        self.setPolygon(arrow_polygon)

        if self.show_text:
            # if 90 < line.angle() <= 270:
            #     label_p = base_pt - QTransform().rotate(-angle).map(QPointF(20, -10 if self.under else 35))
            #     self.label.setPos(label_p)
            #     self.label.setRotation(-angle)
            # else:
            #     label_p = base_pt - QTransform().rotate(angle).map(QPointF(20, -10 if self.under else 35))
            #     self.label.setPos(label_p)
            #     self.label.setRotation(angle)

            if 90 < line.angle() <= 270:
                label_p = base_pt - QTransform().rotate(angle).map(QPointF(-20, -35 if self.under else +10))
                self.label.setRotation(angle + 180)
            else:
                label_p = base_pt - QTransform().rotate(angle).map(QPointF(40, -10 if self.under else 35))
                self.label.setRotation(angle)
            self.label.set_anchor_position(label_p)


class RouteSegmentHandleItem(QGraphicsEllipseItem):
    """
    Draggable handle for one editable interior route segment.
    """

    def __init__(self,
                 parent_branch: "LineGraphicTemplateItem",
                 segment_index: int,
                 radius: float = 6.0):
        """
        Initialize one draggable route handle.

        :param parent_branch: Owning branch graphic.
        :param segment_index: Editable segment index.
        :param radius: Handle radius.
        """
        QGraphicsEllipseItem.__init__(self, -radius, -radius, radius * 2.0, radius * 2.0, parent_branch)

        self.parent_branch: LineGraphicTemplateItem = parent_branch
        self.segment_index: int = segment_index
        self._drag_origin_scene_pos: QPointF | None = None
        self._drag_origin_route_points: list[tuple[float, float]] = list()

        self.setBrush(QBrush(QColor(245, 195, 70, 255)))
        self.setPen(QPen(QColor(32, 32, 32, 255), 1.5))
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self.setZValue(10)
        self.setVisible(False)

    def set_segment_index(self, segment_index: int) -> None:
        """
        Update the editable segment index.

        :param segment_index: Editable segment index.
        :return: ``None``.
        """
        self.segment_index = segment_index

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Capture the route state at the start of a segment drag.

        :param event: Mouse event.
        :return: ``None``.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin_scene_pos = event.scenePos()
            self._drag_origin_route_points = self.parent_branch.get_route_points_for_editing()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Move the owning branch polyline segment.

        :param event: Mouse event.
        :return: ``None``.
        """
        if self._drag_origin_scene_pos is None:
            super().mouseMoveEvent(event)
        else:
            delta = event.scenePos() - self._drag_origin_scene_pos
            self.parent_branch.move_route_segment(segment_index=self.segment_index,
                                                  original_points=self._drag_origin_route_points,
                                                  delta_x=delta.x(),
                                                  delta_y=delta.y())
            event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Finish the current route-segment drag.

        :param event: Mouse event.
        :return: ``None``.
        """
        self._drag_origin_scene_pos = None
        self._drag_origin_route_points = list()
        event.accept()


class RouteVertexHandleItem(QGraphicsRectItem):
    """
    Draggable handle for one interior route vertex.
    """

    def __init__(self,
                 parent_branch: "LineGraphicTemplateItem",
                 vertex_index: int,
                 half_size: float = 5.0):
        """
        Initialize one draggable vertex handle.

        :param parent_branch: Owning branch graphic.
        :param vertex_index: Editable vertex index.
        :param half_size: Half side length of the square handle.
        """
        QGraphicsRectItem.__init__(self, -half_size, -half_size, half_size * 2.0, half_size * 2.0, parent_branch)

        self.parent_branch: LineGraphicTemplateItem = parent_branch
        self.vertex_index: int = vertex_index

        self.setBrush(QBrush(QColor(85, 180, 255, 255)))
        self.setPen(QPen(QColor(20, 20, 20, 255), 1.5))
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self.setZValue(11)
        self.setVisible(False)

    def set_vertex_index(self, vertex_index: int) -> None:
        """
        Update the controlled vertex index.

        :param vertex_index: Vertex index.
        :return: ``None``.
        """
        self.vertex_index = vertex_index

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Move the associated route vertex.

        :param event: Mouse event.
        :return: ``None``.
        """
        self.parent_branch.move_route_vertex(vertex_index=self.vertex_index, scene_pos=event.scenePos())
        event.accept()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Accept the drag start.

        :param event: Mouse event.
        :return: ``None``.
        """
        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Accept the drag end.

        :param event: Mouse event.
        :return: ``None``.
        """
        event.accept()


class EndpointAlignmentHandleItem(QGraphicsEllipseItem):
    """
    Draggable handle for one branch endpoint alignment on its host node.
    """

    def __init__(self,
                 parent_branch: "LineGraphicTemplateItem",
                 endpoint: str,
                 radius: float = 5.5):
        """
        Initialize one endpoint alignment handle.

        :param parent_branch: Owning branch graphic.
        :param endpoint: Endpoint key.
        :param radius: Handle radius.
        """
        QGraphicsEllipseItem.__init__(self, -radius, -radius, radius * 2.0, radius * 2.0, parent_branch)

        self.parent_branch: LineGraphicTemplateItem = parent_branch
        self.endpoint: str = endpoint
        self._hit_radius: float = max(radius, 11.0)

        self.setBrush(QBrush(QColor(130, 255, 150, 255)))
        self.setPen(QPen(QColor(20, 20, 20, 255), 1.5))
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setZValue(40)
        self.setVisible(False)

    def shape(self) -> QPainterPath:
        """
        Widen hit testing so endpoint dragging does not fail when the handle overlaps the bus bar.

        :return: Hit-test path.
        """
        path = QPainterPath()
        path.addEllipse(QPointF(0.0, 0.0), self._hit_radius, self._hit_radius)
        return path

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Move the endpoint alignment along the owning node side.

        :param event: Mouse event.
        :return: ``None``.
        """
        self.parent_branch.move_endpoint_alignment(endpoint=self.endpoint, scene_pos=event.scenePos())
        event.accept()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Accept the drag start.

        :param event: Mouse event.
        :return: ``None``.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Accept the drag end.

        :param event: Mouse event.
        :return: ``None``.
        """
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        event.accept()


class LineGraphicTemplateItem(GenericDiagramWidget, QGraphicsLineItem):
    """
    LineGraphicItem
    """

    def __init__(self,
                 from_port: Union[BarTerminalItem, RoundTerminalItem],
                 to_port: Union[BarTerminalItem, RoundTerminalItem, None],
                 editor: SchematicWidget,
                 width=5,
                 api_object: Union[Line, Transformer2W, VSC, UPFC, HvdcLine, DcLine, FluidPath, None] = None,
                 arrow_size=10,
                 draw_labels: bool = True,
                 arrow_f_pos=0.2,
                 arrow_t_pos=0.8, ):
        """

        :param from_port:
        :param to_port:
        :param editor:
        :param width:
        :param api_object:
        :param arrow_size:
        :param draw_labels:
        """
        GenericDiagramWidget.__init__(self, parent=None, api_object=api_object, editor=editor, draw_labels=draw_labels)
        QGraphicsLineItem.__init__(self)

        if isinstance(api_object, Transformer2W):
            if isinstance(api_object, Winding):  # Winding is a sublass of Transformer
                self.symbol = None
            else:
                self.symbol = TransformerSymbol(parent=self, pen_width=width, h=80, w=80)
        elif isinstance(api_object, VSC):
            self.symbol = VscSymbol(parent=self, pen_width=width, h=68, w=68, icon_route=None)
        elif isinstance(api_object, UPFC):
            self.symbol = UpfcSymbol(parent=self, pen_width=width, h=48, w=48)
        elif isinstance(api_object, HvdcLine):
            self.symbol = HvdcSymbol(parent=self, pen_width=width, h=30, w=30)
        elif isinstance(api_object, SeriesReactance):
            self.symbol = SeriesReactanceSymbol(parent=self, pen_width=width, h=30, w=30)
        elif isinstance(api_object, Switch):
            if api_object.graphic_type == SwitchGraphicType.CircuitBreaker:
                self.symbol = SwitchSymbol(parent=self, pen_width=width, h=36, w=44)
            elif api_object.graphic_type == SwitchGraphicType.Disconnector:
                self.symbol = DisconnectorSymbol(parent=self, pen_width=width, h=36, w=44)
            else:
                self.symbol = DisconnectorSymbol(parent=self, pen_width=width, h=36, w=44)
        else:
            self.symbol = None

        self.scale = 1.0
        self.pen_style = Qt.PenStyle.SolidLine
        self.pen_color = QColor(0, 0, 0, 255)  # Black
        self.pen_width = width
        self.width = width

        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(self.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._route_item = QGraphicsPathItem(parent=self)
        self._route_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._route_item.setFlag(self.GraphicsItemFlag.ItemIsSelectable, False)
        # Render the branch stroke below symbols/arrows so converter/transformer
        # glyphs are not visually traversed by the line.
        self._route_item.setZValue(-5)
        self._rendered_path = QPainterPath()
        self._route_points: list[tuple[float, float]] = list()
        self._route_handles: list[RouteSegmentHandleItem] = list()
        self._vertex_handles: list[RouteVertexHandleItem] = list()
        self._endpoint_handles: dict[str, EndpointAlignmentHandleItem] = {
            "from": EndpointAlignmentHandleItem(parent_branch=self, endpoint="from"),
            "to": EndpointAlignmentHandleItem(parent_branch=self, endpoint="to"),
        }
        self._route_edit_active: bool = False

        self.pos1: QPointF = QPointF(0.0, 0.0)
        self.pos2: QPointF = QPointF(0.0, 0.0)

        self._from_port: Union[BarTerminalItem, RoundTerminalItem, None] = None
        self._to_port: Union[BarTerminalItem, RoundTerminalItem, None] = None

        # arrows
        self.view_arrows = True
        self.arrow_p_from = ArrowHead(parent=self, arrow_size=arrow_size, position=arrow_f_pos, under=False)
        self.arrow_q_from = ArrowHead(parent=self, arrow_size=arrow_size, position=arrow_f_pos, under=True)
        self.arrow_p_to = ArrowHead(parent=self, arrow_size=arrow_size, position=arrow_t_pos, under=False)
        self.arrow_q_to = ArrowHead(parent=self, arrow_size=arrow_size, position=arrow_t_pos, under=True)

        if from_port:
            self.set_from_port(from_port)

        if to_port:
            self.set_to_port(to_port)

        self.load_route_points_from_diagram()

        if from_port and to_port:
            if self.editor.is_loading_diagram():
                pass
            else:
                self.redraw()
        else:
            pass

        self.set_colour(self.color, self.width, self.style)

    @property
    def parent(self) -> NODE_GRAPHIC:
        return self._parent

    @property
    def editor(self) -> SchematicWidget:
        return self._editor

    @property
    def api_object(self) -> BRANCH_TYPES:
        return self._api_object

    def delete_from_associations(self):
        """
        Delete this object from other associations, i.e. for a line, delete from the terminal connections
        :return:
        """
        self._from_port.delete_hosting_connection(graphic_obj=self)
        self._to_port.delete_hosting_connection(graphic_obj=self)

    def get_terminal_from(self) -> Union[None, BarTerminalItem, RoundTerminalItem]:
        """
        Get the terminal from
        :return: TerminalItem 
        """
        return self._from_port

    def get_terminal_to(self) -> Union[None, BarTerminalItem, RoundTerminalItem]:
        """
        Get the terminal to
        :return: TerminalItem
        """
        return self._to_port

    def get_terminal_from_parent(self) -> Union[None, BusGraphicItem, Transformer3WGraphicItem, TransformerNWGraphicItem,
                                                FluidNodeGraphicItem, VscGraphicItem3Term]:
        """
        Get the terminal from parent object
        :return: TerminalItem 
        """
        if self._from_port is None:
            return None
        else:
            return self._from_port.get_parent()

    def get_terminal_to_parent(self) -> Union[None, BusGraphicItem, Transformer3WGraphicItem, TransformerNWGraphicItem,
                                              FluidNodeGraphicItem, VscGraphicItem3Term]:
        """
        Get the terminal to parent object
        :return: TerminalItem
        """
        if self._to_port is None:
            return None
        else:
            return self._to_port.get_parent()

    def update_ports(self):
        """

        :return:
        """
        self._from_port.update()
        self._to_port.update()

    def recolour_mode(self) -> None:
        """
        Change the colour according to the system theme
        """
        super().recolour_mode()

        self.set_colour(self.color, self.width, self.style)

    def enable_label_drawing(self) -> None:
        """
        Enable branch power labels immediately for visible arrows.

        :return: ``None``.
        """
        super().enable_label_drawing()
        self.arrow_p_from.label.setVisible(self.arrow_p_from.isVisible())
        self.arrow_q_from.label.setVisible(self.arrow_q_from.isVisible())
        self.arrow_p_to.label.setVisible(self.arrow_p_to.isVisible())
        self.arrow_q_to.label.setVisible(self.arrow_q_to.isVisible())

    def disable_label_drawing(self) -> None:
        """
        Disable branch power labels immediately.

        :return: ``None``.
        """
        super().disable_label_drawing()
        self.arrow_p_from.label.setVisible(False)
        self.arrow_q_from.label.setVisible(False)
        self.arrow_p_to.label.setVisible(False)
        self.arrow_q_to.label.setVisible(False)

    def load_route_points_from_diagram(self) -> None:
        """
        Load any persisted route points from the diagram compatibility layer.
        """
        if self.api_object is None:
            if self.is_vsc3_terminal_connection():
                owner_graphic = self.get_vsc3_connection_owner()

                if owner_graphic is None:
                    return
                else:
                    self._route_points = normalize_route_points(owner_graphic.get_connection_route_points(conn_line=self))
                    return
            else:
                return

        location = self.editor.diagram.query_point(self.api_object)
        if location is None:
            return

        route_points = self.editor.diagram.get_branch_route_points(self.api_object)
        if len(route_points) >= 2:
            self._route_points = normalize_route_points(route_points)

    def upgrade_legacy_layout_from_diagram(self) -> None:
        """
        Synthesize structured layout data for legacy branches before the first redraw.
        """
        if self.api_object is None:
            return
        elif self._from_port is None:
            return
        elif self._to_port is None:
            return
        else:
            pass

        self.editor.diagram.sync_branch_attachments(api_object=self.api_object)

        start_point: QPointF = self.get_endpoint_anchor(endpoint="from")
        end_point: QPointF = self.get_endpoint_anchor(endpoint="to")

        self.editor.diagram.upgrade_legacy_branch_layout(api_object=self.api_object,
                                                         start=(start_point.x(), start_point.y()),
                                                         end=(end_point.x(), end_point.y()))

    def get_render_points(self) -> list[tuple[float, float]]:
        """
        Replace persisted endpoints with the live endpoint positions and keep
        the saved interior polyline points when the route is manual.
        """
        start_point: QPointF = self.get_endpoint_anchor(endpoint="from")
        end_point: QPointF = self.get_endpoint_anchor(endpoint="to")
        start = (start_point.x(), start_point.y())
        end = (end_point.x(), end_point.y())

        if self.editor.is_loading_diagram() and len(self._route_points) >= 2:
            return merge_route_with_endpoints(start=start,
                                              end=end,
                                              persisted_points=self._route_points)
        elif self.api_object is not None and self.editor.diagram.should_preserve_branch_route_shape(self.api_object) and len(self._route_points) >= 2:
            return merge_route_with_endpoints(start=start,
                                              end=end,
                                              persisted_points=self._route_points)
        elif self.api_object is None:
            if self.is_vsc3_terminal_connection():
                owner_graphic = self.get_vsc3_connection_owner()

                if owner_graphic is None:
                    return [start, end]
                elif owner_graphic.should_preserve_connection_route_shape(conn_line=self) and len(self._route_points) >= 2:
                    return merge_route_with_endpoints(start=start,
                                                      end=end,
                                                      persisted_points=self._route_points)
                else:
                    return build_default_branch_route(start=start,
                                                      end=end,
                                                      route_style=self.get_branch_auto_route_style())
            else:
                return [start, end]
        else:
            from_attachment = self.get_persisted_endpoint_attachment(endpoint="from")
            to_attachment = self.get_persisted_endpoint_attachment(endpoint="to")
            from_order = from_attachment.get("order", None)
            to_order = to_attachment.get("order", None)
            return build_default_branch_route(start=start,
                                              end=end,
                                              start_order=from_order,
                                              end_order=to_order,
                                              route_style=self.get_branch_auto_route_style())

    def get_branch_auto_route_style(self) -> SchematicAutoRouteStyle:
        """
        Return the automatic route style currently assigned to this branch.

        :return: Branch-specific automatic route-style enum.
        """
        if self.api_object is None:
            if self.is_vsc3_terminal_connection():
                owner_graphic = self.get_vsc3_connection_owner()

                if owner_graphic is None:
                    return SchematicAutoRouteStyle.RETICULAR
                else:
                    return owner_graphic.get_connection_auto_route_style(conn_line=self)
            else:
                return SchematicAutoRouteStyle.STRAIGHT
        elif self.editor.diagram is None:
            return SchematicAutoRouteStyle.STRAIGHT
        else:
            return self.editor.diagram.get_branch_auto_route_style(api_object=self.api_object)

    def set_branch_auto_route_style(self, route_style: SchematicAutoRouteStyle) -> None:
        """
        Persist one branch-specific automatic route style and redraw the branch.

        :param route_style: Requested route-style enum.
        :return: ``None``.
        """
        if self.api_object is None:
            if self.is_vsc3_terminal_connection():
                owner_graphic = self.get_vsc3_connection_owner()

                if owner_graphic is None:
                    return
                else:
                    owner_graphic.set_connection_auto_route_style(conn_line=self, route_style=route_style)
                    self._route_points = list()
                    self.redraw()
                    return
            else:
                return
        elif self.editor.diagram is None:
            return
        else:
            self.editor.diagram.set_branch_auto_route_style(api_object=self.api_object, route_style=route_style)

        self.load_route_points_from_diagram()
        self.redraw()

    def set_branch_auto_route_style_reticular(self) -> None:
        """
        Switch this branch to the reticular automatic route style.

        :return: ``None``.
        """
        self.set_branch_auto_route_style(route_style=SchematicAutoRouteStyle.RETICULAR)

    def set_branch_auto_route_style_straight(self) -> None:
        """
        Switch this branch to the straight automatic route style.

        :return: ``None``.
        """
        self.set_branch_auto_route_style(route_style=SchematicAutoRouteStyle.STRAIGHT)

    def add_auto_route_style_menu(self, menu: QMenu) -> None:
        """
        Add the per-branch automatic route-style submenu when this branch is auto-routed.

        :param menu: Parent context menu.
        :return: ``None``.
        """
        current_route_style: SchematicAutoRouteStyle
        route_style_menu: QMenu
        reticular_action: object
        straight_action: object

        if self.api_object is None:
            if self.is_vsc3_terminal_connection():
                current_route_style = self.get_branch_auto_route_style()
                route_style_menu = menu.addMenu(translate_context_menu_text("Auto route style"))
                reticular_action = route_style_menu.addAction(translate_context_menu_text("Reticular"))
                straight_action = route_style_menu.addAction(translate_context_menu_text("Straight"))
            else:
                return
        else:
            current_route_style = self.get_branch_auto_route_style()
            route_style_menu = menu.addMenu(translate_context_menu_text("Auto route style"))
            reticular_action = route_style_menu.addAction(translate_context_menu_text("Reticular"))
            straight_action = route_style_menu.addAction(translate_context_menu_text("Straight"))

        reticular_action.setCheckable(True)
        straight_action.setCheckable(True)
        reticular_action.setChecked(current_route_style == SchematicAutoRouteStyle.RETICULAR)
        straight_action.setChecked(current_route_style == SchematicAutoRouteStyle.STRAIGHT)
        reticular_action.triggered.connect(self.set_branch_auto_route_style_reticular)
        straight_action.triggered.connect(self.set_branch_auto_route_style_straight)

    def get_route_points_for_editing(self) -> list[tuple[float, float]]:
        """
        Return the currently rendered route points used by the manual editor.

        :return: Route points.
        """
        return normalize_route_points(self.get_render_points())

    def refresh_z_order(self) -> None:
        """
        Keep the branch subtree above buses only while it is selected for editing.

        :return: ``None``.
        """
        if self.is_route_edit_active():
            self.setZValue(4)
        else:
            self.setZValue(-1)

    def is_route_edit_active(self) -> bool:
        """
        Return whether the manual route editor is explicitly active for this branch.

        Plain selection must not show edit handles. Handles only appear after a direct
        click activates editing on the selected branch.

        :return: ``True`` when route-edit handles should be shown.
        """
        return self._route_edit_active and self.isSelected()

    def set_route_edit_active(self, active: bool) -> None:
        """
        Set the explicit route-edit activation state.

        :param active: Requested edit activation state.
        :return: ``None``.
        """
        self._route_edit_active = bool(active)
        self.refresh_z_order()
        self.refresh_route_handles()

    def get_persisted_endpoint_attachment(self, endpoint: str) -> dict[str, object]:
        """
        Return persisted attachment data for one endpoint.

        :param endpoint: Endpoint key.
        :return: Attachment dictionary.
        """
        if self.api_object is None:
            if self.is_vsc3_terminal_connection():
                owner_graphic = self.get_vsc3_connection_owner()

                if owner_graphic is None:
                    return dict()
                else:
                    return owner_graphic.get_connection_attachment(conn_line=self, endpoint=endpoint)
            else:
                return dict()
        else:
            return self.editor.get_persisted_attachment(api_object=self.api_object, endpoint=endpoint)

    def get_endpoint_owner_graphic(self, endpoint: str) -> NODE_GRAPHIC | None:
        """
        Return the owner graphic of one endpoint.

        :param endpoint: Endpoint key.
        :return: Owner graphic or ``None``.
        """
        if endpoint == "from":
            return self.get_terminal_from_parent()
        elif endpoint == "to":
            return self.get_terminal_to_parent()
        else:
            return None

    def get_editable_segment_indexes(self, points: list[tuple[float, float]]) -> list[int]:
        """
        Return interior segment indexes that may be dragged by the user.

        :param points: Current route points.
        :return: Editable segment indexes.
        """
        editable_indexes: list[int] = list()
        segment_index: int

        if len(points) < 4:
            return editable_indexes
        else:
            pass

        for segment_index in range(1, len(points) - 2):
            p1 = points[segment_index]
            p2 = points[segment_index + 1]

            if p1 == p2:
                pass
            else:
                editable_indexes.append(segment_index)

        return editable_indexes

    def get_editable_vertex_indexes(self, points: list[tuple[float, float]]) -> list[int]:
        """
        Return the editable interior route-vertex indexes.

        :param points: Current route points.
        :return: Editable vertex indexes.
        """
        if len(points) < 3:
            return list()
        else:
            return list(range(1, len(points) - 1))

    def move_route_segment(self,
                           segment_index: int,
                           original_points: list[tuple[float, float]],
                           delta_x: float,
                           delta_y: float) -> None:
        """
        Move one interior route segment and persist the result as a manual polyline.

        :param segment_index: Editable segment index.
        :param original_points: Route points captured at drag start.
        :param delta_x: Horizontal scene delta.
        :param delta_y: Vertical scene delta.
        :return: ``None``.
        """
        if self.api_object is None:
            if self.is_vsc3_terminal_connection():
                owner_graphic = self.get_vsc3_connection_owner()

                if owner_graphic is None:
                    return
                else:
                    pass
            else:
                return
        else:
            pass

        moved_points = move_polyline_route_segment(points=original_points,
                                                   segment_index=segment_index,
                                                   delta_x=delta_x,
                                                   delta_y=delta_y)
        self._route_points = normalize_route_points(moved_points)
        if self.api_object is None:
            owner_graphic.set_connection_route_points(conn_line=self,
                                                      points=self._route_points,
                                                      kind=SchematicRouteKind.MANUAL_POLYLINE,
                                                      locked=False)
        else:
            self.editor.diagram.set_branch_route_points(api_object=self.api_object,
                                                        points=self._route_points,
                                                        kind=SchematicRouteKind.MANUAL_POLYLINE,
                                                        locked=False)
        self.redraw()

    def move_route_vertex(self, vertex_index: int, scene_pos: QPointF) -> None:
        """
        Move one interior route vertex and persist the manual polyline.

        :param vertex_index: Vertex index.
        :param scene_pos: New scene position.
        :return: ``None``.
        """
        if self.api_object is None:
            if self.is_vsc3_terminal_connection():
                owner_graphic = self.get_vsc3_connection_owner()

                if owner_graphic is None:
                    return
                else:
                    pass
            else:
                return
        else:
            pass

        current_points = self.get_route_points_for_editing()
        moved_points = move_polyline_route_vertex(points=current_points,
                                                  vertex_index=vertex_index,
                                                  new_x=scene_pos.x(),
                                                  new_y=scene_pos.y())
        self._route_points = normalize_route_points(moved_points)
        if self.api_object is None:
            owner_graphic.set_connection_route_points(conn_line=self,
                                                      points=self._route_points,
                                                      kind=SchematicRouteKind.MANUAL_POLYLINE,
                                                      locked=False)
        else:
            self.editor.diagram.set_branch_route_points(api_object=self.api_object,
                                                        points=self._route_points,
                                                        kind=SchematicRouteKind.MANUAL_POLYLINE,
                                                        locked=False)
        self.redraw()

    def move_endpoint_alignment(self, endpoint: str, scene_pos: QPointF) -> None:
        """
        Move one endpoint anchor along the hosting node side and persist the alignment.

        :param endpoint: Endpoint key.
        :param scene_pos: Scene point chosen by the user.
        :return: ``None``.
        """
        owner_graphic = self.get_endpoint_owner_graphic(endpoint=endpoint)

        if owner_graphic is None:
            return
        elif not self.can_edit_endpoint_alignment(endpoint=endpoint):
            return
        else:
            pass

        attachment = self.get_persisted_endpoint_attachment(endpoint=endpoint)
        local_anchor: QPointF = self.get_owner_local_anchor_from_scene_point(owner_graphic=owner_graphic,
                                                                             scene_pos=scene_pos)
        attachment["anchor_x"] = float(local_anchor.x())
        attachment["anchor_y"] = float(local_anchor.y())
        attachment["anchor_auto"] = False
        if self.api_object is None:
            if self.is_vsc3_terminal_connection():
                vsc_owner = self.get_vsc3_connection_owner()

                if vsc_owner is None:
                    return
                else:
                    vsc_owner.set_connection_attachment(conn_line=self,
                                                        endpoint=endpoint,
                                                        attachment=attachment)
            else:
                return
        else:
            self.editor.diagram.set_attachment(api_object=self.api_object,
                                               endpoint=endpoint,
                                               attachment=attachment)
        self.redraw()

    def get_owner_local_anchor_from_scene_point(self,
                                                owner_graphic: NODE_GRAPHIC,
                                                scene_pos: QPointF) -> QPointF:
        """
        Project one scene point to the owner-local attachment manifold.

        :param owner_graphic: Endpoint owner graphic.
        :param scene_pos: Requested scene point.
        :return: Projected owner-local attachment point.
        """
        if isinstance(owner_graphic, BusGraphicItem):
            return owner_graphic.get_connection_local_point_from_scene_point(scene_pos)
        elif isinstance(owner_graphic, FluidNodeGraphicItem):
            return owner_graphic.get_connection_local_point_from_scene_point(scene_pos)
        else:
            return QPointF(0.0, 0.0)

    def get_owner_scene_anchor_from_attachment(self,
                                               owner_graphic: NODE_GRAPHIC,
                                               attachment: dict[str, object],
                                               fallback_point: QPointF) -> QPointF:
        """
        Resolve one endpoint anchor from coordinate metadata.

        :param owner_graphic: Endpoint owner graphic.
        :param attachment: Persisted attachment metadata.
        :param fallback_point: Fallback scene point.
        :return: Scene attachment point.
        """
        anchor_x = attachment.get("anchor_x", None)
        anchor_y = attachment.get("anchor_y", None)

        if anchor_x is None or anchor_y is None:
            if isinstance(owner_graphic, BusGraphicItem):
                return owner_graphic.get_connection_scene_point_from_local_point(owner_graphic.get_default_connection_local_point())
            elif isinstance(owner_graphic, FluidNodeGraphicItem):
                return owner_graphic.get_connection_scene_point_from_local_point(owner_graphic.get_default_connection_local_point())
            else:
                return fallback_point
        elif isinstance(owner_graphic, BusGraphicItem):
            return owner_graphic.get_connection_scene_point_from_local_point(QPointF(float(anchor_x), float(anchor_y)))
        elif isinstance(owner_graphic, FluidNodeGraphicItem):
            return owner_graphic.get_connection_scene_point_from_local_point(QPointF(float(anchor_x), float(anchor_y)))
        else:
            return fallback_point

    def resolve_endpoint_alignment_side_key(self,
                                            endpoint: str,
                                            attachment: dict[str, object]) -> SchematicAttachmentSlot:
        """
        Resolve the canonical node side used when dragging one endpoint alignment handle.

        This path must not trust stale legacy ``side`` values blindly. Existing diagrams can
        contain migrated attachments where the saved ``terminal_key`` already points to the
        correct bar side but ``side`` still reflects an older heuristic. Endpoint dragging
        should follow the side that the user is actually editing on screen.

        :param endpoint: Endpoint key.
        :param attachment: Persisted attachment metadata.
        :return: Canonical side key.
        """
        terminal_key_value: object | None = attachment.get("terminal_key", None)
        canonical_terminal_keys: tuple[SchematicAttachmentSlot, ...] = (
            SchematicAttachmentSlot.TOP,
            SchematicAttachmentSlot.BOTTOM,
            SchematicAttachmentSlot.LEFT,
            SchematicAttachmentSlot.RIGHT,
            SchematicAttachmentSlot.DEFAULT,
        )

        if terminal_key_value is None:
            pass
        else:
            terminal_key: str = str(terminal_key_value)
            explicit_slot = parse_explicit_slot_key(slot_key=terminal_key)

            if explicit_slot is not None:
                return explicit_slot[1]
            elif parse_attachment_slot(slot_key=terminal_key) in canonical_terminal_keys:
                return parse_attachment_slot(slot_key=terminal_key)
            else:
                pass

        route_points: list[tuple[float, float]] = self.get_route_points_for_editing()
        inferred_side_key: SchematicAttachmentSlot = infer_attachment_slot_from_route(points=route_points,
                                                                                     endpoint=endpoint)

        if inferred_side_key != SchematicAttachmentSlot.DEFAULT:
            return inferred_side_key
        else:
            pass

        side_value: object | None = attachment.get("side", None)

        if side_value is None:
            return SchematicAttachmentSlot.BOTTOM
        else:
            return parse_attachment_slot(slot_key=str(side_value))

    def refresh_route_handles(self) -> None:
        """
        Sync draggable route handles with the current rendered route.

        :return: ``None``.
        """
        points = self.get_route_points_for_editing()
        editable_indexes = self.get_editable_segment_indexes(points=points)
        editable_vertex_indexes = self.get_editable_vertex_indexes(points=points)
        handle_index: int

        can_edit_polyline: bool = self.can_edit_route_geometry()

        while len(self._route_handles) < len(editable_indexes):
            self._route_handles.append(RouteSegmentHandleItem(parent_branch=self, segment_index=0))

        while len(self._route_handles) > len(editable_indexes):
            handle = self._route_handles.pop()
            if handle.scene() is not None:
                handle.scene().removeItem(handle)
            else:
                pass

        for handle_index, segment_index in enumerate(editable_indexes):
            handle = self._route_handles[handle_index]
            segment_start = points[segment_index]
            segment_end = points[segment_index + 1]
            handle_mid_x = (segment_start[0] + segment_end[0]) * 0.5
            handle_mid_y = (segment_start[1] + segment_end[1]) * 0.5
            handle.set_segment_index(segment_index=segment_index)
            handle.setPos(handle_mid_x, handle_mid_y)
            handle.setVisible(self.is_route_edit_active() and can_edit_polyline)

        while len(self._vertex_handles) < len(editable_vertex_indexes):
            self._vertex_handles.append(RouteVertexHandleItem(parent_branch=self, vertex_index=0))

        while len(self._vertex_handles) > len(editable_vertex_indexes):
            handle = self._vertex_handles.pop()
            if handle.scene() is not None:
                handle.scene().removeItem(handle)
            else:
                pass

        for handle_index, vertex_index in enumerate(editable_vertex_indexes):
            handle = self._vertex_handles[handle_index]
            vertex_point = points[vertex_index]
            handle.set_vertex_index(vertex_index=vertex_index)
            handle.setPos(vertex_point[0], vertex_point[1])
            handle.setVisible(self.is_route_edit_active() and can_edit_polyline)

        for endpoint_key, handle in self._endpoint_handles.items():
            anchor_point = self.get_endpoint_anchor(endpoint=endpoint_key)
            handle.setPos(anchor_point)
            handle.setVisible(self.is_route_edit_active() and self.can_edit_endpoint_alignment(endpoint=endpoint_key))

    def itemChange(self, change, value):
        """
        Keep route handles aligned with selection state changes.

        :param change: Graphics item change.
        :param value: New value.
        :return: Base implementation result.
        """
        result = QGraphicsLineItem.itemChange(self, change, value)

        if change == self.GraphicsItemChange.ItemSelectedHasChanged:
            if bool(value):
                pass
            else:
                self._route_edit_active = False
            self.refresh_z_order()
            self.refresh_route_handles()
        else:
            pass

        return result

    def get_endpoint_anchor(self, endpoint: str) -> QPointF:
        """
        Resolve the live scene anchor point for one branch endpoint.
        """
        if endpoint == "from":
            owner_graphic: NODE_GRAPHIC | None = self.get_terminal_from_parent()
            fallback_point: QPointF = self.pos1
        else:
            owner_graphic = self.get_terminal_to_parent()
            fallback_point = self.pos2

        if owner_graphic is None:
            return fallback_point
        elif self.api_object is None:
            if self.is_vsc3_terminal_connection() and self.can_edit_endpoint_alignment(endpoint=endpoint):
                attachment = self.get_persisted_endpoint_attachment(endpoint=endpoint)
                return self.get_owner_scene_anchor_from_attachment(owner_graphic=owner_graphic,
                                                                   attachment=attachment,
                                                                   fallback_point=fallback_point)
            else:
                return fallback_point
        else:
            pass

        attachment = self.get_persisted_endpoint_attachment(endpoint=endpoint)
        coordinate_anchor: QPointF = self.get_owner_scene_anchor_from_attachment(owner_graphic=owner_graphic,
                                                                                 attachment=attachment,
                                                                                 fallback_point=fallback_point)
        return coordinate_anchor

    def sync_route_points_to_diagram(self) -> None:
        """
        Persist the currently rendered route without changing route kind or lock metadata.
        """
        if self.api_object is None:
            if self.is_vsc3_terminal_connection():
                return
            else:
                pass
        else:
            pass

        if self.api_object is None:
            return
        elif self.editor.is_loading_diagram():
            return
        elif self.editor.diagram.should_preserve_branch_route_shape(self.api_object):
            return
        else:
            pass

        location = self.editor.diagram.query_point(self.api_object)
        if location is None:
            return
        else:
            pass

        render_points = self.get_render_points()
        if len(render_points) < 2:
            return
        else:
            pass

        self._route_points = normalize_route_points(render_points)
        self.editor.diagram.sync_branch_route_points(api_object=self.api_object, points=self._route_points)
        self.sync_attachment_slots_to_diagram(render_points=self._route_points)

    def sync_attachment_slots_to_diagram(self, render_points: list[tuple[float, float]]) -> None:
        """
        Synchronize route endpoint coordinates back to the persisted attachment metadata.
        """
        endpoints: tuple[str, str] = ("from", "to")
        endpoint_key: str

        for endpoint_key in endpoints:
            attachment = self.editor.get_persisted_attachment(api_object=self.api_object, endpoint=endpoint_key)
            if endpoint_key == "from":
                owner_graphic: NODE_GRAPHIC | None = self.get_terminal_from_parent()
                scene_point = QPointF(render_points[0][0], render_points[0][1])
            else:
                owner_graphic = self.get_terminal_to_parent()
                scene_point = QPointF(render_points[-1][0], render_points[-1][1])

            if owner_graphic is None:
                owner_device = None
            else:
                local_anchor = self.get_owner_local_anchor_from_scene_point(owner_graphic=owner_graphic,
                                                                            scene_pos=scene_point)
                attachment["anchor_x"] = float(local_anchor.x())
                attachment["anchor_y"] = float(local_anchor.y())
                if "anchor_auto" not in attachment:
                    attachment["anchor_auto"] = True
                else:
                    pass
                owner_device = owner_graphic.api_object

            self.editor.diagram.set_attachment(api_object=self.api_object,
                                               endpoint=endpoint_key,
                                               attachment=attachment)
            self.editor.diagram.sync_attachment(api_object=self.api_object,
                                                endpoint=endpoint_key,
                                                owner_device=owner_device)

    def get_route_sample(self, position: float) -> tuple[QPointF, tuple[tuple[float, float], tuple[float, float]]]:
        """
        Sample the rendered route at a normalized path position.
        """
        point, segment = sample_route_segment(self.get_render_points(), position)
        return QPointF(point[0], point[1]), segment

    def get_symbol_transform(self, rect: QRectF) -> QTransform:
        """
        Build the transform for a branch symbol using the route midpoint orientation.
        """
        base_pt, segment = self.get_route_sample(0.5)
        h = segment[1][1] - segment[0][1]
        b = segment[1][0] - segment[0][0]
        ang = np.arctan2(h, b)
        h2 = rect.height() / 2.0
        w2 = rect.width() / 2.0
        a = h2 * np.cos(ang) - w2 * np.sin(ang)
        b = w2 * np.sin(ang) + h2 * np.cos(ang)

        center = base_pt - QPointF(a, b)

        transform = QTransform()
        transform.translate(center.x(), center.y())
        transform.rotate(np.rad2deg(ang))
        return transform

    def set_colour(self, color: QColor, w, style: Qt.PenStyle):
        """
        Set color and style
        :param color: QColor instance
        :param w: width
        :param style: PenStyle instance
        :return:
        """

        pen = QPen(color, w, style, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)

        self._route_item.setPen(pen)
        self.setPen(QPen(TRANSPARENT,
                         max(1, int(round(float(w)))),
                         style,
                         Qt.PenCapStyle.RoundCap,
                         Qt.PenJoinStyle.RoundJoin))
        self.arrow_p_from.set_colour(color)
        self.arrow_q_from.set_colour(color)
        self.arrow_p_to.set_colour(color)
        self.arrow_q_to.set_colour(color)

        if self.symbol is not None:
            self.symbol.set_colour(color, w, style)

    def setToolTipText(self, toolTip: str):
        """
        Set branch tool tip text
        Args:
            toolTip: text
        """
        self.setToolTip(toolTip)

        if self.symbol is not None:
            self.symbol.setToolTipText(toolTip=toolTip)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """
        mouse press: display the editor
        :param event:
        :return:
        """
        if self.api_object is not None:
            self.editor.set_editor_model(api_object=self.api_object)
        else:
            pass

        if event.button() == Qt.MouseButton.LeftButton:
            self.set_route_edit_active(True)
        else:
            pass

        QGraphicsLineItem.mousePressEvent(self, event)

    def can_edit_route_geometry(self) -> bool:
        """
        Determine whether this line supports manual polyline editing.

        Normal branches always support this. VSC three-terminal connector lines
        also support polyline editing even though they do not map to a branch
        API object.

        :return: ``True`` when blue/yellow route handles may be shown.
        """
        if self.api_object is not None:
            return True
        elif self.is_vsc3_terminal_connection():
            return True
        else:
            return False

    def can_edit_endpoint_alignment(self, endpoint: str) -> bool:
        """
        Determine whether one endpoint supports green-handle alignment editing.

        Only endpoints hosted by buses or fluid nodes expose a movable electrical
        connection locus. Device-local round terminals such as the VSC symbol
        terminals stay fixed at their own center points.

        :param endpoint: Endpoint key.
        :return: ``True`` when the endpoint may expose a green handle.
        """
        owner_graphic = self.get_endpoint_owner_graphic(endpoint=endpoint)

        if isinstance(owner_graphic, BusGraphicItem):
            return True
        elif isinstance(owner_graphic, FluidNodeGraphicItem):
            return True
        else:
            return False

    def get_vsc3_connection_owner(self) -> "VscGraphicItem3Term | None":
        """
        Return the owning three-terminal VSC graphic when this line is one of its connectors.

        :return: VSC graphic or ``None``.
        """
        if self.is_from_port_a_vsc3():
            return self.get_terminal_from_parent()
        elif self.is_to_port_a_vsc3():
            return self.get_terminal_to_parent()
        else:
            return None

    def is_vsc3_terminal_connection(self) -> bool:
        """
        Return whether this line is one of the three-terminal VSC connector links.

        :return: ``True`` for VSC terminal connector lines.
        """
        if self.api_object is not None:
            return False
        elif self.is_from_port_a_vsc3():
            return True
        elif self.is_to_port_a_vsc3():
            return True
        else:
            return False

    def contextMenuEvent(self, event) -> None:
        """
        Show a lightweight route-style menu for VSC terminal connector lines.

        :param event: Context-menu event.
        :return: ``None``.
        """
        if self.is_vsc3_terminal_connection():
            menu = QMenu()
            self.add_auto_route_style_menu(menu=menu)
            menu.exec_(event.screenPos())
        else:
            super().contextMenuEvent(event)

    def paint(self,
              painter: QPainter,
              option: QStyleOptionGraphicsItem,
              widget: QWidget | None = None) -> None:
        """
        Keep the controller item visually inert.

        The visible branch stroke is rendered by ``self._route_item``. If the
        ``QGraphicsLineItem`` base class also paints its straight controller
        line, scene invalidation can leave faint shadows while selection and
        redraw update the routed child path. The parent item therefore only
        exists for selection, hit testing, and child ownership.

        :param painter: Unused painter.
        :param option: Unused style option.
        :param widget: Unused target widget.
        :return: ``None``.
        """
        return None

    def remove_widget(self):
        """
        Remove this object in the diagram
        @return:
        """
        self.editor._remove_from_scene(self)

    def delete(self, ask=True):
        """
        Remove this object in the diagram and the API
        @return:
        """
        deleted, delete_from_db_final = self.editor.delete_with_dialogue(selected=[self], delete_from_db=False)

    def enable_disable_toggle(self):
        """

        @return:
        """
        if self.api_object is not None:
            if self.api_object.active:
                self.set_enable(False)
            else:
                self.set_enable(True)

            if self._editor.circuit.get_time_number() > 0:
                ok = yes_no_question('Do you want to update the time series active status accordingly?',
                                     'Update time series active status')

                if ok:
                    # change the bus state (time series)
                    self._editor.set_active_status_to_profile(self.api_object, override_question=True)

    def set_enable(self, val=True):
        """
        Set the enable value, graphically and in the API
        @param val:
        @return:
        """
        self.api_object.active = val
        if self.api_object is not None:
            if self.api_object.active:
                self.style = ACTIVE['style']
                self.color = ACTIVE['color']
            else:
                self.style = DEACTIVATED['style']
                self.color = DEACTIVATED['color']
        else:
            self.style = OTHER['style']
            self.color = OTHER['color']

        if self.symbol:
            if self.api_object.active:
                if isinstance(self.symbol, SwitchSymbol):
                    self.symbol.setBrush(QColor(self.color))
                else:
                    self.symbol.setBrush(self.color)
                self.symbol.setPen(QPen(ACTIVE['color']))
            else:
                if isinstance(self.symbol, SwitchSymbol):
                    self.symbol.setBrush(QColor(0, 0, 0, 0))
                else:
                    inactive_fill = QColor(DEACTIVATED['color'])
                    inactive_fill.setAlpha(72)
                    self.symbol.setBrush(inactive_fill)
                self.symbol.setPen(QPen(DEACTIVATED['color']))

        # Set pen for everyone
        self.set_pen(QPen(self.color, self.width, self.style))

        self.arrow_p_from.setVisible(val)
        self.arrow_q_from.setVisible(val)
        self.arrow_p_to.setVisible(val)
        self.arrow_q_to.setVisible(val)

    def plot_profiles(self):
        """
        Plot the time series profiles
        @return:
        """
        # get the index of this object
        i = self._editor.circuit.get_branches().index(self.api_object)
        self._editor.plot_branch(i, self.api_object)

    def set_from_port(self, from_port: BarTerminalItem | RoundTerminalItem) -> None:
        """
        Set the From terminal in a connection
        @param from_port: TerminalItem
        """

        if self._from_port:
            # there was a port before, unregister it
            self._from_port.delete_hosting_connection(graphic_obj=self)

        # register the new port
        self._from_port = from_port
        self._from_port.add_hosting_connection(graphic_obj=self, callback=self.setBeginPos)
        self._from_port.update()
        self._from_port.get_parent().setZValue(0)

    def set_to_port(self, to_port: BarTerminalItem | RoundTerminalItem) -> None:
        """
        Set the To terminal in a connection
        @param to_port: TerminalItem
        """
        if self._to_port:
            # there was a port before, unregister it
            self._to_port.delete_hosting_connection(graphic_obj=self)

        # register the new port
        self._to_port = to_port
        self._to_port.add_hosting_connection(graphic_obj=self, callback=self.setEndPos)
        self._to_port.update()
        self._to_port.get_parent().setZValue(0)

    def unregister_port_from(self) -> None:
        """

        :return:
        """
        if self._from_port:
            self._from_port.delete_hosting_connection(graphic_obj=self)

    def unregister_port_to(self) -> None:
        """

        :return:
        """
        if self._to_port:
            self._to_port.delete_hosting_connection(graphic_obj=self)

    def setEndPos(self, endpos: QPointF):
        """
        Set the starting position
        @param endpos:
        @return:
        """
        self.pos2 = endpos
        if self.editor.is_loading_diagram():
            pass
        elif self.editor.is_batch_refreshing_branches():
            pass
        else:
            self.redraw()

    def setBeginPos(self, pos1: QPointF):
        """
        Set the starting position
        @param pos1:
        @return:
        """
        self.pos1 = pos1
        if self.editor.is_loading_diagram():
            pass
        elif self.editor.is_batch_refreshing_branches():
            pass
        else:
            self.redraw()

    def _build_render_path(self) -> QPainterPath:
        """
        Build the visible route path for the current branch.
        """
        points = self.get_render_points()
        path = QPainterPath()

        if not points:
            return path

        path.moveTo(points[0][0], points[0][1])

        for x, y in points[1:]:
            path.lineTo(x, y)

        return path

    def shape(self) -> QPainterPath:
        """
        Use the rendered route path for hit testing so routed branches remain selectable.
        """
        path = QPainterPath()

        if self._rendered_path.isEmpty():
            path = super().shape()
        else:
            stroker = QPainterPathStroker()
            stroker.setWidth(max(8.0, float(self.pen_width) + 4.0))
            stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
            stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            path = stroker.createStroke(self._rendered_path)

        if self.symbol is None:
            return path
        else:
            symbol_bounds = self.symbol.mapRectToParent(self.symbol.boundingRect()).adjusted(-6.0, -6.0, 6.0, 6.0)
            symbol_path = QPainterPath()
            symbol_path.addRoundedRect(symbol_bounds, 8.0, 8.0)
            return path.united(symbol_path)

    def boundingRect(self) -> QRectF:
        """
        Keep the item bounds aligned with the rendered route path.
        """
        if self._rendered_path.isEmpty():
            return super().boundingRect()

        return self.shape().boundingRect()

    def redraw(self) -> None:
        """
        Redraw the line with the given positions
        @return:
        """
        if self.pos1 is not None and self.pos2 is not None:

            # The controller item uses a path-based bounding rect. Notify the
            # scene before replacing the rendered route so old pixels are
            # invalidated correctly during selection and redraw updates.
            self.prepareGeometryChange()

            # Set position
            self.setLine(QLineF(self.pos1, self.pos2))
            self.sync_route_points_to_diagram()
            self._rendered_path = self._build_render_path()
            self._route_item.setPath(self._rendered_path)

            # keep editable branches above nodes only while selected
            self.refresh_z_order()

            if self.api_object is not None:

                # arrows
                if self.view_arrows:
                    self.arrow_p_from.redraw()
                    self.arrow_q_from.redraw()
                    self.arrow_p_to.redraw()
                    self.arrow_q_to.redraw()

                if self.symbol is not None:
                    self.symbol.redraw()

            self.refresh_route_handles()

    def set_pen(self, pen, scale: float = 1.0):
        """
        Set pen to all objects
        :param pen:
        :param scale:
        :return:
        """

        route_pen = QPen(pen)
        self.pen_style = route_pen.style()
        self.pen_color = route_pen.color()
        self.pen_width = route_pen.width()
        self.scale = scale

        api_object_is_active: bool = True

        if self.api_object is None:
            pass
        elif isinstance(self.api_object, FluidPath):
            api_object_is_active = True
        else:
            api_object_is_active = bool(self.api_object.active)

        if not api_object_is_active:
            inactive_color = QColor(route_pen.color())
            inactive_color.setAlpha(185)
            route_pen.setColor(inactive_color)
            route_pen.setDashPattern([4.0, 3.0])
            self._route_item.setOpacity(0.82)
            if self.symbol is None:
                pass
            else:
                self.symbol.setOpacity(0.88)
        else:
            self._route_item.setOpacity(1.0)
            if self.symbol is None:
                pass
            else:
                self.symbol.setOpacity(1.0)

        route_pen.setWidth(self.pen_width / scale)

        self._route_item.setPen(route_pen)
        self.setPen(QPen(TRANSPARENT,
                         max(1, int(round(self.pen_width / scale))),
                         route_pen.style(),
                         Qt.PenCapStyle.RoundCap,
                         Qt.PenJoinStyle.RoundJoin))

        if self.symbol:
            self.symbol.set_pen(route_pen)
            if isinstance(self.symbol, SwitchSymbol):
                if self.api_object is not None and self.api_object.active:
                    self.symbol.setBrush(QColor(route_pen.color()))
                else:
                    self.symbol.setBrush(QColor(0, 0, 0, 0))

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

    def set_arrows_with_power(self, Sf: complex | None, St: complex | None) -> None:
        """
        Set the arrow directions
        :param Sf: Complex power from
        :param St: Complex power to
        """

        if Sf is not None:
            if St is None:
                St = -Sf

            Pf = Sf.real
            Qf = Sf.imag
            Pt = St.real
            Qt_ = St.imag
            self.arrow_p_from.set_value(Pf, True, Pf < 0, name="Pf", units="MW", draw_label=self.draw_labels)
            self.arrow_q_from.set_value(Qf, True, Qf < 0, name="Qf", units="MVAr", draw_label=self.draw_labels)
            self.arrow_p_to.set_value(Pt, True, Pt > 0, name="Pt", units="MW", draw_label=self.draw_labels)
            self.arrow_q_to.set_value(Qt_, True, Qt_ > 0, name="Qt", units="MVAr", draw_label=self.draw_labels)
        else:
            if St is None:
                self.arrow_p_from.setVisible(False)
                self.arrow_q_from.setVisible(False)
                self.arrow_p_to.setVisible(False)
                self.arrow_q_to.setVisible(False)

    def set_arrows_with_hvdc_power(self, Pf: float, Pt: float) -> None:
        """
        Set the arrow directions
        :param Pf: Complex power from
        :param Pt: Complex power to
        """
        self.arrow_p_from.set_value(Pf, True, Pf < 0, name="Pf", units="MW", draw_label=self.draw_labels)
        self.arrow_q_from.set_value(Pf, True, Pf < 0, name="Pf", units="MW", draw_label=self.draw_labels)
        self.arrow_p_to.set_value(Pt, True, Pt > 0, name="Pt", units="MW", draw_label=self.draw_labels)
        self.arrow_q_to.set_value(Pt, True, Pt > 0, name="Pt", units="MW", draw_label=self.draw_labels)

    def set_arrows_with_fluid_flow(self, flow: float) -> None:
        """
        Set the arrow directions
        :param flow: branch_flow (m3/s)
        """
        self.arrow_p_from.set_value(flow, True, flow < 0, name="flow", units="m3/s", draw_label=self.draw_labels)
        self.arrow_q_from.set_value(flow, True, flow < 0, name="flow", units="m3/s", draw_label=False)
        self.arrow_p_to.setVisible(False)
        self.arrow_q_to.setVisible(False)

    def change_bus(self):
        """
        change the from or to bus of the nbranch with another selected bus
        """
        self._editor.change_bus(line_graphics=self)

    def get_from_graphic_object(self):
        """

        :return:
        """
        if self._from_port:
            return self.get_terminal_from_parent()
        else:
            return None

    def get_to_graphic_object(self):
        """

        :return:
        """
        if self._to_port:
            return self.get_terminal_to_parent()
        else:
            return None

    def is_from_port_a_bus(self) -> bool:
        """

        :return:
        """
        if self._from_port:
            return isinstance(self.get_terminal_from_parent(), BusGraphicItem)
        else:
            return False

    def is_to_port_a_bus(self) -> bool:
        """

        :return:
        """
        if self._to_port:
            return isinstance(self.get_terminal_to_parent(), BusGraphicItem)
        else:
            return False

    def is_from_port_a_tr3(self) -> bool:
        """

        :return:
        """
        if self._from_port:
            if 'Transformer3WGraphicItem' not in sys.modules:
                # keep this here, we need an actual instance
                from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.transformer3w_graphics import \
                    Transformer3WGraphicItem
            if 'TransformerNWGraphicItem' not in sys.modules:
                from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.transformerNw_graphics import \
                    TransformerNWGraphicItem
            return isinstance(self.get_terminal_from_parent(), (Transformer3WGraphicItem, TransformerNWGraphicItem))
        else:
            return False

    def is_to_port_a_tr3(self) -> bool:
        """

        :return:
        """
        if self._to_port:
            if 'Transformer3WGraphicItem' not in sys.modules:
                # keep this here, we need an actual instance
                from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.transformer3w_graphics import \
                    Transformer3WGraphicItem
            if 'TransformerNWGraphicItem' not in sys.modules:
                from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.transformerNw_graphics import \
                    TransformerNWGraphicItem
            return isinstance(self.get_terminal_to_parent(), (Transformer3WGraphicItem, TransformerNWGraphicItem))
        else:
            return False

    def is_from_port_a_fluid_node(self) -> bool:
        """

        :return:
        """
        if self._from_port:
            return isinstance(self.get_terminal_from_parent(), FluidNodeGraphicItem)
        else:
            return False

    def is_to_port_a_fluid_node(self) -> bool:
        """

        :return:
        """
        if self._to_port:
            return isinstance(self.get_terminal_to_parent(), FluidNodeGraphicItem)
        else:
            return False

    def is_from_port_a_vsc3(self) -> bool:
        """

        :return:
        """
        if self._from_port:
            if 'VscGraphicItem3Term' not in sys.modules:
                # keep this here, we need an actual instance
                from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.vsc_graphics_3term import VscGraphicItem3Term
            return isinstance(self.get_terminal_from_parent(), VscGraphicItem3Term)
        else:
            return False

    def is_to_port_a_vsc3(self) -> bool:
        """

        :return:
        """
        if self._to_port:
            if 'VscGraphicItem3Term' not in sys.modules:
                # keep this here, we need an actual instance
                from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.vsc_graphics_3term import VscGraphicItem3Term
            return isinstance(self.get_terminal_to_parent(), VscGraphicItem3Term)
        else:
            return False

    def get_bus_from(self) -> Bus:
        """

        :return:
        """
        return self.get_from_graphic_object().api_object

    def get_bus_to(self) -> Bus:
        """

        :return:
        """
        return self.get_to_graphic_object().api_object

    def get_cn_from(self) -> Bus:
        """

        :return:
        """
        return self.get_from_graphic_object().api_object

    def get_cn_to(self) -> Bus:
        """

        :return:
        """
        return self.get_to_graphic_object().api_object

    def get_busbar_from(self) -> BusBar:
        """

        :return:
        """
        return self.get_from_graphic_object()._api_object

    def get_busbar_to(self) -> BusBar:
        """

        :return:
        """
        return self.get_to_graphic_object()._api_object

    def get_fluid_node_from(self) -> FluidNode:
        """

        :return:
        """
        return self.get_from_graphic_object()._api_object

    def get_fluid_node_to(self) -> FluidNode:
        """

        :return:
        """
        return self.get_to_graphic_object()._api_object

    def get_fluid_node_graphics_from(self) -> FluidNodeGraphicItem:
        """

        :return:
        """
        return self.get_from_graphic_object()

    def get_fluid_node_graphics_to(self) -> FluidNodeGraphicItem:
        """

        :return:
        """
        return self.get_to_graphic_object()

    def connected_between_buses(self):
        """

        :return:
        """
        return self.is_from_port_a_bus() and self.is_to_port_a_bus()

    def connected_between_bus_and_tr3(self):
        """

        :return:
        """
        return self.is_from_port_a_bus() and self.is_to_port_a_tr3()

    def conneted_between_tr3_and_bus(self):
        """

        :return:
        """
        return self.is_from_port_a_tr3() and self.is_to_port_a_bus()

    def connected_between_fluid_nodes(self):
        """

        :return:
        """
        return self.is_from_port_a_fluid_node() and self.is_to_port_a_fluid_node()

    def connected_between_fluid_node_and_bus(self):
        """

        :return:
        """
        return self.is_from_port_a_fluid_node() and self.is_to_port_a_bus()

    def connected_between_bus_and_fluid_node(self):
        """

        :return:
        """
        return self.is_from_port_a_bus() and self.is_to_port_a_fluid_node()

    def connected_between_bus_and_vsc3(self):
        """

        :return:
        """
        return self.is_from_port_a_bus() and self.is_to_port_a_vsc3()

    def connected_between_vsc3_and_bus(self):
        """

        :return:
        """
        return self.is_from_port_a_vsc3() and self.is_to_port_a_bus()

    def should_be_a_converter(self) -> bool:
        """

        :return:
        """
        return self.get_bus_from().is_dc != self.get_bus_to().is_dc

    def should_be_a_dc_line(self) -> bool:
        """

        :return:
        """
        return self.get_bus_from().is_dc and self.get_bus_to().is_dc

    def should_be_a_transformer(self, branch_connection_voltage_tolerance: float = 0.1) -> bool:
        """

        :param branch_connection_voltage_tolerance:
        :return:
        """
        bus_from = self.get_bus_from()
        bus_to = self.get_bus_to()

        V1 = min(bus_to.Vnom, bus_from.Vnom)
        V2 = max(bus_to.Vnom, bus_from.Vnom)
        if V2 > 0:
            per = V1 / V2
            return per < (1.0 - branch_connection_voltage_tolerance)
        else:
            return V1 != V2
