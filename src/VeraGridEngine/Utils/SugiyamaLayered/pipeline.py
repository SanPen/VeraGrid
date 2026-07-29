# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Pipeline infrastructure for the Sugiyama layered engine."""

from __future__ import annotations

from time import perf_counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from VeraGridEngine.Utils.SugiyamaLayered.Phases.cycle_breaking import FlatEdge
    from VeraGridEngine.Utils.SugiyamaLayered.Phases.long_edges import VirtualNode

from VeraGridEngine.Utils.SugiyamaLayered.model import SugiyamaGraph
from VeraGridEngine.Utils.SugiyamaLayered.options import SugiyamaOptionResolver


class PhaseTiming:
    """Execution timing for one pipeline phase.

    :param name: Phase name.
    :type name: str
    :param seconds: Execution time in seconds.
    :type seconds: float
    """

    __slots__ = ("_name", "_seconds")

    def __init__(self, name: str, seconds: float) -> None:
        self._name: str = name
        self._seconds: float = seconds

    @property
    def name(self) -> str:
        """Return the phase name.

        :return: Phase name.
        :rtype: str
        """
        return self._name

    @property
    def seconds(self) -> float:
        """Return the elapsed phase time.

        :return: Elapsed phase time.
        :rtype: float
        """
        return self._seconds


class PipelineReport:
    """Pipeline execution report.

    :param timings: Optional phase timings.
    :type timings: list[PhaseTiming] | None
    :param notes: Optional diagnostic notes.
    :type notes: list[str] | None
    """

    __slots__ = ("_timings", "_notes")

    def __init__(
            self,
            timings: list[PhaseTiming] | None = None,
            notes: list[str] | None = None,
    ) -> None:
        timings_data: list[PhaseTiming]
        notes_data: list[str]

        if timings is None:
            timings_data = list()
        else:
            timings_data = list(timings)

        if notes is None:
            notes_data = list()
        else:
            notes_data = list(notes)

        self._timings: list[PhaseTiming] = timings_data
        self._notes: list[str] = notes_data

    @property
    def timings(self) -> list[PhaseTiming]:
        """Return the timing records.

        :return: Phase timing records.
        :rtype: list[PhaseTiming]
        """
        return self._timings

    @property
    def notes(self) -> list[str]:
        """Return the diagnostic notes.

        :return: Diagnostic notes.
        :rtype: list[str]
        """
        return self._notes

    def add_timing(self, timing: PhaseTiming) -> None:
        """Store one phase timing entry.

        :param timing: Phase timing entry.
        :type timing: PhaseTiming
        :return: None.
        :rtype: None
        """
        self._timings.append(timing)

    def add_note(self, note: str) -> None:
        """Store one diagnostic note.

        :param note: Diagnostic note text.
        :type note: str
        :return: None.
        :rtype: None
        """
        self._notes.append(note)


class LayoutPhaseState:
    """Typed shared state exchanged by the layout phases.

    :param components: Connected components of the original graph.
    :type components: list[list[str]] | None
    :param flat_edges: Flattened edge descriptors used by cycle breaking.
    :type flat_edges: list[FlatEdge] | None
    :param node_order: Deterministic node order from cycle breaking.
    :type node_order: list[str] | None
    :param reversed_edges: Identifiers of reversed edges.
    :type reversed_edges: set[str] | None
    :param feedback_edges: Identifiers of feedback edges.
    :type feedback_edges: set[str] | None
    :param dag_successors: DAG successor adjacency.
    :type dag_successors: dict[str, set[str]] | None
    :param dag_predecessors: DAG predecessor adjacency.
    :type dag_predecessors: dict[str, set[str]] | None
    :param oriented_edges: Oriented edge descriptors.
    :type oriented_edges: list[dict[str, str | bool | None]] | None
    :param skipped_edges: Identifiers of skipped edges.
    :type skipped_edges: set[str] | None
    :param topological_order: Topological node order.
    :type topological_order: list[str] | None
    :param layer_of: Layer index per node.
    :type layer_of: dict[str, int] | None
    :param long_edges: Identifiers of long edges.
    :type long_edges: list[str] | None
    :param expanded_nodes: Expanded-node lookup.
    :type expanded_nodes: dict[str, VirtualNode] | None
    :param expanded_layers: Expanded nodes grouped by layer.
    :type expanded_layers: dict[int, list[str]] | None
    :param expanded_edges: Expanded edge tuples.
    :type expanded_edges: list[tuple[str, str, str, int]] | None
    :param edge_paths: Expanded edge paths.
    :type edge_paths: dict[str, list[str]] | None
    :param ordered_layers: Ordered expanded layers.
    :type ordered_layers: dict[int, list[str]] | None
    :param expanded_successors: Expanded successor adjacency.
    :type expanded_successors: dict[str, set[str]] | None
    :param expanded_predecessors: Expanded predecessor adjacency.
    :type expanded_predecessors: dict[str, set[str]] | None
    :param order_in_layer: Position of nodes inside each layer.
    :type order_in_layer: dict[str, int] | None
    :param virtual_positions: Placed node coordinates.
    :type virtual_positions: dict[str, tuple[float, float]] | None
    :param layer_x: Primary-axis coordinate per layer.
    :type layer_x: dict[int, float] | None
    :param y_of_node: Orthogonal coordinate per node.
    :type y_of_node: dict[str, float] | None
    """

    __slots__ = (
        "_components",
        "_flat_edges",
        "_node_order",
        "_reversed_edges",
        "_feedback_edges",
        "_dag_successors",
        "_dag_predecessors",
        "_oriented_edges",
        "_skipped_edges",
        "_topological_order",
        "_layer_of",
        "_long_edges",
        "_expanded_nodes",
        "_expanded_layers",
        "_expanded_edges",
        "_edge_paths",
        "_ordered_layers",
        "_expanded_successors",
        "_expanded_predecessors",
        "_order_in_layer",
        "_virtual_positions",
        "_layer_x",
        "_y_of_node",
    )

    def __init__(
        self,
        components: list[list[str]] | None = None,
        flat_edges: list["FlatEdge"] | None = None,
        node_order: list[str] | None = None,
        reversed_edges: set[str] | None = None,
        feedback_edges: set[str] | None = None,
        dag_successors: dict[str, set[str]] | None = None,
        dag_predecessors: dict[str, set[str]] | None = None,
        oriented_edges: list[dict[str, str | bool | None]] | None = None,
        skipped_edges: set[str] | None = None,
        topological_order: list[str] | None = None,
        layer_of: dict[str, int] | None = None,
        long_edges: list[str] | None = None,
        expanded_nodes: dict[str, "VirtualNode"] | None = None,
        expanded_layers: dict[int, list[str]] | None = None,
        expanded_edges: list[tuple[str, str, str, int]] | None = None,
        edge_paths: dict[str, list[str]] | None = None,
        ordered_layers: dict[int, list[str]] | None = None,
        expanded_successors: dict[str, set[str]] | None = None,
        expanded_predecessors: dict[str, set[str]] | None = None,
        order_in_layer: dict[str, int] | None = None,
        virtual_positions: dict[str, tuple[float, float]] | None = None,
        layer_x: dict[int, float] | None = None,
        y_of_node: dict[str, float] | None = None,
    ) -> None:
        self._components: list[list[str]] = list() if components is None else list(components)
        self._flat_edges: list["FlatEdge"] = list() if flat_edges is None else list(flat_edges)
        self._node_order: list[str] = list() if node_order is None else list(node_order)
        self._reversed_edges: set[str] = set() if reversed_edges is None else set(reversed_edges)
        self._feedback_edges: set[str] = set() if feedback_edges is None else set(feedback_edges)
        self._dag_successors: dict[str, set[str]] = dict() if dag_successors is None else dict(dag_successors)
        self._dag_predecessors: dict[str, set[str]] = dict() if dag_predecessors is None else dict(dag_predecessors)
        self._oriented_edges: list[dict[str, str | bool | None]] = list() if oriented_edges is None else list(oriented_edges)
        self._skipped_edges: set[str] = set() if skipped_edges is None else set(skipped_edges)
        self._topological_order: list[str] = list() if topological_order is None else list(topological_order)
        self._layer_of: dict[str, int] = dict() if layer_of is None else dict(layer_of)
        self._long_edges: list[str] = list() if long_edges is None else list(long_edges)
        self._expanded_nodes: dict[str, "VirtualNode"] = dict() if expanded_nodes is None else dict(expanded_nodes)
        self._expanded_layers: dict[int, list[str]] = dict() if expanded_layers is None else dict(expanded_layers)
        self._expanded_edges: list[tuple[str, str, str, int]] = list() if expanded_edges is None else list(expanded_edges)
        self._edge_paths: dict[str, list[str]] = dict() if edge_paths is None else dict(edge_paths)
        self._ordered_layers: dict[int, list[str]] = dict() if ordered_layers is None else dict(ordered_layers)
        self._expanded_successors: dict[str, set[str]] = dict() if expanded_successors is None else dict(expanded_successors)
        self._expanded_predecessors: dict[str, set[str]] = dict() if expanded_predecessors is None else dict(expanded_predecessors)
        self._order_in_layer: dict[str, int] = dict() if order_in_layer is None else dict(order_in_layer)
        self._virtual_positions: dict[str, tuple[float, float]] = dict() if virtual_positions is None else dict(virtual_positions)
        self._layer_x: dict[int, float] = dict() if layer_x is None else dict(layer_x)
        self._y_of_node: dict[str, float] = dict() if y_of_node is None else dict(y_of_node)

    @property
    def components(self) -> list[list[str]]:
        """Return the connected components.

        :returns: Connected components.
        """
        return self._components

    @property
    def flat_edges(self) -> list["FlatEdge"]:
        """Return the flattened edges.

        :returns: Flattened edges.
        """
        return self._flat_edges

    @property
    def node_order(self) -> list[str]:
        """Return the deterministic node order.

        :returns: Node order.
        """
        return self._node_order

    @property
    def reversed_edges(self) -> set[str]:
        """Return the reversed edge identifiers.

        :returns: Reversed edge identifiers.
        """
        return self._reversed_edges

    @property
    def feedback_edges(self) -> set[str]:
        """Return the feedback edge identifiers.

        :returns: Feedback edge identifiers.
        """
        return self._feedback_edges

    @property
    def dag_successors(self) -> dict[str, set[str]]:
        """Return the DAG successor adjacency.

        :returns: DAG successor adjacency.
        """
        return self._dag_successors

    @property
    def dag_predecessors(self) -> dict[str, set[str]]:
        """Return the DAG predecessor adjacency.

        :returns: DAG predecessor adjacency.
        """
        return self._dag_predecessors

    @property
    def oriented_edges(self) -> list[dict[str, str | bool | None]]:
        """Return the oriented edges.

        :returns: Oriented edges.
        """
        return self._oriented_edges

    @property
    def skipped_edges(self) -> set[str]:
        """Return the skipped edge identifiers.

        :returns: Skipped edge identifiers.
        """
        return self._skipped_edges

    @property
    def topological_order(self) -> list[str]:
        """Return the topological order.

        :returns: Topological order.
        """
        return self._topological_order

    @property
    def layer_of(self) -> dict[str, int]:
        """Return the layer mapping.

        :returns: Layer mapping.
        """
        return self._layer_of

    @property
    def long_edges(self) -> list[str]:
        """Return the long-edge identifiers.

        :returns: Long-edge identifiers.
        """
        return self._long_edges

    @property
    def expanded_nodes(self) -> dict[str, "VirtualNode"]:
        """Return the expanded-node lookup.

        :returns: Expanded-node lookup.
        """
        return self._expanded_nodes

    @property
    def expanded_layers(self) -> dict[int, list[str]]:
        """Return the expanded layers.

        :returns: Expanded layers.
        """
        return self._expanded_layers

    @property
    def expanded_edges(self) -> list[tuple[str, str, str, int]]:
        """Return the expanded edges.

        :returns: Expanded edges.
        """
        return self._expanded_edges

    @property
    def edge_paths(self) -> dict[str, list[str]]:
        """Return the expanded edge paths.

        :returns: Expanded edge paths.
        """
        return self._edge_paths

    @property
    def ordered_layers(self) -> dict[int, list[str]]:
        """Return the ordered layers.

        :returns: Ordered layers.
        """
        return self._ordered_layers

    @property
    def expanded_successors(self) -> dict[str, set[str]]:
        """Return the expanded successor adjacency.

        :returns: Expanded successor adjacency.
        """
        return self._expanded_successors

    @property
    def expanded_predecessors(self) -> dict[str, set[str]]:
        """Return the expanded predecessor adjacency.

        :returns: Expanded predecessor adjacency.
        """
        return self._expanded_predecessors

    @property
    def order_in_layer(self) -> dict[str, int]:
        """Return the in-layer order.

        :returns: In-layer order.
        """
        return self._order_in_layer

    @property
    def virtual_positions(self) -> dict[str, tuple[float, float]]:
        """Return the virtual positions.

        :returns: Virtual positions.
        """
        return self._virtual_positions

    @property
    def layer_x(self) -> dict[int, float]:
        """Return the primary-axis layer coordinates.

        :returns: Primary-axis layer coordinates.
        """
        return self._layer_x

    @property
    def y_of_node(self) -> dict[str, float]:
        """Return the orthogonal node coordinates.

        :returns: Orthogonal node coordinates.
        """
        return self._y_of_node


class LayoutContext:
    """Shared mutable pipeline context.

    :param graph: Graph being laid out.
    :type graph: SugiyamaGraph
    :param option_resolver: Option resolver used by the phases.
    :type option_resolver: SugiyamaOptionResolver
    :param report: Optional pipeline report.
    :type report: PipelineReport | None
    :param phase_state: Optional shared phase state storage.
    :type phase_state: LayoutPhaseState | None
    """

    __slots__ = ("_graph", "_option_resolver", "_report", "_phase_state")

    def __init__(
            self,
            graph: SugiyamaGraph,
            option_resolver: SugiyamaOptionResolver,
            report: PipelineReport | None = None,
            phase_state: LayoutPhaseState | None = None,
    ) -> None:
        report_data: PipelineReport
        phase_state_data: LayoutPhaseState

        if report is None:
            report_data = PipelineReport()
        else:
            report_data = report

        if phase_state is None:
            phase_state_data = LayoutPhaseState()
        else:
            phase_state_data = phase_state

        self._graph: SugiyamaGraph = graph
        self._option_resolver: SugiyamaOptionResolver = option_resolver
        self._report: PipelineReport = report_data
        self._phase_state: LayoutPhaseState = phase_state_data

    @property
    def graph(self) -> SugiyamaGraph:
        """Return the graph under layout.

        :return: Graph under layout.
        :rtype: SugiyamaGraph
        """
        return self._graph

    @property
    def option_resolver(self) -> SugiyamaOptionResolver:
        """Return the option resolver.

        :return: Option resolver.
        :rtype: SugiyamaOptionResolver
        """
        return self._option_resolver

    @property
    def report(self) -> PipelineReport:
        """Return the pipeline report.

        :return: Pipeline report.
        :rtype: PipelineReport
        """
        return self._report

    @property
    def phase_state(self) -> LayoutPhaseState:
        """Return the shared phase state storage.

        :return: Shared phase state storage.
        :rtype: LayoutPhaseState
        """
        return self._phase_state


class LayoutPhaseBase:
    """Base class for layered layout phases."""

    __slots__ = ()

    name: str = ""

    def run(self, context: LayoutContext) -> None:
        """Execute the phase.

        :param context: Shared pipeline context.
        :type context: LayoutContext
        :return: None.
        :rtype: None
        """
        raise NotImplementedError("Layout phases must implement run().")


class LayoutPipeline:
    """Ordered collection of layout phases.

    :param phases: Pipeline phase instances.
    :type phases: list[LayoutPhaseBase]
    """

    __slots__ = ("_phases",)

    def __init__(self, phases: list[LayoutPhaseBase]) -> None:
        self._phases: list[LayoutPhaseBase] = list(phases)

    @property
    def phases(self) -> list[LayoutPhaseBase]:
        """Return the pipeline phases.

        :return: Pipeline phases.
        :rtype: list[LayoutPhaseBase]
        """
        return self._phases

    def run(self, context: LayoutContext) -> PipelineReport:
        """Execute all phases in sequence.

        The pipeline records each phase timing immediately after the phase
        completes so failures can be correlated with the already executed
        portion of the algorithm.

        :param context: Shared pipeline context.
        :type context: LayoutContext
        :return: Pipeline report.
        :rtype: PipelineReport
        """
        phase: LayoutPhaseBase

        for phase in self._phases:
            start_seconds: float = perf_counter()
            phase.run(context)
            elapsed_seconds: float = perf_counter() - start_seconds
            context.report.add_timing(PhaseTiming(name=phase.name, seconds=elapsed_seconds))

        return context.report
