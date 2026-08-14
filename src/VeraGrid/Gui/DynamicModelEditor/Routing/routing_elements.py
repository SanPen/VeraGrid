# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from enum import Enum

from VeraGridEngine.enumerations import RoutingAxis, RoutingPortSide

class RoutingPoint:
    """
    Store one engine-space 2D point.

    :returns: None.
    """

    __slots__ = ("_x", "_y")

    def __init__(self, x_pos: float, y_pos: float) -> None:
        """
        Build one point.

        :param x_pos: Horizontal coordinate.
        :param y_pos: Vertical coordinate.
        :returns: None.
        """
        self._x: float = float(x_pos)
        self._y: float = float(y_pos)

    def get_x(self) -> float:
        """
        Return the horizontal coordinate.

        :returns: Horizontal coordinate.
        """
        return self._x

    def get_y(self) -> float:
        """
        Return the vertical coordinate.

        :returns: Vertical coordinate.
        """
        return self._y

    def set_x(self, x_pos: float) -> None:
        """
        Set the horizontal coordinate.

        :param x_pos: New horizontal coordinate.
        :returns: None.
        """
        self._x = float(x_pos)

    def set_y(self, y_pos: float) -> None:
        """
        Set the vertical coordinate.

        :param y_pos: New vertical coordinate.
        :returns: None.
        """
        self._y = float(y_pos)

    def copy(self) -> "RoutingPoint":
        """
        Build a copy of the point.

        :returns: Point copy.
        """
        point_copy: RoutingPoint = RoutingPoint(self._x, self._y)
        return point_copy


class RoutingNodeKind(Enum):
    """
    Enumerate the supported node kinds in Phase 1.

    :returns: Enumeration values describing supported node kinds.
    """

    PORT = "port"
    STUB = "stub"
    ELBOW = "elbow"


class RoutingNode:
    """
    Represent one topological routing node.

    :returns: None.
    """

    __slots__ = ("_node_id", "_kind", "_position", "_incident_segment_ids", "_port_side")

    def __init__(
            self,
            node_id: int,
            kind: RoutingNodeKind,
            position: RoutingPoint,
            port_side: RoutingPortSide | None = None,
    ) -> None:
        """
        Build one routing node.

        :param node_id: Stable node identifier.
        :param kind: Node kind.
        :param position: Node position.
        :param port_side: Physical block side for port nodes.
        :returns: None.
        """
        self._node_id: int = int(node_id)
        self._kind: RoutingNodeKind = kind
        self._position: RoutingPoint = position
        self._incident_segment_ids: list[int] = list()
        self._port_side: RoutingPortSide | None = port_side

    def get_node_id(self) -> int:
        """
        Return the stable node identifier.

        :returns: Stable node identifier.
        """
        return self._node_id

    def get_kind(self) -> RoutingNodeKind:
        """
        Return the node kind.

        :returns: Node kind.
        """
        return self._kind

    def get_position(self) -> RoutingPoint:
        """
        Return the node position.

        :returns: Node position.
        """
        return self._position

    def set_position(self, position: RoutingPoint) -> None:
        """
        Set the node position.

        :param position: New node position.
        :returns: None.
        """
        self._position = position

    def has_port_side(self) -> bool:
        """
        Return whether this node carries one physical port-side value.

        :returns: ``True`` when the node stores one physical port side.
        """
        if self._kind != RoutingNodeKind.PORT:
            return False
        elif self._port_side is None:
            return False
        else:
            return True

    def get_port_side(self) -> RoutingPortSide | None:
        """
        Return the physical block side for this node when available.

        :returns: Physical port side or ``None``.
        """
        return self._port_side

    def set_port_side(self, port_side: RoutingPortSide | None) -> None:
        """
        Set the physical block side for this node.

        :param port_side: Physical port side or ``None``.
        :returns: None.
        """
        self._port_side = port_side

    def get_incident_segment_ids(self) -> list[int]:
        """
        Return the incident segment identifiers.

        :returns: Incident segment identifiers.
        """
        return list(self._incident_segment_ids)

    def add_incident_segment_id(self, segment_id: int) -> bool:
        """
        Attach one incident segment identifier to the node.

        :param segment_id: Incident segment identifier.
        :returns: ``True`` when the identifier was added.
        """
        segment_identifier: int = int(segment_id)

        # The node owns its local adjacency so degree and traversal remain
        # simple and do not require scanning every segment in the graph.
        if segment_identifier in self._incident_segment_ids:
            return False
        else:
            self._incident_segment_ids.append(segment_identifier)
            return True

    def remove_incident_segment_id(self, segment_id: int) -> bool:
        """
        Remove one incident segment identifier from the node.

        :param segment_id: Incident segment identifier.
        :returns: ``True`` when the identifier was removed.
        """
        segment_identifier: int = int(segment_id)
        if segment_identifier in self._incident_segment_ids:
            self._incident_segment_ids.remove(segment_identifier)
            return True
        else:
            return False

    def clone(self) -> "RoutingNode":
        """
        Build a detached copy of the node.

        :returns: Node copy.
        """
        node_copy: RoutingNode = RoutingNode(
            node_id=self._node_id,
            kind=self._kind,
            position=self._position.copy(),
            port_side=self._port_side,
        )
        segment_id: int
        for segment_id in self._incident_segment_ids:
            node_copy.add_incident_segment_id(segment_id)
        return node_copy


class RoutingSegment:
    """
    Represent one routing edge between exactly two nodes.

    :returns: None.
    """

    __slots__ = ("_segment_id", "_start_node_id", "_end_node_id")

    def __init__(self, segment_id: int, start_node_id: int, end_node_id: int) -> None:
        """
        Build one routing segment.

        :param segment_id: Stable segment identifier.
        :param start_node_id: Start node identifier.
        :param end_node_id: End node identifier.
        :returns: None.
        """
        self._segment_id: int = int(segment_id)
        self._start_node_id: int = int(start_node_id)
        self._end_node_id: int = int(end_node_id)

    def get_segment_id(self) -> int:
        """
        Return the stable segment identifier.

        :returns: Stable segment identifier.
        """
        return self._segment_id

    def get_start_node_id(self) -> int:
        """
        Return the start node identifier.

        :returns: Start node identifier.
        """
        return self._start_node_id

    def get_end_node_id(self) -> int:
        """
        Return the end node identifier.

        :returns: End node identifier.
        """
        return self._end_node_id

    def get_other_node_id(self, node_id: int) -> int | None:
        """
        Return the opposite node identifier when the given node belongs to the segment.

        :param node_id: Known endpoint identifier.
        :returns: Opposite endpoint identifier or ``None``.
        """
        node_identifier: int = int(node_id)
        if node_identifier == self._start_node_id:
            return self._end_node_id
        elif node_identifier == self._end_node_id:
            return self._start_node_id
        else:
            return None

    def clone(self) -> "RoutingSegment":
        """
        Build a detached copy of the segment.

        :returns: Segment copy.
        """
        segment_copy: RoutingSegment = RoutingSegment(
            segment_id=self._segment_id,
            start_node_id=self._start_node_id,
            end_node_id=self._end_node_id,
        )
        return segment_copy


def derive_segment_axis(
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
) -> RoutingAxis | None:
    """
    Derive the axis of one segment from its endpoint coordinates.

    This helper stays inside ``routing_elements`` so the element model remains
    self-contained after the module consolidation. It mirrors the shared visual
    alignment criterion used by ``RoutingGeometry`` without importing that
    helper, which would create a circular dependency now that both points and
    port sides live in this module.

    :param start_x: Start x coordinate.
    :param start_y: Start y coordinate.
    :param end_x: End x coordinate.
    :param end_y: End y coordinate.
    :returns: Derived axis or ``None`` when the segment is diagonal or null.
    """
    numerical_epsilon: float = 1.0e-9
    visual_alignment_threshold: float = 3.0
    delta_x: float = abs(float(start_x) - float(end_x))
    delta_y: float = abs(float(start_y) - float(end_y))
    same_x: bool = delta_x <= visual_alignment_threshold
    same_y: bool = delta_y <= visual_alignment_threshold

    if same_y and not same_x:
        return RoutingAxis.HORIZONTAL
    elif same_x and not same_y:
        return RoutingAxis.VERTICAL
    elif same_x and same_y:
        if delta_x <= numerical_epsilon and delta_y <= numerical_epsilon:
            return None
        elif delta_x >= delta_y:
            return RoutingAxis.HORIZONTAL
        else:
            return RoutingAxis.VERTICAL
    else:
        return None
