# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Top-level engine entry point for the Sugiyama layered package."""

from __future__ import annotations

from VeraGridEngine.Utils.SugiyamaLayered.model import SugiyamaGraph
from VeraGridEngine.Utils.SugiyamaLayered.options import SugiyamaOptionResolver
from VeraGridEngine.Utils.SugiyamaLayered.Phases.components import ConnectedComponentsPhase
from VeraGridEngine.Utils.SugiyamaLayered.Phases.crossing_minimization import CrossingMinimizationPhase
from VeraGridEngine.Utils.SugiyamaLayered.Phases.cycle_breaking import CycleBreakingPhase
from VeraGridEngine.Utils.SugiyamaLayered.Phases.edge_routing import EdgeRoutingPhase
from VeraGridEngine.Utils.SugiyamaLayered.Phases.labels import LabelPlacementPhase
from VeraGridEngine.Utils.SugiyamaLayered.Phases.layering import LayeringPhase
from VeraGridEngine.Utils.SugiyamaLayered.Phases.long_edges import LongEdgePhase
from VeraGridEngine.Utils.SugiyamaLayered.Phases.node_placement import NodePlacementPhase
from VeraGridEngine.Utils.SugiyamaLayered.pipeline import LayoutContext, LayoutPipeline, PipelineReport


class EngineResult:
    """Result container returned by the Sugiyama engine.

    :param graph: Laid out graph.
    :type graph: SugiyamaGraph
    :param report: Pipeline execution report.
    :type report: PipelineReport
    """

    __slots__ = ("_graph", "_report")

    def __init__(self, graph: SugiyamaGraph, report: PipelineReport) -> None:
        self._graph: SugiyamaGraph = graph
        self._report: PipelineReport = report

    @property
    def graph(self) -> SugiyamaGraph:
        """Return the laid out graph.

        :return: Laid out graph.
        :rtype: SugiyamaGraph
        """
        return self._graph

    @property
    def report(self) -> PipelineReport:
        """Return the pipeline report.

        :return: Pipeline report.
        :rtype: PipelineReport
        """
        return self._report


class SugiyamaLayeredPythonEngine:
    """Python-native Sugiyama layered layout engine."""

    __slots__ = ("_option_resolver", "_pipeline")

    def __init__(self, option_resolver: SugiyamaOptionResolver | None = None) -> None:
        """Create the layered layout engine.

        :param option_resolver: Optional option resolver override.
        :type option_resolver: SugiyamaOptionResolver | None
        :return: None.
        :rtype: None
        """
        resolver: SugiyamaOptionResolver

        if option_resolver is None:
            resolver = SugiyamaOptionResolver()
        else:
            resolver = option_resolver

        self._option_resolver: SugiyamaOptionResolver = resolver
        self._pipeline: LayoutPipeline = LayoutPipeline(
            phases=[
                ConnectedComponentsPhase(),
                CycleBreakingPhase(),
                LayeringPhase(),
                LongEdgePhase(),
                CrossingMinimizationPhase(),
                NodePlacementPhase(),
                EdgeRoutingPhase(),
                LabelPlacementPhase(),
            ]
        )

    @property
    def option_resolver(self) -> SugiyamaOptionResolver:
        """Return the engine option resolver.

        :return: Option resolver.
        :rtype: SugiyamaOptionResolver
        """
        return self._option_resolver

    @property
    def pipeline(self) -> LayoutPipeline:
        """Return the configured layout pipeline.

        :return: Layout pipeline.
        :rtype: LayoutPipeline
        """
        return self._pipeline

    def compute(self, graph: SugiyamaGraph) -> EngineResult:
        """Run the layered layout pipeline on one graph.

        :param graph: Input graph.
        :type graph: SugiyamaGraph
        :return: Engine result with graph and report.
        :rtype: EngineResult
        """
        context: LayoutContext = LayoutContext(graph=graph, option_resolver=self._option_resolver)
        report: PipelineReport = self._pipeline.run(context)
        result: EngineResult = EngineResult(graph=graph, report=report)
        return result
