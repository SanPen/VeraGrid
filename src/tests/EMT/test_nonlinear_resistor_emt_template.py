from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Templates.Emt.nonlinear_resistor_emt_template import get_nonlinear_resistor_emt_template
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


def test_nonlinear_resistor_emt_template_builds_grounded_vi_curve_block() -> None:
    vf: VarFactory = VarFactory()
    templ: EmtModelTemplate = get_nonlinear_resistor_emt_template(
        vf=vf,
        voltage_points=list([0.0, 1.0, 1.5]),
        current_points=list([0.0, 0.1, 1.0]),
        name="nlr_case",
    )

    event_names: set[str] = set(var.name for var in templ.block.event_dict.keys())

    assert len(templ.block.in_vars) == 1
    assert len(templ.block.out_vars) == 1
    assert templ.block.external_mapping[VarPowerFlowReferenceType.v_N] is templ.block.in_vars[0]
    assert templ.block.external_mapping[VarPowerFlowReferenceType.i_N] is templ.block.out_vars[0]
    assert templ.block.in_vars[0].ref == VarPowerFlowReferenceType.v_N
    assert templ.block.out_vars[0].ref == VarPowerFlowReferenceType.i_N
    assert templ.block.out_vars[0] in templ.block.init_eqs
    assert any(child.name.endswith("_ground") for child in templ.block.children)
    assert "arr_v1_nlr_case" in event_names
    assert "arr_i3_nlr_case" in event_names
