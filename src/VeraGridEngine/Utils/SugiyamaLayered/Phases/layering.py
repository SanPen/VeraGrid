# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections import deque
from typing import Any

from VeraGridEngine.Utils.SugiyamaLayered.model import SugiyamaNode
from VeraGridEngine.Utils.SugiyamaLayered.options import ConsiderModelOrderStrategy, LayeringStrategy
from VeraGridEngine.Utils.SugiyamaLayered.pipeline import LayoutContext, LayoutPhaseBase


def _read_integer_candidate(value: Any) -> int | None:
    """Parse an optional integer candidate.

    :param value: Raw value coming from properties or layout options.
    :returns: Parsed integer when conversion is valid, otherwise ``None``.
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


def _node_model_order(node_id: str, fallback: int, node_by_id: dict[str, SugiyamaNode]) -> int:
    """Return the model-order hint used to stabilize ordering.

    :param node_id: Identifier of the node to inspect.
    :param fallback: Stable fallback index when no explicit value exists.
    :param node_by_id: Node lookup table.
    :returns: Numeric ordering hint for the node.
    """
    node: SugiyamaNode | None = node_by_id.get(node_id, None)
    resolved_order: int = fallback

    if node is not None:
        candidates: tuple[Any, Any, Any, Any] = (
            node.get_property("modelOrder", None),
            node.get_property("model_order", None),
            node.get_layout_option(
                "org.vera.sugiyama.layered.considerModelOrder.groupModelOrder.layeringId",
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


def _sort_key_for_node(
    node_id: str,
    node_order: dict[str, int],
    node_by_id: dict[str, SugiyamaNode],
    prefer_model_order: bool,
) -> tuple[int, str]:
    """Build the stable sorting key used by layering.

    :param node_id: Identifier of the node being ranked.
    :param node_order: Original order of nodes in the graph.
    :param node_by_id: Node lookup table.
    :param prefer_model_order: Whether model-order hints must override insertion order.
    :returns: Tuple used for deterministic ordering.
    """
    fallback_order: int = node_order.get(node_id, 0)
    primary_order: int = fallback_order

    if prefer_model_order:
        primary_order = _node_model_order(node_id, fallback_order, node_by_id)
    else:
        primary_order = fallback_order

    return primary_order, node_id


def _sorted_node_ids(
    node_ids: list[str],
    node_order: dict[str, int],
    node_by_id: dict[str, SugiyamaNode],
    prefer_model_order: bool,
) -> list[str]:
    """Sort node identifiers with the deterministic strategy of this phase.

    :param node_ids: Node identifiers to sort.
    :param node_order: Original order of nodes in the graph.
    :param node_by_id: Node lookup table.
    :param prefer_model_order: Whether model-order hints should be preferred.
    :returns: Sorted node identifiers.
    """
    decorated_items: list[tuple[tuple[int, str], str]] = list()
    sorted_items: list[str] = list()
    node_id: str

    # The layering algorithm repeatedly needs deterministic node order; precomputing
    # the key list makes the queue logic explicit and avoids inline lambdas.
    for node_id in node_ids:
        key: tuple[int, str] = _sort_key_for_node(node_id, node_order, node_by_id, prefer_model_order)
        decorated_items.append((key, node_id))

    decorated_items.sort()

    for _, resolved_node_id in decorated_items:
        sorted_items.append(resolved_node_id)

    return sorted_items


def _consider_model_order_enabled(context: LayoutContext) -> bool:
    """Return whether model-order hints must affect layering.

    :param context: Pipeline execution context.
    :returns: ``True`` when model-order hints are enabled.
    """
    options: dict[str, Any] = context.option_resolver.resolve_for_element(context.graph.layout_options)
    strategy_value: ConsiderModelOrderStrategy = options.get(
        "org.vera.sugiyama.layered.considerModelOrder.strategy",
        ConsiderModelOrderStrategy.NONE,
    )
    is_enabled: bool = strategy_value is not ConsiderModelOrderStrategy.NONE
    return is_enabled


def _layering_strategy(context: LayoutContext) -> LayeringStrategy:
    """Return the configured layering strategy.

    :param context: Pipeline execution context.
    :returns: Configured strategy.
    """
    options: dict[str, Any] = context.option_resolver.resolve_for_element(context.graph.layout_options)
    strategy_value: LayeringStrategy = options.get(
        "org.vera.sugiyama.layered.layering.strategy",
        LayeringStrategy.NETWORK_SIMPLEX,
    )
    return strategy_value


def _topological_order(
    node_ids: list[str],
    successors: dict[str, set[str]],
    predecessors: dict[str, set[str]],
    node_by_id: dict[str, SugiyamaNode],
    prefer_model_order: bool,
) -> list[str]:
    """Compute a deterministic topological order for the DAG.

    :param node_ids: Node identifiers present in the graph.
    :param successors: Successor adjacency table.
    :param predecessors: Predecessor adjacency table.
    :param node_by_id: Node lookup table.
    :param prefer_model_order: Whether model-order hints should affect queue ordering.
    :returns: Ordered node identifiers.
    """
    indegree: dict[str, int] = dict()
    node_order: dict[str, int] = dict()
    zero_indegree_nodes: list[str] = list()
    queue: deque[str]
    order: list[str] = list()
    node_id: str

    # The phase first measures DAG indegrees because Kahn's algorithm requires the
    # count of unresolved predecessors before a node can be emitted.
    for index, resolved_node_id in enumerate(node_ids):
        node_order[resolved_node_id] = index
        indegree[resolved_node_id] = len(predecessors.get(resolved_node_id, set()))

    for resolved_node_id in node_ids:
        degree: int = indegree[resolved_node_id]
        if degree == 0:
            zero_indegree_nodes.append(resolved_node_id)
        else:
            zero_indegree_nodes = zero_indegree_nodes

    zero_indegree_nodes = _sorted_node_ids(
        zero_indegree_nodes,
        node_order,
        node_by_id,
        prefer_model_order,
    )
    queue = deque(zero_indegree_nodes)

    # The queue emits nodes whose predecessors are already fixed, producing the base
    # order for longest-path layering and all following compaction steps.
    while queue:
        current_node_id: str = queue.popleft()
        order.append(current_node_id)

        successor_ids: list[str] = _sorted_node_ids(
            list(successors.get(current_node_id, set())),
            node_order,
            node_by_id,
            prefer_model_order,
        )
        for successor_id in successor_ids:
            remaining_indegree: int = indegree[successor_id] - 1
            indegree[successor_id] = remaining_indegree
            if remaining_indegree == 0:
                queue.append(successor_id)
            else:
                queue = queue

    # If the DAG data is incomplete we still emit all nodes so that later phases can
    # work with a total order instead of failing on missing entries.
    sorted_all_nodes: list[str] = _sorted_node_ids(node_ids, node_order, node_by_id, prefer_model_order)
    for resolved_node_id in sorted_all_nodes:
        if resolved_node_id not in order:
            order.append(resolved_node_id)
        else:
            order = order

    return order


def _longest_path_layers(order: list[str], predecessors: dict[str, set[str]]) -> dict[str, int]:
    """Assign initial layers using longest-path distances from sources.

    :param order: Topological order of nodes.
    :param predecessors: Predecessor adjacency table.
    :returns: Mapping from node identifier to layer index.
    """
    layer_of: dict[str, int] = dict()
    node_id: str

    # Every node starts at layer zero; predecessors then push the node down until all
    # edge directions respect the DAG orientation.
    for node_id in order:
        layer_of[node_id] = 0

    for node_id in order:
        predecessor_ids: set[str] = predecessors.get(node_id, set())
        if predecessor_ids:
            max_predecessor_layer: int = max(layer_of[predecessor_id] + 1 for predecessor_id in predecessor_ids)
            layer_of[node_id] = max_predecessor_layer
        else:
            layer_of[node_id] = layer_of[node_id]

    return layer_of


def _compact_to_sinks(
    order: list[str],
    layer_of: dict[str, int],
    successors: dict[str, set[str]],
) -> None:
    """Push nodes towards their successors without breaking edge directions.

    :param order: Topological order of nodes.
    :param layer_of: Mutable layer assignment.
    :param successors: Successor adjacency table.
    :returns: ``None``.
    """
    changed: bool = True

    # Reverse sweeps pull nodes closer to their sinks, reducing edge span while
    # keeping the acyclic constraints established by the longest-path layering.
    while changed:
        changed = False
        for node_id in reversed(order):
            successor_ids: set[str] = successors.get(node_id, set())
            if successor_ids:
                upper_bound: int = min(layer_of[successor_id] - 1 for successor_id in successor_ids)
                if upper_bound > layer_of[node_id]:
                    layer_of[node_id] = upper_bound
                    changed = True
                else:
                    changed = changed
            else:
                changed = changed


def _layer_bounds(
    node_id: str,
    layer_of: dict[str, int],
    predecessors: dict[str, set[str]],
    successors: dict[str, set[str]],
) -> tuple[int, int]:
    """Return the feasible layer interval for a node.

    :param node_id: Identifier of the node being relocated.
    :param layer_of: Current layer assignment.
    :param predecessors: Predecessor adjacency table.
    :param successors: Successor adjacency table.
    :returns: Inclusive lower and upper bounds.
    """
    lower_bound: int = 0
    upper_bound: int = max(layer_of.values(), default=0)
    predecessor_ids: set[str] = predecessors.get(node_id, set())
    successor_ids: set[str] = successors.get(node_id, set())

    if predecessor_ids:
        lower_bound = max(layer_of[predecessor_id] + 1 for predecessor_id in predecessor_ids)
    else:
        lower_bound = lower_bound

    if successor_ids:
        upper_bound = min(layer_of[successor_id] - 1 for successor_id in successor_ids)
    else:
        upper_bound = upper_bound

    if upper_bound < lower_bound:
        upper_bound = lower_bound
    else:
        upper_bound = upper_bound

    return lower_bound, upper_bound


def _node_span_cost(
    node_id: str,
    candidate_layer: int,
    layer_of: dict[str, int],
    predecessors: dict[str, set[str]],
    successors: dict[str, set[str]],
) -> int:
    """Measure the total edge span induced by a candidate layer.

    :param node_id: Identifier of the node being evaluated.
    :param candidate_layer: Candidate layer for the node.
    :param layer_of: Current layer assignment.
    :param predecessors: Predecessor adjacency table.
    :param successors: Successor adjacency table.
    :returns: Sum of predecessor and successor spans.
    """
    cost: int = 0
    predecessor_id: str
    successor_id: str

    # The promotion heuristic minimizes local edge lengths to reduce the amount of
    # dummy nodes that later phases need to insert for long edges.
    for predecessor_id in predecessors.get(node_id, set()):
        cost += candidate_layer - layer_of[predecessor_id]

    for successor_id in successors.get(node_id, set()):
        cost += layer_of[successor_id] - candidate_layer

    return cost


def _promote_nodes(
    order: list[str],
    layer_of: dict[str, int],
    predecessors: dict[str, set[str]],
    successors: dict[str, set[str]],
) -> None:
    """Relocate nodes within feasible bounds to reduce local span cost.

    :param order: Topological order of nodes.
    :param layer_of: Mutable layer assignment.
    :param predecessors: Predecessor adjacency table.
    :param successors: Successor adjacency table.
    :returns: ``None``.
    """
    max_iterations: int = 8

    # A bounded number of local passes is enough here because the heuristic is only a
    # refinement stage after longest-path layering and sink compaction.
    for _ in range(max_iterations):
        moved: bool = False
        node_id: str

        for node_id in order:
            lower_bound: int
            upper_bound: int
            lower_bound, upper_bound = _layer_bounds(node_id, layer_of, predecessors, successors)
            current_layer: int = layer_of[node_id]
            best_layer: int = current_layer
            best_cost: int = _node_span_cost(node_id, current_layer, layer_of, predecessors, successors)

            candidate_layer: int
            for candidate_layer in range(lower_bound, upper_bound + 1):
                candidate_cost: int = _node_span_cost(
                    node_id,
                    candidate_layer,
                    layer_of,
                    predecessors,
                    successors,
                )
                if candidate_cost < best_cost:
                    best_cost = candidate_cost
                    best_layer = candidate_layer
                else:
                    best_cost = best_cost

            if best_layer != current_layer:
                layer_of[node_id] = best_layer
                moved = True
            else:
                moved = moved

        _compact_to_sinks(order, layer_of, successors)

        if not moved:
            break
        else:
            moved = moved


def _node_layer_constraint(node: SugiyamaNode | None) -> str:
    """Return the normalized layer constraint of a node.

    :param node: Node to inspect.
    :returns: Constraint name or the empty string.
    """
    constraint: str = ""

    if node is not None:
        value: Any = (
            node.get_property("layer_constraint", None)
            or node.get_property("layerConstraint", None)
            or node.get_layout_option("org.vera.sugiyama.layered.layering.layerConstraint", None)
            or ""
        )
        constraint = str(value).upper()
    else:
        constraint = ""

    return constraint


def _node_layer_id(node: SugiyamaNode | None) -> int | None:
    """Return the explicit layer id requested by a node.

    :param node: Node to inspect.
    :returns: Non-negative layer id or ``None``.
    """
    parsed_layer: int | None = None

    if node is not None:
        value: Any = (
            node.get_property("layer_id", None)
            or node.get_property("layerId", None)
            or node.get_layout_option("org.vera.sugiyama.layered.layering.layerId", None)
        )
        candidate_layer: int | None = _read_integer_candidate(value)
        if candidate_layer is not None and candidate_layer >= 0:
            parsed_layer = candidate_layer
        else:
            parsed_layer = None
    else:
        parsed_layer = None

    return parsed_layer


def _apply_first_constraints(
    first_nodes: list[str],
    order: list[str],
    layer_of: dict[str, int],
    predecessors: dict[str, set[str]],
) -> None:
    """Apply FIRST constraints and re-propagate predecessor feasibility.

    :param first_nodes: Nodes constrained to the first layer.
    :param order: Topological order.
    :param layer_of: Mutable layer assignment.
    :param predecessors: Predecessor adjacency table.
    :returns: ``None``.
    """
    node_id: str
    changed: bool

    for node_id in first_nodes:
        layer_of[node_id] = 0

    changed = True
    while changed:
        changed = False
        for node_id in order:
            predecessor_ids: set[str] = predecessors.get(node_id, set())
            if predecessor_ids:
                required_layer: int = max(layer_of[predecessor_id] + 1 for predecessor_id in predecessor_ids)
                if required_layer > layer_of[node_id]:
                    layer_of[node_id] = required_layer
                    changed = True
                else:
                    changed = changed
            else:
                changed = changed


def _apply_last_constraints(last_nodes: list[str], layer_of: dict[str, int]) -> None:
    """Push LAST-constrained nodes behind the unconstrained suffix.

    :param last_nodes: Nodes constrained to the last layer.
    :param layer_of: Mutable layer assignment.
    :returns: ``None``.
    """
    excluded_nodes: set[str] = set(last_nodes)
    max_other_layer: int = max(
        (layer for node_id, layer in layer_of.items() if node_id not in excluded_nodes),
        default=0,
    )
    target_last_layer: int = max_other_layer + 1
    node_id: str

    for node_id in last_nodes:
        layer_of[node_id] = max(layer_of[node_id], target_last_layer)


def _apply_exact_constraints(exact_nodes: list[str], node_by_id: dict[str, SugiyamaNode], layer_of: dict[str, int]) -> None:
    """Apply explicit numeric layer ids.

    :param exact_nodes: Nodes with an explicit layer id.
    :param node_by_id: Node lookup table.
    :param layer_of: Mutable layer assignment.
    :returns: ``None``.
    """
    node_id: str

    for node_id in exact_nodes:
        exact_layer: int | None = _node_layer_id(node_by_id.get(node_id, None))
        if exact_layer is not None:
            layer_of[node_id] = max(layer_of[node_id], exact_layer)
        else:
            layer_of[node_id] = layer_of[node_id]


def _apply_constraints(
    node_by_id: dict[str, SugiyamaNode],
    layer_of: dict[str, int],
    order: list[str],
    predecessors: dict[str, set[str]],
) -> None:
    """Apply supported layer constraints on top of the heuristic layering.

    :param node_by_id: Node lookup table.
    :param layer_of: Mutable layer assignment.
    :param order: Topological order.
    :param predecessors: Predecessor adjacency table.
    :returns: ``None``.
    """
    first_nodes: list[str] = list()
    last_nodes: list[str] = list()
    exact_nodes: list[str] = list()
    node_id: str

    # Constraints are extracted first so the mutation phase is explicit and later
    # changes can apply the groups in a deterministic order.
    for node_id in order:
        node: SugiyamaNode | None = node_by_id.get(node_id, None)
        constraint: str = _node_layer_constraint(node)
        layer_id: int | None = _node_layer_id(node)

        if constraint == "FIRST":
            first_nodes.append(node_id)
        else:
            first_nodes = first_nodes

        if constraint == "LAST":
            last_nodes.append(node_id)
        else:
            last_nodes = last_nodes

        if layer_id is not None:
            exact_nodes.append(node_id)
        else:
            exact_nodes = exact_nodes

    if first_nodes:
        _apply_first_constraints(first_nodes, order, layer_of, predecessors)
    else:
        first_nodes = first_nodes

    if last_nodes:
        _apply_last_constraints(last_nodes, layer_of)
    else:
        last_nodes = last_nodes

    if exact_nodes:
        _apply_exact_constraints(exact_nodes, node_by_id, layer_of)
    else:
        exact_nodes = exact_nodes


def _normalize_layers(layer_of: dict[str, int]) -> dict[str, int]:
    """Compact sparse layer ids into a dense zero-based range.

    :param layer_of: Layer assignment to normalize.
    :returns: New dense layer assignment.
    """
    used_layers: list[int] = sorted(set(layer_of.values()))
    remap: dict[int, int] = dict()
    normalized_layers: dict[str, int] = dict()
    layer_index: int
    layer_value: int

    # Dense layer ids simplify the subsequent phases because they can use the index
    # directly when creating per-layer arrays and routing structures.
    for layer_index, layer_value in enumerate(used_layers):
        remap[layer_value] = layer_index

    for node_id, original_layer in layer_of.items():
        normalized_layers[node_id] = remap[original_layer]

    return normalized_layers


def _build_default_adjacency(node_ids: list[str]) -> dict[str, set[str]]:
    """Create an empty adjacency table for all nodes.

    :param node_ids: Node identifiers present in the graph.
    :returns: Empty adjacency mapping with one set per node.
    """
    adjacency: dict[str, set[str]] = dict()
    node_id: str

    for node_id in node_ids:
        adjacency[node_id] = set()

    return adjacency


class LayeringPhase(LayoutPhaseBase):
    """Assign graph nodes to discrete layers."""

    __slots__ = ()
    name: str = "layering"

    def run(self, context: LayoutContext) -> None:
        """Compute the layer assignment for the current graph.

        :param context: Pipeline execution context.
        :returns: ``None``.
        """
        node_ids: list[str] = [node.identifier for node in context.graph.children]
        node_by_id: dict[str, SugiyamaNode] = context.graph.node_by_id()
        prefer_model_order: bool = _consider_model_order_enabled(context)
        strategy: LayeringStrategy = _layering_strategy(context)
        successors: dict[str, set[str]] = context.phase_state.dag_successors
        predecessors: dict[str, set[str]] = context.phase_state.dag_predecessors

        # The layering phase requires a complete DAG view; when previous phases did not
        # populate adjacency we still create empty tables so all downstream code sees a
        # uniform structure.
        if not successors:
            successors = _build_default_adjacency(node_ids)
        else:
            successors = successors

        if not predecessors:
            predecessors = _build_default_adjacency(node_ids)
        else:
            predecessors = predecessors

        # The final layering combines deterministic topological order, longest-path
        # placement and optional refinement depending on the configured strategy.
        order: list[str] = _topological_order(
            node_ids,
            successors,
            predecessors,
            node_by_id,
            prefer_model_order,
        )
        layer_of: dict[str, int] = _longest_path_layers(order, predecessors)

        if strategy in {LayeringStrategy.NETWORK_SIMPLEX, LayeringStrategy.INTERACTIVE}:
            _compact_to_sinks(order, layer_of, successors)
            _promote_nodes(order, layer_of, predecessors, successors)
        else:
            if strategy in {LayeringStrategy.LONGEST_PATH, LayeringStrategy.LONGEST_PATH_SOURCE}:
                strategy = strategy
            else:
                _compact_to_sinks(order, layer_of, successors)

        _apply_constraints(node_by_id, layer_of, order, predecessors)
        normalized_layer_of: dict[str, int] = _normalize_layers(layer_of)

        context.phase_state.topological_order.clear()
        context.phase_state.topological_order.extend(order)
        context.phase_state.layer_of.clear()
        context.phase_state.layer_of.update(normalized_layer_of)
        context.report.add_note(
            "Layering uses longest-path assignment, sink compaction, local node promotion, "
            "basic layer constraints and layer normalization.",
        )
