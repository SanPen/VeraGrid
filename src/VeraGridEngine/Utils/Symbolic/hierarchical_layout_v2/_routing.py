# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Orthogonal edge routing with exclusive channels and collision avoidance.

Port-aware: edge start/end points come from port positions on node
boundaries (LEFT / RIGHT) instead of node centre.

For each gap between adjacent layers, every edge gets its own dedicated
vertical channel.  Channels are evenly distributed across the available
height so no two edges share the same vertical segment.

Horizontal segments stay at port y-coordinates; vertical segments stay
in their assigned channel.  Collision detection verifies that no segment
passes through a node bounding box.
"""
from __future__ import annotations

from typing import Dict, List, Set, Tuple

from ._types import LayoutGraph
from ._ports import port_abs_position


def _segment_hits_bbox(
    x1: float, y1: float,
    x2: float, y2: float,
    bbox: Tuple[float, float, float, float],
) -> bool:
    l, t, r, b = bbox
    seg_l, seg_r = (x1, x2) if x1 < x2 else (x2, x1)
    seg_t, seg_b = (y1, y2) if y1 < y2 else (y2, y1)
    if seg_r <= l or seg_l >= r or seg_b <= t or seg_t >= b:
        return False
    return True


def _clean_path(path: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    if not path:
        return path
    cleaned = [path[0]]
    for pt in path[1:]:
        if pt != cleaned[-1]:
            cleaned.append(pt)
    return cleaned


def compute_edge_paths(
    graph: LayoutGraph,
    positions: Dict[int, Tuple[float, float]],
) -> Dict[Tuple[int, int], List[Tuple[float, float]]]:
    """
    Orthogonal edge routing using port positions.

    If *graph.port_edges* is populated, the start/end y-coordinates are
    taken from the port positions on the node boundaries.  Falls back to
    node-centre when port info is unavailable.
    """
    cfg = graph.config
    paths: Dict[Tuple[int, int], List[Tuple[float, float]]] = {}
    L = len(graph.layers)

    # Build port lookup for port_edges
    port_to_y: Dict[Tuple[int, int], float] = {}
    if graph.port_map and graph.port_edges:
        for src, sp, dst, dp in graph.port_edges:
            _, sy = port_abs_position(src, sp, positions, graph)
            port_to_y[(src, dst)] = sy

    node_bboxes: Dict[int, Tuple[float, float, float, float]] = {}
    for v in graph.original_nodes:
        w = cfg.node_w
        h = cfg.node_h
        x, y = positions.get(v, (0.0, 0.0))
        node_bboxes[v] = (x, y, x + w, y + h)

    for l in range(L - 1):
        upper = graph.layers[l]
        lower = graph.layers[l + 1]

        gap_edges: List[Tuple[int, int]] = []
        for u in upper:
            for d in graph.successors.get(u, set()):
                if d in lower:
                    gap_edges.append((u, d))

        if not gap_edges:
            continue

        # Vertical extent of this gap
        gap_top = float("inf")
        gap_bottom = float("-inf")
        for u in upper:
            _, t, _, b = node_bboxes.get(u, (0, 0, cfg.node_w, cfg.node_h))
            gap_top = min(gap_top, t)
            gap_bottom = max(gap_bottom, b)
        for d in lower:
            _, t, _, b = node_bboxes.get(d, (0, 0, cfg.node_w, cfg.node_h))
            gap_top = min(gap_top, t)
            gap_bottom = max(gap_bottom, b)

        # Fallback if no real nodes (dummy-only gap)
        if gap_top == float("inf"):
            gap_top = cfg.margin_y
            gap_bottom = cfg.margin_y + cfg.node_h * 4

        avail = gap_bottom - gap_top
        if avail <= 0:
            avail = cfg.node_h * 2

        # Sort edges by source port y (or node centre-y as fallback)
        sorted_edges: List[Tuple[int, int, float]] = []
        for src, tgt in gap_edges:
            port_y = port_to_y.get((src, tgt))
            if port_y is not None:
                src_y = port_y
            else:
                sx, sy = positions.get(src, (0.0, 0.0))
                src_y = sy + cfg.node_h / 2.0
            sorted_edges.append((src, tgt, src_y))
        sorted_edges.sort(key=lambda x: x[2])

        # Exclusive channels
        num = len(sorted_edges)
        pitch = avail / (num + 1)

        for idx, (src, tgt, _) in enumerate(sorted_edges):
            channel_y = gap_top + (idx + 1) * pitch

            # Source port position
            src_port_y = port_to_y.get((src, tgt))
            if src_port_y is not None:
                src_cy = src_port_y
            else:
                _, sy = positions.get(src, (0.0, 0.0))
                src_cy = sy + cfg.node_h / 2.0

            # Target port position
            tgt_port_y = None
            if graph.port_map and graph.port_edges:
                for s, sp, d, dp in graph.port_edges:
                    if s == tgt:
                        _, ty = port_abs_position(tgt, dp, positions, graph)
                        tgt_port_y = ty
                        break
            if tgt_port_y is not None:
                tgt_cy = tgt_port_y
            else:
                _, ty = positions.get(tgt, (0.0, 0.0))
                tgt_cy = ty + cfg.node_h / 2.0

            sx, sy = positions.get(src, (0.0, 0.0))
            src_right = sx + cfg.node_w

            tx, ty = positions.get(tgt, (0.0, 0.0))
            tgt_left = tx

            raw: List[Tuple[float, float]] = []

            if tgt_left >= src_right:
                raw = [
                    (src_right, src_cy),
                    (src_right, channel_y),
                    (tgt_left, channel_y),
                    (tgt_left, tgt_cy),
                ]
            else:
                mid_x = (src_right + tgt_left) / 2.0
                raw = [
                    (src_right, src_cy),
                    (src_right, channel_y),
                    (mid_x, channel_y),
                    (mid_x, tgt_cy),
                    (tgt_left, tgt_cy),
                ]

            path = _resolve_collisions(raw, node_bboxes)
            paths[(src, tgt)] = _clean_path(path)

    return paths


def _resolve_collisions(
    path: List[Tuple[float, float]],
    node_bboxes: Dict[int, Tuple[float, float, float, float]],
) -> List[Tuple[float, float]]:
    """
    If any segment collides with a node bbox, try shifting the
    vertical channel up/down in increments until clear.
    Falls back to original path if no clear channel found.
    """

    def _collides(p: List[Tuple[float, float]]) -> bool:
        for i in range(len(p) - 1):
            x1, y1 = p[i]
            x2, y2 = p[i + 1]
            for node_id, bbox in node_bboxes.items():
                if _segment_hits_bbox(x1, y1, x2, y2, bbox):
                    return True
        return False

    if not _collides(path):
        return path

    # Find the channel y (the vertical segment's y)
    channel_idx = -1
    for i in range(len(path) - 1):
        if abs(path[i][0] - path[i + 1][0]) < 0.01 and abs(path[i][1] - path[i + 1][1]) > 0.01:
            channel_idx = i
            break
    if channel_idx < 0:
        return path

    base_y = path[channel_idx][1]

    for direction in (1, -1):
        for step in range(1, 10):
            shift = base_y + direction * step * 20.0
            shifted = list(path)
            for i in range(len(shifted)):
                if abs(shifted[i][1] - base_y) < 0.01:
                    shifted[i] = (shifted[i][0], shift)
            if not _collides(shifted):
                return shifted

    return path
