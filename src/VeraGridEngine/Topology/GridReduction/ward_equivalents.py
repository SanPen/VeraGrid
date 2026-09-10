# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Tuple, Sequence, TYPE_CHECKING

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

import VeraGridEngine.Devices as dev
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.basic_structures import Logger, IntVec, CxVec

if TYPE_CHECKING:
    from VeraGridEngine.Devices.multi_circuit import MultiCircuit


def get_reduction_sets_1(nc: NumericalCircuit,
                         reduction_bus_indices: Sequence[int]) -> Tuple[IntVec, IntVec, IntVec, IntVec]:
    """
    Generate the set of bus indices for grid reduction
    :param nc: NumericalCircuit
    :param reduction_bus_indices: array of bus indices to reduce (external set)
    :return: external, boundary, internal, boundary_branches
    """

    external_set = set(reduction_bus_indices)
    boundary_set = set()
    internal_set = set()
    boundary_branches = list()

    for k in range(nc.nbr):
        f = nc.passive_branch_data.F[k]
        t = nc.passive_branch_data.T[k]
        if f in external_set:
            if t in external_set:
                # the branch belongs to the external set
                pass
            else:
                # the branch is a boundary link and t is a frontier bus
                boundary_set.add(t)
                boundary_branches.append(k)
        else:
            # we know f is not external...

            if t in external_set:
                # f is not in the external set, but t is: the branch is a boundary link and f is a frontier bus
                boundary_set.add(f)
                boundary_branches.append(k)
            else:
                # f nor t are in the external set: both belong to the internal set
                internal_set.add(f)
                internal_set.add(t)

    # buses cannot be in both the internal and boundary set
    elms_to_remove = list()
    for i in internal_set:
        if i in boundary_set:
            elms_to_remove.append(i)

    for i in elms_to_remove:
        internal_set.remove(i)

    # convert to arrays and sort
    external = np.sort(np.array(list(external_set)))
    boundary = np.sort(np.array(list(boundary_set)))
    internal = np.sort(np.array(list(internal_set)))
    boundary_branches = np.array(boundary_branches)

    return external, boundary, internal, boundary_branches


def ward_standard_reduction(grid: MultiCircuit,
                           reduction_bus_indices: IntVec,
                           V0: CxVec) -> Tuple[MultiCircuit, Logger]:
    """
    Ward standard reduction according to:
    REVIEW OF THE WARD CLASS OF EXTERNAL EQUIVALENTS FOR POWER SYSTEMS
    by J.W. Bandler, M.A. El-Kady and G. Centkowski, October 1983
    :param grid: MultiCircuit
    :param reduction_bus_indices: Indices of the buses to reduce
    :param V0: Initial power flow voltages
    :return: Modified (in-place) MultiCircuit
    """
    logger = Logger()

    nc = compile_numerical_circuit_at(grid, t_idx=None)

    # find the boundary set: buses from the internal set the join to the external set
    e_buses, b_buses, i_buses, b_branches = get_reduction_sets_1(
        nc=nc,
        reduction_bus_indices=reduction_bus_indices
    )

    ne = len(e_buses)
    ni = len(i_buses)
    nb = len(b_buses)

    if ne == 0:
        logger.add_info(msg="Nothing to reduce")
        return grid, logger

    if ni == 0:
        logger.add_info(msg="Nothing to keep (null grid as a result)")
        return grid, logger

    if nb == 0:
        logger.add_info(msg="The reducible and non reducible sets are disjoint and cannot be reduced")
        return grid, logger

    # Get the admittance matrix, contains the shunts at the diagonal
    adm = nc.get_admittance_matrices()

    # slice admittances and voltages
    YBE = adm.Ybus[np.ix_(b_buses, e_buses)]
    YEB = adm.Ybus[np.ix_(e_buses, b_buses)]
    YEE = adm.Ybus[np.ix_(e_buses, e_buses)]

    VB = V0[b_buses]
    VE = V0[e_buses]

    # YEE^-1
    YEE_fact = spla.factorized(YEE.tocsc())

    # Equivalent admittances at the boundary (eq. 6)
    Yeq = sp.csc_matrix(YBE @ YEE_fact(YEB.toarray()))

    IE = YEB @ VB + YEE @ VE

    # Ieq = - YBE @ YEE_fact(IE)
    Ieq = YBE @ YEE_fact(IE)

    # Equivalent power injections at the boundary
    Seq = (VB * np.conj(Ieq)) * nc.Sbase

    # ----------------------------------------------------------------------
    # Add equivalent branches at the boundary
    # ----------------------------------------------------------------------
    # add boundary equivalent sub-grid: traverse only the triangular
    for i in range(len(b_buses)):

        # add shunt reactance
        bus = grid.buses[b_buses[i]]
        yeq_row_i = Yeq[i, :].toarray().copy()[0, :]
        yeq_row_i[i] = 0
        ysh = Yeq[i, i] - np.sum(yeq_row_i)
        grid.add_shunt(bus=bus,
                       api_obj=dev.Shunt(name=f"Equivalent shunt {i}",
                                         B=ysh.imag, G=ysh.real))

        for j in range(i):

            if i != j:
                # add series reactance
                f = b_buses[i]
                t = b_buses[j]

                # Avoid adding impedances for disconnected cross-boundaries
                if abs(Yeq[i, j]) > 1e-6:
                    z = 1.0 / Yeq[i, j]

                    grid.add_series_reactance(obj=dev.SeriesReactance(
                        name=f"Equivalent boundary impedance {b_buses[i]}-{b_buses[j]}",
                        bus_from=grid.buses[f],
                        bus_to=grid.buses[t],
                        r=z.real,
                        x=z.imag,
                        rate=9999.0
                    ))
                else:
                    logger.add_warning(msg=f"Impedance between buses {f} and {t} is too small, \
                                       skipping the boundary series reactance")

    # ----------------------------------------------------------------------
    # Add equivalent loads at the boundary
    # ----------------------------------------------------------------------

    # add loads
    for ib, i in enumerate(b_buses):
        grid.add_load(bus=grid.buses[i],
                      api_obj=dev.Load(name=f"compensation {i}", P=Seq[ib].real, Q=Seq[ib].imag))

    # ----------------------------------------------------------------------
    # Remove the external buses
    # ----------------------------------------------------------------------
    grid.delete_buses(lst=[grid.buses[e] for e in e_buses], delete_associated=True)

    return grid, logger
