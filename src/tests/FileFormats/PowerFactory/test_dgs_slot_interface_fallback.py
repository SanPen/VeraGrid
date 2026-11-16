# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Use exact model interfaces when a dynamic slot omits its port declarations."""
from __future__ import annotations

from pathlib import Path

import pytest

from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import BlkDef, BlkSig, BlkSlot, ElmComp, ElmDsl
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    DgsDirectRootBuildResult, DgsRootBlockResult, DgsSlotSignalDirection,
    build_dgs_root_block_from_circuit, build_direct_root_elmcomp_block,
    parse_dgs_block_definitions_from_circuit,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var


def source_with_empty_slots() -> DgsCircuit:
    """Create a wired input after an unwired initialized private input.

    :return: Complete source with no explicit slot interfaces.
    """
    source: DgsCircuit = DgsCircuit()
    frame: BlkDef = BlkDef()
    frame.ID = 'frame'
    frame.loc_name = 'frame'
    source.blkdefs.append(frame)
    root: ElmComp = ElmComp()
    root.ID = 'root'
    root.loc_name = 'Example'
    root.typ_id = 'frame'
    root.pblk = list(('source_slot', 'target_slot'))
    root.pelm = list(('source_instance', 'target_instance'))
    source.elmcomps.append(root)
    identifier: str
    inputs: list[str]
    outputs: list[str]
    equations: list[str]
    for identifier, inputs, outputs, equations in (
        ('source', list(('setpoint',)), list(('out',)), list(('inc(setpoint)=3', 'out=2*setpoint'))),
        ('target', list(('held', 'signal')), list(('result',)),
         list(('inc(held)=5', 'inc(signal)=6', 'result=held+signal'))),
    ):
        definition: BlkDef = BlkDef()
        definition.ID = identifier
        definition.loc_name = identifier
        definition.inputs = inputs
        definition.outputs = outputs
        definition.equations_raw = equations
        source.blkdefs.append(definition)
        instance: ElmDsl = ElmDsl()
        instance.ID = f'{identifier}_instance'
        instance.loc_name = identifier
        instance.typ_id = identifier
        instance.fold_id = root.ID
        source.elmdsls.append(instance)
        slot: BlkSlot = BlkSlot()
        slot.ID = f'{identifier}_slot'
        slot.loc_name = identifier
        slot.filtmod = 'ElmDsl*'
        source.blkslots.append(slot)
    cable: BlkSig = BlkSig()
    cable.ID = 'wire'
    cable.pnodfrom = 'source_slot'
    cable.pnodto = 'target_slot'
    cable.inodfrom = 0
    cable.inodto = 1
    cable.iconfrom = 2
    cable.iconto = 1
    cable.loc_name = 'different_public_alias'
    source.blksigs.append(cable)
    return source


def materialize(source: DgsCircuit) -> DgsDirectRootBuildResult:
    """Build using the normal direct composite import path.

    :param source: DGS source under test.
    :return: Executable graph and exact slot relations.
    """
    root: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        source, parse_dgs_block_definitions_from_circuit(source), 'Example', root_dgs_id='root')
    return build_direct_root_elmcomp_block(source, root)


def test_missing_slot_ports_use_definition_order_and_keep_private_setpoints() -> None:
    """Connect by declared model ordinal without holding a live initialized input.

    :return: None.
    """
    source: DgsCircuit = source_with_empty_slots()
    result: DgsDirectRootBuildResult = materialize(source)
    producer: Block = result.child_block_by_slot_id['source_slot']
    consumer: Block = result.child_block_by_slot_id['target_slot']
    assert consumer.in_vars == list((producer.out_vars[0],))
    assert producer.in_vars == list()
    assert producer.out_vars[0] not in consumer.event_dict
    assert any(variable.name == 'held' for variable in consumer.event_dict)
    assert not any(variable.name == 'signal' for variable in consumer.event_dict)
    assert result.direct_entries[0].slot_outputs == list()
    assert result.direct_entries[0].get_slot_signal_groups(DgsSlotSignalDirection.Output) == list((list(('out',)),))
    assert all(slot.inputs == list() and slot.outputs == list() for slot in source.blkslots)


def test_explicit_slot_subset_keeps_its_order_over_the_definition() -> None:
    """An explicit subset must never be replaced by the wider model interface.

    :return: None.
    """
    source: DgsCircuit = source_with_empty_slots()
    source.blkslots[0].outputs = list(('public_name',))
    source.blkslots[1].inputs = list(('signal',))
    source.blksigs[0].inodto = 0
    result: DgsDirectRootBuildResult = materialize(source)
    assert result.child_block_by_slot_id['target_slot'].in_vars[0] is result.child_block_by_slot_id['source_slot'].out_vars[0]
    assert result.direct_entries[1].get_slot_signal_groups(DgsSlotSignalDirection.Input) == list((list(('signal',)),))


def test_empty_output_interface_uses_the_selected_definition_output() -> None:
    """Preserve the declared output ordinal when several outputs are available.

    :return: None.
    """
    source: DgsCircuit = source_with_empty_slots()
    definition: BlkDef = next(block for block in source.blkdefs if block.ID == 'source')
    definition.outputs.insert(0, 'unused')
    definition.equations_raw.append('unused=1')
    source.blksigs[0].inodfrom = 1
    result: DgsDirectRootBuildResult = materialize(source)
    producer: Block = result.child_block_by_slot_id['source_slot']
    consumer: Block = result.child_block_by_slot_id['target_slot']
    assert consumer.in_vars[0] is producer.out_vars[1]
    assert consumer.in_vars[0].uid != producer.out_vars[0].uid


@pytest.mark.parametrize('direction, ordinal', (('input', -1), ('input', 2), ('output', -1), ('output', 1)))
def test_invalid_fallback_ordinal_is_reported(direction: str, ordinal: int) -> None:
    """A broken executable cable must not be silently skipped.

    :param direction: Endpoint to invalidate.
    :param ordinal: Out-of-range connector number.
    :return: None.
    """
    source: DgsCircuit = source_with_empty_slots()
    if direction == 'input':
        source.blksigs[0].inodto = ordinal
    else:
        source.blksigs[0].inodfrom = ordinal
    with pytest.raises(ValueError, match=f'DGS {direction} ordinal {ordinal} is outside BlkDef'):
        materialize(source)


def test_incompatible_vector_width_is_reported_for_a_missing_interface() -> None:
    """Do not guess a vector grouping absent from the source model contract.

    :return: None.
    """
    source: DgsCircuit = source_with_empty_slots()
    source.blkslots[1].inputs = list(('held;signal',))
    source.blksigs[0].inodto = 0
    with pytest.raises(ValueError, match='DGS cable wire has incompatible executable port widths: 1 -> 2'):
        materialize(source)


def test_dfig_voltage_controller_is_connected_on_both_sides() -> None:
    """Resolve cables 673 and 661 without altering the empty exported slot.

    :return: None.
    """
    path: Path = Path(__file__).resolve().parents[4] / 'trunk/dynamics/DFIG_RMS_v5_Export.dgs'
    if not path.is_file():
        pytest.skip('Local PowerFactory DFIG export is unavailable')
    else:
        pass
    source: DgsCircuit = DgsCircuit()
    source.parse_dgs(str(path))
    root: DgsRootBlockResult = build_dgs_root_block_from_circuit(
        source, parse_dgs_block_definitions_from_circuit(source), 'RMS', root_dgs_id='947')
    result: DgsDirectRootBuildResult = build_direct_root_elmcomp_block(source, root)
    controller: Block = result.child_block_by_slot_id['905']
    limiter: Block = result.child_block_by_slot_id['900']
    voltage: Block = result.child_block_by_slot_id['904']
    assert limiter.in_vars[0] is controller.out_vars[0]
    assert controller.in_vars[0] is voltage.out_vars[0]
    assert controller.in_vars[0] not in controller.event_dict
    owned: set[int] = set(variable.uid for block in result.root_block.get_all_blocks()
                          for variable in block.algebraic_vars)
    assert limiter.in_vars[0].uid in owned
