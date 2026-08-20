from __future__ import annotations

import copy
from typing import Any, Dict, List

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block, normalize_dynamic_connection_intents
from VeraGridEngine.Utils.Symbolic.dynamic_connection_intent import (DynamicConnectionIntent,
                                                                     DynamicConnectionIntentDirection,
                                                                     DynamicConnectionIntentOrigin)
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.Symbolic.symbolic_io import BlockParser, BlockSaver, duplicate_block
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


def _build_block_with_connection_intents(var_factory: VarFactory) -> Block:
    """
    Build one root block with active and suppressed typed intents.

    :param var_factory: Factory that owns the symbolic variables.
    :return: Root block prepared for intent tests.
    """
    root_input: Var = var_factory.add_var(name="root_v_A", reference=VarPowerFlowReferenceType.v_A)
    root_output: Var = var_factory.add_var(name="root_i_A", reference=VarPowerFlowReferenceType.i_A)
    internal_input: Var = var_factory.add_var(name="internal_v_A", reference=VarPowerFlowReferenceType.v_A)
    internal_output: Var = var_factory.add_var(name="internal_i_A", reference=VarPowerFlowReferenceType.i_A)
    child_block: Block = Block(name="Internal",
                               in_vars=list([internal_input]),
                               out_vars=list([internal_output]))
    root_block: Block = Block(name="Root",
                              in_vars=list([root_input]),
                              out_vars=list([root_output]),
                              children=list([child_block]))

    root_block.connection_intents = list([
        DynamicConnectionIntent(origin=DynamicConnectionIntentOrigin.USER,
                                root_reference=VarPowerFlowReferenceType.v_A,
                                direction=DynamicConnectionIntentDirection.INPUT,
                                internal_block_uid=child_block.uid,
                                internal_variable_uid=internal_input.non_mutable_uid),
        DynamicConnectionIntent(origin=DynamicConnectionIntentOrigin.TEMPLATE_DERIVED,
                                root_reference=VarPowerFlowReferenceType.i_A,
                                direction=DynamicConnectionIntentDirection.OUTPUT,
                                internal_block_uid=child_block.uid,
                                internal_variable_uid=internal_output.non_mutable_uid,
                                suppressed=True),
    ])
    return root_block


def _parse_saved_blocks(saver: BlockSaver) -> List[Block]:
    """
    Parse all symbolic collections emitted by one saver.

    :param saver: Populated block saver.
    :return: Parsed root blocks.
    """
    parsed_factory: VarFactory = VarFactory()
    parser: BlockParser = BlockParser(var_factory=parsed_factory)
    parser.parse_references(saver.get_shared_references_to_save())
    parser.parse_consts(saver.get_const_to_save())
    parser.parse_vars(saver.get_vars_to_save())
    parser.parse_diff_vars(saver.get_diff_vars_to_save())
    return parser.parse_blocks(blocks_data=saver.get_blocks(),
                               main_block_uids=saver.main_block_uids)


def test_connection_intent_normalization_keeps_only_current_state() -> None:
    """
    Verify repeated edits replace state instead of creating session history.

    :return: None.
    """
    root_block: Block = _build_block_with_connection_intents(var_factory=VarFactory())
    original_intent: DynamicConnectionIntent = root_block.connection_intents[0]
    replacement_intent: DynamicConnectionIntent = DynamicConnectionIntent(
        origin=original_intent.get_origin(),
        root_reference=original_intent.get_root_reference(),
        direction=original_intent.get_direction(),
        internal_block_uid=original_intent.get_internal_block_uid(),
        internal_variable_uid=original_intent.get_internal_variable_uid(),
        suppressed=True,
    )
    root_block.connection_intents.append(replacement_intent)

    normalize_dynamic_connection_intents(block=root_block)

    assert len(root_block.connection_intents) == 2
    assert root_block.connection_intents[0] is replacement_intent
    assert root_block.connection_intents[0].is_suppressed() is True


def test_block_saver_round_trip_preserves_typed_connection_intents() -> None:
    """
    Verify the principal .veragrid symbolic serializer preserves current intent state.

    :return: None.
    """
    source_factory: VarFactory = VarFactory()
    source_block: Block = _build_block_with_connection_intents(var_factory=source_factory)
    saver: BlockSaver = BlockSaver(var_factory=source_factory)
    saved_root: Dict[str, Any] = saver.save_block(blk=source_block, main=True)
    persisted_intents: List[Dict[str, object]] = saved_root["connection_intents"]

    assert len(persisted_intents) == 2
    assert "internal_variable_uid" in persisted_intents[0]
    assert "internal_port_index" not in persisted_intents[0]
    assert "root_direction" not in persisted_intents[0]

    parsed_blocks: List[Block] = _parse_saved_blocks(saver=saver)
    parsed_block: Block = parsed_blocks[0]
    parsed_input_intent: DynamicConnectionIntent = parsed_block.connection_intents[0]
    parsed_output_intent: DynamicConnectionIntent = parsed_block.connection_intents[1]

    assert parsed_input_intent.get_direction() == DynamicConnectionIntentDirection.INPUT
    assert parsed_input_intent.get_internal_variable_uid() == parsed_block.children[0].in_vars[0].non_mutable_uid
    assert parsed_output_intent.get_direction() == DynamicConnectionIntentDirection.OUTPUT
    assert parsed_output_intent.get_internal_variable_uid() == parsed_block.children[0].out_vars[0].non_mutable_uid
    assert parsed_output_intent.is_suppressed() is True


def test_block_saver_preserves_intent_while_root_phase_is_unavailable() -> None:
    """
    Verify a temporarily unavailable root phase remains restorable after reopening.

    :return: None.
    """
    source_factory: VarFactory = VarFactory()
    source_block: Block = _build_block_with_connection_intents(var_factory=source_factory)

    # Removing the current root port represents a topology in which phase A is
    # unavailable. The desired internal connection must remain independent of
    # that temporary graphical interface.
    source_block.in_vars = list()
    saver: BlockSaver = BlockSaver(var_factory=source_factory)
    saver.save_block(blk=source_block, main=True)

    parsed_blocks: List[Block] = _parse_saved_blocks(saver=saver)
    parsed_block: Block = parsed_blocks[0]
    parsed_intent: DynamicConnectionIntent = parsed_block.connection_intents[0]

    assert parsed_block.in_vars == list()
    assert parsed_intent.get_root_reference() == VarPowerFlowReferenceType.v_A
    assert parsed_intent.get_internal_variable_uid() == parsed_block.children[0].in_vars[0].non_mutable_uid


def test_block_parser_upgrades_legacy_port_index_intent() -> None:
    """
    Verify an old positional intent becomes one stable typed variable reference.

    :return: None.
    """
    source_factory: VarFactory = VarFactory()
    source_block: Block = _build_block_with_connection_intents(var_factory=source_factory)
    saver: BlockSaver = BlockSaver(var_factory=source_factory)
    saver.save_block(blk=source_block, main=True)
    saved_blocks: Dict[int, Dict[str, Any]] = copy.deepcopy(saver.get_blocks())
    saved_root: Dict[str, Any] = saved_blocks[source_block.uid]
    saved_root["connection_intents"] = list([dict({
        "origin": DynamicConnectionIntentOrigin.USER.value,
        "root_ref": VarPowerFlowReferenceType.v_A.value,
        "root_direction": "output",
        "internal_block_uid": source_block.children[0].uid,
        "internal_port_direction": "input",
        "internal_port_index": 0,
        "suppressed": False,
    })])

    parsed_factory: VarFactory = VarFactory()
    parser: BlockParser = BlockParser(var_factory=parsed_factory)
    parser.parse_references(saver.get_shared_references_to_save())
    parser.parse_consts(saver.get_const_to_save())
    parser.parse_vars(saver.get_vars_to_save())
    parser.parse_diff_vars(saver.get_diff_vars_to_save())
    parsed_blocks: List[Block] = parser.parse_blocks(blocks_data=saved_blocks,
                                                     main_block_uids=saver.main_block_uids)
    parsed_block: Block = parsed_blocks[0]
    parsed_intent: DynamicConnectionIntent = parsed_block.connection_intents[0]

    assert parsed_intent.get_direction() == DynamicConnectionIntentDirection.INPUT
    assert parsed_intent.get_internal_variable_uid() == parsed_block.children[0].in_vars[0].non_mutable_uid


def test_duplicate_block_remaps_connection_intent_identities() -> None:
    """
    Verify duplication targets the cloned block and cloned variable identities.

    :return: None.
    """
    source_block: Block = _build_block_with_connection_intents(var_factory=VarFactory())
    duplicated_block: Block = duplicate_block(block=source_block, var_factory=VarFactory())
    duplicated_input_intent: DynamicConnectionIntent = duplicated_block.connection_intents[0]

    assert duplicated_block.children[0].uid != source_block.children[0].uid
    assert duplicated_input_intent.get_internal_block_uid() == duplicated_block.children[0].uid
    assert duplicated_input_intent.get_internal_variable_uid() == duplicated_block.children[0].in_vars[0].non_mutable_uid
    assert duplicated_input_intent.get_internal_variable_uid() != source_block.children[0].in_vars[0].non_mutable_uid


def test_block_deep_copy_preserves_detached_typed_intents() -> None:
    """
    Verify an ordinary block copy owns detached intent objects with equal state.

    :return: None.
    """
    source_block: Block = _build_block_with_connection_intents(var_factory=VarFactory())
    copied_block: Block = source_block.copy()
    source_intent: DynamicConnectionIntent = source_block.connection_intents[0]
    copied_intent: DynamicConnectionIntent = copied_block.connection_intents[0]

    assert copied_intent is not source_intent
    assert copied_intent.has_same_identity(source_intent)
    assert copied_intent.is_suppressed() == source_intent.is_suppressed()


def test_alternate_block_dict_round_trip_preserves_typed_intents() -> None:
    """
    Verify the alternate Block dictionary path uses the same typed intent schema.

    :return: None.
    """
    source_block: Block = _build_block_with_connection_intents(var_factory=VarFactory())
    parsed_block: Block = Block.parse(data=source_block.to_dict())

    assert len(parsed_block.connection_intents) == 2
    assert parsed_block.connection_intents[0].get_direction() == DynamicConnectionIntentDirection.INPUT
    assert parsed_block.connection_intents[1].is_suppressed() is True
