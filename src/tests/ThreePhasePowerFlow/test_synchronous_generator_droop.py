"""Synchronous Q-U1 control reuses k_droop without losing passive sequences."""
import numpy as np
import pytest
import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.IO.dgs.dgs_objects import ElmSym, TypSym
from VeraGridEngine.IO.dgs.dgs_to_veragrid import convert_dgs_to_generator
from VeraGridEngine.IO.dgs.veragrid_to_dgs import convert_generator
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.discrete_controls import QvDroopControlState
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import generator_qv_droop
from tests.ThreePhasePowerFlow.test_3ph_positive_sequence_voltage_control import make_grid, solve, target_voltages


def droop_grid(sbase=100.0, unbalanced=True):
    grid = make_grid(sbase=sbase, unbalanced=unbalanced)
    gen = grid.generators[1]
    gen.control_mode = vge.GeneratorControlMode.QVDroop
    gen.k_droop, gen.Qmax, gen.Qmin, gen.Snom = 40.0, 50.0, -40.0, 60.0
    return grid


@pytest.mark.parametrize('sbase', (25.0, 100.0))
@pytest.mark.parametrize('connection', (vge.ShuntConnectionType.GroundedStar,
                                      vge.ShuntConnectionType.FloatingStar, vge.ShuntConnectionType.Delta))
def test_droop_terminal_power_i0_i2(sbase, connection):
    grid = droop_grid(sbase)
    gen = grid.generators[1]
    gen.conn = connection
    result = solve(grid, control_q=False)
    voltage = target_voltages(result)
    power = np.array((result.Sbus_A[1], result.Sbus_B[1], result.Sbus_C[1]))
    power += np.array((8+3j, 5+2j, 2+1j))
    a = np.exp(2j*np.pi/3)
    transform = np.array(((1, 1, 1), (1, a, a*a), (1, a*a, a))) / 3
    v012 = transform @ voltage
    i012 = transform @ (np.conj(power / voltage) * 3 / sbase)
    expected_q = gen.k_droop*gen.Qmax*(gen.Vset-abs(v012[1]))
    np.testing.assert_allclose(power.sum(), gen.P + 1j*expected_q, atol=1e-6)
    i0 = -v012[0]/complex(gen.R0, gen.X0) if connection == vge.ShuntConnectionType.GroundedStar else 0j
    np.testing.assert_allclose(i012[[0, 2]], (i0, -v012[2]/complex(gen.R2, gen.X2)), atol=2e-8)
    assert abs(v012[2]) > 1e-4


@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM, vge.SolverType.PowellDogLeg))
def test_balanced_droop_matches_abc_and_reports_q(solver):
    grid = droop_grid(unbalanced=False)
    abc = solve(grid, solver=solver, control_q=False)
    positive = vge.power_flow(grid, vge.PowerFlowOptions(solver_type=solver, tolerance=1e-9,
        control_q=False, retry_with_other_methods=False, use_autodiff_jacobian=True, max_iter=100))
    assert positive.converged
    np.testing.assert_allclose(abc.voltage_A, positive.voltage, atol=1e-8)
    gen = grid.generators[1]
    q = gen.k_droop*gen.Qmax*(gen.Vset-abs(positive.voltage[1]))
    np.testing.assert_allclose(positive.gen_q[1], q, atol=1e-6)
    np.testing.assert_allclose(positive.Sbus[1] + 15 + 6j, gen.P + 1j*q, atol=1e-6)


def test_droop_roundtrip_compilation_and_legacy(tmp_path):
    grid = droop_grid()
    nc = compile_numerical_circuit_at(grid)
    np.testing.assert_array_equal(nc.generator_data.copy().k_droop, nc.generator_data.k_droop)
    sliced = nc.generator_data.slice(np.array((1,)), np.arange(2), np.arange(2))
    assert sliced.k_droop[0] == 40.0
    assert not hasattr(nc.generator_data, "droop")
    assert QvDroopControlState(nc.get_power_injections_pu(), nc).apply(
        nc.get_power_injections_pu(), np.array((1., .98)))
    filename = str(tmp_path/'droop.veragrid')
    vge.save_file(grid, filename)
    restored = vge.open_file(filename)
    assert restored.generators[1].k_droop == 40.0
    assert "droop" not in restored.generators[1].registered_properties
    assert "droop" not in vge.Battery().registered_properties
    np.testing.assert_allclose(target_voltages(solve(restored)), target_voltages(solve(grid)))
    # Existing gain/dead-band/Qmax data keep their existing discrete-control law.
    gen = grid.generators[1]
    gen.k_droop, gen.dead_band, gen.Qmax, gen.Qmin = 10.0, .005, 40.0, -30.0
    nc = compile_numerical_circuit_at(grid)
    powers = nc.get_power_injections_pu()
    before = powers.imag.copy()
    QvDroopControlState(powers, nc).apply(powers, np.array((1., .98)))
    np.testing.assert_allclose(powers.imag[1]-before[1], (.03-.005)*10*40/grid.Sbase)


def test_dgs_synchronous_droop_roundtrip_and_missing_input():
    original = droop_grid().generators[1]
    typ, source = convert_generator(original, 't', 'g', 100, None)
    typ = TypSym.parse_line(typ.to_dgs_line(), {p.name:i for i,p in enumerate(TypSym.properties_list)})
    source = ElmSym.parse_line(source.to_dgs_line(), {p.name:i for i,p in enumerate(ElmSym.properties_list)})
    _, restored = convert_dgs_to_generator(source, {'g':[0]}, [original.bus], {'t':typ},
                                          100, vge.Logger(), {}, {})
    assert restored.control_mode == vge.GeneratorControlMode.QVDroop
    np.testing.assert_allclose((restored.k_droop, restored.Vset, restored.Snom),
                               (original.k_droop, original.Vset, original.Snom))
    source.ddroop = None
    source.qgini = 7.0
    logger = vge.Logger()
    _, legacy = convert_dgs_to_generator(source, {'g':[0]}, [original.bus], {'t':typ},
                                         100, logger, {}, {})
    assert legacy.control_mode == vge.GeneratorControlMode.Q
    assert (legacy.P, legacy.Q, legacy.Vset) == pytest.approx((source.pgini, source.qgini, source.usetp))
    assert any(entry.device == legacy.name and 'Missing ElmSym ddroop' in entry.msg
               for entry in logger.entries)
    for invalid in (0.0, -3.0, np.nan):
        source.ddroop = invalid
        with pytest.raises(ValueError, match='positive ElmSym ddroop'):
            convert_dgs_to_generator(source, {'g':[0]}, [original.bus], {'t':typ}, 100, vge.Logger(), {}, {})
    source.ddroop = 3.0
    with pytest.raises(ValueError, match='positive TypSym sgn'):
        convert_dgs_to_generator(source, {'g':[0]}, [original.bus], {}, 100, vge.Logger(), {}, {})


def test_colocated_droop_types_and_pv_share_results_without_double_counting():
    grid = droop_grid(unbalanced=False)
    grid.add_static_generator(grid.buses[1], vge.StaticGenerator(P=2, Q=1, Snom=10,
        control_mode=vge.StaticGeneratorControlMode.QVDroop, vset=1.01, droop=4))
    grid.add_controllable_shunt(grid.buses[1], vge.ControllableShunt(
        control_mode=vge.ShuntControlMode.QVDroop, vset=1.01, droop=5, Snom=10))
    grid.add_generator(grid.buses[1], vge.Generator(P=2, vset=1.005,
        r0=.01, x0=.08, r2=.02, x2=.10))
    positive = vge.power_flow(grid, vge.PowerFlowOptions(tolerance=1e-9, control_q=False,
        retry_with_other_methods=False, use_autodiff_jacobian=True))
    assert positive.converged
    abc = solve(grid, control_q=False)
    np.testing.assert_allclose(abc.voltage_A, positive.voltage, atol=1e-8)
    expected_q = 100*60/3*(1.01-1.005)
    np.testing.assert_allclose(positive.gen_q[1], expected_q, atol=1e-6)
    # PV must supply exactly the remainder after all three droop devices.
    other_q = (1+100*10/4*.005) + (100*10/5*.005)
    np.testing.assert_allclose(positive.gen_q[1:].sum()+other_q-6, positive.Sbus[1].imag, atol=1e-6)


def test_droop_retains_ideal_u0():
    grid = droop_grid()
    gen = grid.generators[1]
    gen.R0 = gen.X0 = 0.0
    result = solve(grid, control_q=False)
    voltage = target_voltages(result)
    np.testing.assert_allclose(voltage.mean(), 0, atol=1e-9)
    power = np.array((result.Sbus_A[1], result.Sbus_B[1], result.Sbus_C[1])) + np.array((8+3j, 5+2j, 2+1j))
    a = np.exp(2j*np.pi/3)
    v1 = voltage @ np.array((1, a, a*a)) / 3
    expected_q = gen.k_droop*gen.Qmax*(gen.Vset-abs(v1))
    np.testing.assert_allclose(power.sum(), gen.P+1j*expected_q, atol=1e-6)


@pytest.mark.parametrize('qref', (0.0, 8.0, -5.0))
@pytest.mark.parametrize('sbase', (25.0, 100.0))
def test_parser_converts_pf_percentage_and_q_reference_to_existing_gain(qref, sbase):
    gen = droop_grid(sbase).generators[1]
    typ, source = convert_generator(gen, 't', 'g', sbase, None)
    source.qgini, source.usetp, source.ddroop = qref, 1.01, 3.0
    bus, imported = convert_dgs_to_generator(source, {'g':[0]}, [gen.bus], {'t':typ},
                                           sbase, vge.Logger(), {}, {})
    imported.bus = bus
    assert imported.k_droop == pytest.approx(40.0)
    assert imported.Vset == pytest.approx(1.01 + qref / 2000.0)
    assert imported.Vset_prof.default_value == pytest.approx(imported.Vset)
    assert (imported.Qmin, imported.Qmax) == (gen.Qmin, gen.Qmax)
    for voltage in (.97, 1.0, 1.01, 1.02, 1.05):
        expected = np.clip(qref + 2000*(1.01-voltage), gen.Qmin, gen.Qmax)
        actual = generator_qv_droop(voltage, imported.Vset, imported.k_droop,
                                   imported.dead_band, imported.Qmin, imported.Qmax)
        assert actual == pytest.approx(expected, abs=1e-10)
    # The inverse conversion preserves the physical curve, not the original intercept convention.
    exported_type, exported = convert_generator(imported, 't', 'g', sbase, None)
    assert exported.qgini == 0.0
    assert exported.ddroop == pytest.approx(3.0)
    _, again = convert_dgs_to_generator(exported, {'g':[0]}, [gen.bus], {'t':exported_type},
                                      sbase, vge.Logger(), {}, {})
    assert again.Vset == pytest.approx(imported.Vset)
    assert again.k_droop == pytest.approx(imported.k_droop)
    source.q_max = 0.0
    with pytest.raises(ValueError, match='positive finite Qmax'):
        convert_dgs_to_generator(source, {'g':[0]}, [gen.bus], {'t':typ}, sbase, vge.Logger(), {}, {})


@pytest.mark.parametrize('vset', (.94, .999, 1.0, 1.001, 1.06))
def test_same_dead_band_and_q_limits_in_balanced_and_abc(vset):
    grid = droop_grid(unbalanced=False)
    gen = grid.generators[1]
    gen.Vset, gen.dead_band = vset, .005
    gen.Qmin, gen.Qmax = -10., 10.
    # A colocated PV keeps U1=1 so this checks both limits and the dead band exactly.
    grid.add_generator(grid.buses[1], vge.Generator(P=0, vset=1,
        r0=.01, x0=.08, r2=.02, x2=.1))
    abc = solve(grid, control_q=False)
    positive = vge.power_flow(grid, vge.PowerFlowOptions(tolerance=1e-9, control_q=False,
        retry_with_other_methods=False, use_autodiff_jacobian=True))
    assert positive.converged
    np.testing.assert_allclose(abc.voltage_A, positive.voltage, atol=1e-8)
    dv = vset - 1.0
    expected = np.clip(np.sign(dv)*max(abs(dv)-.005, 0)*40*10, -10, 10)
    assert positive.gen_q[1] == pytest.approx(expected, abs=1e-6)
