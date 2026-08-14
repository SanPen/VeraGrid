# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from PySide6.QtGui import QPainterPath

from VeraGrid.Gui.DynamicModelEditor.Routing.route_builder import RouteBuilder
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_editor import RoutingEditor
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingSegment
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_graph import RoutingGraph
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_serializer import RoutingGraphSerializer
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_serializer import RoutingSerializedGraph
from VeraGrid.Gui.DynamicModelEditor.RoutingQt.routing_qt_adapter import QtRoutingGraphAdapter
from VeraGrid.Gui.DynamicModelEditor.RoutingQt.routing_qt_port_snapshot import QtRoutingPortSnapshot
from VeraGrid.Gui.DynamicModelEditor.RoutingQt.routing_qt_port_snapshot import build_qt_routing_port_snapshot
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_graphics import PortItem


class QtRoutingSession:
    """
    Bridge Qt connection gestures with the new routing engine graph model.

    :returns: None.
    """

    __slots__ = ("_graphs_by_connection_uid", "_serializer", "_adapter")

    def __init__(self) -> None:
        """
        Build one Qt routing session for the new routing engine.

        :returns: None.
        """
        self._graphs_by_connection_uid: dict[int, RoutingGraph] = dict()
        self._serializer: RoutingGraphSerializer = RoutingGraphSerializer()
        self._adapter: QtRoutingGraphAdapter = QtRoutingGraphAdapter()

    def has_connection(self, connection_uid: int) -> bool:
        """
        Return whether one connection graph is registered.

        :param connection_uid: Stable connection identifier.
        :returns: ``True`` when the graph exists in the session.
        """
        if int(connection_uid) in self._graphs_by_connection_uid:
            return True
        else:
            return False

    def remove_connection(self, connection_uid: int) -> bool:
        """
        Remove one connection graph from the session.

        :param connection_uid: Stable connection identifier.
        :returns: ``True`` when the graph existed and was removed.
        """
        connection_identifier: int = int(connection_uid)
        if connection_identifier in self._graphs_by_connection_uid:
            del self._graphs_by_connection_uid[connection_identifier]
            return True
        else:
            return False

    def get_graph(self, connection_uid: int) -> RoutingGraph | None:
        """
        Return one registered routing graph.

        :param connection_uid: Stable connection identifier.
        :returns: Registered routing graph or ``None``.
        """
        return self._graphs_by_connection_uid.get(int(connection_uid), None)

    def create_connection_graph(
            self,
            connection_uid: int,
            source_port: PortItem,
            destination_port: PortItem,
    ) -> RoutingGraph:
        """
        Create one new routing graph from two Qt ports.

        :param connection_uid: Stable connection identifier.
        :param source_port: Source Qt port item.
        :param destination_port: Destination Qt port item.
        :returns: Created routing graph.
        """
        source_snapshot: QtRoutingPortSnapshot = build_qt_routing_port_snapshot(source_port)
        destination_snapshot: QtRoutingPortSnapshot = build_qt_routing_port_snapshot(destination_port)
        # The session only translates Qt ports into immutable routing inputs.
        # The builder remains the sole component that creates new topology.
        route_builder: RouteBuilder = RouteBuilder(
            source_position=source_snapshot.get_position(),
            destination_position=destination_snapshot.get_position(),
            source_port_side=source_snapshot.get_port_side(),
            destination_port_side=destination_snapshot.get_port_side(),
        )
        routing_graph: RoutingGraph = route_builder.build()
        self._graphs_by_connection_uid[int(connection_uid)] = routing_graph
        return routing_graph

    def ensure_connection_graph(
            self,
            connection_uid: int,
            source_port: PortItem,
            destination_port: PortItem,
    ) -> RoutingGraph:
        """
        Return one existing graph or create it when it does not exist yet.

        :param connection_uid: Stable connection identifier.
        :param source_port: Source Qt port item.
        :param destination_port: Destination Qt port item.
        :returns: Existing or newly created routing graph.
        """
        routing_graph: RoutingGraph | None = self.get_graph(connection_uid)
        if routing_graph is None:
            routing_graph = self.create_connection_graph(
                connection_uid=connection_uid,
                source_port=source_port,
                destination_port=destination_port,
            )
            return routing_graph
        else:
            return routing_graph

    def refresh_connection_graph(
            self,
            connection_uid: int,
            source_port: PortItem,
            destination_port: PortItem,
    ) -> RoutingGraph | None:
        """
        Refresh one connection graph from live Qt port positions.

        :param connection_uid: Stable connection identifier.
        :param source_port: Source Qt port item.
        :param destination_port: Destination Qt port item.
        :returns: Updated routing graph or ``None``.
        """
        routing_graph: RoutingGraph | None = self.get_graph(connection_uid)
        if routing_graph is None:
            return None
        else:
            pass

        source_snapshot: QtRoutingPortSnapshot = build_qt_routing_port_snapshot(source_port)
        destination_snapshot: QtRoutingPortSnapshot = build_qt_routing_port_snapshot(destination_port)
        routing_editor: RoutingEditor = RoutingEditor(routing_graph)
        source_node = routing_graph.get_source_node()
        destination_node = routing_graph.get_destination_node()
        graph_snapshot: RoutingGraph = routing_graph.clone()

        if source_node is None or destination_node is None:
            return None
        else:
            pass

        source_position_changed: bool = (
            source_node.get_position().get_x() != source_snapshot.get_position().get_x()
            or source_node.get_position().get_y() != source_snapshot.get_position().get_y()
        )
        destination_position_changed: bool = (
            destination_node.get_position().get_x() != destination_snapshot.get_position().get_x()
            or destination_node.get_position().get_y() != destination_snapshot.get_position().get_y()
        )

        # A live graph is never replaced. The session only forwards explicit
        # local port updates to the editor when the Qt endpoints actually moved.
        if source_position_changed:
            source_updated: bool = routing_editor.update_port(
                node_id=routing_graph.get_source_node_id(),
                new_position=source_snapshot.get_position(),
            )
            if source_updated:
                pass
            else:
                routing_graph._restore_from(graph_snapshot)
                return None
        else:
            pass

        # Source and destination updates share one snapshot so a failed second
        # update never leaves the graph half-synchronized with the live Qt
        # items. Either both local edits succeed, or the original graph is
        # restored in one step.
        if destination_position_changed:
            destination_updated: bool = routing_editor.update_port(
                node_id=routing_graph.get_destination_node_id(),
                new_position=destination_snapshot.get_position(),
            )
            if destination_updated:
                pass
            else:
                routing_graph._restore_from(graph_snapshot)
                return None
        else:
            pass

        return routing_graph

    def synchronize_connection_graph(
            self,
            connection_uid: int,
            source_port: PortItem,
            destination_port: PortItem,
    ) -> RoutingGraph:
        """
        Ensure that one connection graph exists and is synchronized with live ports.

        :param connection_uid: Stable connection identifier.
        :param source_port: Source Qt port item.
        :param destination_port: Destination Qt port item.
        :returns: Synchronized routing graph.
        """
        routing_graph: RoutingGraph = self.ensure_connection_graph(
            connection_uid=connection_uid,
            source_port=source_port,
            destination_port=destination_port,
        )
        refreshed_graph: RoutingGraph | None = self.refresh_connection_graph(
            connection_uid=connection_uid,
            source_port=source_port,
            destination_port=destination_port,
        )
        if refreshed_graph is None:
            return routing_graph
        else:
            return refreshed_graph

    def move_segment(self, connection_uid: int, segment_id: int, coordinate_offset: float) -> bool:
        """
        Move one segment in one registered graph.

        :param connection_uid: Stable connection identifier.
        :param segment_id: Segment identifier.
        :param coordinate_offset: Offset along the allowed drag axis.
        :returns: ``True`` when the segment moved.
        """
        routing_graph: RoutingGraph | None = self.get_graph(connection_uid)
        if routing_graph is None:
            return False
        else:
            pass

        routing_editor: RoutingEditor = RoutingEditor(routing_graph)
        moved: bool = routing_editor.move_segment(
            segment_id=segment_id,
            coordinate_offset=coordinate_offset,
        )
        return moved

    def build_connection_path(self, connection_uid: int) -> QPainterPath | None:
        """
        Build one Qt painter path from one registered graph.

        :param connection_uid: Stable connection identifier.
        :returns: Qt painter path or ``None``.
        """
        routing_graph: RoutingGraph | None = self.get_graph(connection_uid)
        if routing_graph is None:
            return None
        else:
            # Rendering remains outside the engine. The session only asks the
            # adapter to derive one painter path from the current graph state.
            painter_path: QPainterPath = self._adapter.build_path(routing_graph)
            return painter_path

    def get_segment_path_points(self, connection_uid: int, segment_id: int) -> tuple[object, object] | None:
        """
        Return the Qt endpoints of one segment in one registered graph.

        :param connection_uid: Stable connection identifier.
        :param segment_id: Segment identifier.
        :returns: Segment endpoints or ``None``.
        """
        routing_graph: RoutingGraph | None = self.get_graph(connection_uid)
        if routing_graph is None:
            return None
        else:
            return self._adapter.get_segment_path_points(routing_graph, segment_id)

    def get_ordered_segments(self, connection_uid: int) -> list[RoutingSegment]:
        """
        Return the path segments of one registered graph in deterministic order.

        :param connection_uid: Stable connection identifier.
        :returns: Ordered path segments.
        """
        routing_graph: RoutingGraph | None = self.get_graph(connection_uid)
        if routing_graph is None:
            return list()
        else:
            return routing_graph.get_ordered_segments()

    def export_connection_payload(self, connection_uid: int) -> dict[str, object] | None:
        """
        Export one registered graph to one plain persistence payload.

        :param connection_uid: Stable connection identifier.
        :returns: Plain persistence payload or ``None``.
        """
        routing_graph: RoutingGraph | None = self.get_graph(connection_uid)
        if routing_graph is None:
            return None
        else:
            pass

        serialized_graph: RoutingSerializedGraph = self._serializer.encode_graph(routing_graph)
        payload: dict[str, object] = serialized_graph.to_data()
        return payload

    def import_connection_payload(self, connection_uid: int, payload: dict[str, object]) -> bool:
        """
        Import one plain persistence payload as one registered graph.

        :param connection_uid: Stable connection identifier.
        :param payload: Plain persistence payload.
        :returns: ``True`` when the payload was imported.
        """
        serialized_graph: RoutingSerializedGraph | None = self._serializer.build_serialized_graph_from_data(payload)
        if serialized_graph is None:
            return False
        else:
            pass

        # Import replaces the session entry with the exact graph described by
        # the payload. No Qt item contributes geometry during deserialization.
        routing_graph: RoutingGraph = self._serializer.decode_graph(serialized_graph)
        self._graphs_by_connection_uid[int(connection_uid)] = routing_graph
        return True
