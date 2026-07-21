# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
from copy import copy
from typing import Union, Tuple, Sequence

from VeraGridEngine import ShuntControlMode
from VeraGridEngine.Utils.NumericalMethods.ips import interior_point_solver
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.Simulations.PowerFlow.power_flow_worker import multi_island_pf_nc
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.OPF.opf_options import OptimalPowerFlowOptions
from VeraGridEngine.Simulations.OPF.Formulations.ac_opf_problem import NonLinearOptimalPfProblem, NonlinearOPFResults
from VeraGridEngine.Simulations.OPF.NumericalMethods.newton_raphson_ips_fx import \
    interior_point_solver as interior_point_solver_fx
from VeraGridEngine.Simulations.OPF.NumericalMethods.newton_raphson_ips_pc import \
    interior_point_solver as interior_point_solver_pc
from VeraGridEngine.basic_structures import CxVec, IntVec, Logger
from VeraGridEngine.enumerations import AcOpfMode, SolverType


def remap_original_bus_indices(n_bus, original_bus_idx: Sequence[int]) -> Tuple[IntVec, IntVec]:
    """
    Get arrays of bus mappings
    :param n_bus: number of buses
    :param original_bus_idx: array of bus indices in the multi-island scheme
    :return: original_indices: array of bus indices in the multi-island that apply for this island,
             island_indices: array of island indices that apply for this island
    """
    original_idx = np.arange(n_bus, dtype=int)
    mapping = {o: i for i, o in enumerate(original_idx)}
    island_indices = list()
    original_indices = list()
    for a, o in enumerate(original_bus_idx):
        i = mapping.get(o, None)
        if i is not None:
            island_indices.append(i)
            original_indices.append(a)

    return np.array(original_indices, dtype=int), np.array(island_indices, dtype=int)


def prefer_retry_result(base_results: NonlinearOPFResults,
                        retry_results: NonlinearOPFResults) -> NonlinearOPFResults:
    """
    Choose the better ACOPF result between two candidate solves.

    :param base_results: First candidate result.
    :param retry_results: Second candidate result.
    :return: Preferred result based on convergence first, then solver error.
    """
    if retry_results.converged and not base_results.converged:
        return retry_results
    else:
        pass

    if base_results.converged and not retry_results.converged:
        return base_results
    else:
        pass

    if retry_results.error < base_results.error:
        return retry_results
    else:
        return base_results


def run_nonlinear_opf(grid: MultiCircuit,
                      opf_options: OptimalPowerFlowOptions,
                      t_idx: Union[None, int] = None,
                      plot_error: bool = False,
                      optimize_nodal_capacity: bool = False,
                      nodal_capacity_sign: float = 1.0,
                      capacity_nodes_idx: Union[IntVec, None] = None,
                      logger: Logger = Logger(),
                      allow_seed_retries: bool = True) -> NonlinearOPFResults:
    """
    Run optimal power flow for a MultiCircuit
    :param grid: MultiCircuit
    :param opf_options: OptimalPowerFlowOptions
    :param t_idx: Time index
    :param plot_error: Plot the error evolution
    :param optimize_nodal_capacity:
    :param nodal_capacity_sign:
    :param capacity_nodes_idx:
    :param logger: Logger object
    :param allow_seed_retries: Allow one round of large-case seed retries
    :return: NonlinearOPFResults
    """

    # compile the system
    nc = compile_numerical_circuit_at(circuit=grid, t_idx=t_idx, logger=logger)

    if opf_options.ips_init_with_pf and opf_options.acopf_S0 is not None and opf_options.acopf_v0 is not None:
        # pick the passed values
        Sbus_pf = opf_options.acopf_S0
        voltage_pf = opf_options.acopf_v0
    else:
        # Fall back to the static network data when no PF seed is requested or available.
        Sbus_pf = nc.bus_data.installed_power
        voltage_pf = nc.bus_data.Vbus
        if opf_options.ips_init_with_pf:
            logger.add_error("Initialized with PF, but no PF values were passed")
        else:
            pass

    # split into islands, but considering the HVDC lines as actual links
    split_islands = nc.split_into_islands(ignore_single_node_islands=True,
                                          consider_hvdc_as_island_links=True)

    projected_island_retry = None
    projected_shape_mismatch = (
            len(split_islands) == 1
            and split_islands[0].nbus == nc.nbus
            and (
                    split_islands[0].ngen != nc.ngen
                    or split_islands[0].nbr != nc.nbr
                    or split_islands[0].nshunt != nc.nshunt
                    or split_islands[0].nhvdc != nc.nhvdc
                    or split_islands[0].vsc_data.nelm != nc.vsc_data.nelm
            )
    )

    if projected_shape_mismatch:
        # Some single-island benchmark cases keep the full bus set while the
        # island projection changes the generator or branch tables. Different
        # cases need different sides of that split, so solve the original
        # compiled circuit first and retry the projected island only if
        # needed.
        islands = [nc]
        projected_island_retry = split_islands
    elif len(split_islands) == 1 and split_islands[0].nbus == nc.nbus:
        islands = [nc]
    else:
        islands = split_islands

    # A PF state can still be a useful primal seed. The PF-specific
    # multiplier bootstrap is unstable on plain AC benchmark cases, but the
    # AC/DC path still relies on it for the converter-coupled formulation.
    # Keep the decision local to each compiled problem so VSC cases can
    # retain the historical bootstrap.
    use_pf_state_init: bool = opf_options.ips_init_with_pf

    def solve_compiled_islands(compiled_islands) -> NonlinearOPFResults:
        results = NonlinearOPFResults()
        results.initialize(nbus=nc.nbus, nbr=nc.nbr, nsh=nc.nshunt, ng=nc.ngen,
                           nil=len(nc.passive_branch_data.get_monitor_enabled_indices()),
                           nhvdc=nc.nhvdc, ncap=len(capacity_nodes_idx) if capacity_nodes_idx is not None else 0,
                           nvsc=nc.vsc_data.nelm)

        for i, island in enumerate(compiled_islands):

            if capacity_nodes_idx is not None:
                (capacity_nodes_idx_org,
                 capacity_nodes_idx_isl) = remap_original_bus_indices(n_bus=nc.nbus,
                                                                      original_bus_idx=capacity_nodes_idx)
            else:
                capacity_nodes_idx_org = None
                capacity_nodes_idx_isl = None

            problem = NonLinearOptimalPfProblem(nc=island,
                                                options=opf_options,
                                                pf_init=use_pf_state_init,
                                                Sbus_pf=Sbus_pf[island.bus_data.original_idx],
                                                voltage_pf=voltage_pf[island.bus_data.original_idx],
                                                optimize_nodal_capacity=optimize_nodal_capacity,
                                                nodal_capacity_sign=nodal_capacity_sign,
                                                capacity_nodes_idx=capacity_nodes_idx_isl,
                                                logger=logger
                                                )

            use_pf_multiplier_init: bool = bool(
                problem.nvsc) and opf_options.ips_init_with_pf and opf_options.acopf_pf_converged

            # The VSC current-definition equalities can become ill-conditioned when
            # a converter is close to its hard current limit.  Keep a little more
            # distance from the inequality boundary in that active set while keeping
            # the historical fraction-to-boundary value for ordinary AC OPF cases.
            xi = 0.995 if problem.nvsc else 0.99995
            # Large plain-AC PGLIB cases are sensitive to the IPS trajectory even
            # when the derivatives are correct. Keep the undamped historical path
            # for small cases, but switch to a conservative trust-controlled path
            # on large ACOPF instances to avoid late KKT breakdowns.
            use_step_control = False
            trust_radius = opf_options.ips_trust_radius
            if (not problem.nvsc) and problem.nbus >= 1000:
                use_step_control = True
                if use_pf_state_init:
                    trust_radius = min(trust_radius, 0.2)
                else:
                    trust_radius = min(trust_radius, 0.1)
            else:
                pass

            if opf_options.ips_method == SolverType.NR_PC:
                ips_results = interior_point_solver_pc(problem=problem,
                                                       max_iter=opf_options.ips_iterations,
                                                       tol=opf_options.ips_tolerance,
                                                       pf_init=use_pf_multiplier_init,
                                                       trust=trust_radius,
                                                       verbose=opf_options.verbose,
                                                       step_control=use_step_control,
                                                       xi=xi)

            elif opf_options.ips_method == SolverType.NR:

                ips_results = interior_point_solver_fx(problem=problem,
                                                       max_iter=opf_options.ips_iterations,
                                                       tol=opf_options.ips_tolerance,
                                                       pf_init=use_pf_multiplier_init,
                                                       trust=trust_radius,
                                                       verbose=opf_options.verbose,
                                                       step_control=use_step_control,
                                                       xi=xi)
            else:
                ips_results = interior_point_solver_fx(problem=problem,
                                                       max_iter=opf_options.ips_iterations,
                                                       tol=opf_options.ips_tolerance,
                                                       pf_init=use_pf_multiplier_init,
                                                       trust=trust_radius,
                                                       verbose=opf_options.verbose,
                                                       step_control=use_step_control,
                                                       xi=xi)

            island_res = problem.get_solution(ips_results=ips_results, verbose=opf_options.verbose,
                                              plot_error=plot_error)

            results.merge(other=island_res,
                          bus_idx=island.bus_data.original_idx,
                          br_idx=island.passive_branch_data.original_idx,
                          il_idx=island.passive_branch_data.get_monitor_enabled_indices(),
                          gen_idx=island.generator_data.original_idx,
                          hvdc_idx=island.hvdc_data.original_idx,
                          ncap_idx=capacity_nodes_idx_org,
                          contshunt_idx=
                          np.where(island.shunt_data.control_mode_int == ShuntControlMode.Continuous.idx())[0],
                          acopf_mode=opf_options.acopf_mode,
                          vsc_idx=island.vsc_data.original_idx)
            if i > 0:
                results.error = max(results.error, island_res.error)
                results.iterations = max(results.iterations, island_res.iterations)
                results.converged = results.converged and island_res.converged if i > 0 else island_res.converged
            else:
                results.error = island_res.error
                results.iterations = island_res.iterations
                results.converged = island_res.converged

        return results

    results = solve_compiled_islands(islands)

    if projected_island_retry is not None and not results.converged:
        retry_results = solve_compiled_islands(projected_island_retry)
        results = prefer_retry_result(base_results=results, retry_results=retry_results)

    # expand voltages if there was a bus topology reduction
    if nc.topology_performed:
        results.Va = nc.propagate_bus_result(results.Va)
        results.Vm = nc.propagate_bus_result(results.Vm)
        results.voltage = nc.propagate_bus_result(results.voltage)

    if allow_seed_retries and nc.vsc_data.nelm == 0 and nc.nbus >= 2000 and not results.converged:
        # A PF seed can land in a wrong OPF basin on some large benchmark
        # cases. Retry once from the flat interior start, but only when the
        # original seed came from a genuinely converged PF state.
        if opf_options.ips_init_with_pf:
            retry_options: OptimalPowerFlowOptions = copy(opf_options)
            retry_options.ips_init_with_pf = False
            retry_options.acopf_v0 = None
            retry_options.acopf_S0 = None
            retry_options.acopf_pf_converged = False
            retry_results: NonlinearOPFResults = run_nonlinear_opf(grid=grid,
                                                                   opf_options=retry_options,
                                                                   t_idx=t_idx,
                                                                   plot_error=plot_error,
                                                                   optimize_nodal_capacity=optimize_nodal_capacity,
                                                                   nodal_capacity_sign=nodal_capacity_sign,
                                                                   capacity_nodes_idx=capacity_nodes_idx,
                                                                   logger=logger,
                                                                   allow_seed_retries=False)
            return prefer_retry_result(base_results=results, retry_results=retry_results)
        else:
            return results
    else:
        return results
