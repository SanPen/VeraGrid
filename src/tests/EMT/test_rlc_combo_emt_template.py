from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.load_exponential_emt_template import get_exponential_load_emt
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import get_grounding_link_emt_template
from VeraGridEngine.Templates.Emt.load_RLC_emt_template import get_shunt_rlc_combo_emt_template
from VeraGridEngine.Templates.Emt.load_zip_emt_template import get_load_ZIP_emt_template
from VeraGridEngine.enumerations import BlockType, ShuntConnectionType, VarPowerFlowReferenceType


def test_rlc_combo_emt_template_builds_r_plus_l_star_case() -> None:
    vf = VarFactory()
    templ = get_shunt_rlc_combo_emt_template(
        vf=vf,
        include_r=True,
        include_l=True,
        include_c=False,
        phA=True,
        phB=False,
        phC=False,
        connection_type=ShuntConnectionType.GroundedStar,
        name="rlc_combo_case",
    )

    assert templ.tpe.name == "LoadDevice"
    assert len(templ.block.in_vars) == 2
    assert len(templ.block.out_vars) == 2
    assert len(templ.block.algebraic_vars) == 2
    assert any(child.name.endswith("_grounding_link") for child in templ.block.children)
    assert any(node.tpe == BlockType.GROUNDING_LINK_EMT.name for node in templ.block.diagram.node_data.values())


def test_rlc_combo_emt_template_builds_neutralstar_with_explicit_neutral_port() -> None:
    vf = VarFactory()
    templ = get_shunt_rlc_combo_emt_template(
        vf=vf,
        include_r=True,
        include_l=False,
        include_c=False,
        phA=True,
        phB=False,
        phC=False,
        connection_type=ShuntConnectionType.NeutralStar,
        direct_r_value=25.0,
        name="rlc_combo_neutral",
    )

    input_names = [var.name for var in templ.block.in_vars]
    output_names = [var.name for var in templ.block.out_vars]

    assert input_names == ["v_N", "v_A"]
    assert output_names == ["i_N", "i_A"]
    assert templ.block.external_mapping[VarPowerFlowReferenceType.v_N] is templ.block.in_vars[0]
    assert templ.block.external_mapping[VarPowerFlowReferenceType.i_N] is templ.block.out_vars[0]
    assert not any(node.tpe == BlockType.GROUNDING_LINK_EMT.name for node in templ.block.diagram.node_data.values())


def test_rlc_combo_emt_template_builds_delta_with_direct_values() -> None:
    vf = VarFactory()
    templ = get_shunt_rlc_combo_emt_template(
        vf=vf,
        include_r=True,
        include_l=False,
        include_c=False,
        phA=True,
        phB=True,
        phC=True,
        connection_type=ShuntConnectionType.Delta,
        direct_r_value=25.0,
        name="rlc_combo_delta",
    )

    event_values_by_name: dict[str, float] = dict()
    parameter_var = None
    parameter_expr = None
    for parameter_var, parameter_expr in templ.block.event_dict.items():
        if parameter_var.name.startswith("R_"):
            assert parameter_expr.value is not None
            event_values_by_name[parameter_var.name] = float(parameter_expr.value)
        else:
            pass

    assert len(templ.block.in_vars) == 3
    assert len(templ.block.out_vars) == 3
    assert templ.block.external_mapping[VarPowerFlowReferenceType.v_N] is None
    assert templ.block.external_mapping[VarPowerFlowReferenceType.i_N] is None
    assert not any(node.tpe == BlockType.GROUNDING_LINK_EMT.name for node in templ.block.diagram.node_data.values())
    assert event_values_by_name["R_AB"] == 25.0
    assert event_values_by_name["R_BC"] == 25.0
    assert event_values_by_name["R_CA"] == 25.0


def test_rlc_combo_emt_template_rejects_delta_single_phase_case() -> None:
    vf = VarFactory()

    try:
        get_shunt_rlc_combo_emt_template(
            vf=vf,
            include_r=True,
            include_l=False,
            include_c=False,
            phA=True,
            phB=False,
            phC=False,
            connection_type=ShuntConnectionType.Delta,
            direct_r_value=25.0,
            name="rlc_combo_delta",
        )
    except ValueError as exc:
        assert "at least two active phases" in str(exc)
    else:
        raise AssertionError("Single-phase delta should be rejected")


def test_rlc_combo_emt_template_overrides_r_l_c_values_directly() -> None:
    vf = VarFactory()
    templ = get_shunt_rlc_combo_emt_template(
        vf=vf,
        include_r=True,
        include_l=True,
        include_c=True,
        phA=True,
        phB=False,
        phC=False,
        connection_type=ShuntConnectionType.GroundedStar,
        direct_r_value=25.0,
        direct_l_value=0.02,
        direct_c_value=4.0e-6,
        name="rlc_combo_direct_values",
    )

    event_values_by_prefix: dict[str, float] = dict()
    parameter_var = None
    parameter_expr = None
    for parameter_var, parameter_expr in templ.block.event_dict.items():
        if parameter_var.name.startswith(("R_", "L_", "C_")):
            assert parameter_expr.value is not None
            event_values_by_prefix[parameter_var.name[:2]] = float(parameter_expr.value)
        else:
            pass

    assert event_values_by_prefix["R_"] == 25.0
    assert event_values_by_prefix["L_"] == 0.02
    assert event_values_by_prefix["C_"] == 4.0e-6


def test_grounding_link_emt_template_builds_direct_r_plus_c_case() -> None:
    vf = VarFactory()
    templ = get_grounding_link_emt_template(
        vf=vf,
        include_r=True,
        include_l=False,
        include_c=True,
        direct_r_value=15.0,
        direct_c_value=3.0e-6,
        name="grounding_link_case",
    )

    assert len(templ.block.in_vars) == 1
    assert len(templ.block.out_vars) == 1
    assert templ.block.external_mapping[VarPowerFlowReferenceType.v_N] is templ.block.in_vars[0]
    assert templ.block.external_mapping[VarPowerFlowReferenceType.i_N] is templ.block.out_vars[0]
    assert any(child.name.endswith("_ground") for child in templ.block.children)


def test_exponential_load_emt_template_builds_neutralstar_topology() -> None:
    vf = VarFactory()
    templ = get_exponential_load_emt(
        vf=vf,
        phA=True,
        phB=False,
        phC=False,
        connection_type=ShuntConnectionType.NeutralStar,
        name="exp_load_neutral",
    )

    input_names = [var.name for var in templ.block.in_vars]
    output_names = [var.name for var in templ.block.out_vars]

    assert input_names == ["v_N", "v_A"]
    assert output_names == ["i_N", "i_A"]
    assert templ.block.external_mapping[VarPowerFlowReferenceType.v_N] is templ.block.in_vars[0]
    assert templ.block.external_mapping[VarPowerFlowReferenceType.i_N] is templ.block.out_vars[0]
    assert not any(node.tpe == BlockType.GROUNDING_LINK_EMT.name for node in templ.block.diagram.node_data.values())


def test_exponential_load_emt_template_builds_delta_topology() -> None:
    vf = VarFactory()
    templ = get_exponential_load_emt(
        vf=vf,
        phA=True,
        phB=True,
        phC=True,
        connection_type=ShuntConnectionType.Delta,
        name="exp_load_delta",
    )

    input_names = [var.name for var in templ.block.in_vars]
    output_names = [var.name for var in templ.block.out_vars]

    assert input_names == ["v_A", "v_B", "v_C"]
    assert output_names == ["i_A", "i_B", "i_C"]
    assert templ.block.external_mapping[VarPowerFlowReferenceType.v_N] is None
    assert templ.block.external_mapping[VarPowerFlowReferenceType.i_N] is None


def test_zip_load_emt_template_builds_delta_topology() -> None:
    vf = VarFactory()
    templ = get_load_ZIP_emt_template(
        vf=vf,
        phA=True,
        phB=True,
        phC=True,
        connection_type=ShuntConnectionType.Delta,
        name="zip_load_delta",
    )

    input_names = [var.name for var in templ.block.in_vars]
    output_names = [var.name for var in templ.block.out_vars]

    assert input_names == ["v_A", "v_B", "v_C"]
    assert output_names == ["i_A", "i_B", "i_C"]
    assert templ.block.external_mapping[VarPowerFlowReferenceType.v_N] is None
    assert templ.block.external_mapping[VarPowerFlowReferenceType.i_N] is None
