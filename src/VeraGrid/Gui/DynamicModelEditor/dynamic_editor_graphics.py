from __future__ import annotations

import math
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING, cast

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QBrush, QPainter, QPainterPath, QPen, QAction, QPolygonF
from PySide6.QtWidgets import QApplication, QColorDialog, QGraphicsEllipseItem, QGraphicsItem, \
    QGraphicsPathItem, QGraphicsPolygonItem, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem, \
    QGraphicsView, QMenu, QWidget

import VeraGrid.ThirdParty.darkdetect as darkdetect
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagram
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import BlockType
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Expr, BinOp, UnOp
from VeraGridEngine.enumerations import DynamicSimulationMode

if TYPE_CHECKING:
    from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI


class EditorGraphicsDefaultsDark:
    BLOCK_BORDER: QColor = QColor("white")
    BLOCK_BORDER_SELECTED: QColor = QColor("#cc6f2c")
    BLOCK_TITLE: QColor = QColor("#173042")
    WIRE_COLOR: QColor = QColor("white")
    HANDLE_FILL: QColor = QColor("#36536b")
    BLOCK_FILL: QColor = QColor("#f5fdff")
    PORT_LABEL_COLOR: QColor = QColor("#173042")
    WIRE_ELBOW_OFFSET: float = 36.0
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


class EditorGraphicsDefaultsLight:
    BLOCK_BORDER: QColor = QColor("#202124")
    BLOCK_BORDER_SELECTED: QColor = QColor("#cc6f2c")
    BLOCK_TITLE: QColor = QColor("#173042")
    WIRE_COLOR: QColor = QColor("black")
    HANDLE_FILL: QColor = QColor("#36536b")
    BLOCK_FILL: QColor = QColor("#f5fdff")
    PORT_LABEL_COLOR: QColor = QColor("#173042")
    WIRE_ELBOW_OFFSET: float = 36.0
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


def _get_editor_constants() -> type[EditorGraphicsDefaultsLight] | type[EditorGraphicsDefaultsDark] | DynamicBlockEditorGUI:

    try:
        is_dark = darkdetect.theme() == "Dark"
    except ImportError:
        is_dark = False

    if is_dark:
        return EditorGraphicsDefaultsDark
    else:
        return EditorGraphicsDefaultsLight

def _new_uid() -> int:
    return uuid.uuid4().int


def _grid_node_f_cost_sort_key(node: Any) -> float:
    return float(node.f_cost)


def _transformer_modal_config_allows_modify(modal_kind: str | None, modal_config: Dict[str, Any] | None) -> bool:
    if modal_kind == "transformer_topology_emt" and isinstance(modal_config, dict):
        return bool(modal_config.get("allow_modify_template", True))
    else:
        return modal_kind is not None


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


class BlockPositionChangedCallback:
    __slots__ = ("_editor", "_block_uid")

    def __init__(self, editor: "DynamicBlockEditorGUI", block_uid: int) -> None:
        self._editor = editor
        self._block_uid = block_uid

    def __call__(self, x_pos: float, y_pos: float) -> None:
        self._editor.on_block_position_changed(self._block_uid, x_pos, y_pos)


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


class OrthogonalRouter:
    GRID_SIZE: float = 10.0
    BASE_COST: int = 1
    TURN_COST: int = 10
    BLOCKED_COST: int = 1000000

    class GridNode:
        def __init__(self, x: int, y: int):
            self.x = x
            self.y = y
            self.g_cost: int = 0
            self.h_cost: int = 0
            self.f_cost: int = 0
            self.parent: "OrthogonalRouter.GridNode | None" = None
            self.direction: str | None = None

        def __hash__(self):
            return hash((self.x, self.y))

        def __eq__(self, other):
            return self.x == other.x and self.y == other.y

    @staticmethod
    def _pos_to_grid(pos: QPointF) -> tuple[int, int]:
        return (int(pos.x() / OrthogonalRouter.GRID_SIZE),
                int(pos.y() / OrthogonalRouter.GRID_SIZE))

    @staticmethod
    def _grid_to_pos(gx: int, gy: int) -> QPointF:
        return QPointF(gx * OrthogonalRouter.GRID_SIZE, gy * OrthogonalRouter.GRID_SIZE)

    @staticmethod
    def _get_neighbors(node: "OrthogonalRouter.GridNode") -> List[tuple]:
        return [
            (node.x + 1, node.y, "right"),
            (node.x - 1, node.y, "left"),
            (node.x, node.y + 1, "down"),
            (node.x, node.y - 1, "up")
        ]

    @staticmethod
    def _heuristic(x1: int, y1: int, x2: int, y2: int) -> int:
        return abs(x2 - x1) + abs(y2 - y1)

    @staticmethod
    def _is_blocked(gx: int, gy: int, scene: QGraphicsScene | None,
                    source_port: "PortItem | BranchingItem | None",
                    target_port: "PortItem | BranchingItem | None") -> bool:
        if scene is None:
            return False
        else:
            pass

        pos = QPointF(gx * OrthogonalRouter.GRID_SIZE, gy * OrthogonalRouter.GRID_SIZE)
        rect = QtCore.QRectF(pos.x() - OrthogonalRouter.GRID_SIZE / 2,
                             pos.y() - OrthogonalRouter.GRID_SIZE / 2,
                             OrthogonalRouter.GRID_SIZE, OrthogonalRouter.GRID_SIZE)

        items = scene.items(rect)
        item: QGraphicsItem
        for item in items:
            if isinstance(item, (ConnectionItem, PortItem, BranchingItem)):
                pass
            elif item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable:
                if source_port is not None and item == source_port.subsystem:
                    pass
                elif target_port is not None and item == target_port.subsystem:
                    pass
                else:
                    return True
            else:
                pass
        return False

    @staticmethod
    def compute_path(source_pos: QPointF,
                     target_pos: QPointF,
                     source_port: "PortItem | BranchingItem | None" = None,
                     target_port: "PortItem | BranchingItem | None" = None,
                     scene: QGraphicsScene | None = None,
                     elbow_offset: float = 36.0) -> QPainterPath:
        if scene is None:
            return build_orthogonal_connection_path(source_pos, target_pos, elbow_offset)
        else:
            pass

        start_gx, start_gy = OrthogonalRouter._pos_to_grid(source_pos)
        end_gx, end_gy = OrthogonalRouter._pos_to_grid(target_pos)

        open_set: List[OrthogonalRouter.GridNode] = list()
        closed_set: set = set()

        start_node = OrthogonalRouter.GridNode(start_gx, start_gy)
        start_node.g_cost = 0
        start_node.h_cost = OrthogonalRouter._heuristic(start_gx, start_gy, end_gx, end_gy)
        start_node.f_cost = start_node.g_cost + start_node.h_cost
        start_node.direction = None
        open_set.append(start_node)

        while open_set:
            open_set.sort(key=_grid_node_f_cost_sort_key)
            current = open_set.pop(0)

            if current.x == end_gx and current.y == end_gy:
                path_points = OrthogonalRouter._reconstruct_path(current)
                return OrthogonalRouter._build_qpainterpath(path_points, source_pos, target_pos)
            else:
                pass

            closed_set.add((current.x, current.y))

            gx: int
            gy: int
            direction: str
            for gx, gy, direction in OrthogonalRouter._get_neighbors(current):
                if (gx, gy) in closed_set:
                    pass
                elif OrthogonalRouter._is_blocked(gx, gy, scene, source_port, target_port):
                    pass
                else:
                    g_cost = current.g_cost + OrthogonalRouter.BASE_COST
                    if current.direction is not None and current.direction != direction:
                        g_cost += OrthogonalRouter.TURN_COST
                    else:
                        pass

                    neighbor = OrthogonalRouter.GridNode(gx, gy)
                    in_open = False
                    node: OrthogonalRouter.GridNode
                    for node in open_set:
                        if node.x == gx and node.y == gy:
                            in_open = True
                            if g_cost < node.g_cost:
                                node.g_cost = g_cost
                                node.f_cost = node.g_cost + node.h_cost
                                node.parent = current
                                node.direction = direction
                            else:
                                pass
                            break
                        else:
                            pass

                    if not in_open:
                        neighbor.g_cost = g_cost
                        neighbor.h_cost = OrthogonalRouter._heuristic(gx, gy, end_gx, end_gy)
                        neighbor.f_cost = neighbor.g_cost + neighbor.h_cost
                        neighbor.parent = current
                        neighbor.direction = direction
                        open_set.append(neighbor)
                    else:
                        pass

        return build_orthogonal_connection_path(source_pos, target_pos, elbow_offset)

    @staticmethod
    def _reconstruct_path(end_node: "OrthogonalRouter.GridNode") -> List[QPointF]:
        path: List[QPointF] = list()
        current = end_node
        while current is not None:
            path.append(OrthogonalRouter._grid_to_pos(current.x, current.y))
            current = current.parent
        path.reverse()
        return path

    @staticmethod
    def _build_qpainterpath(grid_path: List[QPointF], source_pos: QPointF, target_pos: QPointF) -> QPainterPath:
        if len(grid_path) < 2:
            path = QPainterPath(source_pos)
            path.lineTo(target_pos)
            return path
        else:
            pass

        path = QPainterPath(source_pos)
        path.lineTo(grid_path[0])
        simplified = OrthogonalRouter._simplify_path(grid_path)

        point: QPointF
        for point in simplified:
            path.lineTo(point)

        path.lineTo(target_pos)
        return path

    @staticmethod
    def _simplify_path(points: List[QPointF]) -> List[QPointF]:
        if len(points) < 3:
            return points
        else:
            pass

        simplified: List[QPointF] = list([points[0]])

        i: int
        for i in range(1, len(points) - 1):
            dx1 = points[i].x() - points[i - 1].x()
            dy1 = points[i].y() - points[i - 1].y()
            dx2 = points[i + 1].x() - points[i].x()
            dy2 = points[i + 1].y() - points[i].y()

            dir1 = "h" if abs(dx1) > abs(dy1) else "v"
            dir2 = "h" if abs(dx2) > abs(dy2) else "v"

            if dir1 != dir2:
                simplified.append(points[i])
            else:
                pass

        simplified.append(points[-1])
        return simplified

    @staticmethod
    def compute_path_simple(source_pos: QPointF, target_pos: QPointF, elbow_offset: float = 36.0) -> QPainterPath:
        return build_orthogonal_connection_path(source_pos, target_pos, elbow_offset)


class Node:
    def __init__(self, name, data=None, parent=None):
        self.name = name
        self.data = data
        self.parent = parent
        self.children = []

    def add_child(self, node):
        self.children.append(node)
        node.parent = self


class ResizeHandle(QGraphicsRectItem):
    def __init__(self, block_item: "BlockItem | PairedItem", size: int = 10):
        super().__init__(0, 0, size, size, block_item)
        editor_constants = _get_editor_constants()
        self.setBrush(QBrush(editor_constants.HANDLE_FILL))
        self.setPen(QPen(QColor("#ffffff"), 1))
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setZValue(2)
        self.block: BlockItem | PairedItem = block_item
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)

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


class PortItem(QGraphicsPolygonItem):
    def __init__(self,
                 subsystem: "BlockItem | GenericBlockItem | PairedItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem",
                 is_input: bool,
                 index: int,
                 total: int,
                 size: int = 12):
        width = size
        height = int(size * 0.83)

        if is_input:
            polygon = QPolygonF([
                QPointF(0, 0),
                QPointF(-width, height / 2),
                QPointF(-width, -height / 2),
            ])
        else:
            polygon = QPolygonF([
                QPointF(0, -height / 2),
                QPointF(0, height / 2),
                QPointF(width, 0),
            ])

        super().__init__(polygon, subsystem)
        self.setBrush(QBrush(QColor("#40FE9F")))
        self.setPen(QPen(QColor("#202124"), 1.2))
        self.setZValue(3)
        self.setAcceptHoverEvents(True)
        self.subsystem: "BlockItem | GenericBlockItem | PairedItem | RoundBaseArithmeticOpItem | RectBaseArithmeticOpItem" = subsystem
        self.is_input: bool = is_input
        self.connections: List["ConnectionItem"] | None = None
        self.index: int = index
        self.total: int = total
        self.base_var: Var | None = None
        self._validation_highlighted: bool = False

        self.setPos(0, 0)

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        QApplication.restoreOverrideCursor()

    def is_connected(self) -> bool:
        if self.connections is not None:
            return True
        else:
            return False

    def _update_port_visibility(self) -> None:
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

        # The validation overlay uses a red fill and border so missing port
        # connections remain visible even when the section stays collapsed.
        if self._validation_highlighted:
            self.setBrush(QBrush(QColor("#b42318")))
            self.setPen(QPen(QColor("#b42318"), 1.2))
        else:
            self.setBrush(QBrush(QColor("#40FE9F")))
            self.setPen(QPen(QColor("#202124"), 1.2))


class BranchingItem(QGraphicsEllipseItem):
    def __init__(self,
                 subsystem: "BlockItem",
                 index: int,
                 radius: int = 6):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        editor_constants = _get_editor_constants()
        fill_color: QColor = editor_constants.OUTPUT_PORT_FILL
        self.setBrush(QBrush(fill_color))
        self.setPen(QPen(editor_constants.PORT_BORDER, 1.5))
        self.setZValue(3)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.subsystem: BlockItem = subsystem
        self.index: int = index
        self.connections: List["ConnectionItem"] | None = None
        self.base_var: Var | None = None

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        QApplication.restoreOverrideCursor()

    def is_connected(self) -> bool:
        if self.connections is not None:
            return True
        else:
            return False


class ConnectionItem(QGraphicsPathItem):
    def __init__(self,
                 source_port: PortItem | BranchingItem,
                 target_port: PortItem | BranchingItem,
                 diagram=None,
                 con_uid=None,
                 uid=None,
                 elbow_points: List[QPointF] = None,
                 editor: "DynamicBlockEditorGUI | None" = None):
        super().__init__()
        if editor is not None:
            self.editor: DynamicBlockEditorGUI | None = editor
        else:
            self.editor = source_port.subsystem.editor
        self.uid: int = uid if uid is not None else _new_uid()
        self.setZValue(-1)
        self.source_port: PortItem | BranchingItem = source_port
        self.target_port: PortItem | BranchingItem = target_port
        self.diagram = diagram
        self.con_uid = con_uid if con_uid is not None else self.uid

        if self.source_port.connections is None:
            self.source_port.connections = list()
        self.source_port.connections.append(self)

        if self.target_port.connections is None:
            self.target_port.connections = list()
        self.target_port.connections.append(self)

        if isinstance(self.source_port.subsystem, BlockItem):
            self.source_port.subsystem._refresh_connection_color()
        if isinstance(self.target_port.subsystem, BlockItem):
            self.target_port.subsystem._refresh_connection_color()

        if isinstance(self.source_port, PortItem):
            self.source_port._update_port_visibility()
        if isinstance(self.target_port, PortItem):
            self.target_port._update_port_visibility()

        try:
            is_dark = darkdetect.theme() == "Dark"
        except ImportError:
            is_dark = False

        if is_dark:
            self.set_dark_mode()
        else:
            self.set_light_mode()
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

        self.elbow_points: List[QPointF] = elbow_points if elbow_points is not None else list()
        self.elbows: List[ElbowItem] = list()
        self._dragging_segment: int = -1
        self._original_path_elements: List[QPointF] = list()
        self.update_path()

        if self.diagram is not None:
            self.diagram.add_branch(
                connectionitem_uid=self.con_uid,
                device_uid_from=self.source_port.subsystem.subsys.uid,
                device_uid_to=self.target_port.subsystem.subsys.uid,
                port_number_from=self.source_port.index,
                port_number_to=self.target_port.index,
                color=self.pen().color().name(),
                elbow_points=[(pt.x(), pt.y()) for pt in self.elbow_points]
            )

    def set_dark_mode(self):
        editor_constants = _get_editor_constants()
        pen = self.pen()
        pen.setColor(editor_constants.WIRE_COLOR)
        self.setPen(pen)
        self.update()

    def set_light_mode(self):
        editor_constants = _get_editor_constants()
        pen = self.pen()
        pen.setColor(editor_constants.WIRE_COLOR)
        self.setPen(pen)
        self.update()

    def update_path(self) -> None:
        path: QPainterPath = QPainterPath(self.source_port.scenePos())

        if self.elbow_points:
            pt: QPointF
            for pt in self.elbow_points:
                path.lineTo(pt)
        else:
            path = build_orthogonal_connection_path(
                self.source_port.scenePos(),
                self.target_port.scenePos(),
                _get_editor_constants().WIRE_ELBOW_OFFSET,
            )

        path.lineTo(self.target_port.scenePos())
        self.setPath(path)

    def _create_elbow_items(self) -> None:
        elbow: ElbowItem
        for elbow in self.elbows:
            elbow.setParentItem(cast(QGraphicsItem | None, None))
            if elbow.scene():
                elbow.scene().removeItem(elbow)
            else:
                pass
        self.elbows.clear()

        i: int
        pt: QPointF
        for i, pt in enumerate(self.elbow_points):
            elbow = ElbowItem(self, i, pt)
            self.scene().addItem(elbow)
            self.elbows.append(elbow)

    def on_elbow_moved(self, index: int, new_pos: QPointF) -> None:
        if index < 0 or index >= len(self.elbows):
            return
        else:
            pass

        self.elbow_points[index] = new_pos

        prev_pt = self.source_port.scenePos()
        next_pt = self.target_port.scenePos()

        if index > 0:
            prev_pt = self.elbow_points[index - 1]
        else:
            pass
        if index < len(self.elbow_points) - 1:
            next_pt = self.elbow_points[index + 1]
        else:
            pass

        dx1 = new_pos.x() - prev_pt.x()
        dy1 = new_pos.y() - prev_pt.y()
        dx2 = next_pt.x() - new_pos.x()
        dy2 = next_pt.y() - new_pos.y()

        if abs(dx1) > abs(dy1):
            self.elbow_points[index].setY(prev_pt.y())
        else:
            self.elbow_points[index].setX(prev_pt.x())

        if index < len(self.elbow_points) - 1:
            if abs(dx2) > abs(dy2):
                self.elbow_points[index + 1].setY(new_pos.y())
            else:
                self.elbow_points[index + 1].setX(new_pos.x())
        else:
            pass

        i: int
        elbow: ElbowItem
        for i, elbow in enumerate(self.elbows):
            elbow.setPos(self.elbow_points[i])

        self.update_path()
        self._save_elbow_points()

    def _save_elbow_points(self) -> None:
        if self.con_uid in self.diagram.con_data:
            self.diagram.con_data[self.con_uid].elbow_points = [
                (pt.x(), pt.y()) for pt in self.elbow_points
            ]
        else:
            pass

    def _segment_hit_test(self, pos: QPointF, threshold: float = 12.0) -> tuple:
        path: QPainterPath = self.path()
        if path.isEmpty():
            return -1, False
        else:
            pass

        elements: List[QPointF] = list()
        i: int
        for i in range(path.elementCount()):
            elem = path.elementAt(i)
            elements.append(QPointF(elem.x, elem.y))

        if len(elements) < 2:
            return -1, False
        else:
            pass

        for i in range(len(elements) - 1):
            p1: QPointF = elements[i]
            p2: QPointF = elements[i + 1]

            dy: float = abs(p2.y() - p1.y())
            dx: float = abs(p2.x() - p1.x())

            if dy < 1:
                if p1.y() - threshold <= pos.y() <= p1.y() + threshold:
                    if min(p1.x(), p2.x()) - threshold <= pos.x() <= max(p1.x(), p2.x()) + threshold:
                        return i, True
                    else:
                        pass
                else:
                    pass
            elif dx < 1:
                if p1.x() - threshold <= pos.x() <= p1.x() + threshold:
                    if min(p1.y(), p2.y()) - threshold <= pos.y() <= max(p1.y(), p2.y()) + threshold:
                        return i, False
                    else:
                        pass
                else:
                    pass
            else:
                min_x: float = min(p1.x(), p2.x()) - threshold
                max_x: float = max(p1.x(), p2.x()) + threshold
                min_y: float = min(p1.y(), p2.y()) - threshold
                max_y: float = max(p1.y(), p2.y()) + threshold
                if min_x <= pos.x() <= max_x and min_y <= pos.y() <= max_y:
                    return i, False
                else:
                    pass

        return -1, False

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        scene_pos: QPointF = event.scenePos()
        seg_idx, is_horizontal = self._segment_hit_test(scene_pos)
        if seg_idx >= 0:
            self._dragging_segment = seg_idx
            self._original_path_elements = list()
            path: QPainterPath = self.path()
            i: int
            for i in range(path.elementCount()):
                elem = path.elementAt(i)
                self._original_path_elements.append(QPointF(elem.x, elem.y))
            event.accept()
            return
        else:
            pass
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if self._dragging_segment >= 0:
            new_pos: QPointF = event.scenePos()
            path: QPainterPath = self.path()
            elements: List[QPointF] = list()
            i: int
            for i in range(path.elementCount()):
                elem = path.elementAt(i)
                elements.append(QPointF(elem.x, elem.y))

            if not elements or self._dragging_segment >= len(elements) - 1:
                super().mouseMoveEvent(event)
                return
            else:
                pass

            seg_idx: int = self._dragging_segment
            p1: QPointF = elements[seg_idx]
            p2: QPointF = elements[seg_idx + 1]

            dy: float = abs(p2.y() - p1.y())
            dx: float = abs(p2.x() - p1.x())

            if dy < 1:
                new_y: float = new_pos.y()
                new_x: float = p1.x()
            elif dx < 1:
                new_x = new_pos.x()
                new_y = p1.y()
            else:
                new_x = new_pos.x()
                new_y = new_pos.y()

            new_elements: List[QPointF] = [QPointF(pt) for pt in elements]

            if dy < 1:
                if seg_idx == 0:
                    new_elements[seg_idx + 1] = QPointF(elements[seg_idx + 1].x(), new_y)
                elif seg_idx == len(elements) - 2:
                    new_elements[seg_idx] = QPointF(elements[seg_idx].x(), new_y)
                else:
                    new_elements[seg_idx] = QPointF(elements[seg_idx].x(), new_y)
                    new_elements[seg_idx + 1] = QPointF(elements[seg_idx + 1].x(), new_y)
            elif dx < 1:
                if seg_idx == 0:
                    new_elements[seg_idx + 1] = QPointF(new_x, elements[seg_idx + 1].y())
                elif seg_idx == len(elements) - 2:
                    new_elements[seg_idx] = QPointF(new_x, elements[seg_idx].y())
                else:
                    new_elements[seg_idx] = QPointF(new_x, elements[seg_idx].y())
                    new_elements[seg_idx + 1] = QPointF(new_x, elements[seg_idx + 1].y())
            else:
                pass

            self._rebuild_path_from_elements(new_elements)
            event.accept()
            return
        else:
            pass
        super().mouseMoveEvent(event)

    def _rebuild_path_from_elements(self, elements: List[QPointF]) -> None:
        if len(elements) < 2:
            return
        else:
            pass

        path: QPainterPath = QPainterPath(elements[0])
        i: int
        for i in range(1, len(elements)):
            path.lineTo(elements[i])
        self.setPath(path)

        if len(elements) > 2:
            self.elbow_points = elements[1:-1]
        else:
            self.elbow_points = list()
        self._save_elbow_points()

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if self._dragging_segment >= 0:
            self._dragging_segment = -1
            self._original_path_elements = list()
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
    def __init__(self, connection_item: "ConnectionItem", index: int, pos: QPointF = QPointF()):
        radius = 5
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.connection_item = connection_item
        self.index = index
        editor_constants = _get_editor_constants()
        self.setBrush(QBrush(editor_constants.WIRE_COLOR))
        self.setPen(QPen(QColor("#173042"), 1.5))
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

        self.name_item = QGraphicsTextItem(self.subsys.name, self)

        try:
            is_dark = darkdetect.theme() == "Dark"
        except ImportError:
            is_dark = False

        if is_dark:
            self.set_dark_mode()
        else:
            self.set_light_mode()

        name_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 9)
        name_font.setBold(True)
        self.name_item.setFont(name_font)
        self.update_name_position()

        self.inputs: List[PortItem] = list()
        self.outputs: List[PortItem] = list()
        self.input_labels: List[QGraphicsTextItem] = list()
        self.output_labels: List[QGraphicsTextItem] = list()



        self.editor_window: DynamicBlockEditorGUI | None = None
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

        name_font = QtGui.QFont("DejaVu Sans", 9)
        name_font.setBold(True)
        self.name_item.setFont(name_font)
        self.update_name_position()

        n_inputs = len(self.subsys.in_vars)
        n_outputs = len(self.subsys.out_vars)
        self.inputs = [PortItem(self, True, i, n_inputs) for i in range(n_inputs)]
        self.outputs = [PortItem(self, False, i, n_outputs) for i in range(n_outputs)]
        self.input_labels = [self.create_port_label_item() for _ in range(n_inputs)]
        self.output_labels = [self.create_port_label_item() for _ in range(n_outputs)]

        self.refresh_port_metadata()
        self.resize_handle = ResizeHandle(self)
        self.resize_to_content()

    def set_dark_mode(self):
        editor_constants = _get_editor_constants()
        self.name_item.setDefaultTextColor(editor_constants.BLOCK_TITLE)
        self.setBrush(QBrush(editor_constants.BLOCK_FILL))
        self.setPen(QPen(editor_constants.BLOCK_BORDER, 1))

    def set_light_mode(self):
        editor_constants = _get_editor_constants()
        self.name_item.setDefaultTextColor(editor_constants.BLOCK_TITLE)
        self.setBrush(QBrush(editor_constants.BLOCK_FILL))
        self.setPen(QPen(editor_constants.BLOCK_BORDER, 1))

    def mousePressEvent(self, event):
        # check if ctrl + click
        if (
                event.button() == Qt.MouseButton.LeftButton
                and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            if self.editor_window is None and self.subsys.is_eq_decomposable():
                self.editor_window = self.editor.new_editor(
                                    var_factory=self.var_factory,
                                    block=self.subsys,
                                    api_object=self.api_object,
                                    circuit=self.editor.circuit,
                                    mode=self.mode,
                )
                if self.editor_window is not None:
                    self.editor_window.decompose_block_in_place(self.subsys)
                    self.editor_window.diagram = self.subsys.diagram
                    self.editor_window.main_block = self.subsys
                    self.editor_window.rebuild_scene_from_diagram()
                    self.editor_window.show()

            elif self.editor_window is None:
                self.editor_window = self.editor.new_editor(
                                    var_factory=self.var_factory,
                                    block=self.subsys,
                                    api_object=self.api_object,
                                    circuit=self.editor.circuit,
                                    mode=self.mode,
                )
                if self.editor_window is not None:
                    self.editor_window.show()

            elif self.editor_window is not None:
                self.editor_window.show()
            else:
                pass
            event.accept()
            return

        # fall back to normal behaviour of mousepressevent
        super().mousePressEvent(event)

    # def mouseDoubleClickEvent(self, event):
    #     if self.editor_window is None and self.subsys.children:
    #         # if self.editor is None:
    #         #     return
    #         # else:
    #         #     pass
    #         # from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
    #         # self.editor_window = DynamicBlockEditorGUI(
    #         #     var_factory=self.var_factory,
    #         #     block=self.subsys,
    #         #     api_object=self.api_object,
    #         #     circuit=self.editor.circuit,
    #         #     mode=self.mode,
    #         # )
    #         self.editor_window = self.editor.new_editor(
    #                 var_factory=self.var_factory,
    #                 block=self.subsys,
    #                 api_object=self.api_object,
    #                 circuit=self.editor.circuit,
    #                 mode=self.mode,
    #         )
    #
    #     elif self.editor_window is None and self.subsys.is_eq_decomposable():
    #         # if self.editor is None:
    #         #     return
    #         # else:
    #         #     pass
    #         # from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
    #         # self.editor_window = DynamicBlockEditorGUI(
    #         #     var_factory=self.var_factory,
    #         #     block=self.subsys,
    #         #     api_object=self.api_object,
    #         #     circuit=self.editor.circuit,
    #         #     mode=self.mode,
    #         # )
    #         self.editor_window = self.editor.new_editor(
    #             var_factory=self.var_factory,
    #             block=self.subsys,
    #             api_object=self.api_object,
    #             circuit=self.editor.circuit,
    #             mode=self.mode,
    #         )
    #         self.editor_window.decompose_block_in_place(self.subsys)
    #         self.editor_window.diagram = self.subsys.diagram
    #         self.editor_window.main_block = self.subsys
    #         self.editor_window.rebuild_scene_from_diagram()
    #     else:
    #         pass
    #
    #     if self.editor_window is not None:
    #         self.editor_window.show()
    #     else:
    #         pass

    def close_editor_window(self) -> None:
        """
        Close the floating child editor associated with this block item.

        :return: None.
        """
        editor_window: DynamicBlockEditorGUI | None = self.editor_window
        if editor_window is None:
            return
        else:
            pass

        # Clear the back-reference first so later scene teardown cannot reuse
        # an editor window that is already on the way out.
        self.editor_window = None
        editor_window.prepare_to_delete()
        editor_window.close()
        editor_window.deleteLater()

    def set_subsystem(self, block: Block) -> None:
        self.subsys = block

    def build_item(self) -> None:
        if self.subsys is not None:
            self.name_item = QGraphicsTextItem(self.name, self)
            editor_constants = _get_editor_constants()
            self.name_item.setDefaultTextColor(editor_constants.BLOCK_TITLE)
            name_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 9)
            name_font.setBold(True)
            self.name_item.setFont(name_font)
            self.update_name_position()

            n_inputs: int = len(self.subsys.in_vars)
            n_outputs: int = len(self.subsys.out_vars)
            self.inputs = [PortItem(self, True, i, n_inputs) for i in range(n_inputs)]
            self.outputs = [PortItem(self, False, i, n_outputs) for i in range(n_outputs)]
            self.input_labels = [self.create_port_label_item() for _ in range(n_inputs)]
            self.output_labels = [self.create_port_label_item() for _ in range(n_outputs)]
            self.refresh_port_metadata()
            self.resize_handle = ResizeHandle(self)
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
        self.resize_handle.setPos(rect.width(), rect.height())
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
        shadow_rect: QtCore.QRectF = outer_rect.translated(2.5, 3.0)
        body_rect: QtCore.QRectF = outer_rect

        editor_constants = _get_editor_constants()

        if self._validation_highlighted:
            border_color: QColor = QColor("#b42318")
        else:
            border_color = (
                editor_constants.BLOCK_BORDER_SELECTED
                if self.isSelected()
                else editor_constants.BLOCK_BORDER
            )

        fill_color: QColor = self.brush().color()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        radius = 4.0

        # body
        painter.setBrush(QBrush(fill_color))
        painter.drawRoundedRect(body_rect, radius, radius)

        # delimiter
        painter.setPen(QPen(border_color, 1.6))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(body_rect, radius, radius)

    def set_validation_highlighted(self, val: bool) -> None:
        """
        Toggle the validation overlay state for this block.

        :param val: Whether the block should be outlined as a validation issue.
        :return: None.
        """
        self._validation_highlighted = val
        self.update()

    def _set_rect_internal(self, w, h):
        QGraphicsRectItem.setRect(self, 0, 0, w, h)
        self.update_ports()
        self.update_handle_position()

    def set_rectangle(self, x, y, w, h):
        if not self._suppress_resize:
            self._set_rect_internal(w, h)
        else:
            pass

    def get_minimum_block_size(self) -> tuple[float, float]:
        editor_constants = _get_editor_constants()
        port_rows: int = max(len(self.inputs), len(self.outputs), 1)
        min_height: float = max(
            editor_constants.BLOCK_MIN_HEIGHT,
            editor_constants.BLOCK_HEADER_HEIGHT + editor_constants.BLOCK_PORT_SECTION_PADDING +
            port_rows * editor_constants.BLOCK_PORT_ROW_HEIGHT
        )

        input_label_width = 0.0
        for label in self.input_labels:
            input_label_width = max(input_label_width, label.boundingRect().width())

        output_label_width = 0.0
        for label in self.output_labels:
            output_label_width = max(output_label_width, label.boundingRect().width())

        name_width = self.name_item.boundingRect().width()
        padding = 28.0

        min_width = max(
            editor_constants.BLOCK_MIN_WIDTH,
            input_label_width + output_label_width + name_width + padding
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
        label_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 9)
        label_item.setFont(label_font)
        label_item.setDefaultTextColor(_get_editor_constants().PORT_LABEL_COLOR)
        label_item.setZValue(4)
        return label_item

    def refresh_port_metadata(self) -> None:
        if self.subsys is not None:
            i: int
            port: PortItem
            label_item: QGraphicsTextItem
            variable_name: str
            for i, port in enumerate(self.inputs):
                if port.base_var is None:
                    port.base_var = self.subsys.in_vars[i]
                else:
                    pass
                variable_name = self.subsys.in_vars[i].name
                port.setToolTip(_build_port_tooltip("Input", i, variable_name))
                label_item = self.input_labels[i]
                label_item.setPlainText(truncate_port_label(variable_name, _get_editor_constants().PORT_LABEL_MAX_CHARS))

            for i, port in enumerate(self.outputs):
                if port.base_var is None:
                    port.base_var = self.subsys.out_vars[i]
                else:
                    pass
                variable_name = self.subsys.out_vars[i].name
                port.setToolTip(_build_port_tooltip("Output", i, variable_name))
                label_item = self.output_labels[i]
                label_item.setPlainText(truncate_port_label(variable_name, _get_editor_constants().PORT_LABEL_MAX_CHARS))
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
            label_item.setPos(14.0, port.pos().y() - 8.0)

        for i, label_item in enumerate(self.output_labels):
            port = self.outputs[i]
            label_width: float = label_item.boundingRect().width()
            label_item.setPos(self.rect().width() - label_width - 14.0, port.pos().y() - 8.0)

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
        QApplication.restoreOverrideCursor()

    def itemChange(self, change, value):
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
                 paired_item: "PairedItem | None" = None,
                 position_changed_callback=None,
                 editor: "DynamicBlockEditorGUI | None" = None):
        super().__init__()
        self._paired_item: PairedItem | None = paired_item
        self.editor: DynamicBlockEditorGUI | None = editor
        self.var_factory = var_factory
        self.subsys = subsys
        self.mode = mode
        self.name: str = name
        self.api_object = api_object
        self.position_changed_callback = position_changed_callback
        self._is_signal_in: bool = bool(self.subsys.in_vars) and not bool(self.subsys.out_vars)

        self.name_item = QGraphicsTextItem(self.subsys.name, self)

        try:
            is_dark = darkdetect.theme() == "Dark"
        except ImportError:
            is_dark = False

        if is_dark:
            self.set_dark_mode()
        else:
            self.set_light_mode()

        name_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 7)
        name_font.setBold(True)
        self.name_item.setFont(name_font)

        self.inputs: List[PortItem] = list()
        self.outputs: List[PortItem] = list()
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)

        n_inputs = len(self.subsys.in_vars)
        n_outputs = len(self.subsys.out_vars)
        self.inputs = [PortItem(self, True, i, n_inputs) for i in range(n_inputs)]
        self.outputs = [PortItem(self, False, i, n_outputs) for i in range(n_outputs)]

        self.refresh_port_metadata()
        self._build_polygon()

    def set_dark_mode(self):
        editor_constants = _get_editor_constants()
        self.name_item.setDefaultTextColor(editor_constants.BLOCK_TITLE)
        self.setBrush(QBrush(editor_constants.BLOCK_FILL))
        self.setPen(QPen(editor_constants.BLOCK_BORDER, 1))

    def set_light_mode(self):
        editor_constants = _get_editor_constants()
        self.name_item.setDefaultTextColor(editor_constants.BLOCK_TITLE)
        self.setBrush(QBrush(editor_constants.BLOCK_FILL))
        self.setPen(QPen(editor_constants.BLOCK_BORDER, 1))

    def rect(self) -> QtCore.QRectF:
        return self.polygon().boundingRect()

    def _build_polygon(self) -> None:
        w = self._LABEL_W
        h = self._LABEL_H
        notch = self._NOTCH_DEPTH
        tip = self._TIP_BASE
        half = h / 2.0
        if self._is_signal_in:
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

        if self._is_signal_in:
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

    def set_paired_item(self, paired_item: "PairedItem") -> None:
        self._paired_item = paired_item

    def set_subsystem(self, block: Block) -> None:
        self.subsys = block

    def build_item(self) -> None:
        if self.subsys is not None:
            self._is_signal_in = bool(self.subsys.in_vars) and not bool(self.subsys.out_vars)

            self.name_item = QGraphicsTextItem(self.name, self)
            editor_constants = _get_editor_constants()
            self.name_item.setDefaultTextColor(editor_constants.BLOCK_TITLE)
            name_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 7)
            name_font.setBold(True)
            self.name_item.setFont(name_font)
            self.setBrush(QBrush(editor_constants.BLOCK_FILL))

            n_inputs: int = len(self.subsys.in_vars)
            n_outputs: int = len(self.subsys.out_vars)
            self.inputs = [PortItem(self, True, i, n_inputs) for i in range(n_inputs)]
            self.outputs = [PortItem(self, False, i, n_outputs) for i in range(n_outputs)]
            self.refresh_port_metadata()
            self._build_polygon()
        else:
            pass

    def resize_block(self, width, height):
        pass

    def update_handle_position(self):
        pass

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        polygon: QtGui.QPolygonF = self.polygon()
        editor_constants = _get_editor_constants()
        border_color: QColor = editor_constants.BLOCK_BORDER_SELECTED if self.isSelected() else editor_constants.BLOCK_BORDER
        fill_color: QColor = self.brush().color()

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        shadow_poly = polygon.translated(2.5, 3.0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(editor_constants.BLOCK_SHADOW))
        painter.drawPolygon(shadow_poly)
        painter.setBrush(QBrush(fill_color))
        painter.drawPolygon(polygon)
        painter.setPen(QPen(border_color, 1.6))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolygon(polygon)

    def _set_rect_internal(self, w, h):
        pass

    def set_rectangle(self, x, y, w, h):
        pass

    def get_minimum_block_size(self) -> tuple[float, float]:
        return self._LABEL_W, self._LABEL_H

    def resize_to_content(self) -> None:
        self._build_polygon()

    def refresh_port_metadata(self) -> None:
        if self.subsys is not None:
            i: int
            port: PortItem
            variable_name: str
            for i, port in enumerate(self.inputs):
                if port.base_var is None:
                    port.base_var = self.subsys.in_vars[i]
                else:
                    pass
                variable_name = self.subsys.in_vars[i].name
                port.setToolTip(_build_port_tooltip("Input", i, variable_name))

            for i, port in enumerate(self.outputs):
                if port.base_var is None:
                    port.base_var = self.subsys.out_vars[i]
                else:
                    pass
                variable_name = self.subsys.out_vars[i].name
                port.setToolTip(_build_port_tooltip("Output", i, variable_name))
        else:
            pass

        if self._paired_item is not None:
            other = self._paired_item
            other._paired_item = None
            other.refresh_port_metadata()
            other._paired_item = self
        else:
            pass

    def update_ports(self):
        self._position_name_and_ports()

    def hoverEnterEvent(self, event):
        QApplication.setOverrideCursor(Qt.CursorShape.OpenHandCursor)

    def hoverLeaveEvent(self, event):
        QApplication.restoreOverrideCursor()

    def contextMenuEvent(self, event):
        if not self._is_signal_in and self._paired_item is not None:
            menu = QMenu()
            duplicate_action = QAction("Duplicate", menu)
            duplicate_action.triggered.connect(lambda: duplicate_paired_item(self))
            menu.addAction(duplicate_action)
            menu.exec(event.screenPos())
        else:
            super().contextMenuEvent(event)

    def itemChange(self, change, value):
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


def duplicate_paired_item(original: PairedItem) -> PairedItem | None:
    if original.editor is None or original._is_signal_in or original._paired_item is None:
        return None

    editor = original.editor
    from_item = original._paired_item
    var_factory = original.var_factory

    shared_var = var_factory.add_var("var_to")
    shared_var.uid = from_item.subsys.in_vars[0].uid

    blk_new = Block(
        # algebraic_vars=[shared_var],
        out_vars=[shared_var],
        name=original.name,
    )

    editor.main_block.add(blk_new)

    new_item = PairedItem(
        editor=editor,
        var_factory=var_factory,
        subsys=blk_new,
        api_object=original.api_object,
        mode=original.mode,
        name=blk_new.name,
        paired_item=from_item,
        position_changed_callback=editor._build_position_changed_callback(blk_new.uid),
    )
    new_item.setPos(original.pos() + QPointF(0.0, 80.0))
    editor.scene.addItem(new_item)
    editor.diagram.add_node(
        name=blk_new.name,
        x=original.pos().x(),
        y=original.pos().y() + 80.0,
        tpe="signal_out",
        device_uid=blk_new.uid,
    )

    editor.mark_unapplied_changes()
    return new_item


class BlockItem(QGraphicsRectItem):
    def __init__(self,
                 var_factory: VarFactory,
                 name: str,
                 api_object=None,
                 mode: DynamicSimulationMode = None,
                 position_changed_callback=None,
                 editor: "DynamicBlockEditorGUI | None" = None):
        super().__init__(0, 0, 80, 40)
        self.editor: DynamicBlockEditorGUI | None = editor
        self.var_factory: VarFactory = var_factory
        self.api_object = api_object
        self.mode = mode
        self.name: str = name
        self.position_changed_callback = position_changed_callback
        self.resize_handle: ResizeHandle | None = None
        self.resizing_from_handle: bool = False
        self.subsys: Block | None = None
        self.editor_window: DynamicBlockEditorGUI | None = None
        self.name_item: QGraphicsTextItem | None = None

        try:
            is_dark = darkdetect.theme() == "Dark"
        except ImportError:
            is_dark = False

        if is_dark:
            self.set_dark_mode()
        else:
            self.set_light_mode()

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
        self.setPen(
            QPen(
                QColor("#202124"),
                1.6
            )
        )

        self.setBrush(
            QBrush(
                QColor("#f5fdff")
            )
        )

    def set_dark_mode(self):
        editor_constants = _get_editor_constants()
        if self.name_item is not None:
            self.name_item.setDefaultTextColor(editor_constants.BLOCK_TITLE)
        self.setBrush(QBrush(editor_constants.BLOCK_FILL))
        self.setPen(QPen(editor_constants.BLOCK_BORDER, 1))

    def set_light_mode(self):
        editor_constants = _get_editor_constants()
        if self.name_item is not None:
            self.name_item.setDefaultTextColor(editor_constants.BLOCK_TITLE)
        self.setBrush(QBrush(editor_constants.BLOCK_FILL))
        self.setPen(QPen(editor_constants.BLOCK_BORDER, 1))

    def set_subsystem(self, block: Block) -> None:
        self.subsys = block

    def build_item(self) -> None:
        if self.subsys is not None:
            self.name_item = QGraphicsTextItem(self.name, self)
            editor_constants = _get_editor_constants()
            self.name_item.setDefaultTextColor(editor_constants.BLOCK_TITLE)
            name_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 7)
            name_font.setBold(True)
            self.name_item.setFont(name_font)

            n_inputs: int = len(self.subsys.in_vars)
            n_outputs: int = len(self.subsys.out_vars)
            self.inputs = [PortItem(self, True, i, n_inputs) for i in range(n_inputs)]
            self.outputs = [PortItem(self, False, i, n_outputs) for i in range(n_outputs)]
            # self.input_labels = [self.create_port_label_item() for _ in range(n_inputs)]
            # self.output_labels = [self.create_port_label_item() for _ in range(n_outputs)]
            self.refresh_port_metadata()

            self.resize_to_content()
        else:
            pass

    def create_port_label_item(self) -> QGraphicsTextItem:
        label_item: QGraphicsTextItem = QGraphicsTextItem("", self)
        label_font: QtGui.QFont = QtGui.QFont("DejaVu Sans", 7)
        label_item.setFont(label_font)
        label_item.setDefaultTextColor(_get_editor_constants().PORT_LABEL_COLOR)
        label_item.setZValue(4)
        return label_item

    def get_minimum_block_size(self) -> tuple[float, float]:
        editor_constants = _get_editor_constants()
        port_rows: int = max(len(self.inputs), len(self.outputs), 1)
        min_height: float = max(
            editor_constants.BLOCK_COMPACT_MIN_HEIGHT,
            editor_constants.BLOCK_COMPACT_HEADER_HEIGHT + editor_constants.BLOCK_COMPACT_PORT_SECTION_PADDING +
            port_rows * editor_constants.BLOCK_COMPACT_PORT_ROW_HEIGHT
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
        min_width = max(editor_constants.BLOCK_COMPACT_MIN_WIDTH, name_width + 10, port_width + 20)
        return min_width, min_height

    def resize_to_content(self) -> None:
        self.prepareGeometryChange()
        min_width: float
        min_height: float
        min_width, min_height = self.get_minimum_block_size()
        QGraphicsRectItem.setRect(self, 0, 0, min_width, min_height)
        self.update_ports()
        self.update_handle_position()
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
                if port.base_var is None:
                    port.base_var = self.subsys.in_vars[i]
                else:
                    pass
                variable_name = self.subsys.in_vars[i].name
                port.setToolTip(_build_port_tooltip("Input", i, variable_name))
                # label_item = self.input_labels[i]
                # label_item.setPlainText(truncate_port_label(variable_name, _get_editor_constants(self.editor).PORT_LABEL_MAX_CHARS))

            for i, port in enumerate(self.outputs):
                if port.base_var is None:
                    port.base_var = self.subsys.out_vars[i]
                else:
                    pass
                variable_name = self.subsys.out_vars[i].name
                port.setToolTip(_build_port_tooltip("Output", i, variable_name))
                # label_item = self.output_labels[i]
                # label_item.setPlainText(truncate_port_label(variable_name, _get_editor_constants(self.editor).PORT_LABEL_MAX_CHARS))
        else:
            pass

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        rect: QtCore.QRectF = self.rect()
        outer_rect: QtCore.QRectF = rect.adjusted(2, 2, -2, -2)
        shadow_rect: QtCore.QRectF = outer_rect.translated(2.5, 3.0)
        body_rect: QtCore.QRectF = outer_rect
        radius: float = body_rect.height() / 2.0

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # body
        painter.setBrush(QBrush(QColor("#f5fdff")))
        painter.drawRoundedRect(body_rect, radius, radius)

        # border
        if self._validation_highlighted:
            border_color: QColor = QColor("#b42318")
        else:
            border_color = QColor("#202124")

        painter.setPen(QPen(border_color, 1.6))
        painter.setBrush(Qt.BrushStyle.NoBrush)
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

    def update_handle_position(self) -> None:
        rect = self.rect()
        if self.resize_handle is not None:
            self.resizing_from_handle = False
            self.resize_handle.setPos(rect.width(), rect.height())
            self.resizing_from_handle = True
        else:
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

        self.update_handle_position()
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

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
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

    def close_editor_window(self) -> None:
        """
        Close the floating child editor associated with this block item.

        :return: None.
        """
        editor_window: DynamicBlockEditorGUI | None = self.editor_window
        if editor_window is None:
            return
        else:
            pass

        # Clear the back-reference first so later scene teardown cannot reuse
        # an editor window that is already on the way out.
        self.editor_window = None
        editor_window.prepare_to_delete()
        editor_window.close()
        editor_window.deleteLater()


class ProtectedConnectionBlockItem(BlockItem):
    pass


class RoundBaseArithmeticOpItem(QGraphicsEllipseItem):
    def __init__(self,
                 subsys: Block,
                 var_factory: VarFactory,
                 block_type: BlockType, 
                 editor: "DynamicBlockEditorGUI | None" = None,
                 position_changed_callback = None):
        size = 48.0
        super().__init__(-size / 2, -size / 2, size, size)
        self.block_type: BlockType = block_type
        self.subsys: Block = subsys
        self.var_factory: VarFactory = var_factory
        self.editor: "DynamicBlockEditorGUI | None" = editor
        self.inputs: List[PortItem] = list()
        self.outputs: List[PortItem] = list()
        self.input_labels: List[QGraphicsTextItem] = list()
        self._input_signs: List[str] = list()

        try:
            is_dark = darkdetect.theme() == "Dark"
        except ImportError:
            is_dark = False

        if is_dark:
            self.set_dark_mode()
        else:
            self.set_light_mode()

        n_inputs = len(self.subsys.in_vars)
        if n_inputs > 3:
            raise ValueError("SumItem only supports up to 3 input ports")
        n_outputs = len(self.subsys.out_vars)
        for i in range(n_inputs):
            port = PortItem(self, True, i, n_inputs)
            self.inputs.append(port)
            label = QGraphicsTextItem("", self)
            label_font = QtGui.QFont("DejaVu Sans", 8)
            label.setFont(label_font)
            label.setDefaultTextColor(QColor("#173042"))
            self.input_labels.append(label)

        for i in range(n_outputs):
            port = PortItem(self, False, i, n_outputs)
            self.outputs.append(port)


        self._analyze_input_signs()
        self.update_ports()

        self.setPen(QPen(QColor("#202124"), 1.6))
        self.setBrush(QBrush(QColor("#f5fdff")))
        self.setZValue(2)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)

    def set_dark_mode(self):
        editor_constants = _get_editor_constants()
        self.name_item.setDefaultTextColor(editor_constants.BLOCK_TITLE)
        self.setBrush(QBrush(editor_constants.BLOCK_BORDER))
        self.setPen(QPen(editor_constants.BLOCK_FILL, 1))

    def set_light_mode(self):
        editor_constants = _get_editor_constants()
        self.name_item.setDefaultTextColor(editor_constants.BLOCK_TITLE)
        self.setBrush(QBrush(editor_constants.BLOCK_BORDER))
        self.setPen(QPen(editor_constants.BLOCK_FILL, 1))

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

            tw = label.boundingRect().width()
            th = label.boundingRect().height()

            if n_inputs == 1:
                label.setPos(port.pos().x(), port.pos().y() - th / 2)
            elif n_inputs == 2:
                if i == 0:
                    label.setPos(port.pos().x() - tw / 2, port.pos().y())
                else:
                    label.setPos(port.pos().x(), port.pos().y() - th / 2)
            elif n_inputs == 3:
                if i == 0:
                    label.setPos(port.pos().x() - tw / 2, port.pos().y())
                elif i == 1:
                    label.setPos(port.pos().x(), port.pos().y() - th / 2)
                else:
                    label.setPos(port.pos().x() - tw / 2, port.pos().y() - th)

    def paint(self,
              painter: QPainter,
              option: QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[QWidget] = None) -> None:
        rect = self.rect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setBrush(QBrush(QColor("#f5fdff")))
        painter.setPen(QPen(QColor("#202124"), 1.6))
        painter.drawEllipse(rect)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
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
                 editor: "DynamicBlockEditorGUI | None" = None,
                 position_changed_callback=None):
        n_inputs = len(subsys.in_vars)
        n_outputs = len(subsys.out_vars)
        width = 50.0
        height = max(60.0, n_inputs * 28.0)
        super().__init__(0, 0, width, height)
        self.block_type: BlockType = block_type
        self.subsys: Block = subsys
        self.var_factory: VarFactory = var_factory
        self.editor: "DynamicBlockEditorGUI | None" = editor
        self.inputs: List[PortItem] = list()
        self.outputs: List[PortItem] = list()
        self.input_labels: List[QGraphicsTextItem] = list()
        self._input_signs: List[str] = list()

        for i in range(n_inputs):
            port = PortItem(self, True, i, n_inputs)
            self.inputs.append(port)
            label = QGraphicsTextItem("", self)
            label_font = QtGui.QFont("DejaVu Sans", 8)
            label.setFont(label_font)
            label.setDefaultTextColor(QColor("#173042"))
            self.input_labels.append(label)

        for i in range(n_outputs):
            port = PortItem(self, False, i, n_outputs)
            self.outputs.append(port)

        self._analyze_input_signs()
        self.update_ports()

        self.setPen(QPen(QColor("#202124"), 1.6))
        self.setBrush(QBrush(QColor("#f5fdff")))
        self.setZValue(2)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)

    def set_dark_mode(self):
        pass

    def set_light_mode(self):
        pass

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
        painter.setBrush(QBrush(QColor("#f5fdff")))
        painter.setPen(QPen(QColor("#202124"), 1.6))
        painter.drawRoundedRect(rect, 6.0, 6.0)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
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
            if event.button() == Qt.MouseButton.LeftButton and bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier):
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
        self.editor: DynamicBlockEditorGUI = editor
        self.temp_line: QGraphicsPathItem | None = None
        self.source_port: PortItem | BranchingItem | None = None
        self.context_item: BlockItem | ConnectionItem | None = None

    def get_modal_template_metadata(self, block: Block | None) -> tuple[str | None, Dict[str, Any] | None]:
        return self.editor.get_modal_template_metadata(block)

    def change_item_fill_color(self, item: BlockItem | GenericBlockItem | ConnectionItem) -> None:
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

    def contextMenuEvent(self, event: QtWidgets.QGraphicsSceneContextMenuEvent) -> None:
        item: QGraphicsItem
        for item in self.items(event.scenePos()):
            if isinstance(item, (GenericBlockItem, ConnectionItem, RoundBaseArithmeticOpItem, RectBaseArithmeticOpItem)):
                menu: QMenu = QMenu()
                if item is not None:
                    self.context_item = item

                    remove_action: QAction = QAction("Remove", menu)
                    remove_action.triggered.connect(self.remove_context_item)
                    menu.addAction(remove_action)

                    color_action: QAction = QAction("Change Color", menu)
                    color_action.triggered.connect(self.recolor_context_item)
                    menu.addAction(color_action)


                    menu.exec(event.screenPos())
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
                    try:
                        is_dark = darkdetect.theme() == "Dark"
                    except ImportError:
                        is_dark = False
                    print(is_dark)
                    #
                    # pen: QPen = QPen(QColor("white"), 1, Qt.PenStyle.DashLine) if is_dark else QPen(
                    #     QColor("black"), 1, Qt.PenStyle.DashLine)
                    pen: QPen = QPen(QColor("black"), 1, Qt.PenStyle.DashLine)
                    self.temp_line = self.addPath(path, pen)
                    return
                else:
                    pass

            if isinstance(item, BranchingItem):
                self.source_port = item
                path = QPainterPath(item.scenePos())
                try:
                    is_dark = darkdetect.theme() == "Dark"
                except ImportError:
                    is_dark = False

                pen = QPen(QColor("white"), 1, Qt.PenStyle.DashLine) if is_dark else QPen(Qt.PenStyle.DashLine)
                self.temp_line = self.addPath(path, pen)
                return
            else:
                pass

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if self.temp_line is not None:
            if self.source_port is not None:
                start: QPointF = self.source_port.scenePos()
                end: QPointF = event.scenePos()
                path: QPainterPath = build_orthogonal_connection_path(start, end, self.editor.WIRE_ELBOW_OFFSET)
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
        super().mouseDoubleClickEvent(event)

    def connect_ports(self, source_port: PortItem | BranchingItem, target_port: PortItem) -> None:
        source_block: BlockItem | GenericBlockItem | PairedItem = source_port.subsystem
        target_block: BlockItem | GenericBlockItem | PairedItem = target_port.subsystem

        if source_block.subsys is not None and target_block.subsys is not None:
            connection: ConnectionItem = ConnectionItem(
                source_port,
                target_port,
                diagram=self.editor.diagram,
                editor=self.editor,
            )

            dst_var: Var = source_block.subsys.out_vars[source_port.index]
            target_input_var: Var = target_block.subsys.in_vars[target_port.index]

            if target_input_var.network_conn:
                self.editor.var_factory.add_connection(dst_var, target_input_var)
                source_block.refresh_port_metadata()
            else:
                self.editor.var_factory.add_connection(target_input_var, dst_var)
                if not isinstance(target_block, (RoundBaseArithmeticOpItem, RectBaseArithmeticOpItem)):
                    target_block.refresh_port_metadata()
            self.addItem(connection)

            self.editor.diagram.add_branch(
                connectionitem_uid=connection.uid,
                device_uid_from=source_block.subsys.uid,
                device_uid_to=target_block.subsys.uid,
                port_number_from=source_port.index,
                port_number_to=target_port.index,
                color=connection.pen().color().name(),
                elbow_points=list()
            )
        else:
            pass
