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

    assert [var.name for var in templ.block.in_vars] == [
        f"v_A_{resolved_name}",
        f"v_C_{resolved_name}",
    ]
    assert [var.name for var in templ.block.out_vars] == [
        f"i_A_{resolved_name}",
        f"i_C_{resolved_name}",
    ]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        f"I_amp_A_{resolved_name}",
        f"I_amp_C_{resolved_name}",
        f"I_offset_A_{resolved_name}",
        f"I_offset_C_{resolved_name}",
        f"f_src_{resolved_name}",
        f"phi_deg_A_{resolved_name}",
        f"phi_deg_C_{resolved_name}",
    ]
    assert templ.block.external_mapping[VarPowerFlowReferenceType.v_A].name == f"v_A_{resolved_name}"
    assert templ.block.external_mapping[VarPowerFlowReferenceType.i_C].name == f"i_C_{resolved_name}"


def test_controlled_current_source_emt_template_exposes_command_inputs() -> None:
    vf: VarFactory = VarFactory()
    templ = get_controlled_current_source_emt_template(vf=vf, phN=True, phA=True, phB=False, phC=False, name="ControlledCurrentCase")
    resolved_name: str = "ControlledCurrentCase_2ph"

    assert [var.name for var in templ.block.in_vars] == [
        f"v_N_{resolved_name}",
        f"i_amp_cmd_N_{resolved_name}",
        f"v_A_{resolved_name}",
        f"i_amp_cmd_A_{resolved_name}",
    ]
    assert [var.name for var in templ.block.out_vars] == [
        f"i_N_{resolved_name}",
        f"i_A_{resolved_name}",
    ]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        f"I_offset_A_{resolved_name}",
        f"I_offset_N_{resolved_name}",
        f"f_src_{resolved_name}",
        f"phi_deg_A_{resolved_name}",
        f"phi_deg_N_{resolved_name}",
    ]


def test_voltage_source_emt_template_exposes_source_parameters_and_norton_outputs() -> None:
    vf: VarFactory = VarFactory()
    templ = get_voltage_source_emt_template(vf=vf, phN=False, phA=True, phB=True, phC=False, name="VoltageSourceCase")
    resolved_name: str = "VoltageSourceCase_2ph"

    assert [var.name for var in templ.block.in_vars] == [
        f"v_A_{resolved_name}",
        f"v_B_{resolved_name}",
    ]
    assert [var.name for var in templ.block.out_vars] == [
        f"i_A_{resolved_name}",
        f"i_B_{resolved_name}",
    ]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        f"V_amp_A_{resolved_name}",
        f"V_amp_B_{resolved_name}",
        f"V_offset_A_{resolved_name}",
        f"V_offset_B_{resolved_name}",
        f"f_src_{resolved_name}",
        f"g_src_{resolved_name}",
        f"phi_deg_A_{resolved_name}",
        f"phi_deg_B_{resolved_name}",
    ]


def test_controlled_voltage_source_emt_template_exposes_command_inputs_and_conductance_param() -> None:
    vf: VarFactory = VarFactory()
    templ = get_controlled_voltage_source_emt_template(vf=vf, phN=False, phA=False, phB=True, phC=True, name="ControlledVoltageCase")
    resolved_name: str = "ControlledVoltageCase_2ph"

    assert [var.name for var in templ.block.in_vars] == [
        f"v_B_{resolved_name}",
        f"v_amp_cmd_B_{resolved_name}",
        f"v_C_{resolved_name}",
        f"v_amp_cmd_C_{resolved_name}",
    ]
    assert [var.name for var in templ.block.out_vars] == [
        f"i_B_{resolved_name}",
        f"i_C_{resolved_name}",
    ]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        f"V_offset_B_{resolved_name}",
        f"V_offset_C_{resolved_name}",
        f"f_src_{resolved_name}",
        f"g_src_{resolved_name}",
        f"phi_deg_B_{resolved_name}",
        f"phi_deg_C_{resolved_name}",
    ]
