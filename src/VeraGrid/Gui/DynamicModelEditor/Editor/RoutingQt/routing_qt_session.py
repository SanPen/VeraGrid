# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import QGraphicsScene

from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.route_builder import RouteBuilder
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_editor import RoutingEditor
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_elements import RoutingNode
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_elements import RoutingSegment
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_graph import RoutingGraph
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingConnectionGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingSegmentObstacle
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingSceneGeometrySnapshot
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_serializer import RoutingGraphSerializer
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_serializer import RoutingSerializedGraph
from VeraGrid.Gui.DynamicModelEditor.Editor.RoutingQt.routing_qt_adapter import QtRoutingGraphAdapter
from VeraGrid.Gui.DynamicModelEditor.Editor.RoutingQt.routing_qt_port_snapshot import QtRoutingPortSnapshot
from VeraGrid.Gui.DynamicModelEditor.Editor.RoutingQt.routing_qt_port_snapshot import build_qt_routing_port_snapshot
from VeraGrid.Gui.DynamicModelEditor.Editor.RoutingQt.routing_qt_scene_geometry_adapter import QtRoutingSceneGeometryAdapter
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_editor_graphics import PortItem


class QtRoutingSession:
    """
    Bridge Qt connection gestures with the new routing engine graph model.

    :return: None.
    """

    __slots__ = (
        "_graphs_by_connection_uid",
        "_serializer",
        "_adapter",
        "_scene_geometry_adapter",
        "_drag_graph_snapshots",
        "_drag_connection_uids",
        "_drag_failed_connection_uids",
        "_drag_scene_geometry_snapshot",
        "_drag_finalization_prepared",
    )

    def __init__(self) -> None:
        """
        Build one Qt routing session for the new routing engine.

        :return: None.
        """
        self._graphs_by_connection_uid: dict[int, RoutingGraph] = dict()
        self._serializer: RoutingGraphSerializer = RoutingGraphSerializer()
        self._adapter: QtRoutingGraphAdapter = QtRoutingGraphAdapter()
        self._scene_geometry_adapter: QtRoutingSceneGeometryAdapter = QtRoutingSceneGeometryAdapter()
        self._drag_graph_snapshots: dict[int, RoutingGraph] = dict()
        self._drag_connection_uids: set[int] = set()
        self._drag_failed_connection_uids: set[int] = set()
        self._drag_scene_geometry_snapshot: RoutingSceneGeometrySnapshot | None = None
        self._drag_finalization_prepared: bool = False

    def begin_drag_transaction(self, connection_uids: list[int]) -> None:
        """Capture every committed graph affected by one block drag.

        :param connection_uids: Connection identifiers incident to the block.
        :return: None.
        """
        self._drag_graph_snapshots = dict()
        self._drag_connection_uids = set(connection_uids)
        self._drag_failed_connection_uids = set()
        self._drag_scene_geometry_snapshot = None
        self._drag_finalization_prepared = False

        # Clone each registered graph once so all incident routes share the same
        # transaction boundary even though Qt refreshes them independently.
        connection_uid: int
        for connection_uid in self._drag_connection_uids:
            routing_graph: RoutingGraph | None = self.get_graph(connection_uid=connection_uid)
            if routing_graph is not None:
                self._drag_graph_snapshots[connection_uid] = routing_graph.clone()
            else:
                pass

    def finish_drag_transaction(self, commit_requested: bool = True) -> bool:
        """Commit or roll back every graph participating in the active drag.

        :param commit_requested: Whether the caller completed the drag normally.
        :return: ``True`` when all route synchronizations succeeded.
        """
        transaction_succeeded: bool = (
            commit_requested
            and len(self._drag_failed_connection_uids) == 0
        )
        if transaction_succeeded:
            pass
        else:
            # Restore graph objects in place so references held by connection
            # items and adapters remain valid after the atomic rollback.
            connection_uid: int
            for connection_uid in self._drag_connection_uids:
                graph_snapshot: RoutingGraph | None = self._drag_graph_snapshots.get(connection_uid, None)
                routing_graph: RoutingGraph | None = self.get_graph(connection_uid=connection_uid)
                if routing_graph is not None and graph_snapshot is not None:
                    routing_graph._restore_from(graph_snapshot)
                elif routing_graph is not None:
                    # A graph created during a failed drag did not exist at the
                    # transaction boundary and must not survive the rollback.
                    self.remove_connection(connection_uid=connection_uid)
                else:
                    pass

        self._drag_graph_snapshots = dict()
        self._drag_connection_uids = set()
        self._drag_failed_connection_uids = set()
        self._drag_scene_geometry_snapshot = None
        self._drag_finalization_prepared = False
        return transaction_succeeded

    def prepare_drag_finalization(self) -> None:
        """Restore committed graphs before the definitive routing calculation.

        Preview routing may freely alter the registered working graphs while a
        block follows the pointer. Final routing must instead start from the
        manual geometry captured at the transaction boundary.

        :return: None.
        """
        connection_uid: int
        for connection_uid in self._drag_connection_uids:
            graph_snapshot: RoutingGraph | None = self._drag_graph_snapshots.get(connection_uid, None)
            routing_graph: RoutingGraph | None = self.get_graph(connection_uid=connection_uid)
            if routing_graph is not None and graph_snapshot is not None:
                routing_graph._restore_from(graph_snapshot)
            elif routing_graph is not None:
                self.remove_connection(connection_uid=connection_uid)
            else:
                pass

        # Only definitive synchronizations performed after this point decide
        # whether the complete drag transaction can commit.
        self._drag_failed_connection_uids = set()
        self._drag_scene_geometry_snapshot = None
        self._drag_finalization_prepared = True

    def preview_connection_graph(
            self,
            connection_uid: int,
            source_port: PortItem,
            destination_port: PortItem,
    ) -> RoutingGraph | None:
        """Update endpoints cheaply while a block follows the mouse pointer.

        The preview deliberately omits scene geometry, automatic obstacle
        search and persistence. The transaction snapshot remains the committed
        source used by the definitive refresh after mouse release.

        :param connection_uid: Stable connection identifier.
        :param source_port: Live source endpoint.
        :param destination_port: Live destination endpoint.
        :return: Preview graph, or ``None`` when no simple route can be built.
        """
        source_snapshot: QtRoutingPortSnapshot = build_qt_routing_port_snapshot(source_port)
        destination_snapshot: QtRoutingPortSnapshot = build_qt_routing_port_snapshot(destination_port)
        routing_graph: RoutingGraph | None = self.get_graph(connection_uid=connection_uid)

        if routing_graph is None:
            route_builder: RouteBuilder = RouteBuilder(
                source_position=source_snapshot.get_position(),
                destination_position=destination_snapshot.get_position(),
                source_port_side=source_snapshot.get_port_side(),
                destination_port_side=destination_snapshot.get_port_side(),
                connection_geometry=None,
            )
            try:
                routing_graph = route_builder.build()
            except ValueError:
                return None
            else:
                self._graphs_by_connection_uid[int(connection_uid)] = routing_graph
        else:
            pass

        preview_snapshot: RoutingGraph = routing_graph.clone()
        routing_editor: RoutingEditor = RoutingEditor(
            graph=routing_graph,
            connection_geometry=None,
        )
        source_node: RoutingNode | None = routing_graph.get_source_node()
        destination_node: RoutingNode | None = routing_graph.get_destination_node()
        if source_node is None or destination_node is None:
            return None
        else:
            pass

        source_changed: bool = (
            source_node.get_position().get_x() != source_snapshot.get_position().get_x()
            or source_node.get_position().get_y() != source_snapshot.get_position().get_y()
        )
        destination_changed: bool = (
            destination_node.get_position().get_x() != destination_snapshot.get_position().get_x()
            or destination_node.get_position().get_y() != destination_snapshot.get_position().get_y()
        )
        source_updated: bool = True
        destination_updated: bool = True
        if source_changed:
            source_updated = routing_editor.update_port(
                node_id=routing_graph.get_source_node_id(),
                new_position=source_snapshot.get_position(),
            )
        else:
            pass
        if source_updated and destination_changed:
            destination_updated = routing_editor.update_port(
                node_id=routing_graph.get_destination_node_id(),
                new_position=destination_snapshot.get_position(),
            )
        else:
            pass

        if source_updated and destination_updated and self._graph_matches_port_snapshots(
                routing_graph=routing_graph,
                source_snapshot=source_snapshot,
                destination_snapshot=destination_snapshot,
        ):
            return routing_graph
        else:
            # A simple deterministic route is a cheap preview fallback when the
            # manual neighbourhood cannot absorb the live endpoint displacement.
            routing_graph._restore_from(preview_snapshot)
            fallback_builder: RouteBuilder = RouteBuilder(
                source_position=source_snapshot.get_position(),
                destination_position=destination_snapshot.get_position(),
                source_port_side=source_snapshot.get_port_side(),
                destination_port_side=destination_snapshot.get_port_side(),
                connection_geometry=None,
            )
            try:
                fallback_graph: RoutingGraph = fallback_builder.build()
            except ValueError:
                return None
            else:
                routing_graph._restore_from(fallback_graph)
                return routing_graph

    def _record_drag_synchronization(self, connection_uid: int, synchronized: bool) -> None:
        """Record one incident connection result in the active transaction.

        :param connection_uid: Connection whose synchronization completed.
        :param synchronized: Whether the connection reached the live endpoints.
        :return: None.
        """
        connection_identifier: int = int(connection_uid)
        if connection_identifier in self._drag_connection_uids and not synchronized:
            self._drag_failed_connection_uids.add(connection_identifier)
        elif connection_identifier in self._drag_failed_connection_uids:
            # The final refresh of a connection supersedes a transient failure
            # observed at an intermediate mouse position.
            self._drag_failed_connection_uids.remove(connection_identifier)
        else:
            pass

    def has_connection(self, connection_uid: int) -> bool:
        """
        Return whether one connection graph is registered.

        :param connection_uid: Stable connection identifier.
        :return: ``True`` when the graph exists in the session.
        """
        if int(connection_uid) in self._graphs_by_connection_uid:
            return True
        else:
            return False

    def remove_connection(self, connection_uid: int) -> bool:
        """
        Remove one connection graph from the session.

        :param connection_uid: Stable connection identifier.
        :return: ``True`` when the graph existed and was removed.
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
        :return: Registered routing graph or ``None``.
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
        :return: Created routing graph.
        """
        source_snapshot: QtRoutingPortSnapshot = build_qt_routing_port_snapshot(source_port)
        destination_snapshot: QtRoutingPortSnapshot = build_qt_routing_port_snapshot(destination_port)
        connection_geometry: RoutingConnectionGeometry = self._capture_connection_geometry(
            connection_uid=connection_uid,
            source_port=source_port,
            destination_port=destination_port,
        )
        # The session only translates Qt ports into immutable routing inputs.
        # The builder remains the sole component that creates new topology.
        route_builder: RouteBuilder = RouteBuilder(
            source_position=source_snapshot.get_position(),
            destination_position=destination_snapshot.get_position(),
            source_port_side=source_snapshot.get_port_side(),
            destination_port_side=destination_snapshot.get_port_side(),
            connection_geometry=connection_geometry,
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
        :return: Existing or newly created routing graph.
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
        :return: Updated routing graph or ``None``.
        """
        routing_graph: RoutingGraph | None = self.get_graph(connection_uid)
        if routing_graph is None:
            return None
        else:
            pass

        source_snapshot: QtRoutingPortSnapshot = build_qt_routing_port_snapshot(source_port)
        destination_snapshot: QtRoutingPortSnapshot = build_qt_routing_port_snapshot(destination_port)
        connection_geometry: RoutingConnectionGeometry = self._capture_connection_geometry(
            connection_uid=connection_uid,
            source_port=source_port,
            destination_port=destination_port,
        )
        routing_editor: RoutingEditor = RoutingEditor(
            graph=routing_graph,
            connection_geometry=connection_geometry,
        )
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
                return self._rebuild_connection_graph_for_ports(
                    routing_graph=routing_graph,
                    source_snapshot=source_snapshot,
                    destination_snapshot=destination_snapshot,
                    connection_geometry=connection_geometry,
                )
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
                return self._rebuild_connection_graph_for_ports(
                    routing_graph=routing_graph,
                    source_snapshot=source_snapshot,
                    destination_snapshot=destination_snapshot,
                    connection_geometry=connection_geometry,
                )
        else:
            pass

        if self._graph_matches_port_snapshots(
                routing_graph=routing_graph,
                source_snapshot=source_snapshot,
                destination_snapshot=destination_snapshot,
        ):
            return routing_graph
        else:
            routing_graph._restore_from(graph_snapshot)
            return self._rebuild_connection_graph_for_ports(
                routing_graph=routing_graph,
                source_snapshot=source_snapshot,
                destination_snapshot=destination_snapshot,
                connection_geometry=connection_geometry,
            )

    def _rebuild_connection_graph_for_ports(
            self,
            routing_graph: RoutingGraph,
            source_snapshot: QtRoutingPortSnapshot,
            destination_snapshot: QtRoutingPortSnapshot,
            connection_geometry: RoutingConnectionGeometry,
    ) -> RoutingGraph | None:
        """
        Rebuild one complete route after incremental endpoint repair fails.

        The existing graph object remains registered and is replaced only after
        the detached builder returns a fully validated route. This preserves
        references held by the Qt session while preventing an old endpoint
        position from being rendered against a block that has already moved.

        :param routing_graph: Registered live graph to replace after success.
        :param source_snapshot: Current source port snapshot.
        :param destination_snapshot: Current destination port snapshot.
        :param connection_geometry: Current block and connection obstacles.
        :return: Rebuilt registered graph or ``None`` when no route exists.
        """
        route_builder: RouteBuilder = RouteBuilder(
            source_position=source_snapshot.get_position(),
            destination_position=destination_snapshot.get_position(),
            source_port_side=source_snapshot.get_port_side(),
            destination_port_side=destination_snapshot.get_port_side(),
            connection_geometry=connection_geometry,
        )
        try:
            rebuilt_graph: RoutingGraph = route_builder.build()
        except ValueError:
            return None
        else:
            if self._graph_matches_port_snapshots(
                    routing_graph=rebuilt_graph,
                    source_snapshot=source_snapshot,
                    destination_snapshot=destination_snapshot,
            ):
                routing_graph._restore_from(rebuilt_graph)
                return routing_graph
            else:
                return None

    def _graph_matches_port_snapshots(
            self,
            routing_graph: RoutingGraph,
            source_snapshot: QtRoutingPortSnapshot,
            destination_snapshot: QtRoutingPortSnapshot,
    ) -> bool:
        """
        Return whether graph endpoints exactly represent both live Qt ports.

        :param routing_graph: Candidate synchronized graph.
        :param source_snapshot: Current source Qt port snapshot.
        :param destination_snapshot: Current destination Qt port snapshot.
        :return: ``True`` when positions and physical sides match.
        """
        source_node: RoutingNode | None = routing_graph.get_source_node()
        destination_node: RoutingNode | None = routing_graph.get_destination_node()
        if source_node is None or destination_node is None:
            return False
        else:
            pass

        source_position_matches: bool = (
            source_node.get_position().get_x() == source_snapshot.get_position().get_x()
            and source_node.get_position().get_y() == source_snapshot.get_position().get_y()
        )
        destination_position_matches: bool = (
            destination_node.get_position().get_x() == destination_snapshot.get_position().get_x()
            and destination_node.get_position().get_y() == destination_snapshot.get_position().get_y()
        )
        source_side_matches: bool = source_node.get_port_side() == source_snapshot.get_port_side()
        destination_side_matches: bool = destination_node.get_port_side() == destination_snapshot.get_port_side()
        if (source_position_matches
                and destination_position_matches
                and source_side_matches
                and destination_side_matches):
            return True
        else:
            return False

    def synchronize_connection_graph(
            self,
            connection_uid: int,
            source_port: PortItem,
            destination_port: PortItem,
    ) -> RoutingGraph | None:
        """
        Ensure that one connection graph exists and is synchronized with live ports.

        :param connection_uid: Stable connection identifier.
        :param source_port: Source Qt port item.
        :param destination_port: Destination Qt port item.
        :return: Synchronized routing graph or ``None`` when rebuilding fails.
        """
        # A failed synchronization is recoverable: the registered graph is the
        # last committed route and must remain available until a replacement is
        # built and validated completely.
        try:
            routing_graph: RoutingGraph = self.ensure_connection_graph(
                connection_uid=connection_uid,
                source_port=source_port,
                destination_port=destination_port,
            )
        except ValueError:
            return None
        else:
            pass
        refreshed_graph: RoutingGraph | None = self.refresh_connection_graph(
            connection_uid=connection_uid,
            source_port=source_port,
            destination_port=destination_port,
        )
        if refreshed_graph is None:
            # Keep the committed graph registered. The caller receives failure
            # and therefore neither renders nor persists a partial candidate.
            self._record_drag_synchronization(
                connection_uid=connection_uid,
                synchronized=False,
            )
            return None
        else:
            self._record_drag_synchronization(
                connection_uid=connection_uid,
                synchronized=True,
            )
            return refreshed_graph

    def move_segment(
            self,
            connection_uid: int,
            segment_id: int,
            coordinate_offset: float,
            source_port: PortItem,
            destination_port: PortItem,
    ) -> bool:
        """
        Move one segment in one registered graph.

        :param connection_uid: Stable connection identifier.
        :param segment_id: Segment identifier.
        :param coordinate_offset: Offset along the allowed drag axis.
        :param source_port: Live source endpoint used to capture current block geometry.
        :param destination_port: Live destination endpoint used to capture current block geometry.
        :return: ``True`` when the segment moved.
        """
        routing_graph: RoutingGraph | None = self.get_graph(connection_uid)
        if routing_graph is None:
            return False
        else:
            pass

        connection_geometry: RoutingConnectionGeometry = self._capture_connection_geometry(
            connection_uid=connection_uid,
            source_port=source_port,
            destination_port=destination_port,
        )
        routing_editor: RoutingEditor = RoutingEditor(
            graph=routing_graph,
            connection_geometry=connection_geometry,
        )
        moved: bool = routing_editor.move_segment(
            segment_id=segment_id,
            coordinate_offset=coordinate_offset,
        )
        return moved

    def _capture_connection_geometry(
            self,
            connection_uid: int,
            source_port: PortItem,
            destination_port: PortItem,
    ) -> RoutingConnectionGeometry:
        """
        Capture one current non-Qt block-geometry snapshot for an operation.

        :param connection_uid: Connection whose own graph must be excluded.
        :param source_port: Live source endpoint.
        :param destination_port: Live destination endpoint.
        :return: Immutable connection geometry snapshot.
        """
        source_scene: QGraphicsScene | None = source_port.scene()
        if self._drag_finalization_prepared:
            if self._drag_scene_geometry_snapshot is None:
                # Capture Qt blocks and all committed routing segments once.
                # Later connections only reclassify this immutable snapshot.
                all_connection_segments: tuple[
                    RoutingSegmentObstacle, ...
                ] = self._capture_all_connection_segments()
                self._drag_scene_geometry_snapshot = self._scene_geometry_adapter.capture_scene_geometry(
                    scene=source_scene,
                    connection_segments=all_connection_segments,
                )
            else:
                pass
            return self._scene_geometry_adapter.build_connection_geometry_from_snapshot(
                snapshot=self._drag_scene_geometry_snapshot,
                source_port=source_port,
                destination_port=destination_port,
                connection_uid=connection_uid,
            )
        else:
            other_connection_segments: tuple[
                RoutingSegmentObstacle, ...
            ] = self._capture_other_connection_segments(
                connection_uid=connection_uid,
            )
            connection_geometry: RoutingConnectionGeometry = (
                self._scene_geometry_adapter.capture_connection_geometry(
                    scene=source_scene,
                    source_port=source_port,
                    destination_port=destination_port,
                    other_connection_segments=other_connection_segments,
                )
            )
            return connection_geometry

    def _capture_all_connection_segments(self) -> tuple[RoutingSegmentObstacle, ...]:
        """Capture every registered route segment for one shared scene snapshot.

        :return: Immutable point-in-time sequence of all connection segments.
        """
        obstacle_segments: list[RoutingSegmentObstacle] = list()
        connection_uid: int
        routing_graph: RoutingGraph
        for connection_uid, routing_graph in self._graphs_by_connection_uid.items():
            route_segment: RoutingSegment
            for route_segment in routing_graph.get_segments():
                start_node: RoutingNode | None = routing_graph.get_node(route_segment.get_start_node_id())
                end_node: RoutingNode | None = routing_graph.get_node(route_segment.get_end_node_id())
                if start_node is not None and end_node is not None:
                    obstacle_segments.append(
                        RoutingSegmentObstacle(
                            connection_uid=connection_uid,
                            segment_id=route_segment.get_segment_id(),
                            start_position=start_node.get_position(),
                            end_position=end_node.get_position(),
                        )
                    )
                else:
                    pass
        return tuple(obstacle_segments)

    def _capture_other_connection_segments(
            self,
            connection_uid: int,
    ) -> tuple[RoutingSegmentObstacle, ...]:
        """
        Capture segments from every registered graph except the active one.

        Routing graphs remain the source of truth. Painter paths are never
        inspected, and the active connection is excluded as one complete graph
        so its adjacent segments cannot be mistaken for external crossings.

        :param connection_uid: Active connection identifier to exclude.
        :return: Immutable point-in-time sequence of foreign route segments.
        """
        active_connection_uid: int = int(connection_uid)
        obstacle_segments: list[RoutingSegmentObstacle] = list()
        other_connection_uid: int
        other_graph: RoutingGraph

        for other_connection_uid, other_graph in self._graphs_by_connection_uid.items():
            if other_connection_uid == active_connection_uid:
                pass
            else:
                route_segment: RoutingSegment
                for route_segment in other_graph.get_segments():
                    start_node: RoutingNode | None = other_graph.get_node(route_segment.get_start_node_id())
                    end_node: RoutingNode | None = other_graph.get_node(route_segment.get_end_node_id())
                    if start_node is None or end_node is None:
                        pass
                    else:
                        obstacle_segment: RoutingSegmentObstacle = RoutingSegmentObstacle(
                            connection_uid=other_connection_uid,
                            segment_id=route_segment.get_segment_id(),
                            start_position=start_node.get_position(),
                            end_position=end_node.get_position(),
                        )
                        obstacle_segments.append(obstacle_segment)

        return tuple(obstacle_segments)

    def build_connection_path(self, connection_uid: int) -> QPainterPath | None:
        """
        Build one Qt painter path from one registered graph.

        :param connection_uid: Stable connection identifier.
        :return: Qt painter path or ``None``.
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
        :return: Segment endpoints or ``None``.
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
        :return: Ordered path segments.
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
        :return: Plain persistence payload or ``None``.
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
        :return: ``True`` when the payload was imported.
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
