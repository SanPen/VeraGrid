# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingNode
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingSegment
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import derive_segment_axis
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_geometry import RoutingGeometry
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_validation import RoutingValidationMessage
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_validation import RoutingValidationReport
from VeraGridEngine.enumerations import RoutingAxis, RoutingNodeKind, RoutingValidationMessageLevel


class RoutingGraph:
    """
    Represent one complete routed connection as one simple graph path.

    :return: None.
    """

    __slots__ = ("_nodes_by_id", "_segments_by_id", "_source_node_id", "_destination_node_id", "_geometry")

    def __init__(self, source_node_id: int, destination_node_id: int) -> None:
        """
        Build one empty routing graph.

        :param source_node_id: Source port node identifier.
        :param destination_node_id: Destination port node identifier.
        :return: None.
        """
        self._nodes_by_id: dict[int, RoutingNode] = dict()
        self._segments_by_id: dict[int, RoutingSegment] = dict()
        self._source_node_id: int = int(source_node_id)
        self._destination_node_id: int = int(destination_node_id)
        self._geometry: RoutingGeometry = RoutingGeometry()

    def get_geometry(self) -> RoutingGeometry:
        """
        :return: Shared routing geometry helper.
        """
        return self._geometry

    def get_source_node_id(self) -> int:
        """
        :return: Source port node identifier.
        """
        return self._source_node_id

    def get_destination_node_id(self) -> int:
        """
        :return: Destination port node identifier.
        """
        return self._destination_node_id

    def get_source_node(self) -> RoutingNode | None:
        """
        Return the source port node.

        :return: Source port node or ``None``.
        """
        return self.get_node(self._source_node_id)

    def get_destination_node(self) -> RoutingNode | None:
        """
        Return the destination port node.

        :return: Destination port node or ``None``.
        """
        return self.get_node(self._destination_node_id)

    def get_node(self, node_id: int) -> RoutingNode | None:
        """
        Return one node by identifier.

        :param node_id: Node identifier.
        :return: Node or ``None``.
        """
        return self._nodes_by_id.get(int(node_id), None)

    def get_segment(self, segment_id: int) -> RoutingSegment | None:
        """
        Return one segment by identifier.

        :param segment_id: Segment identifier.
        :return: Segment or ``None``.
        """
        return self._segments_by_id.get(int(segment_id), None)

    def get_nodes(self) -> list[RoutingNode]:
        """
        Return every node in the graph.

        :return: Graph nodes.
        """
        return list(self._nodes_by_id.values())

    def get_segments(self) -> list[RoutingSegment]:
        """
        Return every segment in the graph.

        :return: Graph segments.
        """
        return list(self._segments_by_id.values())

    def adjacent_segments(self, node_id: int) -> list[RoutingSegment]:
        """
        Return the segments incident to one node.

        :param node_id: Node identifier.
        :return: Adjacent segments.
        """
        adjacent_items: list[RoutingSegment] = list()
        route_node: RoutingNode | None = self.get_node(node_id)
        if route_node is None:
            return adjacent_items
        else:
            pass

        segment_id: int
        for segment_id in route_node.get_incident_segment_ids():
            route_segment: RoutingSegment | None = self.get_segment(segment_id)
            if route_segment is None:
                pass
            else:
                adjacent_items.append(route_segment)
        return adjacent_items

    def adjacent_nodes(self, node_id: int) -> list[RoutingNode]:
        """
        Return the nodes adjacent to one node.

        :param node_id: Node identifier.
        :return: Adjacent nodes.
        """
        adjacent_items: list[RoutingNode] = list()
        route_segment: RoutingSegment
        for route_segment in self.adjacent_segments(node_id):
            other_node_id: int | None = route_segment.get_other_node_id(node_id)
            if other_node_id is None:
                pass
            else:
                other_node: RoutingNode | None = self.get_node(other_node_id)
                if other_node is None:
                    pass
                else:
                    adjacent_items.append(other_node)
        return adjacent_items

    def degree(self, node_id: int) -> int:
        """
        Return the degree of one node.

        :param node_id: Node identifier.
        :return: Node degree.
        """
        route_node: RoutingNode | None = self.get_node(node_id)
        if route_node is None:
            return 0
        else:
            return len(route_node.get_incident_segment_ids())

    def get_segment_axis(self, segment_id: int) -> RoutingAxis | None:
        """
        Return the derived axis of one segment.

        :param segment_id: Segment identifier.
        :return: Derived axis or ``None``.
        """
        route_segment: RoutingSegment | None = self.get_segment(segment_id)
        if route_segment is None:
            return None
        else:
            pass

        start_node: RoutingNode | None = self.get_node(route_segment.get_start_node_id())
        end_node: RoutingNode | None = self.get_node(route_segment.get_end_node_id())
        if start_node is None or end_node is None:
            return None
        else:
            pass

        axis = derive_segment_axis(
            start_x=start_node.get_position().get_x(),
            start_y=start_node.get_position().get_y(),
            end_x=end_node.get_position().get_x(),
            end_y=end_node.get_position().get_y(),
        )
        return axis

    def get_ordered_nodes(self) -> list[RoutingNode]:
        """
        Return the nodes ordered from source to destination.

        :return: Ordered graph nodes.
        """
        ordered_items: list[RoutingNode] = list()
        source_node: RoutingNode | None = self.get_source_node()
        destination_node: RoutingNode | None = self.get_destination_node()
        if source_node is None or destination_node is None:
            return ordered_items
        else:
            pass

        previous_node_id: int | None = None
        current_node_id: int | None = self._source_node_id

        # The Phase 1 graph is a simple path, so walking from the source by
        # repeatedly choosing the neighbour that is not the previous node
        # deterministically yields the entire ordered route.
        while current_node_id is not None:
            current_node: RoutingNode | None = self.get_node(current_node_id)
            if current_node is None:
                return list()
            else:
                ordered_items.append(current_node)

            if current_node_id == self._destination_node_id:
                return ordered_items
            else:
                pass

            next_node_id: int | None = self._find_next_node_in_path(current_node_id, previous_node_id)
            previous_node_id = current_node_id
            current_node_id = next_node_id

        return list()

    def get_ordered_segments(self) -> list[RoutingSegment]:
        """
        Return the segments ordered from source to destination.

        :return: Ordered graph segments.
        """
        ordered_items: list[RoutingSegment] = list()
        ordered_nodes: list[RoutingNode] = self.get_ordered_nodes()
        if len(ordered_nodes) < 2:
            return ordered_items
        else:
            pass

        node_index: int
        for node_index in range(len(ordered_nodes) - 1):
            start_node: RoutingNode = ordered_nodes[node_index]
            end_node: RoutingNode = ordered_nodes[node_index + 1]
            route_segment: RoutingSegment | None = self.find_segment_between_nodes(
                start_node.get_node_id(),
                end_node.get_node_id(),
            )
            if route_segment is None:
                return list()
            else:
                ordered_items.append(route_segment)
        return ordered_items

    def find_segment_between_nodes(self, first_node_id: int, second_node_id: int) -> RoutingSegment | None:
        """
        Return the segment connecting two nodes when it exists.

        :param first_node_id: First node identifier.
        :param second_node_id: Second node identifier.
        :return: Connecting segment or ``None``.
        """
        route_segment: RoutingSegment
        for route_segment in self.adjacent_segments(first_node_id):
            other_node_id: int | None = route_segment.get_other_node_id(first_node_id)
            if other_node_id == int(second_node_id):
                return route_segment
            else:
                pass
        return None

    def clone(self) -> "RoutingGraph":
        """
        Build a detached copy of the graph.

        :return: Graph copy.
        """
        graph_copy: RoutingGraph = RoutingGraph(
            source_node_id=self._source_node_id,
            destination_node_id=self._destination_node_id,
        )

        node_id: int
        for node_id in sorted(self._nodes_by_id.keys()):
            graph_copy._add_node(self._nodes_by_id[node_id].clone())

        segment_id: int
        for segment_id in sorted(self._segments_by_id.keys()):
            graph_copy._add_segment(self._segments_by_id[segment_id].clone())

        return graph_copy

    def _restore_from(self, other_graph: "RoutingGraph") -> None:
        """
        Restore the full graph state from one detached snapshot.

        :param other_graph: Snapshot used as the restoration source.
        :return: None.
        """
        self._nodes_by_id = dict()
        self._segments_by_id = dict()
        self._source_node_id = other_graph.get_source_node_id()
        self._destination_node_id = other_graph.get_destination_node_id()

        node_id: int
        for node_id in sorted([route_node.get_node_id() for route_node in other_graph.get_nodes()]):
            route_node: RoutingNode | None = other_graph.get_node(node_id)
            if route_node is None:
                pass
            else:
                self._add_node(route_node.clone())

        segment_id: int
        for segment_id in sorted([route_segment.get_segment_id() for route_segment in other_graph.get_segments()]):
            route_segment: RoutingSegment | None = other_graph.get_segment(segment_id)
            if route_segment is None:
                pass
            else:
                self._add_segment(route_segment.clone())

    def validate(self) -> RoutingValidationReport:
        """
        Validate the graph invariants.

        :return: Validation report.
        """
        report: RoutingValidationReport = RoutingValidationReport()
        self._validate_source_and_destination_nodes(report)
        self._validate_segments(report)
        self._validate_node_degrees(report)
        self._validate_orphans(report)
        self._validate_connectivity(report)
        self._validate_path_order(report)
        return report

    def _add_node(self, node: RoutingNode) -> bool:
        """
        Add one node to the graph.

        :param node: Node to add.
        :return: ``True`` when the node was added.
        """
        node_id: int = node.get_node_id()
        if node_id in self._nodes_by_id:
            return False
        else:
            self._nodes_by_id[node_id] = node
            return True

    def _remove_node(self, node_id: int) -> bool:
        """
        Remove one isolated node from the graph.

        :param node_id: Node identifier.
        :return: ``True`` when the node was removed.
        """
        route_node: RoutingNode | None = self.get_node(node_id)
        if route_node is None:
            return False
        elif len(route_node.get_incident_segment_ids()) > 0:
            return False
        else:
            del self._nodes_by_id[int(node_id)]
            return True

    def _add_segment(self, segment: RoutingSegment) -> bool:
        """
        Add one segment to the graph.

        :param segment: Segment to add.
        :return: ``True`` when the segment was added.
        """
        segment_id: int = segment.get_segment_id()
        if segment_id in self._segments_by_id:
            return False
        else:
            pass

        start_node: RoutingNode | None = self.get_node(segment.get_start_node_id())
        end_node: RoutingNode | None = self.get_node(segment.get_end_node_id())
        if start_node is None or end_node is None:
            return False
        else:
            pass

        if self.find_segment_between_nodes(segment.get_start_node_id(), segment.get_end_node_id()) is None:
            pass
        else:
            return False

        self._segments_by_id[segment_id] = segment
        start_node.add_incident_segment_id(segment_id)
        end_node.add_incident_segment_id(segment_id)
        return True

    def _remove_segment(self, segment_id: int) -> bool:
        """
        Remove one segment from the graph.

        :param segment_id: Segment identifier.
        :return: ``True`` when the segment was removed.
        """
        route_segment: RoutingSegment | None = self.get_segment(segment_id)
        if route_segment is None:
            return False
        else:
            pass

        start_node: RoutingNode | None = self.get_node(route_segment.get_start_node_id())
        end_node: RoutingNode | None = self.get_node(route_segment.get_end_node_id())
        if start_node is None or end_node is None:
            return False
        else:
            pass

        start_node.remove_incident_segment_id(segment_id)
        end_node.remove_incident_segment_id(segment_id)
        del self._segments_by_id[int(segment_id)]
        return True

    def _find_next_node_in_path(self, current_node_id: int, previous_node_id: int | None) -> int | None:
        """
        Return the next node when traversing the simple path.

        :param current_node_id: Current node identifier.
        :param previous_node_id: Previously visited node identifier or ``None``.
        :return: Next node identifier or ``None``.
        """
        route_segment: RoutingSegment
        for route_segment in self.adjacent_segments(current_node_id):
            other_node_id: int | None = route_segment.get_other_node_id(current_node_id)
            if other_node_id is None:
                pass
            elif previous_node_id is None:
                return other_node_id
            elif other_node_id != previous_node_id:
                return other_node_id
            else:
                pass
        return None

    def _validate_source_and_destination_nodes(self, report: RoutingValidationReport) -> None:
        """
        Validate the source and destination node definitions.

        :param report: Validation report to update.
        :return: None.
        """
        source_node: RoutingNode | None = self.get_source_node()
        destination_node: RoutingNode | None = self.get_destination_node()
        if source_node is None:
            report.add_message(
                RoutingValidationMessage(
                    level=RoutingValidationMessageLevel.ERROR,
                    code="missing_source_node",
                    message="The graph does not contain the source port node.",
                    node_id=self._source_node_id,
                    segment_id=None,
                )
            )
        elif source_node.get_kind() != RoutingNodeKind.PORT:
            report.add_message(
                RoutingValidationMessage(
                    level=RoutingValidationMessageLevel.ERROR,
                    code="invalid_source_kind",
                    message="The source node is not a port node.",
                    node_id=source_node.get_node_id(),
                    segment_id=None,
                )
            )
        else:
            pass

        if destination_node is None:
            report.add_message(
                RoutingValidationMessage(
                    level=RoutingValidationMessageLevel.ERROR,
                    code="missing_destination_node",
                    message="The graph does not contain the destination port node.",
                    node_id=self._destination_node_id,
                    segment_id=None,
                )
            )
        elif destination_node.get_kind() != RoutingNodeKind.PORT:
            report.add_message(
                RoutingValidationMessage(
                    level=RoutingValidationMessageLevel.ERROR,
                    code="invalid_destination_kind",
                    message="The destination node is not a port node.",
                    node_id=destination_node.get_node_id(),
                    segment_id=None,
                )
            )
        else:
            pass

    def _validate_segments(self, report: RoutingValidationReport) -> None:
        """
        Validate segment endpoint references and orthogonality.

        :param report: Validation report to update.
        :return: None.
        """
        route_segment: RoutingSegment
        for route_segment in self.get_segments():
            start_node: RoutingNode | None = self.get_node(route_segment.get_start_node_id())
            end_node: RoutingNode | None = self.get_node(route_segment.get_end_node_id())
            if start_node is None or end_node is None:
                report.add_message(
                    RoutingValidationMessage(
                        level=RoutingValidationMessageLevel.ERROR,
                        code="dangling_segment",
                        message="One segment references one or more missing nodes.",
                        node_id=None,
                        segment_id=route_segment.get_segment_id(),
                    )
                )
            elif route_segment.get_start_node_id() == route_segment.get_end_node_id():
                report.add_message(
                    RoutingValidationMessage(
                        level=RoutingValidationMessageLevel.ERROR,
                        code="self_loop_segment",
                        message="One segment connects one node to itself.",
                        node_id=start_node.get_node_id(),
                        segment_id=route_segment.get_segment_id(),
                    )
                )
            elif self.get_segment_axis(route_segment.get_segment_id()) is None:
                report.add_message(
                    RoutingValidationMessage(
                        level=RoutingValidationMessageLevel.ERROR,
                        code="non_orthogonal_segment",
                        message="One segment is diagonal or has zero length.",
                        node_id=None,
                        segment_id=route_segment.get_segment_id(),
                    )
                )
            else:
                pass

    def _validate_node_degrees(self, report: RoutingValidationReport) -> None:
        """
        Validate degree rules for all nodes.

        :param report: Validation report to update.
        :return: None.
        """
        route_node: RoutingNode
        for route_node in self.get_nodes():
            node_degree: int = self.degree(route_node.get_node_id())
            if route_node.get_kind() == RoutingNodeKind.PORT:
                if route_node.get_node_id() == self._source_node_id or route_node.get_node_id() == self._destination_node_id:
                    if node_degree == 1:
                        pass
                    else:
                        report.add_message(
                            RoutingValidationMessage(
                                level=RoutingValidationMessageLevel.ERROR,
                                code="invalid_port_degree",
                                message="A port node does not have degree one.",
                                node_id=route_node.get_node_id(),
                                segment_id=None,
                            )
                        )
                else:
                    report.add_message(
                        RoutingValidationMessage(
                            level=RoutingValidationMessageLevel.ERROR,
                            code="unexpected_port_node",
                            message="One port node is neither the source nor the destination.",
                            node_id=route_node.get_node_id(),
                            segment_id=None,
                        )
                    )
            elif route_node.get_kind() == RoutingNodeKind.ELBOW or route_node.get_kind() == RoutingNodeKind.STUB:
                if node_degree == 2:
                    pass
                else:
                    report.add_message(
                        RoutingValidationMessage(
                            level=RoutingValidationMessageLevel.ERROR,
                            code="invalid_bend_degree",
                            message="A bend node does not have degree two.",
                            node_id=route_node.get_node_id(),
                            segment_id=None,
                        )
                    )
            else:
                report.add_message(
                    RoutingValidationMessage(
                        level=RoutingValidationMessageLevel.ERROR,
                        code="unsupported_node_kind",
                        message="The graph contains an unsupported node kind.",
                        node_id=route_node.get_node_id(),
                        segment_id=None,
                    )
                )

    def _validate_orphans(self, report: RoutingValidationReport) -> None:
        """
        Validate that no orphan nodes exist.

        :param report: Validation report to update.
        :return: None.
        """
        route_node: RoutingNode
        for route_node in self.get_nodes():
            if len(route_node.get_incident_segment_ids()) == 0:
                report.add_message(
                    RoutingValidationMessage(
                        level=RoutingValidationMessageLevel.ERROR,
                        code="orphan_node",
                        message="The graph contains one orphan node.",
                        node_id=route_node.get_node_id(),
                        segment_id=None,
                    )
                )
            else:
                pass

    def _validate_connectivity(self, report: RoutingValidationReport) -> None:
        """
        Validate that the graph is connected.

        :param report: Validation report to update.
        :return: None.
        """
        source_node: RoutingNode | None = self.get_source_node()
        if source_node is None:
            return
        else:
            pass

        visited_node_ids: list[int] = list()
        pending_node_ids: list[int] = list()
        pending_node_ids.append(source_node.get_node_id())

        while len(pending_node_ids) > 0:
            current_node_id: int = pending_node_ids.pop(0)
            if current_node_id in visited_node_ids:
                pass
            else:
                visited_node_ids.append(current_node_id)
                adjacent_node: RoutingNode
                for adjacent_node in self.adjacent_nodes(current_node_id):
                    if adjacent_node.get_node_id() in visited_node_ids:
                        pass
                    else:
                        pending_node_ids.append(adjacent_node.get_node_id())

        if len(visited_node_ids) == len(self._nodes_by_id):
            pass
        else:
            report.add_message(
                RoutingValidationMessage(
                    level=RoutingValidationMessageLevel.ERROR,
                    code="disconnected_graph",
                    message="The graph is not connected.",
                    node_id=None,
                    segment_id=None,
                )
            )

    def _validate_path_order(self, report: RoutingValidationReport) -> None:
        """
        Validate that stable source-to-destination traversal exists.

        :param report: Validation report to update.
        :return: None.
        """
        ordered_nodes: list[RoutingNode] = self.get_ordered_nodes()
        ordered_segments: list[RoutingSegment] = self.get_ordered_segments()
        if len(self._nodes_by_id) == 0:
            return
        elif len(ordered_nodes) != len(self._nodes_by_id):
            report.add_message(
                RoutingValidationMessage(
                    level=RoutingValidationMessageLevel.ERROR,
                    code="invalid_node_traversal",
                    message="The graph cannot derive a complete ordered node traversal.",
                    node_id=None,
                    segment_id=None,
                )
            )
        elif len(ordered_segments) != len(self._segments_by_id):
            report.add_message(
                RoutingValidationMessage(
                    level=RoutingValidationMessageLevel.ERROR,
                    code="invalid_segment_traversal",
                    message="The graph cannot derive a complete ordered segment traversal.",
                    node_id=None,
                    segment_id=None,
                )
            )
        else:
            pass
