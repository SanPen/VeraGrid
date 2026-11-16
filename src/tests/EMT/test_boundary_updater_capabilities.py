# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Optional boundary-updater APIs are resolved once per simulation, not on every substep."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pytest

from tests.EMT.test_alignment_step_three_solvers import ForcedEventTracker
from tests.EMT.test_discretization_verify import GenericEmtProblem, create_decay_system, make_solver
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Simulations.EMT.problems import emt_problem_template
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import get_solver_forced_event_time, resolve_solver_boundary_step
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import JitSymbolicSolver
from VeraGridEngine.Simulations.EMT.solvers.solver_AD import JitAdSolver
from VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver import StructuralVectorizedSolver
from VeraGridEngine.Simulations.EMT.solvers.structural_compiled_solver import StructuralCompiledSolver
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var


class _UpdateOnlyUpdater:
    """Legacy boundary updater exposing only ``update``."""

    __slots__ = ()

    def update(self, t: float, x_prev: np.ndarray, full_params: np.ndarray) -> float | None:
        """
        Leave the parameters untouched.

        :param t: Target time.
        :param x_prev: Last accepted state.
        :param full_params: Mutable parameter buffer.
        :return: None.
        """
        return None


class _DirCountingTracker(ForcedEventTracker):
    """Forced-event tracker that counts how often ``dir()`` inspects it."""

    __slots__ = ("dir_calls",)

    def __init__(self, forced_times: Tuple[float, ...]) -> None:
        """
        Build the tracker.

        :param forced_times: Forced alignment times.
        """
        super().__init__(forced_times=forced_times)
        self.dir_calls: int = 0

    def __dir__(self) -> List[str]:
        """
        Count the inspection and return the usual attribute names.

        :return: Attribute names.
        """
        self.dir_calls += 1
        return list(super().__dir__())


def test_capabilities_follow_the_updater_api() -> None:
    """A tracker exposes the three optional APIs, an update-only updater none, and no updater none."""
    full: "emt_problem_template.BoundaryUpdaterCapabilities" = emt_problem_template.BoundaryUpdaterCapabilities(ForcedEventTracker(forced_times=(0.05,)))
    legacy: "emt_problem_template.BoundaryUpdaterCapabilities" = emt_problem_template.BoundaryUpdaterCapabilities(_UpdateOnlyUpdater())
    missing: "emt_problem_template.BoundaryUpdaterCapabilities" = emt_problem_template.BoundaryUpdaterCapabilities(None)
    assert (full.forced_event_time, full.step_resolution, full.commit_boundary) == (True, True, True)
    assert (legacy.forced_event_time, legacy.step_resolution, legacy.commit_boundary) == (False, False, False)
    assert (missing.forced_event_time, missing.step_resolution, missing.commit_boundary) == (False, False, False)


def test_helpers_use_the_given_capabilities() -> None:
    """The helpers trust resolved capabilities and fall back to inspecting the updater without them."""
    tracker: ForcedEventTracker = ForcedEventTracker(forced_times=(0.05,))
    none_available: "emt_problem_template.BoundaryUpdaterCapabilities" = emt_problem_template.BoundaryUpdaterCapabilities(_UpdateOnlyUpdater())
    params: np.ndarray = np.zeros(1)
    assert get_solver_forced_event_time(tracker, 0.0, 0.1) == pytest.approx(0.05)
    assert get_solver_forced_event_time(tracker, 0.0, 0.1, capabilities=none_available) is None
    assert resolve_solver_boundary_step(tracker, True, params, capabilities=none_available) is None
    assert tracker.resolve_calls == list()
    assert resolve_solver_boundary_step(tracker, True, params) is None
    assert tracker.resolve_calls == list((True,))


@pytest.mark.parametrize("solver_class", (JitSymbolicSolver, JitAdSolver, StructuralVectorizedSolver, StructuralCompiledSolver))
def test_updater_is_inspected_once_per_simulation(solver_class: type) -> None:
    """
    Every EMT solver inspects the boundary updater once per simulation (one resolution: two dir() inspections),
    independent of the number of substeps, and still honours the forced alignment time, the step resolution and the
    boundary commit of every accepted substep.

    :param solver_class: EMT solver class.
    """
    block: Block
    x: Var
    k: Var
    block, x, k = create_decay_system(k_val=1.0)
    solver: JitSymbolicSolver | JitAdSolver | StructuralVectorizedSolver | StructuralCompiledSolver
    problem: GenericEmtProblem
    solver, problem = make_solver(solver_class, block, 0.2, 0.01, DynamicIntegrationMethod.DaeBackEuler)
    tracker: _DirCountingTracker = _DirCountingTracker(forced_times=(0.055,))
    result: Tuple[np.ndarray, np.ndarray, np.ndarray, bool, bool] = solver.simulate(
        x0=np.ones(1), dx0=-np.ones(1), params0=np.zeros(problem.get_variable_parameter_number()), boundary_updater=tracker)
    assert result[4]
    assert 0.055 in [round(float(t), 12) for t in tracker.update_calls]
    assert len(tracker.resolve_calls) > 20
    assert all(tracker.resolve_calls)
    assert len(tracker.commit_calls) == len(tracker.resolve_calls)
    assert tracker.dir_calls <= 2
