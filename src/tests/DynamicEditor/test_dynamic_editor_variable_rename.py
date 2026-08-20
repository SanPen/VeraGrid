from __future__ import annotations

import copy

from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.procedural_logic import FixedSampleLogic
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Const, Var
from VeraGridEngine.Utils.Symbolic.symbolic_io import BlockParser, BlockSaver


class _AliasPropagationEditorStub:
    """
    Minimal editor state required by alias propagation tests.
    """

    __slots__ = ("root_block", "main_block", "var_factory")

    def __init__(self,
                 root_block: Block,
                 main_block: Block,
                 var_factory: VarFactory) -> None:
        """
        Store the detached working tree and shared variable factory.

        :param root_block: Complete document working tree.
        :param main_block: Nested block currently displayed by the editor.
        :param var_factory: Shared connection registry.
        :return: None.
        """
        self.root_block: Block = root_block
        self.main_block: Block = main_block
        self.var_factory: VarFactory = var_factory


def test_connected_variable_roundtrip_restores_original_identity_on_disconnect() -> None:
    """
    Preserve stable identities and restoration metadata through save/reopen.

    :return: None.
    """
    source_factory: VarFactory = VarFactory()
    source_var: Var = source_factory.add_var(name="source_signal")
    target_var: Var = source_factory.add_var(name="target_input")
    target_original_uid: int = target_var.uid
    target_stable_uid: int = target_var.non_mutable_uid
    source_stable_uid: int = source_var.non_mutable_uid

    # Keep the target variable in both the interface and an expression. The
    # serializer must preserve the physical target object in both locations.
    block: Block = Block(
        algebraic_vars=list([target_var]),
        algebraic_eqs=list([target_var + Const(1.0)]),
        in_vars=list([target_var]),
        out_vars=list([source_var]),
        name="rename_roundtrip",
    )

    source_factory.add_connection(var_to_subs=target_var, incoming_var=source_var)
    source_var.set_name("renamed_source")
    source_factory.connect_variables_by_uid(
        var_to_subs_non_mutable_uid=source_stable_uid,
        incoming_var_uid=source_var.uid,
        incoming_var_name=source_var.name,
    )

    saver: BlockSaver = BlockSaver(var_factory=source_factory)
    saver.save_block(blk=block, main=True)

    restored_factory: VarFactory = VarFactory()
    parser: BlockParser = BlockParser(var_factory=restored_factory)
    parser.parse_consts(data=saver.get_const_to_save())
    parser.parse_vars(data=saver.get_vars_to_save())
    parser.parse_diff_vars(data=saver.get_diff_vars_to_save())
    parser.parse_connections(data=saver.get_connections_to_save())
    restored_block: Block = parser.parse_block(
        blocks_data=saver.get_blocks(),
        main_block_uid=block.uid,
    )

    restored_source: Var = restored_factory.get_vars_dict()[source_stable_uid]
    restored_target: Var = restored_factory.get_vars_dict()[target_stable_uid]

    assert restored_source.non_mutable_uid == source_stable_uid
    assert restored_target.non_mutable_uid == target_stable_uid
    assert restored_target.uid == restored_source.uid
    assert restored_target.name == "renamed_source"
    assert restored_block.in_vars[0] is restored_target
    assert restored_block.out_vars[0] is restored_source

    restored_equation: BinOp = restored_block.algebraic_eqs[0]
    assert isinstance(restored_equation, BinOp)
    assert restored_equation.left is restored_target

    # The saved Connection record must still address the physical target after
    # reload and restore its exact pre-connection identity.
    restored_factory.remove_connection(
        var_to_disconnect=restored_target,
        outgoing_var=restored_source,
    )

    assert restored_target.uid == target_original_uid
    assert restored_target.name == "target_input"
    assert restored_source.name == "renamed_source"


def test_legacy_mutable_uid_resolves_vars_and_diff_var_base() -> None:
    """
    Load legacy properties and differential bases stored by mutable UID.

    :return: None.
    """
    var_factory: VarFactory = VarFactory()
    variable_uid: int = 101
    variable_stable_uid: int = 201
    diff_var_uid: int = 102
    diff_var_stable_uid: int = 202

    var_factory.parse_var_dict(data_list=list([
        dict({
            "type": "Var",
            "name": "legacy_base",
            "uid": variable_uid,
            "non_mutable_uid": variable_stable_uid,
            "shared_ref": None,
            "ref": None,
        })
    ]))
    var_factory.parse_diff_var_dict(data_list=list([
        dict({
            "type": "DiffVar",
            "name": "legacy_diff",
            "uid": diff_var_uid,
            "non_mutable_uid": diff_var_stable_uid,
            "base_var": variable_uid,
            "shared_ref": None,
            "ref": None,
        })
    ]))

    restored_base: Var = var_factory.get_vars_dict()[variable_stable_uid]
    restored_diff: Var = var_factory.get_diff_var_dict()[diff_var_stable_uid]

    # Device VarType properties in old files still use the mutable value.
    assert var_factory.get_var(variable_uid) is restored_base
    assert var_factory.get_diff_var(diff_var_uid) is restored_diff
    assert restored_diff.base_var is restored_base
    assert restored_base.non_mutable_uid == variable_stable_uid
    assert restored_diff.non_mutable_uid == diff_var_stable_uid


def test_nested_editor_alias_propagation_updates_complete_root_tree() -> None:
    """
    Propagate a nested target edit from the canonical source across root state.

    :return: None.
    """
    var_factory: VarFactory = VarFactory()
    source_var: Var = var_factory.add_var(name="source_signal")
    target_var: Var = var_factory.add_var(name="nested_target")
    target_initial_uid: int = target_var.uid

    nested_block: Block = Block(
        algebraic_vars=list([target_var]),
        algebraic_eqs=list([target_var]),
        init_eqs=dict({target_var: Const(0.0)}),
        procedural_logic=list([
            FixedSampleLogic(
                output_var_name="nested_target",
                condition_expr=target_var > Const(0.0),
            )
        ]),
        name="nested_block",
    )
    source_root: Block = Block(
        out_vars=list([source_var]),
        children=list([nested_block]),
        name="root_block",
    )

    # The editor document owns detached variables, while VarFactory receives
    # the live connection and changes only its canonical registered objects.
    working_root: Block = copy.deepcopy(source_root)
    working_nested: Block = working_root.children[0]
    working_target: Var = working_nested.algebraic_vars[0]
    var_factory.add_connection(var_to_subs=target_var, incoming_var=source_var)

    editor_stub: _AliasPropagationEditorStub = _AliasPropagationEditorStub(
        root_block=working_root,
        main_block=working_nested,
        var_factory=var_factory,
    )
    DynamicBlockEditorGUI._propagate_alias_to_working_tree(
        editor_stub,
        source_non_mutable_uid=working_target.non_mutable_uid,
        incoming_uid=source_var.uid,
        incoming_name=source_var.name,
    )

    assert target_initial_uid != source_var.uid
    assert working_target.uid == source_var.uid
    assert working_target.name == "source_signal"
    assert working_target in working_nested.init_eqs
    assert working_nested.var_mapping["source_signal"] is working_target
    assert "nested_target" not in working_nested.var_mapping

    restored_logic: FixedSampleLogic = working_nested.procedural_logic[0]
    assert isinstance(restored_logic, FixedSampleLogic)
    assert restored_logic.output_var_name == "source_signal"


def test_alias_chain_rename_and_disconnect_restore_each_connection_boundary() -> None:
    """
    Restore saved names correctly across a signal-pair-style alias chain.

    :return: None.
    """
    var_factory: VarFactory = VarFactory()
    upstream_var: Var = var_factory.add_var(name="upstream")
    signal_pair_var: Var = var_factory.add_var(name="signal_pair")
    consumer_var: Var = var_factory.add_var(name="consumer_input")
    signal_pair_original_uid: int = signal_pair_var.uid
    consumer_original_uid: int = consumer_var.uid

    # Model the symbolic path upstream -> From/To canonical variable ->
    # downstream consumer using the same directional records as the editor.
    var_factory.add_connection(var_to_subs=signal_pair_var,
                               incoming_var=upstream_var)
    var_factory.add_connection(var_to_subs=consumer_var,
                               incoming_var=signal_pair_var)

    canonical_source_uid: int = var_factory.get_connection_source_non_mutable_uid(
        variable_non_mutable_uid=consumer_var.non_mutable_uid,
    )
    assert canonical_source_uid == upstream_var.non_mutable_uid

    upstream_var.set_name("renamed_network")
    var_factory.connect_variables_by_uid(
        var_to_subs_non_mutable_uid=canonical_source_uid,
        incoming_var_uid=upstream_var.uid,
        incoming_var_name=upstream_var.name,
    )

    assert signal_pair_var.name == "renamed_network"
    assert consumer_var.name == "renamed_network"

    # Detaching the upstream wire restores the signal pair's pre-connection
    # identity and propagates that boundary identity to its active consumer.
    var_factory.remove_connection(var_to_disconnect=signal_pair_var,
                                  outgoing_var=upstream_var)
    assert signal_pair_var.uid == signal_pair_original_uid
    assert signal_pair_var.name == "signal_pair"
    assert consumer_var.uid == signal_pair_original_uid
    assert consumer_var.name == "signal_pair"

    # Detaching the downstream wire then restores the consumer's own original
    # identity rather than the signal pair's or upstream network's label.
    var_factory.remove_connection(var_to_disconnect=consumer_var,
                                  outgoing_var=signal_pair_var)
    assert consumer_var.uid == consumer_original_uid
    assert consumer_var.name == "consumer_input"
