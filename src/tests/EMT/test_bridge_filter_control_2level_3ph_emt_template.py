# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Dict
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Templates.Emt.bridge_filter_control_2level_3ph_emt_template import get_bridge_filter_control_2level_3ph_emt_template
from VeraGridEngine.Utils.Symbolic.block import find_name_in_block


class GenericEmtProblem(EmtProblemTemplate):
    """
    Minimal EMT problem used by standalone bridge + filter + control tests.
    """

    __slots__ = []


def test_bridge_filter_control_2level_3ph_template_builds_and_exposes_expected_blocks() -> None:
    """
    Verify that the bridge + filter + control template builds, exposes the expected child blocks and carries procedural PWM logic.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    static_parameter_values_mapping: Dict[Var, Const] = dict()
    templ = get_bridge_filter_control_2level_3ph_emt_template(vf=vf, name="bridge_filter_control_case")
    problem = GenericEmtProblem(sys_block=templ.block, glob_time=vf.add_var("t_bridge_filter_control_case"),static_parameter_values_mapping=static_parameter_values_mapping)

    assert find_name_in_block("gate_a", templ.block) is not None
    assert find_name_in_block("i_A", templ.block) is not None
    assert find_name_in_block("theta_pll", templ.block) is not None
    assert find_name_in_block("v_cmd_d", templ.block) is not None
    assert len(problem.get_runtime_mode_parameters()) == 3


def test_bridge_filter_control_2level_3ph_template_exposes_bridge_pwm_variables() -> None:
    """
    Verify that the bridge + filter + control template exposes the embedded bridge PWM variables needed for the next integration step.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    static_parameter_values_mapping: Dict[Var, Const] = dict()
    templ = get_bridge_filter_control_2level_3ph_emt_template(vf=vf, name="bridge_filter_control_case")
    problem = GenericEmtProblem(sys_block=templ.block, glob_time=vf.add_var("t_bridge_filter_control_case_pwm"),static_parameter_values_mapping=static_parameter_values_mapping)
    mode_names = [var.name for var in problem.get_runtime_mode_parameters()]

    assert find_name_in_block("m_a", problem.sys_block) is not None
    assert find_name_in_block("m_b", problem.sys_block) is not None
    assert find_name_in_block("m_c", problem.sys_block) is not None
    assert "gate_a_mode" in mode_names
    assert "gate_b_mode" in mode_names
    assert "gate_c_mode" in mode_names
