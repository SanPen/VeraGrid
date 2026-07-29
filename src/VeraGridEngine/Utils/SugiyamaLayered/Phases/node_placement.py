# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from VeraGridEngine.Utils.SugiyamaLayered.Phases.long_edges import VirtualNode
from VeraGridEngine.Utils.SugiyamaLayered.model import SugiyamaNode, SugiyamaPort
from VeraGridEngine.Utils.SugiyamaLayered.options import (
    FixedAlignment,
    LayoutDirection,
    PortAlignment,
    PortConstraint,
    PortSide,
    coerce_enum_value,
)
from VeraGridEngine.Utils.SugiyamaLayered.pipeline import LayoutContext, LayoutPhaseBase


def _node_dimensions(
    node_id: str,
    expanded_nodes: dict[str, VirtualNode],
    node_by_id: dict[str, SugiyamaNode],
) -> tuple[float, float]:
    """Return the width and height of one expanded node.

    :param node_id: Node identifier.
    :param expanded_nodes: Expanded-node lookup.
    :param node_by_id: Original graph node lookup.
    :returns: Node width and height.
    """
    dimensions: tuple[float, float] = (30.0, 30.0)
    node_info: VirtualNode | None = expanded_nodes.get(node_id, None)

    if node_info is not None:
        dimensions = (node_info.width, node_info.height)
    else:
        node: SugiyamaNode | None = node_by_id.get(node_id, None)
        if node is not None:
            dimensions = (node.width, node.height)
        else:
            dimensions = dimensions

    return dimensions


def _node_height(
    node_id: str,
    expanded_nodes: dict[str, VirtualNode],
    node_by_id: dict[str, SugiyamaNode],
) -> float:
    """Return the height of one expanded node.

    :param node_id: Node identifier.
    :param expanded_nodes: Expanded-node lookup.
    :param node_by_id: Original graph node lookup.
    :returns: Node height.
    """
    return _node_dimensions(node_id, expanded_nodes, node_by_id)[1]


def _node_width(
    node_id: str,
    expanded_nodes: dict[str, VirtualNode],
    node_by_id: dict[str, SugiyamaNode],
) -> float:
    """Return the width of one expanded node.

    :param node_id: Node identifier.
    :param expanded_nodes: Expanded-node lookup.
    :param node_by_id: Original graph node lookup.
    :returns: Node width.
    """
    return _node_dimensions(node_id, expanded_nodes, node_by_id)[0]


def _layout_direction(context: LayoutContext) -> LayoutDirection:
    """Return the normalized layout direction.

    :param context: Shared pipeline context.
    :returns: Layout direction.
    """
    options: dict[str, Any] = context.option_resolver.resolve_for_element(context.graph.layout_options)
    direction: LayoutDirection = options.get("org.vera.sugiyama.direction", LayoutDirection.RIGHT)
    return direction


def _fixed_alignment(context: LayoutContext) -> FixedAlignment:
    """Return the configured fixed Brandes-Koepf alignment.

    :param context: Shared pipeline context.
    :returns: Fixed alignment option.
    """
    options: dict[str, Any] = context.option_resolver.resolve_for_element(context.graph.layout_options)
    alignment: FixedAlignment = options.get(
        "org.vera.sugiyama.layered.nodePlacement.bk.fixedAlignment",
        FixedAlignment.NONE,
    )
    return alignment


def _port_side(port: SugiyamaPort) -> PortSide:
    """Return the explicit side of one port.

    :param port: Port to inspect.
    :returns: Normalized side name.
    """
    side_value: Any = (
        port.get_layout_option("org.vera.sugiyama.port.side", None)
        or port.get_property("side", None)
        or ""
    )
    side: PortSide = coerce_enum_value(PortSide, side_value, PortSide.UNDEFINED)
    return side


def _effective_port_side(port: SugiyamaPort, role: str, direction: LayoutDirection) -> PortSide:
    """Resolve the effective side of one port.

    :param port: Port to inspect.
    :param role: Port role string.
    :param direction: Layout direction.
    :returns: Effective side name.
    """
    explicit_side: PortSide = _port_side(port)
    resolved_side: PortSide = explicit_side

    if explicit_side is not PortSide.UNDEFINED:
        resolved_side = explicit_side
    else:
        if direction is LayoutDirection.LEFT:
            resolved_side = PortSide.WEST if role == "output" else PortSide.EAST
        else:
            if direction is LayoutDirection.DOWN:
                resolved_side = PortSide.SOUTH if role == "output" else PortSide.NORTH
            else:
                if direction is LayoutDirection.UP:
                    resolved_side = PortSide.NORTH if role == "output" else PortSide.SOUTH
                else:
                    resolved_side = PortSide.EAST if role == "output" else PortSide.WEST

    return resolved_side


def _port_side_rank(side: PortSide) -> int:
    """Return the stable rank of one port side.

    :param side: Side name.
    :returns: Stable numeric rank.
    """
    rank: int = 4

    if side is PortSide.WEST:
        rank = 0
    else:
        if side is PortSide.NORTH:
            rank = 1
        else:
            if side is PortSide.SOUTH:
                rank = 2
            else:
                if side is PortSide.EAST:
                    rank = 3
                else:
                    rank = 4

    return rank


def _read_integer_candidate(value: Any) -> int | None:
    """Parse an optional integer value.

    :param value: Raw value to parse.
    :returns: Parsed integer or ``None``.
    """
    parsed_value: int | None = None

    if value is not None:
        try:
            parsed_value = int(value)
        except (TypeError, ValueError):
            parsed_value = None
    else:
        parsed_value = None

    return parsed_value


def _port_sort_key(port: SugiyamaPort) -> tuple[int, int, str]:
    """Return the stable ordering key for one port.

    :param port: Port to rank.
    :returns: Stable ordering key.
    """
    side_rank: int = _port_side_rank(_port_side(port))
    index_value: Any = port.get_property("port_index", 0)
    index: int = _read_integer_candidate(index_value) or 0
    return side_rank, index, port.identifier


def _sort_ports(ports: list[SugiyamaPort]) -> list[SugiyamaPort]:
    """Sort ports deterministically.

    :param ports: Ports to sort.
    :returns: Sorted ports.
    """
    decorated_ports: list[tuple[tuple[int, int, str], SugiyamaPort]] = list()
    sorted_ports: list[SugiyamaPort] = list()
    port: SugiyamaPort

    for port in ports:
        decorated_ports.append((_port_sort_key(port), port))

    decorated_ports.sort()

    for _, resolved_port in decorated_ports:
        sorted_ports.append(resolved_port)

    return sorted_ports


def _port_alignment(node: SugiyamaNode, context: LayoutContext, side: PortSide) -> PortAlignment:
    """Return the alignment policy for one node side.

    :param node: Node to inspect.
    :param context: Shared pipeline context.
    :param side: Side name.
    :returns: Port-alignment policy.
    """
    options: dict[str, Any] = context.option_resolver.resolve_for_element(
        context.graph.layout_options,
        node.layout_options,
    )
    side_key: str = f"org.vera.sugiyama.portAlignment.{side.name.lower()}"
    value: Any = options.get(side_key, None) or options.get(
        "org.vera.sugiyama.portAlignment.default",
        PortAlignment.CENTER,
    )
    alignment: PortAlignment = coerce_enum_value(PortAlignment, value, PortAlignment.CENTER)
    return alignment


def _node_port_constraints(node: SugiyamaNode, context: LayoutContext) -> PortConstraint:
    """Return the port-constraint policy of one node.

    :param node: Node to inspect.
    :param context: Shared pipeline context.
    :returns: Port-constraint policy.
    """
    options: dict[str, Any] = context.option_resolver.resolve_for_element(
        context.graph.layout_options,
        node.layout_options,
    )
    value: Any = options.get("org.vera.sugiyama.portConstraints", PortConstraint.UNDEFINED)
    constraints: PortConstraint = coerce_enum_value(PortConstraint, value, PortConstraint.UNDEFINED)
    return constraints


def _align_norm(norm: float, alignment: PortAlignment, count: int) -> float:
    """Adjust a normalized side coordinate according to the alignment option.

    :param norm: Raw normalized coordinate.
    :param alignment: Alignment mode.
    :param count: Number of ports on the side.
    :returns: Adjusted normalized coordinate.
    """
    adjusted_norm: float = norm

    if alignment is PortAlignment.BEGIN:
        adjusted_norm = min(norm, 0.25 if count > 1 else 0.5)
    else:
        if alignment is PortAlignment.END:
            adjusted_norm = max(norm, 0.75 if count > 1 else 0.5)
        else:
            adjusted_norm = norm

    return adjusted_norm


def _assign_port_positions(context: LayoutContext) -> None:
    """Assign port coordinates once node coordinates are known.

    :param context: Shared pipeline context.
    :returns: ``None``.
    """
    direction: LayoutDirection = _layout_direction(context)
    node: SugiyamaNode

    # Port coordinates are derived last because they depend on the final node box and
    # on the side chosen from layout direction and explicit constraints.
    for node in context.graph.children:
        if node.x is not None and node.y is not None and node.ports:
            constraints: PortConstraint = _node_port_constraints(node, context)
            grouped_ports: dict[PortSide, list[SugiyamaPort]] = dict()
            grouped_ports[PortSide.WEST] = list()
            grouped_ports[PortSide.EAST] = list()
            grouped_ports[PortSide.NORTH] = list()
            grouped_ports[PortSide.SOUTH] = list()
            grouped_ports[PortSide.UNDEFINED] = list()

            sorted_ports: list[SugiyamaPort] = _sort_ports(node.ports)
            port: SugiyamaPort
            for port in sorted_ports:
                role: str = str(port.get_property("role", "")).lower()
                effective_side: PortSide = _effective_port_side(port, role, direction)
                target_ports: list[SugiyamaPort] = grouped_ports.get(effective_side, None) or list()
                target_ports.append(port)
                grouped_ports[effective_side] = target_ports

            side: PortSide
            ports_on_side: list[SugiyamaPort]
            for side, ports_on_side in grouped_ports.items():
                if ports_on_side:
                    alignment_side: PortSide = side if side is not PortSide.UNDEFINED else PortSide.EAST
                    alignment: PortAlignment = _port_alignment(node, context, alignment_side)
                    count: int = len(ports_on_side)
                    port_index: int
                    for port_index, port in enumerate(ports_on_side):
                        if constraints in {PortConstraint.FIXED_POS, PortConstraint.FIXED_RATIO} and port.x is not None and port.y is not None:
                            port.x = port.x
                            port.y = port.y
                        else:
                            norm: float = (port_index + 1) / (count + 1) if count else 0.5
                            norm = _align_norm(norm, alignment, count)

                            if side is PortSide.WEST:
                                port.x = node.x - port.width / 2.0
                                port.y = node.y + norm * node.height - port.height / 2.0
                            else:
                                if side is PortSide.NORTH:
                                    port.x = node.x + norm * node.width - port.width / 2.0
                                    port.y = node.y - port.height / 2.0
                                else:
                                    if side is PortSide.SOUTH:
                                        port.x = node.x + norm * node.width - port.width / 2.0
                                        port.y = node.y + node.height - port.height / 2.0
                                    else:
                                        port.x = node.x + node.width - port.width / 2.0
                                        port.y = node.y + norm * node.height - port.height / 2.0
                else:
                    grouped_ports = grouped_ports
        else:
            node = node


def _layer_extent(
    node_ids: list[str],
    expanded_nodes: dict[str, VirtualNode],
    node_by_id: dict[str, SugiyamaNode],
    vertical_flow: bool,
) -> float:
    """Return the primary-axis extent of one layer.

    :param node_ids: Node identifiers in the layer.
    :param expanded_nodes: Expanded-node lookup.
    :param node_by_id: Original graph node lookup.
    :param vertical_flow: Whether layers are stacked vertically.
    :returns: Layer extent along the primary axis.
    """
    extent: float = 30.0
    current_extent: float = 30.0
    node_id: str

    for node_id in node_ids:
        if vertical_flow:
            current_extent = _node_height(node_id, expanded_nodes, node_by_id)
        else:
            current_extent = _node_width(node_id, expanded_nodes, node_by_id)

        if current_extent > extent:
            extent = current_extent
        else:
            extent = extent

    return extent


def _assign_node_coordinates(
    context: LayoutContext,
    ordered_layers: dict[int, list[str]],
    expanded_nodes: dict[str, VirtualNode],
    node_by_id: dict[str, SugiyamaNode],
    spacing_x: float,
    spacing_y: float,
    y_of_node: dict[str, float],
) -> tuple[dict[str, tuple[float, float]], dict[int, float]]:
    """Assign primary-axis coordinates to nodes once orthogonal positions are known.

    :param context: Shared pipeline context.
    :param ordered_layers: Ordered nodes per layer.
    :param expanded_nodes: Expanded-node lookup.
    :param node_by_id: Original graph node lookup.
    :param spacing_x: Horizontal spacing between layers.
    :param spacing_y: Vertical spacing between layers.
    :param y_of_node: Orthogonal coordinate per node.
    :returns: Virtual positions and primary-axis layer coordinates.
    """
    direction: LayoutDirection = _layout_direction(context)
    vertical_flow: bool = direction in {LayoutDirection.DOWN, LayoutDirection.UP}
    reverse_flow: bool = direction in {LayoutDirection.LEFT, LayoutDirection.UP}
    layer_positions: dict[int, float] = dict()
    current_position: float = 0.0
    virtual_positions: dict[str, tuple[float, float]] = dict()

    # Layer positions along the flow direction are computed first so all nodes in the
    # same layer can share the same primary-axis coordinate.
    layer_id: int
    node_ids: list[str]
    for layer_id, node_ids in sorted(ordered_layers.items()):
        layer_positions[layer_id] = current_position
        layer_extent: float = _layer_extent(node_ids, expanded_nodes, node_by_id, vertical_flow)
        if vertical_flow:
            current_position += layer_extent + spacing_y
        else:
            current_position += layer_extent + spacing_x

    max_layer_position: float = max(layer_positions.values(), default=0.0)

    for layer_id, node_ids in sorted(ordered_layers.items()):
        layer_position: float = layer_positions[layer_id]
        if reverse_flow:
            layer_position = max_layer_position - layer_position
        else:
            layer_position = layer_position

        node_id: str
        for node_id in node_ids:
            orthogonal_position: float = y_of_node.get(node_id, 0.0)
            if vertical_flow:
                virtual_positions[node_id] = (orthogonal_position, layer_position)
            else:
                virtual_positions[node_id] = (layer_position, orthogonal_position)

    return virtual_positions, layer_positions


def _neighbor_sort_key(node_id: str, order_in_layer: dict[str, int]) -> tuple[int, str]:
    """Return the stable key for one neighbor lookup.

    :param node_id: Neighbor identifier.
    :param order_in_layer: Position of nodes inside their layer.
    :returns: Stable sorting key.
    """
    return order_in_layer.get(node_id, 0), node_id


def _ordered_neighbors(
    node_id: str,
    neighbors: dict[str, set[str]],
    order_in_layer: dict[str, int],
) -> list[str]:
    """Return neighbors ordered by their in-layer position.

    :param node_id: Node whose neighbors are requested.
    :param neighbors: Adjacency mapping.
    :param order_in_layer: Position of nodes inside their layer.
    :returns: Ordered neighbor identifiers.
    """
    decorated_neighbors: list[tuple[tuple[int, str], str]] = list()
    ordered: list[str] = list()
    neighbor_id: str

    for neighbor_id in neighbors.get(node_id, set()):
        decorated_neighbors.append((_neighbor_sort_key(neighbor_id, order_in_layer), neighbor_id))

    decorated_neighbors.sort()

    for _, resolved_neighbor in decorated_neighbors:
        ordered.append(resolved_neighbor)

    return ordered


def _median_neighbor(
    node_id: str,
    neighbors: dict[str, set[str]],
    order_in_layer: dict[str, int],
) -> str | None:
    """Return the median neighbor of one node.

    :param node_id: Node whose median neighbor is requested.
    :param neighbors: Adjacency mapping.
    :param order_in_layer: Position of nodes inside their layer.
    :returns: Median neighbor or ``None``.
    """
    ordered: list[str] = _ordered_neighbors(node_id, neighbors, order_in_layer)
    median_id: str | None = None

    if ordered:
        median_id = ordered[(len(ordered) - 1) // 2]
    else:
        median_id = None

    return median_id


def _collect_all_layer_nodes(ordered_layers: dict[int, list[str]], layer_ids: list[int]) -> list[str]:
    """Collect all node identifiers from the ordered layers.

    :param ordered_layers: Ordered nodes per layer.
    :param layer_ids: Layer identifiers in traversal order.
    :returns: Flattened node identifiers.
    """
    all_nodes: list[str] = list()
    layer_id: int

    for layer_id in layer_ids:
        all_nodes.extend(ordered_layers[layer_id])

    return all_nodes


def _alignment_pass(
    ordered_layers: dict[int, list[str]],
    layer_ids: list[int],
    order_in_layer: dict[str, int],
    neighbors: dict[str, set[str]],
    reverse_layers: bool,
) -> tuple[dict[str, str], dict[str, str]]:
    """Run one Brandes-Koepf alignment pass.

    :param ordered_layers: Ordered nodes per layer.
    :param layer_ids: Layer identifiers in traversal order.
    :param order_in_layer: Position of nodes inside their layer.
    :param neighbors: Adjacency mapping used by the pass.
    :param reverse_layers: Whether the pass traverses layers in reverse order.
    :returns: Root and alignment maps.
    """
    all_nodes: list[str] = _collect_all_layer_nodes(ordered_layers, layer_ids)
    root: dict[str, str] = dict()
    align: dict[str, str] = dict()
    traversed_layers: list[int] = list(layer_ids)
    node_id: str

    for node_id in all_nodes:
        root[node_id] = node_id
        align[node_id] = node_id

    if reverse_layers:
        traversed_layers = list(reversed(traversed_layers))
    else:
        traversed_layers = traversed_layers

    # Each pass aligns nodes to median neighbors to build vertical blocks that later
    # share a common orthogonal coordinate.
    layer_id: int
    for layer_id in traversed_layers:
        layer_nodes: list[str] = list(ordered_layers[layer_id])
        barrier: int = -1

        if reverse_layers:
            layer_nodes.reverse()
            barrier = len(ordered_layers[layer_id])
        else:
            barrier = -1

        for node_id in layer_nodes:
            median_id: str | None = _median_neighbor(node_id, neighbors, order_in_layer)
            if median_id is not None:
                median_position: int = order_in_layer.get(median_id, 0)
                can_align: bool = median_position < barrier if reverse_layers else median_position > barrier

                if can_align and align[node_id] == node_id:
                    align[median_id] = node_id
                    root[node_id] = root[median_id]
                    barrier = median_position
                else:
                    barrier = barrier
            else:
                barrier = barrier

    return root, align


def _build_blocks(root: dict[str, str], align: dict[str, str]) -> list[list[str]]:
    """Build aligned blocks from root and alignment mappings.

    :param root: Block-root mapping.
    :param align: Successor alignment mapping.
    :returns: Blocks of vertically aligned nodes.
    """
    visited: set[str] = set()
    blocks: list[list[str]] = list()
    node_id: str

    for node_id in root:
        if node_id not in visited and root[node_id] == node_id:
            block: list[str] = list()
            current_id: str = node_id
            block.append(current_id)
            visited.add(current_id)

            while align[current_id] != current_id:
                current_id = align[current_id]
                block.append(current_id)
                visited.add(current_id)

            blocks.append(block)
        else:
            visited = visited

    # The alignment pass can leave orphan nodes when a previous median link is
    # superseded by a later one. Those nodes still exist in the layered order and
    # must receive a singleton block so downstream compaction sees a total mapping.
    for node_id in root:
        if node_id not in visited:
            blocks.append([node_id])
            visited.add(node_id)
        else:
            visited = visited

    return blocks


def _block_neighbors(
    ordered_layers: dict[int, list[str]],
    layer_of: dict[str, int],
    order_in_layer: dict[str, int],
    blocks: list[list[str]],
    block_of: dict[str, int],
    block_index: int,
) -> set[int]:
    """Return adjacent block indices sharing a layer neighborhood.

    :param ordered_layers: Ordered nodes per layer.
    :param layer_of: Layer index per node.
    :param order_in_layer: Position of nodes inside their layer.
    :param blocks: Block contents.
    :param block_of: Block index per node.
    :param block_index: Block being inspected.
    :returns: Neighbor block indices.
    """
    neighbor_blocks: set[int] = set()
    node_id: str

    for node_id in blocks[block_index]:
        layer_id: int = layer_of[node_id]
        order_index: int = order_in_layer[node_id]
        layer_nodes: list[str] = ordered_layers[layer_id]

        if order_index > 0:
            left_node_id: str = layer_nodes[order_index - 1]
            left_block_index: int = block_of[left_node_id]
            if left_block_index != block_index:
                neighbor_blocks.add(left_block_index)
            else:
                neighbor_blocks = neighbor_blocks
        else:
            neighbor_blocks = neighbor_blocks

        if order_index < len(layer_nodes) - 1:
            right_node_id: str = layer_nodes[order_index + 1]
            right_block_index: int = block_of[right_node_id]
            if right_block_index != block_index:
                neighbor_blocks.add(right_block_index)
            else:
                neighbor_blocks = neighbor_blocks
        else:
            neighbor_blocks = neighbor_blocks

    return neighbor_blocks


def _initial_block_offsets(
    ordered_layers: dict[int, list[str]],
    layer_of: dict[str, int],
    order_in_layer: dict[str, int],
    blocks: list[list[str]],
    block_of: dict[str, int],
    expanded_nodes: dict[str, VirtualNode],
    node_by_id: dict[str, SugiyamaNode],
    spacing_y: float,
) -> tuple[dict[int, float], dict[int, float]]:
    """Build initial block positions and heights.

    :param ordered_layers: Ordered nodes per layer.
    :param layer_of: Layer index per node.
    :param order_in_layer: Position of nodes inside their layer.
    :param blocks: Block contents.
    :param block_of: Block index per node.
    :param expanded_nodes: Expanded-node lookup.
    :param node_by_id: Original graph node lookup.
    :param spacing_y: Vertical node spacing.
    :returns: Initial block offsets and heights.
    """
    block_y: dict[int, float] = dict()
    block_height: dict[int, float] = dict()
    block_index: int
    block_nodes: list[str]

    for block_index, block_nodes in enumerate(blocks):
        first_node_id: str = block_nodes[0]
        layer_id: int = layer_of[first_node_id]
        order_index: int = order_in_layer[first_node_id]
        preceding_nodes: list[str] = ordered_layers[layer_id][:order_index]
        base_y: float = 0.0
        node_id: str

        for node_id in preceding_nodes:
            if block_of[node_id] != block_index:
                base_y += _node_height(node_id, expanded_nodes, node_by_id) + spacing_y
            else:
                base_y = base_y

        block_y[block_index] = base_y
        block_height[block_index] = max(
            _node_height(node_id, expanded_nodes, node_by_id)
            for node_id in block_nodes
        )

    return block_y, block_height


def _block_min_allowed(
    block_index: int,
    block_nodes: list[str],
    ordered_layers: dict[int, list[str]],
    layer_of: dict[str, int],
    order_in_layer: dict[str, int],
    blocks: list[list[str]],
    block_of: dict[str, int],
    block_y: dict[int, float],
    expanded_nodes: dict[str, VirtualNode],
    node_by_id: dict[str, SugiyamaNode],
    spacing_y: float,
) -> float:
    """Return the minimum feasible vertical coordinate for one block.

    :param block_index: Block being placed.
    :param block_nodes: Nodes inside the block.
    :param ordered_layers: Ordered nodes per layer.
    :param layer_of: Layer index per node.
    :param order_in_layer: Position of nodes inside their layer.
    :param blocks: Block contents.
    :param block_of: Block index per node.
    :param block_y: Current block positions.
    :param expanded_nodes: Expanded-node lookup.
    :param node_by_id: Original graph node lookup.
    :param spacing_y: Vertical node spacing.
    :returns: Minimum feasible y coordinate.
    """
    minimum_y: float = 0.0
    neighbor_block_index: int

    for neighbor_block_index in sorted(
        _block_neighbors(ordered_layers, layer_of, order_in_layer, blocks, block_of, block_index)
    ):
        node_id: str
        other_node_id: str
        for node_id in block_nodes:
            for other_node_id in blocks[neighbor_block_index]:
                same_layer: bool = layer_of[node_id] == layer_of[other_node_id]
                is_left_neighbor: bool = order_in_layer[other_node_id] < order_in_layer[node_id]
                if same_layer and is_left_neighbor:
                    candidate_y: float = (
                        block_y[neighbor_block_index]
                        + _node_height(other_node_id, expanded_nodes, node_by_id)
                        + spacing_y
                    )
                    if candidate_y > minimum_y:
                        minimum_y = candidate_y
                    else:
                        minimum_y = minimum_y
                else:
                    minimum_y = minimum_y

    return minimum_y


def _block_barycenter_target(
    block_nodes: list[str],
    block_height: float,
    block_of: dict[str, int],
    block_y: dict[int, float],
    predecessors: dict[str, set[str]],
    successors: dict[str, set[str]],
    expanded_nodes: dict[str, VirtualNode],
    node_by_id: dict[str, SugiyamaNode],
) -> float | None:
    """Return the barycentric target position for one block.

    :param block_nodes: Nodes inside the block.
    :param block_height: Height of the block.
    :param block_of: Block index per node.
    :param block_y: Current block positions.
    :param predecessors: Predecessor adjacency.
    :param successors: Successor adjacency.
    :param expanded_nodes: Expanded-node lookup.
    :param node_by_id: Original graph node lookup.
    :returns: Target y coordinate or ``None``.
    """
    barycenters: list[float] = list()
    node_id: str

    # The block target is based on adjacent blocks so vertically aligned chains stay
    # close to the center of their incident edges.
    for node_id in block_nodes:
        connected_blocks: list[str] = list()
        neighbor_node_id: str

        for neighbor_node_id in predecessors.get(node_id, set()):
            if neighbor_node_id in block_of:
                connected_blocks.append(neighbor_node_id)
            else:
                connected_blocks = connected_blocks

        for neighbor_node_id in successors.get(node_id, set()):
            if neighbor_node_id in block_of:
                connected_blocks.append(neighbor_node_id)
            else:
                connected_blocks = connected_blocks

        if connected_blocks:
            total_center: float = 0.0
            for neighbor_node_id in connected_blocks:
                total_center += (
                    block_y[block_of[neighbor_node_id]]
                    + _node_height(neighbor_node_id, expanded_nodes, node_by_id) / 2.0
                )
            barycenters.append(total_center / len(connected_blocks))
        else:
            barycenters = barycenters

    if barycenters:
        return (sum(barycenters) / len(barycenters)) - block_height / 2.0
    else:
        return None


def _compact_blocks(
    ordered_layers: dict[int, list[str]],
    layer_of: dict[str, int],
    order_in_layer: dict[str, int],
    blocks: list[list[str]],
    block_of: dict[str, int],
    expanded_nodes: dict[str, VirtualNode],
    node_by_id: dict[str, SugiyamaNode],
    predecessors: dict[str, set[str]],
    successors: dict[str, set[str]],
    spacing_y: float,
) -> dict[int, float]:
    """Compact vertical blocks while respecting layer order.

    :param ordered_layers: Ordered nodes per layer.
    :param layer_of: Layer index per node.
    :param order_in_layer: Position of nodes inside their layer.
    :param blocks: Block contents.
    :param block_of: Block index per node.
    :param expanded_nodes: Expanded-node lookup.
    :param node_by_id: Original graph node lookup.
    :param predecessors: Predecessor adjacency.
    :param successors: Successor adjacency.
    :param spacing_y: Vertical node spacing.
    :returns: Vertical coordinate per block.
    """
    block_y: dict[int, float]
    block_height: dict[int, float]
    block_y, block_height = _initial_block_offsets(
        ordered_layers,
        layer_of,
        order_in_layer,
        blocks,
        block_of,
        expanded_nodes,
        node_by_id,
        spacing_y,
    )

    changed: bool = True
    iteration: int = 0

    # A bounded relaxation loop is enough here because the block system is only a
    # heuristic refinement of the in-layer ordering produced by previous phases.
    while changed and iteration < 24:
        iteration += 1
        changed = False

        block_index: int
        block_nodes: list[str]
        for block_index, block_nodes in enumerate(blocks):
            minimum_y: float = _block_min_allowed(
                block_index,
                block_nodes,
                ordered_layers,
                layer_of,
                order_in_layer,
                blocks,
                block_of,
                block_y,
                expanded_nodes,
                node_by_id,
                spacing_y,
            )
            target_y: float | None = _block_barycenter_target(
                block_nodes,
                block_height[block_index],
                block_of,
                block_y,
                predecessors,
                successors,
                expanded_nodes,
                node_by_id,
            )
            desired_y: float = block_y[block_index]
            if target_y is not None:
                desired_y = target_y
            else:
                desired_y = desired_y

            new_y: float = max(minimum_y, desired_y)
            if abs(new_y - block_y[block_index]) > 1e-6:
                block_y[block_index] = new_y
                changed = True
            else:
                changed = changed

    return block_y


def _positions_from_blocks(blocks: list[list[str]], block_y: dict[int, float]) -> dict[str, float]:
    """Expand block coordinates into node coordinates.

    :param blocks: Block contents.
    :param block_y: Vertical coordinate per block.
    :returns: Vertical coordinate per node.
    """
    y_of_node: dict[str, float] = dict()
    block_index: int
    block_nodes: list[str]

    for block_index, block_nodes in enumerate(blocks):
        node_id: str
        for node_id in block_nodes:
            y_of_node[node_id] = block_y[block_index]

    return y_of_node


def _available_alignment_passes(
    fixed_alignment: FixedAlignment,
    predecessors: dict[str, set[str]],
    successors: dict[str, set[str]],
) -> list[tuple[dict[str, set[str]], bool]]:
    """Return the alignment passes requested by the fixed-alignment option.

    :param fixed_alignment: Fixed-alignment option.
    :param predecessors: Predecessor adjacency.
    :param successors: Successor adjacency.
    :returns: Alignment pass definitions.
    """
    all_passes: dict[FixedAlignment, tuple[dict[str, set[str]], bool]] = dict()
    passes: list[tuple[dict[str, set[str]], bool]] = list()

    all_passes[FixedAlignment.LEFT_UP] = (predecessors, False)
    all_passes[FixedAlignment.RIGHT_UP] = (predecessors, True)
    all_passes[FixedAlignment.LEFT_DOWN] = (successors, False)
    all_passes[FixedAlignment.RIGHT_DOWN] = (successors, True)

    if fixed_alignment in all_passes:
        passes.append(all_passes[fixed_alignment])
    else:
        pass_key: FixedAlignment
        for pass_key in all_passes:
            passes.append(all_passes[pass_key])

    return passes


def _build_block_of(blocks: list[list[str]]) -> dict[str, int]:
    """Build the block index of every node.

    :param blocks: Block contents.
    :returns: Block index per node.
    """
    block_of: dict[str, int] = dict()
    block_index: int
    block_nodes: list[str]

    for block_index, block_nodes in enumerate(blocks):
        node_id: str
        for node_id in block_nodes:
            block_of[node_id] = block_index

    return block_of


def _median_of_values(values: list[float]) -> float:
    """Return the median of a non-empty numeric list.

    :param values: Numeric values.
    :returns: Median value.
    """
    ordered_values: list[float] = sorted(values)
    middle_index: int = len(ordered_values) // 2

    if len(ordered_values) % 2 == 1:
        return ordered_values[middle_index]
    else:
        return (ordered_values[middle_index - 1] + ordered_values[middle_index]) / 2.0


def _compute_vertical_coordinates(
    ordered_layers: dict[int, list[str]],
    layer_of: dict[str, int],
    order_in_layer: dict[str, int],
    predecessors: dict[str, set[str]],
    successors: dict[str, set[str]],
    expanded_nodes: dict[str, VirtualNode],
    node_by_id: dict[str, SugiyamaNode],
    spacing_y: float,
    fixed_alignment: FixedAlignment,
) -> dict[str, float]:
    """Compute orthogonal coordinates with multi-pass block alignment.

    :param ordered_layers: Ordered nodes per layer.
    :param layer_of: Layer index per node.
    :param order_in_layer: Position of nodes inside their layer.
    :param predecessors: Predecessor adjacency.
    :param successors: Successor adjacency.
    :param expanded_nodes: Expanded-node lookup.
    :param node_by_id: Original graph node lookup.
    :param spacing_y: Vertical node spacing.
    :param fixed_alignment: Fixed Brandes-Koepf alignment.
    :returns: Orthogonal coordinate per node.
    """
    layer_ids: list[int] = sorted(ordered_layers)
    variants: list[dict[str, float]] = list()
    passes: list[tuple[dict[str, set[str]], bool]] = _available_alignment_passes(
        fixed_alignment,
        predecessors,
        successors,
    )

    pass_neighbors: dict[str, set[str]]
    reverse_layers: bool
    for pass_neighbors, reverse_layers in passes:
        root: dict[str, str]
        align: dict[str, str]
        root, align = _alignment_pass(
            ordered_layers,
            layer_ids,
            order_in_layer,
            pass_neighbors,
            reverse_layers,
        )
        blocks: list[list[str]] = _build_blocks(root, align)
        block_of: dict[str, int] = _build_block_of(blocks)
        block_y: dict[int, float] = _compact_blocks(
            ordered_layers,
            layer_of,
            order_in_layer,
            blocks,
            block_of,
            expanded_nodes,
            node_by_id,
            predecessors,
            successors,
            spacing_y,
        )
        variants.append(_positions_from_blocks(blocks, block_y))

    y_of_node: dict[str, float] = dict()
    all_nodes: list[str] = _collect_all_layer_nodes(ordered_layers, layer_ids)
    node_id: str

    # The final orthogonal coordinate is the median across all alignment variants to
    # reduce bias from any single sweep direction.
    for node_id in all_nodes:
        coordinates: list[float] = list()
        variant: dict[str, float]

        for variant in variants:
            coordinates.append(variant.get(node_id, 0.0))

        if coordinates:
            y_of_node[node_id] = _median_of_values(coordinates)
        else:
            y_of_node[node_id] = 0.0

    return y_of_node


def _stack_layer(
    node_ids: list[str],
    y_of_node: dict[str, float],
    spacing_y: float,
    expanded_nodes: dict[str, VirtualNode],
    node_by_id: dict[str, SugiyamaNode],
) -> None:
    """Resolve residual overlaps within one layer by vertical stacking.

    :param node_ids: Node identifiers in the layer.
    :param y_of_node: Orthogonal coordinate per node.
    :param spacing_y: Vertical node spacing.
    :param expanded_nodes: Expanded-node lookup.
    :param node_by_id: Original graph node lookup.
    :returns: ``None``.
    """
    cursor_y: float = 0.0
    node_id: str

    for node_id in node_ids:
        node_y: float = max(cursor_y, y_of_node.get(node_id, 0.0))
        y_of_node[node_id] = node_y
        cursor_y = node_y + _node_height(node_id, expanded_nodes, node_by_id) + spacing_y


def _straighten_dummy_chains(
    edge_paths: dict[str, list[str]],
    y_of_node: dict[str, float],
    expanded_nodes: dict[str, VirtualNode],
    node_by_id: dict[str, SugiyamaNode],
    ordered_layers: dict[int, list[str]],
    spacing_y: float,
) -> None:
    """Interpolate dummy-node chains between their endpoints.

    :param edge_paths: Expanded edge paths.
    :param y_of_node: Orthogonal coordinate per node.
    :param expanded_nodes: Expanded-node lookup.
    :param node_by_id: Original graph node lookup.
    :param ordered_layers: Ordered nodes per layer.
    :param spacing_y: Vertical node spacing.
    :returns: ``None``.
    """
    desired_y: dict[str, float] = dict()
    path: list[str]

    # Dummy chains are straightened after block alignment so long edges become more
    # visually direct without rebuilding the whole placement.
    for path in edge_paths.values():
        if len(path) > 2:
            source_id: str = path[0]
            target_id: str = path[-1]

            if source_id in y_of_node and target_id in y_of_node:
                source_center: float = y_of_node[source_id] + _node_height(source_id, expanded_nodes, node_by_id) / 2.0
                target_center: float = y_of_node[target_id] + _node_height(target_id, expanded_nodes, node_by_id) / 2.0
                steps: int = len(path) - 1
                index: int
                node_id: str

                for index, node_id in enumerate(path[1:-1], start=1):
                    node_info: VirtualNode | None = expanded_nodes.get(node_id, None)
                    if node_info is not None and node_info.is_dummy:
                        interpolated_center: float = source_center + (target_center - source_center) * (index / steps)
                        desired_y[node_id] = (
                            interpolated_center - _node_height(node_id, expanded_nodes, node_by_id) / 2.0
                        )
                    else:
                        desired_y = desired_y
            else:
                desired_y = desired_y
        else:
            desired_y = desired_y

    if desired_y:
        node_ids: list[str]
        for node_ids in ordered_layers.values():
            node_id: str
            for node_id in node_ids:
                if node_id in desired_y:
                    y_of_node[node_id] = desired_y[node_id]
                else:
                    y_of_node = y_of_node
            _stack_layer(node_ids, y_of_node, spacing_y, expanded_nodes, node_by_id)
    else:
        desired_y = desired_y


def _tile_components(
    virtual_positions: dict[str, tuple[float, float]],
    expanded_nodes: dict[str, VirtualNode],
    components: list[list[str]],
    edge_paths: dict[str, list[str]],
    spacing_components: float,
    direction: LayoutDirection,
) -> None:
    """Separate disconnected components along the primary layout axis.

    :param virtual_positions: Current node positions.
    :param expanded_nodes: Expanded-node lookup.
    :param components: Connected components of original nodes.
    :param edge_paths: Expanded edge paths.
    :param spacing_components: Spacing between components.
    :param direction: Layout direction.
    :returns: ``None``.
    """
    if len(components) > 1:
        node_to_component: dict[str, int] = dict()
        component_index: int
        component_nodes: list[str]

        for component_index, component_nodes in enumerate(components):
            node_id: str
            for node_id in component_nodes:
                node_to_component[node_id] = component_index

        path: list[str]
        for path in edge_paths.values():
            if path:
                owner_index: int | None = node_to_component.get(path[0], None)
                if owner_index is not None:
                    node_id: str
                    for node_id in path[1:-1]:
                        if node_id in expanded_nodes:
                            node_to_component[node_id] = owner_index
                        else:
                            node_to_component = node_to_component
                else:
                    node_to_component = node_to_component
            else:
                node_to_component = node_to_component

        component_bounds: list[tuple[float, float, float, float] | None] = [None] * len(components)
        node_id: str
        coordinates: tuple[float, float]

        for node_id, coordinates in virtual_positions.items():
            component_owner: int | None = node_to_component.get(node_id, None)
            node_info: VirtualNode | None = expanded_nodes.get(node_id, None)

            if component_owner is not None and node_info is not None:
                x_value: float = coordinates[0]
                y_value: float = coordinates[1]
                right_value: float = x_value + node_info.width
                bottom_value: float = y_value + node_info.height
                current_bounds: tuple[float, float, float, float] | None = component_bounds[component_owner]

                if current_bounds is None:
                    component_bounds[component_owner] = (x_value, y_value, right_value, bottom_value)
                else:
                    component_bounds[component_owner] = (
                        min(current_bounds[0], x_value),
                        min(current_bounds[1], y_value),
                        max(current_bounds[2], right_value),
                        max(current_bounds[3], bottom_value),
                    )
            else:
                component_bounds = component_bounds

        vertical_flow: bool = direction in {LayoutDirection.DOWN, LayoutDirection.UP}
        cursor: float = 0.0

        for component_index, bounds in enumerate(component_bounds):
            if bounds is not None:
                shift_x: float = 0.0
                shift_y: float = 0.0

                if vertical_flow:
                    shift_x = 0.0
                    shift_y = cursor - bounds[1]
                else:
                    shift_x = cursor - bounds[0]
                    shift_y = 0.0

                if abs(shift_x) > 1e-9 or abs(shift_y) > 1e-9:
                    node_id = ""
                    owner_index = 0
                    for node_id, owner_index in node_to_component.items():
                        if owner_index == component_index and node_id in virtual_positions:
                            current_position: tuple[float, float] = virtual_positions[node_id]
                            virtual_positions[node_id] = (
                                current_position[0] + shift_x,
                                current_position[1] + shift_y,
                            )
                        else:
                            virtual_positions = virtual_positions
                else:
                    shift_x = shift_x

                cursor += (bounds[3] - bounds[1] if vertical_flow else bounds[2] - bounds[0]) + spacing_components
            else:
                cursor = cursor
    else:
        components = components


def _rectangles_overlap(
    left_a: float,
    top_a: float,
    right_a: float,
    bottom_a: float,
    left_b: float,
    top_b: float,
    right_b: float,
    bottom_b: float,
    margin: float = 0.0,
) -> bool:
    """Return whether two rectangles overlap.

    :param left_a: Left coordinate of rectangle A.
    :param top_a: Top coordinate of rectangle A.
    :param right_a: Right coordinate of rectangle A.
    :param bottom_a: Bottom coordinate of rectangle A.
    :param left_b: Left coordinate of rectangle B.
    :param top_b: Top coordinate of rectangle B.
    :param right_b: Right coordinate of rectangle B.
    :param bottom_b: Bottom coordinate of rectangle B.
    :param margin: Optional separation margin.
    :returns: ``True`` when rectangles overlap.
    """
    return not (
        right_a + margin <= left_b
        or right_b + margin <= left_a
        or bottom_a + margin <= top_b
        or bottom_b + margin <= top_a
    )


def _position_sort_key(item: tuple[str, float, float, float, float]) -> tuple[float, float, str]:
    """Return the stable sorting key for overlap resolution items.

    :param item: Tuple describing one positioned node.
    :returns: Stable sorting key.
    """
    return item[1], item[2], item[0]


def _sort_position_items(items: list[tuple[str, float, float, float, float]]) -> list[tuple[str, float, float, float, float]]:
    """Sort positioned nodes deterministically.

    :param items: Position items.
    :returns: Sorted items.
    """
    decorated_items: list[tuple[tuple[float, float, str], tuple[str, float, float, float, float]]] = list()
    sorted_items: list[tuple[str, float, float, float, float]] = list()
    item: tuple[str, float, float, float, float]

    for item in items:
        decorated_items.append((_position_sort_key(item), item))

    decorated_items.sort()

    for _, resolved_item in decorated_items:
        sorted_items.append(resolved_item)

    return sorted_items


def _resolve_node_overlaps(
    virtual_positions: dict[str, tuple[float, float]],
    expanded_nodes: dict[str, VirtualNode],
    spacing_x: float,
    spacing_y: float,
    direction: LayoutDirection,
) -> None:
    """Resolve residual node overlaps by local displacement.

    :param virtual_positions: Current node positions.
    :param expanded_nodes: Expanded-node lookup.
    :param spacing_x: Horizontal spacing.
    :param spacing_y: Vertical spacing.
    :param direction: Layout direction.
    :returns: ``None``.
    """
    horizontal_flow: bool = direction in {LayoutDirection.RIGHT, LayoutDirection.LEFT}
    primary_gap: float = spacing_x if horizontal_flow else spacing_y
    secondary_gap: float = spacing_y if horizontal_flow else spacing_x
    iteration: int

    # This final local pass only repairs remaining box overlaps; it intentionally
    # preserves most of the previous placement structure.
    for iteration in range(16):
        moved: bool = False
        items: list[tuple[str, float, float, float, float]] = list()
        node_id: str
        position: tuple[float, float]

        for node_id, position in virtual_positions.items():
            node_info: VirtualNode | None = expanded_nodes.get(node_id, None)
            if node_info is not None:
                items.append(
                    (
                        node_id,
                        position[0],
                        position[1],
                        position[0] + node_info.width,
                        position[1] + node_info.height,
                    )
                )
            else:
                items = items

        items = _sort_position_items(items)

        left_index: int
        for left_index, left_item in enumerate(items):
            if not moved:
                right_item: tuple[str, float, float, float, float]
                for right_item in items[left_index + 1:]:
                    left_node_id: str = left_item[0]
                    left_left: float = left_item[1]
                    left_top: float = left_item[2]
                    left_right: float = left_item[3]
                    left_bottom: float = left_item[4]
                    right_node_id: str = right_item[0]
                    right_left: float = right_item[1]
                    right_top: float = right_item[2]
                    right_right: float = right_item[3]
                    right_bottom: float = right_item[4]

                    if _rectangles_overlap(
                        left_left,
                        left_top,
                        left_right,
                        left_bottom,
                        right_left,
                        right_top,
                        right_right,
                        right_bottom,
                        margin=2.0,
                    ):
                        right_position: tuple[float, float] = virtual_positions[right_node_id]
                        shifted_x: float = right_position[0]
                        shifted_y: float = right_position[1]

                        if horizontal_flow:
                            same_column: bool = abs(left_left - right_left) < max(primary_gap * 0.5, 1.0)
                            if same_column:
                                shifted_y = left_bottom + secondary_gap
                            else:
                                shifted_x = left_right + primary_gap
                        else:
                            same_row: bool = abs(left_top - right_top) < max(primary_gap * 0.5, 1.0)
                            if same_row:
                                shifted_x = left_right + secondary_gap
                            else:
                                shifted_y = left_bottom + primary_gap

                        virtual_positions[right_node_id] = (shifted_x, shifted_y)
                        moved = True
                        break
                    else:
                        moved = moved
            else:
                moved = moved

        if not moved:
            break
        else:
            iteration = iteration


def _build_layer_of(ordered_layers: dict[int, list[str]]) -> dict[str, int]:
    """Build the layer index of every node.

    :param ordered_layers: Ordered nodes per layer.
    :returns: Layer index per node.
    """
    layer_of: dict[str, int] = dict()
    layer_id: int
    node_ids: list[str]

    for layer_id, node_ids in ordered_layers.items():
        node_id: str
        for node_id in node_ids:
            layer_of[node_id] = layer_id

    return layer_of


class NodePlacementPhase(LayoutPhaseBase):
    """Assign node and port coordinates for the layered layout."""

    __slots__ = ()
    name: str = "node-placement"

    def run(self, context: LayoutContext) -> None:
        """Execute the node-placement phase.

        :param context: Shared pipeline context.
        :returns: ``None``.
        """
        graph_options: dict[str, Any] = context.option_resolver.resolve_for_element(context.graph.layout_options)
        spacing_x: float = float(graph_options["org.vera.sugiyama.layered.spacing.nodeNodeBetweenLayers"])
        spacing_y: float = float(graph_options["org.vera.sugiyama.spacing.nodeNode"])
        spacing_components: float = float(graph_options["org.vera.sugiyama.spacing.componentComponent"])
        direction: LayoutDirection = _layout_direction(context)
        fixed_alignment: FixedAlignment = _fixed_alignment(context)
        ordered_layers: dict[int, list[str]] = context.phase_state.ordered_layers
        expanded_nodes: dict[str, VirtualNode] = context.phase_state.expanded_nodes
        edge_paths: dict[str, list[str]] = context.phase_state.edge_paths
        predecessors: dict[str, set[str]] = context.phase_state.expanded_predecessors
        successors: dict[str, set[str]] = context.phase_state.expanded_successors
        components: list[list[str]] = context.phase_state.components
        layer_of: dict[str, int] = _build_layer_of(ordered_layers)
        order_in_layer: dict[str, int] = context.phase_state.order_in_layer
        node_by_id: dict[str, SugiyamaNode] = context.graph.node_by_id()

        # The phase first computes orthogonal coordinates from aligned blocks, then
        # projects them onto the primary flow axis and finally derives port positions.
        y_of_node: dict[str, float] = _compute_vertical_coordinates(
            ordered_layers,
            layer_of,
            order_in_layer,
            predecessors,
            successors,
            expanded_nodes,
            node_by_id,
            spacing_y,
            fixed_alignment,
        )

        _straighten_dummy_chains(
            edge_paths,
            y_of_node,
            expanded_nodes,
            node_by_id,
            ordered_layers,
            spacing_y,
        )

        node_ids: list[str]
        for _, node_ids in sorted(ordered_layers.items()):
            _stack_layer(node_ids, y_of_node, spacing_y, expanded_nodes, node_by_id)

        virtual_positions: dict[str, tuple[float, float]]
        layer_positions: dict[int, float]
        virtual_positions, layer_positions = _assign_node_coordinates(
            context,
            ordered_layers,
            expanded_nodes,
            node_by_id,
            spacing_x,
            spacing_y,
            y_of_node,
        )

        _tile_components(
            virtual_positions,
            expanded_nodes,
            components,
            edge_paths,
            spacing_components,
            direction,
        )
        _resolve_node_overlaps(
            virtual_positions,
            expanded_nodes,
            spacing_x,
            spacing_y,
            direction,
        )

        node_id: str
        coordinates: tuple[float, float]
        for node_id, coordinates in virtual_positions.items():
            node: SugiyamaNode | None = node_by_id.get(node_id, None)
            if node is not None:
                node.x = coordinates[0]
                node.y = coordinates[1]
            else:
                node = node

        _assign_port_positions(context)

        context.phase_state.virtual_positions.clear()
        context.phase_state.virtual_positions.update(virtual_positions)
        context.phase_state.layer_x.clear()
        context.phase_state.layer_x.update(layer_positions)
        context.phase_state.y_of_node.clear()
        context.phase_state.y_of_node.update(y_of_node)
        context.report.add_note(
            "Node placement uses a Brandes-Koepf-style multi-pass vertical alignment.",
        )
