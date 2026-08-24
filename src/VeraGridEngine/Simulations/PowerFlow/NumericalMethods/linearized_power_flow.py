# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

import time
import warnings
import scipy.sparse as sp
import numpy as np
from scipy.sparse.csgraph import connected_components
from typing import List, Tuple

from VeraGridEngine.Utils.NumericalMethods.sparse_solve import get_sparse_type, get_linear_solver
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import NumericPowerFlowResults
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
import VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions as cf
from VeraGridEngine.basic_structures import CxVec, Vec, IntVec, BoolVec, CscMat, Logger
from VeraGridEngine.enumerations import ConverterControlType

linear_solver = get_linear_solver()
sparse = get_sparse_type()


def linear_pf(nc: NumericalCircuit,
              Ybus: sp.csc_matrix, Bpqpv: sp.csc_matrix, Bref: sp.csc_matrix, Bf: sp.csc_matrix,
              S0: CxVec, I0: CxVec, Y0: CxVec, V0: CxVec, tau: Vec,
              vd: IntVec, no_slack: IntVec, pq: IntVec, pv: IntVec) -> NumericPowerFlowResults:
    """
    Solves a linear-DC power flow.
    :param nc: NumericalCircuit instance
    :param Ybus: Normal circuit admittance matrix
    :param Bpqpv: Susceptance matrix reduced
    :param Bref: Susceptance matrix sliced for the slack node
    :param Bf: Susceptance matrix of the Branches to nodes (used to include the phase shifters)
    :param S0: Complex power Injections at all the nodes
    :param I0: Complex current Injections at all the nodes
    :param Y0: Complex admittance Injections at all the nodes
    :param V0: Array of complex seed voltage (it contains the ref voltages)
    :param tau: Array of branch angles
    :param vd: array of the indices of the slack nodes
    :param no_slack: array of the indices of the non-slack nodes
    :param pq: array of the indices of the pq nodes
    :param pv: array of the indices of the pv nodes
    :return: NumericPowerFlowResults instance
    """

    start = time.time()
    npq = len(pq)
    npv = len(pv)
    if (npq + npv) > 0:
        # Decompose the voltage in angle and magnitude
        Va_ref = np.angle(V0[vd])  # we only need the angles at the slack nodes
        Vm = np.abs(V0)

        # initialize result vector
        Va = np.empty(len(V0))

        # Compute the power injection at the flat voltage this model assumes. 
        # Evaluating the ZIP at the seeded voltages would mix unused input data with a
        # model that treats every magnitude as 1 p.u. everywhere else.
        Sbus = cf.compute_zip_power(S0, I0, Y0, np.ones_like(Vm))

        # compose the reduced power injections (Pinj)
        # Since we have removed the slack nodes, we must account their influence as Injections Bref * Va_ref
        # We also need to account for the effect of the phase shifters (Pps)
        Pps = Bf.T @ tau
        Pinj = Sbus[no_slack].real - (Bref @ Va_ref) * Vm[no_slack] + Pps[no_slack]  # TODO: add G from shunts

        # update angles for non-reference buses
        Va[no_slack] = linear_solver(Bpqpv, Pinj)
        Va[vd] = Va_ref

        # re assemble the voltage
        V = cf.polar_to_rect(Vm, Va)

        # compute the calculated power injection and the error of the voltage solution
        Scalc = cf.compute_power(Ybus, V)

        # compute the power mismatch between the specified power Sbus and the calculated power Scalc
        mismatch = cf.compute_fx(Scalc, S0, no_slack, pq)

        # check for convergence
        norm_f = np.linalg.norm(mismatch, np.inf)
    else:
        norm_f = 0.0
        V = V0
        Scalc = cf.compute_power(Ybus, V)

    end = time.time()
    elapsed = end - start

    Sf, St, If, It, Vbranch, loading, losses, Sbus = cf.power_flow_post_process_linear(
        Sbus=Scalc,
        V=V,
        active=nc.passive_branch_data.active,
        X=nc.passive_branch_data.X,
        tap_module=nc.active_branch_data.tap_module,
        tap_angle=nc.active_branch_data.tap_angle,
        F=nc.passive_branch_data.F,
        T=nc.passive_branch_data.T,
        branch_rates=nc.passive_branch_data.rates,
        Sbase=nc.Sbase
    )

    return NumericPowerFlowResults(V=V,
                                   Scalc=Scalc * nc.Sbase,
                                   m=np.ones(nc.nbr, dtype=float),
                                   tau=np.zeros(nc.nbr, dtype=float),
                                   Sf=Sf,
                                   St=St,
                                   If=If,
                                   It=It,
                                   loading=loading,
                                   losses=losses,
                                   Pfp_vsc=np.zeros(nc.nvsc, dtype=float),
                                   Pfn_vsc=np.zeros(nc.nvsc, dtype=float),
                                   St_vsc=np.zeros(nc.nvsc, dtype=complex),
                                   If_vsc=np.zeros(nc.nvsc, dtype=float),
                                   It_vsc=np.zeros(nc.nvsc, dtype=complex),
                                   losses_vsc=np.zeros(nc.nvsc, dtype=float),
                                   loading_vsc=np.zeros(nc.nvsc, dtype=float),
                                   Sf_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                   St_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                   losses_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                   loading_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                   norm_f=norm_f,
                                   converged=True,
                                   iterations=1,
                                   elapsed=elapsed)


class VscLinearModel:
    """
    Linear (DC) representation of the VSC converters.

    A converter moves power from its DC bus to its AC bus, and how much it moves is decided
    by its control mode, never by an impedance. Three behaviours cover every mode:

    - scheduled: it holds a P_dc or P_ac set point
    - droop (P-mode 3): it follows ``P = P0 + k · (theta_ctrl - theta_ac)``
    - DC slack: it controls the DC voltage, so it has no schedule of its own and instead
      closes the power balance of its DC subgrid.
    """

    __slots__ = ("is_droop", "is_dc_slack", "p_set", "k_droop", "ctrl_bus", "dc_island")

    def __init__(self, n_vsc: int):
        """
        Constructor

        :param n_vsc: number of converters
        """
        self.is_droop: BoolVec = np.zeros(n_vsc, dtype=bool)
        self.is_dc_slack: BoolVec = np.zeros(n_vsc, dtype=bool)
        self.p_set: Vec = np.zeros(n_vsc, dtype=float)  # p.u. (droop base power for droop converters)
        self.k_droop: Vec = np.zeros(n_vsc, dtype=float)  # p.u./rad
        self.ctrl_bus: IntVec = np.full(n_vsc, -1, dtype=int)
        self.dc_island: IntVec = np.zeros(n_vsc, dtype=int)


def build_vsc_linear_model(nc: NumericalCircuit) -> VscLinearModel:
    """
    Classify every converter for the linear power flow and label the DC subgrid it belongs
    to, so that the converter that fixes the DC voltage can later close that subgrid's
    power balance.

    :param nc: NumericalCircuit
    :return: VscLinearModel
    """
    model = VscLinearModel(n_vsc=nc.vsc_data.nelm)

    if nc.vsc_data.nelm == 0:
        return model
    else:
        pass  # there are converters to classify

    # label the DC subgrids through the DC branches
    dc_adjacency = sp.lil_matrix((nc.nbus, nc.nbus))
    for k in range(nc.nbr):
        f = int(nc.passive_branch_data.F[k])
        t = int(nc.passive_branch_data.T[k])
        if nc.passive_branch_data.active[k] and nc.bus_data.is_dc[f] and nc.bus_data.is_dc[t]:
            dc_adjacency[f, t] = 1.0
            dc_adjacency[t, f] = 1.0
        else:
            pass  # not an active DC branch
    n_dc_islands, dc_label = connected_components(dc_adjacency.tocsr(), directed=False)

    droop_code = ConverterControlType.Pdc_angle_droop.idx()
    vm_dc_code = ConverterControlType.Vm_dc.idx()
    pdc_code = ConverterControlType.Pdc.idx()
    pac_code = ConverterControlType.Pac.idx()

    for m in range(nc.vsc_data.nelm):

        model.dc_island[m] = int(dc_label[int(nc.vsc_data.F[m])])
        c1 = nc.vsc_data.control1_int[m]
        c2 = nc.vsc_data.control2_int[m]

        if not nc.vsc_data.active[m]:
            pass  # an inactive converter moves no power

        elif c1 == droop_code or c2 == droop_code:
            # P-mode 3: the droop constant is given in MW/deg and is needed in p.u./rad.
            model.is_droop[m] = True
            model.k_droop[m] = float(nc.vsc_data.control1_val[m]) * 57.295779513 / nc.Sbase
            model.p_set[m] = -float(nc.vsc_data.control2_val[m]) / nc.Sbase
            model.ctrl_bus[m] = int(nc.vsc_data.control1_bus_idx[m])

        elif c1 == vm_dc_code or c2 == vm_dc_code:
            # it fixes the DC voltage, so it closes the DC balance
            model.is_dc_slack[m] = True

        else:
            # Scheduled converter. The model works with the power that leaves the DC bus
            # towards the AC bus, which is the "from" side.
            if c1 == pdc_code:
                model.p_set[m] = float(nc.vsc_data.control1_val[m]) / nc.Sbase
            elif c2 == pdc_code:
                model.p_set[m] = float(nc.vsc_data.control2_val[m]) / nc.Sbase
            elif c1 == pac_code:
                model.p_set[m] = -float(nc.vsc_data.control1_val[m]) / nc.Sbase
            elif c2 == pac_code:
                model.p_set[m] = -float(nc.vsc_data.control2_val[m]) / nc.Sbase
            else:
                model.p_set[m] = 0.0  # no power control at all, it moves nothing

    return model


def add_vsc_linear_terms(nc: NumericalCircuit,
                         model: VscLinearModel,
                         A: sp.lil_matrix,
                         pinned: Vec) -> Vec:
    """
    Add the converter behaviour to the linear (DC) power flow system.

    :param nc: NumericalCircuit
    :param model: VscLinearModel with the classification
    :param A: system matrix being mounted, modified in place
    :param pinned: per converter forced power in p.u., NaN where the converter is free.
                   A droop converter is pinned once it reaches its rating.
    :return: constant power injections caused by the converters, in p.u.
    """
    p_vsc: Vec = np.zeros(nc.nbus, dtype=float)

    for m in range(nc.vsc_data.nelm):

        if not nc.vsc_data.active[m] or model.is_dc_slack[m]:
            pass  # inactive, or the DC slack that is handled by the closure below

        else:
            fr = int(nc.vsc_data.F[m])
            to = int(nc.vsc_data.T[m])
            free_droop = (model.is_droop[m] and np.isnan(pinned[m]) and model.ctrl_bus[m] >= 0)

            if free_droop:
                ctrl = int(model.ctrl_bus[m])
                k_droop = float(model.k_droop[m])
                p0 = float(model.p_set[m])
                p_vsc[fr] -= p0
                p_vsc[to] += p0
                A[fr, ctrl] += k_droop
                A[fr, to] -= k_droop
                A[to, ctrl] -= k_droop
                A[to, to] += k_droop
            else:
                p_fixed = float(model.p_set[m]) if np.isnan(pinned[m]) else float(pinned[m])
                p_vsc[fr] -= p_fixed
                p_vsc[to] += p_fixed

    # The DC voltage controlling converter of each subgrid delivers to
    # its AC bus whatever the other converters of that same subgrid inject into the DC side
    for m_slack in range(nc.vsc_data.nelm):

        if model.is_dc_slack[m_slack] and nc.vsc_data.active[m_slack]:
            fr_slack = int(nc.vsc_data.F[m_slack])
            to_slack = int(nc.vsc_data.T[m_slack])

            for m_other in range(nc.vsc_data.nelm):

                same_island = (nc.vsc_data.active[m_other]
                               and m_other != m_slack
                               and not model.is_dc_slack[m_other]
                               and model.dc_island[m_other] == model.dc_island[m_slack])

                if same_island:
                    free_droop = (model.is_droop[m_other]
                                  and np.isnan(pinned[m_other])
                                  and model.ctrl_bus[m_other] >= 0)
                    p0 = float(model.p_set[m_other]) if np.isnan(pinned[m_other]) else float(pinned[m_other])
                    p_vsc[fr_slack] += p0
                    p_vsc[to_slack] -= p0

                    if free_droop:
                        ctrl = int(model.ctrl_bus[m_other])
                        to_other = int(nc.vsc_data.T[m_other])
                        k_droop = float(model.k_droop[m_other])
                        A[fr_slack, ctrl] -= k_droop
                        A[fr_slack, to_other] += k_droop
                        A[to_slack, ctrl] += k_droop
                        A[to_slack, to_other] -= k_droop
                    else:
                        pass  # a fixed power converter only contributes the constant part
                else:
                    pass  # a converter of another DC subgrid, or the slack itself

        else:
            pass  # not a DC voltage controlling converter

    return p_vsc


def compute_vsc_powers(nc: NumericalCircuit,
                       model: VscLinearModel,
                       va: Vec,
                       pinned: Vec) -> Vec:
    """
    Evaluate the power that every converter moves from its DC bus to its AC bus, given the
    solved bus angles.

    :param nc: NumericalCircuit
    :param model: VscLinearModel with the classification
    :param va: solved bus angles in radians
    :param pinned: per converter forced power in p.u., NaN where the converter is free
    :return: converter powers in p.u.
    """
    powers: Vec = np.zeros(nc.vsc_data.nelm, dtype=float)

    for m in range(nc.vsc_data.nelm):

        if not nc.vsc_data.active[m] or model.is_dc_slack[m]:
            pass  # the DC slack is resolved by the closure below

        elif not np.isnan(pinned[m]):
            powers[m] = float(pinned[m])

        elif model.is_droop[m] and model.ctrl_bus[m] >= 0:
            ctrl = int(model.ctrl_bus[m])
            to = int(nc.vsc_data.T[m])
            powers[m] = float(model.p_set[m]) + float(model.k_droop[m]) * (va[ctrl] - va[to])

        else:
            powers[m] = float(model.p_set[m])

    # the DC slack converter carries what the rest of its DC subgrid injects
    for m_slack in range(nc.vsc_data.nelm):
        if model.is_dc_slack[m_slack] and nc.vsc_data.active[m_slack]:
            island_total = 0.0
            for m_other in range(nc.vsc_data.nelm):
                if (nc.vsc_data.active[m_other] and m_other != m_slack
                        and not model.is_dc_slack[m_other]
                        and model.dc_island[m_other] == model.dc_island[m_slack]):
                    island_total += powers[m_other]
                else:
                    pass  # another subgrid, or the slack itself
            powers[m_slack] = -island_total
        else:
            pass  # not a DC voltage controlling converter

    return powers


def acdc_lin_pf(nc: NumericalCircuit,
                Bbus: sp.csc_matrix, Bf: sp.csc_matrix,
                Gbus: sp.csc_matrix, Gf: sp.csc_matrix,
                ac: IntVec, dc: IntVec, vd: IntVec, pv: IntVec,
                S0: CxVec, I0: CxVec, Y0: CxVec, V0: CxVec, tau: Vec) -> NumericPowerFlowResults:
    """
    Solves a linear-ACDC power flow.
    :param nc:
    :param Bbus:
    :param Bf:
    :param Gbus:
    :param Gf:
    :param ac:
    :param dc:
    :param vd:
    :param pv:
    :param S0:
    :param I0:
    :param Y0:
    :param V0:
    :param tau:
    :return:
    """

    """
    
    :param nc: NumericalCircuit instance
    :param Ybus: Normal circuit admittance matrix
    :param Bpqpv: Susceptance matrix reduced
    :param Bref: Susceptane matrix sliced for the slack node
    :param Bf: Susceptance matrix of the Branches to nodes (used to include the phase shifters)
    :param S0: Complex power Injections at all the nodes
    :param I0: Complex current Injections at all the nodes
    :param Y0: Complex admittance Injections at all the nodes
    :param V0: Array of complex seed voltage (it contains the ref voltages)
    :param tau: Array of branch angles
    :param vd: array of the indices of the slack nodes
    :param no_slack: array of the indices of the non-slack nodes
    :param pq: array of the indices of the pq nodes
    :param pv: array of the indices of the pv nodes
    :return: NumericPowerFlowResults instance
    """

    start = time.time()

    n = nc.nbus

    # Decompose the voltage in angle and magnitude
    Va = np.angle(V0)
    Vm = np.abs(V0)

    # mount the base matrix
    A = sp.lil_matrix((n, n))
    Af = sp.lil_matrix((nc.nbr, n))

    # per branch susceptance, kept to build the phase shift term of the flows later
    ys_arr: Vec = np.zeros(nc.nbr, dtype=float)

    for k in range(nc.nbr):
        f = nc.passive_branch_data.F[k]
        t = nc.passive_branch_data.T[k]

        if nc.bus_data.is_dc[f] and nc.bus_data.is_dc[t]:
            # this is a dc branch
            ys = float(nc.passive_branch_data.active[k]) / (nc.passive_branch_data.R[k] + 1e-20)

        elif not nc.bus_data.is_dc[f] and not nc.bus_data.is_dc[t]:
            # this is an ac branch
            ys = float(nc.passive_branch_data.active[k]) / (nc.passive_branch_data.X[k] + 1e-20)

        else:
            # this is an error
            raise AttributeError(f"The branch {k} is nether fully AC not fully DC :(")

        ys_arr[k] = ys
        Af[k, f] = ys
        Af[k, t] = -ys

        A[f, f] += ys
        A[f, t] -= ys
        A[t, f] -= ys
        A[t, t] += ys

    # Copy because of the droop saturation loop
    A_branches = A.copy()
    vsc_model: VscLinearModel = build_vsc_linear_model(nc=nc)
    vsc_pinned: Vec = np.full(nc.vsc_data.nelm, np.nan, dtype=float)
    p_vsc: Vec = add_vsc_linear_terms(nc=nc, model=vsc_model, A=A, pinned=vsc_pinned)

    # detect how to slice
    no_slack = list()
    dc_sl = list()
    ac_sl = list()
    for i in range(n):
        if nc.bus_data.is_dc[i]:
            if nc.bus_data.is_vm_controlled[i]:
                dc_sl.append(i)
            else:
                no_slack.append(i)
        else:
            if nc.bus_data.is_vm_controlled[i] and nc.bus_data.is_va_controlled[i]:
                ac_sl.append(i)
            else:
                no_slack.append(i)

    Ared = A[no_slack, :][:, no_slack]

    # Compute the power injection at the flat voltage this model assumes, for the same
    # reason as in linear_pf
    Sbus = cf.compute_zip_power(S0, I0, Y0, np.ones_like(Vm))

    # compose the reduced power injections (Pinj)
    # Since we have removed the slack nodes, we must account their influence as Injections Bref * Va_ref
    # We also need to account for the effect of the phase shifters (Pps)
    Pps = Bf.T @ tau

    Bref = Bbus[:, vd]
    Pref = (Bref @ Va[vd]) * Vm

    # the part of the injections that does not depend on the converters
    P_base = Sbus.real - Pref + Pps

    P = P_base + p_vsc
    Pred = P[no_slack]

    zm = np.zeros(nc.nbr)

    with warnings.catch_warnings():
        warnings.filterwarnings('error')
        try:
            dx = sp.linalg.spsolve(Ared.tocsc(), Pred)
        except sp.linalg.MatrixRankWarning as e:
            # logger.add_error("ACDC PTDF singular matrix. Does each subgrid have a slack?")
            print(e)

            norm_f = 0.0
            Pf = zm
            V = V0

            return NumericPowerFlowResults(V=V,
                                           Scalc=S0 * nc.Sbase,
                                           m=np.ones(nc.nbr, dtype=float),
                                           tau=np.zeros(nc.nbr, dtype=float),
                                           Sf=Pf,
                                           St=-Pf,
                                           If=zm,
                                           It=zm,
                                           loading=zm,
                                           losses=zm,
                                           Pfp_vsc=np.zeros(nc.nvsc, dtype=float),
                                           Pfn_vsc=np.zeros(nc.nvsc, dtype=float),
                                           St_vsc=np.zeros(nc.nvsc, dtype=complex),
                                           If_vsc=np.zeros(nc.nvsc, dtype=float),
                                           It_vsc=np.zeros(nc.nvsc, dtype=complex),
                                           losses_vsc=np.zeros(nc.nvsc, dtype=float),
                                           loading_vsc=np.zeros(nc.nvsc, dtype=float),
                                           Sf_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                           St_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                           losses_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                           loading_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                           norm_f=norm_f,
                                           converged=True,
                                           iterations=1,
                                           elapsed=time.time() - start)

    x = np.r_[Va, Vm]

    # Assign because the reduced system already returns the absolute angles
    x[no_slack] = dx

    # update angles for non-reference buses
    Va = x[0:n]
    Vm = x[n:2 * n]

    # Droop saturation: a P-mode 3 converter follows its droop law only up to its rating,
    # beyond that it holds the rating.
    vsc_rates_pu: Vec = nc.vsc_data.rates / nc.Sbase
    max_saturation_passes: int = int(np.sum(vsc_model.is_droop))
    saturation_pass: int = 0
    saturating: bool = max_saturation_passes > 0

    while saturating and saturation_pass < max_saturation_passes:

        vsc_powers = compute_vsc_powers(nc=nc, model=vsc_model, va=Va, pinned=vsc_pinned)
        newly_pinned: int = 0
        for m in range(nc.vsc_data.nelm):
            over_rate = (vsc_model.is_droop[m]
                         and np.isnan(vsc_pinned[m])
                         and abs(vsc_powers[m]) > vsc_rates_pu[m] + 1e-8)
            if over_rate:
                vsc_pinned[m] = float(np.sign(vsc_powers[m]) * vsc_rates_pu[m])
                newly_pinned += 1
            else:
                pass  # this converter is inside its rating, or already pinned

        if newly_pinned == 0:
            saturating = False  # every converter respects its rating, the solution stands
        else:
            A_it = A_branches.copy()
            p_vsc = add_vsc_linear_terms(nc=nc, model=vsc_model, A=A_it, pinned=vsc_pinned)
            Va = np.zeros(n)
            Va[vd] = np.angle(V0[vd])
            Va[no_slack] = sp.linalg.spsolve(A_it[no_slack, :][:, no_slack].tocsc(),
                                             (P_base + p_vsc)[no_slack])

        saturation_pass += 1

    vsc_powers = compute_vsc_powers(nc=nc, model=vsc_model, va=Va, pinned=vsc_pinned)

    # re assemble the voltage
    V = cf.polar_to_rect(Vm, Va)

    # Compute the flows from angles instead of complex voltages
    Pf = (Af @ Va - ys_arr * tau) * nc.Sbase

    # check for convergence
    norm_f = 0.0

    # Sf, St, If, It, Vbranch, loading, losses, Sbus = cf.power_flow_post_process_linear(
    #     Sbus=S0,
    #     V=V,
    #     active=nc.passive_branch_data.active,
    #     X=nc.passive_branch_data.X,
    #     tap_module=nc.active_branch_data.tap_module,
    #     tap_angle=nc.active_branch_data.tap_angle,
    #     F=nc.passive_branch_data.F,
    #     T=nc.passive_branch_data.T,
    #     branch_rates=nc.passive_branch_data.rates,
    #     Sbase=nc.Sbase
    # )

    loading = Pf / (nc.passive_branch_data.rates + 1e-20)

    return NumericPowerFlowResults(V=V,
                                   Scalc=S0 * nc.Sbase,
                                   m=np.ones(nc.nbr, dtype=float),
                                   tau=np.zeros(nc.nbr, dtype=float),
                                   Sf=Pf,
                                   St=-Pf,
                                   If=zm,
                                   It=zm,
                                   loading=loading,
                                   losses=zm,
                                   Pfp_vsc=vsc_powers * nc.Sbase,
                                   Pfn_vsc=np.zeros(nc.nvsc, dtype=float),
                                   St_vsc=np.zeros(nc.nvsc, dtype=complex),
                                   If_vsc=np.zeros(nc.nvsc, dtype=float),
                                   It_vsc=np.zeros(nc.nvsc, dtype=complex),
                                   losses_vsc=np.zeros(nc.nvsc, dtype=float),
                                   loading_vsc=vsc_powers / (vsc_rates_pu + 1e-20),
                                   Sf_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                   St_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                   losses_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                   loading_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                   norm_f=norm_f,
                                   converged=True,
                                   iterations=1,
                                   elapsed=time.time() - start)


def lacpf(nc: NumericalCircuit,
          Ybus: CscMat, Yf: CscMat, Yt: CscMat, Ys: CscMat, Yshunt_bus: CxVec,
          S0: CxVec, V0: CxVec, pq: IntVec, pv: IntVec, vd: IntVec,
          logger: Logger) -> NumericPowerFlowResults:
    """
    Linearized AC Load Flow

    form the article:

    Linearized AC Load Flow Applied to Analysis in Electric Power Systems
        by: P. Rossoni, W. M da Rosa and E. A. Belati
    :param nc: NumericalCircuit instance
    :param Ybus: Admittance matrix
    :param Yf: Admittance from matrix
    :param Yt: Admittance to matrix
    :param Ys: Admittance matrix of the series elements
    :param Yshunt_bus: Admittance vector of the series elements per bus
    :param S0: Power Injections vector of all the nodes
    :param V0: Set voltages of all the nodes (used for the slack and PV nodes)
    :param pq: list of indices of the pq nodes
    :param pv: list of indices of the pv nodes
    :param vd: Array with the indices of the slack buses
    :param logger: Logger
    :return: NumericPowerFlowResults
    """

    start = time.time()

    pvpq = np.r_[pv, pq]
    npq = len(pq)
    npv = len(pv)
    npqpv = npq + npv
    n = len(V0)

    if (npq + npv) > 0:
        # compose the system matrix
        # G = Y.real
        # B = Y.imag
        # Gp = Ys.real
        # Bp = Ys.imag

        A11 = -Ys.imag[np.ix_(pvpq, pvpq)]
        A12 = Ybus.real[np.ix_(pvpq, pq)]
        A21 = -Ys.real[np.ix_(pq, pvpq)]
        A22 = -Ybus.imag[np.ix_(pq, pq)]

        Asys = sp.vstack([sp.hstack([A11, A12]),
                          sp.hstack([A21, A22])], format="csc")

        # compose the right hand side (power vectors)
        rhs = np.r_[S0.real[pvpq], S0.imag[pq]]

        # solve the linear system
        try:
            x = linear_solver(Asys, -rhs)
        except RuntimeError as e:
            V = V0
            # Calculate the error and check the convergence
            Scalc = cf.compute_power(Ybus, V)
            mismatch = cf.compute_fx(Scalc=Scalc, Sbus=S0, idx_dP=pvpq, idx_dQ=pq)
            norm_f = cf.compute_fx_error(mismatch)

            # check for convergence
            end = time.time()
            elapsed = end - start

            logger.add_error("Failed linear system solution",
                             device="Linear power flow with voltage modules",
                             comment=str(e))

            return NumericPowerFlowResults(V=V,
                                           Scalc=Scalc * nc.Sbase,
                                           m=np.ones(nc.nbr, dtype=float),
                                           tau=np.zeros(nc.nbr, dtype=float),
                                           Sf=np.zeros(nc.nbr, dtype=complex),
                                           St=np.zeros(nc.nbr, dtype=complex),
                                           If=np.zeros(nc.nbr, dtype=complex),
                                           It=np.zeros(nc.nbr, dtype=complex),
                                           loading=np.zeros(nc.nbr, dtype=complex),
                                           losses=np.zeros(nc.nbr, dtype=complex),
                                           Pfp_vsc=np.zeros(nc.nvsc, dtype=float),
                                           Pfn_vsc=np.zeros(nc.nvsc, dtype=float),
                                           St_vsc=np.zeros(nc.nvsc, dtype=complex),
                                           If_vsc=np.zeros(nc.nvsc, dtype=float),
                                           It_vsc=np.zeros(nc.nvsc, dtype=complex),
                                           losses_vsc=np.zeros(nc.nvsc, dtype=float),
                                           loading_vsc=np.zeros(nc.nvsc, dtype=float),
                                           Sf_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                           St_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                           losses_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                           loading_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                           norm_f=norm_f,
                                           converged=False,
                                           iterations=1,
                                           elapsed=elapsed)

        # compose the results vector
        V = V0.copy()

        #  set the pv voltages
        va_pv = x[0:npv]
        vm_pv = np.abs(V0[pv])
        V[pv] = cf.polar_to_rect(vm_pv, va_pv)

        # set the PQ voltages
        va_pq = x[npv:npv + npq]
        vm_pq = np.ones(npq) - x[npv + npq::]
        V[pq] = cf.polar_to_rect(vm_pq, va_pq)

        # Calculate the error and check the convergence
        Scalc = cf.compute_power(Ybus, V)
        mismatch = cf.compute_fx(Scalc, S0, pvpq, pq)
        norm_f = cf.compute_fx_error(mismatch)
    else:
        norm_f = 0.0
        V = V0
        Scalc = cf.compute_power(Ybus, V)

    end = time.time()
    elapsed = end - start

    # Compute the Branches power and the slack buses power
    Sf, St, If, It, Vbranch, loading, losses, Sbus = cf.power_flow_post_process_nonlinear(
        Sbus=Scalc,
        V=V,
        F=nc.passive_branch_data.F,
        T=nc.passive_branch_data.T,
        pv=pv,
        vd=vd,
        Ybus=Ybus,
        Yf=Yf,
        Yt=Yt,
        Yshunt_bus=Yshunt_bus,
        branch_rates=nc.passive_branch_data.rates,
        Sbase=nc.Sbase
    )

    return NumericPowerFlowResults(V=V,
                                   Scalc=Scalc * nc.Sbase,
                                   m=np.ones(nc.nbr, dtype=float),
                                   tau=np.zeros(nc.nbr, dtype=float),
                                   Sf=Sf,
                                   St=St,
                                   If=If,
                                   It=It,
                                   loading=loading,
                                   losses=losses,
                                   Pfp_vsc=np.zeros(nc.nvsc, dtype=float),
                                   Pfn_vsc=np.zeros(nc.nvsc, dtype=float),
                                   St_vsc=np.zeros(nc.nvsc, dtype=complex),
                                   If_vsc=np.zeros(nc.nvsc, dtype=float),
                                   It_vsc=np.zeros(nc.nvsc, dtype=complex),
                                   losses_vsc=np.zeros(nc.nvsc, dtype=float),
                                   loading_vsc=np.zeros(nc.nvsc, dtype=float),
                                   Sf_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                   St_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                   losses_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                   loading_hvdc=np.zeros(nc.nhvdc, dtype=complex),
                                   norm_f=norm_f,
                                   converged=True,
                                   iterations=1,
                                   elapsed=elapsed)
