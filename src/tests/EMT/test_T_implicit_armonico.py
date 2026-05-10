# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can see it at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Any, Tuple, Dict
import pandas as pd
from pandas.testing import assert_frame_equal

import os

import numpy as np

from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import JitSymbolicSolver
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory

class GenericEmtProblem(EmtProblemTemplate):
    __slots__ = list()


def integrator(initial_val: Any, vf: VarFactory, name: str) -> Tuple[Var, Block]:
    """
    Creates a state variable and a container block with a placeholder equation.
    """
    var= vf.add_var(name)
    diff_var = vf.add_diff_var(name = f"d_{name}", base_var=var)
    blk: Block = Block(
        name=f"int_{name}",
        state_vars=list([var]),
        diff_vars = list([diff_var]),
        state_eqs=list([Const(0.0)])
    )
    return var, blk


def build_oscillator_system(vf: VarFactory, omega: float = 1.0) -> Tuple[Block, Var, Var]:
    """
    Constructs the State-Space model for a harmonic oscillator.
    """
    x, blk_x = integrator(None, name="x", vf= vf)
    v, blk_v = integrator(None, name="v", vf= vf)

    # Coupling: dx/dt = v, dv/dt = -omega^2 * x
    blk_x.state_eqs[0] = v
    blk_v.state_eqs[0] = Const(-(omega ** 2)) * x

    system: Block = Block(
        name="HarmonicOscillator",
        children=list([blk_x, blk_v])
    )
    return system, x, v


def test_implicit_armonic() -> None:
    """
    Executes the validation routine comparing Trapezoidal and BDF2 methods.
    """
    # retrieve reference results df
    fname = os.path.join(os.path.dirname(__file__), '..', 'data', 'dynamics', "implicit_armonic.csv")
    reference_df = pd.read_csv(fname)

    t0: float = 0.0
    t_end: float = 20.0
    h: float = 0.01
    omega: float = 2.0

    print(f"--- NUMERICAL VALIDATION START ---")
    print(f"System: Harmonic Oscillator (omega={omega})")
    print(f"Interval: [{t0}, {t_end}] s, step h={h} s")

    # 1. Build Block and Unify
    vf = VarFactory()
    sys_block, var_x, var_v = build_oscillator_system(vf=vf, omega = omega)
    sys_block.unify_blocks()
    glob_time = vf.add_var("t_glob")
    static_parameter_values_mapping: Dict[Var, Const] = dict()

    # 2. Setup Problem
    problem: GenericEmtProblem = GenericEmtProblem(sys_block=sys_block,
                         static_parameter_values_mapping=static_parameter_values_mapping,
                         glob_time=glob_time,)

    idx_x: int = problem.get_var_idx(var_x)
    idx_v: int = problem.get_var_idx(var_v)

    custom_x0: np.ndarray = problem.get_x0()
    custom_x0[idx_x] = 1.0
    custom_x0[idx_v] = 0.0

    problem.get_x0 = lambda: custom_x0.copy()

    # --- CASE 1: Trapezoidal Method (A-Stable) ---
    print("\n[1] Running Implicit Solver (Method: Trapezoidal)...")
    solver_trap = JitSymbolicSolver(
        problem=problem, t0=t0, t_end=t_end, h=h,
        method=DynamicIntegrationMethod.DaeTrapezoidal,
        verbose=True
    )
    t_trap, y_trap_full, _, _, _ = solver_trap.simulate()

    # --- CASE 2: BDF2 Method (L-Stable) ---
    print("\n[2] Running Implicit Solver (Method: BDF2)...")
    solver_bdf = JitSymbolicSolver(
        problem=problem, t0=t0, t_end=t_end, h=h,
        method=DynamicIntegrationMethod.DaeBDF2,
        verbose=True
    )
    t_bdf, y_bdf_full,_, _, _= solver_bdf.simulate()

    # --- Analysis ---
    x_trap: np.ndarray = y_trap_full[:, idx_x]
    v_trap: np.ndarray = y_trap_full[:, idx_v]
    x_bdf: np.ndarray = y_bdf_full[:, idx_x]
    v_bdf: np.ndarray = y_bdf_full[:, idx_v]

    # Analytical solution: x(t) = x0 * cos(w*t)
    x_exact: np.ndarray = 1.0 * np.cos(omega * t_trap)

    err_trap: float = float(np.linalg.norm(x_trap - x_exact) / np.sqrt(len(t_trap)))
    err_bdf: float = float(np.linalg.norm(x_bdf - x_exact) / np.sqrt(len(t_bdf)))

    print("\n--- ERROR REPORT (RMS) ---")
    print(f"Trapezoidal: {err_trap:.6e} (A-Stable, Conservation of Energy)")
    print(f"BDF2       : {err_bdf:.6e} (L-Stable, Numerical Damping)")
    print("-" * 30)

    res = np.column_stack((x_trap, v_trap, x_bdf, v_bdf))

    cols = ["x_trap", "v_trap", "x_bdf", "v_bdf"]
    results_df = pd.DataFrame(res, columns=cols)
    results_df.index.name = "time_s"

    assert_frame_equal(
        results_df.reset_index(drop=True),
        reference_df.reset_index(drop=True),
        check_dtype=False,
        check_index_type=False,
        atol=1e-6
    )





if __name__ == "__main__":
    test_implicit_armonic()
