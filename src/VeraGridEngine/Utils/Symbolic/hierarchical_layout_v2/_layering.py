"""
Phase 1: Longest-path layer assignment  (O(V + E))
Phase 2: Long-edge splitting via dummy nodes  (O(V + E))
"""
from __future__ import annotations

from collections import deque
from typing import Dict, List, Set

from ._types import LayoutConfig, LayoutGraph


def _topological_order(
    n: int,
    successors: Dict[int, Set[int]],
    predecessors: Dict[int, Set[int]],
) -> List[int]:
    in_degree = {i: len(predecessors.get(i, set())) for i in range(n)}
    queue = deque([i for i in range(n) if in_degree[i] == 0])
    order: List[int] = []
    temp_deg = dict(in_degree)
    while queue:
        node = queue.popleft()
        order.append(node)
        for succ in successors.get(node, set()):
            temp_deg[succ] -= 1
            if temp_deg[succ] == 0:
                queue.append(succ)
    remaining = set(range(n)) - set(order)
    order.extend(remaining)
    return order


def assign_layers(graph: LayoutGraph) -> List[List[int]]:
    """
    Longest-path layering with optional region-awareness bias.

    DAG constraint (hard):  layer[v] > layer[p] for every predecessor p.
    Region bias (soft):     if node is ahead of its region's median, push
                            it forward so the region stays more compact.

    Returns layers[layer_idx] = [node_ids...].  O(V + E)
    """
    n = graph.total_n
    order = _topological_order(n, graph.successors, graph.predecessors)

    has_regions = bool(graph.node_to_region and graph.regions)
    if has_regions:
        region_assignments: Dict[int, List[int]] = {
            rid: [] for rid in range(len(graph.regions))
        }

    SPREAD_ALLOWED = 2
    REGION_BIAS_MAX = 3

    layer_of: Dict[int, int] = {i: 0 for i in range(n)}
    for node in order:
        min_layer = 0
        for p in graph.predecessors.get(node, set()):
            min_layer = max(min_layer, layer_of.get(p, 0) + 1)

        layer = min_layer

        # Region cohesion bias: push node forward if it's far ahead of region
        if has_regions:
            rid = graph.node_to_region.get(node)
            if rid is not None:
                assigned = region_assignments[rid]
                if assigned:
                    sorted_layers = sorted(assigned)
                    median_layer = sorted_layers[len(sorted_layers) // 2]
                    if min_layer < median_layer - SPREAD_ALLOWED:
                        bias = min(
                            median_layer - min_layer - SPREAD_ALLOWED,
                            REGION_BIAS_MAX,
                        )
                        layer = min_layer + bias
                region_assignments[rid].append(layer)

        layer_of[node] = layer

    max_layer = max(layer_of.values()) if layer_of else 0
    layers: List[List[int]] = [[] for _ in range(max_layer + 1)]
    for node in range(n):
        layers[layer_of[node]].append(node)

    graph.layer_of = layer_of
    graph.layers = layers
    return layers


def split_long_edges(graph: LayoutGraph) -> None:
    """
    Insert dummy nodes for edges spanning >1 layer gap.

    After this, graph.total_n, graph.layers, graph.successors,
    graph.predecessors, graph.is_dummy, graph.original_of
    are all updated.

    O(V + E) amortised.

    Also assigns chain_of / chain_nodes so all dummy nodes belonging
    to the same long edge are grouped under one chain_id.
    """
    next_id = graph.total_n
    new_layers: List[List[int]] = [list(layer) for layer in graph.layers]
    chain_counter = 0

    for layer_idx in range(len(graph.layers) - 1, 0, -1):
        nodes_to_check = list(new_layers[layer_idx])
        for node in nodes_to_check:
            parents = list(graph.predecessors.get(node, set()))
            for parent in parents:
                p_layer = graph.layer_of[parent]
                gap = layer_idx - p_layer
                if gap <= 1:
                    continue

                # Remove direct edge parent -> node
                graph.successors[parent].discard(node)
                graph.predecessors[node].discard(parent)

                # Insert chain of dummy nodes, all sharing one chain_id
                chain_id = chain_counter
                chain_counter += 1
                chain_dummies: List[int] = []
                prev = parent
                for intermediate in range(1, gap):
                    dummy = next_id
                    next_id += 1
                    graph.is_dummy.add(dummy)
                    graph.original_of[dummy] = node
                    graph.chain_of[dummy] = chain_id
                    chain_dummies.append(dummy)
                    graph.layer_of[dummy] = p_layer + intermediate
                    graph.successors[prev].add(dummy)
                    graph.predecessors[dummy] = {prev}
                    graph.successors[dummy] = set()
                    new_layers[p_layer + intermediate].append(dummy)
                    prev = dummy

                graph.chain_nodes[chain_id] = chain_dummies
                graph.successors[prev].add(node)
                graph.predecessors[node].add(prev)

    graph.total_n = next_id
    graph.layers = new_layers
