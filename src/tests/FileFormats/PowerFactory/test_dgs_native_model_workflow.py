# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Independent detection, physical construction and exact-slot RMS assembly."""

import pytest

from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import ElmGenstat
from VeraGridEngine.IO.dgs.dgs_to_blocks import DgsDirectRootBuildResult, ElmCompInstanceEntry
from VeraGridEngine.IO.dgs.dynamic_models.dgs_adapter_block_from_native_dgs import (
    build_dgs_elmgenstat_block, build_dgs_elmvsc_block, build_dgs_elmvscmono_block,
    build_dgs_elmsym_block, build_dgs_elmsvs_block, build_dgs_regc_voltage_source_block,
)
from VeraGridEngine.IO.dgs.dynamic_models.dgs_native_model_workflow import (
    NativeDgsEquipmentKind, NativeDgsEquipmentPlan,
    assemble_native_dgs_model, construct_native_dgs_equipment,
    construct_protected_native_dgs_blocks, detect_native_dgs_equipment,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from tests.FileFormats.PowerFactory.test_dgs_adapter_block_from_native_dgs import _machine_parameters


def _entry(slot_id: str, kind: str, inputs: list[str], outputs: list[str]) -> ElmCompInstanceEntry:
    """Describe one exact source slot with complete source-reference evidence.

    :param slot_id: Unique slot FID.
    :param kind: Source DGS element class.
    :param inputs: Declared scalar consumer labels.
    :param outputs: Declared scalar producer labels.
    :return: Resolved direct relation.
    """
    return ElmCompInstanceEntry(
        slot_id=slot_id, slot_name=slot_id, element_id=slot_id, element_name=slot_id,
        element_kind=kind, element_outserv=0, type_id=None, type_name=None,
        slot_inputs=inputs, slot_outputs=outputs,
        slot_reference_is_resolved=True, element_reference_is_resolved=True)


@pytest.mark.parametrize("kind", tuple(NativeDgsEquipmentKind))
def test_detection_uses_native_slot_identity_and_does_not_mutate_control(kind: NativeDgsEquipmentKind) -> None:
    """Recognize supported source equipment without relying on signal spellings.

    :param kind: Native equipment family.
    :return: None.
    """
    control: Block = Block(name="Control")
    source: ElmCompInstanceEntry = _entry("equipment", kind.value, list(), list())
    direct: DgsDirectRootBuildResult = DgsDirectRootBuildResult(
        control, dict(), dict(), list((source, _entry("meter", "StaVmea", list(), list(("u",))))))
    plans: tuple[NativeDgsEquipmentPlan, ...] = detect_native_dgs_equipment(direct)
    assert len(plans) == 1
    assert plans[0].kind == kind
    assert plans[0].entry is source
    assert len(control.children) == 0
    assert len(control.algebraic_eqs) == 0


def test_detection_rejects_ambiguous_or_unresolved_source_slots() -> None:
    """Do not silently fall back to adapters for an invalid native requirement.

    :return: None.
    """
    source: ElmCompInstanceEntry = _entry("equipment", "ElmGenstat", list(), list())
    direct: DgsDirectRootBuildResult = DgsDirectRootBuildResult(Block(), dict(), dict(), list((source, source)))
    with pytest.raises(ValueError, match="Ambiguous"):
        detect_native_dgs_equipment(direct)
    source.element_reference_is_resolved = False
    direct.direct_entries = list((source,))
    with pytest.raises(ValueError, match="resolved"):
        detect_native_dgs_equipment(direct)


@pytest.mark.parametrize("kind", tuple(NativeDgsEquipmentKind))
def test_assembly_connects_declared_commands_without_legacy_builders(kind: NativeDgsEquipmentKind) -> None:
    """Assemble all supported equipment families using new physical blocks.

    :param kind: Physical builder family.
    :return: None.
    """
    equipment: Block
    names: tuple[str, ...]
    if kind == NativeDgsEquipmentKind.MonopolarVsc:
        equipment = build_dgs_elmvscmono_block(100.0, 90.0, 230.0, 400.0, 400.0, 0.01, 0.1)
        names = ("Pmd", "Pmq", "cosref", "sinref")
    elif kind == NativeDgsEquipmentKind.BipolarVsc:
        equipment = build_dgs_elmvsc_block(100.0, 200.0, 230.0, 320.0, 320.0, 640.0, 1000.0, 0.01, 0.1)
        names = ("Pmr", "Pmi", "mdc")
    elif kind == NativeDgsEquipmentKind.SynchronousMachine:
        equipment = build_dgs_elmsym_block(_machine_parameters(True), 100.0, 50.0)
        names = ("pt", "ve")
    elif kind == NativeDgsEquipmentKind.StaticGenerator:
        equipment = build_dgs_elmgenstat_block(100.0, 50.0)
        names = ("id_ref", "iq_ref")
    else:
        equipment = build_dgs_elmsvs_block(100.0, 40.0, -20.0, 5.0, 2.0, 1.0)
        names = ("bsvs",)
    commands: list[Var] = list(Var(name) for name in names)
    controller: Block = Block(out_vars=commands, event_dict=dict((variable, Const(1.0)) for variable in commands))
    root: Block = Block(name="Final model", children=list((controller,)))
    physical_entry: ElmCompInstanceEntry = _entry("equipment", kind.value, list(names), list())
    controller_entry: ElmCompInstanceEntry = _entry("control", "ElmDsl", list(), list(names))
    direct: DgsDirectRootBuildResult = DgsDirectRootBuildResult(
        root, dict((("control", controller),)), dict(), list((physical_entry, controller_entry)))
    result: Block = assemble_native_dgs_model(
        NativeDgsEquipmentPlan(kind, physical_entry), equipment, direct, DgsCircuit(), Logger())
    assert result is equipment
    assert result.children[0] is root
    assert len(result.external_mapping) > 0
    assert all(variable not in result.in_vars for variable in commands)
    assert commands[0] in result.init_eqs


def test_physical_construction_uses_host_bases() -> None:
    """Extract the exact host ratings before invoking the native constructor.

    :return: None.
    """
    host: Generator = Generator(idtag="equipment", Snom=50.0)
    plan: NativeDgsEquipmentPlan = NativeDgsEquipmentPlan(
        NativeDgsEquipmentKind.StaticGenerator, _entry("equipment", "ElmGenstat", list(), list()))
    circuit: DgsCircuit = DgsCircuit()
    source: ElmGenstat = ElmGenstat()
    source.ID = "equipment"
    source.sgn = 50.0
    source.iSimModel = 1
    circuit.elmgenstats.append(source)
    block: Block = construct_native_dgs_equipment(plan, host, circuit, 100.0, 50.0)
    assert len(block.children) == 0
    assert len(block.in_vars) == 4
    assert len(block.algebraic_eqs) == 8


def test_protected_regc_is_constructed_on_existing_port_identities() -> None:
    """Restore the protected voltage source while preserving all existing cables.

    :return: None.
    """
    source: Block = build_dgs_regc_voltage_source_block(0.1, 0.01, 0.1)
    delay: Var = Var("Te")
    resistance: Var = Var("re")
    reactance: Var = Var("xe")
    source.event_dict = dict(((delay, Const(0.1)), (resistance, Const(0.01)), (reactance, Const(0.1))))
    original_inputs: list[Var] = list(source.in_vars)
    original_outputs: list[Var] = list(source.out_vars)
    source.state_eqs = list()
    source.algebraic_eqs = list()
    assert construct_protected_native_dgs_blocks(source) == 1
    assert source.in_vars == original_inputs
    assert source.out_vars == original_outputs
    assert len(source.state_eqs) == 2
    assert len(source.algebraic_eqs) == 2
    assert construct_protected_native_dgs_blocks(source) == 0


def test_assembly_preserves_measurement_outputs_and_their_base_conversion() -> None:
    """Do not collapse a scaled measured P onto the physical system-base P.

    :return: None.
    """
    equipment: Block = build_dgs_elmgenstat_block(100.0, 50.0)
    raw_power: Var = Var("raw", reference=VarPowerFlowReferenceType.P)
    measured_power: Var = Var("P_act", reference=VarPowerFlowReferenceType.P)
    meter: Block = Block(name="Power meter", in_vars=list((raw_power,)), out_vars=list((measured_power,)),
                         algebraic_vars=list((measured_power,)), algebraic_eqs=list((measured_power - 0.5 * raw_power,)))
    direct: Var = Var("id_ref")
    quadrature: Var = Var("iq_ref")
    control: Block = Block(in_vars=list((measured_power,)), out_vars=list((direct, quadrature)),
                           event_dict=dict(((direct, Const(0.0)), (quadrature, Const(0.0)))))
    root: Block = Block(children=list((control, meter)))
    native_entry: ElmCompInstanceEntry = _entry("native", "ElmGenstat", list(("id_ref", "iq_ref")), list())
    control_entry: ElmCompInstanceEntry = _entry("control", "ElmDsl", list(("P_act",)), list(("id_ref", "iq_ref")))
    result: DgsDirectRootBuildResult = DgsDirectRootBuildResult(
        root, dict((("control", control),)), dict(), list((native_entry, control_entry)))
    assembled: Block = assemble_native_dgs_model(
        NativeDgsEquipmentPlan(NativeDgsEquipmentKind.StaticGenerator, native_entry),
        equipment, result, DgsCircuit(), Logger())
    physical_power: Var = assembled.external_mapping[VarPowerFlowReferenceType.P]
    assert meter.in_vars[0] is physical_power
    assert control.in_vars[0] is measured_power
    assert measured_power is not physical_power
    assert meter.algebraic_eqs[0].eval_uid(dict(((physical_power.uid, 0.2), (measured_power.uid, 0.1)))) \
        == pytest.approx(0.0)
