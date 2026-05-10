# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.dc_source_emt_template import get_controlled_dc_current_source_emt_template
from VeraGridEngine.Templates.Emt.dc_source_emt_template import get_controlled_dc_voltage_source_emt_template
from VeraGridEngine.Templates.Emt.dc_source_emt_template import get_dc_current_source_emt_template
from VeraGridEngine.Templates.Emt.dc_source_emt_template import get_dc_voltage_source_emt_template
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType


def test_dc_current_source_emt_template_exposes_dc_bus_input_and_event_current() -> None:
    vf: VarFactory = VarFactory()
    templ = get_dc_current_source_emt_template(vf=vf, source_current_value=0.25, name="DcCurrentCase")

    assert [var.name for var in templ.block.in_vars] == ["v_dc_DcCurrentCase"]
    assert [var.name for var in templ.block.out_vars] == ["i_dc_DcCurrentCase"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == ["I_src_DcCurrentCase"]
    assert templ.block.external_mapping[VarPowerFlowRefferenceType.Vdc].name == "v_dc_DcCurrentCase"
    assert templ.block.external_mapping[VarPowerFlowRefferenceType.Idc].name == "i_dc_DcCurrentCase"


def test_controlled_dc_current_source_emt_template_exposes_current_command_input() -> None:
    vf: VarFactory = VarFactory()
    templ = get_controlled_dc_current_source_emt_template(vf=vf, name="ControlledDcCurrentCase")

    assert [var.name for var in templ.block.in_vars] == [
        "v_dc_ControlledDcCurrentCase",
        "i_cmd_ControlledDcCurrentCase",
    ]
    assert [var.name for var in templ.block.out_vars] == ["i_dc_ControlledDcCurrentCase"]
    assert len(templ.block.event_dict) == 0


def test_dc_voltage_source_emt_template_exposes_fixed_voltage_and_conductance() -> None:
    vf: VarFactory = VarFactory()
    templ = get_dc_voltage_source_emt_template(vf=vf, source_voltage_value=1.1, source_conductance_value=75.0, name="DcVoltageCase")

    assert [var.name for var in templ.block.in_vars] == ["v_dc_DcVoltageCase"]
    assert [var.name for var in templ.block.out_vars] == ["i_dc_DcVoltageCase"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "V_src_DcVoltageCase",
        "g_src_DcVoltageCase",
    ]


def test_controlled_dc_voltage_source_emt_template_exposes_voltage_command_input() -> None:
    vf: VarFactory = VarFactory()
    templ = get_controlled_dc_voltage_source_emt_template(vf=vf, source_conductance_value=60.0, name="ControlledDcVoltageCase")

    assert [var.name for var in templ.block.in_vars] == [
        "v_dc_ControlledDcVoltageCase",
        "v_cmd_ControlledDcVoltageCase",
    ]
    assert [var.name for var in templ.block.out_vars] == ["i_dc_ControlledDcVoltageCase"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == ["g_src_ControlledDcVoltageCase"]
