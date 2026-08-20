# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import math
import uuid
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QBrush, QPainter, QPainterPath, QPen, QAction, QPolygonF
from PySide6.QtWidgets import QAbstractGraphicsShapeItem, QApplication, QColorDialog, QGraphicsEllipseItem, \
    QGraphicsItem, \
    QGraphicsPathItem, QGraphicsPolygonItem, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem, \
    QGraphicsView, QMenu, QWidget

from PySide6.QtCore import Signal

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagram
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.enumerations import BlockType
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Expr, BinOp, UnOp
from VeraGridEngine.enumerations import DynamicSimulationMode
if TYPE_CHECKING:
    from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
else:
    pass


def _build_port_tooltip(direction: str, index: int, variable_name: str) -> str:
    """
    Build one translated tooltip for a block-editor port.

    :param direction: Port direction label.
    :param index: Zero-based port index.
    :param variable_name: Variable currently exposed by the port.
    :return: User-facing tooltip text.
    """
    return QtCore.QCoreApplication.translate(
        "DynamicEditorGraphics",
        "{direction} {index}: {name}",
    ).format(direction=direction, index=index, name=variable_name)


def get_signal_pair_suffix(
        block_name: str,
        is_signal_input: bool,
) -> str | None:
    """
    Return the persistent suffix used to associate one From/To signal pair.

    Both historical names (``From_1``/``To_1``) and current names
    (``From1``/``To1``) are accepted. The visible PairedItem label is not
    used because it follows the propagated variable name and therefore changes
    whenever the signal is reconnected.

    :param block_name: Persistent symbolic block name.
    :param is_signal_input: ``True`` for the From/input block.
    :return: Pair suffix, or ``None`` when the block name is not recognizable.
    """
    prefix_candidates: tuple[str, str]
    prefix: str
    suffix: str

    if is_signal_input:
        prefix_candidates = ("From_", "From")
    else:
        prefix_candidates = ("To_", "To")

    for prefix in prefix_candidates:
        if block_name.startswith(prefix):
            suffix = block_name[len(prefix):]
            if len(suffix) > 0:
                return suffix
            else:
                pass
        else:
            pass

    return None


def duplicate_paired_item(original: PairedItem) -> PairedItem | None:
    """
    Duplicate one To/output tag while preserving its From signal identity.

    :param original: Existing To/output PairedItem selected by the user.
    :return: Newly created output item, or ``None`` when duplication is invalid.
    """
    editor: DynamicBlockEditorGUI
    paired_items: List[PairedItem]
    paired_item: PairedItem
    signal_input_item: PairedItem | None = None
    canonical_var: Var | None
    pair_suffix: str | None
    block_name: str
    block_model: Block
    new_item: PairedItem

    if original.editor is None or original.is_signal_in or original.paired_items is None:
        return None
    else:
        editor = original.editor
        paired_items = original.paired_items

    # A To tag must be associated with exactly one From-side owner. Ignore any
    # malformed same-side entries that may survive from an older editor session.
    for paired_item in paired_items:
        if paired_item.is_signal_in and signal_input_item is None:
            signal_input_item = paired_item
        else:
            pass

    if signal_input_item is None:
        return None
    else:
        pass

    canonical_var = signal_input_item.get_signal_var()
    if canonical_var is None or signal_input_item.subsys is None:
        return None
    else:
        pass

    # The symbolic block name is the persistent pair key. The visible item name
    # follows the connected variable and must never be used for reconstruction.
    pair_suffix = get_signal_pair_suffix(
        block_name=signal_input_item.subsys.name,
        is_signal_input=True,
    )
    if pair_suffix is None:
        pair_suffix = str(signal_input_item.subsys.uid)
    else:
        pass

    block_name = f"To{pair_suffix}"
    block_model = Block(
        out_vars=list((canonical_var,)),
        name=block_name,
    )
    editor.main_block.add(block_model)

    new_item = PairedItem(
        editor=editor,
        var_factory=original.var_factory,
        subsys=block_model,
        api_object=original.api_object,
        mode=original.mode,
        name=block_model.name,
        paired_items=list((signal_input_item,)),
        position_changed_callback=editor.build_position_changed_callback(block_model.uid),
    )

    new_item.setPos(original.pos() + QPointF(0.0, 80.0))
    editor.scene.addItem(new_item)
    editor.diagram.add_node(
        name=block_model.name,
        x=new_item.pos().x(),
        y=new_item.pos().y(),
        tpe="signal_out",
        device_uid=block_model.uid,
    )

    # The editor normalizes the symbolic variable object and migrates any
    # VarFactory propagation edges owned by a legacy output identity.
    editor._bind_signal_pair_items(
        signal_input_item=signal_input_item,
        signal_output_items=list((new_item,)),
    )

    editor.mark_unapplied_changes()
    return new_item


def truncate_port_label(text: str, max_chars: int) -> str:
    """Truncate one port label while preserving a readable suffix.

    :param text: Source text.
    :param max_chars: Maximum visible character count.
    :return: Value produced by the graphics operation.
    """
    if len(text) <= max_chars:
        return text
    else:
        return text[:max_chars]


def build_orthogonal_connection_path(start: QPointF, end: QPointF, elbow_offset: float) -> QPainterPath:
    """Build the orthogonal painter path joining two scene positions.

    :param start: Connection start position.
    :param end: Connection end position.
    :param elbow_offset: Value supplied for ``elbow_offset``.
    :return: Value produced by the graphics operation.
    """
    path: QPainterPath = QPainterPath(start)
    delta_x: float = end.x() - start.x()
    delta_y: float = end.y() - start.y()

    if abs(delta_y) < 1 or abs(delta_x) < 1:
        path.lineTo(end)
        return path
    else:
        pass

    offset: float = min(elbow_offset, abs(delta_x) / 2.0) if delta_x != 0 else elbow_offset
    start_elbow_x: float = start.x() + offset
    end_elbow_x: float = end.x() - offset

    if end.x() >= start.x():
        path.lineTo(start_elbow_x, start.y())
        path.lineTo(start_elbow_x, end.y())
    else:
        middle_x: float = start.x() + max(elbow_offset, abs(delta_x) / 2.0)
        path.lineTo(middle_x, start.y())
        path.lineTo(middle_x, end.y())

    path.lineTo(end_elbow_x, end.y())
    path.lineTo(end)
    return path


def _is_dynamic_block_item(item: QGraphicsItem) -> bool:
    """Return whether an item participates in dynamic-block collision handling.

    :param item: Graphics item being inspected.
    :return: Value produced by the graphics operation.
    """
    return item.__class__.__name__ in set(("GenericBlockItem", "PairedItem", "BlockItem", "ProtectedConnectionBlockItem", "UnOpItem", "RoundBaseArithmeticOpItem", "RectBaseArithmeticOpItem",))


def _expanded_item_scene_rect(item: QGraphicsItem, pos: QPointF, margin: float) -> QtCore.QRectF:
    """Return one item scene rectangle expanded by the requested clearance.

    :param item: Graphics item being inspected.
    :param pos: Initial local position.
    :param margin: Value supplied for ``margin``.
    :return: Value produced by the graphics operation.
    """
    delta = pos - item.pos()
    return item.sceneBoundingRect().translated(delta).adjusted(-margin, -margin, margin, margin)


def _position_collides_with_blocks(item: QGraphicsItem, pos: QPointF, margin: float) -> bool:
    """Return whether a proposed item rectangle overlaps another root block.

    :param item: Item being positioned.
    :param pos: Proposed scene position.
    :param margin: Additional collision clearance around both blocks.
    :return: ``True`` when another root block intersects the candidate rectangle.
    """
    scene = item.scene()
    if scene is None:
        return False
    else:
        pass

    candidate_rect = _expanded_item_scene_rect(item, pos, margin)
    other: QGraphicsItem
    for other in scene.items(candidate_rect):
        is_distinct_root_block: bool = (
            other is not item
            and _is_dynamic_block_item(other)
            and other.parentItem() is None
        )
        if is_distinct_root_block:
            if candidate_rect.intersects(other.sceneBoundingRect().adjusted(-margin, -margin, margin, margin)):
                return True
            else:
                pass
        else:
            pass
    return False


def _resolve_non_overlapping_position(item: GenericBlockItem | PairedItem | BlockItem
                                      | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem,
                                      proposed_pos: QPointF,
                                      margin: float = 6.0) -> QPointF:
    """Resolve a collision-free position while preserving the last valid point.

    :param item: Movable dynamic block item.
    :param proposed_pos: Position requested by the drag operation.
    :param margin: Clearance maintained between block rectangles.
    :return: Accepted proposal, an axis-only alternative, or the previous point.
    """
    if item.scene() is None:
        return proposed_pos
    else:
        pass

    current_pos = item.pos()
    if not _position_collides_with_blocks(item, proposed_pos, margin):
        return proposed_pos
    else:
        pass

    dx = proposed_pos.x() - current_pos.x()
    dy = proposed_pos.y() - current_pos.y()
    axis_candidates: List[QPointF]
    if abs(dx) >= abs(dy):
        axis_candidates = list((QPointF(proposed_pos.x(), current_pos.y()), QPointF(current_pos.x(), proposed_pos.y()),))
    else:
        axis_candidates = list((QPointF(current_pos.x(), proposed_pos.y()), QPointF(proposed_pos.x(), current_pos.y()),))

    candidate: QPointF
    for candidate in axis_candidates:
        if not _position_collides_with_blocks(item, candidate, margin):
            return candidate
        else:
            pass

    last_valid: QPointF = item._last_valid_pos
    if isinstance(last_valid, QPointF) and not _position_collides_with_blocks(item, last_valid, margin):
        return QPointF(last_valid)
    else:
        pass
    return current_pos


def _handle_block_item_change(item: GenericBlockItem | PairedItem | BlockItem
                              | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem,
                              change: QGraphicsItem.GraphicsItemChange,
                              value: object) -> object:
    """Persist the latest collision-free position reported by Qt.

    :param item: Dynamic block item reporting the change.
    :param change: Qt graphics-item change kind.
    :param value: Opaque Qt change payload returned unchanged.
    :return: Original Qt change payload.
    """
    if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
        if not _position_collides_with_blocks(item, item.pos(), 6.0):
            item._last_valid_pos = QPointF(item.pos())
        else:
            pass
    else:
        pass
    return value


def _refresh_block_item_connections(item: GenericBlockItem | PairedItem | BlockItem
                                    | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem) -> None:
    """Recompute every graphical connection attached to one block.

    :param item: Dynamic block whose incident paths must be refreshed.
    :return: None.
    """
    ports: List[PortItem] = list(item.inputs)
    ports.extend(item.outputs)
    port: PortItem
    for port in ports:
        connections: List[ConnectionItem] | None = port.connections
        if connections is not None:
            connection: ConnectionItem
            for connection in connections:
                connection.update_path()
        else:
            pass


def _notify_block_item_manual_route_drag(item: GenericBlockItem | PairedItem | BlockItem
                                         | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem,
                                         started: bool) -> None:
    """Notify incident connections that a manual endpoint drag changed state.

    :param item: Dynamic block whose incident routes receive the notification.
    :param started: Whether the endpoint drag is starting or ending.
    :return: None.
    """
    ports: List[PortItem] = list(item.inputs)
    ports.extend(item.outputs)
    port: PortItem

    for port in ports:
        connections: List[ConnectionItem] | None = port.connections
        if connections is not None:
            connection: ConnectionItem
            for connection in connections:
                if started:
                    connection.begin_manual_block_drag(port)
                else:
                    connection.end_manual_block_drag(port)
        else:
            pass


def _finalize_block_drop(item: GenericBlockItem | PairedItem | BlockItem
                         | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem,
                         margin: float = 6.0) -> None:
    """Resolve a final block position and update its incident paths.

    :param item: Dynamic block completing a drag operation.
    :param margin: Minimum clearance maintained from neighbouring blocks.
    :return: None.
    """
    if item.scene() is None:
        return
    else:
        pass
    current_pos = item.pos()
    corrected_pos = _resolve_non_overlapping_position(item, current_pos, margin)
    if corrected_pos != current_pos:
        item.setPos(corrected_pos)
        position_changed_callback: BlockPositionChangedCallback | None = item.position_changed_callback
        if position_changed_callback is not None:
            position_changed_callback(corrected_pos.x(), corrected_pos.y())
        else:
            pass
    else:
        pass
    _refresh_block_item_connections(item)


class EditorGraphicsDefaultsDark:
    """Colour palette used by the editor's dark visual mode."""

    __slots__ = ()

    BLOCK_BORDER: QColor = QColor("#e1f7ff")
    BLOCK_BORDER_SELECTED: QColor = QColor("#cc6f2c")
    BLOCK_TITLE: QColor = QColor("#e1f7ff")
    WIRE_COLOR: QColor = QColor("#e1f7ff")
    BLOCK_FILL: QColor = QColor("#022633")
    PORT_LABEL_COLOR: QColor = QColor("#173042")
    WIRE_ELBOW_OFFSET: float = 36.0
    WIRE_TERMINAL_STUB_LENGTH: float = 18.0
    PORT_LABEL_MAX_CHARS: int = 12
    BLOCK_HEADER_HEIGHT: float = 30.0
    BLOCK_PORT_ROW_HEIGHT: float = 20.0
    BLOCK_PORT_SECTION_PADDING: float = 10.0
    BLOCK_MIN_WIDTH: float = 160.0
    BLOCK_MIN_HEIGHT: float = 70.0
    BLOCK_COMPACT_MIN_WIDTH: float = 100.0
    BLOCK_COMPACT_MIN_HEIGHT: float = 40.0
    BLOCK_COMPACT_HEADER_HEIGHT: float = 20.0
    BLOCK_COMPACT_PORT_ROW_HEIGHT: float = 14.0
    BLOCK_COMPACT_PORT_SECTION_PADDING: float = 6.0
    PORT_ITEM_COLOR: QColor = QColor("#e1f7ff")
    VALIDATION_HICHLIGHTED_BORDER = QColor("#b42318")


class EditorGraphicsDefaultsLight:
    """Colour palette used by the editor's light visual mode."""

    BLOCK_BORDER: QColor = QColor("#03384f")
    BLOCK_BORDER_SELECTED: QColor = QColor("#00bbff")
    BLOCK_TITLE: QColor = QColor("#03384f")
    WIRE_COLOR: QColor = QColor("#03384f")
    BLOCK_FILL: QColor = QColor("#f5fdff")
    PORT_LABEL_COLOR: QColor = QColor("#173042")
    WIRE_ELBOW_OFFSET: float = 36.0
    WIRE_TERMINAL_STUB_LENGTH: float = 18.0
    PORT_LABEL_MAX_CHARS: int = 12
    BLOCK_HEADER_HEIGHT: float = 30.0
    BLOCK_PORT_ROW_HEIGHT: float = 20.0
    BLOCK_PORT_SECTION_PADDING: float = 10.0
    BLOCK_MIN_WIDTH: float = 160.0
    BLOCK_MIN_HEIGHT: float = 70.0
    BLOCK_COMPACT_MIN_WIDTH: float = 100.0
    BLOCK_COMPACT_MIN_HEIGHT: float = 40.0
    BLOCK_COMPACT_HEADER_HEIGHT: float = 20.0
    BLOCK_COMPACT_PORT_ROW_HEIGHT: float = 14.0
    BLOCK_COMPACT_PORT_SECTION_PADDING: float = 6.0
    PORT_ITEM_COLOR: QColor = QColor("#03384f")
    VALIDATION_HICHLIGHTED_BORDER = QColor("#b42318")


class EditorGraphicsCommonFeatures:
    """Shared visual dimensions and roles used by every editor palette."""

    VALIDATION_HICHLIGHTED_BORDER = QColor("#b42318")
    BLOCK_BORDER_SELECTED: QColor = QColor("#00bbff")
    dirtyStateChanged = Signal(bool)
    WIRE_ELBOW_OFFSET: float = 36.0
    WIRE_TERMINAL_STUB_LENGTH: float = 18.0
    WIRE_BLOCK_CLEARANCE: float = 18.0
    WIRE_BLOCK_MARGIN: float = 8.0
    PORT_LABEL_MAX_CHARS: int = 12
    BLOCK_HEADER_HEIGHT: float = 30.0
    BLOCK_PORT_ROW_HEIGHT: float = 20.0
    BLOCK_PORT_SECTION_PADDING: float = 10.0
    BLOCK_MIN_WIDTH: float = 160.0
    BLOCK_MIN_HEIGHT: float = 70.0
    BLOCK_COMPACT_MIN_WIDTH: float = 100.0
    BLOCK_COMPACT_MIN_HEIGHT: float = 40.0
    BLOCK_COMPACT_HEADER_HEIGHT: float = 20.0
    BLOCK_COMPACT_PORT_ROW_HEIGHT: float = 14.0
    BLOCK_COMPACT_PORT_SECTION_PADDING: float = 6.0
    TEMPLATE_NODE_TYPE: str = "TEMPLATE"
    INITIAL_LAYOUT_SCALE: float = 0.60
    INITIAL_VIEW_SCALE: float = 1.3
    LAYOUT_MARGIN: float = 40.0
    PARAMETER_VALUE_TYPE_ROLE: int = int(QtCore.Qt.ItemDataRole.UserRole) + 500
    PARAMETER_EDITABLE_ROLE: int = int(QtCore.Qt.ItemDataRole.UserRole) + 501
    LIBRARY_SEARCH_TEXT_ROLE: int = int(QtCore.Qt.ItemDataRole.UserRole) + 502
    BLOCK_SEARCH_ROLE: int = int(QtCore.Qt.ItemDataRole.UserRole) + 503
    MODAL_TEMPLATE_KIND_ATTR: str = "_modal_template_kind"
    MODAL_TEMPLATE_CONFIG_ATTR: str = "_modal_template_config"


class BlockPositionChangedCallback:
    """Forward block movement through an explicit typed callable object."""

    __slots__ = ("_editor", "_block_uid")

    def __init__(self, editor: DynamicBlockEditorGUI, block_uid: int) -> None:
        """Bind one editor and symbolic block identifier.

        :param editor: Editor that persists diagram coordinates.
        :param block_uid: Symbolic block whose position is updated.
        :return: None.
        """
        self._editor: DynamicBlockEditorGUI = editor
        self._block_uid: int = block_uid

    def __call__(self, x_pos: float, y_pos: float) -> None:
        """Forward one position update to the owning editor.

        :param x_pos: New scene x coordinate.
        :param y_pos: New scene y coordinate.
        :return: None.
        """
        self._editor.on_block_position_changed(self._block_uid, x_pos, y_pos)


def _build_rounded_triangle_path(v0: QPointF,
                                 v1: QPointF,
                                 v2: QPointF,
                                 radius: float) -> QPainterPath:
    """Build the antialiased rounded triangular path used by a port.

    :param v0: First triangle vertex.
    :param v1: Second triangle vertex.
    :param v2: Third triangle vertex.
    :param radius: Distance trimmed from each sharp corner.
    :return: Closed rounded-triangle painter path.
    """
    delta_01: QPointF = v1 - v0
    length_01: float = math.sqrt(delta_01.x() * delta_01.x() + delta_01.y() * delta_01.y())
    unit_01: QPointF = (QPointF(0.0, 0.0) if length_01 < 1.0e-10
                        else QPointF(delta_01.x() / length_01, delta_01.y() / length_01))
    start_0: QPointF = v0 + unit_01 * radius
    end_0: QPointF = v1 - unit_01 * radius

    delta_12: QPointF = v2 - v1
    length_12: float = math.sqrt(delta_12.x() * delta_12.x() + delta_12.y() * delta_12.y())
    unit_12: QPointF = (QPointF(0.0, 0.0) if length_12 < 1.0e-10
                        else QPointF(delta_12.x() / length_12, delta_12.y() / length_12))
    start_1: QPointF = v1 + unit_12 * radius
    end_1: QPointF = v2 - unit_12 * radius

    delta_20: QPointF = v0 - v2
    length_20: float = math.sqrt(delta_20.x() * delta_20.x() + delta_20.y() * delta_20.y())
    unit_20: QPointF = (QPointF(0.0, 0.0) if length_20 < 1.0e-10
                        else QPointF(delta_20.x() / length_20, delta_20.y() / length_20))
    start_2: QPointF = v2 + unit_20 * radius
    end_2: QPointF = v0 - unit_20 * radius

    path: QPainterPath = QPainterPath()
    path.moveTo(start_0)
    path.lineTo(end_0)
    path.quadTo(v1, start_1)
    path.lineTo(end_1)
    path.quadTo(v2, start_2)
    path.lineTo(end_2)
    path.quadTo(v0, start_0)
    path.closeSubpath()
    return path


class ResizeHandle(QGraphicsItem):
    """Interactive lower-right resize handle owned by one generic block."""

    __slots__ = ("editor", "_size", "block", "pen_color")

    def __init__(self, block_item: GenericBlockItem, editor: DynamicBlockEditorGUI, size: int = 10) -> None:
        """Create a resize handle for one block.

        :param block_item: Block whose rectangle is resized.
        :param editor: Owning dynamic editor.
        :param size: Visual handle size in scene units.
        :return: None.
        """
        super().__init__(block_item)
        self.editor: DynamicBlockEditorGUI = editor
        self._size: int = size
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setZValue(2)
        self.block: GenericBlockItem = block_item
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)
        self.pen_color: QColor = QColor("#03384f")

    def boundingRect(self) -> QtCore.QRectF:
        """Return the local clickable handle rectangle.

        :return: Local handle bounds.
        """
        return QtCore.QRectF(0, 0, 13, 13)

    def shape(self) -> QPainterPath:
        """Return the precise rectangular hit-test path.

        :return: Handle hit-test path.
        """
        path: QPainterPath = QPainterPath()
        path.addRect(QtCore.QRectF(0, 0, 13, 13))
        return path

    def recolour_mode(self) -> None:
        """Apply the active editor palette to the handle.

        :return: None.
        """
        self.pen_color = self.editor.colors_palet.WIRE_COLOR

    def recolour(self, use_custom_color: bool = False) -> None:
        """Refresh handle colours unless a caller preserves custom colours.

        :param use_custom_color: Whether the existing custom colour is retained.
        :return: None.
        """
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def paint(self, painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:

        """Paint the graphics item using its current palette and interaction state.

        :param painter: Painter supplied by Qt.
        :param option: Qt style options for the item.
        :param widget: Optional target widget.
        :return: None.
        """
        pen = QPen(self.pen_color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.drawLine(QPointF(2, 2), QPointF(11, 11))
        painter.drawLine(QPointF(11, 11), QPointF(8, 11))
        painter.drawLine(QPointF(11, 11), QPointF(11, 8))

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        """Translate handle movement into bounded block dimensions.

        :param change: Qt item-change kind.
        :param value: Opaque Qt value, normally a proposed position.
        :return: Bounded position or the base-class result.
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.block.resizing_from_handle:
                new_pos: QPointF = value
                min_width: float
                min_height: float
                min_width, min_height = self.block.get_minimum_block_size()
                new_width: float = max(new_pos.x(), min_width)
                new_height: float = max(new_pos.y(), min_height)
                self.block.resize_block(new_width, new_height)
                return QPointF(new_width, new_height)
            else:
                return super().itemChange(change, value)
        else:
            return super().itemChange(change, value)


class PortItem(QAbstractGraphicsShapeItem):
    """Graphical input or output port attached to one dynamic block."""

    __slots__ = (
        "_size",
        "editor",
        "is_input",
        "_path",
        "subsystem",
        "connections",
        "index",
        "total",
        "base_var",
        "_validation_highlighted",
    )

    _CORNER_RADIUS: float = 2.0

    def __init__(self,
                 subsystem: BlockItem | GenericBlockItem | PairedItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem,
                 editor: DynamicBlockEditorGUI,
                 is_input: bool,
                 index: int,
                 total: int,
                 size: int = 10) -> None:
        """Create one typed triangular block port.

        :param subsystem: Graphical block owning the port.
        :param editor: Owning dynamic editor.
        :param is_input: Whether the port receives a signal.
        :param index: Zero-based position within its side.
        :param total: Total number of ports on the same side.
        :param size: Triangle side length in scene units.
        :return: None.
        """
        super().__init__(subsystem)
        self._size: int = size
        self.editor: DynamicBlockEditorGUI = editor
        self.is_input: bool = is_input
        self._path: QPainterPath = QPainterPath()
        self._build_path()
        self.setZValue(3)
        self.setAcceptHoverEvents(True)
        self.subsystem: BlockItem | GenericBlockItem | PairedItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem = subsystem
        self.connections: List["ConnectionItem"] | None = None
        self.index: int = index
        self.total: int = total
        self.base_var: Var | None = None
        self._validation_highlighted: bool = False

        self.setPos(0, 0)

    def recolour_mode(self) -> None:
        """Apply the active editor palette to this graphics item.

        :return: None.
        """
        self.setBrush(QBrush(self.editor.colors_palet.PORT_ITEM_COLOR))
        self.setPen(QPen(Qt.PenStyle.NoPen))

    def recolour(self, use_custom_color: bool = False) -> None:
        """Refresh this graphics item unless a custom colour must be preserved.

        :param use_custom_color: Whether an existing custom colour is preserved.
        :return: None.
        """
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def _build_path(self) -> None:
        """Rebuild the local painter path that defines the graphics item.

        :return: None.
        """
        side = self._size
        h = math.sqrt(3) / 2 * side
        r = self._CORNER_RADIUS

        if self.is_input:
            v0 = QPointF(0, 0)
            v1 = QPointF(-h, -side / 2)
            v2 = QPointF(-h, side / 2)
        else:
            v0 = QPointF(h, 0)
            v1 = QPointF(0, -side / 2)
            v2 = QPointF(0, side / 2)

        self._path = _build_rounded_triangle_path(v0, v1, v2, r)

    # --- QGraphicsItem interface ---

    def boundingRect(self) -> QtCore.QRectF:
        """Return the local bounding rectangle used by the graphics scene.

        :return: Value produced by the graphics operation.
        """
        return self._path.boundingRect().adjusted(-0.5, -0.5, 0.5, 0.5)

    def shape(self) -> QPainterPath:
        """Return the precise painter path used for hit testing.

        :return: Value produced by the graphics operation.
        """
        return self._path

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        """Paint the graphics item using its current palette and interaction state.

        :param painter: Painter supplied by Qt.
        :param option: Qt style options for the item.
        :param widget: Optional target widget.
        :return: None.
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawPath(self._path)

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """Apply the hover interaction state when the pointer enters the item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """Restore the normal interaction state when the pointer leaves the item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        QApplication.restoreOverrideCursor()

    def is_connected(self) -> bool:
        """Return whether this endpoint owns at least one connection.

        :return: Value produced by the graphics operation.
        """
        if self.connections is not None:
            return True
        else:
            return False

    def update_port_visibility(self) -> None:
        """Hide connected interface tags and show disconnected ones.

        :return: None.
        """
        if self.connections is not None and len(self.connections) > 0:
            self.setVisible(False)
        else:
            self.setVisible(True)

    def set_validation_highlighted(self, val: bool) -> None:
        """
        Toggle the validation overlay state for this port.

        :param val: Whether the port should be shown as a validation issue.
        :return: None.
        """
        self._validation_highlighted = val

        if self._validation_highlighted:
            self.setBrush(QBrush(EditorGraphicsCommonFeatures.VALIDATION_HICHLIGHTED_BORDER))
        else:
            self.setBrush(self.brush())


class BranchingItem(QGraphicsEllipseItem):
    """Movable junction used to branch one visible dynamic connection."""

    __slots__ = ()

    def __init__(self,
                 subsystem: "BlockItem",
                 editor: DynamicBlockEditorGUI,
                 index: int,
                 radius: int = 6) -> None:
        """Initialize the graphics object and its interaction state.

        :param subsystem: Owning block graphics item.
        :param editor: Owning dynamic editor.
        :param index: Zero-based item or port index.
        :param radius: Visible junction radius.
        :return: None.
        """
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)

        self.editor = editor
        self.setZValue(3)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.subsystem: BlockItem = subsystem
        self.index: int = index
        self.connections: List["ConnectionItem"] | None = None
        self.base_var: Var | None = None
        self.owner_connection: ConnectionItem | None = None
        self.routing_node_id: int | None = None

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """Apply the hover interaction state when the pointer enters the item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """Restore the normal interaction state when the pointer leaves the item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        QApplication.restoreOverrideCursor()

    def is_connected(self) -> bool:
        """Return whether this endpoint owns at least one connection.

        :return: Value produced by the graphics operation.
        """
        if self.connections is not None:
            return True
        else:
            return False

    def recolour_mode(self) -> None:
        """Apply the active editor palette to this graphics item.

        :return: None.
        """
        self.setBrush(QBrush(self.editor.colors_palet.BLOCK_FILL))
        self.setPen(QPen(self.editor.colors_palet.BLOCK_BORDER, 1))

    def recolour(self, use_custom_color: bool = False) -> None:
        """Refresh this graphics item unless a custom colour must be preserved.

        :param use_custom_color: Whether an existing custom colour is preserved.
        :return: None.
        """
        if use_custom_color:
            pass
        else:
            self.recolour_mode()


class ConnectionItem(QGraphicsPathItem):
    """Graphical wire joining two compatible dynamic-model ports."""

    __slots__ = ()

    def __init__(self,
                 source_port: PortItem | BranchingItem,
                 target_port: PortItem | BranchingItem,
                 diagram: BlockDiagram | None = None,
                 con_uid: int | None = None,
                 uid: int | None = None,
                 editor: DynamicBlockEditorGUI | None = None) -> None:
        """Initialize the graphics object and its interaction state.

        :param source_port: Connection source endpoint.
        :param target_port: Connection target endpoint.
        :param diagram: Persisted block diagram.
        :param con_uid: Persisted connection identifier.
        :param uid: Graphics connection identifier.
        :param editor: Owning dynamic editor.
        :return: None.
        """
        super().__init__()
        if editor is not None:
            self.editor: DynamicBlockEditorGUI | None = editor
        else:
            self.editor = source_port.subsystem.editor
        self.uid: int = uid if uid is not None else uuid.uuid4().int
        self.setZValue(-1)
        self.source_port: PortItem | BranchingItem = source_port
        self.target_port: PortItem | BranchingItem = target_port
        self.diagram = diagram
        self.con_uid = con_uid if con_uid is not None else self.uid

        if self.source_port.connections is None:
            self.source_port.connections = list()
        else:
            pass
        if self.source_port.connections is not None:
            self.source_port.connections.append(self)
        else:
            pass

        if self.target_port.connections is None:
            self.target_port.connections = list()
        else:
            pass
        if self.target_port.connections is not None:
            self.target_port.connections.append(self)
        else:
            pass

        if isinstance(self.source_port, PortItem):
            self.source_port.update_port_visibility()
        else:
            pass
        if isinstance(self.target_port, PortItem):
            self.target_port.update_port_visibility()
        else:
            pass

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self._dragging_segment: int = -1
        self._drag_start_scene_pos: QPointF | None = None
        self.update_path()

    def recolour_mode(self) -> None:
        """Apply the active editor palette to this graphics item.

        :return: None.
        """
        if self.editor is not None:
            pen = self.pen()
            pen.setColor(self.editor.colors_palet.WIRE_COLOR)
            self.setPen(pen)
            self.update()
        else:
            pen = self.pen()
            pen.setColor(self.source_port.subsystem.editor.colors_palet.WIRE_COLOR)
            self.setPen(pen)
            self.update()

    def recolour(self, use_custom_color: bool = False) -> None:
        """Refresh this graphics item unless a custom colour must be preserved.

        :param use_custom_color: Whether an existing custom colour is preserved.
        :return: None.
        """
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def _uses_routing_graph(self) -> bool:
        """
        Return whether this connection is currently owned by the new routing engine.

        :return: Ownership state.
        """
        if self.editor is not None:
            return self.editor.supports_routing_graph_connection(self)
        else:
            return False

    def update_path(self) -> None:
        """Recompute the complete visible path from the current connection geometry.

        :return: None.
        """
        if self._uses_routing_graph():
            if self.editor is not None:
                if self.editor.sync_connection_with_routing_graph(self):
                    return
                else:
                    return
            else:
                return
        else:
            return

    def begin_manual_block_drag(self, port: PortItem | BranchingItem) -> None:
        """
        Legacy manual-route dragging no longer exists.

        :param port: Port whose owning block has started moving.
        :return: None.
        """
        del port

    def end_manual_block_drag(self, port: PortItem | BranchingItem) -> None:
        """
        Legacy manual-route dragging no longer exists.

        :param port: Port whose owning block has finished moving.
        :return: None.
        """
        del port

    def on_elbow_moved(self, index: int, new_pos: QPointF) -> None:
        """Persist one moved elbow and refresh the connection path.

        :param index: Zero-based item or port index.
        :param new_pos: Value supplied for ``new_pos``.
        :return: None.
        """
        del index
        del new_pos

    def get_route_points_for_editing(self) -> list[tuple[float, float]]:
        """
        :return: The current rendered route points as a normalized point list.
        """
        path: QPainterPath = self.path()
        if path.isEmpty():
            return list()
        else:
            pass

        points: list[tuple[float, float]] = list()
        index: int
        for index in range(path.elementCount()):
            element = path.elementAt(index)
            points.append((float(element.x), float(element.y)))
        return points

    def find_segment_at_scene_position(
            self,
            pos: QPointF,
            threshold: float = 12.0,
            editable_only: bool = True,
    ) -> tuple[int, bool]:
        """
        Return the path segment index under one scene position.

        :param pos: Scene position to inspect.
        :param threshold: Hit-test tolerance.
        :param editable_only: Whether only editable drag segments are allowed.
        :return: Tuple ``(segment_index, is_horizontal)`` or ``(-1, False)``.
        """
        if self._uses_routing_graph():
            if self.editor is not None:
                return self._find_routing_graph_segment_at_scene_position(
                    pos=pos,
                    threshold=threshold,
                    editable_only=editable_only,
                )
            else:
                return -1, False
        else:
            return -1, False

    def _find_routing_graph_segment_at_scene_position(
            self,
            pos: QPointF,
            threshold: float,
            editable_only: bool,
    ) -> tuple[int, bool]:
        """
        Return the routing-graph segment under one scene position.

        :param pos: Scene position to inspect.
        :param threshold: Hit-test tolerance.
        :param editable_only: Whether only editable drag segments are allowed.
        :return: Tuple ``(segment_index, is_horizontal)`` or ``(-1, False)``.
        """
        if self.editor is None:
            return -1, False
        else:
            pass

        ordered_segments: List[Tuple[int, QPointF, QPointF]] = self.editor.get_connection_routing_graph_segments(self)
        if len(ordered_segments) == 0:
            return -1, False
        else:
            pass

        editable_segment_indices: List[int] = list()
        if editable_only:
            if len(ordered_segments) >= 3:
                if len(ordered_segments) == 3:
                    editable_segment_indices.append(1)
                else:
                    pass

                interior_segment_index: int
                for interior_segment_index in range(2, len(ordered_segments) - 2):
                    editable_segment_indices.append(interior_segment_index)
            else:
                pass
        else:
            segment_index: int
            for segment_index in range(len(ordered_segments)):
                editable_segment_indices.append(segment_index)

        if len(editable_segment_indices) == 0:
            return -1, False
        else:
            pass

        segment_index = 0
        for segment_index in editable_segment_indices:
            segment_entry: Tuple[int, QPointF, QPointF] = ordered_segments[segment_index]
            start_point: QPointF = segment_entry[1]
            end_point: QPointF = segment_entry[2]
            delta_y: float = abs(end_point.y() - start_point.y())
            delta_x: float = abs(end_point.x() - start_point.x())

            if delta_y < 1.0:
                if start_point.y() - threshold <= pos.y() <= start_point.y() + threshold:
                    if min(start_point.x(), end_point.x()) - threshold <= pos.x() <= max(start_point.x(), end_point.x()) + threshold:
                        return segment_index, True
                    else:
                        pass
                else:
                    pass
            elif delta_x < 1.0:
                if start_point.x() - threshold <= pos.x() <= start_point.x() + threshold:
                    if min(start_point.y(), end_point.y()) - threshold <= pos.y() <= max(start_point.y(), end_point.y()) + threshold:
                        return segment_index, False
                    else:
                        pass
                else:
                    pass
            else:
                minimum_x: float = min(start_point.x(), end_point.x()) - threshold
                maximum_x: float = max(start_point.x(), end_point.x()) + threshold
                minimum_y: float = min(start_point.y(), end_point.y()) - threshold
                maximum_y: float = max(start_point.y(), end_point.y()) + threshold
                if minimum_x <= pos.x() <= maximum_x and minimum_y <= pos.y() <= maximum_y:
                    return segment_index, False
                else:
                    pass

        return -1, False

    def _segment_hit_test(self, pos: QPointF, threshold: float = 12.0) -> tuple:
        """
        Return the editable segment under one scene position.

        :param pos: Scene position to inspect.
        :param threshold: Hit-test tolerance.
        :return: Tuple ``(segment_index, is_horizontal)`` or ``(-1, False)``.
        """
        return self.find_segment_at_scene_position(
            pos=pos,
            threshold=threshold,
            editable_only=True,
        )

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Handle a graphics-scene mouse press for this item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        scene_pos: QPointF = event.scenePos()
        seg_idx, is_horizontal = self._segment_hit_test(scene_pos)
        if seg_idx >= 0:
            del is_horizontal
            self._dragging_segment = seg_idx
            self._drag_start_scene_pos = QPointF(scene_pos)
            event.accept()
            return
        else:
            pass
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Handle pointer movement for dragging or resizing this item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        if self._dragging_segment >= 0:
            if self._drag_start_scene_pos is None:
                super().mouseMoveEvent(event)
                return
            else:
                pass

            if self._uses_routing_graph() and self.editor is not None:
                new_pos_for_engine: QPointF = event.scenePos()
                original_elements_for_engine: List[QPointF] = list()
                path: QPainterPath = self.path()
                element_index: int
                for element_index in range(path.elementCount()):
                    path_element = path.elementAt(element_index)
                    original_elements_for_engine.append(QPointF(path_element.x, path_element.y))
                if self._dragging_segment < len(original_elements_for_engine) - 1:
                    segment_start: QPointF = original_elements_for_engine[self._dragging_segment]
                    segment_end: QPointF = original_elements_for_engine[self._dragging_segment + 1]
                    engine_delta_x: float = 0.0
                    engine_delta_y: float = 0.0

                    if abs(segment_end.x() - segment_start.x()) < 1.0:
                        engine_delta_x = new_pos_for_engine.x() - self._drag_start_scene_pos.x()
                    else:
                        pass

                    if abs(segment_end.y() - segment_start.y()) < 1.0:
                        engine_delta_y = new_pos_for_engine.y() - self._drag_start_scene_pos.y()
                    else:
                        pass

                    if self.editor.move_connection_segment_with_routing_graph(
                            self,
                            segment_index=self._dragging_segment,
                            delta_x=engine_delta_x,
                            delta_y=engine_delta_y,
                    ):
                        self._drag_start_scene_pos = QPointF(new_pos_for_engine)
                        event.accept()
                        return
                    else:
                        event.accept()
                        return
                else:
                    event.accept()
                    return
            else:
                event.accept()
                return
        else:
            pass
        super().mouseMoveEvent(event)

    def _sync_elbow_items(self) -> None:
        """Synchronize interactive elbow handles with the stored route points.

        :return: None.
        """
        scene = self.scene()
        if scene is None:
            return
        else:
            pass
        item: QGraphicsItem
        for item in list(scene.items()):
            if isinstance(item, ElbowItem) and item.connection_item is self:
                scene.removeItem(item)
            elif isinstance(item, BranchingItem) and item.owner_connection is self:
                scene.removeItem(item)
            else:
                pass
        if self._uses_routing_graph():
            pass
        else:
            pass

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Finalize the current graphics interaction after mouse release.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        if self._dragging_segment >= 0:
            self._dragging_segment = -1
            self._drag_start_scene_pos = None
            if self._uses_routing_graph() and self.editor is not None:
                if self.editor.finalize_connection_routing_graph_drag(self):
                    event.accept()
                    return
                else:
                    event.accept()
                    return
            else:
                event.accept()
                return
        else:
            pass
        super().mouseReleaseEvent(event)

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        """Paint the graphics item using its current palette and interaction state.

        :param painter: Painter supplied by Qt.
        :param option: Qt style options for the item.
        :param widget: Optional target widget.
        :return: None.
        """
        super().paint(painter, option, widget)

        path = self.path()
        count = path.elementCount()
        if count < 2:
            return
        else:
            pass

        last = path.elementAt(count - 1)
        prev = path.elementAt(count - 2)
        end = QPointF(last.x, last.y)
        prev_pt = QPointF(prev.x, prev.y)

        dx = end.x() - prev_pt.x()
        dy = end.y() - prev_pt.y()
        length = math.sqrt(dx * dx + dy * dy)
        if length < 0.1:
            return
        else:
            pass

        dx /= length
        dy /= length

        arrow_size = 8.0
        arrow_angle = 0.5
        cos_a = math.cos(arrow_angle)
        sin_a = math.sin(arrow_angle)
        perp_x = -dy
        perp_y = dx

        p1 = end
        p2 = end + QPointF(
            -dx * arrow_size * cos_a + perp_x * arrow_size * sin_a,
            -dy * arrow_size * cos_a + perp_y * arrow_size * sin_a,
        )
        p3 = end + QPointF(
            -dx * arrow_size * cos_a - perp_x * arrow_size * sin_a,
            -dy * arrow_size * cos_a - perp_y * arrow_size * sin_a,
        )

        arrow = QPolygonF(list((p1, p2, p3,)))
        painter.setBrush(QBrush(self.pen().color()))
        painter.setPen(QPen(self.pen().color(), 1.5,
                            Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap,
                            Qt.PenJoinStyle.RoundJoin))
        painter.drawPolygon(arrow)

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """Apply the hover interaction state when the pointer enters the item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)
        pen: QPen = self.pen()
        # pen.setColor(_get_editor_constants(self.editor).WIRE_HOVER_COLOR)
        pen.setWidthF(3.5)
        self.setPen(pen)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """Restore the normal interaction state when the pointer leaves the item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        QApplication.restoreOverrideCursor()
        pen: QPen = self.pen()
        # pen.setColor(_get_editor_constants(self.editor).WIRE_COLOR)
        pen.setWidthF(1.5)
        self.setPen(pen)


class ElbowItem(QGraphicsEllipseItem):
    """Movable bend point belonging to one orthogonal connection path."""

    __slots__ = ()

    def __init__(self, connection_item: ConnectionItem, index: int, pos: QPointF = QPointF()) -> None:
        """Initialize the graphics object and its interaction state.

        :param connection_item: Connection that owns this elbow.
        :param index: Zero-based item or port index.
        :param pos: Initial local position.
        :return: None.
        """
        radius = 5
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.connection_item = connection_item
        self.index = index
        self.setZValue(2)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPos(pos)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        """Process one Qt graphics-item state change and propagate dependent geometry.

        :param change: Qt graphics-item change kind.
        :param value: Opaque value associated with the Qt change.
        :return: Value produced by the graphics operation.
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            scene = self.connection_item.scene()
            if scene is not None:
                rect = scene.sceneRect()
                x = max(rect.left(), min(value.x(), rect.right()))
                y = max(rect.top(), min(value.y(), rect.bottom()))
                return QPointF(x, y)
            else:
                pass
        else:
            pass
        return super().itemChange(change, value)

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Handle pointer movement for dragging or resizing this item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        super().mouseMoveEvent(event)
        self.connection_item.on_elbow_moved(self.index, self.scenePos())

    def recolour_mode(self) -> None:
        """Apply the active editor palette to this graphics item.

        :return: None.
        """
        if self.connection_item.editor is not None:
            color_fill = self.connection_item.editor.colors_palet.BLOCK_FILL
            pen_color = self.connection_item.editor.colors_palet.BLOCK_BORDER
        else:
            color_fill = self.connection_item.source_port.editor.colors_palet.BLOCK_FILL
            pen_color = self.connection_item.source_port.editor.colors_palet.BLOCK_BORDER

        self.setBrush(QBrush(color_fill))
        self.setPen(QPen(pen_color, 1))

    def recolour(self, use_custom_color: bool = False) -> None:
        """Refresh this graphics item unless a custom colour must be preserved.

        :param use_custom_color: Whether an existing custom colour is preserved.
        :return: None.
        """
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def contextMenuEvent(self, event: QtWidgets.QGraphicsSceneContextMenuEvent) -> None:
        """
        Show the default elbow context menu behaviour.

        :param event: Qt context-menu event.
        :return: None.
        """
        super().contextMenuEvent(event)


class GenericBlockItem(QGraphicsRectItem):
    """Resizable graphics item exposing every port of one symbolic block."""

    __slots__ = ()

    def __init__(self,
                 editor: DynamicBlockEditorGUI,
                 var_factory: VarFactory,
                 subsys: Block,
                 api_object: ALL_DEV_TYPES,
                 mode: DynamicSimulationMode,
                 name: str,
                 position_changed_callback: BlockPositionChangedCallback | None = None) -> None:
        """
        Create one resizable graphics item for a symbolic block.

        :param editor: Dynamic editor that owns the item and its interactions.
        :param var_factory: Factory that owns the symbolic variables shown by the item.
        :param subsys: Symbolic block represented by this graphics item.
        :param api_object: Static grid device associated with the edited dynamic model.
        :param mode: RMS or EMT editing mode used to configure the item.
        :param name: Display name written below the block.
        :param position_changed_callback: Optional callback used to persist position changes.
        :return: None.
        """
        super().__init__(0, 0, 100, 60)

        self.editor: DynamicBlockEditorGUI = editor
        self.var_factory = var_factory
        self.subsys = subsys
        self.mode = mode
        self.name: str = name
        self.api_object = api_object
        self.position_changed_callback = position_changed_callback
        self.name_item = QGraphicsTextItem(self.name, self)

        self.update_name_position()

        self.update_name_position()

        self.inputs: List[PortItem] = list()
        self.outputs: List[PortItem] = list()
        self.input_labels: List[QGraphicsTextItem] = list()
        self.output_labels: List[QGraphicsTextItem] = list()

        self.resize_handle: ResizeHandle | None = None
        self.resizing_from_handle = False
        self._suppress_resize: bool = False
        self._validation_highlighted: bool = False
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)
        self._last_valid_pos: QPointF = QPointF(self.pos())

        self.update_name_position()

        n_inputs = len(self.subsys.in_vars)
        n_outputs = len(self.subsys.out_vars)
        self.inputs = [PortItem(self, self.editor, True, i, n_inputs) for i in range(n_inputs)]
        self.outputs = [PortItem(self, self.editor, False, i, n_outputs) for i in range(n_outputs)]
        for port_item in self.inputs:
            port_item.recolour()
        for port_item in self.outputs:
            port_item.recolour()
        self.input_labels = [self.create_port_label_item() for _ in range(n_inputs)]
        self.output_labels = [self.create_port_label_item() for _ in range(n_outputs)]

        self.refresh_port_metadata()
        self.resize_handle = ResizeHandle(self, self.editor)
        self.resize_to_content()

    def recolour_mode(self) -> None:
        """Apply the active editor palette to this graphics item.

        :return: None.
        """
        self.name_item.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)
        self.setBrush(QBrush(self.editor.colors_palet.BLOCK_FILL))
        self.setPen(QPen(self.editor.colors_palet.BLOCK_BORDER, 1))
        for input_label_item in self.input_labels:
            input_label_item.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)
        for output_label_item in self.output_labels:
            output_label_item.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)

    def recolour(self, use_custom_color: bool = False) -> None:
        """Refresh this graphics item unless a custom colour must be preserved.

        :param use_custom_color: Whether an existing custom colour is preserved.
        :return: None.
        """
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Handle a graphics-scene mouse press for this item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        if (
                event.button() == Qt.MouseButton.LeftButton
                and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.editor.request_navigate_to_block(self.subsys)

            event.accept()
            return
        else:
            pass

        if event.button() == Qt.MouseButton.LeftButton:
            _notify_block_item_manual_route_drag(self, started=True)
        else:
            pass

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Finalize the current graphics interaction after mouse release.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        super().mouseReleaseEvent(event)
        _notify_block_item_manual_route_drag(self, started=False)
        _finalize_block_drop(self)

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """
        Open the modal block properties dialogue on a left-button double click.

        :param event: Incoming Qt event.
        :return: None.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.editor.request_open_block_properties(self.subsys)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def set_subsystem(self, block: Block) -> None:
        """Associate this graphics item with its authoritative symbolic block.

        :param block: Authoritative symbolic block.
        :return: None.
        """
        self.subsys = block

    def refresh_block_name(self) -> None:
        """
        Refresh the visible block name from the authoritative symbolic block.

        :return: None.
        """
        if self.subsys is not None:
            # The symbolic block owns the authoritative name. The graphics item
            # mirrors that value so rename operations keep model and scene text in sync.
            self.name = self.subsys.name
            self.name_item.setPlainText(self.name)
            self.update_name_position()
            self.resize_to_content()
        else:
            pass

    def build_item(self) -> None:
        """Build ports, labels, and resize controls from the symbolic block.

        :return: None.
        """
        if self.subsys is not None:
            self.update_name_position()
            n_inputs: int = len(self.subsys.in_vars)
            n_outputs: int = len(self.subsys.out_vars)
            self.inputs = [PortItem(self, self.editor, True, i, n_inputs) for i in range(n_inputs)]
            for port_item in self.inputs:
                port_item.recolour()
            for port_item in self.outputs:
                port_item.recolour()
            self.outputs = [PortItem(self, self.editor, False, i, n_outputs) for i in range(n_outputs)]
            for port_item in self.inputs:
                port_item.recolour()
            for port_item in self.outputs:
                port_item.recolour()
            self.input_labels = [self.create_port_label_item() for _ in range(n_inputs)]
            self.output_labels = [self.create_port_label_item() for _ in range(n_outputs)]
            self.refresh_port_metadata()
            self.resize_handle = ResizeHandle(self, self.editor)
            self.resize_to_content()
        else:
            pass

    def resize_block(self, width: float, height: float) -> None:
        """Resize the block while enforcing its content-derived minimum dimensions.

        :param width: Requested body width.
        :param height: Requested body height.
        :return: None.
        """
        self.prepareGeometryChange()
        min_width: float
        min_height: float
        min_width, min_height = self.get_minimum_block_size()
        QGraphicsRectItem.setRect(self, 0, 0, max(width, min_width), max(height, min_height))
        self.update_ports()
        self.update_handle_position()
        self.update_name_position()

    def update_handle_position(self) -> None:
        """Move the resize handle to the current lower-right block corner.

        :return: None.
        """
        rect = self.rect()
        self.resizing_from_handle = False
        self.resize_handle.setPos(rect.width() - 9, rect.height() - 9)
        self.resizing_from_handle = True

    def update_name_position(self) -> None:
        """Centre the visible block name below the current body rectangle.

        :return: None.
        """
        if self.name_item is None:
            return
        else:
            pass

        rect = self.rect()

        text_width = self.name_item.boundingRect().width()

        x = (rect.width() - text_width) / 2
        y = rect.height() + 5

        self.name_item.setPos(x, y)

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:

        """Paint the graphics item using its current palette and interaction state.

        :param painter: Painter supplied by Qt.
        :param option: Qt style options for the item.
        :param widget: Optional target widget.
        :return: None.
        """
        rect: QtCore.QRectF = self.rect()
        outer_rect: QtCore.QRectF = rect.adjusted(2, 2, -2, -2)
        body_rect: QtCore.QRectF = outer_rect

        if self._validation_highlighted:
            border_color: QColor = EditorGraphicsCommonFeatures.VALIDATION_HICHLIGHTED_BORDER
        else:
            border_color = (
                EditorGraphicsCommonFeatures.BLOCK_BORDER_SELECTED
                if self.isSelected()
                else self.pen().color()
            )

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        radius = 4.0

        # body
        painter.setBrush(self.brush())

        # delimiter
        painter.setPen(QPen(border_color, 1.6))
        painter.drawRoundedRect(body_rect, radius, radius)

    def set_validation_highlighted(self, val: bool) -> None:
        """
        Toggle the validation overlay state for this block.

        :param val: Whether the block should be outlined as a validation issue.
        :return: None.
        """
        self._validation_highlighted = val
        self.update()

    def get_minimum_block_size(self) -> tuple[float, float]:
        """Compute the minimum dimensions required by ports and labels.

        :return: Value produced by the graphics operation.
        """
        port_rows: int = max(len(self.inputs), len(self.outputs), 1)
        min_height: float = max(
            EditorGraphicsCommonFeatures.BLOCK_MIN_HEIGHT,
            EditorGraphicsCommonFeatures.BLOCK_HEADER_HEIGHT + EditorGraphicsCommonFeatures.BLOCK_PORT_SECTION_PADDING +
            port_rows * EditorGraphicsCommonFeatures.BLOCK_PORT_ROW_HEIGHT
        )

        input_label_width = 0.0
        for label in self.input_labels:
            input_label_width = max(input_label_width, label.boundingRect().width())

        output_label_width = 0.0
        for label in self.output_labels:
            output_label_width = max(output_label_width, label.boundingRect().width())

        padding = 28.0

        min_width = max(
            EditorGraphicsCommonFeatures.BLOCK_MIN_WIDTH,
            input_label_width + output_label_width + padding
        )
        return min_width, min_height

    def resize_to_content(self) -> None:
        """Resize the block to fit its current ports, labels, and title.

        :return: None.
        """
        self.prepareGeometryChange()
        min_width: float
        min_height: float
        min_width, min_height = self.get_minimum_block_size()
        QGraphicsRectItem.setRect(self, 0, 0, min_width, min_height)
        self.update_ports()
        self.update_handle_position()
        self.update_name_position()

    def create_port_label_item(self) -> QGraphicsTextItem:
        """Create one non-interactive text label for a block port.

        :return: Value produced by the graphics operation.
        """
        label_item: QGraphicsTextItem = QGraphicsTextItem("", self)
        label_item.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)
        label_item.setZValue(4)

        return label_item

    def refresh_port_metadata(self) -> None:
        """Synchronize visible port variables, labels, and tooltips.

        :return: None.
        """
        if self.subsys is not None:
            i: int
            port: PortItem
            label_item: QGraphicsTextItem
            variable_name: str
            for i, port in enumerate(self.inputs):
                port.base_var = self.subsys.in_vars[i]
                variable_name = self.subsys.in_vars[i].name
                port.setToolTip(_build_port_tooltip("Input", i, variable_name))
                label_item = self.input_labels[i]
                label_item.setPlainText(
                    truncate_port_label(variable_name, EditorGraphicsCommonFeatures.PORT_LABEL_MAX_CHARS))

            for i, port in enumerate(self.outputs):
                port.base_var = self.subsys.out_vars[i]
                variable_name = self.subsys.out_vars[i].name
                port.setToolTip(_build_port_tooltip("Output", i, variable_name))
                label_item = self.output_labels[i]
                label_item.setPlainText(
                    truncate_port_label(variable_name, EditorGraphicsCommonFeatures.PORT_LABEL_MAX_CHARS))
        else:
            pass

    def update_ports(self) -> None:
        """Position ports and labels and refresh their attached connection paths.

        :return: None.
        """
        i: int
        port: PortItem
        for i, port in enumerate(self.inputs):
            spacing = self.rect().height() / (len(self.inputs) + 1)
            port.setPos(0, spacing * (i + 1))
        for i, port in enumerate(self.outputs):
            spacing = self.rect().height() / (len(self.outputs) + 1)
            port.setPos(self.rect().width(), spacing * (i + 1))

        label_item: QGraphicsTextItem
        for i, label_item in enumerate(self.input_labels):
            port = self.inputs[i]
            label_item.setPos(14.0, port.pos().y() - label_item.boundingRect().height() / 2)

        for i, label_item in enumerate(self.output_labels):
            port = self.outputs[i]
            label_width = label_item.boundingRect().width()
            label_height = label_item.boundingRect().height()

            label_item.setPos(
                self.rect().width() - label_width - 14.0,
                port.pos().y() - label_height / 2
            )

        self.update_handle_position()
        port_collection: List[PortItem]
        for port_collection in (self.inputs, self.outputs):
            for port in port_collection:
                if port.connections:
                    conn: ConnectionItem
                    for conn in port.connections:
                        conn.update_path()
                else:
                    pass

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """Apply the hover interaction state when the pointer enters the item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        QApplication.setOverrideCursor(Qt.CursorShape.OpenHandCursor)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """Restore the normal interaction state when the pointer leaves the item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        if self.resize_handle is not None and self.resize_handle.isVisible():
            self.resize_handle.hide()
        else:
            pass
        QApplication.restoreOverrideCursor()

    def hoverMoveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """Update resize-handle visibility while the pointer moves over the block.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        pos = event.pos()
        rect = self.rect()
        margin = 10.0
        near_corner = (pos.x() >= rect.width() - margin and
                       pos.y() >= rect.height() - margin)
        if self.resize_handle is not None:
            if near_corner and not self.resize_handle.isVisible():
                self.resize_handle.show()
            elif not near_corner and self.resize_handle.isVisible():
                self.resize_handle.hide()
            else:
                pass
        else:
            pass

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        """Process one Qt graphics-item state change and propagate dependent geometry.

        :param change: Qt graphics-item change kind.
        :param value: Opaque value associated with the Qt change.
        :return: Value produced by the graphics operation.
        """
        value = _handle_block_item_change(self, change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.position_changed_callback is not None:
                self.position_changed_callback(value.x(), value.y())
            else:
                pass
            port: PortItem
            port_collection: List[PortItem]
            for port_collection in (self.inputs, self.outputs):
                for port in port_collection:
                    if port.connections:
                        conn: ConnectionItem
                        for conn in port.connections:
                            conn.update_path()
                    else:
                        pass
        else:
            pass
        return super().itemChange(change, value)


class PairedItem(QGraphicsPolygonItem):
    """Named From/To signal tag paired with equivalent tags in the scene."""

    __slots__ = ()

    _LABEL_W: float = 70.0
    _LABEL_H: float = 28.0
    _NOTCH_DEPTH: float = 6.0
    _TIP_BASE: float = 20.0

    def __init__(self,
                 var_factory: VarFactory,
                 subsys: Block,
                 api_object: ALL_DEV_TYPES,
                 mode: DynamicSimulationMode,
                 name: str,
                 editor: DynamicBlockEditorGUI,
                 paired_items: List["PairedItem"] | None = None,
                 position_changed_callback: BlockPositionChangedCallback | None = None) -> None:
        """Initialize the graphics object and its interaction state.

        :param var_factory: Factory that owns symbolic variables.
        :param subsys: Symbolic block represented by the item.
        :param api_object: Static network device associated with the model.
        :param mode: Dynamic simulation mode.
        :param name: Visible block name.
        :param editor: Owning dynamic editor.
        :param paired_items: Other graphics items sharing the same signal identity.
        :param position_changed_callback: Typed callback used to persist movement.
        :return: None.
        """
        super().__init__()
        self.paired_items: List[PairedItem] | None = [paired_item for paired_item in
                                                      paired_items] if paired_items else None
        self.editor: DynamicBlockEditorGUI = editor
        self.var_factory = var_factory
        self.subsys = subsys
        self.mode = mode
        self.name: str = name
        self.api_object = api_object
        self.position_changed_callback = position_changed_callback
        self.is_signal_in: bool = bool(self.subsys.in_vars) and not bool(self.subsys.out_vars)

        self.name_item = QGraphicsTextItem(self.name, self)

        self.inputs: List[PortItem] = list()
        self.outputs: List[PortItem] = list()
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)
        self._last_valid_pos: QPointF = QPointF(self.pos())

        n_inputs = len(self.subsys.in_vars)
        n_outputs = len(self.subsys.out_vars)
        self.inputs = [PortItem(self, self.editor, True, i, n_inputs) for i in range(n_inputs)]
        self.outputs = [PortItem(self, self.editor, False, i, n_outputs) for i in range(n_outputs)]
        for port_item in self.inputs:
            port_item.recolour()
        for port_item in self.outputs:
            port_item.recolour()

        self.refresh_port_metadata()
        self._build_polygon()

    def recolour_mode(self) -> None:
        """Apply the active editor palette to this graphics item.

        :return: None.
        """
        self.name_item.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)
        self.setBrush(QBrush(self.editor.colors_palet.BLOCK_FILL))
        self.setPen(QPen(self.editor.colors_palet.BLOCK_BORDER, 1))

    def recolour(self, use_custom_color: bool = False) -> None:
        """Refresh this graphics item unless a custom colour must be preserved.

        :param use_custom_color: Whether an existing custom colour is preserved.
        :return: None.
        """
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def rect(self) -> QtCore.QRectF:
        """Return the local body rectangle represented by the polygon item.

        :return: Value produced by the graphics operation.
        """
        return self.polygon().boundingRect()

    def _build_polygon(self) -> None:
        """Rebuild the directional signal-tag polygon and its port positions.

        :return: None.
        """
        w = self._LABEL_W
        h = self._LABEL_H
        notch = self._NOTCH_DEPTH
        tip = self._TIP_BASE
        half = h / 2.0
        if self.is_signal_in:
            poly = QtGui.QPolygonF(list((QtCore.QPointF(w, 0.0), QtCore.QPointF(tip, 0.0), QtCore.QPointF(0.0, half), QtCore.QPointF(tip, h), QtCore.QPointF(w, h), QtCore.QPointF(w - notch, half),)))
        else:
            poly = QtGui.QPolygonF(list((QtCore.QPointF(0.0, 0.0), QtCore.QPointF(w - tip, 0.0), QtCore.QPointF(w, half), QtCore.QPointF(w - tip, h), QtCore.QPointF(0.0, h), QtCore.QPointF(notch, half),)))
        self.setPolygon(poly)
        self._position_name_and_ports()

    def _position_name_and_ports(self) -> None:
        """Position the signal name and endpoint around the current polygon.

        :return: None.
        """
        w = self._LABEL_W
        h = self._LABEL_H
        notch = self._NOTCH_DEPTH
        tip = self._TIP_BASE
        half = h / 2.0

        if self.is_signal_in:
            if self.inputs:
                port = self.inputs[0]
                port.setPos(0.0, half)
            else:
                pass
            body_left = tip
            body_right = w - notch
        else:
            if self.outputs:
                port = self.outputs[0]
                port.setPos(w, half)
            else:
                pass
            body_left = notch
            body_right = w - tip

        body_width = body_right - body_left
        name_width = self.name_item.boundingRect().width()
        name_height = self.name_item.boundingRect().height()
        name_x = body_left + (body_width - name_width) / 2.0
        self.name_item.setPos(name_x, half - name_height / 2.0)

        port: PortItem
        port_collection: List[PortItem]
        for port_collection in (self.inputs, self.outputs):
            for port in port_collection:
                if port.connections:
                    conn: ConnectionItem
                    for conn in port.connections:
                        conn.update_path()
                else:
                    pass

    def get_signal_var(self) -> Var | None:
        """
        Return the symbolic variable represented by this signal tag.

        :return: Input or output signal variable, or ``None`` for an invalid block.
        """
        if self.subsys is None:
            return None
        elif len(self.subsys.in_vars) == 1 and len(self.subsys.out_vars) == 0:
            return self.subsys.in_vars[0]
        elif len(self.subsys.out_vars) == 1 and len(self.subsys.in_vars) == 0:
            return self.subsys.out_vars[0]
        else:
            return None

    def refresh_variable_name(self) -> None:
        """
        Refresh the visible signal-pair label from its symbolic variable.

        :return: None.
        """
        signal_var: Var | None = self.get_signal_var()

        if signal_var is None:
            pass
        else:
            self.name = signal_var.name
            self.name_item.setPlainText(signal_var.name)
            self._position_name_and_ports()

    def set_paired_item(self, paired_item: PairedItem) -> None:
        """
        Add one associated signal tag without duplicating the relationship.

        :param paired_item: Signal tag belonging to the same logical pair.
        :return: None.
        """
        if paired_item is self:
            pass
        elif self.paired_items is None:
            self.paired_items = list((paired_item,))
        elif paired_item not in self.paired_items:
            self.paired_items.append(paired_item)
        else:
            pass

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        """Paint the graphics item using its current palette and interaction state.

        :param painter: Painter supplied by Qt.
        :param option: Qt style options for the item.
        :param widget: Optional target widget.
        :return: None.
        """
        polygon: QtGui.QPolygonF = self.polygon()
        border_color: QColor = EditorGraphicsCommonFeatures.BLOCK_BORDER_SELECTED if self.isSelected() else self.pen().color()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(border_color, 1.6))
        painter.setBrush(self.brush())
        painter.drawPolygon(polygon)

    def _refresh_local_port_metadata(self) -> None:
        """
        Refresh only this item, without recursively traversing paired tags.

        :return: None.
        """
        i: int
        port: PortItem
        variable_name: str

        if self.subsys is not None:
            for i, port in enumerate(self.inputs):
                port.base_var = self.subsys.in_vars[i]
                variable_name = self.subsys.in_vars[i].name
                port.setToolTip(_build_port_tooltip("Input", i, variable_name))

            for i, port in enumerate(self.outputs):
                port.base_var = self.subsys.out_vars[i]
                variable_name = self.subsys.out_vars[i].name
                port.setToolTip(_build_port_tooltip("Output", i, variable_name))
        else:
            pass

        self.refresh_variable_name()

    def refresh_port_metadata(self) -> None:
        """
        Refresh this signal tag and every associated tag exactly once.

        :return: None.
        """
        paired_item: PairedItem

        self._refresh_local_port_metadata()

        # Pair refresh must not remove and re-add relationship entries. The old
        # recursive implementation could leave asymmetric pair lists while one
        # endpoint was being disconnected and immediately reconnected.
        if self.paired_items is not None:
            for paired_item in self.paired_items:
                if paired_item is self:
                    pass
                else:
                    paired_item._refresh_local_port_metadata()
        else:
            pass

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """Apply the hover interaction state when the pointer enters the item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        QApplication.setOverrideCursor(Qt.CursorShape.OpenHandCursor)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """Restore the normal interaction state when the pointer leaves the item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        QApplication.restoreOverrideCursor()

    def _duplicate_paired_output(self, _checked: bool = False) -> None:
        """Create another output tag for this signal-pair identity.

        :param _checked: Unused QAction checked state supplied by Qt.
        :return: None.
        """
        duplicate_paired_item(self)

    def contextMenuEvent(self, event: QtWidgets.QGraphicsSceneContextMenuEvent) -> None:
        """Show the duplicate action for output-side signal tags.

        :param event: Incoming graphics-scene context-menu event.
        :return: None.
        """
        if not self.is_signal_in and self.paired_items is not None:
            menu: QMenu = QMenu()
            duplicate_action: QAction = QAction("Duplicate", menu)
            duplicate_action.triggered.connect(self._duplicate_paired_output)
            menu.addAction(duplicate_action)
            menu.exec(event.screenPos())
        else:
            super().contextMenuEvent(event)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Handle a graphics-scene mouse press for this item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            _notify_block_item_manual_route_drag(self, started=True)
        else:
            pass
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Finalize the current graphics interaction after mouse release.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        super().mouseReleaseEvent(event)
        _notify_block_item_manual_route_drag(self, started=False)
        _finalize_block_drop(self)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        """Process one Qt graphics-item state change and propagate dependent geometry.

        :param change: Qt graphics-item change kind.
        :param value: Opaque value associated with the Qt change.
        :return: Value produced by the graphics operation.
        """
        value = _handle_block_item_change(self, change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.position_changed_callback is not None:
                self.position_changed_callback(value.x(), value.y())
            else:
                pass
            port: PortItem
            port_collection: List[PortItem]
            for port_collection in (self.inputs, self.outputs):
                for port in port_collection:
                    if port.connections:
                        conn: ConnectionItem
                        for conn in port.connections:
                            conn.update_path()
                    else:
                        pass
        else:
            pass
        return super().itemChange(change, value)

    def select_group(self) -> None:
        """Select every graphics item belonging to the same signal-pair group.

        :return: None.
        """
        scene = self.scene()
        if scene is None:
            return
        else:
            pass

        scene.clearSelection()
        self.setSelected(True)

        if self.paired_items:
            for item in self.paired_items:
                if item is not None:
                    item.setSelected(True)
                else:
                    pass
        else:
            pass


class BlockItem(QGraphicsRectItem):
    """Compact graphics item representing one nested symbolic subsystem."""

    __slots__ = ()

    def __init__(self,
                 var_factory: VarFactory,
                 name: str,
                 editor: DynamicBlockEditorGUI,
                 mode: DynamicSimulationMode,
                 api_object: ALL_DEV_TYPES,
                 position_changed_callback: BlockPositionChangedCallback | None = None
                 ) -> None:
        """Initialize the graphics object and its interaction state.

        :param var_factory: Factory that owns symbolic variables.
        :param name: Visible block name.
        :param editor: Owning dynamic editor.
        :param mode: Dynamic simulation mode.
        :param api_object: Static network device associated with the model.
        :param position_changed_callback: Typed callback used to persist movement.
        :return: None.
        """
        super().__init__(0, 0, 80, 40)
        self.editor: DynamicBlockEditorGUI = editor
        self.var_factory: VarFactory = var_factory
        self.api_object = api_object
        self.mode = mode
        self.name: str = name
        self.name_item = QGraphicsTextItem(self.name, self)
        self.position_changed_callback = position_changed_callback
        self.resize_handle: ResizeHandle | None = None
        self.resizing_from_handle: bool = False
        self.subsys: Block | None = None

        self.inputs: List[PortItem] = list()
        self.outputs: List[PortItem] = list()
        self.input_labels: List[QGraphicsTextItem] = list()
        self.output_labels: List[QGraphicsTextItem] = list()
        self._validation_highlighted: bool = False

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)
        self._last_valid_pos: QPointF = QPointF(self.pos())

    def recolour_mode(self) -> None:
        """Apply the active editor palette to this graphics item.

        :return: None.
        """
        self.name_item.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)
        self.setBrush(QBrush(self.editor.colors_palet.BLOCK_FILL))
        self.setPen(QPen(self.editor.colors_palet.BLOCK_BORDER, 1))

    def recolour(self, use_custom_color: bool = False) -> None:
        """Refresh this graphics item unless a custom colour must be preserved.

        :param use_custom_color: Whether an existing custom colour is preserved.
        :return: None.
        """
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def set_subsystem(self, block: Block) -> None:
        """Associate this graphics item with its authoritative symbolic block.

        :param block: Authoritative symbolic block.
        :return: None.
        """
        self.subsys = block

    def refresh_block_name(self) -> None:
        """
        Refresh the visible block name from the authoritative symbolic block.

        :return: None.
        """
        if self.subsys is not None:
            # Compact block items also mirror the symbolic block name locally so
            # the rendered label stays consistent after a rename from the editor.
            self.name = self.subsys.name
            self.name_item.setPlainText(self.name)
            self.resize_to_content()
            self._center_name()
        else:
            pass

    def build_item(self) -> None:
        """Build ports, labels, and resize controls from the symbolic block.

        :return: None.
        """
        if self.subsys is not None:
            self.name_item = QGraphicsTextItem(self.name, self)

            n_inputs: int = len(self.subsys.in_vars)
            n_outputs: int = len(self.subsys.out_vars)
            self.inputs = [PortItem(self, self.editor, True, i, n_inputs) for i in range(n_inputs)]
            self.outputs = [PortItem(self, self.editor, False, i, n_outputs) for i in range(n_outputs)]
            for port_item in self.inputs:
                port_item.recolour()
            for port_item in self.outputs:
                port_item.recolour()
            self.refresh_port_metadata()

            self.resize_to_content()
        else:
            pass

    def create_port_label_item(self) -> QGraphicsTextItem:
        """Create one non-interactive text label for a block port.

        :return: Value produced by the graphics operation.
        """
        label_item: QGraphicsTextItem = QGraphicsTextItem("", self)
        label_item.setDefaultTextColor(self.editor.colors_palet.PORT_LABEL_COLOR)
        label_item.setZValue(4)
        return label_item

    def get_minimum_block_size(self) -> tuple[float, float]:

        """Compute the minimum dimensions required by ports and labels.

        :return: Value produced by the graphics operation.
        """
        port_rows: int = max(len(self.inputs), len(self.outputs), 1)
        min_height: float = max(
            EditorGraphicsCommonFeatures.BLOCK_COMPACT_MIN_HEIGHT,
            EditorGraphicsCommonFeatures.BLOCK_COMPACT_HEADER_HEIGHT + EditorGraphicsCommonFeatures.BLOCK_COMPACT_PORT_SECTION_PADDING +
            port_rows * EditorGraphicsCommonFeatures.BLOCK_COMPACT_PORT_ROW_HEIGHT
        )
        name_width = len(self.name) * 5
        max_label_length = 0
        if self.subsys:
            var: Var
            for var in self.subsys.in_vars:
                max_label_length = max(max_label_length, len(var.name))
            for var in self.subsys.out_vars:
                max_label_length = max(max_label_length, len(var.name))
        else:
            pass
        port_width = max_label_length * 5
        min_width = max(EditorGraphicsCommonFeatures.BLOCK_COMPACT_MIN_WIDTH, name_width + 10, port_width + 20)
        return min_width, min_height

    def resize_to_content(self) -> None:
        """Resize the block to fit its current ports, labels, and title.

        :return: None.
        """
        self.prepareGeometryChange()
        min_width: float
        min_height: float
        min_width, min_height = self.get_minimum_block_size()
        QGraphicsRectItem.setRect(self, 0, 0, min_width, min_height)
        self.update_ports()
        # self.update_handle_position()
        self._center_name()

    def _center_name(self) -> None:
        """Centre the block title below the current body rectangle.

        :return: None.
        """
        if self.name_item is None:
            return
        else:
            pass
        rect = self.rect()
        text_width = self.name_item.boundingRect().width()
        text_height = self.name_item.boundingRect().height()
        self.name_item.setPos(
            (rect.width() - text_width) / 2,
            (rect.height() - text_height) / 2,
        )

    def refresh_port_metadata(self) -> None:
        """Synchronize visible port variables, labels, and tooltips.

        :return: None.
        """
        if self.subsys is not None:
            i: int
            port: PortItem
            label_item: QGraphicsTextItem
            variable_name: str
            for i, port in enumerate(self.inputs):
                port.base_var = self.subsys.in_vars[i]
                variable_name = self.subsys.in_vars[i].name
                port.setToolTip(_build_port_tooltip("Input", i, variable_name))
                if i < len(self.input_labels):
                    label_item = self.input_labels[i]
                    label_item.setPlainText(
                        truncate_port_label(variable_name, EditorGraphicsCommonFeatures.PORT_LABEL_MAX_CHARS))
                else:
                    pass

            for i, port in enumerate(self.outputs):
                port.base_var = self.subsys.out_vars[i]
                variable_name = self.subsys.out_vars[i].name
                port.setToolTip(_build_port_tooltip("Output", i, variable_name))
                if i < len(self.output_labels):
                    label_item = self.output_labels[i]
                    label_item.setPlainText(
                        truncate_port_label(variable_name, EditorGraphicsCommonFeatures.PORT_LABEL_MAX_CHARS))
                else:
                    pass

            self.update_ports()

        else:
            pass

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        """Paint the graphics item using its current palette and interaction state.

        :param painter: Painter supplied by Qt.
        :param option: Qt style options for the item.
        :param widget: Optional target widget.
        :return: None.
        """
        rect: QtCore.QRectF = self.rect()
        outer_rect: QtCore.QRectF = rect.adjusted(2, 2, -2, -2)
        body_rect: QtCore.QRectF = outer_rect
        radius: float = body_rect.height() / 2.0

        if self._validation_highlighted:
            border_color: QColor = EditorGraphicsCommonFeatures.VALIDATION_HICHLIGHTED_BORDER
        else:
            border_color = (
                EditorGraphicsCommonFeatures.BLOCK_BORDER_SELECTED
                if self.isSelected()
                else self.pen().color()
            )

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # body
        painter.setBrush(self.brush())
        painter.setPen(QPen(border_color, 1.6))
        painter.drawRoundedRect(body_rect, radius, radius)

    def set_validation_highlighted(self, val: bool) -> None:
        """
        Toggle the validation overlay state for this compact block item.

        :param val: Whether the block should be outlined as a validation issue.
        :return: None.
        """
        self._validation_highlighted = val
        self.update()

    def resize_block(self, width: float, height: float) -> None:
        """Resize the block while enforcing its content-derived minimum dimensions.

        :param width: Requested body width.
        :param height: Requested body height.
        :return: None.
        """
        pass

    def update_ports(self) -> None:
        """Position ports and labels and refresh their attached connection paths.

        :return: None.
        """
        block_height: float = self.rect().height()

        i: int
        port: PortItem
        for i, port in enumerate(self.inputs):
            input_spacing = block_height / (len(self.inputs) + 1)
            port.setPos(0, input_spacing * (i + 1))

        for i, port in enumerate(self.outputs):
            output_spacing = block_height / (len(self.outputs) + 1)
            port.setPos(self.rect().width(), output_spacing * (i + 1))

        label_item: QGraphicsTextItem
        for i, label_item in enumerate(self.input_labels):
            port = self.inputs[i]
            label_item.setPos(10.0, port.pos().y() - 6.0)

        for i, label_item in enumerate(self.output_labels):
            port = self.outputs[i]
            label_width: float = label_item.boundingRect().width()
            label_item.setPos(self.rect().width() - label_width - 10.0, port.pos().y() - 6.0)

        port_collection: List[PortItem]
        for port_collection in (self.inputs, self.outputs):
            for port in port_collection:
                if port.connections is not None:
                    conn: ConnectionItem
                    for conn in port.connections:
                        conn.update_path()
                else:
                    pass

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """Apply the hover interaction state when the pointer enters the item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        QApplication.setOverrideCursor(Qt.CursorShape.OpenHandCursor)
        self.update()

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        """Restore the normal interaction state when the pointer leaves the item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        QApplication.restoreOverrideCursor()
        self.update()

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Handle a graphics-scene mouse press for this item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            _notify_block_item_manual_route_drag(self, started=True)
        else:
            pass
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Finalize the current graphics interaction after mouse release.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        super().mouseReleaseEvent(event)
        _notify_block_item_manual_route_drag(self, started=False)
        _finalize_block_drop(self)

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """
        Open the modal block properties dialogue on a left-button double click.

        :param event: Incoming Qt event.
        :return: None.
        """
        if event.button() == Qt.MouseButton.LeftButton and self.subsys is not None:
            self.editor.request_open_block_properties(self.subsys)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        """Process one Qt graphics-item state change and propagate dependent geometry.

        :param change: Qt graphics-item change kind.
        :param value: Opaque value associated with the Qt change.
        :return: Value produced by the graphics operation.
        """
        value = _handle_block_item_change(self, change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.position_changed_callback is not None:
                self.position_changed_callback(value.x(), value.y())
            else:
                pass
            port: PortItem
            port_collection: List[PortItem]
            for port_collection in (self.inputs, self.outputs):
                for port in port_collection:
                    if port.connections:
                        conn: ConnectionItem
                        for conn in port.connections:
                            conn.update_path()
                    else:
                        pass
            return super().itemChange(change, value)
        else:
            return super().itemChange(change, value)



class ProtectedConnectionBlockItem(BlockItem):
    __slots__ = ()

    def get_interface_var(self) -> Var | None:
        """
        Return the single symbolic variable represented by this root oval.

        :return: Wrapped interface variable, or ``None`` for an invalid shape.
        """
        block_model: Block | None = self.subsys

        if block_model is None:
            return None
        elif len(block_model.in_vars) == 1 and len(block_model.out_vars) == 0:
            return block_model.in_vars[0]
        elif len(block_model.in_vars) == 0 and len(block_model.out_vars) == 1:
            return block_model.out_vars[0]
        else:
            return None


class UnOpItem(BlockItem):
    """Compact graphics item for one unary symbolic operation."""

    __slots__ = ()

    SIZE: float = 38.0
    RADIUS: float = 4.0

    _SYMBOL_TEXT: Dict[BlockType, str] = dict(((BlockType.CONST, "k"), (BlockType.ABS, "|x|"), (BlockType.INTEGRATOR, "∫"), (BlockType.POWER, "x^y"), (BlockType.SIN, "sin"), (BlockType.COS, "cos"), (BlockType.TAN, "tan"), (BlockType.EXP, "exp"), (BlockType.LOG, "ln"), (BlockType.LOG10, "log"), (BlockType.SQRT, "√"), (BlockType.ASIN, "asin"), (BlockType.ACOS, "acos"), (BlockType.ATAN, "atan"), (BlockType.SINH, "sinh"), (BlockType.COSH, "cosh"), (BlockType.TANH, "tanh"), (BlockType.REAL, "Re"), (BlockType.IMAG, "Im"), (BlockType.CONJ, "z*"), (BlockType.ANGLE, "∠"),))

    def __init__(self,
                 editor: DynamicBlockEditorGUI,
                 var_factory: VarFactory,
                 subsys: Block,
                 api_object: ALL_DEV_TYPES,
                 mode: DynamicSimulationMode,
                 block_type: BlockType,
                 name: str,
                 position_changed_callback: BlockPositionChangedCallback | None = None) -> None:
        """Initialize the graphics object and its interaction state.

        :param editor: Owning dynamic editor.
        :param var_factory: Factory that owns symbolic variables.
        :param subsys: Symbolic block represented by the item.
        :param api_object: Static network device associated with the model.
        :param mode: Dynamic simulation mode.
        :param block_type: Symbolic operation type.
        :param name: Visible block name.
        :param position_changed_callback: Typed callback used to persist movement.
        :return: None.
        """
        super().__init__(
            var_factory=var_factory,
            name=name,
            editor=editor,
            mode=mode,
            api_object=api_object,
            position_changed_callback=position_changed_callback,
        )
        self.subsys = subsys
        self.block_type: BlockType = block_type
        self.name_item.setVisible(False)
        self.build_item()

    def build_item(self) -> None:
        """Build ports, labels, and resize controls from the symbolic block.

        :return: None.
        """
        if self.subsys is None:
            return
        else:
            pass

        n_inputs: int = len(self.subsys.in_vars)
        n_outputs: int = len(self.subsys.out_vars)
        self.inputs = [PortItem(self, self.editor, True, i, n_inputs) for i in range(n_inputs)]
        self.outputs = [PortItem(self, self.editor, False, i, n_outputs) for i in range(n_outputs)]
        for port_item in self.inputs:
            port_item.recolour()
        for port_item in self.outputs:
            port_item.recolour()
        self.refresh_port_metadata()
        self.resize_to_content()

    def get_minimum_block_size(self) -> tuple[float, float]:
        """Compute the minimum dimensions required by ports and labels.

        :return: Value produced by the graphics operation.
        """
        return self.SIZE, self.SIZE

    def resize_to_content(self) -> None:
        """Resize the block to fit its current ports, labels, and title.

        :return: None.
        """
        self.prepareGeometryChange()
        QGraphicsRectItem.setRect(self, 0, 0, self.SIZE, self.SIZE)
        self.update_ports()

    def update_ports(self) -> None:
        """Position ports and labels and refresh their attached connection paths.

        :return: None.
        """
        rect = self.rect()
        center_y = rect.height() / 2.0

        if self.inputs:
            self.inputs[0].setPos(0.0, center_y)
        else:
            pass
        for port in self.inputs[1:]:
            port.setPos(0.0, center_y)

        if self.outputs:
            self.outputs[0].setPos(rect.width(), center_y)
        else:
            pass
        for port in self.outputs[1:]:
            port.setPos(rect.width(), center_y)

        port_collection: List[PortItem]
        for port_collection in (self.inputs, self.outputs):
            for port in port_collection:
                if port.connections:
                    conn: ConnectionItem
                    for conn in port.connections:
                        conn.update_path()
                else:
                    pass

    def _draw_center_symbol(self, painter: QPainter, body_rect: QtCore.QRectF) -> None:
        """Draw the unary-operation symbol inside the supplied body rectangle.

        :param painter: Painter supplied by Qt.
        :param body_rect: Value supplied for ``body_rect``.
        :return: None.
        """
        painter.setPen(QPen(self.editor.colors_palet.BLOCK_TITLE, 1.2))

        if self.block_type == BlockType.GAIN:
            triangle = QtGui.QPolygonF(list((QPointF(body_rect.left() + body_rect.width() * 0.33, body_rect.top() + body_rect.height() * 0.25), QPointF(body_rect.left() + body_rect.width() * 0.33, body_rect.bottom() - body_rect.height() * 0.25), QPointF(body_rect.right() - body_rect.width() * 0.25, body_rect.center().y()),)))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPolygon(triangle)
            return
        else:
            pass

        symbol = self._SYMBOL_TEXT.get(self.block_type, self.block_type.value)
        font = painter.font()
        point_size = 8.5
        if len(symbol) >= 4:
            point_size = 7.0
        elif len(symbol) == 3:
            point_size = 7.6
        else:
            pass
        font.setPointSizeF(point_size)
        painter.setFont(font)
        painter.drawText(body_rect, Qt.AlignmentFlag.AlignCenter, symbol)

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        """Paint the graphics item using its current palette and interaction state.

        :param painter: Painter supplied by Qt.
        :param option: Qt style options for the item.
        :param widget: Optional target widget.
        :return: None.
        """
        rect: QtCore.QRectF = self.rect()
        body_rect: QtCore.QRectF = rect.adjusted(2, 2, -2, -2)

        if self._validation_highlighted:
            border_color: QColor = EditorGraphicsCommonFeatures.VALIDATION_HICHLIGHTED_BORDER
        else:
            border_color = (
                EditorGraphicsCommonFeatures.BLOCK_BORDER_SELECTED
                if self.isSelected()
                else self.pen().color()
            )

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setBrush(self.brush())
        painter.setPen(QPen(border_color, 1.6))
        painter.drawRoundedRect(body_rect, self.RADIUS, self.RADIUS)
        self._draw_center_symbol(painter, body_rect)


class RoundBaseArithmeticOpItem(QGraphicsEllipseItem):
    """Circular graphics item for addition and subtraction expressions."""

    __slots__ = ()

    LABEL_OUTSET: float = 5.0

    def __init__(self,
                 subsys: Block,
                 var_factory: VarFactory,
                 block_type: BlockType,
                 editor: DynamicBlockEditorGUI,
                 position_changed_callback: BlockPositionChangedCallback | None = None) -> None:
        """Initialize the graphics object and its interaction state.

        :param subsys: Symbolic block represented by the item.
        :param var_factory: Factory that owns symbolic variables.
        :param block_type: Symbolic operation type.
        :param editor: Owning dynamic editor.
        :param position_changed_callback: Typed callback used to persist movement.
        :return: None.
        """
        size = 35.0
        super().__init__(-size / 2, -size / 2, size, size)
        self.block_type: BlockType = block_type
        self.subsys: Block = subsys
        self.var_factory: VarFactory = var_factory
        self.editor: DynamicBlockEditorGUI = editor
        self.inputs: List[PortItem] = list()
        self.outputs: List[PortItem] = list()
        self.input_labels: List[QGraphicsTextItem] = list()
        self._input_signs: List[str] = list()

        n_inputs = len(self.subsys.in_vars)
        if n_inputs > 3:
            raise ValueError("SumItem only supports up to 3 input ports")
        else:
            pass
        n_outputs = len(self.subsys.out_vars)

        for i in range(n_inputs):
            port = PortItem(self, self.editor, True, i, n_inputs)
            port.recolour()
            self.inputs.append(port)
            label = QGraphicsTextItem("", self)
            self.input_labels.append(label)

        for i in range(n_outputs):
            port = PortItem(self, self.editor, False, i, n_outputs)
            port.recolour()
            self.outputs.append(port)

        self._analyze_input_signs()
        self.update_ports()
        self.setZValue(2)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)
        self._last_valid_pos: QPointF = QPointF(self.pos())

    def recolour_mode(self) -> None:
        """Apply the active editor palette to this graphics item.

        :return: None.
        """
        for label in self.input_labels:
            label.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)
        self.setBrush(QBrush(self.editor.colors_palet.BLOCK_FILL))
        self.setPen(QPen(self.editor.colors_palet.BLOCK_BORDER, 1))

    def recolour(self, use_custom_color: bool = False) -> None:
        """Refresh this graphics item unless a custom colour must be preserved.

        :param use_custom_color: Whether an existing custom colour is preserved.
        :return: None.
        """
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def _walk_sum_expr(self, expr: Expr, sign: int, result: Dict[int, int]) -> None:
        """Traverse a symbolic sum and record the effective sign of each variable.

        :param expr: Symbolic expression being traversed.
        :param sign: Effective arithmetic sign.
        :param result: Mutable variable-sign lookup.
        :return: None.
        """
        if isinstance(expr, Var):
            result[expr.uid] = sign
        elif isinstance(expr, BinOp):
            if expr.op == "+":
                self._walk_sum_expr(expr.left, sign, result)
                self._walk_sum_expr(expr.right, sign, result)
            elif expr.op == "-":
                self._walk_sum_expr(expr.left, sign, result)
                self._walk_sum_expr(expr.right, -sign, result)
            else:
                pass
        elif isinstance(expr, UnOp):
            if expr.op == "-":
                self._walk_sum_expr(expr.operand, -sign, result)
            else:
                pass
        else:
            pass

    def _walk_product_expr(self, expr: Expr, label: str, result: Dict[int, str]) -> None:
        """Traverse a symbolic product and record numerator or denominator placement.

        :param expr: Symbolic expression being traversed.
        :param label: Value supplied for ``label``.
        :param result: Mutable variable-sign lookup.
        :return: None.
        """
        if isinstance(expr, Var):
            result[expr.uid] = label
        elif isinstance(expr, BinOp):
            if expr.op == "*":
                self._walk_product_expr(expr.left, "x", result)
                self._walk_product_expr(expr.right, "x", result)
            elif expr.op == "/":
                self._walk_product_expr(expr.left, "x", result)
                self._walk_product_expr(expr.right, "/", result)
            else:
                pass
        elif isinstance(expr, UnOp):
            self._walk_product_expr(expr.operand, label, result)
        else:
            pass

    def _analyze_input_signs(self) -> None:
        """Derive the sign or division marker displayed beside every input.

        :return: None.
        """
        self._input_signs = list()
        if not self.subsys.algebraic_eqs:
            return
        else:
            pass

        eq = self.subsys.algebraic_eqs[0]
        if not isinstance(eq, BinOp) or eq.op != "-":
            return
        else:
            pass

        out_var = self.subsys.algebraic_vars[0]

        if isinstance(eq.left, Var) and eq.left.uid == out_var.uid:
            expr = eq.right
        elif isinstance(eq.right, Var) and eq.right.uid == out_var.uid:
            expr = eq.left
        else:
            expr = eq.right

        if self.block_type == BlockType.SUM:
            sign_map: Dict[int, int] = dict()
            self._walk_sum_expr(expr, 1, sign_map)
            for var in self.subsys.in_vars:
                s = sign_map.get(var.uid, 1)
                self._input_signs.append("+" if s >= 0 else "-")

        elif self.block_type == BlockType.PRODUCT:
            label_map: Dict[int, str] = dict()
            self._walk_product_expr(expr, "x", label_map)
            for var in self.subsys.in_vars:
                self._input_signs.append(label_map.get(var.uid, "x"))
        else:
            pass

    def _get_label_outset_offset(self, port: PortItem) -> QPointF:
        """Compute the horizontal offset needed by an exterior input marker.

        :param port: Value supplied for ``port``.
        :return: Value produced by the graphics operation.
        """
        rect = self.rect()
        cx = rect.center().x()
        cy = rect.center().y()
        dx = port.pos().x() - cx
        dy = port.pos().y() - cy
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1e-6:
            return QPointF(0, 0)
        else:
            pass
        return QPointF(dx / length * self.LABEL_OUTSET,
                       dy / length * self.LABEL_OUTSET)

    def refresh_port_metadata(self) -> None:
        """Synchronize visible port variables, labels, and tooltips.

        :return: None.
        """
        if self.subsys is not None:
            i: int
            port: PortItem
            label_item: QGraphicsTextItem
            variable_name: str
            for i, port in enumerate(self.inputs):
                port.base_var = self.subsys.in_vars[i]
                variable_name = self.subsys.in_vars[i].name
                port.setToolTip(_build_port_tooltip("Input", i, variable_name))

            for i, port in enumerate(self.outputs):
                port.base_var = self.subsys.out_vars[i]
                variable_name = self.subsys.out_vars[i].name
                port.setToolTip(_build_port_tooltip("Output", i, variable_name))

        else:
            pass

    def update_ports(self) -> None:
        """Position ports and labels and refresh their attached connection paths.

        :return: None.
        """
        rect = self.rect()
        cx = rect.center().x()
        cy = rect.center().y()
        top = rect.top()
        left = rect.left()
        bottom = rect.bottom()
        right = rect.right()

        n_inputs = len(self.inputs)

        if n_inputs == 1:
            self.inputs[0].setRotation(0)
            self.inputs[0].setPos(left, cy)
        elif n_inputs == 2:
            self.inputs[0].setRotation(90)
            self.inputs[0].setPos(cx, top)
            self.inputs[1].setRotation(0)
            self.inputs[1].setPos(left, cy)
        elif n_inputs == 3:
            self.inputs[0].setRotation(90)
            self.inputs[0].setPos(cx, top)
            self.inputs[1].setRotation(0)
            self.inputs[1].setPos(left, cy)
            self.inputs[2].setRotation(-90)
            self.inputs[2].setPos(cx, bottom)
        else:
            pass

        for i, port in enumerate(self.outputs):
            port.setRotation(0)
            port.setPos(right, cy)

        for i, label in enumerate(self.input_labels):
            if i < len(self._input_signs):
                label.setPlainText(self._input_signs[i])
            else:
                pass
            port = self.inputs[i]

            rect = label.boundingRect()
            center = port.pos() - self._get_label_outset_offset(port)
            label.setPos(
                center.x() - rect.width() / 2,
                center.y() - rect.height() / 2,
            )

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        """Paint the graphics item using its current palette and interaction state.

        :param painter: Painter supplied by Qt.
        :param option: Qt style options for the item.
        :param widget: Optional target widget.
        :return: None.
        """
        rect = self.rect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawEllipse(rect)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Handle a graphics-scene mouse press for this item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            _notify_block_item_manual_route_drag(self, started=True)
        else:
            pass
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Finalize the current graphics interaction after mouse release.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        super().mouseReleaseEvent(event)
        _notify_block_item_manual_route_drag(self, started=False)
        _finalize_block_drop(self)

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """
        Open the modal properties editor for a compact arithmetic block.

        :param event: Incoming Qt event.
        :return: None.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.editor.request_open_block_properties(self.subsys)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        """Process one Qt graphics-item state change and propagate dependent geometry.

        :param change: Qt graphics-item change kind.
        :param value: Opaque value associated with the Qt change.
        :return: Value produced by the graphics operation.
        """
        value = _handle_block_item_change(self, change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            port_collection: List[PortItem]
            for port_collection in (self.inputs, self.outputs):
                for port in port_collection:
                    if port.connections:
                        for conn in port.connections:
                            conn.update_path()
                    else:
                        pass
            return super().itemChange(change, value)
        else:
            return super().itemChange(change, value)


class RectBaseArithmeticOpItem(QGraphicsRectItem):
    """Rectangular graphics item for product and division expressions."""

    __slots__ = ()

    def __init__(self,
                 subsys: Block,
                 var_factory: VarFactory,
                 block_type: BlockType,
                 editor: DynamicBlockEditorGUI,
                 position_changed_callback: BlockPositionChangedCallback | None = None) -> None:
        """Initialize the graphics object and its interaction state.

        :param subsys: Symbolic block represented by the item.
        :param var_factory: Factory that owns symbolic variables.
        :param block_type: Symbolic operation type.
        :param editor: Owning dynamic editor.
        :param position_changed_callback: Typed callback used to persist movement.
        :return: None.
        """
        n_inputs = len(subsys.in_vars)
        n_outputs = len(subsys.out_vars)
        width = 50.0
        height = max(60.0, n_inputs * 28.0)
        super().__init__(0, 0, width, height)
        self.block_type: BlockType = block_type
        self.subsys: Block = subsys
        self.var_factory: VarFactory = var_factory
        self.editor: DynamicBlockEditorGUI = editor
        self.inputs: List[PortItem] = list()
        self.outputs: List[PortItem] = list()
        self.input_labels: List[QGraphicsTextItem] = list()
        self._input_signs: List[str] = list()

        for i in range(n_inputs):
            port = PortItem(self, self.editor, True, i, n_inputs)
            port.recolour()
            self.inputs.append(port)

            label = QGraphicsTextItem("", self)
            label.setDefaultTextColor(QColor("#173042"))
            self.input_labels.append(label)

        for i in range(n_outputs):
            port = PortItem(self, self.editor, False, i, n_outputs)
            self.outputs.append(port)
            port.recolour()

        self._analyze_input_signs()
        self.update_ports()

        self.setZValue(2)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)
        self._last_valid_pos: QPointF = QPointF(self.pos())

    def recolour_mode(self) -> None:
        """Apply the active editor palette to this graphics item.

        :return: None.
        """
        for label in self.input_labels:
            label.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)
        self.setBrush(QBrush(self.editor.colors_palet.BLOCK_FILL))
        self.setPen(QPen(self.editor.colors_palet.BLOCK_BORDER, 1))

    def recolour(self, use_custom_color: bool = False) -> None:
        """Refresh this graphics item unless a custom colour must be preserved.

        :param use_custom_color: Whether an existing custom colour is preserved.
        :return: None.
        """
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def _walk_sum_expr(self, expr: Expr, sign: int, result: Dict[int, int]) -> None:
        """Traverse a symbolic sum and record the effective sign of each variable.

        :param expr: Symbolic expression being traversed.
        :param sign: Effective arithmetic sign.
        :param result: Mutable variable-sign lookup.
        :return: None.
        """
        if isinstance(expr, Var):
            result[expr.uid] = sign
        elif isinstance(expr, BinOp):
            if expr.op == "+":
                self._walk_sum_expr(expr.left, sign, result)
                self._walk_sum_expr(expr.right, sign, result)
            elif expr.op == "-":
                self._walk_sum_expr(expr.left, sign, result)
                self._walk_sum_expr(expr.right, -sign, result)
            else:
                pass
        elif isinstance(expr, UnOp):
            if expr.op == "-":
                self._walk_sum_expr(expr.operand, -sign, result)
            else:
                pass
        else:
            pass

    def _walk_product_expr(self, expr: Expr, label: str, result: Dict[int, str]) -> None:
        """Traverse a symbolic product and record numerator or denominator placement.

        :param expr: Symbolic expression being traversed.
        :param label: Value supplied for ``label``.
        :param result: Mutable variable-sign lookup.
        :return: None.
        """
        if isinstance(expr, Var):
            result[expr.uid] = label
        elif isinstance(expr, BinOp):
            if expr.op == "*":
                self._walk_product_expr(expr.left, "x", result)
                self._walk_product_expr(expr.right, "x", result)
            elif expr.op == "/":
                self._walk_product_expr(expr.left, "x", result)
                self._walk_product_expr(expr.right, "/", result)
            else:
                pass
        elif isinstance(expr, UnOp):
            self._walk_product_expr(expr.operand, label, result)
        else:
            pass

    def _analyze_input_signs(self) -> None:
        """Derive the sign or division marker displayed beside every input.

        :return: None.
        """
        self._input_signs = list()
        if not self.subsys.algebraic_eqs:
            return
        else:
            pass

        eq = self.subsys.algebraic_eqs[0]
        if not isinstance(eq, BinOp) or eq.op != "-":
            return
        else:
            pass

        out_var = self.subsys.algebraic_vars[0]

        if isinstance(eq.left, Var) and eq.left.uid == out_var.uid:
            expr = eq.right
        elif isinstance(eq.right, Var) and eq.right.uid == out_var.uid:
            expr = eq.left
        else:
            expr = eq.right

        if self.block_type == BlockType.SUM:
            sign_map: Dict[int, int] = dict()
            self._walk_sum_expr(expr, 1, sign_map)
            for var in self.subsys.in_vars:
                s = sign_map.get(var.uid, 1)
                self._input_signs.append("+" if s >= 0 else "-")

        elif self.block_type == BlockType.PRODUCT:
            label_map: Dict[int, str] = dict()
            self._walk_product_expr(expr, "x", label_map)
            for var in self.subsys.in_vars:
                self._input_signs.append(label_map.get(var.uid, "x"))
        else:
            pass

    def refresh_port_metadata(self) -> None:
        """Synchronize visible port variables, labels, and tooltips.

        :return: None.
        """
        if self.subsys is not None:
            i: int
            port: PortItem
            label_item: QGraphicsTextItem
            variable_name: str
            for i, port in enumerate(self.inputs):
                port.base_var = self.subsys.in_vars[i]
                variable_name = self.subsys.in_vars[i].name
                port.setToolTip(_build_port_tooltip("Input", i, variable_name))

            for i, port in enumerate(self.outputs):
                port.base_var = self.subsys.out_vars[i]
                variable_name = self.subsys.out_vars[i].name
                port.setToolTip(_build_port_tooltip("Output", i, variable_name))

        else:
            pass

    def update_ports(self) -> None:
        """Position ports and labels and refresh their attached connection paths.

        :return: None.
        """
        rect = self.rect()
        w = rect.width()
        h = rect.height()
        n_inputs = len(self.inputs)

        for i, port in enumerate(self.inputs):
            spacing = h / (n_inputs + 1)
            port.setRotation(0)
            port.setPos(0, spacing * (i + 1))

        for i, port in enumerate(self.outputs):
            port.setRotation(0)
            port.setPos(w, h / 2)

        for i, label in enumerate(self.input_labels):
            if i < len(self._input_signs):
                label.setPlainText(self._input_signs[i])
            else:
                pass
            port = self.inputs[i]
            tw = label.boundingRect().width()
            th = label.boundingRect().height()
            label.setPos(port.pos().x() + 2.0, port.pos().y() - th / 2)

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        """Paint the graphics item using its current palette and interaction state.

        :param painter: Painter supplied by Qt.
        :param option: Qt style options for the item.
        :param widget: Optional target widget.
        :return: None.
        """
        rect = self.rect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(rect, 6.0, 6.0)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Handle a graphics-scene mouse press for this item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            _notify_block_item_manual_route_drag(self, started=True)
        else:
            pass
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Finalize the current graphics interaction after mouse release.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        super().mouseReleaseEvent(event)
        _notify_block_item_manual_route_drag(self, started=False)
        _finalize_block_drop(self)

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """
        Open the modal properties editor for an arithmetic block.

        :param event: Incoming Qt event.
        :return: None.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.editor.request_open_block_properties(self.subsys)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        """Process one Qt graphics-item state change and propagate dependent geometry.

        :param change: Qt graphics-item change kind.
        :param value: Opaque value associated with the Qt change.
        :return: Value produced by the graphics operation.
        """
        value = _handle_block_item_change(self, change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            port_collection: List[PortItem]
            for port_collection in (self.inputs, self.outputs):
                for port in port_collection:
                    if port.connections:
                        for conn in port.connections:
                            conn.update_path()
                    else:
                        pass
            return super().itemChange(change, value)
        else:
            return super().itemChange(change, value)


class GraphicsView(QGraphicsView):
    """Graphics view providing zoom, pan, and fit-to-content interactions."""

    __slots__ = ()

    ZOOM_FACTOR: float = 1.15

    def __init__(self, scene: QGraphicsScene) -> None:
        """Initialize the graphics object and its interaction state.

        :param scene: Graphics scene displayed by the view.
        :return: None.
        """
        super().__init__(scene)
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.IntersectsItemShape)
        self._panning: bool = False
        self._pan_start: QPointF = QPointF()

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """Convert the mouse-wheel direction into a scene zoom operation.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        self.apply_zoom(event.angleDelta().y() > 0)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle a graphics-scene mouse press for this item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            if event.button() == Qt.MouseButton.LeftButton and bool(
                    event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            else:
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle pointer movement for dragging or resizing this item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        if self._panning:
            delta: QPointF = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y()))
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """Finalize the current graphics interaction after mouse release.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def apply_zoom(self, zoom_in: bool) -> None:
        """Scale the view around the pointer in the requested direction.

        :param zoom_in: Whether to zoom in instead of out.
        :return: None.
        """
        zoom_factor: float = self.ZOOM_FACTOR if zoom_in else 1.0 / self.ZOOM_FACTOR
        self.scale(zoom_factor, zoom_factor)

    def zoom_in(self) -> None:
        """Increase the current graphics-view scale by one step.

        :return: None.
        """
        self.apply_zoom(True)

    def zoom_out(self) -> None:
        """Decrease the current graphics-view scale by one step.

        :return: None.
        """
        self.apply_zoom(False)

    def center_items(self) -> None:
        """Fit selected blocks, or all blocks, inside the current viewport.

        :return: None.
        """
        target_items: List[QGraphicsItem] = self.scene().selectedItems()
        block_items: List[QGraphicsItem] = list()

        if len(target_items) == 0:
            item: QGraphicsItem
            for item in self.scene().items():
                if isinstance(item, (BlockItem, GenericBlockItem)):
                    block_items.append(item)
                else:
                    pass
            target_items = block_items
        else:
            target_items = [item for item in target_items if isinstance(item, (BlockItem, GenericBlockItem))]

        if len(target_items) > 0:
            target_rect: QtCore.QRectF = QtCore.QRectF()
            item: QGraphicsItem
            for item in target_items:
                if target_rect.isNull():
                    target_rect = item.sceneBoundingRect()
                else:
                    target_rect = target_rect.united(item.sceneBoundingRect())

            margin_x = max(target_rect.width() * 0.08, 30.0)
            margin_y = max(target_rect.height() * 0.08, 30.0)
            target_rect = target_rect.adjusted(-margin_x, -margin_y, margin_x, margin_y)
            self.fitInView(target_rect, Qt.AspectRatioMode.KeepAspectRatio)
        else:
            pass


class DiagramScene(QGraphicsScene):
    """Scene coordinating block selection, wiring, and context actions."""

    __slots__ = ()

    def __init__(self, editor: "DynamicBlockEditorGUI") -> None:
        """Initialize the graphics object and its interaction state.

        :param editor: Owning dynamic editor.
        :return: None.
        """
        super().__init__()
        self.editor: DynamicBlockEditorGUI | None = editor
        self.temp_line: QGraphicsPathItem | None = None
        self.source_port: PortItem | BranchingItem | None = None
        self.context_item: BlockItem | GenericBlockItem | ConnectionItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem | PairedItem | None = None

    def prepare_to_delete(self) -> None:
        """
        Break Python references between scene items before Qt destroys them.

        ``QGraphicsScene.clear()`` deletes its C++ items immediately.  The
        corresponding Python wrappers can nevertheless remain alive when the
        editor graph contains cycles such as ``port -> connection -> port`` or
        ``item -> editor -> scene``.  If cyclic garbage collection later
        finalizes one of those stale wrappers, PySide can attempt to touch an
        already-deleted C++ object.  Detaching the graph first gives Qt and
        Python the same destruction order.

        :return: None.
        """
        scene_items: list[QGraphicsItem] = list(self.items())

        item: QGraphicsItem
        for item in scene_items:
            if isinstance(item, (PortItem, BranchingItem)):
                item.connections = None
            else:
                pass

        for item in scene_items:
            if isinstance(item, ConnectionItem):
                item.editor = None
                item.diagram = None
                item.source_port = None
                item.target_port = None
                item._drag_start_scene_pos = None
            elif isinstance(item, ElbowItem):
                item.connection_item = None
            elif isinstance(item, BranchingItem):
                item.editor = None
                item.subsystem = None
                item.owner_connection = None
                item.base_var = None
            elif isinstance(item, PortItem):
                item.editor = None
                item.subsystem = None
                item.base_var = None
            elif isinstance(item, ResizeHandle):
                item.editor = None
                item.block = None
            elif isinstance(item, (BlockItem,
                                   GenericBlockItem,
                                   PairedItem,
                                   RoundBaseArithmeticOpItem,
                                   RectBaseArithmeticOpItem)):
                item.editor = None
                item.inputs.clear()
                item.outputs.clear()
                item.position_changed_callback = None
                if isinstance(item, (BlockItem, GenericBlockItem)):
                    item.resize_handle = None
                    item.input_labels.clear()
                    item.output_labels.clear()
                elif isinstance(item, PairedItem):
                    item.paired_items = None
                else:
                    item.input_labels.clear()
            else:
                pass

        self.temp_line = None
        self.source_port = None
        self.context_item = None
        self.editor = None
        self.clear()

    def change_item_fill_color(self,
                               item: BlockItem | GenericBlockItem | ConnectionItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem | PairedItem) -> None:
        """Open the colour picker and apply a custom fill to the context item.

        :param item: Graphics item being inspected.
        :return: None.
        """
        new_color: QColor = QColorDialog.getColor()

        if new_color.isValid():
            if isinstance(item, GenericBlockItem):
                if item.subsys is not None:
                    brush: QBrush = item.brush()
                    brush.setColor(new_color)
                    item.setBrush(brush)
                    self.update()

                    if item.subsys.uid in self.editor.diagram.node_data:
                        self.editor.diagram.node_data[item.subsys.uid].color = new_color.name()
                    else:
                        pass
                else:
                    pass
            elif isinstance(item, ConnectionItem):
                pen: QPen = item.pen()
                pen.setColor(new_color)
                item.setPen(pen)
                self.update()

                if item.uid in self.editor.diagram.con_data:
                    self.editor.diagram.con_data[item.uid].color = new_color.name()
                else:
                    pass
            else:
                pass
        else:
            pass

    def remove_context_item(self) -> None:
        """Remove the graphics item selected by the scene context menu.

        :return: None.
        """
        if self.context_item is not None:
            self.editor.remove_item(self.context_item)
        else:
            pass

    def recolor_context_item(self) -> None:
        """Reapply the active palette to the scene context item.

        :return: None.
        """
        if self.context_item is not None:
            self.change_item_fill_color(self.context_item)
        else:
            pass


    def rename_context_item(self) -> None:
        """
        Rename the current context item through the editor controller.

        :return: None.
        """
        if isinstance(self.context_item, ProtectedConnectionBlockItem):
            interface_var: Var | None = self.context_item.get_interface_var()
            if interface_var is not None:
                self.editor.rename_variable_item(self.context_item)
            else:
                self.editor.rename_block_item(self.context_item)
        elif isinstance(self.context_item, BlockItem):
            self.editor.rename_block_item(self.context_item)
        elif isinstance(self.context_item, GenericBlockItem):
            self.editor.rename_block_item(self.context_item)
        else:
            pass


    def contextMenuEvent(self, event: QtWidgets.QGraphicsSceneContextMenuEvent) -> None:
        """
        Show the context menu for one diagram item.

        :param event: Qt context-menu event.
        :return: None.
        """
        item: QGraphicsItem
        for item in self.items(event.scenePos()):
            if isinstance(
                    item,
                    (GenericBlockItem, BlockItem, ConnectionItem,
                     RoundBaseArithmeticOpItem, RectBaseArithmeticOpItem, UnOpItem),
            ):
                self.context_item = item
                menu: QMenu = QMenu()
                is_variable_item: bool = (
                    isinstance(item, ProtectedConnectionBlockItem)
                    and item.get_interface_var() is not None
                )
                remove_action: QAction | None
                color_action: QAction | None
                rename_action: QAction | None

                # Root interface ovals are part of the device contract and can
                # only be renamed from this menu.
                if is_variable_item:
                    remove_action = None
                    color_action = None
                else:
                    remove_action = QAction("Remove", menu)
                    menu.addAction(remove_action)
                    color_action = QAction("Change Color", menu)
                    menu.addAction(color_action)

                if isinstance(item, (GenericBlockItem, BlockItem)):
                    if is_variable_item:
                        rename_action = QAction("Change Variable Name", menu)
                    else:
                        rename_action = QAction("Change Name", menu)
                    menu.addAction(rename_action)
                else:
                    rename_action = None

                selected_action: QAction | None = menu.exec(event.screenPos())
                if remove_action is not None and selected_action is remove_action:
                    self.remove_context_item()
                elif color_action is not None and selected_action is color_action:
                    self.recolor_context_item()
                elif rename_action is not None and selected_action is rename_action:
                    self.rename_context_item()
                else:
                    pass

                self.context_item = None
                return
            elif isinstance(item, PairedItem):
                self.context_item = item
                menu = QMenu()
                remove_action = QAction("Remove", menu)
                menu.addAction(remove_action)
                duplicate_action: QAction = QAction("Duplicate", menu)
                menu.addAction(duplicate_action)
                color_action = QAction("Change Color", menu)
                menu.addAction(color_action)

                selected_action = menu.exec(event.screenPos())
                if selected_action is remove_action:
                    self.remove_context_item()
                elif selected_action is duplicate_action:
                    duplicate_paired_item(item)
                elif selected_action is color_action:
                    self.recolor_context_item()
                else:
                    pass

                self.context_item = None
                return
            else:
                pass

        super().contextMenuEvent(event)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Handle a graphics-scene mouse press for this item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        item: QGraphicsItem

        for item in self.items(event.scenePos()):
            if isinstance(item, PortItem):
                if not item.is_input:
                    self.source_port = item
                    path: QPainterPath = QPainterPath(item.scenePos())
                    pen: QPen = QPen(QColor(self.editor.colors_palet.WIRE_COLOR), 1, Qt.PenStyle.DashLine)
                    self.temp_line = self.addPath(path, pen)
                    return
                else:
                    pass

            else:
                pass

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Handle pointer movement for dragging or resizing this item.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        if self.temp_line is not None:
            if self.source_port is not None:
                start: QPointF = self.source_port.scenePos()
                end: QPointF = event.scenePos()
                path: QPainterPath = build_orthogonal_connection_path(
                    start,
                    end,
                    EditorGraphicsCommonFeatures.WIRE_TERMINAL_STUB_LENGTH,
                )
                self.temp_line.setPath(path)
            else:
                pass
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Finalize the current graphics interaction after mouse release.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        if self.temp_line is not None:
            if self.source_port is not None:
                item: QGraphicsItem
                for item in self.items(event.scenePos()):
                    if isinstance(item, PortItem):
                        if item.is_input and not item.is_connected():
                            self.connect_ports(self.source_port, item)
                            break
                        else:
                            pass
                    else:
                        pass
            else:
                pass

            self.removeItem(self.temp_line)
            self.temp_line = None
            self.source_port = None
            self.editor.mark_unapplied_changes()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Open the properties editor for the block under a double click.

        :param event: Incoming Qt graphics event.
        :return: None.
        """
        for item in self.items(event.scenePos()):
            if isinstance(item, PairedItem):
                item.select_group()
                event.accept()
                return
            else:
                pass
        super().mouseDoubleClickEvent(event)

    def connect_ports(
            self,
            source_port: PortItem | BranchingItem,
            target_port: PortItem,
    ) -> None:
        """
        Create one live graphical and symbolic port connection.

        :param source_port: Source output port.
        :param target_port: Destination input port.
        :return: None.
        """
        if isinstance(source_port, BranchingItem):
            return
        else:
            pass

        source_block: BlockItem | GenericBlockItem | PairedItem | \
            RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem = source_port.subsystem
        target_block: BlockItem | GenericBlockItem | PairedItem | \
            RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem = target_port.subsystem

        if source_block.subsys is not None and target_block.subsys is not None:
            connection: ConnectionItem = ConnectionItem(
                source_port=source_port,
                target_port=target_port,
                diagram=self.editor.diagram,
                editor=self.editor,
            )

            # The editor controller owns symbolic registration, persistence,
            # endpoint refresh, and routing for every connection lifecycle.
            self.editor.attach_new_connection_item(item=connection)
        else:
            pass
