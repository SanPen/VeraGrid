# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple
import numba as nb
import numpy as np
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Simulations.OPF.simple_dispatch_ts import greedy_dispatch2
from VeraGridEngine.basic_structures import IntMat, Vec, Mat
import VeraGridEngine as vge

"""
Common reliability indicators:


(System Average Interruption Frequency Index)
SAIFI = total number of customer interruptions / total number of customers

(System Average Interruption Duration Index)
SAIDI = Total number of customer hours of interruption / Total number of customers

(Customer Average Interruption Duration Index)
CAIDI = Total number of customer hours of interruption / total number of customer interruptions 

(Average System Availability Index)
ASAI = (8760 - SAIDI) / 8760

"""


@nb.jit(cache=True)
def compose_states(mttf: float, mttr: float, horizon: int, initially_working: bool = True):
    """
    Compose random states vector (on -> off -> on -> ...)
    :param mttf: Mean time to failure (h)
    :param mttr: Mean time to recovery (h)
    :param horizon: Time horizon (h)
    :param initially_working: is the component initially working?
    :return: Vector of states (size horizon) [1: on, 0: off]
    """
    n_failures = 0
    active = np.zeros(int(horizon), dtype=nb.bool)

    if mttf == 0:
        return np.ones(int(horizon), dtype=nb.bool), n_failures

    if mttr == 0:
        return np.ones(int(horizon), dtype=nb.bool), n_failures

    if initially_working:
        # If it's working, first we simulate the failure, then the recovery
        factor_1 = mttf
        factor_2 = mttr
    else:
        # If it's not working, first we simulate the recovery, then the failure
        factor_1 = mttr
        factor_2 = mttf

    a: int = 0
    b: int = 0

    while b < horizon:

        # simulate failure
        duration = int(- mttf * np.log(np.random.rand()))
        b = a + duration
        if b > horizon:
            active[a:horizon] = 1
            return active, n_failures
        else:
            active[a:b] = 1
        a = b

        # simulate recovery
        duration = int(- mttr * np.log(np.random.rand()))
        b = a + duration
        if b > horizon:
            active[a:horizon] = 0
            n_failures += 1
            return active, n_failures
        else:
            active[a:b] = 0
            n_failures += 1

        a = b

    return active, n_failures


@nb.jit(cache=True)
def generate_states_matrix(mttf: Vec, mttr: Vec, horizon: int, initially_working: bool = True):
    """
    Generate random states vector (on -> off -> on -> ...)
    :param mttf: Vector of Mean time to failure (h)
    :param mttr: Vector of Mean time to recovery (h)
    :param horizon: Time horizon (h)
    :param initially_working: is the component initially working?
    :return: matrix of states (size horizon, size mttf) [1: on, 0: off]
    """
    assert len(mttf) == len(mttr)

    n_elm = len(mttf)
    n_failures = 0
    states = np.empty((horizon, n_elm), dtype=nb.bool)

    for k in range(n_elm):
        states[:, k], n_fail = compose_states(mttf[k], mttr[k], horizon, initially_working)
        n_failures += n_fail

    return states, n_failures


@nb.jit(cache=True)
def find_different_states(mat1: IntMat, mat2: IntMat):
    """
    Find different states
    :param mat1: Matrix 1 of states
    :param mat2: Matrix 1 of states
    :return: Array of states
    """
    assert mat1.shape == mat2.shape
    keep = np.zeros(mat1.shape[0], dtype=nb.bool)
    count = 0

    for t in range(mat1.shape[0]):
        diff = False
        k = 0
        while k < mat1.shape[1] and not diff:
            if mat1[t, k] != mat2[t, k]:
                diff = True
            k += 1

        if diff:
            keep[t] = True
            count += 1

    states = np.empty(count, dtype=nb.int64)
    n = 0
    for i, val in enumerate(keep):
        if val:
            states[n] = i
            n += 1

    return states


@nb.jit()
def find_time_blocks(horizon: int, all_actives: IntMat):
    """
    Get the contigous time blocks of failure
    :param horizon: number of time steps (ntime)
    :param all_actives: matrix of active states (ntime, n_device)
    :return:
    """
    blocks = list()
    idx_list = list()
    for tidx in range(horizon):

        val = all_actives[tidx, :].sum()

        if val != all_actives.shape[1]:
            # there is at least one failure
            idx_list.append(tidx)
        else:
            # there is no failure
            if len(idx_list) > 0:
                blocks.append(idx_list.copy())
                idx_list.clear()
    return blocks


@nb.jit(cache=True)
def compute_loss_of_load_because_of_lack_of_generation(gen_pmax: Mat, load: Mat, dt: Vec):
    """
    Compute the loss of load because of lack of generation
    :param gen_pmax: Matrix of available generation (MW)
    :param load: Matrix of load (MW)
    :param dt: Time step array (h)
    :return: loss of load values in MWh
    """
    assert gen_pmax.shape[0] == load.shape[0]

    nt = gen_pmax.shape[0]
    load_lost = 0
    for t in range(nt):
        max_gen_t = gen_pmax[t, :].sum()
        total_load_t = load[t, :].sum()

        if total_load_t > max_gen_t:
            load_lost += dt[t] * (total_load_t - max_gen_t)

    return load_lost


@nb.jit(cache=True, parallel=True)
def reliability_simulation(n_sim: int,
                           load_profile: Mat,

                           gen_profile: Mat,
                           gen_p_max: Mat,
                           gen_p_min: Mat,
                           gen_dispatchable: Mat,
                           gen_active: Mat,
                           gen_cost: Mat,
                           gen_mttf: Vec,
                           gen_mttr: Vec,

                           batt_active: Mat,
                           batt_p_max_charge: Mat,
                           batt_p_max_discharge: Mat,
                           batt_energy_max: Mat,
                           batt_eff_charge: Mat,
                           batt_eff_discharge: Mat,
                           batt_cost: Mat,
                           batt_soc0: Vec,
                           batt_soc_min: Vec,

                           dt: Vec,
                           force_charge_if_low: bool = True,
                           tol=1e-6):
    """

    :param n_sim:
    :param load_profile:
    :param gen_profile:
    :param gen_p_max:
    :param gen_p_min:
    :param gen_dispatchable:
    :param gen_active:
    :param gen_cost:
    :param gen_mttf:
    :param gen_mttr:
    :param batt_active:
    :param batt_p_max_charge:
    :param batt_p_max_discharge:
    :param batt_energy_max:
    :param batt_eff_charge:
    :param batt_eff_discharge:
    :param batt_soc0:
    :param batt_soc_min:
    :param batt_cost:
    :param dt:
    :param force_charge_if_low:
    :param tol:
    :return:
    """
    lole_arr = np.zeros(n_sim)
    total_cost_arr = np.zeros(n_sim)
    curtailment_arr = np.zeros(n_sim)
    for sim_idx in nb.prange(n_sim):
        simulated_gen_actives, n_failures = generate_states_matrix(mttf=gen_mttf,
                                                                   mttr=gen_mttr,
                                                                   horizon=len(dt),
                                                                   initially_working=False)

        if n_failures:
            simulated_gen_active = gen_active * simulated_gen_actives
            simulated_gen_max = gen_p_max * simulated_gen_active
            simulated_gen_min = gen_p_min * simulated_gen_active

            # lole[sim_idx] = compute_loss_of_load_because_of_lack_of_generation(gen_pmax=simulated_gen_max,
            #                                                                    load=load_p,
            #                                                                    dt=dt)

            (gen_dispatch, batt_dispatch,
             batt_energy, total_cost,
             load_not_supplied, load_shedding,
             ndg_surplus_after_batt,
             ndg_curtailment_per_gen) = greedy_dispatch2(
                load_profile=load_profile,
                gen_profile=gen_profile,
                gen_p_max=simulated_gen_max,
                gen_p_min=simulated_gen_min,
                gen_dispatchable=gen_dispatchable,
                gen_active=simulated_gen_active,
                gen_cost=gen_cost,
                batt_active=batt_active,
                batt_p_max_charge=batt_p_max_charge,
                batt_p_max_discharge=batt_p_max_discharge,
                batt_energy_max=batt_energy_max,
                batt_eff_charge=batt_eff_charge,
                batt_eff_discharge=batt_eff_discharge,
                batt_cost=batt_cost,
                batt_soc0=batt_soc0,
                batt_soc_min=batt_soc_min,
                dt=dt,
                force_charge_if_low=force_charge_if_low,
                tol=tol
            )

            lole_arr[sim_idx] = np.sum(load_not_supplied)
            total_cost_arr[sim_idx] = total_cost
            curtailment_arr[sim_idx] = np.sum(ndg_surplus_after_batt)

    return lole_arr, total_cost_arr, curtailment_arr


@nb.jit(cache=True, parallel=True)
def reliability_grid_simulation(nc,
                                grid,
                                n_sim: int,
                                branch_mttf: Vec,
                                branch_mttr: Vec,
                                dt: Vec,
                                tol=1e-6):
    """

    :param n_sim:
    :param gen_mttf:
    :param gen_mttr:
    :param dt:
    :param tol:
    :return:
    """
    lole_arr = np.zeros(n_sim)

    power_not_supplied = 0
    n_hours_not_supplied = 0

    for sim_idx in nb.prange(n_sim):
        simulated_branch_actives, n_failures = generate_states_matrix(mttf=branch_mttf,
                                                                      mttr=branch_mttr,
                                                                      horizon=len(dt),
                                                                      initially_working=False)

        if n_failures:

            time_failures = np.sum(simulated_branch_actives, axis=0)

            for i in range(len(nc.passive)):
                grid.lines[i].active_prof = simulated_branch_actives[i, :]

            for k, value in time_failures:

                if value > 0:

                    opf_options = vge.OptimalPowerFlowOptions(ips_tolerance=tol)
                    opf_driver = vge.OptimalPowerFlowTimeSeriesDriver(grid=grid, options=opf_options, time_indices=k)
                    opf_driver.run()

                    branch_loading = opf_driver.results.loading

                    if np.any(branch_loading > 1.1):
                        n_hours_not_supplied += 1
                        power_not_supplied += sum(grid.loads.P for load in grid.loads if load.active)

                    lole_arr[sim_idx] = np.sum(power_not_supplied)

    return lole_arr, n_hours_not_supplied
