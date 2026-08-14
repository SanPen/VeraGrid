# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import (
    IntVec,
    Logger,
)
from VeraGridEngine.enumerations import (
    AcOpfMode,
    MIPSolvers,
    OpfDispatchMode,
    SolverType,
    TimeGrouping,
    ZonalGrouping,
)
import numpy as np
import time
from typing import TYPE_CHECKING, Union
from VeraGridEngine.Compilers.Gslv.conversion import to_gslv

if TYPE_CHECKING:
    from VeraGridEngine.Simulations.OPF.opf_options import OptimalPowerFlowOptions


def get_gslv_opf_options(opt: OptimalPowerFlowOptions,
                         circuit: MultiCircuit,
                         gslv_circuit: "pg.MultiCircuit") -> "pg.OptimalPowerFlowOptions":
    """
    Translate VeraGrid power flow options to GSLV power flow options
    :param opt:
    :param circuit:
    :param gslv_circuit:
    :return:
    """
    # OpfDispatchMode, MIPSolvers, ZonalGrouping, TimeGrouping

    dispatch_mode_dict = {
        OpfDispatchMode.Normal: pg.OpfDispatchMode.Normal,
        OpfDispatchMode.InterAreaRedispatch: pg.OpfDispatchMode.InterAreaRedispatch,
        OpfDispatchMode.UnitCommitment: pg.OpfDispatchMode.UnitCommitment,
        OpfDispatchMode.NodalCapacity: pg.OpfDispatchMode.NodalCapacity,
        OpfDispatchMode.GenerationExpansionPlanning: pg.OpfDispatchMode.GenerationExpansionPlanning,
    }

    mip_solver_dict = {
        MIPSolvers.HIGHS: pg.MIPSolvers.HIGHS,
        MIPSolvers.SCIP: pg.MIPSolvers.SCIP,
        MIPSolvers.CPLEX: pg.MIPSolvers.CPLEX,
        MIPSolvers.GUROBI: pg.MIPSolvers.GUROBI,
        MIPSolvers.XPRESS: pg.MIPSolvers.XPRESS,
        # MIPSolvers.CBC: pg.MIPSolvers.CBC,
        # MIPSolvers.PDLP: pg.MIPSolvers.PDLP,
    }

    zonal_grouping_dict = {
        ZonalGrouping.NoGrouping: pg.ZonalGrouping.NoGrouping,
        ZonalGrouping.Area: pg.ZonalGrouping.Area,
        ZonalGrouping.All: pg.ZonalGrouping.All,
    }

    time_grouping_dict = {
        TimeGrouping.NoGrouping: pg.TimeGrouping.NoGrouping,
        TimeGrouping.Monthly: pg.TimeGrouping.Monthly,
        TimeGrouping.Weekly: pg.TimeGrouping.Weekly,
        TimeGrouping.Daily: pg.TimeGrouping.Daily,
        TimeGrouping.Hourly: pg.TimeGrouping.Hourly,
    }
    acopf_mode_dict = {
        AcOpfMode.ACOPFstd: pg.AcOpfMode.ACOPFstd,
        AcOpfMode.ACOPFslacks: pg.AcOpfMode.ACOPFslacks,
        AcOpfMode.ACOPFMaxInjections: pg.AcOpfMode.ACOPFMaxInjections,
    }
    ips_method_dict = {
        SolverType.NR: pg.SolverType.NR,
        SolverType.HELM: pg.SolverType.HELM,
        SolverType.IWAMOTO: pg.SolverType.IWAMOTO,
        SolverType.LM: pg.SolverType.LM,
        SolverType.FASTDECOUPLED: pg.SolverType.FASTDECOUPLED,
        SolverType.LACPF: pg.SolverType.LACPF,
        SolverType.Linear: pg.SolverType.DC,
    }

    cg_dict = {elm.get_idtag(): elm for elm in gslv_circuit.contingency_groups}

    contingency_groups_used = [cg_dict[cg.idtag] for cg in opt.contingency_groups_used]
    if opt.acopf_pf_converged:
        acopf_v0 = None if opt.acopf_v0 is None else np.asarray(opt.acopf_v0, dtype=np.complex128)
        acopf_s0 = None if opt.acopf_S0 is None else np.asarray(opt.acopf_S0, dtype=np.complex128)
    else:
        # Do not inject a failed PF state into GSLV's nonlinear OPF bootstrap.
        acopf_v0 = None
        acopf_s0 = None

    return pg.OptimalPowerFlowOptions(
        dispatch_mode=dispatch_mode_dict[opt.dispatch_mode],
        solver_type=mip_solver_dict[opt.mip_solver],
        zonal_grouping=zonal_grouping_dict[opt.zonal_grouping],
        time_grouping=time_grouping_dict[opt.time_grouping],
        skip_generation_limits=opt.skip_generation_limits,
        consider_contingencies=opt.consider_contingencies,
        contingency_groups_used=contingency_groups_used,
        ramp_constraints=opt.consider_ramps,
        consider_time_up_down=opt.consider_time_up_down,
        area_spinning_reserve=opt.area_spinning_reserve,
        lodf_threshold=opt.lodf_tolerance,
        inter_aggregation_info=opt.inter_aggregation_info,  # translate
        nodal_capacity_sign=1.0,
        capacity_nodes_idx_in=None,
        use_glsk_as_cost=opt.use_glsk_as_cost,
        add_losses_approximation=opt.add_losses_approximation,
        verbose=opt.verbose,
        robust=opt.robust,
        acopf_mode=acopf_mode_dict[opt.acopf_mode],
        ips_method=ips_method_dict.get(opt.ips_method, pg.SolverType.NR),
        ips_tolerance=opt.ips_tolerance,
        ips_iterations=opt.ips_iterations,
        ips_trust_radius=opt.ips_trust_radius,
        ips_init_with_pf=opt.ips_init_with_pf,
        ips_control_q_limits=opt.ips_control_q_limits,
        acopf_v0=acopf_v0,
        acopf_s0=acopf_s0,
        acopf_pf_converged=opt.acopf_pf_converged,
    )


def gslv_opf(circuit: MultiCircuit,
             opf_options: OptimalPowerFlowOptions,
             time_series: bool = False,
             time_indices: Union[IntVec, None] = None,
             logger: Logger = Logger()) -> "pg.OptimalPowerFlowResults":
    """
    GSLV power flow
    :param logger:
    :param circuit: MultiCircuit instance
    :param opf_options: Power Flow Options
    :param time_series: Compile with VeraGrid time series?
    :param time_indices: Array of time indices
    :return: GSLV Power flow results object
    """
    gslv_grid, _ = to_gslv(circuit,
                           use_time_series=time_series,
                           time_indices=None,
                           override_branch_controls=False,
                           opf_results=None)

    run_nonlinear: bool = opf_options.solver == SolverType.NONLINEAR_OPF and not time_series
    opf_options = get_gslv_opf_options(opf_options, circuit, gslv_grid)

    if time_series:
        # Keep the GSLV grid at the circuit time resolution and ask the solver
        # for the requested global time indices explicitly.
        if time_indices is None:
            time_indices = [i for i in range(circuit.get_time_number())]
        else:
            time_indices = list(time_indices)
        n_threads = 0  # max threads
    else:
        time_indices = [0]
        n_threads = 1

    t0 = time.time()

    if run_nonlinear:
        opf_res = pg.nonlinear_optimal_power_flow(
            grid=gslv_grid,
            options=opf_options,
            t_idx=0,
        )
    else:
        opf_res = pg.optimal_power_flow(
            grid=gslv_grid,
            options=opf_options,
            n_threads=n_threads,
            time_indices=time_indices,
        )

    logger.add_info("gslv time", value=f"{(time.time() - t0)} s")

    return opf_res
