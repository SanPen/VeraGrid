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

    assert [var.name for var in templ.block.in_vars] == [
        f"v_A_{resolved_name}",
        f"v_C_{resolved_name}",
    ]
    assert [var.name for var in templ.block.out_vars] == [
        f"i_A_{resolved_name}",
        f"i_C_{resolved_name}",
    ]
    assert [var.name for var in templ.block.state_vars] == [f"t_src_{resolved_name}"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        f"arr_x1_{resolved_name}",
        f"arr_x2_{resolved_name}",
        f"arr_x3_{resolved_name}",
        f"arr_y1_{resolved_name}",
        f"arr_y2_{resolved_name}",
        f"arr_y3_{resolved_name}",
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

    assert [var.name for var in templ.block.in_vars] == [
        f"v_A_{resolved_name}",
        f"v_B_{resolved_name}",
    ]
    assert [var.name for var in templ.block.out_vars] == [
        f"i_A_{resolved_name}",
        f"i_B_{resolved_name}",
    ]
    assert [var.name for var in templ.block.state_vars] == [f"t_src_{resolved_name}"]
    assert sorted(var.name for var in templ.block.event_dict.keys()) == [
        f"arr_x1_{resolved_name}",
        f"arr_x2_{resolved_name}",
        f"arr_x3_{resolved_name}",
        f"arr_y1_{resolved_name}",
        f"arr_y2_{resolved_name}",
        f"arr_y3_{resolved_name}",
        f"g_src_{resolved_name}",
    ]
