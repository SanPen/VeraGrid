# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Derivative columns in the RMS small-signal mass matrix follow base variables."""

from importlib import import_module
from types import SimpleNamespace

import numpy as np
import pytest
import scipy.sparse as sp


@pytest.mark.parametrize("module_name,class_name", [
    ("rms_problem_dae_vectorized", "RmsProblemDaeVec"),
    ("rms_problem_dae_full_vectorized", "RmsProblemDaeFullVec"),
    ("rms_problem_dae_full_vectorized_numba_comp", "RmsProblemDaeFullVec"),
])
def test_derivative_mass_columns_follow_base_variables(monkeypatch, module_name, class_name):
    module = import_module(f"VeraGridEngine.Simulations.Rms.problems.{module_name}")
    partial = np.array([[2.0, 3.0], [5.0, 7.0], [11.0, 13.0]])

    class FakeJacobian:
        def __init__(self, **kwargs):
            assert kwargs["variables"] == problem._diff_vars

        def __call__(self, *args, **kwargs):
            return sp.csc_matrix(partial)

    monkeypatch.setattr(module, "SymbolicJacobian", FakeJacobian)
    state = SimpleNamespace(uid=10)
    algebraic = SimpleNamespace(uid=20)
    problem = SimpleNamespace(
        _state_eqs=[None], _algebraic_eqs=[None, None],
        _diff_vars=[SimpleNamespace(base_var=algebraic), SimpleNamespace(base_var=state)],
        _uid2idx_vars={state.uid: 0, algebraic.uid: 2},
        _compiler_names_dict={}, _alias_names_dict={},
        _variable_parameters_values=np.array([]), _constant_params=np.array([]),
        _n_vars=3, get_states_number=lambda: 1,
    )
    for name in ("VARS_NAME", "DIFF_NAME", "VARIABLE_PARAMS_NAME", "CONSTANT_PARAMS_NAME"):
        setattr(problem, name, name)

    result = getattr(module, class_name).get_E_matrix(problem, np.zeros(3), np.zeros(2))
    np.testing.assert_array_equal(result, [
        [2.0, 0.0, 2.0],
        [7.0, 0.0, 5.0],
        [13.0, 0.0, 11.0],
    ])
