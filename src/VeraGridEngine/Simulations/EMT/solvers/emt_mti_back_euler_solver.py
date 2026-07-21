# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np

from VeraGridEngine.Simulations.EMT.problems.emt_problem_mti import EmtProblemMTI
from VeraGridEngine.Simulations.Rms.numerical.back_euler_mti import BackEulerImplicitIntegrationMTI
from VeraGridEngine.basic_structures import Mat, Vec


class EmtMtiBackEulerSolver:
    """EMT-facing wrapper around the shared BackEuler MTI integrator."""

    def __init__(
        self,
        problem: EmtProblemMTI,
        t0: float,
        t_end: float,
        h: float,
        max_iter: int = 20,
        tolerance: float = 1e-7,
        inequality_tolerance: float = 1e-9,
        event_bisect_iter: int = 2,
        mti_max_iter: int = 300,
    ) -> None:
        self.problem = problem
        self._solver = BackEulerImplicitIntegrationMTI(
            problem=problem,
            t0=t0,
            t_end=t_end,
            h=h,
            max_iter=max_iter,
            tolerance=tolerance,
            inequality_tolerance=inequality_tolerance,
        )
        self._solver.event_bisect_iter = max(1, int(event_bisect_iter))
        self._solver.mti_max_iter = max(1, int(mti_max_iter))
        self.z: Mat = np.zeros((0, 0), dtype=float)

    def simulate(self) -> tuple[Vec, Mat, Mat, bool, bool]:
        t, y, well_initialized, converged = self._solver.simulate()
        self.z = self._solver.z[: len(t), :].copy()
        dy = self._estimate_derivatives(t=t, y=y)
        return t, y, dy, well_initialized, converged

    @staticmethod
    def _estimate_derivatives(t: Vec, y: Mat) -> Mat:
        dy = np.zeros_like(y)
        if len(t) < 2:
            return dy
        dt = np.diff(t)
        valid = dt > 0.0
        if np.any(valid):
            dy[1:][valid, :] = np.diff(y, axis=0)[valid, :] / dt[valid, None]
            dy[0, :] = dy[1, :]
        return dy
