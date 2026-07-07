# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import numba as nb
from typing import Optional, Tuple, Union
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Topology.admittance_matrices import AdmittanceMatrices, AdmittanceMatricesFast
from VeraGridEngine.enumerations import BusMode, ShuntControlMode, GeneratorControlMode
from VeraGridEngine.basic_structures import Vec, IntVec, CxVec


def get_q_increment(V1, V2, k):
    """
    Logistic function to get the Q increment gain using the difference
    between the current voltage (V1) and the target voltage (V2).

    The gain varies between 0 (at V1 = V2) and inf (at V2 - V1 = inf).

    The default steepness factor k was set through trial an error. Other values may
    be specified as a :ref:`PowerFlowOptions<pf_options>`.

    Arguments:

        **V1** (float): Current voltage

        **V2** (float): Target voltage

        **k** (float, 30): Steepness factor

    Returns:

        Q increment gain
    """

    return 2 * (1 / (1 + np.exp(-k * np.abs(V2 - V1))) - 0.5)


def control_q_direct(V, Vm, Vset, Q, Qmax, Qmin, types, original_types, verbose=False):
    """
    Change the buses type in order to control the generators reactive power.
    :param V: Array of complex voltages
    :param Vm: Array of voltage modules (for speed)
    :param Vset: array of voltage Set points
    :param Q: Array of reactive power values per bus
    :param Qmax: Array of Qmax per bus
    :param Qmin: Array of Qmin per bus
    :param types: Array of bus types
    :param original_types: Array of original bus types
    :param verbose: More info?
    :return:
            **Vnew** (list): New voltage values

            **Qnew** (list): New reactive power values

            **types_new** (list): Modified types array

            **any_control_issue** (bool): Was there any control issue?
    """

    """
    Logic:

    ON PV-PQ BUS TYPE SWITCHING LOGIC IN POWER FLOW COMPUTATION
    Jinquan Zhao

    1) Bus i is a PQ bus in the previous iteration and its
       reactive power was fixed at its lower limit:

        If its voltage magnitude Vi ≥ Viset, then

            it is still a PQ bus at current iteration and set Qi = Qimin .

            If Vi < Viset , then

                compare Qi with the upper and lower limits.

                If Qi ≥ Qimax , then
                    it is still a PQ bus but set Qi = Qimax .
                If Qi ≤ Qimin , then
                    it is still a PQ bus and set Qi = Qimin .
                If Qimin < Qi < Qi max , then
                    it is switched to PV bus, set Vinew = Viset.

    2) Bus i is a PQ bus in the previous iteration and
       its reactive power was fixed at its upper limit:

        If its voltage magnitude Vi ≤ Viset , then:
            bus i still a PQ bus and set Q i = Q i max.

            If Vi > Viset , then

                Compare between Qi and its upper/lower limits

                If Qi ≥ Qimax , then
                    it is still a PQ bus and set Q i = Qimax .
                If Qi ≤ Qimin , then
                    it is still a PQ bus but let Qi = Qimin in current iteration.
                If Qimin < Qi < Qimax , then
                    it is switched to PV bus and set Vinew = Viset

    3) Bus i is a PV bus in the previous iteration.

        Compare Q i with its upper and lower limits.

        If Qi ≥ Qimax , then
            it is switched to PQ and set Qi = Qimax .
        If Qi ≤ Qimin , then
            it is switched to PQ and set Qi = Qimin .
        If Qi min < Qi < Qimax , then
            it is still a PV bus.
    """

    if verbose:
        print('Q control logic (fast)')

    n = len(V)
    Qnew = Q.copy()
    Vnew = V.copy()
    types_new = types.copy()
    any_control_issue = False

    for i in range(n):

        if types[i] == BusMode.Slack_tpe.value:
            pass

        elif types[i] == BusMode.PQ_tpe.value and original_types[i] == BusMode.PV_tpe.value:

            if Vm[i] != Vset[i]:

                if Q[i] >= Qmax[i]:  # it is still a PQ bus but set Q = Qmax .
                    Qnew[i] = Qmax[i]

                elif Q[i] <= Qmin[i]:  # it is still a PQ bus and set Q = Qmin .
                    Qnew[i] = Qmin[i]

                else:  # switch back to PV, set Vnew = Vset.

                    types_new[i] = BusMode.PV_tpe.value
                    Vnew[i] = complex(Vset[i], 0)

                    if verbose:
                        print('Bus', i, 'switched back to PV')

                any_control_issue = True

            else:
                pass  # The voltages are equal

        elif types[i] == BusMode.PV_tpe.value:

            if Q[i] >= Qmax[i]:  # it is switched to PQ and set Q = Qmax .

                types_new[i] = BusMode.PQ_tpe.value
                Qnew[i] = Qmax[i]
                any_control_issue = True

                if verbose:
                    print('Bus', i, 'switched to PQ: Q', Q[i], ' Qmax:', Qmax[i])

            elif Q[i] <= Qmin[i]:  # it is switched to PQ and set Q = Qmin .

                types_new[i] = BusMode.PQ_tpe.value
                Qnew[i] = Qmin[i]
                any_control_issue = True

                if verbose:
                    print('Bus', i, 'switched to PQ: Q', Q[i], ' Qmin:', Qmin[i])

            else:  # it is still a PV bus.
                pass

        else:
            pass

    return Vnew, Qnew, types_new, any_control_issue


@nb.njit(cache=True)
def control_q_inside_method(Scalc: CxVec, S0: CxVec,
                            pv: IntVec, pq: IntVec, pqv: IntVec, p: IntVec,
                            Qmin: Vec, Qmax: Vec):
    """
    Control of reactive power within the numerical method
    :param Scalc: Calculated power array (changed inside)
    :param S0: Specified power array (changed inside)
    :param pv: array of pv bus indices (changed inside)
    :param pq: array of pq bus indices (changed inside)
    :param pqv: array of pqv bus indices (changed inside)
    :param p: array of p bus indices (changed inside)
    :param Qmin: Array of lower reactive power limits per bus in p.u.
    :param Qmax: Array of upper reactive power limits per bus in p.u.
    :return: any change?, Scalc, Sbus, pv, pq, pqv, p
    """
    pv_indices = list()
    changed = list()
    for k, i in enumerate(pv):
        Q = Scalc[i].imag
        if Q > Qmax[i]:
            S0[i] = np.complex128(complex(S0[i].real, Qmax[i]))
            changed.append(i)
            pv_indices.append(k)
        elif Q < Qmin[i]:
            S0[i] = np.complex128(complex(S0[i].real, Qmin[i]))
            changed.append(i)
            pv_indices.append(k)

    if len(changed) > 0:
        # convert PV nodes to PQ
        pq_new = np.array(changed)
        pq = np.concatenate((pq, pq_new))
        pv = np.delete(pv, pv_indices)
        pq.sort()

    return changed, pv, pq, pqv, p


@nb.njit(cache=True)
def control_discrete_shunts(Vm: Vec,
                            shunt_discrete_ctrl_idx: IntVec,
                            shunt_discrete_bus_idx: IntVec,
                            shunt_discrete_vmax: Vec,
                            shunt_discrete_vmin: Vec,
                            shunt_step: IntVec,
                            shunt_g_steps: np.ndarray,
                            shunt_b_steps: np.ndarray,
                            shunt_n_steps: IntVec,
                            sbase: float):
    """
    Control discrete shunts within the numerical method.
    The sparse Ybus diagonal update is returned to the caller and applied outside numba.
    :param Vm: Voltage module array.
    :param shunt_discrete_ctrl_idx: Array of controlled shunt indices in the full shunt arrays.
    :param shunt_discrete_bus_idx: Array of bus indices for the controlled shunts.
    :param shunt_discrete_vmax: Array of upper voltage bounds for the controlled shunts.
    :param shunt_discrete_vmin: Array of lower voltage bounds for the controlled shunts.
    :param shunt_step: Array of current shunt steps in the full shunt arrays (changed inside).
    :param shunt_g_steps: Packed cumulative G steps for the controlled shunts.
    :param shunt_b_steps: Packed cumulative B steps for the controlled shunts.
    :param shunt_n_steps: Number of valid steps for each controlled shunt.
    :param sbase: Base power.
    :return: changed bus indices, Ybus diagonal increments, number of changed shunts.
    """
    n_ctrl = len(shunt_discrete_ctrl_idx)
    changed_bus_idx = np.empty(n_ctrl, dtype=np.int64)
    changed_delta_y = np.empty(n_ctrl, dtype=np.complex128)
    n_changed = 0

    for ctrl_k, sh_i in enumerate(shunt_discrete_ctrl_idx):
        bus_i = shunt_discrete_bus_idx[ctrl_k]
        step_i = shunt_step[sh_i]

        if Vm[bus_i] > shunt_discrete_vmax[ctrl_k]:
            # decrease B
            if step_i > 0:
                prev_g = shunt_g_steps[ctrl_k, step_i] / sbase
                prev_b = shunt_b_steps[ctrl_k, step_i] / sbase
                step_i -= 1
                shunt_step[sh_i] = step_i
                g = prev_g - shunt_g_steps[ctrl_k, step_i] / sbase
                b = prev_b - shunt_b_steps[ctrl_k, step_i] / sbase
                changed_bus_idx[n_changed] = bus_i
                changed_delta_y[n_changed] = np.complex128(complex(g, b) - complex(prev_g, prev_b))
                n_changed += 1

        elif Vm[bus_i] < shunt_discrete_vmin[ctrl_k]:
            # increase B
            if step_i < (shunt_n_steps[ctrl_k] - 1):
                prev_g = shunt_g_steps[ctrl_k, step_i] / sbase
                prev_b = shunt_b_steps[ctrl_k, step_i] / sbase
                step_i += 1
                shunt_step[sh_i] = step_i
                g = prev_g + shunt_g_steps[ctrl_k, step_i] / sbase
                b = prev_b + shunt_b_steps[ctrl_k, step_i] / sbase
                changed_bus_idx[n_changed] = bus_i
                changed_delta_y[n_changed] = np.complex128(complex(g, b) - complex(prev_g, prev_b))
                n_changed += 1

        else:
            # within boundaries
            pass

    return changed_bus_idx, changed_delta_y, n_changed


@nb.njit()
def control_q_for_generalized_method(Scalc: CxVec, S0: CxVec,
                                     pv: IntVec, i_u_vm: IntVec, i_k_q: IntVec,
                                     Qmin: Vec, Qmax: Vec):
    """
    Control of reactive power within the numerical method
    Assume we only want to change regular PV buses to PQ buses (as in the conventional method)
    :param Scalc: Calculated power array (changed inside)
    :param S0: Specified power array (changed inside)
    :param pv: array of pv bus indices (changed inside)
    :param i_u_vm: array of buses with unknown Vm (changed inside)
    :param i_k_q: array of buses with known Q (changed inside)
    :param Qmin: Array of lower bus reactive power limits per bus in p.u.
    :param Qmax: Array of upper bus reactive power limits per bus in p.u.
    :return: list of changed buses, i_u_vm, i_k_q
    """
    changed = list()

    for k, i in enumerate(pv):
        Q = Scalc[i].imag
        if Q > Qmax[i]:
            S0[i] = np.complex128(complex(S0[i].real, Qmax[i]))
            changed.append(i)
        elif Q < Qmin[i]:
            S0[i] = np.complex128(complex(S0[i].real, Qmin[i]))
            changed.append(i)

    if len(changed) > 0:
        # convert PV nodes to PQ
        # we are able to avoid deletions
        vm_to_q = np.array(changed)
        i_k_q = np.concatenate((i_k_q, vm_to_q))
        i_u_vm = np.concatenate((i_u_vm, vm_to_q))
        i_k_q.sort()
        i_u_vm.sort()

    return changed, i_u_vm, i_k_q


@nb.njit(cache=True)
def update_qv_droop_generators(S0: CxVec,
                               Q0: Vec,
                               generator_q: Vec,
                               qv_droop_bus_idx: IntVec,
                               qv_droop_gen_idx: IntVec,
                               generator_bus_idx: IntVec,
                               generator_k_droop: Vec,
                               generator_dead_band: Vec,
                               generator_v: Vec,
                               generator_qmin: Vec,
                               generator_qmax: Vec,
                               Vm: Vec) -> bool:
    """
    Update generators with QV droop control within the numerical method.
    :param S0: Specified power array (changed inside).
    :param Q0: Initial specified reactive power per bus.
    :param generator_q: Reactive power per generator (changed inside).
    :param qv_droop_bus_idx: Buses hosting QV droop generators.
    :param qv_droop_gen_idx: Generator indices with QV droop control.
    :param generator_bus_idx: Generator-to-bus map.
    :param generator_k_droop: Generator droop gain.
    :param generator_dead_band: Generator dead-band.
    :param generator_v: Generator voltage set point.
    :param generator_qmax: Generator reactive power upper limit (p.u.).
    :param generator_qmin: Generator reactive power lower limit (p.u.).
    :param Vm: Voltage module array.
    :return: Was there any change?
    """
    any_change = False

    # initialize
    S0.imag[qv_droop_bus_idx] = Q0[qv_droop_bus_idx]

    for k in qv_droop_gen_idx:
        bus_i = generator_bus_idx[k]
        k_droop = generator_k_droop[k]
        db = generator_dead_band[k]
        dV = generator_v[k] - Vm[bus_i]

        if abs(dV) > db:
            if dV > db:
                any_change = True
                generator_q[k] = (dV - db) * k_droop * generator_qmax[k]

                if generator_q[k] > generator_qmax[k]:
                    generator_q[k] = generator_qmax[k]

                if generator_q[k] < generator_qmin[k]:
                    generator_q[k] = generator_qmin[k]

                S0.imag[bus_i] += generator_q[k]
            elif dV < -db:
                any_change = True
                generator_q[k] = (dV + db) * k_droop * generator_qmax[k]

                if generator_q[k] > generator_qmax[k]:
                    generator_q[k] = generator_qmax[k]

                if generator_q[k] < generator_qmin[k]:
                    generator_q[k] = generator_qmin[k]

                S0.imag[bus_i] += generator_q[k]
            else:
                pass
        else:
            pass

    return any_change


class DiscreteShuntControlState:
    """
    Python-side state holder for discrete shunt controls.

    The packed arrays owned by this class are consumed by the Numba kernel so
    the formulations only need to keep a lightweight wrapper object.
    """
    __slots__ = (
        "_sbase",
        "_shunt_discrete_ctrl_idx",
        "_shunt_step",
        "_shunt_discrete_bus_idx",
        "_shunt_discrete_vmax",
        "_shunt_discrete_vmin",
        "_shunt_g_steps",
        "_shunt_b_steps",
        "_shunt_n_steps",
    )

    def __init__(self, nc: NumericalCircuit) -> None:
        """
        Build the discrete shunt control state.

        :param nc: Numerical circuit hosting the shunt control data.
        """
        max_shunt_steps: int
        n_discrete_shunts: int
        sh_i: int
        k: int
        g_steps: IntVec
        b_steps: IntVec
        n_steps: int

        # Store the base power once because all shunt increments are normalized by it.
        self._sbase = nc.Sbase

        # Select only the shunts that participate in discrete control.
        self._shunt_discrete_ctrl_idx = np.where(
            nc.shunt_data.control_mode_int == ShuntControlMode.Discrete.idx()
        )[0]

        # Copy the mutable step vector so the solver state remains local to the formulation.
        self._shunt_step = nc.shunt_data.step.copy()
        self._shunt_discrete_bus_idx = nc.shunt_data.bus_idx[self._shunt_discrete_ctrl_idx].copy()
        self._shunt_discrete_vmax = nc.shunt_data.vmax[self._shunt_discrete_ctrl_idx].copy()
        self._shunt_discrete_vmin = nc.shunt_data.vmin[self._shunt_discrete_ctrl_idx].copy()

        # Pack the ragged cumulative shunt step arrays into a dense layout once
        # so the compiled kernel never touches Python objects during the solve.
        max_shunt_steps = 0
        for sh_i in self._shunt_discrete_ctrl_idx:
            max_shunt_steps = max(max_shunt_steps, len(nc.shunt_data.b_steps[sh_i]))
        else:
            pass

        n_discrete_shunts = len(self._shunt_discrete_ctrl_idx)
        self._shunt_g_steps = np.zeros((n_discrete_shunts, max_shunt_steps), dtype=float)
        self._shunt_b_steps = np.zeros((n_discrete_shunts, max_shunt_steps), dtype=float)
        self._shunt_n_steps = np.zeros(n_discrete_shunts, dtype=int)

        for k, sh_i in enumerate(self._shunt_discrete_ctrl_idx):
            g_steps = nc.shunt_data.g_steps[sh_i]
            b_steps = nc.shunt_data.b_steps[sh_i]
            n_steps = len(b_steps)
            self._shunt_g_steps[k, :n_steps] = g_steps
            self._shunt_b_steps[k, :n_steps] = b_steps
            self._shunt_n_steps[k] = n_steps
        else:
            pass

    def get_shunt_step(self) -> IntVec:
        """
        Get the mutable shunt step vector.

        :return: Current discrete shunt step vector.
        """
        return self._shunt_step

    def apply(self,
              Vm: Vec,
              adm: Union[AdmittanceMatrices, AdmittanceMatricesFast],
              yshunt_bus: Optional[CxVec] = None) -> bool:
        """
        Apply one discrete shunt control step.

        :param Vm: Voltage magnitude vector.
        :param adm: Admittance container updated in place.
        :param yshunt_bus: Optional external shunt-bus vector that must remain
                           synchronized with ``adm.Yshunt_bus``.
        :return: ``True`` if any discrete shunt changed state, ``False`` otherwise.
        """
        changed_bus_idx: IntVec
        changed_delta_y: CxVec
        n_changed: int
        k: int
        bus_i: int
        delta_y: np.complex128

        # Evaluate the compiled control law on the packed control arrays.
        changed_bus_idx, changed_delta_y, n_changed = control_discrete_shunts(
            Vm=Vm,
            shunt_discrete_ctrl_idx=self._shunt_discrete_ctrl_idx,
            shunt_discrete_bus_idx=self._shunt_discrete_bus_idx,
            shunt_discrete_vmax=self._shunt_discrete_vmax,
            shunt_discrete_vmin=self._shunt_discrete_vmin,
            shunt_step=self._shunt_step,
            shunt_g_steps=self._shunt_g_steps,
            shunt_b_steps=self._shunt_b_steps,
            shunt_n_steps=self._shunt_n_steps,
            sbase=self._sbase
        )

        if yshunt_bus is None:
            yshunt_bus = adm.Yshunt_bus
        else:
            pass

        # Propagate every shunt increment to all admittance storages that must
        # stay synchronized across later fast updates or full rebuilds.
        for k in range(n_changed):
            bus_i = changed_bus_idx[k]
            delta_y = changed_delta_y[k]
            yshunt_bus[bus_i] += delta_y
            if yshunt_bus is not adm.Yshunt_bus:
                adm.Yshunt_bus[bus_i] += delta_y
            else:
                pass
            adm.Ybus[bus_i, bus_i] += delta_y
        else:
            pass

        return n_changed > 0


class QvDroopControlState:
    """
    Python-side state holder for generator QV droop controls.

    The arrays are allocated once and the numerical update remains delegated to
    the Numba kernel.
    """
    __slots__ = (
        "_Q0",
        "_generator_q",
        "_qv_droop_gen_idx",
        "_qv_droop_bus_idx",
        "_generator_bus_idx",
        "_generator_k_droop",
        "_generator_dead_band",
        "_generator_v",
        "_generator_qmax",
        "_generator_qmin",
        "_sbase",
    )

    def __init__(self, S0: CxVec, nc: NumericalCircuit) -> None:
        """
        Build the QV droop control state.

        :param S0: Initial specified bus power.
        :param nc: Numerical circuit hosting the generator control data.
        """
        # Copy the initial reactive schedules because the droop update resets
        # the controlled buses to that baseline on every control pass.
        self._Q0 = S0.imag.copy()
        self._generator_q = nc.generator_data.q.copy()
        self._qv_droop_gen_idx = np.where(
            nc.generator_data.control_mode_int == GeneratorControlMode.QVDroop.idx()
        )[0]
        self._qv_droop_bus_idx = np.unique(nc.generator_data.bus_idx[self._qv_droop_gen_idx])
        self._generator_bus_idx = nc.generator_data.bus_idx
        self._generator_k_droop = nc.generator_data.k_droop
        self._generator_dead_band = nc.generator_data.dead_band
        self._generator_v = nc.generator_data.v
        self._generator_qmin: Vec = nc.generator_data.qmin / nc.Sbase
        self._generator_qmax: Vec = nc.generator_data.qmax / nc.Sbase
        self._sbase = nc.Sbase

    def get_generator_q(self) -> Vec:
        """
        Get the per-generator reactive power buffer.

        :return: Generator reactive power vector.
        """
        return self._generator_q

    def apply(self, S0: CxVec, Vm: Vec) -> bool:
        """
        Apply one QV droop control step.

        :param S0: Specified bus power updated in place.
        :param Vm: Voltage magnitude vector.
        :return: ``True`` if any droop generator changed, ``False`` otherwise.
        """
        return update_qv_droop_generators(
            S0=S0,
            Q0=self._Q0,
            generator_q=self._generator_q,
            qv_droop_bus_idx=self._qv_droop_bus_idx,
            qv_droop_gen_idx=self._qv_droop_gen_idx,
            generator_bus_idx=self._generator_bus_idx,
            generator_k_droop=self._generator_k_droop,
            generator_dead_band=self._generator_dead_band,
            generator_v=self._generator_v,
            generator_qmin=self._generator_qmin,
            generator_qmax=self._generator_qmax,
            Vm=Vm
        )


def compute_slack_distribution(Scalc: CxVec, vd: IntVec, bus_installed_power: Vec) -> Tuple[bool, Vec]:
    """
    Slack distribution logic
    :param Scalc: Computed power array
    :param vd: slack indices
    :param bus_installed_power: Amount of installed power
    :return: is slack division possible?
    """
    # Distribute the slack power
    slack_power = Scalc[vd].real.sum()
    total_installed_power = bus_installed_power.sum()

    if total_installed_power > 0.0:
        delta = slack_power * bus_installed_power / total_installed_power
        ok = True
    else:
        delta = np.zeros(len(Scalc))
        ok = False

    return ok, delta
