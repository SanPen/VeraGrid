"""Common-mode references preserve physical KCL and resolved earth paths."""
import numpy as np
from scipy.sparse import csc_matrix
import pytest
from scipy.optimize import root
import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations import pf_basic_formulation_3ph as abc
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.pf_basic_formulation_3ph import (
    PfBasicFormulation3Ph, expand3ph, expandVoltage3ph, compute_power_loads, compute_current_loads)
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.newton_raphson_fx import newton_raphson_fx


@pytest.fixture
def explicit_passive_nodes(monkeypatch) -> None:
    """Exercise the aggregate balance rows independently of passive-node elimination."""
    monkeypatch.setattr(abc, 'passive_neutral_reduction',
                        lambda nc, ybus, mask: (np.arange(ybus.shape[0]), None))


def floating_grid(explicit_neutral: bool = False) -> vge.MultiCircuit:
    """Build a supplied, unbalanced feeder whose two downstream buses share a free reference.

    :param explicit_neutral: Use a floating N conductor and phase-to-neutral powers.
    :return: Three-bus feeder with physical nonzero zero-sequence series impedances.
    """
    grid: vge.MultiCircuit = vge.MultiCircuit()
    source: vge.Bus = grid.add_bus(vge.Bus(name='Slack', Vnom=110, is_slack=True))
    first: vge.Bus = grid.add_bus(vge.Bus(name='First', Vnom=11))
    second: vge.Bus = grid.add_bus(vge.Bus(name='Second', Vnom=11))
    grid.add_generator(source, vge.Generator())
    transformer: vge.Transformer2W = vge.Transformer2W(bus_from=source, bus_to=first,
        HV=110, LV=11, r=0.01, x=0.1, r0=0.02, x0=0.12, r2=0.01, x2=0.1, g0=0, b0=0)
    transformer.conn_f = vge.WindingType.Delta
    transformer.conn_t = vge.WindingType.Delta
    grid.add_transformer2w(transformer)
    line: vge.Line = vge.Line(bus_from=first, bus_to=second, r=0.01, x=0.03, r0=0.03, x0=0.07,
                              b=0, b0=0, b2=0)
    if explicit_neutral:
        line.disable_auto_updates()
        line.ys.values = np.diag(1/np.array((0.02+0.04j, 0.01+0.03j, 0.012+0.032j, 0.014+0.035j)))
        line.ys.phN = True
        line.ys.phA = line.ys.phB = line.ys.phC = True
        line.ysh.values = np.zeros((4, 4), dtype=complex)
    else:
        pass
    grid.add_line(line)
    load: vge.Load = vge.Load(P=12, Q=3, P1=6, P2=4, P3=2, Q1=1, Q2=0.5, Q3=1.5)
    load.conn = vge.ShuntConnectionType.NeutralStar if explicit_neutral else vge.ShuntConnectionType.Delta
    grid.add_load(second, load)
    return grid


def formulation(grid: vge.MultiCircuit, shift: complex = 0j,
                nc: NumericalCircuit | None = None) -> PfBasicFormulation3Ph:
    """Use the production compiler and formulation with an optional displaced initial guess.

    :param grid: Physical device model.
    :param shift: Common initial displacement of all downstream NABC conductors.
    :param nc: Optional already compiled physical model.
    :return: Existing Newton formulation.
    """
    if nc is None:
        nc = compile_numerical_circuit_at(grid, fill_three_phase=True)
    else:
        pass
    nc.get_simulation_indices(Sbus=nc.get_power_injections_pu())
    qmax, qmin = nc.get_reactive_power_limits()
    voltage: np.ndarray = expandVoltage3ph(nc.bus_data.Vbus)
    voltage[4:] += shift
    return PfBasicFormulation3Ph(V0=voltage, S0=expand3ph(nc.get_power_injections_pu()),
        Qmin=qmin, Qmax=qmax, nc=nc, options=vge.PowerFlowOptions(control_q=False,
        control_taps_modules=False, control_taps_phase=False, tolerance=1e-9), logger=vge.Logger())


@pytest.mark.parametrize('shift', (0j, 0.03+0.02j, -0.02+0.04j))
def test_group_reference_and_original_kcl(shift: complex) -> None:
    """Recover identical physical voltages from different common-mode initial guesses.

    :param shift: Arbitrary initial common-mode displacement.
    """
    grid: vge.MultiCircuit = floating_grid()
    problem: PfBasicFormulation3Ph = formulation(grid, shift)
    assert len(problem.common_mode.phases) == 1
    result = newton_raphson_fx(problem, tol=1e-9, max_iter=40, logger=vge.Logger())
    assert result.converged
    np.testing.assert_allclose(np.mean(problem.V[problem.common_mode.phases]), 0, atol=1e-9)
    # Independently evaluate all original complex current equations, including the replaced phase.
    power, _, _ = compute_power_loads(problem.nc.load_data.bus_idx, problem.bus_lookup, problem.V,
        problem.nc.load_data.S3_star, problem.nc.load_data.S3_floatingstar, problem.nc.load_data.S3_delta)
    current, _, _ = compute_current_loads(problem.nc.load_data.bus_idx, problem.bus_lookup, problem.V,
        problem.nc.load_data.I3_star, problem.nc.load_data.I3_delta, problem.nc.load_data.I3_floatingstar)
    injected: np.ndarray = problem.generator_currents(problem.V, problem.positive_sequence.q)+power+current
    mismatch: np.ndarray = problem.Ybus @ problem.V - injected/(grid.Sbase/3)
    np.testing.assert_allclose(mismatch[problem.no_slack], 0, atol=2e-9)
    baseline = vge.power_flow3ph(grid, options=vge.PowerFlowOptions(control_q=False,
        tolerance=1e-9, retry_with_other_methods=False))
    expected: np.ndarray = np.column_stack((baseline.voltage_N, baseline.voltage_A,
                                           baseline.voltage_B, baseline.voltage_C)).ravel()
    np.testing.assert_allclose(result.V, expected, atol=1e-8)


@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM, vge.SolverType.PowellDogLeg))
def test_existing_solvers_with_floating_group(solver: vge.SolverType) -> None:
    """Keep all existing numerical methods, including their original convergence checks.

    :param solver: Existing method, with fallback disabled.
    """
    result = vge.power_flow3ph(floating_grid(), options=vge.PowerFlowOptions(solver_type=solver,
        control_q=False, tolerance=1e-9, max_iter=100, retry_with_other_methods=False))
    assert result.converged
    assert np.max(abs(result.voltage_A+result.voltage_B+result.voltage_C)) < 1e-8


@pytest.mark.parametrize('admittance', (1.0, 1e-12, 1e-25))
def test_finite_earth_paths_and_opposite_shunts(admittance: float) -> None:
    """A tiny earth path or cancelling earth shunts must never become a floating reference.

    :param admittance: Phase-to-earth conductance, including values below aggregate roundoff.
    """
    grid: vge.MultiCircuit = floating_grid()
    grid.add_shunt(grid.buses[2], vge.Shunt(G1=admittance))
    assert len(formulation(grid).common_mode.phases) == 0
    grid.add_shunt(grid.buses[2], vge.Shunt(G1=-admittance))
    assert len(formulation(grid).common_mode.phases) == 0


def test_weak_line_charging_and_grounded_load() -> None:
    """Use declared shunt data even when series terms mask it, and protect earth-based powers.

    :return: None.
    """
    grid: vge.MultiCircuit = floating_grid()
    grid.lines[0].B0 = 1e-25
    assert len(formulation(grid).common_mode.phases) == 0
    grid.lines[0].B0 = 0
    grid.loads[0].conn = vge.ShuntConnectionType.GroundedStar
    assert len(formulation(grid).common_mode.phases) == 0


@pytest.mark.parametrize('connection', (vge.ShuntConnectionType.FloatingStar, vge.ShuntConnectionType.GroundedStar))
def test_u1_generator_connection(connection: vge.ShuntConnectionType) -> None:
    """A U1 control leaves U0 free only when the physical generator connection blocks I0.

    :param connection: Actual passive zero-sequence return path.
    """
    grid: vge.MultiCircuit = floating_grid()
    gen: vge.Generator = vge.Generator(P=2, vset=1.0, r0=1e20, x0=0, r2=0.02, x2=0.1)
    gen.conn = connection
    grid.add_generator(grid.buses[2], gen)
    expected: int = 1 if connection == vge.ShuntConnectionType.FloatingStar else 0
    assert len(formulation(grid).common_mode.phases) == expected


@pytest.mark.parametrize('connection, r0, references', (
    (vge.ShuntConnectionType.GroundedStar, 1.0, 0),
    (vge.ShuntConnectionType.GroundedStar, 1e6, 0),
    (vge.ShuntConnectionType.GroundedStar, 1e25, 1),
    (vge.ShuntConnectionType.FloatingStar, 1.0, 1),
    (vge.ShuntConnectionType.Delta, 1.0, 1)))
def test_static_generator_sequence_path_from_abc(connection: vge.ShuntConnectionType,
                                                 r0: float, references: int) -> None:
    """Infer the I0 path from the compiled ABC matrix, including after copying or slicing.

    :param connection: Static-generator winding connection.
    :param r0: Zero-sequence resistance; 1e25 makes Y0 unresolvable beside Y2 in ABC.
    :param references: Number of free common-mode references in the compiled model.
    """
    grid: vge.MultiCircuit = floating_grid()
    gen: vge.StaticGenerator = vge.StaticGenerator(P=1, r0=r0, x0=0, r2=0.01, x2=0.1)
    gen.conn = connection
    grid.add_static_generator(grid.buses[2], gen)
    problem: PfBasicFormulation3Ph = formulation(grid)
    assert len(problem.common_mode.phases) == references
    nc: NumericalCircuit
    for nc in (problem.nc.copy(), problem.nc.split_into_islands()[0]):
        np.testing.assert_array_equal(nc.load_data.Y3_star, problem.nc.load_data.Y3_star)
        assert len(formulation(grid, nc=nc).common_mode.phases) == references


def test_fault_recompilation_removes_reference() -> None:
    """A newly connected phase-to-earth fault determines the previously free common mode.

    :return: None.
    """
    grid: vge.MultiCircuit = floating_grid()
    assert len(formulation(grid).common_mode.phases) == 1
    grid.add_shunt(grid.buses[2], vge.Shunt(name='A-earth fault', G1=100))
    assert len(formulation(grid).common_mode.phases) == 0


@pytest.mark.parametrize('shift', (0j, 0.03+0.02j))
def test_explicit_neutral_and_passive_reconstruction(shift: complex) -> None:
    """Translate N with ABC and retain the original neutral current balances.

    :param shift: Initial common displacement of the floating four-wire feeder.
    """
    grid: vge.MultiCircuit = floating_grid(explicit_neutral=True)
    nc: NumericalCircuit = compile_numerical_circuit_at(grid, fill_three_phase=True)
    # The existing NeutralStar load compiler includes a 1e-4 neutral-earth term.
    # Respect it, then explicitly build an ungrounded numerical fixture for this test.
    assert len(formulation(grid, shift, nc.copy()).common_mode.phases) == 0
    nc.load_data.Y3_star[0, 0] = 0
    problem: PfBasicFormulation3Ph = formulation(grid, shift, nc)
    assert len(problem.common_mode.phases) == 1
    assert problem.voltage_lift is not None
    # Verify the invariance itself before solving: the first neutral is reconstructed
    # and the loaded neutral remains nonlinear. Neither may provide an earth reference.
    full_y: csc_matrix = problem.Ybus_full
    mask: np.ndarray = problem.bus_lookup_full >= 0
    lookup: np.ndarray = problem.bus_lookup_full
    voltage: np.ndarray = problem.voltage_lift @ problem.V
    power, _, _ = compute_power_loads(nc.load_data.bus_idx, lookup, voltage,
        nc.load_data.S3_star, nc.load_data.S3_floatingstar, nc.load_data.S3_delta)
    translated: np.ndarray = problem.V.copy()
    translated[problem.no_slack] += 0.1+0.05j
    translated = problem.voltage_lift @ translated
    shifted_power, _, _ = compute_power_loads(nc.load_data.bus_idx, lookup, translated,
        nc.load_data.S3_star, nc.load_data.S3_floatingstar, nc.load_data.S3_delta)
    np.testing.assert_allclose(shifted_power, power, atol=1e-12)
    np.testing.assert_allclose(full_y @ (translated-voltage), 0, atol=1e-12)
    np.testing.assert_allclose(voltage[lookup[4]], voltage[lookup[8]], atol=1e-12)


def test_independent_groups_get_independent_references() -> None:
    """A delta winding separates two common modes even within one supplied AC island.

    :return: None.
    """
    grid: vge.MultiCircuit = floating_grid()
    grid.lines.clear()
    transformer: vge.Transformer2W = vge.Transformer2W(bus_from=grid.buses[1], bus_to=grid.buses[2],
        HV=11, LV=11, r=0.01, x=0.1, r0=0.02, x0=0.12, r2=0.01, x2=0.1, g0=0, b0=0)
    transformer.conn_f = transformer.conn_t = vge.WindingType.Delta
    grid.add_transformer2w(transformer)
    problem: PfBasicFormulation3Ph = formulation(grid, 0.02+0.03j)
    assert len(problem.common_mode.phases) == 2
    result = newton_raphson_fx(problem, tol=1e-9, max_iter=40, logger=vge.Logger())
    assert result.converged
    np.testing.assert_allclose(np.mean(problem.V[problem.common_mode.phases], axis=1), 0, atol=1e-9)


def weak_passive_grid(charging: float = 1e-4) -> vge.MultiCircuit:
    """Supply a passive delta-bounded line with unequal, finite phase-earth capacitances."""
    grid = floating_grid()
    grid.loads.clear()
    line = grid.lines[0]
    line.R2, line.X2 = line.R, line.X
    # Materialize the existing sequence-based series stamp before editing just the shunt.
    series = line.ys
    shunt = line.ysh
    line.disable_auto_updates()
    line.ys = series
    # Line.ysh stores the pu shunt scaled by 1e6, reversed by the existing compiler.
    shunt.values = np.diag(np.array((0, 1, 1.2, 0.8)) * charging * 1e6j)
    line.ysh = shunt
    return grid


@pytest.mark.parametrize('charging', (1e-3, 1e-5))
@pytest.mark.parametrize('shift', (0j, 0.05+0.03j))
def test_passive_balance_preserves_finite_u0_and_original_kcl(charging: float, shift: complex,
                                                            explicit_passive_nodes) -> None:
    """Match an independent linear solve, including its nonzero U0, without altering Ybus."""
    grid = weak_passive_grid(charging)
    problem = formulation(grid, shift)
    assert len(problem.common_mode.phases) == 0
    assert len(problem.common_mode.balance_real_rows) == 1
    original_y = problem.Ybus.copy()
    unknown = problem.no_slack
    known = np.setdiff1d(np.arange(len(problem.V)), unknown)
    expected = np.linalg.solve(original_y[unknown, :][:, unknown].toarray(),
                               -original_y[unknown, :][:, known] @ problem.V[known])
    # Even when the normalized aggregate is small, every original KCL is still checked.
    original_error = np.max(abs(original_y @ problem.V)[unknown])
    assert problem.check_error(problem.var2x())[0] >= original_error / np.sqrt(2) - 1e-12
    # Explicitly requesting the analytic path must still differentiate the replaced rows.
    # The analytic path now differs from the diagnostic implementation.
    # A central oracle avoids the one-sided 1e-8 truncation/roundoff error.
    point: np.ndarray = problem.var2x().copy()
    analytic: np.ndarray = problem.Jacobian(False).toarray()
    reference: np.ndarray = np.empty(analytic.shape)
    step: float = 1e-6
    column: int
    for column in range(len(point)):
        plus: np.ndarray = point.copy()
        minus: np.ndarray = point.copy()
        plus[column] += step
        minus[column] -= step
        reference[:, column] = (problem.compute_f(plus) - problem.compute_f(minus)) / (2.0 * step)
    np.testing.assert_allclose(analytic, reference, rtol=1e-7, atol=2e-8)
    result = newton_raphson_fx(problem, tol=1e-9, max_iter=20, logger=vge.Logger())
    assert result.converged
    np.testing.assert_allclose(problem.V[unknown], expected, atol=2e-8, rtol=0)
    np.testing.assert_allclose((original_y @ problem.V)[unknown], 0, atol=2e-9)
    assert abs(np.mean(problem.V[unknown[:3]])) > 0.01
    np.testing.assert_array_equal(problem.Ybus.toarray(), original_y.toarray())


@pytest.mark.parametrize('kind', ('load', 'static_generator', 'generator', 'battery', 'shunt'))
def test_passive_balance_excludes_active_devices(kind: str, explicit_passive_nodes) -> None:
    """Do not replace injected-current balances by a zero-injection group balance."""
    grid = weak_passive_grid()
    device = {'load': vge.Load(P=1), 'static_generator': vge.StaticGenerator(P=1),
              'generator': vge.Generator(P=1, r0=0.01, x0=0.1, r2=0.01, x2=0.1),
              'battery': vge.Battery(P=1, r0=0.01, x0=0.1, r2=0.01, x2=0.1),
              'shunt': vge.Shunt(G1=1)}[kind]
    getattr(grid, 'add_' + kind)(grid.buses[2], device)
    assert len(formulation(grid).common_mode.balance_real_rows) == 0
    device.active = False
    assert len(formulation(grid).common_mode.balance_real_rows) == 1


def test_passive_balance_does_not_amplify_roundoff_or_fix_free_voltage() -> None:
    """A free mode uses the existing reference; unresolved finite charging is not amplified."""
    grid = floating_grid()
    grid.loads.clear()
    problem = formulation(grid)
    assert len(problem.common_mode.phases) == 1
    assert len(problem.common_mode.balance_real_rows) == 0
    grid.lines[0].B0 = 1e-25
    problem = formulation(grid)
    assert len(problem.common_mode.phases) == 0
    assert len(problem.common_mode.balance_real_rows) == 0


def test_passive_balance_with_independent_groups_and_reordered_buses(explicit_passive_nodes) -> None:
    """Detect groups from electrical connectivity, independently of names and bus ordering."""
    grid = weak_passive_grid()
    third = grid.add_bus(vge.Bus(name='Third', Vnom=11))
    fourth = grid.add_bus(vge.Bus(name='Fourth', Vnom=11))
    transformer = vge.Transformer2W(bus_from=grid.buses[0], bus_to=third,
        HV=110, LV=11, r=0.01, x=0.1, r0=0.02, x0=0.12, r2=0.01, x2=0.1, g0=0, b0=0)
    transformer.conn_f = transformer.conn_t = vge.WindingType.Delta
    grid.add_transformer2w(transformer)
    grid.add_line(vge.Line(bus_from=third, bus_to=fourth, r=0.01, x=0.03,
        r0=0.03, x0=0.07, r2=0.01, x2=0.03, b=1e-4, b0=1e-4, b2=1e-4))
    for bus in grid.buses:
        bus.name = 'Same name'
    grid.buses.reverse()
    problem = formulation(grid)
    assert len(problem.common_mode.balance_real_rows) == 2
    result = newton_raphson_fx(problem, tol=1e-9, max_iter=20, logger=vge.Logger())
    assert result.converged
    np.testing.assert_allclose((problem.Ybus @ problem.V)[problem.no_slack], 0, atol=2e-9)


@pytest.mark.parametrize('charging', (1e-3, 1e-5))
@pytest.mark.parametrize('shift', (0j, 0.05+0.03j))
def test_reduced_passive_group_preserves_finite_u0_and_original_kcl(charging: float, shift: complex) -> None:
    """Reconstruct the weakly grounded network and compare with its original linear equations."""
    grid = weak_passive_grid(charging)
    problem = formulation(grid, shift)
    original_y: csc_matrix = problem.Ybus_full
    mask: np.ndarray = problem.bus_lookup_full >= 0
    lookup: np.ndarray = problem.bus_lookup_full
    untouched_y = original_y.copy()
    known = lookup[1:4]
    unknown = np.setdiff1d(np.arange(original_y.shape[0]), known)
    initial = expandVoltage3ph(problem.nc.bus_data.Vbus)[mask]
    expected = np.linalg.solve(original_y[unknown, :][:, unknown].toarray(),
                               -original_y[unknown, :][:, known] @ initial[known])
    assert problem.voltage_lift is not None
    assert len(problem.no_slack) == 0
    result = newton_raphson_fx(problem, tol=1e-9, max_iter=20, logger=vge.Logger())
    assert result.converged
    reconstructed = problem.voltage_lift @ problem.V
    np.testing.assert_allclose(reconstructed[unknown], expected, atol=2e-8, rtol=0)
    np.testing.assert_allclose(result.V[mask], reconstructed, atol=1e-12, rtol=0)
    np.testing.assert_allclose((original_y @ reconstructed)[unknown], 0, atol=2e-9, rtol=0)
    assert abs(np.mean(reconstructed[unknown[:3]])) > 0.01
    np.testing.assert_array_equal(original_y.toarray(), untouched_y.toarray())


@pytest.mark.parametrize('sbase, reverse', ((25.0, False), (100.0, False), (100.0, True)))
def test_weak_zero_sequence_coupling_still_has_one_free_group(sbase: float, reverse: bool,
                                                            explicit_passive_nodes) -> None:
    """Strong ABC stamps cannot turn a weak interbus I0 path into an earth reference."""
    grid = floating_grid()
    grid.Sbase = sbase
    factor = sbase / 100.0
    grid.lines[0].R, grid.lines[0].X = 0.03, 0.07
    for branch in (*grid.lines, *grid.transformers2w):
        for parameter in ('R', 'X', 'R0', 'X0', 'R2', 'X2'):
            setattr(branch, parameter, getattr(branch, parameter) * factor)
    # This changes the interbus I0 impedance, but there is no earth return anywhere.
    grid.lines[0].R0 = 999.0 * factor
    grid.lines[0].X0 = 999.0 * factor
    if reverse:
        grid.buses.reverse()
        for bus in grid.buses:
            bus.name = 'Same name'
    problem = formulation(grid)
    assert len(problem.common_mode.phases) == 1
    assert len(problem.common_mode.balance_real_rows) == 0
    problem.V[problem.no_slack] += 0.03 + 0.02j
    problem.Vm[:] = np.abs(problem.V)
    problem.Va[:] = np.angle(problem.V)
    result = newton_raphson_fx(problem, tol=1e-9, max_iter=30, logger=vge.Logger())
    assert result.converged
    np.testing.assert_allclose(np.mean(problem.V[problem.common_mode.phases]), 0, atol=1e-9)
    power, _, _ = compute_power_loads(problem.nc.load_data.bus_idx, problem.bus_lookup, problem.V,
        problem.nc.load_data.S3_star, problem.nc.load_data.S3_floatingstar, problem.nc.load_data.S3_delta)
    mismatch = problem.Ybus @ problem.V - power / (sbase / 3)
    np.testing.assert_allclose(mismatch[problem.no_slack], 0, atol=2e-9)
    # Translate both downstream ABC terminals: all branch currents must be unchanged.
    translated = problem.V.copy()
    translated[problem.no_slack] += 0.1 - 0.07j
    np.testing.assert_allclose(problem.Ybus @ (translated - problem.V), 0, atol=2e-12)


@pytest.mark.parametrize('earth_path', ('line_charging', 'shunt', 'grounded_power'))
def test_weak_zero_sequence_coupling_keeps_real_earth_paths(earth_path: str,
                                                         explicit_passive_nodes) -> None:
    """The numerical free-mode tolerance must not erase declared tiny earth paths."""
    grid = floating_grid()
    grid.lines[0].R, grid.lines[0].X = 0.03, 0.07
    grid.lines[0].R0 = grid.lines[0].X0 = 999.0
    if earth_path == 'line_charging':
        grid.lines[0].B0 = 1e-25
    elif earth_path == 'shunt':
        grid.add_shunt(grid.buses[2], vge.Shunt(G1=1e-25))
    else:
        grid.loads[0].conn = vge.ShuntConnectionType.GroundedStar
    assert len(formulation(grid).common_mode.phases) == 0


@pytest.mark.parametrize('kind', ('delta_admittance', 'delta_power', 'floating_static'))
@pytest.mark.parametrize('sbase', (25.0, 100.0))
def test_zero_sum_injections_keep_the_physical_weak_earth_balance(kind: str, sbase: float) -> None:
    """Retain finite nonzero U0 with active three-wire injections and original full KCL."""
    grid = weak_passive_grid(charging=1e-5)
    target = grid.buses[2]
    grid.Sbase = sbase
    factor = sbase / 100.0
    transformer = grid.transformers2w[0]
    for parameter in ('R', 'X', 'R0', 'X0', 'R2', 'X2'):
        setattr(transformer, parameter, getattr(transformer, parameter) * factor)
    grid.lines[0].ys.values /= factor
    grid.lines[0].ysh.values /= factor
    if kind == 'delta_admittance':
        load = vge.Load(G1=6, G2=4, G3=2, B1=-1, B2=-0.5, B3=-1.5)
        load.conn = vge.ShuntConnectionType.Delta
        grid.add_load(target, load)
    elif kind == 'delta_power':
        load = vge.Load(P=12, Q=3, P1=6, P2=4, P3=2, Q1=1, Q2=0.5, Q3=1.5)
        load.conn = vge.ShuntConnectionType.Delta
        grid.add_load(target, load)
    else:
        generator = vge.StaticGenerator(P=3, Q=1, r2=0.02 * factor, x2=0.1 * factor)
        generator.conn = vge.ShuntConnectionType.FloatingStar
        grid.add_static_generator(target, generator)
    problem = formulation(grid, shift=0.04 + 0.03j)
    assert len(problem.common_mode.phases) == 0
    assert len(problem.common_mode.balance_real_rows) == 1
    original_y: csc_matrix = problem.Ybus_full
    mask: np.ndarray = problem.bus_lookup_full >= 0
    lookup: np.ndarray = problem.bus_lookup_full
    original_y = original_y.copy()
    target_phases = lookup[9:12]
    known = lookup[1:4]
    unknown = np.setdiff1d(np.arange(original_y.shape[0]), known)
    initial = expandVoltage3ph(problem.nc.bus_data.Vbus)[mask]
    rotation = np.exp(-2j * np.pi / 3 * np.arange(3))

    def physical_current(voltage: np.ndarray) -> np.ndarray:
        """Device terminal currents from complex powers and phase-to-phase voltages."""
        injected = np.zeros(len(voltage), dtype=complex)
        terminal = voltage[target_phases]
        if kind == 'delta_power':
            branch_current = np.conj(np.array((6 + 1j, 4 + 0.5j, 2 + 1.5j)) /
                                     (terminal - np.roll(terminal, -1))) * 3 / sbase
            injected[target_phases] = np.roll(branch_current, 1) - branch_current
        elif kind == 'floating_static':
            v1 = terminal @ rotation.conj() / 3
            injected[target_phases] = np.conj((3 + 1j) / sbase / v1) * rotation
        return injected

    # Solve the untouched terminal equations in Cartesian coordinates, independently
    # of the production polar residual and its normalized aggregate balance.
    def residual(values: np.ndarray) -> np.ndarray:
        voltage = initial.copy()
        voltage[unknown] = values[:len(unknown)] + 1j * values[len(unknown):]
        current = (original_y @ voltage - physical_current(voltage))[unknown]
        return np.r_[current.real, current.imag]

    if kind == 'delta_admittance':
        expected = np.linalg.solve(original_y[unknown, :][:, unknown].toarray(),
                                   -original_y[unknown, :][:, known] @ initial[known])
    else:
        reference = root(residual, np.r_[initial[unknown].real, initial[unknown].imag], tol=1e-11)
        assert reference.success, reference.message
        np.testing.assert_allclose(residual(reference.x), 0, atol=1e-11)
        expected = reference.x[:len(unknown)] + 1j * reference.x[len(unknown):]
    result = newton_raphson_fx(problem, tol=1e-9, max_iter=30, logger=vge.Logger())
    assert result.converged
    voltage = result.V[mask]
    np.testing.assert_allclose(voltage[unknown], expected, atol=2e-8, rtol=0)
    np.testing.assert_allclose((original_y @ voltage - physical_current(voltage))[unknown], 0, atol=2e-9)
    assert abs(np.mean(voltage[target_phases])) > 0.01
    np.testing.assert_array_equal(problem.Ybus_full.toarray(), original_y.toarray())
