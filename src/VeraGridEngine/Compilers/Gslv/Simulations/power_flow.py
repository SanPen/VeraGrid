# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.Simulations.PowerFlow.power_flow_ts_results import PowerFlowTimeSeriesResults
from VeraGridEngine.basic_structures import (
    ConvergenceReport,
    IntVec,
    Logger,
)
from VeraGridEngine.enumerations import SolverType
import numpy as np
import time
from typing import TYPE_CHECKING, Union
from VeraGridEngine.Compilers.Gslv.conversion import to_gslv

if TYPE_CHECKING:
    from VeraGridEngine.Simulations.OPF.opf_results import OptimalPowerFlowResults

def get_gslv_pf_options(opt: PowerFlowOptions) -> "pg.PowerFlowOptions":
    """
    Translate VeraGrid power flow options to GSLV power flow options
    :param opt:
    :return:
    """
    solver_dict = {SolverType.NR: pg.SolverType.NR,
                   SolverType.Linear: pg.SolverType.DC,
                   SolverType.HELM: pg.SolverType.HELM,
                   SolverType.IWAMOTO: pg.SolverType.IWAMOTO,
                   SolverType.LM: pg.SolverType.LM,
                   SolverType.LACPF: pg.SolverType.LACPF,
                   SolverType.FASTDECOUPLED: pg.SolverType.FASTDECOUPLED
                   }

    if opt.solver_type in solver_dict.keys():
        solver_type = solver_dict[opt.solver_type]
    else:
        solver_type = pg.SolverType.NR

    """
    solver_type: GSLVpa.SolverType = <SolverType.NR: 0>, 
    retry_with_other_methods: bool = True, 
    verbose: bool = False, 
    initialize_with_existing_solution: bool = False, 
    tolerance: float = 1e-06, 
    max_iter: int = 15, 
    control_q_mode: GSLVpa.ReactivePowerControlMode = <ReactivePowerControlMode.NoControl: 0>, 
    tap_control_mode: GSLVpa.TapsControlMode = <TapsControlMode.NoControl: 0>, 
    distributed_slack: bool = False, 
    ignore_single_node_islands: bool = False, 
    correction_parameter: float = 0.5, 
    mu0: float = 1.0
    """

    """
    solver_type: pygslv.SolverType = <SolverType.NR: 0>, 
    retry_with_other_methods: bool = True, 
    verbose: int = 0, 
    initialize_with_existing_solution: bool = False, 
    tolerance: float = 1e-06, 
    max_iter: int = 25, 
    max_outer_loop_iter: int = 100, 
    control_Q: bool = True, 
    control_taps_modules: bool = True, 
    control_taps_phase: bool = True, 
    control_remote_voltage: bool = True, 
    orthogonalize_controls: bool = True, 
    apply_temperature_correction: bool = True, 
    branch_impedance_tolerance_mode: pygslv.BranchImpedanceMode = <BranchImpedanceMode.Specified: 0>, 
    distributed_slack: bool = False, 
    ignore_single_node_islands: bool = False, 
    trust_radius: float = 1.0, 
    backtracking_parameter: float = 0.05, 
    use_stored_guess: bool = False, 
    generate_report: bool = False)

    """

    return pg.PowerFlowOptions(
        solver_type=solver_type,
        retry_with_other_methods=opt.retry_with_other_methods,
        verbose=opt.verbose,
        initialize_with_existing_solution=opt.use_stored_guess,
        tolerance=opt.tolerance,
        max_iter=opt.max_iter,
        control_Q=opt.control_Q,
        control_taps_modules=opt.control_taps_modules,
        control_taps_phase=opt.control_taps_phase,
        control_remote_voltage=opt.control_remote_voltage,
        orthogonalize_controls=opt.orthogonalize_controls,
        apply_temperature_correction=opt.orthogonalize_controls,
        branch_impedance_tolerance_mode=pg.BranchImpedanceMode.Specified,
        distributed_slack=opt.distributed_slack,
        ignore_single_node_islands=opt.ignore_single_node_islands,
        trust_radius=opt.trust_radius,
        backtracking_parameter=opt.backtracking_parameter,
        use_stored_guess=opt.use_stored_guess,
        generate_report=opt.generate_report
    )

def gslv_pf(circuit: MultiCircuit,
            pf_opt: PowerFlowOptions,
            time_series: bool = False,
            time_indices: Union[IntVec, None] = None,
            opf_results: Union[None, OptimalPowerFlowResults] = None,
            logger: Logger | None = None) -> "pg.PowerFlowResults":
    """
    GSLV power flow
    :param logger: Optional execution logger.
    :param circuit: MultiCircuit instance
    :param pf_opt: Power Flow Options
    :param time_series: Compile with VeraGrid time series?
    :param time_indices: Array of time indices
    :param opf_results: Instance of
    :return: GSLV Power flow results object
    """
    logger_obj: Logger
    override_branch_controls = not (pf_opt.control_taps_modules and pf_opt.control_taps_phase)

    if logger is None:
        logger_obj = Logger()
    else:
        logger_obj = logger

    gslv_grid, _ = to_gslv(circuit,
                           use_time_series=time_series,
                           time_indices=None,
                           override_branch_controls=override_branch_controls,
                           opf_results=opf_results)

    pf_options = get_gslv_pf_options(pf_opt)

    if time_series:
        # it is already sliced to the relevant time indices
        if time_indices is None:
            time_indices = [i for i in range(circuit.get_time_number())]
        else:
            time_indices = list(time_indices)
        # GSLV's batched multi-threaded PF path is not stable with controllable shunts.
        n_threads = 1 if len(circuit.get_controllable_shunts()) > 0 else 0
    else:
        time_indices = [0]
        n_threads = 1

    t0 = time.time()
    pf_res = pg.multi_island_pf(grid=gslv_grid,
                                options=pf_options,
                                time_indices=time_indices,
                                n_threads=n_threads)

    logger_obj.add_info("gslv time", value=f"{(time.time() - t0)} s")

    return pf_res

def translate_gslv_pf_results(
        grid: MultiCircuit,
        res: "pg.PowerFlowResults",
) -> PowerFlowResults:
    """
    Translate the GSLV Power Analytics results back to VeraGrid
    :param grid: MultiCircuit instance
    :param res: GSLV's PowerFlowResults instance
    :return: PowerFlowResults instance
    """
    results = PowerFlowResults(
        n=grid.get_bus_number(),
        m=grid.get_branch_number(add_switch=True, add_vsc=False, add_hvdc=False),
        n_hvdc=grid.get_hvdc_number(),
        n_vsc=grid.get_vsc_number(),
        n_gen=grid.get_generators_number(),
        n_batt=grid.get_batteries_number(),
        n_sh=grid.get_shunt_like_device_number(),
        bus_names=grid.get_bus_names(),
        branch_names=grid.get_branch_names(add_switch=True, add_vsc=False, add_hvdc=False),
        hvdc_names=grid.get_hvdc_names(),
        vsc_names=grid.get_vsc_names(),
        gen_names=grid.get_generator_names(),
        batt_names=grid.get_battery_names(),
        sh_names=grid.get_shunt_like_devices_names(),
        bus_types=np.ones(grid.get_bus_number(), dtype=int)
    )

    results.voltage = res.voltage[0, :]
    results.Sbus = res.S[0, :]
    results.Sf = res.Sf[0, :]
    results.St = res.St[0, :]
    results.loading = res.loading[0, :]
    results.losses = res.losses[0, :]
    # results.Vbranch = res.Vbranch[0, :]
    results.If = res.If[0, :]
    results.It = res.It[0, :]

    results.tap_module = res.tap_module[0, :]
    results.tap_angle = res.tap_angle[0, :]
    # results.F = res.F
    # results.T = res.T
    # results.hvdc_F = res.hvdc_F[0, :]
    # results.hvdc_T = res.hvdc_T[0, :]
    results.Pf_hvdc = res.Pf_hvdc[0, :]
    results.Pt_hvdc = res.Pt_hvdc[0, :]
    results.loading_hvdc = res.loading_hvdc[0, :]
    results.losses_hvdc = res.losses_hvdc[0, :]

    results.Pfp_vsc = res.Pfp_vsc[0, :]
    results.Pfn_vsc = res.Pfn_vsc[0, :]
    results.St_vsc = res.St_vsc[0, :]
    results.If_vsc = res.If_vsc[0, :]
    results.It_vsc = res.It_vsc[0, :]
    results.loading_vsc = res.loading_vsc[0, :]
    results.losses_vsc = res.losses_vsc[0, :]
    results.gen_p = res.gen_p[0, :]
    results.battery_p = res.battery_p[0, :]
    results.gen_q = res.gen_q[0, :]
    results.battery_q = res.battery_q[0, :]
    results.shunt_q = res.shunt_q[0, :]

    results.bus_area_indices = grid.get_bus_area_indices()
    results.area_names = [a.name for a in grid.areas]
    # results.bus_types = convert_bus_types(res.bus_types[0])  # this is a list of lists

    for rep in res.reports[0]:
        report = ConvergenceReport()
        for i in range(len(rep.converged)):
            report.add(method=str(rep.methods[i].name),
                       converged=rep.converged[i],
                       error=rep.error[i],
                       elapsed=rep.elapsed[i],
                       iterations=rep.iterations[i])
            results.convergence_reports.append(report)

    return results

def translate_gslv_pf_time_series_results(
        grid: MultiCircuit,
        res: "pg.PowerFlowResults",
        options: PowerFlowOptions,
        time_indices: Union[IntVec, None],
        clustering_results,
) -> PowerFlowTimeSeriesResults:
    """
    Translate GSLV time-series power-flow results to VeraGrid results.

    :param grid: MultiCircuit instance.
    :param res: GSLV power-flow results.
    :param options: Power-flow options used for the run.
    :param time_indices: Requested global time indices, or ``None`` for all.
    :param clustering_results: Optional clustering metadata.
    :return: PowerFlowTimeSeriesResults instance.
    """
    if time_indices is None:
        selected_time_indices: IntVec = np.array(grid.get_all_time_indices(), dtype=int)
    else:
        selected_time_indices = np.array(time_indices, dtype=int)

    n_bus: int = grid.get_bus_number()
    results = PowerFlowTimeSeriesResults(
        n=n_bus,
        m=grid.get_branch_number(add_switch=True, add_vsc=False, add_hvdc=False),
        n_hvdc=grid.get_hvdc_number(),
        n_vsc=grid.get_vsc_number(),
        n_gen=grid.get_generators_number(),
        n_batt=grid.get_batteries_number(),
        n_sh=grid.get_shunt_like_device_number(),
        bus_names=grid.get_bus_names(),
        branch_names=grid.get_branch_names(add_switch=True, add_vsc=False, add_hvdc=False),
        hvdc_names=grid.get_hvdc_names(),
        vsc_names=grid.get_vsc_names(),
        gen_names=grid.get_generator_names(),
        batt_names=grid.get_battery_names(),
        sh_names=grid.get_shunt_like_devices_names(),
        bus_types=np.ones(n_bus, dtype=int),
        time_array=grid.get_time_array()[selected_time_indices],
        area_names=grid.get_area_names(),
        clustering_results=clustering_results,
    )

    # GSLV returns full-length time-series arrays. Slice them to the requested
    # time positions so the VeraGrid result object preserves its usual shape.
    results.voltage = res.voltage[selected_time_indices, :]
    results.S = res.S[selected_time_indices, :]
    results.Sf = res.Sf[selected_time_indices, :]
    results.St = res.St[selected_time_indices, :]
    results.If = res.If[selected_time_indices, :]
    results.It = res.It[selected_time_indices, :]
    results.loading = res.loading[selected_time_indices, :]
    results.losses = res.losses[selected_time_indices, :]
    results.tap_module = res.tap_module[selected_time_indices, :]
    results.tap_angle = res.tap_angle[selected_time_indices, :]
    results.hvdc_Pf = res.Pf_hvdc[selected_time_indices, :]
    results.hvdc_Pt = res.Pt_hvdc[selected_time_indices, :]
    results.hvdc_loading = res.loading_hvdc[selected_time_indices, :]
    results.hvdc_losses = res.losses_hvdc[selected_time_indices, :]
    results.Pf_vsc = res.Pfp_vsc[selected_time_indices, :]
    results.Pfn_vsc = res.Pfn_vsc[selected_time_indices, :]
    results.St_vsc = res.St_vsc[selected_time_indices, :]
    results.If_vsc = res.If_vsc[selected_time_indices, :]
    results.It_vsc = res.It_vsc[selected_time_indices, :]
    results.loading_vsc = res.loading_vsc[selected_time_indices, :]
    results.losses_vsc = res.losses_vsc[selected_time_indices, :]
    results.gen_p = res.gen_p[selected_time_indices, :]
    results.battery_p = res.battery_p[selected_time_indices, :]
    results.gen_q = res.gen_q[selected_time_indices, :]
    results.battery_q = res.battery_q[selected_time_indices, :]
    results.shunt_q = res.shunt_q[selected_time_indices, :]
    results.error_values = res.error_values[selected_time_indices]
    results.converged_values = res.converged_values[selected_time_indices]

    return results
