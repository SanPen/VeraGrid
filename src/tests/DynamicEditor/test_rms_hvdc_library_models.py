"""Regression tests for the native RMS HVDC Dynamic Editor library models."""

from __future__ import annotations

from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_library import DynamicEditorLibrary, LibraryLeafSpec
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_preparation import prepare_block_for_editing
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_utilities import (
    create_block_of_type,
    get_blocktype2template_builder_dict,
    initialize_template_builder_from_block,
)
from VeraGridEngine.Devices.Branches.dc_line import DcLine
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Templates.Rms.dc_line_rms_template_v2 import DcLineRmsTemplateV2
from VeraGridEngine.Templates.Rms.hvdc_vsc_gfl_rms_template_v2 import HvdcVscGflRmsTemplate
from VeraGridEngine.Templates.template_definition import TemplateDefinition
from VeraGridEngine.Utils.Symbolic.block import Block, find_connections
from VeraGridEngine.Utils.Symbolic.templates_common_functions import synchronize_saved_rms_root_mappings_from_children
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import (
    BlockType,
    ConverterControlType,
    DeviceType,
    DynamicSimulationMode,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)


def _get_device_library_payloads(device: ALL_DEV_TYPES) -> list[BlockType]:
    """Return native RMS block types registered for one static device.

    :param device: Static device used to select the contextual library branch.
    :return: Native block types displayed for that device.
    """
    library: DynamicEditorLibrary = DynamicEditorLibrary(
        api_object=device,
        mode=DynamicSimulationMode.RMS,
    )
    leaves: list[LibraryLeafSpec] = library.device_rms_related_blocks.get(device.device_type, list())
    payloads: list[BlockType] = list()
    for leaf in leaves:
        if isinstance(leaf.payload, BlockType):
            payloads.append(leaf.payload)
        else:
            pass
    return payloads


def test_hvdc_case_devices_are_registered_in_the_rms_library() -> None:
    """Expose one complete RMS model for every dynamic HVDC-case device."""
    assert BlockType.VOLTAGE_SOURCE_RMS in _get_device_library_payloads(Generator())
    assert BlockType.TRANSFORMER_2W_RMS in _get_device_library_payloads(Transformer2W())
    assert BlockType.DC_LINE_RMS in _get_device_library_payloads(DcLine())
    assert BlockType.GFL_VSC_HVDC_RMS in _get_device_library_payloads(VSC())


def test_hvdc_vsc_library_entry_uses_only_the_v2_builder() -> None:
    """Map the single HVDC VSC leaf to the explicit-state configurable builder."""
    builders: dict[BlockType, type[TemplateDefinition]] = get_blocktype2template_builder_dict()
    assert builders[BlockType.GFL_VSC_HVDC_RMS] is HvdcVscGflRmsTemplate
    assert builders[BlockType.DC_LINE_RMS] is DcLineRmsTemplateV2


def test_dc_line_library_uses_the_device_name_only() -> None:
    """Display the explicit-state implementation under the concise device name.

    :return: None.
    """
    library: DynamicEditorLibrary = DynamicEditorLibrary(
        api_object=DcLine(),
        mode=DynamicSimulationMode.RMS,
    )
    leaves: list[LibraryLeafSpec] = library.device_rms_related_blocks.get(
        DeviceType.DCLineDevice,
        list(),
    )
    dc_line_labels: list[str] = [
        leaf.label for leaf in leaves
        if leaf.payload == BlockType.DC_LINE_RMS
    ]
    assert dc_line_labels == ["DC line"]


def test_hvdc_vsc_control_options_survive_block_properties_reopen() -> None:
    """Recover the selected VSC controls from persisted block metadata."""
    var_factory: VarFactory = VarFactory()
    builder: HvdcVscGflRmsTemplate = HvdcVscGflRmsTemplate(var_factory)
    builder.params_dict["control1"].value = ConverterControlType.Pdc
    builder.params_dict["control2"].value = ConverterControlType.Vm_ac
    builder.params_dict["cdc"].value = 0.77
    block: Block = builder.eval().block
    del block.__dict__["_modal_template_kind"]
    del block.__dict__["_modal_template_config"]

    reopened_builder: HvdcVscGflRmsTemplate = HvdcVscGflRmsTemplate(VarFactory())
    initialize_template_builder_from_block(
        builder=reopened_builder,
        block=block,
        block_type=BlockType.GFL_VSC_HVDC_RMS,
    )

    assert reopened_builder.get_value("control1") == ConverterControlType.Pdc
    assert reopened_builder.get_value("control2") == ConverterControlType.Vm_ac
    assert reopened_builder.get_value("cdc") == 0.77
    assert [variable.ref for variable in block.in_vars] == [
        VarPowerFlowReferenceType.Vmt,
        VarPowerFlowReferenceType.Vat,
        VarPowerFlowReferenceType.Vdc,
    ]
    assert [variable.ref for variable in block.out_vars] == [
        VarPowerFlowReferenceType.Pt,
        VarPowerFlowReferenceType.Qt,
        VarPowerFlowReferenceType.Pf,
    ]


def test_hvdc_vsc_control_changes_preserve_the_root_port_contract() -> None:
    """Keep existing diagram wires valid when either controller option changes."""
    first_builder: HvdcVscGflRmsTemplate = HvdcVscGflRmsTemplate(VarFactory())
    first_block: Block = first_builder.eval().block

    second_builder: HvdcVscGflRmsTemplate = HvdcVscGflRmsTemplate(VarFactory())
    second_builder.params_dict["control1"].value = ConverterControlType.Pac
    second_builder.params_dict["control2"].value = ConverterControlType.Vm_ac
    second_block: Block = second_builder.eval().block

    first_inputs: list[tuple[str, VarPowerFlowReferenceType | None]] = [
        (variable.name, variable.ref) for variable in first_block.in_vars
    ]
    second_inputs: list[tuple[str, VarPowerFlowReferenceType | None]] = [
        (variable.name, variable.ref) for variable in second_block.in_vars
    ]
    first_outputs: list[tuple[str, VarPowerFlowReferenceType | None]] = [
        (variable.name, variable.ref) for variable in first_block.out_vars
    ]
    second_outputs: list[tuple[str, VarPowerFlowReferenceType | None]] = [
        (variable.name, variable.ref) for variable in second_block.out_vars
    ]
    assert first_inputs == second_inputs
    assert first_outputs == second_outputs


def test_hvdc_vsc_uses_only_explicit_ordinary_states() -> None:
    """Keep PI, current and DC-link dynamics out of generalized diff vars."""
    block: Block = HvdcVscGflRmsTemplate(VarFactory()).eval().block
    all_blocks: list[Block] = block.get_all_blocks()
    state_names: set[str] = set()
    dynamic_block: Block
    state_variable: Var
    for dynamic_block in all_blocks:
        for state_variable in dynamic_block.state_vars:
            state_names.add(state_variable.name)
        assert len(dynamic_block.diff_vars) == 0

    assert "i_d" in state_names
    assert "i_q" in state_names
    assert "Vdc_state" in state_names
    assert "xi_PLL_integrator" in state_names
    assert "xi_Vdc_ctrl" in state_names


def test_hvdc_vsc_internal_blocks_expose_every_dynamic_signal_connection() -> None:
    """Give the Dynamic Editor explicit edges for every internal VSC signal."""
    block: Block = HvdcVscGflRmsTemplate(VarFactory()).eval().block
    converter_block: Block = block.children[0]
    terminal_block: Block = block.children[1]
    dc_link_block: Block = block.children[2]

    converter_terminal_pairs, _ = find_connections(converter_block, terminal_block)
    converter_dc_pairs, _ = find_connections(converter_block, dc_link_block)
    dc_converter_pairs, _ = find_connections(dc_link_block, converter_block)
    dc_terminal_pairs, _ = find_connections(dc_link_block, terminal_block)
    _, terminal_dc_power_pairs = find_connections(terminal_block, dc_link_block)

    assert {source.name for source, _ in converter_terminal_pairs} == {"P", "Q"}
    assert {source.name for source, _ in converter_dc_pairs} == {"i_d", "i_q"}
    assert {source.name for source, _ in dc_converter_pairs} == {"Vdc_state"}
    assert {source.name for source, _ in dc_terminal_pairs} == {"Vdc_state"}
    assert {source.name for source, _ in terminal_dc_power_pairs} == {"Pf_vsc", "Pt_vsc"}

    converter_children: list[Block] = converter_block.children
    connected_input_names: set[str] = set()
    target_block: Block
    source_block: Block
    for source_block in converter_children:
        for target_block in converter_children:
            if source_block is target_block:
                pass
            else:
                signal_pairs, _ = find_connections(source_block, target_block)
                connected_input_names.update(target.name for _, target in signal_pairs)

    assert {
        "Q",
        "i_d",
        "i_d_ref",
        "i_d_ref_sat",
        "i_q",
        "i_q_ref",
        "i_q_ref_sat",
        "omega",
        "vd",
        "vq",
        "y_vd_hat",
        "y_vq_hat",
    }.issubset(connected_input_names)

    pll_block: Block = converter_children[5]
    coordinate_block: Block = pll_block.children[0]
    pll_integrator_block: Block = pll_block.children[1]
    coordinate_integrator_pairs, _ = find_connections(coordinate_block, pll_integrator_block)
    integrator_coordinate_pairs, _ = find_connections(pll_integrator_block, coordinate_block)
    assert {source.name for source, _ in coordinate_integrator_pairs} == {"theta"}
    assert {source.name for source, _ in integrator_coordinate_pairs} == {"omega"}


def test_hvdc_vsc_initialization_equations_belong_to_variable_owners() -> None:
    """Keep internal P/Q initialization on their algebraic owner block."""
    block: Block = HvdcVscGflRmsTemplate(VarFactory()).eval().block
    converter_block: Block = block.children[0]
    electrical_block: Block = converter_block.children[6]
    initialized_names: set[str] = set(variable.name for variable in electrical_block.init_eqs)

    assert len(block.init_eqs) == 0
    assert {"P", "Q"}.issubset(initialized_names)
    assert set(variable.name for variable in electrical_block.init_eqs).issubset(
        set(variable.name for variable in electrical_block.state_vars + electrical_block.algebraic_vars)
    )


def test_hvdc_vsc_terminal_implicit_dae_is_not_decomposed() -> None:
    """Preserve the terminal voltage constraint when its nested editor opens."""
    block: Block = HvdcVscGflRmsTemplate(VarFactory()).eval().block
    terminal_block: Block = block.children[1]

    assert not terminal_block.is_decomposable
    assert not terminal_block.is_eq_decomposable()
    assert len(terminal_block.algebraic_vars) == 3
    assert len(terminal_block.algebraic_eqs) == 3


def test_legacy_terminal_decomposition_keeps_implicit_equations() -> None:
    """Reject a legacy lossy decomposition and retain its complete DAE."""
    var_factory: VarFactory = VarFactory()
    block: Block = HvdcVscGflRmsTemplate(var_factory).eval().block
    terminal_block: Block = block.children[1]
    terminal_block.is_decomposable = True

    prepared_block, block_types = prepare_block_for_editing(terminal_block, var_factory)

    assert prepared_block is terminal_block
    assert len(block_types) == 0
    assert not terminal_block.is_decomposable
    assert len(terminal_block.children) == 0
    assert len(terminal_block.algebraic_eqs) == 3


def test_voltage_source_and_transformer_native_blocks_can_be_created() -> None:
    """Create the two non-modal complete RMS blocks from their native types."""
    voltage_source: Block | None = create_block_of_type(
        var_factory=VarFactory(),
        block_type=BlockType.VOLTAGE_SOURCE_RMS,
        item_name="Voltage source",
    )
    transformer: Block | None = create_block_of_type(
        var_factory=VarFactory(),
        block_type=BlockType.TRANSFORMER_2W_RMS,
        item_name="Transformer 2W",
    )
    assert voltage_source is not None
    assert transformer is not None
    assert VarPowerFlowReferenceType.P in voltage_source.external_mapping
    assert VarPowerFlowReferenceType.Pf in transformer.external_mapping


def test_dc_line_power_flow_variables_have_no_explicit_init_equations() -> None:
    """Keep If_dc, Pf and Pt under authoritative power-flow initialization."""
    dc_line_block: Block = DcLineRmsTemplateV2(VarFactory()).eval().block
    equation_block: Block = dc_line_block.children[0]
    assert len(equation_block.init_eqs) == 0
    assert VarPowerFlowReferenceType.If_dc in dc_line_block.external_mapping
    assert VarPowerFlowReferenceType.Pf in dc_line_block.external_mapping
    assert VarPowerFlowReferenceType.Pt in dc_line_block.external_mapping
    assert [variable.name for variable in equation_block.out_vars] == ["Pf", "Pt"]
    assert [variable.name for variable in dc_line_block.out_vars] == ["Pf", "Pt"]


def test_dc_line_equation_decomposition_connects_both_terminal_powers() -> None:
    """Expose both Pf and Pt through the decomposed internal block diagram.

    :return: None.
    """
    var_factory: VarFactory = VarFactory()
    dc_line_block: Block = DcLineRmsTemplateV2(var_factory).eval().block
    equation_block: Block = dc_line_block.children[0]

    prepared_block: Block
    block_types: dict[int, BlockType]
    prepared_block, block_types = prepare_block_for_editing(
        block=equation_block,
        var_factory=var_factory,
    )

    decomposed_output_refs: set[VarPowerFlowReferenceType] = set()
    child_block: Block
    output_var: Var
    for child_block in prepared_block.children:
        for output_var in child_block.out_vars:
            if isinstance(output_var.ref, VarPowerFlowReferenceType):
                decomposed_output_refs.add(output_var.ref)
            else:
                pass

    assert len(block_types) > 0
    assert VarPowerFlowReferenceType.Pf in decomposed_output_refs
    assert VarPowerFlowReferenceType.Pt in decomposed_output_refs


def test_rms_save_synchronizes_child_mappings_to_the_root() -> None:
    """Mirror child power-flow and static-parameter mappings on RMS save."""
    generator: Generator = Generator()
    var_factory: VarFactory = VarFactory()
    active_power: Var = var_factory.add_var("P", reference=VarPowerFlowReferenceType.P)
    resistance: Var = var_factory.add_var("R")
    child: Block = Block(
        external_mapping=dict(((VarPowerFlowReferenceType.P, active_power),)),
        api_obj_mapping=dict(((ParamPowerFlowReferenceType.R1, resistance),)),
    )
    root: Block = Block(children=list((child,)))
    generator.rms_model = root

    synchronize_saved_rms_root_mappings_from_children(device=generator)

    assert root.external_mapping[VarPowerFlowReferenceType.P] is active_power
    assert root.api_obj_mapping[ParamPowerFlowReferenceType.R1] is resistance
