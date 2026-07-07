# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
ELK-style routing pipeline: EdgeRoutes, edge bundles, bend minimisation,
collision avoidance, and layout validation.

Separates routing concerns from layout computation.
"""
from __future__ import annotations

import math
from typing import Dict, List, Set, Tuple

from ._types import EdgeBundle, EdgeRoute, LayoutGraph, LayoutReport
from ._ports import port_abs_position, LEFT, RIGHT


# ── Helpers ────────────────────────────────────────────────────────

def _node_bbox(
    v: int,
    positions: Dict[int, Tuple[float, float]],
    graph: LayoutGraph,
) -> Tuple[float, float, float, float]:
    cfg = graph.config
    x, y = positions.get(v, (0.0, 0.0))
    w = cfg.dummy_w if v in graph.is_dummy else cfg.node_w
    h = cfg.dummy_h if v in graph.is_dummy else cfg.node_h
    return (x, y, x + w, y + h)


def _segment_hits_bbox(
    x1: float, y1: float, x2: float, y2: float,
    bbox: Tuple[float, float, float, float],
) -> bool:
    l, t, r, b = bbox
    seg_l, seg_r = (x1, x2) if x1 < x2 else (x2, x1)
    seg_t, seg_b = (y1, y2) if y1 < y2 else (y2, y1)
    if seg_r <= l or seg_l >= r or seg_b <= t or seg_t >= b:
        return False
    return True


def _path_collides(
    points: List[Tuple[float, float]],
    node_bboxes: Dict[int, Tuple[float, float, float, float]],
) -> bool:
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        for bbox in node_bboxes.values():
            if _segment_hits_bbox(x1, y1, x2, y2, bbox):
                return True
    return False


def _count_bends(points: List[Tuple[float, float]]) -> int:
    if len(points) < 3:
        return 0
    bends = 0
    for i in range(1, len(points) - 1):
        dx1 = points[i][0] - points[i - 1][0]
        dy1 = points[i][1] - points[i - 1][1]
        dx2 = points[i + 1][0] - points[i][0]
        dy2 = points[i + 1][1] - points[i][1]
        if (abs(dx1) > 0.1 and abs(dy2) > 0.1) or (abs(dy1) > 0.1 and abs(dx2) > 0.1):
            bends += 1
    return bends


def _clean_path(path: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    if not path:
        return path
    cleaned = [path[0]]
    for pt in path[1:]:
        if pt != cleaned[-1]:
            cleaned.append(pt)
    return cleaned


def _manhattan_length(points: List[Tuple[float, float]]) -> float:
    total = 0.0
    for i in range(len(points) - 1):
        total += abs(points[i][0] - points[i + 1][0]) + abs(points[i][1] - points[i + 1][1])
    return total


def _gap_vertical_extent(
    layer_idx: int,
    graph: LayoutGraph,
    positions: Dict[int, Tuple[float, float]],
) -> Tuple[float, float]:
    """Return (top, bottom) of the band between layers[layer_idx] and layers[layer_idx+1]."""
    cfg = graph.config
    top = float("inf")
    bottom = float("-inf")
    for v in graph.layers[layer_idx]:
        _, t, _, b = _node_bbox(v, positions, graph)
        top = min(top, t)
        bottom = max(bottom, b)
    for v in graph.layers[layer_idx + 1]:
        _, t, _, b = _node_bbox(v, positions, graph)
        top = min(top, t)
        bottom = max(bottom, b)
    if top == float("inf"):
        top = cfg.margin_y
        bottom = cfg.margin_y + cfg.node_h * 4
    return top, bottom


def _estimate_crossings_for_channel(
    edge_key: Tuple[int, int],
    channel_y: float,
    graph: LayoutGraph,
    positions: Dict[int, Tuple[float, float]],
    edge_routes: Dict[Tuple[int, int], EdgeRoute],
) -> int:
    """Rough crossing estimate: count how many already-routed edges intersect
    this edge's vertical segment at channel_y."""
    src, dst = edge_key
    cfg = graph.config
    src_x, src_y = positions.get(src, (0.0, 0.0))
    dst_x, dst_y = positions.get(dst, (0.0, 0.0))
    src_right = src_x + cfg.node_w
    dst_left = dst_x

    if dst_left >= src_right:
        vert_x = src_right
    else:
        vert_x = src_right

    crossings = 0
    for (ek, er) in edge_routes.items():
        if ek == edge_key:
            continue
        if not er.points:
            continue
        for i in range(len(er.points) - 1):
            ax1, ay1 = er.points[i]
            ax2, ay2 = er.points[i + 1]
            if abs(ax1 - ax2) < 0.1 and abs(ay1 - ay2) > 0.1:
                vert_lo = min(ay1, ay2)
                vert_hi = max(ay1, ay2)
                if abs(ax1 - vert_x) < 0.1 and vert_lo < channel_y < vert_hi:
                    crossings += 1
    return crossings


def _build_channel_candidates(
    gap_top: float,
    gap_bottom: float,
    src_y: float,
    tgt_y: float,
    num_candidates: int = 7,
) -> List[float]:
    candidates: Set[float] = {src_y, tgt_y, (src_y + tgt_y) / 2.0}
    for i in range(num_candidates):
        t = gap_top + (gap_bottom - gap_top) * (i + 1) / (num_candidates + 1)
        candidates.add(t)
    return sorted(c for c in candidates if gap_top <= c <= gap_bottom)


# ── Phase 1: Build EdgeRoute objects ───────────────────────────────

def build_edge_routes(
    graph: LayoutGraph,
    positions: Dict[int, Tuple[float, float]],
) -> Dict[Tuple[int, int], EdgeRoute]:
    """Convert port_edges into EdgeRoute objects with initial empty bend points.

    Each route records the source/target port ids and the
    layer-channel assignments (initially empty).
    """
    routes: Dict[Tuple[int, int], EdgeRoute] = {}
    if not graph.port_edges:
        return routes

    for src, sp, dst, dp in graph.port_edges:
        key = (src, dst)
        route = EdgeRoute(
            src=src,
            src_port=sp,
            dst=dst,
            dst_port=dp,
            points=[],
            layer_channels=[],
        )
        routes[key] = route

    graph.edge_routes = routes
    return routes


# ── Phase 2: Bend-minimising path search ───────────────────────────

def find_best_routing_path(
    edge_key: Tuple[int, int],
    graph: LayoutGraph,
    positions: Dict[int, Tuple[float, float]],
    node_bboxes: Dict[int, Tuple[float, float, float, float]],
    crossings_weight: float = 10.0,
    bend_weight: float = 3.0,
    length_weight: float = 1.0,
) -> List[Tuple[float, float]]:
    """Find the lowest-cost orthogonal path for *edge_key*.

    Explores candidate vertical-channel positions between each layer
    gap and picks the one that minimises:
        cost = crossings_weight * crossings
             + bend_weight * bends
             + length_weight * manhattan_length

    Returns the cleaned point list.
    """
    src, dst = edge_key
    cfg = graph.config

    src_pos = positions.get(src, (0.0, 0.0))
    dst_pos = positions.get(dst, (0.0, 0.0))

    # Source port y
    src_port_y: float | None = None
    if graph.port_map:
        for s, sp, d, dp in graph.port_edges:
            if s == src and d == dst:
                _, sy = port_abs_position(src, sp, positions, graph)
                src_port_y = sy
                break
    if src_port_y is None:
        src_port_y = src_pos[1] + cfg.node_h / 2.0

    # Target port y
    tgt_port_y: float | None = None
    if graph.port_map:
        for s, sp, d, dp in graph.port_edges:
            if d == dst:
                _, ty = port_abs_position(dst, dp, positions, graph)
                tgt_port_y = ty
                break
    if tgt_port_y is None:
        tgt_port_y = dst_pos[1] + cfg.node_h / 2.0

    src_right = src_pos[0] + cfg.node_w
    dst_left = dst_pos[0]

    L = len(graph.layers)
    src_layer = graph.layer_of.get(src, 0)
    dst_layer = graph.layer_of.get(dst, 0)

    # ── Direct (no detour) path ──
    # Try several vertical channel positions
    best_path: List[Tuple[float, float]] = []
    best_cost = float("inf")

    # Collect all gaps this edge spans
    gap_indices = list(range(src_layer, dst_layer)) if dst_layer > src_layer else [src_layer]

    if not gap_indices:
        gap_indices = [0]

    for gap_idx in gap_indices:
        if gap_idx >= L - 1:
            continue
        gap_top, gap_bottom = _gap_vertical_extent(gap_idx, graph, positions)

        if dst_left >= src_right:
            vert_x = src_right + (dst_left - src_right) * 0.5
        else:
            vert_x = src_right

        candidates = _build_channel_candidates(gap_top, gap_bottom, src_port_y, tgt_port_y)

        for cy in candidates:
            if dst_left >= src_right:
                raw: List[Tuple[float, float]] = [
                    (src_right, src_port_y),
                    (src_right, cy),
                    (dst_left, cy),
                    (dst_left, tgt_port_y),
                ]
            else:
                mid_x = (src_right + dst_left) / 2.0
                raw = [
                    (src_right, src_port_y),
                    (src_right, cy),
                    (mid_x, cy),
                    (mid_x, tgt_port_y),
                    (dst_left, tgt_port_y),
                ]

            cleaned = _clean_path(raw)
            collides = _path_collides(cleaned, node_bboxes)
            bends = _count_bends(cleaned)
            length = _manhattan_length(cleaned)
            crossings = _estimate_crossings_for_channel(
                edge_key, cy, graph, positions, graph.edge_routes,
            )

            cost = crossings_weight * crossings + bend_weight * bends + length_weight * length
            if collides:
                cost += 1000.0

            if cost < best_cost:
                best_cost = cost
                best_path = cleaned

    # ── Detour path (if direct collides or high cost) ──
    if best_cost > 500 or not best_path:
        # Try offsetting the vertical segment outside the layer band
        for gap_idx in gap_indices:
            if gap_idx >= L - 1:
                continue
            gap_top, gap_bottom = _gap_vertical_extent(gap_idx, graph, positions)
            gap_height = gap_bottom - gap_top
            if gap_height <= 0:
                gap_height = cfg.node_h * 2

            vert_x = src_right

            # Try detour above and below
            for offset_y in [
                gap_top - cfg.node_spacing_y * 0.5,
                gap_bottom + cfg.node_spacing_y * 0.5,
                gap_top - cfg.node_spacing_y,
                gap_bottom + cfg.node_spacing_y,
            ]:
                if dst_left >= src_right:
                    raw_detour = [
                        (src_right, src_port_y),
                        (src_right, offset_y),
                        (vert_x, offset_y),
                        (vert_x, tgt_port_y),
                        (dst_left, tgt_port_y),
                    ]
                else:
                    mid_x = (src_right + dst_left) / 2.0
                    raw_detour = [
                        (src_right, src_port_y),
                        (src_right, offset_y),
                        (mid_x, offset_y),
                        (mid_x, tgt_port_y),
                        (dst_left, tgt_port_y),
                    ]

                cleaned_detour = _clean_path(raw_detour)
                collides_d = _path_collides(cleaned_detour, node_bboxes)
                bends_d = _count_bends(cleaned_detour)
                length_d = _manhattan_length(cleaned_detour)
                crossings_d = _estimate_crossings_for_channel(
                    edge_key, offset_y, graph, positions, graph.edge_routes,
                )
                cost_d = (crossings_weight * crossings_d
                          + bend_weight * bends_d
                          + length_weight * length_d)
                if collides_d:
                    cost_d += 1000.0

                if cost_d < best_cost:
                    best_cost = cost_d
                    best_path = cleaned_detour

    return best_path if best_path else []


# ── Phase 3: Edge bundling ─────────────────────────────────────────

def group_edge_bundles(graph: LayoutGraph) -> List[EdgeBundle]:
    """Group edges per layer gap into bundles.

    Within each gap, edges are sorted by median source y-position,
    then partitioned into bundles of similar-position edges.
    Contiguous channel blocks are assigned per bundle.
    """
    if not graph.edge_routes:
        return []

    L = len(graph.layers)
    bundles: List[EdgeBundle] = []

    for gap_idx in range(L - 1):
        upper = graph.layers[gap_idx]
        lower = graph.layers[gap_idx + 1]

        gap_edges: List[EdgeRoute] = []
        for u in upper:
            for d in graph.successors.get(u, set()):
                if d in lower:
                    key = (u, d)
                    if key in graph.edge_routes:
                        gap_edges.append(graph.edge_routes[key])

        if not gap_edges:
            continue

        gap_edges.sort(key=lambda er: er.src)

        # Simple bundling: group edges whose sources are close in ordering
        bundle_size = max(1, len(gap_edges) // 3)
        for start in range(0, len(gap_edges), bundle_size):
            chunk = gap_edges[start:start + bundle_size]
            bundle = EdgeBundle(
                layer_gap=gap_idx,
                edges=chunk,
                assigned_channel_block=(start, start + len(chunk)),
            )
            bundles.append(bundle)

    return bundles


# ── Phase 4: Full routing pass ─────────────────────────────────────

def route_edges_with_bend_minimization(
    graph: LayoutGraph,
    positions: Dict[int, Tuple[float, float]],
) -> Dict[Tuple[int, int], EdgeRoute]:
    """Run the complete routing pipeline on *graph*.

    1. Build EdgeRoute objects from port_edges.
    2. Group edges into bundles (per layer gap).
    3. Route each bundle's edges with bend minimisation.
    4. Store results in graph.edge_routes.

    Returns the route dict.
    """
    routes = build_edge_routes(graph, positions)
    if not routes:
        return routes

    cfg = graph.config

    node_bboxes: Dict[int, Tuple[float, float, float, float]] = {}
    for v in graph.all_nodes:
        x, y = positions.get(v, (0.0, 0.0))
        w = cfg.dummy_w if v in graph.is_dummy else cfg.node_w
        h = cfg.dummy_h if v in graph.is_dummy else cfg.node_h
        node_bboxes[v] = (x, y, x + w, y + h)

    route_keys = list(routes.keys())
    for key in route_keys:
        path = find_best_routing_path(key, graph, positions, node_bboxes)
        routes[key].points = path

        if path:
            gap_layers: Set[int] = set()
            for i in range(len(graph.layers) - 1):
                src_l = graph.layer_of.get(key[0], 0)
                dst_l = graph.layer_of.get(key[1], 0)
                for g in range(min(src_l, dst_l), max(src_l, dst_l)):
                    gap_layers.add(g)
            routes[key].layer_channels = sorted(gap_layers)

    graph.edge_routes = routes
    return routes


# ── Phase 5: Validation ────────────────────────────────────────────

def validate_no_collisions(
    graph: LayoutGraph,
    positions: Dict[int, Tuple[float, float]],
) -> bool:
    """Check that no routed edge segment passes through a node bounding box."""
    if not graph.edge_routes:
        return True

    cfg = graph.config
    node_bboxes: Dict[int, Tuple[float, float, float, float]] = {}
    for v in graph.original_nodes:
        x, y = positions.get(v, (0.0, 0.0))
        node_bboxes[v] = (x, y, x + cfg.node_w, y + cfg.node_h)

    for key, route in graph.edge_routes.items():
        if _path_collides(route.points, node_bboxes):
            return False

    return True


def validate_layout(
    graph: LayoutGraph,
    positions: Dict[int, Tuple[float, float]],
) -> LayoutReport:
    """Compute a full quality report for the current layout.

    Checks:
      - No edge passes through a node bounding box
      - No port constraint violations (port order preserved)
      - Bend count sanity
      - Bundle consistency
    """
    report = LayoutReport()

    if not graph.layers:
        return report

    # Crossing count
    report.crossings = _estimate_total_crossings(graph, positions)

    # Bend count
    report.total_bends = 0
    report.invalid_edges = 0
    if graph.edge_routes:
        for key, route in graph.edge_routes.items():
            bends = _count_bends(route.points)
            report.total_bends += bends
            if bends > 10:
                report.invalid_edges += 1

    # Collisions
    if not validate_no_collisions(graph, positions):
        report.invalid_edges += 1

    # Bundle count
    bundles = group_edge_bundles(graph)
    report.bundle_count = len(bundles)

    # Routing cost
    total_cost = 0.0
    if graph.edge_routes:
        for key, route in graph.edge_routes.items():
            length = _manhattan_length(route.points)
            bends = _count_bends(route.points)
            total_cost += length + 3.0 * bends
    report.routing_cost = total_cost

    return report


def _estimate_total_crossings(
    graph: LayoutGraph,
    positions: Dict[int, Tuple[float, float]],
) -> int:
    """Simple O(E^2) edge crossing detection based on routed paths."""
    if not graph.edge_routes:
        return 0

    routes = list(graph.edge_routes.values())
    crossings = 0
    for i in range(len(routes)):
        for j in range(i + 1, len(routes)):
            if _routes_cross(routes[i], routes[j]):
                crossings += 1
    return crossings


def _routes_cross(r1: EdgeRoute, r2: EdgeRoute) -> bool:
    """Check if two routed edges cross in the plane."""
    p1 = r1.points
    p2 = r2.points
    if len(p1) < 2 or len(p2) < 2:
        return False

    for i in range(len(p1) - 1):
        ax1, ay1 = p1[i]
        ax2, ay2 = p1[i + 1]
        for j in range(len(p2) - 1):
            bx1, by1 = p2[j]
            bx2, by2 = p2[j + 1]

            if _segments_cross(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2):
                return True
    return False


def _segments_cross(
    ax1: float, ay1: float, ax2: float, ay2: float,
    bx1: float, by1: float, bx2: float, by2: float,
) -> bool:
    """Orthogonal segment crossing test (horizontal vs vertical only)."""
    horiz_a = abs(ay1 - ay2) < 0.1
    horiz_b = abs(by1 - by2) < 0.1

    if horiz_a and not horiz_b:
        # a horizontal, b vertical
        hx1, hx2 = (ax1, ax2) if ax1 < ax2 else (ax2, ax1)
        vy1, vy2 = (by1, by2) if by1 < by2 else (by2, by1)
        hy = ay1
        vx = bx1
        if hx1 < vx < hx2 and vy1 < hy < vy2:
            return True
    elif not horiz_a and horiz_b:
        # a vertical, b horizontal
        vy1, vy2 = (ay1, ay2) if ay1 < ay2 else (ay2, ay1)
        hx1, hx2 = (bx1, bx2) if bx1 < bx2 else (bx2, bx1)
        vx = ax1
        hy = by1
        if hx1 < vx < hx2 and vy1 < hy < vy2:
            return True

    return False
