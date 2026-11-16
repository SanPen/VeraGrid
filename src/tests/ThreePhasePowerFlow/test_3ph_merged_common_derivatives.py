"""Analytic derivatives of physical sequence boundaries and passive reductions."""
import numpy as np
import pytest

import VeraGridEngine.api as vge
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Simulations.PowerFlow3ph.Formulations.pf_basic_formulation_3ph import (
    PfBasicFormulation3Ph, expand3ph, expandVoltage3ph)
from tests.ThreePhasePowerFlow.test_3ph_common_mode import floating_grid, weak_passive_grid
from tests.ThreePhasePowerFlow.test_3ph_internal_reduction import loaded_grid
from tests.ThreePhasePowerFlow.test_3ph_positive_sequence_voltage_control import make_grid
from tests.ThreePhasePowerFlow.test_3ph_synchronous_slack import make_grid as make_slack_grid


class AnalyticOnlyFormulation(PfBasicFormulation3Ph):
    """Make an accidental finite-difference production Jacobian fail explicitly."""

    __slots__ = ()

    def compute_f(self, x: np.ndarray) -> np.ndarray:
        """Reject residual sampling by the requested analytic Jacobian.

        :param x: A trial solution which analytic assembly must not sample.
        :return: No value; production analytic assembly must not call this method.
        :raises AssertionError: If a hidden numerical fallback evaluates residuals.
        """
        raise AssertionError('Jacobian(False) must use analytic derivatives')


def make_problem(grid: vge.MultiCircuit) -> AnalyticOnlyFormulation:
    """Compile the actual physical model without replacing solver functions.

    :param grid: Grid including its actual sequence sources and conductor topology.
    :return: Production formulation with residual-sampling protection.
    """
    nc: NumericalCircuit = compile_numerical_circuit_at(grid, fill_three_phase=True)
    qmax: np.ndarray
    qmin: np.ndarray
    qmax, qmin = nc.get_reactive_power_limits()
    return AnalyticOnlyFormulation(
        V0=expandVoltage3ph(nc.bus_data.Vbus), S0=expand3ph(nc.get_power_injections_pu()),
        Qmin=qmin, Qmax=qmax, nc=nc,
        options=vge.PowerFlowOptions(control_q=False, tolerance=1e-9), logger=vge.Logger())


def check_analytic_derivatives(problem: AnalyticOnlyFormulation) -> None:
    """Compare every solver column at an unbalanced point away from a root.

    Calling the base residual explicitly supplies an independent central-difference
    oracle while the subclass prevents the analytic implementation using that route.

    :param problem: Physical formulation containing the feature under test.
    :return: None.
    """
    random: np.random.Generator = np.random.default_rng(913)
    point: np.ndarray = problem.var2x().copy()
    n_angle: int = len(problem.idx_dVa)
    n_voltage: int = n_angle + len(problem.idx_dVm)
    point[:n_angle] += random.uniform(-0.025, 0.025, n_angle)
    point[n_angle:n_voltage] *= 1.0 + random.uniform(-0.025, 0.025, n_voltage - n_angle)
    point[n_voltage:] += 0.02
    problem.update(point, update_controls=False)
    analytic: np.ndarray = problem.Jacobian(autodiff=False).toarray()
    # Diagnostic residual evaluation must not replace the accepted floating
    # neutral state used by post-processing and subsequent solver iterations.
    floating_power: np.ndarray = problem.Un_floating_power.copy()
    floating_current: np.ndarray = problem.Un_floating_current.copy()
    reference: np.ndarray = np.empty(analytic.shape)
    step: float = 1e-6
    column: int
    for column in range(len(point)):
        plus: np.ndarray = point.copy()
        minus: np.ndarray = point.copy()
        plus[column] += step
        minus[column] -= step
        reference[:, column] = (
            PfBasicFormulation3Ph.compute_f(problem, plus)
            - PfBasicFormulation3Ph.compute_f(problem, minus)) / (2.0 * step)
    np.testing.assert_allclose(analytic, reference, rtol=2e-6, atol=2e-7)
    np.testing.assert_array_equal(problem.var2x(), point)
    np.testing.assert_array_equal(problem.Un_floating_power, floating_power)
    np.testing.assert_array_equal(problem.Un_floating_current, floating_current)


@pytest.mark.parametrize('physical_slack', (False, True))
@pytest.mark.parametrize('ideal_zero', (False, True))
def test_projected_ideal_and_slack_derivatives(physical_slack: bool, ideal_zero: bool) -> None:
    """Check I0/I1 elimination, angular rotation terms and colocated Q columns.

    :param physical_slack: Include the complex synchronous U1 reference.
    :param ideal_zero: Include the physical ideal-ground U0 constraint.
    :return: None.
    """
    grid: vge.MultiCircuit = make_slack_grid() if physical_slack else make_grid()
    generator: vge.Generator = grid.generators[0] if physical_slack else grid.generators[1]
    if not physical_slack:
        # The shared PV helper supplies a physical slack by default. This
        # branch explicitly exercises the separate legacy fixed-ABC boundary.
        grid.generators[0].R0 = 0.0
        grid.generators[0].X0 = 0.0
        grid.generators[0].R2 = 0.0
        grid.generators[0].X2 = 0.0
    else:
        pass
    if ideal_zero:
        generator.R0 = 0.0
        generator.X0 = 0.0
    else:
        pass
    problem: AnalyticOnlyFormulation = make_problem(grid)
    assert len(problem.positive_sequence.slack_bus_idx) == int(physical_slack)
    assert len(problem.common_mode.ideal_phases) == int(ideal_zero)
    if not physical_slack:
        assert len(problem.positive_sequence.q) == 1
    else:
        pass
    check_analytic_derivatives(problem)


@pytest.mark.parametrize('explicit_neutral', (False, True))
def test_floating_reference_and_schur_derivatives(explicit_neutral: bool) -> None:
    """Retain one free group with the same analytic equations after neutral reduction.

    :param explicit_neutral: Include an eliminated passive neutral and a nonlinear neutral.
    :return: None.
    """
    problem: AnalyticOnlyFormulation = make_problem(floating_grid(explicit_neutral))
    # NeutralStar's existing compiler includes its physical neutral-earth
    # term; that case is grounded rather than a free common-mode fixture.
    assert len(problem.common_mode.phases) == int(not explicit_neutral)
    if explicit_neutral:
        assert problem.voltage_lift is not None
    else:
        pass
    check_analytic_derivatives(problem)


def test_finite_common_mode_balance_derivatives() -> None:
    """Differentiate a real weak earth balance without inventing a U0 reference.

    :return: None.
    """
    grid: vge.MultiCircuit = weak_passive_grid(1e-4)
    bus: vge.Bus
    for bus in grid.buses[1:]:
        # Active device presence retains these original nodes; zero scheduled
        # injection leaves their physical common-mode balance linear.
        grid.add_load(bus, vge.Load(P=0.0, Q=0.0))
    problem: AnalyticOnlyFormulation = make_problem(grid)
    assert len(problem.common_mode.phases) == 0
    assert len(problem.common_mode.balance_real_rows) == 1
    check_analytic_derivatives(problem)


def test_internal_abc_schur_derivatives() -> None:
    """Differentiate the reduced nonlinear model with its physical internal ABC lift.

    :return: None.
    """
    grid: vge.MultiCircuit
    transformer: vge.Transformer3W
    grid, transformer = loaded_grid()
    problem: AnalyticOnlyFormulation = make_problem(grid)
    assert transformer.bus0.idtag in problem.nc.bus_data.idtag
    assert problem.voltage_lift is not None
    assert problem.voltage_lift.shape[0] - problem.voltage_lift.shape[1] >= 3
    check_analytic_derivatives(problem)


def test_signed_neutral_magnitude_derivatives() -> None:
    """Keep the actual polar-coordinate derivative when Newton crosses Vm=0.

    A passive neutral starts near zero and may accept a negative magnitude
    coordinate. Its physical voltage is valid; its magnitude column changes sign.

    :return: None.
    """
    problem: AnalyticOnlyFormulation = make_problem(floating_grid(explicit_neutral=True))
    neutral: int = problem.bus_lookup[8]
    assert neutral >= 0
    assert neutral in problem.idx_dVm
    problem.Vm[neutral] = -0.02
    check_analytic_derivatives(problem)
