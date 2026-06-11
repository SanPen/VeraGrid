"""
Hierarchical Layout v2 — ELK-style hierarchical layout engine.

Pipeline:
  1. Detect connected components
  2. For each component:
         a. Detect regions (clusters) via label propagation
         b. Refine regions (merge small / low-cohesion regions)
         c. If >1 region → ELK-style recursive layout:
              i.   Layout each region independently (full Sugiyama)
              ii.  Compute region bounding boxes
              iii. Build supergraph (regions as nodes)
              iv.  Layout supergraph (full Sugiyama with sized nodes)
              v.   Combine positions (region offset + supergraph offset)
              vi.  Assign ports to all nodes
         d. Else (1 region) → flat Sugiyama pipeline:
              i.   Layer assignment (longest path)
              ii.  Long-edge splitting (dummy nodes)
              iii. Crossing minimization
              iv.  Coordinate assignment (strict vertical grid)
         e. Post-process signal routing blocks
  3. Compute component bounding boxes
  4. Pack components (shelf-based)
  5. Export positions

Usage:
    positions = compute_layout(len(children), dep_graph, from_to_tpe)
"""
from __future__ import annotations

from typing import Dict, List, Set, Tuple

from ._types import LayoutConfig, LayoutGraph, LayoutReport, make_graph
from ._layering import assign_layers, split_long_edges
from ._ordering import minimize_crossings
from ._coordinates import assign_coordinates
from ._components import detect_components, detect_regions, extract_subgraph, refine_regions
from ._packing import compute_component_bboxes, pack_components
from ._hierarchy import layout_hierarchical
from ._ports import assign_ports, enforce_port_order_constraints
from ._routing_elk import route_edges_with_bend_minimization, validate_layout


def compute_layout(
    n: int,
    dep_graph: Dict[int, Set[int]],
    from_to_tpe: Dict[int, str] | None = None,
    config: LayoutConfig | None = None,
) -> Dict[int, Tuple[float, float]]:
    """
    Full Sugiyama layout pipeline with connected-component awareness.

    Args:
        n: Number of nodes (len(children)).
        dep_graph: dep_graph[consumer] = {producers}.
        from_to_tpe: Optional dict mapping routing block indices to type.
        config: Optional layout parameters.

    Returns:
        Dict[int, Tuple[float, float]] — node index -> (x, y) top-left.
    """
    if config is None:
        config = LayoutConfig()

    if n == 0:
        return {}

    # Fase 1: Detectar componentes conectadas
    components = detect_components(n, dep_graph)

    if len(components) <= 1:
        # Single component: run standard pipeline
        return _layout_single_component(n, dep_graph, from_to_tpe, config)

    # Multi-component: layout each independently, then pack
    component_layouts: List[Tuple[Set[int], Dict[int, Tuple[float, float]]]] = []

    for comp in components:
        sub_graph, old_to_new, new_to_old = extract_subgraph(comp, dep_graph)
        m = len(comp)

        comp_from_to = None
        if from_to_tpe:
            comp_from_to = {
                old_to_new[k]: v
                for k, v in from_to_tpe.items()
                if k in comp
            }

        sub_positions = _layout_single_component(
            m, sub_graph, comp_from_to, config,
        )

        comp_positions: Dict[int, Tuple[float, float]] = {}
        for new_idx, (x, y) in sub_positions.items():
            old_idx = new_to_old[new_idx]
            comp_positions[old_idx] = (x, y)

        component_layouts.append((comp, comp_positions))

    # Fase 3+4: Compute bboxes, pack
    bboxes = compute_component_bboxes(component_layouts, config)
    positions = pack_components(bboxes, config)

    return positions


def _layout_single_component(
    n: int,
    dep_graph: Dict[int, Set[int]],
    from_to_tpe: Dict[int, str] | None = None,
    config: LayoutConfig | None = None,
) -> Dict[int, Tuple[float, float]]:
    """Run the full Sugiyama pipeline on a single connected component.

    When the component contains multiple regions an ELK-style recursive
    layout is used: each region is laid out independently, then a
    supergraph (regions as nodes) is built and laid out, and positions
    are combined with hierarchical offsets.

    Single-region components fall through to the flat pipeline.
    """
    if config is None:
        config = LayoutConfig()

    if n == 0:
        return {}

    # ── Detect and refine regions ──────────────────────────────────
    regions = detect_regions(n, dep_graph)
    graph = make_graph(n, dep_graph, config)

    if len(regions) > 1:
        node_to_region: Dict[int, int] = {}
        for rid, region in enumerate(regions):
            for v in region:
                node_to_region[v] = rid
        graph.node_to_region = node_to_region
        graph.regions = list(regions)
        # Refine: merge singletons, enforce min-size, improve cohesion
        refine_regions(graph)
        # Use refined regions
        refined_regions = graph.regions
        refined_node_to_region = dict(graph.node_to_region)

        # ── ELK-style hierarchical layout ──
        positions = layout_hierarchical(
            n, dep_graph,
            refined_regions, refined_node_to_region,
            config,
        )
        graph.regions = refined_regions
        graph.node_to_region = refined_node_to_region

        # ── Routing pipeline ──
        enforce_port_order_constraints(graph)
        _ = validate_layout(graph, positions)
        route_edges_with_bend_minimization(graph, positions)
    else:
        # ── Flat Sugiyama (no region structure) — port-aware ──
        assign_layers(graph)
        assign_ports(graph)       # degree-based, barycenter-ordered
        minimize_crossings(graph)  # port-aware ordering
        split_long_edges(graph)
        positions = assign_coordinates(graph)

        # ── Routing pipeline ──
        enforce_port_order_constraints(graph)
        _ = validate_layout(graph, positions)
        route_edges_with_bend_minimization(graph, positions)

    # ── Signal routing post-processing ───────────────────────────────
    if from_to_tpe:
        graph = make_graph(n, dep_graph, config)
        positions = _postprocess_routing(positions, graph, from_to_tpe, config)

    return positions


def _postprocess_routing(
    positions: Dict[int, Tuple[float, float]],
    graph_or_dep: object,
    from_to_tpe: Dict[int, str],
    config: LayoutConfig,
) -> Dict[int, Tuple[float, float]]:
    """
    Place signal_in blocks right of their producer,
    signal_out blocks left of their consumer.
    """
    is_signal: Set[int] = {
        i for i, t in from_to_tpe.items()
        if t in ("signal_in", "signal_out")
    }

    # Build predecessors/successors from the graph or dep graph
    predecessors: Dict[int, Set[int]] = {}
    successors: Dict[int, Set[int]] = {}

    if hasattr(graph_or_dep, 'predecessors'):
        # LayoutGraph object
        predecessors = graph_or_dep.predecessors
        successors = graph_or_dep.successors
    else:
        # Raw dep_graph
        dep = graph_or_dep
        for k, v_set in dep.items():
            successors.setdefault(k, set())
            for v in v_set:
                successors.setdefault(v, set()).add(k)
                predecessors.setdefault(k, set()).add(v)
        for k in range(max(list(dep.keys()) + [0]) + 1):
            predecessors.setdefault(k, set())
            successors.setdefault(k, set())

    for v in is_signal:
        if v not in positions:
            continue

        if from_to_tpe.get(v) == "signal_in":
            preds = predecessors.get(v, set()) - is_signal
            if preds:
                p = next(iter(preds))
                px, py = positions.get(p, (0, 0))
                positions[v] = (
                    px + config.node_w + 60,
                    py + (config.node_h - config.dummy_h) / 2.0,
                )
        elif from_to_tpe.get(v) == "signal_out":
            succs = successors.get(v, set()) - is_signal
            if succs:
                s = next(iter(succs))
                sx, sy = positions.get(s, (0, 0))
                positions[v] = (
                    sx - config.node_w - 60,
                    sy + (config.node_h - config.dummy_h) / 2.0,
                )

    return positions
