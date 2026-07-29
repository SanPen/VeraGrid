# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Long-edge expansion phase for the Sugiyama layered pipeline."""

from __future__ import annotations

from VeraGridEngine.Utils.SugiyamaLayered.pipeline import LayoutContext, LayoutPhaseBase


class VirtualNode:
    """Virtual node inserted to split a long edge across layers.

    :param identifier: Virtual node identifier.
    :type identifier: str
    :param width: Node width.
    :type width: float
    :param height: Node height.
    :type height: float
    :param is_dummy: Whether this node is synthetic.
    :type is_dummy: bool
    :param original_edge_id: Source edge identifier for dummy nodes.
    :type original_edge_id: str | None
    :param chain_index: Position inside the dummy chain.
    :type chain_index: int
    :param chain_priority: Dummy chain priority used in ordering.
    :type chain_priority: int
    :param model_order: Stable model-order key.
    :type model_order: int
    """

    __slots__ = (
        "_identifier",
        "_width",
        "_height",
        "_is_dummy",
        "_original_edge_id",
        "_chain_index",
        "_chain_priority",
        "_model_order",
    )

    def __init__(
            self,
            identifier: str,
            width: float,
            height: float,
            is_dummy: bool = False,
            original_edge_id: str | None = None,
            chain_index: int = 0,
            chain_priority: int = 0,
            model_order: int = 0,
    ) -> None:
        self._identifier: str = identifier
        self._width: float = width
        self._height: float = height
        self._is_dummy: bool = is_dummy
        self._original_edge_id: str | None = original_edge_id
        self._chain_index: int = chain_index
        self._chain_priority: int = chain_priority
        self._model_order: int = model_order

    @property
    def identifier(self) -> str:
        """Return the virtual node identifier.

        :return: Virtual node identifier.
        :rtype: str
        """
        return self._identifier

    @property
    def width(self) -> float:
        """Return the virtual node width.

        :return: Virtual node width.
        :rtype: float
        """
        return self._width

    @property
    def height(self) -> float:
        """Return the virtual node height.

        :return: Virtual node height.
        :rtype: float
        """
        return self._height

    @property
    def is_dummy(self) -> bool:
        """Return whether the node is synthetic.

        :return: ``True`` for dummy nodes.
        :rtype: bool
        """
        return self._is_dummy

    @property
    def original_edge_id(self) -> str | None:
        """Return the original edge identifier.

        :return: Original edge identifier.
        :rtype: str | None
        """
        return self._original_edge_id

    @property
    def chain_index(self) -> int:
        """Return the dummy-chain index.

        :return: Dummy-chain index.
        :rtype: int
        """
        return self._chain_index

    @property
    def chain_priority(self) -> int:
        """Return the dummy-chain priority.

        :return: Dummy-chain priority.
        :rtype: int
        """
        return self._chain_priority

    @property
    def model_order(self) -> int:
        """Return the stable model-order key.

        :return: Stable model-order key.
        :rtype: int
        """
        return self._model_order


def _node_model_order(node_id: str, fallback: int, node_by_id: dict[str, object]) -> int:
    """Resolve the model-order key for one node.

    :param node_id: Node identifier.
    :type node_id: str
    :param fallback: Fallback order.
    :type fallback: int
    :param node_by_id: Node lookup.
    :type node_by_id: dict[str, object]
    :return: Model-order key.
    :rtype: int
    """
    node = node_by_id.get(node_id, None)
    candidates: tuple[object, ...]

    if node is None:
        return fallback
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

        return fallback


def _edge_chain_priority(entry: dict[str, str | bool | None]) -> int:
    """Compute the priority of one expanded edge chain.

    :param entry: Oriented edge entry.
    :type entry: dict[str, str | bool | None]
    :return: Priority key.
    :rtype: int
    """
    reversed_value: object = entry.get("reversed", False)

    if bool(reversed_value):
        return 1
    else:
        return 0


def _virtual_node_sort_key(node_id: str, expanded_nodes: dict[str, VirtualNode]) -> tuple[int, int, int, bool, str]:
    """Build the stable ordering key for one expanded node.

    :param node_id: Expanded node identifier.
    :type node_id: str
    :param expanded_nodes: Expanded node lookup.
    :type expanded_nodes: dict[str, VirtualNode]
    :return: Stable ordering key.
    :rtype: tuple[int, int, int, bool, str]
    """
    virtual_node: VirtualNode = expanded_nodes[node_id]
    key: tuple[int, int, int, bool, str] = (
        virtual_node.chain_priority,
        virtual_node.model_order,
        virtual_node.chain_index,
        virtual_node.is_dummy,
        node_id,
    )
    return key


def _sort_expanded_layer_nodes(node_ids: list[str], expanded_nodes: dict[str, VirtualNode]) -> list[str]:
    """Return one stable ordering of expanded layer nodes.

    :param node_ids: Node identifiers in one expanded layer.
    :type node_ids: list[str]
    :param expanded_nodes: Expanded node lookup.
    :type expanded_nodes: dict[str, VirtualNode]
    :return: Sorted node identifiers.
    :rtype: list[str]
    """
    sortable_items: list[tuple[tuple[int, int, int, bool, str], str]] = list()
    node_id: str

    for node_id in node_ids:
        sortable_items.append((_virtual_node_sort_key(node_id, expanded_nodes), node_id))

    sortable_items.sort()
    return [item[1] for item in sortable_items]


class LongEdgePhase(LayoutPhaseBase):
    """Split edges that span more than one layer."""

    __slots__ = ()

    name: str = "long-edges"

    def run(self, context: LayoutContext) -> None:
        """Execute the long-edge expansion phase.

        The phase inserts one dummy node on every intermediate layer crossed by
        a long edge. That transformation is required so later crossing
        minimization and coordinate assignment can operate on one proper
        layer-by-layer graph.

        :param context: Shared pipeline context.
        :type context: LayoutContext
        :return: None.
        :rtype: None
        """
        layer_of: dict[str, int] = context.phase_state.layer_of
        oriented_edges: list[dict[str, str | bool | None]] = context.phase_state.oriented_edges

        node_by_id: dict[str, object] = context.graph.node_by_id()
        topological_order_obj: list[str] = context.phase_state.topological_order
        node_order: dict[str, int] = dict()
        expanded_nodes: dict[str, VirtualNode] = dict()
        expanded_layers: dict[int, list[str]] = dict()
        expanded_edges: list[tuple[str, str, str, int]] = list()
        edge_paths: dict[str, list[str]] = dict()
        long_edges: list[str] = list()
        dummy_size: float = 12.0
        dummy_counter: int = 0

        for index, node_id in enumerate(topological_order_obj):
            node_order[str(node_id)] = index

        for node in context.graph.children:
            expanded_nodes[node.identifier] = VirtualNode(
                identifier=node.identifier,
                width=node.width,
                height=node.height,
                is_dummy=False,
                model_order=_node_model_order(node.identifier, node_order.get(node.identifier, 0), node_by_id),
            )

        for node_id, layer in layer_of.items():
            layer_index: int = int(layer)
            if layer_index in expanded_layers:
                expanded_layers[layer_index].append(node_id)
            else:
                expanded_layers[layer_index] = [node_id]

        for edge_index, entry in enumerate(oriented_edges):
            edge_id: str = str(entry["edge_id"])
            source_id: str = str(entry["source"])
            target_id: str = str(entry["target"])
            source_layer: int = int(layer_of.get(source_id, 0))
            target_layer: int = int(layer_of.get(target_id, source_layer))

            if source_id == target_id or target_layer - source_layer <= 1:
                expanded_edges.append((edge_id, source_id, target_id, 0))
                edge_paths[edge_id] = [source_id, target_id]
            else:
                long_edges.append(edge_id)
                previous_node_id: str = source_id
                path: list[str] = [source_id]
                source_order: int = _node_model_order(source_id, node_order.get(source_id, edge_index), node_by_id)
                target_order: int = _node_model_order(target_id, node_order.get(target_id, edge_index), node_by_id)
                chain_priority: int = _edge_chain_priority(entry)

                for hop_layer in range(source_layer + 1, target_layer):
                    dummy_id: str = f"__dummy__{edge_id}__{dummy_counter}"
                    dummy_counter += 1
                    expanded_nodes[dummy_id] = VirtualNode(
                        identifier=dummy_id,
                        width=dummy_size,
                        height=dummy_size,
                        is_dummy=True,
                        original_edge_id=edge_id,
                        chain_index=hop_layer - source_layer,
                        chain_priority=chain_priority,
                        model_order=min(source_order, target_order),
                    )

                    if hop_layer in expanded_layers:
                        expanded_layers[hop_layer].append(dummy_id)
                    else:
                        expanded_layers[hop_layer] = [dummy_id]

                    expanded_edges.append((edge_id, previous_node_id, dummy_id, hop_layer - source_layer - 1))
                    path.append(dummy_id)
                    previous_node_id = dummy_id

                expanded_edges.append((edge_id, previous_node_id, target_id, target_layer - source_layer - 1))
                path.append(target_id)
                edge_paths[edge_id] = path

        for layer_index, node_ids in expanded_layers.items():
            expanded_layers[layer_index] = _sort_expanded_layer_nodes(node_ids, expanded_nodes)

        context.phase_state.long_edges.clear()
        context.phase_state.long_edges.extend(sorted(set(long_edges)))
        context.phase_state.expanded_nodes.clear()
        context.phase_state.expanded_nodes.update(expanded_nodes)
        context.phase_state.expanded_layers.clear()
        context.phase_state.expanded_layers.update(expanded_layers)
        context.phase_state.expanded_edges.clear()
        context.phase_state.expanded_edges.extend(expanded_edges)
        context.phase_state.edge_paths.clear()
        context.phase_state.edge_paths.update(edge_paths)
        context.report.add_note(
            f"Long-edge expansion inserted {dummy_counter} dummy node(s) across {len(set(long_edges))} edge(s)."
        )
