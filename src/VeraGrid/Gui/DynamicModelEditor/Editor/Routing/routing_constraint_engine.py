# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_elements import RoutingNode
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_elements import RoutingPoint
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_graph import RoutingGraph
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_geometry import RoutingGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_policy import AutomaticRoutingPolicy
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_elements import RoutingSegment
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingBlockGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingBounds
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingConnectionGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingSegmentObstacle
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_spatial_index import RoutingSpatialIndex
from VeraGridEngine.enumerations import RoutingAxis, RoutingNodeKind, RoutingPortSide


class RoutingConstraintEngine:
    """
    Answer routing-constraint questions without mutating the graph.

    This class centralizes reusable geometric constraints so future routing
    algorithms can validate candidate operations consistently before applying
    them. The constraint engine never edits the graph and never owns rendering
    data.

    """

    __slots__ = (
        "_graph",
        "_geometry",
        "_minimum_segment_length",
        "_minimum_first_segment_length",
        "_minimum_stub_continuation_length",
        "_spatial_index",
    )

    def __init__(self, graph: RoutingGraph, spatial_index: RoutingSpatialIndex | None = None) -> None:
        """
        Build one constraint engine bound to one graph.

        The engine reuses the shared geometry helper already owned by the graph
        so every routing component evaluates visual alignment with exactly the
        same criteria.

        :param graph: Graph to inspect.
        :param spatial_index: Optional routing-core obstacle candidate index.

        :return: None.
        """
        self._graph: RoutingGraph = graph
        self._geometry: RoutingGeometry = graph.get_geometry()
        self._minimum_segment_length: float = 1.0
        self._minimum_first_segment_length: float = 5.0
        self._minimum_stub_continuation_length: float = 5.0
        self._spatial_index: RoutingSpatialIndex | None = spatial_index

    def is_port_connection_perpendicular(
            self,
            port_node: RoutingNode,
            neighbour_node: RoutingNode,
    ) -> bool:
        """
        Return whether the connection leaving one port is perpendicular.

        ``RoutingNode`` persists the physical port side, allowing the engine to
        validate both the expected axis and the direction in which the first
        segment leaves the owning block.

        :param port_node: Port node to inspect.
        :param neighbour_node: Immediate neighbour of the port node.

        :return: ``True`` when the connection satisfies the available check.
        """
        if port_node.get_kind() != RoutingNodeKind.PORT:
            return False
        elif neighbour_node.get_node_id() == port_node.get_node_id():
            return False
        elif not port_node.has_port_side():
            return False
        else:
            # Port-side validation is a two-step check: first verify that the
            # segment uses the expected perpendicular axis, then verify that it
            # also points toward the physically allowed side of the block.
            expected_axis: RoutingAxis | None = self._get_port_perpendicular_axis(port_node=port_node)
            if expected_axis is None:
                return False
            else:
                actual_axis: RoutingAxis | None = self._derive_axis_between_nodes(
                    first_node=port_node,
                    second_node=neighbour_node,
                )
                if actual_axis is None:
                    return False
                elif actual_axis == expected_axis:
                    return self._is_neighbour_in_port_side_direction(
                        port_node=port_node,
                        neighbour_node=neighbour_node,
                    )
                else:
                    return False

    def is_first_segment_long_enough(
            self,
            port_node: RoutingNode,
            neighbour_node: RoutingNode,
    ) -> bool:
        """
        Return whether the first segment connected to one port is long enough.

        :param port_node: Port node at the connection endpoint.
        :param neighbour_node: First neighbour of the port node

        :return: ``True`` when the first segment is long enough.
        """
        if port_node.get_kind() != RoutingNodeKind.PORT:
            return False
        else:
            # The first port segment enforces the minimum stub length. Later
            # segments use the generic segment-length rule below.
            segment_length: float = self._distance_between_nodes(
                first_node=port_node,
                second_node=neighbour_node,
            )
            if segment_length >= self._minimum_first_segment_length:
                return True
            else:
                return False

    def is_segment_long_enough(self, segment: RoutingSegment) -> bool:
        """
        Return whether one segment has a sufficient visible length.

        :param segment: Segment to inspect.

        :return: ``True`` when the segment is long enough.
        """
        start_node: RoutingNode | None = self._graph.get_node(segment.get_start_node_id())
        end_node: RoutingNode | None = self._graph.get_node(segment.get_end_node_id())
        if start_node is None or end_node is None:
            return False
        else:
            # Segment validity is always derived from the live node positions.
            # The segment itself stores only topology, never cached geometry.
            segment_length: float = self._distance_between_nodes(
                first_node=start_node,
                second_node=end_node,
            )
            if segment_length >= self._minimum_segment_length:
                return True
            else:
                return False

    def is_segment_orthogonal(self, segment: RoutingSegment) -> bool:
        """
        Return whether one segment is orthogonal.

        :param segment: Segment to inspect.

        :return: ``True`` when the segment is horizontal or vertical.
        """
        start_node: RoutingNode | None = self._graph.get_node(segment.get_start_node_id())
        end_node: RoutingNode | None = self._graph.get_node(segment.get_end_node_id())
        if start_node is None or end_node is None:
            return False
        else:
            # Orthogonality is delegated to the shared geometry helper so the
            # builder, editor, renderer and constraints all use the same visual
            # alignment criterion.
            return self._geometry.are_orthogonally_aligned(
                first_point=start_node.get_position(),
                second_point=end_node.get_position(),
            )

    def is_nodes_orthogonally_aligned(
            self,
            first_node: RoutingNode,
            second_node: RoutingNode,
    ) -> bool:
        """
        Return whether two nodes can be joined by one orthogonal segment.

        This method exists temporarily during the incremental migration from
        ``RoutingEditor`` to ``RoutingConstraintEngine``. Once every caller uses
        only the higher-level connection validation entry point, this helper can
        become internal.

        :param first_node: First node to inspect.
        :param second_node: Second node to inspect.
        :return: ``True`` when both nodes are orthogonally aligned.
        """
        return self._geometry.are_orthogonally_aligned(
            first_point=first_node.get_position(),
            second_point=second_node.get_position(),
        )

    def segment_intersects_block(
            self,
            segment: RoutingSegment,
            block_bounds: RoutingBounds | None = None,
    ) -> bool:
        """
        Return whether one segment penetrates the owning block interior.

        Contact with the visible boundary is allowed because the segment must
        originate at its port. Penetration beyond the shared visual tolerance
        is rejected. The tolerance absorbs the graphics-item pen width and
        other sub-pixel differences introduced while converting Qt bounds.

        :param segment: Segment to inspect.
        :param block_bounds: Non-Qt bounds of the endpoint's owning block.
        :return: ``True`` when the segment overlaps the effective block interior.
        """
        if block_bounds is None:
            return False
        else:
            pass

        start_node: RoutingNode | None = self._graph.get_node(segment.get_start_node_id())
        end_node: RoutingNode | None = self._graph.get_node(segment.get_end_node_id())
        if start_node is None or end_node is None:
            return False
        else:
            pass

        interior_bounds: RoutingBounds | None = self._build_effective_block_interior(
            block_bounds=block_bounds,
        )
        if interior_bounds is None:
            return False
        else:
            pass

        start_x: float = start_node.get_position().get_x()
        start_y: float = start_node.get_position().get_y()
        end_x: float = end_node.get_position().get_x()
        end_y: float = end_node.get_position().get_y()
        segment_axis: RoutingAxis | None = self._geometry.derive_axis(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
        )

        # Orthogonal segments intersect a rectangle only when their fixed
        # coordinate is interior and their varying interval overlaps it.
        if segment_axis == RoutingAxis.HORIZONTAL:
            if not self._is_value_inside_open_interval(
                    value=start_y,
                    lower_bound=interior_bounds.get_top(),
                    upper_bound=interior_bounds.get_bottom(),
            ):
                return False
            else:
                return self._open_intervals_overlap(
                    first_start=min(start_x, end_x),
                    first_end=max(start_x, end_x),
                    second_start=interior_bounds.get_left(),
                    second_end=interior_bounds.get_right(),
                )
        elif segment_axis == RoutingAxis.VERTICAL:
            if not self._is_value_inside_open_interval(
                    value=start_x,
                    lower_bound=interior_bounds.get_left(),
                    upper_bound=interior_bounds.get_right(),
            ):
                return False
            else:
                return self._open_intervals_overlap(
                    first_start=min(start_y, end_y),
                    first_end=max(start_y, end_y),
                    second_start=interior_bounds.get_top(),
                    second_end=interior_bounds.get_bottom(),
                )
        else:
            # Non-orthogonal geometry is rejected by validate_segment(). This
            # predicate remains conservative and leaves that rule authoritative.
            return False

    def is_segment_inside_block(
            self,
            segment: RoutingSegment,
            block_bounds: RoutingBounds | None = None,
    ) -> bool:
        """
        Return whether both segment endpoints lie inside the owning block.

        Boundary contact remains valid for a real port attachment, so the same
        effective interior used by the intersection check is applied here.

        :param segment: Segment to inspect.
        :param block_bounds: Non-Qt bounds of the endpoint's owning block.
        :return: ``True`` when the complete segment lies in the effective interior.
        """
        if block_bounds is None:
            return False
        else:
            pass

        start_node: RoutingNode | None = self._graph.get_node(segment.get_start_node_id())
        end_node: RoutingNode | None = self._graph.get_node(segment.get_end_node_id())
        if start_node is None or end_node is None:
            return False
        else:
            pass

        interior_bounds: RoutingBounds | None = self._build_effective_block_interior(
            block_bounds=block_bounds,
        )
        if interior_bounds is None:
            return False
        else:
            start_inside: bool = self._is_point_inside_bounds(
                route_node=start_node,
                block_bounds=interior_bounds,
            )
            end_inside: bool = self._is_point_inside_bounds(
                route_node=end_node,
                block_bounds=interior_bounds,
            )
            if start_inside and end_inside:
                return True
            else:
                return False

    def segment_intersects_foreign_block(
            self,
            segment: RoutingSegment,
            block_bounds: RoutingBounds,
    ) -> bool:
        """
        Return whether one segment touches or enters an unrelated block.

        Unlike the owner policy, a foreign block is a complete obstacle. Both
        boundary contact and interior penetration are invalid because no port
        on that block belongs to the connection being validated.

        :param segment: Segment to inspect.
        :param block_bounds: Non-Qt bounds of one unrelated block.
        :return: ``True`` when the segment intersects the closed rectangle.
        """
        start_node: RoutingNode | None = self._graph.get_node(segment.get_start_node_id())
        end_node: RoutingNode | None = self._graph.get_node(segment.get_end_node_id())
        if start_node is None or end_node is None:
            return False
        else:
            pass

        start_x: float = start_node.get_position().get_x()
        start_y: float = start_node.get_position().get_y()
        end_x: float = end_node.get_position().get_x()
        end_y: float = end_node.get_position().get_y()
        segment_axis: RoutingAxis | None = self._geometry.derive_axis(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
        )

        # Foreign obstacles use a closed rectangle. Merely touching their
        # visible outline is therefore a collision, unlike an owning port edge.
        if segment_axis == RoutingAxis.HORIZONTAL:
            if not self._is_value_inside_closed_interval(
                    value=start_y,
                    lower_bound=block_bounds.get_top(),
                    upper_bound=block_bounds.get_bottom(),
            ):
                return False
            else:
                return self._closed_intervals_overlap(
                    first_start=min(start_x, end_x),
                    first_end=max(start_x, end_x),
                    second_start=block_bounds.get_left(),
                    second_end=block_bounds.get_right(),
                )
        elif segment_axis == RoutingAxis.VERTICAL:
            if not self._is_value_inside_closed_interval(
                    value=start_x,
                    lower_bound=block_bounds.get_left(),
                    upper_bound=block_bounds.get_right(),
            ):
                return False
            else:
                return self._closed_intervals_overlap(
                    first_start=min(start_y, end_y),
                    first_end=max(start_y, end_y),
                    second_start=block_bounds.get_top(),
                    second_end=block_bounds.get_bottom(),
                )
        else:
            return False

    def is_point_inside_foreign_block(
            self,
            point: RoutingPoint,
            block_bounds: RoutingBounds,
    ) -> bool:
        """
        Return whether one candidate routing point touches a foreign block.

        Foreign blocks use closed bounds, matching segment collision semantics.
        The automatic builder uses this query to avoid materializing search
        nodes that cannot participate in any valid route.

        :param point: Candidate routing point.
        :param block_bounds: Closed foreign-block bounds.
        :return: ``True`` when the point lies on or inside the block.
        """
        x_inside: bool = self._is_value_inside_closed_interval(
            value=point.get_x(),
            lower_bound=block_bounds.get_left(),
            upper_bound=block_bounds.get_right(),
        )
        y_inside: bool = self._is_value_inside_closed_interval(
            value=point.get_y(),
            lower_bound=block_bounds.get_top(),
            upper_bound=block_bounds.get_bottom(),
        )
        if x_inside and y_inside:
            return True
        else:
            return False

    def segment_intersects_other_connection(
            self,
            segment: RoutingSegment,
            obstacle_segment: RoutingSegmentObstacle,
    ) -> bool:
        """
        Return whether one segment touches or crosses another connection.

        Perpendicular crossings, collinear overlap and endpoint-only contact
        are all invalid. Junction and shared-trunk semantics do not exist yet,
        so accepting any of those shapes would produce a misleading visual
        relationship between electrically independent connections.

        :param segment: Segment from the graph currently being validated.
        :param obstacle_segment: Point-in-time segment from another graph.
        :return: ``True`` when both closed orthogonal segments intersect.
        """
        start_node: RoutingNode | None = self._graph.get_node(segment.get_start_node_id())
        end_node: RoutingNode | None = self._graph.get_node(segment.get_end_node_id())
        if start_node is None or end_node is None:
            return False
        else:
            pass

        start_position: RoutingPoint = start_node.get_position()
        end_position: RoutingPoint = end_node.get_position()
        obstacle_start: RoutingPoint = obstacle_segment.get_start_position()
        obstacle_end: RoutingPoint = obstacle_segment.get_end_position()
        segment_axis: RoutingAxis | None = self._geometry.derive_axis(
            start_x=start_position.get_x(),
            start_y=start_position.get_y(),
            end_x=end_position.get_x(),
            end_y=end_position.get_y(),
        )
        obstacle_axis: RoutingAxis | None = self._geometry.derive_axis(
            start_x=obstacle_start.get_x(),
            start_y=obstacle_start.get_y(),
            end_x=obstacle_end.get_x(),
            end_y=obstacle_end.get_y(),
        )
        if segment_axis is None or obstacle_axis is None:
            return False
        elif segment_axis == RoutingAxis.HORIZONTAL and obstacle_axis == RoutingAxis.HORIZONTAL:
            if not self._geometry.are_y_aligned_values(
                    first_y=start_position.get_y(),
                    second_y=obstacle_start.get_y(),
            ):
                return False
            else:
                return self._closed_intervals_overlap(
                    first_start=min(start_position.get_x(), end_position.get_x()),
                    first_end=max(start_position.get_x(), end_position.get_x()),
                    second_start=min(obstacle_start.get_x(), obstacle_end.get_x()),
                    second_end=max(obstacle_start.get_x(), obstacle_end.get_x()),
                )
        elif segment_axis == RoutingAxis.VERTICAL and obstacle_axis == RoutingAxis.VERTICAL:
            if not self._geometry.are_x_aligned_values(
                    first_x=start_position.get_x(),
                    second_x=obstacle_start.get_x(),
            ):
                return False
            else:
                return self._closed_intervals_overlap(
                    first_start=min(start_position.get_y(), end_position.get_y()),
                    first_end=max(start_position.get_y(), end_position.get_y()),
                    second_start=min(obstacle_start.get_y(), obstacle_end.get_y()),
                    second_end=max(obstacle_start.get_y(), obstacle_end.get_y()),
                )
        elif segment_axis == RoutingAxis.HORIZONTAL:
            crossing_x: float = obstacle_start.get_x()
            crossing_y: float = start_position.get_y()
            return self._orthogonal_crossing_point_belongs_to_both_segments(
                crossing_x=crossing_x,
                crossing_y=crossing_y,
                horizontal_start=start_position,
                horizontal_end=end_position,
                vertical_start=obstacle_start,
                vertical_end=obstacle_end,
            )
        else:
            crossing_x = start_position.get_x()
            crossing_y = obstacle_start.get_y()
            return self._orthogonal_crossing_point_belongs_to_both_segments(
                crossing_x=crossing_x,
                crossing_y=crossing_y,
                horizontal_start=obstacle_start,
                horizontal_end=obstacle_end,
                vertical_start=start_position,
                vertical_end=end_position,
            )

    def validate_segment(
            self,
            segment: RoutingSegment,
            connection_geometry: RoutingConnectionGeometry | None = None,
            routing_policy: AutomaticRoutingPolicy = AutomaticRoutingPolicy.STRICT,
    ) -> bool:
        """
        Return whether one segment satisfies every active segment-level constraint.

        This becomes the public entry point used by routing algorithms so the
        internal list of segment constraints can evolve without changing the
        calling code.

        :param segment: Segment to inspect.
        :param connection_geometry: Point-in-time owner and foreign-block geometry.
        :param routing_policy: Collision policy applied to other connections.
        :return: ``True`` when the segment satisfies every active constraint.
        """
        if not self.validate_hard_segment_constraints(
                segment=segment,
                connection_geometry=connection_geometry,
        ):
            return False
        elif not self._segment_avoids_other_connections(
                segment=segment,
                connection_geometry=connection_geometry,
                routing_policy=routing_policy,
        ):
            return False
        else:
            # Every segment-level rule remains composed here so builders and
            # editors cannot accidentally apply different obstacle policies.
            return True

    def validate_hard_segment_constraints(
            self,
            segment: RoutingSegment,
            connection_geometry: RoutingConnectionGeometry | None = None,
    ) -> bool:
        """
        Validate constraints that no routing policy may relax.

        Orthogonality, minimum length and every block collision remain hard
        constraints. Wire policy is intentionally absent from this entry point
        so automatic graph construction cannot accidentally relax blocks while
        preparing a crossing-permitted fallback.

        :param segment: Segment to inspect.
        :param connection_geometry: Point-in-time owner and block geometry.
        :return: ``True`` when every non-relaxable constraint is satisfied.
        """
        if not self.is_segment_orthogonal(segment=segment):
            return False
        elif not self.is_segment_long_enough(segment=segment):
            return False
        elif not self._segment_avoids_foreign_blocks(
                segment=segment,
                connection_geometry=connection_geometry,
        ):
            return False
        elif not self.is_stub_continuation_valid_for_segment(segment=segment):
            return False
        else:
            return True

    def is_stub_continuation_valid_for_segment(self, segment: RoutingSegment) -> bool:
        """
        Validate an interior segment attached directly to an endpoint stub.

        PORT -> STUB segments retain their separate port constraints. A STUB
        -> interior segment must continue along the same outward axis and keep
        enough length to absorb manual movement of the following segment.

        :param segment: Segment that may be incident to an endpoint stub.
        :return: ``True`` when no continuation rule is violated.
        """
        start_node: RoutingNode | None = self._graph.get_node(segment.get_start_node_id())
        end_node: RoutingNode | None = self._graph.get_node(segment.get_end_node_id())
        if start_node is None or end_node is None:
            return False
        elif start_node.get_kind() == RoutingNodeKind.STUB and end_node.get_kind() != RoutingNodeKind.PORT:
            return self._is_stub_continuation_valid(
                stub_node=start_node,
                continuation_node=end_node,
            )
        elif end_node.get_kind() == RoutingNodeKind.STUB and start_node.get_kind() != RoutingNodeKind.PORT:
            return self._is_stub_continuation_valid(
                stub_node=end_node,
                continuation_node=start_node,
            )
        else:
            return True

    def _is_stub_continuation_valid(
            self,
            stub_node: RoutingNode,
            continuation_node: RoutingNode,
    ) -> bool:
        """
        Validate one stub continuation against its adjacent endpoint port.

        :param stub_node: Fixed endpoint stub.
        :param continuation_node: First movable interior node.
        :return: ``True`` when alignment, direction and length are valid.
        """
        adjacent_node: RoutingNode
        port_node: RoutingNode | None = None
        for adjacent_node in self._graph.adjacent_nodes(stub_node.get_node_id()):
            if adjacent_node.get_kind() == RoutingNodeKind.PORT:
                port_node = adjacent_node
            else:
                pass

        if port_node is None:
            return False
        else:
            port_side: RoutingPortSide | None = port_node.get_port_side()

        if port_side is None:
            return False
        else:
            pass

        stub_position: RoutingPoint = stub_node.get_position()
        continuation_position: RoutingPoint = continuation_node.get_position()
        continuation_length: float = self._distance_between_nodes(
            first_node=stub_node,
            second_node=continuation_node,
        )
        if continuation_length < self._minimum_stub_continuation_length:
            return False
        elif port_side == RoutingPortSide.LEFT:
            return (self._geometry.are_y_aligned(stub_position, continuation_position)
                    and continuation_position.get_x() < stub_position.get_x())
        elif port_side == RoutingPortSide.RIGHT:
            return (self._geometry.are_y_aligned(stub_position, continuation_position)
                    and continuation_position.get_x() > stub_position.get_x())
        elif port_side == RoutingPortSide.TOP:
            return (self._geometry.are_x_aligned(stub_position, continuation_position)
                    and continuation_position.get_y() < stub_position.get_y())
        else:
            return (self._geometry.are_x_aligned(stub_position, continuation_position)
                    and continuation_position.get_y() > stub_position.get_y())

    def segment_has_invalid_own_route_intersection(self, segment: RoutingSegment) -> bool:
        """
        Return whether one segment intersects its own route illegally.

        Non-adjacent segments may never touch, cross or overlap. Adjacent
        segments may meet only at their shared topology node; collinear
        backtracking over the same geometry remains invalid.

        :param segment: Segment to compare with the remaining route.
        :return: ``True`` when the route contains an invalid self-intersection.
        """
        other_segment: RoutingSegment
        for other_segment in self._graph.get_segments():
            if other_segment.get_segment_id() == segment.get_segment_id():
                pass
            elif self._segments_intersect(segment=segment, other_segment=other_segment):
                shared_node_id: int | None = self._get_shared_node_id(
                    first_segment=segment,
                    second_segment=other_segment,
                )
                if shared_node_id is None:
                    return True
                elif self._adjacent_segments_overlap_beyond_shared_node(
                        first_segment=segment,
                        second_segment=other_segment,
                        shared_node_id=shared_node_id,
                ):
                    return True
                else:
                    pass
            else:
                pass
        return False

    def _segments_intersect(
            self,
            segment: RoutingSegment,
            other_segment: RoutingSegment,
    ) -> bool:
        """
        Compare two segments through the shared orthogonal intersection rule.

        :param segment: First segment owned by the active graph.
        :param other_segment: Second segment owned by the same graph.
        :return: ``True`` when both closed segments intersect.
        """
        other_start: RoutingNode | None = self._graph.get_node(other_segment.get_start_node_id())
        other_end: RoutingNode | None = self._graph.get_node(other_segment.get_end_node_id())
        if other_start is None or other_end is None:
            return True
        else:
            obstacle_segment: RoutingSegmentObstacle = RoutingSegmentObstacle(
                connection_uid=-1,
                segment_id=other_segment.get_segment_id(),
                start_position=other_start.get_position(),
                end_position=other_end.get_position(),
            )
            return self.segment_intersects_other_connection(
                segment=segment,
                obstacle_segment=obstacle_segment,
            )

    def _get_shared_node_id(
            self,
            first_segment: RoutingSegment,
            second_segment: RoutingSegment,
    ) -> int | None:
        """
        Return the topology node shared by two adjacent segments.

        :param first_segment: First segment.
        :param second_segment: Second segment.
        :return: Shared node identifier or ``None``.
        """
        first_start_id: int = first_segment.get_start_node_id()
        first_end_id: int = first_segment.get_end_node_id()
        second_start_id: int = second_segment.get_start_node_id()
        second_end_id: int = second_segment.get_end_node_id()
        if first_start_id == second_start_id or first_start_id == second_end_id:
            return first_start_id
        elif first_end_id == second_start_id or first_end_id == second_end_id:
            return first_end_id
        else:
            return None

    def _adjacent_segments_overlap_beyond_shared_node(
            self,
            first_segment: RoutingSegment,
            second_segment: RoutingSegment,
            shared_node_id: int,
    ) -> bool:
        """
        Return whether adjacent collinear segments backtrack over each other.

        :param first_segment: First adjacent segment.
        :param second_segment: Second adjacent segment.
        :param shared_node_id: Their common topology node.
        :return: ``True`` when their intersection exceeds the shared point.
        """
        first_axis: RoutingAxis | None = self._graph.get_segment_axis(first_segment.get_segment_id())
        second_axis: RoutingAxis | None = self._graph.get_segment_axis(second_segment.get_segment_id())
        if first_axis is None or second_axis is None:
            return True
        elif first_axis != second_axis:
            return False
        else:
            pass

        shared_node: RoutingNode | None = self._graph.get_node(shared_node_id)
        first_other_id: int | None = first_segment.get_other_node_id(shared_node_id)
        second_other_id: int | None = second_segment.get_other_node_id(shared_node_id)
        if shared_node is None or first_other_id is None or second_other_id is None:
            return True
        else:
            first_other: RoutingNode | None = self._graph.get_node(first_other_id)
            second_other: RoutingNode | None = self._graph.get_node(second_other_id)

        if first_other is None or second_other is None:
            return True
        elif first_axis == RoutingAxis.HORIZONTAL:
            first_delta: float = first_other.get_position().get_x() - shared_node.get_position().get_x()
            second_delta: float = second_other.get_position().get_x() - shared_node.get_position().get_x()
        else:
            first_delta = first_other.get_position().get_y() - shared_node.get_position().get_y()
            second_delta = second_other.get_position().get_y() - shared_node.get_position().get_y()

        if first_delta * second_delta < 0.0:
            return False
        else:
            return True

    def validate_connection(
            self,
            port_node: RoutingNode,
            neighbour_node: RoutingNode,
            segment: RoutingSegment,
            block_bounds: RoutingBounds | None = None,
            connection_geometry: RoutingConnectionGeometry | None = None,
            routing_policy: AutomaticRoutingPolicy = AutomaticRoutingPolicy.STRICT,
    ) -> bool:
        """
        Return whether one local port connection satisfies every active constraint.

        This method is intentionally generic so any future routing algorithm can
        validate candidate geometry through the same reusable entry point.

        :param port_node: Port node to inspect.
        :param neighbour_node: First neighbour of the port node.
        :param segment: Connecting segment between both nodes.
        :param block_bounds: Non-Qt bounds of the endpoint's owning block.
        :param connection_geometry: Point-in-time owner and obstacle geometry.
        :param routing_policy: Collision policy applied to other connections.
        :return: ``True`` when every active constraint is satisfied.
        """
        if not self.is_port_connection_perpendicular(
                port_node=port_node,
                neighbour_node=neighbour_node,
        ):
            return False
        elif not self.is_first_segment_long_enough(
                port_node=port_node,
                neighbour_node=neighbour_node,
        ):
            return False
        elif not self.validate_segment(
                segment=segment,
                connection_geometry=connection_geometry,
                routing_policy=routing_policy,
        ):
            return False
        elif self.segment_intersects_block(segment=segment, block_bounds=block_bounds):
            return False
        elif self.is_segment_inside_block(segment=segment, block_bounds=block_bounds):
            return False
        else:
            # Connection-level validation composes port-specific and generic
            # segment rules so higher-level algorithms can ask one question
            # without duplicating constraint sequencing.
            return True

    def _segment_avoids_foreign_blocks(
            self,
            segment: RoutingSegment,
            connection_geometry: RoutingConnectionGeometry | None,
    ) -> bool:
        """
        Return whether one segment avoids every block foreign to that segment.

        Endpoint owners are foreign to interior segments but not to the first
        segment attached to their own port. Other scene blocks are always full
        obstacles. Owner-specific penetration is checked separately through
        :meth:`validate_connection`.

        :param segment: Segment to validate against captured block geometry.
        :param connection_geometry: Point-in-time connection geometry or ``None``.
        :return: ``True`` when no foreign block intersects the segment.
        """
        if connection_geometry is None:
            return True
        else:
            pass

        block_geometry: RoutingBlockGeometry
        for block_geometry in self._get_foreign_block_candidates(
                segment=segment,
                connection_geometry=connection_geometry,
        ):
            if self.segment_intersects_foreign_block(
                    segment=segment,
                    block_bounds=block_geometry.get_bounds(),
            ):
                return False
            else:
                pass

        source_owner: RoutingBlockGeometry | None = connection_geometry.get_source_owner()
        destination_owner: RoutingBlockGeometry | None = connection_geometry.get_destination_owner()
        source_segment: bool = self._segment_contains_node(
            segment=segment,
            node_id=self._graph.get_source_node_id(),
        )
        destination_segment: bool = self._segment_contains_node(
            segment=segment,
            node_id=self._graph.get_destination_node_id(),
        )
        same_endpoint_owner: bool = destination_owner is source_owner and destination_owner is not None
        source_owner_is_local: bool = source_segment or (same_endpoint_owner and destination_segment)
        if source_owner is not None and not source_owner_is_local:
            if self.segment_intersects_foreign_block(
                    segment=segment,
                    block_bounds=source_owner.get_bounds(),
            ):
                return False
            else:
                pass
        else:
            pass

        if destination_owner is not None and not same_endpoint_owner and not destination_segment:
            if self.segment_intersects_foreign_block(
                    segment=segment,
                    block_bounds=destination_owner.get_bounds(),
            ):
                return False
            else:
                pass
        elif same_endpoint_owner:
            # A shared endpoint owner was already checked through the source
            # role above, so no duplicate rectangle evaluation is necessary.
            pass
        else:
            pass

        return True

    def _segment_avoids_other_connections(
            self,
            segment: RoutingSegment,
            connection_geometry: RoutingConnectionGeometry | None,
            routing_policy: AutomaticRoutingPolicy,
    ) -> bool:
        """
        Return whether one segment avoids every captured foreign connection.

        :param segment: Segment from the active routing graph.
        :param connection_geometry: Point-in-time geometry or ``None``.
        :param routing_policy: Collision policy applied to other connections.
        :return: ``True`` when no foreign segment touches the active segment.
        """
        if connection_geometry is None:
            return True
        elif routing_policy == AutomaticRoutingPolicy.ALLOW_WIRE_CROSSINGS:
            return True
        else:
            pass

        obstacle_segment: RoutingSegmentObstacle
        for obstacle_segment in self._get_foreign_segment_candidates(
                segment=segment,
                connection_geometry=connection_geometry,
        ):
            if self.segment_intersects_other_connection(
                    segment=segment,
                    obstacle_segment=obstacle_segment,
            ):
                return False
            else:
                pass
        return True

    def count_other_connection_intersections(
            self,
            segment: RoutingSegment,
            connection_geometry: RoutingConnectionGeometry | None,
    ) -> int:
        """
        Count foreign wire segments intersected by one candidate segment.

        The automatic builder uses this non-mutating query to penalize, rather
        than silently ignore, crossings in its relaxed fallback search.

        :param segment: Candidate segment from the active graph.
        :param connection_geometry: Point-in-time connection geometry or ``None``.
        :return: Number of intersected foreign segments.
        """
        intersection_count: int = 0
        if connection_geometry is None:
            return intersection_count
        else:
            pass

        obstacle_segment: RoutingSegmentObstacle
        for obstacle_segment in self._get_foreign_segment_candidates(
                segment=segment,
                connection_geometry=connection_geometry,
        ):
            if self.segment_intersects_other_connection(
                    segment=segment,
                    obstacle_segment=obstacle_segment,
            ):
                intersection_count += 1
            else:
                pass
        return intersection_count

    def _get_foreign_block_candidates(
            self,
            segment: RoutingSegment,
            connection_geometry: RoutingConnectionGeometry,
    ) -> tuple[RoutingBlockGeometry, ...]:
        """Return spatially relevant foreign blocks for exact validation.

        :param segment: Candidate segment from the active graph.
        :param connection_geometry: Complete immutable obstacle geometry.
        :return: Candidate foreign blocks, indexed when possible.
        """
        if self._spatial_index is None:
            return connection_geometry.get_other_blocks()
        else:
            start_node: RoutingNode | None = self._graph.get_node(segment.get_start_node_id())
            end_node: RoutingNode | None = self._graph.get_node(segment.get_end_node_id())
            if start_node is None or end_node is None:
                return connection_geometry.get_other_blocks()
            else:
                indexed_blocks: tuple[RoutingBlockGeometry, ...] = self._spatial_index.query_blocks(
                    start_position=start_node.get_position(),
                    end_position=end_node.get_position(),
                )
                source_owner: RoutingBlockGeometry | None = connection_geometry.get_source_owner()
                destination_owner: RoutingBlockGeometry | None = connection_geometry.get_destination_owner()
                if source_owner is None and destination_owner is None:
                    # Central searches intentionally classify both endpoint
                    # owners as ordinary foreign blocks.
                    return indexed_blocks
                else:
                    candidate_blocks: list[RoutingBlockGeometry] = list()
                    block_geometry: RoutingBlockGeometry
                    for block_geometry in indexed_blocks:
                        is_source_owner: bool = (
                            source_owner is not None
                            and block_geometry.get_block_uid() == source_owner.get_block_uid()
                        )
                        is_destination_owner: bool = (
                            destination_owner is not None
                            and block_geometry.get_block_uid() == destination_owner.get_block_uid()
                        )
                        if is_source_owner or is_destination_owner:
                            pass
                        else:
                            candidate_blocks.append(block_geometry)
                    return tuple(candidate_blocks)

    def _get_foreign_segment_candidates(
            self,
            segment: RoutingSegment,
            connection_geometry: RoutingConnectionGeometry,
    ) -> tuple[RoutingSegmentObstacle, ...]:
        """Return spatially relevant foreign segments for exact validation.

        :param segment: Candidate segment from the active graph.
        :param connection_geometry: Complete immutable obstacle geometry.
        :return: Candidate foreign segments, indexed when possible.
        """
        if self._spatial_index is None:
            return connection_geometry.get_other_connection_segments()
        else:
            start_node: RoutingNode | None = self._graph.get_node(segment.get_start_node_id())
            end_node: RoutingNode | None = self._graph.get_node(segment.get_end_node_id())
            if start_node is None or end_node is None:
                return connection_geometry.get_other_connection_segments()
            else:
                return self._spatial_index.query_segments(
                    start_position=start_node.get_position(),
                    end_position=end_node.get_position(),
                )

    def _orthogonal_crossing_point_belongs_to_both_segments(
            self,
            crossing_x: float,
            crossing_y: float,
            horizontal_start: RoutingPoint,
            horizontal_end: RoutingPoint,
            vertical_start: RoutingPoint,
            vertical_end: RoutingPoint,
    ) -> bool:
        """
        Return whether one perpendicular crossing point lies on both segments.

        :param crossing_x: Horizontal coordinate of the candidate crossing.
        :param crossing_y: Vertical coordinate of the candidate crossing.
        :param horizontal_start: First endpoint of the horizontal segment.
        :param horizontal_end: Second endpoint of the horizontal segment.
        :param vertical_start: First endpoint of the vertical segment.
        :param vertical_end: Second endpoint of the vertical segment.
        :return: ``True`` when the closed segments share the crossing point.
        """
        crossing_on_horizontal: bool = self._is_value_inside_closed_interval(
            value=crossing_x,
            lower_bound=min(horizontal_start.get_x(), horizontal_end.get_x()),
            upper_bound=max(horizontal_start.get_x(), horizontal_end.get_x()),
        )
        crossing_on_vertical: bool = self._is_value_inside_closed_interval(
            value=crossing_y,
            lower_bound=min(vertical_start.get_y(), vertical_end.get_y()),
            upper_bound=max(vertical_start.get_y(), vertical_end.get_y()),
        )
        if crossing_on_horizontal and crossing_on_vertical:
            return True
        else:
            return False

    def _segment_contains_node(self, segment: RoutingSegment, node_id: int) -> bool:
        """
        Return whether one node identifier is an endpoint of a segment.

        :param segment: Segment whose endpoints must be inspected.
        :param node_id: Candidate endpoint identifier.
        :return: ``True`` when the node belongs to the segment.
        """
        if segment.get_start_node_id() == int(node_id):
            return True
        elif segment.get_end_node_id() == int(node_id):
            return True
        else:
            return False

    def _build_effective_block_interior(self, block_bounds: RoutingBounds) -> RoutingBounds | None:
        """
        Build the strict block interior after applying visual-edge tolerance.

        :param block_bounds: Captured scene bounds including their visual pen.
        :return: Effective interior bounds, or ``None`` for a collapsed rectangle.
        """
        tolerance: float = self._geometry.get_visual_alignment_threshold()
        interior_left: float = block_bounds.get_left() + tolerance
        interior_top: float = block_bounds.get_top() + tolerance
        interior_right: float = block_bounds.get_right() - tolerance
        interior_bottom: float = block_bounds.get_bottom() - tolerance
        if interior_left < interior_right and interior_top < interior_bottom:
            return RoutingBounds(
                left=interior_left,
                top=interior_top,
                right=interior_right,
                bottom=interior_bottom,
            )
        else:
            return None

    def _is_point_inside_bounds(
            self,
            route_node: RoutingNode,
            block_bounds: RoutingBounds,
    ) -> bool:
        """
        Return whether one node lies strictly inside supplied bounds.

        :param route_node: Routing node whose position must be inspected.
        :param block_bounds: Effective open rectangle bounds.
        :return: ``True`` when both coordinates are strictly interior.
        """
        x_inside: bool = self._is_value_inside_open_interval(
            value=route_node.get_position().get_x(),
            lower_bound=block_bounds.get_left(),
            upper_bound=block_bounds.get_right(),
        )
        y_inside: bool = self._is_value_inside_open_interval(
            value=route_node.get_position().get_y(),
            lower_bound=block_bounds.get_top(),
            upper_bound=block_bounds.get_bottom(),
        )
        if x_inside and y_inside:
            return True
        else:
            return False

    def _is_value_inside_open_interval(
            self,
            value: float,
            lower_bound: float,
            upper_bound: float,
    ) -> bool:
        """
        Return whether one scalar lies strictly inside an open interval.

        :param value: Scalar coordinate to inspect.
        :param lower_bound: Open interval lower bound.
        :param upper_bound: Open interval upper bound.
        :return: ``True`` when the value is strictly interior.
        """
        if float(lower_bound) < float(value) < float(upper_bound):
            return True
        else:
            return False

    def _is_value_inside_closed_interval(
            self,
            value: float,
            lower_bound: float,
            upper_bound: float,
    ) -> bool:
        """
        Return whether one scalar lies inside a closed interval.

        :param value: Scalar coordinate to inspect.
        :param lower_bound: Closed interval lower bound.
        :param upper_bound: Closed interval upper bound.
        :return: ``True`` when the value lies on or within both bounds.
        """
        if float(lower_bound) <= float(value) <= float(upper_bound):
            return True
        else:
            return False

    def _open_intervals_overlap(
            self,
            first_start: float,
            first_end: float,
            second_start: float,
            second_end: float,
    ) -> bool:
        """
        Return whether two ordered intervals share a non-zero interior span.

        Endpoint-only contact is intentionally excluded so a port connection
        can touch the effective owner boundary without being rejected.

        :param first_start: First interval start.
        :param first_end: First interval end.
        :param second_start: Second interval start.
        :param second_end: Second interval end.
        :return: ``True`` when both intervals overlap beyond one endpoint.
        """
        overlap_start: float = max(float(first_start), float(second_start))
        overlap_end: float = min(float(first_end), float(second_end))
        if overlap_start < overlap_end:
            return True
        else:
            return False

    def _closed_intervals_overlap(
            self,
            first_start: float,
            first_end: float,
            second_start: float,
            second_end: float,
    ) -> bool:
        """
        Return whether two ordered closed intervals touch or overlap.

        :param first_start: First interval start.
        :param first_end: First interval end.
        :param second_start: Second interval start.
        :param second_end: Second interval end.
        :return: ``True`` when the intervals share at least one coordinate.
        """
        overlap_start: float = max(float(first_start), float(second_start))
        overlap_end: float = min(float(first_end), float(second_end))
        if overlap_start <= overlap_end:
            return True
        else:
            return False

    def _get_port_perpendicular_axis(self, port_node: RoutingNode) -> RoutingAxis | None:
        """
        Return the expected perpendicular axis for one port connection.

        :param port_node: Port node to inspect.
        :return: Expected perpendicular axis or ``None``.
        """
        port_side: RoutingPortSide | None = port_node.get_port_side()
        if port_side == RoutingPortSide.LEFT:
            return RoutingAxis.HORIZONTAL
        elif port_side == RoutingPortSide.RIGHT:
            return RoutingAxis.HORIZONTAL
        elif port_side == RoutingPortSide.TOP:
            return RoutingAxis.VERTICAL
        elif port_side == RoutingPortSide.BOTTOM:
            return RoutingAxis.VERTICAL
        else:
            return None

    def _derive_axis_between_nodes(
            self,
            first_node: RoutingNode,
            second_node: RoutingNode,
    ) -> RoutingAxis | None:
        """
        Derive the axis between two nodes.

        :param first_node: First node.
        :param second_node: Second node.
        :return: Derived axis or ``None``.
        """
        return self._geometry.derive_axis(
            start_x=first_node.get_position().get_x(),
            start_y=first_node.get_position().get_y(),
            end_x=second_node.get_position().get_x(),
            end_y=second_node.get_position().get_y(),
        )

    def _distance_between_nodes(
            self,
            first_node: RoutingNode,
            second_node: RoutingNode,
    ) -> float:
        """
        Return the axis-aligned distance between two nodes.

        Orthogonal routing segments vary on a single axis, so the relevant
        visible length is the dominant coordinate difference.

        :param first_node: First node.
        :param second_node: Second node.
        :return: Segment length in pixels.
        """
        delta_x: float = abs(first_node.get_position().get_x() - second_node.get_position().get_x())
        delta_y: float = abs(first_node.get_position().get_y() - second_node.get_position().get_y())
        if delta_x >= delta_y:
            return delta_x
        else:
            return delta_y

    def _is_neighbour_in_port_side_direction(
            self,
            port_node: RoutingNode,
            neighbour_node: RoutingNode,
    ) -> bool:
        """
        Return whether the neighbour lies on the allowed side of the port.

        :param port_node: Port node that owns the connection.
        :param neighbour_node: First node connected to the port.
        :return: ``True`` when the first segment leaves the port in the allowed direction.
        """
        port_side: RoutingPortSide | None = port_node.get_port_side()
        if port_side == RoutingPortSide.LEFT:
            return self._is_value_strictly_less(
                first_value=neighbour_node.get_position().get_x(),
                second_value=port_node.get_position().get_x(),
            )
        elif port_side == RoutingPortSide.RIGHT:
            return self._is_value_strictly_greater(
                first_value=neighbour_node.get_position().get_x(),
                second_value=port_node.get_position().get_x(),
            )
        elif port_side == RoutingPortSide.TOP:
            return self._is_value_strictly_less(
                first_value=neighbour_node.get_position().get_y(),
                second_value=port_node.get_position().get_y(),
            )
        elif port_side == RoutingPortSide.BOTTOM:
            return self._is_value_strictly_greater(
                first_value=neighbour_node.get_position().get_y(),
                second_value=port_node.get_position().get_y(),
            )
        else:
            return False

    def _is_value_strictly_less(self, first_value: float, second_value: float) -> bool:
        """
        Return whether the first coordinate lies strictly before the second one.

        The comparison reuses the shared visual-alignment threshold so values
        that are still visually aligned are not considered directionally valid.

        :param first_value: Candidate neighbour coordinate.
        :param second_value: Port coordinate.
        :return: ``True`` when the first value is strictly smaller.
        """
        threshold: float = self._geometry.get_visual_alignment_threshold()
        if float(first_value) < float(second_value) - threshold:
            return True
        else:
            return False

    def _is_value_strictly_greater(self, first_value: float, second_value: float) -> bool:
        """
        Return whether the first coordinate lies strictly after the second one.

        The comparison reuses the shared visual-alignment threshold so values
        that are still visually aligned are not considered directionally valid.

        :param first_value: Candidate neighbour coordinate.
        :param second_value: Port coordinate.
        :return: ``True`` when the first value is strictly greater.
        """
        threshold: float = self._geometry.get_visual_alignment_threshold()
        if float(first_value) > float(second_value) + threshold:
            return True
        else:
            return False
