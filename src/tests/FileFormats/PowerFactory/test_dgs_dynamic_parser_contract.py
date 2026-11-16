
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import copy
import hashlib
import keyword
import math
from pathlib import Path
from typing import Sequence, get_type_hints

import numpy as np
import pytest

from VeraGridEngine.Utils.Symbolic.explicit_initialization_symbolic import build_explicit_init_graph
from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.series_reactance import SeriesReactance
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit, parse_header
from VeraGridEngine.IO.dgs.dyn_dgs_parser import DynDgsParser
from VeraGridEngine.IO.dgs.dgs_logical_actuator_binding import (
    prepare_dgs_logical_actuator_topology,
)
from VeraGridEngine.IO.dgs.dgs_rms_measurement_binding import (
    DgsRmsMeasurementBindingReport,
    _connect_meter_aliases,
    _get_physical_meter_terminal_side,
    _get_veragrid_meter_name,
    bind_dgs_rms_measurements,
)
from VeraGridEngine.IO.dgs.dgs_rms_preparation import (
    _build_dgs_elmsym_fixed_injection_rms_template,
    bind_dgs_switch_event_runtime,
)
from VeraGridEngine.IO.dgs.dgs_to_veragrid import (
    add_dgs_terminal_buses,
    convert_dgs_to_monopolar_vsc,
    dgs_to_circuit,
)
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    DgsDirectRootBuildResult,
    DgsExpressionParser,
    DgsGraphicTreeResult,
    DgsGraphicalIndexes,
    DgsGraphicalConnectorKind,
    DgsSlotSignalDirection,
    DgsRootBlockResult,
    DgsLookupTable,
    ElmCompInstanceEntry,
    ParsedDgsBlockDefinition,
    UnsupportedDgsExpression,
    _bind_graphical_reference_internals,
    _bind_graphical_reference_states,
    _bind_graphical_reference_lookup_tables,
    _build_block_from_parsed,
    _resolve_graphical_child_lookup_tables,
    _resolve_direct_slot_runtime_output_indices,
    _slot_filter_names_a_registered_class,
    build_dgs_graphical_indexes,
    build_direct_root_elmcomp_block,
    build_graphical_arithmetic_block,
    build_graphical_switch_block,
    build_standalone_blkdef_block_from_parsed_block,
    dgs_to_root_block,
    build_dgs_root_block_from_circuit,
    extract_elmcomp_direct_instances,
    extract_root_slot_block_graphical_tree,
    extract_root_slot_graphical_tree_from_circuit,
    get_elmdsl_lookup_tables,
    get_unambiguous_elmcomp_direct_instances,
    parse_dgs_block_definitions_from_circuit,
)
from VeraGridEngine.IO.dgs.dgs_objects import (
    BlkDef,
    BlkDiv,
    BlkFrom,
    BlkGoto,
    BlkMul,
    BlkRef,
    BlkSig,
    BlkSlot,
    BlkSum,
    ElmComp,
    ElmDsl,
    ElmSind,
    ElmTerm,
    ElmVscmono,
    IntMat,
    PowerFactoryVscType,
    StaCubic,
    TypLne,
)
from VeraGridEngine.IO.dgs.dynamic_models.dgs_native_model_workflow import (
    NativeDgsEquipmentKind,
    NativeDgsEquipmentPlan,
    assemble_native_dgs_model,
    detect_native_dgs_equipment,
)
from VeraGridEngine.IO.dgs.dynamic_models.dynamic_model_import import (
    DgsDynamicTemplateConversionResult,
    DynamicModelImport,
    _assign_dgs_external_input_references,
    add_dynamic_import_selection_requests_to_circuit,
    apply_dgs_dynamic_templates_to_devices,
    build_dgs_dynamic_model_import_bundle,
    build_dynamic_import_template_fingerprint,
    convert_and_add_dgs_dynamic_templates_to_circuit,
    get_dgs_dynamic_host_device_tpe,
)


from VeraGridEngine.IO.file_open import FileOpen, FileOpenOptions
from VeraGridEngine.Topology.simulation_indices import SimulationIndices
from VeraGridEngine.Simulations.Rms.problems.rms_terminal_power_assembly import (
    assemble_rms_mapped_power_references,
)
from VeraGridEngine.IO.dynamic_model_import_types import (
    DynamicModelImportBundle,
    DynamicModelImportEntry,
    DynamicModelImportEntryAvailability,
    DynamicModelImportSelectionRequest,
    DynamicModelImportSource,
)
from VeraGridEngine.Utils.Symbolic.block import (
    Block,
    DynamicModelContract,
    RmsPhysicalMeterKind,
    RmsTerminalSide,
)
from VeraGridEngine.Templates.Rms.buses.bus_rms_template import (
    BusRmsTemplate,
    build_dc_bus_nodal_power_equation,
    dc_bus_rms_model_has_capacitive_state,
)
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import (
    EmtProblemTemplate,
)
from VeraGridEngine.Utils.Symbolic.symbolic import (
    BinOp,
    CmpOp,
    Comparison,
    Const,
    Expr,
    Func,
    Func2,
    UnOp,
    Var,
    get_expression_vars,
    rand,
)
from VeraGridEngine.Utils.procedural_logic import (
    ConditionalDiagnosticLogic,
    DelayedSwitchEventLogic,
    ProceduralLogicCodec,
    SampledValueLogic,
)
from VeraGridEngine.Templates.basic_block_runtime import (
    build_lookup_array_linear_runtime_template,
)
from VeraGridEngine.Templates.Rms.line.line_rms_template import (
    get_dc_line_rms_template,
)
from VeraGridEngine.Templates.Rms.buses.rms_meter_templates import (
    build_rms_phase_locked_loop_block,
)
from VeraGridEngine.Templates.Rms.transformers.transformer_rms_template import (
    get_transformer2w_rms,
)
from VeraGridEngine.basic_structures import LogEntry, Logger
from VeraGridEngine.enumerations import (
    ConverterControlType,
    DeviceType,
    DynamicSimulationMode,
    FileType,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)

from tests.symbolic_block_roundtrip import roundtrip_block


@pytest.mark.parametrize(
    "device_type",
    (DeviceType.GeneratorDevice, DeviceType.BatteryDevice),
)
def test_unresolved_elmsym_shell_uses_generator_power_mapping(
        device_type: DeviceType,
) -> None:
    """An ElmSym fallback must use its owning generator-family P/Q contract."""
    circuit: MultiCircuit = MultiCircuit()
    template: RmsModelTemplate = _build_dgs_elmsym_fixed_injection_rms_template(
        circuit=circuit,
        device_tpe=device_type,
    )
    mappings: dict[ParamPowerFlowReferenceType, Var] = dict()
    for block in template.block.get_all_blocks():
        mappings.update(block.api_obj_mapping)

    assert template.tpe is device_type
    assert ParamPowerFlowReferenceType.generator_p_pu in mappings
    assert ParamPowerFlowReferenceType.generator_q_pu in mappings
    assert ParamPowerFlowReferenceType.Pl0 not in mappings
    assert ParamPowerFlowReferenceType.Ql0 not in mappings


@pytest.mark.parametrize("target_domain", (DynamicSimulationMode.RMS, DynamicSimulationMode.EMT))
def test_dynamic_model_import_shares_parser_context_and_owns_conversion_result(
        target_domain: DynamicSimulationMode,
) -> None:
    """Use one source, destination and result through the parser-owned importer.

    :param target_domain: Explicit dynamic template destination.
    :return: None.
    """
    source: DgsCircuit = DgsCircuit()
    destination: MultiCircuit = MultiCircuit()
    logger: Logger = Logger()
    parser: DynDgsParser = DynDgsParser(source, destination, target_domain, logger)
    # Populate the source after construction: an importer that copied its
    # context would miss this isolated definition and fail to register it.
    source.parse_dgs(str(_get_dynamic_gain_block_dgs_path()))
    result: DgsDynamicTemplateConversionResult = parser.dynamic_model_import.convert_and_add_templates()
    assert result is parser.dynamic_model_import.get_conversion_result()
    assert result is parser.conversion_result
    parser.dynamic_model_import.apply_templates_to_devices()
    if target_domain is DynamicSimulationMode.RMS:
        templates: Sequence[RmsModelTemplate | EmtModelTemplate] = destination.rms_models
        assert len(destination.emt_models) == 0
    else:
        templates = destination.emt_models
        assert len(destination.rms_models) == 0
    assert len(templates) == 1
    assert templates[0].name == "Dynamic gain"
    assert logger.error_count() == 0


def test_dynamic_model_import_reports_invalid_domain_to_shared_logger() -> None:
    """Reject an unspecified destination without registering partial templates.

    :return: None.
    """
    logger: Logger = Logger()
    destination: MultiCircuit = MultiCircuit()
    importer: DynamicModelImport = DynamicModelImport(DgsCircuit(), destination, None, logger)
    result: DgsDynamicTemplateConversionResult = importer.convert_and_add_templates()
    assert result is importer.get_conversion_result()
    assert result.templates_by_root_dgs_id == dict()
    assert logger.error_count() == 1
    assert len(destination.rms_models) == 0 and len(destination.emt_models) == 0


def test_dgs_vsc_unconnected_inputs_create_terminal_measurements() -> None:
    """Create from/to measurements without exposing derived controller inputs.

    :return: None.
    """
    dc_bus: Bus = Bus(name="DC", is_dc=True)
    ac_bus: Bus = Bus(name="AC")
    converter: VSC = VSC(bus_from=dc_bus, bus_to=ac_bus)
    input_names: tuple[str, ...] = (
        "Vdc",
        "Vm",
        "Va",
        "u",
        "ur",
        "ui",
        "cosphi",
        "sinphi",
        "P_act",
        "Q_act",
    )
    controller_inputs: list[Var] = list(
        Var(name=input_name) for input_name in input_names
    )
    controller: Block = Block(
        name="DGS controller",
        in_vars=list(controller_inputs),
    )
    root_block: Block = Block(
        name="DGS VSC",
        children=list((controller,)),
        in_vars=list(controller_inputs),
    )

    _assign_dgs_external_input_references(
        block=root_block,
        device_tpe=DeviceType.VscDevice,
    )
    importer: DynamicModelImport = DynamicModelImport(
        dgs_circuit=DgsCircuit(), circuit=MultiCircuit(),
        target_domain=DynamicSimulationMode.RMS, logger=Logger(),
    )
    importer._add_required_dgs_rms_measurements(
        block=root_block, host_device=converter, native_specs=list(),
    )

    child_names: set[str] = set(
        child_block.name for child_block in root_block.children
    )
    assert "MEASUREMENTS_VOLTAGE_ANGLE_FROM" in child_names
    assert "MEASUREMENTS_VOLTAGE_ANGLE_TO" in child_names
    assert "MEASUREMENTS_VOLTAGE_FROM_POLAR_TO" in child_names
    assert "MEASUREMENTS_PLL_TO" in child_names
    assert "MEASUREMENTS_P_Q_TO" in child_names

    controller_refs: set[VarPowerFlowReferenceType] = set(
        input_var.ref
        for input_var in controller.in_vars
        if isinstance(input_var.ref, VarPowerFlowReferenceType)
    )
    assert VarPowerFlowReferenceType.COSPHIt in controller_refs
    assert VarPowerFlowReferenceType.SINPHIt in controller_refs
    assert VarPowerFlowReferenceType.Ut in controller_refs
    assert VarPowerFlowReferenceType.URt in controller_refs
    assert VarPowerFlowReferenceType.UIt in controller_refs

    remaining_root_refs: set[VarPowerFlowReferenceType] = set(
        input_var.ref
        for input_var in root_block.in_vars
        if isinstance(input_var.ref, VarPowerFlowReferenceType)
    )
    assert VarPowerFlowReferenceType.Ut not in remaining_root_refs
    assert VarPowerFlowReferenceType.URt not in remaining_root_refs
    assert VarPowerFlowReferenceType.UIt not in remaining_root_refs
    assert VarPowerFlowReferenceType.COSPHIt not in remaining_root_refs
    assert VarPowerFlowReferenceType.SINPHIt not in remaining_root_refs
    assert VarPowerFlowReferenceType.Vf_dc in remaining_root_refs
    assert VarPowerFlowReferenceType.Vmt in remaining_root_refs
    assert VarPowerFlowReferenceType.Vat in remaining_root_refs

    # Measurements must share the artificial physical inputs exposed by the
    # root. Those inputs are later rebound to the real bus variables when the
    # parsed template is assigned to its static device.
    root_inputs_by_reference: dict[VarPowerFlowReferenceType, Var] = dict()
    root_input: Var
    for root_input in root_block.in_vars:
        if isinstance(root_input.ref, VarPowerFlowReferenceType):
            root_inputs_by_reference[root_input.ref] = root_input
        else:
            pass
    measurement_block: Block
    measurement_input: Var
    for measurement_block in root_block.children:
        if measurement_block.name.startswith("MEASUREMENTS_"):
            for measurement_input in measurement_block.in_vars:
                assert isinstance(
                    measurement_input.ref,
                    VarPowerFlowReferenceType,
                )
                assert (
                    root_inputs_by_reference[measurement_input.ref]
                    is measurement_input
                )
        else:
            pass

    assert (
        root_inputs_by_reference[VarPowerFlowReferenceType.Vf_dc]
        is not controller_inputs[0]
    )
    assert (
        root_inputs_by_reference[VarPowerFlowReferenceType.Vmt]
        is not controller_inputs[1]
    )
    assert (
        root_inputs_by_reference[VarPowerFlowReferenceType.Vat]
        is not controller_inputs[2]
    )


@pytest.mark.parametrize("conflicting_alias", (False, True))
def test_early_pll_meter_binding_preserves_canonical_output_ownership(
        conflicting_alias: bool,
) -> None:
    """Finalize a stateful PLL without losing early consumer identity.

    :param conflicting_alias: Whether two distinct early outputs claim the
        same prepared PLL output, which must be rejected before mutation.
    :return: None; verify ownership, startup, copy and declarative persistence.
    """
    var_factory: VarFactory = VarFactory()
    angle: Var = var_factory.add_var("measured_angle")
    meter_name: str = _get_veragrid_meter_name(
        meter_kind=RmsPhysicalMeterKind.PHASE_LOCKED_LOOP,
        source_fid="42",
    )
    prepared: Block
    native_outputs: dict[str, Var]
    prepared, native_outputs = build_rms_phase_locked_loop_block(
        vf=var_factory,
        va=angle,
        proportional_gain=200.0,
        integral_gain=10000.0,
        nominal_frequency_hz=50.0,
        name=meter_name,
    )
    retained_output: Var = var_factory.add_var("controller_cosine")
    early: Block = Block(
        name=meter_name,
        algebraic_vars=list([retained_output]),
        algebraic_eqs=list([retained_output - Const(1.0)]),
        out_vars=list([retained_output]),
    )
    controller: Block = Block(in_vars=list([retained_output]))
    aliases: dict[str, Expr] = dict()
    aliases["cosphi"] = native_outputs["cosphi"]
    targets: dict[str, list[Var]] = dict()
    targets["cosphi"] = list([retained_output])
    if conflicting_alias:
        # Both spellings are supported aliases for one native cosine. Their
        # distinct early owners cannot both become that single solved output.
        conflicting_output: Var = var_factory.add_var("other_controller_cosine")
        early.algebraic_vars.append(conflicting_output)
        early.algebraic_eqs.append(conflicting_output - Const(1.0))
        early.out_vars.append(conflicting_output)
        controller.in_vars.append(conflicting_output)
        aliases["cosphi1"] = native_outputs["cosphi"]
        targets["cosphi1"] = list([conflicting_output])
    else:
        pass
    host: Block = Block(children=list([controller, early]))
    host_before: dict[str, object] = host.to_dict()
    prepared_before: dict[str, object] = prepared.to_dict()
    state_uids: tuple[int, ...] = tuple(var.uid for var in prepared.state_vars)

    connected_count: int = _connect_meter_aliases(
        host_model=host,
        targets_by_name=targets,
        alias_expressions=aliases,
        meter_name=meter_name,
        meter_kind=RmsPhysicalMeterKind.PHASE_LOCKED_LOOP,
        var_factory=var_factory,
        prepared_meter_block=prepared,
    )
    if conflicting_alias:
        assert connected_count == 0
        assert host.to_dict() == host_before
        assert prepared.to_dict() == prepared_before
    else:
        assert connected_count == 1
        assert host.children[1] is prepared
        assert prepared.uid == early.uid
        assert tuple(var.uid for var in prepared.state_vars) == state_uids
        assert any(var is retained_output for var in prepared.out_vars)
        assert retained_output in prepared.init_eqs
        assert retained_output.shared_ref is not None
        assert controller.in_vars[0] is retained_output

        # The same equation and variable ownership must survive both
        # supported lifecycle operations, without serializing runtime objects.
        restored: Block
        for restored in (host.copy(), roundtrip_block(host)):
            restored_meter: Block = restored.children[1]
            assert tuple(var.uid for var in restored_meter.state_vars) == state_uids
            assert sum(
                var.uid == retained_output.uid
                for owner in restored.get_all_blocks()
                for var in owner.algebraic_vars
            ) == 1
            assert retained_output.uid in set(var.uid for var in restored_meter.init_eqs)
            assert restored.children[0].in_vars[0].uid == retained_output.uid


def test_physical_meter_terminal_side_rejects_invalid_ordinals() -> None:
    """Reject unsupported DGS cubicle ordinals before building meter equations.

    :return: None.
    """
    from_bus: Bus = Bus(name="From bus", is_dc=True)
    to_bus: Bus = Bus(name="To bus")
    converter: VSC = VSC(bus_from=from_bus, bus_to=to_bus)
    branch: Line = Line(bus_from=from_bus, bus_to=to_bus)
    invalid_terminal_index: int

    assert _get_physical_meter_terminal_side(
        source_device=converter,
        source_terminal_index=0,
    ) is RmsTerminalSide.TO
    assert _get_physical_meter_terminal_side(
        source_device=branch,
        source_terminal_index=0,
    ) is RmsTerminalSide.FROM
    assert _get_physical_meter_terminal_side(
        source_device=branch,
        source_terminal_index=1,
    ) is RmsTerminalSide.TO
    for invalid_terminal_index in (-1, 2):
        assert _get_physical_meter_terminal_side(
            source_device=converter,
            source_terminal_index=invalid_terminal_index,
        ) is None
        assert _get_physical_meter_terminal_side(
            source_device=branch,
            source_terminal_index=invalid_terminal_index,
        ) is None
    else:
        pass


class DgsSwitchEventProblem(EmtProblemTemplate):
    """Provide the smallest runtime problem needed to exercise a DGS switch event."""

    __slots__ = tuple()


def test_dc_bus_nodal_power_equation_annotations_resolve() -> None:
    """Keep the public DC nodal helper annotations runtime-resolvable.

    :return: None.
    """
    assert (
        get_type_hints(build_dc_bus_nodal_power_equation)["return"]
        == Expr | Const
    )


def test_ac_bus_rms_power_ports_have_distinct_symbolic_names() -> None:
    """Keep active and reactive bus ports unambiguous by name and reference.

    :return: None.
    """
    bus_template: BusRmsTemplate = BusRmsTemplate(
        vf=VarFactory(),
        is_dc=False,
    )
    active_power: Var | None = bus_template.block.external_mapping.get(
        VarPowerFlowReferenceType.P,
        None,
    )
    reactive_power: Var | None = bus_template.block.external_mapping.get(
        VarPowerFlowReferenceType.Q,
        None,
    )

    assert isinstance(active_power, Var)
    assert isinstance(reactive_power, Var)
    assert active_power.name == "P"
    assert reactive_power.name == "Q"
    assert active_power.uid != reactive_power.uid
    assert active_power.ref is VarPowerFlowReferenceType.P
    assert reactive_power.ref is VarPowerFlowReferenceType.Q


def test_dc_bus_capacitive_state_detection_rejects_incomplete_topology() -> None:
    """Reject a mapped DC derivative that does not own a complete state.

    :return: None.
    """
    valid_template: BusRmsTemplate = BusRmsTemplate(
        vf=VarFactory(),
        is_dc=True,
        dc_shunt_capacitance_pu_seconds=0.1,
    )
    assert dc_bus_rms_model_has_capacitive_state(
        bus_rms_model=valid_template.block,
    )

    incomplete_template: BusRmsTemplate = BusRmsTemplate(
        vf=VarFactory(),
        is_dc=True,
    )
    incomplete_derivative: Var = Var(name="dVdc_dt")
    incomplete_template.block.external_mapping[
        VarPowerFlowReferenceType.d_Vdc
    ] = incomplete_derivative

    with pytest.raises(
            ValueError,
            match="DC bus has an incomplete capacitive-state topology",
    ):
        dc_bus_rms_model_has_capacitive_state(
            bus_rms_model=incomplete_template.block,
        )


def test_elmterm_bus_addition_rejects_empty_fid_atomically() -> None:
    """Reject an empty terminal FID before adding any source bus.

    :return: None.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    valid_terminal: ElmTerm = ElmTerm()
    valid_terminal.ID = "valid-terminal"
    invalid_terminal: ElmTerm = ElmTerm()
    invalid_terminal.ID = ""
    dgs_circuit.elmterms.append(valid_terminal)
    dgs_circuit.elmterms.append(invalid_terminal)
    destination: MultiCircuit = MultiCircuit()

    with pytest.raises(ValueError, match="ElmTerm FID must not be empty"):
        add_dgs_terminal_buses(
            dgs_grid=dgs_circuit,
            grid=destination,
            pos_by_objid=dict(),
        )

    assert len(destination.buses) == 0


@pytest.mark.parametrize(
    ('line', 'header_map', 'expected_aohl', 'expected_aohl_declared',
     'expected_cohl', 'expected_cohl_declared'),
    (
        ('type-1;1', {'ID': 0, 'systp': 1}, 'cab', False, 0, False),
        ('type-1;cab', {'ID': 0, 'aohl_': 1}, 'cab', True, 0, False),
        ('type-1;0', {'ID': 0, 'cohl_': 1}, 'cab', False, 0, True),
        ('type-1;1', {'ID': 0, 'cohl_': 1}, 'cab', False, 1, True),
        (
            'type-1;cab;1',
            {'ID': 0, 'aohl_': 1, 'cohl_': 2},
            'cab',
            True,
            1,
            True,
        ),
        ('type-1;;', {'ID': 0, 'aohl_': 1, 'cohl_': 2}, None, False, None, False),
        ('type-1;wire;invalid', {'ID': 0, 'aohl_': 1, 'cohl_': 2}, 'wire', True, None, True),
    ),
)
def test_typlne_parser_preserves_installation_evidence(
        line: str,
        header_map: dict[str, int],
        expected_aohl: str | None,
        expected_aohl_declared: bool,
        expected_cohl: int | None,
        expected_cohl_declared: bool,
) -> None:
    """Distinguish absent, empty, invalid, cable, overhead, and conflict rows.

    :param line: Minimal DGS TypLne row.
    :param header_map: Column positions declared by the DGS header.
    :param expected_aohl: Parsed legacy installation value.
    :param expected_aohl_declared: Whether the row declares the legacy field.
    :param expected_cohl: Parsed current installation value.
    :param expected_cohl_declared: Whether the row declares the current field.
    :return: None.
    """
    source_type: TypLne = TypLne.parse_line(
        line=line,
        header_map=header_map,
    )

    assert source_type.aohl_ == expected_aohl
    assert source_type.aohl_declared is expected_aohl_declared
    assert source_type.cohl_ == expected_cohl
    assert source_type.cohl_declared is expected_cohl_declared


def test_elmterm_bus_addition_rejects_duplicate_fid_atomically() -> None:
    """Reject repeated terminal identity before distinct nodes can merge.

    :return: None.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    first_terminal: ElmTerm = ElmTerm()
    first_terminal.ID = "duplicate-terminal"
    second_terminal: ElmTerm = ElmTerm()
    second_terminal.ID = "folder\\duplicate-terminal"
    dgs_circuit.elmterms.append(first_terminal)
    dgs_circuit.elmterms.append(second_terminal)
    destination: MultiCircuit = MultiCircuit()

    with pytest.raises(ValueError, match="Duplicate ElmTerm FID: duplicate-terminal"):
        add_dgs_terminal_buses(
            dgs_grid=dgs_circuit,
            grid=destination,
            pos_by_objid=dict(),
        )

    assert len(destination.buses) == 0


def _get_dynamic_gain_block_dgs_path() -> Path:
    """Return the versioned DGS fixture containing supported and unsupported blocks."""

    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "grids"
        / "DGS"
        / "dynamic_gain_block.dgs"
    )


def _get_native_graphical_operator_dgs_path() -> Path:
    """
    Return the versioned DGS fixture containing native graphical operators.

    :return: Path to the portable ASCII DGS fixture.
    """
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "grids"
        / "DGS"
        / "native_graphical_operators.dgs"
    )


def _get_graphical_parent_signal_binding_dgs_path() -> Path:
    """Return the portable DGS fixture for parent-to-child signal binding.

    :return: Path to the versioned graphical parent contract fixture.
    """
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "grids"
        / "DGS"
        / "graphical_parent_signal_binding.dgs"
    )


def _get_non_executable_slots_dgs_path() -> Path:
    """Return the portable DGS fixture for non-executable source slots.

    :return: Path to physical and vendor slots without exported pElm targets.
    """
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "grids"
        / "DGS"
        / "non_executable_slots.dgs"
    )


# DGS contract: locate complete HVDC fixtures under generic public names.
def _get_complete_hvdc_vsc_dgs_path(file_name: str) -> Path:
    """Return one tracked complete static-and-dynamic HVDC VSC export.

    :param file_name: Exact fixture file name.
    :return: Absolute path to the requested generic HVDC VSC DGS fixture.
    """
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "grids"
        / "DGS"
        / file_name
    )


def _parse_native_graphical_operator_fixture() -> DgsCircuit:
    """
    Parse the portable graph containing native arithmetic and switching nodes.

    :return: Parsed circuit containing the native graphical records and cables.
    """
    dgs_path: Path = _get_native_graphical_operator_dgs_path()
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(path=str(dgs_path))
    return circuit


# Dynamic contract: build a minimal fixture for per-instance BlkRef parameters.
def _build_nested_graphical_parent_fixture() -> tuple[
    DgsCircuit,
    ElmComp,
    ElmComp,
    BlkRef,
]:
    """Build one exact nested ElmComp relation reached by a graphical BlkRef.

    :return: Circuit, selected root, nested component and reached BlkRef.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    circuit.blkslots[0].filtmod = "ElmComp"

    nested_component: ElmComp = ElmComp()
    nested_component.ID = "NESTED_COMPONENT"
    nested_component.loc_name = "Nested graphical component"
    nested_component.typ_id = "MACRO"
    circuit.elmcomps.append(nested_component)
    root_element.pelm[0] = nested_component.ID

    child_definition: BlkDef = BlkDef()
    child_definition.ID = "NESTED_CHILD_DEFINITION"
    child_definition.loc_name = "Nested child definition"
    child_definition.inputs.append("external_x")
    circuit.blkdefs.append(child_definition)

    child_reference: BlkRef = BlkRef()
    child_reference.ID = "NESTED_CHILD_REFERENCE"
    child_reference.typ_id = child_definition.ID
    circuit.blkrefs.append(child_reference)

    child_signal: BlkSig = BlkSig()
    child_signal.ID = "ROOT_TO_NESTED_CHILD"
    child_signal.loc_name = "external_x"
    child_signal.inodfrom = 0
    child_signal.iconfrom = 1
    child_signal.inodto = 0
    child_signal.iconto = 1
    child_signal.pnodfrom = "MACRO"
    child_signal.pnodto = child_reference.ID
    circuit.blksigs.append(child_signal)

    return circuit, root_element, nested_component, child_reference


@pytest.mark.parametrize(
    (
        "file_name",
        "expected_sha256",
        "expected_counts",
    ),
    (
        (
            "hvdc_vsc_v1_complete_static_dynamic.dgs",
            "32D22863FD68D8B23BB2CAD0B7300F5B281ABD142D4F633AA87307014897D581",
            (0, 2, 2, 2, 12, 9, 10),
        ),
        (
            "hvdc_vsc_v2_complete_static_dynamic.dgs",
            "10171A7DD16F39ABB027EC8460AA10224072D76481436DBC4375167448B74C54",
            (0, 2, 2, 2, 11, 11, 10),
        ),
        (
            "hvdc_vsc_v3_complete_static_dynamic.dgs",
            "E34DA6F5DCD229B90379A17940D072E02BAF9382BD8405E96FF7175330294C57",
            (2, 0, 2, 3, 33, 19, 17),
        ),
    ),
)
# DGS contract: verify that the static and dynamic domains survive together.
def test_complete_hvdc_vsc_exports_preserve_static_and_dynamic_sections(
        file_name: str,
        expected_sha256: str,
        expected_counts: tuple[int, int, int, int, int, int, int],
) -> None:
    """Parse immutable generic HVDC exports without losing either model domain.

    :param file_name: Exact tracked fixture name.
    :param expected_sha256: Provenance checksum of the LF-normalized source export.
    :param expected_counts: Expected converter, PLL, composite, DSL, block and bus counts.
    :return: None.
    """
    dgs_path: Path = _get_complete_hvdc_vsc_dgs_path(file_name=file_name)
    source_bytes: bytes = dgs_path.read_bytes()
    # Git may check out the same text fixture with CRLF on Windows. Preserve
    # the content provenance check independently of that checkout convention.
    source_sha256: str = hashlib.sha256(source_bytes.replace(b'\r\n', b'\n')).hexdigest().upper()
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(path=str(dgs_path))
    parsed_counts: tuple[int, int, int, int, int, int, int] = (
        len(circuit.elmvscs),
        len(circuit.elmvscmonos),
        len(circuit.elmphis),
        len(circuit.elmcomps),
        len(circuit.elmdsls),
        len(circuit.blkdefs),
        len(circuit.elmterms),
    )

    assert source_sha256 == expected_sha256
    assert parsed_counts == expected_counts


@pytest.mark.parametrize(
    "file_name",
    (
        "hvdc_vsc_v1_complete_static_dynamic.dgs",
        "hvdc_vsc_v2_complete_static_dynamic.dgs",
    ),
)
def test_two_level_vsc_exports_retain_native_dc_link_capacitance(
        file_name: str,
) -> None:
    """Retain the native two-level topology and DC-link capacitance.

    :param file_name: Exact tracked V1 or V2 fixture name.
    :return: None.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(
        path=str(_get_complete_hvdc_vsc_dgs_path(file_name=file_name))
    )

    assert len(dgs_circuit.elmvscmonos) == 2
    converter: ElmVscmono
    for converter in dgs_circuit.elmvscmonos:
        assert converter.vsctype == PowerFactoryVscType.TwoLevel
        assert converter.Cdc == 76.80000305175781
    else:
        pass


@pytest.mark.parametrize(
    ("file_name", "equipment_class"),
    (
        ("hvdc_vsc_v1_complete_static_dynamic.dgs", "ElmVscmono"),
        ("hvdc_vsc_v2_complete_static_dynamic.dgs", "ElmVscmono"),
        ("hvdc_vsc_v3_complete_static_dynamic.dgs", "ElmVsc"),
    ),
)
# Dynamic contract: verify the exact physical BlkSlot linking each VSC by FID.
def test_complete_hvdc_vsc_exports_declare_directional_equipment_slots(
        file_name: str,
        equipment_class: str,
) -> None:
    """Retain one directional physical slot per converter composite.

    :param file_name: Exact tracked fixture name.
    :param equipment_class: Native converter class expected in each root.
    :return: None.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(
        path=str(_get_complete_hvdc_vsc_dgs_path(file_name=file_name))
    )
    physical_entries: list[ElmCompInstanceEntry] = list()
    root_element: ElmComp
    for root_element in dgs_circuit.elmcomps:
        direct_entry: ElmCompInstanceEntry
        for direct_entry in extract_elmcomp_direct_instances(
                circuit=dgs_circuit,
                root_element=root_element,
        ):
            if direct_entry.element_kind == equipment_class:
                physical_entries.append(direct_entry)
            else:
                pass

    assert len(physical_entries) == 2
    physical_entry: ElmCompInstanceEntry
    for physical_entry in physical_entries:
        assert physical_entry.slot_reference_is_resolved
        assert physical_entry.element_reference_is_resolved
        if equipment_class == "ElmVscmono":
            assert {"id", "iq", "uDC"}.issubset(physical_entry.slot_outputs)
            assert {"Pmd", "Pmq"}.issubset(physical_entry.slot_inputs)
            assert {"cosref", "sinref"}.issubset(physical_entry.slot_inputs)
        else:
            assert equipment_class == "ElmVsc"
            assert {"Pmr", "Pmi", "mdc"}.issubset(
                physical_entry.slot_inputs
            )
            assert (
                {"iDC", "yUcell"}.issubset(physical_entry.slot_outputs)
                or {"idc", "Ucap"}.issubset(physical_entry.slot_outputs)
            )


def test_v2_direct_root_connects_ffs_by_slot_fid_and_connector_ordinal() -> None:
    """Bind the V2 FFS output despite its private producer port name.

    :return: None.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(
        path=str(_get_complete_hvdc_vsc_dgs_path(
            file_name="hvdc_vsc_v2_complete_static_dynamic.dgs",
        ))
    )
    parsed_blocks: dict[str, ParsedDgsBlockDefinition] = (
        parse_dgs_block_definitions_from_circuit(circuit=dgs_circuit)
    )
    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=dgs_circuit,
        parsed_blocks=parsed_blocks,
        root_name="SlavePWM_Model",
    )
    direct_result: DgsDirectRootBuildResult = build_direct_root_elmcomp_block(
        circuit=dgs_circuit,
        result=root_result,
        graphical_indexes=build_dgs_graphical_indexes(circuit=dgs_circuit),
    )
    ffs_entry: ElmCompInstanceEntry | None = None
    active_controller_entry: ElmCompInstanceEntry | None = None
    direct_entry: ElmCompInstanceEntry
    for direct_entry in direct_result.direct_entries:
        if direct_entry.slot_name == "FFS":
            ffs_entry = direct_entry
        elif direct_entry.slot_name == "Outer_ctrl_P_wffs":
            active_controller_entry = direct_entry
        else:
            pass

    assert ffs_entry is not None
    assert active_controller_entry is not None
    assert ffs_entry.slot_id is not None
    assert active_controller_entry.slot_id is not None
    assert active_controller_entry.get_slot_signal_components(
        direction=DgsSlotSignalDirection.Input,
    ) == ["id_limit", "P_act", "uDC", "id", "dP_FFS"]

    ffs_block: Block = direct_result.child_block_by_slot_id[ffs_entry.slot_id]
    active_controller_block: Block = direct_result.child_block_by_slot_id[
        active_controller_entry.slot_id
    ]
    assert len(ffs_block.out_vars) == 1
    ffs_output: Var = ffs_block.out_vars[0]
    connected_inputs: list[Var] = list(
        controller_input
        for controller_input in active_controller_block.in_vars
        if controller_input.uid == ffs_output.uid
    )
    assert connected_inputs == [ffs_output]
    assert not any(
        controller_input.name == "dP_FFS"
        for controller_input in active_controller_block.in_vars
    )
    assert any(
        controller_equation.contains_var(ffs_output)
        for controller_equation in active_controller_block.algebraic_eqs
    )
    assert not any(
        root_variable.name == "dP_FFS"
        for root_variable in direct_result.root_block.algebraic_vars
    )


def test_v3_direct_root_connects_outputs_by_declared_slot_signal() -> None:
    """Bind each cable to the output its slot declares, whatever the block order.

    The V3 protection block orders its outputs differently from its slot, so
    the slot ordinal must select the declared signal by name, not by position.

    :return: None.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(
        path=str(_get_complete_hvdc_vsc_dgs_path(
            file_name="hvdc_vsc_v3_complete_static_dynamic.dgs",
        ))
    )
    parsed_blocks: dict[str, ParsedDgsBlockDefinition] = (
        parse_dgs_block_definitions_from_circuit(circuit=dgs_circuit)
    )
    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=dgs_circuit,
        parsed_blocks=parsed_blocks,
        root_name="HVDC Control A",
    )
    direct_result: DgsDirectRootBuildResult = build_direct_root_elmcomp_block(
        circuit=dgs_circuit,
        result=root_result,
        graphical_indexes=build_dgs_graphical_indexes(circuit=dgs_circuit),
    )
    block_by_slot_name: dict[str, Block] = dict()
    entry_by_slot_name: dict[str, ElmCompInstanceEntry] = dict()
    direct_entry: ElmCompInstanceEntry
    for direct_entry in direct_result.direct_entries:
        if direct_entry.slot_id is not None and direct_entry.slot_id in direct_result.child_block_by_slot_id:
            block_by_slot_name[str(direct_entry.slot_name)] = (
                direct_result.child_block_by_slot_id[direct_entry.slot_id]
            )
            entry_by_slot_name[str(direct_entry.slot_name)] = direct_entry
        else:
            pass

    protection_block: Block = block_by_slot_name["Protection"]
    limiter_block: Block = block_by_slot_name["Current Limiter"]
    assert [var.name for var in protection_block.out_vars] != [
        "trip", "DC_switch_open", "trip_dc", "STATCOM_on", "block", "soft",
    ]
    signal_name: str
    for signal_name in ("block", "soft"):
        protection_outputs: list[Var] = list(
            var for var in protection_block.out_vars if var.name == signal_name
        )
        assert len(protection_outputs) == 1
        assert any(
            limiter_input.uid == protection_outputs[0].uid
            for limiter_input in limiter_block.in_vars
        )

    # The vector connector keeps its declared components in slot order.
    vector_indices: list[int] = _resolve_direct_slot_runtime_output_indices(
        entry=entry_by_slot_name["Protection"],
        child_block=protection_block,
        graphical_output_index=1,
    )
    assert [protection_block.out_vars[index].name for index in vector_indices] == [
        "DC_switch_open", "trip_dc", "STATCOM_on",
    ]


def _resolve_controller_output_names(
        slot_outputs: str,
        block_outputs: list[str],
) -> list[list[str]]:
    """Resolve every output ordinal of one synthetic controller slot.

    :param slot_outputs: Comma-separated declared slot outputs.
    :param block_outputs: Runtime output names of the block, in block order.
    :return: Resolved runtime output names per ordinal.
    """
    entry: ElmCompInstanceEntry = ElmCompInstanceEntry(
        slot_id="slot",
        slot_name="Controller",
        element_id="controller_fid",
        element_name="Controller",
        element_kind="ElmDsl",
        element_outserv=0,
        type_id=None,
        type_name=None,
        slot_outputs=list([slot_outputs]),
        slot_reference_is_resolved=True,
        element_reference_is_resolved=True,
    )
    block: Block = Block(name="Controller", out_vars=list(Var(name=name) for name in block_outputs))
    resolved: list[list[str]] = list()
    ordinal: int
    for ordinal in range(len(slot_outputs.split(","))):
        resolved.append(list(
            block.out_vars[index].name
            for index in _resolve_direct_slot_runtime_output_indices(
                entry=entry, child_block=block, graphical_output_index=ordinal,
            )
        ))
    return resolved


def test_direct_output_ordinals_leave_unmatched_signals_unwired() -> None:
    """Resolve by declared name and never guess an unmatched ordinal by position.

    A slot that lists a graphical-only output must still wire the REGC commands
    by name, and an output without a named match must not reuse another one.
    Blocks whose names all differ from the slot keep the positional order.

    :return: None.
    """
    assert _resolve_controller_output_names(
        slot_outputs="ur_ref,ui_ref,idref,iqref,ghost",
        block_outputs=["iqref", "ur_ref", "ui_ref", "idref"],
    ) == [["ur_ref"], ["ui_ref"], ["idref"], ["iqref"], []]
    assert _resolve_controller_output_names(
        slot_outputs="a,b",
        block_outputs=["b", "x"],
    ) == [[], ["b"]]
    assert _resolve_controller_output_names(
        slot_outputs="dP_FFS",
        block_outputs=["y"],
    ) == [["y"]]


def test_v1_direct_root_internalizes_slot_omitted_setpoints() -> None:
    """Keep initialized controller setpoints behind the concrete slot interface.

    :return: None.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(
        path=str(_get_complete_hvdc_vsc_dgs_path(
            file_name="hvdc_vsc_v1_complete_static_dynamic.dgs",
        ))
    )
    parsed_blocks: dict[str, ParsedDgsBlockDefinition] = (
        parse_dgs_block_definitions_from_circuit(circuit=dgs_circuit)
    )
    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=dgs_circuit,
        parsed_blocks=parsed_blocks,
        root_name="MasterPWM_Model",
    )
    direct_result: DgsDirectRootBuildResult = build_direct_root_elmcomp_block(
        circuit=dgs_circuit,
        result=root_result,
        graphical_indexes=build_dgs_graphical_indexes(circuit=dgs_circuit),
    )

    active_controller: Block | None = None
    reactive_controller: Block | None = None
    child_block: Block
    for child_block in direct_result.root_block.children:
        if child_block.name == "Outer_Ctrl_P":
            active_controller = child_block
        else:
            if child_block.name == "Outer_Ctrl_Q":
                reactive_controller = child_block
            else:
                pass
    else:
        pass

    assert active_controller is not None
    assert reactive_controller is not None
    active_input_names: set[str] = set(
        input_var.name for input_var in active_controller.in_vars
    )
    reactive_input_names: set[str] = set(
        input_var.name for input_var in reactive_controller.in_vars
    )
    assert "Pdc_ref" not in active_input_names
    assert "uDC_ref" not in active_input_names
    assert "Q_ref" not in reactive_input_names
    assert "Vac_ref" not in reactive_input_names

    active_setpoints: dict[str, Expr | Const] = dict(
        (setpoint_var.name, initial_expression)
        for setpoint_var, initial_expression in active_controller.event_dict.items()
        if setpoint_var.name in {"Pdc_ref", "uDC_ref"}
    )
    reactive_setpoints: dict[str, Expr | Const] = dict(
        (setpoint_var.name, initial_expression)
        for setpoint_var, initial_expression in reactive_controller.event_dict.items()
        if setpoint_var.name in {"Q_ref", "Vac_ref"}
    )
    assert set(active_setpoints) == {"Pdc_ref", "uDC_ref"}
    assert set(reactive_setpoints) == {"Q_ref", "Vac_ref"}
    assert str(active_setpoints["Pdc_ref"]) == "P_act"
    assert str(active_setpoints["uDC_ref"]) == "uDC"
    assert str(reactive_setpoints["Q_ref"]) == "Q_act"
    assert str(reactive_setpoints["Vac_ref"]) == "u"


@pytest.mark.parametrize(
    ("file_name", "second_active_power_setpoint", "first_dc_voltage_setpoint"),
    (
        ("hvdc_vsc_v1_complete_static_dynamic.dgs", -1000.0, 1.0),
        ("hvdc_vsc_v2_complete_static_dynamic.dgs", -1000.0, 1.0),
        ("hvdc_vsc_v3_complete_static_dynamic.dgs", 1000.0, 2.0),
    ),
)
# Alex review required: converter controls use configured setpoints, never solved m:* columns.
def test_hvdc_vsc_converter_controls_use_configuration_not_solved_outputs(
        file_name: str,
        second_active_power_setpoint: float,
        first_dc_voltage_setpoint: float,
) -> None:
    """Build generic HVDC converters from configured targets, never ``m:*`` results.

    :param file_name: Exact tracked fixture name.
    :param second_active_power_setpoint: Configured active-power target of converter two.
    :param first_dc_voltage_setpoint: Configured DC voltage converted to the bus base.
    :return: None.
    """
    dgs_path: Path = _get_complete_hvdc_vsc_dgs_path(file_name=file_name)
    circuit: MultiCircuit = dgs_to_circuit(path=str(dgs_path))
    first_converter: VSC = circuit.vsc_devices[0]
    second_converter: VSC = circuit.vsc_devices[1]

    assert len(circuit.vsc_devices) == 2
    assert first_converter.control1 is ConverterControlType.Vm_dc
    # V3 regulates 1050 kV pole-to-pole on 525 kV pole bases; V1/V2 are monopolar.
    assert first_converter.control1_val == pytest.approx(first_dc_voltage_setpoint)
    assert first_converter.control2 is ConverterControlType.Qac
    assert first_converter.control2_val == pytest.approx(0.0)
    assert second_converter.control1 is ConverterControlType.Pac
    assert second_converter.control1_val == pytest.approx(
        second_active_power_setpoint
    )
    assert second_converter.control2 is ConverterControlType.Qac
    assert second_converter.control2_val == pytest.approx(0.0)


def test_v1_external_sources_retain_fids_and_compile_one_reference_per_ac_region() -> None:
    """Keep source semantics and compile one angle reference per AC region.

    :return: None.
    """
    dgs_path: Path = _get_complete_hvdc_vsc_dgs_path(
        file_name="hvdc_vsc_v1_complete_static_dynamic.dgs",
    )
    circuit: MultiCircuit = dgs_to_circuit(path=str(dgs_path))
    expected_source_ids: set[str] = {"128", "129"}
    imported_source_ids: set[str] = set()
    generator: Generator

    # Resolve sources by immutable DGS FID; names remain presentation data.
    for generator in circuit.generators:
        if str(generator.idtag) in expected_source_ids:
            imported_source_ids.add(str(generator.idtag))
            assert generator.bus is not None
            assert not generator.bus.is_slack
            assert float(generator.R1) > 0.0
            assert float(generator.X1) > 0.0
        else:
            pass

    assert imported_source_ids == expected_source_ids

    # Preserve the DGS PV declaration in MultiCircuit. Each disconnected AC
    # phase region promotes its own numerical reference without rewriting imported
    # source data or treating the VSC/DC corridor as an AC phase connection.
    numerical_circuit: NumericalCircuit = compile_numerical_circuit_at(circuit)
    simulation_indices: SimulationIndices = (
        numerical_circuit.get_simulation_indices()
    )
    source_bus_indices: set[int] = set()
    generator_index: int
    for generator_index in range(len(numerical_circuit.generator_data.idtag)):
        generator_idtag: str = str(
            numerical_circuit.generator_data.idtag[generator_index]
        )
        if generator_idtag in expected_source_ids:
            source_bus_indices.add(int(
                numerical_circuit.generator_data.bus_idx[generator_index]
            ))
        else:
            pass

    reference_indices: set[int] = set(
        int(reference_index) for reference_index in simulation_indices.vd
    )
    assert reference_indices == source_bus_indices
    assert len(reference_indices) == 2
    reference_index: int
    for reference_index in reference_indices:
        assert not bool(numerical_circuit.bus_data.is_p_controlled[reference_index])
        assert not bool(numerical_circuit.bus_data.is_q_controlled[reference_index])
        assert bool(numerical_circuit.bus_data.is_vm_controlled[reference_index])
        assert bool(numerical_circuit.bus_data.is_va_controlled[reference_index])


def test_v1_short_lines_keep_declared_series_precision() -> None:
    """Preserve sub-micro-pu series impedance from declarative DGS data.

    :return: None.
    """
    dgs_path: Path = _get_complete_hvdc_vsc_dgs_path(
        file_name="hvdc_vsc_v1_complete_static_dynamic.dgs",
    )
    circuit: MultiCircuit = dgs_to_circuit(path=str(dgs_path))
    master_short_line: Line | None = None
    slave_short_line: Line | None = None
    imported_line: Line

    # Resolve the immutable source FIDs without relying on display names.
    for imported_line in circuit.lines:
        if imported_line.idtag == "104":
            slave_short_line = imported_line
        elif imported_line.idtag == "105":
            master_short_line = imported_line
        else:
            pass

    assert slave_short_line is not None
    assert master_short_line is not None

    # The source type declares R/X in ohm per km and each link is 0.01 km.
    # Convert those values on the exact terminal voltage base retained by DGS.
    slave_impedance_base_ohm: float = 415.0 * 415.0 / circuit.Sbase
    master_impedance_base_ohm: float = 400.0 * 400.0 / circuit.Sbase
    expected_slave_r_pu: float = 0.0178 * 0.01 / slave_impedance_base_ohm
    expected_slave_x_pu: float = 0.278 * 0.01 / slave_impedance_base_ohm
    expected_master_r_pu: float = 0.0178 * 0.01 / master_impedance_base_ohm
    expected_master_x_pu: float = 0.278 * 0.01 / master_impedance_base_ohm

    assert slave_short_line.R == pytest.approx(expected_slave_r_pu)
    assert slave_short_line.X == pytest.approx(expected_slave_x_pu)
    assert master_short_line.R == pytest.approx(expected_master_r_pu)
    assert master_short_line.X == pytest.approx(expected_master_x_pu)


@pytest.mark.parametrize(
    ("file_name", "equipment_class"),
    (
        ("hvdc_vsc_v1_complete_static_dynamic.dgs", "ElmVscmono"),
        ("hvdc_vsc_v2_complete_static_dynamic.dgs", "ElmVscmono"),
        ("hvdc_vsc_v3_complete_static_dynamic.dgs", "ElmVsc"),
    ),
)
# Dynamic contract: V1/V2/V3 follow Block to template to circuit to VSC by FID.
def test_complete_hvdc_vsc_exports_apply_direct_dynamic_templates_by_fid(
        file_name: str,
        equipment_class: str,
) -> None:
    """Register every root and assign each converter template by exact FID.

    :param file_name: Exact tracked fixture name.
    :param equipment_class: Native converter class expected in each root.
    :return: None.
    """
    dgs_path: Path = _get_complete_hvdc_vsc_dgs_path(file_name=file_name)
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(path=str(dgs_path))
    destination: MultiCircuit = dgs_to_circuit(path=str(dgs_path))
    logger: Logger = Logger()
    conversion_result: DgsDynamicTemplateConversionResult = (
        convert_and_add_dgs_dynamic_templates_to_circuit(
            dgs_circuit=dgs_circuit,
            circuit=destination,
            target_domain=DynamicSimulationMode.RMS,
            logger=logger,
        )
    )
    templates_by_root_id: dict[
        str,
        RmsModelTemplate | EmtModelTemplate,
    ] = conversion_result.templates_by_root_dgs_id
    apply_dgs_dynamic_templates_to_devices(
        dgs_circuit=dgs_circuit,
        circuit=destination,
        templates_by_root_dgs_id=templates_by_root_id,
        logger=logger,
    )

    expected_root_ids: set[str] = set()
    root_element: ElmComp
    for root_element in dgs_circuit.elmcomps:
        expected_root_ids.add(root_element.ID)
    import_diagnostics: list[tuple[str, str]] = list()
    log_entry: LogEntry
    for log_entry in logger.entries:
        import_diagnostics.append((log_entry.msg, str(log_entry.value)))
    assert set(templates_by_root_id.keys()) == expected_root_ids, import_diagnostics

    assigned_converter_count: int = 0
    for root_element in dgs_circuit.elmcomps:
        root_template: RmsModelTemplate | EmtModelTemplate = (
            templates_by_root_id[root_element.ID]
        )
        assert any(
            registered_template is root_template
            for registered_template in destination.rms_models
        )
        direct_entry: ElmCompInstanceEntry
        for direct_entry in extract_elmcomp_direct_instances(
                circuit=dgs_circuit,
                root_element=root_element,
        ):
            if direct_entry.element_kind == equipment_class:
                assert direct_entry.element_id is not None
                matching_hosts: list[VSC] = [
                    host
                    for host in destination.vsc_devices
                    if host.idtag == direct_entry.element_id
                ]
                assert len(matching_hosts) == 1
                assert matching_hosts[0].rms_template is root_template
                assert "rms_terminal_power_contributions" not in type(
                    root_template.block.dynamic_model_contract
                ).__slots__
                assert (
                    VarPowerFlowReferenceType.Pf
                    in root_template.block.external_mapping
                )
                assert (
                    VarPowerFlowReferenceType.Pt
                    in root_template.block.external_mapping
                )
                assert (
                    VarPowerFlowReferenceType.Qt
                    in root_template.block.external_mapping
                )
                assert (
                    root_template.block.external_mapping[
                        VarPowerFlowReferenceType.Pt
                    ].ref
                    is VarPowerFlowReferenceType.Pt
                )
                host: VSC = matching_hosts[0]
                active_balance = np.zeros(2, dtype=object)
                reactive_balance = np.zeros(2, dtype=object)
                active_used = np.zeros(2, dtype=bool)
                reactive_used = np.zeros(2, dtype=bool)
                assert assemble_rms_mapped_power_references(
                    model=root_template.block,
                    bus_from_index=0,
                    bus_to_index=1,
                    bus_from_is_dc=host.bus_from.is_dc,
                    bus_to_is_dc=host.bus_to.is_dc,
                    active_power_balance=active_balance,
                    active_power_balance_used=active_used,
                    reactive_power_balance=reactive_balance,
                    reactive_power_balance_used=reactive_used,
                )
                assert active_used.tolist() == [True, True]
                assert reactive_used.tolist() == [False, True]
                assert root_template.block.E(
                    VarPowerFlowReferenceType.Pf
                ) in get_expression_vars(active_balance[0])
                assert root_template.block.E(
                    VarPowerFlowReferenceType.Pt
                ) in get_expression_vars(active_balance[1])
                assert root_template.block.E(
                    VarPowerFlowReferenceType.Qt
                ) in get_expression_vars(reactive_balance[1])
                assigned_converter_count += 1
            else:
                pass

    assert assigned_converter_count == 2
    assert logger.warning_count() == 0
    assert logger.error_count() == 0


@pytest.mark.skip(reason="Incorrect")
def test_v3_dynamic_route_binds_both_logical_chopper_actuators() -> None:
    """Bind each V3 chopper gate and resistance through the public DGS route.

    :return: None.
    """
    dgs_path: Path = _get_complete_hvdc_vsc_dgs_path(
        file_name="hvdc_vsc_v3_complete_static_dynamic.dgs",
    )
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(path=str(dgs_path))
    logger: Logger = Logger()
    circuit: MultiCircuit = dgs_to_circuit(
        path=str(dgs_path),
        use_dynamic_information=True,
        dynamic_simulation_mode=DynamicSimulationMode.RMS,
        logger_=logger,
    )
    actuator_source_ids: set[str] = set()
    source_root: ElmComp
    for source_root in dgs_circuit.elmcomps:
        direct_entry: ElmCompInstanceEntry
        for direct_entry in extract_elmcomp_direct_instances(
                circuit=dgs_circuit,
                root_element=source_root,
        ):
            if (
                    direct_entry.element_kind == "ElmSind"
                    and direct_entry.element_id is not None
            ):
                actuator_source_ids.add(direct_entry.element_id)
            else:
                pass
    assert actuator_source_ids == set(("254", "255"))
    enriched_resistance_count: int = 0
    passive_source: ElmSind
    for passive_source in dgs_circuit.elmsinds:
        if passive_source.ID in actuator_source_ids:
            assert passive_source.initial_resistance_column_declared
            assert passive_source.Rin == 99999.0
            enriched_resistance_count += 1
        else:
            pass
    assert enriched_resistance_count == 2
    actuator_branches: list[Line | SeriesReactance] = list()
    candidate_branch: object
    for candidate_branch in circuit.get_branches_iter(
            add_vsc=False,
            add_hvdc=False,
            add_switch=False,
    ):
        if (
                isinstance(candidate_branch, (Line, SeriesReactance))
                and candidate_branch.idtag in actuator_source_ids
        ):
            actuator_branches.append(candidate_branch)
        else:
            pass

    assert len(actuator_branches) == 2

    projection_source_uids: set[int] = set()
    actuator_branch: Line | SeriesReactance
    for actuator_branch in actuator_branches:
        contract: DynamicModelContract = (
            actuator_branch.rms_model.dynamic_model_contract
        )
        assert actuator_branch.bus_from is not actuator_branch.bus_to
        projection_entries: list[SampledValueLogic] = list(
            entry
            for block in actuator_branch.rms_model.get_all_blocks()
            for entry in block.procedural_logic
            if (
                    isinstance(entry, SampledValueLogic)
                    and entry.name.startswith("project_")
            )
        )
        assert len(projection_entries) == 2, str(logger)
        assert not actuator_branch.active, str(logger)
        projection_entry: SampledValueLogic
        for projection_entry in projection_entries:
            assert projection_entry.output_var_uid is not None
            source_var: Var
            for source_var in projection_entry.source_expr.get_vars():
                projection_source_uids.add(source_var.uid)

    # Both physical poles consume the same gate and resistance variables from
    # one controller instance rather than cloning a controller per branch.
    assert len(projection_source_uids) == 2

    assert logger.error_count() == 0


@pytest.mark.skip(reason="Incorrect")
def test_v3_dynamic_route_keeps_native_meters_as_connected_editor_blocks() -> None:
    """Keep every active V3 meter as one visible connected RMS child block.

    :return: None.
    """
    dgs_path: Path = _get_complete_hvdc_vsc_dgs_path(
        file_name="hvdc_vsc_v3_complete_static_dynamic.dgs",
    )
    logger: Logger = Logger()
    circuit: MultiCircuit = dgs_to_circuit(
        path=str(dgs_path),
        use_dynamic_information=True,
        dynamic_simulation_mode=DynamicSimulationMode.RMS,
        logger_=logger,
    )
    expected_meter_names: set[str] = set((
        "Current meter 423",
        "Current meter 424",
        "Current meter 425",
        "Current meter 426",
        "Current meter 428",
        "Current meter 429",
        "Voltage meter 455",
        "Voltage meter 456",
        "Voltage meter 457",
        "Voltage meter 458",
        "Voltage meter 460",
        "Voltage meter 461",
        "Voltage meter 462",
        "Voltage meter 463",
        "Voltage meter 465",
        "Voltage meter 466",
        "Phase meter 472",
        "Phase meter 473",
    ))
    meter_block_by_name: dict[str, Block] = dict()
    owner_model_by_meter_name: dict[str, Block] = dict()
    candidate_device: object

    # Inspect only final device-owned RMS graphs. Registered templates are
    # catalogue definitions and must not be counted as duplicate GUI nodes.
    for candidate_device in circuit.get_injection_devices():
        if isinstance(candidate_device, DynamicDevice):
            candidate_block: Block
            for candidate_block in candidate_device.rms_model.get_all_blocks():
                if candidate_block.name in expected_meter_names:
                    meter_block_by_name[candidate_block.name] = candidate_block
                    owner_model_by_meter_name[candidate_block.name] = candidate_device.rms_model
                else:
                    pass
        else:
            pass
    for candidate_device in circuit.get_branches(
            add_vsc=True,
            add_hvdc=True,
            add_switch=True,
    ):
        if isinstance(candidate_device, DynamicDevice):
            for candidate_block in candidate_device.rms_model.get_all_blocks():
                if candidate_block.name in expected_meter_names:
                    meter_block_by_name[candidate_block.name] = candidate_block
                    owner_model_by_meter_name[candidate_block.name] = candidate_device.rms_model
                else:
                    pass
        else:
            pass

    assert set(meter_block_by_name.keys()) == expected_meter_names, str(logger)
    meter_name: str
    meter_block: Block
    for meter_name, meter_block in meter_block_by_name.items():
        owner_model: Block = owner_model_by_meter_name[meter_name]
        output_var_uid: int
        for output_var_uid in (output_var.uid for output_var in meter_block.out_vars):
            algebraic_owners: list[tuple[Block, Var]] = list(
                (owner_child, algebraic_var)
                for owner_child in owner_model.get_all_blocks()
                for algebraic_var in owner_child.algebraic_vars
                if algebraic_var.uid == output_var_uid
            )
            assert len(algebraic_owners) == 1, meter_name
            assert algebraic_owners[0][0] is meter_block
            initialization_owner_uids: set[int] = set(
                initialization_var.uid
                for initialization_var in meter_block.init_eqs.keys()
            )
            assert output_var_uid in initialization_owner_uids, meter_name
            assert len(meter_block.algebraic_vars) == len(
                meter_block.algebraic_eqs
            )
            residual_owner_indices: list[int] = list(
                algebraic_index
                for algebraic_index in range(len(meter_block.algebraic_vars))
                if meter_block.algebraic_vars[algebraic_index].uid == output_var_uid
            )
            assert len(residual_owner_indices) == 1, meter_name
            owned_residual: Expr = meter_block.algebraic_eqs[
                residual_owner_indices[0]
            ]
            assert output_var_uid in set(
                residual_var.uid for residual_var in owned_residual.get_vars()
            ), meter_name
        assert "powerfactory" not in meter_name.lower()
        assert all(
            "powerfactory" not in output_var.name.lower()
            for output_var in meter_block.out_vars
        )
        meter_output_reference_uids: set[int] = set(
            output_var.shared_ref.uid
            for output_var in meter_block.out_vars
            if output_var.shared_ref is not None
        )
        connected_controller_reference_uids: set[int] = set(
            input_var.shared_ref.uid
            for owner_child in owner_model.get_all_blocks()
            if owner_child is not meter_block
            for input_var in owner_child.in_vars
            if input_var.shared_ref is not None
        )
        assert (
            len(
                meter_output_reference_uids.intersection(
                    connected_controller_reference_uids,
                )
            ) > 0
        ), meter_name

    assert logger.error_count() == 0


def test_v1_early_native_measurements_preserve_power_and_phase_semantics() -> None:
    """Keep native DGS scale, orientation and stationary-frame equations.

    :return: None.
    """
    dgs_path: Path = _get_complete_hvdc_vsc_dgs_path(
        file_name="hvdc_vsc_v1_complete_static_dynamic.dgs",
    )
    circuit: MultiCircuit = dgs_to_circuit(
        path=str(dgs_path),
        use_dynamic_information=True,
        dynamic_simulation_mode=DynamicSimulationMode.RMS,
    )
    expected_power_meter_names: set[str] = set((
        "Power meter 220",
        "Power meter 221",
    ))
    expected_voltage_meter_names: set[str] = set((
        "Voltage meter 244",
        "Voltage meter 245",
    ))
    found_power_meter_names: set[str] = set()
    found_voltage_meter_names: set[str] = set()
    found_generic_voltage_meter_count: int = 0
    found_stationary_phase_meter_count: int = 0
    found_vsc_converter_count: int = 0
    converter: VSC
    for converter in circuit.vsc_devices:
        candidate_block: Block
        for candidate_block in converter.rms_model.get_all_blocks():
            if candidate_block.name.startswith("MEASUREMENTS_VOLTAGE"):
                found_generic_voltage_meter_count += 1
            else:
                pass
            if candidate_block.name in expected_power_meter_names:
                found_power_meter_names.add(candidate_block.name)
                equation_texts: list[str] = list(
                    str(equation)
                    for equation in candidate_block.algebraic_eqs
                )
                assert any(
                    "-0.07142857142857142" in equation_text
                    and "Pac" in equation_text
                    for equation_text in equation_texts
                )
                assert any(
                    "-0.07142857142857142" in equation_text
                    and "Qac" in equation_text
                    for equation_text in equation_texts
                )
            else:
                equation_texts = list(
                    str(equation)
                    for equation in candidate_block.algebraic_eqs
                )
                if candidate_block.name in expected_voltage_meter_names:
                    found_voltage_meter_names.add(candidate_block.name)
                else:
                    has_stationary_cosine: bool = any(
                        "(cosphi) - (1.0)" == equation_text
                        for equation_text in equation_texts
                    )
                    has_stationary_sine: bool = any(
                        "(sinphi) - (0.0)" == equation_text
                        for equation_text in equation_texts
                    )
                    if has_stationary_cosine and has_stationary_sine:
                        found_stationary_phase_meter_count += 1
                    else:
                        pass

        # The native physical block is now the assembled root and exposes its
        # equipment signals directly, including current and DC conversion probes.
        found_vsc_converter_count += 1
        assert set(
            output_var.name for output_var in converter.rms_model.out_vars
        ) == {
            "id", "iq", "uDC", "Pdc", "Pac", "Qac", "Iac",
            "Idc_network", "Pdc_conversion",
        }
        assert set((
            VarPowerFlowReferenceType.Pf,
            VarPowerFlowReferenceType.Pt,
            VarPowerFlowReferenceType.Qt,
            VarPowerFlowReferenceType.Idc,
        )).issubset(converter.rms_model.external_mapping)

    assert found_power_meter_names == expected_power_meter_names
    assert found_voltage_meter_names == expected_voltage_meter_names
    assert found_generic_voltage_meter_count == 0
    assert found_stationary_phase_meter_count == 2
    assert found_vsc_converter_count == 2


@pytest.mark.parametrize(
    ("file_name", "expected_meter_names"),
    (
        (
            "hvdc_vsc_v1_complete_static_dynamic.dgs",
            set((
                "Power meter 220",
                "Power meter 221",
            )),
        ),
        (
            "hvdc_vsc_v2_complete_static_dynamic.dgs",
            set((
                "Power meter 228",
                "Power meter 229",
            )),
        ),
    ),
)

def test_v1_v2_dynamic_routes_keep_power_meters_as_editor_blocks(
        file_name: str,
        expected_meter_names: set[str],
) -> None:
    """Keep V1 and V2 active-power meters as connected RMS child blocks.

    :param file_name: Exact tracked DGS fixture name.
    :param expected_meter_names: Expected canonical VeraGrid meter names.
    :return: None.
    """
    dgs_path: Path = _get_complete_hvdc_vsc_dgs_path(file_name=file_name)
    logger: Logger = Logger()
    circuit: MultiCircuit = dgs_to_circuit(
        path=str(dgs_path),
        use_dynamic_information=True,
        dynamic_simulation_mode=DynamicSimulationMode.RMS,
        logger_=logger,
    )
    dc_branch: DynamicDevice
    for dc_branch in circuit.get_branches_iter(
            add_vsc=False,
            add_hvdc=False,
            add_switch=True,
    ):
        if dc_branch.bus_from.is_dc and dc_branch.bus_to.is_dc:
            from_bus_vdc: Var | None = dc_branch.bus_from.rms_model.external_mapping.get(
                VarPowerFlowReferenceType.Vdc,
                None,
            )
            to_bus_vdc: Var | None = dc_branch.bus_to.rms_model.external_mapping.get(
                VarPowerFlowReferenceType.Vdc,
                None,
            )
            branch_vdc_from: Var | None = dc_branch.rms_model.external_mapping.get(
                VarPowerFlowReferenceType.Vmf,
                None,
            )
            branch_vdc_to: Var | None = dc_branch.rms_model.external_mapping.get(
                VarPowerFlowReferenceType.Vmt,
                None,
            )
            assert from_bus_vdc is not None
            assert to_bus_vdc is not None
            assert branch_vdc_from is not None
            assert branch_vdc_to is not None
            assert branch_vdc_from.uid == from_bus_vdc.uid
            assert branch_vdc_to.uid == to_bus_vdc.uid
        else:
            pass
    dc_converter: VSC
    for dc_converter in circuit.get_vsc():
        converter_bus_vdc: Var | None = dc_converter.bus_from.rms_model.external_mapping.get(
            VarPowerFlowReferenceType.Vdc,
            None,
        )
        converter_vdc_from: Var | None = dc_converter.rms_model.external_mapping.get(
            VarPowerFlowReferenceType.Vf_dc,
            None,
        )
        assert dc_converter.bus_from.is_dc
        assert converter_bus_vdc is not None
        assert converter_vdc_from is not None
        assert converter_vdc_from.uid == converter_bus_vdc.uid
    meter_block_by_name: dict[str, Block] = dict()
    owner_model_by_meter_name: dict[str, Block] = dict()
    owner_device_by_meter_name: dict[str, DynamicDevice] = dict()
    candidate_device: object

    for candidate_device in circuit.get_injection_devices():
        if isinstance(candidate_device, DynamicDevice):
            candidate_block: Block
            for candidate_block in candidate_device.rms_model.get_all_blocks():
                if candidate_block.name in expected_meter_names:
                    meter_block_by_name[candidate_block.name] = candidate_block
                    owner_model_by_meter_name[candidate_block.name] = candidate_device.rms_model
                    owner_device_by_meter_name[candidate_block.name] = candidate_device
                else:
                    pass
        else:
            pass
    for candidate_device in circuit.get_branches(
            add_vsc=True,
            add_hvdc=True,
            add_switch=True,
    ):
        if isinstance(candidate_device, DynamicDevice):
            for candidate_block in candidate_device.rms_model.get_all_blocks():
                if candidate_block.name in expected_meter_names:
                    meter_block_by_name[candidate_block.name] = candidate_block
                    owner_model_by_meter_name[candidate_block.name] = candidate_device.rms_model
                    owner_device_by_meter_name[candidate_block.name] = candidate_device
                else:
                    pass
        else:
            pass

    assert set(meter_block_by_name.keys()) == expected_meter_names, str(logger)
    meter_name: str
    meter_block: Block
    for meter_name, meter_block in meter_block_by_name.items():
        owner_model: Block = owner_model_by_meter_name[meter_name]
        owner_device: DynamicDevice = owner_device_by_meter_name[meter_name]
        # Direct algebraic assignments now supply meter initialization through
        # the complete controller graph, without duplicating local init_eqs.
        initialization_graph: tuple[dict[Var, Expr], dict[Var, list[Var]], list[Var], dict[Var, Expr]] = (
            build_explicit_init_graph(mdl=owner_model)
        )
        initialization_equations: dict[Var, Expr] = initialization_graph[0]
        initialization_order_uids: set[int] = set(variable.uid for variable in initialization_graph[2])
        assert "powerfactory" not in meter_name.lower()
        assert all("powerfactory" not in output_var.name.lower() for output_var in meter_block.out_vars)
        output_var_uid: int
        for output_var_uid in (output_var.uid for output_var in meter_block.out_vars):
            algebraic_owners: list[tuple[Block, Var]] = list(
                (owner_child, algebraic_var)
                for owner_child in owner_model.get_all_blocks()
                for algebraic_var in owner_child.algebraic_vars
                if algebraic_var.uid == output_var_uid
            )
            assert len(algebraic_owners) == 1, meter_name
            assert algebraic_owners[0][0] is meter_block
            initialization_owner_uids: set[int] = set(
                initialization_var.uid
                for initialization_var in initialization_equations
            )
            assert output_var_uid in initialization_owner_uids, meter_name
            assert output_var_uid in initialization_order_uids, meter_name
            assert len(meter_block.algebraic_vars) == len(
                meter_block.algebraic_eqs
            )
            residual_owner_indices: list[int] = list(
                algebraic_index
                for algebraic_index in range(len(meter_block.algebraic_vars))
                if meter_block.algebraic_vars[algebraic_index].uid == output_var_uid
            )
            assert len(residual_owner_indices) == 1, meter_name
            owned_residual: Expr = meter_block.algebraic_eqs[
                residual_owner_indices[0]
            ]
            assert output_var_uid in set(
                residual_var.uid for residual_var in owned_residual.get_vars()
            ), meter_name
        if file_name == "hvdc_vsc_v1_complete_static_dynamic.dgs":
            # The V1 meters sit behind zero-impedance transformers. Topology
            # reduction removes those internal branch flows, so initialization
            # must relay the unique owner VSC terminal power while preserving
            # the transformer's FID and terminal-side measurement contract.
            assert isinstance(owner_device, VSC)
            owner_active_power: Var | None = owner_device.rms_model.external_mapping.get(
                VarPowerFlowReferenceType.Pt,
                None,
            )
            owner_reactive_power: Var | None = owner_device.rms_model.external_mapping.get(
                VarPowerFlowReferenceType.Qt,
                None,
            )
            assert owner_active_power is not None
            assert owner_reactive_power is not None
            initialization_dependency_uids: set[int] = set(
                dependency_var.uid
                for output_var in meter_block.out_vars
                for dependency_var in initialization_equations[output_var].get_vars()
            )
            assert owner_active_power.uid in initialization_dependency_uids
            assert owner_reactive_power.uid in initialization_dependency_uids
        else:
            pass
        # Early materialization reuses the consumer variables themselves,
        # so connectivity is represented by canonical UIDs rather than shared_ref.
        meter_output_uids: set[int] = set(
            output_var.uid
            for output_var in meter_block.out_vars
        )
        connected_controller_uids: set[int] = set(
            input_var.uid
            for owner_child in owner_model.get_all_blocks()
            if owner_child is not meter_block
            for input_var in owner_child.in_vars
        )
        assert len(meter_output_uids) > 0, meter_name
        assert meter_output_uids.issubset(connected_controller_uids), meter_name

    assert logger.error_count() == 0


def test_logical_actuator_missing_physical_branches_is_diagnostic() -> None:
    """Report declared actuator slots when no physical branch can be resolved.

    :return: None.
    """
    dgs_path: Path = _get_complete_hvdc_vsc_dgs_path(
        file_name="hvdc_vsc_v3_complete_static_dynamic.dgs",
    )
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(path=str(dgs_path))
    templates_by_root_id: dict[str, RmsModelTemplate] = dict()
    source_root: ElmComp
    for source_root in dgs_circuit.elmcomps:
        has_passive_entry: bool = False
        direct_entry: ElmCompInstanceEntry
        for direct_entry in extract_elmcomp_direct_instances(
                circuit=dgs_circuit,
                root_element=source_root,
        ):
            if direct_entry.element_kind == "ElmSind":
                has_passive_entry = True
            else:
                pass
        if has_passive_entry:
            templates_by_root_id[source_root.ID] = RmsModelTemplate(
                name=source_root.loc_name,
            )
        else:
            pass

    destination: MultiCircuit = MultiCircuit()
    logger: Logger = Logger()
    prepared_count: int = prepare_dgs_logical_actuator_topology(
        circuit=destination,
        dgs_circuit=dgs_circuit,
        templates_by_root_dgs_id=templates_by_root_id,
        logger=logger,
    )
    topology_warnings: list[LogEntry] = list(
        entry
        for entry in logger.entries
        if entry.msg == "DGS logical actuator topology is ambiguous"
    )

    assert len(templates_by_root_id) > 0
    assert prepared_count == 0
    assert len(destination.buses) == 0
    assert len(topology_warnings) == len(templates_by_root_id)
    assert all("lines=0" in str(entry.value) for entry in topology_warnings)


@pytest.mark.skip(reason="Incorrect")
def test_v3_switch_events_bind_guarded_modes_to_exact_rms_equipment() -> None:
    """Bind every enabled V3 EvtSwitch chain to a physical conduction state.

    :return: None.
    """
    dgs_path: Path = _get_complete_hvdc_vsc_dgs_path(
        file_name="hvdc_vsc_v3_complete_static_dynamic.dgs"
    )
    logger: Logger = Logger()
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(path=str(dgs_path))
    circuit: MultiCircuit = dgs_to_circuit(path=str(dgs_path))
    conversion_result: DgsDynamicTemplateConversionResult = (
        convert_and_add_dgs_dynamic_templates_to_circuit(
            dgs_circuit=dgs_circuit,
            circuit=circuit,
            target_domain=DynamicSimulationMode.RMS,
            logger=logger,
        )
    )
    templates_by_root_id: dict[
        str,
        RmsModelTemplate | EmtModelTemplate,
    ] = conversion_result.templates_by_root_dgs_id
    apply_dgs_dynamic_templates_to_devices(
        dgs_circuit=dgs_circuit,
        circuit=circuit,
        templates_by_root_dgs_id=templates_by_root_id,
        logger=logger,
    )

    event_target_ids: set[str] = set(("242", "243", "273", "274"))
    prepared_target_ids: set[str] = set()
    target_device: DynamicDevice
    for target_device in circuit.get_branches_iter(
            add_vsc=False,
            add_hvdc=False,
            add_switch=True,
    ):
        if target_device.idtag not in event_target_ids:
            pass
        else:
            if isinstance(target_device, Line):
                target_template: RmsModelTemplate = get_dc_line_rms_template(
                    vfactory=circuit.var_factory,
                    use_dynamic_inductance=False,
                )
            else:
                if isinstance(target_device, Transformer2W):
                    target_template = get_transformer2w_rms(
                        vf=circuit.var_factory,
                    )
                else:
                    raise AssertionError(
                        f"Unexpected switch-event target {target_device.idtag}"
                    )
            target_device.rms_model = target_template.block
            prepared_target_ids.add(target_device.idtag)

    assert prepared_target_ids == event_target_ids

    imported_event_output_names: set[str] = set()
    imported_mode_names: set[str] = set()
    imported_event_count: int = 0
    imported_event_count_by_root_id: dict[str, int] = dict()
    imported_root_template: RmsModelTemplate | EmtModelTemplate
    imported_block: Block
    imported_logic: object
    imported_mode: Var
    for imported_root_template in templates_by_root_id.values():
        root_event_count: int = 0
        for imported_block in imported_root_template.block.get_all_blocks():
            for imported_logic in imported_block.procedural_logic:
                if isinstance(imported_logic, DelayedSwitchEventLogic):
                    imported_event_count += 1
                    root_event_count += 1
                    imported_event_output_names.add(
                        imported_logic.output_var_name
                    )
                else:
                    pass
            for imported_mode in imported_block.mode_dict.keys():
                imported_mode_names.add(imported_mode.name)
        matching_root_ids: list[str] = list(
            root_id
            for root_id, candidate_template in templates_by_root_id.items()
            if candidate_template is imported_root_template
        )
        assert len(matching_root_ids) == 1
        imported_event_count_by_root_id[matching_root_ids[0]] = root_event_count
    assert imported_event_output_names.issubset(imported_mode_names), (
        imported_event_output_names,
        imported_mode_names,
    )
    assert imported_event_count == 16, imported_event_count_by_root_id

    bound_target_count: int = bind_dgs_switch_event_runtime(
        circuit=circuit,
        templates_by_root_dgs_id=templates_by_root_id,
        logger=logger,
    )
    binding_diagnostics: list[tuple[str, str, str]] = list(
        (log_entry.msg, log_entry.device, log_entry.value)
        for log_entry in logger.entries
    )
    assert bound_target_count == 4, binding_diagnostics

    switch_events: list[DelayedSwitchEventLogic] = list()
    registered_template: RmsModelTemplate
    event_block: Block
    logic_entry: object
    for registered_template in circuit.rms_models:
        for event_block in registered_template.block.get_all_blocks():
            for logic_entry in event_block.procedural_logic:
                if isinstance(logic_entry, DelayedSwitchEventLogic):
                    switch_events.append(logic_entry)
                else:
                    pass

    assert len(switch_events) == 16
    assert all(event.initial_closed for event in switch_events)
    assert all(not event.command_closed for event in switch_events)
    switch_ids: set[str] = set(
        event.target_switch_idtag for event in switch_events
    )
    target_device_ids: set[str] = set(
        event.target_device_idtag for event in switch_events
    )
    assert len(switch_ids) == 8
    assert target_device_ids == event_target_ids

    expected_switch_mode_count_by_device: dict[str, int] = dict()
    expected_switch_mode_count_by_device["242"] = 4
    expected_switch_mode_count_by_device["243"] = 4
    expected_switch_mode_count_by_device["273"] = 4
    expected_switch_mode_count_by_device["274"] = 4
    physical_branch: DynamicDevice
    for physical_branch in circuit.get_branches_iter(
            add_vsc=False,
            add_hvdc=False,
            add_switch=True,
    ):
        expected_mode_count: int | None = (
            expected_switch_mode_count_by_device.get(
                physical_branch.idtag,
                None,
            )
        )
        if expected_mode_count is None:
            pass
        else:
            conduction_expressions: list[Expr] = list()
            physical_block: Block
            conduction_parameter: Var
            conduction_expression: Expr
            for physical_block in physical_branch.rms_model.get_all_blocks():
                for conduction_parameter, conduction_expression in physical_block.event_dict.items():
                    if conduction_parameter.name == "u":
                        conduction_expressions.append(conduction_expression)
                    else:
                        pass
            assert len(conduction_expressions) == 1
            switch_mode_names: set[str] = set(
                variable.name
                for variable in conduction_expressions[0].get_vars()
                if variable.name.startswith("dgs_switch_")
            )
            assert len(switch_mode_names) == expected_mode_count

    switch_binding_diagnostics: list[str] = list(
        log_entry.msg
        for log_entry in logger.entries
        if log_entry.msg.startswith("DGS switch")
    )
    assert switch_binding_diagnostics == list()


def test_delayed_switch_event_opens_on_the_guarded_trigger_boundary() -> None:
    """Execute a rising trigger and open the retained mode at exact ``dtime``.

    :return: None.
    """
    variable_factory: VarFactory = VarFactory()
    trigger: Var = variable_factory.add_var("switch_trigger")
    switch_mode: Var = variable_factory.add_var("switch_closed")
    event_logic: DelayedSwitchEventLogic = DelayedSwitchEventLogic(
        output_var_name=switch_mode.name,
        guard_expr=Const(1.0),
        trigger_expr=trigger,
        delay_expr=Const(0.25),
        target_device_idtag="TARGET_DEVICE",
        target_switch_idtag="TARGET_SWITCH",
        target_terminal_index=0,
        initial_closed=True,
        command_closed=False,
        name="Open target switch",
    )
    event_values: dict[Var, Expr] = dict()
    event_values[trigger] = Const(0.0)
    mode_values: dict[Var, Expr] = dict()
    mode_values[switch_mode] = Const(1.0)
    procedural_entries: list[DelayedSwitchEventLogic] = list()
    procedural_entries.append(event_logic)
    block: Block = Block(
        name="DGS delayed switch event runtime",
        event_dict=event_values,
        mode_dict=mode_values,
        procedural_logic=procedural_entries,
    )
    block.unify_blocks()
    problem: DgsSwitchEventProblem = DgsSwitchEventProblem(
        sys_block=block,
        glob_time=variable_factory.add_var("glob_time"),
        static_parameter_values_mapping=dict(block.parameters),
    )
    event_logic.bind(problem=problem)
    params: np.ndarray = problem.event_params_values.copy()
    state: np.ndarray = problem.get_x0().copy()
    trigger_index: int = problem.uid2idx_event_params[trigger.uid]
    switch_index: int = problem.uid2idx_event_params[switch_mode.uid]

    event_logic.update(t=0.0, x=state, params=params)
    assert params[switch_index] == 1.0

    params[trigger_index] = 1.0
    event_logic.update(t=1.0, x=state, params=params)
    forced_event_time: float | None = event_logic.get_next_forced_event_time(
        t_prev=1.0,
        t_target=2.0,
    )
    assert forced_event_time == pytest.approx(1.25)

    event_logic.update(t=1.249, x=state, params=params)
    assert params[switch_index] == 1.0
    event_logic.update(t=1.25, x=state, params=params)
    assert params[switch_index] == 0.0
    assert event_logic.fired


def test_inc0_is_only_a_fallback_for_explicit_initialization() -> None:
    """Keep inc0 unless a later authoritative inc declaration replaces it.

    :return: None.
    """
    fallback_definition: BlkDef = BlkDef()
    fallback_definition.ID = "inc0_fallback"
    fallback_definition.loc_name = "Inc0Fallback"
    fallback_definition.outputs = list(("y",))
    fallback_definition.states = list(("x",))
    fallback_definition.equations_raw = list(("inc0(x)=1.0;y=x",))

    override_definition: BlkDef = BlkDef()
    override_definition.ID = "inc_override"
    override_definition.loc_name = "IncOverride"
    override_definition.outputs = list(("y",))
    override_definition.states = list(("x",))
    override_definition.equations_raw = list((
        "inc0(x)=1.0;inc(x)=2.0;inc0(x)=3.0;y=x",
    ))

    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.blkdefs = list((fallback_definition, override_definition))
    parsed_blocks: dict[str, ParsedDgsBlockDefinition] = (
        parse_dgs_block_definitions_from_circuit(circuit=dgs_circuit)
    )

    fallback_expression: Expr = parsed_blocks["inc0_fallback"].init_rhs["x"]
    override_expression: Expr = parsed_blocks["inc_override"].init_rhs["x"]
    fallback_block: Block = build_standalone_blkdef_block_from_parsed_block(
        parsed_block=parsed_blocks["inc0_fallback"],
    )
    override_block: Block = build_standalone_blkdef_block_from_parsed_block(
        parsed_block=parsed_blocks["inc_override"],
    )
    fallback_block_expression: Expr = next(iter(fallback_block.init_eqs.values()))
    override_block_expression: Expr = next(iter(override_block.init_eqs.values()))

    assert fallback_expression.eval_uid(dict()) == pytest.approx(1.0)
    assert override_expression.eval_uid(dict()) == pytest.approx(2.0)
    assert len(fallback_block.init_eqs) == 1
    assert len(override_block.init_eqs) == 1
    assert fallback_block_expression.eval_uid(dict()) == pytest.approx(1.0)
    assert override_block_expression.eval_uid(dict()) == pytest.approx(2.0)


# Alex review required: an additional VSC cubicle invalidates the complete topology.
def test_monopolar_vsc_rejects_an_unexpected_extra_cubicle() -> None:
    """Reject topology that contains the expected roles plus an extra cubicle.

    :return: None.
    """
    source: ElmVscmono = ElmVscmono()
    source.ID = "VSC_SOURCE"
    source.loc_name = "Generic monopolar converter"
    ac_bus: Bus = Bus(name="AC bus", Vnom=220.0)
    dc_bus: Bus = Bus(name="DC bus", Vnom=320.0)
    extra_bus: Bus = Bus(name="Unexpected bus", Vnom=320.0)

    ac_cubicle: StaCubic = StaCubic()
    ac_cubicle.ID = "AC_CUBICLE"
    ac_cubicle.fold_id = "AC_TERMINAL"
    ac_cubicle.obj_bus = 0
    dc_cubicle: StaCubic = StaCubic()
    dc_cubicle.ID = "DC_CUBICLE"
    dc_cubicle.fold_id = "DC_TERMINAL"
    dc_cubicle.obj_bus = 1
    extra_cubicle: StaCubic = StaCubic()
    extra_cubicle.ID = "EXTRA_CUBICLE"
    extra_cubicle.fold_id = "EXTRA_TERMINAL"
    extra_cubicle.obj_bus = 2
    logger: Logger = Logger()

    converter: VSC | None = convert_dgs_to_monopolar_vsc(
        source=source,
        cubics_by_objid={
            source.ID: [ac_cubicle, dc_cubicle, extra_cubicle],
        },
        bus_by_term_id={
            "AC_TERMINAL": ac_bus,
            "DC_TERMINAL": dc_bus,
            "EXTRA_TERMINAL": extra_bus,
        },
        switch_by_cubic_id=dict(),
        system_base_mva=100.0,
        frequency_hz=50.0,
        logger=logger,
    )

    assert converter is None
    assert logger.warning_count() == 1


def test_dgs_parser_preserves_dynamic_composite_rows_without_inventing_types() -> None:
    """Preserve exact dynamic rows from a tracked PowerFactory DGS export."""

    dgs_path: Path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "grids"
        / "test_ieee14_svs.dgs"
    )
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(path=str(dgs_path))

    composite_rows: list[tuple[str, str, str, int, str | None]] = [
        (model.ID, model.loc_name, model.fold_id, model.outserv, model.typ_id)
        for model in circuit.elmcomps
    ]
    assert composite_rows == [
        ("2", "WECC WT Control System Type 4B(1)", "85", 0, None),
        ("3", "WECC WT Control System Type 4B(2)", "85", 0, None),
        ("4", "WECC WT Control System Type 4B(3)", "85", 0, None),
        ("5", "WECC WT Control System Type 4B(4)", "85", 0, None),
        ("6", "WECC WT Control System Type 4B(6)", "85", 0, None),
        ("7", "WECC WT Control System Type 4B(7)", "85", 0, None),
        ("8", "WECC WT Control System Type 4B(8)", "85", 0, None),
        ("9", "WECC WT Control System Type 4B", "85", 0, None),
    ]
    assert len(circuit.elmdsls) == 40
    assert len(circuit.blkdefs) == 0
    assert len(circuit.blkslots) == 0


def test_dgs_parser_preserves_static_var_system_runtime_constants() -> None:
    """Keep the exact SVC values consumed by the dynamic runtime adapter."""

    dgs_path: Path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "grids"
        / "test_ieee14_svs.dgs"
    )
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(path=str(dgs_path))

    static_var_system_rows: list[
        tuple[str, str, float, float, int, int, float]
    ] = [
        (
            device.ID,
            device.loc_name,
            device.tcrmax,
            device.qmin,
            device.nxcap,
            device.nfixcap,
            device.Qfixcap,
        )
        for device in circuit.elmsvss
    ]
    assert static_var_system_rows == [
        ("86", "SVS_Droop", 10.0, -20.0, 2, 0, 0.0),
        ("87", "SVS_NoControl", 5.0, -10.0, 1, 0, 0.0),
        ("88", "SVS_Qcontrol", 30.0, -15.0, 2, 1, -5.0),
        ("89", "SVS_Ucontrol", 0.0, 0.0, 0, 0, 0.0),
    ]


def test_dgs_parser_preserves_native_graphical_operator_records() -> None:
    """
    Preserve native arithmetic and switch records for later graph materialization.

    :return: None.
    """
    circuit: DgsCircuit = _parse_native_graphical_operator_fixture()

    division_rows: list[tuple[str, str, str]] = [
        (operator.ID, operator.OP, operator.loc_name)
        for operator in circuit.blkdivs
    ]
    multiplication_rows: list[tuple[str, str, str]] = [
        (operator.ID, operator.OP, operator.loc_name)
        for operator in circuit.blkmuls
    ]
    switch_rows: list[tuple[str, str, str, int]] = [
        (operator.ID, operator.OP, operator.loc_name, operator.iNeg)
        for operator in circuit.blkswts
    ]
    assert division_rows == [("DIV", "C", "Divide power by voltage")]
    assert multiplication_rows == [("MUL", "C", "Multiply signals")]
    assert switch_rows == [("SWT", "C", "Select signal", 0)]
    assert circuit.blkgotos[0].signals == ["route_a", "route_b"]


def test_native_graphical_arithmetic_records_build_executable_blocks(
) -> None:
    """
    Execute the ordered division and multiplication encoded by native DGS nodes.

    :return: None.
    """
    circuit: DgsCircuit = _parse_native_graphical_operator_fixture()
    arithmetic_nodes: tuple[BlkDiv | BlkMul, ...] = (
        circuit.blkdivs[0],
        circuit.blkmuls[0],
    )
    arithmetic_results: list[
        tuple[
            Block,
            list[str],
            list[str],
            dict[tuple[DgsGraphicalConnectorKind, int], int],
        ]
    ] = list()
    arithmetic_node: BlkDiv | BlkMul

    for arithmetic_node in arithmetic_nodes:
        arithmetic_results.append(
            build_graphical_arithmetic_block(
                node=arithmetic_node,
                circuit=circuit,
            )
        )

    division_block: Block
    division_inputs: list[str]
    division_outputs: list[str]
    division_input_index_by_connector: dict[
        tuple[DgsGraphicalConnectorKind, int],
        int,
    ]
    (
        division_block,
        division_inputs,
        division_outputs,
        division_input_index_by_connector,
    ) = arithmetic_results[0]
    multiplication_block: Block
    multiplication_inputs: list[str]
    multiplication_outputs: list[str]
    multiplication_input_index_by_connector: dict[
        tuple[DgsGraphicalConnectorKind, int],
        int,
    ]
    (
        multiplication_block,
        multiplication_inputs,
        multiplication_outputs,
        multiplication_input_index_by_connector,
    ) = arithmetic_results[1]

    assert division_inputs == ["Pord", "Vt"]
    assert division_outputs == ["Ip_unlim"]
    assert division_input_index_by_connector == {
        (DgsGraphicalConnectorKind.Input, 0): 0,
        (DgsGraphicalConnectorKind.Input, 1): 1,
    }
    assert division_block.post_init_seed_eqs[
        division_block.out_vars[0]
    ].eval(Pord=0.8, Vt=0.5) == pytest.approx(1.6)
    assert multiplication_inputs == ["a", "b", "c"]
    assert multiplication_outputs == ["product"]
    assert multiplication_input_index_by_connector == {
        (DgsGraphicalConnectorKind.Input, 0): 0,
        (DgsGraphicalConnectorKind.Input, 1): 1,
        (DgsGraphicalConnectorKind.Input, 2): 2,
    }
    assert multiplication_block.post_init_seed_eqs[
        multiplication_block.out_vars[0]
    ].eval(a=2.0, b=3.0, c=4.0) == pytest.approx(24.0)


def test_native_graphical_switch_record_builds_threshold_logic() -> None:
    """
    Execute both native switch positions and the exported inverted position.

    :return: None.
    """
    circuit: DgsCircuit = _parse_native_graphical_operator_fixture()
    switch_block: Block
    switch_inputs: list[str]
    switch_outputs: list[str]
    switch_input_index_by_connector: dict[
        tuple[DgsGraphicalConnectorKind, int],
        int,
    ]
    (
        switch_block,
        switch_inputs,
        switch_outputs,
        switch_input_index_by_connector,
    ) = build_graphical_switch_block(
        node=circuit.blkswts[0],
        circuit=circuit,
    )
    switch_expression: Expr = switch_block.post_init_seed_eqs[switch_block.out_vars[0]]

    assert switch_inputs == ["default_input", "changed_input", "control"]
    assert switch_outputs == ["selected"]
    assert switch_input_index_by_connector == {
        (DgsGraphicalConnectorKind.Input, 0): 0,
        (DgsGraphicalConnectorKind.Input, 1): 1,
        (DgsGraphicalConnectorKind.UpperLimitInput, 0): 2,
    }
    assert switch_expression.eval(
        default_input=10.0,
        changed_input=20.0,
        control=0.4,
    ) == pytest.approx(10.0)
    assert switch_expression.eval(
        default_input=10.0,
        changed_input=20.0,
        control=0.6,
    ) == pytest.approx(20.0)

    circuit.blkswts[0].iNeg = 1
    inverted_block: Block = build_graphical_switch_block(
        node=circuit.blkswts[0],
        circuit=circuit,
    )[0]
    inverted_expression: Expr = inverted_block.post_init_seed_eqs[inverted_block.out_vars[0]]
    assert inverted_expression.eval(
        default_input=10.0,
        changed_input=20.0,
        control=0.4,
    ) == pytest.approx(20.0)
    assert inverted_expression.eval(
        default_input=10.0,
        changed_input=20.0,
        control=0.6,
    ) == pytest.approx(10.0)


# Dynamic contract: a sparse BlkSum retains raw output port four.
def test_sparse_native_sum_resolves_its_exported_output_port() -> None:
    """Resolve a sum with active raw inputs zero and three to output pin four.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    circuit.blksigs = [
        signal
        for signal in circuit.blksigs
        if signal.ID != "MUL_TO_ROOT"
    ]
    sparse_sum: BlkSum = BlkSum()
    sparse_sum.ID = "SPARSE_SUM"
    sparse_sum.loc_name = "Sparse sum producer"
    sparse_sum.iInput0 = 0
    sparse_sum.iInput3 = 0
    circuit.blksums.append(sparse_sum)

    raw_input_index: int
    for raw_input_index in (0, 3):
        input_signal: BlkSig = BlkSig()
        input_signal.ID = f"ROOT_TO_SPARSE_SUM_{raw_input_index}"
        input_signal.loc_name = "external_x"
        input_signal.inodfrom = 0
        input_signal.iconfrom = 1
        input_signal.inodto = raw_input_index
        input_signal.iconto = 0
        input_signal.pnodfrom = "MACRO"
        input_signal.pnodto = sparse_sum.ID
        circuit.blksigs.append(input_signal)

    output_signal: BlkSig = BlkSig()
    output_signal.ID = "SPARSE_SUM_TO_ROOT"
    output_signal.loc_name = "public_y"
    output_signal.inodfrom = 4
    output_signal.iconfrom = 0
    output_signal.inodto = 0
    output_signal.iconto = 2
    output_signal.pnodfrom = sparse_sum.ID
    output_signal.pnodto = "MACRO"
    circuit.blksigs.append(output_signal)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    graphical_tree: DgsGraphicTreeResult | None = (
        extract_root_slot_graphical_tree_from_circuit(
            circuit=circuit,
            result=root_result,
            slot_name="Graphical parent",
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )
    )

    assert graphical_tree is not None
    sparse_block: Block | None = None
    child_block: Block
    for child_block in graphical_tree.view_block.children:
        if child_block.name == sparse_sum.loc_name:
            sparse_block = child_block
        else:
            pass
    assert sparse_block is not None
    assert graphical_tree.view_block.out_vars[0].uid == sparse_block.out_vars[0].uid


def test_graphical_parent_binds_exact_child_signals_and_keeps_live_gaps() -> None:
    """Bind parent initialization through a complete portable DGS graph.

    :return: None.
    """
    graphical_tree: DgsGraphicTreeResult | None = (
        extract_root_slot_block_graphical_tree(
            dgs_path=str(_get_graphical_parent_signal_binding_dgs_path()),
            slot_name="Graphical parent",
            root_name="Graphical root",
            root_typ_id="FRAME",
        )
    )

    assert graphical_tree is not None
    assert graphical_tree.parent_bindings.resolved_internal_names == [
        "blank_internal",
        "produced_internal",
    ]
    assert graphical_tree.parent_bindings.disconnected_input_names == [
        "blank_internal",
    ]
    assert graphical_tree.parent_bindings.unresolved_input_names == [
        "routed_internal",
    ]

    produced_output_uid: int | None = None
    disconnected_input_uid: int | None = None
    disconnected_event: Expr | None = None
    child_block: Block

    # Locate the concrete child identities that must replace the parent's raw
    # internal variables.
    for child_block in graphical_tree.view_block.children:
        if child_block.name == "Multiply parent inputs":
            produced_output_uid = child_block.out_vars[0].uid
        else:
            pass
        if child_block.name == "Consume disconnected input":
            assert len(child_block.event_dict) == 1
            disconnected_input_uid = list(child_block.event_dict.keys())[0].uid
            disconnected_event = list(child_block.event_dict.values())[0]
        else:
            pass

    assert produced_output_uid is not None
    assert disconnected_input_uid is not None
    assert disconnected_event is not None
    assert disconnected_event.eval() == 0.0
    assert graphical_tree.view_block.out_vars[0].uid == produced_output_uid
    assert graphical_tree.view_block.out_vars[0].name == "public_y"

    parent_init_expressions: list[Expr] = list(
        graphical_tree.view_block.init_eqs.values()
    )
    assert len(parent_init_expressions) == 1
    parent_dependency_uids: set[int] = set(
        dependency_var.uid
        for dependency_var in parent_init_expressions[0].get_vars()
    )
    parent_dependency_names: set[str] = set(
        dependency_var.name
        for dependency_var in parent_init_expressions[0].get_vars()
    )
    assert produced_output_uid in parent_dependency_uids
    assert disconnected_input_uid in parent_dependency_uids
    # Unresolved parent internals retain their lexically qualified runtime
    # name so unrelated graphical blocks cannot merge variables by raw name.
    assert "Graphical parent__routed_internal" in parent_dependency_names


# Dynamic contract: a macro output without a producer does not retain a dead Var.
def test_graphical_macro_rejects_an_output_without_semantics() -> None:
    """Reject a public macro output with no producer or explicit equation.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    dynamic_element: ElmDsl = circuit.elmdsls[0]
    dynamic_definition: BlkDef | None = None
    candidate_definition: BlkDef
    for candidate_definition in circuit.blkdefs:
        if candidate_definition.ID == dynamic_element.typ_id:
            dynamic_definition = candidate_definition
        else:
            pass
    assert dynamic_definition is not None
    dynamic_definition.outputs.append("unproduced_output")

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(
        ValueError,
        match="Graphical DGS macro output has no producer",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


# Dynamic contract: inc(y) alone replaces neither a producer nor a runtime equation.
def test_graphical_macro_rejects_an_init_only_output() -> None:
    """Reject a macro output that has initialization but no runtime producer.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    remaining_signals: list[BlkSig] = [
        signal
        for signal in circuit.blksigs
        if signal.ID != "MUL_TO_ROOT"
    ]
    circuit.blksigs = remaining_signals

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(
        ValueError,
        match="Graphical DGS macro output has no producer",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


# Dynamic contract: two explicit cables cannot silently select the first one.
def test_graphical_macro_rejects_multiple_explicit_input_cables() -> None:
    """Reject two exact graphical cables targeting the same runtime input.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]

    duplicate_signal: BlkSig = BlkSig()
    duplicate_signal.ID = "DUPLICATE_ROOT_TO_MUL_0"
    duplicate_signal.loc_name = "external_x"
    duplicate_signal.inodfrom = 0
    duplicate_signal.iconfrom = 1
    duplicate_signal.inodto = 0
    duplicate_signal.iconto = 0
    duplicate_signal.pnodfrom = "MACRO"
    duplicate_signal.pnodto = "MUL"
    circuit.blksigs.append(duplicate_signal)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(
        ValueError,
        match="Graphical DGS input has multiple explicit cables",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


# Dynamic contract: an invalid root source connector does not fall back to aliases.
def test_graphical_macro_rejects_an_invalid_explicit_source_connector() -> None:
    """Reject an exact cable whose root endpoint declares output direction.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    graphical_signal: BlkSig
    for graphical_signal in circuit.blksigs:
        if graphical_signal.ID == "ROOT_TO_MUL_0":
            graphical_signal.iconfrom = 2
        else:
            pass

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(
        ValueError,
        match="invalid root source connector",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


@pytest.mark.parametrize(
    ("source_id", "source_connector", "source_output_index", "diagnostic"),
    (
        ("MUL", 1, 2, "invalid child source connector"),
        ("MISSING_SOURCE", 0, 2, "missing source FID"),
        ("MUL", 0, 999, "invalid source output"),
    ),
)
# Dynamic contract: every macro output validates its exact source.
def test_graphical_macro_rejects_an_invalid_explicit_output_source(
        source_id: str,
        source_connector: int,
        source_output_index: int,
        diagnostic: str,
) -> None:
    """Reject a malformed source endpoint on a child-to-root cable.

    :param source_id: Mutated source FID.
    :param source_connector: Mutated source connector category.
    :param source_output_index: Mutated raw source port.
    :param diagnostic: Expected fail-closed diagnostic fragment.
    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    graphical_signal: BlkSig
    for graphical_signal in circuit.blksigs:
        if graphical_signal.ID == "MUL_TO_ROOT":
            graphical_signal.pnodfrom = source_id
            graphical_signal.iconfrom = source_connector
            graphical_signal.inodfrom = source_output_index
        else:
            pass

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(ValueError, match=diagnostic):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


@pytest.mark.parametrize(
    ("target_id", "target_connector", "target_output_index", "diagnostic"),
    (
        ("MACRO", 1, 0, "invalid root output"),
        ("MACRO", 2, 999, "invalid root output"),
        ("MISSING_TARGET", 2, 0, "missing target FID"),
    ),
)
# Dynamic contract: every macro output validates its exact target.
def test_graphical_macro_rejects_an_invalid_explicit_output_target(
        target_id: str,
        target_connector: int,
        target_output_index: int,
        diagnostic: str,
) -> None:
    """Reject a malformed macro endpoint on a child-to-root cable.

    :param target_id: Mutated target FID.
    :param target_connector: Mutated target connector category.
    :param target_output_index: Mutated raw target port.
    :param diagnostic: Expected fail-closed diagnostic fragment.
    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    graphical_signal: BlkSig
    for graphical_signal in circuit.blksigs:
        if graphical_signal.ID == "MUL_TO_ROOT":
            graphical_signal.pnodto = target_id
            graphical_signal.iconto = target_connector
            graphical_signal.inodto = target_output_index
        else:
            pass

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(ValueError, match=diagnostic):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


# Dynamic contract: a root output does not accept two exact cables.
def test_graphical_macro_rejects_multiple_explicit_output_cables() -> None:
    """Reject two exact graphical cables targeting one macro output.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    duplicate_signal: BlkSig = BlkSig()
    duplicate_signal.ID = "DUPLICATE_MUL_TO_ROOT"
    duplicate_signal.loc_name = "public_y"
    duplicate_signal.inodfrom = 2
    duplicate_signal.iconfrom = 0
    duplicate_signal.inodto = 0
    duplicate_signal.iconto = 2
    duplicate_signal.pnodfrom = "MUL"
    duplicate_signal.pnodto = "MACRO"
    circuit.blksigs.append(duplicate_signal)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(
        ValueError,
        match="root output has multiple explicit cables",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


# Dynamic contract: an explicitly blank root output does not fall back to aliases.
def test_graphical_macro_rejects_an_explicit_blank_output_source() -> None:
    """Reject a blank child-to-root cable despite a compatible producer alias.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    graphical_signal: BlkSig
    for graphical_signal in circuit.blksigs:
        if graphical_signal.ID == "MUL_TO_ROOT":
            graphical_signal.pnodfrom = ""
        else:
            pass
    alias_signal: BlkSig = BlkSig()
    alias_signal.ID = "UNCONNECTED_PUBLIC_OUTPUT_ALIAS"
    alias_signal.loc_name = "public_y"
    alias_signal.inodfrom = 2
    alias_signal.iconfrom = 0
    alias_signal.inodto = 0
    alias_signal.iconto = 0
    alias_signal.pnodfrom = "MUL"
    alias_signal.pnodto = ""
    circuit.blksigs.append(alias_signal)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(
        ValueError,
        match="root output cable has no exact source",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


# Dynamic contract: an explicitly blank cable does not re-enter through aliases.
def test_graphical_macro_does_not_invent_a_source_for_an_explicit_blank_cable(
) -> None:
    """Keep a live blank-source pin unresolved despite a compatible alias.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    route_reader: BlkFrom = circuit.blkfroms[0]
    route_reader.signals.append("external_x")

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(
        ValueError,
        match="unresolved live inputs: routed_internal",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


# Dynamic contract: multiple root aliases are not resolved by list order.
def test_graphical_macro_rejects_ambiguous_root_aliases() -> None:
    """Reject a routed input compatible with two macro-boundary variables.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    dynamic_element: ElmDsl = circuit.elmdsls[0]
    dynamic_definition: BlkDef | None = None
    candidate_definition: BlkDef
    for candidate_definition in circuit.blkdefs:
        if candidate_definition.ID == dynamic_element.typ_id:
            dynamic_definition = candidate_definition
        else:
            pass
    assert dynamic_definition is not None
    dynamic_definition.inputs.append("secondary_input")
    route_reader: BlkFrom = circuit.blkfroms[0]
    route_reader.signals = [
        "ambiguous_route",
        "external_x",
        "secondary_input",
    ]

    alias_definition: BlkDef = BlkDef()
    alias_definition.ID = "AMBIGUOUS_ALIAS_DEFINITION"
    alias_definition.loc_name = "Ambiguous alias consumer"
    alias_definition.inputs.append("ambiguous_route")
    alias_definition.outputs.append("unused_alias_output")
    alias_definition.equations_raw.append(
        "unused_alias_output=ambiguous_route"
    )
    circuit.blkdefs.append(alias_definition)
    alias_reference: BlkRef = BlkRef()
    alias_reference.ID = "AMBIGUOUS_ALIAS_REFERENCE"
    alias_reference.typ_id = alias_definition.ID
    alias_reference.cdisName = alias_definition.loc_name
    circuit.blkrefs.append(alias_reference)
    rescue_signal: BlkSig = BlkSig()
    rescue_signal.ID = "RESCUE_AMBIGUOUS_ALIAS_REFERENCE"
    rescue_signal.loc_name = "external_x"
    rescue_signal.inodfrom = 0
    rescue_signal.iconfrom = 2
    rescue_signal.inodto = 0
    rescue_signal.iconto = 0
    rescue_signal.pnodfrom = alias_reference.ID
    rescue_signal.pnodto = ""
    circuit.blksigs.append(rescue_signal)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(
        ValueError,
        match="Graphical DGS input has ambiguous root aliases",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


# Dynamic contract: tied graphical producers fail closed.
def test_graphical_macro_rejects_ambiguous_output_producers() -> None:
    """Reject two equally ranked producers for one public macro output.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    source_signal: BlkSig
    for source_signal in circuit.blksigs:
        if source_signal.ID == "MUL_TO_ROOT":
            source_signal.iconto = 0
            source_signal.pnodto = ""
        else:
            pass

    duplicate_multiplier: BlkMul = BlkMul()
    duplicate_multiplier.ID = "DUPLICATE_MULTIPLIER"
    duplicate_multiplier.loc_name = "Duplicate output producer"
    circuit.blkmuls.append(duplicate_multiplier)

    duplicate_input_zero: BlkSig = BlkSig()
    duplicate_input_zero.ID = "ROOT_TO_DUPLICATE_0"
    duplicate_input_zero.loc_name = "external_x"
    duplicate_input_zero.inodfrom = 0
    duplicate_input_zero.iconfrom = 1
    duplicate_input_zero.inodto = 0
    duplicate_input_zero.iconto = 0
    duplicate_input_zero.pnodfrom = "MACRO"
    duplicate_input_zero.pnodto = duplicate_multiplier.ID
    circuit.blksigs.append(duplicate_input_zero)

    duplicate_input_one: BlkSig = BlkSig()
    duplicate_input_one.ID = "ROOT_TO_DUPLICATE_1"
    duplicate_input_one.loc_name = "external_x"
    duplicate_input_one.inodfrom = 0
    duplicate_input_one.iconfrom = 1
    duplicate_input_one.inodto = 1
    duplicate_input_one.iconto = 0
    duplicate_input_one.pnodfrom = "MACRO"
    duplicate_input_one.pnodto = duplicate_multiplier.ID
    circuit.blksigs.append(duplicate_input_one)

    duplicate_output: BlkSig = BlkSig()
    duplicate_output.ID = "DUPLICATE_TO_ROOT"
    duplicate_output.loc_name = "public_y"
    duplicate_output.inodfrom = 2
    duplicate_output.iconfrom = 0
    duplicate_output.inodto = 0
    duplicate_output.iconto = 0
    duplicate_output.pnodfrom = duplicate_multiplier.ID
    duplicate_output.pnodto = ""
    circuit.blksigs.append(duplicate_output)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(
        ValueError,
        match="Graphical DGS macro output has ambiguous producers",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


# Dynamic contract: a reached BlkRef requires a typ_id resolvable by FID.
def test_graphical_macro_rejects_a_missing_nested_blkdef() -> None:
    """Reject an exact graphical child whose block definition is absent.

    :return: None.
    """
    fixture: tuple[DgsCircuit, ElmComp, ElmComp, BlkRef] = (
        _build_nested_graphical_parent_fixture()
    )
    circuit: DgsCircuit = fixture[0]
    root_element: ElmComp = fixture[1]
    source_reference: BlkRef = fixture[3]
    source_reference.typ_id = "MISSING_NESTED_BLOCK_DEFINITION"

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(
        ValueError,
        match="references missing BlkDef FID",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


# Dynamic contract: an unsupported typed graphical child cannot disappear.
def test_graphical_macro_rejects_an_unsupported_reached_child() -> None:
    """Reject a reached BlkSlot that cannot materialize as a runtime child.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    unsupported_slot: BlkSlot = BlkSlot()
    unsupported_slot.ID = "UNSUPPORTED_GRAPHICAL_SLOT"
    unsupported_slot.loc_name = "Unsupported graphical slot"
    circuit.blkslots.append(unsupported_slot)
    unsupported_signal: BlkSig = BlkSig()
    unsupported_signal.ID = "ROOT_TO_UNSUPPORTED_GRAPHICAL_SLOT"
    unsupported_signal.loc_name = "external_x"
    unsupported_signal.inodfrom = 0
    unsupported_signal.iconfrom = 1
    unsupported_signal.inodto = 0
    unsupported_signal.iconto = 1
    unsupported_signal.pnodfrom = "MACRO"
    unsupported_signal.pnodto = unsupported_slot.ID
    circuit.blksigs.append(unsupported_signal)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(
        ValueError,
        match="component contains an unsupported child type",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


# Dynamic contract: nested parameters do not select repeated names.
def test_graphical_macro_rejects_an_ambiguous_nested_instance_label() -> None:
    """Reject two nested parameter sources sharing one BlkRef label.

    :return: None.
    """
    circuit: DgsCircuit
    root_element: ElmComp
    nested_component: ElmComp
    child_reference: BlkRef
    (
        circuit,
        root_element,
        nested_component,
        child_reference,
    ) = _build_nested_graphical_parent_fixture()
    child_reference.cdisName = "Repeated nested instance"

    relation_index: int
    for relation_index in range(2):
        nested_slot: BlkSlot = BlkSlot()
        nested_slot.ID = f"NESTED_SLOT_{relation_index}"
        nested_slot.loc_name = child_reference.cdisName
        nested_slot.filtmod = "ElmDsl"
        nested_element: ElmDsl = ElmDsl()
        nested_element.ID = f"NESTED_ELEMENT_{relation_index}"
        nested_element.loc_name = f"Nested element {relation_index}"
        nested_element.typ_id = child_reference.typ_id
        nested_slot.element = nested_element.ID
        circuit.blkslots.append(nested_slot)
        circuit.elmdsls.append(nested_element)
        nested_component.pblk.append(nested_slot.ID)
        nested_component.pelm.append(nested_element.ID)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(
        ValueError,
        match="Graphical BlkRef instance label is ambiguous",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


# Dynamic contract: nested parameters require the same typ_id FID.
def test_graphical_macro_rejects_nested_parameters_from_another_blkdef() -> None:
    """Reject a named nested parameter source owned by another BlkDef FID.

    :return: None.
    """
    circuit: DgsCircuit
    root_element: ElmComp
    nested_component: ElmComp
    child_reference: BlkRef
    (
        circuit,
        root_element,
        nested_component,
        child_reference,
    ) = _build_nested_graphical_parent_fixture()
    child_reference.cdisName = "Mismatched nested instance"

    nested_slot: BlkSlot = BlkSlot()
    nested_slot.ID = "MISMATCHED_NESTED_SLOT"
    nested_slot.loc_name = child_reference.cdisName
    nested_slot.filtmod = "ElmDsl"
    nested_element: ElmDsl = ElmDsl()
    nested_element.ID = "MISMATCHED_NESTED_ELEMENT"
    nested_element.loc_name = "Mismatched nested element"
    nested_element.typ_id = "FRAME"
    nested_slot.element = nested_element.ID
    circuit.blkslots.append(nested_slot)
    circuit.elmdsls.append(nested_element)
    nested_component.pblk.append(nested_slot.ID)
    nested_component.pelm.append(nested_element.ID)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    with pytest.raises(
        ValueError,
        match="resolved parameters from a different BlkDef FID",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


def test_dgs_root_selection_does_not_require_a_model_specific_name() -> None:
    """Select the only valid document root without a hard-coded model name.

    :return: None.
    """
    root_result: DgsRootBlockResult = dgs_to_root_block(
        path=str(_get_graphical_parent_signal_binding_dgs_path()),
    )

    assert root_result.root_element.ID == "ROOT"
    assert root_result.root_element.loc_name == "Graphical root"
    assert root_result.root_element.typ_id == "FRAME"


def test_dgs_root_selection_rejects_distinct_resolvable_roots() -> None:
    """Reject an ambiguous document even when candidate sizes differ.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))

    alternate_frame: BlkDef = BlkDef()
    alternate_frame.ID = "ALTERNATE_FRAME"
    alternate_frame.loc_name = "Alternate frame"
    alternate_frame.inputs.append("alternate_x")
    alternate_frame.outputs.append("alternate_y")
    alternate_frame.outputs.append("alternate_z")
    circuit.blkdefs.append(alternate_frame)

    alternate_root: ElmComp = ElmComp()
    alternate_root.ID = "ALTERNATE_ROOT"
    alternate_root.loc_name = "Alternate root"
    alternate_root.typ_id = alternate_frame.ID
    circuit.elmcomps.append(alternate_root)

    parsed_blocks: dict[str, ParsedDgsBlockDefinition] = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)
    )
    with pytest.raises(
        ValueError,
        match="Several ElmComp roots match the available selectors",
    ):
        build_dgs_root_block_from_circuit(
            circuit=circuit,
            parsed_blocks=parsed_blocks,
            root_name=None,
        )


def test_dgs_direct_instances_reject_incomplete_and_ambiguous_relations() -> None:
    """Keep malformed source relations visible without executing them.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    parsed_blocks: dict[str, ParsedDgsBlockDefinition] = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)
    )
    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parsed_blocks,
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    graphical_indexes: DgsGraphicalIndexes = (
        build_dgs_graphical_indexes(circuit=circuit)
    )
    slot_id_value: str | None = root_element.pblk[0]
    element_id_value: str | None = root_element.pelm[0]
    assert slot_id_value is not None
    assert element_id_value is not None
    slot_id: str = slot_id_value
    element_id: str = element_id_value

    selected_counts: list[int] = list()
    relation_stage: int
    for relation_stage in range(3):
        if relation_stage == 0:
            # The extra pElm stays reportable, but cannot create a child.
            root_element.pelm.append(element_id)
        elif relation_stage == 1:
            # Reusing the slot makes both complete rows ambiguous.
            root_element.pblk.append(slot_id)
        else:
            # A non-resolving pblk cannot become valid through name fallback.
            root_element.pblk.clear()
            root_element.pblk.append("MISSING_SLOT")
            root_element.pelm.clear()
            root_element.pelm.append(element_id)

        entries: list[ElmCompInstanceEntry] = (
            extract_elmcomp_direct_instances(circuit, root_element)
        )
        selected_entries: list[ElmCompInstanceEntry] = (
            get_unambiguous_elmcomp_direct_instances(entries=entries)
        )
        with pytest.raises(
            ValueError,
            match="Direct ElmComp relations contain",
        ):
            build_direct_root_elmcomp_block(
                circuit=circuit,
                result=root_result,
                graphical_indexes=graphical_indexes,
            )
        if relation_stage == 0:
            assert len(entries) == 2
            assert entries[1].slot_id is None
            assert len(selected_entries) == 1
            assert selected_entries[0].slot_id == slot_id
        elif relation_stage == 1:
            assert len(entries) == 2
            assert len(selected_entries) == 0
        else:
            assert len(entries) == 1
            assert not entries[0].slot_reference_is_resolved
            assert len(selected_entries) == 0

        selected_counts.append(len(selected_entries))

    assert tuple(selected_counts) == (1, 0, 0)


# Dynamic contract: a duplicated BlkDef FID can never select the last record.
def test_dgs_block_definition_index_rejects_duplicate_fids() -> None:
    """Reject ambiguous block definitions before selecting a root type.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    source_definition: BlkDef = circuit.blkdefs[0]
    duplicate_definition: BlkDef = BlkDef()
    duplicate_definition.ID = source_definition.ID
    duplicate_definition.loc_name = "Duplicate block definition"
    circuit.blkdefs.append(duplicate_definition)

    with pytest.raises(
        ValueError,
        match="DGS BlkDef FID is duplicated",
    ):
        parse_dgs_block_definitions_from_circuit(circuit=circuit)


# Dynamic contract: an ambiguous pblk cannot resolve by list order.
def test_dgs_element_index_rejects_duplicate_blkslot_fids() -> None:
    """Reject an ambiguous exact slot relation before materialization.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    source_slot: BlkSlot = circuit.blkslots[0]
    duplicate_slot: BlkSlot = BlkSlot()
    duplicate_slot.ID = source_slot.ID
    duplicate_slot.loc_name = "Duplicate slot"
    circuit.blkslots.append(duplicate_slot)

    with pytest.raises(
        ValueError,
        match="DGS element FID is duplicated",
    ):
        extract_elmcomp_direct_instances(
            circuit=circuit,
            root_element=root_element,
        )


# Dynamic contract: an ambiguous pelm cannot resolve by list order.
def test_dgs_element_index_rejects_duplicate_pelm_fids() -> None:
    """Reject an ambiguous exact dynamic-instance relation.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    source_element: ElmDsl = circuit.elmdsls[0]
    duplicate_element: ElmDsl = ElmDsl()
    duplicate_element.ID = source_element.ID
    duplicate_element.loc_name = "Duplicate dynamic instance"
    circuit.elmdsls.append(duplicate_element)

    with pytest.raises(
        ValueError,
        match="DGS element FID is duplicated",
    ):
        extract_elmcomp_direct_instances(
            circuit=circuit,
            root_element=root_element,
        )


def test_dgs_direct_builder_rejects_a_missing_dynamic_blkdef() -> None:
    """Reject a resolved dynamic slot whose declared type cannot materialize.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    circuit.elmdsls[0].typ_id = "MISSING_BLOCK_DEFINITION"

    with pytest.raises(
        ValueError,
        match="references a missing parsed BlkDef",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


def test_dgs_direct_builder_rejects_a_physical_target_in_a_dynamic_slot() -> None:
    """Reject a resolved physical object where BlkSlot requires ElmDsl.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    physical_target: StaCubic = StaCubic()
    physical_target.ID = "PHYSICAL_SLOT_TARGET"
    physical_target.loc_name = "Physical slot target"
    circuit.stacubics.append(physical_target)
    root_element.pelm[0] = physical_target.ID
    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )

    with pytest.raises(
        ValueError,
        match="has no resolved ElmDsl or ElmComp instance",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


# Dynamic contract: ElmDsl cannot impersonate a registered physical class.
def test_dgs_direct_builder_requires_an_exact_slot_element_class() -> None:
    """Reject a generic dynamic container in a concrete equipment slot.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    dynamic_slot: BlkSlot = circuit.blkslots[0]
    dynamic_slot.filtmod = "ElmVsc*"

    with pytest.raises(
        ValueError,
        match="does not satisfy its typed BlkSlot filter",
    ):
        build_direct_root_elmcomp_block(
            circuit=circuit,
            result=root_result,
            graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
        )


# Dynamic contract: unregistered Elm roles retain their ElmDsl container.
def test_dgs_direct_builder_accepts_a_specialized_dynamic_role() -> None:
    """Accept an ElmDsl container for an unregistered specialized role.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    dynamic_element: ElmDsl = circuit.elmdsls[0]
    dynamic_definition: BlkDef | None = None
    candidate_definition: BlkDef
    for candidate_definition in circuit.blkdefs:
        if candidate_definition.ID == dynamic_element.typ_id:
            dynamic_definition = candidate_definition
        else:
            pass
    assert dynamic_definition is not None
    dynamic_definition.isMacro = 0
    dynamic_slot: BlkSlot = circuit.blkslots[0]
    dynamic_slot.filtmod = "ElmEpc*"

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    direct_result: DgsDirectRootBuildResult = build_direct_root_elmcomp_block(
        circuit=circuit,
        result=root_result,
        graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
    )

    assert direct_result.root_block is root_result.root_block
    assert len(direct_result.root_block.children) == 1
    assert direct_result.root_block.children[0].name == dynamic_definition.loc_name


# Dynamic contract: an empty specialized dynamic role stays unconnected (User Manual 30.2).
def test_dgs_direct_builder_leaves_an_empty_specialized_dynamic_role_unconnected() -> None:
    """Build a root whose specialized dynamic role is left empty, as PowerFactory allows.

    An empty Composite Model slot is legal whatever its filter (User Manual
    30.2); its inputs and outputs are simply not connected.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    dynamic_slot: BlkSlot = circuit.blkslots[0]
    dynamic_slot.filtmod = "ElmEpc*"
    root_element.pelm.clear()

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    direct_result: DgsDirectRootBuildResult = build_direct_root_elmcomp_block(
        circuit=circuit,
        result=root_result,
        graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
    )

    assert dynamic_slot.ID not in direct_result.child_block_by_slot_id


def test_direct_dynamic_import_rejects_partial_graphical_topology() -> None:
    """Do not register a root whose live graphical input has no producer.

    :return: None.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    destination: MultiCircuit = MultiCircuit()
    logger: Logger = Logger()

    conversion_result: DgsDynamicTemplateConversionResult = (
        convert_and_add_dgs_dynamic_templates_to_circuit(
            dgs_circuit=dgs_circuit,
            circuit=destination,
            target_domain=DynamicSimulationMode.RMS,
            logger=logger,
        )
    )
    templates_by_root_id: dict[str, RmsModelTemplate | EmtModelTemplate] = (
        conversion_result.templates_by_root_dgs_id
    )

    assert templates_by_root_id == dict()
    assert len(destination.rms_models) == 0
    assert any(
        entry.msg == "DGS dynamic root could not be materialized"
        and "unresolved live inputs" in str(entry.value)
        for entry in logger.entries
    )


def test_direct_dynamic_import_rejects_unsupported_root_syntax() -> None:
    """Do not register a root after any source statement failed to parse.

    :return: None.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(
        str(
            _get_complete_hvdc_vsc_dgs_path(
                file_name="hvdc_vsc_v1_complete_static_dynamic.dgs",
            )
        )
    )
    source_root: ElmComp = dgs_circuit.elmcomps[0]
    dgs_circuit.elmcomps = [source_root]
    root_definition: BlkDef | None = None
    candidate_definition: BlkDef
    for candidate_definition in dgs_circuit.blkdefs:
        if candidate_definition.ID == source_root.typ_id:
            root_definition = candidate_definition
        else:
            pass
    assert root_definition is not None
    root_definition.equations_raw.append("unsupported syntax")

    destination: MultiCircuit = MultiCircuit()
    logger: Logger = Logger()
    conversion_result: DgsDynamicTemplateConversionResult = (
        convert_and_add_dgs_dynamic_templates_to_circuit(
            dgs_circuit=dgs_circuit,
            circuit=destination,
            target_domain=DynamicSimulationMode.RMS,
            logger=logger,
        )
    )
    templates_by_root_id: dict[str, RmsModelTemplate | EmtModelTemplate] = (
        conversion_result.templates_by_root_dgs_id
    )

    assert templates_by_root_id == dict()
    assert len(destination.rms_models) == 0
    assert any(
        entry.msg == "DGS dynamic root could not be materialized"
        and "unsupported source statements" in str(entry.value)
        for entry in logger.entries
    )


# Dynamic contract: a supported root equation cannot be omitted either.
def test_direct_dynamic_import_rejects_supported_root_equations() -> None:
    """Reject supported equations instead of dropping them from the root shell.

    :return: None.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(
        str(
            _get_complete_hvdc_vsc_dgs_path(
                file_name="hvdc_vsc_v1_complete_static_dynamic.dgs",
            )
        )
    )
    source_root: ElmComp = dgs_circuit.elmcomps[0]
    dgs_circuit.elmcomps = [source_root]
    root_definition: BlkDef | None = None
    candidate_definition: BlkDef
    for candidate_definition in dgs_circuit.blkdefs:
        if candidate_definition.ID == source_root.typ_id:
            root_definition = candidate_definition
        else:
            pass
    assert root_definition is not None
    root_definition.equations_raw.append("synthetic_root_signal=1")

    destination: MultiCircuit = MultiCircuit()
    logger: Logger = Logger()
    conversion_result: DgsDynamicTemplateConversionResult = (
        convert_and_add_dgs_dynamic_templates_to_circuit(
            dgs_circuit=dgs_circuit,
            circuit=destination,
            target_domain=DynamicSimulationMode.RMS,
            logger=logger,
        )
    )
    templates_by_root_id: dict[str, RmsModelTemplate | EmtModelTemplate] = (
        conversion_result.templates_by_root_dgs_id
    )

    assert templates_by_root_id == dict()
    assert len(destination.rms_models) == 0
    assert any(
        entry.msg == "DGS dynamic root could not be materialized"
        and "purely structural frame" in str(entry.value)
        for entry in logger.entries
    )


# Dynamic contract: a root inequality cannot be lost in the shell either.
def test_direct_dynamic_import_rejects_root_parameter_limits() -> None:
    """Reject root inequalities that the structural shell cannot own.

    :return: None.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(
        str(
            _get_complete_hvdc_vsc_dgs_path(
                file_name="hvdc_vsc_v1_complete_static_dynamic.dgs",
            )
        )
    )
    source_root: ElmComp = dgs_circuit.elmcomps[0]
    dgs_circuit.elmcomps = [source_root]
    root_definition: BlkDef | None = None
    candidate_definition: BlkDef
    for candidate_definition in dgs_circuit.blkdefs:
        if candidate_definition.ID == source_root.typ_id:
            root_definition = candidate_definition
        else:
            pass
    assert root_definition is not None
    root_definition.internals.append("synthetic_internal")
    root_definition.equations_raw.append(
        "limfix(synthetic_internal)=[0,1]"
    )

    destination: MultiCircuit = MultiCircuit()
    logger: Logger = Logger()
    conversion_result: DgsDynamicTemplateConversionResult = (
        convert_and_add_dgs_dynamic_templates_to_circuit(
            dgs_circuit=dgs_circuit,
            circuit=destination,
            target_domain=DynamicSimulationMode.RMS,
            logger=logger,
        )
    )
    templates_by_root_id: dict[str, RmsModelTemplate | EmtModelTemplate] = (
        conversion_result.templates_by_root_dgs_id
    )

    assert templates_by_root_id == dict()
    assert len(destination.rms_models) == 0
    assert any(
        entry.msg == "DGS dynamic root could not be materialized"
        and "purely structural frame" in str(entry.value)
        for entry in logger.entries
    )


# Dynamic contract: non-executable root comments preserve the valid frame.
def test_structural_root_accepts_ignored_comment_statements() -> None:
    """Allow source comments that carry no executable root semantics.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    root_definition: BlkDef | None = None
    candidate_definition: BlkDef
    for candidate_definition in circuit.blkdefs:
        if candidate_definition.ID == root_element.typ_id:
            root_definition = candidate_definition
        else:
            pass
    assert root_definition is not None
    root_definition.equations_raw.append(
        "! Structural frame comment without runtime semantics"
    )

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )

    assert root_result.root_element is root_element
    assert root_result.root_block.children == list()


# Dynamic contract: overlapping names do not create implicit children.
def test_root_shell_does_not_materialize_signal_overlap_candidates() -> None:
    """Keep an unrelated BlkDef out of the exact direct-root hierarchy.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    root_definition: BlkDef | None = None
    candidate_definition: BlkDef
    for candidate_definition in circuit.blkdefs:
        if candidate_definition.ID == root_element.typ_id:
            root_definition = candidate_definition
        else:
            pass
    assert root_definition is not None
    assert len(root_definition.inputs) > 0

    overlap_definition: BlkDef = BlkDef()
    overlap_definition.ID = "UNRELATED_OVERLAP_BLOCK"
    overlap_definition.loc_name = "Unrelated overlap block"
    overlap_definition.inputs.append(root_definition.inputs[0])
    overlap_definition.outputs.append("unrelated_overlap_output")
    overlap_definition.equations_raw.append(
        f"unrelated_overlap_output={root_definition.inputs[0]}"
    )
    circuit.blkdefs.append(overlap_definition)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    retained_overlap: ParsedDgsBlockDefinition | None = (
        root_result.parsed_blocks.get(overlap_definition.ID, None)
    )

    assert retained_overlap is not None
    assert root_result.root_block.children == list()


def test_direct_dynamic_import_excludes_every_empty_or_duplicate_root_fid() -> None:
    """Never retain the first root when its supposedly exact FID is not unique.

    :return: None.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    source_root: ElmComp = dgs_circuit.elmcomps[0]

    duplicate_root: ElmComp = ElmComp()
    duplicate_root.ID = source_root.ID
    duplicate_root.loc_name = "Duplicate root"
    duplicate_root.typ_id = source_root.typ_id
    duplicate_root.pblk = list(source_root.pblk)
    duplicate_root.pelm = list(source_root.pelm)
    dgs_circuit.elmcomps.append(duplicate_root)

    empty_id_root: ElmComp = ElmComp()
    empty_id_root.loc_name = "Empty FID root"
    empty_id_root.typ_id = source_root.typ_id
    dgs_circuit.elmcomps.append(empty_id_root)

    destination: MultiCircuit = MultiCircuit()
    logger: Logger = Logger()
    conversion_result: DgsDynamicTemplateConversionResult = (
        convert_and_add_dgs_dynamic_templates_to_circuit(
            dgs_circuit=dgs_circuit,
            circuit=destination,
            target_domain=DynamicSimulationMode.RMS,
            logger=logger,
        )
    )
    templates_by_root_id: dict[str, RmsModelTemplate | EmtModelTemplate] = (
        conversion_result.templates_by_root_dgs_id
    )
    logged_messages: set[str] = set()
    log_entry: LogEntry
    for log_entry in logger.entries:
        logged_messages.add(log_entry.msg)

    assert templates_by_root_id == dict()
    assert len(destination.rms_models) == 0
    assert "DGS dynamic root skipped because its FID is empty" in logged_messages
    assert (
        "DGS dynamic roots skipped because their FID is duplicated"
        in logged_messages
    )


def test_rms_measurement_binding_rejects_a_duplicated_root_with_a_shell() -> None:
    """Do not treat a prepared standard RMS shell as DGS activation evidence.

    :return: None.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(
        str(
            _get_complete_hvdc_vsc_dgs_path(
                file_name="hvdc_vsc_v1_complete_static_dynamic.dgs",
            )
        )
    )
    source_root: ElmComp = dgs_circuit.elmcomps[0]
    duplicate_root: ElmComp = ElmComp()
    duplicate_root.ID = source_root.ID
    duplicate_root.loc_name = "Duplicate measurement root"
    duplicate_root.typ_id = source_root.typ_id
    duplicate_root.pblk = list(source_root.pblk)
    duplicate_root.pelm = list(source_root.pelm)
    dgs_circuit.elmcomps = [source_root, duplicate_root]

    host_source_id: str | None = None
    direct_entry: ElmCompInstanceEntry
    for direct_entry in extract_elmcomp_direct_instances(
            circuit=dgs_circuit,
            root_element=source_root,
    ):
        if direct_entry.element_kind == "ElmVscmono":
            host_source_id = direct_entry.element_id
        else:
            pass
    assert host_source_id is not None

    destination: MultiCircuit = MultiCircuit()
    dc_bus: Bus = Bus(name="DC host bus", is_dc=True)
    ac_bus: Bus = Bus(name="AC host bus")
    destination.add_bus(dc_bus)
    destination.add_bus(ac_bus)
    physical_host: VSC = VSC(
        bus_from=dc_bus,
        bus_to=ac_bus,
        idtag=host_source_id,
    )
    destination.add_vsc(physical_host)
    prepared_shell: RmsModelTemplate = RmsModelTemplate(
        name="Prepared standard shell",
    )
    shell_var: Var = Var(name="shell_signal")
    prepared_shell.block = Block(
        name="Prepared standard shell",
        algebraic_vars=[shell_var],
        algebraic_eqs=[shell_var],
    )
    physical_host.rms_template = prepared_shell

    report: DgsRmsMeasurementBindingReport = bind_dgs_rms_measurements(
        circuit=destination,
        dgs_circuit=dgs_circuit,
        templates_by_root_dgs_id={source_root.ID: prepared_shell},
        child_blocks_by_root_and_slot_id=dict(),
        logger=Logger(),
    )

    assert report.get_bound_meter_count() == 0
    assert report.get_bound_signal_count() == 0
    assert report.get_skipped_meter_count() == 0
    assert report.get_failed_meter_count() == 0


def test_rms_measurement_binding_reports_active_meter_without_host() -> None:
    """Fail closed when an active supported root has no resolvable RMS host.

    :return: None.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(
        str(
            _get_complete_hvdc_vsc_dgs_path(
                file_name="hvdc_vsc_v1_complete_static_dynamic.dgs",
            )
        )
    )
    source_root: ElmComp | None = None
    candidate_root: ElmComp
    for candidate_root in dgs_circuit.elmcomps:
        candidate_entry: ElmCompInstanceEntry
        for candidate_entry in extract_elmcomp_direct_instances(
                circuit=dgs_circuit,
                root_element=candidate_root,
        ):
            if (
                    source_root is None
                    and int(candidate_root.outserv) == 0
                    and candidate_entry.element_kind in (
                        "StaVmea",
                        "StaImea",
                        "StaPqmea",
                        "ElmPhi",
                    )
            ):
                source_root = candidate_root
            else:
                pass
    assert source_root is not None
    prepared_template: RmsModelTemplate = RmsModelTemplate(
        name="Registered active controller",
    )
    templates_by_root_id: dict[str, RmsModelTemplate] = dict()
    templates_by_root_id[source_root.ID] = prepared_template
    logger: Logger = Logger()

    report: DgsRmsMeasurementBindingReport = bind_dgs_rms_measurements(
        circuit=MultiCircuit(),
        dgs_circuit=dgs_circuit,
        templates_by_root_dgs_id=templates_by_root_id,
        child_blocks_by_root_and_slot_id=dict(),
        logger=logger,
    )
    host_warnings: list[LogEntry] = list(
        entry
        for entry in logger.entries
        if entry.msg == "DGS native RMS meter has no unique active host"
    )

    assert source_root.outserv == 0
    assert report.get_bound_meter_count() == 0
    assert report.get_bound_signal_count() == 0
    assert report.get_failed_meter_count() > 0
    assert len(host_warnings) == report.get_failed_meter_count()


def test_dgs_dynamic_import_catalog_reports_live_graphical_binding_gaps() -> None:
    """Carry typed parent-binding diagnostics into the DGS import catalogue.

    :return: None.
    """
    bundle: DynamicModelImportBundle
    bundle_logger: Logger
    bundle, bundle_logger = build_dgs_dynamic_model_import_bundle(
        dgs_path=str(_get_graphical_parent_signal_binding_dgs_path()),
    )
    graphical_entries: list[DynamicModelImportEntry] = [
        entry
        for entry in bundle.get_entries()
        if entry.get_display_name() == "Graphical parent"
    ]
    assert len(graphical_entries) == 1
    graphical_entry: DynamicModelImportEntry = graphical_entries[0]
    source_block: Block | None = graphical_entry.get_source_block()
    topology_warnings: list[LogEntry] = [
        entry
        for entry in bundle_logger.entries
        if entry.msg == "DGS graphical operator topology incomplete"
    ]

    assert source_block is not None
    assert graphical_entry.get_persistence_spec() is None
    assert len(topology_warnings) == 1
    assert "routed_internal" in str(topology_warnings[0].value)
    assert "blank_internal" not in str(topology_warnings[0].value)


def test_dgs_block_definition_builds_one_self_contained_symbolic_block() -> None:
    """Materialize the equation declared by a versioned DGS block definition."""

    dgs_path: Path = _get_dynamic_gain_block_dgs_path()
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(path=str(dgs_path))
    parsed_blocks: dict[str, ParsedDgsBlockDefinition] = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)
    )
    parsed_gain_block = parsed_blocks["2"]
    block: Block = build_standalone_blkdef_block_from_parsed_block(
        parsed_block=parsed_gain_block,
    )

    assert parsed_gain_block.unsupported_lines == []
    assert block.name == "Dynamic gain"
    assert tuple(var.name for var in block.in_vars) == ("u",)
    assert tuple(var.name for var in block.out_vars) == ("y",)
    assert len(block.algebraic_eqs) == 1
    parameter_vars: list[Var] = list(block.event_dict)
    assert len(parameter_vars) == 1
    parameter_var: Var = parameter_vars[0]
    assert parameter_var.name == "Dynamic gain__K"
    equation_bindings: dict[str, float] = dict()
    equation_bindings[block.in_vars[0].name] = 3.0
    equation_bindings[block.out_vars[0].name] = 6.0
    equation_bindings[parameter_var.name] = 2.0
    assert block.algebraic_eqs[0].eval(**equation_bindings) == 0.0


def test_dgs_block_definition_preserves_open_and_closed_limfix_bounds() -> None:
    """Keep infinite endpoints and bracket semantics as canonical inequalities.

    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "PARAMETER_LIMIT_DEFINITION"
    definition.loc_name = "Parameter limits"
    definition.params = [
        "Kp",
        "Ki",
        "upper_closed",
        "upper_open",
        "bounded",
        "expression_bound",
        "Kmin",
    ]
    definition.equations_raw = [
        "limfix(Kp)=(0,)",
        "limfix(Ki)=[0,)",
        "limfix(upper_closed)=(,0]",
        "limfix(upper_open)=(,0)",
        "limfix(bounded)=[0,1]",
        "limfix(expression_bound)=[max(0,Kmin),)",
    ]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )
    block: Block = build_standalone_blkdef_block_from_parsed_block(
        parsed_block=parsed,
    )
    constraints: list[Comparison] = [
        constraint
        for constraint in block.inequalities
        if isinstance(constraint, Comparison)
    ]

    assert parsed.unsupported_lines == []
    assert len(constraints) == 7
    assert [constraint.op for constraint in constraints] == [
        CmpOp.GT,
        CmpOp.GE,
        CmpOp.LE,
        CmpOp.LT,
        CmpOp.GE,
        CmpOp.LE,
        CmpOp.GE,
    ]
    assert [constraint.lhs.name for constraint in constraints] == [
        "Parameter limits__Kp",
        "Parameter limits__Ki",
        "Parameter limits__upper_closed",
        "Parameter limits__upper_open",
        "Parameter limits__bounded",
        "Parameter limits__bounded",
        "Parameter limits__expression_bound",
    ]
    assert constraints[0].rhs.eval() == 0.0
    assert constraints[1].rhs.eval() == 0.0
    assert constraints[2].rhs.eval() == 0.0
    assert constraints[3].rhs.eval() == 0.0


@pytest.mark.parametrize(
    "statement",
    (
        "limfix(unknown)=(0,)",
        "limfix(Kp)=(,)",
        "limfix(Kp)={0,1]",
        "limfix(Kp)=[0,1,2]",
        "limfix(Kp)=[Kp<1,)",
    ),
)
def test_dgs_block_definition_rejects_malformed_limfix_bounds(
        statement: str,
) -> None:
    """Reject ambiguous parameter domains instead of ignoring their text.

    :param statement: Invalid PowerFactory parameter-domain declaration.
    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "INVALID_PARAMETER_LIMIT_DEFINITION"
    definition.loc_name = "Invalid parameter limits"
    definition.params = ["Kp"]
    definition.equations_raw = [statement]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )

    assert parsed.unsupported_lines == [statement]


def test_dgs_boolean_helpers_accept_comparisons_only_as_conditions() -> None:
    """Convert nested selector conditions without weakening numeric positions.

    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "BOOLEAN_HELPER_DEFINITION"
    definition.loc_name = "Boolean helpers"
    definition.inputs = ["u1", "flag"]
    definition.outputs = ["selected", "fixed"]
    definition.params = ["u_db_low", "high_value", "low_value"]
    definition.equations_raw = [
        "selected=select(u1<(1+u_db_low),high_value,low_value)",
        "fixed=selfix(u1<(1+u_db_low),high_value,low_value)",
        "latched=flipflop("
        "{selfix(high_value,u1<low_value,u1>high_value).and.flag},"
        "{.not.selfix(low_value,u1>high_value,u1<low_value)}"
        ")",
    ]
    definition.outputs.append("latched")
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )
    block: Block = build_standalone_blkdef_block_from_parsed_block(
        parsed_block=parsed,
    )

    assert parsed.unsupported_lines == []
    assert len(block.algebraic_eqs) == 3
    assert len(block.procedural_logic) == 5


def test_dgs_selector_uses_powerfactory_half_threshold() -> None:
    """Select argument two only above PowerFactory's 0.5 threshold.

    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "POWERFACTORY_SELECTOR_HALF_THRESHOLD"
    definition.loc_name = "PowerFactory selector half threshold"
    definition.outputs = ["below_threshold", "above_threshold"]
    definition.equations_raw = [
        "below_threshold=select(0.25,11,22)",
        "above_threshold=select(0.75,11,22)",
    ]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )

    assert parsed.unsupported_lines == []
    assert isinstance(parsed.algebraic_rhs["below_threshold"], Const)
    assert isinstance(parsed.algebraic_rhs["above_threshold"], Const)
    assert parsed.algebraic_rhs["below_threshold"].value == 22.0
    assert parsed.algebraic_rhs["above_threshold"].value == 11.0


def test_dgs_numeric_helper_rejects_a_comparison_argument() -> None:
    """Fail closed when a boolean comparison occupies a numeric helper slot.

    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "INVALID_BOOLEAN_POSITION_DEFINITION"
    definition.loc_name = "Invalid boolean position"
    definition.inputs = ["u1"]
    definition.outputs = ["result"]
    definition.params = ["limit"]
    definition.equations_raw = ["result=max(u1<limit,limit)"]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )

    assert parsed.unsupported_lines == definition.equations_raw


def test_dgs_conditional_diagnostics_are_canonical_and_round_trip() -> None:
    """Preserve ``output`` and ``outfix`` as inert typed block declarations.

    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "CONDITIONAL_DIAGNOSTIC_DEFINITION"
    definition.loc_name = "Conditional diagnostics"
    definition.inputs = ["enabled", "measured"]
    definition.params = ["limit"]
    definition.equations_raw = [
        "output(enabled.and.{measured>limit},'Limit exceeded, controller active!')",
        "outfix(measured<0.0,'Measured value has wrong polarity.')",
    ]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )
    block: Block = build_standalone_blkdef_block_from_parsed_block(
        parsed_block=parsed,
    )
    diagnostics: list[ConditionalDiagnosticLogic] = [
        entry
        for entry in block.procedural_logic
        if isinstance(entry, ConditionalDiagnosticLogic)
    ]
    rebuilt_block: Block = roundtrip_block(block, procedural_logic_codec=ProceduralLogicCodec())
    rebuilt_diagnostics: list[ConditionalDiagnosticLogic] = [
        entry
        for entry in rebuilt_block.procedural_logic
        if isinstance(entry, ConditionalDiagnosticLogic)
    ]

    assert parsed.unsupported_lines == []
    assert len(diagnostics) == 2
    assert [entry.initialization_only for entry in diagnostics] == [False, True]
    assert [entry.message for entry in diagnostics] == [
        "Limit exceeded, controller active!",
        "Measured value has wrong polarity.",
    ]
    assert len(rebuilt_diagnostics) == 2
    assert [entry.initialization_only for entry in rebuilt_diagnostics] == [
        False,
        True,
    ]
    assert [entry.message for entry in rebuilt_diagnostics] == [
        "Limit exceeded, controller active!",
        "Measured value has wrong polarity.",
    ]


@pytest.mark.parametrize(
    "statement",
    (
        "event(enabled,trigger,'create=EvtSwitch target=CB1 "
        "name=Open_CB1 i_switch=0 dtime=delay')",
        "event(enabled,trigger)",
        "event(enabled,trigger,configuration_symbol)",
        "event(enabled,trigger,'')",
    ),
)
def test_dgs_external_event_fails_closed_without_runtime_actuation(
        statement: str,
) -> None:
    """Reject every event until its switch action can execute at runtime.

    :param statement: External event declaration lacking canonical actuation.
    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "INVALID_EXTERNAL_EVENT_DEFINITION"
    definition.loc_name = "Invalid external event"
    definition.inputs = ["enabled", "trigger", "configuration_symbol"]
    definition.equations_raw = [statement]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )

    assert parsed.unsupported_lines == [statement]


@pytest.mark.parametrize(
    "statement",
    (
        "output(enabled)",
        "output(enabled,message_symbol)",
        "output(enabled,'message','extra')",
        "outfix(,'message')",
    ),
)
def test_dgs_conditional_diagnostics_reject_ambiguous_surfaces(
        statement: str,
) -> None:
    """Fail closed for unsupported diagnostic arity or nonliteral messages.

    :param statement: Malformed diagnostic declaration.
    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "INVALID_CONDITIONAL_DIAGNOSTIC_DEFINITION"
    definition.loc_name = "Invalid conditional diagnostic"
    definition.inputs = ["enabled", "message_symbol"]
    definition.equations_raw = [statement]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )

    assert parsed.unsupported_lines == [statement]


def test_dgs_bracket_unit_metadata_preserves_exact_known_symbol_unit() -> None:
    """Retain the exact PowerFactory ``[symbol]='unit'`` declaration.

    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "BRACKET_UNIT_METADATA_DEFINITION"
    definition.loc_name = "Bracket unit metadata"
    definition.internals = ["theta1"]
    definition.equations_raw = ["[theta1]='rad'"]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )

    assert parsed.unsupported_lines == []
    assert len(parsed.variable_units) == 1
    assert parsed.variable_units[0].symbol_name == "theta1"
    assert parsed.variable_units[0].unit_text == "rad"


def test_dgs_bracket_unit_metadata_rejects_an_unknown_symbol() -> None:
    """Fail closed when bracket unit metadata names no declared block symbol.

    :return: None.
    """
    statement: str = "[unknown]='rad'"
    definition: BlkDef = BlkDef()
    definition.ID = "UNKNOWN_BRACKET_UNIT_METADATA_DEFINITION"
    definition.loc_name = "Unknown bracket unit metadata"
    definition.equations_raw = [statement]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )

    assert parsed.unsupported_lines == [statement]


def test_dgs_equation_continuation_preserves_one_nested_expression() -> None:
    """Join exact ``;&`` continuation markers before splitting statements.

    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "CONTINUED_EXPRESSION_DEFINITION"
    definition.loc_name = "Continued expression"
    definition.inputs = ["trip", "trigger", "voltage", "power"]
    definition.outputs = ["result"]
    definition.params = ["minimum"]
    definition.equations_raw = [
        "result=select(trip,minimum,; &"
        " select(trigger,sqr(voltage)/max(abs(power),0.000001),minimum))"
    ]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )

    assert parsed.unsupported_lines == []
    assert "result" in parsed.algebraic_rhs


def test_dgs_equation_continuation_discards_interleaved_comments() -> None:
    """Join a continued expression across bounded PowerFactory comments.

    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "COMMENTED_CONTINUED_EXPRESSION_DEFINITION"
    definition.loc_name = "Commented continued expression"
    definition.inputs = ["trip", "trigger", "voltage", "power"]
    definition.outputs = ["result"]
    definition.params = ["minimum"]
    definition.equations_raw = [
        "result=select(trip,minimum, ! first branch",
        "& select(trigger,sqr(voltage)/max(abs(power),0.000001),"
        " ! second branch",
        "! exported note",
        "& minimum))",
    ]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )

    assert parsed.unsupported_lines == []
    assert "result" in parsed.algebraic_rhs


def test_dgs_inline_comment_keeps_its_semicolons_as_comment_text() -> None:
    """Treat a semicolon inside an inline ``!`` comment as comment text.

    The GB REGC_C definition exports ``limfix`` rows whose comments contain a
    semicolon; DSL comments run to the end of the line, so nothing after the
    marker may become a statement.

    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "SEMICOLON_COMMENT_DEFINITION"
    definition.loc_name = "Semicolon comment"
    definition.inputs = ["u"]
    definition.outputs = ["y"]
    definition.params = ["rrpwr", "Te"]
    definition.equations_raw = [
        "y = rrpwr*u",
        "limfix(rrpwr)    = (0,)          ! rrpwr > 0; typical: 1-20",
        "limfix(Te)       = (0.0,0.02]    ! 0.0 < Te <= 0.02; note: Te has to be larger than zero",
        "vardef(y) = 'p.u.';'Output; scaled'",
    ]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )

    assert parsed.unsupported_lines == []
    assert "y" in parsed.algebraic_rhs


def test_dgs_blkslot_preserves_filter_after_quoted_semicolons() -> None:
    """Keep typed slot columns aligned after quoted signal declarations.

    :return: None.
    """
    dgs_path: Path = _get_complete_hvdc_vsc_dgs_path(
        file_name="hvdc_vsc_v3_complete_static_dynamic.dgs",
    )
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(path=str(dgs_path))
    island_control_slot: BlkSlot | None = None
    candidate_slot: BlkSlot
    for candidate_slot in circuit.blkslots:
        if candidate_slot.ID == "186":
            island_control_slot = candidate_slot
        else:
            pass

    assert island_control_slot is not None
    assert island_control_slot.element is None
    assert island_control_slot.filtmod == "ElmV_f*"
    assert "uac_loc" in island_control_slot.inputs


def test_dgs_runtime_limits_become_continuous_diagnostics() -> None:
    """Preserve ``limits`` as runtime violation declarations, not constraints.

    :return: None.
    """
    statement: str = "limits(enabled)=[0,1]"
    definition: BlkDef = BlkDef()
    definition.ID = "RUNTIME_LIMIT_DEFINITION"
    definition.loc_name = "Runtime limit"
    definition.inputs = ["enabled"]
    definition.equations_raw = [statement]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )
    diagnostics: list[ConditionalDiagnosticLogic] = [
        entry
        for entry in parsed.procedural_logic
        if isinstance(entry, ConditionalDiagnosticLogic)
    ]
    diagnostic_conditions: list[Comparison] = [
        entry.condition_expr
        for entry in diagnostics
        if isinstance(entry.condition_expr, Comparison)
    ]

    assert parsed.unsupported_lines == []
    assert parsed.parameter_limits == []
    assert len(diagnostics) == 2
    assert len(diagnostic_conditions) == 2
    assert [condition.op for condition in diagnostic_conditions] == [
        CmpOp.LT,
        CmpOp.GT,
    ]
    assert [entry.message for entry in diagnostics] == [statement, statement]
    assert [entry.initialization_only for entry in diagnostics] == [
        False,
        False,
    ]


def test_dgs_modulo_and_variadic_extrema_preserve_numeric_semantics() -> None:
    """Materialize documented modulo and multi-operand extrema expressions.

    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "MODULO_VARIADIC_EXTREMA_DEFINITION"
    definition.loc_name = "modulo_variadic_extrema"
    definition.inputs = ["angle"]
    definition.outputs = ["wrapped", "limited"]
    definition.equations_raw = [
        "wrapped=modulo(angle+pi(),twopi())-pi()",
        "limited=min(4.0,max(-2.0,angle,1.0),3.0)",
    ]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )
    wrapped_expr: Expr = parsed.algebraic_rhs["wrapped"]
    limited_expr: Expr = parsed.algebraic_rhs["limited"]
    angle_name: str = parsed.symbol_table["angle"].name

    assert parsed.unsupported_lines == []
    assert angle_name == "angle"
    assert wrapped_expr.eval(angle=-1.5 * math.pi) == pytest.approx(
        0.5 * math.pi,
    )
    assert limited_expr.eval(angle=-3.0) == 1.0
    assert limited_expr.eval(angle=5.0) == 3.0


def test_dgs_not_equal_is_supported_inside_a_selector_condition() -> None:
    """Parse PowerFactory ``<>`` only through its declared boolean context.

    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "NOT_EQUAL_SELECTOR_DEFINITION"
    definition.loc_name = "Not equal selector"
    definition.inputs = ["T1", "T2", "selected", "alternate"]
    definition.outputs = ["result"]
    definition.equations_raw = [
        "result=select(T1-T2<>0.and.T2<>0,selected,alternate)"
    ]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )

    assert parsed.unsupported_lines == []


def _build_single_definition_block(
        inputs: list[str],
        outputs: list[str],
        states: list[str],
        equations: list[str],
) -> Block:
    """Build one DSL definition without a graphical context.

    :param inputs: Input names.
    :param outputs: Output names.
    :param states: State names.
    :param equations: DSL statements.
    :return: Materialized block.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "KEYWORD_DEFINITION"
    definition.loc_name = "LPF"
    definition.inputs = inputs
    definition.outputs = outputs
    definition.states = states
    definition.equations_raw = equations
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)
    parsed: dict[str, ParsedDgsBlockDefinition] = parse_dgs_block_definitions_from_circuit(circuit=circuit)
    return _build_block_from_parsed(parsed[definition.ID], dict())


def _evaluate_by_local_name(expression: Expr, values: dict[str, float]) -> float:
    """Evaluate an expression with values keyed by the local DSL name of each variable.

    :param expression: Expression to evaluate.
    :param values: Values by local name.
    :return: Expression value.
    """
    return expression.eval_uid({var.uid: values[var.name.rsplit("__", 1)[-1]] for var in expression.get_vars()})


@pytest.mark.parametrize("name", [name for name in keyword.kwlist if name not in ("and", "or", "not")])
def test_dgs_keyword_symbol_parses_like_any_other_name(name: str) -> None:
    """Parse a DSL symbol spelled as a Python keyword exactly as the same symbol renamed.

    T3T4 DFIG low-pass filters write ``x.=(in-x)/T`` and their turbines
    ``lambda=w_turbine*K_speed/wind_speed``.

    :param name: Python keyword used as a DSL input name.
    :return: None.
    """
    keyword_block: Block = _build_single_definition_block(
        inputs=[name], outputs=["y"], states=["x"],
        equations=[f"x.=({name}-x)/0.1", f"y=2*{name}+x"],
    )
    renamed_block: Block = _build_single_definition_block(
        inputs=["u"], outputs=["y"], states=["x"],
        equations=["x.=(u-x)/0.1", "y=2*u+x"],
    )

    keyword_eqs: list[Expr] = keyword_block.state_eqs + keyword_block.algebraic_eqs
    renamed_eqs: list[Expr] = renamed_block.state_eqs + renamed_block.algebraic_eqs
    assert len(keyword_eqs) == len(renamed_eqs) == 2
    for keyword_eq, renamed_eq in zip(keyword_eqs, renamed_eqs):
        assert _evaluate_by_local_name(keyword_eq, {name: 0.3, "x": 0.1, "y": 0.7}) == pytest.approx(
            _evaluate_by_local_name(renamed_eq, {"u": 0.3, "x": 0.1, "y": 0.7}))


def test_dgs_keyword_symbol_is_renamed_only_as_a_whole_word() -> None:
    """Keep functions and longer names that contain a keyword symbol unchanged.

    T3T4 DFIG definitions declare ``in1`` to ``in5`` next to ``in``.

    :return: None.
    """
    block: Block = _build_single_definition_block(
        inputs=["in", "x_in", "in1"], outputs=["y"], states=[],
        equations=["y=sin(in)+x_in+in1"],
    )

    assert _evaluate_by_local_name(block.algebraic_eqs[0],
                                   {"in": 0.3, "x_in": 0.5, "in1": 0.25, "y": 0.0}) == pytest.approx(
        -(math.sin(0.3) + 0.5 + 0.25))


def test_dgs_undeclared_keyword_variable_is_read_by_a_later_statement() -> None:
    """Read an undeclared helper spelled as a Python keyword after the statement that computes it.

    :return: None.
    """
    block: Block = _build_single_definition_block(
        inputs=["w"], outputs=["y"], states=[],
        equations=["lambda=2*w", "y=lambda+1"],
    )

    values: dict[str, float] = {"w": 0.25, "lambda": 0.5, "y": 1.5}
    assert sorted(var.name.rsplit("__", 1)[-1] for var in block.algebraic_vars) == ["lambda", "y"]
    assert all(_evaluate_by_local_name(eq, values) == pytest.approx(0.0) for eq in block.algebraic_eqs)


def test_dgs_keyword_symbol_registered_after_construction_is_parsed() -> None:
    """Parse a keyword symbol registered on the parser after its construction.

    The support report registers a statement left-hand side that the symbol
    table does not declare yet.

    :return: None.
    """
    parser: DgsExpressionParser = DgsExpressionParser(symbol_table=dict(), block_name="LPF")
    tip_speed: Var = Var(name="LPF__lambda")
    parser.register_symbol(original_name="lambda", variable=tip_speed)

    expression = parser.parse("lambda+1")
    assert set(var.uid for var in expression.get_vars()) == {tip_speed.uid}


@pytest.mark.parametrize("names", [["in", "in_symbol", "u"], ["in_symbol", "in", "u"]])
def test_dgs_keyword_symbol_sharing_a_parser_name_resolves_each_symbol(names: list[str]) -> None:
    """Resolve a keyword symbol and a symbol spelled like its parser alias to their own variables.

    :param names: Symbol names in declaration order.
    :return: None.
    """
    parser: DgsExpressionParser = DgsExpressionParser(
        symbol_table={name: Var(name=f"LPF__{name}") for name in names}, block_name="LPF")

    assert [var.name for var in parser.parse("in+1").get_vars()] == ["LPF__in"]
    assert [var.name for var in parser.parse("in_symbol+1").get_vars()] == ["LPF__in_symbol"]
    assert [var.name for var in parser.parse("u+1").get_vars()] == ["LPF__u"]


def test_dgs_keyword_symbol_registered_twice_keeps_its_alias() -> None:
    """Keep one parser alias when a keyword symbol is registered again.

    :return: None.
    """
    parser: DgsExpressionParser = DgsExpressionParser(
        symbol_table={"in_symbol": Var(name="LPF__in_symbol")}, block_name="LPF")
    parser.register_symbol(original_name="in", variable=Var(name="LPF__in"))
    parser.register_symbol(original_name="in", variable=Var(name="LPF__in"))

    assert [var.name for var in parser.parse("in+1").get_vars()] == ["LPF__in"]
    assert [var.name for var in parser.parse("in_symbol+1").get_vars()] == ["LPF__in_symbol"]


def test_dgs_keyword_output_is_computed_by_its_equation() -> None:
    """Compute a DSL output spelled as a Python keyword from its own statement.

    :return: None.
    """
    block: Block = _build_single_definition_block(
        inputs=["w"], outputs=["lambda"], states=[],
        equations=["lambda=2*w"],
    )

    assert [var.name.rsplit("__", 1)[-1] for var in block.algebraic_vars] == ["lambda"]
    assert _evaluate_by_local_name(block.algebraic_eqs[0], {"w": 0.25, "lambda": 0.5}) == pytest.approx(0.0)


def test_dgs_inactive_selector_division_has_finite_value_and_derivative() -> None:
    """Preserve lazy branch semantics when a bypassed time constant is zero."""
    definition: BlkDef = BlkDef()
    definition.ID = "ZERO_TIME_CONSTANT_SELECTOR_DEFINITION"
    definition.loc_name = "Zero time constant selector"
    definition.inputs = ["T", "source"]
    definition.outputs = ["result"]
    definition.equations_raw = [
        "result=select(T>0,source/T,0.0)",
    ]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)[definition.ID]
    )
    result_expression: Expr = parsed.algebraic_rhs["result"]
    selector_var: Var = next(iter(parsed.mode_dict))
    time_constant: Var = parsed.symbol_table["T"]
    source: Var = parsed.symbol_table["source"]
    bindings: dict[int, float] = {
        selector_var.uid: 0.0,
        time_constant.uid: 0.0,
        source.uid: 2.0,
    }

    assert result_expression.eval_uid(bindings) == 0.0
    assert result_expression.diff(source).eval_uid(bindings) == 0.0


def test_dgs_network_mode_helpers_use_the_explicit_target_domain() -> None:
    """Resolve ``rms()`` and ``balanced()`` from RMS or EMT import context.

    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "NETWORK_MODE_HELPER_DEFINITION"
    definition.loc_name = "Network mode helpers"
    definition.outputs = ["balanced_result", "rms_result"]
    definition.equations_raw = [
        "balanced_result=selfix(balanced(),1.0,0.0)",
        "rms_result=selfix(rms(),1.0,0.0)",
    ]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)

    rms_parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(
            circuit=circuit,
            simulation_domain=DynamicSimulationMode.RMS,
        )[definition.ID]
    )
    emt_parsed: ParsedDgsBlockDefinition = (
        parse_dgs_block_definitions_from_circuit(
            circuit=circuit,
            simulation_domain=DynamicSimulationMode.EMT,
        )[definition.ID]
    )

    assert rms_parsed.unsupported_lines == []
    assert emt_parsed.unsupported_lines == []
    assert rms_parsed.algebraic_rhs["balanced_result"].eval() == 1.0
    assert rms_parsed.algebraic_rhs["rms_result"].eval() == 1.0
    assert emt_parsed.algebraic_rhs["balanced_result"].eval() == 0.0
    assert emt_parsed.algebraic_rhs["rms_result"].eval() == 0.0


def test_dgs_block_definition_rejects_unsupported_syntax() -> None:
    """Reject a partial template when one DGS equation cannot be represented."""

    dgs_path: Path = _get_dynamic_gain_block_dgs_path()
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(path=str(dgs_path))
    parsed_blocks: dict[str, ParsedDgsBlockDefinition] = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)
    )

    with pytest.raises(
        UnsupportedDgsExpression,
        match="Unsupported dynamic block.*unsupported syntax",
    ):
        build_standalone_blkdef_block_from_parsed_block(
            parsed_block=parsed_blocks["3"],
        )


def test_dynamic_template_fingerprint_uses_declarative_block_identity() -> None:
    """Fingerprint a final block without rendering or executing Python source."""

    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(path=str(_get_dynamic_gain_block_dgs_path()))
    parsed_blocks: dict[str, ParsedDgsBlockDefinition] = (
        parse_dgs_block_definitions_from_circuit(circuit=circuit)
    )
    source_block: Block = build_standalone_blkdef_block_from_parsed_block(
        parsed_block=parsed_blocks["2"],
    )
    rms_template: RmsModelTemplate = RmsModelTemplate(name="First display name")
    rms_template.block = source_block
    first_fingerprint: str | None = build_dynamic_import_template_fingerprint(
        rms_template
    )
    rms_template.name = "Second display name"
    second_fingerprint: str | None = build_dynamic_import_template_fingerprint(
        rms_template
    )
    emt_template: EmtModelTemplate = EmtModelTemplate(name="Second display name")
    emt_template.block = source_block
    emt_fingerprint: str | None = build_dynamic_import_template_fingerprint(
        emt_template
    )

    assert first_fingerprint is not None
    assert second_fingerprint == first_fingerprint
    assert emt_fingerprint is not None
    assert emt_fingerprint != first_fingerprint


def test_dgs_dynamic_import_bundle_reports_supported_and_failed_blocks() -> None:
    """Expose valid DGS equations while retaining unsupported blocks as failures."""

    dgs_path: Path = _get_dynamic_gain_block_dgs_path()
    bundle, _logger = build_dgs_dynamic_model_import_bundle(
        dgs_path=str(dgs_path),
    )
    entries_by_name = {
        entry.get_display_name(): entry
        for entry in bundle.get_entries()
    }

    assert bundle.get_source_tpe() is DynamicModelImportSource.PowerFactoryDgs
    assert set(entries_by_name) == {
        "Dynamic gain",
        "Unsupported dynamic block",
    }
    assert entries_by_name["Dynamic gain"].is_importable()
    assert (
        entries_by_name["Unsupported dynamic block"].get_availability()
        is DynamicModelImportEntryAvailability.Failed
    )


def test_dgs_dynamic_import_keeps_empty_physical_and_vendor_slot_metadata() -> None:
    """Preserve valid empty slots as visible, non-executable metadata.

    :return: None.
    """
    bundle: DynamicModelImportBundle
    bundle, _logger = build_dgs_dynamic_model_import_bundle(
        dgs_path=str(_get_non_executable_slots_dgs_path()),
    )
    entries_by_name: dict[str, DynamicModelImportEntry] = {
        entry.get_display_name(): entry
        for entry in bundle.get_entries()
    }
    reference_name: str
    for reference_name in (
            "Physical phase measurement",
            "Vendor extension reference",
    ):
        reference_entry: DynamicModelImportEntry = entries_by_name[reference_name]
        assert (
            reference_entry.get_availability()
            is DynamicModelImportEntryAvailability.MetadataOnly
        )
        assert reference_entry.get_source_block() is None
        assert not reference_entry.is_importable()

    assert (
        "physical slot has no exported pElm target"
        in entries_by_name["Physical phase measurement"].get_notes_text()
    )
    assert (
        "slot has no exported pElm target"
        in entries_by_name["Vendor extension reference"].get_notes_text()
    )


@pytest.mark.parametrize(
    "target_domain",
    [
        DynamicSimulationMode.RMS,
        DynamicSimulationMode.EMT,
    ],
)
def test_dgs_dynamic_import_materializes_the_selected_domain_end_to_end(
        target_domain: DynamicSimulationMode,
) -> None:
    """Preserve one DGS equation through parsing, selection and installation."""

    bundle, bundle_logger = build_dgs_dynamic_model_import_bundle(
        dgs_path=str(_get_dynamic_gain_block_dgs_path()),
    )
    gain_entry = next(
        entry
        for entry in bundle.get_entries()
        if entry.get_display_name() == "Dynamic gain"
    )
    source_block: Block | None = gain_entry.get_source_block()
    circuit: MultiCircuit = MultiCircuit()
    install_logger: Logger = Logger()

    assert bundle_logger.error_count() == 0
    assert source_block is not None

    added_count: int = add_dynamic_import_selection_requests_to_circuit(
        circuit=circuit,
        bundle=bundle,
        selection_requests=[
            DynamicModelImportSelectionRequest(
                entry_key=gain_entry.get_unique_key(),
                target_domain=target_domain,
                device_tpe=DeviceType.NoDevice,
            )
        ],
        logger=install_logger,
    )
    installed_templates: Sequence[RmsModelTemplate | EmtModelTemplate]
    other_template_count: int
    if target_domain is DynamicSimulationMode.RMS:
        installed_templates = circuit.rms_models
        other_template_count = len(circuit.emt_models)
    else:
        assert target_domain is DynamicSimulationMode.EMT
        installed_templates = circuit.emt_models
        other_template_count = len(circuit.rms_models)

    assert len(installed_templates) == 1
    assert other_template_count == 0

    installed_template: RmsModelTemplate | EmtModelTemplate = (
        installed_templates[0]
    )

    assert added_count == 1
    assert install_logger.error_count() == 0
    assert installed_template.name == "Dynamic gain"
    assert installed_template.tpe is DeviceType.NoDevice
    assert installed_template.block is not source_block
    assert len(installed_template.block.algebraic_eqs) == 1


@pytest.mark.parametrize(
    "dynamic_simulation_mode",
    [
        DynamicSimulationMode.RMS,
        DynamicSimulationMode.EMT,
    ],
)
def test_file_open_installs_dgs_models_in_the_explicit_dynamic_simulation_mode(
        dynamic_simulation_mode: DynamicSimulationMode,
) -> None:
    """Carry the selected RMS or EMT mode through the public DGS file-open path."""

    file_open: FileOpen = FileOpen(
        file_name=str(_get_dynamic_gain_block_dgs_path()),
        options=FileOpenOptions(
            file_type=FileType.DGS,
            dgs_use_dynamic_information=True,
            dgs_dynamic_simulation_mode=dynamic_simulation_mode,
        ),
    )
    circuit: MultiCircuit | None = file_open.open()

    assert circuit is not None

    installed_template: RmsModelTemplate | EmtModelTemplate
    if dynamic_simulation_mode is DynamicSimulationMode.RMS:
        assert len(circuit.rms_models) == 1
        assert len(circuit.emt_models) == 0
        installed_template = circuit.rms_models[0]
    else:
        assert dynamic_simulation_mode is DynamicSimulationMode.EMT
        assert len(circuit.emt_models) == 1
        assert len(circuit.rms_models) == 0
        installed_template = circuit.emt_models[0]

    assert installed_template.name == "Dynamic gain"
    logged_messages: set[str] = set(
        entry.msg for entry in file_open.logger.entries
    )
    assert "DGS dynamic template conversion completed" in logged_messages
    assert "DGS dynamic device assignment completed" in logged_messages


def test_file_open_rejects_dynamic_dgs_import_without_an_explicit_mode() -> None:
    """Keep the static DGS result and report the missing RMS/EMT selection."""

    file_open: FileOpen = FileOpen(
        file_name=str(_get_dynamic_gain_block_dgs_path()),
        options=FileOpenOptions(
            file_type=FileType.DGS,
            dgs_use_dynamic_information=True,
        ),
    )
    circuit: MultiCircuit | None = file_open.open()

    assert circuit is not None

    assert len(circuit.rms_models) == 0
    assert len(circuit.emt_models) == 0
    assert any(
        entry.msg == "DGS dynamic model import requires an explicit RMS or EMT simulation mode"
        for entry in file_open.logger.entries
    )


@pytest.mark.parametrize(
    "source_class,expected_device_tpe",
    (("ElmVsc", DeviceType.VscDevice),
     ("ElmVscmono", DeviceType.VscDevice),
     ("ElmSvs", DeviceType.ControllableShuntDevice),
     ("ElmSym", DeviceType.GeneratorDevice),
     ("ElmGenstat", DeviceType.GeneratorDevice),
     ("ElmLod", DeviceType.LoadDevice),
     ("ElmLodlv", DeviceType.LoadDevice),
     ("ElmLodmv", DeviceType.LoadDevice),
     ("ElmBat", DeviceType.BatteryDevice),
     ("ElmLne", DeviceType.LineDevice),
     ("ElmTr2", DeviceType.Transformer2WDevice),
     ("ElmXnet", DeviceType.GeneratorDevice),
     ("StaSwitch", None),
     ("ElmSind", None),
     (None, None)),
)
def test_dgs_element_host_device_types_follow_powerfactory_classes(
        source_class: str | None,
        expected_device_tpe: DeviceType | None,
) -> None:
    """Map each PowerFactory host class to the VeraGrid device that owns its dynamics.

    Auxiliary classes such as ``StaSwitch`` and ``ElmSind`` provide inputs or
    switching actions and never identify the physical host.

    :param source_class: Referenced DGS ``pElm`` class.
    :param expected_device_tpe: Expected VeraGrid host type, or ``None``.
    :return: None.
    """
    assert get_dgs_dynamic_host_device_tpe(source_element_class=source_class) == expected_device_tpe


@pytest.mark.parametrize(
    "source_class,expected_kind",
    (("ElmGenstat", NativeDgsEquipmentKind.StaticGenerator),
     ("ElmSym", NativeDgsEquipmentKind.SynchronousMachine),
     ("ElmSvs", NativeDgsEquipmentKind.StaticVarSystem),
     ("ElmVsc", NativeDgsEquipmentKind.BipolarVsc),
     ("ElmVscmono", NativeDgsEquipmentKind.MonopolarVsc),
     ("ElmLod", None)),
)
def test_dgs_native_equipment_kind_follows_the_slot_source_class(
        source_class: str,
        expected_kind: NativeDgsEquipmentKind | None,
) -> None:
    """Select the native physical family from the class of the slot element alone.

    The slot signals do not take part: a frame may declare pins its executable
    model leaves unused, so only the source class names the equipment.

    :param source_class: PowerFactory class of the equipment.
    :param expected_kind: Expected native family, or ``None`` for a class without one.
    :return: None.
    """
    entry: ElmCompInstanceEntry = ElmCompInstanceEntry(
        slot_id="equipment_slot",
        slot_name="Equipment",
        element_id="equipment_fid",
        element_name="Equipment",
        element_kind=source_class,
        element_outserv=0,
        type_id=None,
        type_name=None,
        slot_filter=source_class,
        slot_inputs=list(),
        slot_outputs=list(),
        connected_inputs=list(),
        connected_outputs=list(),
        slot_reference_is_resolved=True,
        element_reference_is_resolved=True,
    )
    direct_result: DgsDirectRootBuildResult = DgsDirectRootBuildResult(
        root_block=Block(),
        child_block_by_slot_id=dict(),
        graphical_tree_by_slot_id=dict(),
        direct_entries=list([entry]),
    )

    plans: tuple[NativeDgsEquipmentPlan, ...] = detect_native_dgs_equipment(direct_result)

    assert list(plan.kind for plan in plans) == ([expected_kind] if expected_kind is not None else list())


def _native_slot_entry(slot_id: str, element_kind: str, slot_inputs: list[str],
                       slot_outputs: list[str]) -> ElmCompInstanceEntry:
    """Resolved direct slot holding one element.

    :param slot_id: Slot FID, also used for its element.
    :param element_kind: PowerFactory class of the slot element.
    :param slot_inputs: Declared slot input signals.
    :param slot_outputs: Declared slot output signals.
    :return: Direct-slot relation.
    """
    return ElmCompInstanceEntry(
        slot_id=slot_id, slot_name=slot_id, element_id=slot_id, element_name=slot_id,
        element_kind=element_kind, element_outserv=0, type_id=None, type_name=None,
        slot_filter=element_kind, slot_inputs=slot_inputs, slot_outputs=slot_outputs,
        connected_inputs=list(), connected_outputs=list(),
        slot_reference_is_resolved=True, element_reference_is_resolved=True,
    )


def _native_cable(cable_id: str, name: str, source: str, target: str) -> BlkSig:
    """Scalar BlkSig between the first connectors of two slots.

    :param cable_id: Cable FID.
    :param name: Signal carried by the cable.
    :param source: Producing slot FID.
    :param target: Consuming slot FID.
    :return: Graphical cable record.
    """
    cable: BlkSig = BlkSig()
    cable.ID = cable_id
    cable.loc_name = name
    cable.pnodfrom = source
    cable.pnodto = target
    return cable


def test_native_assembly_keeps_the_terminal_voltage_an_equipment_input() -> None:
    """A frame receiver cabled from the terminal voltage must not own it.

    The frame declares VT as one of its own unknowns, as a PowerFactory composite
    frame does. The cable from the equipment binds VT to the terminal Vm, which
    stays an incoming terminal variable of the assembled model (TechRef: the
    network gives the terminal voltage to the machine and to its controllers).

    :return: None.
    """
    voltage: Var = Var("Vm", reference=VarPowerFlowReferenceType.Vm)
    angle: Var = Var("Va", reference=VarPowerFlowReferenceType.Va)
    susceptance: Var = Var("bsvs")
    reactive: Var = Var("Qsvs", reference=VarPowerFlowReferenceType.Q)
    active: Var = Var("Psvs", reference=VarPowerFlowReferenceType.P)
    equipment: Block = Block(
        name="Equipment", in_vars=list((voltage, angle, susceptance)), out_vars=list((active, reactive, voltage)),
        algebraic_vars=list((active, reactive)),
        algebraic_eqs=list((active - Const(0.0), reactive + susceptance * voltage * voltage)),
        external_mapping=dict(((VarPowerFlowReferenceType.P, active), (VarPowerFlowReferenceType.Q, reactive),
                               (VarPowerFlowReferenceType.Vm, voltage), (VarPowerFlowReferenceType.Va, angle))),
    )
    measured: Var = Var("VT")
    command: Var = Var("bsvs")
    controller: Block = Block(name="Controller", in_vars=list((measured,)), out_vars=list((command,)),
                              algebraic_vars=list((command,)), algebraic_eqs=list((command - (Const(1.0) - measured),)))
    frame: Block = Block(name="Frame", children=list((controller,)), algebraic_vars=list((measured,)))
    equipment_entry: ElmCompInstanceEntry = _native_slot_entry("svs", "ElmSvs", ["bsvs"], ["VT"])
    controller_entry: ElmCompInstanceEntry = _native_slot_entry("ctrl", "ElmDsl", ["VT"], ["bsvs"])
    direct_result: DgsDirectRootBuildResult = DgsDirectRootBuildResult(
        root_block=frame, child_block_by_slot_id=dict((("ctrl", controller),)),
        graphical_tree_by_slot_id=dict(), direct_entries=list((equipment_entry, controller_entry)),
    )
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.blksigs = list((_native_cable("1", "VT", "svs", "ctrl"), _native_cable("2", "bsvs", "ctrl", "svs")))

    assembled: Block = assemble_native_dgs_model(
        NativeDgsEquipmentPlan(NativeDgsEquipmentKind.StaticVarSystem, equipment_entry),
        equipment, direct_result, dgs_circuit, Logger(),
    )

    assert list(variable.uid for variable in assembled.in_vars) == list((voltage.uid, angle.uid))
    assert all(voltage.uid not in set(variable.uid for variable in block.algebraic_vars)
               for block in assembled.get_all_blocks())
    assert any(voltage.uid in set(variable.uid for variable in block.in_vars) for block in assembled.get_all_blocks()
               if block is controller)


@pytest.mark.parametrize(
    ("file_name", "uses_system_base"),
    (
        ("hvdc_vsc_v1_complete_static_dynamic.dgs", False),
        ("hvdc_vsc_v2_complete_static_dynamic.dgs", False),
        ("hvdc_vsc_v3_complete_static_dynamic.dgs", True),
    ),
)
def test_hvdc_vsc_runtime_templates_are_configured_from_their_host_converter(
        file_name: str,
        uses_system_base: bool,
) -> None:
    """Configure each activated converter template with the physical data of its own VSC.

    The native converter equations carry the series reactance of their exact
    host converter as a constant, built when the template is constructed.

    :param file_name: Exact tracked fixture name.
    :param uses_system_base: Whether the equations use the reactance on the system base.
    :return: None.
    """
    dgs_path: Path = _get_complete_hvdc_vsc_dgs_path(file_name=file_name)
    logger: Logger = Logger()
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(path=str(dgs_path))
    circuit: MultiCircuit = dgs_to_circuit(path=str(dgs_path))
    conversion_result: DgsDynamicTemplateConversionResult = convert_and_add_dgs_dynamic_templates_to_circuit(
        dgs_circuit=dgs_circuit,
        circuit=circuit,
        target_domain=DynamicSimulationMode.RMS,
        logger=logger,
    )
    apply_dgs_dynamic_templates_to_devices(
        dgs_circuit=dgs_circuit,
        circuit=circuit,
        templates_by_root_dgs_id=conversion_result.templates_by_root_dgs_id,
        logger=logger,
    )

    assert len(circuit.vsc_devices) == 2
    converter: VSC
    for converter in circuit.vsc_devices:
        template: RmsModelTemplate | None = converter.rms_template
        assert template is not None
        constants: list[float] = list()
        equation: Expr
        for equation in template.block.algebraic_eqs + template.block.state_eqs:
            _collect_constant_values(equation, constants)
        if uses_system_base:
            expected: float = float(converter.x_series) * float(circuit.Sbase) / float(converter.rate)
        else:
            expected = float(converter.x_series)
        assert pytest.approx(expected) in constants


def _collect_constant_values(expression: Expr, constants: list[float]) -> None:
    """Gather the real constants of an expression tree.

    :param expression: Symbolic expression to walk.
    :param constants: Values found so far, extended in place.
    :return: None.
    """
    if isinstance(expression, Const) and isinstance(expression.value, (int, float)):
        constants.append(float(expression.value))
    elif isinstance(expression, BinOp):
        _collect_constant_values(expression.left, constants)
        _collect_constant_values(expression.right, constants)
    elif isinstance(expression, UnOp):
        _collect_constant_values(expression.operand, constants)
    elif isinstance(expression, Func):
        _collect_constant_values(expression.arg, constants)
    elif isinstance(expression, Func2):
        _collect_constant_values(expression.arg1, constants)
        _collect_constant_values(expression.arg2, constants)
    else:
        pass


def _build_lookup_test_definition() -> BlkDef:
    """Build one DSL definition with internal and external characteristics.

    :return: Definition declaring ``array_a``, ``array_b`` and ``oarray_c``.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "LOOKUP_DEFINITION"
    definition.loc_name = "Lookup definition"
    definition.inputs = ["yi"]
    definition.outputs = ["yo"]
    definition.params = ["K", "array_a", "array_b", "oarray_c"]
    definition.equations_raw = ["yo = K*lapprox(yi, array_b)"]
    return definition


def test_dgs_elmdsl_lookup_tables_follow_powerfactory_storage() -> None:
    """Read ``array_`` columns from the model matrix and ``oarray_`` from its IntMat.

    Each internal array owns two adjacent columns in declaration order and
    states its point count in row 0; an external array is the child IntMat
    named after the characteristic (PowerFactory User Manual, chapter 30).
    Native PowerFactory 24.0.2 exports confirm that order for different arrays.

    :return: None.
    """
    element: ElmDsl = ElmDsl()
    element.ID = "DSL_FID"
    element.matrix = [
        [2.0, 0.0, 2.0, 0.0],
        [1.1, 1.1, 1.1, 1.1],
        [1.15, 1.0, 1.15, 1.0],
    ]
    own_table: IntMat = IntMat()
    own_table.loc_name = "c"
    own_table.fold_id = "DSL_FID"
    own_table.matrix = [[0.0, 0.0], [1.0, 10.0]]
    foreign_table: IntMat = IntMat()
    foreign_table.loc_name = "c"
    foreign_table.fold_id = "OTHER_FID"
    foreign_table.matrix = [[0.0, 5.0], [1.0, 6.0]]

    tables: dict[str, DgsLookupTable] = get_elmdsl_lookup_tables(
        element=element,
        blkdef=_build_lookup_test_definition(),
        intmats=[foreign_table, own_table],
    )

    assert sorted(tables.keys()) == ["array_a", "array_b", "oarray_c"]
    assert (tables["array_a"].x_points, tables["array_a"].y_points) == ((1.1, 1.15), (1.1, 1.0))
    assert (tables["array_b"].x_points, tables["array_b"].y_points) == ((1.1, 1.15), (1.1, 1.0))
    assert (tables["oarray_c"].x_points, tables["oarray_c"].y_points) == ((0.0, 1.0), (0.0, 10.0))

    element.matrix = [
        [2.0, 0.0, 3.0, 0.0],
        [1.1, 1.1, 0.0, 0.0],
        [1.15, 1.0, 1.0, 2.0],
        [None, None, 2.0, 4.0],
    ]
    different: dict[str, DgsLookupTable] = get_elmdsl_lookup_tables(
        element=element,
        blkdef=_build_lookup_test_definition(),
        intmats=[foreign_table, own_table],
    )
    assert sorted(different.keys()) == ["array_a", "array_b", "oarray_c"]
    assert (different["array_b"].x_points, different["array_b"].y_points) == ((0.0, 1.0, 2.0), (0.0, 2.0, 4.0))

    # An unreadable array is left out alone; its readable neighbour keeps its columns.
    element.matrix = [
        [2.0, 0.0, 0.0, 0.0],
        [1.1, 1.1, None, None],
        [1.15, 1.0, None, None],
    ]
    partly_readable: dict[str, DgsLookupTable] = get_elmdsl_lookup_tables(
        element=element,
        blkdef=_build_lookup_test_definition(),
        intmats=[foreign_table, own_table],
    )
    assert sorted(partly_readable.keys()) == ["array_a", "oarray_c"]


def _evaluate_lookup_output(block: Block, input_var: Var, input_value: float) -> float:
    """Evaluate the single algebraic output of a lookup block for one input.

    :param block: Block whose only equation is ``yo - f(yi)``.
    :param input_var: Its input variable.
    :param input_value: Input value.
    :return: Output value.
    """
    bindings: dict[int, float] = dict([(input_var.uid, input_value)])
    parameter_var: Var
    parameter_value: Expr
    for parameter_var, parameter_value in list(block.event_dict.items()) + list(block.mode_dict.items()):
        bindings[parameter_var.uid] = float(parameter_value.value)
    bindings[block.algebraic_vars[0].uid] = 0.0
    return -float(block.algebraic_eqs[0].eval_uid(bindings))


def test_dgs_lapprox_uses_the_catalog_lookup_array_expression() -> None:
    """Evaluate ``lapprox`` exactly as the catalog "Lookup array" block.

    PowerFactory's ``lapprox`` interpolates linearly and holds the end values
    outside the table (DSL macro reference, Lookup array).

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(_build_lookup_test_definition())
    parsed: ParsedDgsBlockDefinition = parse_dgs_block_definitions_from_circuit(circuit=circuit)["LOOKUP_DEFINITION"]
    assert parsed.unsupported_lines == []
    table: DgsLookupTable = DgsLookupTable(x_points=[0.0, 1.0, 2.0], y_points=[0.0, 2.0, 3.0])

    imported: Block = _build_block_from_parsed(
        parsed,
        dict(),
        parameter_values=dict([("K", 1.0)]),
        lookup_tables=dict([("array_b", table)]),
    )
    catalog: EmtModelTemplate = build_lookup_array_linear_runtime_template(
        vf=VarFactory(),
        x_points=list(table.x_points),
        y_points=list(table.y_points),
        clip=True,
    )

    imported_input: Var = next(var for var in imported.in_vars if var.name.endswith("yi"))
    value: float
    for value in (-1.0, 0.0, 0.5, 1.0, 1.7, 2.0, 3.0):
        assert _evaluate_lookup_output(imported, imported_input, value) == pytest.approx(
            _evaluate_lookup_output(catalog.block, catalog.block.in_vars[0], value)
        )
    assert _evaluate_lookup_output(imported, imported_input, 3.0) == pytest.approx(3.0)


def test_dgs_lapprox_without_its_characteristic_fails_closed() -> None:
    """Reject an instance whose characteristic is missing.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(_build_lookup_test_definition())
    parsed: ParsedDgsBlockDefinition = parse_dgs_block_definitions_from_circuit(circuit=circuit)["LOOKUP_DEFINITION"]

    with pytest.raises(UnsupportedDgsExpression):
        _build_block_from_parsed(parsed, dict(), parameter_values=dict([("K", 1.0)]))


def test_dgs_graphical_reference_passes_characteristics_to_its_child() -> None:
    """Bind a macro child's characteristic to the enclosing one named in ``sParams``.

    :return: None.
    """
    child: BlkDef = BlkDef()
    child.ID = "VDL_DEFINITION"
    child.loc_name = "VDL"
    child.inputs = ["yi"]
    child.outputs = ["yo"]
    child.params = ["array_vdl"]
    child.equations_raw = ["yo = lapprox (yi, array_vdl)"]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(child)
    parsed_child: ParsedDgsBlockDefinition = parse_dgs_block_definitions_from_circuit(circuit=circuit)["VDL_DEFINITION"]
    reference: BlkRef = BlkRef()
    reference.params = ["array_vdl2"]
    first: DgsLookupTable = DgsLookupTable(x_points=[0.0, 1.0], y_points=[0.0, 1.0])
    second: DgsLookupTable = DgsLookupTable(x_points=[1.1, 1.15], y_points=[1.1, 1.0])

    bound: dict[str, DgsLookupTable] = _bind_graphical_reference_lookup_tables(
        reference=reference,
        parsed_child=parsed_child,
        root_lookup_tables=dict([("array_vdl1", first), ("array_vdl2", second)]),
    )

    assert bound == dict([("array_vdl", second)])


def test_dgs_malformed_characteristic_cells_keep_the_file_parseable() -> None:
    """Read a malformed IntMat cell or size as unknown instead of aborting the parse.

    :return: None.
    """
    header_map: dict[str, int] = parse_header(
        "$$IntMat;FID(a:40);OP(a:1);loc_name(a:80);fold_id(p);M:SIZEROW(i);M:SIZECOL(i);"
        "M:0:0(r);M:0:1(r);M:1:0(r);M:1:1(r)"
    )[1]

    with_bad_cell: IntMat = IntMat.parse_line(line="  7;C;c;DSL_FID;2;2;0;*;1;bad", header_map=header_map)
    with_bad_size: IntMat = IntMat.parse_line(line="  8;C;c;DSL_FID;*;2;0;0;1;1", header_map=header_map)
    with_infinite_size: IntMat = IntMat.parse_line(line="  9;C;c;DSL_FID;inf;2;0;0;1;1", header_map=header_map)
    with_nan_x: IntMat = IntMat.parse_line(line=" 10;C;c;DSL_FID;2;2;0;0;nan;1", header_map=header_map)
    with_nan_y: IntMat = IntMat.parse_line(line=" 11;C;c;DSL_FID;2;2;0;0;1;nan", header_map=header_map)
    element: ElmDsl = ElmDsl()
    element.ID = "DSL_FID"
    element.matrix = [[float("inf"), 0.0], [0.0, 0.0], [1.0, 1.0]]

    assert with_bad_cell.matrix == [[0.0, None], [1.0, None]]
    assert with_bad_size.matrix == []
    assert with_infinite_size.matrix == []
    nan_table: IntMat
    for nan_table in (with_nan_x, with_nan_y):
        assert get_elmdsl_lookup_tables(element=element, blkdef=_build_lookup_test_definition(),
                                        intmats=[nan_table]) == dict()


def test_dgs_lapprox_reads_an_external_intmat_characteristic() -> None:
    """Build and evaluate one ``oarray_`` lookup from the IntMat owned by the model.

    :return: None.
    """
    definition: BlkDef = BlkDef()
    definition.ID = "VDL_OBJECT_DEFINITION"
    definition.loc_name = "VDL object"
    definition.inputs = ["yi"]
    definition.outputs = ["yo"]
    definition.params = ["oarray_vdl"]
    definition.equations_raw = ["yo = lapprox (yi, oarray_vdl)"]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(definition)
    parsed: ParsedDgsBlockDefinition = parse_dgs_block_definitions_from_circuit(circuit=circuit)[
        "VDL_OBJECT_DEFINITION"
    ]
    element: ElmDsl = ElmDsl()
    element.ID = "VDL_FID"
    table: IntMat = IntMat()
    table.loc_name = "vdl"
    table.fold_id = "VDL_FID"
    table.matrix = [[1.1, 1.1], [1.15, 1.0], [1.3, 0.0]]

    block: Block = _build_block_from_parsed(
        parsed,
        dict(),
        lookup_tables=get_elmdsl_lookup_tables(element=element, blkdef=definition, intmats=[table]),
    )

    block_input: Var = next(var for var in block.in_vars if var.name.endswith("yi"))
    assert _evaluate_lookup_output(block, block_input, 1.2) == pytest.approx(1.0 - (1.2 - 1.15) / 0.15)
    assert _evaluate_lookup_output(block, block_input, 2.0) == pytest.approx(0.0)


def test_dgs_graphical_child_characteristics_prefer_the_sparams_binding() -> None:
    """Prefer the enclosing characteristic named in ``sParams`` over a nested instance.

    :return: None.
    """
    child: BlkDef = BlkDef()
    child.ID = "VDL_PRECEDENCE_DEFINITION"
    child.loc_name = "VDL"
    child.inputs = ["yi"]
    child.outputs = ["yo"]
    child.params = ["array_vdl", "array_own"]
    child.equations_raw = ["yo = lapprox (yi, array_vdl)"]
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.append(child)
    parsed_child: ParsedDgsBlockDefinition = parse_dgs_block_definitions_from_circuit(circuit=circuit)[
        "VDL_PRECEDENCE_DEFINITION"
    ]
    reference: BlkRef = BlkRef()
    reference.params = ["array_vdl1"]
    enclosing: DgsLookupTable = DgsLookupTable(x_points=[1.1, 1.15], y_points=[1.1, 1.0])
    nested_vdl: DgsLookupTable = DgsLookupTable(x_points=[0.0, 1.0], y_points=[0.0, 1.0])
    nested_own: DgsLookupTable = DgsLookupTable(x_points=[0.0, 1.0], y_points=[5.0, 6.0])
    nested: ElmCompInstanceEntry = ElmCompInstanceEntry(
        slot_id=None,
        slot_name="VDL",
        element_id="NESTED_FID",
        element_name="VDL",
        element_kind="ElmDsl",
        element_outserv=0,
        type_id="VDL_PRECEDENCE_DEFINITION",
        type_name="VDL",
        lookup_tables=dict([("array_vdl", nested_vdl), ("array_own", nested_own)]),
    )

    tables: dict[str, DgsLookupTable] = _resolve_graphical_child_lookup_tables(
        reference=reference,
        parsed_child=parsed_child,
        instance_entry=nested,
        root_lookup_tables=dict([("array_vdl1", enclosing)]),
    )

    assert tables == dict([("array_vdl", enclosing), ("array_own", nested_own)])


def _build_v2_slave_root(empty_ffs: bool, ffs_element_id: str | None = None) -> DgsDirectRootBuildResult:
    """Build the V2 SlavePWM_Model root, optionally replacing the element of its FFS slot.

    :param empty_ffs: Replace the FFS ``pelm`` by ``ffs_element_id``.
    :param ffs_element_id: Replacement ``pelm`` (``None`` empties the slot).
    :return: Direct root build result.
    """
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(
        path=str(_get_complete_hvdc_vsc_dgs_path(
            file_name="hvdc_vsc_v2_complete_static_dynamic.dgs",
        ))
    )
    if empty_ffs:
        root: ElmComp = next(comp for comp in dgs_circuit.elmcomps if comp.loc_name == "SlavePWM_Model")
        slot_name_by_id: dict[str, str] = dict((slot.ID, slot.loc_name) for slot in dgs_circuit.blkslots)
        ffs_index: int = next(
            index for index, slot_id in enumerate(root.pblk) if slot_name_by_id.get(slot_id, "") == "FFS"
        )
        root.pelm[ffs_index] = ffs_element_id
    else:
        pass
    parsed_blocks: dict[str, ParsedDgsBlockDefinition] = (
        parse_dgs_block_definitions_from_circuit(circuit=dgs_circuit)
    )
    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=dgs_circuit,
        parsed_blocks=parsed_blocks,
        root_name="SlavePWM_Model",
    )
    return build_direct_root_elmcomp_block(
        circuit=dgs_circuit,
        result=root_result,
        graphical_indexes=build_dgs_graphical_indexes(circuit=dgs_circuit),
    )


def test_empty_dynamic_slot_leaves_its_cables_unconnected() -> None:
    """Build a root whose DSL slot is empty, as PowerFactory allows.

    The empty slot gets no child; every other slot is built as before.

    :return: None.
    """
    complete: DgsDirectRootBuildResult = _build_v2_slave_root(empty_ffs=False)
    without_ffs: DgsDirectRootBuildResult = _build_v2_slave_root(empty_ffs=True, ffs_element_id=None)
    ffs_entry: ElmCompInstanceEntry = next(
        entry for entry in without_ffs.direct_entries if entry.slot_name == "FFS"
    )

    assert ffs_entry.element_id is None
    assert ffs_entry.slot_id not in without_ffs.child_block_by_slot_id
    assert ffs_entry.slot_id in complete.child_block_by_slot_id
    assert set(without_ffs.child_block_by_slot_id) == set(complete.child_block_by_slot_id) - {ffs_entry.slot_id}


def test_unresolved_dynamic_slot_element_is_still_rejected() -> None:
    """Keep rejecting a slot whose element pointer names a missing object.

    :return: None.
    """
    with pytest.raises(ValueError, match="no resolved ElmDsl or ElmComp instance"):
        _build_v2_slave_root(empty_ffs=True, ffs_element_id="MISSING_FID")


def _build_internal_binding_fixture(
        parent_equations: list[str],
        child_equations: list[str],
        bound_names: list[str],
) -> tuple[BlkRef, ParsedDgsBlockDefinition, Block, ParsedDgsBlockDefinition, Block]:
    """Build an enclosing macro and one child sharing an internal through ``sIntern``.

    :param parent_equations: Enclosing definition equations.
    :param child_equations: Child definition equations.
    :param bound_names: Enclosing names written on the ``BlkRef``.
    :return: Reference, parsed child, child block, parsed parent and parent block.
    """
    parent: BlkDef = BlkDef()
    parent.ID = "INTERN_PARENT"
    parent.loc_name = "REEC"
    parent.inputs = ["Vt"]
    parent.outputs = ["Verr"]
    parent.internals = ["Vref"]
    parent.equations_raw = parent_equations
    child: BlkDef = BlkDef()
    child.ID = "INTERN_CHILD"
    child.loc_name = "Vref0_select"
    child.inputs = ["yi"]
    child.outputs = ["yo"]
    child.internals = ["Vsel"]
    child.equations_raw = child_equations
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.extend([parent, child])
    parsed: dict[str, ParsedDgsBlockDefinition] = parse_dgs_block_definitions_from_circuit(circuit=circuit)
    reference: BlkRef = BlkRef()
    reference.ID = "284"
    reference.internals = list(bound_names)
    return (reference, parsed["INTERN_CHILD"], _build_block_from_parsed(parsed["INTERN_CHILD"], dict()),
            parsed["INTERN_PARENT"], _build_block_from_parsed(parsed["INTERN_PARENT"], dict()))


def _uids_read_by(block: Block) -> set[int]:
    """Collect the UIDs read by the runtime equations of one block.

    :param block: Materialized block.
    :return: Variable UIDs.
    """
    return set(var.uid for equation in block.algebraic_eqs for var in equation.get_vars())


def test_dgs_reference_internal_reads_the_enclosing_initialized_variable() -> None:
    """Let a child read the enclosing ``inc()`` variable named in ``sIntern``.

    GB REEC_C sets ``inc(Vref) = Vt`` and its ``Vref0_select`` child reads the
    same ``Vref`` under its own internal name.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_internal_binding_fixture(
        parent_equations=["Verr = Vref - Vt", "inc(Vref) = Vt"],
        child_equations=["yo = Vsel + yi"],
        bound_names=["Vref"],
    )
    parent_vref: Var = next(var for var in parent_block.event_dict if var.name == "REEC__Vref")

    _bind_graphical_reference_internals(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                        parsed_parent=parsed_parent, parent_block=parent_block)

    assert parent_vref.uid in _uids_read_by(child_block)
    assert not any(var.name == "Vref0_select__Vsel" for var in child_block.algebraic_eqs[0].get_vars())


def test_dgs_reference_internal_computed_by_the_child_takes_the_enclosing_inc_as_initial_value() -> None:
    """Treat an enclosing ``inc()`` of a child-computed internal as its initial value.

    GB SVS frames set ``inc(uv1) = 0`` while the Undervoltage Trip child
    computes ``uv1``.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_internal_binding_fixture(
        parent_equations=["Verr = Vref - Vt", "inc(Vref) = 0.25"],
        child_equations=["Vsel = 2 * yi", "yo = Vsel"],
        bound_names=["Vref"],
    )
    child_vsel: Var = next(var for var in child_block.algebraic_vars if var.name == "Vref0_select__Vsel")

    _bind_graphical_reference_internals(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                        parsed_parent=parsed_parent, parent_block=parent_block)

    assert child_vsel.uid in _uids_read_by(parent_block)
    # The shared variable is computed, so it cannot also stay a runtime parameter.
    assert all(var.name != "REEC__Vref" and var.uid != child_vsel.uid for var in parent_block.event_dict)
    assert parent_block.init_eqs[child_vsel].value == pytest.approx(0.25)


def test_dgs_reference_internal_computed_on_both_sides_fails_closed() -> None:
    """Reject one ``sIntern`` variable computed by the child and the enclosing block.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_internal_binding_fixture(
        parent_equations=["Vref = Vt", "Verr = Vref - Vt"],
        child_equations=["Vsel = 2 * yi", "yo = Vsel"],
        bound_names=["Vref"],
    )

    with pytest.raises(ValueError, match="computed by both"):
        _bind_graphical_reference_internals(reference=reference, parsed_child=parsed_child,
                                            child_block=child_block, parsed_parent=parsed_parent,
                                            parent_block=parent_block)


def test_dgs_reference_internal_count_must_match_the_child_definition() -> None:
    """Reject an ``sIntern`` list that does not name every child internal.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_internal_binding_fixture(
        parent_equations=["Verr = Vref - Vt", "inc(Vref) = Vt"],
        child_equations=["yo = Vsel + yi"],
        bound_names=["Vref", "Vt"],
    )

    with pytest.raises(ValueError, match="do not match"):
        _bind_graphical_reference_internals(reference=reference, parsed_child=parsed_child,
                                            child_block=child_block, parsed_parent=parsed_parent,
                                            parent_block=parent_block)


def test_dgs_reference_internal_initialized_on_both_sides_fails_closed() -> None:
    """Reject one ``sIntern`` variable given an ``inc()`` by both sides.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_internal_binding_fixture(
        parent_equations=["Verr = Vref - Vt", "inc(Vref) = 0.25"],
        child_equations=["Vsel = 2 * yi", "yo = Vsel", "inc(Vsel) = 0.5"],
        bound_names=["Vref"],
    )

    with pytest.raises(ValueError, match="initialized by both"):
        _bind_graphical_reference_internals(reference=reference, parsed_child=parsed_child,
                                            child_block=child_block, parsed_parent=parsed_parent,
                                            parent_block=parent_block)


def test_dgs_reference_internal_initialized_by_the_child_but_computed_by_the_enclosing_block_fails_closed() -> None:
    """Reject a child ``inc()`` of a variable the enclosing block computes.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_internal_binding_fixture(
        parent_equations=["Vref = Vt", "Verr = Vref - Vt"],
        child_equations=["yo = Vsel + yi", "inc(Vsel) = 1.0"],
        bound_names=["Vref"],
    )

    with pytest.raises(ValueError, match="initialized by the child but computed"):
        _bind_graphical_reference_internals(reference=reference, parsed_child=parsed_child,
                                            child_block=child_block, parsed_parent=parsed_parent,
                                            parent_block=parent_block)


def test_dgs_reference_internal_naming_an_enclosing_port_fails_closed() -> None:
    """Reject an ``sIntern`` token naming an enclosing input or output.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_internal_binding_fixture(
        parent_equations=["Verr = Vref - Vt", "inc(Vref) = Vt"],
        child_equations=["yo = Vsel + yi"],
        bound_names=["Vt"],
    )

    with pytest.raises(ValueError, match="enclosing port"):
        _bind_graphical_reference_internals(reference=reference, parsed_child=parsed_child,
                                            child_block=child_block, parsed_parent=parsed_parent,
                                            parent_block=parent_block)


def test_graphical_macro_child_reads_the_enclosing_internal_named_in_sintern() -> None:
    """Bind ``sIntern`` while building a complete graphical macro.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    macro: BlkDef = next(definition for definition in circuit.blkdefs if definition.ID == "MACRO")
    macro.internals.append("held")
    macro.equations_raw.append("inc(held) = external_x")

    child_definition: BlkDef = BlkDef()
    child_definition.ID = "SELECTOR_DEFINITION"
    child_definition.loc_name = "Selector"
    child_definition.inputs = ["yi"]
    child_definition.outputs = ["yo"]
    child_definition.internals = ["Vsel"]
    child_definition.equations_raw = ["yo = Vsel + yi"]
    circuit.blkdefs.append(child_definition)
    child_reference: BlkRef = BlkRef()
    child_reference.ID = "SELECTOR_REFERENCE"
    child_reference.typ_id = child_definition.ID
    child_reference.cdisName = "Selector instance"
    child_reference.internals = ["held"]
    circuit.blkrefs.append(child_reference)
    child_signal: BlkSig = BlkSig()
    child_signal.ID = "ROOT_TO_SELECTOR"
    child_signal.loc_name = "external_x"
    child_signal.inodfrom = 0
    child_signal.iconfrom = 1
    child_signal.inodto = 0
    child_signal.iconto = 1
    child_signal.pnodfrom = "MACRO"
    child_signal.pnodto = child_reference.ID
    circuit.blksigs.append(child_signal)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    graphical_tree: DgsGraphicTreeResult | None = extract_root_slot_graphical_tree_from_circuit(
        circuit=circuit,
        result=root_result,
        slot_name="Graphical parent",
        graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
    )

    assert graphical_tree is not None
    held: Var = next(var for var in graphical_tree.view_block.event_dict if var.name.endswith("__held"))
    selector: Block = next(child for child in graphical_tree.view_block.children
                           if child.name == child_reference.cdisName)
    assert held.uid in _uids_read_by(selector)


def _build_labelled_root_input_tree(port: int, label: str) -> tuple[DgsGraphicTreeResult | None, str]:
    """Build the graphical parent with a second root input cabled to a child from one drawing port.

    :param port: Root drawing port the cable leaves from.
    :param label: Cable label.
    :return: Graphical tree and the child instance name.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    macro: BlkDef = next(definition for definition in circuit.blkdefs if definition.ID == "MACRO")
    macro.inputs.append("second_x")

    child_definition: BlkDef = BlkDef()
    child_definition.ID = "COPY_DEFINITION"
    child_definition.loc_name = "Copy"
    child_definition.inputs = ["yi"]
    child_definition.outputs = ["yo"]
    child_definition.equations_raw = ["yo = yi"]
    circuit.blkdefs.append(child_definition)
    child_reference: BlkRef = BlkRef()
    child_reference.ID = "COPY_REFERENCE"
    child_reference.typ_id = child_definition.ID
    child_reference.cdisName = "Copy instance"
    circuit.blkrefs.append(child_reference)
    signal: BlkSig = BlkSig()
    signal.ID = "ROOT_TO_COPY"
    signal.loc_name = label
    signal.inodfrom = port
    signal.iconfrom = 1
    signal.inodto = 0
    signal.iconto = 1
    signal.pnodfrom = "MACRO"
    signal.pnodto = child_reference.ID
    circuit.blksigs.append(signal)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    return extract_root_slot_graphical_tree_from_circuit(
        circuit=circuit,
        result=root_result,
        slot_name="Graphical parent",
        graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
    ), child_reference.cdisName


@pytest.mark.parametrize("port,label", [(2, "second_x"), (0, "second_x(1)")])
def test_graphical_root_input_cable_binds_to_the_input_its_label_names(port: int, label: str) -> None:
    """Bind a root-input cable to the input its label names, not to the drawing port position.

    GB REGC_A draws its inputs on ports 0, 1, 3, 4, 5: port 5 carries Ipcmd
    and port 3 carries Vt, the third declared input.

    :param port: Root drawing port the cable leaves from.
    :param label: Cable label.
    :return: None.
    """
    graphical_tree, child_name = _build_labelled_root_input_tree(port=port, label=label)

    assert graphical_tree is not None
    copy: Block = next(child for child in graphical_tree.view_block.children if child.name == child_name)
    assert {var.name.rsplit("__", 1)[-1] for var in copy.in_vars} == {"second_x"}


@pytest.mark.parametrize("port,root_input", [(0, "external_x"), (1, "second_x")])
def test_graphical_root_input_cable_without_an_input_label_binds_by_port(port: int, root_input: str) -> None:
    """Bind a root-input cable whose label names no root input to the input at its drawing port.

    :param port: Root drawing port the cable leaves from.
    :param root_input: Root input declared at that port.
    :return: None.
    """
    graphical_tree, child_name = _build_labelled_root_input_tree(port=port, label="foo")

    assert graphical_tree is not None
    copy: Block = next(child for child in graphical_tree.view_block.children if child.name == child_name)
    assert {var.name.rsplit("__", 1)[-1] for var in copy.in_vars} == {root_input}


def _build_state_binding_fixture(
        parent_equations: list[str],
        child_equations: list[str],
        bound_names: list[str],
) -> tuple[BlkRef, ParsedDgsBlockDefinition, Block, ParsedDgsBlockDefinition, Block]:
    """Build an enclosing macro and one child sharing a state through ``sStates``.

    :param parent_equations: Enclosing definition equations.
    :param child_equations: Child definition equations.
    :param bound_names: Enclosing names written on the ``BlkRef``.
    :return: Reference, parsed child, child block, parsed parent and parent block.
    """
    parent: BlkDef = BlkDef()
    parent.ID = "STATE_PARENT"
    parent.loc_name = "REGC"
    parent.inputs = ["Ipcmd"]
    parent.outputs = ["idref"]
    parent.states = ["xp"]
    parent.equations_raw = parent_equations
    child: BlkDef = BlkDef()
    child.ID = "STATE_CHILD"
    child.loc_name = "Lag"
    child.inputs = ["yi"]
    child.outputs = ["yo"]
    child.states = ["x"]
    child.equations_raw = child_equations
    circuit: DgsCircuit = DgsCircuit()
    circuit.blkdefs.extend([parent, child])
    parsed: dict[str, ParsedDgsBlockDefinition] = parse_dgs_block_definitions_from_circuit(circuit=circuit)
    reference: BlkRef = BlkRef()
    reference.ID = "290"
    reference.states = list(bound_names)
    return (reference, parsed["STATE_CHILD"], _build_block_from_parsed(parsed["STATE_CHILD"], dict()),
            parsed["STATE_PARENT"], _build_block_from_parsed(parsed["STATE_PARENT"], dict()))


def test_dgs_reference_state_takes_the_enclosing_inc_as_initial_value() -> None:
    """Initialize a child state from the enclosing ``inc()`` named in ``sStates``.

    GB REGC_C sets ``inc(xp)`` while its ``[{1/(1+sT)}]`` child integrates
    the same state as ``x``.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["idref = Ipcmd", "inc(xp) = 2 * Ipcmd"],
        child_equations=["x. = (yi - x) / 0.1", "yo = x"],
        bound_names=["xp"],
    )
    child_x: Var = child_block.state_vars[0]
    parent_ipcmd: Var = parent_block.in_vars[0]

    _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                     parsed_parent=parsed_parent, parent_block=parent_block)

    assert child_x in parent_block.init_eqs
    assert parent_ipcmd.uid in set(var.uid for var in parent_block.init_eqs[child_x].get_vars())
    assert all(var.name != "REGC__xp" for var in parent_block.init_eqs)


def test_dgs_reference_state_read_by_the_enclosing_block_reads_the_child_state() -> None:
    """Replace the enclosing state by the child state in the enclosing equations.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["idref = 2 * xp", "inc(xp) = Ipcmd"],
        child_equations=["x. = (yi - x) / 0.1", "yo = x"],
        bound_names=["xp"],
    )
    child_x: Var = child_block.state_vars[0]

    _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                     parsed_parent=parsed_parent, parent_block=parent_block)

    assert child_x.uid in _uids_read_by(parent_block)
    assert all(var.name != "REGC__xp" for equation in parent_block.algebraic_eqs for var in equation.get_vars())


def test_dgs_reference_state_self_referencing_inc_reads_the_child_state() -> None:
    """Rewrite an enclosing ``inc()`` that reads its own state onto the child state.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["idref = Ipcmd", "inc(xp) = Ipcmd + 0 * xp"],
        child_equations=["x. = (yi - x) / 0.1", "yo = x"],
        bound_names=["xp"],
    )
    child_x: Var = child_block.state_vars[0]

    _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                     parsed_parent=parsed_parent, parent_block=parent_block)

    assert all(var.name != "REGC__xp" for var in parent_block.init_eqs[child_x].get_vars())


def test_dgs_reference_state_naming_an_enclosing_parameter_fails_closed() -> None:
    """Reject an ``sStates`` token naming an enclosing runtime parameter.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["idref = Ipcmd", "inc(xp) = Ipcmd"],
        child_equations=["x. = (yi - x) / 0.1", "yo = x"],
        bound_names=["xp"],
    )
    parent_xp: Var = next(var for var in parent_block.init_eqs if var.name == "REGC__xp")
    parent_block.event_dict[parent_xp] = parent_block.init_eqs.pop(parent_xp)

    with pytest.raises(ValueError, match="enclosing parameter"):
        _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                         parsed_parent=parsed_parent, parent_block=parent_block)


def test_dgs_reference_state_with_a_child_derivative_initialization_fails_closed() -> None:
    """Reject an enclosing ``inc()`` of a state the child initializes through ``diff_init_eqs``.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["idref = Ipcmd", "inc(xp) = Ipcmd"],
        child_equations=["x. = (yi - x) / 0.1", "yo = x"],
        bound_names=["xp"],
    )
    child_block.diff_init_eqs[child_block.state_vars[0]] = Const(0.0)

    with pytest.raises(ValueError, match="initialized by both"):
        _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                         parsed_parent=parsed_parent, parent_block=parent_block)


def test_dgs_reference_state_enclosing_derivative_initialization_moves_to_the_child_state() -> None:
    """Move an enclosing ``diff_init_eqs`` entry of a bound state onto the child state.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["idref = 2 * xp", "inc(xp) = Ipcmd"],
        child_equations=["x. = (yi - x) / 0.1", "yo = x"],
        bound_names=["xp"],
    )
    child_x: Var = child_block.state_vars[0]
    parent_xp: Var = next(var for var in parent_block.init_eqs if var.name == "REGC__xp")
    # Keyed by another object with the same UID, which update_model cannot re-key by identity.
    parent_block.diff_init_eqs[copy.copy(parent_xp)] = Const(0.0)

    _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                     parsed_parent=parsed_parent, parent_block=parent_block)

    assert child_x in parent_block.diff_init_eqs
    assert all(var.name != "REGC__xp" for var in parent_block.diff_init_eqs)


def test_dgs_reference_state_with_an_enclosing_derivative_initialization_and_a_child_inc_fails_closed() -> None:
    """Reject a child ``inc()`` of a state the enclosing block initializes through ``diff_init_eqs``.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["idref = 2 * xp", "inc(xp) = Ipcmd"],
        child_equations=["x. = (yi - x) / 0.1", "yo = x", "inc(x) = yi"],
        bound_names=["xp"],
    )
    parent_xp: Var = next(var for var in parent_block.init_eqs if var.name == "REGC__xp")
    parent_block.diff_init_eqs[parent_xp] = parent_block.init_eqs.pop(parent_xp)

    with pytest.raises(ValueError, match="initialized by both"):
        _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                         parsed_parent=parsed_parent, parent_block=parent_block)


def test_dgs_reference_state_with_a_child_parameter_initialization_fails_closed() -> None:
    """Reject an enclosing ``inc()`` of a state the child holds as a runtime parameter value.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["idref = Ipcmd", "inc(xp) = Ipcmd"],
        child_equations=["x. = (yi - x) / 0.1", "yo = x"],
        bound_names=["xp"],
    )
    child_block.event_dict[child_block.state_vars[0]] = Const(0.0)

    with pytest.raises(ValueError, match="initialized by both"):
        _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                         parsed_parent=parsed_parent, parent_block=parent_block)


def test_dgs_reference_state_absent_from_the_enclosing_runtime_is_skipped() -> None:
    """Leave a child state alone when the enclosing state is never used.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["idref = Ipcmd"],
        child_equations=["x. = (yi - x) / 0.1", "yo = x"],
        bound_names=["xp"],
    )
    child_x: Var = child_block.state_vars[0]

    _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                     parsed_parent=parsed_parent, parent_block=parent_block)

    assert child_x not in parent_block.init_eqs
    assert child_block.state_vars[0] is child_x


def test_dgs_reference_state_count_must_match_the_child_definition() -> None:
    """Reject an ``sStates`` list that does not name every child state.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["idref = Ipcmd", "inc(xp) = Ipcmd"],
        child_equations=["x. = (yi - x) / 0.1", "yo = x"],
        bound_names=["xp", "Ipcmd"],
    )

    with pytest.raises(ValueError, match="do not match"):
        _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                         parsed_parent=parsed_parent, parent_block=parent_block)


def test_dgs_reference_state_initialized_on_both_sides_fails_closed() -> None:
    """Reject one ``sStates`` state given an ``inc()`` by both sides.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["idref = Ipcmd", "inc(xp) = Ipcmd"],
        child_equations=["x. = (yi - x) / 0.1", "yo = x", "inc(x) = yi"],
        bound_names=["xp"],
    )

    with pytest.raises(ValueError, match="initialized by both"):
        _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                         parsed_parent=parsed_parent, parent_block=parent_block)


def test_dgs_reference_state_computed_by_the_enclosing_block_fails_closed() -> None:
    """Reject an ``sStates`` state the enclosing block computes algebraically.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["xp = Ipcmd", "idref = xp"],
        child_equations=["x. = (yi - x) / 0.1", "yo = x"],
        bound_names=["xp"],
    )

    with pytest.raises(ValueError, match="computed by the enclosing block"):
        _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                         parsed_parent=parsed_parent, parent_block=parent_block)


def test_dgs_reference_state_naming_an_enclosing_port_fails_closed() -> None:
    """Reject an ``sStates`` token naming an enclosing input or output.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["idref = Ipcmd", "inc(xp) = Ipcmd"],
        child_equations=["x. = (yi - x) / 0.1", "yo = x"],
        bound_names=["Ipcmd"],
    )

    with pytest.raises(ValueError, match="enclosing port"):
        _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                         parsed_parent=parsed_parent, parent_block=parent_block)


def test_dgs_reference_state_naming_a_child_algebraic_variable_fails_closed() -> None:
    """Reject an ``sStates`` binding whose child variable has no state equation.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["idref = Ipcmd", "inc(xp) = Ipcmd"],
        child_equations=["x = yi", "yo = x"],
        bound_names=["xp"],
    )

    with pytest.raises(ValueError, match="not a state"):
        _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                         parsed_parent=parsed_parent, parent_block=parent_block)


def test_graphical_macro_child_state_takes_the_enclosing_inc_named_in_sstates() -> None:
    """Bind ``sStates`` while building a complete graphical macro.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    macro: BlkDef = next(definition for definition in circuit.blkdefs if definition.ID == "MACRO")
    macro.states.append("held_state")
    macro.equations_raw.append("inc(held_state) = 3 * external_x")

    child_definition: BlkDef = BlkDef()
    child_definition.ID = "LAG_DEFINITION"
    child_definition.loc_name = "Lag"
    child_definition.inputs = ["yi"]
    child_definition.outputs = ["yo"]
    child_definition.states = ["x"]
    child_definition.equations_raw = ["x. = (yi - x) / 0.1", "yo = x"]
    circuit.blkdefs.append(child_definition)
    child_reference: BlkRef = BlkRef()
    child_reference.ID = "LAG_REFERENCE"
    child_reference.typ_id = child_definition.ID
    child_reference.cdisName = "Lag instance"
    child_reference.states = ["held_state"]
    circuit.blkrefs.append(child_reference)
    child_signal: BlkSig = BlkSig()
    child_signal.ID = "ROOT_TO_LAG"
    child_signal.loc_name = "external_x"
    child_signal.inodfrom = 0
    child_signal.iconfrom = 1
    child_signal.inodto = 0
    child_signal.iconto = 1
    child_signal.pnodfrom = "MACRO"
    child_signal.pnodto = child_reference.ID
    circuit.blksigs.append(child_signal)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    graphical_tree: DgsGraphicTreeResult | None = extract_root_slot_graphical_tree_from_circuit(
        circuit=circuit,
        result=root_result,
        slot_name="Graphical parent",
        graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
    )

    assert graphical_tree is not None
    lag: Block = next(child for child in graphical_tree.view_block.children if child.name == child_reference.cdisName)
    assert lag.state_vars[0] in graphical_tree.view_block.init_eqs
    assert all(not var.name.endswith("__held_state") for var in graphical_tree.view_block.init_eqs)


def _build_circular_state_fixture(
        child_equations: list[str],
) -> tuple[BlkRef, ParsedDgsBlockDefinition, Block, ParsedDgsBlockDefinition, Block]:
    """Build an enclosing macro whose ``inc()`` names the output its child computes from the bound state.

    GB ``vol_stator_voltage_REGC_C`` declares ``inc(x_lpf_d)=ur_ref`` while the
    graphical cable makes ``ur_ref`` the output of its lag child.

    :param child_equations: Child definition equations.
    :return: Reference, parsed child, child block, parsed parent and parent block.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["inc(xp) = idref"],
        child_equations=child_equations,
        bound_names=["xp"],
    )
    parent_block.update_model(parent_block.out_vars[0], child_block.out_vars[0])
    return reference, parsed_child, child_block, parsed_parent, parent_block


def test_dgs_reference_state_with_a_circular_inc_starts_a_lag_at_its_equilibrium() -> None:
    """Start a lag whose enclosing ``inc()`` names its own output where its equation is at rest.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_circular_state_fixture(
        child_equations=["x. = (yi - x) / 0.1", "yo = x"],
    )
    child_x: Var = child_block.state_vars[0]
    child_yi: Var = child_block.in_vars[0]

    _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                     parsed_parent=parsed_parent, parent_block=parent_block)

    initial_value = parent_block.init_eqs[child_x]
    assert set(var.uid for var in initial_value.get_vars()) == {child_yi.uid}
    assert initial_value.eval_uid({child_yi.uid: 0.7}) == pytest.approx(0.7)


def test_dgs_reference_state_with_a_circular_inc_keeps_an_integrator_initialization() -> None:
    """Keep the declared ``inc()`` of an integrator, which has no rest point of its own.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_circular_state_fixture(
        child_equations=["x. = yi", "yo = x"],
    )
    child_x: Var = child_block.state_vars[0]
    child_yo: Var = child_block.out_vars[0]

    _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                     parsed_parent=parsed_parent, parent_block=parent_block)

    assert set(var.uid for var in parent_block.init_eqs[child_x].get_vars()) == {child_yo.uid}


def test_dgs_reference_state_with_a_circular_inc_keeps_a_nonlinear_initialization() -> None:
    """Keep the declared ``inc()`` when the state equation is not affine in the state.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_circular_state_fixture(
        child_equations=["x. = yi - x * x", "yo = x"],
    )
    child_x: Var = child_block.state_vars[0]
    child_yo: Var = child_block.out_vars[0]

    _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                     parsed_parent=parsed_parent, parent_block=parent_block)

    assert set(var.uid for var in parent_block.init_eqs[child_x].get_vars()) == {child_yo.uid}


def test_dgs_reference_state_with_a_circular_inc_and_a_vanishing_slope_stays_finite() -> None:
    """Keep the equilibrium seed finite where the slope of the lag vanishes at runtime.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_circular_state_fixture(
        child_equations=["x. = yi * (1 - x)", "yo = x"],
    )
    child_x: Var = child_block.state_vars[0]
    child_yi: Var = child_block.in_vars[0]

    _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                     parsed_parent=parsed_parent, parent_block=parent_block)

    initial_value = parent_block.init_eqs[child_x]
    assert initial_value.eval_uid({child_yi.uid: 0.5}) == pytest.approx(1.0)
    assert math.isfinite(initial_value.eval_uid({child_yi.uid: 0.0}))


def test_dgs_reference_state_with_a_circular_inc_and_no_symbolic_derivative_keeps_its_initialization() -> None:
    """Keep the declared ``inc()`` when the state equation has no symbolic derivative.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_circular_state_fixture(
        child_equations=["x. = (yi - x) / 0.1", "yo = x"],
    )
    child_x: Var = child_block.state_vars[0]
    child_yo: Var = child_block.out_vars[0]
    child_block.state_eqs[0] = child_block.state_eqs[0] * rand(child_x)

    _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                     parsed_parent=parsed_parent, parent_block=parent_block)

    assert set(var.uid for var in parent_block.init_eqs[child_x].get_vars()) == {child_yo.uid}


def test_dgs_reference_state_with_a_non_circular_inc_keeps_its_initialization() -> None:
    """Keep an enclosing ``inc()`` that names a variable the child does not compute from the state.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_state_binding_fixture(
        parent_equations=["inc(xp) = idref"],
        child_equations=["x. = (yi - x) / 0.1", "yo = x"],
        bound_names=["xp"],
    )
    child_x: Var = child_block.state_vars[0]
    parent_idref: Var = parent_block.out_vars[0]

    _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                     parsed_parent=parsed_parent, parent_block=parent_block)

    assert set(var.uid for var in parent_block.init_eqs[child_x].get_vars()) == {parent_idref.uid}


def test_dgs_reference_state_with_a_circular_inc_through_another_feedback_keeps_its_initialization() -> None:
    """Keep the declared ``inc()`` when the root of the state equation still reads a variable fed by the state.

    :return: None.
    """
    reference, parsed_child, child_block, parsed_parent, parent_block = _build_circular_state_fixture(
        child_equations=["x. = (yi - x) / 0.1 - 0.5 * yo", "yo = x"],
    )
    child_x: Var = child_block.state_vars[0]
    child_yo: Var = child_block.out_vars[0]

    _bind_graphical_reference_states(reference=reference, parsed_child=parsed_child, child_block=child_block,
                                     parsed_parent=parsed_parent, parent_block=parent_block)

    assert set(var.uid for var in parent_block.init_eqs[child_x].get_vars()) == {child_yo.uid}


def _build_nested_macro_tree(leaf_type_id: str | None,
                             middle_draws_inner: bool = False) -> DgsGraphicTreeResult | None:
    """Build the graphical parent with a nested macro child drawn from its own cables.

    GB REGC_C references ``PLL`` and ``vol_stator_voltage_REGC_C``: macro
    definitions without equations whose content is their own drawing. The
    nested input reuses the enclosing signal name ``external_x``, so a rescue
    by name would pull the enclosing nodes into the nested macro.

    :param leaf_type_id: Definition referenced by the node drawn inside the
        nested macro, or ``None`` for a nested macro without a drawing.
    :param middle_draws_inner: Add a ``MIDDLE_DEFINITION`` macro whose drawing
        references the nested macro again.
    :return: Graphical tree of the root slot.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]

    inner_definition: BlkDef = BlkDef()
    inner_definition.ID = "INNER_DEFINITION"
    inner_definition.loc_name = "Inner"
    inner_definition.isMacro = 1
    inner_definition.inputs = ["external_x"]
    inner_definition.outputs = ["yo"]
    leaf_definition: BlkDef = BlkDef()
    leaf_definition.ID = "LEAF_DEFINITION"
    leaf_definition.loc_name = "Leaf"
    leaf_definition.inputs = ["yi"]
    leaf_definition.outputs = ["yo"]
    leaf_definition.equations_raw = ["yo = 2 * yi"]
    circuit.blkdefs.extend([inner_definition, leaf_definition])

    inner_reference: BlkRef = BlkRef()
    inner_reference.ID = "INNER_REFERENCE"
    inner_reference.typ_id = inner_definition.ID
    inner_reference.cdisName = "Inner instance"
    circuit.blkrefs.append(inner_reference)
    cables: list[tuple[str, str, str]] = [("ROOT_TO_INNER", "MACRO", inner_reference.ID)]
    if leaf_type_id is not None:
        leaf_reference: BlkRef = BlkRef()
        leaf_reference.ID = "LEAF_REFERENCE"
        leaf_reference.typ_id = leaf_type_id
        leaf_reference.cdisName = "Leaf instance"
        circuit.blkrefs.append(leaf_reference)
        cables.append(("INNER_TO_LEAF", inner_definition.ID, leaf_reference.ID))
    else:
        pass
    if middle_draws_inner:
        middle_definition: BlkDef = BlkDef()
        middle_definition.ID = "MIDDLE_DEFINITION"
        middle_definition.loc_name = "Middle"
        middle_definition.isMacro = 1
        middle_definition.inputs = ["external_x"]
        middle_definition.outputs = ["yo"]
        circuit.blkdefs.append(middle_definition)
        back_reference: BlkRef = BlkRef()
        back_reference.ID = "BACK_REFERENCE"
        back_reference.typ_id = inner_definition.ID
        back_reference.cdisName = "Back instance"
        circuit.blkrefs.append(back_reference)
        cables.append(("MIDDLE_TO_BACK", middle_definition.ID, back_reference.ID))
    else:
        pass

    for signal_id, source, target in cables:
        signal: BlkSig = BlkSig()
        signal.ID = signal_id
        signal.loc_name = "external_x"
        signal.inodfrom = 0
        signal.iconfrom = 1
        signal.inodto = 0
        signal.iconto = 1
        signal.pnodfrom = source
        signal.pnodto = target
        circuit.blksigs.append(signal)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    return extract_root_slot_graphical_tree_from_circuit(
        circuit=circuit,
        result=root_result,
        slot_name="Graphical parent",
        graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
    )


def test_graphical_nested_macro_is_built_from_its_own_drawing() -> None:
    """Build a nested macro definition without equations from its own cables.

    :return: None.
    """
    graphical_tree: DgsGraphicTreeResult | None = _build_nested_macro_tree(leaf_type_id="LEAF_DEFINITION")

    assert graphical_tree is not None
    inner: Block = next(child for child in graphical_tree.view_block.children if child.name == "Inner instance")
    leaf: Block = next(child for child in inner.children if child.name == "Leaf instance")
    assert len(leaf.algebraic_eqs) == 1


def test_graphical_nested_macro_keeps_only_its_own_drawing() -> None:
    """Keep enclosing nodes that share a signal name out of a nested macro.

    :return: None.
    """
    graphical_tree: DgsGraphicTreeResult | None = _build_nested_macro_tree(leaf_type_id="LEAF_DEFINITION")

    assert graphical_tree is not None
    inner: Block = next(child for child in graphical_tree.view_block.children if child.name == "Inner instance")
    assert [child.name for child in inner.children] == ["Leaf instance"]


def test_graphical_nested_macro_without_a_drawing_keeps_its_equation_build() -> None:
    """Build a nested macro definition without a drawing from its equations, as before.

    Protected exports omit both the drawing and the equations; the REGC
    ElmGenstat adapter restores such blocks by structural contract.

    :return: None.
    """
    graphical_tree: DgsGraphicTreeResult | None = _build_nested_macro_tree(leaf_type_id=None)

    assert graphical_tree is not None
    inner: Block = next(child for child in graphical_tree.view_block.children if child.name == "Inner instance")
    assert inner.children == []


def test_graphical_nested_macro_referencing_an_enclosing_definition_fails_closed() -> None:
    """Reject a nested macro that draws a reference to a definition enclosing it.

    :return: None.
    """
    with pytest.raises(ValueError, match="enclosing macro definition"):
        _build_nested_macro_tree(leaf_type_id="INNER_DEFINITION")


def test_graphical_nested_macro_cycle_through_another_macro_fails_closed() -> None:
    """Reject a nested macro whose own nested macro draws a reference back to it.

    :return: None.
    """
    with pytest.raises(ValueError, match="enclosing macro definition"):
        _build_nested_macro_tree(leaf_type_id="MIDDLE_DEFINITION", middle_draws_inner=True)


def _build_limit_port_tree(connector: int) -> tuple[DgsGraphicTreeResult | None, str]:
    """Build the graphical parent with a root input cabled to limit port 0 of a child that also has limit parameters.

    :param connector: Target connector code, 4 for the upper limit and 3 for the lower limit.
    :return: Graphical tree and the child instance name.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    macro: BlkDef = next(definition for definition in circuit.blkdefs if definition.ID == "MACRO")
    macro.inputs.append("second_x")

    child_definition: BlkDef = BlkDef()
    child_definition.ID = "LIMITED_DEFINITION"
    child_definition.loc_name = "Limited lag"
    child_definition.inputs = ["yi"]
    child_definition.upper_limit_params = ["r_max"]
    child_definition.upper_limit_inputs = ["up_lim"]
    child_definition.lower_limit_params = ["r_min"]
    child_definition.lower_limit_inputs = ["low_lim"]
    # The DGS reader also lists limit parameters among the parameters.
    child_definition.params = ["r_max", "r_min"]
    child_definition.outputs = ["yo"]
    child_definition.equations_raw = ["yo = yi"]
    circuit.blkdefs.append(child_definition)
    child_reference: BlkRef = BlkRef()
    child_reference.ID = "LIMITED_REFERENCE"
    child_reference.typ_id = child_definition.ID
    child_reference.cdisName = "Limited instance"
    circuit.blkrefs.append(child_reference)
    signal: BlkSig = BlkSig()
    signal.ID = "ROOT_TO_LIMIT_PORT"
    signal.loc_name = "second_x"
    signal.inodfrom = macro.inputs.index("second_x")
    signal.iconfrom = 1
    signal.inodto = 0
    signal.iconto = connector
    signal.pnodfrom = "MACRO"
    signal.pnodto = child_reference.ID
    circuit.blksigs.append(signal)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    return extract_root_slot_graphical_tree_from_circuit(
        circuit=circuit,
        result=root_result,
        slot_name="Graphical parent",
        graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
    ), child_reference.cdisName


@pytest.mark.parametrize("connector,bound_input", [(4, "up_lim"), (3, "low_lim")])
def test_graphical_limit_port_binds_the_limit_input_not_the_limit_parameter(connector: int, bound_input: str) -> None:
    """Bind a cable on limit port 0 to the first limit input, never to a limit parameter.

    PowerFactory draws only limit inputs as ports. GB REGC_A cables Lvpl_lim to
    upper limit port 0 of a lag declaring r_max (parameter) and lvpl_lim (input);
    REEC_C and REEC_D cable freeze_up_s and freeze_low_s the same way.

    :param connector: Target connector code, 4 for the upper limit and 3 for the lower limit.
    :param bound_input: Limit input the cable must reach.
    :return: None.
    """
    graphical_tree, child_name = _build_limit_port_tree(connector=connector)

    assert graphical_tree is not None
    limited: Block = next(child for child in graphical_tree.view_block.children if child.name == child_name)
    expected: list[str] = ["yi", "r_max", "up_lim", "r_min", "low_lim"]
    expected[expected.index(bound_input)] = "second_x"
    assert [var.name.rsplit("__", 1)[-1] for var in limited.in_vars] == expected


def test_graphical_routed_limit_cable_binds_the_limit_input_by_name_and_keeps_the_parameter() -> None:
    """Bind a limit cable from a routing node by name, never a limit parameter.

    REEC_C and REEC_D cable freeze_up_s from a BlkFrom into upper limit port 0
    of a freeze PI declaring y_max (parameter) and freeze_up (input); REEC_C
    also has a sibling whose output is named y_max, which must not overwrite
    the parameter the BlkRef sets.

    :return: None.
    """
    circuit: DgsCircuit = DgsCircuit()
    circuit.parse_dgs(str(_get_graphical_parent_signal_binding_dgs_path()))
    root_element: ElmComp = circuit.elmcomps[0]
    macro: BlkDef = next(definition for definition in circuit.blkdefs if definition.ID == "MACRO")

    producer_definition: BlkDef = BlkDef()
    producer_definition.ID = "ROUTED_PRODUCER_DEFINITION"
    producer_definition.loc_name = "Routed producer"
    producer_definition.inputs = ["u"]
    producer_definition.outputs = ["up_lim", "r_max"]
    producer_definition.equations_raw = ["up_lim = 2*u", "r_max = 3*u"]
    circuit.blkdefs.append(producer_definition)
    limited_definition: BlkDef = BlkDef()
    limited_definition.ID = "ROUTED_LIMITED_DEFINITION"
    limited_definition.loc_name = "Routed limited lag"
    limited_definition.inputs = ["yi"]
    limited_definition.upper_limit_params = ["r_max"]
    limited_definition.upper_limit_inputs = ["up_lim"]
    # The DGS reader also lists limit parameters among the parameters.
    limited_definition.params = ["r_max"]
    limited_definition.outputs = ["yo"]
    limited_definition.equations_raw = ["yo = yi"]
    circuit.blkdefs.append(limited_definition)

    references: list[BlkRef] = list()
    definition: BlkDef
    for definition in (producer_definition, limited_definition):
        reference: BlkRef = BlkRef()
        reference.ID = definition.ID.replace("DEFINITION", "REFERENCE")
        reference.typ_id = definition.ID
        reference.cdisName = definition.loc_name
        circuit.blkrefs.append(reference)
        references.append(reference)
    producer_reference, limited_reference = references
    # A second limiter of the same definition with no limit cable, like the
    # REEC_C limiters whose y_max the BlkRef sets.
    unwired_reference: BlkRef = BlkRef()
    unwired_reference.ID = "ROUTED_UNWIRED_REFERENCE"
    unwired_reference.typ_id = limited_definition.ID
    unwired_reference.cdisName = "Unwired limited lag"
    circuit.blkrefs.append(unwired_reference)
    # The Goto writing the tag the BlkFrom reads, fed by the producer's up_lim
    routed_writer: BlkGoto = BlkGoto()
    routed_writer.ID = "GOTO_ROUTE"
    routed_writer.loc_name = "Write routed internal"
    routed_writer.signals = list((circuit.blkfroms[0].signals[0],))
    circuit.blkgotos.append(routed_writer)

    signal_specs: list[tuple[str, int, int, str, int, int, str]] = [
        ("PRODUCER_TO_GOTO", 2, 0, producer_reference.ID, 1, 0, routed_writer.ID),
        ("ROOT_TO_PRODUCER", 1, macro.inputs.index("external_x"), "MACRO", 1, 0, producer_reference.ID),
        ("ROOT_TO_LIMITED", 1, macro.inputs.index("external_x"), "MACRO", 1, 0, limited_reference.ID),
        ("ROUTE_TO_LIMIT_PORT", 2, 0, circuit.blkfroms[0].ID, 4, 0, limited_reference.ID),
        ("ROOT_TO_UNWIRED", 1, macro.inputs.index("external_x"), "MACRO", 1, 0, unwired_reference.ID),
    ]
    spec: tuple[str, int, int, str, int, int, str]
    for spec in signal_specs:
        signal: BlkSig = BlkSig()
        signal.ID, signal.iconfrom, signal.inodfrom, signal.pnodfrom = spec[0], spec[1], spec[2], spec[3]
        signal.iconto, signal.inodto, signal.pnodto = spec[4], spec[5], spec[6]
        signal.loc_name = "up_lim_s" if spec[0] in ("ROUTE_TO_LIMIT_PORT", "PRODUCER_TO_GOTO") else "external_x"
        circuit.blksigs.append(signal)

    root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        circuit=circuit,
        parsed_blocks=parse_dgs_block_definitions_from_circuit(circuit=circuit),
        root_name=root_element.loc_name,
        root_typ_id=root_element.typ_id,
        root_dgs_id=root_element.ID,
    )
    graphical_tree: DgsGraphicTreeResult | None = extract_root_slot_graphical_tree_from_circuit(
        circuit=circuit,
        result=root_result,
        slot_name="Graphical parent",
        graphical_indexes=build_dgs_graphical_indexes(circuit=circuit),
    )

    assert graphical_tree is not None
    children: dict[str, Block] = {child.name: child for child in graphical_tree.view_block.children}
    producer: Block = children[producer_reference.cdisName]
    limited: Block = children[limited_reference.cdisName]
    assert limited.in_vars[2] is producer.out_vars[0]
    assert limited.in_vars[1] is not producer.out_vars[1]
    assert limited.in_vars[1] in limited.event_dict
    unwired: Block = children[unwired_reference.cdisName]
    assert unwired.in_vars[1] is not producer.out_vars[1]
    assert unwired.in_vars[1] in unwired.event_dict


@pytest.mark.parametrize(
    ("patterns", "expected"),
    (
        (list(("ElmVsc*",)), True),
        (list(("ElmComp*",)), True),
        (list(("ElmPvsys*",)), False),
        (list(("ElmCom*",)), False),
        (list(), False),
    ),
)
def test_slot_filter_is_checked_only_against_registered_classes(patterns: list[str], expected: bool) -> None:
    """Verify a filter only when it names a class the DGS registry knows.

    :param patterns: Declared slot class patterns.
    :param expected: Whether the importer can verify the filter.
    :return: None.
    """
    assert _slot_filter_names_a_registered_class(element_kind_patterns=patterns) is expected
