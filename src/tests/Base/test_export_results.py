# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import zipfile

import numpy as np

import VeraGridEngine.api as gce
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Simulations.results_template import ResultsTemplate
from VeraGridEngine.Simulations.EMT.emt_results import EmtResults
from VeraGridEngine.Simulations.Rms.rms_results import RmsResults
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import DeviceType, ResultTypes, StudyResultsType


class _FakeGenericResults(ResultsTemplate):
    """
    Minimal generic results object used to test archive filename sanitization.

    The generic export path builds one filename from ``results.name`` and the
    selected ``ResultTypes`` label. This light test double exposes exactly one
    result so the exporter can be exercised without running any simulation.
    """

    __slots__ = ("_table",)

    def __init__(self) -> None:
        """
        Build one fake generic results object with a colon-bearing result label.

        :return: None.
        """
        ResultsTemplate.__init__(self,
                                 name="Power flow",
                                 available_results=[ResultTypes.BranchActivePowerTo],
                                 time_array=None,
                                 clustering_results=None,
                                 study_results_type=StudyResultsType.PowerFlow)

        # The table payload is intentionally tiny because this test validates
        # only the generated archive member name, not numerical correctness.
        self._table: ResultsTable = ResultsTable(data=np.array([[1.0]], dtype=float),
                                                 columns=np.array(["value"], dtype=str),
                                                 index=np.array(["row-1"], dtype=str),
                                                 title="fake result",
                                                 units="MW",
                                                 idx_device_type=DeviceType.NoDevice,
                                                 cols_device_type=DeviceType.NoDevice)

    def mdl(self, result_type: ResultTypes) -> ResultsTable | None:
        """
        Return the single fake table requested by the generic export path.

        :param result_type: Requested generic result type.
        :return: Fake results table when the requested type matches, else ``None``.
        """
        if result_type == ResultTypes.BranchActivePowerTo:
            return self._table
        else:
            return None


def _build_minimal_rms_results() -> RmsResults:
    """
    Build one minimal RMS results object for archive export tests.

    :return: Minimal RMS results object.
    """
    variable: Var = Var(name="omega", uid=101)
    results: RmsResults = RmsResults(
        time_array=np.array([0.0, 1.0], dtype=float),
        rms_events_group_names=np.array(["RMS Group A", "RMS Group B"], dtype=str),
        rms_events_group_idtags=np.array(["rms-group-a", "rms-group-b"], dtype=str),
        variables=[variable],
        uid2idx={variable.uid: 0},
        vars_glob_name2uid={"device-a:omega:101": variable.uid},
        devices_vars_info=dict(),
        has_event_group_results=np.array([True, False], dtype=bool),
    )

    # Populate only the active event-group payload because the exporter must
    # write simulated groups and skip declared groups with no runtime data.
    results.values[:, :, 0] = np.array([[0.0], [1.0]], dtype=float)

    return results


def _build_minimal_emt_results() -> EmtResults:
    """
    Build one minimal EMT results object for archive export tests.

    :return: Minimal EMT results object.
    """
    variable: Var = Var(name="Vm", uid=201)
    diff_variable: Var = Var(name="domega", uid=202)
    results: EmtResults = EmtResults(
        time_array=np.array([0.0, 1.0], dtype=float),
        emt_events_group_names=np.array(["EMT Group A", "EMT Group B"], dtype=str),
        emt_events_group_idtags=np.array(["emt-group-a", "emt-group-b"], dtype=str),
        variables=[variable],
        diff_variables=[diff_variable],
        uid2idx_vars={variable.uid: 0},
        uid2idx_diff={diff_variable.uid: 0},
        vars_glob_name2uid={"device-a:Vm:201": variable.uid,
                            "device-a:domega:202": diff_variable.uid},
        devices_vars_info=dict(),
        has_event_group_results=np.array([True, False], dtype=bool),
    )

    # Populate both EMT payload namespaces for the active event group because
    # the exporter must emit one CSV for values and one for diff values.
    results.values[:, :, 0] = np.array([[1.0], [2.0]], dtype=float)
    results.diff_values[:, :, 0] = np.array([[3.0], [4.0]], dtype=float)

    return results


def test_export_results():
    """
    Test that the results export works
    :return:
    """
    fname = os.path.join("data", "grids", "IEEE39_1W.gridcal")

    grid = gce.open_file(fname)

    # create the driver
    pf_driver = gce.PowerFlowTimeSeriesDriver(grid=grid,
                                              options=gce.PowerFlowOptions(),
                                              time_indices=grid.get_all_time_indices())
    # run
    pf_driver.run()

    power_flow_options = gce.PowerFlowOptions(gce.SolverType.NR,
                                              verbose=0,
                                              control_q=False,
                                              retry_with_other_methods=False)

    opf_options = gce.OptimalPowerFlowOptions(verbose=0,
                                              solver=gce.SolverType.LINEAR_OPF,
                                              power_flow_options=power_flow_options,
                                              time_grouping=gce.TimeGrouping.Daily,
                                              mip_solver=gce.MIPSolvers.HIGHS,
                                              generate_report=True)

    # run the opf time series
    opf_ts_driver = gce.OptimalPowerFlowTimeSeriesDriver(grid=grid,
                                                         options=opf_options,
                                                         time_indices=grid.get_all_time_indices())
    opf_ts_driver.run()

    if not os.path.exists(os.path.join("data", "output")):
        os.makedirs(os.path.join("data", "output"))

    export_fame = os.path.join("data", "output", "IEEE39_1W_results.zip")
    gce.export_drivers(drivers_list=[pf_driver, opf_ts_driver], file_name=export_fame)

    os.remove(export_fame)


def test_export_results_rms_dynamic_layout(tmp_path) -> None:
    """
    Verify that RMS dynamic export writes one CSV per active event group.

    :param tmp_path: Temporary directory provided by pytest.
    :return: None.
    """
    results: RmsResults = _build_minimal_rms_results()
    export_file_name: str = os.path.join(str(tmp_path), "rms_results.zip")

    # Export the synthetic RMS results so the archive layout can be validated
    # independently from any heavier simulation pipeline.
    gce.export_results(results_list=[results], file_name=export_file_name)

    with zipfile.ZipFile(export_file_name, "r") as zip_file:
        archive_names: list[str] = sorted(zip_file.namelist())

        # Only the active event group must be present because inactive groups
        # are declared metadata placeholders rather than runtime results.
        assert archive_names == ["RMS simulation/000_RMS Group A.csv"]


def test_export_results_emt_dynamic_layout(tmp_path) -> None:
    """
    Verify that EMT dynamic export writes values and diff-values CSV files in one folder.

    :param tmp_path: Temporary directory provided by pytest.
    :return: None.
    """
    results: EmtResults = _build_minimal_emt_results()
    export_file_name: str = os.path.join(str(tmp_path), "emt_results.zip")

    # Export the synthetic EMT results so the archive layout can be validated
    # independently from any heavier simulation pipeline.
    gce.export_results(results_list=[results], file_name=export_file_name)

    with zipfile.ZipFile(export_file_name, "r") as zip_file:
        archive_names: list[str] = sorted(zip_file.namelist())

        # Both EMT payload namespaces must coexist in the same folder, while
        # inactive event groups must still be skipped.
        assert archive_names == [
            "EMT simulation/000_EMT Group A.csv",
            "EMT simulation/000_EMT Group A_diff_values.csv",
        ]


def test_export_results_generic_names_are_windows_safe(tmp_path) -> None:
    """
    Verify that generic exported result names are sanitized for Windows extraction.

    :param tmp_path: Temporary directory provided by pytest.
    :return: None.
    """
    results: _FakeGenericResults = _FakeGenericResults()
    export_file_name: str = os.path.join(str(tmp_path), "generic_results.zip")

    # Export one generic results table whose enum label contains ``:`` because
    # Windows extraction rejects those characters inside file names.
    gce.export_results(results_list=[results], file_name=export_file_name)

    with zipfile.ZipFile(export_file_name, "r") as zip_file:
        archive_names: list[str] = sorted(zip_file.namelist())

        # The generated name must keep the historical wording while replacing
        # reserved Windows filename characters with safe separators.
        assert archive_names == ["Power flow Pt Active power to.csv"]
