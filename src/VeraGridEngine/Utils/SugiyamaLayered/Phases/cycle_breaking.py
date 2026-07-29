# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Cycle breaking phase for the Sugiyama layered pipeline."""

from __future__ import annotations

from VeraGridEngine.Utils.SugiyamaLayered.options import ConsiderModelOrderStrategy, CycleBreakingStrategy
from VeraGridEngine.Utils.SugiyamaLayered.pipeline import LayoutContext, LayoutPhaseBase


class FlatEdge:
    """Flattened edge between resolved node endpoints.

    :param edge_id: Original edge identifier.
    :type edge_id: str
    :param source: Source node identifier.
    :type source: str
    :param target: Target node identifier.
    :type target: str
    :param source_port: Optional source port identifier.
    :type source_port: str | None
    :param target_port: Optional target port identifier.
    :type target_port: str | None
    """

    __slots__ = ("_edge_id", "_source", "_target", "_source_port", "_target_port")

    def __init__(
            self,
            edge_id: str,
            source: str,
            target: str,
            source_port: str | None = None,
            target_port: str | None = None,
    ) -> None:
        self._edge_id: str = edge_id
        self._source: str = source
        self._target: str = target
        self._source_port: str | None = source_port
        self._target_port: str | None = target_port

    @property
    def edge_id(self) -> str:
        """Return the original edge identifier.

        :return: Original edge identifier.
        :rtype: str
        """
        return self._edge_id

    @property
    def source(self) -> str:
        """Return the source node identifier.

        :return: Source node identifier.
        :rtype: str
        """
        return self._source

    @property
    def target(self) -> str:
        """Return the target node identifier.

        :return: Target node identifier.
        :rtype: str
        """
        return self._target

    @property
    def source_port(self) -> str | None:
        """Return the optional source port identifier.

        :return: Source port identifier.
        :rtype: str | None
        """
        return self._source_port

    @property
    def target_port(self) -> str | None:
        """Return the optional target port identifier.

        :return: Target port identifier.
        :rtype: str | None
        """
        return self._target_port


def _edge_direction_priority(edge: object | None) -> int:
    """Resolve the direction priority of one edge.

    :param edge: Original graph edge.
    :type edge: object | None
    :return: Direction priority.
    :rtype: int
    """
    candidates: tuple[object, ...]

    if edge is None:
        return 0
    else:
        candidates = (
            edge.get_property("directionPriority", None),
            edge.get_property("direction_priority", None),
            edge.get_layout_option("org.vera.sugiyama.layered.priority.direction", None),
        )

        for value in candidates:
            if value is None:
                pass
            else:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    pass

        return 0


def _node_model_order(node_id: str, node_order: dict[str, int], node_by_id: dict[str, object]) -> int:
    """Resolve the stable model order of one node.

    :param node_id: Node identifier.
    :type node_id: str
    :param node_order: Fallback order map.
    :type node_order: dict[str, int]
    :param node_by_id: Node lookup.
    :type node_by_id: dict[str, object]
    :return: Model-order key.
    :rtype: int
    """
    node = node_by_id.get(node_id, None)
    candidates: tuple[object, ...]

    if node is None:
        return node_order.get(node_id, 0)
    else:
        candidates = (
            node.get_property("modelOrder", None),
            node.get_property("model_order", None),
            node.get_layout_option("org.vera.sugiyama.layered.considerModelOrder.groupModelOrder.cycleBreakingId", None),
        )

        for value in candidates:
            if value is None:
                pass
            else:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    pass

        return node_order.get(node_id, 0)


def _node_kind_bias(node_id: str, node_by_id: dict[str, object]) -> int:
    """Return the kind-based direction bias of one node.

    :param node_id: Node identifier.
    :type node_id: str
    :param node_by_id: Node lookup.
    :type node_by_id: dict[str, object]
    :return: Direction bias.
    :rtype: int
    """
    node = node_by_id.get(node_id, None)

    if node is None:
        return 0
    else:
        kind_name: str = str(node.get_property("kind", "")).upper()

        if kind_name == "INPUT_CONN":
            return 2
        else:
            if kind_name == "OUTPUT_CONN":
                return -2
            else:
                return 0


def _consider_model_order_strength(context: LayoutContext) -> int:
    """Return the model-order preference strength.

    :param context: Shared pipeline context.
    :type context: LayoutContext
    :return: Preference strength.
    :rtype: int
    """
    options: dict[str, object] = context.option_resolver.resolve_for_element(context.graph.layout_options)
    strategy_name: ConsiderModelOrderStrategy = options.get(
        "org.vera.sugiyama.layered.considerModelOrder.strategy",
        ConsiderModelOrderStrategy.NONE,
    )

    if strategy_name is ConsiderModelOrderStrategy.NONE:
        return 0
    else:
        if strategy_name in {
            ConsiderModelOrderStrategy.NODES,
            ConsiderModelOrderStrategy.NODES_AND_EDGES,
            ConsiderModelOrderStrategy.PREFER_NODES,
        }:
            return 1
        else:
            return 0


def _feedback_edges_enabled(context: LayoutContext) -> bool:
    """Return whether feedback edges should be reported.

    :param context: Shared pipeline context.
    :type context: LayoutContext
    :return: ``True`` when feedback edges are enabled.
    :rtype: bool
    """
    options: dict[str, object] = context.option_resolver.resolve_for_element(context.graph.layout_options)
    value: object = options.get("org.vera.sugiyama.layered.feedbackEdges", False)

    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    else:
        return bool(value)


def _cycle_breaking_strategy(context: LayoutContext) -> CycleBreakingStrategy:
    """Resolve the cycle-breaking strategy.

    :param context: Shared pipeline context.
    :type context: LayoutContext
    :return: Strategy name.
    :rtype: CycleBreakingStrategy
    """
    options: dict[str, object] = context.option_resolver.resolve_for_element(context.graph.layout_options)
    strategy_name: CycleBreakingStrategy = options.get(
        "org.vera.sugiyama.layered.cycleBreaking.strategy",
        CycleBreakingStrategy.GREEDY,
    )
    return strategy_name


def _flatten_edges(context: LayoutContext) -> tuple[list[FlatEdge], list[str]]:
    """Flatten graph edges to pure node-to-node edges.

    :param context: Shared pipeline context.
    :type context: LayoutContext
    :return: Flattened edges and skipped edge identifiers.
    :rtype: tuple[list[FlatEdge], list[str]]
    """
    node_ids: set[str] = set()
    port_to_owner: dict[str, str] = dict()
    flat_edges: list[FlatEdge] = list()
    skipped_edges: list[str] = list()

    for node in context.graph.children:
        node_ids.add(node.identifier)
        for port in node.ports:
            port_to_owner[port.identifier] = node.identifier

    for edge in context.graph.edges:
        if len(edge.sources) == 0 or len(edge.targets) == 0:
            skipped_edges.append(edge.identifier)
        else:
            for source in edge.sources:
                for target in edge.targets:
                    source_node: str | None
                    target_node: str | None

                    if source in node_ids:
                        source_node = source
                    else:
                        source_node = port_to_owner.get(source, None)

                    if target in node_ids:
                        target_node = target
                    else:
                        target_node = port_to_owner.get(target, None)

                    if source_node is None or target_node is None:
                        skipped_edges.append(edge.identifier)
                    else:
                        flat_edges.append(
                            FlatEdge(
                                edge_id=edge.identifier,
                                source=source_node,
                                target=target_node,
                                source_port=None if source in node_ids else source,
                                target_port=None if target in node_ids else target,
                            )
                        )

    return flat_edges, skipped_edges


def _build_adjacency(
        node_ids: list[str],
        flat_edges: list[FlatEdge],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Build successor and predecessor adjacency maps.

    :param node_ids: Node identifiers.
    :type node_ids: list[str]
    :param flat_edges: Flattened graph edges.
    :type flat_edges: list[FlatEdge]
    :return: Successor and predecessor maps.
    :rtype: tuple[dict[str, set[str]], dict[str, set[str]]]
    """
    successors: dict[str, set[str]] = dict()
    predecessors: dict[str, set[str]] = dict()
    node_id: str

    for node_id in node_ids:
        successors[node_id] = set()
        predecessors[node_id] = set()

    for flat_edge in flat_edges:
        if flat_edge.source == flat_edge.target:
            pass
        else:
            successors[flat_edge.source].add(flat_edge.target)
            predecessors[flat_edge.target].add(flat_edge.source)

    return successors, predecessors


def _build_weighted_adjacency(
        node_ids: list[str],
        flat_edges: list[FlatEdge],
        edge_by_id: dict[str, object],
) -> tuple[dict[str, int], dict[str, int]]:
    """Build weighted in-degree and out-degree maps.

    :param node_ids: Node identifiers.
    :type node_ids: list[str]
    :param flat_edges: Flattened graph edges.
    :type flat_edges: list[FlatEdge]
    :param edge_by_id: Original edge lookup.
    :type edge_by_id: dict[str, object]
    :return: Weighted out-degree and in-degree maps.
    :rtype: tuple[dict[str, int], dict[str, int]]
    """
    weighted_out: dict[str, int] = dict()
    weighted_in: dict[str, int] = dict()
    node_id: str

    for node_id in node_ids:
        weighted_out[node_id] = 0
        weighted_in[node_id] = 0

    for flat_edge in flat_edges:
        if flat_edge.source == flat_edge.target:
            pass
        else:
            input_edge: object | None = edge_by_id.get(flat_edge.edge_id, None)
            priority: int = _edge_direction_priority(input_edge)
            weight: int = 1 + abs(priority)
            weighted_out[flat_edge.source] = weighted_out[flat_edge.source] + weight
            weighted_in[flat_edge.target] = weighted_in[flat_edge.target] + weight

    return weighted_out, weighted_in


def _sorted_sink_candidates(
        remaining: set[str],
        successors: dict[str, set[str]],
        node_order: dict[str, int],
        node_by_id: dict[str, object],
) -> list[str]:
    """Return the sorted sink candidates.

    :param remaining: Remaining node identifiers.
    :type remaining: set[str]
    :param successors: Successor adjacency map.
    :type successors: dict[str, set[str]]
    :param node_order: Fallback order.
    :type node_order: dict[str, int]
    :param node_by_id: Node lookup.
    :type node_by_id: dict[str, object]
    :return: Sorted sink candidates.
    :rtype: list[str]
    """
    items: list[tuple[tuple[int, str], str]] = list()
    node_id: str

    for node_id in sorted(remaining):
        local_successors: set[str] = successors.get(node_id, set()) & remaining
        if len(local_successors) == 0:
            key: tuple[int, str] = (_node_model_order(node_id, node_order, node_by_id), node_id)
            items.append((key, node_id))
        else:
            pass

    items.sort()
    return [item[1] for item in items]


def _sorted_source_candidates(
        remaining: set[str],
        predecessors: dict[str, set[str]],
        node_order: dict[str, int],
        node_by_id: dict[str, object],
        model_order_strength: int,
) -> list[str]:
    """Return the sorted source candidates.

    :param remaining: Remaining node identifiers.
    :type remaining: set[str]
    :param predecessors: Predecessor adjacency map.
    :type predecessors: dict[str, set[str]]
    :param node_order: Fallback order.
    :type node_order: dict[str, int]
    :param node_by_id: Node lookup.
    :type node_by_id: dict[str, object]
    :param model_order_strength: Model-order preference strength.
    :type model_order_strength: int
    :return: Sorted source candidates.
    :rtype: list[str]
    """
    items: list[tuple[tuple[int, str], str]] = list()
    node_id: str

    for node_id in sorted(remaining):
        local_predecessors: set[str] = predecessors.get(node_id, set()) & remaining
        if len(local_predecessors) == 0:
            if model_order_strength != 0:
                primary_order: int = _node_model_order(node_id, node_order, node_by_id)
            else:
                primary_order = node_order.get(node_id, 0)
            key: tuple[int, str] = (primary_order, node_id)
            items.append((key, node_id))
        else:
            pass

    items.sort()
    return [item[1] for item in items]


def _score_cycle_breaking_node(
        node_id: str,
        remaining: set[str],
        successors: dict[str, set[str]],
        predecessors: dict[str, set[str]],
        weighted_out: dict[str, int],
        weighted_in: dict[str, int],
        node_order: dict[str, int],
        node_by_id: dict[str, object],
        model_order_strength: int,
) -> tuple[int, int, int, int, str]:
    """Score one node during greedy cycle breaking.

    :param node_id: Node identifier.
    :type node_id: str
    :param remaining: Remaining node identifiers.
    :type remaining: set[str]
    :param successors: Successor adjacency map.
    :type successors: dict[str, set[str]]
    :param predecessors: Predecessor adjacency map.
    :type predecessors: dict[str, set[str]]
    :param weighted_out: Weighted out-degree map.
    :type weighted_out: dict[str, int]
    :param weighted_in: Weighted in-degree map.
    :type weighted_in: dict[str, int]
    :param node_order: Fallback order.
    :type node_order: dict[str, int]
    :param node_by_id: Node lookup.
    :type node_by_id: dict[str, object]
    :param model_order_strength: Model-order preference strength.
    :type model_order_strength: int
    :return: Score tuple.
    :rtype: tuple[int, int, int, int, str]
    """
    out_degree: int = len(successors.get(node_id, set()) & remaining)
    in_degree: int = len(predecessors.get(node_id, set()) & remaining)
    model_order: int = _node_model_order(node_id, node_order, node_by_id)
    kind_bias: int = _node_kind_bias(node_id, node_by_id)
    weighted_bias: int = weighted_out.get(node_id, 0) - weighted_in.get(node_id, 0)
    ordering_term: int

    if model_order_strength != 0:
        ordering_term = -model_order
    else:
        ordering_term = -node_order.get(node_id, 0)

    return (out_degree - in_degree + kind_bias, weighted_bias, ordering_term, kind_bias, node_id)


def _choose_best_cycle_breaking_node(
        remaining: set[str],
        successors: dict[str, set[str]],
        predecessors: dict[str, set[str]],
        weighted_out: dict[str, int],
        weighted_in: dict[str, int],
        node_order: dict[str, int],
        node_by_id: dict[str, object],
        model_order_strength: int,
) -> str:
    """Choose the next node in the greedy cycle-breaking order.

    :param remaining: Remaining node identifiers.
    :type remaining: set[str]
    :param successors: Successor adjacency map.
    :type successors: dict[str, set[str]]
    :param predecessors: Predecessor adjacency map.
    :type predecessors: dict[str, set[str]]
    :param weighted_out: Weighted out-degree map.
    :type weighted_out: dict[str, int]
    :param weighted_in: Weighted in-degree map.
    :type weighted_in: dict[str, int]
    :param node_order: Fallback order.
    :type node_order: dict[str, int]
    :param node_by_id: Node lookup.
    :type node_by_id: dict[str, object]
    :param model_order_strength: Model-order preference strength.
    :type model_order_strength: int
    :return: Chosen node identifier.
    :rtype: str
    """
    best_node_id: str = ""
    best_score: tuple[int, int, int, int, str] | None = None
    node_id: str

    for node_id in sorted(remaining):
        current_score: tuple[int, int, int, int, str] = _score_cycle_breaking_node(
            node_id=node_id,
            remaining=remaining,
            successors=successors,
            predecessors=predecessors,
            weighted_out=weighted_out,
            weighted_in=weighted_in,
            node_order=node_order,
            node_by_id=node_by_id,
            model_order_strength=model_order_strength,
        )
        if best_score is None or current_score > best_score:
            best_score = current_score
            best_node_id = node_id
        else:
            pass

    return best_node_id


def _greedy_order(
        node_ids: list[str],
        successors: dict[str, set[str]],
        predecessors: dict[str, set[str]],
        weighted_out: dict[str, int],
        weighted_in: dict[str, int],
        node_by_id: dict[str, object],
        model_order_strength: int,
) -> list[str]:
    """Build a greedy acyclic ordering.

    :param node_ids: Node identifiers.
    :type node_ids: list[str]
    :param successors: Successor adjacency map.
    :type successors: dict[str, set[str]]
    :param predecessors: Predecessor adjacency map.
    :type predecessors: dict[str, set[str]]
    :param weighted_out: Weighted out-degree map.
    :type weighted_out: dict[str, int]
    :param weighted_in: Weighted in-degree map.
    :type weighted_in: dict[str, int]
    :param node_by_id: Node lookup.
    :type node_by_id: dict[str, object]
    :param model_order_strength: Model-order preference strength.
    :type model_order_strength: int
    :return: Greedy node order.
    :rtype: list[str]
    """
    remaining: set[str] = set(node_ids)
    left: list[str] = list()
    right: list[str] = list()
    node_order: dict[str, int] = dict()
    index: int

    for index, node_id in enumerate(node_ids):
        node_order[node_id] = index

    while len(remaining) > 0:
        sinks: list[str] = _sorted_sink_candidates(remaining, successors, node_order, node_by_id)
        if len(sinks) > 0:
            selected_sink: str = sinks[0]
            right.append(selected_sink)
            remaining.remove(selected_sink)
        else:
            sources: list[str] = _sorted_source_candidates(
                remaining,
                predecessors,
                node_order,
                node_by_id,
                model_order_strength,
            )
            if len(sources) > 0:
                selected_source: str = sources[0]
                left.append(selected_source)
                remaining.remove(selected_source)
            else:
                chosen_node_id: str = _choose_best_cycle_breaking_node(
                    remaining=remaining,
                    successors=successors,
                    predecessors=predecessors,
                    weighted_out=weighted_out,
                    weighted_in=weighted_in,
                    node_order=node_order,
                    node_by_id=node_by_id,
                    model_order_strength=model_order_strength,
                )
                left.append(chosen_node_id)
                remaining.remove(chosen_node_id)

    return left + list(reversed(right))


def _create_oriented_edge_entry(
        flat_edge: FlatEdge,
        source: str,
        target: str,
        reversed_flag: bool,
) -> dict[str, str | bool | None]:
    """Create one oriented edge entry for phase state.

    :param flat_edge: Flattened edge data.
    :type flat_edge: FlatEdge
    :param source: Oriented source identifier.
    :type source: str
    :param target: Oriented target identifier.
    :type target: str
    :param reversed_flag: Whether the original edge was reversed.
    :type reversed_flag: bool
    :return: Oriented edge entry.
    :rtype: dict[str, str | bool | None]
    """
    oriented_edge: dict[str, str | bool | None] = dict()
    oriented_edge["edge_id"] = flat_edge.edge_id
    oriented_edge["source"] = source
    oriented_edge["target"] = target
    oriented_edge["reversed"] = reversed_flag
    oriented_edge["source_port"] = flat_edge.source_port
    oriented_edge["target_port"] = flat_edge.target_port
    return oriented_edge


class CycleBreakingPhase(LayoutPhaseBase):
    """Orient edges to obtain one acyclic graph."""

    __slots__ = ()

    name: str = "cycle-breaking"

    def run(self, context: LayoutContext) -> None:
        """Execute the cycle-breaking phase.

        The phase first flattens port endpoints to their owner nodes, then
        computes one greedy node order, and finally orients all edges according
        to that order and the configured option biases.

        :param context: Shared pipeline context.
        :type context: LayoutContext
        :return: None.
        :rtype: None
        """
        node_ids: list[str] = [node.identifier for node in context.graph.children]
        node_by_id: dict[str, object] = context.graph.node_by_id()
        model_order_strength: int = _consider_model_order_strength(context)
        feedback_edges_enabled: bool = _feedback_edges_enabled(context)
        strategy_name: str = _cycle_breaking_strategy(context)
        flat_edges: list[FlatEdge]
        skipped_edges: list[str]
        flat_edges, skipped_edges = _flatten_edges(context)
        successors: dict[str, set[str]]
        predecessors: dict[str, set[str]]
        successors, predecessors = _build_adjacency(node_ids, flat_edges)
        edge_by_id: dict[str, object] = dict()
        weighted_out: dict[str, int]
        weighted_in: dict[str, int]
        greedy_order: list[str]
        rank: dict[str, int] = dict()
        reversed_edges: list[str] = list()
        feedback_edges: list[str] = list()
        dag_successors: dict[str, set[str]] = dict()
        dag_predecessors: dict[str, set[str]] = dict()
        oriented_edges: list[dict[str, str | bool | None]] = list()
        index: int
        flat_edge: FlatEdge

        for edge in context.graph.edges:
            edge_by_id[edge.identifier] = edge

        weighted_out, weighted_in = _build_weighted_adjacency(node_ids, flat_edges, edge_by_id)

        if strategy_name is CycleBreakingStrategy.NONE:
            greedy_order = list(node_ids)
        else:
            greedy_order = _greedy_order(
                node_ids=node_ids,
                successors=successors,
                predecessors=predecessors,
                weighted_out=weighted_out,
                weighted_in=weighted_in,
                node_by_id=node_by_id,
                model_order_strength=model_order_strength,
            )

        for index, node_id in enumerate(greedy_order):
            rank[node_id] = index
            dag_successors[node_id] = set()
            dag_predecessors[node_id] = set()

        for flat_edge in flat_edges:
            source_id: str = flat_edge.source
            target_id: str = flat_edge.target

            if source_id == target_id:
                if feedback_edges_enabled:
                    feedback_edges.append(flat_edge.edge_id)
                else:
                    pass

                oriented_edges.append(
                    _create_oriented_edge_entry(
                        flat_edge=flat_edge,
                        source=source_id,
                        target=target_id,
                        reversed_flag=False,
                    )
                )
            else:
                input_edge: object | None = edge_by_id.get(flat_edge.edge_id, None)
                priority: int = _edge_direction_priority(input_edge)
                source_rank: int = rank.get(source_id, 0)
                target_rank: int = rank.get(target_id, 0)
                reverse: bool = source_rank > target_rank

                if source_rank == target_rank and model_order_strength != 0:
                    source_model: int = _node_model_order(source_id, rank, node_by_id)
                    target_model: int = _node_model_order(target_id, rank, node_by_id)
                    reverse = source_model > target_model
                else:
                    pass

                if priority > 0:
                    reverse = False
                else:
                    if priority < 0:
                        reverse = True
                    else:
                        pass

                if reverse:
                    oriented_source_id: str = target_id
                    oriented_target_id: str = source_id
                    reversed_edges.append(flat_edge.edge_id)
                    if feedback_edges_enabled:
                        feedback_edges.append(flat_edge.edge_id)
                    else:
                        pass
                else:
                    oriented_source_id = source_id
                    oriented_target_id = target_id

                dag_successors[oriented_source_id].add(oriented_target_id)
                dag_predecessors[oriented_target_id].add(oriented_source_id)
                oriented_edges.append(
                    _create_oriented_edge_entry(
                        flat_edge=flat_edge,
                        source=oriented_source_id,
                        target=oriented_target_id,
                        reversed_flag=reverse,
                    )
                )

        context.phase_state.flat_edges.clear()
        context.phase_state.flat_edges.extend(flat_edges)
        context.phase_state.node_order.clear()
        context.phase_state.node_order.extend(greedy_order)
        context.phase_state.reversed_edges.clear()
        context.phase_state.reversed_edges.update(reversed_edges)
        context.phase_state.feedback_edges.clear()
        context.phase_state.feedback_edges.update(feedback_edges)
        context.phase_state.dag_successors.clear()
        context.phase_state.dag_successors.update(dag_successors)
        context.phase_state.dag_predecessors.clear()
        context.phase_state.dag_predecessors.update(dag_predecessors)
        context.phase_state.oriented_edges.clear()
        context.phase_state.oriented_edges.extend(oriented_edges)

        if len(skipped_edges) > 0:
            context.phase_state.skipped_edges.clear()
            context.phase_state.skipped_edges.update(skipped_edges)
        else:
            context.phase_state.skipped_edges.clear()

        context.report.add_note(
            f"Cycle breaking oriented {len(oriented_edges)} flat edge(s) and reversed {len(reversed_edges)}."
        )
