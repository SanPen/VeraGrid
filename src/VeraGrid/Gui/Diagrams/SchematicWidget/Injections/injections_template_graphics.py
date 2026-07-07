# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING, List, Any
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QCursor, QPainter, QPainterPath, QColor, QBrush, QPainterPathStroker
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsItemGroup, QMenu,
                               QGraphicsSceneContextMenuEvent, QGraphicsPathItem,
                               QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsSceneMouseEvent,
                               QGraphicsSceneHoverEvent, QGraphicsTextItem, QStyleOptionGraphicsItem, QWidget)
from VeraGrid.Gui.messages import yes_no_question, error_msg
from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGrid.Gui.gui_functions import add_menu_entry, translate_context_menu_text
from VeraGrid.Gui.Diagrams.generic_graphics import (GenericDiagramWidget, ACTIVE, DEACTIVATED, OTHER, Square, Circle,
                                                    Polygon, Condenser, InjectionSymbolBase, DraggableLabelItem)
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.route_geometry import (merge_route_with_endpoints,
                                                                           move_polyline_route_segment,
                                                                           move_polyline_route_vertex,
                                                                           normalize_route_points)
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.slot_geometry import (SchematicAttachmentSlot,
                                                                          )
from VeraGridEngine.Devices.Diagrams.schematic_layout import (build_default_branch_route,
                                                              parse_schematic_route_kind)
from VeraGridEngine.enumerations import SchematicRouteKind, DynamicSimulationMode


from VeraGridEngine.Devices.types import INJECTION_DEVICE_TYPES

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget
    from VeraGrid.Gui.Diagrams.SchematicWidget.Substation.bus_graphics import BusGraphicItem
    from VeraGrid.Gui.Diagrams.SchematicWidget.Fluid.fluid_node_graphics import FluidNodeGraphicItem

    NODE_GRAPHIC = BusGraphicItem | FluidNodeGraphicItem


def get_opposite_attachment_side(side: SchematicAttachmentSlot) -> SchematicAttachmentSlot:
    """
    Get the opposite attachment side for a nexus endpoint.

    :param side: Parent-side attachment key.
    :return: Opposite child-side attachment key.
    """
    if side == SchematicAttachmentSlot.TOP:
        return SchematicAttachmentSlot.BOTTOM
    elif side == SchematicAttachmentSlot.BOTTOM:
        return SchematicAttachmentSlot.TOP
    elif side == SchematicAttachmentSlot.LEFT:
        return SchematicAttachmentSlot.RIGHT
    else:
        return SchematicAttachmentSlot.LEFT


def clamp_alignment(alignment: float | None) -> float:
    """
    Clamp one normalized alignment value.

    :param alignment: Optional alignment.
    :return: Clamped alignment.
    """
    if alignment is None:
        return 0.5
    else:
        pass

    alignment_value: float = float(alignment)

    if alignment_value < 0.0:
        return 0.0
    elif alignment_value > 1.0:
        return 1.0
    else:
        return alignment_value


def get_rect_side_anchor(origin: QPointF,
                         width: float,
                         height: float,
                         side: SchematicAttachmentSlot,
                         alignment: float | None) -> QPointF:
    """
    Get one side anchor on a rectangle in scene coordinates.

    :param origin: Top-left scene point.
    :param width: Rectangle width.
    :param height: Rectangle height.
    :param side: Requested side.
    :param alignment: Normalized alignment on that side.
    :return: Scene anchor point.
    """
    alignment_value: float = clamp_alignment(alignment)

    if side == SchematicAttachmentSlot.TOP:
        return QPointF(origin.x() + width * alignment_value, origin.y())
    elif side == SchematicAttachmentSlot.BOTTOM:
        return QPointF(origin.x() + width * alignment_value, origin.y() + height)
    elif side == SchematicAttachmentSlot.LEFT:
        return QPointF(origin.x(), origin.y() + height * alignment_value)
    else:
        return QPointF(origin.x() + width, origin.y() + height * alignment_value)


def get_local_rect_side_anchor(width: float,
                               height: float,
                               side: SchematicAttachmentSlot,
                               alignment: float | None) -> QPointF:
    """
    Get one side anchor in item-local coordinates.

    :param width: Rectangle width.
    :param height: Rectangle height.
    :param side: Requested side.
    :param alignment: Normalized alignment on that side.
    :return: Local anchor point.
    """
    return get_rect_side_anchor(origin=QPointF(0.0, 0.0),
                                width=width,
                                height=height,
                                side=side,
                                alignment=alignment)


class InjectionNexusPathItem(QGraphicsPathItem):
    """
    Selectable nexus path that drives nexus-only editing for injections.
    """

    def __init__(self, owner_item: "InjectionTemplateGraphicItem"):
        """
        Initialize the selectable nexus path.

        :param owner_item: Owning injection item.
        """
        QGraphicsPathItem.__init__(self)

        self.owner_item: InjectionTemplateGraphicItem = owner_item
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def shape(self) -> QPainterPath:
        """
        Widen hit testing so the nexus can be selected easily.

        :return: Hit-test path.
        """
        stroker = QPainterPathStroker()
        stroker.setWidth(max(10.0, self.pen().widthF() + 6.0))
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        return stroker.createStroke(self.path())

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Select the nexus itself instead of the injection glyph.

        :param event: Mouse event.
        :return: ``None``.
        """
        self.owner_item.setSelected(False)
        self.owner_item.editor.set_editor_model(api_object=self.owner_item.api_object)

        if event.button() == Qt.MouseButton.LeftButton:
            self.owner_item.set_nexus_edit_active(True)
        else:
            pass

        QGraphicsPathItem.mousePressEvent(self, event)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """
        Refresh nexus edit handles when nexus selection changes.

        :param change: Graphics item change.
        :param value: New value.
        :return: Base implementation result.
        """
        result = QGraphicsPathItem.itemChange(self, change, value)

        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.owner_item.clear_nexus_edit_if_fully_deselected()
            self.owner_item.refresh_nexus_z_order()
            self.owner_item.refresh_nexus_handles()
        else:
            pass

        return result


class NexusSegmentHandleItem(QGraphicsEllipseItem):
    """
    Draggable handle for one interior nexus segment.
    """

    def __init__(self,
                 parent_item: "InjectionTemplateGraphicItem",
                 parent_graphic: QGraphicsItem,
                 segment_index: int,
                 radius: float = 6.0):
        """
        Initialize one nexus segment handle.

        :param parent_item: Owning injection item.
        :param segment_index: Editable segment index.
        :param radius: Handle radius.
        """
        QGraphicsEllipseItem.__init__(self, -radius, -radius, radius * 2.0, radius * 2.0, parent_graphic)

        self.parent_item: InjectionTemplateGraphicItem = parent_item
        self.segment_index: int = segment_index
        self._drag_origin_scene_pos: QPointF | None = None
        self._drag_origin_route_points: list[tuple[float, float]] = list()

        self.setBrush(QBrush(QColor(245, 195, 70, 255)))
        self.setPen(QPen(QColor(32, 32, 32, 255), 1.5))
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self.setZValue(40)
        self.setVisible(False)

    def set_segment_index(self, segment_index: int) -> None:
        """
        Set the controlled segment index.

        :param segment_index: Segment index.
        :return: ``None``.
        """
        self.segment_index = segment_index

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Capture route state for segment dragging.

        :param event: Mouse event.
        :return: ``None``.
        """
        self._drag_origin_scene_pos = event.scenePos()
        self._drag_origin_route_points = self.parent_item.get_nexus_route_points_for_editing()
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Drag one interior nexus segment.

        :param event: Mouse event.
        :return: ``None``.
        """
        if self._drag_origin_scene_pos is None:
            event.accept()
        else:
            delta = event.scenePos() - self._drag_origin_scene_pos
            self.parent_item.move_nexus_segment(segment_index=self.segment_index,
                                                original_points=self._drag_origin_route_points,
                                                delta_x=delta.x(),
                                                delta_y=delta.y())
            event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Finish the current segment drag.

        :param event: Mouse event.
        :return: ``None``.
        """
        self._drag_origin_scene_pos = None
        self._drag_origin_route_points = list()
        event.accept()


class NexusVertexHandleItem(QGraphicsRectItem):
    """
    Draggable handle for one interior nexus vertex.
    """

    def __init__(self,
                 parent_item: "InjectionTemplateGraphicItem",
                 parent_graphic: QGraphicsItem,
                 vertex_index: int,
                 half_size: float = 5.0):
        """
        Initialize one nexus vertex handle.

        :param parent_item: Owning injection item.
        :param vertex_index: Editable vertex index.
        :param half_size: Half handle size.
        """
        QGraphicsRectItem.__init__(self, -half_size, -half_size, half_size * 2.0, half_size * 2.0, parent_graphic)

        self.parent_item: InjectionTemplateGraphicItem = parent_item
        self.vertex_index: int = vertex_index

        self.setBrush(QBrush(QColor(85, 180, 255, 255)))
        self.setPen(QPen(QColor(20, 20, 20, 255), 1.5))
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self.setZValue(41)
        self.setVisible(False)

    def set_vertex_index(self, vertex_index: int) -> None:
        """
        Set the controlled vertex index.

        :param vertex_index: Vertex index.
        :return: ``None``.
        """
        self.vertex_index = vertex_index

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Accept the drag start.

        :param event: Mouse event.
        :return: ``None``.
        """
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Drag one nexus vertex.

        :param event: Mouse event.
        :return: ``None``.
        """
        self.parent_item.move_nexus_vertex(vertex_index=self.vertex_index, scene_pos=event.scenePos())
        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Accept the drag end.

        :param event: Mouse event.
        :return: ``None``.
        """
        event.accept()


class NexusEndpointHandleItem(QGraphicsEllipseItem):
    """
    Draggable handle for one nexus endpoint alignment.
    """

    def __init__(self,
                 parent_item: "InjectionTemplateGraphicItem",
                 parent_graphic: QGraphicsItem,
                 endpoint: str,
                 radius: float = 5.5):
        """
        Initialize one nexus endpoint handle.

        :param parent_item: Owning injection item.
        :param endpoint: ``"child"`` or ``"parent"``.
        :param radius: Handle radius.
        """
        QGraphicsEllipseItem.__init__(self, -radius, -radius, radius * 2.0, radius * 2.0, parent_graphic)

        self.parent_item: InjectionTemplateGraphicItem = parent_item
        self.endpoint: str = endpoint

        self.setBrush(QBrush(QColor(130, 255, 150, 255)))
        self.setPen(QPen(QColor(20, 20, 20, 255), 1.5))
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.setZValue(42)
        self.setVisible(False)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Accept the drag start.

        :param event: Mouse event.
        :return: ``None``.
        """
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Drag one nexus endpoint alignment.

        :param event: Mouse event.
        :return: ``None``.
        """
        self.parent_item.move_nexus_endpoint_alignment(endpoint=self.endpoint, scene_pos=event.scenePos())
        event.accept()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Accept the drag end.

        :param event: Mouse event.
        :return: ``None``.
        """
        event.accept()


class InjectionTemplateGraphicItem(GenericDiagramWidget, QGraphicsItemGroup):
    """
    InjectionTemplateGraphicItem
    """

    def __init__(self,
                 parent: NODE_GRAPHIC,
                 api_obj: INJECTION_DEVICE_TYPES,
                 device_type_name: str,
                 w: int,
                 h: int,
                 editor: SchematicWidget,
                 draw_labels: bool = True):
        """

        :param parent:
        :param api_obj:
        :param device_type_name:
        :param w:
        :param h:
        """
        GenericDiagramWidget.__init__(self,
                                      parent=parent,
                                      api_object=api_obj,
                                      editor=editor,
                                      draw_labels=draw_labels)
        QGraphicsItemGroup.__init__(self, parent)

        self.w = w
        self.h = h
        self.glyph: Square | Circle | Polygon | Condenser | InjectionSymbolBase | None = None
        self.scale = 1.0
        self.device_type_name = device_type_name

        # Properties of the container:
        self.setFlags(self.GraphicsItemFlag.ItemIsSelectable | self.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges, True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setAcceptHoverEvents(True)

        self.width = 4
        self._is_hovered: bool = False
        self._result_color: QColor | None = None
        self._result_lines: list[str] = list()
        self._default_tooltip: str = self.api_object.name if self.api_object is not None else ""

        # Routed nexus path tying this object with the original bus or node.
        self.nexus = InjectionNexusPathItem(owner_item=self)
        self.nexus.setPen(QPen(self.color,
                               self.width,
                               self.style,
                               Qt.PenCapStyle.FlatCap,
                               Qt.PenJoinStyle.MiterJoin))
        self.nexus.setBrush(Qt.BrushStyle.NoBrush)

        self._interaction_target = QGraphicsPathItem(parent=self)
        self._interaction_target.setPen(QPen(QColor(0, 0, 0, 0), 14.0, Qt.PenStyle.SolidLine,
                                             Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        self._interaction_target.setBrush(Qt.BrushStyle.NoBrush)
        self._interaction_target.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._interaction_target.setZValue(-3)

        self._interaction_ring = QGraphicsPathItem(parent=self)
        self._interaction_ring.setBrush(Qt.BrushStyle.NoBrush)
        self._interaction_ring.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._interaction_ring.setZValue(-2)

        self._result_badge = QGraphicsPathItem(parent=self)
        self._result_badge.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._result_badge.setVisible(False)
        self._result_badge.setZValue(2)

        self._result_label = DraggableLabelItem(parent=self, moved_callback=self.refresh_result_label_badge_geometry)
        self._result_label.document().setDocumentMargin(0.0)
        self._result_label.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self._result_label.setVisible(False)
        self._result_label.setZValue(3)

        self._nexus_route_points: list[tuple[float, float]] = list()
        self._nexus_segment_handles: list[NexusSegmentHandleItem] = list()
        self._nexus_vertex_handles: list[NexusVertexHandleItem] = list()
        self._nexus_endpoint_handles: dict[str, NexusEndpointHandleItem] = {
            "child": NexusEndpointHandleItem(parent_item=self, parent_graphic=self.nexus, endpoint="child"),
            "parent": NexusEndpointHandleItem(parent_item=self, parent_graphic=self.nexus, endpoint="parent"),
        }
        self._nexus_edit_active: bool = False
        self._nexus_edit_locks_applied: bool = False
        self._owner_movable_before_nexus_edit: bool = True
        self._parent_movable_before_nexus_edit: bool = True
        self.setTransformOriginPoint(self.get_rotation_origin_local_point())

    def set_glyph(self, glyph: QGraphicsItem) -> None:
        """

        :param glyph:
        :return:
        """
        self.glyph = glyph
        self.addToGroup(self.glyph)

        self.setPos(0.0, 100.0)
        self.clear_result_visuals()
        self.refresh_visual_style()
        self.refresh_result_label_layout()
        self.update_nexus(self.scenePos())

        self._editor.add_to_scene(self.nexus)

    def get_rotation_origin_local_point(self) -> QPointF:
        """
        Return the local rotation origin used for injection widgets.

        The injection symbol must rotate as a rigid body around its geometric
        center so the main widget does not orbit around one corner while the
        nexus route is refreshed.

        :return: Local rotation origin.
        """
        return QPointF(float(self.w) * 0.5, float(self.h) * 0.5)

    def apply_rotation_state(self, angle_degrees: float) -> None:
        """
        Apply one rotation angle around the widget center.

        :param angle_degrees: Rotation angle in degrees.
        :return: ``None``.
        """
        normalized_angle: float = float(angle_degrees) % 360.0

        # Keep the pivot synchronized with the current widget size before rotating.
        self.setTransformOriginPoint(self.get_rotation_origin_local_point())
        self.setRotation(normalized_angle)

    @property
    def parent(self) -> NODE_GRAPHIC:
        """

        :return:
        """
        return self._parent

    @property
    def api_object(self) -> INJECTION_DEVICE_TYPES:
        return self._api_object

    @property
    def editor(self) -> SchematicWidget:
        return self._editor

    def delete_from_associations(self):
        """
        Delete this object from the bus or other parent hosting it
        """
        self.parent.delete_child(self)

    def get_associated_widgets(self) -> List["GenericDiagramWidget" | "QGraphicsLineItem"]:
        """
        Get a list of all associated graphics
        :return:
        """
        return list()

    def get_extra_graphics(self):
        """
        Get a list of all QGraphicsItem that are not GenericDiagramWidget elements associated with this widget.
        :return:
        """
        return [self.nexus, self.glyph]

    def recolour_mode(self):
        """
        Change the colour according to the system theme
        """
        super().recolour_mode()
        self.refresh_visual_style()

    def enable_disable_toggle(self):
        """

        @return:
        """
        if self.api_object is not None:
            if self.api_object.active:
                self.set_enable(False)
            else:
                self.set_enable(True)

            if self.editor.circuit.has_time_series:
                ok = yes_no_question('Do you want to update the time series active status accordingly?',
                                     'Update time series active status')

                if ok:
                    # change the bus state (time series)
                    self.editor.set_active_status_to_profile(self.api_object, override_question=True)

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

        self.refresh_visual_style()

    def enable_label_drawing(self):
        """
        Enable visible result badges for this injection.
        """
        super().enable_label_drawing()
        self.refresh_result_label_layout()

    def disable_label_drawing(self):
        """
        Disable visible result badges for this injection.
        """
        super().disable_label_drawing()
        self.refresh_result_label_layout()

    def _get_glyph_bounds(self) -> QGraphicsRectItem | Any:
        """
        Return the current glyph bounds in owner-local coordinates.
        """
        if self.glyph is None:
            return self.childrenBoundingRect()
        else:
            return self.glyph.mapRectToParent(self.glyph.boundingRect())

    def _build_interaction_path(self) -> QPainterPath:
        """
        Build the padded local path used for hit-testing and hover affordance.
        """
        glyph_bounds = self._get_glyph_bounds()
        widget_bounds = QRectF(0.0, 0.0, float(self.w), float(self.h))
        bounds = glyph_bounds.united(widget_bounds).adjusted(-6.0, -6.0, 6.0, 6.0)
        path = QPainterPath()
        path.addRoundedRect(bounds, 8.0, 8.0)
        return path

    def _apply_tooltip(self, text: str) -> None:
        """
        Apply one tooltip to the parent item and the visible child overlays.
        """
        self.setToolTip(text)
        self.nexus.setToolTip(text)
        self._interaction_target.setToolTip(text)
        self._interaction_ring.setToolTip(text)
        self._result_badge.setToolTip(text)
        self._result_label.setToolTip(text)

        if self.glyph is not None:
            self.glyph.setToolTip(text)
        else:
            pass

    def _get_symbol_fill_brush(self) -> QBrush:
        """
        Build the current symbol fill brush.
        """
        if self.api_object is not None and not self.api_object.active:
            fill_color = QColor(115, 115, 115, 32)
        elif self._result_color is not None:
            fill_color = QColor(self._result_color)
            fill_color.setAlpha(68)
        else:
            fill_color = QColor(ACTIVE['background'])
            fill_color.setAlpha(28)

        return QBrush(fill_color)

    def refresh_visual_style(self) -> None:
        """
        Refresh the symbol, nexus, hover ring, and results badge styling.
        """
        glyph_color = QColor(self.color)

        if self.api_object is not None and self.api_object.active and self._result_color is not None:
            glyph_color = QColor(self._result_color)
        else:
            pass

        glyph_pen = QPen(glyph_color, self.width, self.style, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        nexus_pen = QPen(glyph_color, self.width, self.style, Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.MiterJoin)
        self.nexus.setPen(nexus_pen)

        if self.glyph is not None:
            self.glyph.setPen(glyph_pen)
        else:
            pass

        if isinstance(self.glyph, (Square, Circle, Polygon, InjectionSymbolBase)):
            self.glyph.setBrush(self._get_symbol_fill_brush())
        else:
            pass

        self._interaction_target.setPath(self._build_interaction_path())
        self._interaction_ring.setPath(self._build_interaction_path())

        ring_color = QColor(glyph_color)
        ring_color.setAlpha(200 if (self.isSelected() or self._is_hovered) else 0)
        ring_width = 2.4 if self.isSelected() else 1.6
        self._interaction_ring.setPen(QPen(ring_color, ring_width, Qt.PenStyle.SolidLine,
                                           Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))

        badge_stroke = QColor(glyph_color)
        badge_stroke.setAlpha(150)
        badge_fill = QColor(ACTIVE['background'])
        badge_fill.setAlpha(215)
        self._result_badge.setPen(QPen(badge_stroke, 1.0))
        self._result_badge.setBrush(QBrush(badge_fill))
        self._result_label.setDefaultTextColor(glyph_color if self._result_color is not None else ACTIVE['text'])
        self.refresh_result_label_layout()

    def refresh_result_label_layout(self) -> None:
        """
        Position and show or hide the compact results badge.
        """
        has_label: bool = self.draw_labels and len(self._result_lines) > 0
        self._result_label.setVisible(has_label)
        self._result_badge.setVisible(has_label)

        if not has_label:
            return
        else:
            pass

        badge_rows: str = "<br/>".join(self._result_lines)
        self._result_label.setHtml(
            f'<div style="font-size:9pt; font-weight:600; text-align:center;">{badge_rows}</div>'
        )
        label_rect = self._result_label.boundingRect()
        label_x = float(self.w) * 0.5 - (label_rect.x() + label_rect.width() * 0.5)
        bounds = self._get_glyph_bounds()
        symbol_bottom: float = max(float(bounds.bottom()), float(self.h))
        label_y = symbol_bottom + 8.0
        self._result_label.set_anchor_position(QPointF(label_x, label_y))
        self.refresh_result_label_badge_geometry()

    def refresh_result_label_badge_geometry(self) -> None:
        """
        Refresh the rounded badge path around the current result label position.

        :return: ``None``.
        """
        if not self._result_label.isVisible():
            return
        else:
            pass

        label_rect = self._result_label.boundingRect()
        badge_rect = self._result_label.mapRectToParent(label_rect).adjusted(-4.0, -2.0, 4.0, 2.0)
        badge_path = QPainterPath()
        badge_path.addRoundedRect(badge_rect, 4.0, 4.0)
        self._result_badge.setPath(badge_path)

    def clear_result_visuals(self) -> None:
        """
        Remove result-driven styling and restore the default tooltip.
        """
        self._result_color = None
        self._result_lines = list()
        self._result_label.setHtml("")
        self._apply_tooltip(self._default_tooltip)
        self.refresh_visual_style()

    def set_result_visuals(self, lines: list[str], tooltip: str, color: QColor | None = None) -> None:
        """
        Apply one set of compact result lines and one result-driven color.
        """
        self._result_lines = [line for line in lines if line]
        self._result_color = QColor(color) if color is not None else None
        self._apply_tooltip(tooltip if len(tooltip) > 0 else self._default_tooltip)
        self.refresh_visual_style()

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """
        Show a subtle halo when the injection is hovered.
        """
        self._is_hovered = True
        self.refresh_visual_style()
        QGraphicsItemGroup.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """
        Hide the hover halo when the pointer leaves the injection.
        """
        self._is_hovered = False
        self.refresh_visual_style()
        QGraphicsItemGroup.hoverLeaveEvent(self, event)

    def update_nexus(self, pos: QPointF):
        """
        Update the routed nexus path that joins the parent and this object.
        :param pos: position of this object
        """
        path = QPainterPath()
        route_points = self.get_nexus_render_points()

        if len(route_points) > 0:
            path.moveTo(route_points[0][0], route_points[0][1])

            route_point: tuple[float, float]
            for route_point in route_points[1:]:
                path.lineTo(route_point[0], route_point[1])
        else:
            pass

        self.nexus.setPath(path)
        self.refresh_nexus_z_order()
        self.refresh_nexus_handles()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """
        Keep the nexus line synchronized with scene-position changes.
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            if self.editor.is_loading_diagram():
                pass
            elif self.nexus.isSelected():
                pass
            else:
                self.sync_manual_dock_metadata_from_position()
            self.update_nexus(self.scenePos())
            return value
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if bool(value):
                self.nexus.setSelected(False)
            else:
                pass
            self.clear_nexus_edit_if_fully_deselected()
            self.refresh_nexus_z_order()
            self.refresh_nexus_handles()
            self.refresh_visual_style()
            return value
        else:
            return super().itemChange(change, value)

    def paint(self,
              painter: QPainter,
              option: QStyleOptionGraphicsItem,
              widget: QWidget | None = None) -> None:
        """
        Keep the container item visually inert.

        Children paint the actual symbol, labels, and nexus overlays. The group item
        itself must not add the default Qt selection rectangle because selection is
        represented by the shared rounded interaction ring instead.

        :param painter: Unused painter.
        :param option: Unused style option.
        :param widget: Unused target widget.
        :return: ``None``.
        """
        return None

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Persist manual child placement after interactive dragging.

        :param event: Mouse event.
        :return: ``None``.
        """
        QGraphicsItemGroup.mouseReleaseEvent(self, event)

        if self.editor.is_loading_diagram():
            return
        elif self.nexus.isSelected():
            return
        else:
            self.sync_manual_dock_metadata_from_position()

    def get_dock_metadata(self) -> dict[str, Any]:
        """
        Return persisted dock metadata for this injection.

        :return: Dock metadata.
        """
        return self.editor.diagram.sync_injection_dock(api_object=self.api_object,
                                                       owner_device=self.parent.api_object,
                                                       side="bottom")

    def set_dock_metadata(self, dock: dict[str, Any]) -> None:
        """
        Persist dock metadata and keep the nexus refreshed.

        :param dock: Dock metadata.
        :return: ``None``.
        """
        self.editor.diagram.set_dock(self.api_object, dock)

    def infer_manual_dock_side(self) -> SchematicAttachmentSlot:
        """
        Infer the dock side from the current child center relative to the parent center.

        :return: Inferred dock side.
        """
        parent_center_x: float = float(self.parent.rect().width()) * 0.5
        parent_center_y: float = float(self.parent.rect().height()) * 0.5
        child_center_x: float = float(self.x()) + float(self.w) * 0.5
        child_center_y: float = float(self.y()) + float(self.h) * 0.5

        dx: float = child_center_x - parent_center_x
        dy: float = child_center_y - parent_center_y
        norm_x: float = abs(dx) / max(parent_center_x, 1e-9)
        norm_y: float = abs(dy) / max(parent_center_y, 1e-9)

        if norm_x > norm_y:
            if dx < 0.0:
                return SchematicAttachmentSlot.LEFT
            else:
                return SchematicAttachmentSlot.RIGHT
        else:
            if dy < 0.0:
                return SchematicAttachmentSlot.TOP
            else:
                return SchematicAttachmentSlot.BOTTOM

    def get_manual_dock_alignment(self, side: SchematicAttachmentSlot) -> float:
        """
        Compute the normalized alignment of the child center on one dock side.

        :param side: Dock side.
        :return: Alignment factor.
        """
        local_center_x: float = float(self.x()) + float(self.w) * 0.5
        local_center_y: float = float(self.y()) + float(self.h) * 0.5
        parent_width: float = float(self.parent.rect().width())
        parent_height: float = float(self.parent.rect().height())

        if side == SchematicAttachmentSlot.LEFT or side == SchematicAttachmentSlot.RIGHT:
            if parent_height <= 0.0:
                return 0.5
            else:
                return clamp_alignment(local_center_y / parent_height)
        else:
            if parent_width <= 0.0:
                return 0.5
            else:
                return clamp_alignment(local_center_x / parent_width)

    def get_manual_dock_offset(self, side: SchematicAttachmentSlot) -> float:
        """
        Compute the perpendicular offset of the child origin from one dock side baseline.

        :param side: Dock side.
        :return: Dock offset.
        """
        if side == SchematicAttachmentSlot.TOP:
            return max(0.0, -float(self.y()) - float(self.h) - 40.0)
        elif side == SchematicAttachmentSlot.LEFT:
            return max(0.0, -float(self.x()) - float(self.w) - 40.0)
        elif side == SchematicAttachmentSlot.RIGHT:
            return max(0.0, float(self.x()) - float(self.parent.w) - 40.0)
        else:
            return max(0.0, float(self.y()) - float(self.parent.get_bottom_dock_baseline()))

    def get_child_anchor_local_point_from_parent_scene_anchor(self, parent_scene_anchor: QPointF) -> QPointF:
        """
        Project one parent anchor scene point to the child perimeter.

        :param parent_scene_anchor: Parent-side scene anchor.
        :return: Child-local anchor point.
        """
        local_reference_point: QPointF = self.mapFromScene(parent_scene_anchor)
        dock = self.get_dock_metadata()
        side_value: str = str(dock.get("side", SchematicAttachmentSlot.BOTTOM.value))

        if side_value == SchematicAttachmentSlot.TOP.value:
            child_side: SchematicAttachmentSlot = SchematicAttachmentSlot.BOTTOM
        elif side_value == SchematicAttachmentSlot.LEFT.value:
            child_side = SchematicAttachmentSlot.RIGHT
        elif side_value == SchematicAttachmentSlot.RIGHT.value:
            child_side = SchematicAttachmentSlot.LEFT
        else:
            child_side = SchematicAttachmentSlot.TOP

        if child_side == SchematicAttachmentSlot.TOP or child_side == SchematicAttachmentSlot.BOTTOM:
            alignment: float = clamp_alignment(float(local_reference_point.x()) / max(float(self.w), 1e-9))
        else:
            alignment = clamp_alignment(float(local_reference_point.y()) / max(float(self.h), 1e-9))

        return get_local_rect_side_anchor(width=float(self.w),
                                          height=float(self.h),
                                          side=child_side,
                                          alignment=alignment)

    def get_child_anchor_local_point_from_dock(self, dock: dict[str, Any]) -> QPointF:
        """
        Resolve the child-local nexus anchor from dock metadata.

        :param dock: Dock metadata.
        :return: Child-local anchor point.
        """
        child_anchor_x: Any = dock.get("child_anchor_x", None)
        child_anchor_y: Any = dock.get("child_anchor_y", None)

        if child_anchor_x is None or child_anchor_y is None:
            parent_anchor_scene_point: QPointF = self.get_parent_nexus_anchor()
            return self.get_child_anchor_local_point_from_parent_scene_anchor(parent_scene_anchor=parent_anchor_scene_point)
        else:
            side_value: str = str(dock.get("side", SchematicAttachmentSlot.BOTTOM.value))

            if side_value == SchematicAttachmentSlot.TOP.value:
                child_side: SchematicAttachmentSlot = SchematicAttachmentSlot.BOTTOM
            elif side_value == SchematicAttachmentSlot.LEFT.value:
                child_side = SchematicAttachmentSlot.RIGHT
            elif side_value == SchematicAttachmentSlot.RIGHT.value:
                child_side = SchematicAttachmentSlot.LEFT
            else:
                child_side = SchematicAttachmentSlot.TOP

            if child_side == SchematicAttachmentSlot.TOP or child_side == SchematicAttachmentSlot.BOTTOM:
                alignment: float = clamp_alignment(float(child_anchor_x) / max(float(self.w), 1e-9))
            else:
                alignment = clamp_alignment(float(child_anchor_y) / max(float(self.h), 1e-9))

            return get_local_rect_side_anchor(width=float(self.w),
                                              height=float(self.h),
                                              side=child_side,
                                              alignment=alignment)

    def sync_manual_dock_metadata_from_position(self) -> None:
        """
        Persist the current child position as manual dock metadata.

        :return: ``None``.
        """
        dock = self.get_dock_metadata()
        side: SchematicAttachmentSlot = self.infer_manual_dock_side()
        alignment: float = self.get_manual_dock_alignment(side=side)
        offset: float = self.get_manual_dock_offset(side=side)
        child_anchor_x: Any = dock.get("child_anchor_x", None)
        child_anchor_y: Any = dock.get("child_anchor_y", None)
        parent_anchor_local_point: QPointF = self.get_parent_anchor_local_point_from_child_position()

        if child_anchor_x is None or child_anchor_y is None:
            child_anchor_local_point: QPointF = self.get_child_anchor_local_point_from_parent_scene_anchor(
                parent_scene_anchor=self.parent.get_connection_scene_point_from_local_point(parent_anchor_local_point)
            )
        else:
            child_anchor_local_point = QPointF(float(child_anchor_x), float(child_anchor_y))

        dock["side"] = side.value
        dock["alignment"] = alignment
        dock["offset"] = offset
        dock["auto_layout"] = False
        dock["anchor_x"] = float(parent_anchor_local_point.x())
        dock["anchor_y"] = float(parent_anchor_local_point.y())
        dock["anchor_auto"] = False
        dock["child_anchor_x"] = float(child_anchor_local_point.x())
        dock["child_anchor_y"] = float(child_anchor_local_point.y())
        self.set_dock_metadata(dock)
        self.update_nexus(self.scenePos())

        self.editor.update_diagram_element(device=self.api_object,
                                           x=self.scenePos().x(),
                                           y=self.scenePos().y(),
                                           w=float(self.w),
                                           h=float(self.h),
                                           r=float(self.rotation()),
                                           draw_labels=self.draw_labels,
                                           graphic_object=self)

    def get_parent_anchor_local_point_from_child_position(self) -> QPointF:
        """
        Project the current child center to the parent electrical connection locus.

        :return: Parent-local anchor point.
        """
        child_center_local_x: float = float(self.x()) + float(self.w) * 0.5
        child_center_local_y: float = float(self.y()) + float(self.h) * 0.5
        return self.parent.get_connection_local_point_from_local_point(QPointF(child_center_local_x,
                                                                               child_center_local_y))

    def get_parent_anchor_local_point_from_dock(self, dock: dict[str, Any]) -> QPointF:
        """
        Resolve the parent-local nexus anchor from dock metadata.

        :param dock: Dock metadata.
        :return: Parent-local anchor point.
        """
        anchor_x: Any = dock.get("anchor_x", None)
        anchor_y: Any = dock.get("anchor_y", None)

        if anchor_x is None or anchor_y is None:
            child_center_local_x: float = float(self.x()) + float(self.w) * 0.5
            child_center_local_y: float = float(self.y()) + float(self.h) * 0.5
            return self.parent.get_connection_local_point_from_local_point(QPointF(child_center_local_x,
                                                                                   child_center_local_y))
        else:
            return self.parent.get_connection_local_point_from_local_point(QPointF(float(anchor_x),
                                                                                   float(anchor_y)))

    def get_child_nexus_anchor(self) -> QPointF:
        """
        Get the current child-side nexus anchor.

        :return: Child-side scene anchor.
        """
        dock = self.get_dock_metadata()
        local_anchor = self.get_child_anchor_local_point_from_dock(dock=dock)
        return self.mapToScene(local_anchor)

    def get_parent_nexus_anchor(self) -> QPointF:
        """
        Get the current parent-side nexus anchor.

        :return: Parent-side scene anchor.
        """
        dock = self.get_dock_metadata()
        parent_anchor_local_point: QPointF = self.get_parent_anchor_local_point_from_dock(dock=dock)
        return self.parent.get_connection_scene_point_from_local_point(parent_anchor_local_point)

    def get_nexus_route_points_for_editing(self) -> list[tuple[float, float]]:
        """
        Return the currently rendered nexus route points.

        :return: Route points.
        """
        return normalize_route_points(self.get_nexus_render_points())

    def should_preserve_nexus_route_shape(self) -> bool:
        """
        Determine whether the persisted nexus route should keep its elbows.

        :return: ``True`` when the persisted nexus path is manual.
        """
        dock = self.get_dock_metadata()
        route_kind: SchematicRouteKind | None = parse_schematic_route_kind(dock.get("nexus_route_kind", None))
        auto_route_kinds: set[SchematicRouteKind] = {
            SchematicRouteKind.ORTHOGONAL,
            SchematicRouteKind.AUTO,
            SchematicRouteKind.AUTO_ORTHOGONAL,
            SchematicRouteKind.AUTO_POLYLINE,
        }

        if route_kind in auto_route_kinds:
            return False
        elif route_kind is None and str(dock.get("nexus_route_kind", "")) == "":
            return False
        else:
            return True

    def get_nexus_render_points(self) -> list[tuple[float, float]]:
        """
        Get the currently rendered nexus route points.

        :return: Route points.
        """
        child_anchor = self.get_child_nexus_anchor()
        parent_anchor = self.get_parent_nexus_anchor()
        start = (child_anchor.x(), child_anchor.y())
        end = (parent_anchor.x(), parent_anchor.y())
        dock = self.get_dock_metadata()
        persisted_points_raw = dock.get("nexus_route_points", list())

        if self.should_preserve_nexus_route_shape() and isinstance(persisted_points_raw, list) and len(persisted_points_raw) >= 2:
            persisted_points = normalize_route_points(persisted_points_raw)
            return merge_route_with_endpoints(start=start,
                                              end=end,
                                              persisted_points=persisted_points)
        else:
            return build_default_branch_route(start=start,
                                              end=end)

    def persist_manual_nexus_route(self, points: list[tuple[float, float]]) -> None:
        """
        Persist one manual nexus polyline.

        :param points: Route points.
        :return: ``None``.
        """
        dock = self.get_dock_metadata()
        dock["nexus_route_points"] = normalize_route_points(points)
        dock["nexus_route_kind"] = SchematicRouteKind.MANUAL_POLYLINE.value
        self.set_dock_metadata(dock)

    def move_nexus_segment(self,
                           segment_index: int,
                           original_points: list[tuple[float, float]],
                           delta_x: float,
                           delta_y: float) -> None:
        """
        Move one interior nexus segment.

        :param segment_index: Segment index.
        :param original_points: Route points captured at drag start.
        :param delta_x: Horizontal scene delta.
        :param delta_y: Vertical scene delta.
        :return: ``None``.
        """
        moved_points = move_polyline_route_segment(points=original_points,
                                                   segment_index=segment_index,
                                                   delta_x=delta_x,
                                                   delta_y=delta_y)
        self._nexus_route_points = normalize_route_points(moved_points)
        self.persist_manual_nexus_route(self._nexus_route_points)
        self.update_nexus(self.scenePos())

    def move_nexus_vertex(self, vertex_index: int, scene_pos: QPointF) -> None:
        """
        Move one interior nexus vertex.

        :param vertex_index: Vertex index.
        :param scene_pos: New scene position.
        :return: ``None``.
        """
        current_points = self.get_nexus_route_points_for_editing()
        moved_points = move_polyline_route_vertex(points=current_points,
                                                  vertex_index=vertex_index,
                                                  new_x=scene_pos.x(),
                                                  new_y=scene_pos.y())
        self._nexus_route_points = normalize_route_points(moved_points)
        self.persist_manual_nexus_route(self._nexus_route_points)
        self.update_nexus(self.scenePos())

    def move_nexus_endpoint_alignment(self, endpoint: str, scene_pos: QPointF) -> None:
        """
        Move one nexus endpoint alignment along its host side.

        :param endpoint: ``"child"`` or ``"parent"``.
        :param scene_pos: Scene point chosen by the user.
        :return: ``None``.
        """
        dock = self.get_dock_metadata()

        if endpoint == "parent":
            parent_anchor_local_point: QPointF = self.parent.get_connection_local_point_from_scene_point(scene_pos)
            dock["anchor_x"] = float(parent_anchor_local_point.x())
            dock["anchor_y"] = float(parent_anchor_local_point.y())
            dock["anchor_auto"] = False
        else:
            child_anchor_local_point = self.get_child_anchor_local_point_from_parent_scene_anchor(parent_scene_anchor=scene_pos)
            dock["child_anchor_x"] = float(child_anchor_local_point.x())
            dock["child_anchor_y"] = float(child_anchor_local_point.y())

        self.set_dock_metadata(dock)
        self.update_nexus(self.scenePos())

    def refresh_nexus_z_order(self) -> None:
        """
        Keep the selected nexus editor above the parent node.

        :return: ``None``.
        """
        if self.is_nexus_edit_active():
            self.setZValue(6)
            self.nexus.setZValue(4)
            self.nexus.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        else:
            self.setZValue(0)
            self.nexus.setZValue(-1)
            self.nexus.setAcceptedMouseButtons(Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)

        self.refresh_nexus_edit_locks()

    def is_nexus_edit_active(self) -> bool:
        """
        Determine whether nexus editing is active either from the glyph or nexus path.

        :return: ``True`` when nexus handles should be visible.
        """
        return self._nexus_edit_active and self.nexus.isSelected()

    def set_nexus_edit_active(self, active: bool) -> None:
        """
        Set the explicit nexus-edit activation state.

        Plain selection must not surface nexus edit handles. Only a direct click on the
        injection glyph or nexus path enables the editor.

        :param active: Requested activation state.
        :return: ``None``.
        """
        self._nexus_edit_active = bool(active)

        # Keep the nexus selection synchronized with the explicit edit-mode state so programmatic
        # activation follows the same path as a direct nexus click.
        if active:
            self.nexus.setSelected(True)
        else:
            pass

        self.refresh_nexus_z_order()
        self.refresh_nexus_handles()

    def clear_nexus_edit_if_fully_deselected(self) -> None:
        """
        Clear nexus editing when neither the glyph nor the nexus path remains selected.

        :return: ``None``.
        """
        if self.isSelected() or self.nexus.isSelected():
            return
        else:
            self._nexus_edit_active = False

    def prepare_for_glyph_interaction(self) -> None:
        """
        Leave nexus edit mode before normal glyph interaction starts.

        Clicking the injection glyph must preserve normal selection and dragging.
        Nexus editing is only entered through the nexus path itself.

        :return: ``None``.
        """
        self.nexus.setSelected(False)
        self.set_nexus_edit_active(False)

    def refresh_nexus_edit_locks(self) -> None:
        """
        Disable owner and parent dragging while nexus editing is active.

        :return: ``None``.
        """
        nexus_selected = self.is_nexus_edit_active()

        if nexus_selected and not self._nexus_edit_locks_applied:
            self._owner_movable_before_nexus_edit = bool(self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
            self._parent_movable_before_nexus_edit = bool(self.parent.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self.parent.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self._nexus_edit_locks_applied = True
        elif not nexus_selected and self._nexus_edit_locks_applied:
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, bool(self._owner_movable_before_nexus_edit))
            self.parent.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, bool(self._parent_movable_before_nexus_edit))
            self._nexus_edit_locks_applied = False
        else:
            pass

    def refresh_nexus_handles(self) -> None:
        """
        Refresh all visible nexus editor handles.

        :return: ``None``.
        """
        points = self.get_nexus_route_points_for_editing()
        segment_indexes = list()
        vertex_indexes = list()
        handle_index: int

        if len(points) >= 4:
            segment_indexes = list(range(1, len(points) - 2))
        else:
            pass

        if len(points) >= 3:
            vertex_indexes = list(range(1, len(points) - 1))
        else:
            pass

        while len(self._nexus_segment_handles) < len(segment_indexes):
            self._nexus_segment_handles.append(NexusSegmentHandleItem(parent_item=self,
                                                                      parent_graphic=self.nexus,
                                                                      segment_index=0))

        while len(self._nexus_segment_handles) > len(segment_indexes):
            handle = self._nexus_segment_handles.pop()
            if handle.scene() is not None:
                handle.scene().removeItem(handle)
            else:
                pass

        for handle_index, segment_index in enumerate(segment_indexes):
            handle = self._nexus_segment_handles[handle_index]
            segment_start = points[segment_index]
            segment_end = points[segment_index + 1]
            handle.set_segment_index(segment_index=segment_index)
            handle.setPos((segment_start[0] + segment_end[0]) * 0.5,
                          (segment_start[1] + segment_end[1]) * 0.5)
            handle.setVisible(self.is_nexus_edit_active())

        while len(self._nexus_vertex_handles) < len(vertex_indexes):
            self._nexus_vertex_handles.append(NexusVertexHandleItem(parent_item=self,
                                                                    parent_graphic=self.nexus,
                                                                    vertex_index=0))

        while len(self._nexus_vertex_handles) > len(vertex_indexes):
            handle = self._nexus_vertex_handles.pop()
            if handle.scene() is not None:
                handle.scene().removeItem(handle)
            else:
                pass

        for handle_index, vertex_index in enumerate(vertex_indexes):
            handle = self._nexus_vertex_handles[handle_index]
            vertex_point = points[vertex_index]
            handle.set_vertex_index(vertex_index=vertex_index)
            handle.setPos(vertex_point[0], vertex_point[1])
            handle.setVisible(self.is_nexus_edit_active())

        child_anchor = self.get_child_nexus_anchor()
        parent_anchor = self.get_parent_nexus_anchor()
        self._nexus_endpoint_handles["child"].setPos(child_anchor)
        self._nexus_endpoint_handles["parent"].setPos(parent_anchor)
        self._nexus_endpoint_handles["child"].setVisible(self.is_nexus_edit_active())
        self._nexus_endpoint_handles["parent"].setVisible(self.is_nexus_edit_active())

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
        Open the default injection editor.

        :return: ``True`` when the editor was opened.
        """
        circuit = self._editor.circuit
        dialog = TemplateDeviceEditor(api_object=self.api_object, circuit=circuit)
        dialog.exec()
        return True

    def mousePressEvent(self, QGraphicsSceneMouseEvent):
        """
        mouse press: display the editor
        :param QGraphicsSceneMouseEvent:
        :return:
        """
        self.prepare_for_glyph_interaction()
        self._editor.set_editor_model(api_object=self.api_object)

        QGraphicsItemGroup.mousePressEvent(self, QGraphicsSceneMouseEvent)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Open the device editor on double click.

        :param event: Mouse event.
        :return: ``None``.
        """
        QGraphicsItemGroup.mouseDoubleClickEvent(self, event)
        self.open_device_editor()

    def change_bus(self):
        """
        Change the generator bus
        """
        self._editor.change_injection_bus(injection_graphics=self)

    def move_behind_converter(self):
        """
        Create a DC bus and a converter and move the injection there
        :return:
        """
        self._editor.move_behind_converter(injection_graphics=self)

    def rescale(self, scale: float = 1.0):
        """

        :param scale:
        :return:
        """
        self.scale = scale

    def set_dock_side(self, side: str) -> None:
        """
        Set the dock side for this injection and rearrange the parent node.
        """
        dock = self.editor.diagram.get_dock(self.api_object)
        dock["side"] = side
        dock["auto_layout"] = True
        dock.pop("alignment", None)
        self.editor.diagram.set_dock(self.api_object, dock)
        self.parent.arrange_children()

    def dock_top(self) -> None:
        """
        Dock this injection on the top side of the parent node.
        """
        self.set_dock_side("top")

    def dock_bottom(self) -> None:
        """
        Dock this injection on the bottom side of the parent node.
        """
        self.set_dock_side("bottom")

    def dock_left(self) -> None:
        """
        Dock this injection on the left side of the parent node.
        """
        self.set_dock_side("left")

    def dock_right(self) -> None:
        """
        Dock this injection on the right side of the parent node.
        """
        self.set_dock_side("right")

    def move_dock_order(self, delta: int) -> None:
        """
        Move this injection earlier or later within its dock side ordering.
        """
        dock = self.editor.diagram.get_dock(self.api_object)
        current_order = int(dock.get("order", 1))
        dock["order"] = max(1, current_order + int(delta))
        dock["auto_layout"] = True
        self.editor.diagram.set_dock(self.api_object, dock)
        self.parent.arrange_children()

    def move_dock_order_earlier(self) -> None:
        """
        Move this injection earlier within its dock side ordering.
        """
        self.move_dock_order(-1)

    def move_dock_order_later(self) -> None:
        """
        Move this injection later within its dock side ordering.
        """
        self.move_dock_order(1)

    def nudge_dock_offset(self, delta: float) -> None:
        """
        Move this injection farther from or closer to the parent node.
        """
        dock = self.editor.diagram.get_dock(self.api_object)
        current_offset = float(dock.get("offset", 0.0))
        dock["offset"] = max(0.0, current_offset + float(delta))
        self.editor.diagram.set_dock(self.api_object, dock)
        self.parent.arrange_children()

    def nudge_dock_outward(self) -> None:
        """
        Move this injection farther away from the parent node.
        """
        self.nudge_dock_offset(20.0)

    def nudge_dock_inward(self) -> None:
        """
        Move this injection closer to the parent node.
        """
        self.nudge_dock_offset(-20.0)

    def rotate_90(self) -> None:
        """
        Rotate this injection graphic by 90 degrees and persist the new angle.

        :return: ``None``.
        """
        new_angle: float = (float(self.rotation()) + 90.0) % 360.0
        self.apply_rotation_state(angle_degrees=new_angle)
        self.update_nexus(self.scenePos())
        self.editor.update_diagram_element(device=self.api_object,
                                           x=self.scenePos().x(),
                                           y=self.scenePos().y(),
                                           w=float(self.w),
                                           h=float(self.h),
                                           r=new_angle,
                                           draw_labels=self.draw_labels,
                                           graphic_object=self)

    def get_base_context_menu(self) -> QMenu:
        """
        Generate the base menu for injections
        :return:
        """
        menu = QMenu()

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Active"),
                       function_ptr=self.enable_disable_toggle,
                       checkeable=True,
                       checked_value=self.api_object.active)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Change bus"),
                       function_ptr=self.change_bus,
                       icon_path=":/Icons/icons/move_bus.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Draw labels"),
                       function_ptr=self.enable_disable_label_drawing,
                       checkeable=True,
                       checked_value=self.draw_labels)

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Editor"),
                       function_ptr=self.open_device_editor,
                       icon_path=":/Icons/icons/edit.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Move behind converter"),
                       function_ptr=self.move_behind_converter,
                       icon_path=":/Icons/icons/to_vsc.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Plot profiles"),
                       function_ptr=self.plot,
                       icon_path=":/Icons/icons/plot.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("RMS Editor"),
                       function_ptr=self.edit_dynamic_rms,
                       icon_path=":/Icons/icons/dyn_edit.png")

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("EMT Editor"),
                       function_ptr=self.edit_dynamic_emt,
                       icon_path=":/Icons/icons/dyn_emt_edit.png")

        menu.addSeparator()

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Rotate 90"),
                       function_ptr=self.rotate_90,
                       icon_path=":/Icons/icons/rotate.svg")

        menu.addSeparator()

        add_menu_entry(menu=menu,
                       text=translate_context_menu_text("Delete"),
                       function_ptr=self.delete,
                       icon_path=":/Icons/icons/delete_schematic.png")

        return menu

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        """
        Display context menu
        @param event:
        @return:
        """
        menu = self.get_base_context_menu()

        menu.exec(event.screenPos())

    def edit_dynamic_rms(self):
        """
        Open the unified dynamic editor workspace for this generator.
        """

        self.editor.gui.open_dynamic_editor(api_object=self.api_object,
                                            circuit=self.editor.circuit,
                                            preferred_mode=DynamicSimulationMode.RMS)

    def edit_dynamic_emt(self):
        """
        Open the unified dynamic editor workspace for this generator.
        """

        self.editor.gui.open_dynamic_editor(api_object=self.api_object,
                                            circuit=self.editor.circuit,
                                            preferred_mode=DynamicSimulationMode.EMT)
