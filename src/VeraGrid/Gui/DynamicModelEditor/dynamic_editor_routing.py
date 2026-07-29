# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import heapq
from typing import Iterable, List, Sequence, Tuple


RoutePoint = Tuple[float, float]
Rect = Tuple[float, float, float, float]


def build_stub_point(point: Sequence[float], side: str | None, stub_length: float) -> RoutePoint:
    """
    Build one perpendicular stub point from an endpoint and its attachment side.
    """
    x = float(point[0])
    y = float(point[1])
    distance = float(stub_length)
    side_key = "" if side is None else str(side).lower()

    if side_key == "left":
        return x - distance, y
    if side_key == "right":
        return x + distance, y
    if side_key == "top":
        return x, y - distance
    if side_key == "bottom":
        return x, y + distance
    return x, y


def normalize_route_points(points: Iterable[Sequence[float]]) -> List[RoutePoint]:
    """
    Normalize arbitrary numeric route points to float tuples.
    """
    normalized: List[RoutePoint] = list()
    point: Sequence[float]

    for point in points:
        if len(point) != 2:
            raise ValueError(f"Expected 2D route point, got {point!r}")
        normalized.append((float(point[0]), float(point[1])))

    return normalized


def compress_route_points(points: Iterable[Sequence[float]]) -> List[RoutePoint]:
    """
    Remove duplicate consecutive points, collinear elbows and axis reversals.
    """
    normalized_points = normalize_route_points(points)
    compressed_points: List[RoutePoint] = list()
    point: RoutePoint

    for point in normalized_points:
        if len(compressed_points) == 0 or compressed_points[-1] != point:
            compressed_points.append(point)

    if len(compressed_points) < 3:
        return compressed_points

    changed = True
    while changed and len(compressed_points) >= 3:
        changed = False
        simplified_points: List[RoutePoint] = [compressed_points[0]]
        point_index: int

        for point_index in range(1, len(compressed_points) - 1):
            previous_point = simplified_points[-1]
            current_point = compressed_points[point_index]
            next_point = compressed_points[point_index + 1]

            is_vertical_chain = previous_point[0] == current_point[0] and current_point[0] == next_point[0]
            is_horizontal_chain = previous_point[1] == current_point[1] and current_point[1] == next_point[1]

            if is_vertical_chain or is_horizontal_chain:
                changed = True
                continue

            simplified_points.append(current_point)

        simplified_points.append(compressed_points[-1])
        compressed_points = simplified_points

    return compressed_points


def is_axis_aligned_route_segment(start: Sequence[float], end: Sequence[float]) -> bool:
    """
    Return whether one route segment is horizontal or vertical.
    """
    return float(start[0]) == float(end[0]) or float(start[1]) == float(end[1])


def is_orthogonal_route(points: Iterable[Sequence[float]]) -> bool:
    """
    Return whether every segment in the route is axis aligned.
    """
    normalized_points = normalize_route_points(points)

    if len(normalized_points) < 2:
        return False

    point_index: int
    for point_index in range(len(normalized_points) - 1):
        if not is_axis_aligned_route_segment(
            start=normalized_points[point_index],
            end=normalized_points[point_index + 1],
        ):
            return False

    return True


def translate_route_points(points: Iterable[Sequence[float]], delta: Sequence[float]) -> List[RoutePoint]:
    """
    Translate all route points by one common delta.
    """
    normalized_points = normalize_route_points(points)
    translated_points: List[RoutePoint] = list()
    point: RoutePoint

    for point in normalized_points:
        translated_points.append((point[0] + float(delta[0]), point[1] + float(delta[1])))

    return translated_points


def _is_zero_delta(delta: RoutePoint, tolerance: float = 1e-9) -> bool:
    return abs(delta[0]) <= tolerance and abs(delta[1]) <= tolerance


def _deltas_are_equal(delta_1: RoutePoint, delta_2: RoutePoint, tolerance: float = 1e-9) -> bool:
    return abs(delta_1[0] - delta_2[0]) <= tolerance and abs(delta_1[1] - delta_2[1]) <= tolerance


def _get_single_interior_delta(start_delta: RoutePoint, end_delta: RoutePoint) -> RoutePoint:
    if _deltas_are_equal(start_delta, end_delta):
        return start_delta
    if _is_zero_delta(start_delta):
        return end_delta
    if _is_zero_delta(end_delta):
        return start_delta
    return ((start_delta[0] + end_delta[0]) * 0.5, (start_delta[1] + end_delta[1]) * 0.5)


def merge_route_with_endpoints(
    start: Sequence[float],
    end: Sequence[float],
    persisted_points: Iterable[Sequence[float]],
) -> List[RoutePoint]:
    """
    Replace persisted route endpoints with live endpoint positions while keeping interior elbows.
    """
    normalized_points = normalize_route_points(persisted_points)
    start_point = (float(start[0]), float(start[1]))
    end_point = (float(end[0]), float(end[1]))

    if len(normalized_points) < 2:
        return [start_point, end_point]

    start_delta: RoutePoint = (
        start_point[0] - normalized_points[0][0],
        start_point[1] - normalized_points[0][1],
    )
    end_delta: RoutePoint = (
        end_point[0] - normalized_points[-1][0],
        end_point[1] - normalized_points[-1][1],
    )

    if _deltas_are_equal(start_delta, end_delta):
        merged_points = translate_route_points(points=normalized_points, delta=start_delta)
    else:
        merged_points = list(normalized_points)
        merged_points[0] = start_point
        merged_points[-1] = end_point

        if len(merged_points) == 3:
            interior_delta = _get_single_interior_delta(start_delta=start_delta, end_delta=end_delta)
            merged_points[1] = (
                merged_points[1][0] + interior_delta[0],
                merged_points[1][1] + interior_delta[1],
            )
        elif len(merged_points) > 3:
            if not _is_zero_delta(start_delta):
                merged_points[1] = (
                    merged_points[1][0] + start_delta[0],
                    merged_points[1][1] + start_delta[1],
                )
            if not _is_zero_delta(end_delta):
                merged_points[-2] = (
                    merged_points[-2][0] + end_delta[0],
                    merged_points[-2][1] + end_delta[1],
                )

    return compress_route_points(merged_points)


def build_orthogonal_connection_route(
    start: Sequence[float],
    end: Sequence[float],
    elbow_offset: float,
) -> List[RoutePoint]:
    """
    Build one default orthogonal route between two points.
    """
    start_point = (float(start[0]), float(start[1]))
    end_point = (float(end[0]), float(end[1]))
    delta_x = end_point[0] - start_point[0]
    delta_y = end_point[1] - start_point[1]

    if abs(delta_y) < 1.0 or abs(delta_x) < 1.0:
        return compress_route_points([start_point, end_point])

    offset = min(float(elbow_offset), abs(delta_x) / 2.0) if delta_x != 0 else float(elbow_offset)
    start_elbow_x = start_point[0] + offset
    end_elbow_x = end_point[0] - offset

    if end_point[0] >= start_point[0]:
        route = [
            start_point,
            (start_elbow_x, start_point[1]),
            (start_elbow_x, end_point[1]),
            (end_elbow_x, end_point[1]),
            end_point,
        ]
    else:
        middle_x = start_point[0] + max(float(elbow_offset), abs(delta_x) / 2.0)
        route = [
            start_point,
            (middle_x, start_point[1]),
            (middle_x, end_point[1]),
            (end_elbow_x, end_point[1]),
            end_point,
        ]

    return compress_route_points(route)


def build_default_connection_route(
    start: Sequence[float],
    end: Sequence[float],
    route_style: str = "RETICULAR",
    elbow_offset: float = 36.0,
) -> List[RoutePoint]:
    """
    Build one default connection route in straight or orthogonal style.
    """
    start_point = (float(start[0]), float(start[1]))
    end_point = (float(end[0]), float(end[1]))

    if str(route_style).upper() == "STRAIGHT":
        return compress_route_points([start_point, end_point])
    return build_orthogonal_connection_route(start=start_point, end=end_point, elbow_offset=elbow_offset)


def orthogonalize_route_points(points: Iterable[Sequence[float]]) -> List[RoutePoint]:
    """
    Replace diagonal segments with orthogonal doglegs while preserving point order.
    """
    normalized_points = normalize_route_points(points)
    if len(normalized_points) < 2:
        return normalized_points

    orthogonal_points: List[RoutePoint] = [normalized_points[0]]
    previous_point: RoutePoint = normalized_points[0]
    point: RoutePoint
    for point in normalized_points[1:]:
        if abs(previous_point[0] - point[0]) <= 1e-9 or abs(previous_point[1] - point[1]) <= 1e-9:
            orthogonal_points.append(point)
            previous_point = point
            continue

        intermediate_point = (point[0], previous_point[1])
        if orthogonal_points[-1] != intermediate_point:
            orthogonal_points.append(intermediate_point)
        orthogonal_points.append(point)
        previous_point = point

    return compress_route_points(orthogonal_points)


def _segment_intersects_rect(
    p1: RoutePoint,
    p2: RoutePoint,
    rect: Rect,
    margin: float = 0.0,
) -> bool:
    left, top, right, bottom = rect
    left -= margin
    top -= margin
    right += margin
    bottom += margin

    if abs(p1[0] - p2[0]) <= 1e-9:
        x = p1[0]
        if not (left < x < right):
            return False
        seg_top = min(p1[1], p2[1])
        seg_bottom = max(p1[1], p2[1])
        return not (seg_bottom <= top or seg_top >= bottom)

    if abs(p1[1] - p2[1]) <= 1e-9:
        y = p1[1]
        if not (top < y < bottom):
            return False
        seg_left = min(p1[0], p2[0])
        seg_right = max(p1[0], p2[0])
        return not (seg_right <= left or seg_left >= right)

    return False


def _point_inside_rect(point: RoutePoint, rect: Rect, margin: float = 0.0) -> bool:
    left, top, right, bottom = rect
    return (
        left - margin < point[0] < right + margin
        and top - margin < point[1] < bottom + margin
    )


def _segment_clear_of_rectangles(
    p1: RoutePoint,
    p2: RoutePoint,
    rects: Iterable[Rect],
    margin: float = 0.0,
) -> bool:
    rect: Rect
    for rect in rects:
        if _segment_intersects_rect(p1, p2, rect, margin=margin):
            return False
    return True


def path_hits_rectangles(
    points: Iterable[Sequence[float]],
    rects: Iterable[Rect],
    margin: float = 0.0,
) -> bool:
    normalized_points = normalize_route_points(points)
    rect_list = list(rects)

    point_index: int
    for point_index in range(len(normalized_points) - 1):
        p1 = normalized_points[point_index]
        p2 = normalized_points[point_index + 1]
        rect: Rect
        for rect in rect_list:
            if _segment_intersects_rect(p1, p2, rect, margin=margin):
                return True
    return False


def violates_endpoint_directions(
    points: Iterable[Sequence[float]],
    start_side: str | None,
    end_side: str | None,
) -> bool:
    normalized_points = normalize_route_points(points)
    if len(normalized_points) < 2:
        return False

    if len(normalized_points) >= 2:
        first = normalized_points[0]
        second = normalized_points[1]
        dx = second[0] - first[0]
        dy = second[1] - first[1]
        if str(start_side).lower() == "left" and dx > 1e-9:
            return True
        if str(start_side).lower() == "right" and dx < -1e-9:
            return True
        if str(start_side).lower() == "top" and dy > 1e-9:
            return True
        if str(start_side).lower() == "bottom" and dy < -1e-9:
            return True

    if len(normalized_points) >= 2:
        previous = normalized_points[-2]
        last = normalized_points[-1]
        dx = last[0] - previous[0]
        dy = last[1] - previous[1]
        if str(end_side).lower() == "left" and dx < -1e-9:
            return True
        if str(end_side).lower() == "right" and dx > 1e-9:
            return True
        if str(end_side).lower() == "top" and dy < -1e-9:
            return True
        if str(end_side).lower() == "bottom" and dy > 1e-9:
            return True

    return False


def _first_hit_rectangle(
    points: Iterable[Sequence[float]],
    rects: Iterable[Rect],
    margin: float = 0.0,
) -> tuple[int, Rect] | None:
    normalized_points = normalize_route_points(points)
    rect_list = list(rects)

    point_index: int
    for point_index in range(len(normalized_points) - 1):
        p1 = normalized_points[point_index]
        p2 = normalized_points[point_index + 1]
        rect: Rect
        for rect in rect_list:
            if _segment_intersects_rect(p1, p2, rect, margin=margin):
                return point_index, rect
    return None


def reroute_around_rectangles(
    points: Iterable[Sequence[float]],
    rects: Iterable[Rect],
    start_side: str | None = None,
    end_side: str | None = None,
    clearance: float = 10.0,
    margin: float = 4.0,
) -> List[RoutePoint]:
    route = compress_route_points(points)
    rect_list = list(rects)
    if len(route) < 2:
        return route

    start = route[0]
    end = route[-1]

    x_guides = {start[0], end[0]}
    y_guides = {start[1], end[1]}

    point: RoutePoint
    for point in route:
        x_guides.add(point[0])
        y_guides.add(point[1])

    rect: Rect
    for rect in rect_list:
        left, top, right, bottom = rect
        x_guides.add(left - clearance)
        x_guides.add(right + clearance)
        y_guides.add(top - clearance)
        y_guides.add(bottom + clearance)

    x_values = sorted(x_guides)
    y_values = sorted(y_guides)

    nodes = {
        node
        for node in ((x, y) for x in x_values for y in y_values)
        if not any(_point_inside_rect(node, rect, margin=margin) for rect in rect_list)
    }
    nodes.add(start)
    nodes.add(end)

    adjacency: dict[RoutePoint, list[tuple[RoutePoint, str, float]]] = {node: [] for node in nodes}

    for y in y_values:
        row_nodes = sorted([node for node in nodes if abs(node[1] - y) <= 1e-9], key=lambda node: node[0])
        for index in range(len(row_nodes) - 1):
            left_node = row_nodes[index]
            right_node = row_nodes[index + 1]
            if _segment_clear_of_rectangles(left_node, right_node, rect_list, margin=margin):
                cost = abs(right_node[0] - left_node[0])
                adjacency[left_node].append((right_node, "H", cost))
                adjacency[right_node].append((left_node, "H", cost))

    for x in x_values:
        col_nodes = sorted([node for node in nodes if abs(node[0] - x) <= 1e-9], key=lambda node: node[1])
        for index in range(len(col_nodes) - 1):
            upper_node = col_nodes[index]
            lower_node = col_nodes[index + 1]
            if _segment_clear_of_rectangles(upper_node, lower_node, rect_list, margin=margin):
                cost = abs(lower_node[1] - upper_node[1])
                adjacency[upper_node].append((lower_node, "V", cost))
                adjacency[lower_node].append((upper_node, "V", cost))

    def violates_start_step(p_from: RoutePoint, p_to: RoutePoint) -> bool:
        dx = p_to[0] - p_from[0]
        dy = p_to[1] - p_from[1]
        if str(start_side).lower() == "left" and dx > 1e-9:
            return True
        if str(start_side).lower() == "right" and dx < -1e-9:
            return True
        if str(start_side).lower() == "top" and dy > 1e-9:
            return True
        if str(start_side).lower() == "bottom" and dy < -1e-9:
            return True
        return False

    def violates_end_step(p_from: RoutePoint, p_to: RoutePoint) -> bool:
        dx = p_to[0] - p_from[0]
        dy = p_to[1] - p_from[1]
        if str(end_side).lower() == "left" and dx < -1e-9:
            return True
        if str(end_side).lower() == "right" and dx > 1e-9:
            return True
        if str(end_side).lower() == "top" and dy < -1e-9:
            return True
        if str(end_side).lower() == "bottom" and dy > 1e-9:
            return True
        return False

    heap: list[tuple[float, float, RoutePoint, str | None]] = [(0.0, 0.0, start, None)]
    best_cost: dict[tuple[RoutePoint, str | None], float] = {(start, None): 0.0}
    prev_state: dict[tuple[RoutePoint, str | None], tuple[RoutePoint, str | None] | None] = {(start, None): None}

    end_state: tuple[RoutePoint, str | None] | None = None

    while heap:
        _, cost_so_far, node, prev_dir = heapq.heappop(heap)
        state = (node, prev_dir)
        if cost_so_far > best_cost.get(state, float("inf")) + 1e-9:
            continue
        if node == end:
            end_state = state
            break

        neighbor: RoutePoint
        direction: str
        step_cost: float
        for neighbor, direction, step_cost in adjacency.get(node, []):
            if node == start and violates_start_step(node, neighbor):
                continue
            if neighbor == end and violates_end_step(node, neighbor):
                continue

            bend_penalty = 0.0 if prev_dir is None or prev_dir == direction else 32.0
            new_cost = cost_so_far + step_cost + bend_penalty
            next_state = (neighbor, direction)
            if new_cost + 1e-9 < best_cost.get(next_state, float("inf")):
                best_cost[next_state] = new_cost
                prev_state[next_state] = state
                heuristic = abs(end[0] - neighbor[0]) + abs(end[1] - neighbor[1])
                heapq.heappush(heap, (new_cost + heuristic, new_cost, neighbor, direction))

    if end_state is None:
        return compress_route_points(route)

    recovered: list[RoutePoint] = []
    cursor: tuple[RoutePoint, str | None] | None = end_state
    while cursor is not None:
        recovered.append(cursor[0])
        cursor = prev_state.get(cursor)

    recovered.reverse()
    simplified = compress_route_points(recovered)
    if violates_endpoint_directions(simplified, start_side, end_side):
        return compress_route_points(route)
    return simplified


def move_polyline_route_segment(
    points: Iterable[Sequence[float]],
    segment_index: int,
    delta_x: float,
    delta_y: float,
) -> List[RoutePoint]:
    """
    Move one interior orthogonal route segment while keeping endpoints attached.
    """
    normalized_points = normalize_route_points(points)
    point_count = len(normalized_points)

    if point_count < 4 or segment_index <= 0 or segment_index >= point_count - 2:
        return normalized_points

    moved_points = list(normalized_points)
    start_point = normalized_points[segment_index]
    end_point = normalized_points[segment_index + 1]

    if abs(start_point[1] - end_point[1]) <= 1e-9:
        moved_points[segment_index] = (start_point[0], start_point[1] + float(delta_y))
        moved_points[segment_index + 1] = (end_point[0], end_point[1] + float(delta_y))
    elif abs(start_point[0] - end_point[0]) <= 1e-9:
        moved_points[segment_index] = (start_point[0] + float(delta_x), start_point[1])
        moved_points[segment_index + 1] = (end_point[0] + float(delta_x), end_point[1])
    else:
        return normalized_points

    return compress_route_points(moved_points)


def move_polyline_route_vertex(
    points: Iterable[Sequence[float]],
    vertex_index: int,
    new_x: float,
    new_y: float,
) -> List[RoutePoint]:
    """
    Move one interior route vertex.
    """
    normalized_points = normalize_route_points(points)
    point_count = len(normalized_points)

    if point_count < 3 or vertex_index <= 0 or vertex_index >= point_count - 1:
        return normalized_points

    moved_points = list(normalized_points)
    moved_points[vertex_index] = (float(new_x), float(new_y))
    return compress_route_points(moved_points)
