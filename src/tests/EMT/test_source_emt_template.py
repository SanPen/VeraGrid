# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.source_emt_template import get_controlled_current_source_emt_template
from VeraGridEngine.Templates.Emt.source_emt_template import get_controlled_voltage_source_emt_template
from VeraGridEngine.Templates.Emt.source_emt_template import get_current_source_emt_template
from VeraGridEngine.Templates.Emt.source_emt_template import get_voltage_source_emt_template
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


def test_current_source_emt_template_exposes_phase_inputs_outputs_and_event_values() -> None:
    vf: VarFactory = VarFactory()
    templ = get_current_source_emt_template(vf=vf, phN=False, phA=True, phB=False, phC=True, name="CurrentSourceCase")
    resolved_name: str = "CurrentSourceCase_2ph"

    assert [var.name for var in templ.block.in_vars] == ["v_A", "v_C"]
    assert [var.name for var in templ.block.out_vars] == ["i_A", "i_C"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "I_amp_A",
        "I_amp_C",
        "I_offset_A",
        "I_offset_C",
        "f_src",
        "phi_deg_A",
        "phi_deg_C",
    ]
    assert templ.block.external_mapping[VarPowerFlowReferenceType.v_A].name == "v_A"
    assert templ.block.external_mapping[VarPowerFlowReferenceType.i_C].name == "i_C"


def test_controlled_current_source_emt_template_exposes_command_inputs() -> None:
    vf: VarFactory = VarFactory()
    templ = get_controlled_current_source_emt_template(vf=vf, phN=True, phA=True, phB=False, phC=False, name="ControlledCurrentCase")
    resolved_name: str = "ControlledCurrentCase_2ph"

    assert [var.name for var in templ.block.in_vars] == ["v_N", "i_amp_cmd_N", "v_A", "i_amp_cmd_A"]
    assert [var.name for var in templ.block.out_vars] == ["i_N", "i_A"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "I_offset_A",
        "I_offset_N",
        "f_src",
        "phi_deg_A",
        "phi_deg_N",
    ]


def test_voltage_source_emt_template_exposes_source_parameters_and_norton_outputs() -> None:
    vf: VarFactory = VarFactory()
    templ = get_voltage_source_emt_template(vf=vf, phN=False, phA=True, phB=True, phC=False, name="VoltageSourceCase")
    resolved_name: str = "VoltageSourceCase_2ph"

    assert [var.name for var in templ.block.in_vars] == ["v_A", "v_B"]
    assert [var.name for var in templ.block.out_vars] == ["i_A", "i_B"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "V_amp_A",
        "V_amp_B",
        "V_offset_A",
        "V_offset_B",
        "f_src",
        "g_src",
        "phi_deg_A",
        "phi_deg_B",
    ]


def test_controlled_voltage_source_emt_template_exposes_command_inputs_and_conductance_param() -> None:
    vf: VarFactory = VarFactory()
    templ = get_controlled_voltage_source_emt_template(vf=vf, phN=False, phA=False, phB=True, phC=True, name="ControlledVoltageCase")
    resolved_name: str = "ControlledVoltageCase_2ph"

    assert [var.name for var in templ.block.in_vars] == ["v_B", "v_amp_cmd_B", "v_C", "v_amp_cmd_C"]
    assert [var.name for var in templ.block.out_vars] == ["i_B", "i_C"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "V_offset_B",
        "V_offset_C",
        "f_src",
        "g_src",
        "phi_deg_B",
        "phi_deg_C",
    ]
