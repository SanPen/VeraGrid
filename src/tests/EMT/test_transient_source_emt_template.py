# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.transient_source_emt_template import get_cigre_surge_current_source_emt_template
from VeraGridEngine.Templates.Emt.transient_source_emt_template import get_double_exponential_current_source_emt_template
from VeraGridEngine.Templates.Emt.transient_source_emt_template import get_heidler_current_source_emt_template
from VeraGridEngine.Templates.Emt.transient_source_emt_template import get_ramp_voltage_source_emt_template
from VeraGridEngine.Templates.Emt.transient_source_emt_template import get_step_current_source_emt_template


def test_step_current_source_emt_template_exposes_time_state_and_step_parameters() -> None:
    vf: VarFactory = VarFactory()
    templ = get_step_current_source_emt_template(vf=vf, name="StepCurrentCase")

    assert [var.name for var in templ.block.state_vars] == ["t_src_StepCurrentCase_1ph"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "step_final_StepCurrentCase_1ph",
        "step_init_StepCurrentCase_1ph",
        "step_time_StepCurrentCase_1ph",
    ]


def test_ramp_voltage_source_emt_template_exposes_ramp_parameters_and_conductance() -> None:
    vf: VarFactory = VarFactory()
    templ = get_ramp_voltage_source_emt_template(vf=vf, name="RampVoltageCase")

    assert [var.name for var in templ.block.state_vars] == ["t_src_RampVoltageCase_1ph"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "g_src_RampVoltageCase_1ph",
        "ramp_end_RampVoltageCase_1ph",
        "ramp_final_RampVoltageCase_1ph",
        "ramp_init_RampVoltageCase_1ph",
        "ramp_start_RampVoltageCase_1ph",
    ]


def test_double_exponential_current_source_emt_template_exposes_impulse_parameters() -> None:
    vf: VarFactory = VarFactory()
    templ = get_double_exponential_current_source_emt_template(vf=vf, name="DoubleExpCase")

    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "alpha_DoubleExpCase_1ph",
        "amp_DoubleExpCase_1ph",
        "beta_DoubleExpCase_1ph",
        "delay_DoubleExpCase_1ph",
    ]


def test_heidler_current_source_emt_template_exposes_heidler_parameters() -> None:
    vf: VarFactory = VarFactory()
    templ = get_heidler_current_source_emt_template(vf=vf, name="HeidlerCase")

    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "delay_HeidlerCase_1ph",
        "front_time_HeidlerCase_1ph",
        "order_HeidlerCase_1ph",
        "peak_HeidlerCase_1ph",
        "tail_time_HeidlerCase_1ph",
    ]


def test_cigre_surge_current_source_emt_template_exposes_cigre_parameters() -> None:
    vf: VarFactory = VarFactory()
    templ = get_cigre_surge_current_source_emt_template(vf=vf, name="CigreCase")

    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "a_CigreCase_1ph",
        "b_CigreCase_1ph",
        "delay_CigreCase_1ph",
        "i1_CigreCase_1ph",
        "i2_CigreCase_1ph",
        "n_CigreCase_1ph",
        "t1_CigreCase_1ph",
        "t2_CigreCase_1ph",
        "tn_CigreCase_1ph",
    ]
