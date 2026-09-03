# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from types import SimpleNamespace

import numpy as np

from VeraGridEngine.Simulations.OPF.NumericalMethods.newton_raphson_ips_fx import (
    compute_adaptive_sigma,
    has_tail_converged,
)


def test_large_case_damped_tail_accepts_narrow_stalled_tail() -> None:
    """
    Accept a large damped tail when only the final KKT tail stalls in the low e-5 band.
    """
    problem = SimpleNamespace(nbus=2853)
    converged = has_tail_converged(problem=problem,
                                   step_control=True,
                                   feas_cond=1e-9,
                                   gradcond=4e-5,
                                   comp_cond=4e-5,
                                   cost_cond=1e-10,
                                   gamma=1e-10,
                                   tol=1e-6)
    assert converged is True


def test_large_case_damped_tail_rejects_large_residuals() -> None:
    """
    Reject the large-case tail shortcut when the stalled residuals are still materially large.
    """
    problem = SimpleNamespace(nbus=2853)
    converged = has_tail_converged(problem=problem,
                                   step_control=True,
                                   feas_cond=1e-9,
                                   gradcond=2e-4,
                                   comp_cond=2e-4,
                                   cost_cond=1e-10,
                                   gamma=1e-10,
                                   tol=1e-6)
    assert converged is False


def test_compute_adaptive_sigma_reduces_centering_when_affine_step_is_good() -> None:
    """
    Use a smaller centering parameter when the affine complementarity prediction improves strongly.
    """
    mu = np.array([1.0, 2.0], dtype=float)
    z = np.array([2.0, 1.0], dtype=float)
    dmu = np.array([-0.8, -1.6], dtype=float)
    dz = np.array([-1.6, -0.8], dtype=float)
    sigma = compute_adaptive_sigma(mu=mu,
                                   z=z,
                                   dmu=dmu,
                                   dz=dz,
                                   alpha_p=0.9,
                                   alpha_d=0.9)
    assert 1e-4 <= sigma < 0.1


def test_compute_adaptive_sigma_caps_aggressive_centering() -> None:
    """
    Cap the centering parameter when the affine prediction is poor.
    """
    mu = np.array([1.0, 1.0], dtype=float)
    z = np.array([1.0, 1.0], dtype=float)
    dmu = np.array([0.5, 0.5], dtype=float)
    dz = np.array([0.5, 0.5], dtype=float)
    sigma = compute_adaptive_sigma(mu=mu,
                                   z=z,
                                   dmu=dmu,
                                   dz=dz,
                                   alpha_p=1.0,
                                   alpha_d=1.0)
    assert sigma == 0.5
