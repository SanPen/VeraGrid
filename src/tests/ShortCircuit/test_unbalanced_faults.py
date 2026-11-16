# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import os
import scipy.sparse as sp

from VeraGridEngine.api import *
from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.enumerations import FaultType
from VeraGridEngine.enumerations import WindingType
from VeraGridEngine.Simulations.ShortCircuitStudies.NumericalMethods.short_circuit_sequences import compute_admittances_seq


def test_unbalanced_short_circuit():
    """
    Example 10.6b from Hadi Saadat - Power System Analysis (pag 498)
    Single line-to-ground fault at bus 3 through a fault impedance Zj = jO.1
    """

    fname = os.path.join('data', 'grids', '5bus_Saadat.xlsx')
    grid = FileOpen(fname).open()

    pf_options = PowerFlowOptions(
        solver_type=SolverType.NR,  # Base method to use
        verbose=False,  # Verbose option where available
        tolerance=1e-6,  # power error in p.u.
        max_iter=25,  # maximum iteration number
    )
    pf = PowerFlowDriver(grid, pf_options)
    pf.run()

    sc_options = ShortCircuitOptions()

    grid.add_short_circuit_event(
        ShortCircuitEvent(
            device=grid.buses[2],
            fault_type=FaultType.LG,
            method=MethodShortCircuit.sequences,
            phases=PhasesShortCircuit.a,
            x_fault=0.1
        )
    )

    sc = ShortCircuitDriver(
        grid,
        options=sc_options,
        pf_options=pf_options,
        pf_results=pf.results,
        pf_results3ph=None
    )
    sc.run()

    print('\t|V0|:', np.abs(sc.results.voltage0))
    print('\t|V1|:', np.abs(sc.results.voltage1))
    print('\t|V2|:', np.abs(sc.results.voltage2))

    vm0 = np.abs(sc.results.voltage0[:, 0])
    vm1 = np.abs(sc.results.voltage1[:, 0])
    vm2 = np.abs(sc.results.voltage2[:, 0])

    vm0_book = [0.12844037, 0.05963303, 0.32110092, 0.09633028, 0.0]
    vm1_book = [0.88073394, 0.88990826, 0.79816514, 0.92844037, 0.93394495]
    vm2_book = [0.11926606, 0.11009174, 0.20183486, 0.07155963, 0.06605505]

    v0_ok = np.allclose(vm0, vm0_book, atol=1e-2)
    v1_ok = np.allclose(vm1, vm1_book, atol=1e-2)
    v2_ok = np.allclose(vm2, vm2_book, atol=1e-2)

    assert v0_ok
    assert v1_ok
    assert v2_ok


def test_sequence_admittance_supports_every_winding_pair() -> None:
    """Build every sequence matrix for every canonical transformer winding pair."""
    cf: sp.csc_matrix = sp.csc_matrix(([1.0], ([0], [0])), shape=(1, 2))
    ct: sp.csc_matrix = sp.csc_matrix(([1.0], ([0], [1])), shape=(1, 2))
    connection_from: WindingType
    connection_to: WindingType
    for connection_from in WindingType:
        for connection_to in WindingType:
            sequence: int
            for sequence in (0, 1, 2):
                admittance = compute_admittances_seq(
                    R=np.array([0.01]), X=np.array([0.1]), G=np.zeros(1), B=np.zeros(1),
                    tap_module=np.ones(1), vtap_f=np.ones(1), vtap_t=np.ones(1), tap_angle=np.zeros(1),
                    Cf=cf, Ct=ct, Yshunt_bus=np.zeros(2, dtype=complex),
                    conn_f=np.array([connection_from.idx()]), conn_t=np.array([connection_to.idx()]),
                    vector_group_number=np.array([1]), seq=sequence,
                )
                assert admittance.Ybus.shape == (2, 2)
                assert np.isfinite(admittance.Ybus.data).all()


def test_three_phase_line_fault_sequence_dispatch() -> None:
    """
    The sequence short-circuit dispatcher must accept valid ``LLL`` events.

    :return: None.
    """
    fname: str = os.path.join('data', 'grids', '5bus_Saadat.xlsx')
    grid = FileOpen(fname).open()

    pf_options: PowerFlowOptions = PowerFlowOptions(
        solver_type=SolverType.NR,
        verbose=False,
        tolerance=1e-6,
        max_iter=25,
    )
    pf: PowerFlowDriver = PowerFlowDriver(grid, pf_options)
    pf.run()

    grid.add_short_circuit_event(
        ShortCircuitEvent(
            device=grid.buses[2],
            fault_type=FaultType.LLL,
            method=MethodShortCircuit.sequences,
            phases=PhasesShortCircuit.abc,
            x_fault=0.1
        )
    )

    sc: ShortCircuitDriver = ShortCircuitDriver(
        grid,
        options=ShortCircuitOptions(),
        pf_options=pf_options,
        pf_results=pf.results,
        pf_results3ph=None
    )
    sc.run()

    assert sc.results is not None
    assert not sc.logger.has_errors()
    assert np.all(np.isfinite(sc.results.voltage1))


if __name__ == '__main__':
    test_unbalanced_short_circuit()
