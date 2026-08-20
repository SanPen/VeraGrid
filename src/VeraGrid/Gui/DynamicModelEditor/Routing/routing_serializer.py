# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingNode
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingPoint
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingSegment
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_graph import RoutingGraph
from VeraGridEngine.enumerations import RoutingNodeKind, RoutingPortSide


class RoutingSerializedNode:
    """
    Store one serialized routing node record.

    :return: None.
    """

    __slots__ = ("_node_id", "_kind", "_x_pos", "_y_pos", "_port_side")

    def __init__(
            self,
            node_id: int,
            kind: RoutingNodeKind,
            x_pos: float,
            y_pos: float,
            port_side: RoutingPortSide | None,
    ) -> None:
        """
        Build one serialized node record.

        :param node_id: Stable node identifier.
        :param kind: Node kind.
        :param x_pos: Horizontal coordinate.
        :param y_pos: Vertical coordinate.
        :param port_side: Physical block side for port nodes.
        :return: None.
        """
        self._node_id: int = int(node_id)
        self._kind: RoutingNodeKind = kind
        self._x_pos: float = float(x_pos)
        self._y_pos: float = float(y_pos)
        self._port_side: RoutingPortSide | None = port_side

    def get_node_id(self) -> int:
        """
        :return: Node identifier.
        """
        return self._node_id

    def get_kind(self) -> RoutingNodeKind:
        """
        :return: Node kind.
        """
        return self._kind

    def get_x(self) -> float:
        """
        :return: Horizontal coordinate.
        """
        return self._x_pos

    def get_y(self) -> float:
        """
        :return: Vertical coordinate.
        """
        return self._y_pos

    def has_port_side(self) -> bool:
        """
        Return whether this serialized node stores one physical port side.

        :return: ``True`` when a physical port side exists.
        """
        if self._port_side is None:
            return False
        else:
            return True

    def get_port_side(self) -> RoutingPortSide | None:
        """
        Return the stored physical port side.

        :return: Physical port side or ``None``.
        """
        return self._port_side

    def to_data(self) -> dict[str, object]:
        """
        Convert the serialized node record to one plain persistence payload.

        :return: Plain node payload.
        """
        payload: dict[str, object] = dict()
        payload["node_id"] = self._node_id
        payload["kind"] = self._kind.value
        payload["x"] = self._x_pos
        payload["y"] = self._y_pos
        if self._port_side is None:
            pass
        else:
            payload["port_side"] = self._port_side.value
        return payload


class RoutingSerializedSegment:
    """
    Store one serialized routing segment record.

    :return: None.
    """

    __slots__ = ("_segment_id", "_start_node_id", "_end_node_id")

    def __init__(self, segment_id: int, start_node_id: int, end_node_id: int) -> None:
        """
        Build one serialized segment record.

        :param segment_id: Stable segment identifier.
        :param start_node_id: Start node identifier.
        :param end_node_id: End node identifier.
        :return: None.
        """
        self._segment_id: int = int(segment_id)
        self._start_node_id: int = int(start_node_id)
        self._end_node_id: int = int(end_node_id)

    def get_segment_id(self) -> int:
        """
        :return: Segment identifier.
        """
        return self._segment_id

    def get_start_node_id(self) -> int:
        """
        :return: Start node identifier.
        """
        return self._start_node_id

    def get_end_node_id(self) -> int:
        """
        :return: End node identifier.
        """
        return self._end_node_id

    def to_data(self) -> dict[str, object]:
        """
        Convert the serialized segment record to one plain persistence payload.

        :return: Plain segment payload.
        """
        payload: dict[str, object] = dict()
        payload["segment_id"] = self._segment_id
        payload["start_node_id"] = self._start_node_id
        payload["end_node_id"] = self._end_node_id
        return payload


class RoutingSerializedGraph:
    """
    Store one serialized routing graph payload.

    :return: None.
    """

    __slots__ = ("_source_node_id", "_destination_node_id", "_nodes", "_segments")

    def __init__(
            self,
            source_node_id: int,
            destination_node_id: int,
            nodes: list[RoutingSerializedNode],
            segments: list[RoutingSerializedSegment],
    ) -> None:
        """
        Build one serialized graph payload.

        :param source_node_id: Source port node identifier.
        :param destination_node_id: Destination port node identifier.
        :param nodes: Serialized node records.
        :param segments: Serialized segment records.
        :return: None.
        """
        self._source_node_id: int = int(source_node_id)
        self._destination_node_id: int = int(destination_node_id)
        self._nodes: list[RoutingSerializedNode] = list(nodes)
        self._segments: list[RoutingSerializedSegment] = list(segments)

    def get_source_node_id(self) -> int:
        """
        :return: Source node identifier.
        """
        return self._source_node_id

    def get_destination_node_id(self) -> int:
        """
        :return: Destination node identifier.
        """
        return self._destination_node_id

    def get_nodes(self) -> list[RoutingSerializedNode]:
        """
        :return: Serialized node records.
        """
        return list(self._nodes)

    def get_segments(self) -> list[RoutingSerializedSegment]:
        """
        :return: Serialized segment records.
        """
        return list(self._segments)

    def to_data(self) -> dict[str, object]:
        """
        Convert the serialized graph to one plain persistence payload.

        :return: Plain graph payload.
        """
        node_payloads: list[dict[str, object]] = list()
        segment_payloads: list[dict[str, object]] = list()

        node_record: RoutingSerializedNode
        for node_record in self._nodes:
            node_payloads.append(node_record.to_data())

        segment_record: RoutingSerializedSegment
        for segment_record in self._segments:
            segment_payloads.append(segment_record.to_data())

        payload: dict[str, object] = dict()
        payload["source_node_id"] = self._source_node_id
        payload["destination_node_id"] = self._destination_node_id
        payload["nodes"] = node_payloads
        payload["segments"] = segment_payloads
        return payload


class RoutingGraphSerializer:
    """
    Encode and decode one routing graph as one persistence payload.

    :return: None.
    """

    __slots__ = tuple()

    def encode_graph(self, routing_graph: RoutingGraph) -> RoutingSerializedGraph:
        """
        Encode one routing graph.

        :param routing_graph: Graph to encode.
        :return: Serialized graph payload.
        """
        node_records: list[RoutingSerializedNode] = list()
        segment_records: list[RoutingSerializedSegment] = list()

        route_node: RoutingNode
        for route_node in routing_graph.get_ordered_nodes():
            node_records.append(
                RoutingSerializedNode(
                    node_id=route_node.get_node_id(),
                    kind=route_node.get_kind(),
                    x_pos=route_node.get_position().get_x(),
                    y_pos=route_node.get_position().get_y(),
                    port_side=route_node.get_port_side(),
                )
            )

        route_segment: RoutingSegment
        for route_segment in routing_graph.get_ordered_segments():
            segment_records.append(
                RoutingSerializedSegment(
                    segment_id=route_segment.get_segment_id(),
                    start_node_id=route_segment.get_start_node_id(),
                    end_node_id=route_segment.get_end_node_id(),
                )
            )

        serialized_graph: RoutingSerializedGraph = RoutingSerializedGraph(
            source_node_id=routing_graph.get_source_node_id(),
            destination_node_id=routing_graph.get_destination_node_id(),
            nodes=node_records,
            segments=segment_records,
        )
        return serialized_graph

    def decode_graph(self, serialized_graph: RoutingSerializedGraph) -> RoutingGraph:
        """
        Decode one serialized graph payload.

        :param serialized_graph: Serialized graph payload.
        :return: Decoded routing graph.
        """
        routing_graph: RoutingGraph = RoutingGraph(
            source_node_id=serialized_graph.get_source_node_id(),
            destination_node_id=serialized_graph.get_destination_node_id(),
        )

        node_record: RoutingSerializedNode
        for node_record in serialized_graph.get_nodes():
            routing_graph._add_node(
                RoutingNode(
                    node_id=node_record.get_node_id(),
                    kind=node_record.get_kind(),
                    position=RoutingPoint(
                        x_pos=node_record.get_x(),
                        y_pos=node_record.get_y(),
                    ),
                    port_side=node_record.get_port_side(),
                )
            )

        segment_record: RoutingSerializedSegment
        for segment_record in serialized_graph.get_segments():
            routing_graph._add_segment(
                RoutingSegment(
                    segment_id=segment_record.get_segment_id(),
                    start_node_id=segment_record.get_start_node_id(),
                    end_node_id=segment_record.get_end_node_id(),
                )
            )

        return routing_graph

    def build_serialized_graph_from_data(self, data: dict[str, object]) -> RoutingSerializedGraph | None:
        """
        Build one serialized graph payload object from one plain persistence mapping.

        :param data: Plain persistence mapping.
        :return: Serialized graph payload or ``None`` when the payload is malformed.
        """
        source_node_value: object | None = data.get("source_node_id", None)
        destination_node_value: object | None = data.get("destination_node_id", None)
        node_payload_value: object | None = data.get("nodes", None)
        segment_payload_value: object | None = data.get("segments", None)

        if isinstance(source_node_value, int):
            pass
        else:
            return None
        if isinstance(destination_node_value, int):
            pass
        else:
            return None
        if isinstance(node_payload_value, list):
            pass
        else:
            return None
        if isinstance(segment_payload_value, list):
            pass
        else:
            return None

        node_records: list[RoutingSerializedNode] = list()
        segment_records: list[RoutingSerializedSegment] = list()

        node_payload: object
        for node_payload in node_payload_value:
            if isinstance(node_payload, dict):
                pass
            else:
                return None

            node_id_value: object | None = node_payload.get("node_id", None)
            kind_value: object | None = node_payload.get("kind", None)
            x_value: object | None = node_payload.get("x", None)
            y_value: object | None = node_payload.get("y", None)
            port_side_value: object | None = node_payload.get("port_side", None)

            if isinstance(node_id_value, int):
                pass
            else:
                return None
            if isinstance(kind_value, str):
                pass
            else:
                return None
            if isinstance(x_value, int) or isinstance(x_value, float):
                pass
            else:
                return None
            if isinstance(y_value, int) or isinstance(y_value, float):
                pass
            else:
                return None
            if isinstance(port_side_value, str) or port_side_value is None:
                pass
            else:
                return None

            node_kind: RoutingNodeKind | None = self._build_node_kind(kind_value)
            if node_kind is None:
                return None
            else:
                pass

            node_port_side: RoutingPortSide | None = self._build_port_side(port_side_value)
            if port_side_value is None:
                pass
            elif node_port_side is None:
                return None
            else:
                pass

            node_records.append(
                RoutingSerializedNode(
                    node_id=node_id_value,
                    kind=node_kind,
                    x_pos=float(x_value),
                    y_pos=float(y_value),
                    port_side=node_port_side,
                )
            )

        segment_payload: object
        for segment_payload in segment_payload_value:
            if isinstance(segment_payload, dict):
                pass
            else:
                return None

            segment_id_value: object | None = segment_payload.get("segment_id", None)
            start_node_value: object | None = segment_payload.get("start_node_id", None)
            end_node_value: object | None = segment_payload.get("end_node_id", None)
            if isinstance(segment_id_value, int):
                pass
            else:
                return None
            if isinstance(start_node_value, int):
                pass
            else:
                return None
            if isinstance(end_node_value, int):
                pass
            else:
                return None

            segment_records.append(
                RoutingSerializedSegment(
                    segment_id=segment_id_value,
                    start_node_id=start_node_value,
                    end_node_id=end_node_value,
                )
            )

        serialized_graph: RoutingSerializedGraph = RoutingSerializedGraph(
            source_node_id=source_node_value,
            destination_node_id=destination_node_value,
            nodes=node_records,
            segments=segment_records,
        )
        return serialized_graph

    def _build_node_kind(self, raw_kind: str) -> RoutingNodeKind | None:
        """
        Convert one raw node-kind string to one enum member.

        :param raw_kind: Raw node-kind string.
        :return: Node-kind enum member or ``None``.
        """
        if raw_kind == RoutingNodeKind.PORT.value:
            return RoutingNodeKind.PORT
        elif raw_kind == RoutingNodeKind.STUB.value:
            return RoutingNodeKind.STUB
        elif raw_kind == RoutingNodeKind.ELBOW.value:
            return RoutingNodeKind.ELBOW
        else:
            return None

    def _build_port_side(self, raw_port_side: str | None) -> RoutingPortSide | None:
        """
        Convert one raw port-side string to one enum member.

        :param raw_port_side: Raw port-side string or ``None``.
        :return: Port-side enum member or ``None``.
        """
        if raw_port_side == RoutingPortSide.LEFT.value:
            return RoutingPortSide.LEFT
        elif raw_port_side == RoutingPortSide.RIGHT.value:
            return RoutingPortSide.RIGHT
        elif raw_port_side == RoutingPortSide.TOP.value:
            return RoutingPortSide.TOP
        elif raw_port_side == RoutingPortSide.BOTTOM.value:
            return RoutingPortSide.BOTTOM
        else:
            return None
