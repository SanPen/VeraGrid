# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np
import networkx as nx
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import Normalizer

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.LinearFactors.linear_analysis_driver import LinearAnalysisResults
from VeraGridEngine.enumerations import SimulationTypes
from VeraGridEngine.Simulations.driver_template import DriverTemplate
from VeraGridEngine.Simulations.Topology.node_groups_results import NodeGroupsResults


class NodeGroupsDriver(DriverTemplate):
    """
    NodeGroupsDriver
    """
    __slots__ = (
        "sigmas",
        "min_group_size",
        "use_ptdf",
        "ptdf_results",
    )

    name = 'Node groups'
    tpe = SimulationTypes.NodeGrouping_run

    def __init__(
            self,
            grid: MultiCircuit,
            sigmas: float,
            min_group_size: int,
            ptdf_results: LinearAnalysisResults) -> None:
        """
        Build the node grouping driver.

        :param grid: MultiCircuit instance to analyse.
        :param sigmas: Clustering distance threshold.
        :param min_group_size: Minimum number of elements required in a group.
        :param ptdf_results: Linear analysis results used to build the feature
            matrix when PTDF-based grouping is enabled.
        """
        DriverTemplate.__init__(self, grid=grid)

        self.grid = grid

        self.sigmas = sigmas

        self.min_group_size = min_group_size

        n: int = len(grid.buses)

        self.use_ptdf = True

        self.ptdf_results = ptdf_results

        # The result object is allocated during construction so the driver uses
        # the same persistence and session interfaces as the other studies.
        self.results: NodeGroupsResults = NodeGroupsResults(n=n)


    def build_weighted_graph(self) -> nx.Graph:
        """
        Build the topology graph used by the Dijkstra-based distance mode.

        :return: Weighted graph whose nodes are bus indices.
        """
        graph: nx.Graph = nx.Graph()

        # The bus to index map is created explicitly because the branch
        # traversal works with bus objects while the graph works with indices.
        bus_dictionary: dict = dict()
        for bus_index, bus in enumerate(self.grid.get_buses()):
            bus_dictionary[bus] = bus_index

        for branch_list in self.grid.get_branch_lists(add_vsc=True, add_hvdc=True, add_switch=True):
            for branch in branch_list:
                # if branch.active:
                from_bus_index: int = bus_dictionary[branch.bus_from]
                to_bus_index: int = bus_dictionary[branch.bus_to]
                weight: float = branch.get_weight()
                graph.add_edge(from_bus_index, to_bus_index, weight=weight)

        return graph

    def run(self) -> None:
        """
        Execute the node grouping study.

        :return: ``None``.
        """
        self.tic()
        self.report_progress(0.0)

        n: int = self.grid.get_bus_number()
        results: NodeGroupsResults = self.results

        if self.use_ptdf:
            self.report_text('Analyzing PTDF...')

            # The PTDF matrix is normalized before clustering so the DBSCAN
            # distance threshold is applied on a comparable feature scale.
            normalized_training_matrix: np.ndarray = Normalizer().fit_transform(self.ptdf_results.PTDF.T)
            results.set_training_matrix(normalized_training_matrix)

            metric: str = 'euclidean'
        else:
            self.report_text('Exploring Dijkstra distances...')
            # The weighted grid graph is explored to obtain the pairwise bus
            # distances that will act as a precomputed clustering metric.
            graph: nx.Graph = self.build_weighted_graph()
            iteration_index: int = 0
            for source_bus_index, distances_dict in nx.all_pairs_dijkstra_path_length(graph):
                for target_bus_index, distance in distances_dict.items():
                    results.X_train[source_bus_index, target_bus_index] = distance

                self.report_progress2(iteration_index, n)
                iteration_index += 1
            metric = 'precomputed'

        # The global distance spread is preserved because callers may use it to
        # understand how aggressive the grouping threshold was.
        results.set_sigma(float(np.std(results.get_training_matrix())))
        max_distance: float = self.sigmas

        # The clustering stage transforms the distance representation into
        # explicit group assignments for each bus.
        self.report_text('Building groups with DBSCAN...')

        model: DBSCAN = DBSCAN(eps=max_distance,
                               min_samples=self.min_group_size,
                               metric=metric)

        db: DBSCAN = model.fit(results.get_training_matrix())

        # Noise labels are discarded because the GUI only colours buses that
        # belong to actual clusters.
        labels: list[int] = list({label for label in db.labels_ if label > -1})
        groups_by_name: list[list[str]] = list()
        groups_by_index: list[list[int]] = list()
        for _ in labels:
            groups_by_name.append(list())
            groups_by_index.append(list())

        # Each bus is placed in the cluster bucket that matches the DBSCAN
        # label so the names and indices stay aligned for downstream consumers.
        for i, (bus, group_idx) in enumerate(zip(self.grid.buses, db.labels_)):
            if group_idx > -1:
                groups_by_name[group_idx].append(bus.name)
                groups_by_index[group_idx].append(i)
            else:
                pass

        results.set_groups(groups_by_name=groups_by_name, groups_by_index=groups_by_index)

        # The driver finishes only after the results object contains the final
        # group assignments used by the session and GUI layers.
        self.report_done()
        self.toc()
