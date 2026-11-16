# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Detect, construct and assemble native RMS equipment without legacy wrappers."""

from __future__ import annotations

from enum import Enum
from typing import Iterable

from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.static_generator import StaticGenerator
from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import ElmSvs, ElmVsc, ElmGenstat, PowerFactoryVscType
from VeraGridEngine.IO.dgs.dgs_graphical_routing import DgsGraphicalRoutingResolver
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    DgsDirectRootBuildResult, DgsSlotSignalDirection, ElmCompInstanceEntry,
    _resolve_direct_slot_runtime_input_indices,
    _resolve_direct_slot_runtime_output_indices,
)
from VeraGridEngine.IO.dgs.dynamic_models.dgs_adapter_block_from_native_dgs import (
    DgsElmSymMachineParameters,
    build_dgs_elmgenstat_block, build_dgs_elmgenstat_voltage_source_block, build_dgs_elmsvs_block, build_dgs_elmsym_block,
    build_dgs_elmvsc_block, build_dgs_elmvscmono_block, build_dgs_elmvsc_two_level_block,
    build_dgs_regc_current_pll_block, build_dgs_regc_voltage_source_block,
)
from VeraGridEngine.IO.dgs.dynamic_models.dgs_genstat_protection import apply_genstat_voltage_protection
from VeraGridEngine.IO.dgs.dynamic_models.dgs_vsc_interfaces import add_native_vsc_dq_interface
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Const, Expr, Var
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


class NativeDgsEquipmentKind(Enum):
    """Native DGS source classes supported by the new physical-block workflow."""

    MonopolarVsc = "ElmVscmono"
    BipolarVsc = "ElmVsc"
    SynchronousMachine = "ElmSym"
    StaticGenerator = "ElmGenstat"
    StaticVarSystem = "ElmSvs"


class NativeDgsStaticSourceModel(Enum):
    """Exported ElmGenstat iSimModel realizations supported by native builders."""

    InferFromSignals = 0
    Current = 1
    Voltage = 2
    Impedance = 3
    Power = 4


class NativeDgsEquipmentPlan:
    """One construction requirement identified by an exact native slot and FID."""

    __slots__ = ("kind", "entry", "converter_type", "static_source_model")

    def __init__(self, kind: NativeDgsEquipmentKind, entry: ElmCompInstanceEntry,
                 converter_type: PowerFactoryVscType | None = None,
                 static_source_model: NativeDgsStaticSourceModel = NativeDgsStaticSourceModel.Current) -> None:
        """Retain source evidence without allocating or mutating a symbolic block.

        :param kind: Physical equation family selected from the source class.
        :param entry: Resolved native equipment slot in the selected root.
        :param converter_type: Exact converter topology when exported by the source.
        :param static_source_model: Native current or voltage command realization.
        :return: None.
        """
        self.static_source_model: NativeDgsStaticSourceModel = static_source_model
        self.kind: NativeDgsEquipmentKind = kind
        self.entry: ElmCompInstanceEntry = entry
        self.converter_type: PowerFactoryVscType | None = converter_type


def detect_native_dgs_equipment(
        direct_result: DgsDirectRootBuildResult, dgs_circuit: DgsCircuit | None = None,
) -> tuple[NativeDgsEquipmentPlan, ...]:
    """Identify native equipment needs from source slot classes and identities.

    This phase deliberately does not infer physics from missing signal names.
    Measurement slots remain owned by the existing measurement workflow.

    :param direct_result: Controller graph plus exact source-slot relations.
    :param dgs_circuit: Source rows supplying topology selectors when available.
    :return: All supported native equipment requirements in source order.
    """
    plans: list[NativeDgsEquipmentPlan] = list()
    seen_slots: set[str] = set()
    entry: ElmCompInstanceEntry
    for entry in direct_result.direct_entries:
        kind: NativeDgsEquipmentKind | None = None
        candidate: NativeDgsEquipmentKind
        for candidate in NativeDgsEquipmentKind:
            if entry.element_kind == candidate.value:
                kind = candidate
            else:
                pass
        if kind is None:
            pass
        else:
            if (entry.slot_id is None or entry.element_id is None
                    or not entry.slot_reference_is_resolved or not entry.element_reference_is_resolved):
                raise ValueError("Native equipment requires a resolved DGS slot and element FID")
            elif entry.slot_id in seen_slots:
                raise ValueError(f"Ambiguous native equipment slot {entry.slot_id}")
            else:
                seen_slots.add(entry.slot_id)
                converter_type: PowerFactoryVscType | None = None
                if kind == NativeDgsEquipmentKind.BipolarVsc and dgs_circuit is not None:
                    sources: list[ElmVsc] = list(source for source in dgs_circuit.elmvscs
                                                if source.ID == entry.element_id)
                    if len(sources) != 1:
                        raise ValueError("Native ElmVsc requires one exact source row")
                    elif sources[0].vsctype is None:
                        raise ValueError("Native ElmVsc requires an explicit vsctype selector")
                    else:
                        converter_type = PowerFactoryVscType(sources[0].vsctype)
                else:
                    pass
                static_model: NativeDgsStaticSourceModel = NativeDgsStaticSourceModel.Current
                if kind == NativeDgsEquipmentKind.StaticGenerator:
                    labels: set[str] = set(entry.get_connected_signal_components(DgsSlotSignalDirection.Input))
                    if dgs_circuit is not None:
                        native_sources: list[ElmGenstat] = list(source for source in dgs_circuit.elmgenstats if source.ID == entry.element_id)
                        if len(native_sources) == 1:
                            selector: int | None = native_sources[0].iSimModel
                            static_model = (NativeDgsStaticSourceModel.Current if selector is None
                                            else NativeDgsStaticSourceModel(selector))
                        else:
                            pass
                    else:
                        pass
                    if static_model == NativeDgsStaticSourceModel.InferFromSignals:
                        # Detection and construction must select the same law:
                        # a connected current order takes precedence over voltage.
                        current_orders: set[str] = labels & {'id_ref', 'iq_ref'}
                        voltage_orders: set[str] = labels & {'u1r_in', 'u1i_in'}
                        if current_orders:
                            static_model = NativeDgsStaticSourceModel.Current
                        elif voltage_orders == {'u1r_in', 'u1i_in'}:
                            static_model = NativeDgsStaticSourceModel.Voltage
                        elif voltage_orders:
                            raise ValueError("Ambiguous automatic ElmGenstat voltage/current input selection")
                        else:
                            static_model = NativeDgsStaticSourceModel.Current
                    elif static_model in (NativeDgsStaticSourceModel.Impedance, NativeDgsStaticSourceModel.Power):
                        raise ValueError("Native ElmGenstat impedance/power realization is unsupported")
                    else:
                        pass
                    if (static_model == NativeDgsStaticSourceModel.Voltage and dgs_circuit is not None
                            and any(source.ID == entry.element_id and source.iDelay not in (None, 0) for source in dgs_circuit.elmgenstats)):
                        raise ValueError("Native ElmGenstat voltage command delay is unsupported")
                    else:
                        pass
                else:
                    pass
                plans.append(NativeDgsEquipmentPlan(kind, entry, converter_type, static_model))
    return tuple(plans)


def _local_signal_lookup(block: Block) -> dict[str, Var]:
    """Index declared symbols inside one exact block, including parser aliases.

    :param block: One controller child or freshly built equipment block.
    :return: Local signal labels mapped to their declared variable objects.
    """
    result: dict[str, Var] = dict((label.rsplit("__", 1)[-1], variable)
                                   for label, variable in block.var_mapping.items())
    collection: Iterable[Var]
    variable: Var
    for collection in (block.in_vars, block.out_vars, block.state_vars, block.algebraic_vars,
                       block.parameters.keys(), block.event_dict.keys(), block.init_eqs.keys()):
        for variable in collection:
            result[variable.name.rsplit("__", 1)[-1]] = variable
    return result


def _constant_value(block: Block, variable: Var) -> float:
    """Read one explicit protected-model parameter without name-based guessing.

    :param block: Exact protected controller block.
    :param variable: Parameter identity declared by that block.
    :return: Numeric construction parameter.
    """
    expression: Expr | None = block.event_dict.get(variable, None)
    if expression is None:
        expression = block.parameters.get(variable, None)
    else:
        pass
    if isinstance(expression, Const) and isinstance(expression.value, (float, int)):
        return float(expression.value)
    else:
        raise ValueError(f"Protected native parameter {variable.name} must be numeric")


def construct_protected_native_dgs_blocks(control: Block) -> int:
    """Materialize the two supported protected REGC submodels in their own slots.

    :param control: Imported controller hierarchy, updated in place.
    :return: Number of protected blocks reconstructed using the new builders.
    """
    count: int = 0
    child: Block
    for child in control.get_all_blocks():
        if len(child.state_eqs) > 0 or len(child.algebraic_eqs) > 0:
            pass
        else:
            signals: dict[str, Var] = _local_signal_lookup(child)
            native: Block | None = None
            if set(("ur_ref", "ui_ref", "Te", "re", "xe", "x_lpf_d", "x_lpf_q")).issubset(signals):
                native = build_dgs_regc_voltage_source_block(
                    _constant_value(child, signals["Te"]), _constant_value(child, signals["re"]),
                    _constant_value(child, signals["xe"]), child.name)
            elif set(("ir", "ii", "ur", "ui", "id", "iq", "x0", "x1",
                      "Kppll", "Kipll", "Vpllfrz", "wmin", "wmax")).issubset(signals):
                native = build_dgs_regc_current_pll_block(
                    _constant_value(child, signals["Kppll"]), _constant_value(child, signals["Kipll"]),
                    _constant_value(child, signals["Vpllfrz"]), _constant_value(child, signals["wmin"]),
                    _constant_value(child, signals["wmax"]), child.name)
            else:
                pass
            if native is None:
                pass
            else:
                aliases: dict[str, str] = dict((
                    ("ur", "Vt_r"), ("ui", "Vt_i"), ("id_ref", "idref"),
                    ("iq_ref", "iqref"), ("u", "Vt"),
                ))
                substitutions: dict[Var, Var] = dict()
                new_variable: Var
                for new_variable in native.in_vars:
                    old_variable: Var | None = signals.get(new_variable.name, None)
                    if old_variable is None:
                        old_variable = signals.get(aliases.get(new_variable.name, ""), None)
                    else:
                        pass
                    if old_variable is None:
                        raise ValueError(f"Incomplete protected native port {new_variable.name}")
                    else:
                        substitutions[new_variable] = old_variable
                for new_variable in native.out_vars:
                    substitutions[new_variable] = signals[new_variable.name]
                for new_variable in native.state_vars:
                    substitutions[new_variable] = signals[new_variable.name]
                for new_variable in native.algebraic_vars:
                    old_variable = signals.get(new_variable.name, None)
                    if old_variable is not None:
                        substitutions[new_variable] = old_variable
                    else:
                        pass
                native.update_model_bulk(substitutions)
                child.state_vars = native.state_vars
                child.state_eqs = native.state_eqs
                child.algebraic_vars = native.algebraic_vars
                child.algebraic_eqs = native.algebraic_eqs
                child.diff_vars = list(Var("d" + variable.name + "_dt", base_var=variable)
                                       for variable in child.state_vars)
                child.init_eqs.update(native.init_eqs)
                child.post_init_seed_eqs.update(native.post_init_seed_eqs)
                count += 1
    return count


def construct_native_dgs_equipment(
        plan: NativeDgsEquipmentPlan,
        host: DynamicDevice,
        dgs_circuit: DgsCircuit,
        system_base_mva: float,
        frequency_hz: float,
        machine_parameters: DgsElmSymMachineParameters | None = None,
) -> Block:
    """Resolve physical values and invoke an independent native block builder.

    :param plan: Exact native equipment requirement from the detection phase.
    :param host: Already imported physical device matching the source FID.
    :param dgs_circuit: Source data for SVC-specific physical parameters.
    :param system_base_mva: Circuit power base in MVA.
    :param frequency_hz: Circuit nominal frequency in Hz.
    :param machine_parameters: Exact ElmSym/TypSym values when required.
    :return: Fully configured equipment-only RMS block.
    """
    if plan.kind == NativeDgsEquipmentKind.MonopolarVsc and isinstance(host, VSC):
        return build_dgs_elmvscmono_block(
            system_base_mva, float(host.rate), float(host.bus_to.Vnom), float(host.bus_from.Vnom),
            float(host.dc_voltage_base), float(host.r_series), float(host.x_series))
    elif plan.kind == NativeDgsEquipmentKind.BipolarVsc and isinstance(host, VSC):
        if host.bus_dc_n is None or float(host.rate) <= 0.0:
            raise ValueError("Native three-terminal VSC requires two DC poles and a positive rating")
        elif plan.converter_type == PowerFactoryVscType.TwoLevel:
            equipment = build_dgs_elmvsc_two_level_block(
                system_base_mva, float(host.rate), float(host.bus_to.Vnom), float(host.bus_from.Vnom),
                float(host.bus_dc_n.Vnom), float(host.r_series), float(host.x_series),
                float(host.alpha1), float(host.alpha2),
                max(0.0, float(host.alpha3) - float(host.r_series) * system_base_mva / float(host.rate)))
        elif plan.converter_type in (PowerFactoryVscType.HalfBridgeMmc, PowerFactoryVscType.FullBridgeMmc):
            if host.mmc_consider_arm_reactor_dc:
                raise ValueError("Native MMC does not support the DC-side arm-reactor option")
            else:
                equipment = build_dgs_elmvsc_block(
                    system_base_mva, float(host.rate), float(host.bus_to.Vnom), float(host.bus_from.Vnom),
                    float(host.bus_dc_n.Vnom), float(host.dc_voltage_base), float(host.mmc_arm_capacitance_uf),
                    float(host.r_series), float(host.x_series), float(host.alpha1), float(host.alpha2), float(host.alpha3))
        else:
            raise ValueError("Native ElmVsc construction requires its detected converter topology")
        # Complete the VSC realization before entering another equipment family.
        inputs: set[str] = set(plan.entry.get_connected_signal_components(DgsSlotSignalDirection.Input))
        if {'Pmd', 'Pmq', 'cosref', 'sinref'}.issubset(inputs):
            equipment = add_native_vsc_dq_interface(equipment, system_base_mva, float(host.rate))
        else:
            pass
        return equipment
    elif plan.kind == NativeDgsEquipmentKind.StaticGenerator and isinstance(host, (Generator, StaticGenerator)):
        sources = [source for source in dgs_circuit.elmgenstats
                   if str(source.ID).lstrip('#') == str(plan.entry.element_id).lstrip('#')]
        if len(sources) != 1:
            raise ValueError("Native ElmGenstat requires one exact source row")
        source = sources[0]
        equipment_base = float(host.Snom) if isinstance(host, Generator) else float(source.sgn)
        if source.iSimModel not in (None, 0, 1, 2) or source.ip_ctrl == 1:
            raise ValueError(f"Unsupported native ElmGenstat RMS model: iSimModel={source.iSimModel}, ip_ctrl={source.ip_ctrl}")
        commands = set(plan.entry.get_connected_signal_components(DgsSlotSignalDirection.Input))
        voltage_commands = commands & {'u1r_in', 'u1i_in'}
        # "According to connected input signals": connected current references select the
        # current source, which ignores cabled voltage references (TechRef Static Generator, section 6)
        current_commands = commands & {'id_ref', 'iq_ref'}
        voltage_source = source.iSimModel == 2 or (source.iSimModel == 0 and bool(voltage_commands)
                                                   and not current_commands)
        if voltage_source:
            if source.iSimModel == 0 and voltage_commands != {'u1r_in', 'u1i_in'}:
                raise ValueError("Ambiguous automatic ElmGenstat voltage/current input selection")
            if source.uk is None or source.Pcu is None:
                raise ValueError("ElmGenstat voltage source requires exported uk and Pcu")
            block = build_dgs_elmgenstat_voltage_source_block(
                system_base_mva, equipment_base, source.uk, source.Pcu)
            return apply_genstat_voltage_protection(block, source.umin or 0., source.uonthr, source.Tondelay)
        commands = set(plan.entry.get_connected_signal_components(DgsSlotSignalDirection.Input))
        external_reference = bool(commands & {'cosref', 'sinref', 'cosphi', 'sinphi'})
        if external_reference:
            raise ValueError("Native ElmGenstat external dq-reference inputs require explicit equipment binding")
        if source.iDelay not in (None, 0, 1):
            raise ValueError(f"Unsupported native ElmGenstat iDelay={source.iDelay}")
        delay = 0.0
        if source.iDelay == 1:
            if source.Tdelay is None or not 0.0 < source.Tdelay < float('inf'):
                raise ValueError("Native ElmGenstat enabled angle delay requires a positive finite Tdelay")
            delay = source.Tdelay
        block = build_dgs_elmgenstat_block(system_base_mva, equipment_base, angle_delay_seconds=delay)
        return apply_genstat_voltage_protection(block, source.umin or 0., source.uonthr, source.Tondelay)
    elif plan.kind == NativeDgsEquipmentKind.SynchronousMachine and isinstance(host, Generator):
        if machine_parameters is None:
            raise ValueError("Native ElmSym requires exact source machine/type parameters")
        else:
            return build_dgs_elmsym_block(machine_parameters, system_base_mva, frequency_hz)
    elif plan.kind == NativeDgsEquipmentKind.StaticVarSystem:
        sources: list[ElmSvs] = list(source for source in dgs_circuit.elmsvss
                                     if str(source.ID).lstrip("#") == str(plan.entry.element_id).lstrip("#"))
        if len(sources) != 1:
            raise ValueError("Native SVC requires one exact source equipment record")
        else:
            source: ElmSvs = sources[0]
            return build_dgs_elmsvs_block(system_base_mva, float(source.tcrmax), float(source.qmin),
                                          float(source.Qfixcap), float(source.nxcap), float(source.nfixcap))
    else:
        raise ValueError(f"Native equipment {plan.kind.name} does not match its imported host")


def _equipment_signal_aliases(equipment: Block) -> dict[str, Var]:
    """Expose supported native slot labels without changing physical identities.

    :param equipment: Newly constructed physical block.
    :return: Canonical labels plus explicit documented private aliases.
    """
    signals: dict[str, Var] = _local_signal_lookup(equipment)
    aliases: tuple[tuple[str, str], ...] = (
        ("cosphi", "cosref"), ("sinphi", "sinref"), ("yUcell", "Ucap"), ("idc", "iDC"),
        ("VT", "Vm"), ("ut", "Vm"), ("ie", "IFDIEEE"), ("pgt", "RPOWER"),
        ("cur1r", "ID"), ("cur1i", "IQ"), ("sgnn", "SG"), ("SN", "SG"),
        ("xspeed", "speed"), ("utr", "VTD"), ("uti", "VTQ"), ("TD0S", "Td0_prime"),
        ("Td0s", "Td0_prime"), ("ve_rated", "VFDrated"), ("EFD", "ve"), ("PT", "pt"),
        ("idref", "id_ref"), ("iqref", "iq_ref"),
        ("Vt", "Vm"), ("u", "Vm"), ("ur", "Vt_r"), ("ui", "Vt_i"),
        ("ir", "It_r"), ("ii", "It_i"), ("ysvs", "bsvs"),
    )
    alias: str
    canonical: str
    for alias, canonical in aliases:
        variable: Var | None = signals.get(canonical, None)
        if variable is not None:
            signals[alias] = variable
        else:
            pass
    return signals


def _required_command_names(plan: NativeDgsEquipmentPlan) -> tuple[str, ...]:
    """Return physical command inputs which must have exact producers.

    :param plan: Native equipment family and source topology.
    :return: Required signal labels in the physical builder contract.
    """
    if plan.kind == NativeDgsEquipmentKind.MonopolarVsc:
        return ("Pmd", "Pmq", "cosref", "sinref")
    elif plan.kind == NativeDgsEquipmentKind.BipolarVsc:
        inputs = set(plan.entry.get_connected_signal_components(DgsSlotSignalDirection.Input))
        if {'Pmd', 'Pmq', 'cosref', 'sinref'}.issubset(inputs):
            commands = ('Pmd', 'Pmq', 'cosref', 'sinref')
            return commands if plan.converter_type == PowerFactoryVscType.TwoLevel else commands + ('mdc',)
        if plan.converter_type == PowerFactoryVscType.TwoLevel:
            return ("Pmr", "Pmi")
        else:
            return ("Pmr", "Pmi", "mdc")
    elif plan.kind == NativeDgsEquipmentKind.SynchronousMachine:
        return ("pt", "ve")
    elif plan.kind == NativeDgsEquipmentKind.StaticGenerator:
        if plan.static_source_model == NativeDgsStaticSourceModel.Voltage:
            return ("u1r_in", "u1i_in")
        else:
            return ("id_ref", "iq_ref")
    else:
        return ("bsvs",)


def _declared_producer(direct_result: DgsDirectRootBuildResult, signal_name: str) -> Var | None:
    """Resolve a declared direct-slot output when an export omits its cable row.

    :param direct_result: Exact slot-to-controller lookup.
    :param signal_name: Canonical native command label.
    :return: Unique producer, or None when no source was declared.
    """
    candidates: dict[int, Var] = dict()
    aliases: dict[str, tuple[str, ...]] = dict((
        ("cosref", ("cosref", "cosphi")), ("sinref", ("sinref", "sinphi")),
        ("ve", ("ve", "EFD", "efd", "Vf")), ("pt", ("pt", "PT")),
    ))
    accepted_labels: tuple[str, ...] = aliases.get(signal_name, (signal_name,))
    entry: ElmCompInstanceEntry
    for entry in direct_result.direct_entries:
        child: Block | None = direct_result.child_block_by_slot_id.get(entry.slot_id, None)
        if child is None:
            pass
        else:
            labels: list[str] = entry.get_slot_signal_components(DgsSlotSignalDirection.Output)
            for index, label in enumerate(labels):
                if label in accepted_labels and index < len(child.out_vars):
                    candidate: Var = child.out_vars[index]
                    candidates[candidate.uid] = candidate
                else:
                    pass
    if len(candidates) == 1:
        return next(iter(candidates.values()))
    elif len(candidates) == 0:
        return None
    else:
        raise ValueError(f"Ambiguous native command producer {signal_name}")


def _remove_equipment_owned_control_aliases(control: Block, equipment: Block) -> None:
    """Give physical outputs one runtime owner and authoritative startup seeds.

    :param control: Controller hierarchy after exact cable substitution.
    :param equipment: Physical equation owner surrounding the controller.
    :return: None.
    """
    owned: set[int] = set(variable.uid for variable in equipment.algebraic_vars)
    owned.update(variable.uid for variable in equipment.state_vars)
    owned.update(variable.uid for variable in equipment.parameters)
    # A meter may expose a voltage magnitude as an algebraic output. After
    # binding it to the physical terminal input, the bus owns that variable;
    # retaining the meter's output equation would internalize the bus voltage.
    owned.update(variable.uid for variable in equipment.in_vars
                 if variable.ref is not None
                 and equipment.external_mapping.get(variable.ref) is variable)
    seeded: set[int] = set(variable.uid for variable in equipment.init_eqs)
    child: Block
    for child in control.get_all_blocks():
        child.algebraic_vars = list(variable for variable in child.algebraic_vars if variable.uid not in owned)
        child.algebraic_eqs = list(equation for equation in child.algebraic_eqs
                                   if not (isinstance(equation, BinOp) and isinstance(equation.left, Var)
                                           and equation.left.uid in owned))
        child.state_eqs = list(equation for variable, equation in zip(child.state_vars, child.state_eqs)
                               if variable.uid not in owned)
        child.state_vars = list(variable for variable in child.state_vars if variable.uid not in owned)
        child.parameters = dict((variable, expression) for variable, expression in child.parameters.items()
                                if variable.uid not in owned)
        child.event_dict = dict((variable, expression) for variable, expression in child.event_dict.items()
                                if variable.uid not in owned)
        child.mode_dict = dict((variable, expression) for variable, expression in child.mode_dict.items()
                               if variable.uid not in owned)
        child.init_eqs = dict((variable, expression) for variable, expression in child.init_eqs.items()
                              if variable.uid not in seeded)
        child.post_init_seed_eqs = dict((variable, expression) for variable, expression in child.post_init_seed_eqs.items()
                                        if variable.uid not in seeded)


def _slot_input_variables(entry: ElmCompInstanceEntry, child: Block, connector: int) -> list[Var]:
    """Resolve a declared receiver even when the parser internalized its seed.

    :param entry: Exact source slot owning the consumer.
    :param child: Corresponding controller instance, never an unrelated tree.
    :param connector: Exported graphical connector ordinal.
    :return: Scalar variables in the selected slot group.
    """
    groups: list[list[str]] = entry.get_slot_signal_groups(DgsSlotSignalDirection.Input)
    if not 0 <= connector < len(groups):
        return list()
    else:
        indices: list[int] = _resolve_direct_slot_runtime_input_indices(entry, child, connector)
        if len(indices) == len(groups[connector]):
            return list(child.in_vars[index] for index in indices)
        else:
            signals: dict[str, Var] = _local_signal_lookup(child)
            result: list[Var] = list()
            matching_count: int = sum(label in signals for label in groups[connector])
            if 0 < matching_count < len(groups[connector]):
                raise ValueError(f"Partially unresolved native vector connector on slot {entry.slot_id}")
            else:
                pass
            for label in groups[connector]:
                variable: Var | None = signals.get(label, None)
                if variable is None:
                    return list()
                else:
                    result.append(variable)
            return result


def _native_vsc_holds_initial_modulation(plan: NativeDgsEquipmentPlan,
                                        circuit: DgsCircuit) -> bool:
    """PF2024 PWM section 5.5: current references with i_ctrl=0 hold modulation.

    Require the exact exported selector and connected current-reference pair.
    Missing source rows or selector data cannot establish this default.
    """
    if plan.kind != NativeDgsEquipmentKind.MonopolarVsc:
        return False
    sources = [source for source in circuit.elmvscmonos
               if str(source.ID).lstrip('#') == str(plan.entry.element_id).lstrip('#')]
    inputs = set(plan.entry.get_connected_signal_components(DgsSlotSignalDirection.Input))
    return (len(sources) == 1 and sources[0].i_ctrl == 0
            and {'id_ref', 'iq_ref'}.issubset(inputs)
            and not inputs.intersection({'Pmd', 'Pmq', 'Pmr', 'Pmi', 'Pm_in'}))


def assemble_native_dgs_model(
        plan: NativeDgsEquipmentPlan,
        equipment: Block,
        direct_result: DgsDirectRootBuildResult,
        dgs_circuit: DgsCircuit,
        logger: Logger,
        controller_scope: Block | None = None,
) -> Block:
    """Connect native equipment by exact BlkSig endpoints and slot port ordinals.

    :param plan: Native slot being implemented.
    :param equipment: Fully configured physical block from its builder.
    :param direct_result: Imported controller with exact direct-slot relations.
    :param dgs_circuit: Authoritative graphical cable records.
    :param logger: Import diagnostic sink.
    :param controller_scope: All partition controls receiving native output substitutions.
    :return: Final physical equipment and controller hierarchy.
    """
    control: Block = direct_result.root_block
    signals: dict[str, Var] = _equipment_signal_aliases(equipment)
    entries: dict[str, ElmCompInstanceEntry] = dict((entry.slot_id, entry) for entry in direct_result.direct_entries
                                                  if entry.slot_id is not None)
    commands: set[int] = set()
    control_substitutions: dict[Var, Var] = dict()
    equipment_substitutions: dict[Var, Var] = dict()
    # A converter reference can arrive through a scoped From/Goto route.
    # Resolve those exact producer ports before matching executable child pins.
    frame_ids = {slot.fold_id for slot in dgs_circuit.blkslots
                 if slot.ID == plan.entry.slot_id and slot.fold_id}
    routing = None
    if (plan.kind in (NativeDgsEquipmentKind.MonopolarVsc, NativeDgsEquipmentKind.BipolarVsc)
            and len(frame_ids) == 1):
        routing = DgsGraphicalRoutingResolver(
            dgs_circuit, next(iter(frame_ids)), [], set(entries))
    # Resolve all endpoints before substitutions change the controller interfaces.
    for source_cable in dgs_circuit.blksigs:
        cable = source_cable
        if (routing is not None
                and str(cable.pnodto).lstrip('#') == plan.entry.slot_id):
            cable = routing.resolve(cable)
        source_slot: str = str(cable.pnodfrom).lstrip("#")
        target_slot: str = str(cable.pnodto).lstrip("#")
        if source_slot == plan.entry.slot_id:
            other: ElmCompInstanceEntry | None = entries.get(target_slot, None)
            child: Block | None = direct_result.child_block_by_slot_id.get(target_slot, None)
            groups: list[list[str]] = plan.entry.get_slot_signal_groups(DgsSlotSignalDirection.Output)
            if other is None or child is None or not 0 <= int(cable.inodfrom) < len(groups):
                pass
            else:
                labels: list[str] = groups[int(cable.inodfrom)]
                target_variables: list[Var] = _slot_input_variables(other, child, int(cable.inodto))
                # The cable name lists its signals element by element, so it names a vector connector too
                cable_labels: list[str] = str(cable.loc_name).split(";")
                if len(target_variables) == len(labels):
                    for position, (label, target_variable) in enumerate(zip(labels, target_variables)):
                        physical: Var | None = signals.get(label, None)
                        if physical is None and len(cable_labels) == len(labels):
                            physical = signals.get(cable_labels[position], None)
                        else:
                            pass
                        if physical is None:
                            raise ValueError(f"Unsupported native output {label} on slot {plan.entry.slot_id}")
                        else:
                            control_substitutions[target_variable] = physical
                else:
                    # A frame can advertise unused pins absent from its actual
                    # executable BlkDef. Such a cable has no equation consumer.
                    logger.add_info(msg="Native graphical cable has no executable consumer",
                                    device=other.element_name, value=cable.ID)
        elif target_slot == plan.entry.slot_id:
            other = entries.get(source_slot, None)
            child = direct_result.child_block_by_slot_id.get(source_slot, None)
            groups = plan.entry.get_slot_signal_groups(DgsSlotSignalDirection.Input)
            if other is None or child is None or not 0 <= int(cable.inodto) < len(groups):
                pass
            else:
                labels = groups[int(cable.inodto)]
                cable_labels = str(cable.loc_name).split(";")
                consumed: list[Var | None] = list(
                    signals.get(label, signals.get(cable_labels[position], None) if len(cable_labels) == len(labels)
                                else None) for position, label in enumerate(labels))
                indices = _resolve_direct_slot_runtime_output_indices(other, child, int(cable.inodfrom))
                if all(physical is None for physical in consumed):
                    # A port no physical implementation consumes needs no producer: the current
                    # source ignores cabled voltage references (TechRef Static Generator, section 6)
                    logger.add_info(msg="Native auxiliary command is outside the physical contract",
                                    device=plan.entry.element_name, value=str(cable.loc_name))
                elif len(indices) == len(labels):
                    for label, index, physical in zip(labels, indices, consumed):
                        if physical is None:
                            # Preserve the current supported equipment contract:
                            # some native frames advertise auxiliary commands
                            # which neither physical implementation consumes.
                            logger.add_info(msg="Native auxiliary command is outside the physical contract",
                                            device=plan.entry.element_name, value=label)
                        else:
                            equipment_substitutions[physical] = child.out_vars[index]
                            commands.add(physical.uid)
                else:
                    raise ValueError(f"Unresolved native command cable {cable.ID}")
        else:
            pass
    # Older exports may declare a direct scalar relation without BlkSig records.
    required_commands = (_required_command_names(plan) if plan.kind != NativeDgsEquipmentKind.StaticGenerator
                         else tuple(variable.name for variable in equipment.in_vars if variable.ref is None))
    for command_name in required_commands:
        command: Var = signals[command_name]
        if command.uid in commands:
            pass
        else:
            producer: Var | None = _declared_producer(direct_result, command_name)
            if producer is None:
                # PF2024 ElmSym reference, section 6.1.2.7: a generator
                # without mechanical inputs initializes pt from equilibrium.
                # Require an exact cable from a resolved, explicitly empty
                # governor slot; broken/missing references are not defaults.
                empty_governor = any(
                    entry.slot_reference_is_resolved and entry.element_id is None
                    and entry.slot_index is not None
                    and bool(set(entry.get_slot_signal_components(DgsSlotSignalDirection.Output)) & {'pt', 'PT'})
                    and any(str(cable.pnodfrom).lstrip('#') == entry.slot_id
                            and str(cable.pnodto).lstrip('#') == plan.entry.slot_id
                            for cable in dgs_circuit.blksigs)
                    for entry in direct_result.direct_entries)
                sources = [source for source in dgs_circuit.elmsyms
                           if str(source.ID).lstrip('#') == str(plan.entry.element_id).lstrip('#')]
                if (command_name in ('Pmd', 'Pmq')
                        and _native_vsc_holds_initial_modulation(plan, dgs_circuit)
                        and command in equipment.init_eqs):
                    equipment.event_dict[command] = equipment.init_eqs[command]
                    commands.add(command.uid)
                    logger.add_info(
                        msg="Native VSC modulation held at initialized value (integrated controller disabled)",
                        device=plan.entry.element_name, value=command_name)
                elif (plan.kind == NativeDgsEquipmentKind.SynchronousMachine
                        and command_name == 'pt' and empty_governor
                        # Motor mode too: a synchronous condenser (GB i_mot=1) keeps its
                        # initialized mechanical input when the governor slot is empty
                        and len(sources) == 1 and sources[0].i_mot in (0, 1)
                        and 'xmdm' not in plan.entry.get_connected_signal_components(DgsSlotSignalDirection.Input)
                        and command in equipment.init_eqs):
                    equipment.event_dict[command] = equipment.init_eqs[command]
                    commands.add(command.uid)
                else:
                    raise ValueError(f"No exact producer for native command {command_name}")
            else:
                equipment_substitutions[command] = producer
                commands.add(command.uid)
    # Measurement construction has already resolved terminal semantics. Bind only
    # its exposed typed inputs to the corresponding physical terminal identities.
    produced_uids: set[int] = set(variable.uid for child in control.get_all_blocks() for variable in child.out_vars)
    for child in control.get_all_blocks():
        for variable in child.in_vars:
            physical = equipment.external_mapping.get(variable.ref, None)
            if physical is not None and variable.uid not in produced_uids:
                control_substitutions[variable] = physical
            else:
                pass
    scope: Block = control if controller_scope is None else controller_scope
    scope.update_model_bulk(control_substitutions)
    equipment_substitutions = dict((target, control_substitutions.get(source, source))
                                    for target, source in equipment_substitutions.items())
    equipment.update_model_bulk(equipment_substitutions)
    _remove_equipment_owned_control_aliases(scope, equipment)
    protected_count: int = construct_protected_native_dgs_blocks(control)
    equipment.children = list((control,))
    equipment.name = control.name
    internal_uids: set[int] = set()
    for child in equipment.get_all_blocks():
        for collection in (child.state_vars, child.algebraic_vars, child.parameters.keys(), child.event_dict.keys()):
            internal_uids.update(variable.uid for variable in collection)
    external_inputs: list[Var] = list(variable for variable in equipment.in_vars if variable.uid not in internal_uids)
    known_inputs: set[int] = set(variable.uid for variable in external_inputs)
    for variable in control.in_vars:
        if variable.uid not in known_inputs and variable.uid not in internal_uids:
            external_inputs.append(variable)
            known_inputs.add(variable.uid)
        else:
            pass
    if controller_scope is None:
        equipment.in_vars = external_inputs
    else:
        # In a partition the native equipment is drawn as a child block, so
        # command ports remain visible for local and interconnection cables.
        pass
    logger.add_info(msg="DGS native equipment constructed and assembled", device=plan.entry.element_name,
                    device_class=plan.entry.element_kind, value=plan.entry.element_id,
                    expected_value=f"{plan.kind.name}; protected_blocks={protected_count}")
    return equipment
