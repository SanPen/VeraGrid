# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can see it at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import time
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

import os

from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const, Expr
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Simulations.EMT.solvers.jit_symbolic_solver import JitSymbolicSolver, BoundaryUpdateWrapper
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory


class GenericEmtProblem(EmtProblemTemplate):
    __slots__ = list()


class BoostPWMWrapper(BoundaryUpdateWrapper):
    __slots__ = ['f_sw', 'duty', 'offset', 'idx']

    def __init__(self, f_sw: float, duty: float, offset: int, idx: int):
        self.f_sw: float = f_sw
        self.duty: float = duty
        self.offset: int = offset
        self.idx: int = idx

    def update(self, t: float, x: np.ndarray, params: np.ndarray) -> None:
        t_mod: float = t % (1.0 / self.f_sw)
        if t_mod < (self.duty / self.f_sw):
            sw_val: float = 1.0
        else:
            sw_val: float = 0.0

        params[self.offset + self.idx] = sw_val


def create_boost_system(vf: VarFactory) -> Tuple[Block, Var, Var]:

    i_L = vf.add_var("i_L")
    v_C = vf.add_var("v_C")
    Vin = vf.add_var("Vin")
    Sw = vf.add_var("Sw")
    R = vf.add_var("R")
    L = vf.add_var("L")
    C = vf.add_var("C")

    d_i_L = vf.add_diff_var(name="d_i_L", base_var=i_L)
    d_v_C = vf.add_diff_var(name="d_v_C", base_var=v_C)

    state_vars: List[Var] = list([i_L, v_C])
    diff_vars: List[Var] = list([d_i_L, d_v_C])
    state_eqs: List[Expr] = list([
        (Vin - (Const(1.0) - Sw) * v_C) / L,
        ((Const(1.0) - Sw) * i_L - v_C / R) / C
    ])
    parameters: Dict[Var, Const] = dict({
        Vin: Const(12.0),
        Sw: Const(1.0),
        R: Const(10.0),
        L: Const(50e-6),
        C: Const(220e-6)
    })

    boost: Block = Block(
        name="Boost_Benchmark",
        state_vars=state_vars,
        diff_vars=diff_vars,
        state_eqs=state_eqs,
        parameters=parameters
    )
    return boost, Sw, Vin


def test_method_benchmark() -> None:
    # retrieve reference results df
    fname = os.path.join(os.path.dirname(__file__), '..', 'data', 'dynamics', "tradeoff_stability_accuracy.csv")
    reference_df = pd.read_csv(fname)

    print("==================================================================")
    print("   IMPLICIT METHODS BENCHMARK: STABILITY VS ACCURACY")
    print("==================================================================")

    DUTY: float = 0.5
    F_SW: float = 25e3
    DT: float = 1e-6
    T_END: float = 0.004

    # Using string identifiers for the new JIT architecture
    methods: List[Tuple[DynamicIntegrationMethod, str]] = list([
        (DynamicIntegrationMethod.DaeBackEuler, "Backward Euler (L-Stable)"),
        (DynamicIntegrationMethod.DaeTrapezoidal, "Trapezoidal (A-Stable)"),
        (DynamicIntegrationMethod.DaeBDF2, "BDF2 (L-Stable)")
    ])

    results: Dict[str, Dict[str, np.ndarray]] = dict()
    kpis: List[Dict[str, Any]] = list()

    vf = VarFactory()
    sys_block, sw_var, _ = create_boost_system(vf)
    sys_block.unify_blocks()
    glob_time = vf.add_var("t_glob")

    # 1. Create BaseProblem (Network Topology & Equations)
    static_parameter_values_mapping: Dict[Var, Const] = dict(sys_block.parameters)
    problem: GenericEmtProblem = GenericEmtProblem(
        sys_block=sys_block,
        glob_time=glob_time,
        static_parameter_values_mapping=static_parameter_values_mapping,
    )

    # 2. Configure Controller
    offset: int = problem.get_variable_parameter_number()
    idx: int = problem.uid2idx_params[sw_var.uid]
    pwm_updater: BoostPWMWrapper = BoostPWMWrapper(F_SW, DUTY, offset, idx)

    for method_enum, method_name in methods:
        print(f"\n> Testing: {method_name}...")

        # 3. Instantiate JIT Solver
        solver = JitSymbolicSolver(
            problem=problem, t0=0.0, t_end=T_END, h=DT,
            method=method_enum, verbose=False
        )

        # 4. Simulate
        t0: float = time.perf_counter()
        t_arr, y_arr, dy_arr, _, _ = solver.simulate(boundary_updater=pwm_updater)
        elapsed: float = time.perf_counter() - t0

        # Extract Data
        i_L: np.ndarray = y_arr[:, problem.get_var_idx(sys_block.state_vars[0])]
        v_C: np.ndarray = y_arr[:, problem.get_var_idx(sys_block.state_vars[1])]

        # Metrics
        mask_ss: np.ndarray = t_arr > (T_END * 0.8)
        ripple_current: float = float(np.max(i_L[mask_ss]) - np.min(i_L[mask_ss]))
        avg_voltage: float = float(np.mean(v_C[mask_ss]))

        if ripple_current < 1.0:
            behavior: str = "High Damping"
        else:
            behavior: str = "Accurate"

        kpis.append(dict({
            "Method": method_name.split(' ')[0],
            "Sim Time (s)": f"{elapsed:.4f}",
            "V_out Avg (V)": f"{avg_voltage:.2f}",
            "Ripple I_L (A)": f"{ripple_current:.3f}",
            "Behavior": behavior
        }))

        results[method_name] = dict({'t': t_arr, 'i': i_L, 'v': v_C})

    flat_results = dict()

    for method_name, method_data in results.items():
        flat_results[f"{method_name}_t"] = method_data["t"]
        flat_results[f"{method_name}_i"] = method_data["i"]
        flat_results[f"{method_name}_v"] = method_data["v"]

    results_df = pd.DataFrame(flat_results)
    results_df.index.name = "step"

    assert_frame_equal(
        results_df.reset_index(drop=True),
        reference_df.reset_index(drop=True),
        check_dtype=False,
        check_index_type=False,
        atol=1e-6
    )


if __name__ == "__main__":
    test_method_benchmark()
