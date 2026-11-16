# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Iterator, List, Type, Optional, Tuple, Any, Set, Iterable

from VeraGridEngine.Utils.Symbolic.symbolic_io import duplicate_block
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Branches.dc_line import DcLine
from VeraGridEngine.Devices.Branches.line import Line

from VeraGridEngine.Devices.Branches.series_reactance import SeriesReactance

from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var, heaviside
from VeraGridEngine.Utils.procedural_logic import sampled_value, DelayedSwitchEventLogic
from VeraGridEngine.enumerations import (
    VarPowerFlowReferenceType,
    DgsImportField,
)
from VeraGridEngine.Templates.Rms.buses.bus_rms_template import (
    initialize_bus_rms,
    promote_dc_bus_voltage_to_capacitive_state,
)
from VeraGridEngine.Devices.Injections.generator import Generator

from VeraGridEngine.IO.dgs.dgs_logical_actuator_binding import (_find_common_passive_bus,
                                                                _collect_unique_named_vars,
                                                                _resolve_terminal_id,
                                                                _DgsLogicalActuatorBranchBindingPlan,
                                                                _build_logical_actuator_branch_plan,
                                                                _can_seed_open_resistive_actuator,
                                                                _seed_open_resistive_actuator)
from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice
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
    BlkSwt,
    ChaRef,
    ChaVec,
    ComLdf,
    DgsProperty,
    DGSElement,
    ElmArea,
    ElmAsm,
    ElmBranch,
    ElmComp,
    ElmCoup,
    ElmDsl,
    ElmFeeder,
    ElmGenstat,
    # Alex review required: VSC equipment rows converted into the final MultiCircuit.
    ElmVsc,
    ElmVscmono,
    ElmLne,
    ElmLnesec,
    ElmLod,
    ElmLodlv,
    ElmLodlvp,
    ElmNet,
    ElmPhi,
    ElmScap,
    ElmShnt,
    ElmSind,
    ElmSite,
    ElmSubstat,
    ElmSvs,
    ElmSym,
    ElmTerm,
    ElmTow,
    ElmTr2,
    ElmTr3,
    ElmTr4,
    ElmVac,
    ElmXnet,
    ElmZone,
    ElmZpu,
    General,
    IntFolder,
    IntGrf,
    IntGrfcon,
    IntGrfgroup,
    IntGrfnet,
    IntRef,
    IntTemplate,
    Matrix,
    RelFuse,
    StaCt,
    StaCubic,
    StaSwitch,
    StaImea,
    StaPqmea,
    StaVmea,
    StaVt,
    TypAsmo,
    TypCab,
    TypCabsys,
    TypCon,
    TypCt,
    TypFuse,
    TypGeo,
    TypLne,
    TypLod,
    TypSind,
    TypSwitch,
    TypSym,
    TypTow,
    TypTr2,
    TypTr3,
    TypTr4,
    TypVt,
    _split_dgs_line,
)
from VeraGridEngine.IO.dgs.dynamic_models.dynamic_model_import import (
    DynamicModelImport, DgsDynamicTemplateConversionResult,
)

from VeraGridEngine.IO.dgs.dgs_rms_preparation import (_get_monopolar_vsc_dc_capacitance_pu_seconds,
                                                       _select_ideal_ac_connector_constraint_ids,
                                                       _build_dgs_default_rms_template,
                                                       resolve_dgs_elmgenstat_source,
                                                       build_dgs_elmgenstat_fallback,
                                                       _bind_dgs_elmsym_reference_frequencies,
                                                       _find_unique_rms_conduction_parameter)

from VeraGridEngine.Utils.Symbolic.block import (
    Block,
)
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    DgsDirectRootBuildResult,
    DgsGraphicalIndexes,
    DgsRootBlockResult,
    DgsStandaloneBlockOccurrence,
    ElmCompInstanceEntry,
    ParsedDgsBlockDefinition,
    UnsupportedDgsExpression,
    build_dgs_graphical_indexes,
    build_direct_root_elmcomp_block,
    build_standalone_blkdef_block_from_parsed_block,
    build_dgs_root_block_from_circuit,
    extract_elmcomp_direct_instances,
    get_unique_elmcomp_slot_entries,
)
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate

from VeraGridEngine.enumerations import (
    DynamicSimulationMode,
)

from VeraGridEngine.IO.dgs.dgs_import_metadata import (
    get_import_field,
    set_import_field,
    assign_import_template,
)


def _ref_id(x: str | None) -> str | None:
    """
    Ref id.

    :param x: x parameter.
    :return: Function result.
    """
    if x is None:
        return None
    s = str(x)
    if "\\" in s:
        return s.split("\\")[-1]
    else:
        return s


def _entry_slot_sort_key(entry: ElmCompInstanceEntry) -> int:
    """Return the exported frame order of one direct DGS entry.

    :param entry: Transient direct root-slot entry.
    :return: Source slot index, with absent indices sorted last.
    """
    slot_index: int | None = entry.slot_index
    if slot_index is None:
        return 2_147_483_647
    else:
        return slot_index


class DynDgsParser:
    """
    DynDgsParser
    """

    __slots__ = ("dgs_grid",
                 "grid",
                 "dynamic_simulation_mode",
                 "logger",
                 "dynamic_model_import",
                 "external_grid_source_ids",
                 "elm_gen_stat_source_ids",
                 "elm_sym_source_ids",
                 "elm_sym_reference_source_ids",
                 "effective_elm_sym_reference_source_ids",
                 "typeless_elm_lod_source_ids", "actuator_topology")

    def __init__(self,
                 dgs_grid: DgsCircuit,
                 grid: MultiCircuit,
                 dynamic_simulation_mode: DynamicSimulationMode,
                 logger: Logger) -> None:

        """Share one import context with the dynamic-template importer.

        :param dgs_grid: Parsed source object graph.
        :param grid: Destination circuit shared with static import.
        :param dynamic_simulation_mode: Explicit RMS or EMT target.
        :param logger: Shared import diagnostic sink.
        :return: None.
        """
        super().__init__()

        self.dgs_grid: DgsCircuit = dgs_grid
        self.grid: MultiCircuit = grid
        self.dynamic_simulation_mode: DynamicSimulationMode = dynamic_simulation_mode
        self.logger: Logger = logger

        self.dynamic_model_import: DynamicModelImport = DynamicModelImport(
            dgs_circuit=dgs_grid, circuit=grid, target_domain=dynamic_simulation_mode, logger=logger,
        )
        self.external_grid_source_ids: Set[str] = set()
        self.elm_gen_stat_source_ids: Set[str] = set()
        self.elm_sym_source_ids: Set[str] = set()
        self.elm_sym_reference_source_ids: Set[str] = set()
        self.effective_elm_sym_reference_source_ids: Set[str] = set()
        self.typeless_elm_lod_source_ids: Set[str] = set()
        self.actuator_topology: Dict[DynamicDevice, Tuple[str, float | None]] = dict()

    @property
    def conversion_result(self) -> DgsDynamicTemplateConversionResult:
        """Expose importer-owned associations to physical preparation stages.

        :return: Canonical conversion result without a second mutable owner.
        """
        return self.dynamic_model_import.get_conversion_result()

    def bind_dgs_switch_event_runtime(self) -> int:
        """Connect imported guarded switch modes to physical RMS conduction states.

        Multiple physical switches can sit in series on one equipment object. Their
        exported binary positions are multiplied so opening either terminal removes
        that equipment from the fixed-size RMS equations.

        :return: Number of installed physical models connected to switch-event modes.
        """
        device_by_idtag: Dict[str, DynamicDevice] = dict()
        physical_device: DynamicDevice
        for physical_device in self.grid.get_branches_iter(
                add_vsc=False,
                add_hvdc=False,
                add_switch=True,
        ):
            device_by_idtag[physical_device.idtag] = physical_device

        modes_by_device_idtag: Dict[str, List[Var]] = dict()
        root_template: RmsModelTemplate | EmtModelTemplate
        root_block: Block
        logic_entry: object
        mode_block: Block
        mode_parameter: Var
        root_id: str
        for root_id, root_template in self.conversion_result.templates_by_root_dgs_id.items():
            if isinstance(root_template, RmsModelTemplate):
                pass
            else:
                raise ValueError(
                    "DGS RMS switch-event binding received a non-RMS template"
                )
            installed_model: Block | None = self.conversion_result.models_by_root_dgs_id.get(root_id, None)
            if installed_model is None:
                installed_model = root_template.block
            else:
                pass
            for root_block in installed_model.get_all_blocks():
                for logic_entry in root_block.procedural_logic:
                    if isinstance(logic_entry, DelayedSwitchEventLogic):
                        if logic_entry.command_closed:
                            self.logger.add_warning(
                                msg="DGS close-switch event binding is not supported",
                                device=logic_entry.name,
                                value=logic_entry.target_switch_idtag,
                            )
                        else:
                            matching_modes: List[Var] = list()
                            matching_mode_uids: Set[int] = set()
                            for mode_block in installed_model.get_all_blocks():
                                for mode_parameter in mode_block.mode_dict.keys():
                                    if mode_parameter.name == logic_entry.output_var_name:
                                        if mode_parameter.uid not in matching_mode_uids:
                                            matching_modes.append(mode_parameter)
                                            matching_mode_uids.add(mode_parameter.uid)
                                        else:
                                            pass
                                    else:
                                        pass
                            if len(matching_modes) == 1:
                                device_modes: List[Var] | None = modes_by_device_idtag.get(
                                    logic_entry.target_device_idtag,
                                    None,
                                )
                                if device_modes is None:
                                    device_modes = list()
                                    device_modes.append(matching_modes[0])
                                    modes_by_device_idtag[
                                        logic_entry.target_device_idtag
                                    ] = device_modes
                                else:
                                    mode_is_new: bool = True
                                    existing_device_mode: Var
                                    for existing_device_mode in device_modes:
                                        if existing_device_mode.uid == matching_modes[0].uid:
                                            mode_is_new = False
                                        else:
                                            pass
                                    if mode_is_new:
                                        device_modes.append(matching_modes[0])
                                    else:
                                        pass
                            else:
                                self.logger.add_warning(
                                    msg="DGS switch event mode is missing or ambiguous",
                                    device=logic_entry.name,
                                    value=(
                                        f"{logic_entry.output_var_name}; "
                                        f"matches={len(matching_modes)}"
                                    ),
                                )
                    else:
                        pass

        bound_count: int = 0
        device_idtag: str
        switch_modes: List[Var]
        for device_idtag, switch_modes in modes_by_device_idtag.items():
            physical_device = device_by_idtag.get(device_idtag, None)
            if physical_device is None or physical_device.rms_model.empty():
                self.logger.add_warning(
                    msg="DGS switch event physical target is unavailable",
                    device=device_idtag,
                )
            else:
                conduction_owner: Block | None
                conduction_parameter: Var | None
                conduction_owner, conduction_parameter = (
                    _find_unique_rms_conduction_parameter(
                        block=physical_device.rms_model,
                    )
                )
                if conduction_owner is None or conduction_parameter is None:
                    self.logger.add_warning(
                        msg="DGS switch event target has no unique RMS conduction state",
                        device=device_idtag,
                    )
                else:
                    conduction_expression: Expr | Const = conduction_owner.event_dict[
                        conduction_parameter
                    ]
                    switch_mode: Var
                    for switch_mode in switch_modes:
                        conduction_expression = conduction_expression * switch_mode
                    conduction_owner.event_dict[conduction_parameter] = (
                        conduction_expression
                    )
                    bound_count += 1
        return bound_count

    def bind_dgs_logical_actuator_runtime(self) -> int:
        """Bind each complete logical actuator group as one atomic operation.
        :return: Number of passive actuator RMS models bound.
        """
        branches_by_root_id: Dict[str, List[Line | SeriesReactance]] = dict()
        open_resistance_by_root_id: Dict[str, float] = dict()
        conflicting_root_ids: set[str] = set()
        candidate_branch: object
        for candidate_branch in self.actuator_topology:
            if isinstance(candidate_branch, (Line, SeriesReactance)):
                root_id: str | None = (
                    get_import_field(
                        candidate_branch.rms_model,
                        DgsImportField.DGS_LOGICAL_ACTUATOR_ROOT_ID,
                        self.dynamic_model_import.get_import_metadata(),
                    )
                )
                resistance_ohm: float | None = (
                    get_import_field(
                        candidate_branch.rms_model,
                        DgsImportField.DGS_OPEN_RESISTANCE_OHM,
                        self.dynamic_model_import.get_import_metadata(),
                    )
                )
                if root_id is None:
                    pass
                else:
                    root_branches: List[Line | SeriesReactance] | None = (
                        branches_by_root_id.get(root_id, None)
                    )
                    if root_branches is None:
                        root_branches = list()
                        branches_by_root_id[root_id] = root_branches
                    else:
                        pass
                    root_branches.append(candidate_branch)

                    if (
                            resistance_ohm is not None
                            and math.isfinite(resistance_ohm)
                            and resistance_ohm > 0.0
                    ):
                        existing_resistance: float | None = (
                            open_resistance_by_root_id.get(root_id, None)
                        )
                        if existing_resistance is None:
                            open_resistance_by_root_id[root_id] = resistance_ohm
                        else:
                            if math.isclose(
                                    existing_resistance,
                                    resistance_ohm,
                                    rel_tol=1.0e-12,
                                    abs_tol=1.0e-12,
                            ):
                                pass
                            else:
                                conflicting_root_ids.add(root_id)
                    else:
                        pass
            else:
                pass

        bound_count: int = 0
        root_id: str
        for root_id in sorted(branches_by_root_id.keys()):
            root_template: RmsModelTemplate | None = self.conversion_result.templates_by_root_dgs_id.get(
                root_id,
                None,
            )
            template_gate_vars: List[Var] = list()
            template_resistance_vars: List[Var] = list()
            if isinstance(root_template, RmsModelTemplate):
                template_gate_vars = _collect_unique_named_vars(
                    block=root_template.block,
                    variable_name="gate",
                )
                template_resistance_vars = _collect_unique_named_vars(
                    block=root_template.block,
                    variable_name="R",
                )
            else:
                pass

            branch_plans: List[_DgsLogicalActuatorBranchBindingPlan] = list()
            plan_is_complete: bool = True
            branch: Line | SeriesReactance
            for branch in branches_by_root_id[root_id]:
                branch_plan: _DgsLogicalActuatorBranchBindingPlan | None = (
                    _build_logical_actuator_branch_plan(
                        line=branch,
                        circuit=self.grid,
                        import_metadata=self.dynamic_model_import.get_import_metadata(),
                    )
                )
                if branch_plan is None:
                    plan_is_complete = False
                else:
                    branch_plans.append(branch_plan)

            if (
                    root_id in conflicting_root_ids
                    or not isinstance(root_template, RmsModelTemplate)
                    or root_template.block.empty()
                    or len(template_gate_vars) != 1
                    or len(template_resistance_vars) != 1
                    or not plan_is_complete
                    or len(branch_plans) == 0
            ):
                self.logger.add_warning(
                    msg="DGS logical actuator group is incomplete or contradictory",
                    device=root_id,
                    value=len(branch_plans),
                    expected_value=len(branches_by_root_id[root_id]),
                )
            else:
                controller_block: Block = duplicate_block(root_template.block, self.grid.var_factory)
                seed_applied: bool = _seed_open_resistive_actuator(
                    block=controller_block,
                    open_resistance_ohm=open_resistance_by_root_id.get(root_id, None),
                )
                controller_gate_vars: List[Var] = _collect_unique_named_vars(
                    block=controller_block,
                    variable_name="gate",
                )
                controller_resistance_vars: List[Var] = _collect_unique_named_vars(
                    block=controller_block,
                    variable_name="R",
                )
                if (
                        seed_applied
                        and len(controller_gate_vars) == 1
                        and len(controller_resistance_vars) == 1
                ):
                    # The first branch owns the sole controller instance. Every
                    # other pole references its variables in the final RMS graph.
                    branch_plans[0].line.rms_model.add(controller_block)
                    self.conversion_result.models_by_root_dgs_id[root_id] = controller_block
                    gate_expression: Expr = heaviside(controller_gate_vars[0])
                    branch_plan: _DgsLogicalActuatorBranchBindingPlan
                    for branch_plan in branch_plans:
                        branch_plan.status_owner.event_dict[
                            branch_plan.status_var
                        ] = gate_expression
                        branch_plan.status_owner.procedural_logic.append(
                            sampled_value(
                                output=branch_plan.status_var,
                                source=gate_expression,
                                name=(
                                    f"project_{branch_plan.status_var.name}"
                                    "_from_gate"
                                ),
                            )
                        )

                        branch_plan.resistance_owner.parameters.pop(
                            branch_plan.resistance_parameter,
                            None,
                        )
                        resistance_expression: Expr = (
                                controller_resistance_vars[0]
                                / Const(branch_plan.impedance_base_ohm)
                        )
                        branch_plan.resistance_owner.event_dict[
                            branch_plan.resistance_parameter
                        ] = resistance_expression
                        branch_plan.resistance_owner.procedural_logic.append(
                            sampled_value(
                                output=branch_plan.resistance_parameter,
                                source=resistance_expression,
                                name=(
                                    f"project_{branch_plan.resistance_parameter.name}"
                                    "_from_resistance"
                                ),
                            )
                        )

                        if (
                                branch_plan.inductance_parameter is not None
                                and branch_plan.inductance_owner is not None
                                and branch_plan.inductance_pu_seconds is not None
                        ):
                            branch_plan.inductance_owner.parameters[
                                branch_plan.inductance_parameter
                            ] = Const(branch_plan.inductance_pu_seconds)
                        else:
                            pass
                        # A successfully bound branch remains outside the static
                        # admittance matrix because its RMS model represents the
                        # complete valve-plus-impedance assembly.
                        branch_plan.line.active = False
                        branch_plan.line.active_prof.fill(False)
                        bound_count += 1
                else:
                    self.logger.add_warning(
                        msg="DGS logical actuator controller initialization is incomplete",
                        device=root_id,
                    )

        return bound_count

    def get_unambiguous_elmcomp_direct_instances(
            self, entries: Iterable[ElmCompInstanceEntry],
    ) -> List[ElmCompInstanceEntry]:
        """Select complete pblk/pelm relations with one unique slot identifier.

        Incomplete relations remain available in the source catalogue, but cannot
        become executable children or provide runtime parameter values.

        :param entries: Extracted direct relations, including source gaps.
        :return: Complete relations whose slot identifier occurs exactly once.
        """
        unique_slot_entries: List[ElmCompInstanceEntry] = (
            get_unique_elmcomp_slot_entries(entries=entries)
        )
        selected_entries: List[ElmCompInstanceEntry] = list()
        entry: ElmCompInstanceEntry
        for entry in unique_slot_entries:
            if (
                    entry.element_id is None
                    or not entry.element_reference_is_resolved
            ):
                pass
            else:
                selected_entries.append(entry)

        return selected_entries

    def prepare_dgs_logical_actuator_topology(self) -> int:
        """Reconstruct zero-impedance valve placement for logical composites.

        PowerFactory frames may export valve slots without physical ``ElmValve``
        rows. The paired passive branch and voltage-measurement terminals still
        define the exact series topology. Replacing the isolated valve-side node by
        the measured rail is electrically equivalent once the passive RMS branch
        receives the exported gate status.

        :param circuit: Imported VeraGrid circuit.
        :param dgs_circuit: Parsed source DGS tables.
        :param templates_by_root_dgs_id: Registered RMS templates by exact root FID.
        :param logger: Import diagnostic sink.
        :return: Number of passive actuator branches prepared for RMS.
        """
        dgs_element_by_id: Dict[str, DGSElement] = self.dgs_grid.build_dgs_element_index()

        bus_by_id: Dict[str, Bus] = dict()
        bus: Bus
        for bus in self.grid.buses:
            bus_by_id[str(bus.idtag)] = bus

        line_by_id: Dict[str, Line | SeriesReactance] = dict()
        physical_branch: object
        for physical_branch in self.grid.get_branches_iter(
                add_vsc=False,
                add_hvdc=False,
                add_switch=False,
        ):
            if isinstance(physical_branch, (Line, SeriesReactance)):
                line_by_id[str(physical_branch.idtag)] = physical_branch
            else:
                pass

        prepared_count: int = 0
        source_root: ElmComp
        for source_root in self.dgs_grid.elmcomps:
            root_id: str = str(source_root.ID)
            if int(source_root.outserv) == 0:
                direct_entries: List[ElmCompInstanceEntry] = (
                    self.get_unambiguous_elmcomp_direct_instances(
                        entries=extract_elmcomp_direct_instances(
                            circuit=self.dgs_grid,
                            root_element=source_root,
                        )
                    )
                )
                passive_entries: List[ElmCompInstanceEntry] = list()
                voltage_entries: List[ElmCompInstanceEntry] = list()
                direct_entry: ElmCompInstanceEntry
                for direct_entry in direct_entries:
                    if direct_entry.element_kind == "ElmSind":
                        passive_entries.append(direct_entry)
                    else:
                        if direct_entry.element_kind == "StaVmea":
                            voltage_entries.append(direct_entry)
                        else:
                            pass

                passive_entries.sort(key=_entry_slot_sort_key)
                voltage_entries.sort(key=_entry_slot_sort_key)
                passive_lines: List[Line | SeriesReactance] = list()
                passive_entry: ElmCompInstanceEntry
                for passive_entry in passive_entries:
                    passive_source_id: str | None = passive_entry.element_id
                    passive_line: Line | SeriesReactance | None = (
                        line_by_id.get(passive_source_id, None)
                        if passive_source_id is not None
                        else None
                    )
                    if passive_line is None:
                        pass
                    else:
                        passive_lines.append(passive_line)

                common_bus: Bus | None = _find_common_passive_bus(lines=passive_lines)
                if (
                        common_bus is None
                        or len(passive_lines) == 0
                        or len(passive_lines) != len(passive_entries)
                        or len(passive_lines) != len(voltage_entries)
                ):
                    if len(passive_entries) > 0:
                        self.logger.add_warning(
                            msg="DGS logical actuator topology is ambiguous",
                            device=source_root.loc_name,
                            value=(
                                f"lines={len(passive_lines)}, "
                                f"meters={len(voltage_entries)}"
                            ),
                            expected_value=f"ElmSind={len(passive_entries)}",
                        )
                    else:
                        pass
                else:
                    rail_buses: List[Bus | None] = list(
                        None for passive_line in passive_lines
                    )
                    open_resistance_by_pair: List[float | None] = list(
                        None for passive_line in passive_lines
                    )
                    topology_is_complete: bool = True
                    root_open_resistance_ohm: float | None = None
                    resistance_is_coherent: bool = True
                    physical_resistance_declared: bool = False
                    legacy_resistance_omitted: bool = False
                    pair_index: int
                    for pair_index, passive_line in enumerate(passive_lines):
                        passive_source_id: str | None = passive_entries[
                            pair_index
                        ].element_id
                        passive_source_element: DGSElement | None = (
                            dgs_element_by_id.get(passive_source_id, None)
                            if passive_source_id is not None
                            else None
                        )
                        if isinstance(passive_source_element, ElmSind):
                            if passive_source_element.initial_resistance_column_declared:
                                physical_resistance_declared = True
                                if (
                                        passive_source_element.Rin is not None
                                        and math.isfinite(passive_source_element.Rin)
                                        and passive_source_element.Rin > 0.0
                                ):
                                    pair_resistance_ohm: float = float(
                                        passive_source_element.Rin
                                    )
                                    open_resistance_by_pair[pair_index] = pair_resistance_ohm
                                    if root_open_resistance_ohm is None:
                                        root_open_resistance_ohm = pair_resistance_ohm
                                    else:
                                        if math.isclose(
                                                root_open_resistance_ohm,
                                                pair_resistance_ohm,
                                                rel_tol=1.0e-12,
                                                abs_tol=1.0e-12,
                                        ):
                                            pass
                                        else:
                                            resistance_is_coherent = False
                                else:
                                    topology_is_complete = False
                                    self.logger.add_warning(
                                        msg="DGS logical actuator has invalid physical open resistance",
                                        device=passive_source_id,
                                        value=passive_source_element.Rin,
                                    )
                            else:
                                legacy_resistance_omitted = True
                        else:
                            topology_is_complete = False
                            self.logger.add_warning(
                                msg="DGS logical actuator physical source could not be resolved",
                                device=passive_source_id,
                            )

                        voltage_source_id: str | None = voltage_entries[
                            pair_index
                        ].element_id
                        voltage_meter: DGSElement | None = (
                            dgs_element_by_id.get(voltage_source_id, None)
                            if voltage_source_id is not None
                            else None
                        )
                        terminal_id: str | None = (
                            _resolve_terminal_id(
                                pointer_id=voltage_meter.pbusbar,
                                dgs_element_by_id=dgs_element_by_id,
                            )
                            if isinstance(voltage_meter, StaVmea)
                            else None
                        )
                        rail_bus: Bus | None = (
                            bus_by_id.get(terminal_id, None)
                            if terminal_id is not None
                            else None
                        )
                        if rail_bus is None:
                            topology_is_complete = False
                            self.logger.add_warning(
                                msg="DGS logical actuator rail could not be resolved",
                                device=passive_line.name,
                                value=voltage_source_id,
                            )
                        else:
                            rail_buses[pair_index] = rail_bus
                            if (
                                    passive_line.bus_from is common_bus
                                    or passive_line.bus_to is common_bus
                            ):
                                pass
                            else:
                                topology_is_complete = False
                                self.logger.add_warning(
                                    msg="DGS passive actuator does not touch the shared node",
                                    device=passive_line.name,
                                    value=root_id,
                                )
                    if resistance_is_coherent:
                        pass
                    else:
                        topology_is_complete = False
                        self.logger.add_warning(
                            msg="DGS logical actuator has conflicting physical open resistances",
                            device=root_id,
                        )
                    if physical_resistance_declared and legacy_resistance_omitted:
                        topology_is_complete = False
                        self.logger.add_warning(
                            msg="DGS logical actuator mixes enriched and legacy resistance evidence",
                            device=root_id,
                        )
                    else:
                        pass
                    if topology_is_complete:
                        for pair_index, passive_line in enumerate(passive_lines):
                            rail_bus = rail_buses[pair_index]
                            if rail_bus is not None:
                                if passive_line.bus_from is common_bus:
                                    passive_line.bus_to = rail_bus
                                else:
                                    passive_line.bus_from = rail_bus

                                # The retained impedance is only one part of the
                                # PowerFactory valve-plus-impedance assembly. An
                                # exported in-service ElmSind must therefore not
                                # enter the static power flow by itself when the
                                # omitted ElmValve is open. Keep the physical shell
                                # out of the static admittance matrix. The DAE RMS
                                # formulation compiles every non-empty branch model,
                                # where gate and resistance are projected from the
                                # logical controller.
                                passive_line.active = False
                                passive_line.active_prof.fill(False)
                                self.actuator_topology[passive_line] = (
                                    root_id, open_resistance_by_pair[pair_index],
                                )
                                prepared_count += 1
                            else:
                                pass
                    else:
                        pass
            else:
                pass
        return prepared_count

    def _prepare_dgs_rms_device(
            self,
            device: DynamicDevice,
            ideal_ac_connector_constraint_ids: Set[str]) -> None:
        """Instantiate a standard template and register its concrete model.

        :param device: Static device whose model is prepared.
        :param ideal_ac_connector_constraint_ids: Independent ideal voltage constraints.
        :return: None.
        """
        if device.rms_model.empty():
            source = resolve_dgs_elmgenstat_source(str(device.idtag), self.dgs_grid.elmgenstats)
            if source is not None:
                has_controller = any(root.outserv == 0 and any(
                    str(reference).strip().lstrip('#') == source.ID for reference in root.pelm
                    if reference is not None) for root in self.dgs_grid.elmcomps)
                template = build_dgs_elmgenstat_fallback(
                    self.grid, device, source, self.logger, has_controller=has_controller)
            else:
                template = _build_dgs_default_rms_template(
                    circuit=self.grid,
                    device=device,
                    external_grid_source_ids=self.external_grid_source_ids,
                    elmgenstat_source_ids=self.elm_gen_stat_source_ids,
                    elmsym_source_ids=self.elm_sym_source_ids,
                    typeless_elmlod_source_ids=self.typeless_elm_lod_source_ids,
                    ideal_ac_connector_constraint_ids=ideal_ac_connector_constraint_ids,
                )
            if template is None:
                self.logger.add_warning(msg="DGS device has no standard RMS shell",
                                        device=device.name, device_class=device.device_type.value)
            else:
                assign_import_template(device, template)
                if template not in self.grid.rms_models:
                    self.grid.add_rms_model(template)
                else:
                    pass
        else:
            pass

        # Topology evidence belongs to the installed branch, never its template.
        actuator: Tuple[str, float | None] | None = self.actuator_topology.get(device, None)
        if actuator is not None and not device.rms_model.empty():
            set_import_field(device.rms_model, DgsImportField.DGS_LOGICAL_ACTUATOR_ROOT_ID,
                             actuator[0], self.dynamic_model_import.get_import_metadata())
            set_import_field(device.rms_model, DgsImportField.DGS_OPEN_RESISTANCE_OHM,
                             actuator[1], self.dynamic_model_import.get_import_metadata())
        else:
            pass

    def prepare_dgs_circuit_for_rms(self) -> None:
        """
        Instantiate missing standard RMS models after one massive DGS import.

        Imported models take priority. Each missing model is instantiated as soon
        as its template is selected; metadata records the installed block UID.

        :return: None.
        """

        bus: Bus
        branch_devices: List[DynamicDevice] = list(
            self.grid.get_branches_iter(
                add_vsc=False,
                add_hvdc=False,
                add_switch=True,
            )
        )
        ideal_ac_connector_constraint_ids: Set[str] = (
            _select_ideal_ac_connector_constraint_ids(
                circuit=self.grid,
                branch_devices=branch_devices,
            )
        )
        injection_devices: List[DynamicDevice] = list(self.grid.get_injection_devices_iter())
        device: DynamicDevice
        dc_bus_capacitance: Dict[Bus, float] = dict()

        # Split each active physical cable capacitance equally between its terminal
        # nodes, which is the standard lumped pi representation used by RMS.
        for bus in self.grid.buses:
            dc_bus_capacitance[bus] = 0.0
        dc_line: DcLine
        for dc_line in self.grid.dc_lines:
            if dc_line.active:
                dynamic_values: tuple[float, float] = dc_line.get_dynamic_values_pu_seconds(
                    Sbase=float(self.grid.Sbase),
                    logger=self.logger,
                )
                terminal_capacitance: float = 0.5 * max(
                    0.0,
                    float(dynamic_values[1]),
                )
                dc_bus_capacitance[dc_line.bus_from] += terminal_capacitance
                dc_bus_capacitance[dc_line.bus_to] += terminal_capacitance
            else:
                pass

        # A native monopolar converter places its exported cell energy directly at
        # its single DC terminal.  Add it to the same nodal coefficient as cable
        # shunts so the solver advances one physical voltage state rather than two
        # constrained copies of the same DC-link voltage.
        converter: VSC
        for converter in self.grid.get_vsc():
            converter_capacitance: float = (
                _get_monopolar_vsc_dc_capacitance_pu_seconds(
                    converter=converter,
                    system_base_mva=float(self.grid.Sbase),
                )
            )
            if converter_capacitance > 0.0:
                dc_bus_capacitance[converter.bus_from] += converter_capacitance
            else:
                pass

        # Every device template connects against an existing bus shell, so buses are
        # initialized first and only when an imported model has not already done it.
        for bus in self.grid.buses:
            if bus.is_dc and not bus.is_grounded:
                bus_capacitance: float = dc_bus_capacitance.get(bus, 0.0)
            else:
                bus_capacitance = 0.0
            vdc_shell_var: Var | None = bus.rms_model.external_mapping.get(
                VarPowerFlowReferenceType.Vdc,
                None,
            )
            is_replaceable_dc_shell: bool = (
                    bus_capacitance > 0.0
                    and vdc_shell_var is not None
                    and len(bus.rms_model.state_vars) == 0
                    and len(bus.rms_model.algebraic_vars) == 1
                    and len(bus.rms_model.algebraic_eqs) == 0
                    and len(bus.rms_model.children) == 0
            )
            if bus.rms_model.empty():
                initialize_bus_rms(
                    bus=bus,
                    vf=self.grid.var_factory,
                    dc_shunt_capacitance_pu_seconds=bus_capacitance,
                )

            elif is_replaceable_dc_shell and vdc_shell_var is not None:
                # Dynamic association has already connected controller inputs to
                # this exact Vdc UID. Promote the existing variable in place so no
                # imported symbolic connection is invalidated by a replacement.
                promote_dc_bus_voltage_to_capacitive_state(
                    bus_rms_model=bus.rms_model,
                    vf=self.grid.var_factory,
                    dc_shunt_capacitance_pu_seconds=bus_capacitance,
                )

            else:
                pass

        # Branches are connected before injections so all passive network equations
        # are available when the RMS problem compiles its nodal balances.
        for device in branch_devices:
            self._prepare_dgs_rms_device(
                device=device,
                ideal_ac_connector_constraint_ids=ideal_ac_connector_constraint_ids,

            )

        for device in self.grid.get_vsc():
            self._prepare_dgs_rms_device(
                device=device,
                ideal_ac_connector_constraint_ids=ideal_ac_connector_constraint_ids,

            )

        for device in injection_devices:
            self._prepare_dgs_rms_device(
                device=device,
                ideal_ac_connector_constraint_ids=ideal_ac_connector_constraint_ids
            )

    def complete_model_references(self) -> None:
        """Connect machine frames using the definitive device-owned variables.

        :return: None.
        """
        _bind_dgs_elmsym_reference_frequencies(
            circuit=self.grid,
            branch_devices=list(self.grid.get_branches_iter(add_vsc=False, add_hvdc=False, add_switch=True)),
            elmsym_reference_source_ids=self.elm_sym_reference_source_ids,
            logger=self.logger,
            import_metadata=self.dynamic_model_import.get_import_metadata(),
        )

    def classify_static_dev_and_build_missing_models(self) -> None:
        """Classify source equipment before topology and template construction.

        :return: None.
        """
        external_grid_source: ElmXnet
        for external_grid_source in self.dgs_grid.elmxnets:
            if external_grid_source.ID == "":
                pass
            else:
                self.external_grid_source_ids.add(external_grid_source.ID)

        elm_gen_stat_source: ElmGenstat
        for elm_gen_stat_source in self.dgs_grid.elmgenstats:
            if elm_gen_stat_source.ID == "":
                pass
            else:
                self.elm_gen_stat_source_ids.add(elm_gen_stat_source.ID)

        self.elm_sym_reference_source_ids.clear()
        elm_sym_source: ElmSym
        for elm_sym_source in self.dgs_grid.elmsyms:
            if elm_sym_source.ID == "":
                pass
            else:
                self.elm_sym_source_ids.add(elm_sym_source.ID)
                if int(elm_sym_source.ip_ctrl) == 1:
                    self.elm_sym_reference_source_ids.add(elm_sym_source.ID)
                else:
                    pass

        elmlod_source: ElmLod
        for elmlod_source in self.dgs_grid.elmlods:
            if (
                    elmlod_source.ID != ""
                    and _ref_id(elmlod_source.typ_id) in {None, ""}
            ):
                self.typeless_elm_lod_source_ids.add(elmlod_source.ID)
            else:
                pass


def parse_header(line: str) -> Tuple[str, Dict[str, int]]:
    """
    Parse $$ header line and return property -> index map.
    """
    element_type = line[2:].split(";", 1)[0]
    parts = line.strip().split(';')[1:]  # skip $$ElementType
    header_map: Dict[str, int] = {}

    for i, name_stub in enumerate(parts):
        name_stub = parts[i]
        stubs = name_stub.split("(")
        prop_name = stubs[0] if len(stubs) > 0 else name_stub
        header_map[prop_name] = i

        # PowerFactory exports commonly use 'FID' as the unique identifier column.
        # The schema in dgs_objects.py uses the python attribute name 'ID'. Map both.
        if prop_name == 'FID':
            header_map['ID'] = i

    return element_type, header_map


def _elm_sind_initial_resistance_envelope_is_declared(
        elements: List[ElmSind],
) -> bool:
    """Validate and select the ``ElmSind.s:Rin`` output envelope.

    A DGS table owns one header for every row. Consequently, a legacy table
    cannot be mixed with enriched rows without changing the meaning of its
    missing resistance evidence. Validation occurs before the output file is
    opened so a rejected table cannot leave a truncated artifact.

    :param elements: Series-impedance rows scheduled for serialization.
    :return: Whether the output table must declare ``s:Rin``.
    :raises ValueError: If enriched and legacy rows are mixed or an enriched
        resistance is invalid.
    """
    declared_count: int = 0
    element: ElmSind
    for element in elements:
        if element.initial_resistance_column_declared:
            declared_count += 1
        else:
            pass

    if declared_count == 0:
        return False
    else:
        if declared_count == len(elements):
            for element in elements:
                if (
                        element.Rin is not None
                        and math.isfinite(element.Rin)
                        and element.Rin > 0.0
                ):
                    pass
                else:
                    raise ValueError(
                        "Cannot write an enriched ElmSind table with an invalid s:Rin value"
                    )
            return True
        else:
            raise ValueError(
                "Cannot write one ElmSind table with mixed legacy and enriched s:Rin evidence"
            )


class DgsCircuit:
    """Strongly-typed container for a PowerFactory DGS file."""
    __slots__ = (
        "_id_counter",
        "generals",
        "blkdefs",
        "blkdivs",
        "blkfroms",
        "blkgotos",
        "blkmuls",
        "blkrefs",
        "blksigs",
        "blkslots",
        "blksums",
        "comldfs",
        "blkswts",
        "elmcomps",
        "elmdsls",
        "elmbranches",
        "charefs",
        "chavecs",
        "elmasms",
        "elmcoups",
        "elmfeeders",
        "elmgenstats",
        "elmvscs",
        "elmvscmonos",
        "elmlnes",
        "elmtows",
        "elmsinds",
        "elmlnesecs",
        "elmvacs",
        "elmlods",
        "elmlodlvs",
        "elmlodlvps",
        "elmnets",
        "elmphis",
        "elmshnts",
        "elmsvss",
        "elmzpus",
        "elmscaps",
        "elmsites",
        "elmsubstats",
        "elmsyms",
        "elmterms",
        "elmtr2s",
        "elmtr3s",
        "elmtr4s",
        "elmxnets",
        "elmzones",
        "elmareas",
        "intfolders",
        "intrefs",
        "inttemplates",
        "intgrfs",
        "intgrfcons",
        "intgrfgroups",
        "intgrfnets",
        "matrixes",
        "relfuses",
        "stacubics",
        "stacts",
        "staimeas",
        "stapqmeas",
        "staswitchs",
        "stavmeas",
        "stavts",
        "typswitches",
        "typasmos",
        "typcts",
        "typfuses",
        "typcabs",
        "typcabsys",
        "typcons",
        "typgeos",
        "typlnes",
        "typtows",
        "typsinds",
        "typlods",
        "typsyms",
        "typtr2s",
        "typtr3s",
        "typtr4s",
        "typvts",
        "_CLASS_TO_LIST",
        "logger",
    )

    _ELEMENT_CLASSES: List[Type[DGSElement]] = [
        General,
        BlkDef,
        BlkDiv,
        BlkFrom,
        BlkGoto,
        BlkMul,
        BlkRef,
        BlkSig,
        BlkSlot,
        BlkSum,
        BlkSwt,
        ChaRef,
        ChaVec,
        ComLdf,
        ElmComp,
        ElmDsl,
        ElmBranch,
        ElmAsm,
        ElmCoup,
        ElmFeeder,
        ElmGenstat,
        # Alex review required: recognize both VSC formats as declarative DGS elements.
        ElmVsc,
        ElmVscmono,
        ElmLne,
        ElmTow,
        ElmZpu,
        ElmScap,
        ElmSind,
        ElmLnesec,
        ElmVac,
        ElmLod,
        ElmLodlv,
        ElmLodlvp,
        ElmNet,
        ElmPhi,
        ElmShnt,
        ElmSvs,
        ElmSite,
        ElmSubstat,
        ElmSym,
        ElmTerm,
        ElmTr2,
        ElmTr3,
        ElmTr4,
        ElmXnet,
        ElmZone,
        ElmArea,
        General,
        IntFolder,
        IntRef,
        IntTemplate,
        IntGrf,
        IntGrfcon,
        IntGrfgroup,
        IntGrfnet,
        Matrix,
        RelFuse,
        StaCubic,
        StaCt,
        StaImea,
        StaPqmea,
        StaSwitch,
        StaVmea,
        StaVt,
        TypSwitch,
        TypAsmo,
        TypCt,
        TypFuse,
        TypCab,
        TypCabsys,
        TypCon,
        TypGeo,
        TypLne,
        TypTow,
        TypSind,
        TypLod,
        TypSym,
        TypTr2,
        TypTr3,
        TypTr4,
        TypVt,
    ]

    ELEMENT_CLASS_BY_KIND: Dict[str, Type[DGSElement]] = {
        cls.element_type: cls for cls in _ELEMENT_CLASSES
    }

    def __init__(self) -> None:
        """

        """
        self._id_counter = 0

        self.generals: List[General] = list()
        self.blkdefs: List[BlkDef] = list()
        self.blkdivs: List[BlkDiv] = list()
        self.blkfroms: List[BlkFrom] = list()
        self.blkgotos: List[BlkGoto] = list()
        self.blkmuls: List[BlkMul] = list()
        self.blkrefs: List[BlkRef] = list()
        self.blksigs: List[BlkSig] = list()
        self.blkslots: List[BlkSlot] = list()
        self.blksums: List[BlkSum] = list()
        self.comldfs: List[ComLdf] = list()
        self.blkswts: List[BlkSwt] = list()
        self.elmcomps: List[ElmComp] = list()
        self.elmdsls: List[ElmDsl] = list()
        self.elmbranches: List[ElmBranch] = list()
        self.charefs: List[ChaRef] = list()
        self.chavecs: List[ChaVec] = list()
        self.elmasms: List[ElmAsm] = list()
        self.elmcoups: List[ElmCoup] = list()
        self.elmfeeders: List[ElmFeeder] = list()
        self.elmgenstats: List[ElmGenstat] = list()
        # Alex review required: discard transient collections after creating the final VSC devices.
        self.elmvscs: List[ElmVsc] = list()
        self.elmvscmonos: List[ElmVscmono] = list()
        self.elmlnes: List[ElmLne] = list()
        self.elmtows: List[ElmTow] = list()
        self.elmsinds: List[ElmSind] = list()
        self.elmlnesecs: List[ElmLnesec] = list()
        self.elmvacs: List[ElmVac] = list()
        self.elmlods: List[ElmLod] = list()
        self.elmlodlvs: List[ElmLodlv] = list()
        self.elmlodlvps: List[ElmLodlvp] = list()
        self.elmnets: List[ElmNet] = list()
        self.elmphis: List[ElmPhi] = list()
        self.elmshnts: List[ElmShnt] = list()
        self.elmsvss: List[ElmSvs] = list()
        self.elmzpus: List[ElmZpu] = list()
        self.elmscaps: List[ElmScap] = list()
        self.elmsites: List[ElmSite] = list()
        self.elmsubstats: List[ElmSubstat] = list()
        self.elmsyms: List[ElmSym] = list()
        self.elmterms: List[ElmTerm] = list()
        self.elmtr2s: List[ElmTr2] = list()
        self.elmtr3s: List[ElmTr3] = list()
        self.elmtr4s: List[ElmTr4] = list()
        self.elmxnets: List[ElmXnet] = list()
        self.elmzones: List[ElmZone] = list()
        self.elmareas: List[ElmArea] = list()
        self.intfolders: List[IntFolder] = list()
        self.intrefs: List[IntRef] = list()
        self.inttemplates: List[IntTemplate] = list()
        self.intgrfs: List[IntGrf] = list()
        self.intgrfcons: List[IntGrfcon] = list()
        self.intgrfgroups: List[IntGrfgroup] = list()
        self.intgrfnets: List[IntGrfnet] = list()
        self.matrixes: List[Matrix] = list()
        self.relfuses: List[RelFuse] = list()
        self.stacubics: List[StaCubic] = list()
        self.stacts: List[StaCt] = list()
        self.staimeas: List[StaImea] = list()
        self.stapqmeas: List[StaPqmea] = list()
        self.staswitchs: List[StaSwitch] = list()
        self.stavmeas: List[StaVmea] = list()
        self.stavts: List[StaVt] = list()
        self.typswitches: List[TypSwitch] = list()
        self.typasmos: List[TypAsmo] = list()
        self.typcts: List[TypCt] = list()
        self.typfuses: List[TypFuse] = list()
        self.typcabs: List[TypCab] = list()
        self.typcabsys: List[TypCabsys] = list()
        self.typcons: List[TypCon] = list()
        self.typgeos: List[TypGeo] = list()
        self.typlnes: List[TypLne] = list()
        self.typtows: List[TypTow] = list()
        self.typsinds: List[TypSind] = list()
        self.typlods: List[TypLod] = list()
        self.typsyms: List[TypSym] = list()
        self.typtr2s: List[TypTr2] = list()
        self.typtr3s: List[TypTr3] = list()
        self.typtr4s: List[TypTr4] = list()
        self.typvts: List[TypVt] = list()

        self._CLASS_TO_LIST: Dict[Type[DGSElement], List[DGSElement]] = {
            General: self.generals,
            BlkDef: self.blkdefs,
            BlkDiv: self.blkdivs,
            BlkFrom: self.blkfroms,
            BlkGoto: self.blkgotos,
            BlkMul: self.blkmuls,
            BlkRef: self.blkrefs,
            BlkSig: self.blksigs,
            BlkSlot: self.blkslots,
            BlkSum: self.blksums,
            BlkSwt: self.blkswts,
            ChaRef: self.charefs,
            ChaVec: self.chavecs,
            ComLdf: self.comldfs,
            ElmComp: self.elmcomps,
            ElmDsl: self.elmdsls,
            ElmBranch: self.elmbranches,
            ElmAsm: self.elmasms,
            ElmCoup: self.elmcoups,
            ElmFeeder: self.elmfeeders,
            ElmGenstat: self.elmgenstats,
            # Alex review required: route each VSC table into its typed import collection.
            ElmVsc: self.elmvscs,
            ElmVscmono: self.elmvscmonos,
            ElmLne: self.elmlnes,
            ElmTow: self.elmtows,
            ElmZpu: self.elmzpus,
            ElmScap: self.elmscaps,
            ElmSind: self.elmsinds,
            ElmLnesec: self.elmlnesecs,
            ElmVac: self.elmvacs,
            ElmLod: self.elmlods,
            ElmLodlv: self.elmlodlvs,
            ElmLodlvp: self.elmlodlvps,
            ElmNet: self.elmnets,
            ElmPhi: self.elmphis,
            ElmShnt: self.elmshnts,
            ElmSvs: self.elmsvss,
            ElmSite: self.elmsites,
            ElmSubstat: self.elmsubstats,
            ElmSym: self.elmsyms,
            ElmTerm: self.elmterms,
            ElmTr2: self.elmtr2s,
            ElmTr3: self.elmtr3s,
            ElmTr4: self.elmtr4s,
            ElmXnet: self.elmxnets,
            ElmZone: self.elmzones,
            ElmArea: self.elmareas,
            IntFolder: self.intfolders,
            IntRef: self.intrefs,
            IntTemplate: self.inttemplates,
            IntGrf: self.intgrfs,
            IntGrfcon: self.intgrfcons,
            IntGrfgroup: self.intgrfgroups,
            IntGrfnet: self.intgrfnets,
            Matrix: self.matrixes,
            RelFuse: self.relfuses,
            StaCubic: self.stacubics,
            StaCt: self.stacts,
            StaImea: self.staimeas,
            StaPqmea: self.stapqmeas,
            StaSwitch: self.staswitchs,
            StaVmea: self.stavmeas,
            StaVt: self.stavts,
            TypSwitch: self.typswitches,
            TypAsmo: self.typasmos,
            TypCt: self.typcts,
            TypFuse: self.typfuses,
            TypCab: self.typcabs,
            TypCabsys: self.typcabsys,
            TypCon: self.typcons,
            TypGeo: self.typgeos,
            TypLne: self.typlnes,
            TypTow: self.typtows,
            TypSind: self.typsinds,
            TypLod: self.typlods,
            TypSym: self.typsyms,
            TypTr2: self.typtr2s,
            TypTr3: self.typtr3s,
            TypTr4: self.typtr4s,
            TypVt: self.typvts,
        }

        self.logger = Logger()

    def new_id(self) -> str:
        """

        :return:
        """
        self._id_counter += 1
        return str(self._id_counter)

    def get_all_elements_iter(self) -> Iterator[DGSElement]:
        """Iterate over every parsed DGS element in schema order.

        This public boundary lets import layers build exact FID indexes without
        reaching into the circuit's private class registry.

        :return: Iterator over all parsed DGS elements.
        """
        element_list: List[DGSElement]
        element: DGSElement
        for element_list in self._CLASS_TO_LIST.values():
            for element in element_list:
                yield element

    def add_element_cubicles(self, element_id: str, dgs_buses: List[ElmTerm]):
        """
        Add cubicles + their StaSwitch objects.
        IMPORTANT: Import expects StaSwitch.fold_id == StaCubic.ID.
        """
        for i, b in enumerate(dgs_buses):
            c = StaCubic()
            c.ID = self.new_id()
            c.loc_name = f"StaCubic_{c.ID}"
            c.obj_id = element_id
            c.obj_bus = i
            c.fold_id = b.ID
            c.it2p1 = 0
            c.it2p2 = 1
            c.it2p3 = 2
            self.stacubics.append(c)

            # Create the switch that belongs to this cubicle
            sw = StaSwitch()
            sw.ID = self.new_id()
            sw.loc_name = f"StaSwitch_{sw.ID}"
            sw.fold_id = c.ID  # points to StaCubic.ID
            sw.on_off = 1  # default closed
            sw.typ_id = ""
            sw.iUse = 0
            sw.for_name = ""
            sw.aUsage = "cbk"  # matches typical PF exports
            self.staswitchs.append(sw)

    def parse_dgs(self, path: str) -> None:
        """
        Parse a DGS file and populate the typed lists.
        """
        path2 = Path(path)
        current_cls: Optional[Type[DGSElement]] = None
        header_map: Dict[str, int] | None = None

        with path2.open("r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                line = raw_line.strip()

                if line == "" or line.startswith("*"):
                    # Empty line or comment
                    pass

                elif line.startswith("$$"):
                    # Header line
                    element_type, header_map = parse_header(line)
                    normalized_element_type: str
                    if element_type in ("ElmPhi__pll", "ElmPhi__Pll"):
                        # PowerFactory exposes the implementation suffix on
                        # some native PLL exports. Both names share the exact
                        # declarative ElmPhi row contract.
                        normalized_element_type = "ElmPhi"
                    else:
                        normalized_element_type = element_type
                    current_cls = self.ELEMENT_CLASS_BY_KIND.get(
                        normalized_element_type,
                        None,
                    )

                else:
                    # Data line
                    if current_cls is not None:
                        obj = current_cls.parse_line(line=line, header_map=header_map)

                        if obj is not None:
                            if isinstance(obj, ElmSind):
                                if header_map is not None:
                                    # Preserve whether the source declared the
                                    # enriched physical-resistance envelope so
                                    # invalid data cannot masquerade as legacy.
                                    obj.initial_resistance_column_declared = (
                                            "s:Rin" in header_map
                                    )
                                else:
                                    obj.initial_resistance_column_declared = False
                            else:
                                pass
                            objects_lst = self._CLASS_TO_LIST[current_cls]
                            objects_lst.append(obj)

    def write_dgs(self, path: str) -> None:
        """Write the circuit to a declarative DGS file.

        :param path: Destination DGS path.
        :return: None.
        """
        path2 = Path(path)
        elm_sind_resistance_declared: bool = (
            _elm_sind_initial_resistance_envelope_is_declared(
                elements=self.elmsinds,
            )
        )

        with path2.open("w", encoding="utf-8") as f:

            comment = "*" * 80 + "\n"
            comment += "* Created with VeraGrid\n"
            comment += "*" * 80 + "\n"
            f.write(comment + "\n")

            for cls in self._ELEMENT_CLASSES:
                objects: List[DGSElement] = self._CLASS_TO_LIST[cls]

                if len(objects) > 0:
                    output_properties: List[DgsProperty] = list()
                    prop: DgsProperty
                    for prop in cls.properties_list:
                        omit_legacy_resistance: bool = (
                                cls is ElmSind
                                and not elm_sind_resistance_declared
                                and prop.name == "s:Rin"
                        )
                        if omit_legacy_resistance:
                            pass
                        else:
                            output_properties.append(prop)

                    header = "$$" + cls.element_type + ";" + ";".join(
                        f"{prop.name}({prop.dgs_type})"
                        for prop in output_properties
                    )
                    f.write(header + "\n")

                    comment = "*" * 80 + "\n"
                    for prp in output_properties:
                        comment += f"* {prp.name}: {prp.dgs_type}: {prp.description}\n"

                    comment += "*" * 80
                    f.write(comment + "\n")

                    for obj in objects:
                        serialized_line: str = obj.to_dgs_line()
                        if cls is ElmSind and not elm_sind_resistance_declared:
                            serialized_parts: List[str] = _split_dgs_line(
                                serialized_line
                            )
                            output_parts: List[str] = list()
                            property_index: int
                            for property_index, prop in enumerate(
                                    cls.properties_list
                            ):
                                if prop.name == "s:Rin":
                                    pass
                                else:
                                    output_parts.append(
                                        serialized_parts[property_index]
                                    )
                            f.write(";".join(output_parts) + "\n")
                        else:
                            f.write(serialized_line + "\n")

                    f.write("\n")
