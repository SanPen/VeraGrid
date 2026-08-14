# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import numpy as np
import time
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Compilers.Gslv.conversion import to_gslv
from VeraGridEngine.Compilers.Gslv.Simulations.power_flow import get_gslv_pf_options
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow3ph.power_flow_results_3ph import PowerFlowResults3Ph
from VeraGridEngine.basic_structures import ConvergenceReport, IntVec, Logger, StrVec


def gslv_pf_3ph(circuit: MultiCircuit,
                pf_opt: PowerFlowOptions,
                t_idx: int | None = None,
                logger: Logger | None = None) -> "pg.NumericPowerFlowResults":
    """
    Run one native GSLV three-phase power flow.

    :param circuit: VeraGrid circuit.
    :param pf_opt: VeraGrid power-flow options.
    :param t_idx: Optional VeraGrid time index to export as one sliced snapshot.
    :param logger: Optional execution logger.
    :return: GSLV numeric three-phase results.
    """
    logger_obj: Logger
    pf_options = get_gslv_pf_options(pf_opt)
    snapshot_time_indices: IntVec | None

    if logger is None:
        logger_obj = Logger()
    else:
        logger_obj = logger

    if t_idx is None:
        snapshot_time_indices = None
    else:
        snapshot_time_indices = np.array([int(t_idx)], dtype=int)

    gslv_grid, _ = to_gslv(
        circuit=circuit,
        use_time_series=t_idx is not None,
        time_indices=snapshot_time_indices,
        override_branch_controls=not (pf_opt.control_taps_modules and pf_opt.control_taps_phase),
        opf_results=None,
        add_three_phase_data=True,
    )

    t0: float = time.time()
    results = pg.power_flow_3ph(
        grid=gslv_grid,
        options=pf_options,
        t_idx=0,
        logger=pg.Logger(),
    )
    logger_obj.add_info("gslv 3ph time", value=f"{(time.time() - t0)} s")
    return results


def translate_gslv_pf_3ph_results(grid: MultiCircuit,
                                  res: "pg.NumericPowerFlowResults") -> PowerFlowResults3Ph:
    """
    Translate one GSLV native three-phase result into VeraGrid's three-phase container.

    :param grid: Original VeraGrid circuit.
    :param res: GSLV three-phase numeric result.
    :return: VeraGrid three-phase power-flow results.
    """
    bus_names: StrVec = grid.get_bus_names()
    branch_names: StrVec = grid.get_branch_names(add_hvdc=False, add_vsc=False, add_switch=True)
    results = PowerFlowResults3Ph(
        n=3 * len(bus_names),
        m=3 * len(branch_names),
        n_hvdc=grid.get_hvdc_number(),
        n_vsc=grid.get_vsc_number(),
        n_gen=grid.get_generation_like_number(),
        n_batt=grid.get_batteries_number(),
        n_sh=grid.get_shunt_like_device_number(),
        n_load=grid.get_load_like_device_number(),
        bus_names=bus_names,
        branch_names=branch_names,
        hvdc_names=grid.get_hvdc_names(),
        vsc_names=grid.get_vsc_names(),
        gen_names=grid.get_generation_like_names(),
        batt_names=grid.get_battery_names(),
        sh_names=grid.get_shunt_like_devices_names(),
        load_names=grid.get_load_like_devices_names(),
        bus_types=np.ones(len(bus_names), dtype=int),
    )

    bus_idx: IntVec = np.arange(len(bus_names), dtype=int)
    branch_idx: IntVec = np.arange(len(branch_names), dtype=int)
    hvdc_idx: IntVec = np.arange(grid.get_hvdc_number(), dtype=int)
    vsc_idx: IntVec = np.arange(grid.get_vsc_number(), dtype=int)
    report: ConvergenceReport = ConvergenceReport()

    report.add(
        method=res.method,
        converged=bool(res.converged),
        error=float(res.norm_f),
        elapsed=float(res.elapsed),
        iterations=int(res.iterations),
    )

    results.apply_from_island(
        results=res,
        b_idx=bus_idx,
        br_idx=branch_idx,
        hvdc_idx=hvdc_idx,
        vsc_idx=vsc_idx,
    )
    results.convergence_reports.append(report)
    return results
