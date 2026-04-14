# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from math import hypot
from typing import Iterable, List, Tuple

RoutePoint = Tuple[float, float]
RouteSegment = Tuple[RoutePoint, RoutePoint]


def normalize_route_points(points: Iterable[RoutePoint]) -> List[RoutePoint]:
    """
    Normalize arbitrary numeric route points to float tuples.
    """
    normalized: List[RoutePoint] = list()

    for point in points:
        if len(point) != 2:
            raise ValueError(f"Expected 2D route point, got {point!r}")
        normalized.append((float(point[0]), float(point[1])))

    return normalized


def compress_route_points(points: Iterable[RoutePoint]) -> List[RoutePoint]:
    """
    Remove only duplicate consecutive route points.

    :param points: Route points.
    :return: Simplified route points.
    """
    normalized_points = normalize_route_points(points)
    compressed_points: List[RoutePoint] = list()
    point: RoutePoint

    for point in normalized_points:
        if len(compressed_points) == 0:
            compressed_points.append(point)
        elif compressed_points[-1] != point:
            compressed_points.append(point)
        else:
            pass

    return compressed_points


def align_adjacent_point_to_endpoint(endpoint_point: RoutePoint,
                                     adjacent_point: RoutePoint,
                                     side: str | None) -> RoutePoint:
    """
    Align one endpoint-adjacent elbow to preserve orthogonality after the endpoint moves.

    :param endpoint_point: Live endpoint position.
    :param adjacent_point: Persisted adjacent route point.
    :param side: Endpoint attachment side.
    :return: Realigned adjacent route point.
    """
    if side in ("top", "bottom"):
        return float(endpoint_point[0]), float(adjacent_point[1])
    elif side in ("left", "right"):
        return float(adjacent_point[0]), float(endpoint_point[1])
    else:
        return float(adjacent_point[0]), float(adjacent_point[1])


def is_zero_delta(delta: RoutePoint, tolerance: float = 1e-9) -> bool:
    """
    Determine whether one route delta is effectively zero.

    :param delta: Delta vector.
    :param tolerance: Absolute tolerance.
    :return: ``True`` when the delta is negligible.
    """
    return abs(float(delta[0])) <= tolerance and abs(float(delta[1])) <= tolerance


def deltas_are_equal(delta_1: RoutePoint,
                     delta_2: RoutePoint,
                     tolerance: float = 1e-9) -> bool:
    """
    Determine whether two route deltas are effectively equal.

    :param delta_1: First delta vector.
    :param delta_2: Second delta vector.
    :param tolerance: Absolute tolerance.
    :return: ``True`` when both deltas match.
    """
    return abs(float(delta_1[0]) - float(delta_2[0])) <= tolerance and abs(float(delta_1[1]) - float(delta_2[1])) <= tolerance


def translate_route_points(points: Iterable[RoutePoint], delta: RoutePoint) -> List[RoutePoint]:
    """
    Translate all route points by one common delta.

    :param points: Route points.
    :param delta: Translation delta.
    :return: Translated route points.
    """
    normalized_points = normalize_route_points(points)
    translated_points: List[RoutePoint] = list()
    point: RoutePoint

    for point in normalized_points:
        translated_points.append((point[0] + float(delta[0]), point[1] + float(delta[1])))

    return translated_points


def get_single_interior_delta(start_delta: RoutePoint, end_delta: RoutePoint) -> RoutePoint:
    """
    Choose the delta applied to the only interior point of a three-point route.

    :param start_delta: Start-endpoint delta.
    :param end_delta: End-endpoint delta.
    :return: Delta for the single interior point.
    """
    if deltas_are_equal(start_delta, end_delta):
        return start_delta
    elif is_zero_delta(start_delta):
        return end_delta
    elif is_zero_delta(end_delta):
        return start_delta
    else:
        return ((float(start_delta[0]) + float(end_delta[0])) * 0.5,
                (float(start_delta[1]) + float(end_delta[1])) * 0.5)


def merge_route_with_endpoints(start: RoutePoint,
                               end: RoutePoint,
                               persisted_points: Iterable[RoutePoint],
                               start_side: str | None = None,
                               end_side: str | None = None) -> List[RoutePoint]:
    """
    Replace persisted route endpoints with the live endpoint positions while keeping interior elbows.
    """
    normalized_points = normalize_route_points(persisted_points)
    start_point = (float(start[0]), float(start[1]))
    end_point = (float(end[0]), float(end[1]))

    if len(normalized_points) >= 2:
        start_delta: RoutePoint = (start_point[0] - normalized_points[0][0],
                                   start_point[1] - normalized_points[0][1])
        end_delta: RoutePoint = (end_point[0] - normalized_points[-1][0],
                                 end_point[1] - normalized_points[-1][1])

        if deltas_are_equal(start_delta, end_delta):
            merged_points = translate_route_points(points=normalized_points, delta=start_delta)
        else:
            merged_points = list(normalized_points)
            merged_points[0] = start_point
            merged_points[-1] = end_point

            if len(merged_points) == 3:
                interior_delta = get_single_interior_delta(start_delta=start_delta,
                                                           end_delta=end_delta)
                merged_points[1] = (merged_points[1][0] + interior_delta[0],
                                    merged_points[1][1] + interior_delta[1])
            elif len(merged_points) > 3:
                if is_zero_delta(start_delta):
                    pass
                else:
                    merged_points[1] = (merged_points[1][0] + start_delta[0],
                                        merged_points[1][1] + start_delta[1])

                if is_zero_delta(end_delta):
                    pass
                else:
                    merged_points[-2] = (merged_points[-2][0] + end_delta[0],
                                         merged_points[-2][1] + end_delta[1])
            else:
                pass

        return compress_route_points(merged_points)
    else:
        return [start_point, end_point]


def move_polyline_route_segment(points: Iterable[RoutePoint],
                                segment_index: int,
                                delta_x: float,
                                delta_y: float) -> List[RoutePoint]:
    """
    Move one interior polyline segment as a rigid segment.

    The editable segment must not be the first or last segment because the
    start and end points remain attached to their owning nodes.

    :param points: Route points.
    :param segment_index: Zero-based segment index.
    :param delta_x: Horizontal scene delta.
    :param delta_y: Vertical scene delta.
    :return: Updated route points.
    """
    normalized_points = normalize_route_points(points)
    point_count = len(normalized_points)

    if point_count < 4:
        return normalized_points
    elif segment_index <= 0:
        return normalized_points
    elif segment_index >= point_count - 2:
        return normalized_points
    else:
        pass

    moved_points = list(normalized_points)
    start_point = normalized_points[segment_index]
    end_point = normalized_points[segment_index + 1]
    moved_delta_x = float(delta_x)
    moved_delta_y = float(delta_y)

    moved_points[segment_index] = (start_point[0] + moved_delta_x, start_point[1] + moved_delta_y)
    moved_points[segment_index + 1] = (end_point[0] + moved_delta_x, end_point[1] + moved_delta_y)

    return compress_route_points(moved_points)


def move_polyline_route_vertex(points: Iterable[RoutePoint],
                               vertex_index: int,
                               new_x: float,
                               new_y: float) -> List[RoutePoint]:
    """
    Move one interior polyline vertex.

    :param points: Route points.
    :param vertex_index: Index of the vertex to move.
    :param new_x: New scene X coordinate.
    :param new_y: New scene Y coordinate.
    :return: Updated route points.
    """
    normalized_points = normalize_route_points(points)
    point_count = len(normalized_points)

    if point_count < 3:
        return normalized_points
    elif vertex_index <= 0:
        return normalized_points
    elif vertex_index >= point_count - 1:
        return normalized_points
    else:
        pass

    moved_points = list(normalized_points)
    moved_points[vertex_index] = (float(new_x), float(new_y))
    return compress_route_points(moved_points)


def move_orthogonal_route_segment(points: Iterable[RoutePoint],
                                  segment_index: int,
                                  delta_x: float,
                                  delta_y: float) -> List[RoutePoint]:
    """
    Backward-compatible wrapper that now moves generic polyline segments.
    """
    return move_polyline_route_segment(points=points,
                                      segment_index=segment_index,
                                      delta_x=delta_x,
                                      delta_y=delta_y)


def move_orthogonal_route_vertex(points: Iterable[RoutePoint],
                                 vertex_index: int,
                                 new_x: float,
                                 new_y: float) -> List[RoutePoint]:
    """
    Backward-compatible wrapper that now moves generic polyline vertices.
    """
    return move_polyline_route_vertex(points=points,
                                     vertex_index=vertex_index,
                                     new_x=new_x,
                                     new_y=new_y)


def sample_route_segment(points: Iterable[RoutePoint], position: float) -> Tuple[RoutePoint, RouteSegment]:
    """
    Sample a route at a normalized path position and return the point plus its local segment.
    """
    normalized_points = normalize_route_points(points)

    if len(normalized_points) == 0:
        raise ValueError("At least two route points are required")
    elif len(normalized_points) == 1:
        point: RoutePoint = normalized_points[0]
        return point, (point, point)
    else:
        pass

    clamped_position = min(max(float(position), 0.0), 1.0)
    segments: List[Tuple[RouteSegment, float]] = list()
    total_length = 0.0

    for idx in range(len(normalized_points) - 1):
        p1 = normalized_points[idx]
        p2 = normalized_points[idx + 1]
        length = hypot(p2[0] - p1[0], p2[1] - p1[1])
        if length > 0.0:
            segments.append((((p1[0], p1[1]), (p2[0], p2[1])), length))
            total_length += length

    if not segments:
        point = normalized_points[0]
        return point, (point, point)

    target_length = total_length * clamped_position
    traversed = 0.0

    for segment, length in segments:
        next_traversed = traversed + length

        if target_length <= next_traversed:
            remaining = target_length - traversed
            factor = remaining / length if length > 0.0 else 0.0
            p1, p2 = segment
            point = (p1[0] + (p2[0] - p1[0]) * factor,
                     p1[1] + (p2[1] - p1[1]) * factor)
            return point, segment

        traversed = next_traversed

    last_segment = segments[-1][0]
    return last_segment[1], last_segment
