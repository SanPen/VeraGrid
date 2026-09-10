# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_elements import RoutingNode
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_elements import RoutingPoint
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_elements import RoutingSegment
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_graph import RoutingGraph
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_geometry import RoutingGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.automatic_route_builder import AutomaticRouteBuilder
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_constraint_engine import RoutingConstraintEngine
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_graph import RoutingGraph
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_geometry import RoutingGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingBlockGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingBounds
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingConnectionGeometry
from VeraGridEngine.enumerations import RoutingNodeKind, RoutingPortSide


class RouteBuilder:
    """
    Build one deterministic orthogonal routing graph between two ports.

    :return: None.
    """

    __slots__ = (
        "_source_position",
        "_destination_position",
        "_source_port_side",
        "_destination_port_side",
        "_connection_geometry",
        "_geometry",
    )

    def __init__(
            self,
            source_position: RoutingPoint,
            destination_position: RoutingPoint,
            source_port_side: RoutingPortSide,
            destination_port_side: RoutingPortSide,
            connection_geometry: RoutingConnectionGeometry | None = None,
    ) -> None:
        """
        Build one route builder.

        :param source_position: Source port position.
        :param destination_position: Destination port position.
        :param source_port_side: Physical side of the source port on its block.
        :param destination_port_side: Physical side of the destination port on its block.
        :param connection_geometry: Point-in-time non-Qt block geometry for the connection.
        :return: None.
        """
        self._source_position: RoutingPoint = source_position.copy()
        self._destination_position: RoutingPoint = destination_position.copy()
        self._source_port_side: RoutingPortSide = source_port_side
        self._destination_port_side: RoutingPortSide = destination_port_side
        self._connection_geometry: RoutingConnectionGeometry | None = connection_geometry
        self._geometry: RoutingGeometry = RoutingGeometry()

    def build(self) -> RoutingGraph:
        """
        Build one deterministic orthogonal graph.

        :return: Built routing graph.
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

        if self._is_built_graph_valid(routing_graph=routing_graph):
            return routing_graph
        elif self._connection_geometry is not None:
            automatic_builder: AutomaticRouteBuilder = AutomaticRouteBuilder(
                graph=routing_graph,
                connection_geometry=self._connection_geometry,
            )
            alternative_graph: RoutingGraph | None = automatic_builder.build_alternative()
            if alternative_graph is not None:
                return alternative_graph
            else:
                raise ValueError("RouteBuilder could not find a valid automatic routing alternative.")
        else:
            # A deterministic builder failure is a programming error rather
            # than a recoverable edit. The invalid graph is never accepted by
            # the caller or exposed to the Qt routing session.
            raise ValueError("RouteBuilder produced an invalid routing graph.")

    def _is_built_graph_valid(self, routing_graph: RoutingGraph) -> bool:
        """
        Validate one newly constructed graph before exposing it to callers.

        When Qt supplies a point-in-time geometry snapshot, the builder also
        checks endpoint owners, foreign blocks and existing routed connections.
        Pure-core callers remain supported by omitting that optional snapshot.

        :param routing_graph: Newly materialized graph.
        :return: ``True`` when topology and active constraints are valid.
        """
        if routing_graph.validate().is_valid():
            pass
        else:
            return False

        constraint_engine: RoutingConstraintEngine = RoutingConstraintEngine(graph=routing_graph)
        route_segment: RoutingSegment
        for route_segment in routing_graph.get_segments():
            if constraint_engine.segment_has_invalid_own_route_intersection(segment=route_segment):
                return False
            else:
                pass
            start_node: RoutingNode | None = routing_graph.get_node(route_segment.get_start_node_id())
            end_node: RoutingNode | None = routing_graph.get_node(route_segment.get_end_node_id())
            if start_node is None or end_node is None:
                return False
            else:
                pass

            start_is_port: bool = start_node.get_kind() == RoutingNodeKind.PORT
            end_is_port: bool = end_node.get_kind() == RoutingNodeKind.PORT
            if not start_is_port and not end_is_port:
                if constraint_engine.validate_segment(
                        segment=route_segment,
                        connection_geometry=self._connection_geometry,
                ):
                    pass
                else:
                    return False
            else:
                pass

            if start_is_port:
                start_owner_bounds: RoutingBounds | None = self._get_port_owner_bounds(
                    routing_graph=routing_graph,
                    port_node=start_node,
                )
                if constraint_engine.validate_connection(
                        port_node=start_node,
                        neighbour_node=end_node,
                        segment=route_segment,
                        block_bounds=start_owner_bounds,
                        connection_geometry=self._connection_geometry,
                ):
                    pass
                else:
                    return False
            else:
                pass

            if end_is_port:
                end_owner_bounds: RoutingBounds | None = self._get_port_owner_bounds(
                    routing_graph=routing_graph,
                    port_node=end_node,
                )
                if constraint_engine.validate_connection(
                        port_node=end_node,
                        neighbour_node=start_node,
                        segment=route_segment,
                        block_bounds=end_owner_bounds,
                        connection_geometry=self._connection_geometry,
                ):
                    pass
                else:
                    return False
            else:
                pass

        return True

    def _get_port_owner_bounds(
            self,
            routing_graph: RoutingGraph,
            port_node: RoutingNode,
    ) -> RoutingBounds | None:
        """
        Return the captured owner bounds for one route endpoint.

        :param routing_graph: Graph whose endpoint role must be resolved.
        :param port_node: Port node being validated.
        :return: Matching endpoint-owner bounds or ``None`` when unavailable.
        """
        if self._connection_geometry is None:
            return None
        elif port_node.get_node_id() == routing_graph.get_source_node_id():
            source_owner: RoutingBlockGeometry | None = self._connection_geometry.get_source_owner()
            if source_owner is not None:
                return source_owner.get_bounds()
            else:
                return None
        elif port_node.get_node_id() == routing_graph.get_destination_node_id():
            destination_owner: RoutingBlockGeometry | None = self._connection_geometry.get_destination_owner()
            if destination_owner is not None:
                return destination_owner.get_bounds()
            else:
                return None
        else:
            return None

    def _build_stub_topology(self, routing_graph: RoutingGraph) -> None:
        """
        Build the route with fixed stubs and minimum straight continuations.

        The builder still uses the same deterministic orthogonal route
        algorithm for the central geometry. Its effective endpoints are two
        continuation elbows beyond the fixed endpoint stubs, which leaves a
        movable segment beside each stub without stretching the stub itself.

        :param routing_graph: Graph under construction.
        :return: None.
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
        source_continuation: RoutingPoint = self._geometry.build_stub_continuation_point(
            stub_position=source_stub,
            port_side=self._source_port_side,
        )
        destination_continuation: RoutingPoint = self._geometry.build_stub_continuation_point(
            stub_position=destination_stub,
            port_side=self._destination_port_side,
        )
        # The central route keeps the legacy minimal dogleg algorithm. Only the
        # effective endpoints change from the ports themselves to the endpoint
        # continuations, so the visible construction policy stays simple.
        inner_route_points: list[RoutingPoint] = self._build_minimal_route_points(
            start_position=source_continuation,
            end_position=destination_continuation,
        )

        # The final point chain always includes both real ports so the graph
        # keeps explicit topology for the physical block attachment points.
        route_points.append(self._source_position.copy())
        route_points.append(source_stub.copy())
        inner_point: RoutingPoint
        for inner_point in inner_route_points:
            route_points.append(inner_point.copy())
        route_points.append(destination_stub.copy())
        route_points.append(self._destination_position.copy())
        # The builder owns the only topology-from-scratch step. Once the full
        # point chain is known, the graph is materialized in one deterministic
        # pass so later editor operations only transform existing nodes.
        self._build_graph_from_route_points(routing_graph, route_points)

    def _build_minimal_route_points(
            self,
            start_position: RoutingPoint,
            end_position: RoutingPoint,
    ) -> list[RoutingPoint]:
        """
        Build the existing minimal orthogonal route between two endpoints.

        :param start_position: Effective route start.
        :param end_position: Effective route end.
        :return: Ordered route points including both endpoints.
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
            elbow_point1: RoutingPoint = RoutingPoint(
                x_pos=((end_position.get_x() - start_position.get_x())/2)+start_position.get_x(),
                y_pos=start_position.get_y(),
            )

            elbow_point2: RoutingPoint = RoutingPoint(
                x_pos=((end_position.get_x() - start_position.get_x())/2)+start_position.get_x(),
                y_pos=end_position.get_y(),
            )

            route_points.append(elbow_point1)
            route_points.append(elbow_point2)
            route_points.append(end_position.copy())

        return route_points

    def _build_stub_point(self, port_position: RoutingPoint, port_side: RoutingPortSide) -> RoutingPoint:
        """
        Build one stub point offset from a port along its physical side.

        :param port_position: Port position.
        :param port_side: Physical side of the port.
        :return: Stub endpoint.
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
        :return: None.
        """
        node_ids: list[int] = list((1,))
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
        :return: Routing segment.
        """
        route_segment: RoutingSegment = RoutingSegment(
            segment_id=segment_id,
            start_node_id=start_node_id,
            end_node_id=end_node_id,
        )
        return route_segment
