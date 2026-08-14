# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Compilers.Gslv.activation import (
    contingency_method_dict,
    pg,
)
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import IntVec
from typing import TYPE_CHECKING, Union
from VeraGridEngine.Compilers.Gslv.conversion import to_gslv
from VeraGridEngine.Compilers.Gslv.Simulations.power_flow import get_gslv_pf_options

if TYPE_CHECKING:
    from VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_options import ContingencyAnalysisOptions
    from VeraGridEngine.Simulations.OPF.opf_results import OptimalPowerFlowResults


def gslv_contingencies_snapshot(
        circuit: MultiCircuit,
        con_opt: ContingencyAnalysisOptions,
        opf_results: Union[None, OptimalPowerFlowResults] = None,
) -> "pg.ContingencyResultsSnapshot":
    """
    GSLV power flow
    :param circuit: MultiCircuit instance
    :param con_opt: ContingencyAnalysisOptions
    :param opf_results: OptimalPowerFlowResults (optional)
    :return: GSLV Power flow results object
    """
    override_branch_controls = not (con_opt.pf_options.control_taps_modules and con_opt.pf_options.control_taps_phase)

    gslv_grid, _ = to_gslv(circuit,
                           use_time_series=False,
                           time_indices=None,
                           override_branch_controls=override_branch_controls,
                           opf_results=opf_results)

    con_opt_gslv = pg.ContingencyAnalysisOptions(
        pf_options=get_gslv_pf_options(con_opt.pf_options),
        lin_options=pg.LinearAnalysisOptions(
            distributeSlack=con_opt.lin_options.distribute_slack,
            correctValues=con_opt.lin_options.correct_values,
            ptdfThreshold=con_opt.lin_options.ptdf_threshold,
            lodfThreshold=con_opt.lin_options.lodf_threshold,
        ),
        use_srap=con_opt.use_srap,
        srap_max_power=con_opt.srap_max_power,
        srap_top_n=con_opt.srap_top_n,
        srap_dead_band=con_opt.srap_deadband,
        srap_rever_to_nominal_rating=con_opt.srap_revert_to_nominal_rating,
        detailed_massive_report=con_opt.detailed_massive_report,
        contingency_dead_band=con_opt.contingency_deadband,
        contingency_method=contingency_method_dict[con_opt.contingency_method],
    )

    n_threads = 0  # max threads

    logger = pg.Logger()

    res = pg.run_contingencies_at(grid=gslv_grid,
                                  options=con_opt_gslv,
                                  n_threads=n_threads,
                                  t_idx=0,
                                  # logger=logger
                                  )

    return res


def gslv_contingencies_ts(circuit: MultiCircuit,
                          con_opt: ContingencyAnalysisOptions,
                          time_series: bool = False,
                          time_indices: Union[IntVec, None] = None) -> "pg.ContingencyAnalysisResults":
    """
    GSLV power flow
    :param circuit: MultiCircuit instance
    :param con_opt: ContingencyAnalysisOptions
    :param time_series: Compile with VeraGrid time series?
    :param time_indices: Array of time indices
    :return: GSLV Power flow results object
    """
    override_branch_controls = not (con_opt.pf_options.control_taps_modules and con_opt.pf_options.control_taps_phase)

    gslv_grid, _ = to_gslv(circuit,
                           use_time_series=time_series,
                           time_indices=None,
                           override_branch_controls=override_branch_controls,
                           opf_results=None)

    con_opt_gslv = pg.ContingencyAnalysisOptions(
        pf_options=get_gslv_pf_options(con_opt.pf_options),
        lin_options=pg.LinearAnalysisOptions(
            distributeSlack=con_opt.lin_options.distribute_slack,
            correctValues=con_opt.lin_options.correct_values,
            ptdfThreshold=con_opt.lin_options.ptdf_threshold,
            lodfThreshold=con_opt.lin_options.lodf_threshold,
        ),
        use_srap=con_opt.use_srap,
        srap_max_power=con_opt.srap_max_power,
        srap_top_n=con_opt.srap_top_n,
        srap_dead_band=con_opt.srap_deadband,
        srap_rever_to_nominal_rating=con_opt.srap_revert_to_nominal_rating,
        detailed_massive_report=con_opt.detailed_massive_report,
        contingency_dead_band=con_opt.contingency_deadband,
        contingency_method=contingency_method_dict[con_opt.contingency_method],
    )

    if time_series:
        # it is already sliced to the relevant time indices
        if time_indices is None:
            time_indices = [i for i in range(circuit.get_time_number())]
        else:
            time_indices = list(time_indices)
        n_threads = 0  # max threads
    else:
        time_indices = [0]
        n_threads = 1

    logger = pg.Logger()

    res = pg.run_contingencies(grid=gslv_grid,
                               options=con_opt_gslv,
                               n_threads=n_threads,
                               time_indices=time_indices,
                               logger=logger)

    return res
