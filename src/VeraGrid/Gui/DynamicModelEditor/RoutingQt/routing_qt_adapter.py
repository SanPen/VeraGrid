# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainterPath

from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingNode
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingSegment
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_geometry import RoutingGeometry
from VeraGrid.Gui.DynamicModelEditor.Routing.routing_graph import RoutingGraph
from VeraGridEngine.enumerations import RoutingAxis


class QtRoutingGraphAdapter:
    """
    Adapt one Qt-independent routing graph to Qt drawing primitives.

    :returns: None.
    """

    __slots__ = tuple()

    def build_path(self, routing_graph: RoutingGraph) -> QPainterPath:
        """
        Build one Qt painter path from one routing graph.

        :param routing_graph: Routing graph to render.
        :returns: Qt painter path.
        """
        painter_path: QPainterPath = QPainterPath()
        ordered_nodes: list[RoutingNode] = routing_graph.get_ordered_nodes()
        if len(ordered_nodes) == 0:
            return painter_path
        else:
            pass

        first_node: RoutingNode = ordered_nodes[0]
        routing_geometry: RoutingGeometry = routing_graph.get_geometry()
        current_point: QPointF = QPointF(
            first_node.get_position().get_x(),
            first_node.get_position().get_y(),
        )
        painter_path.moveTo(current_point)

        route_node: RoutingNode
        for route_node in ordered_nodes[1:]:
            target_point: QPointF = QPointF(
                route_node.get_position().get_x(),
                route_node.get_position().get_y(),
            )
            rendered_target_point: QPointF = self._build_rendered_target_point(
                routing_geometry=routing_geometry,
                current_point=current_point,
                target_point=target_point,
            )
            painter_path.lineTo(rendered_target_point)
            current_point = QPointF(rendered_target_point)
        return painter_path

    def get_segment_path_points(self, routing_graph: RoutingGraph, segment_id: int) -> tuple[QPointF, QPointF] | None:
        """
        Return the Qt endpoints of one graph segment.

        :param routing_graph: Routing graph to inspect.
        :param segment_id: Segment identifier.
        :returns: Segment endpoints or ``None``.
        """
        route_segment: RoutingSegment | None = routing_graph.get_segment(segment_id)
        if route_segment is None:
            return None
        else:
            pass

        start_node: RoutingNode | None = routing_graph.get_node(route_segment.get_start_node_id())
        end_node: RoutingNode | None = routing_graph.get_node(route_segment.get_end_node_id())
        if start_node is None or end_node is None:
            return None
        else:
            pass

        routing_geometry: RoutingGeometry = routing_graph.get_geometry()
        start_point: QPointF = QPointF(
            start_node.get_position().get_x(),
            start_node.get_position().get_y(),
        )
        raw_end_point: QPointF = QPointF(
            end_node.get_position().get_x(),
            end_node.get_position().get_y(),
        )
        segment_axis: RoutingAxis | None = routing_graph.get_segment_axis(segment_id)
        if segment_axis == RoutingAxis.HORIZONTAL:
            end_point: QPointF = QPointF(raw_end_point.x(), start_point.y())
        elif segment_axis == RoutingAxis.VERTICAL:
            end_point = QPointF(start_point.x(), raw_end_point.y())
        else:
            end_point = self._build_rendered_target_point(
                routing_geometry=routing_geometry,
                current_point=start_point,
                target_point=raw_end_point,
            )
        return start_point, end_point

    def _build_rendered_target_point(
            self,
            routing_geometry: RoutingGeometry,
            current_point: QPointF,
            target_point: QPointF,
    ) -> QPointF:
        """
        Build the rendered endpoint of one path step.

        :param routing_geometry: Shared routing geometry helper.
        :param current_point: Current rendered path point.
        :param target_point: Next raw node position.
        :returns: Rendered target point.
        """
        if routing_geometry.are_y_aligned_values(current_point.y(), target_point.y()):
            return QPointF(target_point.x(), current_point.y())
        elif routing_geometry.are_x_aligned_values(current_point.x(), target_point.x()):
            return QPointF(current_point.x(), target_point.y())
        else:
            return QPointF(target_point)
