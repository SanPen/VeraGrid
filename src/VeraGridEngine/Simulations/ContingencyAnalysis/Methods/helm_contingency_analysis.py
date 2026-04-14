# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np
from typing import Union, TYPE_CHECKING
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_results import ContingencyAnalysisResults
from VeraGridEngine.Simulations.ContingencyAnalysis.Methods.helm_contingencies import HelmVariations
from VeraGridEngine.Simulations.PowerFlow.power_flow_worker import multi_island_pf_nc
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions, SolverType
from VeraGridEngine.Simulations.ContingencyAnalysis.contingency_analysis_options import ContingencyAnalysisOptions
from VeraGridEngine.enumerations import ContingencyOperationTypes

if TYPE_CHECKING:  # Only imports the below statements during type checking
    from VeraGridEngine.Compilers.circuit_to_data import VALID_OPF_RESULTS


def helm_contingency_analysis(grid: MultiCircuit,
                              options: ContingencyAnalysisOptions,
                              calling_class,
                              opf_results: VALID_OPF_RESULTS | None = None,
                              t: Union[int, None] = None,
                              t_prob: float = 1.0) -> ContingencyAnalysisResults:
    """
    Run N-1 simulation in series with HELM, non-linear solution
    :param grid:
    :param options:
    :param calling_class:
    :param opf_results: OPF results, to be used if not None
    :param t: time index, if None the snapshot is used
    :param t_prob: probability of te time
    :return: returns the results
    """

    # set the numerical circuit
    nc = compile_numerical_circuit_at(grid,
                                      opf_results=opf_results,
                                      t_idx=t)

    if options.pf_options is None:
        pf_opts = PowerFlowOptions(solver_type=SolverType.Linear,
                                   ignore_single_node_islands=True)

    else:
        pf_opts = options.pf_options

    # declare the results
    results = ContingencyAnalysisResults(ncon=len(grid.contingency_groups),
                                         nbr=nc.nbr,
                                         nbus=nc.nbus,
                                         branch_names=nc.passive_branch_data.names,
                                         bus_names=nc.bus_data.names,
                                         bus_types=nc.bus_data.bus_types,
                                         con_names=grid.get_contingency_group_names())

    # get contingency groups dictionary
    cg_dict = grid.get_contingency_group_dict()

    branches_dict = grid.get_branches_dict(add_vsc=False, add_hvdc=False, add_switch=True)
    # calc_branches = grid.get_branches(add_hvdc=False, add_vsc=False, add_switch=True)
    mon_idx = nc.passive_branch_data.get_monitor_enabled_indices()

    # keep the original states
    original_br_active = nc.passive_branch_data.active.copy()
    original_gen_active = nc.generator_data.active.copy()
    original_gen_p = nc.generator_data.p.copy()

    # run 0
    pf_res_0 = multi_island_pf_nc(nc=nc,
                                  options=pf_opts)

    helm_variations = HelmVariations(numerical_circuit=nc)

    Sbus = nc.get_power_injections_pu()

    # for each contingency group
    for ic, contingency_group in enumerate(grid.contingency_groups):

        # get the group's contingencies
        contingencies = cg_dict[contingency_group.idtag]

        # apply the contingencies
        contingency_br_indices = list()
        for cnt in contingencies:

            # search for the contingency in the Branches
            br_idx = branches_dict.get(cnt.device_idtag, None)
            if br_idx is not None:
                if cnt.prop == ContingencyOperationTypes.Active:
                    contingency_br_indices.append(br_idx)
                else:
                    print(f'Unknown contingency property {cnt.prop} at {cnt.name} {cnt.idtag}')
            else:
                print(f"Contingency device not found in branches: {cnt.device_idtag}")

        # report progress
        if t is None:
            if calling_class is not None:
                calling_class.report_text(f'Contingency group: {contingency_group.name}')
                calling_class.report_progress2(ic, len(grid.contingency_groups) * 100)

        # run
        V, Sf, loading = helm_variations.compute_variations(
            contingency_br_indices=np.array(contingency_br_indices)
        )

        results.voltage[ic, :] = V
        results.Sf[ic, :] = Sf
        results.Sbus[ic, :] = Sbus
        results.loading[ic, :] = loading
        results.report.analyze(t=t,
                               t_prob=t_prob,
                               mon_idx=mon_idx,
                               nc=nc,
                               base_flow=np.abs(pf_res_0.Sf),
                               base_loading=np.abs(pf_res_0.loading),
                               contingency_flows=np.abs(Sf),
                               contingency_loadings=np.abs(loading),
                               contingency_idx=ic,
                               contingency_group=contingency_group,
                               srap_ratings=nc.passive_branch_data.protection_rates, )

        # revert the states for the next run
        nc.passive_branch_data.active = original_br_active.copy()
        nc.generator_data.active = original_gen_active.copy()
        nc.generator_data.p = original_gen_p.copy()

        if calling_class is not None:
            if calling_class.is_cancel():
                return results

    return results
