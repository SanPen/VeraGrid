# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Coupled BDF dynamics using the production ME adapter and a deterministic FMI host."""
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
import scipy.sparse as sp

from VeraGridEngine.IO.fmu.model_exchange import FmuMeDeviceAdapter, FmuMeSolverPolicy
from VeraGridEngine.IO.fmu.host import FmiTwoEventUpdate
from VeraGridEngine.Simulations.Rms.numerical.adaptive_bdf15 import AdaptiveBdf15Integration
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Utils.NumericalMethods.emt_sparse_superlu_backend import SuperLUSparseBackendProvider
from VeraGridEngine.enumerations import DynamicIntegrationMethod, FmiVersion


class Host:
    """FMU state s'=-x, output s+0.2*x: a coupled oscillator with feedthrough."""
    def __init__(self, event=None, decay=None):
        self.t, self.s, self.x = 0., 0. if decay is None else 1., 1.
        self.event, self.decay = event, decay
        self.events = []
        self.accepted = []
        self.closed = False
        self.metadata = SimpleNamespace(fmi_version_family=FmiVersion.FMI_2_0)

    def set_time(self, t): self.t = t
    def set_real(self, values): self.x = values['u']
    def set_continuous_states(self, values): self.s = values[0]
    def get_continuous_states(self): return [self.s]
    def get_derivatives(self): return [-self.x if self.decay is None else -self.decay * self.s]
    def get_real(self, names): return {'out': self.s + 0.2 * self.x}
    def get_event_indicators(self):
        return [] if self.event is None else [self.event - self.t if not self.events else 1.]
    def needs_completed_integrator_step(self): return True
    def completed_integrator_step(self):
        self.accepted.append(self.t)
        return False, False
    def close(self): self.closed = True
    def enter_event_mode(self): self.events.append(self.t)
    def enter_continuous_time_mode(self): pass
    def new_discrete_states(self):
        self.s = 2.
        return FmiTwoEventUpdate(False, False, False, True, None)


class Adapter:
    def __init__(self, host):
        self.host = host
        spec = SimpleNamespace(state_variable_names=('s',), input_variable_names=('u',),
                               output_variable_names=('out',),
                               output_bindings=(SimpleNamespace(reference='out'),),
                               maximum_event_iterations=10)
        policy = FmuMeSolverPolicy(DynamicIntegrationMethod.DaeAdaptiveBdf15, 1e-8, 1e-8, 20, 128)
        self.runtime_adapter = FmuMeDeviceAdapter(spec, policy)
        self.last_outputs = {}

    def _build_input_values(self, network): return {'u': network[0]}
    def apply_outputs(self, parameters, outputs): parameters[0] = outputs['out']

    def initialize(self):
        r, h = self.runtime_adapter, self.host
        r.runtime_host, r.state_vector, r.initialized = h, np.array([h.s]), True
        r.fmi_two_accepted_input_values = (h.x,)
        r.fmi_two_accepted_derivative_values = tuple(h.get_derivatives())
        r.fmi_two_accepted_readable_values = (h.get_real([])['out'],)
        r.fmi_two_accepted_event_indicators = tuple(h.get_event_indicators())


class Problem:
    def __init__(self, event=None, decay=None):
        self.host = Host(event, decay)
        self._fmu_me_adapters = [Adapter(self.host)]
        self._fmu_cs_adapters = []
        self._manufacturer_native_runtime_session = None
        self._variable_parameters_values = np.array([self.host.s + .2])
        self.options = RmsOptions(integration_method=DynamicIntegrationMethod.DaeAdaptiveBdf15)
        self.logger = Mock()

    def get_forced_event_times(self): return []

    def get_all_vars_number(self): return 2
    def get_states_number(self): return 1
    def get_diff_var_number(self): return 0
    def get_x0(self): return np.array([1., self.host.s + .2])
    def get_dx0(self): return np.empty(0)
    def rhs_state(self, y, dx): return np.array([y[1] - .2*y[0] if self.host.decay is None else 0.])
    def rhs_algebraic(self, y, dx): return np.array([y[1] - self._variable_parameters_values[0]])
    def evaluate_equations(self, y, dx):
        return np.r_[self.rhs_state(y, dx), self.rhs_algebraic(y, dx)]
    def get_j22(self, *args): return sp.eye(1, format='csc')
    def get_small_signal_reference_indices(self): return None
    def update_variable_params(self, *args, **kwargs): pass
    def update(self, *args): pass
    def report_progress2(self, *args): pass
    def get_next_forced_event_time(self, now, end):
        times = [a.runtime_adapter.get_next_event_time() for a in self._fmu_me_adapters]
        return min((t for t in times if t is not None and now < t <= end), default=None)
    def initialize_fmu_me_devices(self, *args):
        for a in self._fmu_me_adapters: a.initialize()
    def close_fmu_me_devices(self):
        for a in self._fmu_me_adapters: a.runtime_adapter.close()


def solve(problem, tolerance=1e-6, end=1., **kwargs):
    solver = AdaptiveBdf15Integration(problem, 0., end, .01, 20,
                                      tolerance=1e-10, absolute_tolerance=tolerance,
                                      relative_tolerance=tolerance,
                                      sparse_solver_backend_provider=SuperLUSparseBackendProvider(),
                                      **kwargs)
    t, y, initialized, converged = solver.simulate()
    return solver, t, y, initialized, converged


def test_coupled_oscillator_and_feedthrough():
    problem = Problem()
    solver, t, y, initialized, converged = solve(problem)
    assert initialized and converged
    np.testing.assert_allclose(y[:, 0], np.cos(t), atol=8e-5)
    np.testing.assert_allclose(solver.fmu_y[:, 0], -np.sin(t), atol=8e-5)
    np.testing.assert_allclose(y[:, 1], solver.fmu_y[:, 0] + .2*y[:, 0], atol=1e-9)
    assert solver.order_counts[2:].sum() > 0
    assert problem.host.closed
    assert np.all(np.diff(problem.host.accepted) > 0)


def test_fmu_only_transient_controls_error_and_rolls_back():
    errors = []
    for tolerance in (1e-3, 1e-6):
        problem = Problem(decay=100.)
        solver, t, y, initialized, converged = solve(problem, tolerance, end=.1)
        assert initialized and converged, solver.last_failure
        assert solver.rejected_steps > 0
        errors.append(np.max(np.abs(solver.fmu_y[:, 0] - np.exp(-100*t))))
        np.testing.assert_allclose(y[:, 0], 1., atol=1e-12)
        assert len(problem.host.accepted) == solver.accepted_steps
        assert problem.host.closed
    assert errors[1] < errors[0] / 10


def test_state_event_localizes_combined_step_and_restarts_history():
    problem = Problem(event=.037123)
    solver, t, y, initialized, converged = solve(problem, end=.1)
    assert initialized and converged, solver.last_failure
    assert len(problem.host.events) == 1
    assert abs(problem.host.events[0] - .037123) <= problem.options.fmi_state_event_time_tolerance
    assert solver.fmu_event_retries > 0
    assert solver.fmu_y[-1, 0] > 1.8
    assert problem.host.closed


def test_cancel_and_probe_failure_close_runtime():
    problem = Problem()
    solver, t, y, initialized, converged = solve(problem, cancel_checker=lambda: True)
    assert initialized and not converged and len(t) == 1
    assert problem.host.closed
    problem = Problem()
    problem.host.get_derivatives = Mock(side_effect=RuntimeError('probe failure'))
    with pytest.raises(RuntimeError, match='probe failure'):
        solve(problem)
    assert problem.host.closed


def test_scheduled_fmu_event_reprojects_algebraic_output():
    problem = Problem()
    initialize = problem.initialize_fmu_me_devices
    def initialize_with_event(*args):
        initialize(*args)
        problem._fmu_me_adapters[0].runtime_adapter.fmi_two_next_event_time = .04
    problem.initialize_fmu_me_devices = initialize_with_event
    solver, t, y, initialized, converged = solve(problem, end=.1)
    assert initialized and converged
    np.testing.assert_allclose(problem.host.events, [.04], atol=1e-14)
    index = int(np.flatnonzero(np.isclose(t, .04))[0])
    assert solver.fmu_y[index, 0] == 2.
    np.testing.assert_allclose(y[index, 1], 2. + .2*y[index, 0], atol=1e-9)
    assert solver.fmu_event_retries == 0
    assert len(problem.host.accepted) == solver.accepted_steps


def test_continuous_state_indicator_localization():
    problem = Problem()
    host = problem.host
    host.get_derivatives = lambda: [-1.]
    host.get_event_indicators = lambda: [host.s + .037123 if not host.events else 1.]
    solver, t, y, initialized, converged = solve(problem, end=.1)
    assert initialized and converged
    assert len(host.events) == 1
    assert abs(host.events[0] - .037123) <= problem.options.fmi_state_event_time_tolerance
    assert solver.fmu_y[-1, 0] == pytest.approx(2 - (.1 - host.events[0]), abs=1e-8)


def test_multiple_fmus_share_acceptance_and_error_control():
    problem = Problem(decay=25.)
    second = Adapter(Host(decay=100.))
    problem._fmu_me_adapters.append(second)
    solver, t, y, initialized, converged = solve(problem, tolerance=1e-8, end=.1)
    assert initialized and converged
    np.testing.assert_allclose(solver.fmu_y[:, 0], np.exp(-25*t), atol=2e-5)
    np.testing.assert_allclose(solver.fmu_y[:, 1], np.exp(-100*t), atol=2e-5)
    np.testing.assert_array_equal(problem.host.accepted, second.host.accepted)
    assert second.host.closed and problem.host.closed
    assert solver.rejected_steps > 0


def test_budget_exhaustion_and_cs_guard():
    problem = Problem()
    problem.options.fmi_me_max_runtime_evaluations_per_step = 10
    with pytest.raises(RuntimeError, match='budget'):
        solve(problem)
    assert problem.host.closed
    problem = Problem()
    problem._fmu_cs_adapters = [object()]
    with pytest.raises(NotImplementedError, match='Co-Simulation'):
        solve(problem)
    assert not problem.host.accepted
