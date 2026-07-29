# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from VeraGridEngine.Utils.SugiyamaLayered.model import (
    SugiyamaEdge,
    SugiyamaEdgeSection,
    SugiyamaLabel,
    SugiyamaNode,
    SugiyamaPort,
)
from VeraGridEngine.Utils.SugiyamaLayered.options import LayoutDirection, PortSide, coerce_enum_value
from VeraGridEngine.Utils.SugiyamaLayered.pipeline import LayoutContext, LayoutPhaseBase


def _section_path_points(section: SugiyamaEdgeSection) -> list[tuple[float, float]]:
    """Return all explicit points of one routed edge section.

    :param section: Edge section to inspect.
    :returns: Ordered list of start, bend and end points.
    """
    points: list[tuple[float, float]] = list()

    if section.start_point is not None:
        points.append(section.start_point)
    else:
        points = points

    points.extend(section.bend_points)

    if section.end_point is not None:
        points.append(section.end_point)
    else:
        points = points

    return points


def _polyline_midpoint(points: list[tuple[float, float]]) -> tuple[float, float] | None:
    """Return the midpoint along a polyline.

    :param points: Ordered polyline points.
    :returns: Midpoint on the polyline or ``None`` when empty.
    """
    midpoint: tuple[float, float] | None = None

    if points:
        if len(points) == 1:
            midpoint = points[0]
        else:
            segment_lengths: list[float] = list()
            total_length: float = 0.0
            segment_index: int

            # The edge-label placement needs an arc-length midpoint instead of the
            # geometric center so labels remain stable on routed orthogonal polylines.
            for segment_index in range(len(points) - 1):
                x_start: float
                y_start: float
                x_end: float
                y_end: float
                x_start, y_start = points[segment_index]
                x_end, y_end = points[segment_index + 1]
                segment_length: float = abs(x_end - x_start) + abs(y_end - y_start)
                segment_lengths.append(segment_length)
                total_length += segment_length

            if total_length <= 0.0:
                midpoint = points[len(points) // 2]
            else:
                halfway: float = total_length / 2.0
                walked_length: float = 0.0

                for segment_index, segment_length in enumerate(segment_lengths):
                    if walked_length + segment_length >= halfway and segment_length > 0.0:
                        x_start, y_start = points[segment_index]
                        x_end, y_end = points[segment_index + 1]
                        ratio: float = (halfway - walked_length) / segment_length
                        midpoint = (
                            x_start + (x_end - x_start) * ratio,
                            y_start + (y_end - y_start) * ratio,
                        )
                        break
                    else:
                        walked_length += segment_length

                if midpoint is None:
                    midpoint = points[-1]
                else:
                    midpoint = midpoint
    else:
        midpoint = None

    return midpoint


def _longest_segment_midpoint(points: list[tuple[float, float]]) -> tuple[float, float] | None:
    """Return the midpoint of the longest segment in a polyline.

    :param points: Ordered polyline points.
    :returns: Midpoint of the longest segment or a polyline midpoint fallback.
    """
    midpoint: tuple[float, float] | None = None

    if len(points) >= 2:
        best_length: float = -1.0
        segment_index: int

        # Using the longest segment tends to place labels on the visually dominant
        # part of the edge, which is more stable than using short dogleg segments.
        for segment_index in range(len(points) - 1):
            x_start: float
            y_start: float
            x_end: float
            y_end: float
            x_start, y_start = points[segment_index]
            x_end, y_end = points[segment_index + 1]
            segment_length: float = abs(x_end - x_start) + abs(y_end - y_start)

            if segment_length > best_length:
                best_length = segment_length
                midpoint = ((x_start + x_end) / 2.0, (y_start + y_end) / 2.0)
            else:
                best_length = best_length
    else:
        midpoint = _polyline_midpoint(points)

    return midpoint


def _update_bounds_with_rectangle(
    left: float | None,
    top: float | None,
    right: float | None,
    bottom: float | None,
    rectangle_left: float,
    rectangle_top: float,
    rectangle_right: float,
    rectangle_bottom: float,
) -> tuple[float, float, float, float]:
    """Expand bounds to include one rectangle.

    :param left: Current left bound.
    :param top: Current top bound.
    :param right: Current right bound.
    :param bottom: Current bottom bound.
    :param rectangle_left: Rectangle left coordinate.
    :param rectangle_top: Rectangle top coordinate.
    :param rectangle_right: Rectangle right coordinate.
    :param rectangle_bottom: Rectangle bottom coordinate.
    :returns: Updated finite bounds.
    """
    resolved_left: float = rectangle_left if left is None else min(left, rectangle_left)
    resolved_top: float = rectangle_top if top is None else min(top, rectangle_top)
    resolved_right: float = rectangle_right if right is None else max(right, rectangle_right)
    resolved_bottom: float = rectangle_bottom if bottom is None else max(bottom, rectangle_bottom)
    return resolved_left, resolved_top, resolved_right, resolved_bottom


def _update_bounds_with_label(
    left: float | None,
    top: float | None,
    right: float | None,
    bottom: float | None,
    label: SugiyamaLabel,
) -> tuple[float | None, float | None, float | None, float | None]:
    """Expand bounds to include one positioned label.

    :param left: Current left bound.
    :param top: Current top bound.
    :param right: Current right bound.
    :param bottom: Current bottom bound.
    :param label: Label to include.
    :returns: Updated bounds.
    """
    updated_left: float | None = left
    updated_top: float | None = top
    updated_right: float | None = right
    updated_bottom: float | None = bottom

    if label.x is not None and label.y is not None:
        updated_left, updated_top, updated_right, updated_bottom = _update_bounds_with_rectangle(
            left,
            top,
            right,
            bottom,
            label.x,
            label.y,
            label.x + label.width,
            label.y + label.height,
        )
    else:
        updated_left = updated_left

    return updated_left, updated_top, updated_right, updated_bottom


def _graph_bounds(context: LayoutContext) -> tuple[float, float, float, float] | None:
    """Return the overall bounds of the laid out graph.

    :param context: Shared pipeline context.
    :returns: Graph bounds or ``None`` when no positioned geometry exists.
    """
    left: float | None = None
    top: float | None = None
    right: float | None = None
    bottom: float | None = None
    node: SugiyamaNode

    # The final layout needs normalization to positive coordinates, so the phase
    # measures all node, port, edge and label geometry before applying the shift.
    for node in context.graph.all_nodes():
        if node.x is not None and node.y is not None:
            left, top, right, bottom = _update_bounds_with_rectangle(
                left,
                top,
                right,
                bottom,
                node.x,
                node.y,
                node.x + node.width,
                node.y + node.height,
            )
        else:
            left = left

        label: SugiyamaLabel
        for label in node.labels:
            left, top, right, bottom = _update_bounds_with_label(left, top, right, bottom, label)

        port: SugiyamaPort
        for port in node.ports:
            if port.x is not None and port.y is not None:
                left, top, right, bottom = _update_bounds_with_rectangle(
                    left,
                    top,
                    right,
                    bottom,
                    port.x,
                    port.y,
                    port.x + port.width,
                    port.y + port.height,
                )
            else:
                left = left

            for label in port.labels:
                left, top, right, bottom = _update_bounds_with_label(left, top, right, bottom, label)

    edge: SugiyamaEdge
    for edge in context.graph.edges:
        section: SugiyamaEdgeSection
        for section in edge.sections:
            if section.start_point is not None:
                x_start: float = section.start_point[0]
                y_start: float = section.start_point[1]
                left, top, right, bottom = _update_bounds_with_rectangle(
                    left,
                    top,
                    right,
                    bottom,
                    x_start,
                    y_start,
                    x_start,
                    y_start,
                )
            else:
                left = left

            bend_point: tuple[float, float]
            for bend_point in section.bend_points:
                bend_x: float = bend_point[0]
                bend_y: float = bend_point[1]
                left, top, right, bottom = _update_bounds_with_rectangle(
                    left,
                    top,
                    right,
                    bottom,
                    bend_x,
                    bend_y,
                    bend_x,
                    bend_y,
                )

            if section.end_point is not None:
                x_end: float = section.end_point[0]
                y_end: float = section.end_point[1]
                left, top, right, bottom = _update_bounds_with_rectangle(
                    left,
                    top,
                    right,
                    bottom,
                    x_end,
                    y_end,
                    x_end,
                    y_end,
                )
            else:
                left = left

        for label in edge.labels:
            left, top, right, bottom = _update_bounds_with_label(left, top, right, bottom, label)

    if left is not None and top is not None and right is not None and bottom is not None:
        return left, top, right, bottom
    else:
        return None


def _shift_layout(context: LayoutContext, dx: float, dy: float) -> None:
    """Translate the whole layout by a constant offset.

    :param context: Shared pipeline context.
    :param dx: X displacement.
    :param dy: Y displacement.
    :returns: ``None``.
    """
    node: SugiyamaNode

    if abs(dx) > 1e-9 or abs(dy) > 1e-9:
        # The normalization shift happens only once after all coordinates exist, so
        # every geometric primitive is translated coherently by the same offset.
        for node in context.graph.all_nodes():
            if node.x is not None:
                node.x += dx
            else:
                node.x = node.x

            if node.y is not None:
                node.y += dy
            else:
                node.y = node.y

            label: SugiyamaLabel
            for label in node.labels:
                if label.x is not None:
                    label.x += dx
                else:
                    label.x = label.x

                if label.y is not None:
                    label.y += dy
                else:
                    label.y = label.y

            port: SugiyamaPort
            for port in node.ports:
                if port.x is not None:
                    port.x += dx
                else:
                    port.x = port.x

                if port.y is not None:
                    port.y += dy
                else:
                    port.y = port.y

                for label in port.labels:
                    if label.x is not None:
                        label.x += dx
                    else:
                        label.x = label.x

                    if label.y is not None:
                        label.y += dy
                    else:
                        label.y = label.y

        edge: SugiyamaEdge
        for edge in context.graph.edges:
            section: SugiyamaEdgeSection
            for section in edge.sections:
                if section.start_point is not None:
                    section.start_point = (section.start_point[0] + dx, section.start_point[1] + dy)
                else:
                    section.start_point = section.start_point

                if section.end_point is not None:
                    section.end_point = (section.end_point[0] + dx, section.end_point[1] + dy)
                else:
                    section.end_point = section.end_point

                if section.bend_points:
                    shifted_bend_points: list[tuple[float, float]] = list()
                    bend_point: tuple[float, float]
                    for bend_point in section.bend_points:
                        shifted_bend_points.append((bend_point[0] + dx, bend_point[1] + dy))
                    section.clear_bend_points()
                    section.extend_bend_points(shifted_bend_points)
                else:
                    section.clear_bend_points()

            for label in edge.labels:
                if label.x is not None:
                    label.x += dx
                else:
                    label.x = label.x

                if label.y is not None:
                    label.y += dy
                else:
                    label.y = label.y
    else:
        dx = dx


def _layout_direction(context: LayoutContext) -> LayoutDirection:
    """Return the layout direction.

    :param context: Shared pipeline context.
    :returns: Normalized layout direction.
    """
    options: dict[str, object] = context.option_resolver.resolve_for_element(context.graph.layout_options)
    direction: LayoutDirection = options.get("org.vera.sugiyama.direction", LayoutDirection.RIGHT)
    return direction


def _port_side(port: SugiyamaPort) -> PortSide:
    """Return the explicit port side.

    :param port: Port to inspect.
    :returns: Normalized port side.
    """
    side_value: object = (
        port.get_layout_option("org.vera.sugiyama.port.side", None)
        or port.get_property("side", None)
        or ""
    )
    side: PortSide = coerce_enum_value(PortSide, side_value, PortSide.UNDEFINED)
    return side


def _effective_port_side(port: SugiyamaPort, role: str, direction: LayoutDirection) -> PortSide:
    """Resolve the effective side of a port.

    :param port: Port to inspect.
    :param role: Port role string.
    :param direction: Layout direction.
    :returns: Effective port side.
    """
    explicit_side: PortSide = _port_side(port)
    resolved_side: PortSide = explicit_side

    if explicit_side is not PortSide.UNDEFINED:
        resolved_side = explicit_side
    else:
        if direction is LayoutDirection.LEFT:
            resolved_side = PortSide.WEST if role == "output" else PortSide.EAST
        else:
            if direction is LayoutDirection.DOWN:
                resolved_side = PortSide.SOUTH if role == "output" else PortSide.NORTH
            else:
                if direction is LayoutDirection.UP:
                    resolved_side = PortSide.NORTH if role == "output" else PortSide.SOUTH
                else:
                    resolved_side = PortSide.EAST if role == "output" else PortSide.WEST

    return resolved_side


def _place_node_labels(node: SugiyamaNode) -> None:
    """Place labels attached directly to one node.

    :param node: Node being annotated.
    :returns: ``None``.
    """
    label: SugiyamaLabel

    for label in node.labels:
        if node.x is not None and node.y is not None:
            label.x = node.x + max((node.width - label.width) / 2.0, 0.0)
            if label.height:
                label.y = node.y - label.height
            else:
                label.y = node.y
        else:
            label.x = None
            label.y = None


def _place_port_labels(node: SugiyamaNode, direction: LayoutDirection) -> None:
    """Place labels attached to the ports of one node.

    :param node: Node whose ports are processed.
    :param direction: Layout direction.
    :returns: ``None``.
    """
    port: SugiyamaPort

    for port in node.ports:
        label: SugiyamaLabel
        for label in port.labels:
            if port.x is not None and port.y is not None:
                role: str = str(port.get_property("role", "")).lower()
                side: PortSide = _effective_port_side(port, role, direction)

                if side is PortSide.WEST:
                    label.x = port.x - label.width - 4.0
                    label.y = port.y + max((port.height - label.height) / 2.0, 0.0)
                else:
                    if side is PortSide.EAST:
                        label.x = port.x + port.width + 4.0
                        label.y = port.y + max((port.height - label.height) / 2.0, 0.0)
                    else:
                        if side is PortSide.NORTH:
                            label.x = port.x + max((port.width - label.width) / 2.0, 0.0)
                            label.y = port.y - label.height - 4.0
                        else:
                            label.x = port.x + max((port.width - label.width) / 2.0, 0.0)
                            label.y = port.y + port.height + 4.0
            else:
                label.x = None
                label.y = None


def _place_edge_labels(edge: SugiyamaEdge) -> None:
    """Place labels on one edge using its first section.

    :param edge: Edge being annotated.
    :returns: ``None``.
    """
    midpoint: tuple[float, float] | None = None

    if edge.sections:
        section: SugiyamaEdgeSection = edge.sections[0]
        midpoint = _longest_segment_midpoint(_section_path_points(section))
    else:
        midpoint = None

    if midpoint is not None:
        label: SugiyamaLabel
        for label in edge.labels:
            if label.width:
                label.x = midpoint[0] - label.width / 2.0
            else:
                label.x = midpoint[0]

            if label.height:
                label.y = midpoint[1] - label.height - 4.0
            else:
                label.y = midpoint[1]
    else:
        label = None


class LabelPlacementPhase(LayoutPhaseBase):
    """Place node, port and edge labels and normalize the final layout."""

    __slots__ = ()

    name: str = "labels"

    def run(self, context: LayoutContext) -> None:
        """Execute the label-placement phase.

        :param context: Shared pipeline context.
        :returns: ``None``.
        """
        direction: LayoutDirection = _layout_direction(context)
        node: SugiyamaNode
        edge: SugiyamaEdge

        # Labels are placed after node and edge geometry exists because they depend on
        # the final routed positions of every primitive.
        for node in context.graph.all_nodes():
            _place_node_labels(node)
            _place_port_labels(node, direction)

        for edge in context.graph.edges:
            _place_edge_labels(edge)

        bounds: tuple[float, float, float, float] | None = _graph_bounds(context)
        if bounds is not None:
            left: float = bounds[0]
            top: float = bounds[1]
            right: float = bounds[2]
            bottom: float = bounds[3]
            _shift_layout(context, -left, -top)
            context.graph.width = max(right - left, 0.0)
            context.graph.height = max(bottom - top, 0.0)
        else:
            bounds = bounds
