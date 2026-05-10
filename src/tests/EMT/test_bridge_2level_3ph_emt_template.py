# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Dict, List, Tuple

import numpy as np

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Templates.Emt.bridge_2level_3ph_emt_template import get_bridge_2level_3ph_emt_template
from VeraGridEngine.Utils.procedural_logic import build_boundary_updater_from_block
from VeraGridEngine.Utils.Symbolic.block import Block, find_name_in_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


class GenericEmtProblem(EmtProblemTemplate):
    """
    Minimal EMT problem used by standalone bridge tests.
    """

    __slots__ = []


def _build_constant_algebraic_var(vf: VarFactory, name: str, value: float) -> Tuple[Var, Expr]:
    """
    Build one algebraic variable constrained to a constant reference value.

    :param vf: Shared symbolic variable factory.
    :param name: Variable name.
    :param value: Constant reference value.
    :return: Tuple ``(variable, equation)``.
    """
    variable: Var = vf.add_var(name=name)
    reference_value: Const = Const(float(value))
    equation: Expr = variable - reference_value
    return variable, equation


def _build_bridge_standalone_problem() -> Tuple[GenericEmtProblem, Dict[str, Var]]:
    """
    Build one standalone 2-level bridge EMT problem for fast PWM/gate validation.

    The problem intentionally avoids solving a full implicit network because the
    bridge electrical equations are validated elsewhere through the converter and
    valve integration tests. Here we only need a consistent symbolic container so
    the procedural PWM logic can update the retained gate modes.

    :return: EMT problem and tracked variables.
    """
    vf: VarFactory = VarFactory()
    bridge_name: str = "bridge_2level_test"
    theta_pll: Var
    theta_pll_eq: Expr
    v_cmd_d: Var
    v_cmd_d_eq: Expr
    v_cmd_q: Var
    v_cmd_q_eq: Expr
    v_cmd_0: Var
    v_cmd_0_eq: Expr
    v_dc: Var
    v_dc_eq: Expr
    k_v_conv: Var
    k_v_conv_eq: Expr
    m_max: Var
    m_max_eq: Expr
    vdc_floor: Var
    vdc_floor_eq: Expr
    omega_sw: Var = vf.add_var(name="omega_sw_test")
    carrier_phase: Var = vf.add_var(name="carrier_phase_test")
    bridge_block: Block = get_bridge_2level_3ph_emt_template(vf=vf, name=bridge_name).block
    root_block: Block
    problem: GenericEmtProblem
    tracked_vars: Dict[str, Var] = dict()
    init_name: str
    init_values: Dict[str, float] = dict()
    init_var: Var | None
    all_problem_vars: List[Var]

    theta_pll, theta_pll_eq = _build_constant_algebraic_var(vf=vf, name="theta_pll_test", value=0.0)
    v_cmd_d, v_cmd_d_eq = _build_constant_algebraic_var(vf=vf, name="v_cmd_d_test", value=0.3)
    v_cmd_q, v_cmd_q_eq = _build_constant_algebraic_var(vf=vf, name="v_cmd_q_test", value=0.0)
    v_cmd_0, v_cmd_0_eq = _build_constant_algebraic_var(vf=vf, name="v_cmd_0_test", value=0.0)
    v_dc, v_dc_eq = _build_constant_algebraic_var(vf=vf, name="v_dc_test", value=1.0)
    k_v_conv, k_v_conv_eq = _build_constant_algebraic_var(vf=vf, name="k_v_conv_test", value=0.5)
    m_max, m_max_eq = _build_constant_algebraic_var(vf=vf, name="m_max_test", value=0.95)
    vdc_floor, vdc_floor_eq = _build_constant_algebraic_var(vf=vf, name="vdc_floor_test", value=0.05)

    bridge_block.connect(
        bridge_block.in_vars,
        list([
            theta_pll,
            v_cmd_d,
            v_cmd_q,
            v_cmd_0,
            v_dc,
            k_v_conv,
            m_max,
            vdc_floor,
            omega_sw,
            carrier_phase,
        ]),
    )

    root_block = Block(
        name="Bridge2LevelStandaloneCase",
        children=list([bridge_block]),
        algebraic_vars=list([theta_pll, v_cmd_d, v_cmd_q, v_cmd_0, v_dc, k_v_conv, m_max, vdc_floor]),
        algebraic_eqs=list([
            theta_pll_eq,
            v_cmd_d_eq,
            v_cmd_q_eq,
            v_cmd_0_eq,
            v_dc_eq,
            k_v_conv_eq,
            m_max_eq,
            vdc_floor_eq,
        ]),
        event_dict=dict([
            (omega_sw, Const(2.0 * np.pi * 1000.0)),
            (carrier_phase, Const(0.0)),
        ]),
        init_eqs=dict([
            (theta_pll, Const(0.0)),
            (v_cmd_d, Const(0.3)),
            (v_cmd_q, Const(0.0)),
            (v_cmd_0, Const(0.0)),
            (v_dc, Const(1.0)),
            (k_v_conv, Const(0.5)),
            (m_max, Const(0.95)),
            (vdc_floor, Const(0.05)),
        ]),
    )
    root_block.unify_blocks()
    static_parameter_values_mapping: Dict[Var, Const] = dict()

    problem = GenericEmtProblem(sys_block=root_block, glob_time=vf.add_var("t_bridge_test"), static_parameter_values_mapping=static_parameter_values_mapping)
    tracked_vars["m_a"] = find_name_in_block(f"m_a_{bridge_name}", problem.sys_block)
    tracked_vars["m_b"] = find_name_in_block(f"m_b_{bridge_name}", problem.sys_block)
    tracked_vars["m_c"] = find_name_in_block(f"m_c_{bridge_name}", problem.sys_block)
    tracked_vars["gate_a"] = find_name_in_block(f"gate_a_{bridge_name}", problem.sys_block)
    tracked_vars["gate_b"] = find_name_in_block(f"gate_b_{bridge_name}", problem.sys_block)
    tracked_vars["gate_c"] = find_name_in_block(f"gate_c_{bridge_name}", problem.sys_block)

    all_problem_vars = list(problem.get_state_vars()) + list(problem.get_algebraic_vars())
    init_values = dict([
        ("theta_pll_test", 0.0),
        ("v_cmd_d_test", 0.3),
        ("v_cmd_q_test", 0.0),
        ("v_cmd_0_test", 0.0),
        ("v_dc_test", 1.0),
        ("k_v_conv_test", 0.5),
        ("m_max_test", 0.95),
        ("vdc_floor_test", 0.05),
        (f"m_a_{bridge_name}", 0.0),
        (f"m_b_{bridge_name}", -0.6),
        (f"m_c_{bridge_name}", 0.6),
    ])

    for init_name, init_value in init_values.items():
        init_var = next((var for var in all_problem_vars if var.name == init_name), None)
        if init_var is not None:
            problem.init_guess[init_var.uid] = float(init_value)
        else:
            pass

    return problem, tracked_vars


def test_bridge_2level_3ph_pwm_logic_switches_all_phases() -> None:
    """
    Verify that the standalone bridge PWM logic toggles all three retained gate modes.

    :return: None.
    """
    problem: GenericEmtProblem
    tracked_vars: Dict[str, Var]
    boundary_updater = None
    x: np.ndarray
    params: np.ndarray
    time_samples: np.ndarray
    mode_hist: np.ndarray
    mode_a_idx: int
    mode_b_idx: int
    mode_c_idx: int
    gate_a_hist: np.ndarray
    gate_b_hist: np.ndarray
    gate_c_hist: np.ndarray
    sample_idx: int

    problem, tracked_vars = _build_bridge_standalone_problem()
    boundary_updater = build_boundary_updater_from_block(problem)
    x = problem.get_x0().copy()
    params = problem.event_params_values.copy()
    time_samples = np.linspace(0.0, 1.2e-3, 80, dtype=float)
    gate_a_hist = np.zeros(len(time_samples), dtype=float)
    gate_b_hist = np.zeros(len(time_samples), dtype=float)
    gate_c_hist = np.zeros(len(time_samples), dtype=float)

    mode_a_idx = problem.uid2idx_event_params[next(var.uid for var in problem.get_runtime_mode_parameters() if var.name == "gate_a_mode_bridge_2level_test")]
    mode_b_idx = problem.uid2idx_event_params[next(var.uid for var in problem.get_runtime_mode_parameters() if var.name == "gate_b_mode_bridge_2level_test")]
    mode_c_idx = problem.uid2idx_event_params[next(var.uid for var in problem.get_runtime_mode_parameters() if var.name == "gate_c_mode_bridge_2level_test")]

    sample_idx = 0
    while sample_idx < len(time_samples):
        current_time: float = float(time_samples[sample_idx])
        theta_value: float = float(2.0 * np.pi * 50.0 * current_time)
        x[problem.get_var_idx(next(var for var in problem.get_algebraic_vars() if var.name == "theta_pll_test"))] = theta_value
        x[problem.get_var_idx(tracked_vars["m_a"])] = 0.3 * np.sin(theta_value)
        x[problem.get_var_idx(tracked_vars["m_b"])] = 0.3 * np.sin(theta_value - 2.0 * np.pi / 3.0)
        x[problem.get_var_idx(tracked_vars["m_c"])] = 0.3 * np.sin(theta_value + 2.0 * np.pi / 3.0)
        boundary_updater.update(current_time, x, params)
        gate_a_hist[sample_idx] = params[mode_a_idx]
        gate_b_hist[sample_idx] = params[mode_b_idx]
        gate_c_hist[sample_idx] = params[mode_c_idx]
        sample_idx += 1

    assert float(np.max(gate_a_hist) - np.min(gate_a_hist)) > 0.5
    assert float(np.max(gate_b_hist) - np.min(gate_b_hist)) > 0.5
    assert float(np.max(gate_c_hist) - np.min(gate_c_hist)) > 0.5
    assert float(np.min(gate_a_hist)) >= 0.0
    assert float(np.min(gate_b_hist)) >= 0.0
    assert float(np.min(gate_c_hist)) >= 0.0
    assert float(np.max(gate_a_hist)) <= 1.0
    assert float(np.max(gate_b_hist)) <= 1.0
    assert float(np.max(gate_c_hist)) <= 1.0
