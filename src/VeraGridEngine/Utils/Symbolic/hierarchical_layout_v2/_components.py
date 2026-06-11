"""
Fase 1: Connected component detection.
Fase 1b: Region (cluster) detection within a component.

Component detection: O(V + E) con DFS.
Region detection: O(I * V * deg) via label propagation.

Also provides the subgraph extraction helpers used by the main pipeline.
"""
from __future__ import annotations

from typing import Dict, List, Set, Tuple

from ._types import LayoutGraph


def _count_cross_edges(
    a: Set[int],
    b: Set[int],
    dep_graph: Dict[int, Set[int]],
) -> int:
    """Number of directed edges between sets A and B (undirected count)."""
    count = 0
    for consumer, producers in dep_graph.items():
        for producer in producers:
            if (consumer in a and producer in b) or (consumer in b and producer in a):
                count += 1
    return count


def detect_regions(
    n: int,
    dep_graph: Dict[int, Set[int]],
    max_iterations: int = 10,
) -> List[Set[int]]:
    """
    Detect regions (clusters) within a connected component using
    label propagation on the undirected adjacency graph.

    Algorithm
    ---------
    1. Each node starts with its own label.
    2. Each iteration: every node adopts the most frequent label
       among its neighbours.  Ties → smallest label wins.
    3. Stop when no label changes or *max_iterations* reached.
    4. Merge any region with < 3 nodes into the neighbouring region
       that shares the most edges with it.

    Returns list of disjoint node sets covering all 0..n-1.
    """
    # Build undirected adjacency
    adj: Dict[int, Set[int]] = {i: set() for i in range(n)}
    for consumer, producers in dep_graph.items():
        for producer in producers:
            adj[consumer].add(producer)
            adj[producer].add(consumer)

    # Initialise
    label: Dict[int, int] = {v: v for v in range(n)}

    for _ in range(max_iterations):
        changed = False
        new_label: Dict[int, int] = dict(label)
        for v in range(n):
            neighbours = adj.get(v, set())
            if not neighbours:
                continue
            counts: Dict[int, int] = {}
            for nb in neighbours:
                lbl = label[nb]
                counts[lbl] = counts.get(lbl, 0) + 1
            max_count = max(counts.values())
            best = min(lbl for lbl, cnt in counts.items() if cnt == max_count)
            if best != label[v]:
                new_label[v] = best
                changed = True
        label = new_label
        if not changed:
            break

    # Group by label
    label_to_nodes: Dict[int, Set[int]] = {}
    for v in range(n):
        label_to_nodes.setdefault(label[v], set()).add(v)
    regions: List[Set[int]] = list(label_to_nodes.values())

    # Merge small regions (< 3 nodes) into the best-connected neighbour
    THRESHOLD = 3
    small = [r for r in regions if len(r) < THRESHOLD]
    large = [r for r in regions if len(r) >= THRESHOLD]

    if small and large:
        for sr in small:
            best = max(large, key=lambda lr: _count_cross_edges(sr, lr, dep_graph))
            best.update(sr)
        regions = large
    elif small and not large:
        merged: Set[int] = set()
        for sr in small:
            merged.update(sr)
        regions = [merged]

    return regions


def detect_components(
    n: int,
    dep_graph: Dict[int, Set[int]],
) -> List[Set[int]]:
    """
    Detect connected components in the undirected version of the DAG.

    Returns list of sets ordered by minimum node index.
    """
    adj: Dict[int, Set[int]] = {i: set() for i in range(n)}
    for consumer, producers in dep_graph.items():
        for producer in producers:
            adj[consumer].add(producer)
            adj[producer].add(consumer)

    visited: Set[int] = set()
    components: List[Set[int]] = []

    for start in range(n):
        if start in visited:
            continue
        stack = [start]
        comp: Set[int] = set()
        while stack:
            v = stack.pop()
            if v in visited:
                continue
            visited.add(v)
            comp.add(v)
            for nb in adj.get(v, set()):
                if nb not in visited:
                    stack.append(nb)
        if comp:
            components.append(comp)

    return components


def extract_subgraph(
    component: Set[int],
    dep_graph: Dict[int, Set[int]],
) -> Tuple[Dict[int, Set[int]], Dict[int, int], Dict[int, int]]:
    """
    Build a subgraph restricted to nodes in `component`.

    Returns:
        sub_graph: dep_graph with remapped indices (0..len-1)
        old_to_new: original index -> new index
        new_to_old: new index -> original index
    """
    comp_list = sorted(component)
    old_to_new: Dict[int, int] = {old: new for new, old in enumerate(comp_list)}
    new_to_old: Dict[int, int] = {v: k for k, v in old_to_new.items()}

    sub_graph: Dict[int, Set[int]] = {}
    for new_idx, old_idx in new_to_old.items():
        parents = dep_graph.get(old_idx, set()) & component
        sub_graph[new_idx] = {old_to_new[p] for p in parents}

    return sub_graph, old_to_new, new_to_old


# ──────────────────────────────────────────────
# Region refinement (post-detection cleanup)
# ──────────────────────────────────────────────

def refine_regions(graph: LayoutGraph) -> None:
    """
    Refine and stabilise region structure *after* initial detection,
    *before* Sugiyama layering/ordering.

    Operates in-place on ``graph.regions`` and ``graph.node_to_region``.

    Steps
    -----
    1. Merge singleton regions (size == 1) into best-connected neighbour.
    2. Enforce minimum size 3 — any region with 1 or 2 nodes is merged.
    3. Merge regions whose external edges exceed internal edges
       (low internal cohesion).
    4. Rebuild ``graph.node_to_region`` for consistency.

    Each step is iterative: after each merge it re-scans from the
    beginning.  This is safe because the number of regions is small
    (typically < 10).
    """
    if not graph.regions or len(graph.regions) <= 1:
        return

    n = graph.original_n
    successors = graph.successors
    node_to_region = graph.node_to_region
    regions = graph.regions

    # ------- helpers -------

    def _cross_edges(rid_a: int, rid_b: int) -> int:
        """Undirected edge count between two regions (both directions)."""
        count = 0
        for v in regions[rid_a]:
            for succ in successors.get(v, set()):
                if succ < n and node_to_region.get(succ) == rid_b:
                    count += 1
        for v in regions[rid_b]:
            for succ in successors.get(v, set()):
                if succ < n and node_to_region.get(succ) == rid_a:
                    count += 1
        return count

    def _best_neighbor(rid: int) -> int:
        """Region id with max cross-edges to *rid* (excludes rid itself).

        Returns -1 if no cross-edges exist.
        """
        best = -1
        max_ce = 0
        for other in range(len(regions)):
            if other == rid or not regions[other]:
                continue
            ce = _cross_edges(rid, other)
            if ce > max_ce:
                max_ce = ce
                best = other
        return best

    def _first_other(rid: int) -> int:
        """Fallback: any other non-empty region."""
        for other in range(len(regions)):
            if other != rid and regions[other]:
                return other
        return -1

    def _merge(source: int, target: int) -> None:
        """Move every node in *source* into *target* and clear *source*."""
        if source == target:
            return
        for v in list(regions[source]):
            node_to_region[v] = target
            regions[target].add(v)
        regions[source].clear()

    def _active() -> List[Tuple[int, Set[int]]]:
        """(rid, region_set) for every non-empty region."""
        return [(i, r) for i, r in enumerate(regions) if r]

    # ======== Step 1 — merge singletons ========
    changed = True
    while changed:
        changed = False
        for rid, region in _active():
            if len(region) == 1:
                best = _best_neighbor(rid)
                if best < 0:
                    best = _first_other(rid)
                if best >= 0:
                    _merge(rid, best)
                    changed = True
                    break

    # ======== Step 2 — enforce minimum size 3 ========
    changed = True
    while changed:
        changed = False
        for rid, region in _active():
            if 0 < len(region) < 3:
                best = _best_neighbor(rid)
                if best < 0:
                    best = _first_other(rid)
                if best >= 0:
                    _merge(rid, best)
                    changed = True
                    break

    # ======== Step 3 — improve connectivity quality ========
    changed = True
    while changed:
        changed = False
        for rid, region in _active():
            if len(region) <= 1:
                continue
            internal = 0
            external = 0
            for v in region:
                for succ in successors.get(v, set()):
                    if succ >= n:
                        continue
                    rid_succ = node_to_region.get(succ)
                    if rid_succ == rid:
                        internal += 1
                    elif rid_succ is not None:
                        external += 1
            if external > internal and external > 0:
                best = _best_neighbor(rid)
                if best < 0:
                    best = _first_other(rid)
                if best >= 0:
                    _merge(rid, best)
                    changed = True
                    break

    # ======== Step 4 — rebuild consistency ========
    graph.regions = [r for r in regions if r]
    if not graph.regions:
        graph.regions = [set(range(n))]
    graph.node_to_region.clear()
    for rid, region in enumerate(graph.regions):
        for v in region:
            graph.node_to_region[v] = rid
