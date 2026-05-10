from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.xfmr_emt_template import get_xfmr_emt_template
from VeraGridEngine.enumerations import BlockType
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType, WindingType


def test_xfmr_emt_template_exposes_neutral_ports_for_grounded_star_sides() -> None:
    vf = VarFactory()
    templ = get_xfmr_emt_template(
        vf=vf,
        conn_f=WindingType.GroundedStar,
        conn_t=WindingType.GroundedStar,
        name="xfmr_yg_yg",
    )
    input_names = [var.name for var in templ.block.in_vars]
    output_names = [var.name for var in templ.block.out_vars]

    assert input_names[:4] == ["vf_N_xfmr_yg_yg", "vf_A_xfmr_yg_yg", "vf_B_xfmr_yg_yg", "vf_C_xfmr_yg_yg"]
    assert input_names[4:] == ["vt_N_xfmr_yg_yg", "vt_A_xfmr_yg_yg", "vt_B_xfmr_yg_yg", "vt_C_xfmr_yg_yg"]
    assert output_names[0] == "if_N_xfmr_yg_yg"
    assert output_names[4] == "it_N_xfmr_yg_yg"
    assert templ.block.external_mapping[VarPowerFlowRefferenceType.vf_N] is templ.block.in_vars[0]
    assert templ.block.external_mapping[VarPowerFlowRefferenceType.vt_N] is templ.block.in_vars[4]
    assert templ.block.external_mapping[VarPowerFlowRefferenceType.if_N] is templ.block.out_vars[0]
    assert templ.block.external_mapping[VarPowerFlowRefferenceType.it_N] is templ.block.out_vars[4]
    assert any(node.tpe == BlockType.GROUNDING_LINK_EMT.name for node in templ.block.diagram.node_data.values())


def test_xfmr_emt_template_exposes_neutral_only_on_star_side_of_delta_wye() -> None:
    vf = VarFactory()
    templ = get_xfmr_emt_template(
        vf=vf,
        conn_f=WindingType.Delta,
        conn_t=WindingType.GroundedStar,
        name="xfmr_d_yg",
    )
    input_names = [var.name for var in templ.block.in_vars]
    output_names = [var.name for var in templ.block.out_vars]

    assert input_names[:3] == ["vf_A_xfmr_d_yg", "vf_B_xfmr_d_yg", "vf_C_xfmr_d_yg"]
    assert input_names[3:] == ["vt_N_xfmr_d_yg", "vt_A_xfmr_d_yg", "vt_B_xfmr_d_yg", "vt_C_xfmr_d_yg"]
    assert output_names[0] == "if_A_xfmr_d_yg"
    assert output_names[3] == "it_N_xfmr_d_yg"
    assert templ.block.external_mapping[VarPowerFlowRefferenceType.vf_N] is None
    assert templ.block.external_mapping[VarPowerFlowRefferenceType.if_N] is None
    assert templ.block.external_mapping[VarPowerFlowRefferenceType.vt_N] is templ.block.in_vars[3]
    assert templ.block.external_mapping[VarPowerFlowRefferenceType.it_N] is templ.block.out_vars[3]


def test_xfmr_emt_template_treats_zigzag_as_one_non_neutral_side() -> None:
    vf = VarFactory()
    templ = get_xfmr_emt_template(
        vf=vf,
        conn_f=WindingType.ZigZag,
        conn_t=WindingType.GroundedStar,
        name="xfmr_z_yg",
    )
    input_names = [var.name for var in templ.block.in_vars]

    assert input_names[:3] == ["vf_A_xfmr_z_yg", "vf_B_xfmr_z_yg", "vf_C_xfmr_z_yg"]
    assert templ.block.external_mapping[VarPowerFlowRefferenceType.vf_N] is None
    assert templ.block.external_mapping[VarPowerFlowRefferenceType.if_N] is None
