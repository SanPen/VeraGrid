# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Numerical and runtime contracts for the single-class adaptive BDF solver."""
import numpy as np
import pytest
from scipy import sparse
from scipy.sparse.linalg import LinearOperator

from VeraGridEngine.Simulations.Rms.numerical.adaptive_bdf15 import AdaptiveBdf15Integration
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.rms_problem_factory import build_rms_problem
from VeraGridEngine.enumerations import RmsInitializationMethod, RmsProblemTypes
from tests.Base.test_dynamic_results_save_load import _build_rms_driver


class DecayDae:
    """x'=-x, z=x², with an optional scaled algebraic equation."""
    def __init__(self, algebraic_scale=1.):
        self._variable_parameters_values = np.empty(0)
        self._fmu_cs_adapters, self._fmu_me_adapters = [], []
        self._manufacturer_native_runtime_session = None
        self.logger = None
        self.scale = algebraic_scale
    def get_sparse_solver_backend_provider(self): return None
    def get_all_vars_number(self): return 2
    def get_states_number(self): return 1
    def get_diff_var_number(self): return 0
    def get_forced_event_times(self): return []
    def get_x0(self): return np.ones(2)
    def get_dx0(self): return np.empty(0)
    def update_variable_params(self, *args, **kwargs): pass
    def update(self, *args): pass
    def get_next_forced_event_time(self, *args): return None
    def report_progress2(self, *args): pass
    def rhs_state(self, y, dx): return -y[:1]
    def rhs_algebraic(self, y, dx): return self.scale * (y[1:] - y[:1]**2)
    def evaluate_equations(self, y, dx): return np.r_[self.rhs_state(y, dx), self.rhs_algebraic(y, dx)]
    def evaluate_jacobian_blocks(self, y, dx, h):
        return self.get_fx_ct(y, dx), self.get_fy_ct(y, dx), self.get_gx_ct(y, dx), self.get_gy_ct(y, dx)
    def get_fx_ct(self, y, dx): return sparse.csc_matrix([[-1.]])
    def get_fy_ct(self, y, dx): return sparse.csc_matrix((1, 1))
    def get_gx_ct(self, y, dx): return sparse.csc_matrix([[-2*self.scale*y[0]]])
    def get_gy_ct(self, y, dx): return sparse.csc_matrix([[self.scale]])
    def get_j22(self, y, dx, h): return self.get_gy_ct(y, dx)
    def get_small_signal_reference_indices(self): return None


def make_solver(problem=None, end=.3, **kwargs):
    return AdaptiveBdf15Integration(DecayDae() if problem is None else problem,
                                   0., end, .01, 8, tolerance=1e-12,
                                   absolute_tolerance=1e-9, relative_tolerance=1e-7, **kwargs)


def test_derivative_free_bdf_uses_raw_equations_and_compiled_discretization():
    class RawDecayDae(DecayDae):
        def evaluate_equations(self, y, dx):
            return np.array([-y[0], y[1] - y[0] ** 2])

        def rhs_state(self, y, dx):
            raise AssertionError("Raw equation evaluation should serve the BDF residual")

        def rhs_algebraic(self, y, dx):
            raise AssertionError("Raw equation evaluation should serve the BDF residual")

        def evaluate_jacobian_blocks(self, y, dx, h):
            return (sparse.csc_matrix([[-1.0]]), sparse.csc_matrix((1, 1)),
                    sparse.csc_matrix([[-2.0 * y[0]]]), sparse.csc_matrix([[1.0]]))

        def get_fx_ct(self, y, dx):
            raise AssertionError("Raw Jacobian blocks should serve the BDF assembler")

    solver = make_solver(RawDecayDae())
    residual = solver._residual(np.array([1.2, 1.4]), 3.0, np.array([-3.0, -3.0]))
    np.testing.assert_allclose(residual, [1.8, -0.04])
    np.testing.assert_allclose(solver._jacobian(np.array([1.2, 1.4]), 3.0).toarray(),
                               [[4.0, 0.0], [-2.4, 1.0]])
    assert solver._jacobian_assembler.get_pattern_build_count() == 1


def test_vectorized_rms_derivative_variables_use_the_bdf_coefficient():
    """Integrate both vectorized grids and check an algebraic derivative column."""
    trajectories = []
    for problem_type in (RmsProblemTypes.PowerBalanceVectorized,
                         RmsProblemTypes.PowerBalanceFullVectorized):
        built = _build_rms_driver()
        options = RmsOptions(
            time_step=0.01, simulation_time=0.03, tolerance=1e-6,
            problem_type=problem_type,
            initialization_method=RmsInitializationMethod.Explicit,
            use_init_values=False,
        )
        problem = build_rms_problem(built.grid, options, built.pf_results)
        problem.set_events_group(built.grid.rms_events_groups[0])
        problem.reset_boundary_update_state(0.0)
        solver = AdaptiveBdf15Integration(problem, 0.0, 0.03, 0.01, 20, tolerance=1e-6)

        initial = problem.get_x0()
        alpha = 100.0
        history = -alpha * initial
        residual = solver._residual(initial, alpha, history)
        j11, j12, j13, j21, j22, j23 = problem.evaluate_jacobian_partials(
            initial, solver._dx_work, solver._derivative_base_indices)
        assert j13.shape == (solver.state_count, problem.get_diff_var_number())
        assert j23.shape == (solver.network_count - solver.state_count,
                             problem.get_diff_var_number())
        assert j23.nnz > 0
        derivative_map = solver._derivative_to_variable
        reconstructed = sparse.bmat(
            [[j11, j12], [j21, j22]], format="csc") + alpha * sparse.vstack(
            [j13, j23], format="csc") @ derivative_map
        c11, c12, c21, c22 = problem.evaluate_jacobian_blocks(
            initial, solver._dx_work, 1.0 / alpha)
        chained = sparse.bmat([[c11, c12], [c21, c22]], format="csc")
        raw = sparse.bmat([[j11, j12], [j21, j22]], format="csc")
        np.testing.assert_allclose(raw.toarray(), chained.toarray(),
                                   rtol=1e-8, atol=1e-8)
        jacobian = solver._jacobian(initial, alpha)
        column = int(solver._derivative_base_indices[0])
        perturbed = initial.copy()
        perturbed[column] += 1e-7
        numerical_column = (solver._residual(perturbed, alpha, history) - residual) / 1e-7
        np.testing.assert_allclose(
            jacobian[:, column].toarray().ravel(), numerical_column,
            rtol=1e-5, atol=1e-5,
        )

        times, values, initialized, converged = solver.simulate()
        assert initialized and converged
        np.testing.assert_allclose(times, [0.0, 0.01, 0.02, 0.03], rtol=0, atol=1e-14)
        assert np.all(np.isfinite(values))
        trajectories.append(values)
    np.testing.assert_allclose(trajectories[0], trajectories[1], rtol=1e-8, atol=1e-10)


@pytest.mark.parametrize('order', [1, 2, 3, 4, 5])
def test_orders_history_and_dense_derivatives(order):
    solver = make_solver(maximum_order=order)
    t, y, initialized, converged = solver.simulate()
    assert initialized and converged
    np.testing.assert_allclose(y[:, 0], np.exp(-t), atol=8e-5, rtol=0)
    np.testing.assert_allclose(y[:, 1], np.exp(-2*t), atol=1.5e-4, rtol=0)
    assert not solver.order_counts[order:].any()
    assert solver.jacobian_reuses > 0
    midpoint = solver._time - solver.used_h/2
    np.testing.assert_allclose(solver.interpolate(midpoint, 1)[0], -np.exp(-midpoint), atol=8e-4)
    with pytest.raises(ValueError, match='last accepted step'):
        solver.interpolate(-1.)


@pytest.mark.parametrize('linear', ['sparse', 'dense', 'gmres'])
def test_scaled_equations_and_linear_solvers(linear):
    solver = make_solver(DecayDae(1. if linear == "gmres" else 1e-12), linear_solver=linear)
    t, y, initialized, converged = solver.simulate()
    assert initialized and converged
    np.testing.assert_allclose(y[:, 0], np.exp(-t), atol=2e-6)
    np.testing.assert_allclose(y[:, 1], y[:, 0]**2, atol=3e-6)


def test_krylov_product_and_preconditioner():
    calls = []
    def product(t, y, yp, cj, vector):
        calls.append(t)
        return np.array([(cj+1)*vector[0], -2*y[0]*vector[0] + vector[1]])
    def preconditioner(t, y, yp, cj):
        return LinearOperator((2, 2), matvec=lambda v: np.array([v[0]/(cj+1), v[1]+2*y[0]*v[0]/(cj+1)]))
    solver = make_solver(linear_solver='gmres', jacobian_vector_product=product, preconditioner=preconditioner)
    t, y, initialized, converged = solver.simulate()
    assert initialized and converged and calls and solver.linear_iterations
    np.testing.assert_allclose(y[:, 0], np.exp(-t), atol=2e-6)


def test_directional_and_terminal_roots():
    solver = make_solver(roots=lambda t,y,yp: [y[0]-.9, y[0]-.8, y[0]-.85],
                         root_directions=[-1,-1,1], root_terminal=[False,True,False])
    t, y, initialized, converged = solver.simulate()
    assert initialized and converged
    assert [event[1] for event in solver.root_events] == [0, 1]
    np.testing.assert_allclose([event[0] for event in solver.root_events], -np.log([.9,.8]), atol=1e-6)
    assert t[-1] == solver.terminal_time
    assert y[-1, 0] == pytest.approx(.8, abs=1e-8)
    assert np.all(np.diff(t) > 0)


def test_vector_tolerances_custom_weights_and_algebraic_mask():
    solver = AdaptiveBdf15Integration(DecayDae(), 0., .1, .01, 8,
                                      absolute_tolerance=np.array([1e-8,1e-10]),
                                      suppress_algebraic=True,
                                      weight_function=lambda y: np.full(y.shape, 1e6))
    assert solver.simulate()[3]
    assert solver.norm(np.array([0.,1.]), mask=True) == 0.
    assert solver.norm(np.array([0.,1.])) > 0.
    with pytest.raises(ValueError, match='positive'):
        make_solver(weight_function=lambda y: np.zeros_like(y)).simulate()


def test_constraints_and_failure_counters():
    class Impossible(DecayDae):
        def get_x0(self): return np.zeros(2)
        def rhs_state(self, y, dx): return -np.ones(1)
        def get_fx_ct(self, y, dx): return sparse.csc_matrix((1,1))
    solver = make_solver(Impossible(), maximum_failures=3, constraints=np.array([1,0]))
    t, y, initialized, converged = solver.simulate()
    assert initialized and not converged
    assert solver.constraint_failures == 3 and solver.accepted_steps == 0
    np.testing.assert_array_equal(t, [0.])
    with pytest.raises(ValueError, match='violates'):
        make_solver(constraints=np.array([-2,0])).simulate()


def test_recoverable_nonfinite_trial_and_work_limit():
    class Recoverable(DecayDae):
        time = 0.
        failed = False
        def update(self, time, *args): self.time = time
        def rhs_state(self, y, dx):
            if self.time > 0 and not self.failed:
                self.failed = True
                return np.array([np.nan])
            return super().rhs_state(y, dx)
    solver = make_solver(Recoverable(), initial_step=.01)
    t, y, initialized, converged = solver.simulate()
    assert initialized and converged
    assert solver.nonlinear_failures and solver.rejected_steps
    np.testing.assert_allclose(y[:, 0], np.exp(-t), atol=2e-6)
    limited = make_solver(maximum_steps=2)
    assert not limited.simulate()[3]
    assert limited.accepted_steps == 2 and 'step count' in limited.stop_reason


def test_options_and_limits():
    options = RmsOptions(time_step=.02, bdf_max_step=.01, bdf_initial_step=.001,
                         bdf_max_order=3, bdf_suppress_algebraic=True)
    assert options.bdf_max_step == .01 and options.time_step == .02
    for kwargs in ({'bdf_max_order':6}, {'bdf_initial_step':.02}, {'bdf_min_step':-.1},
                   {'bdf_linear_solver':'unknown'}, {'bdf_max_steps':0}):
        with pytest.raises(ValueError): RmsOptions(**kwargs)


def test_matches_native_sundials_ida_reference():
    """Reference generated by check_ida_julia.jl with yp0=(-1, 0)."""
    from pathlib import Path
    path = Path(__file__).parents[1] / 'data/powersystems_julia/ida_analytic_reference.csv'
    reference = np.genfromtxt(path, delimiter=',', names=True)
    solver = AdaptiveBdf15Integration(DecayDae(), 0., 1., .01, 8,
                                      absolute_tolerance=1e-8, relative_tolerance=1e-7,
                                      initial_step=1e-5)
    time, values, initialized, converged = solver.simulate()
    assert initialized and converged
    np.testing.assert_allclose(time, reference['time'], atol=1e-15, rtol=0.)
    np.testing.assert_allclose(values, np.column_stack([reference['x'], reference['z']]),
                               atol=1e-11, rtol=0.)
    assert solver.accepted_steps == 126
    assert solver.error_failures == 4
    assert solver.jacobian_refreshes == 21
    # Native IDA reports 160; VeraGrid also evaluates the initial DAE slope.
    assert solver.residual_evaluations == 161
