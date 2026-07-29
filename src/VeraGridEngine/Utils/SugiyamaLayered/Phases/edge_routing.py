# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from VeraGridEngine.Utils.SugiyamaLayered.Phases.long_edges import VirtualNode
from VeraGridEngine.Utils.SugiyamaLayered.model import SugiyamaEdge, SugiyamaEdgeSection, SugiyamaNode, SugiyamaPort
from VeraGridEngine.Utils.SugiyamaLayered.options import (
    EdgeRoutingMode,
    LayoutDirection,
    PortAlignment,
    PortConstraint,
    PortSide,
    SelfLoopDistribution,
    coerce_enum_value,
)
from VeraGridEngine.Utils.SugiyamaLayered.pipeline import LayoutContext, LayoutPhaseBase


def _owner_of_port(context: LayoutContext, port_id: str) -> SugiyamaNode | None:
    """Return the node owning one port.

    :param context: Shared pipeline context.
    :param port_id: Port identifier.
    :returns: Owning node or ``None``.
    """
    node: SugiyamaNode
    for node in context.graph.all_nodes():
        port: SugiyamaPort
        for port in node.ports:
            if port.identifier == port_id:
                return node
            else:
                node = node

    return None


def _port_side(port: SugiyamaPort) -> PortSide:
    """Return the explicit side of one port.

    :param port: Port to inspect.
    :returns: Normalized side name.
    """
    side_value: Any = (
        port.get_layout_option("org.vera.sugiyama.port.side", None)
        or port.get_property("side", None)
        or ""
    )
    side: PortSide = coerce_enum_value(PortSide, side_value, PortSide.UNDEFINED)
    return side


def _port_side_rank(side: PortSide) -> int:
    """Return the stable rank of one port side.

    :param side: Side name.
    :returns: Stable numeric rank.
    """
    rank: int = 4

    if side is PortSide.WEST:
        rank = 0
    else:
        if side is PortSide.NORTH:
            rank = 1
        else:
            if side is PortSide.SOUTH:
                rank = 2
            else:
                if side is PortSide.EAST:
                    rank = 3
                else:
                    rank = 4

    return rank


def _read_integer_candidate(value: Any) -> int | None:
    """Parse an optional integer value.

    :param value: Raw value to parse.
    :returns: Parsed integer or ``None``.
    """
    parsed_value: int | None = None

    if value is not None:
        try:
            parsed_value = int(value)
        except (TypeError, ValueError):
            parsed_value = None
    else:
        parsed_value = None

    return parsed_value


def _port_sort_key(port: SugiyamaPort) -> tuple[int, int, str]:
    """Return the stable ordering key for one port.

    :param port: Port to rank.
    :returns: Stable ordering key.
    """
    side_rank: int = _port_side_rank(_port_side(port))
    index_value: Any = port.get_property("port_index", 0)
    index: int = _read_integer_candidate(index_value) or 0
    return side_rank, index, port.identifier


def _sort_ports(ports: list[SugiyamaPort]) -> list[SugiyamaPort]:
    """Sort ports deterministically.

    :param ports: Ports to sort.
    :returns: Sorted ports.
    """
    decorated_ports: list[tuple[tuple[int, int, str], SugiyamaPort]] = list()
    sorted_ports: list[SugiyamaPort] = list()
    port: SugiyamaPort

    for port in ports:
        decorated_ports.append((_port_sort_key(port), port))

    decorated_ports.sort()

    for _, resolved_port in decorated_ports:
        sorted_ports.append(resolved_port)

    return sorted_ports


def _port_groups(node: SugiyamaNode) -> tuple[list[SugiyamaPort], list[SugiyamaPort]]:
    """Return input and output ports of one node.

    :param node: Node to inspect.
    :returns: Input and output ports.
    """
    input_ports: list[SugiyamaPort] = list()
    output_ports: list[SugiyamaPort] = list()
    sorted_ports: list[SugiyamaPort] = _sort_ports(node.ports)
    port: SugiyamaPort

    for port in sorted_ports:
        role: str = str(port.get_property("role", "")).lower()
        if role == "input":
            input_ports.append(port)
        else:
            if role == "output":
                output_ports.append(port)
            else:
                output_ports = output_ports

    return input_ports, output_ports


def _effective_port_side(port: SugiyamaPort, role: str, direction: LayoutDirection) -> PortSide:
    """Resolve the effective side of one port.

    :param port: Port to inspect.
    :param role: Port role string.
    :param direction: Layout direction.
    :returns: Effective side name.
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


def _port_alignment(node: SugiyamaNode, context: LayoutContext) -> PortAlignment:
    """Return the default port alignment of one node.

    :param node: Node to inspect.
    :param context: Shared pipeline context.
    :returns: Port-alignment policy.
    """
    options: dict[str, Any] = context.option_resolver.resolve_for_element(
        context.graph.layout_options,
        node.layout_options,
    )
    value: Any = options.get("org.vera.sugiyama.portAlignment.default", PortAlignment.CENTER)
    alignment: PortAlignment = coerce_enum_value(PortAlignment, value, PortAlignment.CENTER)
    return alignment


def _layout_direction(context: LayoutContext) -> LayoutDirection:
    """Return the normalized layout direction.

    :param context: Shared pipeline context.
    :returns: Layout direction.
    """
    options: dict[str, Any] = context.option_resolver.resolve_for_element(context.graph.layout_options)
    direction: LayoutDirection = options.get("org.vera.sugiyama.direction", LayoutDirection.RIGHT)
    return direction


def _self_loop_distribution(context: LayoutContext) -> SelfLoopDistribution:
    """Return the self-loop routing preference.

    :param context: Shared pipeline context.
    :returns: Self-loop distribution policy.
    """
    options: dict[str, Any] = context.option_resolver.resolve_for_element(context.graph.layout_options)
    distribution_value: Any = options.get(
        "org.vera.sugiyama.layered.edgeRouting.selfLoopDistribution",
        SelfLoopDistribution.NORTH,
    )
    distribution: SelfLoopDistribution = coerce_enum_value(
        SelfLoopDistribution,
        distribution_value,
        SelfLoopDistribution.NORTH,
    )
    return distribution


def _edge_routing_mode(context: LayoutContext) -> EdgeRoutingMode:
    """Return the edge routing mode.

    :param context: Shared pipeline context.
    :returns: Routing mode.
    """
    options: dict[str, Any] = context.option_resolver.resolve_for_element(context.graph.layout_options)
    mode: EdgeRoutingMode = options.get("org.vera.sugiyama.edgeRouting", EdgeRoutingMode.ORTHOGONAL)
    return mode


def _feedback_edges_enabled(context: LayoutContext) -> bool:
    """Return whether feedback edges are routed specially.

    :param context: Shared pipeline context.
    :returns: ``True`` when feedback-edge routing is enabled.
    """
    options: dict[str, Any] = context.option_resolver.resolve_for_element(context.graph.layout_options)
    value: Any = options.get("org.vera.sugiyama.layered.feedbackEdges", False)
    is_enabled: bool = False

    if isinstance(value, str):
        is_enabled = value.strip().lower() in {"1", "true", "yes", "on"}
    else:
        is_enabled = bool(value)

    return is_enabled


def _node_port_constraints(node: SugiyamaNode, context: LayoutContext) -> PortConstraint:
    """Return the port-constraint policy of one node.

    :param node: Node to inspect.
    :param context: Shared pipeline context.
    :returns: Port-constraint policy.
    """
    options: dict[str, Any] = context.option_resolver.resolve_for_element(
        context.graph.layout_options,
        node.layout_options,
    )
    value: Any = options.get("org.vera.sugiyama.portConstraints", PortConstraint.UNDEFINED)
    constraints: PortConstraint = coerce_enum_value(PortConstraint, value, PortConstraint.UNDEFINED)
    return constraints


def _port_anchor(context: LayoutContext, endpoint_id: str, role: str) -> tuple[float, float] | None:
    """Return the anchor point of one edge endpoint.

    :param context: Shared pipeline context.
    :param endpoint_id: Endpoint identifier.
    :param role: Endpoint role, usually ``input`` or ``output``.
    :returns: Anchor point or ``None``.
    """
    direction: LayoutDirection = _layout_direction(context)
    node_by_id: dict[str, SugiyamaNode] = context.graph.node_by_id()
    node: SugiyamaNode | None = node_by_id.get(endpoint_id, None)
    port: SugiyamaPort | None = None

    if node is None:
        port = context.graph.port_by_id().get(endpoint_id, None)
        if port is not None:
            node = _owner_of_port(context, port.identifier)
        else:
            port = None
    else:
        port = None

    if node is not None and node.x is not None and node.y is not None:
        if port is None:
            if role == "output":
                return node.x + node.width, node.y + node.height / 2.0
            else:
                return node.x, node.y + node.height / 2.0
        else:
            if port.x is not None and port.y is not None:
                return port.x + port.width / 2.0, port.y + port.height / 2.0
            else:
                input_ports: list[SugiyamaPort]
                output_ports: list[SugiyamaPort]
                input_ports, output_ports = _port_groups(node)
                ports: list[SugiyamaPort] = output_ports if role == "output" else input_ports
                constraints: PortConstraint = _node_port_constraints(node, context)

                if port not in ports:
                    if constraints in {PortConstraint.FIXED_ORDER, PortConstraint.FIXED_SIDE}:
                        candidate_ports: list[SugiyamaPort] = list(ports)
                        candidate_ports.append(port)
                        ports = _sort_ports(candidate_ports)
                    else:
                        ports = [port]
                else:
                    ports = ports

                index: int = 0
                if port in ports:
                    index = ports.index(port)
                else:
                    index = 0

                norm: float = 0.5
                if ports:
                    norm = (index + 1) / (len(ports) + 1)
                else:
                    norm = 0.5

                alignment: PortAlignment = _port_alignment(node, context)
                if alignment is PortAlignment.BEGIN:
                    norm = min(norm, 0.25 if len(ports) > 1 else 0.5)
                else:
                    if alignment is PortAlignment.END:
                        norm = max(norm, 0.75 if len(ports) > 1 else 0.5)
                    else:
                        norm = norm

                side: PortSide = _effective_port_side(port, role, direction)
                if side in {PortSide.NORTH, PortSide.SOUTH}:
                    anchor_x: float = node.x + norm * node.width
                    anchor_y: float = node.y if side is PortSide.NORTH else node.y + node.height
                    return anchor_x, anchor_y
                else:
                    if side is PortSide.EAST:
                        return node.x + node.width, node.y + norm * node.height
                    else:
                        if side is PortSide.WEST:
                            return node.x, node.y + norm * node.height
                        else:
                            if role == "output":
                                return node.x + node.width, node.y + norm * node.height
                            else:
                                return node.x, node.y + norm * node.height
    else:
        return None


def _all_node_bounds(context: LayoutContext) -> tuple[float, float, float, float]:
    """Return the bounding box of placed nodes.

    :param context: Shared pipeline context.
    :returns: Bounding box of placed nodes.
    """
    left: float = 0.0
    top: float = 0.0
    right: float = 0.0
    bottom: float = 0.0
    has_nodes: bool = False
    node: SugiyamaNode

    for node in context.graph.children:
        if node.x is not None and node.y is not None:
            if not has_nodes:
                left = node.x
                top = node.y
                right = node.x + node.width
                bottom = node.y + node.height
                has_nodes = True
            else:
                left = min(left, node.x)
                top = min(top, node.y)
                right = max(right, node.x + node.width)
                bottom = max(bottom, node.y + node.height)
        else:
            has_nodes = has_nodes

    if has_nodes:
        return left, top, right, bottom
    else:
        return 0.0, 0.0, 0.0, 0.0


def _node_rects(context: LayoutContext) -> list[tuple[str, float, float, float, float]]:
    """Return rectangles of all placed nodes.

    :param context: Shared pipeline context.
    :returns: Node rectangles.
    """
    rectangles: list[tuple[str, float, float, float, float]] = list()
    node: SugiyamaNode

    for node in context.graph.children:
        if node.x is not None and node.y is not None:
            rectangles.append((node.identifier, node.x, node.y, node.x + node.width, node.y + node.height))
        else:
            rectangles = rectangles

    return rectangles


def _clean(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Remove consecutive duplicate points.

    :param points: Polyline points.
    :returns: Cleaned points.
    """
    cleaned_points: list[tuple[float, float]] = list()
    point: tuple[float, float]

    for point in points:
        if not cleaned_points or cleaned_points[-1] != point:
            cleaned_points.append(point)
        else:
            cleaned_points = cleaned_points

    return cleaned_points


def _is_between(value: float, a: float, b: float) -> bool:
    """Return whether one value lies between two others.

    :param value: Value to test.
    :param a: First bound.
    :param b: Second bound.
    :returns: ``True`` when the value lies between both bounds.
    """
    lower_bound: float = min(a, b)
    upper_bound: float = max(a, b)
    return lower_bound <= value <= upper_bound


def _remove_collinear(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Remove intermediate collinear polyline points.

    :param points: Polyline points.
    :returns: Simplified points.
    """
    if len(points) <= 2:
        return list(points)
    else:
        result: list[tuple[float, float]] = [points[0]]
        index: int

        for index in range(1, len(points) - 1):
            previous_point: tuple[float, float] = result[-1]
            current_point: tuple[float, float] = points[index]
            next_point: tuple[float, float] = points[index + 1]
            same_x: bool = previous_point[0] == current_point[0] == next_point[0]
            same_y: bool = previous_point[1] == current_point[1] == next_point[1]

            if same_x or same_y:
                result = result
            else:
                result.append(current_point)

        result.append(points[-1])
        return result


def _remove_axis_reversals(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Remove immediate axis reversals from a polyline.

    :param points: Polyline points.
    :returns: Simplified points.
    """
    if len(points) <= 2:
        return list(points)
    else:
        result: list[tuple[float, float]] = [points[0]]
        point: tuple[float, float]

        for point in points[1:]:
            result.append(point)
            simplify_loop: bool = True

            while len(result) >= 3 and simplify_loop:
                point_a: tuple[float, float] = result[-3]
                point_b: tuple[float, float] = result[-2]
                point_c: tuple[float, float] = result[-1]

                if point_a == point_c:
                    result.pop(-2)
                    result.pop(-2)
                else:
                    same_x: bool = point_a[0] == point_b[0] == point_c[0]
                    same_y: bool = point_a[1] == point_b[1] == point_c[1]

                    if same_x and _is_between(point_b[1], point_a[1], point_c[1]):
                        result.pop(-2)
                    else:
                        if same_y and _is_between(point_b[0], point_a[0], point_c[0]):
                            result.pop(-2)
                        else:
                            simplify_loop = False

        return result


def _simplify_path(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Repeatedly simplify a polyline.

    :param points: Polyline points.
    :returns: Simplified path.
    """
    simplified: list[tuple[float, float]] = _clean(points)
    previous_length: int = -1

    while previous_length != len(simplified):
        previous_length = len(simplified)
        simplified = _remove_collinear(simplified)
        simplified = _remove_axis_reversals(simplified)
        simplified = _clean(simplified)

    return simplified


def _feedback_path(
    start: tuple[float, float],
    end: tuple[float, float],
    bounds: tuple[float, float, float, float],
    index: int,
    direction: LayoutDirection,
) -> list[tuple[float, float]]:
    """Build a path for one feedback edge.

    :param start: Start point.
    :param end: End point.
    :param bounds: Graph bounds.
    :param index: Feedback-edge index.
    :param direction: Layout direction.
    :returns: Routed path.
    """
    left: float = bounds[0]
    top: float = bounds[1]
    right: float = bounds[2]
    bottom: float = bounds[3]
    route_gap: float = 80.0 + index * 18.0

    if direction is LayoutDirection.LEFT:
        outer_x: float = left - route_gap
        return _clean([start, (outer_x, start[1]), (outer_x, end[1]), end])
    else:
        if direction is LayoutDirection.DOWN:
            outer_y: float = bottom + route_gap
            return _clean([start, (start[0], outer_y), (end[0], outer_y), end])
        else:
            if direction is LayoutDirection.UP:
                outer_y = top - route_gap
                return _simplify_path([start, (start[0], outer_y), (end[0], outer_y), end])
            else:
                outer_x = right + route_gap
                upper_y: float = top - route_gap
                return _simplify_path(
                    [start, (outer_x, start[1]), (outer_x, upper_y), (end[0] - 24.0, upper_y), (end[0] - 24.0, end[1]), end]
                )


def _self_loop_path(
    node: SugiyamaNode,
    start: tuple[float, float],
    end: tuple[float, float],
    index: int,
    direction: LayoutDirection,
    distribution: SelfLoopDistribution,
) -> list[tuple[float, float]]:
    """Build a path for one self-loop.

    :param node: Node owning the self-loop.
    :param start: Start point.
    :param end: End point.
    :param index: Self-loop index.
    :param direction: Layout direction.
    :param distribution: Preferred loop side.
    :returns: Routed path.
    """
    route_gap: float = 80.0 + index * 18.0

    if distribution is SelfLoopDistribution.SOUTH:
        outer_y: float = node.y + node.height + route_gap
        return _simplify_path([start, (start[0], outer_y), (end[0], outer_y), end])
    else:
        if distribution is SelfLoopDistribution.WEST:
            outer_x: float = node.x - route_gap
            return _simplify_path([start, (outer_x, start[1]), (outer_x, end[1]), end])
        else:
            if distribution is SelfLoopDistribution.EAST:
                outer_x = node.x + node.width + route_gap
                return _simplify_path([start, (outer_x, start[1]), (outer_x, end[1]), end])
            else:
                if direction is LayoutDirection.LEFT:
                    outer_x = node.x - route_gap
                    return _simplify_path([start, (outer_x, start[1]), (outer_x, end[1]), end])
                else:
                    if direction is LayoutDirection.DOWN:
                        outer_y = node.y + node.height + route_gap
                        return _simplify_path([start, (start[0], outer_y), (end[0], outer_y), end])
                    else:
                        if direction is LayoutDirection.UP:
                            outer_y = node.y - route_gap
                            return _simplify_path([start, (start[0], outer_y), (end[0], outer_y), end])
                        else:
                            outer_x = node.x + node.width + route_gap
                            upper_y = node.y - route_gap
                            return _simplify_path(
                                [start, (outer_x, start[1]), (outer_x, upper_y), (end[0] - 24.0, upper_y), (end[0] - 24.0, end[1]), end]
                            )


def _same_layer_path(
    start: tuple[float, float],
    end: tuple[float, float],
    index: int,
    direction: LayoutDirection,
) -> list[tuple[float, float]]:
    """Build a detoured path between nodes on the same layer.

    :param start: Start point.
    :param end: End point.
    :param index: Pair index.
    :param direction: Layout direction.
    :returns: Routed path.
    """
    route_gap: float = 36.0 + index * 12.0

    if direction is LayoutDirection.LEFT:
        detour_x: float = min(start[0], end[0]) - route_gap
        return _simplify_path([start, (detour_x, start[1]), (detour_x, end[1]), end])
    else:
        if direction is LayoutDirection.DOWN:
            detour_y: float = max(start[1], end[1]) + route_gap
            return _simplify_path([start, (start[0], detour_y), (end[0], detour_y), end])
        else:
            if direction is LayoutDirection.UP:
                detour_y = min(start[1], end[1]) - route_gap
                return _simplify_path([start, (start[0], detour_y), (end[0], detour_y), end])
            else:
                detour_x = max(start[0], end[0]) + route_gap
                return _simplify_path([start, (detour_x, start[1]), (detour_x, end[1]), end])


def _standard_path(
    points: list[tuple[float, float]],
    index_offset: float = 0.0,
    direction: LayoutDirection = LayoutDirection.RIGHT,
) -> list[tuple[float, float]]:
    """Route a polyline using orthogonal midpoints.

    :param points: Chain points to connect.
    :param index_offset: Offset used to separate parallel edges.
    :param direction: Layout direction.
    :returns: Routed path.
    """
    if len(points) < 2:
        return points
    else:
        routed: list[tuple[float, float]] = [points[0]]
        index: int

        for index in range(len(points) - 1):
            source_point: tuple[float, float] = points[index]
            target_point: tuple[float, float] = points[index + 1]
            is_last_segment: bool = index == len(points) - 2

            if is_last_segment:
                routed.append(target_point)
            else:
                if direction in {LayoutDirection.DOWN, LayoutDirection.UP}:
                    mid_y: float = (source_point[1] + target_point[1]) / 2.0 + index_offset
                    routed.extend([(source_point[0], mid_y), (target_point[0], mid_y), target_point])
                else:
                    mid_x: float = (source_point[0] + target_point[0]) / 2.0 + index_offset
                    routed.extend([(mid_x, source_point[1]), (mid_x, target_point[1]), target_point])

        return _simplify_path(routed)


def _polyline_path(
    points: list[tuple[float, float]],
    index_offset: float = 0.0,
    direction: LayoutDirection = LayoutDirection.RIGHT,
) -> list[tuple[float, float]]:
    """Route a path in polyline mode.

    :param points: Chain points to connect.
    :param index_offset: Offset used to separate parallel edges.
    :param direction: Layout direction.
    :returns: Routed path.
    """
    if len(points) < 2:
        return points
    else:
        if len(points) == 2:
            start: tuple[float, float] = points[0]
            end: tuple[float, float] = points[1]
            if direction in {LayoutDirection.DOWN, LayoutDirection.UP}:
                mid_y: float = (start[1] + end[1]) / 2.0 + index_offset
                return _simplify_path([start, (start[0], mid_y), end])
            else:
                mid_x: float = (start[0] + end[0]) / 2.0 + index_offset
                return _simplify_path([start, (mid_x, start[1]), end])
        else:
            return _simplify_path(points)


def _segment_intersects_rect(
    point_a: tuple[float, float],
    point_b: tuple[float, float],
    rectangle: tuple[float, float, float, float],
    margin: float = 4.0,
) -> bool:
    """Return whether an orthogonal segment intersects one rectangle.

    :param point_a: First segment point.
    :param point_b: Second segment point.
    :param rectangle: Rectangle bounds.
    :param margin: Safety margin around the rectangle.
    :returns: ``True`` when the segment intersects the rectangle.
    """
    left: float = rectangle[0] - margin
    top: float = rectangle[1] - margin
    right: float = rectangle[2] + margin
    bottom: float = rectangle[3] + margin
    x_a: float = point_a[0]
    y_a: float = point_a[1]
    x_b: float = point_b[0]
    y_b: float = point_b[1]

    if x_a == x_b:
        if left <= x_a <= right:
            segment_top: float = min(y_a, y_b)
            segment_bottom: float = max(y_a, y_b)
            return not (segment_bottom < top or segment_top > bottom)
        else:
            return False
    else:
        if y_a == y_b:
            if top <= y_a <= bottom:
                segment_left: float = min(x_a, x_b)
                segment_right: float = max(x_a, x_b)
                return not (segment_right < left or segment_left > right)
            else:
                return False
        else:
            return False


def _path_hits_nodes(
    path: list[tuple[float, float]],
    rectangles: list[tuple[str, float, float, float, float]],
    ignore_ids: set[str],
) -> bool:
    """Return whether a path crosses any node rectangle.

    :param path: Routed path.
    :param rectangles: Node rectangles.
    :param ignore_ids: Node identifiers to ignore.
    :returns: ``True`` when the path hits a node.
    """
    segment_index: int

    for segment_index in range(len(path) - 1):
        point_a: tuple[float, float] = path[segment_index]
        point_b: tuple[float, float] = path[segment_index + 1]
        rectangle_info: tuple[str, float, float, float, float]

        for rectangle_info in rectangles:
            node_id: str = rectangle_info[0]
            if node_id not in ignore_ids:
                if _segment_intersects_rect(point_a, point_b, rectangle_info[1:5]):
                    return True
                else:
                    ignore_ids = ignore_ids
            else:
                ignore_ids = ignore_ids

    return False


def _first_hit_node(
    path: list[tuple[float, float]],
    rectangles: list[tuple[str, float, float, float, float]],
    ignore_ids: set[str],
) -> tuple[int, tuple[str, float, float, float, float]] | None:
    """Return the first rectangle hit by a path.

    :param path: Routed path.
    :param rectangles: Node rectangles.
    :param ignore_ids: Node identifiers to ignore.
    :returns: Segment index and rectangle info, or ``None``.
    """
    segment_index: int

    for segment_index in range(len(path) - 1):
        point_a: tuple[float, float] = path[segment_index]
        point_b: tuple[float, float] = path[segment_index + 1]
        rectangle_info: tuple[str, float, float, float, float]

        for rectangle_info in rectangles:
            node_id: str = rectangle_info[0]
            if node_id not in ignore_ids:
                if _segment_intersects_rect(point_a, point_b, rectangle_info[1:5]):
                    return segment_index, rectangle_info
                else:
                    rectangle_info = rectangle_info
            else:
                rectangle_info = rectangle_info

    return None


def _detour_path(
    start: tuple[float, float],
    end: tuple[float, float],
    bounds: tuple[float, float, float, float],
    direction: LayoutDirection,
    index: int,
) -> list[tuple[float, float]]:
    """Build a coarse detour path around the whole graph.

    :param start: Start point.
    :param end: End point.
    :param bounds: Graph bounds.
    :param direction: Layout direction.
    :param index: Edge index.
    :returns: Detoured path.
    """
    left: float = bounds[0]
    top: float = bounds[1]
    right: float = bounds[2]
    bottom: float = bounds[3]
    gap: float = 56.0 + index * 12.0

    if direction is LayoutDirection.LEFT:
        detour_x: float = left - gap
        return _clean([start, (detour_x, start[1]), (detour_x, end[1]), end])
    else:
        if direction is LayoutDirection.DOWN:
            detour_y: float = bottom + gap
            return _clean([start, (start[0], detour_y), (end[0], detour_y), end])
        else:
            if direction is LayoutDirection.UP:
                detour_y = top - gap
                return _simplify_path([start, (start[0], detour_y), (end[0], detour_y), end])
            else:
                detour_x = right + gap
                return _simplify_path([start, (detour_x, start[1]), (detour_x, end[1]), end])


def _splice_detour(
    path: list[tuple[float, float]],
    segment_index: int,
    replacement: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    """Splice a replacement segment into a path.

    :param path: Original path.
    :param segment_index: Index of the replaced segment.
    :param replacement: Replacement polyline.
    :returns: Updated path.
    """
    return path[:segment_index] + replacement + path[segment_index + 2:]


def _segment_detour_candidates(
    point_a: tuple[float, float],
    point_b: tuple[float, float],
    rectangle: tuple[float, float, float, float],
    bounds: tuple[float, float, float, float],
    clearance: float,
) -> list[list[tuple[float, float]]]:
    """Return detour candidates around one obstructing rectangle.

    :param point_a: First segment point.
    :param point_b: Second segment point.
    :param rectangle: Obstructing rectangle.
    :param bounds: Graph bounds.
    :param clearance: Clearance around the rectangle.
    :returns: Detour candidate polylines.
    """
    left: float = rectangle[0]
    top: float = rectangle[1]
    right: float = rectangle[2]
    bottom: float = rectangle[3]
    graph_left: float = bounds[0]
    graph_top: float = bounds[1]
    graph_right: float = bounds[2]
    graph_bottom: float = bounds[3]
    candidates: list[list[tuple[float, float]]] = list()

    if point_a[0] == point_b[0]:
        x_value: float = point_a[0]
        left_x: float = min(left - clearance, graph_left - clearance)
        right_x: float = max(right + clearance, graph_right + clearance)
        candidates.append([point_a, (left_x, point_a[1]), (left_x, point_b[1]), point_b])
        candidates.append([point_a, (right_x, point_a[1]), (right_x, point_b[1]), point_b])
        candidates.append([point_a, (x_value, top - clearance), (point_b[0], top - clearance), point_b])
        candidates.append([point_a, (x_value, bottom + clearance), (point_b[0], bottom + clearance), point_b])
    else:
        if point_a[1] == point_b[1]:
            y_value: float = point_a[1]
            candidates.append([point_a, (point_a[0], top - clearance), (point_b[0], top - clearance), point_b])
            candidates.append([point_a, (point_a[0], bottom + clearance), (point_b[0], bottom + clearance), point_b])
            candidates.append([point_a, (left - clearance, y_value), (left - clearance, point_b[1]), point_b])
            candidates.append([point_a, (right + clearance, y_value), (right + clearance, point_b[1]), point_b])
        else:
            candidates = candidates

    graph_top = graph_top
    graph_bottom = graph_bottom
    return candidates


def _path_span(path: list[tuple[float, float]]) -> float:
    """Return the Manhattan span of a path.

    :param path: Routed path.
    :returns: Total Manhattan length.
    """
    total_span: float = 0.0
    index: int

    for index in range(len(path) - 1):
        total_span += abs(path[index + 1][0] - path[index][0]) + abs(path[index + 1][1] - path[index][1])

    return total_span


def _candidate_sort_key(candidate: list[tuple[float, float]]) -> tuple[int, float]:
    """Return the stable rank of one rerouting candidate.

    :param candidate: Candidate path.
    :returns: Stable sorting key.
    """
    return len(candidate), _path_span(candidate)


def _best_candidate(candidates: list[list[tuple[float, float]]]) -> list[tuple[float, float]] | None:
    """Return the best rerouting candidate.

    :param candidates: Candidate paths.
    :returns: Best candidate or ``None``.
    """
    decorated_candidates: list[tuple[tuple[int, float], list[tuple[float, float]]]] = list()
    candidate: list[tuple[float, float]]

    for candidate in candidates:
        decorated_candidates.append((_candidate_sort_key(candidate), candidate))

    if decorated_candidates:
        decorated_candidates.sort()
        return decorated_candidates[0][1]
    else:
        return None


def _reroute_around_nodes(
    path: list[tuple[float, float]],
    rectangles: list[tuple[str, float, float, float, float]],
    ignore_ids: set[str],
    bounds: tuple[float, float, float, float],
) -> list[tuple[float, float]]:
    """Iteratively reroute one path around obstructing nodes.

    :param path: Initial routed path.
    :param rectangles: Node rectangles.
    :param ignore_ids: Node identifiers to ignore.
    :param bounds: Graph bounds.
    :returns: Rerouted path.
    """
    rerouted_path: list[tuple[float, float]] = _simplify_path(path)
    attempt: int

    for attempt in range(10):
        hit_info: tuple[int, tuple[str, float, float, float, float]] | None = _first_hit_node(
            rerouted_path,
            rectangles,
            ignore_ids,
        )
        if hit_info is None:
            return _simplify_path(rerouted_path)
        else:
            segment_index: int = hit_info[0]
            rectangle_info: tuple[str, float, float, float, float] = hit_info[1]
            point_a: tuple[float, float] = rerouted_path[segment_index]
            point_b: tuple[float, float] = rerouted_path[segment_index + 1]
            candidates: list[list[tuple[float, float]]] = list()
            replacement: list[tuple[float, float]]

            for replacement in _segment_detour_candidates(
                point_a,
                point_b,
                rectangle_info[1:5],
                bounds,
                clearance=12.0 + attempt * 6.0,
            ):
                candidate: list[tuple[float, float]] = _simplify_path(
                    _splice_detour(rerouted_path, segment_index, replacement)
                )
                if not _path_hits_nodes(candidate, rectangles, ignore_ids):
                    candidates.append(candidate)
                else:
                    candidates = candidates

            best_candidate: list[tuple[float, float]] | None = _best_candidate(candidates)
            if best_candidate is not None:
                rerouted_path = best_candidate
            else:
                break

    return _simplify_path(rerouted_path)


def _pair_key(source_id: str, target_id: str) -> tuple[str, str]:
    """Return the key used to count parallel edge pairs.

    :param source_id: Source node identifier.
    :param target_id: Target node identifier.
    :returns: Pair key.
    """
    return source_id, target_id


def _next_pair_index(pair_counts: dict[tuple[str, str], int], source_id: str, target_id: str) -> int:
    """Return and increment the index of one edge pair.

    :param pair_counts: Pair counters.
    :param source_id: Source node identifier.
    :param target_id: Target node identifier.
    :returns: Current pair index.
    """
    key: tuple[str, str] = _pair_key(source_id, target_id)
    pair_index: int = pair_counts.get(key, 0)
    pair_counts[key] = pair_index + 1
    return pair_index


def _chain_points(
    edge_identifier: str,
    start: tuple[float, float],
    end: tuple[float, float],
    edge_paths: dict[str, list[str]],
    virtual_positions: dict[str, tuple[float, float]],
    expanded_nodes: dict[str, VirtualNode],
) -> list[tuple[float, float]]:
    """Build the routing chain points of one edge.

    :param edge_identifier: Edge identifier.
    :param start: Start anchor.
    :param end: End anchor.
    :param edge_paths: Expanded edge paths.
    :param virtual_positions: Positions of expanded nodes.
    :param expanded_nodes: Expanded-node lookup.
    :returns: Chain points used by the router.
    """
    path_ids: list[str] = edge_paths.get(edge_identifier, list())
    points: list[tuple[float, float]] = list()

    if path_ids:
        points.append(start)
        node_id: str
        for node_id in path_ids[1:-1]:
            position: tuple[float, float] | None = virtual_positions.get(node_id, None)
            node_info: VirtualNode | None = expanded_nodes.get(node_id, None)

            if position is not None and node_info is not None:
                points.append((position[0] + node_info.width / 2.0, position[1] + node_info.height / 2.0))
            else:
                points = points

        points.append(end)
    else:
        points = [start, end]

    return points


def _routing_offset(pair_index: int) -> float:
    """Return the offset used to separate parallel edges.

    :param pair_index: Pair index.
    :returns: Routing offset.
    """
    return pair_index * 7.0


def _build_section(path: list[tuple[float, float]]) -> SugiyamaEdgeSection:
    """Build one edge section from a path.

    :param path: Routed path.
    :returns: Edge section.
    """
    return SugiyamaEdgeSection(
        start_point=path[0],
        end_point=path[-1],
        bend_points=path[1:-1],
    )


def _route_regular_edge(
    start: tuple[float, float],
    end: tuple[float, float],
    source_id: str,
    target_id: str,
    edge_identifier: str,
    edge_paths: dict[str, list[str]],
    virtual_positions: dict[str, tuple[float, float]],
    expanded_nodes: dict[str, VirtualNode],
    pair_counts: dict[tuple[str, str], int],
    routing_mode: EdgeRoutingMode,
    direction: LayoutDirection,
    rectangles: list[tuple[str, float, float, float, float]],
    bounds: tuple[float, float, float, float],
) -> list[tuple[float, float]]:
    """Route a regular non-self-loop, non-feedback edge.

    :param start: Start anchor.
    :param end: End anchor.
    :param source_id: Source node identifier.
    :param target_id: Target node identifier.
    :param edge_identifier: Edge identifier.
    :param edge_paths: Expanded edge paths.
    :param virtual_positions: Positions of expanded nodes.
    :param expanded_nodes: Expanded-node lookup.
    :param pair_counts: Pair counters.
    :param routing_mode: Routing mode.
    :param direction: Layout direction.
    :param rectangles: Node rectangles.
    :param bounds: Graph bounds.
    :returns: Routed path.
    """
    pair_index: int = _next_pair_index(pair_counts, source_id, target_id)
    chain_points: list[tuple[float, float]] = _chain_points(
        edge_identifier,
        start,
        end,
        edge_paths,
        virtual_positions,
        expanded_nodes,
    )
    offset: float = _routing_offset(pair_index)
    path: list[tuple[float, float]] = list()
    ignored_nodes: set[str] = {source_id, target_id}

    if routing_mode in {EdgeRoutingMode.POLYLINE, EdgeRoutingMode.SPLINES}:
        path = _polyline_path(chain_points, index_offset=offset, direction=direction)
    else:
        path = _standard_path(chain_points, index_offset=offset, direction=direction)

    # After the first orthogonal route is built, the path is checked against node
    # rectangles and rerouted locally if necessary.
    if _path_hits_nodes(path, rectangles, ignored_nodes):
        rerouted_path: list[tuple[float, float]] = _reroute_around_nodes(path, rectangles, ignored_nodes, bounds)
        if _path_hits_nodes(rerouted_path, rectangles, ignored_nodes):
            path = _detour_path(start, end, bounds, direction, pair_index)
        else:
            path = rerouted_path
    else:
        path = path

    return _simplify_path(path)


class EdgeRoutingPhase(LayoutPhaseBase):
    """Route edges once node positions are known."""

    __slots__ = ()
    name: str = "edge-routing"

    def run(self, context: LayoutContext) -> None:
        """Execute the edge-routing phase.

        :param context: Shared pipeline context.
        :returns: ``None``.
        """
        edge_paths: dict[str, list[str]] = context.phase_state.edge_paths
        virtual_positions: dict[str, tuple[float, float]] = context.phase_state.virtual_positions
        expanded_nodes: dict[str, VirtualNode] = context.phase_state.expanded_nodes
        feedback_edges: set[str] = set()
        bounds: tuple[float, float, float, float] = _all_node_bounds(context)
        rectangles: list[tuple[str, float, float, float, float]] = _node_rects(context)
        direction: LayoutDirection = _layout_direction(context)
        routing_mode: EdgeRoutingMode = _edge_routing_mode(context)
        self_loop_distribution: SelfLoopDistribution = _self_loop_distribution(context)
        layer_of: dict[str, int] = context.phase_state.layer_of
        pair_counts: dict[tuple[str, str], int] = dict()
        feedback_index: int = 0
        self_loop_index: int = 0
        edge: SugiyamaEdge

        if _feedback_edges_enabled(context):
            feedback_edges = set(context.phase_state.feedback_edges)
        else:
            feedback_edges = set()

        # The router handles self-loops, feedback edges, same-layer edges and regular
        # edges separately because each class needs a different orthogonal template.
        for edge in context.graph.edges:
            edge.clear_sections()

            if edge.sources and edge.targets:
                source_endpoint: str = edge.sources[0]
                target_endpoint: str = edge.targets[0]
                start: tuple[float, float] | None = _port_anchor(context, source_endpoint, "output")
                end: tuple[float, float] | None = _port_anchor(context, target_endpoint, "input")

                if start is not None and end is not None:
                    source_id: str = str(edge.get_property("source_uid", ""))
                    target_id: str = str(edge.get_property("target_uid", ""))
                    source_node: SugiyamaNode | None = context.graph.node_by_id().get(source_id, None)

                    if source_id and source_id == target_id and source_node is not None:
                        self_loop_path: list[tuple[float, float]] = _self_loop_path(
                            source_node,
                            start,
                            end,
                            self_loop_index,
                            direction,
                            self_loop_distribution,
                        )
                        edge.append_section(_build_section(self_loop_path))
                        self_loop_index += 1
                    else:
                        if edge.identifier in feedback_edges:
                            feedback_path: list[tuple[float, float]] = _feedback_path(
                                start,
                                end,
                                bounds,
                                feedback_index,
                                direction,
                            )
                            edge.append_section(_build_section(feedback_path))
                            feedback_index += 1
                        else:
                            source_layer: int | None = layer_of.get(source_id, None)
                            target_layer: int | None = layer_of.get(target_id, None)

                            if source_layer is not None and target_layer is not None and source_layer == target_layer:
                                pair_index: int = _next_pair_index(pair_counts, source_id, target_id)
                                same_layer_path: list[tuple[float, float]] = _same_layer_path(
                                    start,
                                    end,
                                    pair_index,
                                    direction,
                                )
                                edge.append_section(_build_section(same_layer_path))
                            else:
                                regular_path: list[tuple[float, float]] = _route_regular_edge(
                                    start,
                                    end,
                                    source_id,
                                    target_id,
                                    edge.identifier,
                                    edge_paths,
                                    virtual_positions,
                                    expanded_nodes,
                                    pair_counts,
                                    routing_mode,
                                    direction,
                                    rectangles,
                                    bounds,
                                )
                                edge.append_section(_build_section(regular_path))
                else:
                    edge.clear_sections()
            else:
                edge.clear_sections()
