# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Dict, Tuple

import numpy as np

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Templates.Emt.bridge_filter_2level_3ph_emt_template import get_bridge_filter_2level_3ph_emt_template
from VeraGridEngine.Utils.procedural_logic import build_boundary_updater_from_block
from VeraGridEngine.Utils.Symbolic.block import Block, find_name_in_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


class GenericEmtProblem(EmtProblemTemplate):
    """
    Minimal EMT problem used by standalone bridge + filter tests.
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


def _build_bridge_filter_problem() -> Tuple[GenericEmtProblem, Dict[str, Var]]:
    """
    Build one standalone bridge + filter EMT problem.

    :return: EMT problem and tracked variables.
    """
    vf: VarFactory = VarFactory()
    block_name: str = "bridge_filter_case"
    theta_pll: Var
    theta_pll_eq: Expr
    omega_base: Var
    omega_base_eq: Expr
    v_A: Var
    v_A_eq: Expr
    v_B: Var
    v_B_eq: Expr
    v_C: Var
    v_C_eq: Expr
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
    R_f: Var
    R_f_eq: Expr
    L_f: Var
    L_f_eq: Expr
    bridge_filter_block: Block = get_bridge_filter_2level_3ph_emt_template(vf=vf, name=block_name).block
    root_block: Block
    problem: GenericEmtProblem
    tracked_vars: Dict[str, Var] = dict()

    theta_pll, theta_pll_eq = _build_constant_algebraic_var(vf=vf, name="theta_pll_test", value=0.0)
    omega_base, omega_base_eq = _build_constant_algebraic_var(vf=vf, name="omega_base_test", value=2.0 * np.pi * 50.0)
    v_A, v_A_eq = _build_constant_algebraic_var(vf=vf, name="v_A_test", value=0.0)
    v_B, v_B_eq = _build_constant_algebraic_var(vf=vf, name="v_B_test", value=0.0)
    v_C, v_C_eq = _build_constant_algebraic_var(vf=vf, name="v_C_test", value=0.0)
    v_cmd_d, v_cmd_d_eq = _build_constant_algebraic_var(vf=vf, name="v_cmd_d_test", value=0.3)
    v_cmd_q, v_cmd_q_eq = _build_constant_algebraic_var(vf=vf, name="v_cmd_q_test", value=0.0)
    v_cmd_0, v_cmd_0_eq = _build_constant_algebraic_var(vf=vf, name="v_cmd_0_test", value=0.0)
    v_dc, v_dc_eq = _build_constant_algebraic_var(vf=vf, name="v_dc_test", value=1.0)
    k_v_conv, k_v_conv_eq = _build_constant_algebraic_var(vf=vf, name="k_v_conv_test", value=0.5)
    m_max, m_max_eq = _build_constant_algebraic_var(vf=vf, name="m_max_test", value=0.95)
    vdc_floor, vdc_floor_eq = _build_constant_algebraic_var(vf=vf, name="vdc_floor_test", value=0.05)
    R_f, R_f_eq = _build_constant_algebraic_var(vf=vf, name="R_f_test", value=0.02)
    L_f, L_f_eq = _build_constant_algebraic_var(vf=vf, name="L_f_test", value=0.08)

    bridge_filter_block.connect(
        bridge_filter_block.in_vars,
        list([
            theta_pll,
            omega_base,
            v_A,
            v_B,
            v_C,
            v_cmd_d,
            v_cmd_q,
            v_cmd_0,
            v_dc,
            k_v_conv,
            m_max,
            vdc_floor,
            omega_sw,
            carrier_phase,
            R_f,
            L_f,
        ]),
    )

    root_block = Block(
        name="BridgeFilter2LevelStandaloneCase",
        children=list([bridge_filter_block]),
        algebraic_vars=list([theta_pll, omega_base, v_A, v_B, v_C, v_cmd_d, v_cmd_q, v_cmd_0, v_dc, k_v_conv, m_max, vdc_floor, R_f, L_f]),
        algebraic_eqs=list([theta_pll_eq, omega_base_eq, v_A_eq, v_B_eq, v_C_eq, v_cmd_d_eq, v_cmd_q_eq, v_cmd_0_eq, v_dc_eq, k_v_conv_eq, m_max_eq, vdc_floor_eq, R_f_eq, L_f_eq]),
        event_dict=dict([
            (omega_sw, Const(2.0 * np.pi * 1000.0)),
            (carrier_phase, Const(0.0)),
        ]),
    )
    root_block.unify_blocks()
    static_parameter_values_mapping: Dict[Var, Const] = dict()
    problem = GenericEmtProblem(sys_block=root_block, glob_time=vf.add_var("t_bridge_filter_problem"),static_parameter_values_mapping=static_parameter_values_mapping)
    tracked_vars["m_a"] = find_name_in_block("m_a", problem.sys_block)
    tracked_vars["m_b"] = find_name_in_block("m_b", problem.sys_block)
    tracked_vars["m_c"] = find_name_in_block("m_c", problem.sys_block)
    tracked_vars["gate_a"] = find_name_in_block("gate_a", problem.sys_block)
    tracked_vars["gate_b"] = find_name_in_block("gate_b", problem.sys_block)
    tracked_vars["gate_c"] = find_name_in_block("gate_c", problem.sys_block)
    tracked_vars["i_A"] = find_name_in_block("i_A", problem.sys_block)
    tracked_vars["i_B"] = find_name_in_block("i_B", problem.sys_block)
    tracked_vars["i_C"] = find_name_in_block("i_C", problem.sys_block)

    return problem, tracked_vars


def test_bridge_filter_2level_3ph_template_has_filter_states_and_switches_all_phases() -> None:
    """
    Verify that the bridge + filter block exposes filter states and that the PWM logic toggles the three gates.

    :return: None.
    """
    problem: GenericEmtProblem
    tracked_vars: Dict[str, Var]
    boundary_updater = None
    x: np.ndarray
    params: np.ndarray
    time_samples: np.ndarray
    gate_a_hist: np.ndarray
    gate_b_hist: np.ndarray
    gate_c_hist: np.ndarray
    mode_a_idx: int
    mode_b_idx: int
    mode_c_idx: int
    sample_idx: int

    problem, tracked_vars = _build_bridge_filter_problem()
    boundary_updater = build_boundary_updater_from_block(problem)
    x = problem.get_x0().copy()
    params = problem.event_params_values.copy()
    time_samples = np.linspace(0.0, 1.2e-3, 80, dtype=float)
    gate_a_hist = np.zeros(len(time_samples), dtype=float)
    gate_b_hist = np.zeros(len(time_samples), dtype=float)
    gate_c_hist = np.zeros(len(time_samples), dtype=float)

    mode_a_idx = problem.uid2idx_event_params[next(var.uid for var in problem.get_runtime_mode_parameters() if var.name == "gate_a_mode")]
    mode_b_idx = problem.uid2idx_event_params[next(var.uid for var in problem.get_runtime_mode_parameters() if var.name == "gate_b_mode")]
    mode_c_idx = problem.uid2idx_event_params[next(var.uid for var in problem.get_runtime_mode_parameters() if var.name == "gate_c_mode")]

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

    assert len(problem.get_state_vars()) == 3
    assert tracked_vars["i_A"] is not None
    assert tracked_vars["i_B"] is not None
    assert tracked_vars["i_C"] is not None
    assert float(np.max(gate_a_hist) - np.min(gate_a_hist)) > 0.5
    assert float(np.max(gate_b_hist) - np.min(gate_b_hist)) > 0.5
    assert float(np.max(gate_c_hist) - np.min(gate_c_hist)) > 0.5
    assert float(np.min(gate_a_hist)) >= 0.0
    assert float(np.min(gate_b_hist)) >= 0.0
    assert float(np.min(gate_c_hist)) >= 0.0
    assert float(np.max(gate_a_hist)) <= 1.0
    assert float(np.max(gate_b_hist)) <= 1.0
    assert float(np.max(gate_c_hist)) <= 1.0
