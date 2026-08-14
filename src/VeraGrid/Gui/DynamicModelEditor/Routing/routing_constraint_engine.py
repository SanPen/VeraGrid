# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingNode
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingNodeKind
from VeraGridEngine.enumerations import RoutingPortSide
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_graph import RoutingGraph
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_geometry import RoutingGeometry
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingSegment
from VeraGridEngine.enumerations import RoutingAxis


class RoutingConstraintEngine:
    """
    Answer routing-constraint questions without mutating the graph.

    This class centralizes reusable geometric constraints so future routing
    algorithms can validate candidate operations consistently before applying
    them. The constraint engine never edits the graph and never owns rendering
    data.

    :returns: None.
    """

    __slots__ = (
        "_graph",
        "_geometry",
        "_minimum_segment_length",
        "_minimum_first_segment_length",
    )

    def __init__(self, graph: RoutingGraph) -> None:
        """
        Build one constraint engine bound to one graph.

        The engine reuses the shared geometry helper already owned by the graph
        so every routing component evaluates visual alignment with exactly the
        same criteria.

        :param graph: Graph to inspect.
        :returns: None.
        """
        self._graph: RoutingGraph = graph
        self._geometry: RoutingGeometry = graph.get_geometry()
        self._minimum_segment_length: float = 1.0
        self._minimum_first_segment_length: float = 10.0

    def is_port_connection_perpendicular(
            self,
            port_node: RoutingNode,
            neighbour_node: RoutingNode,
    ) -> bool:
        """
        Return whether the connection leaving one port is perpendicular.

        Phase 2.1 introduces only the shared constraint API. The current graph
        model does not yet persist the physical attachment orientation of each
        port, so the engine cannot infer a reliable expected axis from topology
        alone. Until that metadata exists, the constraint remains permissive and
        reports ``True`` for valid port nodes so no editor behaviour changes.

        :param port_node: Port node to inspect.
        :param neighbour_node: Immediate neighbour of the port node.
        :returns: ``True`` when the connection satisfies the available check.
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
        :param neighbour_node: First neighbour of the port node.
        :returns: ``True`` when the first segment is long enough.
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
        :returns: ``True`` when the segment is long enough.
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
        :returns: ``True`` when the segment is horizontal or vertical.
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
        :returns: ``True`` when both nodes are orthogonally aligned.
        """
        return self._geometry.are_orthogonally_aligned(
            first_point=first_node.get_position(),
            second_point=second_node.get_position(),
        )

    def segment_intersects_block(
            self,
            segment: RoutingSegment,
            block_bounds: object | None = None,
    ) -> bool:
        """
        Return whether one segment intersects the owning block geometry.

        The real block-boundary geometry is not part of Phase 2.1 yet. The API
        exists now so future algorithms can ask this question through the same
        constraint engine without redesigning the call sites.

        :param segment: Segment to inspect.
        :param block_bounds: Placeholder block geometry payload.
        :returns: ``False`` until block geometry integration exists.
        """
        del segment
        del block_bounds
        return False

    def is_segment_inside_block(
            self,
            segment: RoutingSegment,
            block_bounds: object | None = None,
    ) -> bool:
        """
        Return whether one segment lies inside the owning block geometry.

        The real block-boundary geometry is not part of Phase 2.1 yet. The API
        exists now so future algorithms can ask this question through the same
        constraint engine without redesigning the call sites.

        :param segment: Segment to inspect.
        :param block_bounds: Placeholder block geometry payload.
        :returns: ``False`` until block geometry integration exists.
        """
        del segment
        del block_bounds
        return False

    def validate_segment(self, segment: RoutingSegment) -> bool:
        """
        Return whether one segment satisfies every active segment-level constraint.

        This becomes the public entry point used by routing algorithms so the
        internal list of segment constraints can evolve without changing the
        calling code.

        :param segment: Segment to inspect.
        :returns: ``True`` when the segment satisfies every active constraint.
        """
        if not self.is_segment_orthogonal(segment=segment):
            return False
        elif not self.is_segment_long_enough(segment=segment):
            return False
        else:
            # Segment-level validation stays intentionally small in this phase.
            # Future constraints can extend this single composition point
            # without changing editor call sites.
            return True

    def validate_connection(
            self,
            port_node: RoutingNode,
            neighbour_node: RoutingNode,
            segment: RoutingSegment,
            block_bounds: object | None = None,
    ) -> bool:
        """
        Return whether one local port connection satisfies every active constraint.

        This method is intentionally generic so any future routing algorithm can
        validate candidate geometry through the same reusable entry point.

        :param port_node: Port node to inspect.
        :param neighbour_node: First neighbour of the port node.
        :param segment: Connecting segment between both nodes.
        :param block_bounds: Placeholder block geometry payload.
        :returns: ``True`` when every active constraint is satisfied.
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
        elif not self.validate_segment(segment=segment):
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

    def is_connection_valid(
            self,
            port_node: RoutingNode,
            neighbour_node: RoutingNode,
            segment: RoutingSegment,
            block_bounds: object | None = None,
    ) -> bool:
        """
        Return whether one local port connection satisfies every active constraint.

        This temporary alias keeps the migration incremental while the higher-
        level public API moves toward ``validate_connection(...)``.

        :param port_node: Port node to inspect.
        :param neighbour_node: First neighbour of the port node.
        :param segment: Connecting segment between both nodes.
        :param block_bounds: Placeholder block geometry payload.
        :returns: ``True`` when every active constraint is satisfied.
        """
        return self.validate_connection(
            port_node=port_node,
            neighbour_node=neighbour_node,
            segment=segment,
            block_bounds=block_bounds,
        )

    def _get_port_perpendicular_axis(self, port_node: RoutingNode) -> RoutingAxis | None:
        """
        Return the expected perpendicular axis for one port connection.

        :param port_node: Port node to inspect.
        :returns: Expected perpendicular axis or ``None``.
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
        :returns: Derived axis or ``None``.
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
        :returns: Segment length in pixels.
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
        :returns: ``True`` when the first segment leaves the port in the allowed direction.
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
        :returns: ``True`` when the first value is strictly smaller.
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
        :returns: ``True`` when the first value is strictly greater.
        """
        threshold: float = self._geometry.get_visual_alignment_threshold()
        if float(first_value) > float(second_value) + threshold:
            return True
        else:
            return False
