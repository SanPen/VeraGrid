# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Exact solver-side elimination of passive NABC nodes, including 3W star points."""
import numpy as np
from scipy.sparse import csc_matrix
import pytest
import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.enumerations import BusMode
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations import pf_basic_formulation_3ph as abc
from VeraGridEngine.Simulations.PowerFlow3ph.power_flow_worker_3ph import (
    multi_island_pf_nc_3ph, multi_island_pf_3ph)
from ThreePhasePowerFlow.test_3ph_transformer3w import make_grid
from ThreePhasePowerFlow.test_3ph_common_mode import floating_grid


def loaded_grid(stiff: bool = False) -> tuple[vge.MultiCircuit, vge.Transformer3W]:
    """Add unequal phase loads to the existing three-terminal test network.

    :param stiff: Use delta secondaries with a small, finite MV-LV zero-sequence impedance.
    :return: Physical grid and its transformer.
    """
    grid, transformer = make_grid()
    if stiff:
        transformer.winding2.conn_f = vge.WindingType.Delta
        transformer.winding3.conn_f = vge.WindingType.Delta
        transformer.winding2.vector_group_number = 1
        transformer.winding3.vector_group_number = 1
        transformer.fill_zero_sequence(0.03 + 0.3j, 2e-7 + 2e-6j, 0.03 + 0.3j)
    for bus, scale in ((transformer.bus2, 1.0), (transformer.bus3, 0.5)):
        load = vge.Load(P=12*scale, Q=3*scale, P1=6*scale, P2=4*scale, P3=2*scale,
                        Q1=scale, Q2=0.5*scale, Q3=1.5*scale)
        load.conn = vge.ShuntConnectionType.Delta
        grid.add_load(bus, load)
    return grid, transformer


def options() -> vge.PowerFlowOptions:
    """Use the same controls and strict stopping tolerance in both formulations."""
    return vge.PowerFlowOptions(tolerance=1e-9, max_iter=80, control_q=False,
        control_taps_modules=False, control_taps_phase=False, retry_with_other_methods=False)


def voltage(result) -> np.ndarray:
    """Return the original NABC bus order, including reconstructed internal voltages."""
    return np.column_stack((result.voltage_N, result.voltage_A,
                            result.voltage_B, result.voltage_C))


def keep_all(nc, ybus, mask):
    """Retain the original nodal equations for an independent reference solve."""
    return np.arange(ybus.shape[0]), None


@pytest.mark.parametrize('stiff', (False, True))
def test_internal_reduction_preserves_voltage_currents_and_original_kcl(monkeypatch, stiff: bool) -> None:
    """Solve the same nonlinear circuit with and without the extra ABC elimination.

    :param monkeypatch: Disable elimination for the reference run.
    :param stiff: Include an ill-conditioned but physically unchanged YNdd star equivalent.
    """
    grid, transformer = loaded_grid(stiff)
    original = abc.passive_neutral_reduction
    reductions = []

    def capture(nc, ybus, mask):
        keep, lift = original(nc, ybus, mask)
        reductions.append((nc, ybus, mask, keep, lift))
        return keep, lift

    monkeypatch.setattr(abc, 'passive_neutral_reduction', capture)
    reduced = vge.power_flow3ph(grid, options())
    assert reduced.converged
    assert len(reductions) == 1
    nc, ybus, mask, keep, lift = reductions[0]
    internal = np.flatnonzero(nc.bus_data.idtag == transformer.bus0.idtag)[0]
    eliminated = np.setdiff1d(np.arange(ybus.shape[0]), keep)
    np.testing.assert_array_equal(np.flatnonzero(mask)[eliminated], 4*internal + np.arange(1, 4))
    assert lift.shape == (ybus.shape[0], ybus.shape[0] - 3)
    full_voltage = voltage(reduced).ravel()[mask]
    np.testing.assert_allclose(lift @ full_voltage[keep], full_voltage, atol=1e-10, rtol=0)
    np.testing.assert_allclose((ybus @ full_voltage)[eliminated], 0, atol=2e-9, rtol=0)

    monkeypatch.setattr(abc, 'passive_neutral_reduction', keep_all)
    explicit = vge.power_flow3ph(grid, options())
    assert explicit.converged
    np.testing.assert_allclose(voltage(reduced), voltage(explicit), atol=2e-8, rtol=0)
    for terminal in ('f', 't'):
        for phase in ('N', 'A', 'B', 'C'):
            np.testing.assert_allclose(getattr(reduced, f'I{terminal}_{phase}'),
                                       getattr(explicit, f'I{terminal}_{phase}'), atol=2e-8, rtol=0)


def test_stiff_internal_reconstruction_uses_the_returned_physical_kcl() -> None:
    """The reconstructed star point must satisfy its original KCL at the solver tolerance."""
    grid, transformer = loaded_grid(stiff=True)
    transformer.fill_zero_sequence(0.03 + 0.3j, 5e-8 + 5e-7j, 0.03 + 0.3j)
    nc = compile_numerical_circuit_at(grid, fill_three_phase=True)
    nc.get_simulation_indices(Sbus=nc.get_power_injections_pu())
    qmax, qmin = nc.get_reactive_power_limits()
    problem = abc.PfBasicFormulation3Ph(V0=abc.expandVoltage3ph(nc.bus_data.Vbus),
        S0=abc.expand3ph(nc.get_power_injections_pu()), Qmin=qmin, Qmax=qmax,
        nc=nc, options=options(), logger=vge.Logger())
    assert problem.voltage_lift is not None
    # Prescribe realistic unbalanced terminal voltages. The passive internal KCL
    # must hold at every iterate, independently of the external load mismatches.
    trial = abc.expandVoltage3ph(nc.bus_data.Vbus)
    rotation = np.exp(-2j * np.pi * np.arange(3) / 3)
    for bus, magnitude in ((transformer.bus2, 0.99), (transformer.bus3, 0.97)):
        index = grid.buses.index(bus)
        trial[4*index + 1:4*index + 4] = (magnitude * np.exp(1j * (0.05 - np.pi/6))
                                         * rotation * np.array((1, 0.999, 1.002)))
    problem.Vm[:] = np.abs(trial[problem.mask])
    problem.Va[:] = np.angle(trial[problem.mask])
    problem.update(problem.var2x())
    result = problem.get_solution(elapsed=0.0, iterations=0)
    original_y: csc_matrix = problem.Ybus_full
    full_mask: np.ndarray = problem.bus_lookup_full >= 0
    returned = result.V[full_mask]
    eliminated = np.setdiff1d(np.arange(original_y.shape[0]), problem.retained)
    original_error = float(np.max(np.abs((original_y @ returned)[eliminated])))
    assert original_error < options().tolerance
    assert problem.passive_current_error(problem.V) == pytest.approx(original_error, abs=1e-15)
    np.testing.assert_array_equal(returned[problem.retained], problem.V)


@pytest.mark.parametrize('device', ('load', 'generator', 'battery', 'static_generator', 'shunt'))
@pytest.mark.parametrize('active', (False, True))
def test_internal_bus_with_active_device_is_retained(device: str, active: bool) -> None:
    """Never eliminate a device's voltage state, even when its scheduled power is zero.

    :param device: Existing injection family sharing an internal bus.
    :param active: Inactive devices must not unnecessarily disable the optimisation.
    """
    grid, transformer = loaded_grid()
    constructors = {'load': vge.Load, 'generator': vge.Generator, 'battery': vge.Battery,
                    'static_generator': vge.StaticGenerator, 'shunt': vge.Shunt}
    getattr(grid, f'add_{device}')(transformer.bus0, constructors[device](active=active))
    nc = compile_numerical_circuit_at(grid, fill_three_phase=True)
    internal = np.flatnonzero(nc.bus_data.idtag == transformer.bus0.idtag)
    ybus, _, _, _, mask, _, _ = abc.compute_ybus(nc)
    keep, lift = abc.passive_neutral_reduction(nc, ybus, mask)
    retained = np.flatnonzero(mask)[keep]
    assert np.isin(4*internal[0] + np.arange(1, 4), retained).all() == active
    assert (lift is None) == active


@pytest.mark.parametrize('protection', ('slack', 'pv', 'vm_control', 'va_control',
                                       'remote_generator', 'remote_battery', 'remote_shunt'))
def test_controlled_internal_bus_is_retained(protection: str) -> None:
    """Keep both local references and remote control targets available to their controls.

    :param protection: Existing bus classification or control reference.
    """
    grid, transformer = loaded_grid()
    if protection.startswith('remote_'):
        family = protection.removeprefix('remote_')
        constructors = {'generator': vge.Generator, 'battery': vge.Battery,
                        'shunt': vge.ControllableShunt}
        device = constructors[family]()
        device.control_bus = transformer.bus0
        getattr(grid, 'add_controllable_shunt' if family == 'shunt' else f'add_{family}')(
            transformer.bus2, device)
    nc = compile_numerical_circuit_at(grid, fill_three_phase=True)
    internal = np.flatnonzero(nc.bus_data.idtag == transformer.bus0.idtag)
    if protection == 'slack':
        nc.bus_data.bus_types[internal] = BusMode.Slack_tpe.value
    elif protection == 'pv':
        nc.bus_data.bus_types[internal] = BusMode.PV_tpe.value
    elif protection == 'vm_control':
        nc.bus_data.is_vm_controlled[internal] = True
    elif protection == 'va_control':
        nc.bus_data.is_va_controlled[internal] = True
    ybus, _, _, _, mask, _, _ = abc.compute_ybus(nc)
    keep, lift = abc.passive_neutral_reduction(nc, ybus, mask)
    np.testing.assert_array_equal(keep, np.arange(ybus.shape[0]))
    assert lift is None


def test_floating_group_remains_free_after_internal_reduction(monkeypatch) -> None:
    """An eliminated star point must not masquerade as an earth reference."""
    grid, transformer = loaded_grid()
    transformer.bus1.is_slack = False
    source = grid.add_bus(vge.Bus(name='Source', Vnom=110, is_slack=True))
    grid.generators[0].bus = source
    isolation = vge.Transformer2W(bus_from=source, bus_to=transformer.bus1,
        HV=110, LV=110, r=0.01, x=0.1, r0=0.02, x0=0.12, r2=0.01, x2=0.1, g0=0, b0=0)
    isolation.conn_f = isolation.conn_t = vge.WindingType.Delta
    grid.add_transformer2w(isolation)
    for winding in (transformer.winding1, transformer.winding2, transformer.winding3):
        winding.G0 = winding.B0 = 0
    nc = compile_numerical_circuit_at(grid, fill_three_phase=True)
    nc.get_simulation_indices(Sbus=nc.get_power_injections_pu())
    qmax, qmin = nc.get_reactive_power_limits()
    internal = np.flatnonzero(nc.bus_data.idtag == transformer.bus0.idtag)
    problem = abc.PfBasicFormulation3Ph(V0=abc.expandVoltage3ph(nc.bus_data.Vbus),
        S0=abc.expand3ph(nc.get_power_injections_pu()), Qmin=qmin, Qmax=qmax,
        nc=nc, options=options(), logger=vge.Logger())
    assert len(problem.common_mode.phases) == 1
    assert problem.voltage_lift is not None
    reduced = vge.power_flow3ph(grid, options())
    assert reduced.converged
    monkeypatch.setattr(abc, 'passive_neutral_reduction', keep_all)
    explicit = vge.power_flow3ph(grid, options())
    assert explicit.converged
    # The free common-mode origin can move when a redundant state is removed;
    # terminal line-line voltages and every winding current are physical invariants.
    np.testing.assert_allclose(np.diff(voltage(reduced)[:, 1:], axis=1),
                               np.diff(voltage(explicit)[:, 1:], axis=1), atol=2e-8, rtol=0)
    for terminal in ('f', 't'):
        for phase in ('A', 'B', 'C'):
            np.testing.assert_allclose(getattr(reduced, f'I{terminal}_{phase}'),
                                       getattr(explicit, f'I{terminal}_{phase}'), atol=2e-8, rtol=0)
    ybus: csc_matrix = problem.Ybus_full
    mask: np.ndarray = problem.bus_lookup_full >= 0
    internal_rows = np.isin(np.flatnonzero(mask), 4*internal[0] + np.arange(1, 4))
    np.testing.assert_allclose((ybus @ voltage(reduced).ravel()[mask])[internal_rows], 0, atol=2e-9)


@pytest.mark.parametrize('singularity', ('zero_block', 'floating_windings'))
def test_singular_internal_block_falls_back_without_grounding(singularity: str) -> None:
    """Keep singular candidates explicit rather than invent an earth admittance.

    :param singularity: Missing equations or a physical free internal common mode.
    """
    grid, transformer = loaded_grid()
    if singularity == 'floating_windings':
        for winding in (transformer.winding1, transformer.winding2, transformer.winding3):
            winding.conn_f = vge.WindingType.FloatingStar
            winding.G0 = winding.B0 = 0
    nc = compile_numerical_circuit_at(grid, fill_three_phase=True)
    internal = np.flatnonzero(nc.bus_data.idtag == transformer.bus0.idtag)
    ybus, _, _, _, mask, _, _ = abc.compute_ybus(nc)
    rows = np.flatnonzero(np.isin(np.flatnonzero(mask), 4*internal[0] + np.arange(1, 4)))
    singular = ybus.tolil()
    if singularity == 'zero_block':
        singular[rows, :] = 0
        singular[:, rows] = 0
    else:
        assert np.linalg.matrix_rank(ybus[rows, :][:, rows].toarray()) == 2
    keep, lift = abc.passive_neutral_reduction(nc, singular.tocsc(), mask)
    assert lift is None
    np.testing.assert_array_equal(keep, np.arange(ybus.shape[0]))


@pytest.mark.parametrize('time_index', (None, 0))
def test_passive_detection_survives_islands_permutation_and_duplicate_names(monkeypatch, time_index: int | None) -> None:
    """Detect passive nodes in snapshots/time steps without name or position assumptions.

    :param monkeypatch: Observe eliminated nodes within each compiled island.
    :param time_index: Snapshot or first time step, with identical physical profiles.
    """
    grid, first = loaded_grid()
    second_grid, second = loaded_grid()
    for bus in (second.bus1, second.bus2, second.bus3):
        grid.add_bus(bus)
    grid.add_transformer3w(second)
    for generator in second_grid.generators:
        grid.add_generator(generator.bus, generator)
    for load in second_grid.loads:
        grid.add_load(load.bus, load)
    ids = {first.bus0.idtag, second.bus0.idtag}
    baseline = vge.power_flow3ph(grid, options())
    assert baseline.converged
    expected = {bus.idtag: row for bus, row in zip(grid.buses, voltage(baseline))}
    grid.buses.reverse()
    for bus in grid.buses:
        bus.name = 'Duplicate'
    grid.create_profiles(steps=1, step_length=1, step_unit='h')
    original = abc.passive_neutral_reduction
    eliminated_ids = set()

    def capture(nc, ybus, mask):
        keep, lift = original(nc, ybus, mask)
        removed = np.setdiff1d(np.arange(ybus.shape[0]), keep)
        eliminated_ids.update(nc.bus_data.idtag[np.unique(np.flatnonzero(mask)[removed] // 4)])
        return keep, lift

    monkeypatch.setattr(abc, 'passive_neutral_reduction', capture)
    result = multi_island_pf_3ph(grid, options(), t=time_index)
    assert result.converged
    assert eliminated_ids == ids
    for bus, actual in zip(grid.buses, voltage(result)):
        np.testing.assert_allclose(actual, expected[bus.idtag], atol=1e-10, rtol=0)


def test_direct_compiled_api_reduces_without_extra_metadata(monkeypatch) -> None:
    """Existing compiled callers obtain the same reduction with their unchanged signature."""
    grid, _ = loaded_grid()
    original = abc.passive_neutral_reduction
    eliminated = []

    def capture(nc, ybus, mask):
        keep, lift = original(nc, ybus, mask)
        eliminated.append(ybus.shape[0] - len(keep))
        return keep, lift

    monkeypatch.setattr(abc, 'passive_neutral_reduction', capture)
    reduced = multi_island_pf_nc_3ph(compile_numerical_circuit_at(grid, fill_three_phase=True),
                                   options())
    assert eliminated == [3]
    monkeypatch.setattr(abc, 'passive_neutral_reduction', keep_all)
    explicit = multi_island_pf_nc_3ph(compile_numerical_circuit_at(grid, fill_three_phase=True), options())
    assert explicit.converged and reduced.converged
    np.testing.assert_allclose(voltage(explicit), voltage(reduced), atol=2e-8, rtol=0)


@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM, vge.SolverType.PowellDogLeg))
def test_all_passive_unknowns_eliminated_is_converged(solver: vge.SolverType) -> None:
    """An exactly reconstructed unloaded network needs no nonlinear unknowns or iterations."""
    grid, _ = make_grid()
    pf_options = options()
    pf_options.solver_type = solver
    result = vge.power_flow3ph(grid, pf_options)
    assert result.converged
    expected = np.tile(np.exp(-2j*np.pi*np.arange(3)/3), (len(grid.buses), 1))
    np.testing.assert_allclose(voltage(result)[:, 1:], expected, atol=1e-10, rtol=0)
    for terminal in ('f', 't'):
        for phase in ('N', 'A', 'B', 'C'):
            np.testing.assert_allclose(getattr(result, f'I{terminal}_{phase}'), 0, atol=1e-10, rtol=0)


@pytest.mark.parametrize('coupled_floating_pair,explicit_neutral', ((False, False), (True, False), (True, True)))
def test_ordinary_passive_buses_preserve_physical_kcl_and_free_modes(monkeypatch,
                                                                  coupled_floating_pair: bool,
                                                                  explicit_neutral: bool) -> None:
    """Reduce ordinary passive buses while preserving singular groups without 3W metadata.

    :param monkeypatch: Compare with the original complete nodal equations.
    :param coupled_floating_pair: Insert two passive buses between delta barriers;
        each 3x3 self-block is invertible but their joint 6x6 block has rank five.
    :param explicit_neutral: A separate four-wire feeder must retain its neutral reduction
        even when the ABC candidate block is singular.
    """
    grid = floating_grid()
    first, load_bus = grid.buses[1:3]
    passive_buses = [first]
    if coupled_floating_pair:
        second = grid.add_bus(vge.Bus(name='Other passive bus', Vnom=11))
        grid.lines[0].bus_to = second
        transformer = vge.Transformer2W(bus_from=second, bus_to=load_bus,
            HV=11, LV=11, r=0.01, x=0.1, r0=0.02, x0=0.12, r2=0.01, x2=0.1,
            g0=0, b0=0)
        transformer.conn_f = transformer.conn_t = vge.WindingType.Delta
        grid.add_transformer2w(transformer)
        passive_buses.append(second)
    if explicit_neutral:
        target = grid.add_bus(vge.Bus(name='Four-wire load', Vnom=110))
        line = vge.Line(bus_from=grid.buses[0], bus_to=target)
        line.disable_auto_updates()
        line.ys.values = np.linalg.inv(np.array((
            (0.08+0.15j, 0.01j, 0.02j, 0.015j), (0.01j, 0.04+0.12j, 0.015j, 0.02j),
            (0.02j, 0.015j, 0.05+0.13j, 0.01j), (0.015j, 0.02j, 0.01j, 0.04+0.11j))))
        line.ys.phN = line.ys.phA = line.ys.phB = line.ys.phC = True
        line.ysh.values = np.zeros((4, 4), dtype=complex)
        grid.add_line(line)
        load = vge.Load(P=30, Q=9, P1=10, P2=11, P3=9, Q1=3, Q2=4, Q3=2)
        load.conn = vge.ShuntConnectionType.Delta
        grid.add_load(target, load)
    assert not grid.transformers3w
    assert all(not bus.internal for bus in passive_buses)
    nc = compile_numerical_circuit_at(grid, fill_three_phase=True)
    nc.get_simulation_indices(Sbus=nc.get_power_injections_pu())
    ybus, _, _, _, mask, lookup, _ = abc.compute_ybus(nc)
    buses = np.array([grid.buses.index(bus) for bus in passive_buses])
    rows = lookup[(4*buses[:, None] + np.arange(1, 4)).ravel()]
    if coupled_floating_pair:
        block = ybus[rows, :][:, rows].toarray()
        assert np.linalg.matrix_rank(block) == 5
        assert np.linalg.matrix_rank(block[:3, :3]) == 3
        assert np.linalg.matrix_rank(block[3:, 3:]) == 3
    keep, lift = abc.passive_neutral_reduction(nc, ybus, mask)
    removed = np.setdiff1d(np.arange(ybus.shape[0]), keep)
    if not coupled_floating_pair:
        np.testing.assert_array_equal(removed, rows)
    else:
        # A whole-group fallback or a retained reference both preserve the free mode.
        assert np.intersect1d(rows, keep).size >= 3
    if explicit_neutral:
        neutral = lookup[4*grid.buses.index(target)]
        assert neutral >= 0
        assert neutral in removed
    if lift is not None:
        trial = lift @ np.exp(1j*np.arange(len(keep)))
        np.testing.assert_allclose((ybus @ trial)[removed], 0, atol=1e-11, rtol=0)
    qmax, qmin = nc.get_reactive_power_limits()
    problem = abc.PfBasicFormulation3Ph(V0=abc.expandVoltage3ph(nc.bus_data.Vbus),
        S0=abc.expand3ph(nc.get_power_injections_pu()), Qmin=qmin, Qmax=qmax,
        nc=nc, options=options(), logger=vge.Logger())
    assert len(problem.common_mode.phases) == (2 if coupled_floating_pair else 1)
    reduced = vge.power_flow3ph(grid, options())
    assert reduced.converged
    np.testing.assert_allclose((ybus @ voltage(reduced).ravel()[mask])[rows], 0, atol=2e-9, rtol=0)
    if explicit_neutral:
        assert abs(reduced.voltage_N[grid.buses.index(target)]) > 1e-5
        np.testing.assert_allclose((ybus @ voltage(reduced).ravel()[mask])[neutral], 0, atol=2e-9, rtol=0)
    monkeypatch.setattr(abc, 'passive_neutral_reduction', keep_all)
    explicit = vge.power_flow3ph(grid, options())
    assert explicit.converged
    np.testing.assert_allclose(np.diff(voltage(reduced)[:, 1:], axis=1),
                               np.diff(voltage(explicit)[:, 1:], axis=1), atol=2e-8, rtol=0)
    for terminal in ('f', 't'):
        for phase in ('N', 'A', 'B', 'C'):
            np.testing.assert_allclose(getattr(reduced, f'I{terminal}_{phase}'),
                                       getattr(explicit, f'I{terminal}_{phase}'), atol=2e-8, rtol=0)
