# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Phase 3: Crossing minimization via barycenter + median + transpose.
         Port-aware: uses port y-positions for finer ordering granularity.

O(K * L * V^2) where K is sweeps, L is layers, V is nodes per layer.
"""
from __future__ import annotations

from typing import Dict, List, Set, Tuple

from ._types import LayoutConfig, LayoutGraph
from ._ports import port_normalized_position, LEFT, RIGHT


def _region_spread_penalty(
    layer: List[int],
    node_to_region: Dict[int, int],
) -> float:
    """Quadratic penalty for how spread out each region is within a layer.

    For each region with ≥2 nodes in this layer, sum the squared gap
    between consecutive region-mates.  This penalises large gaps much
    more than small ones, encouraging compact region blocks.
    """
    if not node_to_region:
        return 0.0
    penalty = 0.0
    region_positions: Dict[int, List[int]] = {}
    for pos, node in enumerate(layer):
        rid = node_to_region.get(node, -1)
        if rid >= 0:
            region_positions.setdefault(rid, []).append(pos)
    for positions in region_positions.values():
        if len(positions) <= 1:
            continue
        for i in range(len(positions) - 1):
            gap = positions[i + 1] - positions[i] - 1
            penalty += gap * gap
    return penalty



def _crossings_between(
    upper: List[int],
    lower: List[int],
    successors: Dict[int, Set[int]],
) -> int:
    lower_pos = {n: i for i, n in enumerate(lower)}
    cnt = 0
    for i, u in enumerate(upper):
        u_conn = [v for v in successors.get(u, set()) if v in lower_pos]
        if not u_conn:
            continue
        for w in upper[i + 1:]:
            w_conn = [v for v in successors.get(w, set()) if v in lower_pos]
            if not w_conn:
                continue
            for a in u_conn:
                pa = lower_pos[a]
                for b in w_conn:
                    if lower_pos[b] < pa:
                        cnt += 1
    return cnt


def _total_crossings(
    layers: List[List[int]],
    successors: Dict[int, Set[int]],
) -> int:
    return sum(
        _crossings_between(layers[i], layers[i + 1], successors)
        for i in range(len(layers) - 1)
    )


def _port_offset(
    neighbor: int,
    node: int,
    port_map: Dict[int, List[Tuple[str, float, int]]] | None,
    side: str,
    pitch_y: float,
    node_h: float,
) -> float:
    """Fractional y-offset [0, 1) from the port on *neighbor* that connects to *node*.

    This refines the integer layer-position index with sub-node precision.
    Returns 0 when port_map is unavailable.
    """
    if not port_map:
        return 0.0
    ports = port_map.get(neighbor, [])
    for p in ports:
        if p[0] == side:
            return p[1] * node_h / pitch_y
    return 0.0


def _parent_barycenter(
    layers: List[List[int]],
    target_layer: int,
    successors: Dict[int, Set[int]],
    predecessors: Dict[int, Set[int]],
    port_map: Dict[int, List[Tuple[str, float, int]]] | None = None,
    pitch_y: float = 190.0,
    node_h: float = 70.0,
) -> None:
    if target_layer == 0:
        return
    items = layers[target_layer]
    prev = layers[target_layer - 1]
    prev_pos = {n: i for i, n in enumerate(prev)}
    scored: List[Tuple[float, int]] = []
    for node in items:
        parents = [p for p in predecessors.get(node, set()) if p in prev_pos]
        if parents:
            total = 0.0
            for p in parents:
                base = prev_pos[p]
                frac = _port_offset(p, node, port_map, RIGHT, pitch_y, node_h)
                total += base + frac
            avg = total / len(parents)
            scored.append((avg, node))
        else:
            scored.append((float(len(prev)), node))
    scored.sort(key=lambda x: (x[0], x[1]))
    layers[target_layer] = [n for _, n in scored]


def _child_barycenter(
    layers: List[List[int]],
    target_layer: int,
    successors: Dict[int, Set[int]],
    predecessors: Dict[int, Set[int]],
    port_map: Dict[int, List[Tuple[str, float, int]]] | None = None,
    pitch_y: float = 190.0,
    node_h: float = 70.0,
) -> None:
    if target_layer >= len(layers) - 1:
        return
    items = layers[target_layer]
    nxt = layers[target_layer + 1]
    nxt_pos = {n: i for i, n in enumerate(nxt)}
    scored: List[Tuple[float, int]] = []
    for node in items:
        children_v = [c for c in successors.get(node, set()) if c in nxt_pos]
        if children_v:
            total = 0.0
            for c in children_v:
                base = nxt_pos[c]
                frac = _port_offset(c, node, port_map, LEFT, pitch_y, node_h)
                total += base + frac
            avg = total / len(children_v)
            scored.append((avg, node))
        else:
            scored.append((float(len(nxt)), node))
    scored.sort(key=lambda x: (x[0], x[1]))
    layers[target_layer] = [n for _, n in scored]


def _parent_median(
    layers: List[List[int]],
    target_layer: int,
    successors: Dict[int, Set[int]],
    predecessors: Dict[int, Set[int]],
    port_map: Dict[int, List[Tuple[str, float, int]]] | None = None,
    pitch_y: float = 190.0,
    node_h: float = 70.0,
) -> None:
    if target_layer == 0:
        return
    items = layers[target_layer]
    prev = layers[target_layer - 1]
    prev_pos = {n: i for i, n in enumerate(prev)}
    scored: List[Tuple[float, int]] = []
    for node in items:
        parents = [p for p in predecessors.get(node, set()) if p in prev_pos]
        positions = sorted([
            prev_pos[p] + _port_offset(p, node, port_map, RIGHT, pitch_y, node_h)
            for p in parents
        ])
        if positions:
            m = len(positions)
            med = float(positions[m // 2]) if m % 2 == 1 else (positions[m // 2 - 1] + positions[m // 2]) / 2.0
        else:
            med = float('inf')
        scored.append((med, node))
    scored.sort(key=lambda x: (x[0], x[1]))
    layers[target_layer] = [n for _, n in scored]


def _transpose(
    layers: List[List[int]],
    successors: Dict[int, Set[int]],
    node_to_region: Dict[int, int] | None = None,
) -> bool:
    improved = False
    for l_idx in range(len(layers)):
        items = layers[l_idx]
        i = 0
        while i < len(items) - 1:
            before = _total_crossings(layers, successors)
            spread_before = _region_spread_penalty(items, node_to_region or {})

            items[i], items[i + 1] = items[i + 1], items[i]

            after = _total_crossings(layers, successors)
            spread_after = _region_spread_penalty(items, node_to_region or {})

            accept = False
            if after < before:
                accept = True  # fewer crossings → always accept
            elif after == before and spread_after < spread_before:
                accept = True  # same crossings, better region cohesion → accept

            if accept:
                improved = True
            else:
                items[i], items[i + 1] = items[i + 1], items[i]
            i += 1
    return improved


def _region_stabilize(
    layers: List[List[int]],
    successors: Dict[int, Set[int]],
    node_to_region: Dict[int, int],
) -> None:
    """
    Within each layer, group consecutive nodes of the same region
    together (stable sort by region ID) if it does not increase crossings
    with the previous layer.

    This is a light post-process that makes region blocks more compact
    without regressing the crossing count.
    """
    if not node_to_region:
        return
    for l_idx in range(len(layers)):
        layer = layers[l_idx]

        # Group nodes by region while preserving relative order within each region
        region_buckets: Dict[int, List[int]] = {}
        region_order: List[int] = []
        seen = set()
        for node in layer:
            rid = node_to_region.get(node, -1)
            if rid not in region_buckets:
                region_buckets[rid] = []
                region_order.append(rid)
            region_buckets[rid].append(node)

        if len(region_buckets) <= 1:
            continue

        # Build candidate: all nodes of each region in a contiguous block
        candidate: List[int] = []
        for rid in region_order:
            candidate.extend(region_buckets[rid])

        # Accept candidate if it does not increase crossings
        if l_idx > 0:
            before = _crossings_between(layers[l_idx - 1], layer, successors)
            after = _crossings_between(layers[l_idx - 1], candidate, successors)
            if after <= before:
                layers[l_idx] = candidate
        else:
            layers[l_idx] = candidate


def minimize_crossings(
    graph: LayoutGraph,
    barycenter_sweeps: int = 6,
    median_sweeps: int = 18,
    transpose_passes: int = 20,
) -> None:
    """
    Run median-heavy crossing minimisation with port-awareness and
    region-awareness.

    For Simulink-style diagrams, median tends to outperform barycenter
    because it's less sensitive to fan-out: a node with many parents
    in the same layer gets a stable position at the median parent,
    rather than being pulled toward the barycenter (which can drift
    as fan-out grows).

    Barycenter is kept for a few initial sweeps (coarse positioning),
    then median takes over for fine-grained ordering.

    When *graph.port_map* is populated, the barycenter/median functions
    use port y-positions to refine ordering with sub-node precision.

    When *graph.node_to_region* is populated, the transpose phase also
    considers region spread: swaps that reduce crossings OR maintain
    crossings while improving region cohesion are accepted.
    A final :func:`_region_stabilize` pass groups region-mates together.
    """
    node_to_region = graph.node_to_region or {}
    port_map = graph.port_map
    pitch_y = graph.config.node_h + graph.config.node_spacing_y
    node_h = graph.config.node_h
    L = len(graph.layers)

    for sweep in range(barycenter_sweeps):
        if sweep % 2 == 0:
            for l in range(1, L):
                _parent_barycenter(
                    graph.layers, l, graph.successors, graph.predecessors,
                    port_map, pitch_y, node_h,
                )
        else:
            for l in range(L - 2, -1, -1):
                _child_barycenter(
                    graph.layers, l, graph.successors, graph.predecessors,
                    port_map, pitch_y, node_h,
                )

    for sweep in range(median_sweeps):
        for l in range(1, L):
            _parent_median(
                graph.layers, l, graph.successors, graph.predecessors,
                port_map, pitch_y, node_h,
            )

    for _ in range(transpose_passes):
        if not _transpose(graph.layers, graph.successors, node_to_region):
            break

    # Final region-grouping pass (does not increase crossings)
    if node_to_region:
        _region_stabilize(graph.layers, graph.successors, node_to_region)
