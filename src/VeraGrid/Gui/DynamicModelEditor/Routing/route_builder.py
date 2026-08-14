# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingNode
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingNodeKind
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingPoint
from VeraGridEngine.enumerations import RoutingPortSide
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingSegment
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_graph import RoutingGraph
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_geometry import RoutingGeometry


class RouteBuilder:
    """
    Build one deterministic orthogonal routing graph between two ports.

    :returns: None.
    """

    __slots__ = (
        "_source_position",
        "_destination_position",
        "_source_port_side",
        "_destination_port_side",
        "_geometry",
    )

    def __init__(
            self,
            source_position: RoutingPoint,
            destination_position: RoutingPoint,
            source_port_side: RoutingPortSide,
            destination_port_side: RoutingPortSide,
    ) -> None:
        """
        Build one route builder.

        :param source_position: Source port position.
        :param destination_position: Destination port position.
        :param source_port_side: Physical side of the source port on its block.
        :param destination_port_side: Physical side of the destination port on its block.
        :returns: None.
        """
        self._source_position: RoutingPoint = source_position.copy()
        self._destination_position: RoutingPoint = destination_position.copy()
        self._source_port_side: RoutingPortSide = source_port_side
        self._destination_port_side: RoutingPortSide = destination_port_side
        self._geometry: RoutingGeometry = RoutingGeometry()

    def build(self) -> RoutingGraph:
        """
        Build one deterministic orthogonal graph.

        :returns: Built routing graph.
        """
        routing_graph: RoutingGraph = RoutingGraph(source_node_id=1, destination_node_id=2)
        source_node: RoutingNode = RoutingNode(
            node_id=1,
            kind=RoutingNodeKind.PORT,
            position=self._source_position.copy(),
            port_side=self._source_port_side,
        )
        destination_node: RoutingNode = RoutingNode(
            node_id=2,
            kind=RoutingNodeKind.PORT,
            position=self._destination_position.copy(),
            port_side=self._destination_port_side,
        )

        # Graph creation is the only place that may construct topology from
        # scratch. All later user interaction must transform the existing graph.
        routing_graph._add_node(source_node)
        routing_graph._add_node(destination_node)

        self._build_stub_topology(routing_graph)

        return routing_graph

    def _build_stub_topology(self, routing_graph: RoutingGraph) -> None:
        """
        Build the route by reusing the existing central path between two stubs.

        The builder still uses the same deterministic orthogonal route
        algorithm for the interior geometry. The only difference is that the
        effective endpoints of that interior route are the two stub points
        rather than the two ports themselves.

        :param routing_graph: Graph under construction.
        :returns: None.
        """
        route_points: list[RoutingPoint] = self._build_stubbed_route_points()
        # The builder owns the only topology-from-scratch step. Once the full
        # point chain is known, the graph is materialized in one deterministic
        # pass so later editor operations only transform existing nodes.
        self._build_graph_from_route_points(routing_graph, route_points)

    def _build_stubbed_route_points(self) -> list[RoutingPoint]:
        """
        Build one full route including both terminal stubs.

        :returns: Route points including both ports and both stubs.
        """
        route_points: list[RoutingPoint] = list()
        source_stub: RoutingPoint = self._build_stub_point(
            port_position=self._source_position,
            port_side=self._source_port_side,
        )
        destination_stub: RoutingPoint = self._build_stub_point(
            port_position=self._destination_position,
            port_side=self._destination_port_side,
        )
        # The central route keeps the legacy minimal dogleg algorithm. Only the
        # effective endpoints change from the ports themselves to the stub
        # endpoints, so the visible construction policy stays simple.
        inner_route_points: list[RoutingPoint] = self._build_minimal_route_points(
            start_position=source_stub,
            end_position=destination_stub,
        )

        # The final point chain always includes both real ports so the graph
        # keeps explicit topology for the physical block attachment points.
        route_points.append(self._source_position.copy())
        inner_point: RoutingPoint
        for inner_point in inner_route_points:
            route_points.append(inner_point.copy())
        route_points.append(self._destination_position.copy())
        return route_points

    def _build_minimal_route_points(
            self,
            start_position: RoutingPoint,
            end_position: RoutingPoint,
    ) -> list[RoutingPoint]:
        """
        Build the existing minimal orthogonal route between two endpoints.

        :param start_position: Effective route start.
        :param end_position: Effective route end.
        :returns: Ordered route points including both endpoints.
        """
        route_points: list[RoutingPoint] = list()
        route_points.append(start_position.copy())

        if self._geometry.are_x_aligned(start_position, end_position):
            route_points.append(end_position.copy())
        elif self._geometry.are_y_aligned(start_position, end_position):
            route_points.append(end_position.copy())
        else:
            # The minimal non-aligned route still uses one deterministic elbow.
            # More advanced path construction belongs to future routing phases,
            # not to this foundational builder.
            elbow_point: RoutingPoint = RoutingPoint(
                x_pos=end_position.get_x(),
                y_pos=start_position.get_y(),
            )
            route_points.append(elbow_point)
            route_points.append(end_position.copy())

        return route_points

    def _build_stub_point(self, port_position: RoutingPoint, port_side: RoutingPortSide) -> RoutingPoint:
        """
        Build one stub point offset from a port along its physical side.

        :param port_position: Port position.
        :param port_side: Physical side of the port.
        :returns: Stub endpoint.
        """
        return self._geometry.build_port_stub_point(
            port_position=port_position,
            port_side=port_side,
        )

    def _build_graph_from_route_points(
            self,
            routing_graph: RoutingGraph,
            route_points: list[RoutingPoint],
    ) -> None:
        """
        Materialize one ordered route-point chain as one routing graph.

        :param routing_graph: Graph under construction.
        :param route_points: Ordered route points including both ports.
        :returns: None.
        """
        node_ids: list[int] = [1]
        next_node_id: int = 3
        interior_point_count: int = len(route_points) - 2
        point_index: int
        for point_index in range(1, len(route_points) - 1):
            node_kind: RoutingNodeKind
            if point_index == 1 or point_index == interior_point_count:
                node_kind = RoutingNodeKind.STUB
            else:
                node_kind = RoutingNodeKind.ELBOW

            # The first and last interior nodes are the explicit stubs. Any
            # remaining interior nodes belong to the orthogonal dogleg itself.
            inner_node: RoutingNode = RoutingNode(
                node_id=next_node_id,
                kind=node_kind,
                position=route_points[point_index].copy(),
            )
            routing_graph._add_node(inner_node)
            node_ids.append(next_node_id)
            next_node_id += 1
        node_ids.append(2)

        segment_index: int
        for segment_index in range(len(node_ids) - 1):
            routing_graph._add_segment(
                self._build_segment(
                    segment_id=segment_index + 1,
                    start_node_id=node_ids[segment_index],
                    end_node_id=node_ids[segment_index + 1],
                )
            )

    def _build_segment(self, segment_id: int, start_node_id: int, end_node_id: int) -> RoutingSegment:
        """
        Build one graph segment.

        :param segment_id: Segment identifier.
        :param start_node_id: Start node identifier.
        :param end_node_id: End node identifier.
        :returns: Routing segment.
        """
        route_segment: RoutingSegment = RoutingSegment(
            segment_id=segment_id,
            start_node_id=start_node_id,
            end_node_id=end_node_id,
        )
        return route_segment
