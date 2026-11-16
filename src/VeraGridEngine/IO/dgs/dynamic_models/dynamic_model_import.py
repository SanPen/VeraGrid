# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import copy
import hashlib
import json
from enum import Enum, auto
from typing import Callable, Dict, List, Sequence, Set, Tuple

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_rms_measurement_binding import (
    _build_dgs_element_index,
    _build_voltage_alias_expressions,
    _build_current_alias_expressions,
    _build_power_alias_expressions,
    _build_pll_alias_expressions,
    _resolve_cubicle_source,
    _connect_meter_aliases,
    _translate_slot_blocks_to_runtime,
    _build_exact_meter_targets,
    _build_implicit_meter_target_by_slot,
    _get_native_source_target_signal_names,
    _get_veragrid_meter_name,
    _remove_meter_target_fallback_ownership,
    _resolve_native_pll_element,
)
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    DgsDirectRootBuildResult,
    DgsGraphicalIndexes,
    DgsGraphicTreeResult,
    DgsRootBlockResult,
    DgsSlotSignalDirection,
    DgsStandaloneBlockCatalogEntry,
    DgsStandaloneBlockOccurrence,
    ElmCompInstanceEntry,
    ParsedDgsBlockDefinition,
    UnsupportedDgsExpression,
    build_dgs_graphical_indexes,
    build_dgs_standalone_block_catalog_from_circuit,
    build_direct_root_elmcomp_block,
    build_standalone_blkdef_block,
    build_standalone_blkdef_block_from_parsed_block,
    build_dgs_root_block_from_circuit,
    extract_elmcomp_direct_instances,
    extract_root_slot_graphical_tree_from_circuit,
    get_blkslot_signal_interface,
    get_unique_elmcomp_slot_entries,
    list_dgs_blkref_catalog_occurrences_from_circuit,
    parse_dgs_block_definitions_from_circuit,
)
from VeraGridEngine.IO.dgs.dgs_objects import BlkSlot
from VeraGridEngine.IO.dgs.dgs_objects import DGSElement
from VeraGridEngine.IO.dgs.dgs_objects import ElmComp
from VeraGridEngine.IO.dgs.dgs_objects import ElmPhi
from VeraGridEngine.IO.dgs.dgs_objects import ElmSym, ElmGenstat, ElmVsc, ElmVscmono, ElmSvs
from VeraGridEngine.IO.dgs.dgs_objects import TypSym
from VeraGridEngine.IO.dgs.dgs_objects import StaImea
from VeraGridEngine.IO.dgs.dgs_objects import StaPqmea
from VeraGridEngine.IO.dgs.dgs_objects import StaVmea
from VeraGridEngine.IO.dynamic_model_import_types import (
    DynamicModelImportBundle,
    DynamicModelImportEntry,
    DynamicModelImportEntryAvailability,
    DynamicModelImportEntryResult,
    DynamicModelImportEntryStatus,
    DynamicModelImportReport,
    DynamicModelImportSelectionRequest,
    DynamicModelImportSource,
    DynamicModelImportSourceProvenance,
    _emit_dynamic_model_import_progress,
)
from VeraGridEngine.IO.dgs.dynamic_models.dgs_model_partition import (
    DgsModelPartition, assign_dgs_slot_owners, connect_dgs_partitions,
    copy_partition_diagrams, build_partition_diagram_connections,
)
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.IO.dgs.dynamic_models.dgs_dynamic_association import infer_dgs_dynamic_association_role
from VeraGridEngine.IO.dgs.dynamic_models.dgs_adapter_block_from_native_dgs import DgsElmSymMachineParameters
from VeraGridEngine.IO.dgs.dynamic_models.dgs_native_machine_parameters import build_dgs_elmsym_machine_parameters
from VeraGridEngine.IO.dgs.dynamic_models.dgs_native_model_workflow import (
    NativeDgsEquipmentKind,
    NativeDgsEquipmentPlan,
    assemble_native_dgs_model,
    construct_native_dgs_equipment,
    detect_native_dgs_equipment,
)
from VeraGridEngine.Utils.Symbolic.block import (
    Block,
    RmsPhysicalMeterKind,
    find_connections,
    rehash_block_var_keyed_dicts,
)
from VeraGridEngine.Utils.Symbolic.rms_measurements_functions import (
    build_rms_pll_measurements,
    build_rms_pll_measurements_from,
    build_rms_pll_measurements_to,
    build_rms_voltage_meter_outputs_from_dc_from,
    build_rms_voltage_meter_outputs_from_dc_to,
    build_rms_voltage_meter_outputs_from_dc,
    build_rms_voltage_meter_outputs_from_polar_from,
    build_rms_voltage_meter_outputs_from_polar_to,
    build_rms_voltage_meter_outputs_from_polar,
    find_measurements_for_inputs_group,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import (
    BlockType,
    DgsImportField,
    ConverterControlType,
    DeviceType,
    DgsDynamicAssociationRole,
    DynamicSimulationMode,
    RmsTerminalSide,
    VarPowerFlowReferenceType,
)

from VeraGridEngine.IO.dgs.dgs_import_metadata import (
    assign_import_template,
    DgsImportMetadata,
    set_import_field,
)


class DgsDynamicParserContractError(RuntimeError):
    """Report that the dynamic DGS parser boundary is incomplete."""


class _DgsRmsMeasurementConnection:
    """Describe one exact native-meter connection to a controller input.

    :param alias_name: Native output alias routed by the DGS signal graph.
    :param target_var: Exact controller input receiving the measurement.
    """

    __slots__ = ("alias_name", "target_var")

    def __init__(self, alias_name: str, target_var: Var) -> None:
        """Store one resolved producer-to-consumer endpoint.

        :param alias_name: Native output alias routed by the DGS signal graph.
        :param target_var: Exact controller input receiving the measurement.
        :return: None.
        """
        self.alias_name: str = alias_name
        self.target_var: Var = target_var


class _DgsRmsMeasurementSpec:
    """Carry native DGS meter semantics into early block materialization.

    :param source_fid: Stable native meter identity.
    :param source_name: Human-readable native meter name.
    :param meter_kind: Physical measurement family.
    :param meter_element: Parsed native meter configuration, when exported.
    :param connections: Exact controller endpoints driven by the meter.
    :param use_stationary_reference: Whether an ElmPhi exports a fixed frame.
    """

    __slots__ = (
        "source_fid",
        "source_name",
        "meter_kind",
        "meter_element",
        "connections",
        "use_stationary_reference",
    )

    def __init__(
            self,
            source_fid: str,
            source_name: str,
            meter_kind: RmsPhysicalMeterKind,
            meter_element: DGSElement | None,
            connections: List[_DgsRmsMeasurementConnection],
            use_stationary_reference: bool,
    ) -> None:
        """Store immutable-shape native measurement construction data.

        :param source_fid: Stable native meter identity.
        :param source_name: Human-readable native meter name.
        :param meter_kind: Physical measurement family.
        :param meter_element: Parsed native meter configuration, when exported.
        :param connections: Exact controller endpoints driven by the meter.
        :param use_stationary_reference: Whether an ElmPhi exports a fixed frame.
        :return: None.
        """
        self.source_fid: str = source_fid
        self.source_name: str = source_name
        self.meter_kind: RmsPhysicalMeterKind = meter_kind
        self.meter_element: DGSElement | None = meter_element
        self.connections: List[_DgsRmsMeasurementConnection] = connections
        self.use_stationary_reference: bool = use_stationary_reference


class DgsDynamicTemplateConversionResult:
    """Own the minimal transient state required after template conversion.

    The final templates are already owned by ``MultiCircuit``. Child-block
    lookups point into those same canonical block trees and exist only until
    exact device assignment and native measurement binding have completed.

    :param models_by_root_dgs_id: Installed physical or logical instances by root FID.
    :param templates_by_root_dgs_id: Single-host final templates indexed by root FID.
    :param partitions_by_root_dgs_id: Multi-host templates and transient ownership plans.
    :param child_blocks_by_root_and_slot_id: Canonical child blocks indexed by
        root FID and source slot FID for exact post-conversion binding.
    """

    __slots__ = (
        "templates_by_root_dgs_id",
        "child_blocks_by_root_and_slot_id",
        "models_by_root_dgs_id",
        "partitions_by_root_dgs_id",
    )

    def __init__(self) -> None:
        """Initialize empty fixed-purpose conversion lookups.

        :return: None.
        """
        self.partitions_by_root_dgs_id: Dict[str, List[DgsModelPartition]] = dict()
        self.models_by_root_dgs_id: Dict[str, Block] = dict()
        self.templates_by_root_dgs_id: Dict[
            str,
            RmsModelTemplate | EmtModelTemplate
        ] = dict()
        self.child_blocks_by_root_and_slot_id: Dict[
            str,
            Dict[str, Block],
        ] = dict()


class _DgsElmCompRelationKind(Enum):
    """Classify one direct DGS relation before any block is executed."""

    __slots__ = ()

    DYNAMIC_CANDIDATE = auto()
    PHYSICAL_REFERENCE = auto()
    OPAQUE_REFERENCE = auto()
    INVALID = auto()


class _DgsElmCompRelationClassification:
    """Carry one typed DGS relation decision and its evidence.

    :param kind: Exact non-executable or dynamic relation kind.
    :param reason: Human-readable evidence behind the decision.
    """

    __slots__ = ("_kind", "_reason")

    def __init__(
            self,
            kind: _DgsElmCompRelationKind,
            reason: str,
    ) -> None:
        """Store one relation decision.

        :param kind: Exact non-executable or dynamic relation kind.
        :param reason: Human-readable evidence behind the decision.
        :return: None.
        """
        self._kind: _DgsElmCompRelationKind = kind
        self._reason: str = reason

    def get_kind(self) -> _DgsElmCompRelationKind:
        """Return the typed relation kind.

        :return: Exact classification kind.
        """
        return self._kind

    def get_reason(self) -> str:
        """Return the evidence behind the relation decision.

        :return: Human-readable classification evidence.
        """
        return self._reason


def _classify_dgs_elmcomp_relation(
        entry: ElmCompInstanceEntry,
        unique_slot_indices: Set[int],
) -> _DgsElmCompRelationClassification:
    """Classify one direct ``ElmComp`` relation without using display names.

    A unique resolved ``pblk`` establishes the source slot envelope. A complete
    resolved dynamic target may then be materialized. Resolved physical targets
    and intentionally empty physical or vendor slots remain visible metadata,
    while missing, unresolved or repeated slot references and unresolved
    supplied targets fail closed.

    :param entry: Exact direct relation extracted from the DGS document.
    :param unique_slot_indices: Ordinals whose ``pblk`` resolves uniquely.
    :return: Typed pre-execution relation classification.
    """
    physical_roles: Set[DgsDynamicAssociationRole] = set([
        DgsDynamicAssociationRole.PhysicalHost,
        DgsDynamicAssociationRole.Measurement,
        DgsDynamicAssociationRole.SwitchActuator,
        DgsDynamicAssociationRole.ValveActuator,
        DgsDynamicAssociationRole.PassiveActuator,
    ])

    if entry.slot_index is None or entry.slot_index not in unique_slot_indices:
        if entry.slot_id is None:
            invalid_reason: str = "missing pblk slot reference"
        else:
            if not entry.slot_reference_is_resolved:
                invalid_reason = "unresolved pblk slot reference"
            else:
                invalid_reason = "repeated pblk slot reference"
        return _DgsElmCompRelationClassification(
            kind=_DgsElmCompRelationKind.INVALID,
            reason=invalid_reason,
        )
    else:
        pass

    association_role: DgsDynamicAssociationRole = (
        infer_dgs_dynamic_association_role(
            slot_index=entry.slot_index,
            source_element_class=entry.element_kind,
            slot_filter=entry.slot_filter,
        )
    )

    if entry.element_id is None:
        if association_role in physical_roles:
            empty_kind: _DgsElmCompRelationKind = (
                _DgsElmCompRelationKind.PHYSICAL_REFERENCE
            )
            empty_reason: str = "physical slot has no exported pElm target"
        else:
            empty_kind = _DgsElmCompRelationKind.OPAQUE_REFERENCE
            empty_reason = "slot has no exported pElm target"
        return _DgsElmCompRelationClassification(
            kind=empty_kind,
            reason=empty_reason,
        )
    else:
        pass

    if not entry.element_reference_is_resolved:
        return _DgsElmCompRelationClassification(
            kind=_DgsElmCompRelationKind.INVALID,
            reason="unresolved supplied pElm target",
        )
    else:
        pass

    if entry.element_kind == "ElmDsl" or entry.element_kind == "ElmComp":
        if entry.type_id is None:
            return _DgsElmCompRelationClassification(
                kind=_DgsElmCompRelationKind.INVALID,
                reason="dynamic pElm target has no exported type reference",
            )
        else:
            return _DgsElmCompRelationClassification(
                kind=_DgsElmCompRelationKind.DYNAMIC_CANDIDATE,
                reason="complete dynamic pblk/pelm relation",
            )
    else:
        pass

    if entry.type_id is None:
        if association_role in physical_roles:
            resolved_kind: _DgsElmCompRelationKind = (
                _DgsElmCompRelationKind.PHYSICAL_REFERENCE
            )
            resolved_reason: str = "resolved physical pElm target"
        else:
            resolved_kind = _DgsElmCompRelationKind.OPAQUE_REFERENCE
            resolved_reason = "resolved non-dynamic pElm target"
        return _DgsElmCompRelationClassification(
            kind=resolved_kind,
            reason=resolved_reason,
        )
    else:
        return _DgsElmCompRelationClassification(
            kind=_DgsElmCompRelationKind.INVALID,
            reason="non-dynamic pElm target declares a dynamic type reference",
        )


def _select_root_frame_display_name(root_block: Block) -> str | None:
    """
    Select the composite frame name used to group one imported PWM root.

    :param root_block: Parsed imported root block.
    :return: Preferred frame display name, or ``None``.
    """
    candidate_names: List[str] = list()
    child_block: Block
    child_name: str

    for child_block in root_block.children:
        child_name = str(child_block.name)

        if child_name == "VSC_Frame":
            return child_name
        else:
            if child_name.startswith("VSC_Frame"):
                candidate_names.append(child_name)
            else:
                pass

    if len(candidate_names) == 0:
        return None
    else:
        candidate_names.sort(key=len)
        return candidate_names[0]


def _build_dgs_non_executable_slot_notes(
        circuit: DgsCircuit,
        root_name: str,
        entry: ElmCompInstanceEntry,
) -> str:
    """
    Build notes for a DGS slot that has no materialized block.

    :param circuit: Parsed DGS circuit.
    :param root_name: Root ElmComp display name.
    :param entry: Direct slot entry.
    :return: Human-readable notes text.
    """
    incoming_signals, outgoing_signals = get_blkslot_signal_interface(
        circuit=circuit,
        slot_id=entry.slot_id,
    )
    notes_parts: List[str] = [f"Root: {root_name}", "Non-executable slot"]
    slot_obj: BlkSlot | None = None
    candidate_slot: BlkSlot

    if entry.slot_id is None:
        pass
    else:
        # The raw BlkSlot carries the physical interface metadata even when no ElmDsl/BlkDef exists behind it.
        for candidate_slot in circuit.blkslots:
            if str(candidate_slot.ID) == str(entry.slot_id):
                slot_obj = candidate_slot
                break
            else:
                pass

    if slot_obj is None:
        pass
    else:
        # The filter and slot IO names make the imported topology readable for valves, switches and measurements.
        if str(slot_obj.filtmod).strip() != "":
            notes_parts.append(f"filter: {slot_obj.filtmod}")
        else:
            pass

        if len(slot_obj.outputs) > 0:
            notes_parts.append(f"slot outputs: {', '.join(slot_obj.outputs)}")
        else:
            pass

        if len(slot_obj.inputs) > 0:
            notes_parts.append(f"slot inputs: {', '.join(slot_obj.inputs)}")
        else:
            pass

    if len(outgoing_signals) > 0:
        notes_parts.append(f"outputs: {', '.join(outgoing_signals)}")
    else:
        pass

    if len(incoming_signals) > 0:
        notes_parts.append(f"inputs: {', '.join(incoming_signals)}")
    else:
        pass

    return " | ".join(notes_parts)


def _build_dgs_import_source_provenance(
        root_element: ElmComp,
        direct_entry: ElmCompInstanceEntry | None = None,
) -> DynamicModelImportSourceProvenance:
    """
    Build typed provenance for one root or direct ElmComp slot entry.

    :param root_element: Owning root ElmComp.
    :param direct_entry: Optional direct pBlk/pElm slot relation.
    :return: Typed root/slot/element source provenance.
    """
    if direct_entry is None:
        slot_dgs_id: str | None = None
        slot_name: str | None = None
        slot_index: int | None = None
        slot_element: str | None = None
        slot_filter: str | None = None
        source_element_dgs_id: str | None = None
        source_element_name: str | None = None
        source_element_class: str | None = None
    else:
        slot_dgs_id = direct_entry.slot_id
        slot_name = direct_entry.slot_name
        slot_index = direct_entry.slot_index
        slot_element = direct_entry.slot_element
        slot_filter = direct_entry.slot_filter
        source_element_dgs_id = direct_entry.element_id
        source_element_name = direct_entry.element_name
        source_element_class = direct_entry.element_kind

    source_provenance: DynamicModelImportSourceProvenance = (
        DynamicModelImportSourceProvenance(
            root_dgs_id=root_element.ID,
            root_name=root_element.loc_name,
            root_typ_id=root_element.typ_id,
            slot_dgs_id=slot_dgs_id,
            slot_name=slot_name,
            slot_index=slot_index,
            slot_element=slot_element,
            slot_filter=slot_filter,
            source_element_dgs_id=source_element_dgs_id,
            source_element_name=source_element_name,
            source_element_class=source_element_class,
        )
    )
    return source_provenance


def _build_dgs_root_elmcomp_entries_with_progress(
        dgs_path: str,
        progress_callback: Callable[[int, str], None] | None,
        progress_start: int,
        progress_end: int,
        dgs_circuit: DgsCircuit | None = None,
        parsed_dgs_blocks: Dict[str, ParsedDgsBlockDefinition] | None = None,
) -> Tuple[List[DynamicModelImportEntry], Logger]:
    """
    Build root ``ElmComp`` import entries while emitting progress updates.

    :param dgs_path: Source DGS path.
    :param progress_callback: Optional UI progress callback.
    :param progress_start: Inclusive start percentage for this phase.
    :param progress_end: Inclusive end percentage for this phase.
    :param dgs_circuit: Optional circuit already parsed for the massive import.
    :param parsed_dgs_blocks: Optional definitions parsed from ``dgs_circuit``.
    :return: Pair ``(entries, logger)``.
    """
    circuit: DgsCircuit
    entries: List[DynamicModelImportEntry] = list()
    logger: Logger = Logger()
    root_element: ElmComp
    root_result: DgsRootBlockResult | None
    root_block: Block | None
    root_entry: DynamicModelImportEntry
    root_direct_entries: List[ElmCompInstanceEntry]
    unique_slot_entries: List[ElmCompInstanceEntry]
    unique_slot_entry: ElmCompInstanceEntry
    unique_slot_indices: Set[int]
    direct_entry: ElmCompInstanceEntry
    relation_classification: _DgsElmCompRelationClassification
    relation_kind: _DgsElmCompRelationKind
    frame_display_name: str | None
    frame_entry_key: str | None
    slot_display_name: str
    non_executable_notes_text: str
    slot_notes_text: str
    slot_parent_key: str
    slot_identity: str
    slot_availability: DynamicModelImportEntryAvailability
    graph_tree: DgsGraphicTreeResult | None
    cached_slot_block: Block | None
    materialized_slot_block: Block | None
    parsed_slot_block: ParsedDgsBlockDefinition | None
    effective_type_id: str | None
    total_root_count: int
    total_slot_count: int = 0
    total_steps: int
    completed_steps: int = 0
    processed_root_count: int = 0
    processed_slot_count: int = 0
    progress_span: int = progress_end - progress_start
    current_progress_value: int
    root_source_provenance: DynamicModelImportSourceProvenance
    slot_source_provenance: DynamicModelImportSourceProvenance
    direct_child_block_by_slot_id: Dict[str, Block]
    direct_graphical_tree_by_slot_id: Dict[
        str,
        DgsGraphicTreeResult,
    ]
    reported_unresolved_graphical_contracts: Set[Tuple[str, ...]] = set()

    if dgs_circuit is None:
        circuit = DgsCircuit()
        circuit.parse_dgs(dgs_path)
    else:
        circuit = dgs_circuit
    total_root_count = len(circuit.elmcomps)

    for root_element in circuit.elmcomps:
        total_slot_count += len(extract_elmcomp_direct_instances(circuit, root_element))

    total_steps = total_root_count + total_slot_count
    if total_steps <= 0:
        _emit_dynamic_model_import_progress(progress_callback, progress_end, "DGS root catalogue ready")
        return entries, logger
    else:
        pass

    # Parsing BlkDef expressions is independent of the concrete ElmDsl
    # parameters. Share those parsed definitions across every root in a massive DGS
    # import, while each root below still materializes its own instances.
    shared_parsed_dgs_blocks: Dict[str, ParsedDgsBlockDefinition]
    if parsed_dgs_blocks is None:
        shared_parsed_dgs_blocks = parse_dgs_block_definitions_from_circuit(
            circuit=circuit
        )
    else:
        shared_parsed_dgs_blocks = parsed_dgs_blocks
    graphical_indexes: DgsGraphicalIndexes = (
        build_dgs_graphical_indexes(circuit=circuit)
    )

    for root_element in circuit.elmcomps:
        root_direct_entries = list(extract_elmcomp_direct_instances(circuit, root_element))
        unique_slot_entries = get_unique_elmcomp_slot_entries(
            entries=root_direct_entries,
        )
        unique_slot_indices = set()
        for unique_slot_entry in unique_slot_entries:
            if unique_slot_entry.slot_index is None:
                pass
            else:
                unique_slot_indices.add(unique_slot_entry.slot_index)
        root_entry_key: str = f"dgs-root|{root_element.ID}"
        root_source_provenance = _build_dgs_import_source_provenance(
            root_element=root_element
        )
        try:
            root_result = build_dgs_root_block_from_circuit(
                circuit=circuit,
                parsed_blocks=shared_parsed_dgs_blocks,
                root_name=root_element.loc_name,
                root_typ_id=root_element.typ_id,
                root_dgs_id=root_element.ID,
            )
        except Exception as exc:
            logger.add_warning(
                msg="DGS root ElmComp import skipped",
                value=f"{root_element.loc_name}: {exc}",
            )
            root_result = None
        else:
            pass

        processed_root_count += 1
        completed_steps += 1
        current_progress_value = progress_start + int(
            round(progress_span * float(completed_steps) / float(total_steps)))
        _emit_dynamic_model_import_progress(
            progress_callback,
            current_progress_value,
            f"Importing DGS roots: {processed_root_count}/{total_root_count}",
        )

        if root_result is None:
            # A failed root remains a catalogue node so the report does not
            # hide the source object or any of its exact pblk/pelm relations.
            entries.append(
                DynamicModelImportEntry(
                    unique_key=root_entry_key,
                    display_name=root_element.loc_name,
                    source_tpe=DynamicModelImportSource.PowerFactoryDgs,
                    source_block=None,
                    notes_text="Root ElmComp could not be materialized",
                    source_provenance=root_source_provenance,
                )
            )

            for direct_entry in root_direct_entries:
                if direct_entry.slot_id is None:
                    slot_identity = f"index-{direct_entry.slot_index}"
                else:
                    slot_identity = str(direct_entry.slot_id)

                if direct_entry.slot_name is None:
                    slot_display_name = f"Slot {direct_entry.slot_index}"
                else:
                    slot_display_name = str(direct_entry.slot_name)

                slot_source_provenance = _build_dgs_import_source_provenance(
                    root_element=root_element,
                    direct_entry=direct_entry,
                )
                entries.append(
                    DynamicModelImportEntry(
                        unique_key=f"dgs-unavailable|{root_element.ID}|{slot_identity}|{direct_entry.element_id}",
                        display_name=slot_display_name,
                        source_tpe=DynamicModelImportSource.PowerFactoryDgs,
                        source_block=None,
                        notes_text=(
                            f"Root: {root_element.loc_name} | "
                            "Slot unavailable because its root could not be materialized"
                        ),
                        parent_key=root_entry_key,
                        source_provenance=slot_source_provenance,
                    )
                )
                processed_slot_count += 1
                completed_steps += 1
                current_progress_value = progress_start + int(
                    round(progress_span * float(completed_steps) / float(total_steps))
                )
                _emit_dynamic_model_import_progress(
                    progress_callback,
                    current_progress_value,
                    f"Importing DGS slots: {processed_slot_count}/{total_slot_count}",
                )
        else:
            try:
                direct_root_build_result: DgsDirectRootBuildResult = (
                    build_direct_root_elmcomp_block(
                        circuit=circuit,
                        result=root_result,
                        graphical_indexes=graphical_indexes,
                    )
                )
                direct_root_block: Block = direct_root_build_result.root_block
                direct_child_block_by_slot_id = (
                    direct_root_build_result.child_block_by_slot_id
                )
                direct_graphical_tree_by_slot_id = (
                    direct_root_build_result.graphical_tree_by_slot_id
                )
                root_block = direct_root_block
                root_block.name = root_element.loc_name
            except Exception as exc:
                logger.add_warning(
                    msg="DGS root ElmComp materialization skipped",
                    value=f"{root_element.loc_name}: {exc}",
                )
                root_block = None
                direct_child_block_by_slot_id = dict()
                direct_graphical_tree_by_slot_id = dict()
                # Keep the independently parsed pblk/pelm relations so every
                # failed slot remains visible in the partial-import report.
                root_direct_entries = list(root_direct_entries)

            if root_block is None:
                frame_display_name = None
            else:
                frame_display_name = _select_root_frame_display_name(root_result.root_block)
            frame_entry_key = None

            if root_block is None:
                entries.append(
                    DynamicModelImportEntry(
                        unique_key=root_entry_key,
                        display_name=root_element.loc_name,
                        source_tpe=DynamicModelImportSource.PowerFactoryDgs,
                        source_block=None,
                        notes_text="Root ElmComp block could not be materialized",
                        source_provenance=root_source_provenance,
                    )
                )
            else:
                root_entry = DynamicModelImportEntry(
                    unique_key=root_entry_key,
                    display_name=root_element.loc_name,
                    source_tpe=DynamicModelImportSource.PowerFactoryDgs,
                    source_block=root_block,
                    notes_text="Root ElmComp block",
                    source_provenance=root_source_provenance,
                )
                entries.append(root_entry)

            if frame_display_name is None:
                pass
            else:
                frame_entry_key = f"dgs-frame|{root_element.ID}|{root_element.typ_id}"
                entries.append(
                    DynamicModelImportEntry(
                        unique_key=frame_entry_key,
                        display_name=frame_display_name,
                        source_tpe=DynamicModelImportSource.PowerFactoryDgs,
                        source_block=None,
                        notes_text=f"Root: {root_element.loc_name} | Composite frame",
                        parent_key=root_entry_key,
                        source_provenance=root_source_provenance,
                        availability=DynamicModelImportEntryAvailability.MetadataOnly,
                    )
                )

            for direct_entry in root_direct_entries:
                relation_classification = _classify_dgs_elmcomp_relation(
                    entry=direct_entry,
                    unique_slot_indices=unique_slot_indices,
                )
                relation_kind = relation_classification.get_kind()
                slot_parent_key = (
                    root_entry_key
                    if frame_entry_key is None
                    else frame_entry_key
                )
                if direct_entry.slot_name is None:
                    slot_display_name = f"Slot {direct_entry.slot_index}"
                else:
                    slot_display_name = str(direct_entry.slot_name)
                if direct_entry.slot_id is None:
                    slot_identity = f"index-{direct_entry.slot_index}"
                else:
                    slot_identity = str(direct_entry.slot_id)
                slot_source_provenance = _build_dgs_import_source_provenance(
                    root_element=root_element,
                    direct_entry=direct_entry,
                )

                if relation_kind != _DgsElmCompRelationKind.DYNAMIC_CANDIDATE:
                    if relation_kind == _DgsElmCompRelationKind.INVALID:
                        slot_availability = (
                            DynamicModelImportEntryAvailability.Failed
                        )
                        slot_notes_text = (
                            f"Root: {root_element.loc_name} | Invalid relation: "
                            f"{relation_classification.get_reason()}"
                        )
                    else:
                        slot_availability = (
                            DynamicModelImportEntryAvailability.MetadataOnly
                        )
                        non_executable_notes_text = (
                            _build_dgs_non_executable_slot_notes(
                                circuit=circuit,
                                root_name=root_element.loc_name,
                                entry=direct_entry,
                            )
                        )
                        slot_notes_text = (
                            f"{non_executable_notes_text}"
                            f" | Relation: {relation_classification.get_reason()}"
                        )
                    entries.append(
                        DynamicModelImportEntry(
                            unique_key=f"dgs-metadata|{root_element.ID}|{slot_identity}|{direct_entry.element_id}",
                            display_name=slot_display_name,
                            source_tpe=DynamicModelImportSource.PowerFactoryDgs,
                            source_block=None,
                            notes_text=slot_notes_text,
                            parent_key=slot_parent_key,
                            source_provenance=slot_source_provenance,
                            availability=slot_availability,
                        )
                    )
                    processed_slot_count += 1
                    completed_steps += 1
                    current_progress_value = progress_start + int(
                        round(progress_span * float(completed_steps) / float(total_steps))
                    )
                    _emit_dynamic_model_import_progress(
                        progress_callback,
                        current_progress_value,
                        f"Importing DGS slots: {processed_slot_count}/{total_slot_count}",
                    )
                else:
                    slot_template_name: str = (
                        f"{root_element.loc_name}::{slot_display_name}"
                    )
                    slot_block: Block | None
                    effective_type_id = direct_entry.type_id

                    if effective_type_id is None:
                        slot_availability = (
                            DynamicModelImportEntryAvailability.Failed
                        )
                        slot_notes_text = (
                            f"Root: {root_element.loc_name} | "
                            "Dynamic relation has no executable type reference"
                        )
                        entries.append(
                            DynamicModelImportEntry(
                                unique_key=(
                                    f"dgs-unavailable|{root_element.ID}|"
                                    f"{slot_identity}|{direct_entry.element_id}"
                                ),
                                display_name=slot_display_name,
                                source_tpe=DynamicModelImportSource.PowerFactoryDgs,
                                source_block=None,
                                notes_text=slot_notes_text,
                                parent_key=slot_parent_key,
                                source_provenance=slot_source_provenance,
                                availability=slot_availability,
                            )
                        )
                    else:
                        # Reuse the exact child materialized while building the
                        # composite root. This avoids parsing the same graphical
                        # controller twice during a massive DGS import.
                        if direct_entry.slot_id is None:
                            cached_slot_block = None
                            graph_tree = None
                        else:
                            slot_id: str = str(direct_entry.slot_id)
                            cached_slot_block = (
                                direct_child_block_by_slot_id.get(
                                    slot_id,
                                    None,
                                )
                            )
                            graph_tree = direct_graphical_tree_by_slot_id.get(
                                slot_id,
                                None,
                            )

                        if cached_slot_block is None:
                            if graph_tree is None:
                                try:
                                    graph_tree = extract_root_slot_graphical_tree_from_circuit(
                                        circuit=circuit,
                                        result=root_result,
                                        slot_name=slot_display_name,
                                        slot_dgs_id=direct_entry.slot_id,
                                        graphical_indexes=graphical_indexes,
                                    )
                                except Exception as exc:
                                    logger.add_warning(
                                        msg="DGS slot import skipped",
                                        value=f"{root_element.loc_name}/{slot_display_name}: {exc}",
                                    )
                                    graph_tree = None
                                else:
                                    pass
                            else:
                                pass

                            if graph_tree is None:
                                materialized_slot_block = None
                            else:
                                materialized_slot_block = graph_tree.view_block
                        else:
                            materialized_slot_block = cached_slot_block

                        if graph_tree is None:
                            unresolved_graphical_input_names: List[str] = list()
                        else:
                            unresolved_graphical_input_names = list(
                                graph_tree.parent_bindings.unresolved_input_names
                            )
                        unresolved_graphical_input_names.sort()
                        if len(unresolved_graphical_input_names) == 0:
                            pass
                        else:
                            unresolved_contract_parts: List[str] = list()
                            unresolved_contract_parts.append(effective_type_id)
                            unresolved_contract_parts.extend(
                                unresolved_graphical_input_names
                            )
                            unresolved_contract_key: Tuple[str, ...] = tuple(
                                unresolved_contract_parts
                            )
                            if unresolved_contract_key in reported_unresolved_graphical_contracts:
                                pass
                            else:
                                reported_unresolved_graphical_contracts.add(
                                    unresolved_contract_key
                                )
                                logger.add_warning(
                                    msg="DGS graphical operator topology incomplete",
                                    value=(
                                        f"{direct_entry.type_name}: live routed inputs "
                                        f"{unresolved_graphical_input_names} have no exported "
                                        "producer. Re-export with BlkDiv, BlkMul and BlkSwt "
                                        "monitors in DGS Export Definitions 7_2/Export DGS."
                                    ),
                                )

                        if materialized_slot_block is None:
                            parsed_slot_block = root_result.parsed_blocks.get(
                                effective_type_id,
                                None,
                            )
                            try:
                                if parsed_slot_block is None:
                                    slot_block = build_standalone_blkdef_block(
                                        dgs_path=dgs_path,
                                        typ_id=effective_type_id,
                                        block_name=slot_template_name,
                                    )
                                else:
                                    slot_block = build_standalone_blkdef_block_from_parsed_block(
                                        parsed_block=parsed_slot_block,
                                        block_name=slot_template_name,
                                    )
                            except Exception as exc:
                                logger.add_warning(
                                    msg="DGS slot block materialization skipped",
                                    value=f"{root_element.loc_name}/{slot_display_name}: {exc}",
                                )
                                slot_block = None

                            if slot_block is None:
                                entries.append(
                                    DynamicModelImportEntry(
                                        unique_key=(
                                            f"dgs-unavailable|{root_element.ID}|"
                                            f"{slot_identity}|{direct_entry.element_id}"
                                        ),
                                        display_name=slot_display_name,
                                        source_tpe=DynamicModelImportSource.PowerFactoryDgs,
                                        source_block=None,
                                        notes_text=(
                                            f"Root: {root_element.loc_name} | "
                                            f"Slot: {slot_display_name} | Block could not be materialized"
                                        ),
                                        parent_key=slot_parent_key,
                                        source_provenance=slot_source_provenance,
                                    )
                                )
                            else:
                                entries.append(
                                    DynamicModelImportEntry(
                                        unique_key=f"dgs-slot|{root_element.ID}|{slot_identity}|{direct_entry.element_id}",
                                        display_name=slot_display_name,
                                        source_tpe=DynamicModelImportSource.PowerFactoryDgs,
                                        source_block=slot_block,
                                        notes_text=f"Root: {root_element.loc_name} | Slot: {slot_display_name}",
                                        parent_key=slot_parent_key,
                                        source_provenance=slot_source_provenance,
                                    )
                                )
                        else:
                            try:
                                slot_block = materialized_slot_block
                                slot_block.name = slot_template_name
                            except Exception as exc:
                                logger.add_warning(
                                    msg="DGS graphical slot materialization skipped",
                                    value=f"{root_element.loc_name}/{slot_display_name}: {exc}",
                                )
                                slot_block = None

                            if slot_block is None:
                                entries.append(
                                    DynamicModelImportEntry(
                                        unique_key=(
                                            f"dgs-unavailable|{root_element.ID}|"
                                            f"{slot_identity}|{direct_entry.element_id}"
                                        ),
                                        display_name=slot_display_name,
                                        source_tpe=DynamicModelImportSource.PowerFactoryDgs,
                                        source_block=None,
                                        notes_text=(
                                            f"Root: {root_element.loc_name} | "
                                            f"Slot: {slot_display_name} | Graph could not be materialized"
                                        ),
                                        parent_key=slot_parent_key,
                                        source_provenance=slot_source_provenance,
                                    )
                                )
                            else:
                                entries.append(
                                    DynamicModelImportEntry(
                                        unique_key=f"dgs-slot|{root_element.ID}|{slot_identity}|{direct_entry.element_id}",
                                        display_name=slot_display_name,
                                        source_tpe=DynamicModelImportSource.PowerFactoryDgs,
                                        source_block=slot_block,
                                        notes_text=f"Root: {root_element.loc_name} | Slot: {slot_display_name}",
                                        parent_key=slot_parent_key,
                                        source_provenance=slot_source_provenance,
                                    )
                                )

                    processed_slot_count += 1
                    completed_steps += 1
                    current_progress_value = progress_start + int(
                        round(progress_span * float(completed_steps) / float(total_steps)))
                    _emit_dynamic_model_import_progress(
                        progress_callback,
                        current_progress_value,
                        f"Importing DGS slots: {processed_slot_count}/{total_slot_count}",
                    )

    _emit_dynamic_model_import_progress(progress_callback, progress_end, "DGS root and slot catalogue ready")
    return entries, logger


def build_dgs_dynamic_model_import_bundle(
        dgs_path: str,
        progress_callback: Callable[[int, str], None] | None = None,
        dgs_circuit: DgsCircuit | None = None,
) -> Tuple[DynamicModelImportBundle, Logger]:
    """
    Parse one PowerFactory DGS file into domain-neutral block candidates.

    :param dgs_path: Source DGS path.
    :param progress_callback: Optional UI progress callback.
    :param dgs_circuit: Optional circuit already parsed by the static importer.
    :return: Pair ``(bundle, logger)``.
    """
    logger: Logger = Logger()
    shared_circuit: DgsCircuit
    shared_parsed_blocks: Dict[str, ParsedDgsBlockDefinition]
    catalog_entries: List[DgsStandaloneBlockCatalogEntry]
    bundle_entries: List[DynamicModelImportEntry] = list()
    root_entries: List[DynamicModelImportEntry]
    root_logger: Logger
    catalog_entry: DgsStandaloneBlockCatalogEntry

    # Static and dynamic import consume the same ASCII object graph. Reuse that
    # graph so a massive DGS is parsed once and every catalogue/root view is
    # guaranteed to observe the same source objects.
    if dgs_circuit is None:
        shared_circuit = DgsCircuit()
        shared_circuit.parse_dgs(dgs_path)
    else:
        shared_circuit = dgs_circuit
    shared_parsed_blocks = parse_dgs_block_definitions_from_circuit(
        circuit=shared_circuit
    )

    _emit_dynamic_model_import_progress(progress_callback, 0, "Scanning DGS dynamic model structure...")
    try:
        catalog_entries = build_dgs_standalone_block_catalog_from_circuit(
            circuit=shared_circuit,
            parsed_blocks=shared_parsed_blocks,
            isolated_only=False,
        )
    except Exception as exc:
        catalog_entries = list()
        logger.add_warning(
            msg="Standalone DGS dynamic-model catalogue skipped",
            value=str(exc),
        )
    _emit_dynamic_model_import_progress(progress_callback, 15, "Building standalone DGS block catalogue...")

    for catalog_entry in catalog_entries:
        source_block: Block | None = None
        notes_lines: List[str] = list()
        notes_text: str

        if catalog_entry.build_error is None:
            try:
                source_block = build_standalone_blkdef_block_from_parsed_block(
                    parsed_block=shared_parsed_blocks[catalog_entry.typ_id],
                    block_name=catalog_entry.blkdef_name,
                )
            except Exception as exc:
                notes_lines.append(f"Build error: {exc}")
                logger.add_warning(
                    msg="DGS dynamic block build error",
                    value=f"{catalog_entry.blkdef_name}: {exc}",
                )
        else:
            notes_lines.append(f"Build error: {catalog_entry.build_error}")
            logger.add_warning(msg="DGS dynamic block build error", value=catalog_entry.build_error)

        if len(catalog_entry.unsupported_lines) > 0:
            notes_lines.append(f"Unsupported statements: {len(catalog_entry.unsupported_lines)}")
        else:
            pass

        notes_lines.append(
            f"Occurrences: {catalog_entry.occurrence_count} | Isolated: {catalog_entry.isolated_occurrence_count} | Connected: {catalog_entry.connected_occurrence_count}"
        )
        notes_text = "\n".join(notes_lines)

        bundle_entries.append(
            DynamicModelImportEntry(
                unique_key=f"dgs|{catalog_entry.typ_id}|{catalog_entry.blkdef_name}",
                display_name=catalog_entry.blkdef_name,
                source_tpe=DynamicModelImportSource.PowerFactoryDgs,
                source_block=source_block,
                notes_text=notes_text,
            )
        )

    if len(shared_circuit.elmcomps) == 0:
        root_entries = list()
        root_logger = Logger()
    else:
        try:
            root_entries, root_logger = _build_dgs_root_elmcomp_entries_with_progress(
                dgs_path=dgs_path,
                progress_callback=progress_callback,
                progress_start=15,
                progress_end=95,
                dgs_circuit=shared_circuit,
                parsed_dgs_blocks=shared_parsed_blocks,
            )
        except Exception as exc:
            root_entries = list()
            root_logger = Logger()
            logger.add_warning(
                msg="Root DGS dynamic-model catalogue skipped",
                value=str(exc),
            )
    if root_logger.has_logs():
        logger += root_logger
    else:
        pass

    bundle_entries.extend(root_entries)
    _emit_dynamic_model_import_progress(progress_callback, 100, "DGS dynamic model catalogue ready")

    bundle: DynamicModelImportBundle = DynamicModelImportBundle(
        source_tpe=DynamicModelImportSource.PowerFactoryDgs,
        source_path=dgs_path,
        entries=bundle_entries,
    )
    return bundle, logger


def get_dgs_dynamic_host_device_tpe(source_element_class: str | None) -> DeviceType | None:
    """
    Map one authoritative PowerFactory host class to a VeraGrid device type.

    Auxiliary composite references such as ``StaSwitch`` and ``ElmSind`` are
    intentionally absent. They provide controller inputs or switching actions,
    but they do not identify the physical device that owns the composite model.

    :param source_element_class: Referenced DGS ``pElm`` class.
    :return: Compatible VeraGrid device type or ``None`` for non-host classes.
    """
    result: DeviceType | None

    if source_element_class in {"ElmVsc", "ElmVscmono"}:
        result = DeviceType.VscDevice
    else:
        if source_element_class == "ElmSvs":
            result = DeviceType.ControllableShuntDevice
        else:
            if source_element_class == "ElmSym":
                result = DeviceType.GeneratorDevice
            else:
                if source_element_class == "ElmGenstat":
                    # A composite-controlled ElmGenstat is a dynamic current
                    # injection. The static importer materializes that contract
                    # as Generator (or its Battery subclass), not as a fixed-PQ
                    # StaticGenerator.
                    result = DeviceType.GeneratorDevice
                else:
                    if source_element_class in {"ElmLod", "ElmLodlv", "ElmLodmv"}:
                        result = DeviceType.LoadDevice
                    else:
                        if source_element_class == "ElmBat":
                            result = DeviceType.BatteryDevice
                        else:
                            if source_element_class == "ElmLne":
                                result = DeviceType.LineDevice
                            else:
                                if source_element_class == "ElmTr2":
                                    result = DeviceType.Transformer2WDevice
                                else:
                                    if source_element_class == "ElmXnet":
                                        # The normal DGS path materializes an
                                        # external grid as a dynamic Generator.
                                        result = DeviceType.GeneratorDevice
                                    else:
                                        result = None

    return result


def is_dgs_dynamic_block_runtime_assignable(
        block: Block,
        device_tpe: DeviceType,
        native_kind: NativeDgsEquipmentKind | None = None,
) -> bool:
    """
    Check that an imported root exposes a complete VeraGrid runtime contract.

    Exact DGS ownership does not imply that the symbolic root includes the
    built-in PowerFactory equipment equations. Promotion therefore requires the
    external power-flow outputs and bus-facing inputs consumed by VeraGrid's
    device compiler. Unsupported families remain catalogue-only until their
    native physical blocks are implemented and validated.

    :param block: Imported domain-neutral symbolic block.
    :param device_tpe: Exact physical host type inferred from DGS.
    :param native_kind: Native equipment family for boundary validation, when known.
    :return: ``True`` only for a complete supported runtime interface.
    """
    mapping_refs: Set[VarPowerFlowReferenceType] = set(block.external_mapping)
    input_refs: Set[VarPowerFlowReferenceType] = set()
    input_var: Var
    for input_var in block.in_vars:
        if isinstance(input_var.ref, VarPowerFlowReferenceType):
            input_refs.add(input_var.ref)
        else:
            pass

    required_mapping_values: Tuple[VarPowerFlowReferenceType, ...]
    required_input_values: Tuple[VarPowerFlowReferenceType, ...]
    if device_tpe == DeviceType.VscDevice:
        required_mapping_values = (
            VarPowerFlowReferenceType.Pf,
            VarPowerFlowReferenceType.Pt,
            VarPowerFlowReferenceType.Qt,
        )
        is_monopolar_vsc: bool = (
                native_kind == NativeDgsEquipmentKind.MonopolarVsc
        )
        if is_monopolar_vsc:
            required_input_values = (
                VarPowerFlowReferenceType.Vf_dc,
                VarPowerFlowReferenceType.Vmt,
                VarPowerFlowReferenceType.Vat,
            )
        else:
            required_input_values = (
                VarPowerFlowReferenceType.Vf_dc,
                VarPowerFlowReferenceType.Vt_dc,
                VarPowerFlowReferenceType.Vmt,
                VarPowerFlowReferenceType.Vat,
            )
    else:
        if device_tpe in {
            DeviceType.ControllableShuntDevice,
            DeviceType.StaticGeneratorDevice,
        }:
            required_mapping_values = (
                VarPowerFlowReferenceType.P,
                VarPowerFlowReferenceType.Q,
            )
            required_input_values = (
                VarPowerFlowReferenceType.Vm,
                VarPowerFlowReferenceType.Va,
            )
        else:
            if device_tpe == DeviceType.GeneratorDevice:
                required_mapping_values = (
                    VarPowerFlowReferenceType.P,
                    VarPowerFlowReferenceType.Q,
                )
                required_input_values = (
                    VarPowerFlowReferenceType.Vm,
                    VarPowerFlowReferenceType.Va,
                )
            else:
                required_mapping_values = tuple()
                required_input_values = tuple()

    required_mapping_refs: Set[VarPowerFlowReferenceType] = set(
        required_mapping_values
    )
    required_input_refs: Set[VarPowerFlowReferenceType] = set(
        required_input_values
    )

    if len(required_mapping_refs) == 0 or len(required_input_refs) == 0:
        result: bool = False
    else:
        result = (
                required_mapping_refs.issubset(mapping_refs)
                and required_input_refs.issubset(input_refs)
        )

    return result


def get_unsupported_dgs_vsc_options(source: ElmVsc | ElmVscmono) -> List[str]:
    """Identify native selections outside the current coupled-voltage adapter.

    Missing columns retain the legacy slot-based import behavior. Explicit
    nondefault selections must not silently acquire the existing voltage-source
    equations. The load-flow-only modulation limit and EMT selector do not
    change the RMS adapter and are deliberately excluded here.
    """
    options = (
        ('i_ctrl', source.i_ctrl, 'integrated current controller'),
        ('iVIsource', source.iVIsource, 'independent AC/DC sources'),
        ('i_mod', source.i_mod, 'modulation variant'),
    )
    return [f'{name}={value} ({description})' for name, value, description in options
            if value not in (None, 0)]


class DynamicModelImport:
    """Own one DGS-to-template conversion and its exact physical assignments.

    Context objects are shared by reference with DynDgsParser. The result
    indexes canonical templates and children; it never duplicates their graph.
    """

    __slots__ = ("_dgs_circuit", "_circuit", "_target_domain", "_logger", "_conversion_result",
                 "block_metadata", "_import_metadata")

    def __init__(self, dgs_circuit: DgsCircuit, circuit: MultiCircuit,
                 target_domain: DynamicSimulationMode | None, logger: Logger,
                 ) -> None:
        """Retain the source graph, destination and diagnostics for one import.

        :param dgs_circuit: Parsed DGS object graph shared with static import.
        :param circuit: Destination owning devices and canonical templates.
        :param target_domain: Explicit RMS or EMT destination.
        :param logger: Import diagnostic sink shared with the caller.
        :return: None.
        """
        self._dgs_circuit: DgsCircuit = dgs_circuit
        self._circuit: MultiCircuit = circuit
        self._target_domain: DynamicSimulationMode | None = target_domain
        self._logger: Logger = logger
        self._conversion_result: DgsDynamicTemplateConversionResult = DgsDynamicTemplateConversionResult()
        self.block_metadata: Dict[int, Dict[str, bool | int | float | str | None]] = dict()
        self._import_metadata: DgsImportMetadata = DgsImportMetadata(self.block_metadata)

    def get_import_metadata(self) -> DgsImportMetadata:
        """Share typed access to the importer's UID-keyed metadata dictionary.

        :return: Registry used by adapters, topology preparation and measurements.
        """
        return self._import_metadata

    def register_imported_rms_model_metadata(
            self, device: DynamicDevice, source_element_class: str) -> None:
        """Register only the machine identities needed by reference binding.

        :param device: Exact static host with its definitive RMS model installed.
        :param source_element_class: Authoritative DGS equipment family.
        :return: None.
        """
        model: Block = device.rms_model
        if source_element_class != "ElmSym" or model.empty():
            return
        else:
            pass
        states: Dict[str, Var] = dict((variable.name, variable) for variable in model.state_vars)
        angle: Var | None = states.get("phi", None)
        speed: Var | None = states.get("speed", None)
        if angle is None or speed is None:
            return
        else:
            pass
        set_import_field(model, DgsImportField.DGS_ELMSYM_RUNTIME_ADAPTER, True, self._import_metadata)
        set_import_field(model, DgsImportField.DGS_ELMSYM_ROTOR_ANGLE_VAR_UID, angle.uid, self._import_metadata)
        set_import_field(model, DgsImportField.DGS_ELMSYM_SPEED_VAR_UID, speed.uid, self._import_metadata)

    def get_conversion_result(self) -> DgsDynamicTemplateConversionResult:
        """Expose the canonical associations used by later preparation phases.

        :return: Current conversion result; template and block objects are shared.
        """
        return self._conversion_result

    def _build_exact_dgs_elmsym_machine_parameters(self,
                                                   source_machine_id: str,
                                                   host_device: Generator,
                                                   ) -> DgsElmSymMachineParameters | None:
        """Resolve exact source ElmSym/TypSym rows without modifying the host.

        :param source_machine_id: Exact source machine FID.
        :param host_device: Imported physical generator supplying operating data.
        :return: Validated machine parameters, or None for an unresolved source.
        """
        source_machine: ElmSym | None = None
        candidate_machine: ElmSym
        for candidate_machine in self._dgs_circuit.elmsyms:
            if str(candidate_machine.ID).lstrip("#") == source_machine_id.lstrip("#"):
                if source_machine is None:
                    source_machine = candidate_machine
                else:
                    return None
            else:
                pass
        if source_machine is None:
            return None
        source_type_id: str = str(source_machine.typ_id).lstrip("#")
        source_type: TypSym | None = None
        candidate_type: TypSym
        for candidate_type in self._dgs_circuit.typsyms:
            if str(candidate_type.ID).lstrip("#") == source_type_id:
                if source_type is None:
                    source_type = candidate_type
                else:
                    return None
            else:
                pass
        if source_type is None:
            return None
        return build_dgs_elmsym_machine_parameters(
            source_machine=source_machine,
            source_type=source_type,
            operating_power_factor=float(host_device.Pf),
        )

    def _collect_native_dgs_rms_measurement_specs(self,
                                                  root_element: ElmComp,
                                                  direct_result: DgsDirectRootBuildResult,
                                                  host_device: DynamicDevice | None,
                                                  ) -> List[_DgsRmsMeasurementSpec]:
        """Resolve native meter semantics and exact consumers before adaptation.

        :param root_element: Composite root whose direct slots are materialized.
        :param direct_result: Exact direct-slot lookup for the controller root.
        :param host_device: Physical host used to interpret implicit ElmPhi frames.
        :return: Ordered native measurement construction specifications.
        """
        element_by_id: Dict[str, DGSElement] = _build_dgs_element_index(
            dgs_circuit=self._dgs_circuit,
        )
        implicit_target_by_slot: Dict[str, str] = (
            _build_implicit_meter_target_by_slot(
                dgs_circuit=self._dgs_circuit,
                root_element=root_element,
                entries=direct_result.direct_entries,
            )
        )
        specs: List[_DgsRmsMeasurementSpec] = list()
        entry: ElmCompInstanceEntry

        # Follow exact direct-slot identities so equal signal names in independent
        # controller children never become an accidental shared measurement.
        for entry in direct_result.direct_entries:
            if entry.slot_id is None:
                pass
            else:
                is_pll_slot: bool = (
                        entry.slot_filter is not None
                        and (
                                "ElmPhi" in entry.slot_filter
                                or "ElmPll" in entry.slot_filter
                        )
                )
                meter_element: DGSElement | None
                if entry.element_id is None:
                    if is_pll_slot:
                        meter_element = _resolve_native_pll_element(
                            root_element=root_element,
                            dgs_circuit=self._dgs_circuit,
                        )
                    else:
                        meter_element = None
                else:
                    meter_element = element_by_id.get(entry.element_id, None)

                meter_kind: RmsPhysicalMeterKind | None
                if isinstance(meter_element, StaVmea):
                    meter_kind = RmsPhysicalMeterKind.VOLTAGE
                else:
                    if isinstance(meter_element, StaImea):
                        meter_kind = RmsPhysicalMeterKind.CURRENT
                    else:
                        if isinstance(meter_element, StaPqmea):
                            meter_kind = RmsPhysicalMeterKind.POWER
                        else:
                            if isinstance(meter_element, ElmPhi) or is_pll_slot:
                                meter_kind = RmsPhysicalMeterKind.PHASE_LOCKED_LOOP
                            else:
                                meter_kind = None

                if meter_kind is None:
                    pass
                else:
                    # Early materialization owns the native meter equations, so it
                    # must retain every exact BlkSig consumer. The late-binding
                    # helper deliberately excludes equipment-owned signals, which
                    # would incorrectly discard complete meters before the runtime
                    # adapter has removed their provisional fallback ownership.
                    targets_by_alias: Dict[str, List[Var]] = (
                        _build_exact_meter_targets(
                            dgs_circuit=self._dgs_circuit,
                            source_slot_id=entry.slot_id,
                            child_block_by_slot_id=(
                                direct_result.child_block_by_slot_id
                            ),
                        )
                    )
                    target_names: List[str] = (
                        _get_native_source_target_signal_names(
                            dgs_circuit=self._dgs_circuit,
                            source_slot_id=entry.slot_id,
                        )
                    )
                    if len(target_names) == 0:
                        implicit_target_name: str | None = (
                            implicit_target_by_slot.get(entry.slot_id, None)
                        )
                        if implicit_target_name is None:
                            target_names = list(targets_by_alias.keys())
                        else:
                            target_names = list((implicit_target_name,))
                    else:
                        pass

                    connections: List[_DgsRmsMeasurementConnection] = list()
                    target_name: str
                    target_var: Var
                    for target_name in target_names:
                        target_vars: List[Var] | None = targets_by_alias.get(
                            target_name,
                            None,
                        )
                        if target_vars is None:
                            pass
                        else:
                            for target_var in target_vars:
                                connections.append(_DgsRmsMeasurementConnection(
                                    alias_name=target_name,
                                    target_var=target_var,
                                ))

                    if len(connections) == 0:
                        pass
                    else:
                        use_stationary_reference: bool = False
                        if isinstance(meter_element, ElmPhi):
                            use_stationary_reference = (
                                    meter_element.pbusbar is None
                                    or str(meter_element.pbusbar).strip() == ""
                            )
                        else:
                            if is_pll_slot and isinstance(host_device, VSC):
                                use_stationary_reference = (
                                        host_device.control1 is ConverterControlType.Pac
                                )
                            else:
                                pass
                        source_fid: str
                        if meter_element is None:
                            source_fid = entry.slot_id
                        else:
                            source_fid = str(meter_element.ID)
                        source_name: str = _get_veragrid_meter_name(
                            meter_kind=meter_kind,
                            source_fid=source_fid,
                        )
                        specs.append(_DgsRmsMeasurementSpec(
                            source_fid=source_fid,
                            source_name=source_name,
                            meter_kind=meter_kind,
                            meter_element=meter_element,
                            connections=connections,
                            use_stationary_reference=use_stationary_reference,
                        ))
        return specs

    def _build_native_dgs_measurement_expression(self,
                                                 spec: _DgsRmsMeasurementSpec,
                                                 alias_name: str,
                                                 physical_inputs_by_reference: Dict[VarPowerFlowReferenceType, Var],
                                                 ) -> Expr | None:
        """Build one native meter output expression from physical placeholders.

        :param spec: Resolved native measurement specification.
        :param alias_name: Exact producer alias connected to a controller input.
        :param physical_inputs_by_reference: Canonical early physical inputs.
        :return: Native output expression, or ``None`` when unsupported.
        """
        normalized_name: str = alias_name.strip().lower()
        expression: Expr | None = None
        references: List[VarPowerFlowReferenceType] = (
            _get_native_dgs_measurement_physical_references(spec=spec)
        )

        if spec.meter_kind is RmsPhysicalMeterKind.POWER:
            power_meter: StaPqmea | None
            if isinstance(spec.meter_element, StaPqmea):
                power_meter = spec.meter_element
            else:
                power_meter = None
            if power_meter is None or power_meter.outserv != 0:
                pass
            else:
                orientation: float = 1.0 if power_meter.i_orient == 0 else -1.0
                if power_meter.Snom > 0.0 and self._circuit.Sbase > 0.0:
                    power_scale: float = float(self._circuit.Sbase) / float(power_meter.Snom)
                else:
                    power_scale = 1.0
                if normalized_name.startswith("q") and len(references) > 1:
                    physical_power: Var | None = physical_inputs_by_reference.get(
                        references[1],
                        None,
                    )
                else:
                    if len(references) > 0:
                        physical_power = physical_inputs_by_reference.get(
                            references[0],
                            None,
                        )
                    else:
                        physical_power = None
                if physical_power is None:
                    pass
                else:
                    expression = Const(orientation * power_scale) * physical_power
        else:
            if spec.meter_kind is RmsPhysicalMeterKind.VOLTAGE:
                if len(references) < 2:
                    pass
                else:
                    voltage_magnitude: Var | None = physical_inputs_by_reference.get(
                        references[0],
                        None,
                    )
                    voltage_angle: Var | None = physical_inputs_by_reference.get(
                        references[1],
                        None,
                    )
                    if voltage_magnitude is None or voltage_angle is None:
                        pass
                    else:
                        if "u1r" in normalized_name or normalized_name == "ur":
                            expression = voltage_magnitude * sym.cos(voltage_angle)
                        else:
                            if "u1i" in normalized_name or normalized_name == "ui":
                                expression = voltage_magnitude * sym.sin(voltage_angle)
                            else:
                                if normalized_name.startswith("cosphi"):
                                    expression = sym.cos(voltage_angle)
                                else:
                                    if normalized_name.startswith("sinphi"):
                                        expression = sym.sin(voltage_angle)
                                    else:
                                        if "phi" in normalized_name:
                                            expression = voltage_angle
                                        else:
                                            if normalized_name in ("fe", "fref"):
                                                expression = Const(1.0)
                                            else:
                                                if (
                                                        normalized_name.startswith("f")
                                                        or "_hz" in normalized_name
                                                ):
                                                    expression = Const(float(self._circuit.fBase))
                                                else:
                                                    expression = voltage_magnitude
            else:
                if spec.meter_kind is RmsPhysicalMeterKind.PHASE_LOCKED_LOOP:
                    if spec.use_stationary_reference:
                        if normalized_name.startswith("cosphi"):
                            expression = Const(1.0)
                        else:
                            if normalized_name.startswith("sinphi"):
                                expression = Const(0.0)
                            else:
                                if normalized_name == "fmeas":
                                    expression = Const(1.0)
                                else:
                                    if "hz" in normalized_name:
                                        expression = Const(float(self._circuit.fBase))
                                    else:
                                        pass
                    else:
                        if len(references) == 0:
                            voltage_angle = None
                        else:
                            voltage_angle = physical_inputs_by_reference.get(
                                references[0],
                                None,
                            )
                        if voltage_angle is None:
                            pass
                        else:
                            if normalized_name.startswith("cosphi"):
                                expression = sym.cos(voltage_angle)
                            else:
                                if normalized_name.startswith("sinphi"):
                                    expression = sym.sin(voltage_angle)
                                else:
                                    pass
                else:
                    pass
        return expression

    def _materialize_native_dgs_rms_measurements(self,
                                                 block: Block,
                                                 native_specs: List[_DgsRmsMeasurementSpec],
                                                 physical_inputs_by_reference: Dict[VarPowerFlowReferenceType, Var],
                                                 var_factory: VarFactory,
                                                 ) -> Set[int]:
        """Create native early measurements and connect exact controller inputs.

        :param block: Imported controller root receiving measurement children.
        :param native_specs: Exact native meter construction specifications.
        :param physical_inputs_by_reference: Shared physical placeholder lookup.
        :param var_factory: Factory owning early measurement variables.
        :return: Object identities of controller inputs replaced successfully.
        """
        replaced_input_object_ids: Set[int] = set()
        spec: _DgsRmsMeasurementSpec
        for spec in native_specs:
            required_references: List[VarPowerFlowReferenceType] = (
                _get_native_dgs_measurement_physical_references(spec=spec)
            )
            required_reference: VarPowerFlowReferenceType
            for required_reference in required_references:
                _get_or_create_dgs_physical_input(
                    block=block,
                    reference=required_reference,
                    physical_inputs_by_reference=physical_inputs_by_reference,
                    var_factory=var_factory,
                )

            measurement_block: Block = Block(name=spec.source_name)
            measurement_block.in_vars = list(
                physical_inputs_by_reference[reference]
                for reference in required_references
            )
            connected_count: int = 0
            output_by_alias: Dict[str, Var] = dict()
            connection: _DgsRmsMeasurementConnection
            for connection in spec.connections:
                output_var: Var | None = output_by_alias.get(
                    connection.alias_name,
                    None,
                )
                if output_var is None:
                    source_expression: Expr | None = (
                        self._build_native_dgs_measurement_expression(
                            spec=spec,
                            alias_name=connection.alias_name,
                            physical_inputs_by_reference=physical_inputs_by_reference,
                        )
                    )
                    if source_expression is None:
                        pass
                    else:
                        # The exact DGS consumer variable becomes the measurement
                        # output. Reusing it prevents a same-name second UID from
                        # appearing when the template is wrapped or duplicated.
                        output_var = connection.target_var
                        _remove_meter_target_fallback_ownership(
                            host_model=block,
                            target_var=output_var,
                        )
                        measurement_block.algebraic_vars.append(output_var)
                        measurement_block.out_vars.append(output_var)
                        measurement_block.algebraic_eqs.append(
                            output_var - source_expression
                        )
                        output_by_alias[connection.alias_name] = output_var
                        replaced_input_object_ids.add(id(connection.target_var))
                        connected_count += 1
                else:
                    # One native output can feed several exact endpoints. Remove
                    # every additional receiver fallback before atomically joining
                    # its complete block interface to the canonical output UID.
                    _remove_meter_target_fallback_ownership(
                        host_model=block,
                        target_var=connection.target_var,
                    )
                    block.update_model(
                        old=connection.target_var,
                        new=output_var,
                    )
                    replaced_input_object_ids.add(id(connection.target_var))
                    connected_count += 1

            if connected_count == 0:
                pass
            else:
                block.children.append(measurement_block)
        return replaced_input_object_ids

    def _add_required_dgs_rms_measurements(self,
                                           block: Block,
                                           host_device: DynamicDevice,
                                           native_specs: List[_DgsRmsMeasurementSpec],
                                           ) -> None:
        """Materialize and connect measurements required by one imported model.

        :param block: Imported DGS composite root.
        :param host_device: Exact static device that owns the final RMS template.
        :param native_specs: Exact native meters resolved from the DGS graph.
        :return: None.
        """
        measurement_var_factory: VarFactory = VarFactory()
        physical_inputs_by_reference: Dict[VarPowerFlowReferenceType, Var] = dict()
        replaced_input_object_ids: Set[int] = (
            self._materialize_native_dgs_rms_measurements(
                block=block,
                native_specs=native_specs,
                physical_inputs_by_reference=physical_inputs_by_reference,
                var_factory=measurement_var_factory,
            )
        )
        unconnected_inputs: List[Tuple[Block, Var]] = (
            _collect_unconnected_dgs_child_inputs(block=block)
        )
        physical_input_object_ids: Set[int] = set(
            id(physical_input)
            for physical_input in physical_inputs_by_reference.values()
        )
        unconnected_inputs = list(
            input_entry
            for input_entry in unconnected_inputs
            if id(input_entry[1]) not in physical_input_object_ids
        )
        inputs_by_terminal: Dict[RmsTerminalSide, List[Tuple[Block, Var]]] = dict((
            (RmsTerminalSide.FROM, list()),
            (RmsTerminalSide.TO, list()),
            (RmsTerminalSide.BUS, list()),
        ))
        owner_block: Block
        input_var: Var
        for owner_block, input_var in unconnected_inputs:
            if isinstance(input_var.ref, VarPowerFlowReferenceType):
                terminal_side: RmsTerminalSide | None = (
                    _classify_rms_measurement_terminal(reference=input_var.ref)
                )
                if terminal_side is None:
                    pass
                else:
                    inputs_by_terminal[terminal_side].append((owner_block, input_var))
            else:
                pass

        terminal_side: RmsTerminalSide
        terminal_inputs: List[Tuple[Block, Var]]
        for terminal_side, terminal_inputs in inputs_by_terminal.items():
            if len(terminal_inputs) == 0:
                pass
            else:
                if isinstance(host_device, BranchParent):
                    if terminal_side is RmsTerminalSide.FROM:
                        terminal_bus = host_device.bus_from
                    else:
                        if terminal_side is RmsTerminalSide.TO:
                            terminal_bus = host_device.bus_to
                        else:
                            terminal_bus = None
                else:
                    if isinstance(host_device, InjectionParent):
                        if terminal_side is RmsTerminalSide.BUS:
                            terminal_bus = host_device.bus
                        else:
                            terminal_bus = None
                    else:
                        terminal_bus = None

                if terminal_bus is None:
                    pass
                else:
                    terminal_vars: List[Var] = list(
                        input_entry[1] for input_entry in terminal_inputs
                    )
                    measurement_types: List[BlockType] = (
                        find_measurements_for_inputs_group(
                            bus=terminal_bus,
                            inputs=terminal_vars,
                        )
                    )
                    measurement_type: BlockType
                    for measurement_type in measurement_types:
                        # Allocate every prerequisite before invoking the builder.
                        # A single canonical input is reused across all measurements
                        # that observe the same physical terminal quantity.
                        required_references: List[VarPowerFlowReferenceType] = (
                            _get_rms_terminal_physical_references(
                                block_type=measurement_type,
                                terminal_side=terminal_side,
                                is_dc_terminal=terminal_bus.is_dc,
                            )
                        )
                        required_reference: VarPowerFlowReferenceType
                        for required_reference in required_references:
                            _get_or_create_dgs_physical_input(
                                block=block,
                                reference=required_reference,
                                physical_inputs_by_reference=physical_inputs_by_reference,
                                var_factory=measurement_var_factory,
                            )
                        measurement_block: Block | None = _build_dgs_rms_measurement_block(
                            block_type=measurement_type,
                            terminal_side=terminal_side,
                            is_dc_terminal=terminal_bus.is_dc,
                            physical_inputs_by_reference=physical_inputs_by_reference,
                            var_factory=measurement_var_factory,
                        )
                        if measurement_block is None:
                            pass
                        else:
                            measurement_output: Var
                            for measurement_output in measurement_block.out_vars:
                                for owner_block, input_var in terminal_inputs:
                                    if (
                                            input_var.ref == measurement_output.ref
                                            and input_var is not measurement_output
                                    ):
                                        owner_block.update_model(
                                            old=input_var,
                                            new=measurement_output,
                                        )
                                        replaced_input_object_ids.add(id(input_var))
                                    else:
                                        pass
                            block.children.append(measurement_block)

        if len(replaced_input_object_ids) == 0:
            pass
        else:
            block.in_vars = list(
                root_input
                for root_input in block.in_vars
                if id(root_input) not in replaced_input_object_ids
            )

    def _native_runtime_validation_kind(self, direct_result: DgsDirectRootBuildResult) -> NativeDgsEquipmentKind | None:
        """Resolve the physical boundary contract from native equipment detection.

        :param direct_result: Root whose native requirements are being detected.
        :return: Physical boundary kind required for final host assignment.
        """
        plans: tuple[NativeDgsEquipmentPlan, ...] = detect_native_dgs_equipment(direct_result, self._dgs_circuit)
        if len(plans) == 0:
            return None
        elif len(plans) != 1:
            raise ValueError("A native dynamic root must resolve one exact physical host")
        else:
            return plans[0].kind

    def _construct_native_runtime_template(
            self, template: RmsModelTemplate, direct_result: DgsDirectRootBuildResult,
            host_device: DynamicDevice | None,
            measurement_specs: List[_DgsRmsMeasurementSpec],
    ) -> RmsModelTemplate:
        """Build and assemble fully configured native physical equipment.

        :param template: Imported controller with required measurements attached.
        :param direct_result: Exact source slots and their controller instances.
        :param host_device: Physical host already resolved from source FID.
        :param measurement_specs: Existing measurements with exact source provenance.
        :return: Complete native template, or the unchanged controller-only root.
        """
        plans: tuple[NativeDgsEquipmentPlan, ...] = detect_native_dgs_equipment(direct_result, self._dgs_circuit)
        if len(plans) == 0:
            return template
        elif len(plans) != 1 or host_device is None:
            raise ValueError("Native construction requires one exact equipment host")
        else:
            plan: NativeDgsEquipmentPlan = plans[0]
            if str(plan.entry.element_id).lstrip("#") != str(host_device.idtag).lstrip("#"):
                raise ValueError("Native equipment FID does not match its resolved host")
            else:
                pass
            machine_parameters: DgsElmSymMachineParameters | None = None
            if plan.kind == NativeDgsEquipmentKind.SynchronousMachine and isinstance(host_device, Generator):
                machine_parameters = self._build_exact_dgs_elmsym_machine_parameters(
                    str(plan.entry.element_id), host_device)
            else:
                pass
            # Register already materialized meters as exact slot producers. No
            # second measurement graph or recursive signal-name lookup is needed.
            for entry in direct_result.direct_entries:
                if entry.slot_id is None or entry.slot_id in direct_result.child_block_by_slot_id:
                    pass
                else:
                    meter_targets: Dict[str, List[Var]] = _build_exact_meter_targets(
                        self._dgs_circuit, entry.slot_id, direct_result.child_block_by_slot_id)
                    cable_target_uids: Set[int] = set(variable.uid for variables in meter_targets.values()
                                                     for variable in variables)
                    for spec in measurement_specs:
                        source_ids: Set[str] = set((entry.slot_id, str(entry.element_id)))
                        target_uids: Set[int] = set(connection.target_var.uid for connection in spec.connections)
                        if spec.source_fid not in source_ids and len(target_uids & cable_target_uids) == 0:
                            pass
                        else:
                            for child in template.block.children:
                                output_uids: Set[int] = set(variable.uid for variable in child.out_vars)
                                if child.name == spec.source_name and len(target_uids & output_uids) > 0:
                                    direct_result.child_block_by_slot_id[entry.slot_id] = child
                                else:
                                    pass
            equipment: Block = construct_native_dgs_equipment(
                plan, host_device, self._dgs_circuit, float(self._circuit.Sbase),
                float(self._circuit.fBase), machine_parameters)
            template.block = assemble_native_dgs_model(plan, equipment, direct_result, self._dgs_circuit, self._logger)
            return template

    def _build_dgs_direct_runtime_template(self,
                                           source_block: Block,
                                           template_name: str,
                                           device_tpe: DeviceType,
                                           direct_result: DgsDirectRootBuildResult | None,
                                           host_device: DynamicDevice | None,
                                           native_measurement_specs: List[_DgsRmsMeasurementSpec],
                                           ) -> RmsModelTemplate | EmtModelTemplate:
        """Wrap one directly materialized DGS block in its final template.

        The caller transfers ownership of ``source_block``.  No catalogue entry,
        serialization payload or duplicate symbolic graph is created between the
        parser and the final ``MultiCircuit`` template.

        :param source_block: Direct root block owned by this conversion.
        :param template_name: Final reusable-template display name.
        :param device_tpe: Exact physical host family or generic dynamic host.
        :param direct_result: Transient direct-root conversion context, if present.
        :param host_device: Exact static host used to resolve measurement terminals.
        :param native_measurement_specs: Native meters resolved from the DGS graph.
        :return: Final RMS or EMT template ready for circuit registration.
        """
        # Type only child inputs whose DGS signal has no internal producer. The
        # synthesized root interface then exposes the same typed Var objects.
        _assign_dgs_external_input_references(
            block=source_block,
            device_tpe=device_tpe,
        )

        # Native PowerFactory meters are not executable ElmDsl children. Replace
        # their missing signals with explicit VeraGrid measurements before the root
        # interface is finalized for the editor and physical assembly.
        if (
                self._target_domain == DynamicSimulationMode.RMS
                and host_device is not None
        ):
            self._add_required_dgs_rms_measurements(
                block=source_block,
                host_device=host_device,
                native_specs=native_measurement_specs,
            )
        else:
            pass

        # Complete only the public composite ports already owned by the child graph.
        _apply_composite_child_interface_if_missing(block=source_block)
        source_block.name = template_name
        template_comment: str = (
            f"PowerFactory DGS dynamic model: {template_name}"
        )

        if self._target_domain == DynamicSimulationMode.EMT:
            emt_template: EmtModelTemplate = EmtModelTemplate(name=template_name)
            emt_template.tpe = device_tpe
            emt_template.block = source_block
            emt_template.name = template_name
            emt_template.comment = template_comment
            result: RmsModelTemplate | EmtModelTemplate = emt_template
        else:
            rms_template: RmsModelTemplate = RmsModelTemplate(name=template_name)
            rms_template.tpe = device_tpe
            rms_template.block = source_block
            rms_template.name = template_name
            rms_template.comment = template_comment
            adapted_template: RmsModelTemplate | None

            # Native equipment receives its physical parameters before assembly.
            if direct_result is not None:
                adapted_template = self._construct_native_runtime_template(
                    rms_template, direct_result, host_device, native_measurement_specs)
            else:
                adapted_template = rms_template

            if adapted_template is None:
                # Preserve the declarative root for inspection, but never expose an
                # incomplete physical adapter as assignable equipment.
                rms_template.tpe = DeviceType.DynamicModelHostDevice
                result = rms_template
            else:
                result = adapted_template
        return result

    def _is_selected_dgs_root_for_host(
            self, root_element: ElmComp,
            host_identity: Tuple[str, DeviceType, str, str | None],
    ) -> bool:
        """Respect native model ownership and service state before assembly.

        :param root_element: Candidate composite declaration.
        :param host_identity: Exact physical host resolved through its native slot.
        :return: Whether this is the unique active model selected for the host.
        """
        if root_element.outserv != 0:
            return False
        else:
            pass
        source_index: Dict[str, DGSElement] = _build_dgs_element_index(self._dgs_circuit)
        source: DGSElement | None = source_index.get(host_identity[0], None)
        if isinstance(source, (ElmVsc, ElmVscmono, ElmSym, ElmGenstat, ElmSvs)):
            if source.outserv != 0:
                return False
            else:
                pass
            selected_root: str = "" if source.c_pmod is None else str(source.c_pmod).strip().lstrip("#")
            if selected_root != "":
                return selected_root == str(root_element.ID).strip().lstrip("#")
            else:
                # Older exports omit c_pmod. Retain compatibility only when one
                # active direct relation establishes an unambiguous owner.
                candidates: List[str] = list()
                candidate: ElmComp
                for candidate in self._dgs_circuit.elmcomps:
                    if candidate.outserv == 0:
                        candidate_entries: List[ElmCompInstanceEntry] = get_unique_elmcomp_slot_entries(
                            extract_elmcomp_direct_instances(self._dgs_circuit, candidate))
                        if any(entry.element_reference_is_resolved and entry.element_id == host_identity[0]
                               and entry.element_kind == host_identity[2] for entry in candidate_entries):
                            candidates.append(candidate.ID)
                        else:
                            pass
                    else:
                        pass
                return len(candidates) == 1 and candidates[0] == root_element.ID
        else:
            # Other existing host families retain their direct typed binding;
            # their native source contracts do not expose this selector here.
            return True

    def _resolve_dgs_direct_root_host_identity(self,
                                               root_element: ElmComp,
                                               ) -> Tuple[str, DeviceType, str, str | None] | None:
        """Resolve at most one physical host directly from root ``pElm`` FIDs.

        :param root_element: Root composite whose host is being resolved.
        :return: FID, VeraGrid type, source class and source name, or ``None``.
        """
        identities: Dict[
            Tuple[str, DeviceType],
            Tuple[str, str | None],
        ] = dict()
        direct_entries: List[ElmCompInstanceEntry] = (
            get_unique_elmcomp_slot_entries(
                entries=extract_elmcomp_direct_instances(
                    circuit=self._dgs_circuit,
                    root_element=root_element,
                )
            )
        )
        direct_entry: ElmCompInstanceEntry

        # Only one resolved unique slot may establish each physical FID identity.
        for direct_entry in direct_entries:
            source_element_id: str | None = direct_entry.element_id
            source_element_class: str | None = direct_entry.element_kind
            host_device_tpe: DeviceType | None = get_dgs_dynamic_host_device_tpe(
                source_element_class=source_element_class,
            )
            if (
                    source_element_id is None
                    or source_element_class is None
                    or not direct_entry.element_reference_is_resolved
                    or host_device_tpe is None
            ):
                pass
            else:
                host_key: Tuple[str, DeviceType] = (
                    source_element_id,
                    host_device_tpe,
                )
                if host_key in identities:
                    pass
                else:
                    identities[host_key] = (
                        source_element_class,
                        direct_entry.element_name,
                    )

        if len(identities) == 1:
            exact_host_key: Tuple[str, DeviceType] = next(iter(identities))
            exact_host_source: Tuple[str, str | None] = identities[exact_host_key]
            resolved_device_tpe: DeviceType = exact_host_key[1]
            if exact_host_source[0] == "ElmSvs":
                imported_svs_types: List[DeviceType] = list()
                candidate_svs_type: DeviceType
                candidate_svs_obj: object
                for candidate_svs_type in (
                        DeviceType.ControllableShuntDevice,
                        DeviceType.StaticGeneratorDevice,
                        DeviceType.VscDevice,
                ):
                    for candidate_svs_obj in self._circuit.get_elements_by_type(
                            device_type=candidate_svs_type,
                    ):
                        if (
                                isinstance(candidate_svs_obj, DynamicDevice)
                                and candidate_svs_obj.idtag == exact_host_key[0]
                        ):
                            imported_svs_types.append(candidate_svs_type)
                        else:
                            pass
                if len(imported_svs_types) == 1:
                    resolved_device_tpe = imported_svs_types[0]
                else:
                    pass
            if exact_host_source[0] == "ElmGenstat":
                imported_hosts: List[DynamicDevice] = _find_exact_dgs_dynamic_host_devices(
                    self._circuit, exact_host_key[0], resolved_device_tpe, exact_host_source[0])
                if len(imported_hosts) == 1:
                    resolved_device_tpe = imported_hosts[0].device_type
                else:
                    pass
            else:
                pass
            result: Tuple[str, DeviceType, str, str | None] | None = (
                exact_host_key[0],
                resolved_device_tpe,
                exact_host_source[0],
                exact_host_source[1],
            )
        else:
            result = None
        return result

    def _register_dgs_direct_template(self,
                                      template_obj: RmsModelTemplate | EmtModelTemplate,
                                      root_dgs_id: str,
                                      existing_names: Set[str],
                                      ) -> bool:
        """Register one direct DGS template with a deterministic FID collision name.

        :param template_obj: Final template owning the parsed block.
        :param root_dgs_id: Exact source root FID used only for collision resolution.
        :param existing_names: Mutable names already registered in the destination domain.
        :return: ``True`` when the template was registered.
        """
        requested_name: str = str(template_obj.name).strip()
        if requested_name == "":
            requested_name = f"DGS dynamic root {root_dgs_id}"
        else:
            pass

        if requested_name in existing_names:
            final_name: str = f"{requested_name} [DGS {root_dgs_id}]"
        else:
            final_name = requested_name

        if final_name in existing_names:
            self._logger.add_warning(
                msg="DGS dynamic root skipped because its FID-qualified name already exists",
                value=final_name,
            )
            registered: bool = False
        else:
            template_obj.name = final_name
            template_obj.block.name = final_name
            if isinstance(template_obj, RmsModelTemplate):
                self._circuit.add_rms_model(template_obj)
            else:
                self._circuit.add_emt_model(template_obj)
            existing_names.add(final_name)
            registered = True
        return registered

    def _activate_dgs_direct_template(self,
                                      template_obj: RmsModelTemplate | EmtModelTemplate,
                                      host_identity: Tuple[str, DeviceType, str, str | None],
                                      native_kind: NativeDgsEquipmentKind | None,
                                      ) -> bool:
        """Configure and assign one template to the exact imported device FID.

        :param template_obj: Registered direct template.
        :param host_identity: Exact FID, VeraGrid type, source class and source name.
        :param native_kind: Native equipment family used for boundary validation.
        :return: ``True`` when the exact host owns this template after the call.
        """
        source_element_id: str = host_identity[0]
        host_device_tpe: DeviceType = host_identity[1]
        source_element_class: str = host_identity[2]
        source_element_name: str | None = host_identity[3]
        host_devices: List[DynamicDevice] = _find_exact_dgs_dynamic_host_devices(
            circuit=self._circuit,
            source_element_dgs_id=source_element_id,
            device_tpe=host_device_tpe,
            source_element_class=source_element_class,
        )
        if len(host_devices) == 1:
            host_device: DynamicDevice | None = host_devices[0]
        else:
            host_device = None

        runtime_equipment_kind: NativeDgsEquipmentKind | None = native_kind
        if (
                runtime_equipment_kind is None
                and source_element_class == "ElmVscmono"
        ):
            # A native monopolar block may already expose the complete equipment
            # boundary and its voltage contract is
            # still monopolar during the final fail-closed assignment check.
            runtime_equipment_kind = NativeDgsEquipmentKind.MonopolarVsc
        else:
            pass

        runtime_contract_ready: bool = (
                host_device is not None
                and template_obj.tpe == host_device_tpe
                and is_dgs_dynamic_block_runtime_assignable(
            block=template_obj.block,
            device_tpe=host_device_tpe,
            native_kind=runtime_equipment_kind,
        )
        )
        if not runtime_contract_ready or host_device is None:
            # An incomplete physical wrapper remains inspectable, but it must not
            # appear in the assignable device-template catalogue.
            template_obj.tpe = DeviceType.DynamicModelHostDevice
            self._logger.add_warning(
                msg=(
                    "DGS dynamic host retained without activation because exact "
                    "resolution or its native physical contract is incomplete"
                ),
                device=source_element_name,
                device_class=source_element_class,
                value=source_element_id,
            )
            activated: bool = False
        else:
            current_template: RmsModelTemplate | EmtModelTemplate | None
            if isinstance(template_obj, RmsModelTemplate):
                current_template = host_device.rms_template
            else:
                current_template = host_device.emt_template

            if current_template is template_obj:
                activated = True
            else:
                if current_template is not None:
                    self._logger.add_warning(
                        msg="DGS dynamic host already owns a different template",
                        device=source_element_name,
                        device_class=source_element_class,
                        value=source_element_id,
                    )
                    activated = False
                else:
                    try:
                        assign_import_template(host_device, template_obj)
                        activated = True
                    except (TypeError, ValueError, KeyError) as error:
                        # A rejected template stays inspectable, but it must not
                        # appear in the assignable device-template catalogue.
                        template_obj.tpe = DeviceType.DynamicModelHostDevice
                        self._logger.add_warning(
                            msg="DGS dynamic host rejected its template",
                            device=source_element_name,
                            device_class=source_element_class,
                            value=str(error),
                        )
                        activated = False

                    if activated and isinstance(template_obj, RmsModelTemplate):
                        self.register_imported_rms_model_metadata(host_device, source_element_class)
                    else:
                        pass
        return activated

    def _get_unique_dgs_dynamic_roots_by_id(self,
                                            emit_diagnostics: bool,
                                            ) -> Dict[str, ElmComp]:
        """Select only roots with one non-empty normalized DGS FID.

        The first occurrence of a duplicated FID is deliberately excluded together
        with every later occurrence.  Keeping the first would let the assignment
        stage reuse one final template for several source roots.

        :param emit_diagnostics: Whether this validation pass records source errors.
        :return: Unique roots keyed by their normalized non-empty FID.
        """
        root_count_by_id: Dict[str, int] = dict()
        first_root_by_id: Dict[str, ElmComp] = dict()
        root_element: ElmComp
        for root_element in self._dgs_circuit.elmcomps:
            root_id: str = str(root_element.ID).strip()
            if root_id == "":
                if emit_diagnostics:
                    self._logger.add_warning(
                        msg="DGS dynamic root skipped because its FID is empty",
                        device=root_element.loc_name,
                        device_class="ElmComp",
                    )
                else:
                    pass
            else:
                current_count: int | None = root_count_by_id.get(root_id, None)
                if current_count is None:
                    root_count_by_id[root_id] = 1
                    first_root_by_id[root_id] = root_element
                else:
                    root_count_by_id[root_id] = current_count + 1

        unique_root_by_id: Dict[str, ElmComp] = dict()
        root_id: str
        for root_id, root_element in first_root_by_id.items():
            root_count: int | None = root_count_by_id.get(root_id, None)
            if root_count == 1:
                unique_root_by_id[root_id] = root_element
            else:
                if emit_diagnostics:
                    self._logger.add_warning(
                        msg="DGS dynamic roots skipped because their FID is duplicated",
                        device=root_element.loc_name,
                        device_class="ElmComp",
                        value=root_id,
                    )
                else:
                    pass
        return unique_root_by_id

    def convert_and_add_templates(self) -> DgsDynamicTemplateConversionResult:
        """Convert DGS roots directly into registered final templates.

        The automatic file-open path owns one transient DGS parse graph.  Each
        successful root follows ``Block -> Template -> MultiCircuit``.  The return
        value is the only cross-stage state: one minimal lookup from the exact root
        FID to the final template already owned by ``MultiCircuit``.

        :return: Final-template associations plus transient canonical slot lookups.
        """
        self._conversion_result: DgsDynamicTemplateConversionResult = (
            DgsDynamicTemplateConversionResult()
        )
        templates_by_root_dgs_id: Dict[
            str,
            RmsModelTemplate | EmtModelTemplate,
        ] = self._conversion_result.templates_by_root_dgs_id
        if self._target_domain not in {
            DynamicSimulationMode.RMS,
            DynamicSimulationMode.EMT,
        }:
            self._logger.add_error(
                msg="DGS dynamic model import requires RMS or EMT mode",
                value=self._target_domain,
            )
            return self._conversion_result
        else:
            pass

        # Reject empty and duplicated root identities before building the shared
        # graphical index. Ambiguous roots must not prevent independent valid roots
        # from reaching their own direct FID conversion.
        unique_root_by_id: Dict[str, ElmComp] = self._get_unique_dgs_dynamic_roots_by_id(

            emit_diagnostics=True,
        )
        excluded_root_ids: Set[str] = set()
        candidate_root: ElmComp
        for candidate_root in self._dgs_circuit.elmcomps:
            if (
                    candidate_root.ID != ""
                    and candidate_root.ID not in unique_root_by_id
            ):
                excluded_root_ids.add(candidate_root.ID)
            else:
                pass

        try:
            parsed_blocks: Dict[str, ParsedDgsBlockDefinition] = (
                parse_dgs_block_definitions_from_circuit(
                    circuit=self._dgs_circuit,
                    simulation_domain=self._target_domain,
                )
            )
            graphical_indexes: DgsGraphicalIndexes = build_dgs_graphical_indexes(
                circuit=self._dgs_circuit,
                excluded_element_ids=excluded_root_ids,
            )
        except (DgsDynamicParserContractError, KeyError, TypeError, ValueError) as error:
            self._logger.add_error(
                msg="DGS dynamic model import is unavailable",
                value=str(error),
            )
            return self._conversion_result
        # Todo: at this point I think circuit.rms_models should be empty
        if self._target_domain == DynamicSimulationMode.RMS:
            existing_names: Set[str] = set(
                template.name for template in self._circuit.rms_models
            )
        else:
            existing_names = set(
                template.name for template in self._circuit.emt_models
            )

        materialized_count: int = 0
        failed_count: int = 0
        root_id: str
        root_element: ElmComp
        for root_id, root_element in unique_root_by_id.items():
            host_identity: Tuple[str, DeviceType, str, str | None] | None = (
                self._resolve_dgs_direct_root_host_identity(

                    root_element=root_element,
                )
            )
            if host_identity is not None and not self._is_selected_dgs_root_for_host(root_element, host_identity):
                self._logger.add_info(
                    msg="DGS secondary or out-of-service root retained without physical assembly",
                    device=root_element.loc_name, device_class="ElmComp", value=root_id)
                host_identity = None
            else:
                pass
            source_vsc: ElmVsc | ElmVscmono | None = None
            unsupported_vsc_options: List[str] = []
            if host_identity is not None and host_identity[2] in {"ElmVsc", "ElmVscmono"}:
                sources = (self._dgs_circuit.elmvscs if host_identity[2] == "ElmVsc"
                           else self._dgs_circuit.elmvscmonos)
                matches = [source for source in sources if source.ID == host_identity[0]]
                if len(matches) == 1:
                    source_vsc = matches[0]
                    unsupported_vsc_options = get_unsupported_dgs_vsc_options(source_vsc)
                if unsupported_vsc_options:
                    self._logger.add_warning(
                        msg="DGS converter options require an unsupported RMS equipment model",
                        device=host_identity[3],
                        device_class=host_identity[2],
                        value="; ".join(unsupported_vsc_options),
                    )
            if unsupported_vsc_options:
                # Keep the parsed controller available, without constructing
                # equipment equations for a native option we do not implement.
                host_identity = None
            source_block: Block | None
            direct_result: DgsDirectRootBuildResult | None = None
            try:
                root_result: DgsRootBlockResult = build_dgs_root_block_from_circuit(
                    circuit=self._dgs_circuit,
                    parsed_blocks=parsed_blocks,
                    root_name=root_element.loc_name,
                    root_typ_id=root_element.typ_id,
                    root_dgs_id=root_id,
                )
                direct_result = build_direct_root_elmcomp_block(
                    circuit=self._dgs_circuit,
                    result=root_result,
                    graphical_indexes=graphical_indexes,
                )
                source_block = direct_result.root_block
            except (
                    DgsDynamicParserContractError,
                    KeyError,
                    TypeError,
                    UnsupportedDgsExpression,
                    ValueError,
            ) as error:
                self._logger.add_warning(
                    msg="DGS dynamic root could not be materialized",
                    device=root_element.loc_name,
                    device_class="ElmComp",
                    value=str(error),
                )
                failed_count += 1
                source_block = None

            if source_block is None or direct_result is None:
                pass
            else:
                try:
                    multi_plans: tuple[NativeDgsEquipmentPlan, ...] = detect_native_dgs_equipment(direct_result, self._dgs_circuit)
                    if self._target_domain == DynamicSimulationMode.RMS and len(multi_plans) > 1:
                        parts: List[DgsModelPartition] = self._convert_partitioned_root(root_element, direct_result, multi_plans)
                        for part in parts:
                            if part.template is not None and self._register_dgs_direct_template(
                                    part.template, f"{root_id}:{part.device.idtag}", existing_names):
                                materialized_count += 1
                            else:
                                raise ValueError("DGS partition template could not be registered")
                        self._conversion_result.partitions_by_root_dgs_id[root_id] = parts
                        self._conversion_result.child_blocks_by_root_and_slot_id[root_id] = dict(direct_result.child_block_by_slot_id)
                    else:
                        self._convert_single_direct_root(root_id, root_element, direct_result, source_block,
                                                         host_identity, existing_names)
                        materialized_count += 1
                except (DgsDynamicParserContractError, KeyError, TypeError, UnsupportedDgsExpression, ValueError) as error:
                    self._logger.add_warning(
                        msg="DGS dynamic root could not be assembled",
                        device=root_element.loc_name, device_class="ElmComp", value=str(error))
                    failed_count += 1

        # Isolated BlkRef occurrences are valid reusable DGS definitions even when
        # the file has no ElmComp root or physical host. Materialize one final
        # catalogue template per exact BlkDef without creating Bundle/Entry state.
        standalone_occurrences: List[DgsStandaloneBlockOccurrence] = (
            list_dgs_blkref_catalog_occurrences_from_circuit(circuit=self._dgs_circuit)
        )
        standalone_id_count: Dict[str, int] = dict()
        standalone_occurrence: DgsStandaloneBlockOccurrence
        for standalone_occurrence in standalone_occurrences:
            standalone_id: str = str(standalone_occurrence.blkref_id).strip()
            current_count: int | None = standalone_id_count.get(standalone_id, None)
            if current_count is None:
                standalone_id_count[standalone_id] = 1
            else:
                standalone_id_count[standalone_id] = current_count + 1

        elmcomp_ids: Set[str] = set()
        source_root: ElmComp
        for source_root in self._dgs_circuit.elmcomps:
            elmcomp_ids.add(str(source_root.ID).strip())
        materialized_standalone_type_ids: Set[str] = set()
        for standalone_occurrence in standalone_occurrences:
            standalone_id = str(standalone_occurrence.blkref_id).strip()
            standalone_id_occurrences: int | None = standalone_id_count.get(
                standalone_id,
                None,
            )
            standalone_is_eligible: bool = bool(
                not standalone_occurrence.connected
                and standalone_id != ""
                and standalone_id_occurrences == 1
                and standalone_id not in elmcomp_ids
                and standalone_occurrence.typ_id
                not in materialized_standalone_type_ids
            )
            if not standalone_is_eligible:
                pass
            else:
                parsed_standalone: ParsedDgsBlockDefinition | None = (
                    parsed_blocks.get(standalone_occurrence.typ_id, None)
                )
                if parsed_standalone is None:
                    self._logger.add_warning(
                        msg="Isolated DGS BlkRef skipped because its BlkDef is missing",
                        device=standalone_occurrence.sample_display_name,
                        device_class="BlkRef",
                        value=standalone_id,
                    )
                    failed_count += 1
                else:
                    try:
                        standalone_block: Block = (
                            build_standalone_blkdef_block_from_parsed_block(
                                parsed_block=parsed_standalone,
                                block_name=parsed_standalone.blkdef.loc_name,
                            )
                        )
                        standalone_template: RmsModelTemplate | EmtModelTemplate = (
                            self._build_dgs_direct_runtime_template(
                                source_block=standalone_block,
                                template_name=parsed_standalone.blkdef.loc_name,
                                device_tpe=DeviceType.DynamicModelHostDevice,
                                direct_result=None,
                                host_device=None,
                                native_measurement_specs=list(),
                            )
                        )
                        standalone_registered: bool = self._register_dgs_direct_template(
                            template_obj=standalone_template,
                            root_dgs_id=standalone_id,
                            existing_names=existing_names,
                        )
                    except (
                            KeyError,
                            TypeError,
                            UnsupportedDgsExpression,
                            ValueError,
                    ) as error:
                        self._logger.add_warning(
                            msg="Isolated DGS BlkRef could not be materialized",
                            device=standalone_occurrence.sample_display_name,
                            device_class="BlkRef",
                            value=str(error),
                        )
                        failed_count += 1
                    else:
                        materialized_standalone_type_ids.add(
                            standalone_occurrence.typ_id
                        )
                        if standalone_registered:
                            materialized_count += 1
                        else:
                            failed_count += 1

        self._logger.add_info(
            msg="DGS dynamic template conversion completed",
            value=(
                f"templates={materialized_count}, "
                f"failed={failed_count}"
            ),
        )
        return self._conversion_result

    def _convert_partitioned_root(self, root_element: ElmComp, direct: DgsDirectRootBuildResult,
                                  plans: tuple[NativeDgsEquipmentPlan, ...]) -> List[DgsModelPartition]:
        """Assign whole controller instances and build one native template per host.

        :param root_element: Composite selected by the physical devices.
        :param direct: Complete controller graph and exact source slot relations.
        :param plans: All native requirements in this composite.
        :return: Deterministically ordered, independently owned partitions.
        """
        native_hosts: Dict[str, str] = dict()
        devices: Dict[str, DynamicDevice] = dict()
        plan: NativeDgsEquipmentPlan
        for plan in plans:
            device_type: DeviceType | None = get_dgs_dynamic_host_device_tpe(plan.entry.element_kind)
            matches: List[DynamicDevice] = _find_exact_dgs_dynamic_host_devices(
                self._circuit, str(plan.entry.element_id), device_type, str(plan.entry.element_kind))
            if len(matches) != 1:
                raise ValueError(f"DGS partition requires one exact device: {plan.entry.element_id}")
            else:
                device: DynamicDevice = matches[0]
                identity: Tuple[str, DeviceType, str, str | None] = (
                    device.idtag, device.device_type, str(plan.entry.element_kind), plan.entry.element_name)
                if not self._is_selected_dgs_root_for_host(root_element, identity):
                    raise ValueError(f"DGS composite is not active and selected by device {device.name}")
                elif device.idtag in devices:
                    raise ValueError("DGS composite repeats a native physical device")
                else:
                    devices[device.idtag] = device
                    native_hosts[str(plan.entry.slot_id)] = device.idtag
        owners: Dict[str, str] = assign_dgs_slot_owners(direct, self._dgs_circuit, native_hosts)
        parts: List[DgsModelPartition] = list()
        host_id: str
        for host_id in sorted(devices):
            plan = next(candidate for candidate in plans if candidate.entry.element_id == host_id)
            device = devices[host_id]
            slots: Set[str] = set(slot for slot, host in owners.items() if host == device.idtag)
            control: Block = Block(name=f"{root_element.loc_name} / {device.name} control")
            control.children = list(child for slot, child in direct.child_block_by_slot_id.items() if slot in slots)
            parts.append(DgsModelPartition(plan, device, control, slots))
        aggregate: Block = Block(children=list(part.control for part in parts))
        # Root-level executable content belongs once to the stable first host.
        original: Block = direct.root_block
        original.children = list()
        if (len(original.state_vars) > 0 or len(original.algebraic_eqs) > 0
                or len(original.parameters) > 0 or len(original.procedural_logic) > 0):
            parts[0].control.add(original)
        else:
            pass
        # Reserve native measurement producers before assembling equipment. Their
        # actual physical expressions are bound once standard network shells exist.
        meter_view: DgsDirectRootBuildResult = DgsDirectRootBuildResult(
            aggregate, direct.child_block_by_slot_id, direct.graphical_tree_by_slot_id,
            list(entry for entry in direct.direct_entries if entry.element_kind not in ("ElmDsl", "ElmComp")))
        specs: List[_DgsRmsMeasurementSpec] = self._collect_native_dgs_rms_measurement_specs(root_element, meter_view, None)
        spec: _DgsRmsMeasurementSpec
        for spec in specs:
            meter_entries: List[ElmCompInstanceEntry] = list(entry for entry in direct.direct_entries
                if entry.element_id == spec.source_fid or entry.slot_id == spec.source_fid)
            if len(meter_entries) != 1 or meter_entries[0].slot_id is None:
                raise ValueError("Native measurement has no unique source slot")
            else:
                slot_id: str = meter_entries[0].slot_id
                part: DgsModelPartition = next(candidate for candidate in parts if slot_id in candidate.slots)
                outputs: Dict[str, Var] = dict()
                substitutions: Dict[Var, Var] = dict()
                connection: _DgsRmsMeasurementConnection
                for connection in spec.connections:
                    _remove_meter_target_fallback_ownership(aggregate, connection.target_var)
                    if connection.alias_name not in outputs:
                        outputs[connection.alias_name] = connection.target_var
                    else:
                        substitutions[connection.target_var] = outputs[connection.alias_name]
                aggregate.update_model_bulk(substitutions)
                meter: Block = Block(name=spec.source_name, out_vars=list(outputs.values()),
                                     algebraic_vars=list(outputs.values()),
                                     algebraic_eqs=list(variable - Const(0.0) for variable in outputs.values()))
                part.control.add(meter)
                direct.child_block_by_slot_id[slot_id] = meter
        for part in parts:
            _apply_composite_child_interface_if_missing(part.control)
            context: DgsDirectRootBuildResult = DgsDirectRootBuildResult(
                part.control, direct.child_block_by_slot_id, direct.graphical_tree_by_slot_id,
                list(entry for entry in direct.direct_entries
                     if entry.slot_id not in native_hosts or entry.slot_id == part.plan.entry.slot_id))
            machine_parameters: DgsElmSymMachineParameters | None = None
            if part.plan.kind == NativeDgsEquipmentKind.SynchronousMachine and isinstance(part.device, Generator):
                machine_parameters = self._build_exact_dgs_elmsym_machine_parameters(part.device.idtag, part.device)
            else:
                pass
            equipment: Block = construct_native_dgs_equipment(part.plan, part.device, self._dgs_circuit,
                float(self._circuit.Sbase), float(self._circuit.fBase), machine_parameters)
            assembled: Block = assemble_native_dgs_model(part.plan, equipment, context, self._dgs_circuit,
                                                          self._logger, controller_scope=aggregate)
            # A flat top-level diagram exposes the native block and local controls.
            assembled.children = list()
            root: Block = Block(name=f"{root_element.loc_name} / {part.device.name}",
                                children=list((assembled,)), in_vars=list(assembled.in_vars),
                                out_vars=list(assembled.out_vars), external_mapping=dict(assembled.external_mapping))
            root.dynamic_model_contract = copy.deepcopy(assembled.dynamic_model_contract)
            root.children.extend(part.control.children)
            local_outputs: Set[int] = set(variable.uid for child in part.control.children for variable in child.out_vars)
            root.in_vars = list(variable for variable in assembled.in_vars if variable.uid not in local_outputs)
            child: Block
            index: int
            for index, child in enumerate(root.children):
                root.diagram.add_node(name=child.name, x=float((index % 4) * 260), y=float((index // 4) * 180),
                                      tpe="TEMPLATE", device_uid=child.uid)
            template: RmsModelTemplate = RmsModelTemplate(name=root.name)
            template.tpe = part.device.device_type
            template.block = root
            template.comment = f"PowerFactory DGS composite {root_element.ID}; device {part.device.idtag}"
            part.template = template
        self._logger.add_info(msg="DGS composite partitioned into physical devices", device=root_element.loc_name,
                              value=", ".join(part.device.idtag for part in parts))
        return parts

    def finalize_partitioned_roots(self) -> bool:
        """Complete independent multi-host imports after network model preparation.

        A failed composite remains inspectable without activating incomplete
        equations or preventing other source composites from being imported.

        :return: True when no partition requires a default-model fallback.
        """
        successful: bool = True
        root_id: str
        parts: List[DgsModelPartition]
        part: DgsModelPartition
        for root_id, parts in self._conversion_result.partitions_by_root_dgs_id.items():
            if any(part.template is None or part.device.rms_template is not part.template for part in parts):
                successful = False
            elif all(part.template.block.uid == part.device.rms_model.uid for part in parts):
                pass
            else:
                try:
                    self._finalize_partitioned_root(root_id, parts)
                except (KeyError, TypeError, ValueError, StopIteration) as error:
                    successful = False
                    for part in parts:
                        if part.template is not None:
                            part.template.tpe = DeviceType.DynamicModelHostDevice
                        else:
                            pass
                        part.device.rms_template = None
                        part.device.rms_model = Block()
                    self._logger.add_warning(msg="DGS partitioned root retained without activation",
                                             device=root_id, value=str(error))
                else:
                    pass
        return successful

    def _finalize_partitioned_root(self, root_id: str, parts: List[DgsModelPartition]) -> None:
        """Connect final instance UIDs and resolve exact physical meter expressions.

        :param root_id: Source composite identity.
        :param parts: Constructed and activated equipment partitions.
        :return: None.
        """
        runtime_slots: Dict[str, Block] = dict()
        canonical_slots: Dict[str, Block] = self._conversion_result.child_blocks_by_root_and_slot_id[root_id]
        part: DgsModelPartition
        for part in parts:
            copy_partition_diagrams(part.template.block, part.device.rms_model)
            runtime_slots.update(_translate_slot_blocks_to_runtime(part.template.block, part.device.rms_model,
                                                                   canonical_slots))
        connect_dgs_partitions(parts, self._circuit.var_factory)
        source_root: ElmComp = next(root for root in self._dgs_circuit.elmcomps if root.ID == root_id)
        entries: List[ElmCompInstanceEntry] = get_unique_elmcomp_slot_entries(
            extract_elmcomp_direct_instances(self._dgs_circuit, source_root))
        view: DgsDirectRootBuildResult = DgsDirectRootBuildResult(
            Block(), runtime_slots, dict(), list(entry for entry in entries
                                                  if entry.element_kind not in ("ElmDsl", "ElmComp")))
        specs: List[_DgsRmsMeasurementSpec] = self._collect_native_dgs_rms_measurement_specs(source_root, view, None)
        elements: Dict[str, DGSElement] = _build_dgs_element_index(self._dgs_circuit)
        all_devices: dict = self._circuit.get_all_elements_dict()[0]
        devices: Dict[str, DynamicDevice] = dict((key, value) for key, value in all_devices.items()
                                                if isinstance(value, DynamicDevice))
        buses: Dict[str, Bus] = dict((bus.idtag, bus) for bus in self._circuit.buses)
        spec: _DgsRmsMeasurementSpec
        for spec in specs:
            entry: ElmCompInstanceEntry = next(entry for entry in entries
                if entry.element_id == spec.source_fid or entry.slot_id == spec.source_fid)
            part = next(candidate for candidate in parts if entry.slot_id in candidate.slots)
            meter: DGSElement | None = spec.meter_element
            names: List[str] = list(dict.fromkeys(connection.alias_name for connection in spec.connections))
            aliases: Dict[str, Expr] = dict()
            prepared: Block | None = None
            if isinstance(meter, StaVmea):
                bus: Bus | None = buses.get(str(meter.pbusbar).lstrip('#'), None)
                if bus is not None:
                    aliases = _build_voltage_alias_expressions(meter, names, bus)
                else:
                    raise ValueError(f"Unresolved DGS voltage measurement terminal: {spec.source_fid}")
            elif isinstance(meter, (StaImea, StaPqmea)):
                measured_device: DynamicDevice | None
                measured_bus: Bus | None
                terminal: int | None
                measured_device, measured_bus, terminal = _resolve_cubicle_source(
                    str(meter.pcubic).lstrip('#'), elements, devices, buses)
                if measured_device is None or measured_bus is None or terminal is None:
                    raise ValueError(f"Unresolved DGS measurement cubicle: {spec.source_fid}")
                elif isinstance(meter, StaImea):
                    aliases = _build_current_alias_expressions(meter, names, measured_bus, measured_device,
                        terminal, float(self._circuit.Sbase), host_model=part.device.rms_model)
                else:
                    aliases = _build_power_alias_expressions(meter, names, measured_device, terminal,
                        float(self._circuit.Sbase), self._circuit, part.device, self._import_metadata)
            elif isinstance(meter, ElmPhi):
                bus = buses.get(str(meter.pbusbar).lstrip('#'), None)
                if bus is not None or spec.use_stationary_reference:
                    aliases, prepared = _build_pll_alias_expressions(self._circuit, names,
                        part.device.bus if bus is None else bus, meter, spec.source_fid, spec.use_stationary_reference)
                else:
                    raise ValueError(f"Unresolved DGS PLL terminal: {spec.source_fid}")
            else:
                raise ValueError(f"Unsupported partitioned DGS measurement: {spec.source_fid}")
            targets: Dict[str, List[Var]] = dict()
            connection: _DgsRmsMeasurementConnection
            for connection in spec.connections:
                if connection.alias_name not in targets:
                    targets[connection.alias_name] = list()
                else:
                    pass
                targets[connection.alias_name].append(connection.target_var)
            if set(aliases) != set(targets):
                raise ValueError(f"Incomplete partitioned DGS measurement outputs: {spec.source_fid}")
            else:
                connected: int = _connect_meter_aliases(part.device.rms_model, targets, aliases, spec.source_name,
                    spec.meter_kind, self._circuit.var_factory, prepared, self._import_metadata)
                if connected == 0:
                    raise ValueError(f"DGS partition measurement could not be connected: {spec.source_fid}")
                else:
                    pass
        # Persist the completed graph, including interconnection nodes, using
        # existing UID/factory semantics. No import plan survives in runtime.
        for part in parts:
            owner: Block
            for owner in part.device.rms_model.get_all_blocks():
                # VarFactory has propagated cross-model UIDs; keyed startup
                # dictionaries must now use those same effective identities.
                rehash_block_var_keyed_dicts(owner)
                owner.post_init_seed_eqs = dict(owner.post_init_seed_eqs.items())
            build_partition_diagram_connections(part.device.rms_model)
            part.template.block = part.device.rms_model.copy()
        self._logger.add_info(msg="DGS partition interconnections and measurements finalized", device=source_root.loc_name,
                              value=f"devices={len(parts)}")

    def _convert_single_direct_root(self, root_id: str, root_element: ElmComp,
                                    direct_result: DgsDirectRootBuildResult, source_block: Block,
                                    host_identity: Tuple[str, DeviceType, str, str | None] | None,
                                    existing_names: Set[str]) -> None:
        """Preserve the existing one-host construction path.

        :param root_id: Exact composite identity.
        :param root_element: Source composite.
        :param direct_result: Parsed children and slot relations.
        :param source_block: Owned controller root.
        :param host_identity: Selected physical host, if present.
        :param existing_names: Registered template names.
        :return: None.
        """
        host_device_for_measurements: DynamicDevice | None = None
        if host_identity is None:
            resolved_device_tpe: DeviceType = (
                DeviceType.DynamicModelHostDevice
            )
            native_kind: NativeDgsEquipmentKind | None = None
        else:
            host_device_tpe: DeviceType = host_identity[1]
            native_kind = self._native_runtime_validation_kind(direct_result)
            native_runtime_ready: bool = (
                is_dgs_dynamic_block_runtime_assignable(
                    block=source_block,
                    device_tpe=host_device_tpe,
                    native_kind=native_kind,
                )
            )
            native_construction_supported: bool = (
                    self._target_domain == DynamicSimulationMode.RMS
                    and native_kind is not None
            )
            typed_vsc_contract_ready: bool = bool(
                host_device_tpe != DeviceType.VscDevice
                or native_kind is not None
            )
            if (
                    typed_vsc_contract_ready
                    and (native_runtime_ready or native_construction_supported)
            ):
                resolved_device_tpe = host_device_tpe
            else:
                resolved_device_tpe = DeviceType.DynamicModelHostDevice
                self._logger.add_warning(
                    msg=(
                        "DGS dynamic root retained as a generic template "
                        "because its physical runtime contract is unsupported"
                    ),
                    device=root_element.loc_name,
                    device_class="ElmComp",
                    value=root_id,
                )

            exact_host_devices_for_measurements: List[DynamicDevice] = (
                _find_exact_dgs_dynamic_host_devices(
                    circuit=self._circuit,
                    source_element_dgs_id=host_identity[0],
                    device_tpe=host_identity[1],
                    source_element_class=host_identity[2],
                )
            )
            if len(exact_host_devices_for_measurements) == 1:
                host_device_for_measurements = (
                    exact_host_devices_for_measurements[0]
                )
            else:
                pass

        native_measurement_specs: List[_DgsRmsMeasurementSpec] = (
            self._collect_native_dgs_rms_measurement_specs(
                root_element=root_element,
                direct_result=direct_result,
                host_device=host_device_for_measurements,
            )
        )
        template_obj: RmsModelTemplate | EmtModelTemplate = (
            self._build_dgs_direct_runtime_template(
                source_block=source_block,
                template_name=root_element.loc_name,
                device_tpe=resolved_device_tpe,
                direct_result=direct_result if host_identity is not None else None,
                host_device=host_device_for_measurements,
                native_measurement_specs=native_measurement_specs,
            )
        )
        registered: bool = self._register_dgs_direct_template(
            template_obj=template_obj,
            root_dgs_id=root_id,
            existing_names=existing_names,
        )
        if registered:
            self._conversion_result.templates_by_root_dgs_id[root_id] = template_obj
            self._conversion_result.child_blocks_by_root_and_slot_id[root_id] = (
                dict(direct_result.child_block_by_slot_id)
            )
            pass
        else:
            raise ValueError("DGS template could not be registered")

    def apply_templates_to_devices(self) -> None:
        """Configure and install each imported model on its exact physical host.

        :return: None; metadata remains keyed by the installed model identities.
        """
        activated_count: int = 0
        failed_count: int = 0
        unique_root_by_id: Dict[str, ElmComp] = self._get_unique_dgs_dynamic_roots_by_id(

            emit_diagnostics=False,
        )
        root_id: str
        root_element: ElmComp
        for root_id, root_element in unique_root_by_id.items():
            template_obj: RmsModelTemplate | EmtModelTemplate | None = (
                self._conversion_result.templates_by_root_dgs_id.get(root_id, None)
            )
            partitioned: List[DgsModelPartition] | None = self._conversion_result.partitions_by_root_dgs_id.get(root_id, None)
            if partitioned is not None:
                try:
                    for part in partitioned:
                        identity: Tuple[str, DeviceType, str, str | None] = (
                            part.device.idtag, part.device.device_type, str(part.plan.entry.element_kind), part.plan.entry.element_name)
                        if part.template is not None and self._activate_dgs_direct_template(part.template, identity, part.plan.kind):
                            pass
                        else:
                            raise ValueError(f"DGS partition could not be activated: {part.device.name}")
                except (KeyError, TypeError, ValueError) as error:
                    for part in partitioned:
                        part.device.rms_template = None
                        part.device.rms_model = Block()
                    self._logger.add_warning(msg="DGS partitioned root could not be activated", device=root_id, value=str(error))
                    failed_count += 1
                else:
                    activated_count += len(partitioned)
            elif template_obj is None:
                pass
            else:
                host_identity: Tuple[
                                   str,
                                   DeviceType,
                                   str,
                                   str | None,
                               ] | None = self._resolve_dgs_direct_root_host_identity(

                    root_element=root_element,
                )
                if host_identity is None or not self._is_selected_dgs_root_for_host(root_element, host_identity):
                    pass
                else:
                    # Each native family is named by its source class, so the host class selects it
                    native_kinds: Dict[str, NativeDgsEquipmentKind] = dict(
                        (kind.value, kind) for kind in NativeDgsEquipmentKind)
                    native_kind: NativeDgsEquipmentKind | None = native_kinds.get(host_identity[2], None)
                    try:
                        activated: bool = self._activate_dgs_direct_template(
                            template_obj=template_obj, host_identity=host_identity, native_kind=native_kind)
                    except (DgsDynamicParserContractError, KeyError, TypeError, UnsupportedDgsExpression, ValueError) as error:
                        activated = False
                        self._logger.add_warning(
                            msg="DGS dynamic root could not be activated",
                            device=root_element.loc_name, device_class="ElmComp", value=str(error))
                    else:
                        pass
                    if activated:
                        hosts: List[DynamicDevice] = _find_exact_dgs_dynamic_host_devices(
                            self._circuit, host_identity[0], host_identity[1], host_identity[2],
                        )
                        if len(hosts) == 1:
                            self._conversion_result.models_by_root_dgs_id[root_id] = (
                                hosts[0].rms_model if isinstance(template_obj, RmsModelTemplate)
                                else hosts[0].emt_model
                            )
                        else:
                            pass
                        activated_count += 1
                    else:
                        failed_count += 1

        self._logger.add_info(
            msg="DGS dynamic device assignment completed",
            value=f"activated={activated_count}, failed={failed_count}",
        )


def _apply_composite_child_interface_if_missing(block: Block) -> None:
    """
    Synthesize one composite interface from child ports when the root lacks one.

    :param block: Candidate composite root block.
    :return: None.
    """
    input_vars_by_uid: Dict[int, Var] = dict()
    output_vars_by_uid: Dict[int, Var] = dict()
    child_block: Block
    input_var: Var
    output_var: Var

    if len(block.children) == 0:
        return
    else:
        pass

    if len(block.in_vars) > 0 or len(block.out_vars) > 0:
        return
    else:
        pass

    # first we discard variables that are interconected between child blocks
    intern_connected_vars_list: List[Var] = list()
    for child_block1 in block.children:
        for child_block2 in block.children:
            pairs, power_flow_pairs = find_connections(child_block1, child_block2)
            for pair in pairs:
                for var in pair:
                    intern_connected_vars_list.append(var)
            for power_flow_pair in power_flow_pairs:
                for var in power_flow_pair:
                    intern_connected_vars_list.append(var)

    for child_block in block.children:
        # Preserve the child order so imported reusable-template ports stay stable.
        for input_var in child_block.in_vars:
            if input_var.uid in input_vars_by_uid or input_var in intern_connected_vars_list:
                pass
            else:
                input_vars_by_uid[input_var.uid] = input_var

        for output_var in child_block.out_vars:
            if output_var.uid in output_vars_by_uid or output_var in intern_connected_vars_list:
                pass
            else:
                output_vars_by_uid[output_var.uid] = output_var

    block.in_vars = list(input_vars_by_uid.values())
    block.out_vars = list(output_vars_by_uid.values())


def _get_internally_connected_input_object_ids(block: Block) -> Set[int]:
    """Return child-input object identities supplied by another child.

    The DGS materializer reuses the exact ``Var`` identity, UID or shared
    reference when it resolves a routed signal. Only inputs absent from this
    internal graph belong to the public power-flow interface.

    :param block: Composite block whose direct children form the signal graph.
    :return: Object identities of child inputs connected inside the composite.
    """
    connected_input_object_ids: Set[int] = set()
    source_block: Block
    target_block: Block
    signal_pairs: List[tuple[Var, Var]]
    power_flow_pairs: List[tuple[Var, Var]]
    signal_pair: tuple[Var, Var]

    # Inspect every directed child pair because DGS signal routing is ordered
    # from a producer output to a consumer input.
    for source_block in block.children:
        for target_block in block.children:
            if source_block is target_block:
                pass
            else:
                signal_pairs, power_flow_pairs = find_connections(
                    source_block,
                    target_block,
                )
                for signal_pair in signal_pairs:
                    connected_input_object_ids.add(id(signal_pair[1]))
                for signal_pair in power_flow_pairs:
                    connected_input_object_ids.add(id(signal_pair[1]))

    return connected_input_object_ids


def _resolve_dgs_external_input_reference(
        input_name: str,
        device_tpe: DeviceType,
) -> VarPowerFlowReferenceType | None:
    """Resolve one public DGS input into its power-flow reference.

    Names are interpreted only after topology has proved that the input has no
    internal producer. Branch-like VSC measurements use terminal-specific
    references so equal physical quantities at opposite terminals cannot be
    joined by the editor merely because their generic reference matches.

    :param input_name: Imported DGS signal name.
    :param device_tpe: Physical device family owning the composite model.
    :return: Matching power-flow reference, or ``None`` for a control signal.
    """
    normalized_name: str = input_name.strip().lower()
    reference: VarPowerFlowReferenceType | None

    if device_tpe == DeviceType.VscDevice:
        vsc_references: Dict[str, VarPowerFlowReferenceType] = dict((
            ("vdc", VarPowerFlowReferenceType.Vf_dc),
            ("vm", VarPowerFlowReferenceType.Vmt),
            ("va", VarPowerFlowReferenceType.Vat),
            ("u", VarPowerFlowReferenceType.Ut),
            ("ur", VarPowerFlowReferenceType.URt),
            ("ui", VarPowerFlowReferenceType.UIt),
            ("ur_a", VarPowerFlowReferenceType.URt_A),
            ("ur_b", VarPowerFlowReferenceType.URt_B),
            ("ur_c", VarPowerFlowReferenceType.URt_C),
            ("ui_a", VarPowerFlowReferenceType.UIt_A),
            ("ui_b", VarPowerFlowReferenceType.UIt_B),
            ("ui_c", VarPowerFlowReferenceType.UIt_C),
            ("p_act", VarPowerFlowReferenceType.Pt),
            ("q_act", VarPowerFlowReferenceType.Qt),
            ("cosphi", VarPowerFlowReferenceType.COSPHIt),
            ("sinphi", VarPowerFlowReferenceType.SINPHIt),
            ("cosref", VarPowerFlowReferenceType.COSPHIt),
            ("sinref", VarPowerFlowReferenceType.SINPHIt),
        ))
        reference = vsc_references.get(normalized_name, None)
    else:
        device_is_injection: bool = device_tpe in (
            DeviceType.GeneratorDevice,
            DeviceType.LoadDevice,
            DeviceType.BatteryDevice,
            DeviceType.ControllableShuntDevice,
        )
        if device_is_injection:
            injection_references: Dict[str, VarPowerFlowReferenceType] = dict((
                ("vm", VarPowerFlowReferenceType.Vm),
                ("va", VarPowerFlowReferenceType.Va),
                ("u", VarPowerFlowReferenceType.U),
                ("ur", VarPowerFlowReferenceType.UR),
                ("ui", VarPowerFlowReferenceType.UI),
                ("ur_a", VarPowerFlowReferenceType.UR_A),
                ("ur_b", VarPowerFlowReferenceType.UR_B),
                ("ur_c", VarPowerFlowReferenceType.UR_C),
                ("ui_a", VarPowerFlowReferenceType.UI_A),
                ("ui_b", VarPowerFlowReferenceType.UI_B),
                ("ui_c", VarPowerFlowReferenceType.UI_C),
                ("p_act", VarPowerFlowReferenceType.P),
                ("q_act", VarPowerFlowReferenceType.Q),
                ("cosphi", VarPowerFlowReferenceType.COSPHI),
                ("sinphi", VarPowerFlowReferenceType.SINPHI),
                ("cosref", VarPowerFlowReferenceType.COSPHI),
                ("sinref", VarPowerFlowReferenceType.SINPHI),
            ))
            reference = injection_references.get(normalized_name, None)
        else:
            reference = None

    return reference


def _assign_dgs_external_input_references(
        block: Block,
        device_tpe: DeviceType,
) -> None:
    """Type child inputs that remain exposed outside a DGS composite.

    :param block: Fully connected composite built from direct DGS children.
    :param device_tpe: Physical device family owning the composite model.
    :return: None.
    """
    connected_input_object_ids: Set[int] = (
        _get_internally_connected_input_object_ids(block=block)
    )
    child_block: Block
    input_var: Var
    resolved_reference: VarPowerFlowReferenceType | None

    # Preserve internal control signals unchanged. The editor must only create
    # physical measurement blocks for inputs that cross the root boundary.
    for child_block in block.children:
        for input_var in child_block.in_vars:
            if id(input_var) in connected_input_object_ids:
                pass
            else:
                resolved_reference = _resolve_dgs_external_input_reference(
                    input_name=input_var.name,
                    device_tpe=device_tpe,
                )
                if resolved_reference is None:
                    pass
                else:
                    input_var.ref = resolved_reference


def _collect_unconnected_dgs_child_inputs(
        block: Block,
) -> List[Tuple[Block, Var]]:
    """Collect direct-child inputs that have no producer inside a composite.

    :param block: Composite DGS root whose direct children are inspected.
    :return: Ordered owner-variable pairs for unconnected child inputs.
    """
    connected_input_object_ids: Set[int] = (
        _get_internally_connected_input_object_ids(block=block)
    )
    unconnected_inputs: List[Tuple[Block, Var]] = list()
    child_block: Block
    input_var: Var
    for child_block in block.children:
        for input_var in child_block.in_vars:
            if id(input_var) in connected_input_object_ids:
                pass
            else:
                unconnected_inputs.append((child_block, input_var))
    return unconnected_inputs


def _classify_rms_measurement_terminal(
        reference: VarPowerFlowReferenceType,
) -> RmsTerminalSide | None:
    """Classify one measurement reference by its physical terminal.

    :param reference: Typed power-flow or measurement reference.
    :return: From, to, bus, or ``None`` when the reference is not measurable.
    """
    from_references: Set[VarPowerFlowReferenceType] = set((
        VarPowerFlowReferenceType.Vmf,
        VarPowerFlowReferenceType.Vaf,
        VarPowerFlowReferenceType.Vf_dc,
        VarPowerFlowReferenceType.Pf,
        VarPowerFlowReferenceType.Qf,
        VarPowerFlowReferenceType.Uf,
        VarPowerFlowReferenceType.URf,
        VarPowerFlowReferenceType.UIf,
        VarPowerFlowReferenceType.URf_A,
        VarPowerFlowReferenceType.URf_B,
        VarPowerFlowReferenceType.URf_C,
        VarPowerFlowReferenceType.UIf_A,
        VarPowerFlowReferenceType.UIf_B,
        VarPowerFlowReferenceType.UIf_C,
        VarPowerFlowReferenceType.COSPHIf,
        VarPowerFlowReferenceType.SINPHIf,
        VarPowerFlowReferenceType.If_dc,
    ))
    to_references: Set[VarPowerFlowReferenceType] = set((
        VarPowerFlowReferenceType.Vmt,
        VarPowerFlowReferenceType.Vat,
        VarPowerFlowReferenceType.Vt_dc,
        VarPowerFlowReferenceType.Pt,
        VarPowerFlowReferenceType.Qt,
        VarPowerFlowReferenceType.Ut,
        VarPowerFlowReferenceType.URt,
        VarPowerFlowReferenceType.UIt,
        VarPowerFlowReferenceType.URt_A,
        VarPowerFlowReferenceType.URt_B,
        VarPowerFlowReferenceType.URt_C,
        VarPowerFlowReferenceType.UIt_A,
        VarPowerFlowReferenceType.UIt_B,
        VarPowerFlowReferenceType.UIt_C,
        VarPowerFlowReferenceType.COSPHIt,
        VarPowerFlowReferenceType.SINPHIt,
        VarPowerFlowReferenceType.It_dc,
    ))
    bus_references: Set[VarPowerFlowReferenceType] = set((
        VarPowerFlowReferenceType.Vm,
        VarPowerFlowReferenceType.Va,
        VarPowerFlowReferenceType.Vdc,
        VarPowerFlowReferenceType.P,
        VarPowerFlowReferenceType.Q,
        VarPowerFlowReferenceType.U,
        VarPowerFlowReferenceType.UR,
        VarPowerFlowReferenceType.UI,
        VarPowerFlowReferenceType.UR_A,
        VarPowerFlowReferenceType.UR_B,
        VarPowerFlowReferenceType.UR_C,
        VarPowerFlowReferenceType.UI_A,
        VarPowerFlowReferenceType.UI_B,
        VarPowerFlowReferenceType.UI_C,
        VarPowerFlowReferenceType.COSPHI,
        VarPowerFlowReferenceType.SINPHI,
        VarPowerFlowReferenceType.I_DC,
    ))
    if reference in from_references:
        terminal_side: RmsTerminalSide | None = RmsTerminalSide.FROM
    else:
        if reference in to_references:
            terminal_side = RmsTerminalSide.TO
        else:
            if reference in bus_references:
                terminal_side = RmsTerminalSide.BUS
            else:
                terminal_side = None
    return terminal_side


def _get_rms_terminal_physical_references(
        block_type: BlockType,
        terminal_side: RmsTerminalSide,
        is_dc_terminal: bool,
) -> List[VarPowerFlowReferenceType]:
    """Return the physical root inputs required by one RMS measurement.

    :param block_type: Measurement family selected for the imported signals.
    :param terminal_side: Physical terminal represented by the measurement.
    :param is_dc_terminal: Whether the selected physical terminal is DC.
    :return: Ordered physical references required to build the measurement.
    """
    if terminal_side is RmsTerminalSide.FROM:
        vm_reference: VarPowerFlowReferenceType = VarPowerFlowReferenceType.Vmf
        va_reference: VarPowerFlowReferenceType = VarPowerFlowReferenceType.Vaf
        vdc_reference: VarPowerFlowReferenceType = VarPowerFlowReferenceType.Vf_dc
        p_reference: VarPowerFlowReferenceType = VarPowerFlowReferenceType.Pf
        q_reference: VarPowerFlowReferenceType = VarPowerFlowReferenceType.Qf
    else:
        if terminal_side is RmsTerminalSide.TO:
            vm_reference = VarPowerFlowReferenceType.Vmt
            va_reference = VarPowerFlowReferenceType.Vat
            vdc_reference = VarPowerFlowReferenceType.Vt_dc
            p_reference = VarPowerFlowReferenceType.Pt
            q_reference = VarPowerFlowReferenceType.Qt
        else:
            vm_reference = VarPowerFlowReferenceType.Vm
            va_reference = VarPowerFlowReferenceType.Va
            vdc_reference = VarPowerFlowReferenceType.Vdc
            p_reference = VarPowerFlowReferenceType.P
            q_reference = VarPowerFlowReferenceType.Q

    # Each measurement receives the smallest physical contract from which its
    # requested derived signals can be calculated.
    if block_type == BlockType.MEASUREMENTS_VOLTAGE_FROM_POLAR:
        required_references: List[VarPowerFlowReferenceType] = list((
            vm_reference,
            va_reference,
        ))
    else:
        if block_type == BlockType.MEASUREMENTS_PLL:
            required_references = list((va_reference,))
        else:
            if block_type == BlockType.MEASUREMENTS_VOLTAGE_FROM_DC:
                required_references = list((vdc_reference,))
            else:
                if block_type == BlockType.MEASUREMENTS_CURRENT_FROM_PQ:
                    required_references = list((
                        vm_reference,
                        va_reference,
                        p_reference,
                        q_reference,
                    ))
                else:
                    if block_type == BlockType.MEASUREMENTS_VOLTAGE_ANGLE:
                        if is_dc_terminal:
                            required_references = list((vdc_reference,))
                        else:
                            required_references = list((
                                vm_reference,
                                va_reference,
                            ))
                    else:
                        if block_type == BlockType.MEASUREMENTS_P_Q:
                            if is_dc_terminal:
                                required_references = list((p_reference,))
                            else:
                                required_references = list((
                                    p_reference,
                                    q_reference,
                                ))
                        else:
                            required_references = list()
    return required_references


def _get_or_create_dgs_physical_input(
        block: Block,
        reference: VarPowerFlowReferenceType,
        physical_inputs_by_reference: Dict[VarPowerFlowReferenceType, Var],
        var_factory: VarFactory,
) -> Var:
    """Resolve one canonical physical input for an imported DGS template.

    :param block: Imported root that exposes the physical input.
    :param reference: Exact power-flow quantity required by a measurement.
    :param physical_inputs_by_reference: Canonical inputs already allocated.
    :param var_factory: Factory owning newly allocated template variables.
    :return: Canonical physical input for the requested reference.
    """
    physical_input: Var | None = physical_inputs_by_reference.get(reference, None)
    if physical_input is None:
        # The parser has no bus model yet. Create the same typed boundary
        # variable used by native templates so device assignment can connect it
        # to the real bus through ``connect_bus_variables_rms`` later.
        physical_input = var_factory.add_var(
            name=reference.name,
            reference=reference,
        )
        physical_inputs_by_reference[reference] = physical_input
        block.in_vars.append(physical_input)
    else:
        pass
    return physical_input


def _build_dgs_rms_measurement_block(
        block_type: BlockType,
        terminal_side: RmsTerminalSide,
        is_dc_terminal: bool,
        physical_inputs_by_reference: Dict[VarPowerFlowReferenceType, Var],
        var_factory: VarFactory,
) -> Block | None:
    """Build one required RMS measurement for an exact terminal.

    :param block_type: Measurement family selected from the reference catalog.
    :param terminal_side: Physical terminal represented by the block.
    :param is_dc_terminal: Whether the selected physical terminal is DC.
    :param physical_inputs_by_reference: Canonical physical template inputs.
    :param var_factory: Isolated factory owned by this imported template.
    :return: Constructed measurement block, or ``None`` without prerequisites.
    """
    measurement_block: Block | None = None
    variables: List[Var]
    vm: Var | None
    va: Var | None
    vdc: Var | None
    if terminal_side is RmsTerminalSide.FROM:
        vm = physical_inputs_by_reference.get(VarPowerFlowReferenceType.Vmf, None)
        va = physical_inputs_by_reference.get(VarPowerFlowReferenceType.Vaf, None)
        vdc = physical_inputs_by_reference.get(VarPowerFlowReferenceType.Vf_dc, None)
    else:
        if terminal_side is RmsTerminalSide.TO:
            vm = physical_inputs_by_reference.get(VarPowerFlowReferenceType.Vmt, None)
            va = physical_inputs_by_reference.get(VarPowerFlowReferenceType.Vat, None)
            vdc = physical_inputs_by_reference.get(VarPowerFlowReferenceType.Vt_dc, None)
        else:
            vm = physical_inputs_by_reference.get(VarPowerFlowReferenceType.Vm, None)
            va = physical_inputs_by_reference.get(VarPowerFlowReferenceType.Va, None)
            vdc = physical_inputs_by_reference.get(VarPowerFlowReferenceType.Vdc, None)

    if block_type == BlockType.MEASUREMENTS_VOLTAGE_FROM_POLAR:
        if vm is None or va is None:
            pass
        else:
            if terminal_side is RmsTerminalSide.FROM:
                measurement_block, variables = build_rms_voltage_meter_outputs_from_polar_from(
                    var_factory=var_factory,
                    vm=vm,
                    va=va,
                )
            else:
                if terminal_side is RmsTerminalSide.TO:
                    measurement_block, variables = build_rms_voltage_meter_outputs_from_polar_to(
                        var_factory=var_factory,
                        vm=vm,
                        va=va,
                    )
                else:
                    nominal_frequency: Const = var_factory.add_const(50.0)
                    measurement_block, variables = build_rms_voltage_meter_outputs_from_polar(
                        var_factory=var_factory,
                        vm=vm,
                        va=va,
                        measured_frequency_hz=nominal_frequency,
                        nominal_frequency_hz=nominal_frequency,
                    )
                    measurement_block.in_vars = list((vm, va))
                    measurement_block.out_vars = variables
    else:
        if block_type == BlockType.MEASUREMENTS_PLL:
            if va is None:
                pass
            else:
                if terminal_side is RmsTerminalSide.FROM:
                    measurement_block, variables = build_rms_pll_measurements_from(
                        va=va,
                        var_factory=var_factory,
                    )
                else:
                    if terminal_side is RmsTerminalSide.TO:
                        measurement_block, variables = build_rms_pll_measurements_to(
                            va=va,
                            var_factory=var_factory,
                        )
                    else:
                        measurement_block, variables = build_rms_pll_measurements(
                            va=va,
                            var_factory=var_factory,
                        )
        else:
            if block_type == BlockType.MEASUREMENTS_VOLTAGE_FROM_DC:
                if vdc is None:
                    pass
                else:
                    if terminal_side is RmsTerminalSide.FROM:
                        measurement_block, variables = build_rms_voltage_meter_outputs_from_dc_from(
                            var_factory=var_factory,
                            vdc=vdc,
                        )
                    else:
                        if terminal_side is RmsTerminalSide.TO:
                            measurement_block, variables = build_rms_voltage_meter_outputs_from_dc_to(
                                var_factory=var_factory,
                                vdc=vdc,
                            )
                        else:
                            nominal_frequency = var_factory.add_const(50.0)
                            measurement_block, variables = build_rms_voltage_meter_outputs_from_dc(
                                var_factory=var_factory,
                                vdc=vdc,
                                nominal_frequency_hz=nominal_frequency,
                            )
                            measurement_block.in_vars = list((vdc,))
                            measurement_block.out_vars = variables
            else:
                if block_type in (
                        BlockType.MEASUREMENTS_VOLTAGE_ANGLE,
                        BlockType.MEASUREMENTS_P_Q,
                ):
                    pass_through_vars: List[Var] = list()
                    required_references: List[VarPowerFlowReferenceType] = (
                        _get_rms_terminal_physical_references(
                            block_type=block_type,
                            terminal_side=terminal_side,
                            is_dc_terminal=is_dc_terminal,
                        )
                    )
                    required_reference: VarPowerFlowReferenceType
                    for required_reference in required_references:
                        input_var: Var | None = physical_inputs_by_reference.get(
                            required_reference,
                            None,
                        )
                        if block_type == BlockType.MEASUREMENTS_VOLTAGE_ANGLE:
                            include_var: bool = input_var in (vm, va, vdc)
                        else:
                            include_var = (
                                    input_var is not None
                                    and input_var.ref == required_reference
                            )
                        if (
                                include_var
                                and input_var is not None
                                and input_var not in pass_through_vars
                        ):
                            pass_through_vars.append(input_var)
                        else:
                            pass
                    if len(pass_through_vars) == 0:
                        pass
                    else:
                        measurement_block = Block(
                            in_vars=list(pass_through_vars),
                            out_vars=pass_through_vars,
                        )
                else:
                    pass

    if measurement_block is None:
        pass
    else:
        measurement_block.name = block_type.name + "_" + terminal_side.name
    return measurement_block


def _get_native_dgs_measurement_physical_references(
        spec: _DgsRmsMeasurementSpec,
) -> List[VarPowerFlowReferenceType]:
    """Return physical inputs required by one early native measurement.

    :param spec: Resolved native measurement specification.
    :return: Ordered physical power-flow references.
    """
    terminal_side: RmsTerminalSide | None = None
    connection: _DgsRmsMeasurementConnection

    # Native meters may export non-terminal signals first, such as ``fe``
    # before ``u``. Inspect every exact endpoint until one identifies the
    # physical side instead of making the result depend on DGS row order.
    for connection in spec.connections:
        candidate_reference: object = connection.target_var.ref
        if isinstance(candidate_reference, VarPowerFlowReferenceType):
            candidate_terminal_side: RmsTerminalSide | None = (
                _classify_rms_measurement_terminal(
                    reference=candidate_reference,
                )
            )
            if terminal_side is None and candidate_terminal_side is not None:
                terminal_side = candidate_terminal_side
            else:
                pass
        else:
            pass

    if terminal_side is None:
        references: List[VarPowerFlowReferenceType] = list()
    else:
        if spec.meter_kind is RmsPhysicalMeterKind.POWER:
            references = _get_rms_terminal_physical_references(
                block_type=BlockType.MEASUREMENTS_P_Q,
                terminal_side=terminal_side,
                is_dc_terminal=False,
            )
        else:
            if spec.meter_kind is RmsPhysicalMeterKind.VOLTAGE:
                references = _get_rms_terminal_physical_references(
                    block_type=BlockType.MEASUREMENTS_VOLTAGE_FROM_POLAR,
                    terminal_side=terminal_side,
                    is_dc_terminal=False,
                )
            else:
                if spec.meter_kind is RmsPhysicalMeterKind.PHASE_LOCKED_LOOP:
                    references = _get_rms_terminal_physical_references(
                        block_type=BlockType.MEASUREMENTS_PLL,
                        terminal_side=terminal_side,
                        is_dc_terminal=False,
                    )
                else:
                    references = list()

    # Some controller aliases use COSPHI/SINPHI references, whose terminal
    # classification identifies the side but not the voltage-angle prerequisite.
    if (
            spec.meter_kind is RmsPhysicalMeterKind.PHASE_LOCKED_LOOP
            and not spec.use_stationary_reference
            and terminal_side is not None
    ):
        if terminal_side is RmsTerminalSide.FROM:
            references = list((VarPowerFlowReferenceType.Vaf,))
        else:
            if terminal_side is RmsTerminalSide.TO:
                references = list((VarPowerFlowReferenceType.Vat,))
            else:
                references = list((VarPowerFlowReferenceType.Va,))
    else:
        pass
    return references


def _clone_import_block(block: Block) -> Block:
    """
    Clone one imported symbolic block for one selected target template.

    :param block: Imported symbolic block.
    :return: Deep-copied block.
    """
    cloned_block: Block = copy.deepcopy(block)
    _apply_composite_child_interface_if_missing(cloned_block)
    return cloned_block


def _build_selected_template_from_import_entry(
        entry: DynamicModelImportEntry,
        selection_request: DynamicModelImportSelectionRequest,
        clone_source_block: bool = True,
) -> RmsModelTemplate | EmtModelTemplate | None:
    """
    Materialize one selected reusable template using the user import choices.

    :param entry: Imported entry.
    :param selection_request: Explicit user import request.
    :param clone_source_block: Clone the source block for reusable GUI bundles.
    :return: Materialized RMS or EMT reusable template, or ``None``.
    """
    source_block: Block | None = entry.get_source_block()
    cloned_block: Block
    template_name: str = entry.get_display_name()
    template_comment: str = f"{entry.get_source_tpe().value} dynamic model: {template_name}"
    emt_template: EmtModelTemplate
    rms_template: RmsModelTemplate

    if source_block is None:
        return None
    else:
        pass

    if clone_source_block:
        cloned_block = _clone_import_block(source_block)
    else:
        # A normal massive DGS open owns an ephemeral bundle. Transfer its
        # symbolic block into the circuit wrapper instead of retaining a second
        # deep copy of every OEM model at peak memory.
        cloned_block = source_block
        _apply_composite_child_interface_if_missing(cloned_block)
    if selection_request.get_target_domain() == DynamicSimulationMode.EMT:
        emt_template = EmtModelTemplate(name=template_name)
        emt_template.tpe = selection_request.get_device_tpe()
        emt_template.block = cloned_block
        emt_template.name = template_name
        emt_template.comment = template_comment
        return emt_template
    else:
        if selection_request.get_target_domain() == DynamicSimulationMode.RMS:
            rms_template = RmsModelTemplate(name=template_name)
            rms_template.tpe = selection_request.get_device_tpe()
            rms_template.block = cloned_block
            rms_template.name = template_name
            rms_template.comment = template_comment
            # Detached catalogue blocks have no exact equipment FID or static
            # host. Physical assembly is performed only by the direct importer.
            return rms_template
        else:
            return None


def build_dynamic_import_template_fingerprint(
        template_obj: RmsModelTemplate | EmtModelTemplate,
) -> str | None:
    """
    Build a deterministic structural fingerprint for one reusable template.

    :param template_obj: Materialized reusable template.
    :return: SHA-256 fingerprint, or ``None`` when canonicalization fails.
    """
    fingerprint_block: Block = copy.copy(template_obj.block)
    fingerprint_block.name = "__veragrid_dynamic_template_root__"
    if isinstance(template_obj, RmsModelTemplate):
        target_domain: DynamicSimulationMode = DynamicSimulationMode.RMS
    else:
        target_domain = DynamicSimulationMode.EMT

    try:
        payload_text: str = _build_user_dynamic_template_payload_text(
            block=fingerprint_block,
            template_name="__veragrid_dynamic_template__",
            target_domain=target_domain,
            device_tpe=template_obj.tpe,
        )
    except (KeyError, TypeError, ValueError):
        return None
    else:
        return hashlib.sha256(payload_text.encode("utf-8")).hexdigest()


def _build_source_qualified_dynamic_import_template_name(
        entry: DynamicModelImportEntry,
        existing_names: Set[str],
) -> str:
    """
    Build a readable unique name for a non-equivalent name collision.

    :param entry: Imported entry whose display name already exists.
    :param existing_names: Names already present in the target domain.
    :return: Unique human-readable template name.
    """
    base_name: str = entry.get_display_name()
    key_parts: List[str] = entry.get_unique_key().split("|")
    source_provenance: DynamicModelImportSourceProvenance | None = (
        entry.get_source_provenance()
    )
    source_label: str = "imported variant"
    candidate_name: str
    suffix_index: int = 2

    if source_provenance is None:
        if len(key_parts) >= 3 and key_parts[0] == "dgs-slot":
            source_label = "child slot"
        else:
            if len(key_parts) >= 2 and key_parts[0].startswith("dgs-"):
                source_label = "DGS variant"
            else:
                pass
    else:
        # Stable FIDs belong in metadata; collision names remain readable by
        # presenting the exported root/slot labels to humans.
        if source_provenance.get_root_name().casefold() == base_name.casefold():
            if source_provenance.get_slot_name() is None:
                source_label = "root variant"
            else:
                source_label = source_provenance.get_slot_name()
        else:
            source_label = source_provenance.get_root_name()

    candidate_name = f"{base_name} [{source_label}]"
    while candidate_name in existing_names:
        candidate_name = f"{base_name} [{source_label} {suffix_index}]"
        suffix_index += 1

    return candidate_name


def _append_dynamic_model_import_entry_result(
        report: DynamicModelImportReport | None,
        entry: DynamicModelImportEntry,
        selection_request: DynamicModelImportSelectionRequest,
        final_name: str | None,
        status: DynamicModelImportEntryStatus,
        message: str,
) -> DynamicModelImportEntryResult | None:
    """
    Append one structured result when the caller requested reporting.

    :param report: Optional aggregate report.
    :param entry: Processed source catalogue entry.
    :param selection_request: Explicit target-domain selection.
    :param final_name: Final circuit template name, when available.
    :param status: Explicit processing status.
    :param message: Human-readable outcome diagnostic.
    :return: Appended result or ``None`` when reporting is disabled.
    """
    if report is None:
        entry_result: DynamicModelImportEntryResult | None = None
    else:
        entry_result = DynamicModelImportEntryResult(
            unique_key=entry.get_unique_key(),
            requested_name=entry.get_display_name(),
            final_name=final_name,
            domain=selection_request.get_target_domain(),
            status=status,
            source_provenance=entry.get_source_provenance(),
            message=message,
        )
        report.add_entry_result(entry_result=entry_result)

    return entry_result


def add_dynamic_import_selection_requests_to_circuit(
        circuit: MultiCircuit,
        bundle: DynamicModelImportBundle,
        selection_requests: Sequence[DynamicModelImportSelectionRequest],
        logger: Logger,
        progress_callback: Callable[[int, str], None] | None = None,
        user_root_folder: str | None = None,
        rename_conflicting_templates: bool = False,
        persist_to_user_catalog: bool = False,
        report: DynamicModelImportReport | None = None,
        template_fingerprint_by_object_id: Dict[int, str | None] | None = None,
        clone_source_blocks: bool = True,
) -> int:
    """
    Add the selected imported dynamic models to the circuit using explicit metadata.

    :param circuit: Target circuit.
    :param bundle: Imported dynamic-model bundle.
    :param selection_requests: Explicit selected import requests.
    :param logger: Logger receiving duplicate or importability diagnostics.
    :param progress_callback: Optional UI progress callback.
    :param user_root_folder: Optional explicit VeraGrid user root used mainly by tests.
    :param rename_conflicting_templates: Rename non-equivalent name collisions instead of dropping them.
    :param persist_to_user_catalog: Legacy request retained for API compatibility;
        executable catalogue persistence is refused.
    :param report: Optional structured outcome report populated entry by entry.
    :param template_fingerprint_by_object_id: Optional identity cache shared
        with deferred DGS persistence.
    :param clone_source_blocks: Clone bundle blocks before installation. Disable
        only when the caller owns and consumes one ephemeral massive bundle.
    :return: Number of templates added to the circuit.
    """
    request_by_entry_key: Dict[str, DynamicModelImportSelectionRequest] = dict()
    existing_rms_names: Set[str] = set()
    existing_emt_names: Set[str] = set()
    existing_rms_templates_by_fingerprint: Dict[str, RmsModelTemplate] = dict()
    existing_emt_templates_by_fingerprint: Dict[str, EmtModelTemplate] = dict()
    processed_entry_keys: Set[str] = set()
    entry: DynamicModelImportEntry
    selection_request: DynamicModelImportSelectionRequest
    template_obj: RmsModelTemplate | EmtModelTemplate | None
    total_selected_count: int
    processed_selected_count: int = 0
    template_deduplicated: bool
    template_renamed: bool
    outcome_message: str
    fingerprint_cache: Dict[int, str | None]

    if persist_to_user_catalog:
        logger.add_warning(
            msg="Executable dynamic-model catalogue persistence refused",
            value=(
                user_root_folder
                if user_root_folder is not None
                else "The declarative template remains registered in MultiCircuit"
            ),
        )
    else:
        pass

    if template_fingerprint_by_object_id is None:
        fingerprint_cache = dict()
    else:
        fingerprint_cache = template_fingerprint_by_object_id

    for selection_request in selection_requests:
        entry_key: str = selection_request.get_entry_key()
        if entry_key in request_by_entry_key:
            logger.add_info(
                msg="Duplicate dynamic model selection ignored",
                value=entry_key,
            )
        else:
            request_by_entry_key[entry_key] = selection_request

    total_selected_count = len(request_by_entry_key)

    for template in circuit.rms_models:
        existing_rms_names.add(template.name)
        template_fingerprint: str | None = build_dynamic_import_template_fingerprint(template)
        fingerprint_cache[id(template)] = template_fingerprint
        if template_fingerprint is not None:
            existing_rms_templates_by_fingerprint[template_fingerprint] = template
        else:
            pass

    for template in circuit.emt_models:
        existing_emt_names.add(template.name)
        template_fingerprint = build_dynamic_import_template_fingerprint(template)
        fingerprint_cache[id(template)] = template_fingerprint
        if template_fingerprint is not None:
            existing_emt_templates_by_fingerprint[template_fingerprint] = template
        else:
            pass

    added_count: int = 0

    for entry in bundle.get_entries():
        entry.set_installed_template(None)
        selection_request = request_by_entry_key.get(entry.get_unique_key(), None)

        if selection_request is None or entry.get_unique_key() in processed_entry_keys:
            if selection_request is None:
                pass
            else:
                logger.add_info(
                    msg="Duplicate dynamic model catalogue entry ignored",
                    value=entry.get_unique_key(),
                )
                _append_dynamic_model_import_entry_result(
                    report=report,
                    entry=entry,
                    selection_request=selection_request,
                    final_name=None,
                    status=DynamicModelImportEntryStatus.Skipped,
                    message="Duplicate catalogue entry key ignored",
                )
        else:
            processed_entry_keys.add(entry.get_unique_key())

            processed_selected_count += 1
            if total_selected_count == 0:
                pass
            else:
                _emit_dynamic_model_import_progress(
                    progress_callback,
                    int(round(60.0 * float(processed_selected_count - 1) / float(total_selected_count))),
                    f"Adding selected dynamic models: {processed_selected_count}/{total_selected_count}",
                )

            outcome_message = ""
            try:
                template_obj = _build_selected_template_from_import_entry(
                    entry=entry,
                    selection_request=selection_request,
                    clone_source_block=clone_source_blocks,
                )
            except Exception as exc:
                template_obj = None
                outcome_message = str(exc)
                logger.add_warning(
                    msg="Dynamic model entry skipped after a materialization error",
                    value=f"{entry.get_display_name()}: {exc}",
                )

            if template_obj is None:
                logger.add_warning(msg="Dynamic model entry skipped because it is not importable",
                                   value=entry.get_display_name())
                if len(outcome_message) == 0:
                    outcome_message = "Source entry is not importable"
                else:
                    pass
                _append_dynamic_model_import_entry_result(
                    report=report,
                    entry=entry,
                    selection_request=selection_request,
                    final_name=None,
                    status=DynamicModelImportEntryStatus.Failed,
                    message=outcome_message,
                )
            else:
                template_added: bool = False
                template_deduplicated = False
                template_renamed = False
                outcome_message = "Template name already exists"
                template_fingerprint: str | None = build_dynamic_import_template_fingerprint(template_obj)
                fingerprint_cache[id(template_obj)] = template_fingerprint
                if isinstance(template_obj, RmsModelTemplate):
                    equivalent_rms_template: RmsModelTemplate | None = None
                    if template_fingerprint is None:
                        pass
                    else:
                        equivalent_rms_template = existing_rms_templates_by_fingerprint.get(
                            template_fingerprint,
                            None,
                        )

                    if rename_conflicting_templates and equivalent_rms_template is not None:
                        logger.add_info(
                            msg="Equivalent dynamic model entry deduplicated",
                            value=f"{template_obj.name} -> {equivalent_rms_template.name}",
                        )
                        entry.set_installed_template(equivalent_rms_template)
                        template_deduplicated = True
                        outcome_message = "Equivalent template reused by structural fingerprint"
                    else:
                        if template_obj.name in existing_rms_names:
                            if rename_conflicting_templates:
                                original_name: str = template_obj.name
                                template_obj.name = _build_source_qualified_dynamic_import_template_name(
                                    entry=entry,
                                    existing_names=existing_rms_names,
                                )
                                template_obj.block.name = template_obj.name
                                logger.add_info(
                                    msg="Dynamic model name collision renamed",
                                    value=f"{original_name} -> {template_obj.name}",
                                )
                                circuit.add_rms_model(template_obj)
                                existing_rms_names.add(template_obj.name)
                                template_added = True
                                template_renamed = True
                                outcome_message = f"Name collision renamed to {template_obj.name}"
                            else:
                                logger.add_warning(
                                    msg="Dynamic model entry skipped because the template name already exists",
                                    value=template_obj.name)
                        else:
                            circuit.add_rms_model(template_obj)
                            existing_rms_names.add(template_obj.name)
                            template_added = True
                            outcome_message = "Template added"

                    if template_added and template_fingerprint is not None:
                        existing_rms_templates_by_fingerprint[template_fingerprint] = template_obj
                    else:
                        pass
                else:
                    if isinstance(template_obj, EmtModelTemplate):
                        equivalent_emt_template: EmtModelTemplate | None = None
                        if template_fingerprint is None:
                            pass
                        else:
                            equivalent_emt_template = existing_emt_templates_by_fingerprint.get(
                                template_fingerprint,
                                None,
                            )

                        if rename_conflicting_templates and equivalent_emt_template is not None:
                            logger.add_info(
                                msg="Equivalent dynamic model entry deduplicated",
                                value=f"{template_obj.name} -> {equivalent_emt_template.name}",
                            )
                            entry.set_installed_template(equivalent_emt_template)
                            template_deduplicated = True
                            outcome_message = "Equivalent template reused by structural fingerprint"
                        else:
                            if template_obj.name in existing_emt_names:
                                if rename_conflicting_templates:
                                    original_name = template_obj.name
                                    template_obj.name = _build_source_qualified_dynamic_import_template_name(
                                        entry=entry,
                                        existing_names=existing_emt_names,
                                    )
                                    template_obj.block.name = template_obj.name
                                    logger.add_info(
                                        msg="Dynamic model name collision renamed",
                                        value=f"{original_name} -> {template_obj.name}",
                                    )
                                    circuit.add_emt_model(template_obj)
                                    existing_emt_names.add(template_obj.name)
                                    template_added = True
                                    template_renamed = True
                                    outcome_message = f"Name collision renamed to {template_obj.name}"
                                else:
                                    logger.add_warning(
                                        msg="Dynamic model entry skipped because the template name already exists",
                                        value=template_obj.name)
                            else:
                                circuit.add_emt_model(template_obj)
                                existing_emt_names.add(template_obj.name)
                                template_added = True
                                outcome_message = "Template added"

                        if template_added and template_fingerprint is not None:
                            existing_emt_templates_by_fingerprint[template_fingerprint] = template_obj
                        else:
                            pass
                    else:
                        outcome_message = "Materialized object has an unsupported template type"

                if template_added:
                    entry.set_installed_template(template_obj)
                    added_count += 1
                    if template_renamed:
                        entry_status: DynamicModelImportEntryStatus = DynamicModelImportEntryStatus.Renamed
                    else:
                        entry_status = DynamicModelImportEntryStatus.Added
                    _append_dynamic_model_import_entry_result(
                        report=report,
                        entry=entry,
                        selection_request=selection_request,
                        final_name=template_obj.name,
                        status=entry_status,
                        message=outcome_message,
                    )
                else:
                    if template_deduplicated:
                        deduplicated_template: RmsModelTemplate | EmtModelTemplate | None = (
                            entry.get_installed_template()
                        )
                        if deduplicated_template is None:
                            final_name: str | None = template_obj.name
                        else:
                            final_name = deduplicated_template.name
                        _append_dynamic_model_import_entry_result(
                            report=report,
                            entry=entry,
                            selection_request=selection_request,
                            final_name=final_name,
                            status=DynamicModelImportEntryStatus.Deduplicated,
                            message=outcome_message,
                        )
                    else:
                        _append_dynamic_model_import_entry_result(
                            report=report,
                            entry=entry,
                            selection_request=selection_request,
                            final_name=None,
                            status=DynamicModelImportEntryStatus.Skipped,
                            message=outcome_message,
                        )

            if total_selected_count == 0:
                pass
            else:
                _emit_dynamic_model_import_progress(
                    progress_callback,
                    int(round(60.0 * float(processed_selected_count) / float(total_selected_count))),
                    f"Adding selected dynamic models: {processed_selected_count}/{total_selected_count}",
                )

    _emit_dynamic_model_import_progress(progress_callback, 100, "Selected dynamic models imported")

    return added_count


def _find_exact_dgs_dynamic_host_devices(
        circuit: MultiCircuit,
        source_element_dgs_id: str,
        device_tpe: DeviceType,
        source_element_class: str | None,
) -> List[DynamicDevice]:
    """
    Find dynamic-capable devices by exact imported DGS FID and device type.

    Parallel-device suffixes are not expanded here. One PowerFactory composite
    does not define whether its states should be duplicated across VeraGrid
    parallel expansions, so such cases must remain unresolved and inspectable.

    :param circuit: Imported VeraGrid circuit.
    :param source_element_dgs_id: Authoritative source equipment FID.
    :param device_tpe: Expected VeraGrid host type.
    :param source_element_class: Authoritative PowerFactory equipment class.
    :return: Exact compatible dynamic devices.
    """
    matches: List[DynamicDevice] = list()
    candidate_obj: object
    candidate_device_types: List[DeviceType] = list([device_tpe])

    # Batteries inherit the Generator RMS contract but live in a separate
    # circuit collection. PowerFactory exports both wind/HVDC sources and
    # storage through ElmGenstat, so exact FID resolution must inspect both
    # compatible VeraGrid collections without relying on display categories.
    if (
            source_element_class == "ElmGenstat"
            and DeviceType.BatteryDevice not in candidate_device_types
    ):
        candidate_device_types.append(DeviceType.BatteryDevice)
    else:
        pass

    if source_element_class == "ElmGenstat" and DeviceType.StaticGeneratorDevice not in candidate_device_types:
        candidate_device_types.append(DeviceType.StaticGeneratorDevice)
    else:
        pass

    candidate_device_type: DeviceType
    for candidate_device_type in candidate_device_types:
        for candidate_obj in circuit.get_elements_by_type(
                device_type=candidate_device_type,
        ):
            if isinstance(candidate_obj, DynamicDevice):
                if candidate_obj.idtag == source_element_dgs_id:
                    matches.append(candidate_obj)
                else:
                    pass
            else:
                pass
        else:
            pass
    else:
        pass

    return matches


def convert_and_add_dgs_dynamic_templates_to_circuit(
        dgs_circuit: DgsCircuit, circuit: MultiCircuit,
        target_domain: DynamicSimulationMode | None, logger: Logger,
) -> DgsDynamicTemplateConversionResult:
    """Convert through the shared importer while preserving the public function API.

    :param dgs_circuit: Parsed source graph.
    :param circuit: Destination circuit.
    :param target_domain: Explicit RMS or EMT destination.
    :param logger: Diagnostic sink.
    :return: Canonical template and child associations.
    """
    importer: DynamicModelImport = DynamicModelImport(dgs_circuit, circuit, target_domain, logger)
    return importer.convert_and_add_templates()


def apply_dgs_dynamic_templates_to_devices(
        dgs_circuit: DgsCircuit, circuit: MultiCircuit,
        templates_by_root_dgs_id: Dict[str, RmsModelTemplate | EmtModelTemplate], logger: Logger,
) -> None:
    """Assign through the shared importer while preserving existing API consumers.

    :param dgs_circuit: Parsed source graph.
    :param circuit: Destination circuit.
    :param templates_by_root_dgs_id: Previously registered canonical templates.
    :param logger: Diagnostic sink.
    :return: None.
    """
    importer: DynamicModelImport = DynamicModelImport(dgs_circuit, circuit, None, logger)
    importer.get_conversion_result().templates_by_root_dgs_id.update(templates_by_root_dgs_id)
    importer.apply_templates_to_devices()


def _build_user_dynamic_template_payload_text(
        block: Block,
        template_name: str,
        target_domain: DynamicSimulationMode,
        device_tpe: DeviceType,
        template_fingerprint: str | None = None,
) -> str:
    """
    Build the complete JSON validation snapshot before filesystem mutation.

    :param block: Persistable symbolic block.
    :param template_name: Final catalogue template name.
    :param target_domain: Selected RMS or EMT domain.
    :param device_tpe: Selected supported device type.
    :param template_fingerprint: Optional precomputed structural identity.
    :return: Deterministic JSON sidecar text.
    """
    payload: Dict[str, object] = dict()

    payload["template_name"] = template_name
    payload["target_domain"] = target_domain.value
    payload["device_tpe"] = device_tpe.name
    if template_fingerprint is None:
        pass
    else:
        payload["template_fingerprint"] = template_fingerprint
    payload["block_data"] = block.to_dict()
    return json.dumps(
        payload,
        indent=2,
        ensure_ascii=True,
        sort_keys=True,
    ) + "\n"
