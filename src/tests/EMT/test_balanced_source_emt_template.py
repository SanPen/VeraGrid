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

    assert [var.name for var in templ.block.in_vars] == ["v_A", "v_B", "v_C"]
    assert [var.name for var in templ.block.out_vars] == ["i_A", "i_B", "i_C"]
    assert [var.name for var in templ.block.state_vars] == ["theta_src"]


def test_controlled_balanced_3ph_current_source_template_exposes_single_amplitude_command() -> None:
    vf: VarFactory = VarFactory()
    templ = get_controlled_balanced_3ph_current_source_emt_template(vf=vf, name="ControlledBalancedCurrentCase")

    assert [var.name for var in templ.block.in_vars] == ["v_A", "v_B", "v_C", "i_amp_cmd"]
    assert [var.name for var in templ.block.out_vars] == ["i_A", "i_B", "i_C"]


def test_balanced_3ph_voltage_source_template_exposes_norton_conductance() -> None:
    vf: VarFactory = VarFactory()
    templ = get_balanced_3ph_voltage_source_emt_template(vf=vf, name="BalancedVoltageCase")

    assert [var.name for var in templ.block.in_vars] == ["v_A", "v_B", "v_C"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "V_amp",
        "V_offset",
        "f_src",
        "g_src",
        "phi_deg_A",
    ]


def test_controlled_balanced_3ph_voltage_source_template_exposes_single_voltage_amplitude_command() -> None:
    vf: VarFactory = VarFactory()
    templ = get_controlled_balanced_3ph_voltage_source_emt_template(vf=vf, name="ControlledBalancedVoltageCase")

    assert [var.name for var in templ.block.in_vars] == ["v_A", "v_B", "v_C", "v_amp_cmd"]
    assert [var.name for var in templ.block.out_vars] == ["i_A", "i_B", "i_C"]
