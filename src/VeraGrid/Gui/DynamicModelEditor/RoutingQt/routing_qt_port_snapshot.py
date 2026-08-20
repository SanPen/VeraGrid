# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsRectItem

from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingPoint
from VeraGridEngine.enumerations import RoutingPortSide
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_graphics import PortItem


class QtRoutingPortSnapshot:
    """
    Store one Qt port snapshot for the new routing engine.

    :return: None.
    """

    __slots__ = ("_block_uid", "_port_index", "_is_input", "_position", "_port_side")

    def __init__(
            self,
            block_uid: int,
            port_index: int,
            is_input: bool,
            position: RoutingPoint,
            port_side: RoutingPortSide,
    ) -> None:
        """
        Build one Qt routing port snapshot.

        :param block_uid: Owning block identifier.
        :param port_index: Port index on the block.
        :param is_input: Whether the port is one input port.
        :param position: Port position in scene coordinates.
        :param port_side: Physical block side where the port is attached.
        :return: None.
        """
        self._block_uid: int = int(block_uid)
        self._port_index: int = int(port_index)
        self._is_input: bool = bool(is_input)
        self._position: RoutingPoint = position
        self._port_side: RoutingPortSide = port_side

    def get_port_index(self) -> int:
        """
        :return: Port index.
        """
        return self._port_index

    def get_position(self) -> RoutingPoint:
        """
        :return: Scene-space port position.
        """
        return self._position

    def get_port_side(self) -> RoutingPortSide:
        """
        :return: Physical block side of the port.
        """
        return self._port_side


def _resolve_port_side(port_item: PortItem) -> RoutingPortSide:
    """
    Resolve the physical block side of one Qt port.

    The side is determined exactly once in the Qt layer and then propagated
    into the routing model. The engine never needs to re-deduce this property
    from graphics again.

    :param port_item: Qt port item to inspect.
    :return: Physical block side of the port.
    """
    parent_item: object = port_item.subsystem
    if isinstance(parent_item, QGraphicsRectItem):
        # When the parent is one plain block rectangle, the nearest rectangle
        # side is the most direct and stable physical-side definition.
        rect = parent_item.rect()
        local_position: QPointF = port_item.pos()
        left_distance: float = abs(local_position.x() - rect.left())
        right_distance: float = abs(local_position.x() - rect.right())
        top_distance: float = abs(local_position.y() - rect.top())
        bottom_distance: float = abs(local_position.y() - rect.bottom())
        minimum_distance: float = min(left_distance, right_distance, top_distance, bottom_distance)

        if minimum_distance == left_distance:
            return RoutingPortSide.LEFT
        elif minimum_distance == right_distance:
            return RoutingPortSide.RIGHT
        elif minimum_distance == top_distance:
            return RoutingPortSide.TOP
        else:
            return RoutingPortSide.BOTTOM
    elif port_item.is_input:
        # The fallback keeps the current editor convention for non-rectangular
        # or legacy parents: inputs attach on the left and outputs on the right.
        return RoutingPortSide.LEFT
    else:
        return RoutingPortSide.RIGHT


def build_qt_routing_port_snapshot(port_item: PortItem) -> QtRoutingPortSnapshot:
    """
    Build one immutable snapshot from one live Qt port item.

    :param port_item: Qt port item to snapshot.
    :return: Immutable Qt routing port snapshot.
    """
    # The Qt layer resolves all live graphics data once and freezes it into a
    # plain snapshot so the routing engine never depends on mutable Qt items.
    scene_position: QPointF = port_item.scenePos()
    routing_point: RoutingPoint = RoutingPoint(scene_position.x(), scene_position.y())
    port_snapshot: QtRoutingPortSnapshot = QtRoutingPortSnapshot(
        block_uid=int(port_item.subsystem.subsys.uid),
        port_index=int(port_item.index),
        is_input=bool(port_item.is_input),
        position=routing_point,
        port_side=_resolve_port_side(port_item),
    )
    return port_snapshot
