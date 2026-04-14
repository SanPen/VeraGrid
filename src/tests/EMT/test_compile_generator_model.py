# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can see it at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

# ==============================================================================
# Unit test for compiling and executing a complex Generator Model (DAE system)
# ==============================================================================

from typing import List, Dict, Callable

import numpy as np

from VeraGridEngine.Utils.Symbolic.symbolic import Var, cos, sin, Const, Expr
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.jit_compiler import EquationCompiler
from VeraGridEngine.enumerations import DynamicIntegrationMethod
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory


class EmtModelTemplate:
    """
    Mock container for the block model.

    :ivar block: The EMT model block, or None if not yet constructed.
    """
    __slots__ = ['block']

    def __init__(self) -> None:
        self.block: Block | None = None


def get_generator_emt_template(vf: VarFactory) -> EmtModelTemplate:
    """
    Constructs the EMT template of a Synchronous Generator.

    Creates a detailed synchronous generator model with electrical and mechanical
    equations in the DQ0 reference frame for EMT simulation.

    :param vf: Variable factory for creating system variables.
    :returns: EmtModelTemplate containing the generator block.
    """
    templ: EmtModelTemplate = EmtModelTemplate()

    # Variables
    theta: Var = vf.add_var(name="theta")
    omega: Var = vf.add_var(name="omega")
    psi_d: Var = vf.add_var(name="psi_d")
    psi_q: Var = vf.add_var(name="psi_q")
    psi_f: Var = vf.add_var(name="psi_f")
    psi_0: Var = vf.add_var(name="psi_0")
    et: Var = vf.add_var(name="et")

    # Differential Variables
    d_omega: Var = vf.add_diff_var(name='d_omega', base_var=omega)
    d_theta: Var = vf.add_diff_var(name='d_theta', base_var=theta)
    d_psi_d: Var = vf.add_diff_var(name='d_psi_d', base_var=psi_d)
    d_psi_q: Var = vf.add_diff_var(name='d_psi_q', base_var=psi_q)
    d_psi_0: Var = vf.add_diff_var(name='d_psi_0', base_var=psi_0)
    d_psi_f: Var = vf.add_diff_var(name='d_psi_f', base_var=psi_f)
    d_et: Var = vf.add_diff_var(name='d_et', base_var=et)

    # Algebraic Variables
    i_a: Var = vf.add_var(name="i_a")
    i_b: Var = vf.add_var(name="i_b")
    i_c: Var = vf.add_var(name="i_c")
    v_d: Var = vf.add_var(name="v_d")
    v_q: Var = vf.add_var(name="v_q")
    v_0: Var = vf.add_var(name="v_0")
    i_d: Var = vf.add_var(name="i_d")
    i_q: Var = vf.add_var(name="i_q")
    i_0: Var = vf.add_var(name="i_0")
    v_f: Var = vf.add_var(name="v_f")
    i_f: Var = vf.add_var(name="i_f")
    Te: Var = vf.add_var(name="Te")
    Tm: Var = vf.add_var(name="Tm")
    Pe: Var = vf.add_var(name='Pe')
    Qe: Var = vf.add_var(name='Qe')
    Pm: Var = vf.add_var(name="Pm")

    # Parameters
    omega_base: Var = vf.add_var(name="omega_base")
    H: Var = vf.add_var(name="H")
    D: Var = vf.add_var(name="D")
    Ra: Var = vf.add_var(name="Ra")
    La: Var = vf.add_var(name="La")
    Lmd: Var = vf.add_var(name="Lmd")
    Lmq: Var = vf.add_var(name="Lmq")
    Lf: Var = vf.add_var(name="Lf")
    Rf: Var = vf.add_var(name="Rf")
    R0: Var = vf.add_var(name="R0")
    L0: Var = vf.add_var(name="L0")
    omega_ref: Var = vf.add_var(name="omega_ref")
    Kp: Var = vf.add_var(name="Kp")
    Ki: Var = vf.add_var(name="Ki")
    v_f0: Var = vf.add_var(name="v_f0")

    # Inputs (External)
    v_a: Var = vf.add_var(name="v_a")
    v_b: Var = vf.add_var(name="v_b")
    v_c: Var = vf.add_var(name="v_c")

    state_eqs: List[Expr] = list([
        v_d - Ra * i_d - omega * psi_q,
        v_q - Ra * i_q + omega * psi_d,
        v_0 - R0 * i_0,
        v_f - Rf * i_f,
        omega_base * omega,
        (Tm - Te - D * (omega - omega_ref)) / (2.0 * H),
        omega_base * (omega_ref - omega),
    ])
    state_vars: List[Var] = list([psi_d, psi_q, psi_0, psi_f, theta, omega, et])

    algebraic_eqs: List[Expr] = list([
        psi_d - ((Lmd + La) * i_d + Lmd * i_f),
        psi_q - ((Lmq + La) * i_q),
        psi_f - (Lmd * i_d + (Lmd + Lf) * i_f),
        psi_0 - L0 * i_0,
        v_d - (2.0 / 3.0) * (
                    v_a * cos(theta) + v_b * cos(theta - 2.0 * np.pi / 3.0) + v_c * cos(theta + 2.0 * np.pi / 3.0)),
        v_q - (2.0 / 3.0) * (
                    v_a * sin(theta) + v_b * sin(theta - 2.0 * np.pi / 3.0) + v_c * sin(theta + 2.0 * np.pi / 3.0)),
        v_0 - (2.0 / 3.0) * (v_a * 0.5 + v_b * 0.5 + v_c * 0.5),
        i_a - (i_d * cos(theta) + i_q * sin(theta) + i_0),
        i_b - (i_d * cos(theta - 2.0 * np.pi / 3.0) + i_q * sin(theta - 2.0 * np.pi / 3.0) + i_0),
        i_c - (i_d * cos(theta + 2.0 * np.pi / 3.0) + i_q * sin(theta + 2.0 * np.pi / 3.0) + i_0),
        Te + (3.0 / 2.0) * (psi_d * i_q - psi_q * i_d),
        Pe - (i_a * v_a + i_b * v_b + i_c * v_c),
        Qe - (1.0 / np.sqrt(3.0)) * ((v_a - v_b) * i_c + (v_b - v_c) * i_a + (v_c - v_a) * i_b),
        Tm - (Te + Kp * (omega_ref - omega) + Ki * et),
        v_f - v_f0,
        Pm - Pe
    ])
    algebraic_vars: List[Var] = list([i_d, i_q, i_f, i_0, v_d, v_q, v_0, i_a, i_b, i_c, Te, Pe, Qe, Tm, v_f, Pm])

    in_vars: List[Var] = list([v_a, v_b, v_c])
    out_vars: List[Var] = list([i_a, i_b, i_c])

    parameters: Dict[Var, Const] = dict()
    parameters[omega_base] = Const(376.99)
    parameters[H] = Const(3.0)
    parameters[D] = Const(0.0)
    parameters[Ra] = Const(0.003)
    parameters[La] = Const(0.2)
    parameters[Lmd] = Const(1.0)
    parameters[Lmq] = Const(0.6)
    parameters[Lf] = Const(0.1)
    parameters[Rf] = Const(0.001)
    parameters[R0] = Const(0.01)
    parameters[L0] = Const(0.1)
    parameters[omega_ref] = Const(1.0)
    parameters[Kp] = Const(10.0)
    parameters[Ki] = Const(1.0)
    parameters[v_f0] = Const(1.0)

    templ.block = Block(
        name="SynchronousGenerator",
        state_eqs=state_eqs,
        state_vars=state_vars,
        algebraic_eqs=algebraic_eqs,
        algebraic_vars=algebraic_vars,
        in_vars=in_vars,
        out_vars=out_vars,
        parameters=parameters
    )

    templ.block.diff_vars = list([d_psi_d, d_psi_q, d_psi_0, d_psi_f, d_theta, d_omega, d_et])
    return templ


def test_compile_and_run_generator() -> None:
    """
    Tests the full pipeline using ONLY the official Block API.

    Verifies that the synchronous generator model can be compiled
    into a step function and executed successfully.
    """
    print("\n=== Generator Model Compilation Test ===")

    vf: VarFactory = VarFactory()
    template: EmtModelTemplate = get_generator_emt_template(vf=vf)
    block: Block = template.block

    all_eqs: List[Expr] = list(block.state_eqs)
    all_eqs.extend(block.algebraic_eqs)

    all_unknowns: List[Var] = list(block.state_vars)
    all_unknowns.extend(block.algebraic_vars)

    params: List[Var] = list(block.parameters.keys())
    params.extend(block.in_vars)

    print(f"States: {len(block.state_vars)}")
    print(f"Algebraics: {len(block.algebraic_vars)}")
    print(f"Parameters & Inputs: {len(params)}")

    compiler: EquationCompiler = EquationCompiler(
        variables=all_unknowns,
        parameters=params,
        method=DynamicIntegrationMethod.DaeTrapezoidal
    )
    step_fn: Callable = compiler.compile(all_eqs, func_name='generator_step_fn')
    print("\n[OK] Function compiled successfully.")

    n_unknowns: int = len(all_unknowns)
    n_params: int = len(params)

    current_state: np.ndarray = np.zeros(n_unknowns, dtype=np.float64)

    unknown_names: List[str] = list([v.name for v in all_unknowns])
    if 'omega' in unknown_names:
        current_state[unknown_names.index('omega')] = 1.0

    history: np.ndarray = current_state.copy()
    d_history: np.ndarray = np.zeros(n_unknowns, dtype=np.float64)
    history2: np.ndarray = np.zeros(n_unknowns, dtype=np.float64)
    param_vals: np.ndarray = np.zeros(n_params, dtype=np.float64)

    for i, p_var in enumerate(params):
        if p_var in block.parameters:
            param_vals[i] = float(block.parameters[p_var].value)
        elif p_var.name == 'v_a':
            param_vals[i] = 1.0
        elif p_var.name == 'v_b':
            param_vals[i] = -0.5
        elif p_var.name == 'v_c':
            param_vals[i] = -0.5

    h: float = 0.001
    residuals: np.ndarray = step_fn(current_state, param_vals, history, d_history, h, history2)

    print(f"Residuals shape: {residuals.shape}")

    assert isinstance(residuals, np.ndarray), "Residuals should be numpy array"
    assert len(residuals) == n_unknowns, f"Expected {n_unknowns} residuals, got {len(residuals)}"
    assert np.all(np.isfinite(residuals)), "All residuals should be finite"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
