"""Regression tests for the native RMS HVDC Dynamic Editor library models."""

from __future__ import annotations

import math

import pytest
from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_library import DynamicEditorLibrary, LibraryLeafSpec
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_graphics import BlockItem, GenericBlockItem
from VeraGrid.Gui.DynamicModelEditor.dynamic_block_preparation import prepare_block_for_editing
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_tab import DynamicEditorTab
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_utilities import (
    create_block_of_type,
    create_default_template_builder,
    get_blocktype2template_builder_dict,
    initialize_template_builder_from_block,
    synchronize_vsc_library_initialization,
)
from VeraGridEngine.Devices.Branches.dc_line import DcLine
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagramNode
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Templates.Rms.dc_line_rms_template_v2 import DcLineRmsTemplateV2
from VeraGridEngine.Templates.Rms.hvdc_vsc_gfl_rms_template_v2 import (
    HvdcVscGflRmsTemplate,
    VscActiveControlRmsTemplate,
    VscReactiveControlRmsTemplate,
)
from VeraGridEngine.Templates.template_definition import TemplateDefinition
from VeraGridEngine.Utils.Symbolic.block import Block, find_connections
from VeraGridEngine.Utils.Symbolic.templates_common_functions import synchronize_saved_rms_root_mappings_from_children
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import (
    BlockType,
    ConverterControlType,
    DeviceType,
    DynamicSimulationMode,
    DynEditorGraphicsModes,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)


@pytest.fixture(scope="module", autouse=True)
def vsc_library_application() -> QtWidgets.QApplication:
    """Keep Qt alive for the Library and real Apply integration tests.

    :return: Shared application using the offscreen platform when newly made.
    """
    application: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if application is None:
        application = QtWidgets.QApplication(list(("VSC library regression", "-platform", "offscreen")))
    else:
        pass
    return application


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
        VarPowerFlowReferenceType.Vdc,
        VarPowerFlowReferenceType.Vmt,
        VarPowerFlowReferenceType.Vat,
    ]
    assert [variable.ref for variable in block.out_vars] == [
        VarPowerFlowReferenceType.Pf,
        VarPowerFlowReferenceType.Pt,
        VarPowerFlowReferenceType.Qt,
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


def test_hvdc_vsc_pi_decomposition_connects_integral_states_to_outputs() -> None:
    """Keep every explicit PI integral state connected to its output.

    :return: None.
    """
    var_factory: VarFactory = VarFactory()
    block: Block = HvdcVscGflRmsTemplate(var_factory).eval().block
    converter_block: Block = block.children[0]
    pll_block: Block = converter_block.children[5]
    pll_integrator_block: Block = pll_block.children[1]
    pi_blocks: list[Block] = list((
        converter_block.children[0],
        converter_block.children[1],
        converter_block.children[3],
        converter_block.children[4],
        pll_integrator_block,
    ))

    # Opening each nested block performs this same equation decomposition. The
    # generated children must preserve both ends of every explicit PI path.
    pi_block: Block
    for pi_block in pi_blocks:
        integral_state: Var = pi_block.state_vars[0]
        controlled_output: Var = pi_block.algebraic_vars[0]
        prepared_block: Block
        block_types: dict[int, BlockType]
        prepared_block, block_types = prepare_block_for_editing(
            block=pi_block,
            var_factory=var_factory,
        )
        integral_state_producers: list[Block] = list()
        integral_state_consumers: list[Block] = list()
        output_producers: list[Block] = list()
        child: Block
        for child in prepared_block.children:
            if integral_state in child.out_vars:
                integral_state_producers.append(child)
            else:
                pass
            if integral_state in child.in_vars:
                integral_state_consumers.append(child)
            else:
                pass
            if controlled_output in child.out_vars:
                output_producers.append(child)
            else:
                pass

        assert len(block_types) > 0, pi_block.name
        assert len(integral_state_producers) > 0, pi_block.name
        assert len(integral_state_consumers) > 0, pi_block.name
        assert len(output_producers) > 0, pi_block.name


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
    """Create complete RMS blocks with the transformer's root port order.

    :return: None.
    """
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
    assert [variable.ref for variable in transformer.out_vars] == [
        VarPowerFlowReferenceType.Pf,
        VarPowerFlowReferenceType.Qf,
        VarPowerFlowReferenceType.Pt,
        VarPowerFlowReferenceType.Qt,
    ]
    assert len(transformer.children) == 1
    equation_block: Block = transformer.children[0]
    assert equation_block.algebraic_vars == transformer.out_vars


def test_dc_line_power_flow_variables_have_no_explicit_init_equations() -> None:
    """Keep If_dc, Pf and Pt under authoritative power-flow initialization."""
    template_definition: DcLineRmsTemplateV2 = DcLineRmsTemplateV2(VarFactory())
    assert set(template_definition.params_dict.keys()) == set(("name",))
    dc_line_block: Block = template_definition.eval().block
    equation_block: Block = dc_line_block.children[0]
    resistance: Var = dc_line_block.api_obj_mapping[ParamPowerFlowReferenceType.dc_line_r_pu]
    inductance: Var = next(variable for variable in equation_block.event_dict if variable.name == "l_dc")
    assert len(equation_block.init_eqs) == 0
    assert equation_block.parameters[resistance].value is None
    assert equation_block.event_dict[inductance].value == 0.05
    dc_line_block.set_parameter_in_model(var_name="l_dc", new_value=0.08)
    assert equation_block.event_dict[inductance].value == 0.08
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


def test_catalogue_assignment_connects_vsc_and_dc_line_dc_terminals() -> None:
    """Connect catalogue-assigned mixed and pure DC RMS terminal contracts.

    :return: None.
    """
    circuit: MultiCircuit = MultiCircuit()
    dc_from_bus: Bus = Bus(name="DC from", is_dc=True)
    dc_to_bus: Bus = Bus(name="DC to", is_dc=True)
    ac_bus: Bus = Bus(name="AC terminal")
    circuit.add_bus(dc_from_bus)
    circuit.add_bus(dc_to_bus)
    circuit.add_bus(ac_bus)

    vsc: VSC = VSC(name="VSC", bus_from=dc_from_bus, bus_to=ac_bus)
    dc_line: DcLine = DcLine(name="DC line", bus_from=dc_from_bus, bus_to=dc_to_bus)
    circuit.add_vsc(vsc)
    circuit.add_dc_line(dc_line)

    # Template-property assignment follows the same automatic copy-and-connect
    # path used when the user selects one reusable model from the catalogue.
    vsc.rms_template = HvdcVscGflRmsTemplate(circuit.var_factory).eval()
    dc_line.rms_template = DcLineRmsTemplateV2(circuit.var_factory).eval()

    vsc_vdc: Var = vsc.rms_model.external_mapping[VarPowerFlowReferenceType.Vdc]
    vsc_vm: Var = vsc.rms_model.external_mapping[VarPowerFlowReferenceType.Vmt]
    vsc_va: Var = vsc.rms_model.external_mapping[VarPowerFlowReferenceType.Vat]
    dc_line_vdc_from: Var = dc_line.rms_model.external_mapping[VarPowerFlowReferenceType.Vmf]
    dc_line_vdc_to: Var = dc_line.rms_model.external_mapping[VarPowerFlowReferenceType.Vmt]
    bus_vdc_from: Var = dc_from_bus.rms_model.external_mapping[VarPowerFlowReferenceType.Vdc]
    bus_vdc_to: Var = dc_to_bus.rms_model.external_mapping[VarPowerFlowReferenceType.Vdc]
    bus_vm: Var = ac_bus.rms_model.external_mapping[VarPowerFlowReferenceType.Vm]
    bus_va: Var = ac_bus.rms_model.external_mapping[VarPowerFlowReferenceType.Va]

    assert vsc_vdc.uid == bus_vdc_from.uid
    assert vsc_vm.uid == bus_vm.uid
    assert vsc_va.uid == bus_va.uid
    assert dc_line_vdc_from.uid == bus_vdc_from.uid
    assert dc_line_vdc_to.uid == bus_vdc_to.uid


def test_rms_save_synchronizes_child_mappings_to_the_root() -> None:
    """Mirror child power-flow and static-parameter mappings on RMS save."""
    generator: Generator = Generator()
    var_factory: VarFactory = VarFactory()
    active_power: Var = var_factory.add_var("P", reference=VarPowerFlowReferenceType.P)
    resistance: Var = var_factory.add_var("R")
    child: Block = Block(
        algebraic_vars=list((active_power,)),
        algebraic_eqs=list((active_power,)),
        out_vars=list((active_power,)),
        parameters=dict(((resistance, Const(None)),)),
        external_mapping=dict(((VarPowerFlowReferenceType.P, active_power),)),
        api_obj_mapping=dict(((ParamPowerFlowReferenceType.R1, resistance),)),
    )
    root: Block = Block(children=list((child,)))
    generator.rms_model = root

    synchronize_saved_rms_root_mappings_from_children(device=generator)

    assert root.external_mapping[VarPowerFlowReferenceType.P] is active_power
    assert root.api_obj_mapping[ParamPowerFlowReferenceType.R1] is resistance


def _build_vsc_library_component(vf: VarFactory, block_type: BlockType, name: str) -> Block:
    """Follow the native-drop builder or direct-factory path for one component.

    :param vf: Shared editor factory.
    :param block_type: Library payload being materialized.
    :param name: Requested component name.
    :return: Generated symbolic component.
    """
    builder: TemplateDefinition | None = create_default_template_builder(vf, block_type, name)
    if builder is None:
        block: Block | None = create_block_of_type(vf, block_type, name)
        assert block is not None
        return block
    else:
        # The actual builder-backed GUI drop consumes .block, not a bare Block.
        template: RmsModelTemplate = builder.eval()
        assert isinstance(template, RmsModelTemplate)
        return template.block


def _assert_vsc_component_is_closed(block: Block) -> None:
    """Reject undeclared dependencies, missing owners and hidden init symbols.

    :param block: Standalone component or assembled model under inspection.
    :return: None.
    """
    declared: set[int] = set(variable.uid for variable in block.in_vars)
    owned: set[int] = set()
    candidate: Block
    variable: Var
    for candidate in block.get_all_blocks():
        assert len(candidate.diff_vars) == 0
        assert len(candidate.state_vars) == len(candidate.state_eqs)
        assert len(candidate.algebraic_vars) == len(candidate.algebraic_eqs)
        local_owned: set[int] = set()
        variable_group: list[Var]
        for variable_group in (candidate.state_vars, candidate.algebraic_vars):
            for variable in variable_group:
                assert variable.uid not in owned
                owned.add(variable.uid)
                local_owned.add(variable.uid)
                declared.add(variable.uid)
        declared.update(variable.uid for variable in candidate.event_dict)
        declared.update(variable.uid for variable in candidate.parameters)
        # Decomposition keeps original init_eqs at the component boundary;
        # the variables themselves then belong to its operation children.
        initialization_scope: set[int] = set(variable.uid for variable in candidate.get_all_vars())
        assert all(variable.uid in initialization_scope for variable in candidate.init_eqs)
    assert all(variable.uid in owned for variable in block.out_vars)

    # Check event and initialization expressions as well as runtime equations;
    # the original nested controls relied on parent-only initialization data.
    expression: Expr
    for candidate in block.get_all_blocks():
        expression_group: list[Expr]
        for expression_group in (
            candidate.state_eqs, candidate.algebraic_eqs,
            list(candidate.init_eqs.values()), list(candidate.event_dict.values()),
        ):
            for expression in expression_group:
                assert all(variable.uid in declared for variable in expression.get_vars()), (
                    candidate.name, str(expression)
                )


@pytest.mark.parametrize("block_type,inputs,outputs", (
    (BlockType.VSC_PLL_RMS, ("Vm", "Va"), ("vd", "vq", "omega")),
    (BlockType.VSC_ELECTRICAL_RMS,
     ("vd", "vq", "omega", "y_vd_hat", "y_vq_hat"),
     ("i_d", "i_q", "P", "Q")),
    (BlockType.VSC_ACTIVE_CONTROL_RMS, ("Vdc_state", "i_q"), ("i_q_ref",)),
    (BlockType.VSC_REACTIVE_CONTROL_RMS, ("Q", "i_d"), ("i_d_ref",)),
    (BlockType.VSC_CURRENT_LIMITER_RMS, ("i_d_ref", "i_q_ref", "i_q"), ("i_d_ref_sat", "i_q_ref_sat")),
    (BlockType.VSC_VD_HAT_RMS, ("i_d", "i_d_ref_sat"), ("y_vd_hat",)),
    (BlockType.VSC_VQ_HAT_RMS, ("i_q", "i_q_ref_sat"), ("y_vq_hat",)),
    (BlockType.VSC_DC_LINK_RMS, ("Vdc", "Pf_vsc", "Pt_vsc", "i_d", "i_q"), ("Vdc_state",)),
    (BlockType.VSC_TERMINAL_POWER_RMS, ("Vdc", "Vdc_state", "P", "Q"), ("Pf_vsc", "Pt_vsc", "Qt_vsc")),
))
def test_vsc_library_components_have_complete_independent_contracts(
        block_type: BlockType, inputs: tuple[str, ...], outputs: tuple[str, ...],
) -> None:
    """Build every public component without borrowing symbols from a parent.

    :param block_type: Library payload to instantiate.
    :param inputs: Expected ordered input labels.
    :param outputs: Expected ordered output labels.
    :return: None.
    """
    vf: VarFactory = VarFactory()
    block: Block = _build_vsc_library_component(vf, block_type, "Component")
    assert tuple(variable.name for variable in block.in_vars) == inputs
    assert tuple(variable.name for variable in block.out_vars) == outputs
    _assert_vsc_component_is_closed(block)

    # Dropping a second identically named block must not connect either copy.
    second: Block = _build_vsc_library_component(vf, block_type, "Component")
    first_ids: set[int] = set(variable.uid for variable in block.get_all_vars())
    second_ids: set[int] = set(variable.uid for variable in second.get_all_vars())
    assert first_ids.isdisjoint(second_ids)
    first_refs: set[int] = set(
        variable.shared_ref.uid for variable in block.get_all_vars() if variable.shared_ref is not None
    )
    second_refs: set[int] = set(
        variable.shared_ref.uid for variable in second.get_all_vars() if variable.shared_ref is not None
    )
    assert first_refs.isdisjoint(second_refs)


def test_vsc_components_are_registered_in_the_requested_library_categories() -> None:
    """Keep the complete VSC and expose devices, controls and terminal equations.

    :return: None.
    """
    library: DynamicEditorLibrary = DynamicEditorLibrary(api_object=VSC(), mode=DynamicSimulationMode.RMS)
    controls: set[BlockType] = set(
        leaf.payload for leaf in library.control_rms_related_blocks[DeviceType.VscDevice]
    )
    assert controls == set((
        BlockType.VSC_PLL_RMS, BlockType.VSC_ACTIVE_CONTROL_RMS,
        BlockType.VSC_REACTIVE_CONTROL_RMS, BlockType.VSC_CURRENT_LIMITER_RMS,
        BlockType.VSC_VD_HAT_RMS, BlockType.VSC_VQ_HAT_RMS,
    ))
    devices: set[BlockType] = set(_get_device_library_payloads(VSC()))
    assert set((BlockType.GFL_VSC_HVDC_RMS, BlockType.VSC_ELECTRICAL_RMS, BlockType.VSC_DC_LINK_RMS)) <= devices
    assert controls.isdisjoint(devices)
    assert BlockType.VSC_TERMINAL_POWER_RMS in set(leaf.payload for leaf in library.common_rms_device_blocks)
    assert library.tree_structure["Control blocks"] == library.control_rms_related_blocks[DeviceType.VscDevice]


@pytest.mark.parametrize("block_type,label,old_name", (
    (BlockType.VSC_VD_HAT_RMS, "d-axis current PI controller", "vd_hat"),
    (BlockType.VSC_VQ_HAT_RMS, "q-axis current PI controller", "vq_hat"),
))
def test_vsc_current_pi_names_preserve_symbolic_and_library_contracts(
        block_type: BlockType, label: str, old_name: str,
) -> None:
    """Rename current PIs without changing ports, state names or native types.

    :param block_type: Historical native identifier retained for saved models.
    :param label: Descriptive name shown for newly built controllers.
    :param old_name: Original controller name and symbolic state suffix.
    :return: None.
    """
    library: DynamicEditorLibrary = DynamicEditorLibrary(api_object=VSC(), mode=DynamicSimulationMode.RMS)
    leaf: LibraryLeafSpec = next(
        candidate for candidate in library.control_rms_related_blocks[DeviceType.VscDevice]
        if candidate.payload == block_type
    )
    assert leaf.label == label
    assert label in leaf.search_text
    assert old_name in leaf.search_text

    # The complete model uses the same names, but preserves its existing
    # integral-state and voltage-correction identifiers for scripts/results.
    complete: Block = HvdcVscGflRmsTemplate(VarFactory()).eval().block
    controller: Block = next(candidate for candidate in complete.get_all_blocks() if candidate.name == label)
    assert controller.state_vars[0].name == f"xi_{old_name}"
    assert controller.out_vars[0].name == f"y_{old_name}"

    # Native drops receive a readable numbered label; explicit caller names
    # and old saved block names remain untouched.
    dropped: Block = _build_vsc_library_component(VarFactory(), block_type, f"{block_type.name}_1")
    assert dropped.name == f"{label}_1"
    assert dropped.state_vars[0].name == f"xi_{block_type.name}_1"
    assert tuple(variable.name for variable in dropped.in_vars) == tuple(
        variable.name for variable in controller.in_vars
    )
    assert dropped.out_vars[0].name == controller.out_vars[0].name
    restored: Block = Block.parse(dropped.to_dict())
    assert restored.name == dropped.name
    assert restored.out_vars[0].uid == dropped.out_vars[0].uid
    custom_name: str
    for custom_name in (old_name, "My current regulator"):
        custom: Block = _build_vsc_library_component(VarFactory(), block_type, custom_name)
        assert custom.name == custom_name
        assert Block.parse(custom.to_dict()).name == custom_name


@pytest.mark.parametrize("block_type,label", (
    (BlockType.VSC_VD_HAT_RMS, "d-axis current PI controller"),
    (BlockType.VSC_VQ_HAT_RMS, "q-axis current PI controller"),
))
@pytest.mark.parametrize("compact", (False, True))
def test_vsc_current_pi_drop_keeps_scene_and_diagram_names_aligned(
        vsc_library_application: QtWidgets.QApplication,
        block_type: BlockType, label: str, compact: bool,
) -> None:
    """Persist the friendly name through both native graphical creation paths.

    :param vsc_library_application: Qt application owning the editor widgets.
    :param block_type: Current controller's unchanged native type.
    :param label: Expected descriptive label before its instance suffix.
    :param compact: Whether to exercise the compact BlockItem creation path.
    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    dc_bus: Bus = Bus(name="DC", is_dc=True)
    ac_bus: Bus = Bus(name="AC")
    grid.add_bus(dc_bus)
    grid.add_bus(ac_bus)
    device: VSC = VSC(bus_from=dc_bus, bus_to=ac_bus)
    grid.add_vsc(device)
    root: Block = Block(name="Current controllers")
    device.rms_model = root
    tab: DynamicEditorTab = DynamicEditorTab(
        var_factory=grid.var_factory, block=root, api_object=device, circuit=grid,
        current_theme=DynEditorGraphicsModes.LIGHT, mode=DynamicSimulationMode.RMS,
    )
    try:
        assert tab._editor is not None
        item: BlockItem | GenericBlockItem | None
        if compact:
            item = tab._editor.create_block_item(block_type, 0.0, 0.0)
        else:
            item = tab._editor.create_block_item_from_blocktype(block_type, 0.0, 0.0)
        assert item is not None
        assert item.subsys is not None
        assert item.subsys.name == f"{label}_1"
        assert item.name_item.toPlainText() == item.subsys.name
        node: BlockDiagramNode | None = tab._editor.diagram.node_data.get(item.subsys.uid, None)
        assert node is not None
        assert node.name == item.subsys.name
        assert node.tpe == block_type.name
    finally:
        tab.prepare_to_delete()
        tab.deleteLater()
        vsc_library_application.processEvents()


@pytest.mark.parametrize("branch_label, expected_types", (
    ("Control blocks", (
        BlockType.VSC_PLL_RMS, BlockType.VSC_ACTIVE_CONTROL_RMS,
        BlockType.VSC_REACTIVE_CONTROL_RMS, BlockType.VSC_CURRENT_LIMITER_RMS,
        BlockType.VSC_VD_HAT_RMS, BlockType.VSC_VQ_HAT_RMS,
    )),
    ("Devices", (
        BlockType.GFL_VSC_HVDC_RMS, BlockType.VSC_ELECTRICAL_RMS, BlockType.VSC_DC_LINK_RMS,
    )),
    ("Basic_devices", (BlockType.VSC_TERMINAL_POWER_RMS,)),
))
def test_vsc_library_components_have_registered_drag_payloads(
        branch_label: str,
        expected_types: tuple[BlockType, ...],
) -> None:
    """Expose the restored components through the restructured Qt drag model.

    :param branch_label: Visible library branch containing the requested blocks.
    :param expected_types: Native payload types expected once in that branch.
    :return: None.
    """
    library: DynamicEditorLibrary = DynamicEditorLibrary(api_object=VSC(), mode=DynamicSimulationMode.RMS)
    seen_types: set[BlockType] = set()
    branch_row: int
    leaf_row: int

    # Inspect the built tree, not only the lists used to construct it: a merge
    # can retain definitions without exposing them as draggable library items.
    for branch_row in range(library.library_model.rowCount()):
        branch_index: QtCore.QModelIndex = library.library_model.index(branch_row, 0)
        if library.library_model.data(branch_index) == branch_label:
            for leaf_row in range(library.library_model.rowCount(branch_index)):
                leaf_index: QtCore.QModelIndex = library.library_model.index(leaf_row, 0, branch_index)
                payload: object = library.library_model.data(leaf_index, library.block_role)
                if isinstance(payload, BlockType) and payload in expected_types:
                    assert payload not in seen_types
                    seen_types.add(payload)
                    assert library.library_model.flags(leaf_index) & QtCore.Qt.ItemFlag.ItemIsDragEnabled
                    # The editor resolves the opaque MIME token back to this
                    # same BlockType before choosing its factory or builder.
                    mime_data: QtCore.QMimeData = library.library_model.mimeData(list((leaf_index,)))
                    token: str = bytes(mime_data.data(library.mime_type)).decode("utf-8")
                    assert library.library_model.get_drag_payload(token) == payload
                else:
                    pass
        else:
            pass
    assert seen_types == set(expected_types)


def test_vsc_control_library_branch_is_contextual() -> None:
    """Keep VSC RMS controls out of EMT and unrelated RMS device editors.

    :return: None.
    """
    emt_library: DynamicEditorLibrary = DynamicEditorLibrary(api_object=VSC(), mode=DynamicSimulationMode.EMT)
    generator_library: DynamicEditorLibrary = DynamicEditorLibrary(
        api_object=Generator(), mode=DynamicSimulationMode.RMS,
    )
    assert "Control blocks" not in emt_library.tree_structure
    assert "Control blocks" not in generator_library.tree_structure


@pytest.mark.parametrize("control1", (
    ConverterControlType.Vm_dc, ConverterControlType.Pdc, ConverterControlType.Pac,
))
@pytest.mark.parametrize("control2", (ConverterControlType.Qac, ConverterControlType.Vm_ac))
def test_standalone_vsc_control_modes_survive_serialization(
        control1: ConverterControlType, control2: ConverterControlType,
) -> None:
    """Recover controller options even when the block was renamed and reloaded.

    :param control1: Active-axis structural mode.
    :param control2: Reactive-axis structural mode.
    :return: None.
    """
    active: VscActiveControlRmsTemplate = VscActiveControlRmsTemplate(VarFactory())
    reactive: VscReactiveControlRmsTemplate = VscReactiveControlRmsTemplate(VarFactory())
    active.params_dict["control1"].value = control1
    reactive.params_dict["control2"].value = control2
    builder: TemplateDefinition
    block_type: BlockType
    for builder, block_type in (
        (active, BlockType.VSC_ACTIVE_CONTROL_RMS), (reactive, BlockType.VSC_REACTIVE_CONTROL_RMS),
    ):
        block: Block = builder.eval().block
        block.name = "Renamed controller"
        restored: Block = Block.parse(block.to_dict())
        reopened: TemplateDefinition | None = create_default_template_builder(VarFactory(), block_type, block.name)
        assert reopened is not None
        initialize_template_builder_from_block(reopened, restored, block_type)
        option_name: str = "control1" if block_type == BlockType.VSC_ACTIVE_CONTROL_RMS else "control2"
        assert reopened.get_value(option_name) == builder.get_value(option_name)
        _assert_vsc_component_is_closed(restored)


def _assemble_vsc_from_library(vf: VarFactory, decomposed: bool = False) -> Block:
    """Wire independent library components as a user would assemble the model.

    :param vf: Editor factory used for native drops and explicit connections.
    :param decomposed: Whether to open the component internals before wiring.
    :return: Flat VSC composition with the same physical root interface.
    """
    pll: Block = _build_vsc_library_component(vf, BlockType.VSC_PLL_RMS, "PLL_explicit_PI")
    electrical: Block = _build_vsc_library_component(vf, BlockType.VSC_ELECTRICAL_RMS, "Electrical")
    active: Block = _build_vsc_library_component(vf, BlockType.VSC_ACTIVE_CONTROL_RMS, "Vdc_ctrl")
    reactive: Block = _build_vsc_library_component(vf, BlockType.VSC_REACTIVE_CONTROL_RMS, "Qac_ctrl")
    limiter: Block = _build_vsc_library_component(vf, BlockType.VSC_CURRENT_LIMITER_RMS, "Current limiter")
    vd: Block = _build_vsc_library_component(vf, BlockType.VSC_VD_HAT_RMS, "vd_hat")
    vq: Block = _build_vsc_library_component(vf, BlockType.VSC_VQ_HAT_RMS, "vq_hat")
    capacitor: Block = _build_vsc_library_component(vf, BlockType.VSC_DC_LINK_RMS, "DC-link capacitor")
    terminal: Block = _build_vsc_library_component(vf, BlockType.VSC_TERMINAL_POWER_RMS, "Terminal")
    if decomposed:
        component: Block
        for component in (electrical, vd, vq):
            prepare_block_for_editing(component, vf)
    else:
        pass
    # Wire exactly the original electrical and current-PI port contracts.
    vf.add_connections(electrical.in_vars, list((
        pll.out_vars[0], pll.out_vars[1], pll.out_vars[2], vd.out_vars[0], vq.out_vars[0],
    )))
    vf.add_connections(active.in_vars, list((capacitor.out_vars[0], electrical.out_vars[1])))
    vf.add_connections(reactive.in_vars, list((electrical.out_vars[3], electrical.out_vars[0])))
    vf.add_connections(limiter.in_vars, list((reactive.out_vars[0], active.out_vars[0], electrical.out_vars[1])))
    vf.add_connections(vd.in_vars, list((electrical.out_vars[0], limiter.out_vars[0])))
    vf.add_connections(vq.in_vars, list((electrical.out_vars[1], limiter.out_vars[1])))
    vf.add_connections(terminal.in_vars[1:], list((
        capacitor.out_vars[0], electrical.out_vars[2], electrical.out_vars[3],
    )))
    vf.add_connections(capacitor.in_vars, list((
        terminal.in_vars[0], terminal.out_vars[0], terminal.out_vars[1],
        electrical.out_vars[0], electrical.out_vars[1],
    )))
    device: VSC = VSC()
    device.rms_model = Block(
        name="Manual VSC",
        children=list((pll, electrical, active, reactive, limiter, vd, vq, capacitor, terminal)),
        in_vars=list((terminal.in_vars[0], pll.in_vars[0], pll.in_vars[1])),
        out_vars=list(terminal.out_vars),
    )
    synchronize_saved_rms_root_mappings_from_children(device)
    # Persist the same type metadata used by a real Library drop. Reopening
    # must not depend on an in-memory block-type lookup or component names.
    block_type: BlockType
    for component, block_type in (
        (electrical, BlockType.VSC_ELECTRICAL_RMS),
        (vd, BlockType.VSC_VD_HAT_RMS),
        (vq, BlockType.VSC_VQ_HAT_RMS),
    ):
        device.rms_model.diagram.node_data[component.uid] = BlockDiagramNode(
            name=component.name, x=0.0, y=0.0, tpe=block_type.name,
            device_uid=component.uid, api_object_name="VSC",
            state_ins=0, state_outs=list(), algeb_ins=len(component.in_vars),
            algeb_outs=list(variable.name for variable in component.out_vars), color="",
        )
    unresolved: list[Var] = synchronize_vsc_library_initialization(
        root=device.rms_model,
    )
    assert unresolved == list()
    return device.rms_model


@pytest.mark.parametrize("manual,decomposed", ((False, False), (True, False), (True, True)))
def test_vsc_components_initialize_consistently_with_nonzero_filter_resistance(
        manual: bool, decomposed: bool,
) -> None:
    """Resolve the explicit initialization graph without a time-domain solver.

    Nonzero R detects incorrect zero PI biases that a lossless example hides.
    Run this for both complete and independently dropped/wired components.

    :param manual: Whether to assemble individual Library entries.
    :param decomposed: Whether the component internals were opened before wiring.
    :return: None.
    """
    vf: VarFactory = VarFactory()
    block: Block = _assemble_vsc_from_library(vf, decomposed) if manual else HvdcVscGflRmsTemplate(vf).eval().block
    _assert_vsc_component_is_closed(block)
    block.set_parameter_in_model(var_name="R", new_value=0.03)
    values: dict[int, float] = dict()
    reference: VarPowerFlowReferenceType
    value: float
    for reference, value in (
        (VarPowerFlowReferenceType.Vdc, 1.0),
        (VarPowerFlowReferenceType.Vmt, 1.0),
        (VarPowerFlowReferenceType.Vat, 0.1),
        (VarPowerFlowReferenceType.Pf, 0.2),
        (VarPowerFlowReferenceType.Pt, -0.2),
        (VarPowerFlowReferenceType.Qt, -0.04),
    ):
        variable: Var | None = block.external_mapping[reference]
        assert variable is not None
        values[variable.uid] = value

    assignments: dict[int, Expr] = dict()
    all_blocks: list[Block] = block.get_all_blocks()
    candidate: Block
    parameter: Var
    expression: Expr
    for candidate in all_blocks:
        for parameter, expression in candidate.parameters.items():
            assert isinstance(expression, Const)
            assert expression.value is None
            assert parameter in block.api_obj_mapping.values()
            values[parameter.uid] = 0.0  # Explicit zero static loss coefficients.
        for parameter, expression in candidate.event_dict.items():
            assignments[parameter.uid] = expression
        for parameter, expression in candidate.init_eqs.items():
            assignments[parameter.uid] = expression

    # Resolve only expressions whose declared dependencies are available.
    # A stalled graph reports the actual missing bias or initialization port.
    while len(assignments) > 0:
        resolved: list[int] = list()
        uid: int
        for uid, expression in assignments.items():
            if all(variable.uid in values for variable in expression.get_vars()):
                values[uid] = float(expression.eval_uid(values))
                resolved.append(uid)
            else:
                pass
        assert len(resolved) > 0, list(str(expression) for expression in assignments.values())
        for uid in resolved:
            del assignments[uid]

    state_count: int = 0
    electrical: Block = block.children[1] if manual else block.children[0].children[6]
    assert math.isclose(values[electrical.in_vars[3].uid], -0.03 * 0.04 + 2.0 * 0.05 * 0.2, abs_tol=1e-12)
    assert math.isclose(values[electrical.in_vars[4].uid], 0.03 * 0.2, abs_tol=1e-12)
    for candidate in all_blocks:
        state_count += len(candidate.state_vars)
        equation_group: list[Expr]
        for equation_group in (candidate.state_eqs, candidate.algebraic_eqs):
            for expression in equation_group:
                if all(variable.uid in values for variable in expression.get_vars()):
                    assert math.isclose(float(expression.eval_uid(values)), 0.0, abs_tol=1.0e-12), (
                        candidate.name, str(expression)
                    )
                else:
                    # ELK auxiliary variables are not new explicit-init targets.
                    # Their runtime algebraic equations define them as before.
                    assert decomposed
    assert state_count == 9


@pytest.mark.parametrize("decomposed", (False, True))
def test_vsc_component_initialization_survives_reopen_and_renaming(decomposed: bool) -> None:
    """Rebind initialization after Ctrl+click, serialization and label changes.

    :param decomposed: Whether to decompose the components before wiring them.
    :return: None.
    """
    original: Block = _assemble_vsc_from_library(VarFactory(), decomposed=decomposed)
    restored: Block = Block.parse(original.to_dict())
    candidate: Block
    variable: Var
    for candidate in restored.get_all_blocks():
        candidate.name = "Renamed block"
        for variable in candidate.get_all_vars():
            variable.name = "renamed_" + str(variable.uid)
    assert synchronize_vsc_library_initialization(restored) == list()
    _assert_vsc_component_is_closed(restored)
    # Repeated save must not change the explicit initialization expressions.
    before: dict[int, str] = dict(
        (variable.uid, str(expression))
        for candidate in restored.get_all_blocks() for variable, expression in candidate.init_eqs.items()
    )
    assert synchronize_vsc_library_initialization(restored) == list()
    after: dict[int, str] = dict(
        (variable.uid, str(expression))
        for candidate in restored.get_all_blocks() for variable, expression in candidate.init_eqs.items()
    )
    assert before == after


def test_vsc_component_initialization_does_not_reconnect_disconnected_powers() -> None:
    """Discard stale init bindings without creating new graphical connections.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    root: Block = _assemble_vsc_from_library(vf)
    electrical: Block = root.children[1]
    terminal: Block = root.children[8]
    disconnected_p: Var = vf.add_var("Disconnected_P")
    disconnected_q: Var = vf.add_var("Disconnected_Q")
    terminal.update_equations(terminal.in_vars[2], disconnected_p)
    terminal.update_equations(terminal.in_vars[3], disconnected_q)
    terminal.in_vars[2] = disconnected_p
    terminal.in_vars[3] = disconnected_q
    connection_count: int = len(root.diagram.con_data)
    unresolved: list[Var] = synchronize_vsc_library_initialization(root)
    assert electrical.out_vars[2] in unresolved
    assert electrical.out_vars[3] in unresolved
    assert electrical.out_vars[2] not in electrical.init_eqs
    assert electrical.out_vars[3] not in electrical.init_eqs
    assert terminal.in_vars[2].uid != electrical.out_vars[2].uid
    assert terminal.in_vars[3].uid != electrical.out_vars[3].uid
    assert len(root.diagram.con_data) == connection_count


def test_vsc_library_apply_saves_initialization_bindings(vsc_library_application: QtWidgets.QApplication) -> None:
    """Exercise the real editor Apply path without running a simulation.

    :param vsc_library_application: Shared Qt application kept alive by pytest.
    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    dc_bus: Bus = Bus(name="DC", is_dc=True)
    ac_bus: Bus = Bus(name="AC")
    grid.add_bus(dc_bus)
    grid.add_bus(ac_bus)
    device: VSC = VSC(bus_from=dc_bus, bus_to=ac_bus)
    grid.add_vsc(device)
    root: Block = _assemble_vsc_from_library(grid.var_factory)
    electrical: Block = root.children[1]
    vd: Block = root.children[5]
    vq: Block = root.children[6]
    electrical.init_eqs.pop(electrical.out_vars[2])
    electrical.init_eqs.pop(electrical.out_vars[3])
    vd.init_eqs.pop(vd.out_vars[0])
    vq.init_eqs.pop(vq.out_vars[0])
    device.rms_model = root
    tab: DynamicEditorTab = DynamicEditorTab(
        var_factory=grid.var_factory, block=root, api_object=device, circuit=grid,
        current_theme=DynEditorGraphicsModes.LIGHT, mode=DynamicSimulationMode.RMS,
    )
    try:
        assert tab._editor is not None
        tab._editor.apply_changes()
        saved_blocks: dict[int, Block] = dict((candidate.uid, candidate) for candidate in device.rms_model.get_all_blocks())
        saved_electrical: Block = saved_blocks[electrical.uid]
        assert saved_electrical.out_vars[2] in saved_electrical.init_eqs
        assert saved_electrical.out_vars[3] in saved_electrical.init_eqs
        assert saved_blocks[vd.uid].out_vars[0] in saved_blocks[vd.uid].init_eqs
        assert saved_blocks[vq.uid].out_vars[0] in saved_blocks[vq.uid].init_eqs
        assert tab._editor.changes_applied
    finally:
        tab.prepare_to_delete()
        tab.deleteLater()
        vsc_library_application.processEvents()
