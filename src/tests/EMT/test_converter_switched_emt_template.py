# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Dict
from VeraGridEngine.Utils.Symbolic.symbolic import Var,Const
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Templates.Emt.converter_switched_emt_template import get_switched_emt_converter
from VeraGridEngine.Utils.Symbolic.block import find_name_in_block


class GenericEmtProblem(EmtProblemTemplate):
    """
    Minimal EMT problem used by switched converter structural tests.
    """

    __slots__ = []


def test_switched_converter_template_builds_on_bridge_filter_control_stack() -> None:
    """
    Verify that the switched converter template builds and exposes the embedded bridge/filter/control stack.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    templ = get_switched_emt_converter(vf=vf, name="VSC")
    static_parameter_values_mapping: Dict[Var, Const] = dict()
    problem = GenericEmtProblem(sys_block=templ.block, glob_time=vf.add_var("t_switched_converter_case"),static_parameter_values_mapping=static_parameter_values_mapping)
    runtime_parameter_names = [var.name for var in problem.get_variable_parameters()]
    mode_names = [var.name for var in problem.get_runtime_mode_parameters()]

    assert find_name_in_block("i_A", templ.block) is not None
    assert find_name_in_block("v_conv_a", templ.block) is not None
    assert find_name_in_block("i_d_ref", templ.block) is not None
    assert find_name_in_block("v_cmd_d", templ.block) is not None
    assert find_name_in_block("gate_a", templ.block) is not None
    assert find_name_in_block("theta_pll", templ.block) is not None
    assert "t_enable_sw" in runtime_parameter_names
    assert "switching_enabled_mode" in mode_names
    assert "gate_a_mode" in mode_names
    assert "gate_b_mode" in mode_names
    assert "gate_c_mode" in mode_names
