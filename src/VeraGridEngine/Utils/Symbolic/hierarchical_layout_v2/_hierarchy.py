# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
ELK-style hierarchical layout — real structural region separation.

Replaces the old soft-penalty region approach with a true recursive
hierarchy where each region is laid out independently as a subgraph,
then assembled via a supergraph that treats regions as opaque nodes.

Pipeline for a multi-region component:
  1. For each region, run full Sugiyama on its *internal* edges only.
  2. Compute its bounding box from the internal layout.
  3. Build a supergraph where each region = one node (edge exists iff
     any inter-region edge exists between nodes of the two regions).
  4. Run full Sugiyama on the supergraph → supergraph positions.
  5. Combine:  final[node] = region_local[node] + super_pos[region_id]
  6. Assign ports to every node (top / bottom / left / right).
  7. Route inter-region edges through region boundary ports.

Regions are now STRUCTURAL blocks — no node from one region can ever
appear in the same layer as a node from another region.
"""
from __future__ import annotations

from typing import Dict, List, Set, Tuple

from ._types import LayoutConfig, LayoutGraph, make_graph
from ._coordinates import assign_coordinates
from ._layering import assign_layers, split_long_edges
from ._ordering import minimize_crossings
from ._ports import assign_ports, enforce_port_order_constraints
from ._routing_elk import route_edges_with_bend_minimization, validate_layout

# ── Helpers ────────────────────────────────────────────────────────

def extract_internal_subgraph(
    nodes: Set[int],
    dep_graph: Dict[int, Set[int]],
) -> Tuple[int, Dict[int, Set[int]], Dict[int, int]]:
    """Build sub-dep_graph containing only edges between *nodes*.

    Returns:
        sub_n:  number of nodes in the subgraph
        sub_dep:  dep_graph with indices remapped 0..sub_n-1
        old_to_new:  original index → new index
    """
    node_list = sorted(nodes)
    old_to_new = {old: i for i, old in enumerate(node_list)}
    sub_dep: Dict[int, Set[int]] = {old_to_new[v]: set() for v in node_list}
    for v in node_list:
        for p in dep_graph.get(v, set()):
            if p in nodes:
                sub_dep[old_to_new[v]].add(old_to_new[p])
    return len(nodes), sub_dep, old_to_new


def _sub_sugiyama(
    sub_n: int,
    sub_dep: Dict[int, Set[int]],
    config: LayoutConfig,
) -> Dict[int, Tuple[float, float]]:
    """Run the full flat Sugiyama pipeline on a subgraph (port-aware).

    Pipeline: assign_layers → assign_ports → minimize_crossings →
              split_long_edges → assign_coordinates →
              routing pipeline.

    Returns positions keyed by the *new* (remapped) node indices.
    """
    graph = make_graph(sub_n, sub_dep, config)
    assign_layers(graph)
    assign_ports(graph)
    minimize_crossings(graph)
    split_long_edges(graph)
    positions = assign_coordinates(graph)
    # Routing pipeline for subgraph
    enforce_port_order_constraints(graph)
    _ = validate_layout(graph, positions)
    route_edges_with_bend_minimization(graph, positions)
    return positions


def _compute_bbox(
    positions: Dict[int, Tuple[float, float]],
    config: LayoutConfig,
) -> Tuple[float, float, float, float]:
    """Return (min_x, min_y, max_x, max_y) accounting for node size."""
    if not positions:
        return 0.0, 0.0, config.node_w, config.node_h
    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    return min(xs), min(ys), max(xs) + config.node_w, max(ys) + config.node_h


def _build_supergraph_dep(
    regions: List[Set[int]],
    node_to_region: Dict[int, int],
    dep_graph: Dict[int, Set[int]],
) -> Dict[int, Set[int]]:
    """Build dep_graph for the supergraph (regions as nodes).

    super_dep[consumer_region] = {producer_regions}
    """
    R = len(regions)
    super_dep: Dict[int, Set[int]] = {i: set() for i in range(R)}
    seen: Set[Tuple[int, int]] = set()
    for consumer, producers in dep_graph.items():
        cr = node_to_region.get(consumer)
        if cr is not None:

            for producer in producers:
                pr = node_to_region.get(producer)
                if pr is not None and cr != pr:
                    key = (pr, cr)
                    if key not in seen:
                        seen.add(key)
                        super_dep[cr].add(pr)
    return super_dep


# ── Core hierarchical layout ───────────────────────────────────────

def _layout_regions(
    regions: List[Set[int]],
    dep_graph: Dict[int, Set[int]],
    config: LayoutConfig,
) -> Tuple[
    Dict[int, Dict[int, Tuple[float, float]]],
    Dict[int, Tuple[float, float, float, float]],
]:
    """Run internal Sugiyama on every region.

    Returns
        region_local[region_id][node] = (x, y)   local positions
        region_bboxes[region_id] = (lx, ly, rx, ry)   bounding boxes
    """
    region_local: Dict[int, Dict[int, Tuple[float, float]]] = {}
    region_bboxes: Dict[int, Tuple[float, float, float, float]] = {}

    for rid, region in enumerate(regions):
        if len(region) < 2:
            pos = {v: (config.margin_x, config.margin_y) for v in region}
            region_local[rid] = pos
            region_bboxes[rid] = (
                config.margin_x,
                config.margin_y,
                config.margin_x + config.node_w,
                config.margin_y + config.node_h,
            )
            continue

        sub_n, sub_dep, old_to_new = extract_internal_subgraph(region, dep_graph)
        sub_pos = _sub_sugiyama(sub_n, sub_dep, config)
        new_to_old = {v: k for k, v in old_to_new.items()}
        orig_pos = {new_to_old[v]: pos for v, pos in sub_pos.items()}

        for v in region:
            if v not in orig_pos:
                orig_pos[v] = (config.margin_x, config.margin_y)

        region_local[rid] = orig_pos
        region_bboxes[rid] = _compute_bbox(orig_pos, config)

    return region_local, region_bboxes


def _super_sugiyama(
    R: int,
    super_dep: Dict[int, Set[int]],
    region_bboxes: Dict[int, Tuple[float, float, float, float]],
    config: LayoutConfig,
) -> Dict[int, Tuple[float, float]]:
    """Run Sugiyama on the supergraph, placing region-sized nodes.

    The standard Sugiyama pipeline treats all nodes as equal-sized.
    Here we replace the coordinate-assignment step with one that
    accounts for each region's bounding box, so that the output
    positions can be used as direct offsets for the sub-layouts.

    Returns
        super_positions[region_id] = (x, y)  top‑left corner of the
            region's bounding box in the global layout.
    """
    graph = make_graph(R, super_dep, config)
    assign_layers(graph)
    split_long_edges(graph)
    minimize_crossings(graph)

    layers = graph.layers
    gap_x = config.layer_spacing_x * 2.5
    gap_y = config.node_spacing_y * 3.0

    # Column widths = widest region per layer
    col_widths: List[float] = []
    for layer in layers:
        max_w = 0.0
        for v in layer:
            if v in region_bboxes:
                bbox = region_bboxes[v]
                max_w = max(max_w, bbox[2] - bbox[0])
        col_widths.append(max(max_w, config.node_w))

    pos: Dict[int, Tuple[float, float]] = {}
    cx = config.margin_x
    for l_idx, layer in enumerate(layers):
        cy = config.margin_y
        for v in layer:
            bbox = region_bboxes.get(v, (0.0, 0.0, config.node_w, config.node_h))
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            pos[v] = (cx + (col_widths[l_idx] - w) / 2.0, cy)
            cy += h + gap_y
        cx += col_widths[l_idx] + gap_x

    return pos


def _combine_positions(
    region_local: Dict[int, Dict[int, Tuple[float, float]]],
    region_bboxes: Dict[int, Tuple[float, float, float, float]],
    super_positions: Dict[int, Tuple[float, float]],
    config: LayoutConfig,
) -> Dict[int, Tuple[float, float]]:
    """Offset each region's local positions by its supergraph placement.

    A small padding is added around each region for visual separation.
    """
    pad = config.node_spacing_y * 0.5
    result: Dict[int, Tuple[float, float]] = {}

    for rid, local_pos in region_local.items():
        if rid in super_positions:
            sx, sy = super_positions[rid]
            bbox = region_bboxes.get(rid, (0.0, 0.0, config.node_w, config.node_h))
            dx = sx - bbox[0] + pad
            dy = sy - bbox[1] + pad
            for v, (lx, ly) in local_pos.items():
                result[v] = (lx + dx, ly + dy)

    return result


# ── Public API ─────────────────────────────────────────────────────

def layout_hierarchical(
    n: int,
    dep_graph: Dict[int, Set[int]],
    regions: List[Set[int]],
    node_to_region: Dict[int, int],
    config: LayoutConfig | None = None,
) -> Dict[int, Tuple[float, float]]:
    """Full ELK-style hierarchical layout for a multi-region component.

    Parameters
    ----------
    n:
        Number of nodes in the component.
    dep_graph:
        dep_graph[consumer] = {producers}  (full component graph).
    regions:
        List of disjoint node sets covering 0..n-1.
    node_to_region:
        node → region_id
    config:
        Layout parameters.

    Returns
    -------
    positions[node] = (x, y)  top‑left corner.
    """
    if config is None:
        config = LayoutConfig()

    # Step 1 — layout each region independently
    region_local, region_bboxes = _layout_regions(regions, dep_graph, config)

    # Step 2 — build and layout supergraph
    R = len(regions)
    if R > 1:
        super_dep = _build_supergraph_dep(regions, node_to_region, dep_graph)
        super_positions = _super_sugiyama(R, super_dep, region_bboxes, config)
    else:
        super_positions = {0: (0.0, 0.0)}

    # Step 3 — combine
    result = _combine_positions(
        region_local, region_bboxes, super_positions, config,
    )

    # Safety net: any unplaced node gets a fallback position
    for v in range(n):
        if v not in result:
            result[v] = (config.margin_x, config.margin_y)

    return result
