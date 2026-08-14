# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import math
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QBrush, QPainter, QPainterPath, QPen, QAction, QPolygonF
from PySide6.QtWidgets import QAbstractGraphicsShapeItem, QApplication, QColorDialog, QGraphicsEllipseItem, \
    QGraphicsItem, \
    QGraphicsPathItem, QGraphicsPolygonItem, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem, \
    QGraphicsView, QMenu, QWidget

from PySide6.QtCore import Signal

import VeraGrid.ThirdParty.darkdetect as darkdetect
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import BlockType
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Expr, BinOp, UnOp
from VeraGridEngine.enumerations import DynamicSimulationMode
if TYPE_CHECKING:
    from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI


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
        out_vars=list([canonical_var]),
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
        paired_items=list([signal_input_item]),
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
        signal_output_items=list([new_item]),
    )

    editor.mark_unapplied_changes()
    return new_item


def truncate_port_label(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    else:
        return text[:max_chars]


def build_orthogonal_connection_path(start: QPointF, end: QPointF, elbow_offset: float) -> QPainterPath:
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
    return item.__class__.__name__ in {
        "GenericBlockItem",
        "PairedItem",
        "BlockItem",
        "ProtectedConnectionBlockItem",
        "UnOpItem",
        "RoundBaseArithmeticOpItem",
        "RectBaseArithmeticOpItem",
    }


def _expanded_item_scene_rect(item: QGraphicsItem, pos: QPointF, margin: float) -> QtCore.QRectF:
    delta = pos - item.pos()
    return item.sceneBoundingRect().translated(delta).adjusted(-margin, -margin, margin, margin)


def _position_collides_with_blocks(item: QGraphicsItem, pos: QPointF, margin: float) -> bool:
    scene = item.scene()
    if scene is None:
        return False

    candidate_rect = _expanded_item_scene_rect(item, pos, margin)
    other: QGraphicsItem
    for other in scene.items(candidate_rect):
        if other is item or not _is_dynamic_block_item(other):
            continue
        if other.parentItem() is not None:
            continue
        if candidate_rect.intersects(other.sceneBoundingRect().adjusted(-margin, -margin, margin, margin)):
            return True
    return False


def _resolve_non_overlapping_position(item: QGraphicsItem,
                                      proposed_pos: QPointF,
                                      margin: float = 6.0) -> QPointF:
    if item.scene() is None:
        return proposed_pos

    current_pos = item.pos()
    if not _position_collides_with_blocks(item, proposed_pos, margin):
        return proposed_pos

    dx = proposed_pos.x() - current_pos.x()
    dy = proposed_pos.y() - current_pos.y()
    axis_candidates: List[QPointF]
    if abs(dx) >= abs(dy):
        axis_candidates = [
            QPointF(proposed_pos.x(), current_pos.y()),
            QPointF(current_pos.x(), proposed_pos.y()),
        ]
    else:
        axis_candidates = [
            QPointF(current_pos.x(), proposed_pos.y()),
            QPointF(proposed_pos.x(), current_pos.y()),
        ]

    candidate: QPointF
    for candidate in axis_candidates:
        if not _position_collides_with_blocks(item, candidate, margin):
            return candidate

    last_valid = getattr(item, "_last_valid_pos", current_pos)
    if isinstance(last_valid, QPointF) and not _position_collides_with_blocks(item, last_valid, margin):
        return QPointF(last_valid)
    return current_pos


def _handle_block_item_change(item: QGraphicsItem, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
    if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
        if not _position_collides_with_blocks(item, item.pos(), 6.0):
            item._last_valid_pos = QPointF(item.pos())
    return value


def _refresh_block_item_connections(item: QGraphicsItem) -> None:
    ports = list(getattr(item, "inputs", [])) + list(getattr(item, "outputs", []))
    port: Any
    for port in ports:
        connections = getattr(port, "connections", None) or []
        conn: Any
        for conn in connections:
            conn.update_path()


def _notify_block_item_manual_route_drag(item: QGraphicsItem, started: bool) -> None:
    """
    Notify every connection attached to one movable block that a manual endpoint drag
    has started or ended.
    """
    ports = list(getattr(item, "inputs", [])) + list(getattr(item, "outputs", []))
    port: Any

    for port in ports:
        connections = getattr(port, "connections", None) or []
        conn: Any
        for conn in connections:
            if isinstance(conn, ConnectionItem):
                if started:
                    conn.begin_manual_block_drag(port)
                else:
                    conn.end_manual_block_drag(port)
            else:
                pass


def _port_stub_axis(side: str | None) -> str:
    """
    Return the dominant stub axis for one connection side.

    :param side: Attachment side of the port on the block.
    :return: ``"x"`` for horizontal stubs and ``"y"`` for vertical stubs.
    """
    if side in ("left", "right"):
        return "x"
    else:
        return "y"


def _finalize_block_drop(item: QGraphicsItem, margin: float = 6.0) -> None:
    if item.scene() is None:
        return
    current_pos = item.pos()
    corrected_pos = _resolve_non_overlapping_position(item, current_pos, margin)
    if corrected_pos != current_pos:
        item.setPos(corrected_pos)
        position_changed_callback = getattr(item, "position_changed_callback", None)
        if position_changed_callback is not None:
            position_changed_callback(corrected_pos.x(), corrected_pos.y())
    _refresh_block_item_connections(item)


class EditorGraphicsDefaultsDark:
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
    __slots__ = ("_editor", "_block_uid")

    def __init__(self, editor: DynamicBlockEditorGUI, block_uid: int) -> None:
        self._editor = editor
        self._block_uid = block_uid

    def __call__(self, x_pos: float, y_pos: float) -> None:
        self._editor.on_block_position_changed(self._block_uid, x_pos, y_pos)


class Node:
    def __init__(self, name, data=None, parent=None):
        self.name = name
        self.data = data
        self.parent = parent
        self.children = []

    def add_child(self, node):
        self.children.append(node)
        node.parent = self


class ResizeHandle(QGraphicsItem):
    def __init__(self, block_item: GenericBlockItem, editor: DynamicBlockEditorGUI, size: int = 10):
        super().__init__(block_item)
        self.editor = editor
        self._size = size
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setZValue(2)
        self.block: GenericBlockItem = block_item
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)
        self.pen_color: QColor = QColor("#03384f")

    def boundingRect(self) -> QtCore.QRectF:
        return QtCore.QRectF(0, 0, 13, 13)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(QtCore.QRectF(0, 0, 13, 13))
        return path

    def recolour_mode(self):
        self.pen_color = self.editor.colors_palet.WIRE_COLOR

    def recolour(self, use_custom_color: bool = False):
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def paint(self, painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:

        pen = QPen(self.pen_color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.drawLine(QPointF(2, 2), QPointF(11, 11))
        painter.drawLine(QPointF(11, 11), QPointF(8, 11))
        painter.drawLine(QPointF(11, 11), QPointF(11, 8))

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
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
    _CORNER_RADIUS: float = 2.0

    def __init__(self,
                 subsystem: BlockItem | GenericBlockItem | PairedItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem,
                 editor: DynamicBlockEditorGUI,
                 is_input: bool,
                 index: int,
                 total: int,
                 size: int = 10):
        super().__init__(subsystem)
        self._size: int = size
        self.editor = editor
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

    # --- geometry helpers ---

    @staticmethod
    def _scale(v: QPointF, s: float) -> QPointF:
        return QPointF(v.x() * s, v.y() * s)

    @staticmethod
    def _add(a: QPointF, b: QPointF) -> QPointF:
        return QPointF(a.x() + b.x(), a.y() + b.y())

    @staticmethod
    def _sub(a: QPointF, b: QPointF) -> QPointF:
        return QPointF(a.x() - b.x(), a.y() - b.y())

    @staticmethod
    def _unit(p1: QPointF, p2: QPointF) -> QPointF:
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1e-10:
            return QPointF(0, 0)
        return QPointF(dx / length, dy / length)

    @staticmethod
    def _build_rounded_triangle(v0: QPointF, v1: QPointF, v2: QPointF, radius: float) -> QPainterPath:
        d01 = PortItem._unit(v0, v1)
        s0 = PortItem._add(v0, PortItem._scale(d01, radius))
        e0 = PortItem._sub(v1, PortItem._scale(d01, radius))

        d12 = PortItem._unit(v1, v2)
        s1 = PortItem._add(v1, PortItem._scale(d12, radius))
        e1 = PortItem._sub(v2, PortItem._scale(d12, radius))

        d20 = PortItem._unit(v2, v0)
        s2 = PortItem._add(v2, PortItem._scale(d20, radius))
        e2 = PortItem._sub(v0, PortItem._scale(d20, radius))

        path = QPainterPath()
        path.moveTo(s0)
        path.lineTo(e0)
        path.quadTo(v1, s1)
        path.lineTo(e1)
        path.quadTo(v2, s2)
        path.lineTo(e2)
        path.quadTo(v0, s0)
        path.closeSubpath()
        return path

    def recolour_mode(self):
        self.setBrush(QBrush(self.editor.colors_palet.PORT_ITEM_COLOR))
        self.setPen(QPen(Qt.PenStyle.NoPen))

    def recolour(self, use_custom_color: bool = False):
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def _build_path(self) -> None:
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

        self._path = self._build_rounded_triangle(v0, v1, v2, r)

    # --- QGraphicsItem interface ---

    def boundingRect(self) -> QtCore.QRectF:
        return self._path.boundingRect().adjusted(-0.5, -0.5, 0.5, 0.5)

    def shape(self) -> QPainterPath:
        return self._path

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawPath(self._path)

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        QApplication.restoreOverrideCursor()

    def is_connected(self) -> bool:
        if self.connections is not None:
            return True
        else:
            return False

    def update_port_visibility(self) -> None:
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
    def __init__(self,
                 subsystem: "BlockItem",
                 editor: DynamicBlockEditorGUI,
                 index: int,
                 radius: int = 6):
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
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        QApplication.restoreOverrideCursor()

    def is_connected(self) -> bool:
        if self.connections is not None:
            return True
        else:
            return False

    def recolour_mode(self):
        self.setBrush(QBrush(self.editor.colors_palet.BLOCK_FILL))
        self.setPen(QPen(self.editor.colors_palet.BLOCK_BORDER, 1))

    def recolour(self, use_custom_color: bool = False):
        if use_custom_color:
            pass
        else:
            self.recolour_mode()


class ConnectionItem(QGraphicsPathItem):
    def __init__(self,
                 source_port: PortItem | BranchingItem,
                 target_port: PortItem | BranchingItem,
                 diagram=None,
                 con_uid=None,
                 uid=None,
                 editor: DynamicBlockEditorGUI | None = None):
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
        if self.source_port.connections is not None:
            self.source_port.connections.append(self)

        if self.target_port.connections is None:
            self.target_port.connections = list()
        if self.target_port.connections is not None:
            self.target_port.connections.append(self)

        if isinstance(self.source_port, PortItem):
            self.source_port.update_port_visibility()
        if isinstance(self.target_port, PortItem):
            self.target_port.update_port_visibility()

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self._dragging_segment: int = -1
        self._drag_start_scene_pos: QPointF | None = None
        self.update_path()

    def recolour_mode(self):
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

    def recolour(self, use_custom_color: bool = False):
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
        del index
        del new_pos

    def get_route_points_for_editing(self) -> list[tuple[float, float]]:
        """
        Return the current rendered route points as a normalized point list.
        """
        path: QPainterPath = self.path()
        if path.isEmpty():
            return list()

        points: list[tuple[float, float]] = []
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
        scene = self.scene()
        if scene is None:
            return
        item: QGraphicsItem
        for item in list(scene.items()):
            if isinstance(item, ElbowItem) and item.connection_item is self:
                scene.removeItem(item)
            elif isinstance(item, BranchingItem) and item.owner_connection is self:
                scene.removeItem(item)
        if self._uses_routing_graph():
            pass
        else:
            pass

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
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
        super().paint(painter, option, widget)

        path = self.path()
        count = path.elementCount()
        if count < 2:
            return

        last = path.elementAt(count - 1)
        prev = path.elementAt(count - 2)
        end = QPointF(last.x, last.y)
        prev_pt = QPointF(prev.x, prev.y)

        dx = end.x() - prev_pt.x()
        dy = end.y() - prev_pt.y()
        length = math.sqrt(dx * dx + dy * dy)
        if length < 0.1:
            return

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

        arrow = QPolygonF([p1, p2, p3])
        painter.setBrush(QBrush(self.pen().color()))
        painter.setPen(QPen(self.pen().color(), 1.5,
                            Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap,
                            Qt.PenJoinStyle.RoundJoin))
        painter.drawPolygon(arrow)

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)
        pen: QPen = self.pen()
        # pen.setColor(_get_editor_constants(self.editor).WIRE_HOVER_COLOR)
        pen.setWidthF(3.5)
        self.setPen(pen)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        QApplication.restoreOverrideCursor()
        pen: QPen = self.pen()
        # pen.setColor(_get_editor_constants(self.editor).WIRE_COLOR)
        pen.setWidthF(1.5)
        self.setPen(pen)


class ElbowItem(QGraphicsEllipseItem):
    def __init__(self, connection_item: ConnectionItem, index: int, pos: QPointF = QPointF()):
        radius = 5
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.connection_item = connection_item
        self.index = index
        self.setZValue(2)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPos(pos)

    def itemChange(self, change, value):
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

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.connection_item.on_elbow_moved(self.index, self.scenePos())

    def recolour_mode(self):
        if self.connection_item.editor is not None:
            color_fill = self.connection_item.editor.colors_palet.BLOCK_FILL
            pen_color = self.connection_item.editor.colors_palet.BLOCK_BORDER
        else:
            color_fill = self.connection_item.source_port.editor.colors_palet.BLOCK_FILL
            pen_color = self.connection_item.source_port.editor.colors_palet.BLOCK_BORDER

        self.setBrush(QBrush(color_fill))
        self.setPen(QPen(pen_color, 1))

    def recolour(self, use_custom_color: bool = False):
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
    def __init__(self,
                 editor: DynamicBlockEditorGUI,
                 var_factory: VarFactory,
                 subsys: Block,
                 api_object,
                 mode: DynamicSimulationMode,
                 name: str,
                 position_changed_callback=None):
        """

        :param editor:
        :param var_factory:
        :param subsys:
        :param api_object:
        :param mode:
        :param name:
        :param position_changed_callback:
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

    def recolour_mode(self):
        self.name_item.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)
        self.setBrush(QBrush(self.editor.colors_palet.BLOCK_FILL))
        self.setPen(QPen(self.editor.colors_palet.BLOCK_BORDER, 1))
        for input_label_item in self.input_labels:
            input_label_item.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)
        for output_label_item in self.output_labels:
            output_label_item.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)

    def recolour(self, use_custom_color: bool = False):
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def mousePressEvent(self, event):
        if (
                event.button() == Qt.MouseButton.LeftButton
                and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.editor.request_navigate_to_block(self.subsys)

            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            _notify_block_item_manual_route_drag(self, started=True)
        else:
            pass

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        _notify_block_item_manual_route_drag(self, started=False)
        _finalize_block_drop(self)

    def mouseDoubleClickEvent(self, event):
        pass

    def set_subsystem(self, block: Block) -> None:
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

    def resize_block(self, width, height):
        self.prepareGeometryChange()
        min_width: float
        min_height: float
        min_width, min_height = self.get_minimum_block_size()
        QGraphicsRectItem.setRect(self, 0, 0, max(width, min_width), max(height, min_height))
        self.update_ports()
        self.update_handle_position()
        self.update_name_position()

    def update_handle_position(self):
        rect = self.rect()
        self.resizing_from_handle = False
        self.resize_handle.setPos(rect.width() - 9, rect.height() - 9)
        self.resizing_from_handle = True

    def update_name_position(self):
        if self.name_item is None:
            return

        rect = self.rect()

        text_width = self.name_item.boundingRect().width()

        x = (rect.width() - text_width) / 2
        y = rect.height() + 5

        self.name_item.setPos(x, y)

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:

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
        self.prepareGeometryChange()
        min_width: float
        min_height: float
        min_width, min_height = self.get_minimum_block_size()
        QGraphicsRectItem.setRect(self, 0, 0, min_width, min_height)
        self.update_ports()
        self.update_handle_position()
        self.update_name_position()

    def create_port_label_item(self) -> QGraphicsTextItem:
        label_item: QGraphicsTextItem = QGraphicsTextItem("", self)
        label_item.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)
        label_item.setZValue(4)

        return label_item

    def refresh_port_metadata(self) -> None:
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

    def update_ports(self):
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
        for port in self.inputs + self.outputs:
            if port.connections:
                conn: ConnectionItem
                for conn in port.connections:
                    conn.update_path()
            else:
                pass

    def hoverEnterEvent(self, event):
        QApplication.setOverrideCursor(Qt.CursorShape.OpenHandCursor)

    def hoverLeaveEvent(self, event):
        if self.resize_handle is not None and self.resize_handle.isVisible():
            self.resize_handle.hide()
        QApplication.restoreOverrideCursor()

    def hoverMoveEvent(self, event):
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

    def itemChange(self, change, value):
        value = _handle_block_item_change(self, change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.position_changed_callback is not None:
                self.position_changed_callback(value.x(), value.y())
            else:
                pass
            port: PortItem
            for port in self.inputs + self.outputs:
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
    _LABEL_W: float = 70.0
    _LABEL_H: float = 28.0
    _NOTCH_DEPTH: float = 6.0
    _TIP_BASE: float = 20.0

    def __init__(self,
                 var_factory: VarFactory,
                 subsys: Block,
                 api_object,
                 mode: DynamicSimulationMode,
                 name: str,
                 editor: DynamicBlockEditorGUI,
                 paired_items: List["PairedItem"] | None = None,
                 position_changed_callback=None):
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

    def recolour_mode(self):
        self.name_item.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)
        self.setBrush(QBrush(self.editor.colors_palet.BLOCK_FILL))
        self.setPen(QPen(self.editor.colors_palet.BLOCK_BORDER, 1))

    def recolour(self, use_custom_color: bool = False):
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def rect(self) -> QtCore.QRectF:
        return self.polygon().boundingRect()

    def _build_polygon(self) -> None:
        w = self._LABEL_W
        h = self._LABEL_H
        notch = self._NOTCH_DEPTH
        tip = self._TIP_BASE
        half = h / 2.0
        if self.is_signal_in:
            poly = QtGui.QPolygonF([
                QtCore.QPointF(w, 0.0),
                QtCore.QPointF(tip, 0.0),
                QtCore.QPointF(0.0, half),
                QtCore.QPointF(tip, h),
                QtCore.QPointF(w, h),
                QtCore.QPointF(w - notch, half),
            ])
        else:
            poly = QtGui.QPolygonF([
                QtCore.QPointF(0.0, 0.0),
                QtCore.QPointF(w - tip, 0.0),
                QtCore.QPointF(w, half),
                QtCore.QPointF(w - tip, h),
                QtCore.QPointF(0.0, h),
                QtCore.QPointF(notch, half),
            ])
        self.setPolygon(poly)
        self._position_name_and_ports()

    def _position_name_and_ports(self) -> None:
        w = self._LABEL_W
        h = self._LABEL_H
        notch = self._NOTCH_DEPTH
        tip = self._TIP_BASE
        half = h / 2.0

        if self.is_signal_in:
            if self.inputs:
                port = self.inputs[0]
                port.setPos(0.0, half)
            body_left = tip
            body_right = w - notch
        else:
            if self.outputs:
                port = self.outputs[0]
                port.setPos(w, half)
            body_left = notch
            body_right = w - tip

        body_width = body_right - body_left
        name_width = self.name_item.boundingRect().width()
        name_height = self.name_item.boundingRect().height()
        name_x = body_left + (body_width - name_width) / 2.0
        self.name_item.setPos(name_x, half - name_height / 2.0)

        port: PortItem
        for port in self.inputs + self.outputs:
            if port.connections:
                conn: ConnectionItem
                for conn in port.connections:
                    conn.update_path()

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
            self.paired_items = list([paired_item])
        elif paired_item not in self.paired_items:
            self.paired_items.append(paired_item)
        else:
            pass

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
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

    def hoverEnterEvent(self, event):
        QApplication.setOverrideCursor(Qt.CursorShape.OpenHandCursor)

    def hoverLeaveEvent(self, event):
        QApplication.restoreOverrideCursor()

    def contextMenuEvent(self, event):
        if not self.is_signal_in and self.paired_items is not None:
            menu = QMenu()
            duplicate_action = QAction("Duplicate", menu)
            duplicate_action.triggered.connect(lambda: duplicate_paired_item(self))
            menu.addAction(duplicate_action)
            menu.exec(event.screenPos())
        else:
            super().contextMenuEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            _notify_block_item_manual_route_drag(self, started=True)
        else:
            pass
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        _notify_block_item_manual_route_drag(self, started=False)
        _finalize_block_drop(self)

    def itemChange(self, change, value):
        value = _handle_block_item_change(self, change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.position_changed_callback is not None:
                self.position_changed_callback(value.x(), value.y())
            else:
                pass
            port: PortItem
            for port in self.inputs + self.outputs:
                if port.connections:
                    conn: ConnectionItem
                    for conn in port.connections:
                        conn.update_path()
                else:
                    pass
        else:
            pass
        return super().itemChange(change, value)

    def select_group(self):
        scene = self.scene()
        if scene is None:
            return

        scene.clearSelection()
        self.setSelected(True)

        if self.paired_items:
            for item in self.paired_items:
                if item is not None:
                    item.setSelected(True)


class BlockItem(QGraphicsRectItem):
    def __init__(self,
                 var_factory: VarFactory,
                 name: str,
                 editor: DynamicBlockEditorGUI,
                 mode: DynamicSimulationMode,
                 api_object,
                 position_changed_callback=None
                 ):
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

    def recolour_mode(self):
        self.name_item.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)
        self.setBrush(QBrush(self.editor.colors_palet.BLOCK_FILL))
        self.setPen(QPen(self.editor.colors_palet.BLOCK_BORDER, 1))

    def recolour(self, use_custom_color: bool = False):
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def set_subsystem(self, block: Block) -> None:
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
        label_item: QGraphicsTextItem = QGraphicsTextItem("", self)
        label_item.setDefaultTextColor(self.editor.colors_palet.PORT_LABEL_COLOR)
        label_item.setZValue(4)
        return label_item

    def get_minimum_block_size(self) -> tuple[float, float]:

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
        self.prepareGeometryChange()
        min_width: float
        min_height: float
        min_width, min_height = self.get_minimum_block_size()
        QGraphicsRectItem.setRect(self, 0, 0, min_width, min_height)
        self.update_ports()
        # self.update_handle_position()
        self._center_name()

    def _center_name(self) -> None:
        if self.name_item is None:
            return
        rect = self.rect()
        text_width = self.name_item.boundingRect().width()
        text_height = self.name_item.boundingRect().height()
        self.name_item.setPos(
            (rect.width() - text_width) / 2,
            (rect.height() - text_height) / 2,
        )

    def _refresh_connection_color(self) -> None:
        pass

    def refresh_port_metadata(self) -> None:
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
        pass

    def update_ports(self) -> None:
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

        for port in self.inputs + self.outputs:
            if port.connections is not None:
                conn: ConnectionItem
                for conn in port.connections:
                    conn.update_path()
            else:
                pass

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        QApplication.setOverrideCursor(Qt.CursorShape.OpenHandCursor)
        self.update()

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        QApplication.restoreOverrideCursor()
        self.update()

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            _notify_block_item_manual_route_drag(self, started=True)
        else:
            pass
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        _notify_block_item_manual_route_drag(self, started=False)
        _finalize_block_drop(self)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        value = _handle_block_item_change(self, change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.position_changed_callback is not None:
                self.position_changed_callback(value.x(), value.y())
            else:
                pass
            port: PortItem
            for port in self.inputs + self.outputs:
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
    SIZE: float = 38.0
    RADIUS: float = 4.0

    _SYMBOL_TEXT: Dict[BlockType, str] = {
        BlockType.CONST: "k",
        BlockType.ABS: "|x|",
        BlockType.INTEGRATOR: "∫",
        BlockType.POWER: "x^y",
        BlockType.SIN: "sin",
        BlockType.COS: "cos",
        BlockType.TAN: "tan",
        BlockType.EXP: "exp",
        BlockType.LOG: "ln",
        BlockType.LOG10: "log",
        BlockType.SQRT: "√",
        BlockType.ASIN: "asin",
        BlockType.ACOS: "acos",
        BlockType.ATAN: "atan",
        BlockType.SINH: "sinh",
        BlockType.COSH: "cosh",
        BlockType.TANH: "tanh",
        BlockType.REAL: "Re",
        BlockType.IMAG: "Im",
        BlockType.CONJ: "z*",
        BlockType.ANGLE: "∠",
    }

    def __init__(self,
                 editor: DynamicBlockEditorGUI,
                 var_factory: VarFactory,
                 subsys: Block,
                 api_object,
                 mode: DynamicSimulationMode,
                 block_type: BlockType,
                 name: str,
                 position_changed_callback=None):
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
        if self.subsys is None:
            return

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
        return self.SIZE, self.SIZE

    def resize_to_content(self) -> None:
        self.prepareGeometryChange()
        QGraphicsRectItem.setRect(self, 0, 0, self.SIZE, self.SIZE)
        self.update_ports()

    def update_ports(self) -> None:
        rect = self.rect()
        center_y = rect.height() / 2.0

        if self.inputs:
            self.inputs[0].setPos(0.0, center_y)
        for port in self.inputs[1:]:
            port.setPos(0.0, center_y)

        if self.outputs:
            self.outputs[0].setPos(rect.width(), center_y)
        for port in self.outputs[1:]:
            port.setPos(rect.width(), center_y)

        for port in self.inputs + self.outputs:
            if port.connections:
                conn: ConnectionItem
                for conn in port.connections:
                    conn.update_path()

    def _draw_center_symbol(self, painter: QPainter, body_rect: QtCore.QRectF) -> None:
        painter.setPen(QPen(self.editor.colors_palet.BLOCK_TITLE, 1.2))

        if self.block_type == BlockType.GAIN:
            triangle = QtGui.QPolygonF([
                QPointF(body_rect.left() + body_rect.width() * 0.33, body_rect.top() + body_rect.height() * 0.25),
                QPointF(body_rect.left() + body_rect.width() * 0.33, body_rect.bottom() - body_rect.height() * 0.25),
                QPointF(body_rect.right() - body_rect.width() * 0.25, body_rect.center().y()),
            ])
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPolygon(triangle)
            return

        symbol = self._SYMBOL_TEXT.get(self.block_type, self.block_type.value)
        font = painter.font()
        point_size = 8.5
        if len(symbol) >= 4:
            point_size = 7.0
        elif len(symbol) == 3:
            point_size = 7.6
        font.setPointSizeF(point_size)
        painter.setFont(font)
        painter.drawText(body_rect, Qt.AlignmentFlag.AlignCenter, symbol)

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
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
    LABEL_OUTSET: float = 5.0

    def __init__(self,
                 subsys: Block,
                 var_factory: VarFactory,
                 block_type: BlockType,
                 editor: DynamicBlockEditorGUI,
                 position_changed_callback=None):
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

    def recolour_mode(self):
        for label in self.input_labels:
            label.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)
        self.setBrush(QBrush(self.editor.colors_palet.BLOCK_FILL))
        self.setPen(QPen(self.editor.colors_palet.BLOCK_BORDER, 1))

    def recolour(self, use_custom_color: bool = False):
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def _walk_sum_expr(self, expr: Expr, sign: int, result: Dict[int, int]) -> None:
        if isinstance(expr, Var):
            result[expr.uid] = sign
        elif isinstance(expr, BinOp):
            if expr.op == "+":
                self._walk_sum_expr(expr.left, sign, result)
                self._walk_sum_expr(expr.right, sign, result)
            elif expr.op == "-":
                self._walk_sum_expr(expr.left, sign, result)
                self._walk_sum_expr(expr.right, -sign, result)
        elif isinstance(expr, UnOp):
            if expr.op == "-":
                self._walk_sum_expr(expr.operand, -sign, result)

    def _walk_product_expr(self, expr: Expr, label: str, result: Dict[int, str]) -> None:
        if isinstance(expr, Var):
            result[expr.uid] = label
        elif isinstance(expr, BinOp):
            if expr.op == "*":
                self._walk_product_expr(expr.left, "x", result)
                self._walk_product_expr(expr.right, "x", result)
            elif expr.op == "/":
                self._walk_product_expr(expr.left, "x", result)
                self._walk_product_expr(expr.right, "/", result)
        elif isinstance(expr, UnOp):
            self._walk_product_expr(expr.operand, label, result)

    def _analyze_input_signs(self) -> None:
        self._input_signs = list()
        if not self.subsys.algebraic_eqs:
            return

        eq = self.subsys.algebraic_eqs[0]
        if not isinstance(eq, BinOp) or eq.op != "-":
            return

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

    def _get_label_outset_offset(self, port: PortItem) -> QPointF:
        rect = self.rect()
        cx = rect.center().x()
        cy = rect.center().y()
        dx = port.pos().x() - cx
        dy = port.pos().y() - cy
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1e-6:
            return QPointF(0, 0)
        return QPointF(dx / length * self.LABEL_OUTSET,
                       dy / length * self.LABEL_OUTSET)

    def refresh_port_metadata(self) -> None:
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

        for i, port in enumerate(self.outputs):
            port.setRotation(0)
            port.setPos(right, cy)

        for i, label in enumerate(self.input_labels):
            if i < len(self._input_signs):
                label.setPlainText(self._input_signs[i])
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
        rect = self.rect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawEllipse(rect)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            _notify_block_item_manual_route_drag(self, started=True)
        else:
            pass
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        _notify_block_item_manual_route_drag(self, started=False)
        _finalize_block_drop(self)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        value = _handle_block_item_change(self, change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            for port in self.inputs + self.outputs:
                if port.connections:
                    for conn in port.connections:
                        conn.update_path()
            return super().itemChange(change, value)
        else:
            return super().itemChange(change, value)


class RectBaseArithmeticOpItem(QGraphicsRectItem):
    def __init__(self,
                 subsys: Block,
                 var_factory: VarFactory,
                 block_type: BlockType,
                 editor: DynamicBlockEditorGUI,
                 position_changed_callback=None):
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

    def recolour_mode(self):
        for label in self.input_labels:
            label.setDefaultTextColor(self.editor.colors_palet.BLOCK_TITLE)
        self.setBrush(QBrush(self.editor.colors_palet.BLOCK_FILL))
        self.setPen(QPen(self.editor.colors_palet.BLOCK_BORDER, 1))

    def recolour(self, use_custom_color: bool = False):
        if use_custom_color:
            pass
        else:
            self.recolour_mode()

    def _walk_sum_expr(self, expr: Expr, sign: int, result: Dict[int, int]) -> None:
        if isinstance(expr, Var):
            result[expr.uid] = sign
        elif isinstance(expr, BinOp):
            if expr.op == "+":
                self._walk_sum_expr(expr.left, sign, result)
                self._walk_sum_expr(expr.right, sign, result)
            elif expr.op == "-":
                self._walk_sum_expr(expr.left, sign, result)
                self._walk_sum_expr(expr.right, -sign, result)
        elif isinstance(expr, UnOp):
            if expr.op == "-":
                self._walk_sum_expr(expr.operand, -sign, result)

    def _walk_product_expr(self, expr: Expr, label: str, result: Dict[int, str]) -> None:
        if isinstance(expr, Var):
            result[expr.uid] = label
        elif isinstance(expr, BinOp):
            if expr.op == "*":
                self._walk_product_expr(expr.left, "x", result)
                self._walk_product_expr(expr.right, "x", result)
            elif expr.op == "/":
                self._walk_product_expr(expr.left, "x", result)
                self._walk_product_expr(expr.right, "/", result)
        elif isinstance(expr, UnOp):
            self._walk_product_expr(expr.operand, label, result)

    def _analyze_input_signs(self) -> None:
        self._input_signs = list()
        if not self.subsys.algebraic_eqs:
            return

        eq = self.subsys.algebraic_eqs[0]
        if not isinstance(eq, BinOp) or eq.op != "-":
            return

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

    def refresh_port_metadata(self) -> None:
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
            port = self.inputs[i]
            tw = label.boundingRect().width()
            th = label.boundingRect().height()
            label.setPos(port.pos().x() + 2.0, port.pos().y() - th / 2)

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        rect = self.rect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(rect, 6.0, 6.0)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            _notify_block_item_manual_route_drag(self, started=True)
        else:
            pass
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        _notify_block_item_manual_route_drag(self, started=False)
        _finalize_block_drop(self)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        value = _handle_block_item_change(self, change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            for port in self.inputs + self.outputs:
                if port.connections:
                    for conn in port.connections:
                        conn.update_path()
            return super().itemChange(change, value)
        else:
            return super().itemChange(change, value)


class GraphicsView(QGraphicsView):
    ZOOM_FACTOR: float = 1.15

    def __init__(self, scene: QGraphicsScene):
        super().__init__(scene)
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.IntersectsItemShape)
        self._panning: bool = False
        self._pan_start: QPointF = QPointF()

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        self.apply_zoom(event.angleDelta().y() > 0)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
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
        if self._panning:
            delta: QPointF = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y()))
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def apply_zoom(self, zoom_in: bool) -> None:
        zoom_factor: float = self.ZOOM_FACTOR if zoom_in else 1.0 / self.ZOOM_FACTOR
        self.scale(zoom_factor, zoom_factor)

    def zoom_in(self) -> None:
        self.apply_zoom(True)

    def zoom_out(self) -> None:
        self.apply_zoom(False)

    def center_items(self) -> None:
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
    def __init__(self, editor: "DynamicBlockEditorGUI"):
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
                if hasattr(item, "position_changed_callback"):
                    item.position_changed_callback = None
                else:
                    pass
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

    def get_modal_template_metadata(self, block: Block | None) -> tuple[str | None, Dict[str, Any] | None]:
        return self.editor.get_modal_template_metadata(block)

    def change_item_fill_color(self,
                               item: BlockItem | GenericBlockItem | ConnectionItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem | PairedItem) -> None:
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
        if self.context_item is not None:
            self.editor.remove_item(self.context_item)
        else:
            pass

    def recolor_context_item(self) -> None:
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
        for item in self.items(event.scenePos()):
            if isinstance(item, PairedItem):
                item.select_group()
                event.accept()
                return
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
