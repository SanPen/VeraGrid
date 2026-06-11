from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple


@dataclass
class LayoutConfig:
    """Global layout parameters."""
    node_w: float = 160.0
    node_h: float = 70.0
    layer_spacing_x: float = 320.0
    node_spacing_y: float = 120.0
    dummy_w: float = 20.0
    dummy_h: float = 10.0
    margin_x: float = 60.0
    margin_y: float = 40.0
    min_gap_x: float = 30.0


@dataclass
class EdgeRoute:
    src: int
    src_port: int
    dst: int
    dst_port: int
    points: List[Tuple[float, float]] = field(default_factory=list)
    layer_channels: List[int] = field(default_factory=list)  # channel index per layer gap traversed


@dataclass
class EdgeBundle:
    layer_gap: int  # index of the upper layer (edges between layers[gap] and layers[gap+1])
    edges: List[EdgeRoute] = field(default_factory=list)
    assigned_channel_block: Tuple[int, int] = (0, 0)  # (start_channel, end_channel) exclusive


@dataclass
class LayoutReport:
    crossings: int = 0
    total_bends: int = 0
    invalid_edges: int = 0
    bundle_count: int = 0
    routing_cost: float = 0.0


@dataclass
class LayoutGraph:
    """
    Expanded graph state through all Sugiyama phases.
    Original indices are 0..original_n-1.
    Dummy nodes get new indices >= original_n.
    """
    original_n: int
    total_n: int
    layers: List[List[int]]
    layer_of: Dict[int, int]
    successors: Dict[int, Set[int]]
    predecessors: Dict[int, Set[int]]
    is_dummy: Set[int]
    original_of: Dict[int, int]          # dummy -> original node
    chain_of: Dict[int, int]             # dummy node -> chain_id (each long edge = one chain)
    chain_nodes: Dict[int, List[int]]    # chain_id -> [dummy1, dummy2, ...] in layer order
    port_edges: List[Tuple[int, int, int, int]]  # src, src_port, dst, dst_port
    node_to_region: Dict[int, int] = field(default_factory=dict)   # node -> region_id
    regions: List[Set[int]] = field(default_factory=list)           # region_id -> {nodes}
    # ── Hierarchy / ELK fields ──
    level: int = 0                        # hierarchy depth (0 = root)
    parent_region: int | None = None      # which region this subgraph belongs to (None = root)
    hierarchy_offset: Tuple[float, float] = (0.0, 0.0)  # accumulated offset from parent levels
    port_map: Dict[int, List[Tuple[str, float, int]]] | None = None  # node -> [(side, coord, port_id)]
    region_bounds: Dict[int, Tuple[float, float, float, float]] = field(default_factory=dict)
    config: LayoutConfig = field(default_factory=LayoutConfig)
    edge_routes: Dict[Tuple[int, int], EdgeRoute] = field(default_factory=dict)

    @property
    def original_nodes(self) -> range:
        return range(self.original_n)

    @property
    def all_nodes(self) -> range:
        return range(self.total_n)

    def is_original(self, v: int) -> bool:
        return v < self.original_n


def make_graph(
    n: int,
    dep_graph: Dict[int, Set[int]],
    config: LayoutConfig | None = None,
) -> LayoutGraph:
    """
    Build a LayoutGraph from the raw dependency graph.
    dep_graph[consumer] = {producers}.
    """
    if config is None:
        config = LayoutConfig()
    successors: Dict[int, Set[int]] = {i: set() for i in range(n)}
    predecessors: Dict[int, Set[int]] = {i: set() for i in range(n)}
    for consumer, producers in dep_graph.items():
        for producer in producers:
            successors[producer].add(consumer)
            predecessors[consumer].add(producer)

    return LayoutGraph(
        original_n=n,
        total_n=n,
        layers=[],
        layer_of={},
        successors=successors,
        predecessors=predecessors,
        is_dummy=set(),
        original_of={},
        chain_of={},
        chain_nodes={},
        port_edges=[],
        config=config,
    )
