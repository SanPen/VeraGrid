from __future__ import annotations

import math
from typing import Dict, List

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.series_reactance import SeriesReactance
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    ElmCompInstanceEntry,
    extract_elmcomp_direct_instances,
    get_unambiguous_elmcomp_direct_instances,
)
from VeraGridEngine.IO.dgs.dgs_objects import DGSElement, ElmComp, ElmSind, StaVmea
from VeraGridEngine.IO.dgs.dgs_rms_measurement_binding import (
    _build_dgs_element_index,
    _resolve_terminal_id,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var, heaviside
from VeraGridEngine.Utils.Symbolic.symbolic_io import duplicate_block
from VeraGridEngine.Utils.procedural_logic import sampled_value
from VeraGridEngine.enumerations import ParamPowerFlowReferenceType


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


def _find_common_passive_bus(
        lines: List[Line | SeriesReactance],
) -> Bus | None:
    """Find the shared neutral node of one multi-branch passive actuator.

    :param lines: Passive branches referenced by one logical composite.
    :return: Shared or grounded bus, or ``None`` when topology is ambiguous.
    """
    endpoint_counts: Dict[Bus, int] = dict()
    line: Line | SeriesReactance
    endpoint_bus: Bus
    for line in lines:
        for endpoint_bus in list([line.bus_from, line.bus_to]):
            endpoint_count: int | None = endpoint_counts.get(endpoint_bus, None)
            if endpoint_count is None:
                endpoint_counts[endpoint_bus] = 1
            else:
                endpoint_counts[endpoint_bus] = endpoint_count + 1

    common_bus: Bus | None = None
    common_count: int = 0
    candidate_bus: Bus
    candidate_count: int
    for candidate_bus, candidate_count in endpoint_counts.items():
        if candidate_bus.is_grounded and candidate_count >= common_count:
            common_bus = candidate_bus
            common_count = candidate_count
        else:
            if candidate_count > common_count and candidate_count > 1:
                common_bus = candidate_bus
                common_count = candidate_count
            else:
                pass
    return common_bus


def _collect_unique_named_vars(block: Block, variable_name: str) -> List[Var]:
    """Collect UID-distinct variables carrying one exact exported name.

    :param block: Imported logical controller root.
    :param variable_name: Exact PowerFactory interface name.
    :return: UID-distinct matching variables.
    """
    matches_by_uid: Dict[int, Var] = dict()
    child_block: Block
    variable_collections: List[List[Var]]
    variable_collection: List[Var]
    variable: Var
    for child_block in block.get_all_blocks():
        variable_collections = list([
            child_block.in_vars,
            child_block.out_vars,
            child_block.state_vars,
            child_block.algebraic_vars,
            list(child_block.event_dict.keys()),
            list(child_block.parameters.keys()),
            list(child_block.init_eqs.keys()),
        ])
        for variable_collection in variable_collections:
            for variable in variable_collection:
                if variable.name == variable_name:
                    matches_by_uid[variable.uid] = variable
                else:
                    pass
    return list(matches_by_uid.values())


def _collect_unique_exported_leaf_vars(
        block: Block,
        variable_name: str,
) -> List[Var]:
    """Collect exact interface variables and humanized child-name variants.

    :param block: Imported logical controller root.
    :param variable_name: Exported PowerFactory leaf identifier.
    :return: UID-distinct variables with the requested semantic leaf name.
    """
    matches_by_uid: Dict[int, Var] = dict()
    child_block: Block
    variable_collections: List[List[Var]]
    variable_collection: List[Var]
    variable: Var
    for child_block in block.get_all_blocks():
        variable_collections = list([
            child_block.in_vars,
            child_block.out_vars,
            child_block.state_vars,
            child_block.algebraic_vars,
            list(child_block.event_dict.keys()),
            list(child_block.parameters.keys()),
            list(child_block.init_eqs.keys()),
        ])
        for variable_collection in variable_collections:
            for variable in variable_collection:
                is_exact_name: bool = variable.name == variable_name
                is_humanized_child_name: bool = variable.name.endswith(
                    "__" + variable_name
                )
                if is_exact_name or is_humanized_child_name:
                    matches_by_uid[variable.uid] = variable
                else:
                    pass
    return list(matches_by_uid.values())


def _seed_open_resistive_actuator(
        block: Block,
        open_resistance_ohm: float | None = None,
) -> bool:
    """Seed an open gated resistor from its exported physical resistance.

    PowerFactory models can leave ``inc(R)=inc(Rinc)=inc(xR)`` as a neutral
    initialization cycle because the physical valve is open. VeraGrid still
    needs a deterministic state before that valve first closes. The exported
    An enriched DGS carries the physical ``ElmSind.s:Rin`` boundary and that
    value has precedence. Older DGS files omit it, so the exported ``Rmax``
    runtime equation remains a deterministic compatibility fallback. A late
    symbolic seed copies the selected value only after all DGS parameters and
    procedural mode selectors have been initialized.

    :param block: Imported logical controller root.
    :param open_resistance_ohm: Optional native open resistance in Ohm.
    :return: Whether the complete declared seed was applied.
    """
    maximum_vars: List[Var] = _collect_unique_exported_leaf_vars(
        block=block,
        variable_name="Rmax",
    )
    target_vars: List[Var] = list()
    complete_target_set: bool = True
    target_name: str
    for target_name in list(["R", "Rinc", "Rx", "xR"]):
        named_vars: List[Var] = _collect_unique_exported_leaf_vars(
            block=block,
            variable_name=target_name,
        )
        if len(named_vars) > 0:
            target_var: Var
            for target_var in named_vars:
                target_vars.append(target_var)
        else:
            complete_target_set = False

    has_physical_seed: bool = (
            open_resistance_ohm is not None
            and math.isfinite(open_resistance_ohm)
            and open_resistance_ohm > 0.0
    )
    if has_physical_seed:
        seed_expression: Expr | None = Const(float(open_resistance_ohm))
    else:
        if len(maximum_vars) == 1:
            seed_expression = maximum_vars[0]
        else:
            seed_expression = None

    if seed_expression is not None and complete_target_set:
        target_var: Var
        for target_var in target_vars:
            block.post_init_seed_eqs[target_var] = seed_expression
            is_initial_resistance: bool = (
                    target_var.name == "Rinc"
                    or target_var.name.endswith("__Rinc")
            )
            if is_initial_resistance:
                child_block: Block
                for child_block in block.get_all_blocks():
                    if target_var in child_block.event_dict:
                        # ``inc(Rinc)=R`` is an initialization assignment, not
                        # a continuous algebraic equation. Retain the resolved
                        # off-state value after the startup pass.
                        child_block.event_dict[target_var] = seed_expression
                    else:
                        pass
            else:
                pass
        return True
    else:
        return False


def _can_seed_open_resistive_actuator(
        block: Block,
        open_resistance_ohm: float | None,
) -> bool:
    """Check whether the complete open-resistance seed can be declared.

    :param block: Imported logical controller root.
    :param open_resistance_ohm: Optional coherent physical resistance in Ohm.
    :return: Whether every required target and one seed source exist.
    """
    maximum_vars: List[Var] = _collect_unique_exported_leaf_vars(
        block=block,
        variable_name="Rmax",
    )
    complete_target_set: bool = True
    target_name: str
    for target_name in list(["R", "Rinc", "Rx", "xR"]):
        target_vars: List[Var] = _collect_unique_exported_leaf_vars(
            block=block,
            variable_name=target_name,
        )
        if len(target_vars) > 0:
            pass
        else:
            complete_target_set = False

    has_physical_seed: bool = (
            open_resistance_ohm is not None
            and math.isfinite(open_resistance_ohm)
            and open_resistance_ohm > 0.0
    )
    has_model_seed: bool = len(maximum_vars) == 1
    return complete_target_set and (has_physical_seed or has_model_seed)


def prepare_dgs_logical_actuator_topology(
        circuit: MultiCircuit,
        dgs_circuit: DgsCircuit,
        templates_by_root_dgs_id: Dict[str, RmsModelTemplate],
        logger: Logger,
) -> int:
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
    dgs_element_by_id: Dict[str, DGSElement] = _build_dgs_element_index(
        dgs_circuit=dgs_circuit,
    )

    bus_by_id: Dict[str, Bus] = dict()
    bus: Bus
    for bus in circuit.buses:
        bus_by_id[str(bus.idtag)] = bus

    line_by_id: Dict[str, Line | SeriesReactance] = dict()
    physical_branch: object
    for physical_branch in circuit.get_branches_iter(
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
    for source_root in dgs_circuit.elmcomps:
        root_id: str = str(source_root.ID)
        root_template: RmsModelTemplate | None = templates_by_root_dgs_id.get(
            root_id,
            None,
        )
        if (
                isinstance(root_template, RmsModelTemplate)
                and int(source_root.outserv) == 0
        ):
            direct_entries: List[ElmCompInstanceEntry] = (
                get_unambiguous_elmcomp_direct_instances(
                    entries=extract_elmcomp_direct_instances(
                        circuit=dgs_circuit,
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
                    logger.add_warning(
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
                template_gate_vars: List[Var] = _collect_unique_named_vars(
                    block=root_template.block,
                    variable_name="gate",
                )
                template_resistance_vars: List[Var] = _collect_unique_named_vars(
                    block=root_template.block,
                    variable_name="R",
                )
                if (
                        len(template_gate_vars) == 1
                        and len(template_resistance_vars) == 1
                ):
                    pass
                else:
                    topology_is_complete = False
                    logger.add_warning(
                        msg="DGS logical actuator controller interface is incomplete",
                        device=root_id,
                    )
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
                                logger.add_warning(
                                    msg="DGS logical actuator has invalid physical open resistance",
                                    device=passive_source_id,
                                    value=passive_source_element.Rin,
                                )
                        else:
                            legacy_resistance_omitted = True
                    else:
                        topology_is_complete = False
                        logger.add_warning(
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
                        logger.add_warning(
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
                            logger.add_warning(
                                msg="DGS passive actuator does not touch the shared node",
                                device=passive_line.name,
                                value=root_id,
                            )
                        existing_template: RmsModelTemplate | None = (
                            passive_line.rms_template
                        )
                        if isinstance(existing_template, RmsModelTemplate):
                            if passive_line.bus_from is common_bus:
                                future_voltage_base_kv: float = float(
                                    passive_line.bus_from.Vnom
                                )
                            else:
                                future_voltage_base_kv = float(rail_bus.Vnom)
                            branch_plan: _DgsLogicalActuatorBranchBindingPlan | None = (
                                _build_logical_actuator_branch_plan(
                                    line=passive_line,
                                    circuit=circuit,
                                    voltage_base_kv=future_voltage_base_kv,
                                )
                            )
                            if branch_plan is None:
                                topology_is_complete = False
                                logger.add_warning(
                                    msg="DGS logical actuator branch interface is incomplete",
                                    device=passive_line.name,
                                    value=root_id,
                                )
                            else:
                                pass
                        else:
                            topology_is_complete = False
                            logger.add_warning(
                                msg="DGS passive actuator has no RMS template",
                                device=passive_line.name,
                                value=root_id,
                            )

                if resistance_is_coherent:
                    pass
                else:
                    topology_is_complete = False
                    logger.add_warning(
                        msg="DGS logical actuator has conflicting physical open resistances",
                        device=root_id,
                    )
                if physical_resistance_declared and legacy_resistance_omitted:
                    topology_is_complete = False
                    logger.add_warning(
                        msg="DGS logical actuator mixes enriched and legacy resistance evidence",
                        device=root_id,
                    )
                else:
                    pass
                if _can_seed_open_resistive_actuator(
                        block=root_template.block,
                        open_resistance_ohm=root_open_resistance_ohm,
                ):
                    pass
                else:
                    topology_is_complete = False
                    logger.add_warning(
                        msg="DGS logical actuator controller seed is incomplete",
                        device=root_id,
                    )

                if topology_is_complete:
                    for pair_index, passive_line in enumerate(passive_lines):
                        rail_bus = rail_buses[pair_index]
                        existing_template = passive_line.rms_template
                        if (
                                rail_bus is not None
                                and isinstance(existing_template, RmsModelTemplate)
                        ):
                            if passive_line.bus_from is common_bus:
                                passive_line.bus_to = rail_bus
                            else:
                                passive_line.bus_from = rail_bus

                            # The first shell was connected to the source's
                            # valve-side placeholder bus. Reassigning the same
                            # template reconnects it to the resolved rail.
                            passive_line.rms_template = existing_template

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
                            passive_line.rms_model.dynamic_model_contract.dgs_logical_actuator_root_id = root_id
                            pair_resistance_ohm: float | None = (
                                open_resistance_by_pair[pair_index]
                            )
                            if pair_resistance_ohm is not None:
                                passive_line.rms_model.dynamic_model_contract.dgs_open_resistance_ohm = float(
                                    pair_resistance_ohm
                                )
                            else:
                                pass
                            prepared_count += 1
                        else:
                            pass
                else:
                    pass
        else:
            pass
    return prepared_count


class _DgsLogicalActuatorBranchBindingPlan:
    """Hold one validated, transient branch-binding operation."""

    __slots__ = (
        "line",
        "status_owner",
        "status_var",
        "resistance_parameter",
        "resistance_owner",
        "inductance_parameter",
        "inductance_owner",
        "impedance_base_ohm",
        "inductance_pu_seconds",
    )

    def __init__(
            self,
            line: Line | SeriesReactance,
            status_owner: Block,
            status_var: Var,
            resistance_parameter: Var,
            resistance_owner: Block,
            inductance_parameter: Var | None,
            inductance_owner: Block | None,
            impedance_base_ohm: float,
            inductance_pu_seconds: float | None,
    ) -> None:
        """Create one plan after every referenced owner has been resolved.

        :param line: Final physical actuator branch.
        :param status_owner: Block owning the conduction event variable.
        :param status_var: Exact conduction event variable.
        :param resistance_parameter: Exact static resistance parameter.
        :param resistance_owner: Block owning the resistance parameter.
        :param inductance_parameter: Optional exact inductance parameter.
        :param inductance_owner: Optional block owning the inductance parameter.
        :param impedance_base_ohm: Branch impedance base in Ohm.
        :param inductance_pu_seconds: Optional RMS inductance coefficient.
        :return: None.
        """
        self.line: Line | SeriesReactance = line
        self.status_owner: Block = status_owner
        self.status_var: Var = status_var
        self.resistance_parameter: Var = resistance_parameter
        self.resistance_owner: Block = resistance_owner
        self.inductance_parameter: Var | None = inductance_parameter
        self.inductance_owner: Block | None = inductance_owner
        self.impedance_base_ohm: float = impedance_base_ohm
        self.inductance_pu_seconds: float | None = inductance_pu_seconds


def _build_logical_actuator_branch_plan(
        line: Line | SeriesReactance,
        circuit: MultiCircuit,
        voltage_base_kv: float | None = None,
) -> _DgsLogicalActuatorBranchBindingPlan | None:
    """Resolve one complete branch plan without changing the circuit.

    :param line: Prepared physical actuator branch.
    :param circuit: Circuit providing RMS system bases.
    :param voltage_base_kv: Optional post-topology voltage base.
    :return: Complete transient plan or ``None`` when evidence is incomplete.
    """
    status_uid: int | None = (
        line.rms_model.dynamic_model_contract.rms_conduction_status_var_uid
    )
    status_owners: List[Block] = list()
    status_vars: List[Var] = list()
    child_block: Block
    event_var: Var
    if status_uid is None:
        pass
    else:
        for child_block in line.rms_model.get_all_blocks():
            for event_var in child_block.event_dict.keys():
                if event_var.uid == status_uid:
                    status_owners.append(child_block)
                    status_vars.append(event_var)
                else:
                    pass

    resistance_parameter: Var | None = line.rms_model.api_obj_mapping.get(
        ParamPowerFlowReferenceType.r,
        None,
    )
    resistance_owners: List[Block] = list()
    if resistance_parameter is None:
        pass
    else:
        for child_block in line.rms_model.get_all_blocks():
            if resistance_parameter in child_block.parameters:
                resistance_owners.append(child_block)
            else:
                pass

    inductance_parameter: Var | None = line.rms_model.api_obj_mapping.get(
        ParamPowerFlowReferenceType.dc_line_l_pu_seconds,
        None,
    )
    inductance_owners: List[Block] = list()
    if inductance_parameter is None:
        pass
    else:
        for child_block in line.rms_model.get_all_blocks():
            if inductance_parameter in child_block.parameters:
                inductance_owners.append(child_block)
            else:
                pass

    sbase: float = float(circuit.Sbase)
    if voltage_base_kv is None:
        effective_voltage_base_kv: float = float(line.bus_from.Vnom)
    else:
        effective_voltage_base_kv = float(voltage_base_kv)
    if sbase > 0.0 and effective_voltage_base_kv > 0.0:
        impedance_base_ohm: float = (
            effective_voltage_base_kv * effective_voltage_base_kv / sbase
        )
    else:
        impedance_base_ohm = 0.0

    if inductance_parameter is None:
        inductance_owner: Block | None = None
        inductance_pu_seconds: float | None = None
        inductance_is_complete: bool = True
    else:
        if len(inductance_owners) == 1:
            inductance_owner = inductance_owners[0]
            if isinstance(line, Line):
                inductance_pu_seconds = float(
                    line.dc_series_inductance_pu_seconds
                )
                inductance_is_complete = True
            else:
                frequency_base_hz: float = float(circuit.fBase)
                if frequency_base_hz > 0.0:
                    inductance_pu_seconds = float(line.X) / (
                        2.0 * math.pi * frequency_base_hz
                    )
                    inductance_is_complete = True
                else:
                    inductance_pu_seconds = None
                    inductance_is_complete = False
        else:
            inductance_owner = None
            inductance_pu_seconds = None
            inductance_is_complete = False

    if (
            not line.rms_model.empty()
            and len(status_owners) == 1
            and len(status_vars) == 1
            and resistance_parameter is not None
            and len(resistance_owners) == 1
            and impedance_base_ohm > 0.0
            and inductance_is_complete
    ):
        return _DgsLogicalActuatorBranchBindingPlan(
            line=line,
            status_owner=status_owners[0],
            status_var=status_vars[0],
            resistance_parameter=resistance_parameter,
            resistance_owner=resistance_owners[0],
            inductance_parameter=inductance_parameter,
            inductance_owner=inductance_owner,
            impedance_base_ohm=impedance_base_ohm,
            inductance_pu_seconds=inductance_pu_seconds,
        )
    else:
        return None


def bind_dgs_logical_actuator_runtime(
        circuit: MultiCircuit,
        templates_by_root_dgs_id: Dict[str, RmsModelTemplate],
        logger: Logger,
) -> int:
    """Bind each complete logical actuator group as one atomic operation.

    :param circuit: Imported circuit after standard RMS shell preparation.
    :param templates_by_root_dgs_id: Registered RMS templates by exact root FID.
    :param logger: Import diagnostic sink.
    :return: Number of passive actuator RMS models bound.
    """
    branches_by_root_id: Dict[str, List[Line | SeriesReactance]] = dict()
    open_resistance_by_root_id: Dict[str, float] = dict()
    conflicting_root_ids: set[str] = set()
    candidate_branch: object
    for candidate_branch in circuit.get_branches_iter(
            add_vsc=False,
            add_hvdc=False,
            add_switch=False,
    ):
        if isinstance(candidate_branch, (Line, SeriesReactance)):
            root_id: str | None = (
                candidate_branch.rms_model.dynamic_model_contract.dgs_logical_actuator_root_id
            )
            resistance_ohm: float | None = (
                candidate_branch.rms_model.dynamic_model_contract.dgs_open_resistance_ohm
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
        root_template: RmsModelTemplate | None = templates_by_root_dgs_id.get(
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
                    circuit=circuit,
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
            logger.add_warning(
                msg="DGS logical actuator group is incomplete or contradictory",
                device=root_id,
                value=len(branch_plans),
                expected_value=len(branches_by_root_id[root_id]),
            )
        else:
            controller_block: Block = duplicate_block(
                block=root_template.block,
                var_factory=circuit.var_factory,
            )
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
                logger.add_warning(
                    msg="DGS logical actuator controller initialization is incomplete",
                    device=root_id,
                )

    return bound_count


def release_dgs_logical_actuator_import_context(
        circuit: MultiCircuit,
) -> int:
    """Discard source-only actuator identity after exact RMS binding.

    Procedural projections remain on the final block because the standard
    boundary updater consumes them declaratively. The DGS root FID and
    exported resistance are import evidence only and must not survive on
    ``MultiCircuit`` blocks.

    :param circuit: Circuit whose logical actuators have completed binding.
    :return: Number of branch blocks whose import context was released.
    """
    released_count: int = 0
    candidate_branch: object
    for candidate_branch in circuit.get_branches_iter(
            add_vsc=False,
            add_hvdc=False,
            add_switch=False,
    ):
        if isinstance(candidate_branch, (Line, SeriesReactance)):
            block: Block = candidate_branch.rms_model
            if (
                    block.dynamic_model_contract.dgs_logical_actuator_root_id
                    is not None
                    or block.dynamic_model_contract.dgs_open_resistance_ohm
                    is not None
            ):
                block.dynamic_model_contract.dgs_logical_actuator_root_id = None
                block.dynamic_model_contract.dgs_open_resistance_ohm = None
                released_count += 1
            else:
                pass
        else:
            pass

    return released_count
