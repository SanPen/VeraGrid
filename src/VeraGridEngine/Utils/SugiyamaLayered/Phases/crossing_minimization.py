# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from VeraGridEngine.Utils.SugiyamaLayered.Phases.long_edges import VirtualNode
from VeraGridEngine.Utils.SugiyamaLayered.model import SugiyamaNode
from VeraGridEngine.Utils.SugiyamaLayered.options import ConsiderModelOrderStrategy, CrossingMinimizationStrategy
from VeraGridEngine.Utils.SugiyamaLayered.pipeline import LayoutContext, LayoutPhaseBase


def _barycenter(values: list[float], fallback: float) -> float:
    """Return the barycenter of a list of positions.

    :param values: Reference positions.
    :param fallback: Fallback value when the list is empty.
    :returns: Barycenter or fallback value.
    """
    result: float = fallback

    if values:
        result = sum(values) / len(values)
    else:
        result = fallback

    return result


def _median(values: list[float], fallback: float) -> float:
    """Return the median of a list of positions.

    :param values: Reference positions.
    :param fallback: Fallback value when the list is empty.
    :returns: Median or fallback value.
    """
    result: float = fallback

    if values:
        ordered_values: list[float] = sorted(values)
        middle_index: int = len(ordered_values) // 2
        if len(ordered_values) % 2 == 1:
            result = ordered_values[middle_index]
        else:
            result = (ordered_values[middle_index - 1] + ordered_values[middle_index]) / 2.0
    else:
        result = fallback

    return result


def _neighbor_positions(
    node_id: str,
    neighbors: dict[str, set[str]],
    reference_order: dict[str, int],
) -> list[float]:
    """Collect neighbor positions from the reference layer.

    :param node_id: Node whose neighbors are inspected.
    :param neighbors: Adjacency mapping used for the sweep direction.
    :param reference_order: Position of nodes in the adjacent layer.
    :returns: Neighbor positions as floats.
    """
    positions: list[float] = list()
    neighbor_id: str

    # The sweep heuristics require positions in the adjacent layer so each node can be
    # moved towards the center of its incident edges.
    for neighbor_id in sorted(neighbors.get(node_id, set())):
        if neighbor_id in reference_order:
            positions.append(float(reference_order[neighbor_id]))
        else:
            positions = positions

    return positions


def _crossings_between(
    upper: list[str],
    lower: list[str],
    successors: dict[str, set[str]],
) -> int:
    """Count edge crossings between two consecutive layers.

    :param upper: Ordered nodes in the upper layer.
    :param lower: Ordered nodes in the lower layer.
    :param successors: Expanded successor adjacency.
    :returns: Number of crossings between both layers.
    """
    lower_position: dict[str, int] = dict()
    count: int = 0
    left_index: int
    left_node: str

    for lower_index, lower_node in enumerate(lower):
        lower_position[lower_node] = lower_index

    # Crossing count is the optimization target of the phase, so we measure every
    # pair of edges induced by every pair of upper-layer nodes.
    for left_index, left_node in enumerate(upper):
        left_targets: list[str] = list()
        for candidate_target in successors.get(left_node, set()):
            if candidate_target in lower_position:
                left_targets.append(candidate_target)
            else:
                left_targets = left_targets

        if left_targets:
            for right_node in upper[left_index + 1:]:
                right_targets: list[str] = list()
                for candidate_target in successors.get(right_node, set()):
                    if candidate_target in lower_position:
                        right_targets.append(candidate_target)
                    else:
                        right_targets = right_targets

                if right_targets:
                    for left_target in left_targets:
                        left_target_position: int = lower_position[left_target]
                        for right_target in right_targets:
                            if lower_position[right_target] < left_target_position:
                                count += 1
                            else:
                                count = count
                else:
                    count = count
        else:
            count = count

    return count


def _read_integer_candidate(value: Any) -> int | None:
    """Parse an optional integer candidate.

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


def _node_model_order(
    node_id: str,
    fallback: int,
    expanded_nodes: dict[str, VirtualNode],
    node_by_id: dict[str, SugiyamaNode],
) -> int:
    """Resolve the stable model-order key for one node.

    :param node_id: Node identifier.
    :param fallback: Fallback ordering key.
    :param expanded_nodes: Expanded-node lookup.
    :param node_by_id: Original graph node lookup.
    :returns: Stable model-order key.
    """
    node_info: VirtualNode | None = expanded_nodes.get(node_id, None)
    resolved_order: int = fallback

    if node_info is not None:
        resolved_order = node_info.model_order
    else:
        node: SugiyamaNode | None = node_by_id.get(node_id, None)
        if node is not None:
            candidates: tuple[Any, Any, Any, Any] = (
                node.get_property("modelOrder", None),
                node.get_property("model_order", None),
                node.get_layout_option(
                    "org.vera.sugiyama.layered.considerModelOrder.groupModelOrder.crossingMinimizationId",
                    None,
                ),
                node.get_layout_option(
                    "org.vera.sugiyama.layered.considerModelOrder.groupModelOrder.cycleBreakingId",
                    None,
                ),
            )
            for candidate in candidates:
                parsed_candidate: int | None = _read_integer_candidate(candidate)
                if parsed_candidate is not None:
                    resolved_order = parsed_candidate
                    break
                else:
                    resolved_order = resolved_order
        else:
            resolved_order = fallback

    return resolved_order


def _consider_model_order_enabled(context: LayoutContext) -> bool:
    """Return whether model-order hints must affect crossing minimization.

    :param context: Shared pipeline context.
    :returns: ``True`` when the feature is enabled.
    """
    options: dict[str, Any] = context.option_resolver.resolve_for_element(context.graph.layout_options)
    strategy_value: ConsiderModelOrderStrategy = options.get(
        "org.vera.sugiyama.layered.considerModelOrder.strategy",
        ConsiderModelOrderStrategy.NONE,
    )
    is_enabled: bool = strategy_value is not ConsiderModelOrderStrategy.NONE
    return is_enabled


def _crossing_strategy(context: LayoutContext) -> CrossingMinimizationStrategy:
    """Return the configured crossing-minimization strategy.

    :param context: Shared pipeline context.
    :returns: Configured strategy.
    """
    options: dict[str, Any] = context.option_resolver.resolve_for_element(context.graph.layout_options)
    strategy_value: CrossingMinimizationStrategy = options.get(
        "org.vera.sugiyama.layered.crossingMinimization.strategy",
        CrossingMinimizationStrategy.LAYER_SWEEP,
    )
    return strategy_value


def _dummy_bias(node_id: str, expanded_nodes: dict[str, VirtualNode]) -> float:
    """Return the bias that keeps dummy nodes stable during ordering.

    :param node_id: Expanded node identifier.
    :param expanded_nodes: Expanded-node lookup.
    :returns: Bias applied to the primary heuristic score.
    """
    bias: float = 0.0
    node_info: VirtualNode | None = expanded_nodes.get(node_id, None)

    if node_info is not None and node_info.is_dummy:
        bias = -0.25
    else:
        bias = 0.0

    return bias


def _sweep_score(
    node_id: str,
    current_order: dict[str, int],
    reference_order: dict[str, int],
    neighbors: dict[str, set[str]],
    chain_order: dict[str, int],
    expanded_nodes: dict[str, VirtualNode],
    model_order: dict[str, int],
    prefer_model_order: bool,
    use_median: bool,
) -> tuple[float, float, int, int, int, str]:
    """Compute the ordering score for one node during one sweep.

    :param node_id: Node to rank.
    :param current_order: Current positions in the active layer.
    :param reference_order: Positions in the adjacent reference layer.
    :param neighbors: Adjacency used by the sweep direction.
    :param chain_order: Order inside dummy-node chains.
    :param expanded_nodes: Expanded-node lookup.
    :param model_order: Stable model-order mapping.
    :param prefer_model_order: Whether model-order must affect ranking.
    :param use_median: Whether the median should be the primary score.
    :returns: Deterministic ranking key.
    """
    fallback_position: float = float(current_order.get(node_id, 0))
    neighbor_values: list[float] = _neighbor_positions(node_id, neighbors, reference_order)
    primary_score: float = fallback_position
    secondary_score: float = fallback_position
    stable_model_order: int = current_order.get(node_id, 0)

    if use_median:
        primary_score = _median(neighbor_values, fallback_position)
        secondary_score = _barycenter(neighbor_values, fallback_position)
    else:
        primary_score = _barycenter(neighbor_values, fallback_position)
        secondary_score = _median(neighbor_values, fallback_position)

    if prefer_model_order:
        stable_model_order = model_order.get(node_id, current_order.get(node_id, 0))
    else:
        stable_model_order = current_order.get(node_id, 0)

    return (
        primary_score + _dummy_bias(node_id, expanded_nodes),
        secondary_score,
        chain_order.get(node_id, 0),
        stable_model_order,
        current_order.get(node_id, 0),
        node_id,
    )


def _sweep_order(
    layer: list[str],
    reference_layer: list[str],
    neighbors: dict[str, set[str]],
    chain_order: dict[str, int],
    expanded_nodes: dict[str, VirtualNode],
    model_order: dict[str, int],
    prefer_model_order: bool,
    use_median: bool,
) -> list[str]:
    """Reorder one layer using barycenter or median sweeps.

    :param layer: Layer being reordered.
    :param reference_layer: Adjacent layer used as reference.
    :param neighbors: Adjacency used by the sweep direction.
    :param chain_order: Order inside dummy-node chains.
    :param expanded_nodes: Expanded-node lookup.
    :param model_order: Stable model-order mapping.
    :param prefer_model_order: Whether model-order must affect ranking.
    :param use_median: Whether the median should be the primary score.
    :returns: Reordered layer.
    """
    reference_order: dict[str, int] = dict()
    current_order: dict[str, int] = dict()
    decorated_items: list[tuple[tuple[float, float, int, int, int, str], str]] = list()
    sorted_layer: list[str] = list()
    node_id: str

    # Reference positions are materialized once per sweep so every node can measure
    # its preferred location relative to the adjacent layer.
    for index, reference_node_id in enumerate(reference_layer):
        reference_order[reference_node_id] = index

    for index, current_node_id in enumerate(layer):
        current_order[current_node_id] = index

    for node_id in layer:
        score: tuple[float, float, int, int, int, str] = _sweep_score(
            node_id,
            current_order,
            reference_order,
            neighbors,
            chain_order,
            expanded_nodes,
            model_order,
            prefer_model_order,
            use_median,
        )
        decorated_items.append((score, node_id))

    decorated_items.sort()

    for _, resolved_node_id in decorated_items:
        sorted_layer.append(resolved_node_id)

    return sorted_layer


def _crossings_for_upper_pair(
    left: str,
    right: str,
    lower_position: dict[str, int],
    successors: dict[str, set[str]],
) -> tuple[int, int]:
    """Count crossings before and after swapping two upper-layer nodes.

    :param left: Left node in the upper layer.
    :param right: Right node in the upper layer.
    :param lower_position: Position of nodes in the lower layer.
    :param successors: Expanded successor adjacency.
    :returns: Crossing count before and after the swap.
    """
    left_targets: list[int] = list()
    right_targets: list[int] = list()
    before: int = 0
    after: int = 0

    for node_id in successors.get(left, set()):
        if node_id in lower_position:
            left_targets.append(lower_position[node_id])
        else:
            left_targets = left_targets

    for node_id in successors.get(right, set()):
        if node_id in lower_position:
            right_targets.append(lower_position[node_id])
        else:
            right_targets = right_targets

    for left_position in left_targets:
        for right_position in right_targets:
            if right_position < left_position:
                before += 1
            else:
                before = before

            if left_position < right_position:
                after += 1
            else:
                after = after

    return before, after


def _crossings_for_lower_pair(
    left: str,
    right: str,
    upper_position: dict[str, int],
    predecessors: dict[str, set[str]],
) -> tuple[int, int]:
    """Count crossings before and after swapping two lower-layer nodes.

    :param left: Left node in the lower layer.
    :param right: Right node in the lower layer.
    :param upper_position: Position of nodes in the upper layer.
    :param predecessors: Expanded predecessor adjacency.
    :returns: Crossing count before and after the swap.
    """
    left_sources: list[int] = list()
    right_sources: list[int] = list()
    before: int = 0
    after: int = 0

    for node_id in predecessors.get(left, set()):
        if node_id in upper_position:
            left_sources.append(upper_position[node_id])
        else:
            left_sources = left_sources

    for node_id in predecessors.get(right, set()):
        if node_id in upper_position:
            right_sources.append(upper_position[node_id])
        else:
            right_sources = right_sources

    for left_position in left_sources:
        for right_position in right_sources:
            if right_position < left_position:
                before += 1
            else:
                before = before

            if left_position < right_position:
                after += 1
            else:
                after = after

    return before, after


def _prefer_swap_tie_break(
    left: str,
    right: str,
    chain_order: dict[str, int],
    model_order: dict[str, int],
    prefer_model_order: bool,
) -> bool:
    """Return whether a tie should prefer swapping two nodes.

    :param left: Left node in the current order.
    :param right: Right node in the current order.
    :param chain_order: Order inside dummy-node chains.
    :param model_order: Stable model-order mapping.
    :param prefer_model_order: Whether model-order must affect ranking.
    :returns: ``True`` when the swap is preferred on ties.
    """
    should_swap: bool = False

    if prefer_model_order:
        left_model: int = model_order.get(left, 0)
        right_model: int = model_order.get(right, 0)
        if left_model != right_model:
            should_swap = left_model > right_model
        else:
            should_swap = should_swap
    else:
        should_swap = should_swap

    if not should_swap:
        left_chain: int = chain_order.get(left, 0)
        right_chain: int = chain_order.get(right, 0)
        if left_chain != right_chain:
            should_swap = left_chain > right_chain
        else:
            should_swap = left > right
    else:
        should_swap = should_swap

    return should_swap


def _transpose_layer_pair_local(
    upper: list[str],
    lower: list[str],
    successors: dict[str, set[str]],
    predecessors: dict[str, set[str]],
    chain_order: dict[str, int],
    model_order: dict[str, int],
    prefer_model_order: bool,
) -> None:
    """Run local adjacent transpositions on one layer pair.

    :param upper: Upper layer, modified in place.
    :param lower: Lower layer, modified in place.
    :param successors: Expanded successor adjacency.
    :param predecessors: Expanded predecessor adjacency.
    :param chain_order: Order inside dummy-node chains.
    :param model_order: Stable model-order mapping.
    :param prefer_model_order: Whether model-order must affect ranking.
    :returns: ``None``.
    """
    changed: bool = True
    iteration: int = 0

    # Local transposition repairs crossing patterns that barycenter and median sweeps
    # alone cannot remove because they depend on pairwise interactions.
    while changed and iteration < 4:
        changed = False
        iteration += 1

        lower_position: dict[str, int] = dict()
        for index, node_id in enumerate(lower):
            lower_position[node_id] = index

        upper_index: int = 0
        while upper_index < len(upper) - 1:
            left_node: str = upper[upper_index]
            right_node: str = upper[upper_index + 1]
            before_count: int
            after_count: int
            before_count, after_count = _crossings_for_upper_pair(left_node, right_node, lower_position, successors)

            if after_count < before_count:
                upper[upper_index], upper[upper_index + 1] = upper[upper_index + 1], upper[upper_index]
                changed = True
            else:
                if after_count == before_count and _prefer_swap_tie_break(
                    left_node,
                    right_node,
                    chain_order,
                    model_order,
                    prefer_model_order,
                ):
                    upper[upper_index], upper[upper_index + 1] = upper[upper_index + 1], upper[upper_index]
                    changed = True
                else:
                    changed = changed

            upper_index += 1

        upper_position: dict[str, int] = dict()
        for index, node_id in enumerate(upper):
            upper_position[node_id] = index

        lower_index: int = 0
        while lower_index < len(lower) - 1:
            left_node = lower[lower_index]
            right_node = lower[lower_index + 1]
            before_count, after_count = _crossings_for_lower_pair(left_node, right_node, upper_position, predecessors)

            if after_count < before_count:
                lower[lower_index], lower[lower_index + 1] = lower[lower_index + 1], lower[lower_index]
                changed = True
            else:
                if after_count == before_count and _prefer_swap_tie_break(
                    left_node,
                    right_node,
                    chain_order,
                    model_order,
                    prefer_model_order,
                ):
                    lower[lower_index], lower[lower_index + 1] = lower[lower_index + 1], lower[lower_index]
                    changed = True
                else:
                    changed = changed

            lower_index += 1


def _total_crossings(layers: dict[int, list[str]], successors: dict[str, set[str]]) -> int:
    """Return the total number of crossings in the expanded graph.

    :param layers: Ordered nodes per layer.
    :param successors: Expanded successor adjacency.
    :returns: Total crossing count.
    """
    layer_ids: list[int] = sorted(layers)
    total_count: int = 0
    pair_index: int

    for pair_index in range(len(layer_ids) - 1):
        upper_layer_id: int = layer_ids[pair_index]
        lower_layer_id: int = layer_ids[pair_index + 1]
        total_count += _crossings_between(layers[upper_layer_id], layers[lower_layer_id], successors)

    return total_count


def _copy_layers(layers: dict[int, list[str]]) -> dict[int, list[str]]:
    """Deep-copy ordered layers.

    :param layers: Layer mapping to copy.
    :returns: Copied layer mapping.
    """
    copied_layers: dict[int, list[str]] = dict()
    layer_id: int
    nodes: list[str]

    for layer_id, nodes in layers.items():
        copied_layers[layer_id] = list(nodes)

    return copied_layers


def _build_expanded_adjacency(
    expanded_edges: list[tuple[str, str, str, int]],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Build successor and predecessor tables for the expanded graph.

    :param expanded_edges: Expanded edges generated by the long-edge phase.
    :returns: Successor and predecessor adjacency tables.
    """
    successors: dict[str, set[str]] = dict()
    predecessors: dict[str, set[str]] = dict()
    edge_id: str
    source_id: str
    target_id: str
    segment_index: int

    for edge_id, source_id, target_id, segment_index in expanded_edges:
        edge_id = edge_id
        segment_index = segment_index
        source_successors: set[str] = successors.get(source_id, None) or set()
        target_predecessors: set[str] = predecessors.get(target_id, None) or set()
        source_successors.add(target_id)
        target_predecessors.add(source_id)
        successors[source_id] = source_successors
        predecessors[target_id] = target_predecessors

    return successors, predecessors


def _build_chain_order(edge_paths: dict[str, list[str]]) -> dict[str, int]:
    """Build the order of nodes inside each dummy chain.

    :param edge_paths: Expanded edge paths.
    :returns: Best-known chain position per node.
    """
    chain_order: dict[str, int] = dict()
    path: list[str]

    for path in edge_paths.values():
        for index, node_id in enumerate(path):
            previous_index: int | None = chain_order.get(node_id, None)
            if previous_index is None or index < previous_index:
                chain_order[node_id] = index
            else:
                chain_order = chain_order

    return chain_order


def _build_model_order(
    layers: dict[int, list[str]],
    expanded_nodes: dict[str, VirtualNode],
    node_by_id: dict[str, SugiyamaNode],
) -> dict[str, int]:
    """Build the stable model-order key for every expanded node.

    :param layers: Ordered nodes per layer.
    :param expanded_nodes: Expanded-node lookup.
    :param node_by_id: Original graph node lookup.
    :returns: Stable model-order mapping.
    """
    model_order: dict[str, int] = dict()
    layer_id: int
    nodes: list[str]

    for layer_id, nodes in layers.items():
        for index, node_id in enumerate(nodes):
            fallback: int = layer_id * 1000 + index
            model_order[node_id] = _node_model_order(node_id, fallback, expanded_nodes, node_by_id)

    return model_order


def _build_order_in_layer(layers: dict[int, list[str]]) -> dict[str, int]:
    """Build the final index of every node inside its layer.

    :param layers: Ordered nodes per layer.
    :returns: Position mapping for every expanded node.
    """
    order_in_layer: dict[str, int] = dict()
    nodes: list[str]

    for nodes in layers.values():
        for index, node_id in enumerate(nodes):
            order_in_layer[node_id] = index

    return order_in_layer


class CrossingMinimizationPhase(LayoutPhaseBase):
    """Reduce edge crossings by alternating layer sweeps and local transpositions."""

    __slots__ = ()
    name: str = "crossing-minimization"

    def run(self, context: LayoutContext) -> None:
        """Execute the crossing-minimization phase.

        :param context: Shared pipeline context.
        :returns: ``None``.
        """
        expanded_layers: dict[int, list[str]] = context.phase_state.expanded_layers
        expanded_edges: list[tuple[str, str, str, int]] = context.phase_state.expanded_edges
        expanded_nodes: dict[str, VirtualNode] = context.phase_state.expanded_nodes
        edge_paths: dict[str, list[str]] = context.phase_state.edge_paths
        node_by_id: dict[str, SugiyamaNode] = context.graph.node_by_id()
        prefer_model_order: bool = _consider_model_order_enabled(context)
        strategy: str = _crossing_strategy(context)

        if expanded_layers:
            layers: dict[int, list[str]] = _copy_layers(expanded_layers)
            successors: dict[str, set[str]]
            predecessors: dict[str, set[str]]
            successors, predecessors = _build_expanded_adjacency(expanded_edges)
            chain_order: dict[str, int] = _build_chain_order(edge_paths)
            model_order: dict[str, int] = _build_model_order(layers, expanded_nodes, node_by_id)
            best_layers: dict[int, list[str]] = _copy_layers(layers)
            best_crossings: int = _total_crossings(best_layers, successors)
            layer_ids: list[int] = sorted(layers)

            if strategy is CrossingMinimizationStrategy.NONE:
                order_in_layer: dict[str, int] = _build_order_in_layer(best_layers)
                context.phase_state.ordered_layers.clear()
                context.phase_state.ordered_layers.update(best_layers)
                context.phase_state.expanded_successors.clear()
                context.phase_state.expanded_successors.update(successors)
                context.phase_state.expanded_predecessors.clear()
                context.phase_state.expanded_predecessors.update(predecessors)
                context.phase_state.order_in_layer.clear()
                context.phase_state.order_in_layer.update(order_in_layer)
                context.report.add_note("Crossing minimization disabled by strategy option.")
            else:
                sweep_index: int
                for sweep_index in range(8):
                    use_median: bool = sweep_index % 2 == 1
                    layer_id: int

                    # Downward sweeps place each layer relative to its predecessors so
                    # the ordering follows the current shape of incoming edges.
                    for layer_id in layer_ids[1:]:
                        layers[layer_id] = _sweep_order(
                            layers[layer_id],
                            layers[layer_id - 1],
                            predecessors,
                            chain_order,
                            expanded_nodes,
                            model_order,
                            prefer_model_order,
                            use_median,
                        )

                    # Upward sweeps mirror the process with successors to avoid biasing
                    # the solution toward only one traversal direction.
                    for layer_id in reversed(layer_ids[:-1]):
                        layers[layer_id] = _sweep_order(
                            layers[layer_id],
                            layers[layer_id + 1],
                            successors,
                            chain_order,
                            expanded_nodes,
                            model_order,
                            prefer_model_order,
                            use_median,
                        )

                    # Local transposition repairs residual inversions between adjacent
                    # nodes once the coarse sweep position has been chosen.
                    pair_index: int
                    for pair_index in range(len(layer_ids) - 1):
                        upper_layer_id: int = layer_ids[pair_index]
                        lower_layer_id: int = layer_ids[pair_index + 1]
                        _transpose_layer_pair_local(
                            layers[upper_layer_id],
                            layers[lower_layer_id],
                            successors,
                            predecessors,
                            chain_order,
                            model_order,
                            prefer_model_order,
                        )

                    current_crossings: int = _total_crossings(layers, successors)
                    if current_crossings < best_crossings:
                        best_crossings = current_crossings
                        best_layers = _copy_layers(layers)
                    else:
                        best_crossings = best_crossings

                order_in_layer = _build_order_in_layer(best_layers)
                context.phase_state.ordered_layers.clear()
                context.phase_state.ordered_layers.update(best_layers)
                context.phase_state.expanded_successors.clear()
                context.phase_state.expanded_successors.update(successors)
                context.phase_state.expanded_predecessors.clear()
                context.phase_state.expanded_predecessors.update(predecessors)
                context.phase_state.order_in_layer.clear()
                context.phase_state.order_in_layer.update(order_in_layer)
                context.report.add_note(
                    "Crossing minimization runs alternating barycenter/median sweeps with "
                    f"local transpose; best crossing count={best_crossings}.",
                )
        else:
            context.phase_state.ordered_layers.clear()
