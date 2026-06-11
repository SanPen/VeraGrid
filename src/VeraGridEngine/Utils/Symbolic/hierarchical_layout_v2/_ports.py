"""
Port system — ELK-style port-aware edges.

Each edge becomes (source_node, source_port) → (target_node, target_port).

Ports are assigned based on:
  - Degree (in-degree → LEFT ports, out-degree → RIGHT ports)
  - Barycenter ordering of neighbors (minimises artificial crossings)
  - Region grouping (edges grouped by region for compactness)

┌─────────────────┐
│                 │
│  LEFT (inputs)  │    RIGHT (outputs)
│  port 0  ← p0   │    port 0  → s0
│  port 1  ← p1   │    port 1  → s1
│  port 2  ← p2   │    port 2  → s2
│                 │
└─────────────────┘

Port positions are normalised [0, 1] along the side:
  - LEFT / RIGHT   → vertical offset from top   (0 = top, 1 = bottom)
  - TOP  / BOTTOM  → horizontal offset from left (0 = left, 1 = right)
"""
from __future__ import annotations

from typing import Dict, List, Set, Tuple

from ._types import LayoutGraph

# ── Side constants ─────────────────────────────────────────────────
LEFT = "left"
RIGHT = "right"
TOP = "top"
BOTTOM = "bottom"


# ── Helpers ────────────────────────────────────────────────────────

def _layer_order_of(
    node: int,
    layers: List[List[int]],
) -> Tuple[int, int] | None:
    """Return (layer_idx, order_idx) or None if node not in layers."""
    for l_idx, layer in enumerate(layers):
        for order, v in enumerate(layer):
            if v == node:
                return l_idx, order
    return None


def _sort_neighbors(
    neighbors: List[int],
    graph: LayoutGraph,
    is_predecessor: bool,
) -> List[int]:
    """Sort neighbours by barycenter position within the layering.

    Ties are broken by node id for determinism.
    """
    if len(neighbors) <= 1:
        return sorted(neighbors)

    layers = graph.layers
    if not layers:
        return sorted(neighbors)

    def _bary(nb: int) -> float:
        if is_predecessor:
            # barycenter of nb's successors (children) in the layering
            succs = graph.successors.get(nb, set())
            positions = []
            for s in succs:
                pos = _layer_order_of(s, layers)
                if pos is not None:
                    positions.append(pos[1])  # order within layer
            return sum(positions) / len(positions) if positions else float("inf")
        else:
            # barycenter of nb's predecessors (parents) in the layering
            preds = graph.predecessors.get(nb, set())
            positions = []
            for p in preds:
                pos = _layer_order_of(p, layers)
                if pos is not None:
                    positions.append(pos[1])
            return sum(positions) / len(positions) if positions else float("inf")

    scored = sorted(
        [(_bary(nb), nb) for nb in neighbors],
        key=lambda x: (x[0], x[1]),
    )
    return [nb for _, nb in scored]


def _group_by_region(
    sorted_nodes: List[int],
    node_to_region: Dict[int, int],
) -> List[int]:
    """Group nodes by region, preserving within-region barycenter order."""
    if not node_to_region:
        return sorted_nodes
    buckets: Dict[int, List[int]] = {}
    for v in sorted_nodes:
        rid = node_to_region.get(v, -1)
        buckets.setdefault(rid, []).append(v)
    result: List[int] = []
    for rid in sorted(buckets):
        result.extend(buckets[rid])
    return result


# ── Port assignment ────────────────────────────────────────────────

def assign_ports(graph: LayoutGraph) -> None:
    """Full ELK-style port assignment on *graph*.

    Operates in-place on ``graph.port_map`` and ``graph.port_edges``.

    Pipeline
    --------
    1. For each node, collect predecessors and successors.
    2. Sort each list by barycenter (uses existing layering).
    3. If ``graph.node_to_region`` is set, group by region (block order).
    4. Assign LEFT ports (one per predecessor, uniform spacing).
    5. Assign RIGHT ports (one per successor, uniform spacing).
    6. Build ``graph.port_edges``: ``(src, src_port_id, dst, dst_port_id)``.
    """
    n = graph.original_n
    node_to_region = graph.node_to_region or {}
    port_map: Dict[int, List[Tuple[str, float, int]]] = {}
    port_counter = 0

    for v in range(n):
        preds = _sort_neighbors(
            list(graph.predecessors.get(v, set())), graph, is_predecessor=True,
        )
        succs = _sort_neighbors(
            list(graph.successors.get(v, set())), graph, is_predecessor=False,
        )

        if node_to_region:
            preds = _group_by_region(preds, node_to_region)
            succs = _group_by_region(succs, node_to_region)

        ports: List[Tuple[str, float, int]] = []

        # LEFT ports (inputs) — one per predecessor
        k_in = len(preds)
        for i in range(k_in):
            pos = (i + 1) / (k_in + 1) if k_in > 0 else 0.5
            ports.append((LEFT, pos, port_counter))
            port_counter += 1

        # RIGHT ports (outputs) — one per successor
        k_out = len(succs)
        for i in range(k_out):
            pos = (i + 1) / (k_out + 1) if k_out > 0 else 0.5
            ports.append((RIGHT, pos, port_counter))
            port_counter += 1

        port_map[v] = ports

    graph.port_map = port_map

    # ── Build port_edges ────────────────────────────────────────
    # Map (src, dst) → index of dst in src's ordered successors
    succ_index: Dict[Tuple[int, int], int] = {}
    pred_index: Dict[Tuple[int, int], int] = {}

    for v in range(n):
        succs = _sort_neighbors(
            list(graph.successors.get(v, set())), graph, is_predecessor=False,
        )
        if node_to_region:
            succs = _group_by_region(succs, node_to_region)
        for idx, s in enumerate(succs):
            succ_index[(v, s)] = idx

    for v in range(n):
        preds = _sort_neighbors(
            list(graph.predecessors.get(v, set())), graph, is_predecessor=True,
        )
        if node_to_region:
            preds = _group_by_region(preds, node_to_region)
        for idx, p in enumerate(preds):
            pred_index[(v, p)] = idx

    port_edges: List[Tuple[int, int, int, int]] = []
    for v in range(n):
        for s in graph.successors.get(v, set()):
            right_ports = [p for p in port_map.get(v, []) if p[0] == RIGHT]
            left_ports = [p for p in port_map.get(s, []) if p[0] == LEFT]
            r_idx = succ_index.get((v, s), 0)
            l_idx = pred_index.get((s, v), 0)
            if r_idx < len(right_ports) and l_idx < len(left_ports):
                port_edges.append((v, right_ports[r_idx][2], s, left_ports[l_idx][2]))

    graph.port_edges = port_edges


# ── Port coordinate helpers ────────────────────────────────────────

def port_abs_position(
    node: int,
    port_id: int,
    positions: Dict[int, Tuple[float, float]],
    graph: LayoutGraph,
) -> Tuple[float, float]:
    """Absolute (x, y) of a port on the node boundary."""
    if not graph.port_map:
        x, y = positions.get(node, (0.0, 0.0))
        return (x + graph.config.node_w / 2.0, y + graph.config.node_h / 2.0)

    ports = graph.port_map.get(node, [])
    info: Tuple[str, float, int] | None = None
    for p in ports:
        if p[2] == port_id:
            info = p
            break
    if info is None:
        x, y = positions.get(node, (0.0, 0.0))
        return (x + graph.config.node_w / 2.0, y + graph.config.node_h / 2.0)

    side, norm, _ = info
    nx, ny = positions.get(node, (0.0, 0.0))
    w = graph.config.node_w
    h = graph.config.node_h

    if side == LEFT:
        return (nx, ny + norm * h)
    elif side == RIGHT:
        return (nx + w, ny + norm * h)
    elif side == TOP:
        return (nx + norm * w, ny)
    elif side == BOTTOM:
        return (nx + norm * w, ny + h)
    return (nx + w / 2.0, ny + h / 2.0)


def port_normalized_position(
    node: int,
    port_id: int,
    graph: LayoutGraph,
) -> Tuple[str, float]:
    """Return (side, normalised_position) for a port."""
    ports = graph.port_map.get(node, [])
    for p in ports:
        if p[2] == port_id:
            return (p[0], p[1])
    return (RIGHT, 0.5)


# ── Port constraint enforcement ────────────────────────────────────

def enforce_port_order_constraints(graph: LayoutGraph) -> None:
    """Reconcile port_map ordering with final crossing-minimised layering.

    After crossing minimisation the order of nodes within each layer may
    have changed.  Ports must be re-ordered to match:
      - RIGHT ports (outputs) are ordered top-to-bottom in the same
        order as their target nodes appear in the next layer.
      - LEFT ports (inputs) are ordered top-to-bottom in the same order
        as their source nodes appear in the previous layer.

    This function rebuilds graph.port_map and graph.port_edges to
    enforce these constraints without changing node positions.

    Operates in-place.
    """
    if not graph.port_map or not graph.layers:
        return

    layer_of = graph.layer_of
    layers = graph.layers
    n = graph.original_n
    port_counter = 0
    new_port_map: Dict[int, List[Tuple[str, float, int]]] = {}

    for v in range(n):
        v_layer = layer_of.get(v, 0)
        ports = []

        # LEFT ports: order by predecessor position in previous layer
        preds = [p for p in graph.predecessors.get(v, set()) if p < n]
        if v_layer > 0 and preds:
            prev_layer = layers[v_layer - 1]
            prev_pos = {node: i for i, node in enumerate(prev_layer)}
            preds_sorted = sorted(preds, key=lambda p: prev_pos.get(p, 0))
        else:
            preds_sorted = sorted(preds)

        k_in = len(preds_sorted)
        for i in range(k_in):
            pos = (i + 1) / (k_in + 1) if k_in > 0 else 0.5
            ports.append((LEFT, pos, port_counter))
            port_counter += 1

        # RIGHT ports: order by successor position in next layer
        succs = [s for s in graph.successors.get(v, set()) if s < n]
        if v_layer < len(layers) - 1 and succs:
            next_layer = layers[v_layer + 1]
            next_pos = {node: i for i, node in enumerate(next_layer)}
            succs_sorted = sorted(succs, key=lambda s: next_pos.get(s, 0))
        else:
            succs_sorted = sorted(succs)

        k_out = len(succs_sorted)
        for i in range(k_out):
            pos = (i + 1) / (k_out + 1) if k_out > 0 else 0.5
            ports.append((RIGHT, pos, port_counter))
            port_counter += 1

        new_port_map[v] = ports

    # Rebuild port_edges from the new ordering
    pred_index: Dict[Tuple[int, int], int] = {}
    succ_index: Dict[Tuple[int, int], int] = {}

    for v in range(n):
        preds = list(graph.predecessors.get(v, set()))
        preds_ord = [p for p in preds if p < n]
        v_layer = layer_of.get(v, 0)
        if v_layer > 0 and preds_ord:
            prev_layer = layers[v_layer - 1]
            prev_pos = {node: i for i, node in enumerate(prev_layer)}
            preds_ord.sort(key=lambda p: prev_pos.get(p, 0))
        for idx, p in enumerate(preds_ord):
            pred_index[(v, p)] = idx

        succs = list(graph.successors.get(v, set()))
        succs_ord = [s for s in succs if s < n]
        if v_layer < len(layers) - 1 and succs_ord:
            next_layer = layers[v_layer + 1]
            next_pos = {node: i for i, node in enumerate(next_layer)}
            succs_ord.sort(key=lambda s: next_pos.get(s, 0))
        for idx, s in enumerate(succs_ord):
            succ_index[(v, s)] = idx

    new_port_edges: List[Tuple[int, int, int, int]] = []
    for v in range(n):
        for s in graph.successors.get(v, set()):
            if s >= n:
                continue
            right_ports = [p for p in new_port_map.get(v, []) if p[0] == RIGHT]
            left_ports = [p for p in new_port_map.get(s, []) if p[0] == LEFT]
            r_idx = succ_index.get((v, s), 0)
            l_idx = pred_index.get((s, v), 0)
            if r_idx < len(right_ports) and l_idx < len(left_ports):
                new_port_edges.append((v, right_ports[r_idx][2], s, left_ports[l_idx][2]))

    graph.port_map = new_port_map
    graph.port_edges = new_port_edges
