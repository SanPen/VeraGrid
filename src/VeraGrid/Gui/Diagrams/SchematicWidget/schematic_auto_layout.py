# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from collections import deque
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

import networkx as nx
import numpy as np
from VeraGridEngine.enumerations import DeviceType, BusGraphicType

if TYPE_CHECKING:
    from VeraGridEngine.Devices.Diagrams.schematic_diagram import SchematicDiagram
    from VeraGridEngine.Devices.Diagrams.graphic_location import GraphicLocation
    from VeraGridEngine.Devices.types import ALL_DEV_TYPES


def should_auto_layout_before_first_draw(diagram: SchematicDiagram,
                                         epsilon: float = 1e-6) -> bool:
    """
    Determine whether the schematic should be auto-laid out before any graphics are created.

    The check intentionally looks only at visible bus-like anchors. If every visible
    anchor is still at the origin, drawing all widgets first would stack them at the
    same scene position and make Qt spend time resolving a pathological geometry state.

    :param diagram: Schematic diagram to inspect.
    :param epsilon: Tolerance used to compare coordinates against the origin.
    :return: ``True`` when an initial auto-layout should run before drawing.
    """
    visible_bus_count: int = 0
    category_points_group = diagram.query_by_type(device_type=DeviceType.BusDevice)

    if category_points_group is None:
        return False
    else:
        location: GraphicLocation

    for location in category_points_group.locations.values():
        api_object: ALL_DEV_TYPES = location.api_object

        if api_object.graphic_type == BusGraphicType.Internal:
            visible_bus_count = visible_bus_count
        else:
            visible_bus_count += 1

            if abs(float(location.x)) <= epsilon and abs(float(location.y)) <= epsilon:
                visible_bus_count = visible_bus_count
            else:
                return False

    if visible_bus_count > 1:
        return True
    else:
        return False


def apply_initial_auto_layout_to_diagram(diagram: SchematicDiagram,
                                         layout_name: str = "power_system_layout",
                                         position_scale: float = 500.0) -> None:
    """
    Apply one automatic layout directly to the stored diagram coordinates.

    This function operates only on the persisted ``GraphicLocation`` records and does
    not require any Qt graphics objects to exist yet. Running it before scene creation
    avoids the expensive transient state where all node widgets are initially stacked
    at the origin.

    :param diagram: Schematic diagram to modify.
    :param layout_name: Automatic layout mode to evaluate.
    :param position_scale: Final coordinate scaling factor in pixels.
    :return: ``None``.
    """
    graph: nx.MultiDiGraph
    node_like_api_objects: List[ALL_DEV_TYPES]
    graph, node_like_api_objects = diagram.build_graph()
    calculated_positions: Dict[int, np.ndarray] = calculate_schematic_layout(graph=graph, sel=layout_name)
    node_idx: int
    elm: ALL_DEV_TYPES

    for node_idx, elm in enumerate(node_like_api_objects):
        loc = diagram.query_point(device=elm)
        pos_vec: np.ndarray | None = calculated_positions.get(node_idx, None)

        if loc is not None and pos_vec is not None:
            # The diagram record must hold stable coordinates before any widget exists.
            loc.x = float(pos_vec[0]) * position_scale
            loc.y = float(pos_vec[1]) * position_scale
        else:
            loc = loc


def get_layout_graph_node_voltage_kv(graph: nx.Graph, node_idx: int) -> float:
    """
    Read the nominal voltage attached to one graph node.

    :param graph: Diagram graph.
    :param node_idx: Graph node index.
    :return: Voltage level in kV.
    """
    node_data: Dict[str, Any] = graph.nodes[node_idx]
    voltage_kv_raw: Any = node_data.get("voltage_kv", 0.0)
    voltage_kv: float = float(voltage_kv_raw)
    return voltage_kv


def get_layout_graph_node_is_slack(graph: nx.Graph, node_idx: int) -> bool:
    """
    Read the slack marker attached to one graph node.

    :param graph: Diagram graph.
    :param node_idx: Graph node index.
    :return: ``True`` when the node is slack.
    """
    node_data: Dict[str, Any] = graph.nodes[node_idx]
    is_slack_raw: Any = node_data.get("is_slack", False)
    is_slack: bool = bool(is_slack_raw)
    return is_slack


def get_layout_graph_node_substation(graph: nx.Graph, node_idx: int) -> str:
    """
    Read the substation name attached to one graph node.

    :param graph: Diagram graph.
    :param node_idx: Graph node index.
    :return: Substation name or an empty string.
    """
    node_data: Dict[str, Any] = graph.nodes[node_idx]
    substation_name_raw: Any = node_data.get("substation", "")
    substation_name: str = str(substation_name_raw)
    return substation_name


def get_layout_graph_node_name(graph: nx.Graph, node_idx: int) -> str:
    """
    Read the display name attached to one graph node.

    :param graph: Diagram graph.
    :param node_idx: Graph node index.
    :return: Node name or an empty string.
    """
    node_data: Dict[str, Any] = graph.nodes[node_idx]
    node_name_raw: Any = node_data.get("name", "")
    node_name: str = str(node_name_raw)
    return node_name


def get_layout_edge_device_tpe_from_data(edge_data: Dict[str, Any]) -> DeviceType | None:
    """
    Read the device type attached to one branch edge.

    :param edge_data: Edge metadata dictionary.
    :return: Edge device type or ``None`` when it cannot be mapped.
    """
    edge_kind_raw: Any = edge_data.get("kind", "")
    edge_kind: str = str(edge_kind_raw)
    device_tpe: DeviceType | None = None
    candidate_tpe: DeviceType

    # Edge metadata is serialized as text when the graph is built. The layout stage
    # converts that text back to the enum immediately so all downstream logic compares
    # explicit device types instead of free-form strings.
    for candidate_tpe in DeviceType:
        if candidate_tpe.value == edge_kind:
            device_tpe = candidate_tpe
        else:
            candidate_tpe = candidate_tpe

    return device_tpe


def get_layout_edge_strength_from_data(edge_data: Dict[str, Any]) -> float:
    """
    Read the spring strength associated with one branch edge.

    :param edge_data: Edge metadata dictionary.
    :return: Positive spring strength.
    """
    strength_raw: Any = edge_data.get("strength", 1.0)
    strength: float = max(float(strength_raw), 1e-6)
    return strength


def get_layout_edge_impedance_from_data(edge_data: Dict[str, Any]) -> float:
    """
    Read the impedance surrogate associated with one branch edge.

    :param edge_data: Edge metadata dictionary.
    :return: Positive impedance surrogate.
    """
    impedance_raw: Any = edge_data.get("impedance", 1.0)
    impedance: float = max(float(impedance_raw), 1e-6)
    return impedance


def get_layout_representative_branch_edge_data(graph: nx.Graph | nx.MultiGraph,
                                               from_idx: int,
                                               to_idx: int) -> Dict[str, Any]:
    """
    Select one representative branch between two nodes for pair-based layout decisions.

    The full multigraph keeps every physical branch so parallel branches are preserved.
    Some layout steps still need a single representative relation between two nodes.
    In that case the strongest branch is selected, with impedance as a tie-breaker.

    :param graph: Diagram graph.
    :param from_idx: Source node index.
    :param to_idx: Target node index.
    :return: Representative edge metadata dictionary.
    """
    selected_edge_data: Dict[str, Any] = dict()

    if graph.is_multigraph():
        parallel_edge_data = graph.get_edge_data(from_idx, to_idx, default=dict())
        best_strength: float = -1.0
        best_impedance: float = float("inf")
        edge_key: Any

        for edge_key, candidate_edge_data in parallel_edge_data.items():
            candidate_strength: float = get_layout_edge_strength_from_data(edge_data=candidate_edge_data)
            candidate_impedance: float = get_layout_edge_impedance_from_data(edge_data=candidate_edge_data)
            use_candidate: bool = False

            if candidate_strength > best_strength:
                use_candidate = True
            elif candidate_strength == best_strength and candidate_impedance < best_impedance:
                use_candidate = True
            else:
                use_candidate = False

            if use_candidate:
                selected_edge_data = candidate_edge_data
                best_strength = candidate_strength
                best_impedance = candidate_impedance
            else:
                edge_key = edge_key
    else:
        selected_edge_data = graph.edges[from_idx, to_idx]

    return selected_edge_data


def get_layout_edge_radius_step(graph: nx.Graph | nx.MultiGraph,
                                from_idx: int,
                                to_idx: int,
                                base_radius_gap: float) -> float:
    """
    Compute the radial step contributed by one backbone edge.

    :param graph: Diagram graph.
    :param from_idx: Source node index.
    :param to_idx: Target node index.
    :param base_radius_gap: Base radial step used for line-like edges.
    :return: Radial increment for the edge.
    """
    edge_data: Dict[str, Any] = get_layout_representative_branch_edge_data(graph=graph,
                                                                           from_idx=from_idx,
                                                                           to_idx=to_idx)
    edge_device_tpe: DeviceType | None = get_layout_edge_device_tpe_from_data(edge_data=edge_data)
    radius_factor: float = 1.0

    # Transformer-like and switching devices should cluster the connected buses more tightly
    # than actual network spans represented by lines and similar corridor devices.
    if edge_device_tpe == DeviceType.Transformer2WDevice:
        radius_factor = 0.16
    elif edge_device_tpe == DeviceType.WindingDevice:
        radius_factor = 0.12
    elif edge_device_tpe == DeviceType.SwitchDevice:
        radius_factor = 0.18
    elif edge_device_tpe == DeviceType.VscDevice:
        radius_factor = 0.22
    elif edge_device_tpe == DeviceType.UpfcDevice:
        radius_factor = 0.25
    elif edge_device_tpe == DeviceType.SeriesReactanceDevice:
        radius_factor = 0.35
    elif edge_device_tpe == DeviceType.HVDCLineDevice:
        radius_factor = 0.75
    elif edge_device_tpe == DeviceType.DCLineDevice:
        radius_factor = 0.85
    elif edge_device_tpe == DeviceType.FluidPathDevice:
        radius_factor = 0.90
    else:
        radius_factor = 1.0

    return base_radius_gap * radius_factor


def is_layout_edge_transformer_compact_kind(edge_device_tpe: DeviceType | None) -> bool:
    """
    Determine whether one edge device type should be aggressively compacted in the schematic.

    Transformer-like couplings do not represent corridor distance. They represent
    a tight electrical relationship around the same station area, so the connected
    node symbols should remain visually close.

    :param edge_device_tpe: Edge device type.
    :return: ``True`` when the edge should be compacted strongly.
    """
    if edge_device_tpe == DeviceType.Transformer2WDevice:
        return True
    elif edge_device_tpe == DeviceType.WindingDevice:
        return True
    else:
        return False


def get_layout_edge_max_compact_distance(edge_data: Dict[str, Any],
                                         base_radius_gap: float) -> float:
    """
    Get the maximum preferred Euclidean distance for one compact branch edge.

    The target distance is intentionally much smaller than the normal radial gap.
    This keeps buses linked through 2-winding transformers or the winding spokes of
    3-winding and N-winding transformers from spreading apart as the radial sectors
    expand.

    :param edge_data: Branch edge metadata.
    :param base_radius_gap: Base radial step used for line-like edges.
    :return: Maximum preferred Euclidean edge length in layout units.
    """
    edge_device_tpe: DeviceType | None = get_layout_edge_device_tpe_from_data(edge_data=edge_data)

    if edge_device_tpe == DeviceType.Transformer2WDevice:
        return base_radius_gap * 0.14
    elif edge_device_tpe == DeviceType.WindingDevice:
        return base_radius_gap * 0.10
    else:
        return base_radius_gap


def refine_positions_for_transformer_compactness(component_graph: nx.Graph | nx.MultiGraph,
                                                 positions: Dict[int, np.ndarray],
                                                 base_radius_gap: float,
                                                 iteration_count: int = 14,
                                                 blend_factor: float = 0.32) -> Dict[int, np.ndarray]:
    """
    Contract transformer-linked nodes after the coarse radial placement.

    The radial tree placement decides the global spider-web geometry, but it can still
    leave transformer-connected nodes too far apart because their angular sectors may
    widen with the surrounding subtree. This refinement only contracts compact
    transformer edges and leaves line corridors untouched.

    :param component_graph: Connected component graph.
    :param positions: Initial node positions for the component.
    :param base_radius_gap: Base radial step used for line-like edges.
    :param iteration_count: Number of contraction iterations.
    :param blend_factor: Fraction of the excess edge length corrected per iteration.
    :return: Refined component positions.
    """
    refined_positions: Dict[int, np.ndarray] = dict()
    node_idx: int

    for node_idx, pos_vec in positions.items():
        refined_positions[node_idx] = np.array([float(pos_vec[0]), float(pos_vec[1])], dtype=float)

    iteration_idx: int
    for iteration_idx in range(iteration_count):
        correction_sum_by_node: Dict[int, np.ndarray] = dict()
        correction_count_by_node: Dict[int, int] = dict()
        from_idx: int
        to_idx: int
        moved_any: bool = False

        for node_idx in refined_positions.keys():
            correction_sum_by_node[node_idx] = np.zeros(2, dtype=float)
            correction_count_by_node[node_idx] = 0

        if component_graph.is_multigraph():
            edge_key: Any
            edge_data: Dict[str, Any]

            for from_idx, to_idx, edge_key, edge_data in component_graph.edges(keys=True, data=True):
                edge_device_tpe: DeviceType | None = get_layout_edge_device_tpe_from_data(edge_data=edge_data)

                if is_layout_edge_transformer_compact_kind(edge_device_tpe=edge_device_tpe):
                    from_pos: np.ndarray = refined_positions[from_idx]
                    to_pos: np.ndarray = refined_positions[to_idx]
                    delta_vec: np.ndarray = to_pos - from_pos
                    distance: float = float(np.linalg.norm(delta_vec))
                    target_distance: float = get_layout_edge_max_compact_distance(edge_data=edge_data,
                                                                                 base_radius_gap=base_radius_gap)

                    if distance > target_distance and distance > 1e-9:
                        excess_ratio: float = (distance - target_distance) / distance
                        correction_vec: np.ndarray = delta_vec * (0.5 * blend_factor * excess_ratio)
                        correction_sum_by_node[from_idx] = correction_sum_by_node[from_idx] + correction_vec
                        correction_sum_by_node[to_idx] = correction_sum_by_node[to_idx] - correction_vec
                        correction_count_by_node[from_idx] += 1
                        correction_count_by_node[to_idx] += 1
                        moved_any = True
                    else:
                        distance = distance
                else:
                    edge_key = edge_key
            else:
                pass
        else:
            edge_data: Dict[str, Any]

            for from_idx, to_idx, edge_data in component_graph.edges(data=True):
                edge_device_tpe: DeviceType | None = get_layout_edge_device_tpe_from_data(edge_data=edge_data)

                if is_layout_edge_transformer_compact_kind(edge_device_tpe=edge_device_tpe):
                    from_pos: np.ndarray = refined_positions[from_idx]
                    to_pos: np.ndarray = refined_positions[to_idx]
                    delta_vec: np.ndarray = to_pos - from_pos
                    distance: float = float(np.linalg.norm(delta_vec))
                    target_distance: float = get_layout_edge_max_compact_distance(edge_data=edge_data,
                                                                                 base_radius_gap=base_radius_gap)

                    if distance > target_distance and distance > 1e-9:
                        excess_ratio: float = (distance - target_distance) / distance
                        correction_vec: np.ndarray = delta_vec * (0.5 * blend_factor * excess_ratio)
                        correction_sum_by_node[from_idx] = correction_sum_by_node[from_idx] + correction_vec
                        correction_sum_by_node[to_idx] = correction_sum_by_node[to_idx] - correction_vec
                        correction_count_by_node[from_idx] += 1
                        correction_count_by_node[to_idx] += 1
                        moved_any = True
                    else:
                        distance = distance
                else:
                    edge_data = edge_data

        for node_idx in refined_positions.keys():
            correction_count: int = correction_count_by_node[node_idx]

            if correction_count > 0:
                average_correction: np.ndarray = correction_sum_by_node[node_idx] / float(correction_count)
                refined_positions[node_idx] = refined_positions[node_idx] + average_correction
            else:
                correction_count = correction_count

        if moved_any:
            moved_any = moved_any
        else:
            break

    iteration_idx = iteration_idx
    return refined_positions


def select_power_system_root(graph: nx.Graph, component_nodes: List[int]) -> int:
    """
    Select the root used to orient one electrical island.

    :param graph: Diagram graph.
    :param component_nodes: Nodes belonging to one connected component.
    :return: Root node index.
    """
    root_node: int = component_nodes[0]
    best_slack_rank: int = -1
    best_voltage_kv: float = -1.0
    best_degree: int = -1
    best_inverse_node_idx: int = -component_nodes[0]
    node_idx: int

    # The root preference is slack first, then the highest nominal voltage,
    # then the most connected node so the layout grows from the electrical backbone.
    for node_idx in component_nodes:
        slack_rank: int = 1 if get_layout_graph_node_is_slack(graph=graph, node_idx=node_idx) else 0
        voltage_kv: float = get_layout_graph_node_voltage_kv(graph=graph, node_idx=node_idx)
        degree: int = int(graph.degree(node_idx))
        inverse_node_idx: int = -node_idx
        is_better: bool = False

        if slack_rank > best_slack_rank:
            is_better = True
        elif slack_rank == best_slack_rank and voltage_kv > best_voltage_kv:
            is_better = True
        elif slack_rank == best_slack_rank and voltage_kv == best_voltage_kv and degree > best_degree:
            is_better = True
        elif (slack_rank == best_slack_rank and voltage_kv == best_voltage_kv and degree == best_degree and
              inverse_node_idx > best_inverse_node_idx):
            is_better = True
        else:
            is_better = False

        if is_better:
            root_node = node_idx
            best_slack_rank = slack_rank
            best_voltage_kv = voltage_kv
            best_degree = degree
            best_inverse_node_idx = inverse_node_idx
        else:
            root_node = root_node

    return root_node


def build_component_bfs_depths(graph: nx.Graph, component_nodes: List[int], root_node: int) -> Dict[int, int]:
    """
    Build the BFS depth map for one connected component.

    :param graph: Undirected diagram graph.
    :param component_nodes: Nodes belonging to one connected component.
    :param root_node: Root used to orient the island.
    :return: BFS depth by node index.
    """
    depth_by_node: Dict[int, int] = dict()
    pending_nodes: deque[int] = deque()
    current_node: int
    neighbour_idx: int

    # Breadth-first levels define the initial topological progression inside each island.
    depth_by_node[root_node] = 0
    pending_nodes.append(root_node)

    while len(pending_nodes) > 0:
        current_node = pending_nodes.popleft()
        neighbours: List[int] = sorted(list(graph.neighbors(current_node)))

        for neighbour_idx in neighbours:
            if neighbour_idx not in depth_by_node:
                depth_by_node[neighbour_idx] = depth_by_node[current_node] + 1
                pending_nodes.append(neighbour_idx)
            else:
                depth_by_node[neighbour_idx] = depth_by_node[neighbour_idx]

    # Every node must receive an explicit depth even for degenerate components.
    for current_node in component_nodes:
        if current_node not in depth_by_node:
            depth_by_node[current_node] = 0
        else:
            depth_by_node[current_node] = depth_by_node[current_node]

    return depth_by_node


def build_component_voltage_layers(graph: nx.Graph, component_nodes: List[int]) -> Dict[float, int]:
    """
    Build the voltage-to-layer lookup for one electrical island.

    :param graph: Diagram graph.
    :param component_nodes: Nodes belonging to one connected component.
    :return: Voltage layer index by voltage value.
    """
    voltage_values: set[float] = set()
    node_idx: int

    # Positive voltage levels define the coarse transmission and distribution strata.
    for node_idx in component_nodes:
        voltage_kv: float = get_layout_graph_node_voltage_kv(graph=graph, node_idx=node_idx)
        if voltage_kv > 0.0:
            voltage_values.add(voltage_kv)
        else:
            voltage_values = voltage_values

    ordered_voltage_values: List[float] = sorted(list(voltage_values), reverse=True)
    layer_by_voltage: Dict[float, int] = dict()
    voltage_idx: int
    voltage_kv: float

    for voltage_idx, voltage_kv in enumerate(ordered_voltage_values):
        layer_by_voltage[voltage_kv] = voltage_idx

    return layer_by_voltage


def build_component_layer_map(graph: nx.Graph,
                              undirected_graph: nx.Graph,
                              component_nodes: List[int]) -> Dict[int, int]:
    """
    Build the layer assignment for one connected component.

    :param graph: Diagram graph with node metadata.
    :param undirected_graph: Undirected view of the same graph.
    :param component_nodes: Nodes belonging to one connected component.
    :return: Layer index by node.
    """
    root_node: int = select_power_system_root(graph=graph, component_nodes=component_nodes)
    depth_by_node: Dict[int, int] = build_component_bfs_depths(graph=undirected_graph,
                                                               component_nodes=component_nodes,
                                                               root_node=root_node)
    layer_by_voltage: Dict[float, int] = build_component_voltage_layers(graph=graph, component_nodes=component_nodes)
    use_voltage_layers: bool = len(layer_by_voltage) > 1
    layer_by_node: Dict[int, int] = dict()
    node_idx: int

    # Voltage levels drive the main columns. Same-voltage systems fall back to BFS depth.
    for node_idx in component_nodes:
        voltage_kv: float = get_layout_graph_node_voltage_kv(graph=graph, node_idx=node_idx)

        if use_voltage_layers:
            if voltage_kv in layer_by_voltage:
                layer_by_node[node_idx] = layer_by_voltage[voltage_kv]
            else:
                layer_by_node[node_idx] = depth_by_node[node_idx]
        else:
            layer_by_node[node_idx] = depth_by_node[node_idx]

    return layer_by_node


def build_initial_layer_rows(graph: nx.Graph,
                             component_nodes: List[int],
                             layer_by_node: Dict[int, int],
                             depth_by_node: Dict[int, int]) -> Dict[int, List[int]]:
    """
    Build the initial deterministic ordering inside each layer.

    :param graph: Diagram graph with node metadata.
    :param component_nodes: Nodes belonging to one connected component.
    :param layer_by_node: Layer assignment by node.
    :param depth_by_node: BFS depth by node.
    :return: Ordered nodes grouped by layer.
    """
    rows_by_layer: Dict[int, List[Tuple[int, str, str, int]]] = dict()
    node_idx: int

    # The initial order is deterministic and electrically meaningful before crossing reduction starts.
    for node_idx in component_nodes:
        layer_idx: int = layer_by_node[node_idx]
        row_entries: List[Tuple[int, str, str, int]] | None = rows_by_layer.get(layer_idx, None)

        if row_entries is None:
            row_entries = list()
            rows_by_layer[layer_idx] = row_entries
        else:
            row_entries = row_entries

        row_entries.append((depth_by_node[node_idx],
                            get_layout_graph_node_substation(graph=graph, node_idx=node_idx),
                            get_layout_graph_node_name(graph=graph, node_idx=node_idx),
                            node_idx))

    ordered_rows_by_layer: Dict[int, List[int]] = dict()
    layer_idx: int

    for layer_idx in sorted(list(rows_by_layer.keys())):
        row_entries = rows_by_layer[layer_idx]
        row_entries.sort()
        ordered_nodes: List[int] = list()
        row_entry: Tuple[int, str, str, int]

        for row_entry in row_entries:
            ordered_nodes.append(row_entry[3])

        ordered_rows_by_layer[layer_idx] = ordered_nodes

    return ordered_rows_by_layer


def build_node_order_lookup(rows_by_layer: Dict[int, List[int]]) -> Dict[int, float]:
    """
    Build the current row position lookup for barycenter ordering.

    :param rows_by_layer: Ordered rows by layer.
    :return: Row position by node.
    """
    order_by_node: Dict[int, float] = dict()
    layer_idx: int

    for layer_idx in sorted(list(rows_by_layer.keys())):
        ordered_nodes: List[int] = rows_by_layer[layer_idx]
        row_idx: int
        node_idx: int

        for row_idx, node_idx in enumerate(ordered_nodes):
            order_by_node[node_idx] = float(row_idx)

    return order_by_node


def compute_layer_barycenter(graph: nx.Graph,
                             rows_by_layer: Dict[int, List[int]],
                             order_by_node: Dict[int, float],
                             current_layer_idx: int,
                             reference_layer_idx: int) -> Dict[int, float]:
    """
    Compute the barycenter score of one layer against one adjacent reference layer.

    :param graph: Diagram graph.
    :param rows_by_layer: Ordered rows by layer.
    :param order_by_node: Current row position by node.
    :param current_layer_idx: Layer being reordered.
    :param reference_layer_idx: Adjacent layer providing the reference order.
    :return: Barycenter score by node.
    """
    barycenter_by_node: Dict[int, float] = dict()
    ordered_nodes: List[int] = rows_by_layer.get(current_layer_idx, list())
    node_idx: int

    for node_idx in ordered_nodes:
        weighted_sum: float = 0.0
        weighted_count: float = 0.0
        neighbour_idx: int

        # Only neighbours in the adjacent layer should influence the Sugiyama ordering pass.
        for neighbour_idx in graph.neighbors(node_idx):
            neighbour_layer_idx: int = -1
            layer_idx: int

            for layer_idx in rows_by_layer.keys():
                if neighbour_idx in rows_by_layer[layer_idx]:
                    neighbour_layer_idx = layer_idx
                else:
                    neighbour_layer_idx = neighbour_layer_idx

            if neighbour_layer_idx == reference_layer_idx:
                representative_edge_data: Dict[str, Any] = get_layout_representative_branch_edge_data(
                    graph=graph,
                    from_idx=node_idx,
                    to_idx=neighbour_idx
                )
                edge_strength: float = get_layout_edge_strength_from_data(edge_data=representative_edge_data)
                neighbour_order: float = order_by_node.get(neighbour_idx, 0.0)
                weighted_sum += edge_strength * neighbour_order
                weighted_count += edge_strength
            else:
                weighted_sum = weighted_sum

        if weighted_count > 0.0:
            barycenter_by_node[node_idx] = weighted_sum / weighted_count
        else:
            barycenter_by_node[node_idx] = order_by_node.get(node_idx, 0.0)

    return barycenter_by_node


def reorder_one_layer(graph: nx.Graph,
                      rows_by_layer: Dict[int, List[int]],
                      current_layer_idx: int,
                      reference_layer_idx: int) -> None:
    """
    Reorder one layer using one barycenter pass.

    :param graph: Diagram graph.
    :param rows_by_layer: Ordered rows by layer.
    :param current_layer_idx: Layer being reordered.
    :param reference_layer_idx: Adjacent layer providing the reference ordering.
    """
    ordered_nodes: List[int] = rows_by_layer.get(current_layer_idx, list())

    if len(ordered_nodes) > 1:
        order_by_node: Dict[int, float] = build_node_order_lookup(rows_by_layer=rows_by_layer)
        barycenter_by_node: Dict[int, float] = compute_layer_barycenter(graph=graph,
                                                                        rows_by_layer=rows_by_layer,
                                                                        order_by_node=order_by_node,
                                                                        current_layer_idx=current_layer_idx,
                                                                        reference_layer_idx=reference_layer_idx)
        sortable_entries: List[Tuple[float, float, str, str, int]] = list()
        row_idx: int
        node_idx: int

        # The stable secondary keys keep deterministic order when barycenters tie.
        for row_idx, node_idx in enumerate(ordered_nodes):
            sortable_entries.append((barycenter_by_node.get(node_idx, float(row_idx)),
                                     float(row_idx),
                                     get_layout_graph_node_substation(graph=graph, node_idx=node_idx),
                                     get_layout_graph_node_name(graph=graph, node_idx=node_idx),
                                     node_idx))

        sortable_entries.sort()
        reordered_nodes: List[int] = list()
        entry: Tuple[float, float, str, str, int]

        for entry in sortable_entries:
            reordered_nodes.append(entry[4])

        rows_by_layer[current_layer_idx] = reordered_nodes
    else:
        rows_by_layer[current_layer_idx] = ordered_nodes


def reduce_crossings_with_barycenter(graph: nx.Graph,
                                     rows_by_layer: Dict[int, List[int]],
                                     max_passes: int = 8) -> Dict[int, List[int]]:
    """
    Reduce crossings with alternating top-down and bottom-up barycenter passes.

    :param graph: Diagram graph.
    :param rows_by_layer: Initial row ordering by layer.
    :param max_passes: Number of alternating passes.
    :return: Improved row ordering by layer.
    """
    improved_rows_by_layer: Dict[int, List[int]] = dict()
    layer_idx: int

    for layer_idx in rows_by_layer.keys():
        improved_rows_by_layer[layer_idx] = list(rows_by_layer[layer_idx])

    ordered_layer_indices: List[int] = sorted(list(improved_rows_by_layer.keys()))
    pass_idx: int

    # Alternating passes approximate the standard Sugiyama crossing-reduction phase.
    for pass_idx in range(max_passes):
        if pass_idx % 2 == 0:
            layer_pos_idx: int

            for layer_pos_idx in range(1, len(ordered_layer_indices)):
                current_layer_idx = ordered_layer_indices[layer_pos_idx]
                reference_layer_idx = ordered_layer_indices[layer_pos_idx - 1]
                reorder_one_layer(graph=graph,
                                  rows_by_layer=improved_rows_by_layer,
                                  current_layer_idx=current_layer_idx,
                                  reference_layer_idx=reference_layer_idx)
        else:
            layer_pos_idx = len(ordered_layer_indices) - 2

            while layer_pos_idx >= 0:
                current_layer_idx = ordered_layer_indices[layer_pos_idx]
                reference_layer_idx = ordered_layer_indices[layer_pos_idx + 1]
                reorder_one_layer(graph=graph,
                                  rows_by_layer=improved_rows_by_layer,
                                  current_layer_idx=current_layer_idx,
                                  reference_layer_idx=reference_layer_idx)
                layer_pos_idx -= 1

    return improved_rows_by_layer


def assign_initial_component_positions(component_origin_x: float,
                                       rows_by_layer: Dict[int, List[int]],
                                       layer_gap_x: float,
                                       row_gap_y: float) -> Dict[int, np.ndarray]:
    """
    Assign initial coordinates from the layer and row order.

    :param component_origin_x: Left origin of the component.
    :param rows_by_layer: Ordered rows by layer.
    :param layer_gap_x: Horizontal gap between layers.
    :param row_gap_y: Vertical gap between nodes inside a layer.
    :return: Initial position by node.
    """
    positions: Dict[int, np.ndarray] = dict()
    layer_idx: int

    # The initial coordinates respect the electrical columns and the reduced-crossing row order.
    for layer_idx in sorted(list(rows_by_layer.keys())):
        ordered_nodes: List[int] = rows_by_layer[layer_idx]
        row_count: int = len(ordered_nodes)
        row_center: float = 0.5 * float(row_count - 1)
        row_idx: int
        node_idx: int

        for row_idx, node_idx in enumerate(ordered_nodes):
            x_pos: float = component_origin_x + float(layer_idx) * layer_gap_x
            y_pos: float = (float(row_idx) - row_center) * row_gap_y
            positions[node_idx] = np.array([x_pos, y_pos], dtype=float)

    return positions


def compute_vertical_targets(graph: nx.Graph,
                             ordered_nodes: List[int],
                             current_positions: Dict[int, np.ndarray]) -> Dict[int, float]:
    """
    Compute vertical target positions from neighbour positions.

    :param graph: Diagram graph.
    :param ordered_nodes: Ordered nodes of one layer.
    :param current_positions: Current position by node.
    :return: Vertical target by node.
    """
    target_by_node: Dict[int, float] = dict()
    node_idx: int

    # Neighbour averaging refines the layout without destroying the existing layer assignment.
    for node_idx in ordered_nodes:
        weighted_sum: float = 0.0
        weighted_count: float = 0.0
        neighbour_idx: int

        for neighbour_idx in graph.neighbors(node_idx):
            representative_edge_data: Dict[str, Any] = get_layout_representative_branch_edge_data(
                graph=graph,
                from_idx=node_idx,
                to_idx=neighbour_idx
            )
            edge_strength: float = get_layout_edge_strength_from_data(edge_data=representative_edge_data)
            neighbour_pos: np.ndarray | None = current_positions.get(neighbour_idx, None)

            if neighbour_pos is not None:
                weighted_sum += edge_strength * float(neighbour_pos[1])
                weighted_count += edge_strength
            else:
                weighted_sum = weighted_sum

        if weighted_count > 0.0:
            target_by_node[node_idx] = weighted_sum / weighted_count
        else:
            current_pos: np.ndarray = current_positions[node_idx]
            target_by_node[node_idx] = float(current_pos[1])

    return target_by_node


def enforce_vertical_spacing(ordered_nodes: List[int],
                             target_by_node: Dict[int, float],
                             row_gap_y: float) -> Dict[int, float]:
    """
    Enforce minimum spacing while staying close to the target positions.

    :param ordered_nodes: Ordered nodes of one layer.
    :param target_by_node: Preferred vertical target by node.
    :param row_gap_y: Minimum spacing between consecutive nodes.
    :return: Spaced vertical coordinate by node.
    """
    spaced_y_by_node: Dict[int, float] = dict()
    row_idx: int
    node_idx: int

    if len(ordered_nodes) == 0:
        return spaced_y_by_node
    else:
        provisional_y: List[float] = list()

    # The forward pass ensures strict ordering and minimum spacing.
    for row_idx, node_idx in enumerate(ordered_nodes):
        target_y: float = target_by_node[node_idx]

        if row_idx == 0:
            provisional_y.append(target_y)
        else:
            previous_y: float = provisional_y[row_idx - 1]
            provisional_y.append(max(target_y, previous_y + row_gap_y))

    # The backward recentering keeps the layer close to the original target cloud.
    last_idx: int = len(ordered_nodes) - 1
    while last_idx >= 0:
        node_idx = ordered_nodes[last_idx]
        target_y = target_by_node[node_idx]

        if last_idx == len(ordered_nodes) - 1:
            provisional_y[last_idx] = min(provisional_y[last_idx], target_y + 0.5 * row_gap_y)
        else:
            next_y: float = provisional_y[last_idx + 1]
            provisional_y[last_idx] = min(provisional_y[last_idx], next_y - row_gap_y)

        last_idx -= 1

    # A final normalization recenters the layer around zero for stable component packing.
    mean_y: float = 0.0
    provisional_y_count: int = len(provisional_y)
    provisional_entry_y: float

    for provisional_entry_y in provisional_y:
        mean_y += provisional_entry_y

    if provisional_y_count > 0:
        mean_y /= float(provisional_y_count)
    else:
        mean_y = 0.0

    for row_idx, node_idx in enumerate(ordered_nodes):
        spaced_y_by_node[node_idx] = provisional_y[row_idx] - mean_y

    return spaced_y_by_node


def refine_component_vertical_positions(graph: nx.Graph,
                                        rows_by_layer: Dict[int, List[int]],
                                        positions: Dict[int, np.ndarray],
                                        row_gap_y: float,
                                        iterations: int = 6) -> Dict[int, np.ndarray]:
    """
    Refine vertical coordinates while keeping the node order and layer columns fixed.

    :param graph: Diagram graph.
    :param rows_by_layer: Ordered rows by layer.
    :param positions: Initial position by node.
    :param row_gap_y: Minimum spacing between vertically adjacent nodes.
    :param iterations: Number of constrained refinement iterations.
    :return: Refined position by node.
    """
    refined_positions: Dict[int, np.ndarray] = dict()
    node_idx: int

    for node_idx in positions.keys():
        refined_positions[node_idx] = np.array([float(positions[node_idx][0]), float(positions[node_idx][1])],
                                               dtype=float)

    iteration_idx: int

    # The refinement behaves like a constrained spring smoothing step:
    # x stays frozen by layer, y is pulled toward neighbour barycenters.
    for iteration_idx in range(iterations):
        layer_idx: int

        for layer_idx in sorted(list(rows_by_layer.keys())):
            ordered_nodes: List[int] = rows_by_layer[layer_idx]
            target_by_node: Dict[int, float] = compute_vertical_targets(graph=graph,
                                                                        ordered_nodes=ordered_nodes,
                                                                        current_positions=refined_positions)
            spaced_y_by_node: Dict[int, float] = enforce_vertical_spacing(ordered_nodes=ordered_nodes,
                                                                          target_by_node=target_by_node,
                                                                          row_gap_y=row_gap_y)
            current_y_center: float = 0.0
            spaced_y_center: float = 0.0

            for node_idx in ordered_nodes:
                current_y_center += float(refined_positions[node_idx][1])
                spaced_y_center += spaced_y_by_node[node_idx]

            if len(ordered_nodes) > 0:
                current_y_center /= float(len(ordered_nodes))
                spaced_y_center /= float(len(ordered_nodes))
            else:
                current_y_center = current_y_center
                spaced_y_center = spaced_y_center

            for node_idx in ordered_nodes:
                x_pos: float = float(refined_positions[node_idx][0])
                target_y: float = spaced_y_by_node[node_idx] - spaced_y_center + current_y_center
                old_y: float = float(refined_positions[node_idx][1])
                blended_y: float = 0.35 * old_y + 0.65 * target_y
                refined_positions[node_idx] = np.array([x_pos, blended_y], dtype=float)

    iteration_idx = iteration_idx
    return refined_positions


def build_hybrid_power_system_layout(graph: nx.MultiDiGraph, position_scale=0.5) -> Dict[int, np.ndarray]:
    """
    Build a hybrid layout for one-line diagrams.

    The algorithm combines three stages:
    1. dominant electrical-backbone extraction with a spanning tree,
    2. rooted tree placement using subtree spans,
    3. constrained spring-like vertical refinement with fixed tree-depth columns.

    :param position_scale: Scale of the nodes' separation
    :param graph: Diagram graph with electrical metadata.
    :return: Position by node index.
    """
    positions: Dict[int, np.ndarray] = dict()

    if graph.number_of_nodes() == 0:
        return positions
    else:
        undirected_graph: nx.MultiGraph = graph.to_undirected()

    component_origin_x: float = 0.0
    radius_gap: float = 3.8
    component_gap_x: float = 6.0
    component_nodes_set: set[int]

    for component_nodes_set in nx.connected_components(undirected_graph):
        component_nodes: List[int] = sorted(list(component_nodes_set))
        root_node: int = select_power_system_root(graph=graph, component_nodes=component_nodes)
        component_graph: nx.MultiGraph = undirected_graph.subgraph(component_nodes).copy()
        backbone_tree: nx.MultiGraph = nx.maximum_spanning_tree(component_graph, weight="strength")
        parent_by_node: Dict[int, int | None] = dict()
        children_by_parent: Dict[int, List[int]] = dict()
        depth_by_node: Dict[int, int] = dict()
        radius_by_node: Dict[int, float] = dict()
        pending_nodes: deque[int] = deque()
        node_idx: int
        sortable_entries: List[Tuple[float, float, int, str, str, int]]
        child_idx: int

        # The backbone tree removes weak mesh edges from the primary placement problem,
        # which gives a one-line shape instead of a voltage-partition shape.
        parent_by_node[root_node] = None
        depth_by_node[root_node] = 0
        radius_by_node[root_node] = 0.0
        pending_nodes.append(root_node)

        while len(pending_nodes) > 0:
            node_idx = pending_nodes.popleft()
            children_by_parent[node_idx] = list()
            sortable_entries = list()

            for child_idx in backbone_tree.neighbors(node_idx):
                if child_idx not in parent_by_node:
                    parent_by_node[child_idx] = node_idx
                    depth_by_node[child_idx] = depth_by_node[node_idx] + 1
                    radius_by_node[child_idx] = (radius_by_node[node_idx] +
                                                 get_layout_edge_radius_step(graph=component_graph,
                                                                             from_idx=node_idx,
                                                                             to_idx=child_idx,
                                                                             base_radius_gap=radius_gap))
                    pending_nodes.append(child_idx)

                    # Child ordering tries to keep strong branches and higher-voltage descendants together.
                    representative_edge_data: Dict[str, Any] = get_layout_representative_branch_edge_data(
                        graph=component_graph,
                        from_idx=node_idx,
                        to_idx=child_idx
                    )
                    sortable_entries.append((-get_layout_edge_strength_from_data(edge_data=representative_edge_data),
                                             -get_layout_graph_node_voltage_kv(graph=graph, node_idx=child_idx),
                                             -int(component_graph.degree(child_idx)),
                                             get_layout_graph_node_substation(graph=graph, node_idx=child_idx),
                                             get_layout_graph_node_name(graph=graph, node_idx=child_idx),
                                             child_idx))
                else:
                    parent_by_node[child_idx] = parent_by_node[child_idx]

            sortable_entries.sort()

            for sortable_entry in sortable_entries:
                children_by_parent[node_idx].append(sortable_entry[5])

        subtree_span_by_node: Dict[int, float] = dict()
        ordered_nodes_by_depth: Dict[int, List[int]] = dict()
        bfs_node_entries: List[Tuple[int, int]] = list()
        bfs_nodes: List[int] = list()
        reverse_node_idx: int

        for node_idx in depth_by_node.keys():
            bfs_node_entries.append((depth_by_node[node_idx], node_idx))

        bfs_node_entries.sort()

        for bfs_node_entry in bfs_node_entries:
            bfs_nodes.append(bfs_node_entry[1])

        # Subtree span is the amount of vertical space reserved for one branch corridor.
        for reverse_node_idx in range(len(bfs_nodes) - 1, -1, -1):
            node_idx = bfs_nodes[reverse_node_idx]
            children_nodes: List[int] = children_by_parent.get(node_idx, list())

            if len(children_nodes) == 0:
                subtree_span_by_node[node_idx] = 1.0
            else:
                total_span: float = 0.0

                for child_idx in children_nodes:
                    total_span += subtree_span_by_node[child_idx]

                subtree_span_by_node[node_idx] = max(total_span, 1.0)

        pending_intervals: deque[Tuple[int, float, float]] = deque()
        angle_by_node: Dict[int, float] = dict()
        pending_intervals.append((root_node, -np.pi, np.pi))

        # The radial placement allocates one angular sector per subtree, which produces
        # the spider-web style requested for meshed substation-centered grids.
        while len(pending_intervals) > 0:
            node_idx, angle_min, angle_max = pending_intervals.popleft()
            angle_by_node[node_idx] = 0.5 * (angle_min + angle_max)
            children_nodes = children_by_parent.get(node_idx, list())

            if len(children_nodes) > 0:
                total_span = 0.0

                for child_idx in children_nodes:
                    total_span += subtree_span_by_node[child_idx]

                running_angle: float = angle_min

                for child_idx in children_nodes:
                    child_span: float = subtree_span_by_node[child_idx]
                    angle_width: float = (child_span / total_span) * (angle_max - angle_min)
                    child_angle_min: float = running_angle
                    child_angle_max: float = running_angle + angle_width
                    pending_intervals.append((child_idx, child_angle_min, child_angle_max))
                    running_angle += angle_width
            else:
                children_nodes = children_nodes

        component_positions: Dict[int, np.ndarray] = dict()

        for node_idx in sorted(list(depth_by_node.keys())):
            depth_idx: int = depth_by_node[node_idx]
            ordered_nodes: List[int] | None = ordered_nodes_by_depth.get(depth_idx, None)

            if ordered_nodes is None:
                ordered_nodes = list()
                ordered_nodes_by_depth[depth_idx] = ordered_nodes
            else:
                ordered_nodes = ordered_nodes

            ordered_nodes.append(node_idx)
            radius: float = radius_by_node[node_idx]
            theta: float = angle_by_node[node_idx]
            x_pos: float = radius * np.cos(theta)
            y_pos: float = radius * np.sin(theta)
            component_positions[node_idx] = np.array([x_pos, y_pos], dtype=float)

        # The radial stage fixes the global island geometry first. A second local pass
        # then contracts transformer-linked nodes so station equipment does not stretch
        # apart simply because its surrounding subtree occupies a wide angular sector.
        component_positions = refine_positions_for_transformer_compactness(component_graph=component_graph,
                                                                           positions=component_positions,
                                                                           base_radius_gap=radius_gap)

        min_component_x: float = 0.0
        max_component_x: float = 0.0
        min_component_y: float = 0.0
        max_component_y: float = 0.0
        first_position: bool = True

        for node_idx in component_positions.keys():
            x_pos = float(component_positions[node_idx][0])
            y_pos = float(component_positions[node_idx][1])

            if first_position:
                min_component_x = x_pos
                max_component_x = x_pos
                min_component_y = y_pos
                max_component_y = y_pos
                first_position = False
            else:
                min_component_x = min(min_component_x, x_pos)
                max_component_x = max(max_component_x, x_pos)
                min_component_y = min(min_component_y, y_pos)
                max_component_y = max(max_component_y, y_pos)

        vertical_center_shift: float = -0.5 * (min_component_y + max_component_y)

        for node_idx in component_positions.keys():
            x_pos = (float(component_positions[node_idx][0]) - min_component_x + component_origin_x) * position_scale
            y_pos = (float(component_positions[node_idx][1]) + vertical_center_shift) * position_scale
            positions[node_idx] = np.array([x_pos, y_pos], dtype=float)

        component_width: float = max_component_x - min_component_x
        component_origin_x += component_width + component_gap_x

    return positions


def apply_multipartite_subsets(graph: nx.MultiDiGraph) -> nx.MultiGraph:
    """
    Create a graph copy carrying the subset attribute required by ``multipartite_layout``.

    :param graph: Diagram graph with electrical metadata.
    :return: Undirected graph copy with subset assignments.
    """
    multipartite_graph: nx.MultiGraph = graph.to_undirected()
    component_nodes_set: set[int]

    for component_nodes_set in nx.connected_components(multipartite_graph):
        component_nodes: List[int] = sorted(list(component_nodes_set))
        layer_by_node: Dict[int, int] = build_component_layer_map(graph=graph,
                                                                  undirected_graph=multipartite_graph,
                                                                  component_nodes=component_nodes)
        node_idx: int

        for node_idx in component_nodes:
            multipartite_graph.nodes[node_idx]["subset"] = layer_by_node[node_idx]

    return multipartite_graph


def build_bipartite_top_nodes(graph: nx.MultiDiGraph) -> set[int]:
    """
    Build the ``top_nodes`` set required by ``bipartite_layout``.

    :param graph: Diagram graph with electrical metadata.
    :return: Nodes assigned to the top bipartite partition.
    """
    top_nodes: set[int] = set()
    undirected_graph: nx.MultiGraph = graph.to_undirected()
    component_nodes_set: set[int]

    for component_nodes_set in nx.connected_components(undirected_graph):
        component_nodes: List[int] = sorted(list(component_nodes_set))
        layer_by_node: Dict[int, int] = build_component_layer_map(graph=graph,
                                                                  undirected_graph=undirected_graph,
                                                                  component_nodes=component_nodes)
        node_idx: int

        for node_idx in component_nodes:
            if layer_by_node[node_idx] % 2 == 0:
                top_nodes.add(node_idx)
            else:
                top_nodes = top_nodes

    return top_nodes


def build_kamada_kawai_distances(graph: nx.MultiDiGraph) -> Dict[int, Dict[int, float]]:
    """
    Build the electrical distance map for ``kamada_kawai_layout``.

    :param graph: Diagram graph with impedance metadata.
    :return: Nested distance dictionary accepted by NetworkX.
    """
    undirected_graph: nx.MultiGraph = graph.to_undirected()
    distances: Dict[int, Dict[int, float]] = dict(nx.all_pairs_dijkstra_path_length(undirected_graph,
                                                                                    weight="impedance"))
    return distances


def calculate_schematic_layout(graph: nx.MultiDiGraph, sel: str) -> Dict[int, np.ndarray]:
    """
    Calculate one automatic schematic layout explicitly for every supported mode.

    :param graph: Diagram graph with electrical metadata.
    :param sel: Layout mode name selected in the GUI.
    :return: Position by node index.
    """
    calculated_positions: Dict[int, np.ndarray]
    undirected_graph: nx.MultiGraph = graph.to_undirected()

    if sel == "power_system_layout":
        calculated_positions = build_hybrid_power_system_layout(graph=graph)
    elif sel == "random_layout":
        calculated_positions = nx.random_layout(graph, seed=7)
    elif sel == "spring_layout":
        calculated_positions = nx.spring_layout(graph, weight="strength", iterations=300, scale=10, seed=7)
    elif sel == "shell_layout":
        calculated_positions = nx.shell_layout(graph, scale=10)
    elif sel == "circular_layout":
        calculated_positions = nx.circular_layout(graph, scale=10)
    elif sel == "kamada_kawai":
        distances: Dict[int, Dict[int, float]] = build_kamada_kawai_distances(graph=graph)
        calculated_positions = nx.kamada_kawai_layout(graph, dist=distances, scale=10)
    elif sel == "fruchterman_reingold_layout":
        calculated_positions = nx.fruchterman_reingold_layout(graph, weight="strength", scale=10, seed=7)
    elif sel == "spectral_layout":
        calculated_positions = nx.spectral_layout(graph, weight="strength", scale=10)
    elif sel == "arf":
        calculated_positions = nx.arf_layout(graph)
    elif sel == "planar":
        is_planar: bool
        is_planar, _ = nx.check_planarity(undirected_graph)
        if is_planar:
            calculated_positions = nx.planar_layout(undirected_graph, scale=10)
        else:
            calculated_positions = build_hybrid_power_system_layout(graph=graph)
    elif sel == "bipartite":
        is_bipartite: bool = nx.is_bipartite(undirected_graph)
        if is_bipartite:
            top_nodes: set[int] = build_bipartite_top_nodes(graph=graph)
            calculated_positions = nx.bipartite_layout(undirected_graph, nodes=top_nodes, scale=10)
        else:
            calculated_positions = build_hybrid_power_system_layout(graph=graph)
    elif sel == "multipartite":
        multipartite_graph: nx.Graph = apply_multipartite_subsets(graph=graph)
        calculated_positions = nx.multipartite_layout(multipartite_graph, subset_key="subset", scale=10)
    else:
        calculated_positions = build_hybrid_power_system_layout(graph=graph)

    return calculated_positions
