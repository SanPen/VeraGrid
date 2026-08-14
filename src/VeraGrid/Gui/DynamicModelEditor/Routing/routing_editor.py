# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from VeraGrid.Gui.DynamicModelEditor.Routing.routing_constraint_engine import RoutingConstraintEngine
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingNode
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingNodeKind
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingPoint
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingSegment
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_geometry import RoutingGeometry
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_graph import RoutingGraph
from VeraGridEngine.enumerations import RoutingAxis


class RoutingEditor:
    """
    Transform one routing graph while preserving graph invariants.

    :returns: None.
    """

    __slots__ = ("_graph", "_geometry", "_constraints")

    def __init__(self, graph: RoutingGraph) -> None:
        """
        Build one routing editor bound to one graph.

        :param graph: Graph to edit.
        :returns: None.
        """
        self._graph: RoutingGraph = graph
        self._geometry: RoutingGeometry = graph.get_geometry()
        self._constraints: RoutingConstraintEngine = RoutingConstraintEngine(graph=graph)

    def get_graph(self) -> RoutingGraph:
        """
        Return the edited graph.

        :returns: Edited graph.
        """
        return self._graph

    def move_elbow(self, elbow_id: int, new_position: RoutingPoint) -> bool:
        """
        Move one elbow by projecting it to one valid orthogonal corner.

        :param elbow_id: Elbow node identifier.
        :param new_position: Requested new elbow position.
        :returns: ``True`` when the elbow changed position.
        """
        elbow_node: RoutingNode | None = self._graph.get_node(elbow_id)
        if elbow_node is None:
            return False
        elif elbow_node.get_kind() != RoutingNodeKind.ELBOW:
            return False
        else:
            pass

        original_position: RoutingPoint = elbow_node.get_position().copy()
        if self._points_are_equal(original_position, new_position):
            return True
        else:
            pass

        # Every public edit starts from one full graph snapshot so the editor
        # can keep the live graph valid even when a later local check fails.
        graph_snapshot: RoutingGraph = self._graph.clone()

        adjacent_nodes: list[RoutingNode] = self._graph.adjacent_nodes(elbow_id)
        if len(adjacent_nodes) != 2:
            return False
        else:
            pass

        # An elbow may only move to one of the two orthogonal corners defined
        # by its adjacent nodes. The editor therefore projects the user request
        # to those two legal candidates and picks the closest one.
        first_candidate: RoutingPoint = RoutingPoint(
            adjacent_nodes[0].get_position().get_x(),
            adjacent_nodes[1].get_position().get_y(),
        )
        second_candidate: RoutingPoint = RoutingPoint(
            adjacent_nodes[1].get_position().get_x(),
            adjacent_nodes[0].get_position().get_y(),
        )

        chosen_position: RoutingPoint = self._choose_closest_candidate(
            requested_position=new_position,
            first_candidate=first_candidate,
            second_candidate=second_candidate,
        )

        # An elbow move changes exactly one graph node. The connected segments
        # change only because they are incident to that node; no topology is
        # rebuilt and no unrelated geometry is touched.
        elbow_node.set_position(chosen_position)
        if self._incident_segments_are_valid_for_nodes([elbow_id]):
            return True
        else:
            elbow_node.set_position(original_position)
            self._graph._restore_from(graph_snapshot)
            return False

    def insert_elbow(self, segment_id: int, split_position: RoutingPoint) -> int | None:
        """
        Split one segment by inserting one elbow.

        :param segment_id: Segment identifier to split.
        :param split_position: Split position on the segment.
        :returns: New elbow identifier or ``None``.
        """
        route_segment: RoutingSegment | None = self._graph.get_segment(segment_id)
        if route_segment is None:
            return None
        else:
            pass

        graph_snapshot: RoutingGraph = self._graph.clone()

        # An inserted elbow must lie on the chosen segment so the split stays
        # purely local and preserves the surrounding topology.
        if self._point_lies_on_segment(route_segment, split_position):
            pass
        else:
            return None

        start_node: RoutingNode | None = self._graph.get_node(route_segment.get_start_node_id())
        end_node: RoutingNode | None = self._graph.get_node(route_segment.get_end_node_id())
        if start_node is None or end_node is None:
            return None
        else:
            pass

        if self._point_matches_node(split_position, start_node):
            return None
        elif self._point_matches_node(split_position, end_node):
            return None
        else:
            pass

        # The original segment is replaced in place by two explicit segments.
        # One keeps the old identifier and the second receives one new stable
        # identifier so the topology change stays minimal and deterministic.
        new_node_id: int = self._allocate_next_node_id()
        new_segment_id: int = self._allocate_next_segment_id()
        elbow_node: RoutingNode = RoutingNode(
            node_id=new_node_id,
            kind=RoutingNodeKind.ELBOW,
            position=split_position.copy(),
        )
        replacement_first: RoutingSegment = RoutingSegment(
            segment_id=route_segment.get_segment_id(),
            start_node_id=route_segment.get_start_node_id(),
            end_node_id=new_node_id,
        )
        replacement_second: RoutingSegment = RoutingSegment(
            segment_id=new_segment_id,
            start_node_id=new_node_id,
            end_node_id=route_segment.get_end_node_id(),
        )

        if self._graph._remove_segment(segment_id):
            pass
        else:
            return None
        if self._graph._add_node(elbow_node):
            pass
        else:
            return None
        if self._graph._add_segment(replacement_first):
            pass
        else:
            return None
        if self._graph._add_segment(replacement_second):
            pass
        else:
            return None

        if self._graph.validate().is_valid():
            return new_node_id
        else:
            self._graph._restore_from(graph_snapshot)
            return None

    def remove_elbow(self, elbow_id: int) -> bool:
        """
        Remove one elbow and merge its adjacent segments.

        :param elbow_id: Elbow node identifier.
        :returns: ``True`` when the elbow was removed.
        """
        elbow_node: RoutingNode | None = self._graph.get_node(elbow_id)
        if elbow_node is None:
            return False
        elif elbow_node.get_kind() != RoutingNodeKind.ELBOW:
            return False
        elif self._graph.degree(elbow_id) != 2:
            return False
        else:
            pass

        graph_snapshot: RoutingGraph = self._graph.clone()

        adjacent_nodes: list[RoutingNode] = self._graph.adjacent_nodes(elbow_id)
        adjacent_segments: list[RoutingSegment] = self._graph.adjacent_segments(elbow_id)
        if len(adjacent_nodes) != 2 or len(adjacent_segments) != 2:
            return False
        else:
            pass

        # Elbow removal is one local merge operation: both neighbouring
        # segments disappear and one direct replacement segment is attempted
        # between the two surviving nodes.
        merged_segment: RoutingSegment = RoutingSegment(
            segment_id=adjacent_segments[0].get_segment_id(),
            start_node_id=adjacent_nodes[0].get_node_id(),
            end_node_id=adjacent_nodes[1].get_node_id(),
        )

        if self._constraints.is_segment_orthogonal(segment=merged_segment):
            pass
        else:
            return False

        first_removed: bool = self._graph._remove_segment(adjacent_segments[0].get_segment_id())
        second_removed: bool = self._graph._remove_segment(adjacent_segments[1].get_segment_id())
        node_removed: bool = self._graph._remove_node(elbow_id)
        if first_removed and second_removed and node_removed:
            pass
        else:
            return False

        if self._graph._add_segment(merged_segment):
            pass
        else:
            return False

        if self._graph.validate().is_valid():
            return True
        else:
            self._graph._restore_from(graph_snapshot)
            return False

    def update_port(self, node_id: int, new_position: RoutingPoint) -> bool:
        """
        Update one port node position after one block movement.

        :param node_id: Port node identifier.
        :param new_position: New port position.
        :returns: ``True`` when the port was updated.
        """
        route_node: RoutingNode | None = self._graph.get_node(node_id)
        if route_node is None:
            return False
        elif route_node.get_kind() != RoutingNodeKind.PORT:
            return False
        elif self._graph.degree(node_id) != 1:
            return False
        else:
            pass

        graph_snapshot: RoutingGraph = self._graph.clone()

        adjacent_nodes: list[RoutingNode] = self._graph.adjacent_nodes(node_id)
        if len(adjacent_nodes) != 1:
            return False
        else:
            pass

        incident_segments: list[RoutingSegment] = self._graph.adjacent_segments(node_id)
        if len(incident_segments) != 1:
            return False
        else:
            pass

        original_position: RoutingPoint = route_node.get_position().copy()
        if self._points_are_equal(original_position, new_position):
            return True
        else:
            pass

        # A port update starts by moving the physical port endpoint itself. The
        # neighbouring stub is then rebuilt from the same shared geometry rule
        # used by the builder so the endpoint topology remains consistent.
        route_node.set_position(new_position.copy())

        stub_node: RoutingNode = adjacent_nodes[0]
        if stub_node.get_kind() != RoutingNodeKind.STUB:
            self._graph._restore_from(graph_snapshot)
            return False
        elif not route_node.has_port_side():
            self._graph._restore_from(graph_snapshot)
            return False
        else:
            stub_position: RoutingPoint = self._geometry.build_port_stub_point(
                port_position=new_position,
                port_side=route_node.get_port_side(),
            )
            stub_node.set_position(stub_position)

        if self._graph.get_source_node_id() == node_id:
            updated: bool = self._update_source_stub_neighbourhood(
                stub_node_id=stub_node.get_node_id(),
            )
        elif self._graph.get_destination_node_id() == node_id:
            updated = self._update_destination_stub_neighbourhood(
                stub_node_id=stub_node.get_node_id(),
            )
        else:
            self._graph._restore_from(graph_snapshot)
            return False

        if updated:
            return True
        else:
            self._graph._restore_from(graph_snapshot)
            return False

    def move_segment(self, segment_id: int, coordinate_offset: float) -> bool:
        """
        Move one interior segment along its perpendicular axis.

        :param segment_id: Segment identifier.
        :param coordinate_offset: Requested offset along the allowed drag axis.
        :returns: ``True`` when the segment moved.
        """
        route_segment: RoutingSegment | None = self._graph.get_segment(segment_id)
        if route_segment is None:
            return False
        else:
            pass

        start_node: RoutingNode | None = self._graph.get_node(route_segment.get_start_node_id())
        end_node: RoutingNode | None = self._graph.get_node(route_segment.get_end_node_id())
        segment_axis: RoutingAxis | None = self._graph.get_segment_axis(segment_id)
        if start_node is None or end_node is None or segment_axis is None:
            return False
        elif start_node.get_kind() != RoutingNodeKind.ELBOW:
            return False
        elif end_node.get_kind() != RoutingNodeKind.ELBOW:
            return False
        else:
            pass

        offset_value: float = float(coordinate_offset)
        if abs(offset_value) <= 1.0e-9:
            return True
        else:
            pass

        # Segment dragging is one local coordinate update on the two endpoint
        # elbows of that segment. The graph topology and every unrelated node
        # stay untouched.
        graph_snapshot: RoutingGraph = self._graph.clone()

        # A segment move edits exactly the two elbow nodes that bound the moved
        # segment. The neighbouring topology stays intact and only the local
        # incident geometry changes as a consequence of those node moves.
        if segment_axis == RoutingAxis.HORIZONTAL:
            start_node.set_position(
                RoutingPoint(
                    start_node.get_position().get_x(),
                    start_node.get_position().get_y() + offset_value,
                )
            )
            end_node.set_position(
                RoutingPoint(
                    end_node.get_position().get_x(),
                    end_node.get_position().get_y() + offset_value,
                )
            )
        else:
            start_node.set_position(
                RoutingPoint(
                    start_node.get_position().get_x() + offset_value,
                    start_node.get_position().get_y(),
                )
            )
            end_node.set_position(
                RoutingPoint(
                    end_node.get_position().get_x() + offset_value,
                    end_node.get_position().get_y(),
                )
            )

        if self._incident_segments_are_valid_for_nodes(
                [start_node.get_node_id(), end_node.get_node_id()]
        ):
            return True
        else:
            self._graph._restore_from(graph_snapshot)
            return False

    def _choose_closest_candidate(
            self,
            requested_position: RoutingPoint,
            first_candidate: RoutingPoint,
            second_candidate: RoutingPoint,
    ) -> RoutingPoint:
        """
        Choose the candidate corner closest to the requested elbow position.

        :param requested_position: Requested elbow position.
        :param first_candidate: First valid orthogonal corner.
        :param second_candidate: Second valid orthogonal corner.
        :returns: Chosen orthogonal corner.
        """
        first_distance: float = self._distance_squared(requested_position, first_candidate)
        second_distance: float = self._distance_squared(requested_position, second_candidate)
        if first_distance <= second_distance:
            return first_candidate
        else:
            return second_candidate

    def _distance_squared(self, first_point: RoutingPoint, second_point: RoutingPoint) -> float:
        """
        Build the squared Euclidean distance between two points.

        :param first_point: First point.
        :param second_point: Second point.
        :returns: Squared Euclidean distance.
        """
        delta_x: float = first_point.get_x() - second_point.get_x()
        delta_y: float = first_point.get_y() - second_point.get_y()
        return delta_x * delta_x + delta_y * delta_y

    def _point_lies_on_segment(self, segment: RoutingSegment, point: RoutingPoint) -> bool:
        """
        Return whether one point lies on one segment.

        :param segment: Segment to inspect.
        :param point: Point to test.
        :returns: ``True`` when the point lies on the segment.
        """
        start_node: RoutingNode | None = self._graph.get_node(segment.get_start_node_id())
        end_node: RoutingNode | None = self._graph.get_node(segment.get_end_node_id())
        if start_node is None or end_node is None:
            return False
        else:
            pass

        segment_axis: RoutingAxis | None = self._graph.get_segment_axis(segment.get_segment_id())
        if segment_axis == RoutingAxis.HORIZONTAL:
            minimum_x: float = min(start_node.get_position().get_x(), end_node.get_position().get_x())
            maximum_x: float = max(start_node.get_position().get_x(), end_node.get_position().get_x())
            same_y: bool = self._geometry.are_y_aligned_values(
                point.get_y(),
                start_node.get_position().get_y(),
            )
            within_x: bool = minimum_x <= point.get_x() <= maximum_x
            if same_y and within_x:
                return True
            else:
                return False
        elif segment_axis == RoutingAxis.VERTICAL:
            minimum_y: float = min(start_node.get_position().get_y(), end_node.get_position().get_y())
            maximum_y: float = max(start_node.get_position().get_y(), end_node.get_position().get_y())
            same_x: bool = self._geometry.are_x_aligned_values(
                point.get_x(),
                start_node.get_position().get_x(),
            )
            within_y: bool = minimum_y <= point.get_y() <= maximum_y
            if same_x and within_y:
                return True
            else:
                return False
        else:
            return False

    def _point_matches_node(self, point: RoutingPoint, node: RoutingNode) -> bool:
        """
        Return whether one point matches one node position.

        :param point: Point to test.
        :param node: Node to compare against.
        :returns: ``True`` when the point matches the node position.
        """
        return self._geometry.are_points_numerically_equal(point, node.get_position())

    def _allocate_next_node_id(self) -> int:
        """
        Allocate the next free node identifier.

        :returns: Next free node identifier.
        """
        node_ids: list[int] = [route_node.get_node_id() for route_node in self._graph.get_nodes()]
        if len(node_ids) == 0:
            return 1
        else:
            return max(node_ids) + 1

    def _allocate_next_segment_id(self) -> int:
        """
        Allocate the next free segment identifier.

        :returns: Next free segment identifier.
        """
        segment_ids: list[int] = [route_segment.get_segment_id() for route_segment in self._graph.get_segments()]
        if len(segment_ids) == 0:
            return 1
        else:
            return max(segment_ids) + 1

    def _update_source_stub_neighbourhood(self, stub_node_id: int) -> bool:
        """
        Update the local source-side neighbourhood after moving its port stub.

        :param stub_node_id: Source stub node identifier.
        :returns: ``True`` when the local update succeeded.
        """
        return self._update_stub_neighbourhood(
            stub_node_id=stub_node_id,
            source_side=True,
        )

    def _update_destination_stub_neighbourhood(self, stub_node_id: int) -> bool:
        """
        Update the local destination-side neighbourhood after moving its port stub.

        :param stub_node_id: Destination stub node identifier.
        :returns: ``True`` when the local update succeeded.
        """
        return self._update_stub_neighbourhood(
            stub_node_id=stub_node_id,
            source_side=False,
        )

    def _update_stub_neighbourhood(
            self,
            stub_node_id: int,
            source_side: bool,
    ) -> bool:
        """
        Update the route neighbourhood immediately after one port-side stub.

        A port move preserves topology by moving the port and then sliding its
        stub only as much as needed to keep the first segment perpendicular.
        The stub length is not fixed here; it may grow or shrink as long as the
        later constraint validation accepts the resulting PORT->STUB segment.

        :param stub_node_id: Stub node identifier.
        :param source_side: Whether the edited port is the source side.
        :returns: ``True`` when the local update succeeded.
        """
        ordered_nodes: list[RoutingNode] = self._graph.get_ordered_nodes()
        if len(ordered_nodes) < 3:
            return False
        else:
            pass

        if source_side:
            anchor_node: RoutingNode = ordered_nodes[1]
            first_neighbour: RoutingNode = ordered_nodes[2]
        else:
            anchor_node = ordered_nodes[-2]
            first_neighbour = ordered_nodes[-3]

        if anchor_node.get_node_id() != stub_node_id:
            return False
        else:
            pass

        # If the stub and its immediate neighbour are already orthogonally
        # aligned, the local port move was absorbed without touching deeper
        # route geometry and the update can stop here.
        if self._constraints.is_nodes_orthogonally_aligned(
                first_node=anchor_node,
                second_node=first_neighbour,
        ):
            return self._incident_segments_are_valid_for_nodes(
                [anchor_node.get_node_id(), first_neighbour.get_node_id()]
            )
        elif first_neighbour.get_kind() != RoutingNodeKind.ELBOW and first_neighbour.get_kind() != RoutingNodeKind.STUB:
            return False
        elif len(ordered_nodes) < 4:
            return False
        else:
            # Otherwise the next interior bend must absorb the remaining change.
            # Only that immediate neighbourhood is eligible for repositioning.
            second_neighbour: RoutingNode
            if source_side:
                second_neighbour = ordered_nodes[3]
            else:
                second_neighbour = ordered_nodes[-4]

            return self._reposition_local_elbow(
                port_node=anchor_node,
                elbow_node=first_neighbour,
                adjacent_node=second_neighbour,
            )

    def _insert_local_elbow(
            self,
            port_node_id: int,
            preferred_axis: RoutingAxis,
            source_side: bool,
    ) -> bool:
        """
        Insert the minimal local elbow topology next to one port.

        :param port_node_id: Port node identifier.
        :param preferred_axis: Original incident-segment axis to preserve when possible.
        :param source_side: Whether the edited port is the source side.
        :returns: ``True`` when one elbow was inserted successfully.
        """
        ordered_nodes: list[RoutingNode] = self._graph.get_ordered_nodes()
        if len(ordered_nodes) < 2:
            return False
        else:
            pass

        if source_side:
            port_node: RoutingNode = ordered_nodes[0]
            first_neighbour: RoutingNode = ordered_nodes[1]
        else:
            port_node = ordered_nodes[-1]
            first_neighbour = ordered_nodes[-2]

        base_segment: RoutingSegment | None = self._graph.find_segment_between_nodes(
            port_node_id,
            first_neighbour.get_node_id(),
        )
        if base_segment is None:
            return False
        else:
            pass

        # Local elbow insertion is the fallback when one direct port-to-neighbour
        # segment can no longer stay orthogonal. The editor inserts exactly one
        # new bend next to the edited port and reuses the old segment id.
        new_node_id: int = self._allocate_next_node_id()
        new_segment_id: int = self._allocate_next_segment_id()
        if preferred_axis == RoutingAxis.HORIZONTAL:
            elbow_position: RoutingPoint = RoutingPoint(
                port_node.get_position().get_x(),
                first_neighbour.get_position().get_y(),
            )
        else:
            elbow_position = RoutingPoint(
                first_neighbour.get_position().get_x(),
                port_node.get_position().get_y(),
            )

        elbow_node: RoutingNode = RoutingNode(
            node_id=new_node_id,
            kind=RoutingNodeKind.ELBOW,
            position=elbow_position,
        )
        if source_side:
            replacement_first: RoutingSegment = RoutingSegment(
                segment_id=base_segment.get_segment_id(),
                start_node_id=port_node.get_node_id(),
                end_node_id=new_node_id,
            )
            replacement_second: RoutingSegment = RoutingSegment(
                segment_id=new_segment_id,
                start_node_id=new_node_id,
                end_node_id=first_neighbour.get_node_id(),
            )
        else:
            replacement_first = RoutingSegment(
                segment_id=base_segment.get_segment_id(),
                start_node_id=first_neighbour.get_node_id(),
                end_node_id=new_node_id,
            )
            replacement_second = RoutingSegment(
                segment_id=new_segment_id,
                start_node_id=new_node_id,
                end_node_id=port_node.get_node_id(),
            )

        if self._graph._remove_segment(base_segment.get_segment_id()):
            pass
        else:
            return False
        if self._graph._add_node(elbow_node):
            pass
        else:
            return False
        if self._graph._add_segment(replacement_first):
            pass
        else:
            return False
        if self._graph._add_segment(replacement_second):
            return self._incident_segments_are_valid_for_nodes(
                [port_node.get_node_id(), new_node_id, first_neighbour.get_node_id()]
            )
        else:
            return False

    def _try_collapse_local_elbow(
            self,
            port_node: RoutingNode,
            elbow_node: RoutingNode,
            adjacent_node: RoutingNode,
    ) -> bool | None:
        """
        Remove one redundant local elbow before any repositioning.

        :param port_node: Edited port node.
        :param elbow_node: First elbow next to the port.
        :param adjacent_node: Node behind that elbow.
        :returns: ``True`` on successful collapse, ``False`` on attempted collapse
            failure, or ``None`` when the elbow cannot be removed yet.
        """
        if self._constraints.is_nodes_orthogonally_aligned(
                first_node=port_node,
                second_node=adjacent_node,
        ):
            # When the port can already see the next surviving node directly,
            # the local elbow has become redundant and can be removed before
            # any repositioning is attempted.
            success: bool = self.remove_elbow(elbow_node.get_node_id())
            if success:
                return self._incident_segments_are_valid_for_nodes(
                    [port_node.get_node_id(), adjacent_node.get_node_id()]
                )
            else:
                return False
        else:
            return None

    def _reposition_local_elbow(
            self,
            port_node: RoutingNode,
            elbow_node: RoutingNode,
            adjacent_node: RoutingNode,
    ) -> bool:
        """
        Reposition one existing local elbow after simplification failed.

        :param port_node: Edited port node.
        :param elbow_node: First elbow next to the edited port.
        :param adjacent_node: Node behind that elbow.
        :returns: ``True`` when the local topology remains valid.
        """
        second_segment: RoutingSegment | None = self._graph.find_segment_between_nodes(
            elbow_node.get_node_id(),
            adjacent_node.get_node_id(),
        )
        if second_segment is None:
            return False
        else:
            pass

        second_axis: RoutingAxis | None = self._graph.get_segment_axis(second_segment.get_segment_id())
        if second_axis is None:
            return False
        else:
            pass

        # Repositioning keeps the same local topology and only slides the first
        # interior bend along the axis allowed by the following segment.
        if second_axis == RoutingAxis.VERTICAL:
            elbow_node.set_position(
                RoutingPoint(
                    elbow_node.get_position().get_x(),
                    port_node.get_position().get_y(),
                )
            )
        else:
            elbow_node.set_position(
                RoutingPoint(
                    port_node.get_position().get_x(),
                    elbow_node.get_position().get_y(),
                )
            )

        if self._constraints.is_nodes_orthogonally_aligned(
                first_node=port_node,
                second_node=elbow_node,
        ):
            return self._incident_segments_are_valid_for_nodes(
                [port_node.get_node_id(), elbow_node.get_node_id(), adjacent_node.get_node_id()]
            )
        else:
            return False

    def _incident_segments_are_valid_for_nodes(self, node_ids: list[int]) -> bool:
        """
        Return whether every segment incident to the given nodes remains valid.

        :param node_ids: Node identifiers whose local neighbourhood changed.
        :returns: ``True`` when every incident segment remains orthogonal and non-zero.
        """
        segment_ids: list[int] = list()
        node_id: int
        for node_id in node_ids:
            route_node: RoutingNode | None = self._graph.get_node(node_id)
            if route_node is None:
                return False
            else:
                pass

            incident_segment_id: int
            for incident_segment_id in route_node.get_incident_segment_ids():
                if incident_segment_id in segment_ids:
                    pass
                else:
                    segment_ids.append(incident_segment_id)

        # Each changed node validates the complete set of incident segments so
        # one local edit cannot leave an unnoticed broken segment nearby.
        segment_id: int
        for segment_id in segment_ids:
            route_segment: RoutingSegment | None = self._graph.get_segment(segment_id)
            if route_segment is None:
                return False
            elif self._constraints.validate_segment(segment=route_segment):
                pass
            else:
                return False
        return True

    def _points_are_equal(self, first_point: RoutingPoint, second_point: RoutingPoint) -> bool:
        """
        Return whether two routing points have the same coordinates.

        :param first_point: First point.
        :param second_point: Second point.
        :returns: ``True`` when both coordinates are equal.
        """
        return self._geometry.are_points_numerically_equal(first_point, second_point)
