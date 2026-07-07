# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os

import numpy as np

import VeraGridEngine.api as gce


def test_node_groups_driver_populates_results() -> None:
    """
    Verify that the node grouping driver stores its study data in a
    NodeGroupsResults object.

    :return: ``None``.
    """
    tests_root: str = os.path.dirname(os.path.dirname(__file__))
    grid_file_name: str = os.path.join(tests_root, "data", "grids", "IEEE14_types_test.gridcal")

    # The grid is loaded from the test fixtures so the study runs on a stable
    # topology that is already used across the test suite.
    grid: gce.MultiCircuit = gce.open_file(grid_file_name)

    # The node grouping study consumes PTDF data, so the linear analysis must
    # be executed first to provide the feature matrix input.
    linear_analysis_driver: gce.LinearAnalysisDriver = gce.LinearAnalysisDriver(grid=grid)
    linear_analysis_driver.run()

    # The node grouping driver is the subject under test and should leave all
    # of its reusable data inside the results object after execution.
    node_groups_driver: gce.NodeGroupsDriver = gce.NodeGroupsDriver(
        grid=grid,
        sigmas=0.5,
        min_group_size=2,
        ptdf_results=linear_analysis_driver.results,
    )
    node_groups_driver.run()

    results: gce.NodeGroupsResults | None = node_groups_driver.results

    assert results is not None
    assert results.X_train.shape == linear_analysis_driver.results.PTDF.T.shape
    assert isinstance(results.groups_by_name, list)
    assert isinstance(results.groups_by_index, list)
    assert np.isfinite(results.sigma)
