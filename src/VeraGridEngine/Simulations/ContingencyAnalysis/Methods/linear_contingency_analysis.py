# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Callable, List
import numpy as np
import numba as nb
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_results import ContingencyAnalysisResults
from VeraGridEngine.Simulations.LinearFactors.linear_analysis import LinearAnalysis, LinearMultiContingencies
from VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_options import ContingencyAnalysisOptions
from VeraGridEngine.basic_structures import Logger, CxVec, IntVec, StrVec, Mat, Vec


def linear_contingency_analysis(nc: NumericalCircuit,
                                options: ContingencyAnalysisOptions,
                                linear_multiple_contingencies: LinearMultiContingencies,
                                area_names: StrVec | List[str],
                                bus_area_indices: StrVec,
                                F: IntVec,
                                T: IntVec,
                                report_text: Callable[[str], None] | None,
                                report_progress2: Callable[[int, int], None] | None,
                                is_cancel: Callable[[], bool] | None,
                                t: int | None = None,
                                t_prob=1.0,
                                logger: Logger | None = None, ) -> ContingencyAnalysisResults:
    """
    Run N-1 simulation in series with HELM, non-linear solution
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
    :param t: time index, if None the snapshot is used
    :param t_prob: probability of te time
    :param logger: logger instance
    :return: returns the results
    """

    if report_text is not None:
        report_text('Analyzing outage distribution factors in a non-linear fashion...')

    # declare the results
    results = ContingencyAnalysisResults(
        ncon=len(linear_multiple_contingencies.contingency_groups_used),
        nbr=nc.nbr,
        nbus=nc.nbus,
        branch_names=nc.passive_branch_data.names,
        bus_names=nc.bus_data.names,
        bus_types=nc.bus_data.bus_types,
        con_names=np.array(linear_multiple_contingencies.get_contingency_group_names())
    )

    linear_analysis = LinearAnalysis(nc=nc,
                                     distributed_slack=options.lin_options.distribute_slack,
                                     correct_values=options.lin_options.correct_values)

    linear_multiple_contingencies.compute(lin=linear_analysis,
                                          ptdf_threshold=options.lin_options.ptdf_threshold,
                                          lodf_threshold=options.lin_options.lodf_threshold)

    # get the contingency branch indices
    mon_idx = nc.passive_branch_data.get_monitor_enabled_indices()
    Pbus = nc.get_power_injections().real

    # compute the branch Sf in "n"
    if options.use_provided_flows:
        flows_n = options.Pf

        if options.Pf is None:
            msg = 'The option to use the provided flows is enabled, but no flows are available'
            logger.add_error(msg)
            raise Exception(msg)
    else:
        Sbus: CxVec = nc.get_power_injections()  # MW
        flows_n = linear_analysis.get_flows(Sbus=Sbus, P_hvdc=nc.hvdc_data.Pset)

    loadings_n = flows_n / (nc.passive_branch_data.rates + 1e-9)

    if report_text is not None:
        report_text('Computing loading...')

    # for each contingency group
    for ic, multi_contingency in enumerate(linear_multiple_contingencies.multi_contingencies):

        if multi_contingency.enabled:

            if multi_contingency.has_injection_contingencies():
                contingency_group = linear_multiple_contingencies.contingency_groups_used[ic]
                contingencies = linear_multiple_contingencies.contingency_group_dict[contingency_group.idtag]
                linear_multiple_contingencies.get_single_con_branch_idx()
                # injections = nc.set_linear_con_or_ra_status(event_list=contingencies)
                injections = nc.set_con_or_ra_status(event_list=contingencies)
            else:
                injections = None

            c_flow = multi_contingency.get_contingency_flows(base_branches_flow=flows_n, injections=injections)
            c_loading = c_flow / (nc.passive_branch_data.rates + 1e-9)

            results.Sf[ic, :] = c_flow  # already in MW
            results.Sbus[ic, :] = Pbus
            results.loading[ic, :] = c_loading
            results.report.analyze(t=t,
                                   t_prob=t_prob,
                                   mon_idx=mon_idx,
                                   nc=nc,
                                   base_flow=flows_n,
                                   base_loading=loadings_n,
                                   contingency_flows=c_flow,
                                   contingency_loadings=c_loading,
                                   contingency_idx=ic,
                                   contingency_group=linear_multiple_contingencies.contingency_groups_used[ic],
                                   using_srap=options.use_srap,
                                   srap_ratings=nc.passive_branch_data.protection_rates,
                                   srap_max_power=options.srap_max_power,
                                   srap_deadband=options.srap_deadband,
                                   contingency_deadband=options.contingency_deadband,
                                   srap_rever_to_nominal_rating=options.srap_rever_to_nominal_rating,
                                   multi_contingency=multi_contingency,
                                   PTDF=linear_analysis.PTDF,
                                   available_power=nc.bus_data.srap_availbale_power,
                                   srap_used_power=results.srap_used_power,
                                   F=F,
                                   T=T,
                                   bus_area_indices=bus_area_indices,
                                   area_names=area_names,
                                   top_n=options.srap_top_n)

        # report progress
        if t is None:
            if report_text is not None:
                report_text(
                    f'Contingency group: {linear_multiple_contingencies.contingency_groups_used[ic].name}')

            if report_progress2 is not None:
                report_progress2(ic, len(linear_multiple_contingencies.multi_contingencies))

        if is_cancel is not None:
            if is_cancel():
                return results

    results.lodf = linear_analysis.LODF

    return results


@nb.njit()
def linear_contingency_scan_numba(nbr: int, n_con_groups: int,
                                  Pbus: Vec, rates: Vec, con_rates: Vec,
                                  PTDF: Mat, LODF: Mat, mon_idx: IntVec,
                                  single_con_br_idx: IntVec, single_con_cg_idx: IntVec):
    """
    Fast contingency scan using the PTDF
    :param nbr: Number of branches
    :param n_con_groups: Number of contingency groups
    :param Pbus: Buses injection (nbus, in MW)
    :param rates: Rates vector (nbr)
    :param con_rates: Contingency rates vector (nbr)
    :param PTDF: PTDF matrix (nbr, nbus)
    :param LODF: LODF matrix (nbr, nbr)
    :param mon_idx: Monitored branches
    :param single_con_br_idx: array of single contingency branch indices
    :param single_con_cg_idx: array of the matching contingency groups
    :return: SbrCon(nconn, nbr), LoadingCon(nconn, nbr), problems(..., (m, c))
    """

    assert len(single_con_br_idx) == len(single_con_cg_idx)

    SbrCon = np.zeros((n_con_groups, nbr))
    LoadingCon = np.zeros((n_con_groups, nbr))

    # base flow
    Sbr0 = PTDF @ Pbus
    problems = list()

    for mm in nb.prange(len(mon_idx)):

        # get the actual branch index
        m = mon_idx[mm]

        # set the base loading
        LoadingCon[:, m] = Sbr0[m] / (rates[m] + 1e-9)

        if abs(Sbr0[m]) <= rates[m]:

            for c, cgi in zip(single_con_br_idx, single_con_cg_idx):  # for each contingency branch

                # contingency flow
                SbrCon[cgi, m] = Sbr0[m] + LODF[m, c] * Sbr0[c]

                if abs(SbrCon[cgi, m]) > con_rates[m]:
                    # actually record the loading
                    LoadingCon[cgi, m] = Sbr0[m] / (con_rates[m] + 1e-9)

                    problems.append((m, c))
        else:
            problems.append((m, -1))

    return SbrCon, LoadingCon, problems
