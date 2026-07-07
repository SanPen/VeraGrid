# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can see it at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import unittest
import numpy as np
from typing import List, Dict, Any


from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const, Expr
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers.StructuralVectorizedSolver import StructuralVectorizedSolver
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory

# ==============================================================================
# SVS Jacobian Backends Verification Suite
# ==============================================================================


class GenericEmtProblem(EmtProblemTemplate):
    __slots__ = list()


# ==============================================================================
# Helpers
# ==============================================================================

def build_buck(vf: VarFactory) -> Block:
    """Simple Buck converter for testing."""
    i_L: Var = vf.add_var("i_L")
    v_C: Var = vf.add_var("v_C")
    Vin: Var = vf.add_var("Vin_sw")
    R: Var = vf.add_var("R")
    L: Var = vf.add_var("L")
    C: Var = vf.add_var("C")

    d_i_L: Var = vf.add_diff_var(name = "d_i_L", base_var=i_L)
    d_v_C: Var = vf.add_diff_var(name = "d_v_C", base_var=v_C)


    state_vars: List[Var] = list([i_L, v_C])
    diff_vars: List[Var] = list([d_i_L, d_v_C])
    state_eqs: List[Expr] = list([(Vin - v_C) / L, (i_L - v_C / R) / C])

    parameters: Dict[Var, Const] = dict({
        Vin: Const(0.0),
        R: Const(5.0),
        L: Const(100e-6),
        C: Const(470e-6)
    })

    block: Block = Block(
        name="Buck",
        state_vars=state_vars,
        state_eqs=state_eqs,
        diff_vars=diff_vars,
        parameters=parameters
    )
    block.unify_blocks()
    return block


def get_full_params(solver: Any) -> np.ndarray:
    """
    Builds the FULL parameter vector [variable_params | static_params].
    This prevents division by zero in Jacobian kernels.
    """
    n_ev: int = len(solver._event_parameters)
    ev_params: np.ndarray = np.zeros(n_ev, dtype=np.float64)

    static_vals: List[float] = list([float(p.value) for p in solver._parameters_values])
    static_params: np.ndarray = np.array(static_vals, dtype=np.float64)

    return np.concatenate((ev_params, static_params))


# ==============================================================================
# Tests for StructuralVectorizedSolver
# ==============================================================================

class TestSVSJacobianBackends(unittest.TestCase):

    def test_svs_clustering_and_jacobian(self) -> None:
        """
        Validates that SVS performs clustering and produces a well-formed Sparse Jacobian.
        """

        vf: VarFactory = VarFactory()
        block: Block = build_buck(vf)
        t_sys: Var = Var("t_sys")
        static_parameter_values_mapping: Dict[Var, Const] = dict(block.parameters)
        problem: GenericEmtProblem = GenericEmtProblem(
            sys_block=block,
            glob_time=t_sys,
            static_parameter_values_mapping=static_parameter_values_mapping,
        )

        solver: StructuralVectorizedSolver = StructuralVectorizedSolver(
            problem, t0=0.0, t_end=1e-3, h=1e-6, method=DynamicIntegrationMethod.DaeTrapezoidal
        )

        x: np.ndarray = problem.get_x0()
        dx: np.ndarray = np.zeros_like(x, dtype=np.float64)

        p_full: np.ndarray = get_full_params(solver)

        # Verify clustering detection
        self.assertGreater(len(solver.vec_kernels), 0)

        J: Any = solver.vec_jacobian(states=x, params=p_full, history=x, d_history=dx, h=1e-6)

        self.assertEqual(J.shape, (len(x), len(x)))
        self.assertTrue(bool(np.all(np.isfinite(J.data))), f"Jacobian contains non-finite values: {J.data}")

    def test_svs_simulation_consistency(self) -> None:
        """
        Ensures SVS simulation runs without divergence in a standard EMT case.
        """
        vf: VarFactory = VarFactory()
        block: Block = build_buck(vf)
        t_sys: Var = Var("t_sys")
        static_parameter_values_mapping: Dict[Var, Const] = dict(block.parameters)
        problem: GenericEmtProblem = GenericEmtProblem(
            sys_block=block,
            glob_time=t_sys,
            static_parameter_values_mapping=static_parameter_values_mapping,
        )

        x0: np.ndarray = problem.get_x0()
        p0: np.ndarray = np.zeros(problem.get_variable_parameter_number(), dtype=np.float64)

        solver: StructuralVectorizedSolver = StructuralVectorizedSolver(
            problem, t0=0.0, t_end=50e-6, h=1e-6, method=DynamicIntegrationMethod.DaeTrapezoidal
        )

        t_arr, y_arr, _, _, _ = solver.simulate(x0=x0, params0=p0)

        self.assertEqual(len(t_arr), y_arr.shape[0])
        self.assertTrue(bool(np.all(np.isfinite(y_arr))))


if __name__ == '__main__':
    unittest.main()
