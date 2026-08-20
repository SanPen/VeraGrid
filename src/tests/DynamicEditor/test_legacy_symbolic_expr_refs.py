from __future__ import annotations

import json
import math
from typing import Any, Dict, List

import numpy as np
import pytest

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory, build_persisted_identity_lookup
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic_io import BlockParser, BlockSaver, expr_to_dict, parse_expr, parse_expr_list


def test_shared_expression_roundtrip_preserves_expr_ref_identity() -> None:
    """
    Verify that repeated composite expressions keep one shared object after roundtrip.

    :return: None.
    """
    variable: sym.Var = sym.Var("x")
    shared_expression: sym.Expr = variable + sym.Const(1.0)
    expression: sym.Expr = shared_expression * shared_expression + sym.sin(shared_expression)
    const_dict: Dict[int, sym.Const] = dict()
    var_dict: Dict[int, sym.Var] = dict(((variable.non_mutable_uid, variable),))
    diff_var_dict: Dict[int, sym.Var] = dict()

    payload: Dict[str, Any] = expr_to_dict(
        expr=expression,
        const_dict=const_dict,
        var_dict=var_dict,
        diff_var_dict=diff_var_dict,
    )
    restored: sym.Expr = parse_expr(
        data=payload,
        const_dict=const_dict,
        var_dict=var_dict,
        diff_var_dict=diff_var_dict,
    )
    restored_payload: Dict[str, Any] = expr_to_dict(
        expr=restored,
        const_dict=const_dict,
        var_dict=var_dict,
        diff_var_dict=diff_var_dict,
    )

    assert '"ExprRef"' in json.dumps(payload)
    assert isinstance(restored, sym.BinOp)
    assert isinstance(restored.left, sym.BinOp)
    assert isinstance(restored.right, sym.Func)
    assert restored.left.left is restored.left.right
    assert restored.left.left is restored.right.arg
    assert restored_payload == payload
    assert math.isclose(restored.eval(x=2.0), expression.eval(x=2.0), rel_tol=1.0e-12)


def test_legacy_expr_ref_resolves_across_expression_list_entries() -> None:
    """
    Verify the historical backward-reference layout used by legacy archives.

    :return: None.
    """
    variable: sym.Var = sym.Var("x")
    constant: sym.Const = sym.Const(1.0)
    full_expression: Dict[str, Any] = dict(
        type="BinOp",
        op="+",
        left=dict(type="Var", uid=variable.non_mutable_uid),
        right=dict(type="Const", uid=constant.uid),
        uid=101,
        graph_id=7,
    )
    referencing_expression: Dict[str, Any] = dict(
        type="BinOp",
        op="*",
        left=dict(type="ExprRef", graph_id=7),
        right=dict(type="Const", uid=constant.uid),
        uid=102,
        graph_id=8,
    )
    payload: List[Dict[str, Any]] = list((full_expression, referencing_expression))
    parsed_expressions: List[sym.Expr] = parse_expr_list(
        lst=payload,
        const_dict=dict(((constant.uid, constant),)),
        var_dict=dict(((variable.non_mutable_uid, variable),)),
        diff_var_dict=dict(),
    )

    referenced_bin_op: sym.BinOp = parsed_expressions[1]
    assert isinstance(referenced_bin_op, sym.BinOp)
    assert referenced_bin_op.left is parsed_expressions[0]
    assert referenced_bin_op.eval(x=2.0) == 3.0


def test_block_roundtrip_shares_expression_registry_across_fields() -> None:
    """
    Verify that one block registry spans equations, events, modes and discrete equations.

    :return: None.
    """
    source_factory: VarFactory = VarFactory()
    variable: sym.Var = source_factory.add_var("x")
    event_variable: sym.Var = source_factory.add_var("event")
    mode_variable: sym.Var = source_factory.add_var("mode")
    discrete_variable: sym.Var = source_factory.add_var("discrete")
    shared_expression: sym.Expr = variable + sym.Const(1.0)
    source_block: Block = Block(
        algebraic_vars=list((variable, event_variable, mode_variable, discrete_variable)),
        algebraic_eqs=list((shared_expression,)),
        event_dict=dict(((event_variable, shared_expression),)),
        mode_dict=dict(((mode_variable, shared_expression),)),
        discrete_eqs=dict(((discrete_variable, shared_expression),)),
        name="legacy_expr_ref_block",
    )
    saver: BlockSaver = BlockSaver(source_factory)
    saver.save_block(source_block, main=True)
    serialized_block: Dict[str, Any] = saver.get_blocks()[source_block.uid]

    parser: BlockParser = BlockParser(VarFactory())
    parser.parse_consts(saver.get_const_to_save())
    parser.parse_vars(saver.get_vars_to_save())
    parser.parse_diff_vars(saver.get_diff_vars_to_save())
    restored_block: Block = parser.parse_block(saver.get_blocks(), source_block.uid)
    restored_expression: sym.Expr = restored_block.algebraic_eqs[0]
    restored_event_expression: sym.Expr = next(iter(restored_block.event_dict.values()))
    restored_mode_expression: sym.Expr = next(iter(restored_block.mode_dict.values()))
    restored_discrete_expression: sym.Expr = next(iter(restored_block.discrete_eqs.values()))

    assert serialized_block["event_dict"][0]["expr"]["type"] == "ExprRef"
    assert serialized_block["mode_dict"][0]["expr"]["type"] == "ExprRef"
    assert serialized_block["discrete_eqs"][0]["expr"]["type"] == "ExprRef"
    assert restored_event_expression is restored_expression
    assert restored_mode_expression is restored_expression
    assert restored_discrete_expression is restored_expression


def test_tree_payload_without_graph_ids_remains_supported() -> None:
    """
    Verify that older tree-only symbolic payloads still deserialize unchanged.

    :return: None.
    """
    variable: sym.Var = sym.Var("x")
    constant: sym.Const = sym.Const(2.0)
    payload: Dict[str, Any] = dict(
        type="BinOp",
        op="+",
        left=dict(type="Var", uid=variable.non_mutable_uid),
        right=dict(type="Const", uid=constant.uid),
        uid=201,
    )

    restored: sym.Expr = parse_expr(
        data=payload,
        const_dict=dict(((constant.uid, constant),)),
        var_dict=dict(((variable.non_mutable_uid, variable),)),
        diff_var_dict=dict(),
    )

    assert restored.eval(x=3.0) == 5.0


def test_dangling_expr_ref_reports_graph_identifier() -> None:
    """
    Verify that broken graph references fail with a diagnostic identifier.

    :return: None.
    """
    payload: Dict[str, Any] = dict(type="ExprRef", graph_id=999)

    with pytest.raises(ValueError, match="999"):
        parse_expr(
            data=payload,
            const_dict=dict(),
            var_dict=dict(),
            diff_var_dict=dict(),
        )


def test_persisted_identity_lookup_keeps_stable_identity_authoritative() -> None:
    """
    Verify that a mutable UID alias never replaces an existing stable identity.

    :return: None.
    """
    stable_variable: sym.Var = sym.Var("stable", uid=99, non_mutable_uid=99)
    aliased_variable: sym.Var = sym.Var("aliased", uid=99, non_mutable_uid=20)
    var_dict: Dict[int, sym.Var] = dict(((20, aliased_variable), (99, stable_variable)))

    identity_lookup: Dict[int, sym.Var] = build_persisted_identity_lookup(var_dict=var_dict)

    assert identity_lookup[20] is aliased_variable
    assert identity_lookup[99] is stable_variable


def test_block_parser_rebuilds_legacy_uid_lookup_after_connections() -> None:
    """
    Verify that connection-propagated legacy UIDs resolve without repeated scans.

    :return: None.
    """
    parser: BlockParser = BlockParser(VarFactory())
    parser.parse_vars(
        data=list((
            dict(type="Var", name="source", uid=99, non_mutable_uid=10, shared_ref=None, ref=None),
            dict(type="Var", name="target", uid=20, non_mutable_uid=20, shared_ref=None, ref=None),
        ))
    )
    parser.parse_diff_vars(data=list())
    parser.parse_connections(
        data=dict({
            10: list((
                dict(type="Connection", non_mutable_uid=20, name="target", uid=20),
            )),
        })
    )
    block_data: Dict[str, Any] = dict(
        uid=1,
        name="legacy_uid_block",
        state_vars=list(),
        state_eqs=list(),
        algebraic_vars=list((20,)),
        algebraic_eqs=list((dict(type="Var", uid=99),)),
        diff_vars=list(),
        differential_eqs=list(),
        inequalities=list(),
        children=list(),
    )
    blocks_data: Dict[int, Dict[str, Any]] = dict(((1, block_data),))

    restored_block: Block = parser.parse_block(blocks_data=blocks_data, main_block_uid=1)
    restored_source: sym.Var | None = parser.var_factory.get_vars_dict().get(10, None)
    restored_target: sym.Var | None = parser.var_factory.get_vars_dict().get(20, None)

    assert restored_source is not None
    assert restored_target is not None
    assert restored_target.uid == restored_source.uid == 99
    assert restored_block.algebraic_vars[0] is restored_target
    assert restored_block.algebraic_eqs[0] is restored_source


def test_legacy_func2_min_max_codegen_uses_elementwise_numpy_operations() -> None:
    """
    Verify legacy binary min/max nodes keep two-operand semantics in generated code.

    :return: None.
    """
    variable: sym.Var = sym.Var("x")
    compiler_names: Dict[int, str] = dict(((variable.uid, "vrs[0]"),))
    legacy_maximum: sym.Func2 = sym.Func2("max", variable, sym.Const(1.0e-12))
    legacy_minimum: sym.Func2 = sym.Func2("min", variable, sym.Const(-1.0e-12))

    maximum_source: str = sym.expression2numba(legacy_maximum, compiler_names)
    minimum_source: str = sym.expression2numba(legacy_minimum, compiler_names)
    evaluation_namespace: Dict[str, Any] = dict(np=np, vrs=np.array([-2.0], dtype=float))
    maximum_value: float = float(eval(maximum_source, evaluation_namespace))
    minimum_value: float = float(eval(minimum_source, evaluation_namespace))

    assert maximum_source == "np.maximum(vrs[0], 1e-12)"
    assert minimum_source == "np.minimum(vrs[0], -1e-12)"
    assert maximum_value == 1.0e-12
    assert minimum_value == -2.0


def test_block_parser_opens_legacy_inline_child_tree_without_main_uids() -> None:
    """
    Verify the inline-child archive layout written by commit ``48bcef198``.

    :return: None.
    """
    child_data: Dict[str, Any] = dict(
        uid=202,
        name="legacy_inline_child",
        children=list(),
    )
    root_data: Dict[str, Any] = dict(
        uid=101,
        name="legacy_inline_root",
        children=list((child_data,)),
    )
    legacy_blocks: Dict[str, Any] = dict({"101": root_data})
    parser: BlockParser = BlockParser(VarFactory())

    # The old symbolic section had no main_block_uids, so the parser must infer
    # the root and flatten the nested child before rebuilding runtime blocks.
    parsed_roots: List[Block] = parser.parse_blocks(blocks_data=legacy_blocks,
                                                     main_block_uids=None)

    assert len(parsed_roots) == 1
    assert parsed_roots[0].uid == 101
    assert len(parsed_roots[0].children) == 1
    assert parsed_roots[0].children[0].uid == 202
    assert parser.block_dict[202] is parsed_roots[0].children[0]


def test_block_parser_opens_legacy_list_table_and_warns_for_missing_pointer_child() -> None:
    """
    Verify list-based pointer archives retain recoverable blocks and warn on loss.

    :return: None.
    """
    child_data: Dict[str, Any] = dict(
        uid=302,
        name="legacy_pointer_child",
        children=list(),
    )
    root_data: Dict[str, Any] = dict(
        uid=301,
        name="legacy_pointer_root",
        children=list((302, 999)),
    )
    legacy_blocks: List[Dict[str, Any]] = list((root_data, child_data))
    logger: Logger = Logger()
    parser: BlockParser = BlockParser(VarFactory(), logger=logger)

    # Pointer-format files predate main_block_uids. The valid edge is restored;
    # an absent referenced record is isolated instead of aborting file opening.
    parsed_roots: List[Block] = parser.parse_blocks(blocks_data=legacy_blocks,
                                                     main_block_uids=None)

    assert len(parsed_roots) == 1
    assert parsed_roots[0].uid == 301
    assert [child.uid for child in parsed_roots[0].children] == [302]
    assert len(logger.entries) == 1
    assert logger.entries[0].msg == "Missing child dynamic block while parsing persisted symbolic data"
    assert logger.entries[0].value == "999"


def test_block_parser_ignores_cyclic_legacy_child_uid_without_recursing_forever() -> None:
    """
    Verify a malformed historical child graph cannot block the file loader.

    :return: None.
    """
    root_data: Dict[str, Any] = dict(
        uid="401",
        name="legacy_cyclic_root",
        children=list((401,)),
    )
    logger: Logger = Logger()
    parser: BlockParser = BlockParser(VarFactory(), logger=logger)

    parsed_roots: List[Block] = parser.parse_blocks(blocks_data=list((root_data,)),
                                                     main_block_uids=None)

    assert len(parsed_roots) == 1
    assert parsed_roots[0].uid == 401
    assert parsed_roots[0].children == list()
    assert len(logger.entries) == 1
    assert logger.entries[0].msg == "Cyclic child dynamic block reference ignored while parsing persisted data"
