"""
Fase 9: Quality metrics for layout comparison.

Computes objective measures to compare different layout outputs.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple


@dataclass
class LayoutMetrics:
    crossings: int = 0
    total_edge_length: float = 0.0
    avg_edge_length: float = 0.0
    max_edge_length: float = 0.0
    area: float = 0.0
    density: float = 0.0
    overlaps: int = 0
    num_components: int = 0
    num_nodes: int = 0
    num_edges: int = 0

    def summary(self) -> str:
        return (
            f"Crossings={self.crossings}, "
            f"AvgEdgeLen={self.avg_edge_length:.1f}, "
            f"Area={self.area:.0f}, "
            f"Density={self.density:.4f}, "
            f"Overlaps={self.overlaps}"
        )


def compute_metrics(
    n: int,
    dep_graph: Dict[int, Set[int]],
    positions: Dict[int, Tuple[float, float]],
    node_w: float = 160.0,
    node_h: float = 70.0,
    components: List[Set[int]] | None = None,
) -> LayoutMetrics:
    metrics = LayoutMetrics()

    if not positions:
        return metrics

    metrics.num_nodes = n
    metrics.num_components = len(components) if components else 1

    # Count edges
    edge_count = 0
    for consumer, producers in dep_graph.items():
        edge_count += len(producers)
    metrics.num_edges = edge_count

    # Crossing count
    metrics.crossings = _count_crossings(dep_graph, positions)

    # Edge length
    total_len = 0.0
    max_len = 0.0
    for consumer, producers in dep_graph.items():
        if consumer not in positions:
            continue
        cx, cy = positions[consumer]
        cx += node_w / 2.0
        cy += node_h / 2.0
        for producer in producers:
            if producer not in positions:
                continue
            px, py = positions[producer]
            px += node_w / 2.0
            py += node_h / 2.0
            length = abs(cx - px) + abs(cy - py)
            total_len += length
            max_len = max(max_len, length)

    metrics.total_edge_length = total_len
    metrics.avg_edge_length = total_len / max(edge_count, 1)
    metrics.max_edge_length = max_len

    # Area
    xs = [p[0] for p in positions.values()] + [p[0] + node_w for p in positions.values()]
    ys = [p[1] for p in positions.values()] + [p[1] + node_h for p in positions.values()]
    if xs and ys:
        width = max(xs) - min(xs) + 1
        height = max(ys) - min(ys) + 1
        metrics.area = width * height

        # Density: nodes * node_area / total_area
        total_node_area = n * node_w * node_h
        metrics.density = total_node_area / metrics.area if metrics.area > 0 else 0.0

    # Overlap detection
    metrics.overlaps = _count_overlaps(positions, node_w, node_h)

    return metrics


def _count_crossings(
    dep_graph: Dict[int, Set[int]],
    positions: Dict[int, Tuple[float, float]],
) -> int:
    """Simple crossing count: O(E^2) but fine for moderate graphs."""
    edges: List[Tuple[int, int, float, float, float, float]] = []
    for consumer, producers in dep_graph.items():
        if consumer not in positions:
            continue
        cx, cy = positions[consumer]
        for producer in producers:
            if producer not in positions:
                continue
            px, py = positions[producer]
            edges.append((producer, consumer, px, py, cx, cy))

    crossings = 0
    for i in range(len(edges)):
        a_src, a_dst, ax1, ay1, ax2, ay2 = edges[i]
        if abs(ay2 - ay1) < 1:
            continue
        for j in range(i + 1, len(edges)):
            b_src, b_dst, bx1, by1, bx2, by2 = edges[j]
            if abs(by2 - by1) < 1:
                continue

            # Check if segments cross
            a_low_y, a_high_y = min(ay1, ay2), max(ay1, ay2)
            b_low_y, b_high_y = min(by1, by2), max(by1, by2)

            a_left_x, a_right_x = min(ax1, ax2), max(ax1, ax2)
            b_left_x, b_right_x = min(bx1, bx2), max(bx1, bx2)

            # Simple crossing test for orthogonal L-shaped edges
            if ax1 != bx1 and ax2 != bx2:
                if a_low_y < b_low_y < a_high_y and b_left_x < a_left_x < b_right_x:
                    crossings += 1
                elif b_low_y < a_low_y < b_high_y and a_left_x < b_left_x < a_right_x:
                    crossings += 1

    return crossings


def compute_region_edge_ratio(
    dep_graph: Dict[int, Set[int]],
    regions: List[Set[int]],
) -> float:
    """
    Region edge ratio = internal_edges / (internal_edges + external_edges).

    A high ratio means regions are well-separated (few cross-region edges).
    Ratio is 1.0 when there are 0 or 1 regions.
    """
    if len(regions) <= 1:
        return 1.0

    node_to_region: Dict[int, int] = {}
    for rid, reg in enumerate(regions):
        for v in reg:
            node_to_region[v] = rid

    internal = 0
    external = 0
    for consumer, producers in dep_graph.items():
        for producer in producers:
            if node_to_region.get(consumer) == node_to_region.get(producer):
                internal += 1
            else:
                external += 1

    total = internal + external
    return internal / total if total > 0 else 1.0


def compute_region_cohesion(
    layers: List[List[int]],
    node_to_region: Dict[int, int],
    regions: List[Set[int]],
) -> Tuple[float, int]:
    """
    Region cohesion score based on layer assignments.

    For each region, computes the layer span (max_layer - min_layer)
    among its nodes.  Returns (avg_span, max_span).

    Lower values = better cohesion (region nodes stay in nearby layers).
    """
    if len(regions) <= 1:
        return 0.0, 0

    layer_of: Dict[int, int] = {}
    for l_idx, layer in enumerate(layers):
        for v in layer:
            layer_of[v] = l_idx

    spans: List[int] = []
    for region in regions:
        if len(region) <= 1:
            continue
        region_layers = [layer_of[v] for v in region if v in layer_of]
        if not region_layers:
            continue
        span = max(region_layers) - min(region_layers)
        spans.append(span)

    if not spans:
        return 0.0, 0

    avg = sum(spans) / len(spans)
    max_span = max(spans)
    return avg, max_span


def _count_overlaps(
    positions: Dict[int, Tuple[float, float]],
    w: float,
    h: float,
) -> int:
    nodes = list(positions.keys())
    overlaps = 0
    for i in range(len(nodes)):
        xi, yi = positions[nodes[i]]
        for j in range(i + 1, len(nodes)):
            xj, yj = positions[nodes[j]]
            if not (xi + w <= xj or xj + w <= xi or yi + h <= yj or yj + h <= yi):
                overlaps += 1
    return overlaps
