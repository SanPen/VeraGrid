# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING, Union, Callable, List
import numpy as np

from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_results import ContingencyAnalysisResults
from VeraGridEngine.Simulations.PowerFlow.power_flow_worker import multi_island_pf_nc
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions, SolverType
from VeraGridEngine.Simulations.LinearFactors.linear_analysis import LinearAnalysis, LinearMultiContingencies
from VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_options import ContingencyAnalysisOptions
from VeraGridEngine.basic_structures import Logger, CxVec, IntVec, StrVec, Mat, Vec

if TYPE_CHECKING:
    from VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_driver import ContingencyAnalysisDriver


def nonlinear_contingency_analysis(nc: NumericalCircuit,
                                   options: ContingencyAnalysisOptions,
                                   linear_multiple_contingencies: LinearMultiContingencies,
                                   area_names: StrVec | List[str],
                                   bus_area_indices: StrVec,
                                   F: IntVec,
                                   T: IntVec,
                                   report_text: Callable[[str], None] | None,
                                   report_progress2: Callable[[int, int], None] | None,
                                   is_cancel: Callable[[], bool] | None,
                                   t_idx: Union[None, int] = None,
                                   t_prob: float = 1.0,
                                   logger: Logger | None = None, ) -> ContingencyAnalysisResults:
    """
    Run a contingency analysis using the power flow options
    :param nc: NumericalCircuit
    :param options: ContingencyAnalysisOptions
    :param linear_multiple_contingencies: LinearMultiContingencies
    :param area_names:
    :param bus_area_indices:
    :param F:
    :param T:
    :param report_text:
    :param report_progress2;
    :param is_cancel:
    :param t_idx: time index, if None the snapshot is used
    :param t_prob: probability of te time
    :param logger: logger instance
    :return: returns the results
    """
    if logger is None:
        logger = Logger()

    if options.pf_options is None:
        pf_opts = PowerFlowOptions(solver_type=SolverType.Linear,
                                   ignore_single_node_islands=True)

    else:
        pf_opts = options.pf_options

    # declare the results
    results = ContingencyAnalysisResults(ncon=len(linear_multiple_contingencies.contingency_groups_used),
                                         nbr=nc.nbr,
                                         nbus=nc.nbus,
                                         branch_names=nc.passive_branch_data.names,
                                         bus_names=nc.bus_data.names,
                                         bus_types=nc.bus_data.bus_types,
                                         con_names=linear_multiple_contingencies.get_contingency_group_names())

    # get contingency groups dictionary
    mon_idx = nc.passive_branch_data.get_monitor_enabled_indices()

    # run 0
    base_res = multi_island_pf_nc(nc=nc,
                                  options=pf_opts)

    if options.use_srap:

        # we need the PTDF for this
        linear_analysis = LinearAnalysis(nc=nc,
                                         distributed_slack=options.lin_options.distribute_slack,
                                         correct_values=options.lin_options.correct_values)

        linear_multiple_contingencies.compute(lin=linear_analysis,
                                              ptdf_threshold=options.lin_options.ptdf_threshold,
                                              lodf_threshold=options.lin_options.lodf_threshold)

        PTDF = linear_analysis.PTDF

    else:
        PTDF = None

    available_power = nc.generator_data.get_injections_per_bus().real

    # for each contingency group
    for ic, contingency_group in enumerate(linear_multiple_contingencies.contingency_groups_used):

        # get the group's contingencies
        contingencies = linear_multiple_contingencies.contingency_group_dict[contingency_group.idtag]

        # set the status
        nc.set_con_or_ra_status(contingencies)

        # report progress
        if report_text is not None:
            report_text(f'Contingency group: {contingency_group.name}')

        if report_progress2 is not None:
            report_progress2(ic, len(linear_multiple_contingencies.contingency_groups_used) * 100)

        # run
        pf_res = multi_island_pf_nc(nc=nc,
                                    options=pf_opts,
                                    V_guess=base_res.voltage,
                                    logger=logger)

        results.Sf[ic, :] = pf_res.Sf
        results.Sbus[ic, :] = pf_res.Sbus
        results.loading[ic, :] = pf_res.loading
        results.voltage[ic, :] = pf_res.voltage
        multi_contingency = linear_multiple_contingencies.multi_contingencies[ic] if options.use_srap else None

        results.report.analyze(t=t_idx,
                               t_prob=t_prob,
                               mon_idx=mon_idx,
                               nc=nc,
                               base_flow=np.abs(base_res.Sf),
                               base_loading=np.abs(base_res.loading),
                               contingency_flows=np.abs(pf_res.Sf),
                               contingency_loadings=np.abs(pf_res.loading),
                               contingency_idx=ic,
                               contingency_group=contingency_group,
                               using_srap=options.use_srap,
                               srap_ratings=nc.passive_branch_data.protection_rates,
                               srap_max_power=options.srap_max_power,
                               srap_deadband=options.srap_deadband,
                               contingency_deadband=options.contingency_deadband,
                               multi_contingency=multi_contingency,
                               PTDF=PTDF,
                               available_power=available_power,
                               srap_used_power=results.srap_used_power,
                               F=F,
                               T=T,
                               bus_area_indices=bus_area_indices,
                               area_names=area_names,
                               top_n=options.srap_top_n)

        # set the status
        nc.set_con_or_ra_status(contingencies, revert=True)

        if is_cancel is not None:
            if is_cancel():
                return results

    return results
