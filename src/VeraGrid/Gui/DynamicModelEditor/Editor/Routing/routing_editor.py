# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.automatic_route_builder import AutomaticRouteBuilder
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_constraint_engine import RoutingConstraintEngine
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_elements import RoutingNode
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_elements import RoutingPoint
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_elements import RoutingSegment
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_edit_validation import RoutingEditValidationResult
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_geometry import RoutingGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_graph import RoutingGraph
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingBlockGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingBounds
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingConnectionGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_validation import RoutingValidationReport
from VeraGridEngine.enumerations import RoutingAxis, RoutingNodeKind, RoutingPortSide


class RoutingEditor:
    """
    Transform one routing graph while preserving graph invariants.

    :return: None.
    """

    __slots__ = ("_graph", "_geometry", "_constraints", "_connection_geometry")

    def __init__(
            self,
            graph: RoutingGraph,
            connection_geometry: RoutingConnectionGeometry | None = None,
    ) -> None:
        """
        Build one routing editor bound to one graph.

        :param graph: Graph to edit.
        :param connection_geometry: Point-in-time non-Qt block geometry for the connection.
        :return: None.
        """
        self._graph: RoutingGraph = graph
        self._geometry: RoutingGeometry = graph.get_geometry()
        self._constraints: RoutingConstraintEngine = RoutingConstraintEngine(graph=graph)
        self._connection_geometry: RoutingConnectionGeometry | None = connection_geometry

    def get_graph(self) -> RoutingGraph:
        """
        :return: Edited graph.
        """
        return self._graph

    def move_elbow(self, elbow_id: int, new_position: RoutingPoint) -> bool:
        """
        Move one elbow by projecting it to one valid orthogonal corner.

        :param elbow_id: Elbow node identifier.
        :param new_position: Requested new elbow position.
        :return: ``True`` when the elbow changed position.
        """
        elbow_node: RoutingNode | None = self._graph.get_node(elbow_id)
        if elbow_node is None:
            return False
        elif elbow_node.get_kind() != RoutingNodeKind.ELBOW:
            return False
        else:
            pass

        if self._points_are_equal(elbow_node.get_position(), new_position):
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
        try:
            elbow_node.set_position(chosen_position)
            validation_result: RoutingEditValidationResult = self._validate_constraints(
                affected_node_ids=list((elbow_id,)),
            )
            if validation_result == RoutingEditValidationResult.VALID:
                return True
            else:
                # Segment dragging is an explicitly manual operation. Every
                # failed internal or environmental constraint restores only
                # this incremental move; automatic reconstruction would change
                # the selected segment identity and make the pointer appear to
                # stop at a freshly generated route position.
                self._graph._restore_from(graph_snapshot)
                return False
        except Exception:
            self._graph._restore_from(graph_snapshot)
            raise

    def update_port(self, node_id: int, new_position: RoutingPoint) -> bool:
        """
        Update one port node position after one block movement.

        :param node_id: Port node identifier.
        :param new_position: New port position.
        :return: ``True`` when the port was updated.
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

        try:
            updated: bool
            affected_node_ids: list[int]
            updated, affected_node_ids = self._apply_port_update(
                route_node=route_node,
                stub_node=adjacent_nodes[0],
                new_position=new_position,
            )
            validation_result: RoutingEditValidationResult = self._validate_constraints(
                affected_node_ids=affected_node_ids,
            )
            if updated and validation_result == RoutingEditValidationResult.VALID:
                return True
            elif updated and self._try_automatic_rebuild(reference_graph=graph_snapshot):
                return True
            else:
                self._graph._restore_from(graph_snapshot)
                return False
        except Exception:
            self._graph._restore_from(graph_snapshot)
            raise

    def _apply_port_update(
            self,
            route_node: RoutingNode,
            stub_node: RoutingNode,
            new_position: RoutingPoint,
    ) -> tuple[bool, list[int]]:
        """
        Apply the complete local port and stub geometry update.

        This helper mutates only the live graph neighbourhood. The public
        operation owns the snapshot, final validation and rollback.

        :param route_node: Port node being moved.
        :param stub_node: Immediate stub connected to the port.
        :param new_position: Requested new port position.
        :return: Update state and node identifiers whose geometry may differ.
        """
        affected_node_ids: list[int] = list()
        node_id: int = route_node.get_node_id()
        port_side: RoutingPortSide | None = route_node.get_port_side()
        if stub_node.get_kind() != RoutingNodeKind.STUB:
            return False, affected_node_ids
        elif not route_node.has_port_side() or port_side is None:
            return False, affected_node_ids
        else:
            pass

        original_port_position: RoutingPoint = route_node.get_position().copy()
        delta_x: float = new_position.get_x() - original_port_position.get_x()
        delta_y: float = new_position.get_y() - original_port_position.get_y()

        # Move the physical endpoint and rebuild its explicit stub through the
        # same geometry policy used by RouteBuilder. Its mandatory continuation
        # receives the same translation so endpoint movement is absorbed by the
        # central route rather than by stretching this local attachment.
        route_node.set_position(new_position.copy())
        stub_position: RoutingPoint = self._geometry.build_port_stub_point(
            port_position=new_position,
            port_side=port_side,
        )
        stub_node.set_position(stub_position)

        if self._graph.get_source_node_id() == node_id:
            updated: bool = self._update_source_stub_neighbourhood(
                stub_node_id=stub_node.get_node_id(),
                delta_x=delta_x,
                delta_y=delta_y,
            )
        elif self._graph.get_destination_node_id() == node_id:
            updated = self._update_destination_stub_neighbourhood(
                stub_node_id=stub_node.get_node_id(),
                delta_x=delta_x,
                delta_y=delta_y,
            )
        else:
            return False, affected_node_ids

        if updated:
            affected_node_ids.append(node_id)
            affected_node_ids.append(stub_node.get_node_id())
            adjacent_node: RoutingNode
            for adjacent_node in self._graph.adjacent_nodes(stub_node.get_node_id()):
                if adjacent_node.get_node_id() in affected_node_ids:
                    pass
                else:
                    affected_node_ids.append(adjacent_node.get_node_id())
                second_adjacent_node: RoutingNode
                for second_adjacent_node in self._graph.adjacent_nodes(adjacent_node.get_node_id()):
                    if second_adjacent_node.get_node_id() in affected_node_ids:
                        pass
                    else:
                        affected_node_ids.append(second_adjacent_node.get_node_id())
            return True, affected_node_ids
        else:
            return False, affected_node_ids

    def move_segment(self, segment_id: int, coordinate_offset: float) -> bool:
        """
        Move one interior segment along its perpendicular axis.

        :param segment_id: Segment identifier.
        :param coordinate_offset: Requested offset along the allowed drag axis.
        :return: ``True`` when the segment moved.
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
        try:
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

            validation_result: RoutingEditValidationResult = self._validate_constraints(
                affected_node_ids=list((start_node.get_node_id(), end_node.get_node_id(),)),
            )
            if validation_result == RoutingEditValidationResult.VALID:
                return True
            elif validation_result == RoutingEditValidationResult.INTERNAL_CONFLICT:
                self._graph._restore_from(graph_snapshot)
                return False
            elif self._try_automatic_rebuild(reference_graph=graph_snapshot):
                return True
            else:
                self._graph._restore_from(graph_snapshot)
                return False
        except Exception:
            self._graph._restore_from(graph_snapshot)
            raise

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
        :return: Chosen orthogonal corner.
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
        :return: Squared Euclidean distance.
        """
        delta_x: float = first_point.get_x() - second_point.get_x()
        delta_y: float = first_point.get_y() - second_point.get_y()
        return delta_x * delta_x + delta_y * delta_y

    def _update_source_stub_neighbourhood(
            self,
            stub_node_id: int,
            delta_x: float,
            delta_y: float,
    ) -> bool:
        """
        Update the local source-side neighbourhood after moving its port stub.

        :param stub_node_id: Source stub node identifier.
        :param delta_x: Horizontal port displacement.
        :param delta_y: Vertical port displacement.
        :return: ``True`` when the local update succeeded.
        """
        return self._update_stub_neighbourhood(
            stub_node_id=stub_node_id,
            source_side=True,
            delta_x=delta_x,
            delta_y=delta_y,
        )

    def _update_destination_stub_neighbourhood(
            self,
            stub_node_id: int,
            delta_x: float,
            delta_y: float,
    ) -> bool:
        """
        Update the local destination-side neighbourhood after moving its port stub.

        :param stub_node_id: Destination stub node identifier.
        :param delta_x: Horizontal port displacement.
        :param delta_y: Vertical port displacement.
        :return: ``True`` when the local update succeeded.
        """
        return self._update_stub_neighbourhood(
            stub_node_id=stub_node_id,
            source_side=False,
            delta_x=delta_x,
            delta_y=delta_y,
        )

    def _update_stub_neighbourhood(
            self,
            stub_node_id: int,
            source_side: bool,
            delta_x: float,
            delta_y: float,
    ) -> bool:
        """
        Update the route neighbourhood immediately after one port-side stub.

        A port move preserves topology by moving the port and then sliding its
        stub only as much as needed to keep the first segment perpendicular.
        The stub length is not fixed here; it may grow or shrink as long as the
        later constraint validation accepts the resulting PORT->STUB segment.

        :param stub_node_id: Stub node identifier.
        :param source_side: Whether the edited port is the source side.
        :param delta_x: Horizontal port displacement.
        :param delta_y: Vertical port displacement.
        :return: ``True`` when the local update succeeded.
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

        if first_neighbour.get_kind() != RoutingNodeKind.ELBOW and first_neighbour.get_kind() != RoutingNodeKind.STUB:
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

            second_segment: RoutingSegment | None = self._graph.find_segment_between_nodes(
                first_neighbour.get_node_id(),
                second_neighbour.get_node_id(),
            )
            if second_segment is None:
                return False
            else:
                second_axis: RoutingAxis | None = self._graph.get_segment_axis(second_segment.get_segment_id())
            if second_axis is None:
                return False
            else:
                pass

            # PORT, STUB and continuation form one rigid endpoint attachment.
            # Keeping their relative coordinates prevents the continuation
            # from remaining at the old block position and later becoming an
            # artificial limit for manual central-segment movement.
            first_neighbour.set_position(
                RoutingPoint(
                    first_neighbour.get_position().get_x() + delta_x,
                    first_neighbour.get_position().get_y() + delta_y,
                )
            )
            return self._reposition_local_elbow(
                stub_node=anchor_node,
                continuation_node=first_neighbour,
                adjacent_node=second_neighbour,
                second_axis=second_axis,
            )

    def _reposition_local_elbow(
            self,
            stub_node: RoutingNode,
            continuation_node: RoutingNode,
            adjacent_node: RoutingNode,
            second_axis: RoutingAxis,
    ) -> bool:
        """
        Reposition one existing local elbow after simplification failed.

        :param stub_node: Rebuilt stub next to the edited port.
        :param continuation_node: Mandatory continuation next to the stub.
        :param adjacent_node: First central-route node behind the continuation.
        :param second_axis: Original axis from the continuation into the central route.
        :return: ``True`` when the local topology remains valid.
        """
        # Preserve the original central-entry axis after translating the rigid
        # endpoint attachment. Only the adjacent elbow receives the transverse
        # coordinate; its longitudinal coordinate and all deeper nodes remain
        # untouched.
        if second_axis == RoutingAxis.HORIZONTAL:
            adjacent_node.set_position(
                RoutingPoint(
                    adjacent_node.get_position().get_x(),
                    continuation_node.get_position().get_y(),
                )
            )
        else:
            adjacent_node.set_position(
                RoutingPoint(
                    continuation_node.get_position().get_x(),
                    adjacent_node.get_position().get_y(),
                )
            )

        stub_segment: RoutingSegment | None = self._graph.find_segment_between_nodes(
            stub_node.get_node_id(),
            continuation_node.get_node_id(),
        )
        if stub_segment is None:
            return False
        elif not self._constraints.is_stub_continuation_valid_for_segment(segment=stub_segment):
            return False
        elif self._constraints.is_nodes_orthogonally_aligned(
                first_node=continuation_node,
                second_node=adjacent_node,
        ):
            return True
        else:
            return False

    def _validate_constraints(
            self,
            affected_node_ids: list[int],
    ) -> RoutingEditValidationResult:
        """
        Validate graph invariants and geometric constraints after one edit.

        The editor owns the transaction and graph mutation. This method only
        identifies the affected geometry and asks the graph and constraint
        engine whether the resulting state can be committed.

        :param affected_node_ids: Nodes whose local geometry may have changed.
        :return: Validation result distinguishing internal and environmental failures.
        """
        graph_report: RoutingValidationReport = self._graph.validate()
        if graph_report.is_valid():
            pass
        else:
            return RoutingEditValidationResult.INTERNAL_CONFLICT

        affected_segment_ids: set[int] = set()
        node_id: int
        for node_id in affected_node_ids:
            route_node: RoutingNode | None = self._graph.get_node(node_id)
            if route_node is None:
                return RoutingEditValidationResult.INTERNAL_CONFLICT
            else:
                pass

            incident_segment_id: int
            for incident_segment_id in route_node.get_incident_segment_ids():
                affected_segment_ids.add(incident_segment_id)

        # Segment constraints run for the complete changed neighbourhood. Port
        # connections then receive their additional side and stub-length rules.
        segment_id: int
        for segment_id in sorted(affected_segment_ids):
            route_segment: RoutingSegment | None = self._graph.get_segment(segment_id)
            if route_segment is None:
                return RoutingEditValidationResult.INTERNAL_CONFLICT
            else:
                pass

            start_node: RoutingNode | None = self._graph.get_node(route_segment.get_start_node_id())
            end_node: RoutingNode | None = self._graph.get_node(route_segment.get_end_node_id())
            if start_node is None or end_node is None:
                return RoutingEditValidationResult.INTERNAL_CONFLICT
            else:
                pass

            # Manual geometry cannot collapse, become diagonal, cross another
            # part of its own route or backtrack over an adjacent segment.
            # These failures act as drag limits and must never invoke automatic
            # route reconstruction.
            if not self._constraints.is_segment_orthogonal(segment=route_segment):
                return RoutingEditValidationResult.INTERNAL_CONFLICT
            elif not self._constraints.is_segment_long_enough(segment=route_segment):
                return RoutingEditValidationResult.INTERNAL_CONFLICT
            elif not self._constraints.is_stub_continuation_valid_for_segment(segment=route_segment):
                return RoutingEditValidationResult.INTERNAL_CONFLICT
            elif self._constraints.segment_has_invalid_own_route_intersection(segment=route_segment):
                return RoutingEditValidationResult.INTERNAL_CONFLICT
            else:
                pass

            start_is_port: bool = start_node.get_kind() == RoutingNodeKind.PORT
            end_is_port: bool = end_node.get_kind() == RoutingNodeKind.PORT
            if start_is_port:
                if (not self._constraints.is_port_connection_perpendicular(
                        port_node=start_node,
                        neighbour_node=end_node,
                ) or not self._constraints.is_first_segment_long_enough(
                        port_node=start_node,
                        neighbour_node=end_node,
                )):
                    return RoutingEditValidationResult.INTERNAL_CONFLICT
                else:
                    pass
            else:
                pass
            if end_is_port:
                if (not self._constraints.is_port_connection_perpendicular(
                        port_node=end_node,
                        neighbour_node=start_node,
                ) or not self._constraints.is_first_segment_long_enough(
                        port_node=end_node,
                        neighbour_node=start_node,
                )):
                    return RoutingEditValidationResult.INTERNAL_CONFLICT
                else:
                    pass
            else:
                pass

            if not start_is_port and not end_is_port:
                if self._constraints.validate_segment(
                        segment=route_segment,
                        connection_geometry=self._connection_geometry,
                ):
                    pass
                else:
                    return RoutingEditValidationResult.ENVIRONMENT_CONFLICT
            else:
                pass

            if start_is_port:
                start_owner_bounds: RoutingBounds | None = self._get_port_owner_bounds(port_node=start_node)
                if self._constraints.validate_connection(
                        port_node=start_node,
                        neighbour_node=end_node,
                        segment=route_segment,
                        block_bounds=start_owner_bounds,
                        connection_geometry=self._connection_geometry,
                ):
                    pass
                else:
                    return RoutingEditValidationResult.ENVIRONMENT_CONFLICT
            else:
                pass

            if end_is_port:
                end_owner_bounds: RoutingBounds | None = self._get_port_owner_bounds(port_node=end_node)
                if self._constraints.validate_connection(
                        port_node=end_node,
                        neighbour_node=start_node,
                        segment=route_segment,
                        block_bounds=end_owner_bounds,
                        connection_geometry=self._connection_geometry,
                ):
                    pass
                else:
                    return RoutingEditValidationResult.ENVIRONMENT_CONFLICT
            else:
                pass
        return RoutingEditValidationResult.VALID

    def _get_port_owner_bounds(self, port_node: RoutingNode) -> RoutingBounds | None:
        """
        Return the captured owner bounds for one source or destination port.

        :param port_node: Port node being validated.
        :return: Matching endpoint-owner bounds or ``None`` when unavailable.
        """
        if self._connection_geometry is None:
            return None
        elif port_node.get_node_id() == self._graph.get_source_node_id():
            source_owner: RoutingBlockGeometry | None = self._connection_geometry.get_source_owner()
            if source_owner is not None:
                return source_owner.get_bounds()
            else:
                return None
        elif port_node.get_node_id() == self._graph.get_destination_node_id():
            destination_owner: RoutingBlockGeometry | None = self._connection_geometry.get_destination_owner()
            if destination_owner is not None:
                return destination_owner.get_bounds()
            else:
                return None
        else:
            return None

    def _try_automatic_rebuild(self, reference_graph: RoutingGraph | None = None) -> bool:
        """
        Replace the current conflicting interval with an automatic candidate.

        The automatic builder works on the current temporary graph and returns
        a detached result. The public edit retains ownership of the original
        snapshot and therefore still performs the final rollback when no
        alternative can be found.

        :param reference_graph: Manual route snapshot used to minimize changes.
        :return: ``True`` when an alternative graph replaced the temporary graph.
        """
        if self._connection_geometry is None:
            return False
        else:
            automatic_builder: AutomaticRouteBuilder = AutomaticRouteBuilder(
                graph=self._graph,
                connection_geometry=self._connection_geometry,
                reference_graph=reference_graph,
            )
            alternative_graph: RoutingGraph | None = automatic_builder.build_alternative()
            if alternative_graph is None:
                return False
            else:
                self._graph._restore_from(alternative_graph)
                return True

    def _points_are_equal(self, first_point: RoutingPoint, second_point: RoutingPoint) -> bool:
        """
        Return whether two routing points have the same coordinates.

        :param first_point: First point.
        :param second_point: Second point.
        :return: ``True`` when both coordinates are equal.
        """
        return self._geometry.are_points_numerically_equal(first_point, second_point)
