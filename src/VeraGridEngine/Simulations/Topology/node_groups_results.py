# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np

from VeraGridEngine.Simulations.results_template import ResultsTemplate, ResultsProperty
from VeraGridEngine.basic_structures import Mat
from VeraGridEngine.enumerations import ResultTypes, StudyResultsType


class NodeGroupsResults(ResultsTemplate):
    """
    Store the reusable data produced by the node grouping simulation.
    """

    LOCAL_RESULTS_DECLARATIONS = (
        ResultsProperty(name="X_train", tpe=Mat, old_names=list()),
        ResultsProperty(name="sigma", tpe=float, old_names=list()),
        ResultsProperty(name="groups_by_name", tpe=list, old_names=list()),
        ResultsProperty(name="groups_by_index", tpe=list, old_names=list()),
    )

    __slots__ = (
        "X_train",
        "sigma",
        "groups_by_name",
        "groups_by_index",
    )

    def __init__(self, n: int) -> None:
        """
        Build the node groups results container.

        :param n: Number of buses in the analysed grid.
        """
        available_results: list[ResultTypes] = list()

        ResultsTemplate.__init__(
            self,
            name="Node groups",
            available_results=available_results,
            time_array=None,
            clustering_results=None,
            study_results_type=StudyResultsType.NodeGroups,
        )

        # The training matrix is allocated once because the algorithm knows
        # its final dimensions before the clustering stage starts.
        self.X_train: Mat = np.zeros((n, n), dtype=float)

        # The distance dispersion is stored explicitly because the caller may
        # need it after the clustering algorithm has finished.
        self.sigma: float = 1.0

        # Group memberships are tracked both by the bus name and by the bus
        # index so that the GUI and persistence layers can reuse the same data.
        self.groups_by_name: list[list[str]] = list()
        self.groups_by_index: list[list[int]] = list()


    def set_training_matrix(self, training_matrix: Mat) -> None:
        """
        Store the matrix used by the clustering algorithm.

        :param training_matrix: Training matrix prepared for DBSCAN.
        """
        self.X_train = training_matrix

    def get_training_matrix(self) -> Mat:
        """
        Get the matrix used by the clustering algorithm.

        :return: Training matrix prepared for DBSCAN.
        """
        return self.X_train

    def set_sigma(self, sigma: float) -> None:
        """
        Store the characteristic distance scale of the training matrix.

        :param sigma: Standard deviation of the training matrix.
        """
        self.sigma = sigma

    def get_sigma(self) -> float:
        """
        Get the characteristic distance scale of the training matrix.

        :return: Standard deviation of the training matrix.
        """
        return self.sigma

    def set_groups(self, groups_by_name: list[list[str]], groups_by_index: list[list[int]]) -> None:
        """
        Store the resulting bus group assignments.

        :param groups_by_name: Bus groups represented by bus names.
        :param groups_by_index: Bus groups represented by bus indices.
        """
        self.groups_by_name = groups_by_name
        self.groups_by_index = groups_by_index

    def get_groups_by_name(self) -> list[list[str]]:
        """
        Get the bus groups represented by bus names.

        :return: Bus groups represented by bus names.
        """
        return self.groups_by_name

    def get_groups_by_index(self) -> list[list[int]]:
        """
        Get the bus groups represented by bus indices.

        :return: Bus groups represented by bus indices.
        """
        return self.groups_by_index

    def mdl(self, result_type: ResultTypes | None = None) -> None:
        """
        Build a tabular representation of the stored results.

        :param result_type: Unused result type placeholder kept for API
            compatibility with the rest of the simulations package.
        :return: ``None`` because no table view is defined for this study yet.
        """
        return None
