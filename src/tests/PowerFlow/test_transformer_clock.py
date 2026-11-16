# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Physical clock displacement must survive the scalar positive-sequence path."""
from types import SimpleNamespace

import numpy as np
import pytest
import VeraGridEngine.api as vge
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.enumerations import TapPhaseControl, WindingType
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.linearized_power_flow import acdc_lin_pf


def two_winding_grid(clock: int, reverse: bool = False, loaded: bool = True):
    """Use independent sequence data so balanced ABC supplies a separate oracle."""
    grid = vge.MultiCircuit()
    hv = grid.add_bus(vge.Bus(name='HV', Vnom=132, is_slack=True))
    lv = grid.add_bus(vge.Bus(name='LV', Vnom=33))
    transformer = vge.Transformer2W(bus_from=lv if reverse else hv,
        bus_to=hv if reverse else lv, name='Transformer', HV=132, LV=33,
        r=0.01, x=0.1, r0=0.02, x0=0.2, r2=0.01, x2=0.1,
        tap_module=1.07, tap_phase=0.08)
    transformer.conn_f = WindingType.GroundedStar if reverse else WindingType.Delta
    transformer.conn_t = WindingType.Delta if reverse else WindingType.GroundedStar
    transformer.vector_group_number = clock
    grid.add_transformer2w(transformer)
    if loaded:
        grid.add_generator(hv, vge.Generator())
        grid.add_load(lv, vge.Load(P=12, Q=3, P1=4, P2=4, P3=4, Q1=1, Q2=1, Q3=1))
    return grid, transformer


def fixed_options():
    """Keep the reference test independent of reactive and tap limit decisions."""
    return vge.PowerFlowOptions(tolerance=1e-10, max_iter=50, control_q=False,
        retry_with_other_methods=False, control_taps_modules=False,
        control_taps_phase=False, use_stored_guess=False)


def assert_balanced_oracle(grid, options):
    """Compare complex terminal voltages and total three-phase port powers."""
    positive = vge.power_flow(grid, options)
    abc = vge.power_flow3ph(grid, options)
    assert positive.converged and abc.converged
    a = np.exp(2j * np.pi / 3)
    np.testing.assert_allclose(positive.voltage, abc.voltage_A, atol=2e-8, rtol=0)
    np.testing.assert_allclose(positive.voltage, abc.voltage_B * a, atol=2e-8, rtol=0)
    np.testing.assert_allclose(positive.voltage, abc.voltage_C / a, atol=2e-8, rtol=0)
    np.testing.assert_allclose(positive.Sf, abc.Sf_A + abc.Sf_B + abc.Sf_C, atol=2e-6, rtol=0)
    np.testing.assert_allclose(positive.St, abc.St_A + abc.St_B + abc.St_C, atol=2e-6, rtol=0)
    return positive


@pytest.mark.parametrize('clock', (0, 1, 11))
@pytest.mark.parametrize('reverse', (False, True))
def test_loaded_two_winding_matches_balanced_abc(clock: int, reverse: bool):
    """A nonzero mechanical phase neither replaces nor duplicates the clock."""
    grid, transformer = two_winding_grid(clock, reverse)
    assert_balanced_oracle(grid, fixed_options())
    assert transformer.tap_phase == 0.08
    assert transformer.vector_group_number == clock


@pytest.mark.parametrize('clock', (0, 1, 11))
@pytest.mark.parametrize('reverse', (False, True))
def test_no_load_clock_ratio_annuls_both_terminal_currents(clock: int, reverse: bool):
    """Check the nameplate ratio directly, including reversed port orientation."""
    grid, transformer = two_winding_grid(clock, reverse, loaded=False)
    nc = compile_numerical_circuit_at(grid)
    displacement = np.deg2rad(30 * clock) * (-1 if reverse else 1)
    from_voltage = 1.0 + 0.0j
    to_voltage = np.exp(-1j * (0.08 + displacement)) / 1.07
    voltage = np.array((to_voltage, from_voltage) if reverse else (from_voltage, to_voltage))
    admittance = nc.get_admittance_matrices()
    np.testing.assert_allclose(admittance.Yf @ voltage, 0, atol=2e-13)
    np.testing.assert_allclose(admittance.Yt @ voltage, 0, atol=2e-13)
    split = nc.get_series_admittance_matrices()
    np.testing.assert_allclose(split.Yseries @ voltage, 0, atol=2e-13)


def three_winding_grid(clocks):
    """A 3W star has independent terminal clocks relative to its common core."""
    grid = vge.MultiCircuit()
    hv = grid.add_bus(vge.Bus(name='HV', Vnom=110, is_slack=True))
    mv = grid.add_bus(vge.Bus(name='MV', Vnom=33))
    lv = grid.add_bus(vge.Bus(name='LV', Vnom=11))
    grid.add_generator(hv, vge.Generator())
    transformer = vge.Transformer3W(bus1=hv, bus2=mv, bus3=lv, V1=110, V2=33, V3=11,
        r12=0.015, x12=0.15, r23=0.022, x23=0.22, r31=0.017, x31=0.17)
    transformer.compute_delta_to_star()
    transformer.fill_zero_sequence(0.03 + 0.3j, 0.05 + 0.5j, 0.04 + 0.4j)
    for winding, clock in zip((transformer.winding1, transformer.winding2, transformer.winding3), clocks):
        winding.vector_group_number = clock
    grid.add_transformer3w(transformer)
    grid.add_load(mv, vge.Load(P=12, Q=3, P1=4, P2=4, P3=4, Q1=1, Q2=1, Q3=1))
    grid.add_load(lv, vge.Load(P=6, Q=1.5, P1=2, P2=2, P3=2, Q1=0.5, Q2=0.5, Q3=0.5))
    return grid, transformer


@pytest.mark.parametrize('clocks', ((0, 0, 0), (0, 1, 0), (0, 11, 0), (0, 1, 11), (1, 11, 0)))
def test_three_winding_clocks_match_balanced_abc(clocks):
    """A nonzero HV clock changes relative terminal angles rather than a global reference."""
    grid, transformer = three_winding_grid(clocks)
    positive = assert_balanced_oracle(grid, fixed_options())
    baseline_grid, _ = three_winding_grid((0, 0, 0))
    baseline = vge.power_flow(baseline_grid, fixed_options())
    assert baseline.converged
    for bus_index, clock in enumerate(clocks):
        expected = baseline.voltage[bus_index] * np.exp(-1j * np.deg2rad(30 * (clock - clocks[0])))
        np.testing.assert_allclose(positive.voltage[bus_index], expected, atol=2e-8, rtol=0)
    assert tuple(w.vector_group_number for w in (transformer.winding1, transformer.winding2,
                                                transformer.winding3)) == clocks


@pytest.mark.parametrize('reverse', (False, True))
def test_winding_clock_uses_internal_bus_orientation(reverse: bool):
    """A winding is terminal-to-core, independently of its numerical voltage ratings."""
    grid = vge.MultiCircuit()
    external = grid.add_bus(vge.Bus(Vnom=33))
    internal = grid.add_bus(vge.Bus(Vnom=1, is_internal=True))
    winding = vge.Winding(bus_from=internal if reverse else external,
        bus_to=external if reverse else internal, HV=33, LV=1,
        r=0.02, x=0.2, tap_module=1.07, tap_phase=0.08)
    winding.vector_group_number = 1
    grid.add_winding(winding)
    nc = compile_numerical_circuit_at(grid)
    np.testing.assert_array_equal(nc.passive_branch_data.vector_group_number,
                                  (1 if reverse else -1,))
    displacement = np.deg2rad(30) * (1 if reverse else -1)
    to_voltage = np.exp(-1j * (0.08 + displacement)) / 1.07
    voltage = np.array((to_voltage, 1) if reverse else (1, to_voltage))
    np.testing.assert_allclose(nc.get_admittance_matrices().Ybus @ voltage, 0, atol=2e-13)


def test_mechanical_profiles_and_opf_input_remain_separate_from_clock():
    """A fixed clock must not be accumulated into snapshots, profiles or OPF output."""
    grid, transformer = two_winding_grid(11, loaded=False)
    transformer.tap_phase_min, transformer.tap_phase_max = -0.12, 0.12
    grid.create_profiles(steps=2, step_length=1, step_unit='h')
    transformer.tap_phase_prof = np.array((0.03, -0.04))
    before_profile = transformer.tap_phase_prof.toarray().copy()
    phases = (0.03, -0.04, 0.03)
    for index, phase in zip((0, 1, 0), phases):
        nc = compile_numerical_circuit_at(grid, t_idx=index)
        np.testing.assert_allclose(nc.active_branch_data.tap_angle, phase, atol=0)
        np.testing.assert_allclose(nc.active_branch_data.tap_angle_min, -0.12, atol=0)
        np.testing.assert_allclose(nc.active_branch_data.tap_angle_max, 0.12, atol=0)
        voltage = np.array((1, np.exp(-1j * (phase + np.deg2rad(330))) / 1.07))
        np.testing.assert_allclose(nc.get_admittance_matrices().Yf @ voltage, 0, atol=2e-13)
    opf = SimpleNamespace(tap_angle=np.array((0.06,)))
    nc = compile_numerical_circuit_at(grid, opf_results=opf)
    np.testing.assert_allclose(nc.active_branch_data.tap_angle, 0.06, atol=0)
    voltage = np.array((1, np.exp(-1j * (0.06 + np.deg2rad(330))) / 1.07))
    np.testing.assert_allclose(nc.get_admittance_matrices().Yf @ voltage, 0, atol=2e-13)
    np.testing.assert_array_equal(transformer.tap_phase_prof.toarray(), before_profile)
    np.testing.assert_array_equal(opf.tap_angle, (0.06,))
    assert transformer.tap_phase == 0.08 and transformer.vector_group_number == 11


def test_clock_survives_copy_slice_and_repeated_admittance_access():
    """Derived clock data follows island copies without mutating the original model."""
    grid, transformer = two_winding_grid(1, loaded=False)
    nc = compile_numerical_circuit_at(grid)
    reference = nc.get_admittance_matrices().Ybus.toarray()
    np.testing.assert_array_equal(nc.get_admittance_matrices().Ybus.toarray(), reference)
    np.testing.assert_array_equal(nc.active_branch_data.tap_angle, (0.08,))
    copy = nc.copy()
    island = nc.get_island(bus_idx=np.array((1, 0)), logger=Logger())
    np.testing.assert_allclose(copy.get_admittance_matrices().Ybus.toarray(), reference, atol=0)
    np.testing.assert_allclose(island.get_admittance_matrices().Ybus.toarray(), reference[::-1, ::-1], atol=0)
    copied_branches = nc.passive_branch_data.copy()
    sliced_branches = nc.passive_branch_data.slice(np.array((0,)), np.array((1, 0)),
        np.array((1, 0)), Logger())
    np.testing.assert_array_equal(copied_branches.vector_group_number,
                                  nc.passive_branch_data.vector_group_number)
    np.testing.assert_array_equal(sliced_branches.vector_group_number,
                                  nc.passive_branch_data.vector_group_number)
    copied_branches.vector_group_number[0] += 1
    sliced_branches.vector_group_number[0] += 2
    np.testing.assert_array_equal(nc.passive_branch_data.vector_group_number, (1,))
    assert transformer.tap_phase == 0.08 and transformer.vector_group_number == 1


def run_linear_case(grid, route):
    """Exercise both the ordinary driver and the control-aware linear numerical route."""
    if route == 'limited':
        options = vge.PowerFlowOptions(solver_type=vge.SolverType.Linear,
            retry_with_other_methods=False, control_q=False,
            control_taps_modules=False, control_taps_phase=False)
        return vge.power_flow(grid, options)
    nc = compile_numerical_circuit_at(grid, control_taps_modules=False, control_taps_phase=False)
    injections = nc.get_power_injections_pu()
    indices = nc.get_simulation_indices(Sbus=injections)
    admittance = nc.get_linear_admittance_matrices(indices=indices)
    numerical = acdc_lin_pf(nc=nc, Bbus=admittance.Bbus, Bf=admittance.Bf,
        Gbus=admittance.Gbus, Gf=admittance.Gf, ac=indices.ac, dc=indices.dc,
        vd=indices.vd, pv=indices.pv, S0=injections,
        I0=nc.get_current_injections_pu(), Y0=nc.get_admittance_injections_pu(),
        V0=nc.bus_data.Vbus, tau=nc.active_branch_data.tap_angle)
    return SimpleNamespace(converged=numerical.converged, voltage=numerical.V,
        Sf=numerical.Sf, St=numerical.St, tap_angle=numerical.tap_angle,
        tap_module=numerical.tap_module)


@pytest.mark.parametrize('route', ('limited', 'acdc'))
@pytest.mark.parametrize('clock', (0, 1, 11))
@pytest.mark.parametrize('reverse', (False, True))
def test_linear_dc_clock_rotates_voltage_without_changing_radial_transfer(clock: int, reverse: bool, route: str):
    """The DC phase source changes the angle across a radial branch, not its transfer."""
    grid, transformer = two_winding_grid(0, reverse)
    reference = run_linear_case(grid, route)
    transformer.vector_group_number = clock
    shifted = run_linear_case(grid, route)
    assert reference.converged and shifted.converged
    expected = reference.voltage.copy()
    expected[1] *= np.exp(-1j * np.deg2rad(30 * clock))
    np.testing.assert_allclose(shifted.voltage, expected, atol=1e-12, rtol=0)
    np.testing.assert_allclose(shifted.Sf.real, reference.Sf.real, atol=1e-9, rtol=0)
    np.testing.assert_allclose(shifted.St.real, reference.St.real, atol=1e-9, rtol=0)
    np.testing.assert_allclose(abs(shifted.Sf.real), (12.0,), atol=1e-9, rtol=0)
    np.testing.assert_allclose(shifted.tap_angle, (0.08,), atol=0)
    np.testing.assert_allclose(shifted.tap_module, (1.07,), atol=0)
    assert transformer.tap_phase == 0.08 and transformer.vector_group_number == clock


@pytest.mark.parametrize('clock', (1, 11))
@pytest.mark.parametrize('reverse', (False, True))
def test_linear_ac_rejects_clock_instead_of_returning_an_inconsistent_solution(clock: int, reverse: bool):
    """LACPF must expose its unsupported clock model rather than report convergence."""
    grid, transformer = two_winding_grid(clock, reverse)
    options = vge.PowerFlowOptions(solver_type=vge.SolverType.LACPF,
        retry_with_other_methods=False, control_q=False,
        control_taps_modules=False, control_taps_phase=False)
    with pytest.raises(NotImplementedError) as error:
        vge.power_flow(grid, options)
    message = str(error.value)
    assert 'LACPF' in message and 'clock' in message.lower()
    assert 'NR' in message and 'Linear' in message
    assert transformer.vector_group_number == clock and transformer.tap_phase == 0.08


def test_phase_power_control_preserves_fixed_clock_and_mechanical_bounds():
    """Regulate P while preserving another fixed transformer's complete series ratio."""
    grid = vge.MultiCircuit()
    source = grid.add_bus(vge.Bus(name='Source', Vnom=110, is_slack=True))
    junction = grid.add_bus(vge.Bus(name='Junction', Vnom=110))
    target = grid.add_bus(vge.Bus(name='Target', Vnom=110))
    grid.add_generator(source, vge.Generator())
    grid.add_load(target, vge.Load(P=20, Q=5, P1=20/3, P2=20/3, P3=20/3,
                                   Q1=5/3, Q2=5/3, Q3=5/3))
    fixed = vge.Transformer2W(bus_from=source, bus_to=junction, name='Fixed series', HV=110, LV=110,
        r=0.005, x=0.05, r0=0.01, x0=0.1, r2=0.005, x2=0.05,
        tap_module=1.03, tap_phase=0.02)
    fixed.vector_group_number = 11
    grid.add_transformer2w(fixed)
    grid.add_line(vge.Line(bus_from=junction, bus_to=target, name='Parallel', r=0.03, x=0.3))
    transformer = vge.Transformer2W(bus_from=junction, bus_to=target, name='PST', HV=110, LV=110,
        r=0.02, x=0.2, r0=0.04, x0=0.4, r2=0.02, x2=0.2,
        tap_phase=0.05, tap_phase_min=-0.12, tap_phase_max=0.12)
    transformer.vector_group_number = 1
    grid.add_transformer2w(transformer)
    abc = vge.power_flow3ph(grid, fixed_options())
    assert abc.converged
    branch_index = list(abc.branch_names).index('PST')
    transformer.Pset = (abc.Sf_A[branch_index] + abc.Sf_B[branch_index] + abc.Sf_C[branch_index]).real
    transformer.tap_phase = 0.0
    transformer.tap_phase_control_mode = TapPhaseControl.Pf
    options = vge.PowerFlowOptions(tolerance=1e-10, max_iter=50, control_q=False,
        retry_with_other_methods=False, control_taps_modules=False,
        control_taps_phase=True, orthogonalize_controls=False)
    result = vge.power_flow(grid, options)
    assert result.converged
    np.testing.assert_allclose(result.Sf[branch_index].real, transformer.Pset, atol=1e-7)
    np.testing.assert_allclose(result.tap_angle[branch_index], 0.05, atol=1e-8)
    np.testing.assert_allclose(result.voltage, abc.voltage_A, atol=2e-8, rtol=0)
    np.testing.assert_allclose(result.Sf, abc.Sf_A + abc.Sf_B + abc.Sf_C, atol=2e-6, rtol=0)
    np.testing.assert_allclose(result.St, abc.St_A + abc.St_B + abc.St_C, atol=2e-6, rtol=0)
    fixed_index = list(result.branch_names).index('Fixed series')
    np.testing.assert_allclose(result.tap_angle[fixed_index], 0.02, atol=0)
    np.testing.assert_allclose(result.tap_module[fixed_index], 1.03, atol=0)
    assert -0.12 <= result.tap_angle[branch_index] <= 0.12
    assert transformer.tap_phase == 0 and transformer.vector_group_number == 1
    assert fixed.tap_phase == 0.02 and fixed.tap_module == 1.03 and fixed.vector_group_number == 11
