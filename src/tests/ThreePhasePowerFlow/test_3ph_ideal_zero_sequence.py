"""An exact grounded Z0=0 imposes U0=0 while its current follows network KCL."""
import numpy as np
import pytest
import VeraGridEngine.api as vge
from VeraGridEngine.enumerations import GeneratorControlMode, ShuntConnectionType
from tests.ThreePhasePowerFlow.test_3ph_positive_sequence_voltage_control import make_grid, solve, target_voltages
from tests.ThreePhasePowerFlow.test_3ph_common_mode import formulation
from tests.ThreePhasePowerFlow.test_3ph_batteries import replace_generator
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.newton_raphson_fx import newton_raphson_fx
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.pf_basic_formulation_3ph import compute_power_loads


@pytest.mark.parametrize('mode', (GeneratorControlMode.V, GeneratorControlMode.Q))
@pytest.mark.parametrize('solver', (vge.SolverType.NR, vge.SolverType.LM, vge.SolverType.PowellDogLeg))
@pytest.mark.parametrize('sbase', (25.0, 100.0))
def test_ideal_grounded_source_kcl_and_power(mode, solver, sbase) -> None:
    """Check the physical constraint and all sequence currents from independent branch results."""
    grid = make_grid(sbase=sbase)
    gen = grid.generators[1]
    gen.R0 = gen.X0 = 0.0
    gen.control_mode, gen.Q = mode, 3.0
    result = solve(grid, control_q=False, solver=solver)
    voltage = target_voltages(result)
    power = np.array((result.St_A[0], result.St_B[0], result.St_C[0])) + (8+3j, 5+2j, 2+1j)
    current = np.conj(power/voltage)*3/sbase
    a = np.exp(2j*np.pi/3)
    transform = np.array(((1,1,1),(1,a,a*a),(1,a*a,a)))/3
    u012, i012 = transform@voltage, transform@current
    assert abs(u012[0]) < 1e-9
    assert abs(i012[0]) > 1e-3  # The ideal source must not be silently disconnected.
    np.testing.assert_allclose(i012[2], -u012[2]/complex(gen.R2,gen.X2), atol=2e-8)
    assert power.sum().real == pytest.approx(gen.P,abs=1e-6)
    if mode == GeneratorControlMode.Q:
        assert power.sum().imag == pytest.approx(gen.Q,abs=1e-6)
    else:
        assert abs(u012[1]) == pytest.approx(gen.Vset,abs=1e-8)
    assert gen.R0 == gen.X0 == 0.0


@pytest.mark.parametrize('mode', (GeneratorControlMode.V, GeneratorControlMode.Q))
def test_colocated_ideal_sources_share_one_constraint(mode) -> None:
    """Splitting a source preserves its total current without duplicate constraints."""
    grid = make_grid()
    gen = grid.generators[1]
    gen.R0 = gen.X0 = 0
    gen.control_mode, gen.Q = mode, 3
    baseline = target_voltages(solve(grid,control_q=False))
    gen.P /= 2
    gen.Q /= 2
    gen.R2 *= 2
    gen.X2 *= 2
    grid.add_generator(grid.buses[1],vge.Generator(P=gen.P,Q=gen.Q,vset=gen.Vset,
        control_mode=mode,r0=0,x0=0,r2=gen.R2,x2=gen.X2))
    grid.add_generator(grid.buses[0],vge.Generator(active=False,r0=0,x0=0))
    assert len(formulation(grid).common_mode.ideal_phases) == 1
    np.testing.assert_allclose(target_voltages(solve(grid,control_q=False)),baseline,atol=1e-8)


@pytest.mark.parametrize('connection', (ShuntConnectionType.Delta, ShuntConnectionType.FloatingStar))
def test_blocked_connection_has_no_ideal_ground(connection) -> None:
    grid = make_grid()
    gen = grid.generators[1]
    gen.R0 = gen.X0 = 0
    gen.conn = connection
    assert len(formulation(grid).common_mode.ideal_phases) == 0
    assert abs(np.mean(target_voltages(solve(grid,control_q=False)))) > 1e-5


def test_finite_and_inactive_branches_do_not_become_ideal() -> None:
    grid = make_grid()
    grid.generators[1].R0,grid.generators[1].X0 = 1e-7,0
    grid.add_generator(grid.buses[1],vge.Generator(active=False,r0=0,x0=0))
    assert len(formulation(grid).common_mode.ideal_phases) == 0


def test_ideal_reference_residual_routes_and_current_recovery() -> None:
    """Line searches and convergence checks must all retain KCL after recovering I0."""
    grid = make_grid()
    grid.generators[1].R0 = grid.generators[1].X0 = 0
    problem = formulation(grid,shift=0.025+0.01j)
    result = newton_raphson_fx(problem,tol=1e-9,max_iter=40,logger=vge.Logger())
    assert result.converged
    x = problem.var2x()
    np.testing.assert_allclose(problem.compute_f(x),problem.fx(),atol=1e-12)
    error,_ = problem.check_error(x)
    assert error < 1e-9
    power,_,_ = compute_power_loads(problem.nc.load_data.bus_idx,problem.bus_lookup,problem.V,
        problem.nc.load_data.S3_star,problem.nc.load_data.S3_floatingstar,problem.nc.load_data.S3_delta)
    mismatch = problem.Ybus@problem.V-(problem.generator_currents(problem.V,problem.positive_sequence.q)+power)/(grid.Sbase/3)
    phases = problem.common_mode.ideal_phases
    i0 = np.mean(mismatch[phases],axis=1)
    assert np.max(abs(i0)) > 1e-3
    mismatch[phases] -= i0[:,None]
    np.testing.assert_allclose(mismatch[problem.no_slack],0,atol=2e-9)


def test_ideal_source_retains_pv_reactive_limit() -> None:
    grid = make_grid()
    gen = grid.generators[1]
    gen.R0 = gen.X0 = 0
    gen.Qmax = 2
    limited = solve(grid)
    gen.control_mode, gen.Q = GeneratorControlMode.Q, 2
    np.testing.assert_allclose(target_voltages(limited),target_voltages(solve(grid)),atol=1e-8)


@pytest.mark.parametrize('mode', (GeneratorControlMode.Q, GeneratorControlMode.V))
def test_battery_ideal_ground_reuses_sequence_controller(mode) -> None:
    """Storage shares the ideal constraint while retaining its own power convention."""
    grid = make_grid()
    battery = replace_generator(grid)
    battery.control_mode, battery.Q = mode, 3.0
    battery.R0 = battery.X0 = 0.0
    result = solve(grid, control_q=False)
    voltage = target_voltages(result)
    power = np.array((result.St_A[0], result.St_B[0], result.St_C[0])) + (8+3j, 5+2j, 2+1j)
    current = np.conj(power/voltage)*3/grid.Sbase
    a = np.exp(2j*np.pi/3)
    transform = np.array(((1,1,1),(1,a,a*a),(1,a*a,a)))/3
    u012, i012 = transform@voltage, transform@current
    assert abs(u012[0]) < 1e-9
    assert abs(i012[0]) > 1e-3
    np.testing.assert_allclose(i012[2],-u012[2]/complex(battery.R2,battery.X2),atol=2e-8)
    if mode == GeneratorControlMode.Q:
        np.testing.assert_allclose(u012[1]*i012[1].conj()*grid.Sbase,battery.P+1j*battery.Q,atol=1e-6)
    else:
        assert abs(u012[1]) == pytest.approx(battery.Vset,abs=1e-8)
        assert power.sum().real == pytest.approx(battery.P,abs=1e-6)
    assert battery.Enom == 80 and battery.soc_0 == 0.65
