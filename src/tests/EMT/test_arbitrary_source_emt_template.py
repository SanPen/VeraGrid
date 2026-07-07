# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.arbitrary_source_emt_template import get_arbitrary_waveform_current_source_emt_template
from VeraGridEngine.Templates.Emt.arbitrary_source_emt_template import get_arbitrary_waveform_voltage_source_emt_template


def test_arbitrary_waveform_current_source_template_exposes_time_state_and_lookup_params() -> None:
    vf: VarFactory = VarFactory()
    templ = get_arbitrary_waveform_current_source_emt_template(
        vf=vf,
        phN=False,
        phA=True,
        phB=False,
        phC=True,
        time_points=(0.0, 0.01, 0.03),
        value_points=(0.0, 1.0, -0.5),
        name="ArbCurrentCase",
    )
    resolved_name: str = "ArbCurrentCase_2ph"

    assert [var.name for var in templ.block.in_vars] == ["v_A", "v_C"]
    assert [var.name for var in templ.block.out_vars] == ["i_A", "i_C"]
    assert [var.name for var in templ.block.state_vars] == ["t_src"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "arr_x1",
        "arr_x2",
        "arr_x3",
        "arr_y1",
        "arr_y2",
        "arr_y3",
    ]


def test_arbitrary_waveform_voltage_source_template_exposes_conductance_and_lookup_params() -> None:
    vf: VarFactory = VarFactory()
    templ = get_arbitrary_waveform_voltage_source_emt_template(
        vf=vf,
        phN=False,
        phA=True,
        phB=True,
        phC=False,
        time_points=(0.0, 0.02, 0.04),
        value_points=(0.0, 0.5, 1.0),
        source_conductance_value=80.0,
        name="ArbVoltageCase",
    )
    resolved_name: str = "ArbVoltageCase_2ph"

    assert [var.name for var in templ.block.in_vars] == ["v_A", "v_B"]
    assert [var.name for var in templ.block.out_vars] == ["i_A", "i_B"]
    assert [var.name for var in templ.block.state_vars] == ["t_src"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        "arr_x1",
        "arr_x2",
        "arr_x3",
        "arr_y1",
        "arr_y2",
        "arr_y3",
        "g_src",
    ]
