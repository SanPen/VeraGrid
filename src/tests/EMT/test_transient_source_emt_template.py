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

    assert [var.name for var in templ.block.state_vars] == ["t_src"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "step_final",
        "step_init",
        "step_time",
    ]


def test_ramp_voltage_source_emt_template_exposes_ramp_parameters_and_conductance() -> None:
    vf: VarFactory = VarFactory()
    templ = get_ramp_voltage_source_emt_template(vf=vf, name="RampVoltageCase")

    assert [var.name for var in templ.block.state_vars] == ["t_src"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "g_src",
        "ramp_end",
        "ramp_final",
        "ramp_init",
        "ramp_start",
    ]


def test_double_exponential_current_source_emt_template_exposes_impulse_parameters() -> None:
    vf: VarFactory = VarFactory()
    templ = get_double_exponential_current_source_emt_template(vf=vf, name="DoubleExpCase")

    assert sorted(var.name for var in templ.block.event_dict.keys()) == ["alpha", "amp", "beta", "delay"]


def test_heidler_current_source_emt_template_exposes_heidler_parameters() -> None:
    vf: VarFactory = VarFactory()
    templ = get_heidler_current_source_emt_template(vf=vf, name="HeidlerCase")

    assert sorted(var.name for var in templ.block.event_dict.keys()) == ["delay", "front_time", "order", "peak", "tail_time"]


def test_cigre_surge_current_source_emt_template_exposes_cigre_parameters() -> None:
    vf: VarFactory = VarFactory()
    templ = get_cigre_surge_current_source_emt_template(vf=vf, name="CigreCase")

    assert sorted(var.name for var in templ.block.event_dict.keys()) == ["a", "b", "delay", "i1", "i2", "n", "t1", "t2", "tn"]
