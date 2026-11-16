# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import pytest
import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.IO.dgs.dgs_objects import ElmScap, StaCubic
from VeraGridEngine.IO.dgs.dgs_to_veragrid import convert_dgs_series_capacitor_to_reactance


@pytest.mark.parametrize('z1,z0,z2', ((0.02+0.06j, 0.04+0.12j, 0.03+0.07j),
    (0.02+0.06j, 1e-20+1e-20j, 0j), (-0.06j, -0.08j, -0.07j), (-0.06j, 1e-20+1e-20j, 0j)))
def test_reactor_sequence_stamps_and_phase_kcl(z1: complex, z0: complex, z2: complex) -> None:
    """Check sequence eigenvalues, no charging and solved unbalanced phase KCL.

    :param z1: Positive-sequence inductive or capacitive impedance.
    :param z0: Homopolar impedance or legacy missing value.
    :param z2: Negative-sequence impedance or missing value.
    """
    grid: vge.MultiCircuit = vge.MultiCircuit()
    source: vge.Bus = grid.add_bus(vge.Bus(Vnom=33, is_slack=True))
    target: vge.Bus = grid.add_bus(vge.Bus(Vnom=33))
    grid.add_generator(source, vge.Generator())
    grid.add_series_reactance(vge.SeriesReactance(bus_from=source, bus_to=target, r=z1.real, x=z1.imag,
        r0=z0.real, x0=z0.imag, r2=z2.real, x2=z2.imag))
    grid.add_load(target, vge.Load(P=6, Q=2, P1=3, P2=2, P3=1, Q1=1, Q2=0.7, Q3=0.3))
    nc: NumericalCircuit = compile_numerical_circuit_at(grid, fill_three_phase=True)
    a: complex = np.exp(2j*np.pi/3)
    transform: np.ndarray = np.array(((1, 1, 1), (1, a*a, a), (1, a, a*a)))
    expected: np.ndarray = np.diag(1 / np.array((z0 if abs(z0)>1e-10 else z1,
                                                 z1, z2 if abs(z2)>1e-10 else z1)))
    ys: np.ndarray = nc.passive_branch_data.Yff3[1:, 1:]
    np.testing.assert_allclose(np.linalg.solve(transform, ys @ transform), expected, atol=1e-12)
    np.testing.assert_allclose(nc.passive_branch_data.Yff3 + nc.passive_branch_data.Yft3, 0)
    np.testing.assert_allclose(nc.passive_branch_data.Ytt3, nc.passive_branch_data.Yff3)
    assert nc.passive_branch_data.phA[0] and nc.passive_branch_data.phB[0] and nc.passive_branch_data.phC[0]
    result: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid, options=vge.PowerFlowOptions(tolerance=1e-9))
    assert result.converged
    voltage: np.ndarray = np.array((result.voltage_A[1], result.voltage_B[1], result.voltage_C[1]))
    source_voltage: np.ndarray = np.array((result.voltage_A[0], result.voltage_B[0], result.voltage_C[0]))
    np.testing.assert_allclose(ys @ (voltage-source_voltage),
        -np.conj(np.array((3+1j, 2+0.7j, 1+0.3j)) / voltage) * 3/100, atol=1e-9)


@pytest.mark.parametrize('sbase', (100.0, 200.0))
@pytest.mark.parametrize('balanced', (True, False))
@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM, vge.SolverType.PowellDogLeg))
def test_imported_series_capacitor_phase_currents(sbase: float, balanced: bool,
                                                solver: vge.SolverType) -> None:
    """Check capacitor current in physical units and the balanced positive-sequence limit.

    :param sbase: Network power base in MVA.
    :param balanced: Use equal or unequal phase powers.
    :param solver: Existing power-flow algorithm, without fallback.
    """
    grid: vge.MultiCircuit = vge.MultiCircuit(Sbase=sbase)
    source: vge.Bus = grid.add_bus(vge.Bus(name='Source', Vnom=400, is_slack=True))
    target: vge.Bus = grid.add_bus(vge.Bus(name='Target', Vnom=400))
    grid.add_generator(source, vge.Generator())
    capacitor: ElmScap = ElmScap()
    capacitor.ID = 'capacitor'
    capacitor.loc_name = 'Series capacitor'
    capacitor.ucn = 400.0
    capacitor.Curn = 4.0
    capacitor.xcap = 9.2
    from_cubic: StaCubic = StaCubic()
    from_cubic.fold_id = 'source'
    from_cubic.obj_bus = 0
    to_cubic: StaCubic = StaCubic()
    to_cubic.fold_id = 'target'
    to_cubic.obj_bus = 1
    logger: vge.Logger = vge.Logger()
    branch: vge.SeriesReactance = convert_dgs_series_capacitor_to_reactance(
        element=capacitor, buses=grid.buses,
        bus_by_terminal_id=dict((('source', source), ('target', target))),
        stacubic_dict=dict(),
        cubics_by_obj_id=dict((('capacitor', list((from_cubic, to_cubic))),)),
        logger=logger, sbase_mva=sbase)
    grid.add_series_reactance(branch)
    if balanced:
        power: np.ndarray = np.full(3, 100+30j, dtype=complex)
    else:
        power: np.ndarray = np.array((150+45j, 100+30j, 50+15j))
    grid.add_load(target, vge.Load(P=float(power.real.sum()), Q=float(power.imag.sum()),
        P1=power[0].real, P2=power[1].real, P3=power[2].real,
        Q1=power[0].imag, Q2=power[1].imag, Q3=power[2].imag))
    options: vge.PowerFlowOptions = vge.PowerFlowOptions(solver_type=solver, tolerance=1e-9,
        max_iter=100, retry_with_other_methods=False, control_q=False)
    result: vge.PowerFlowResults3Ph = vge.power_flow3ph(grid, options=options)
    assert result.converged
    voltage: np.ndarray = np.column_stack((result.voltage_A, result.voltage_B, result.voltage_C))
    # The load and the capacitor must draw the same phase current in kA.
    physical_voltage: np.ndarray = voltage * 400 / np.sqrt(3)
    current: np.ndarray = (physical_voltage[0]-physical_voltage[1]) / (-9.2j)
    np.testing.assert_allclose(current, np.conj(power/physical_voltage[1]), atol=1e-9)
    absorbed: complex = np.sum((physical_voltage[0]-physical_voltage[1])*np.conj(current))
    assert abs(absorbed.real) < 1e-10 and absorbed.imag < 0
    assert branch.R == 0 and branch.X < 0
    if balanced:
        # Both formulations must represent the same balanced physical branch.
        positive: vge.PowerFlowResults = vge.power_flow(grid, options=options)
        assert positive.converged
        np.testing.assert_allclose(result.voltage_A, positive.voltage, atol=1e-8)
    else:
        pass
