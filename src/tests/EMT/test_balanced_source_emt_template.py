# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.balanced_source_emt_template import get_balanced_3ph_current_source_emt_template
from VeraGridEngine.Templates.Emt.balanced_source_emt_template import get_balanced_3ph_voltage_source_emt_template
from VeraGridEngine.Templates.Emt.balanced_source_emt_template import get_controlled_balanced_3ph_current_source_emt_template
from VeraGridEngine.Templates.Emt.balanced_source_emt_template import get_controlled_balanced_3ph_voltage_source_emt_template


def test_balanced_3ph_current_source_template_exposes_three_phase_bus_inputs_and_state() -> None:
    vf: VarFactory = VarFactory()
    templ = get_balanced_3ph_current_source_emt_template(vf=vf, name="BalancedCurrentCase")

    assert [var.name for var in templ.block.in_vars] == [
        "v_A_BalancedCurrentCase",
        "v_B_BalancedCurrentCase",
        "v_C_BalancedCurrentCase",
    ]
    assert [var.name for var in templ.block.out_vars] == [
        "i_A_BalancedCurrentCase",
        "i_B_BalancedCurrentCase",
        "i_C_BalancedCurrentCase",
    ]
    assert [var.name for var in templ.block.state_vars] == ["theta_src_BalancedCurrentCase"]


def test_controlled_balanced_3ph_current_source_template_exposes_single_amplitude_command() -> None:
    vf: VarFactory = VarFactory()
    templ = get_controlled_balanced_3ph_current_source_emt_template(vf=vf, name="ControlledBalancedCurrentCase")

    assert [var.name for var in templ.block.in_vars] == [
        "v_A_ControlledBalancedCurrentCase",
        "v_B_ControlledBalancedCurrentCase",
        "v_C_ControlledBalancedCurrentCase",
        "i_amp_cmd_ControlledBalancedCurrentCase",
    ]
    assert [var.name for var in templ.block.out_vars] == [
        "i_A_ControlledBalancedCurrentCase",
        "i_B_ControlledBalancedCurrentCase",
        "i_C_ControlledBalancedCurrentCase",
    ]


def test_balanced_3ph_voltage_source_template_exposes_norton_conductance() -> None:
    vf: VarFactory = VarFactory()
    templ = get_balanced_3ph_voltage_source_emt_template(vf=vf, name="BalancedVoltageCase")

    assert [var.name for var in templ.block.in_vars] == [
        "v_A_BalancedVoltageCase",
        "v_B_BalancedVoltageCase",
        "v_C_BalancedVoltageCase",
    ]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "V_amp_BalancedVoltageCase",
        "V_offset_BalancedVoltageCase",
        "f_src_BalancedVoltageCase",
        "g_src_BalancedVoltageCase",
        "phi_deg_A_BalancedVoltageCase",
    ]


def test_controlled_balanced_3ph_voltage_source_template_exposes_single_voltage_amplitude_command() -> None:
    vf: VarFactory = VarFactory()
    templ = get_controlled_balanced_3ph_voltage_source_emt_template(vf=vf, name="ControlledBalancedVoltageCase")

    assert [var.name for var in templ.block.in_vars] == [
        "v_A_ControlledBalancedVoltageCase",
        "v_B_ControlledBalancedVoltageCase",
        "v_C_ControlledBalancedVoltageCase",
        "v_amp_cmd_ControlledBalancedVoltageCase",
    ]
    assert [var.name for var in templ.block.out_vars] == [
        "i_A_ControlledBalancedVoltageCase",
        "i_B_ControlledBalancedVoltageCase",
        "i_C_ControlledBalancedVoltageCase",
    ]
