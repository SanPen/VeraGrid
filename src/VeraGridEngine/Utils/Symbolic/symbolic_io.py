# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
import copy
from typing import Dict, Any, List

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Devices.Dynamic.var_factory import (Connection,
                                                        VarFactory,
                                                        build_persisted_identity_lookup,
                                                        find_var_by_persisted_identity)
from VeraGridEngine.Utils.Symbolic import SharedVarReferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Expr, Const, BinOp, UnOp, Func, Func2
from VeraGridEngine.Utils.Symbolic.block import Block, normalize_dynamic_connection_intents
from VeraGridEngine.Utils.Symbolic.dynamic_connection_intent import (DynamicConnectionIntent,
                                                                     DynamicConnectionIntentDirection,
                                                                     dynamic_connection_intent_from_dict,
                                                                     dynamic_connection_intent_to_dict)
from VeraGridEngine.enumerations import VarPowerFlowReferenceType, ParamPowerFlowReferenceType


def symbolic_objects_to_dict(obj_dict: Dict[int | str, Var | Const | Var | SharedVarReferenceType]) -> List[Dict[str, Any]]:
    """
    Save the list of all unique vars, diffvars and const
    :param obj_dict: Dictionary storing the unique objects
    :return: List of dictionaries representing each object
    """
    lst: List[Dict[str, Any]] = list()

    for uuid, expr in obj_dict.items():

        if isinstance(expr, Const):

            # add it to the references dict
            obj_dict[expr.uid] = expr

            # The const didn't exist, we create it here
            if isinstance(expr.value, complex):
                lst.append({"type": "Const",
                            "value": [expr.value.real, expr.value.imag],
                            "kind": "complex",
                            "uid": expr.uid})
            else:
                lst.append({"type": "Const",
                            "value": expr.value,
                            "uid": expr.uid})

        elif isinstance(expr, Var):
            shared = expr.shared_ref
            if expr.base_var is not None:
                if type(expr.ref) == str:
                    lst.append({
                        "type": "DiffVar",
                        "name": expr.name,
                        "uid": expr.uid,
                        "non_mutable_uid": expr.non_mutable_uid,
                        "base_var": expr.base_var.non_mutable_uid,
                        "shared_ref": {"name": shared.name if shared is not None else None,
                                "uid": shared.uid if shared is not None else None},
                        "ref": expr.ref.value if expr.ref is not None else None,
                    })
                else:
                    lst.append({
                        "type": "DiffVar",
                        "name": expr.name,
                        "uid": expr.uid,
                        "non_mutable_uid": expr.non_mutable_uid,
                        "base_var": expr.base_var.non_mutable_uid,
                        "shared_ref": {"name": shared.name if shared is not None else None,
                                "uid": shared.uid if shared is not None else None},
                        "ref": expr.ref.value if expr.ref is not None else None,
                    })



            else:
                # it is a normal var
                if type(expr.ref) == str:
                    lst.append({"type": "Var",
                                "name": expr.name,
                                "uid": expr.uid,
                                "non_mutable_uid": expr.non_mutable_uid,
                                "base_var": None,
                                "shared_ref": {"name": shared.name if shared is not None else None,
                                                "uid": shared.uid if shared is not None else None},
                                "ref": expr.ref.value if expr.ref is not None else None,
                                })
                else:
                    lst.append({"type": "Var",
                                "name": expr.name,
                                "uid": expr.uid,
                                "non_mutable_uid": expr.non_mutable_uid,
                                "base_var": None,
                                "shared_ref": {"name": shared.name if shared is not None else None,
                                                "uid": shared.uid if shared is not None else None},
                                "ref": expr.ref.value if expr.ref is not None else None,
                                })

        if isinstance(expr, SharedVarReferenceType):
            lst.append({"type": "share_reference",
                        "name": expr.name,
                        "uid": expr.uid})

        if isinstance(expr, Connection):
            lst.append({"type": "Connection",
                        "non_mutable_uid": expr.non_mutable_uid,
                        "name": expr.name,
                        "uid": expr.uid})


    return lst

def connections_to_dict(obj_dict: Dict[int, List[Connection]]) -> Dict[int, List[Any]]:


    conn_dict: Dict[int, List[Any]] = dict()

    for uuid, connections_list in obj_dict.items():
        conn_list: List[Any] = list()
        for connection in connections_list:
            conn_list.append({"type": "Connection",
                        "non_mutable_uid": connection.non_mutable_uid,
                        "name": connection.name,
                        "uid": connection.uid})
        conn_dict[uuid] = conn_list
    return conn_dict


def normalize_persisted_block_uid(uid_value: Any) -> int | None:
    """
    Convert one persisted block identifier to the current integer representation.

    JSON object keys are strings while symbolic block UIDs are integers in
    memory. Historical archives can therefore contain either representation.
    Invalid identifiers are ignored by the legacy normalization layer so the
    caller can report the damaged reference without blocking the full file.

    :param uid_value: Persisted block identifier.
    :return: Integer UID or ``None`` when the value is not a valid identifier.
    """
    normalized_uid: int | None
    try:
        normalized_uid = int(uid_value)
    except (TypeError, ValueError):
        normalized_uid = None

    return normalized_uid


def register_persisted_block_tree(block_data: Dict[str, Any],
                                  normalized_blocks: Dict[int, Dict[str, Any]],
                                  fallback_uid: Any = None) -> None:
    """
    Register one block and any historically inline child block records.

    Commit ``48bcef198`` serialized ``children`` as complete nested block
    dictionaries. Later formats store only child UIDs in a flat block table.
    Flattening the old tree before parsing lets both layouts follow the same
    reconstruction path without changing the runtime ``Block`` architecture.

    :param block_data: Persisted block record.
    :param normalized_blocks: Destination table indexed by integer UID.
    :param fallback_uid: Container key used when the record omits ``uid``.
    :return: None.
    """
    block_uid: int | None = normalize_persisted_block_uid(block_data.get("uid", fallback_uid))
    if block_uid is not None:
        if block_uid not in normalized_blocks:
            normalized_blocks[block_uid] = block_data
        else:
            pass

        child_entry: Any
        for child_entry in block_data.get("children", list()):
            if isinstance(child_entry, dict):
                register_persisted_block_tree(block_data=child_entry,
                                              normalized_blocks=normalized_blocks)
            else:
                pass
    else:
        pass


def normalize_persisted_blocks(blocks_data: Dict[Any, Any] | List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    Normalize every block container written by historical dynamics branches.

    The first pointer-based format stored ``blocks`` as a list. It later became
    a JSON dictionary keyed by UID, and one intermediate revision embedded
    children recursively inside each top-level record. This function accepts
    all three shapes and produces the current flat integer-keyed table.

    :param blocks_data: Persisted list, UID mapping or single block record.
    :return: Flat block table indexed by integer UID.
    """
    normalized_blocks: Dict[int, Dict[str, Any]] = dict()

    if isinstance(blocks_data, list):
        block_data: Dict[str, Any]
        for block_data in blocks_data:
            if isinstance(block_data, dict):
                register_persisted_block_tree(block_data=block_data,
                                              normalized_blocks=normalized_blocks)
            else:
                pass
    elif isinstance(blocks_data, dict):
        # A few development snapshots passed one inline root directly instead
        # of wrapping it in the global block table.
        direct_uid: int | None = normalize_persisted_block_uid(blocks_data.get("uid", None))
        if direct_uid is not None:
            register_persisted_block_tree(block_data=blocks_data,
                                          normalized_blocks=normalized_blocks)
        else:
            persisted_key: Any
            persisted_record: Any
            for persisted_key, persisted_record in blocks_data.items():
                if isinstance(persisted_record, dict):
                    register_persisted_block_tree(block_data=persisted_record,
                                                  normalized_blocks=normalized_blocks,
                                                  fallback_uid=persisted_key)
                else:
                    pass
    else:
        pass

    return normalized_blocks


def infer_persisted_main_block_uids(blocks_data: Dict[int, Dict[str, Any]]) -> List[int]:
    """
    Infer root block UIDs for archives predating ``main_block_uids``.

    Roots are the stored blocks that are not referenced as children by any
    other stored block. If a damaged cyclic graph has no discoverable root, all
    records are returned so the parser can retain the recoverable blocks while
    its cycle guard drops only the invalid child edge.

    :param blocks_data: Normalized block table.
    :return: Deterministically ordered root block UIDs.
    """
    child_uids: set[int] = set()
    block_data: Dict[str, Any]
    child_entry: Any
    for block_data in blocks_data.values():
        for child_entry in block_data.get("children", list()):
            if isinstance(child_entry, dict):
                child_uid: int | None = normalize_persisted_block_uid(child_entry.get("uid", None))
            else:
                child_uid = normalize_persisted_block_uid(child_entry)

            if child_uid is not None:
                child_uids.add(child_uid)
            else:
                pass

    root_uids: List[int] = sorted(set(blocks_data.keys()).difference(child_uids))
    if len(root_uids) == 0 and len(blocks_data) > 0:
        root_uids = sorted(blocks_data.keys())
    else:
        pass

    return root_uids


def expr_to_dict(expr: Expr,
                 const_dict: Dict[int, Const],
                 var_dict: Dict[int, Var],
                 diff_var_dict: Dict[int, Var],
                 composite_expression_ids: Dict[int, int] | None = None) -> Dict[str, Any]:
    """
    Serialise any `Expr` tree into a plain Python dictionary that’s
    JSON-friendly.  Each node type becomes a small dict that records:

        • its own type      (\"Const\", \"Var\", \"BinOp\", …)
        • the data it carries (value, name, operator…)
        • its unique uid     (string, so it survives round-trip)
        • nested children    (recursively serialised)
    :param expr: Expression child
    :param const_dict: Dictionary that keeps a reference of the Const objects already saved
    :param var_dict: Dictionary that keeps a reference of the VAr objects already saved
    :param diff_var_dict: Dictionary that keeps a reference of the DiffVar objects already saved
    :param composite_expression_ids: Object identities already serialized in the current block
    :return: Dict to save in jason
    """
    active_composite_expression_ids: Dict[int, int]
    if composite_expression_ids is None:
        active_composite_expression_ids = dict()
    else:
        active_composite_expression_ids = composite_expression_ids

    if isinstance(expr, Const):

        c = const_dict.get(expr.uid, None)

        if c is None:
            # add it to the references dict
            const_dict[expr.uid] = expr

        # the const already exists
        return {
            "type": "Const",
            "uid": expr.uid
        }

    elif isinstance(expr, Var):

        if expr.base_var is not None:

            c = diff_var_dict.get(expr.non_mutable_uid, None)

            if c is None:
                # add it to the references dict
                diff_var_dict[expr.non_mutable_uid] = expr

            # the diffvar already exists
            return {
                "type": "DiffVar",
                "uid": expr.non_mutable_uid
            }

        else:
            c = var_dict.get(expr.non_mutable_uid, None)

            if c is None:
                # add it to the references dict
                var_dict[expr.non_mutable_uid] = expr

            # the var already exists
            return {
                "type": "Var",
                "uid": expr.non_mutable_uid
            }

    else:
        # Composite expressions form a directed acyclic graph because the same
        # object may be reused by several controller equations. The first
        # occurrence is serialized completely and later occurrences become
        # references, preventing exponential expansion of the expression tree.
        expression_object_id: int = id(expr)
        existing_graph_id: int | None = active_composite_expression_ids.get(expression_object_id, None)
        if existing_graph_id is None:
            graph_id: int = len(active_composite_expression_ids)
            active_composite_expression_ids[expression_object_id] = graph_id
        else:
            return {
                "type": "ExprRef",
                "graph_id": existing_graph_id,
            }

    if isinstance(expr, BinOp):
        return {
            "type": "BinOp",
            "op": expr.op,
            "left": expr_to_dict(expr=expr.left,
                                 const_dict=const_dict,
                                 var_dict=var_dict,
                                 diff_var_dict=diff_var_dict,
                                 composite_expression_ids=active_composite_expression_ids),
            "right": expr_to_dict(expr=expr.right,
                                  const_dict=const_dict,
                                  var_dict=var_dict,
                                  diff_var_dict=diff_var_dict,
                                  composite_expression_ids=active_composite_expression_ids),
            "uid": expr.uid,
            "graph_id": graph_id,
        }

    elif isinstance(expr, UnOp):
        return {
            "type": "UnOp",
            "op": expr.op,  # only \"-\" for now
            "operand": expr_to_dict(expr=expr.operand,
                                    const_dict=const_dict,
                                    var_dict=var_dict,
                                    diff_var_dict=diff_var_dict,
                                    composite_expression_ids=active_composite_expression_ids),
            "uid": expr.uid,
            "graph_id": graph_id,
        }

    elif isinstance(expr, Func):
        return {
            "type": "Func",
            "op": expr.op,  # sin, cos, log, …
            "arg": expr_to_dict(expr=expr.arg,
                                const_dict=const_dict,
                                var_dict=var_dict,
                                diff_var_dict=diff_var_dict,
                                composite_expression_ids=active_composite_expression_ids),
            "uid": expr.uid,
            "graph_id": graph_id,
        }

    elif isinstance(expr, Func2):
        return {
            "type": "Func2",
            "name": expr.name,
            "arg1": expr_to_dict(expr=expr.arg1,
                                  const_dict=const_dict,
                                  var_dict=var_dict,
                                  diff_var_dict=diff_var_dict,
                                  composite_expression_ids=active_composite_expression_ids),
            "arg2": expr_to_dict(expr=expr.arg2,
                                  const_dict=const_dict,
                                  var_dict=var_dict,
                                  diff_var_dict=diff_var_dict,
                                  composite_expression_ids=active_composite_expression_ids),
            "uid": expr.uid,
            "graph_id": graph_id,
        }

    else:
        raise TypeError(f"Unsupported Expr subclass: {type(expr).__name__}")


def expr_list_to_list(lst: List[Expr],
                      const_dict: Dict[int, Const],
                      var_dict: Dict[int, Var],
                      diff_var_dict: Dict[int, Var],
                      composite_expression_ids: Dict[int, int] | None = None) -> List[Dict[str, Any]]:
    """

    :param lst:
    :param const_dict:
    :param var_dict:
    :param diff_var_dict:
    :param composite_expression_ids: Object identities already serialized in the current block
    :return:
    """
    active_composite_expression_ids: Dict[int, int]
    if composite_expression_ids is None:
        active_composite_expression_ids = dict()
    else:
        active_composite_expression_ids = composite_expression_ids

    lst2: List[Dict[str, Any]] = list()

    for expr in lst:
        lst2.append(
            expr_to_dict(expr=expr,
                         const_dict=const_dict,
                         var_dict=var_dict,
                         diff_var_dict=diff_var_dict,
                         composite_expression_ids=active_composite_expression_ids)
        )
    return lst2


def parse_expr(data: Dict[str, Any],
               const_dict: Dict[int, Const],
               var_dict: Dict[int, Var],
               diff_var_dict: Dict[int, Var],
               composite_expressions: Dict[int, Expr] | None = None) -> Const | Var | UnOp | BinOp | Func | Func2:
    """
    De-Serialize expression from dictionary
    :param data: Some dictionary containing the expression
    :param const_dict: Dictionary that keeps a reference of the Const objects already saved
    :param var_dict: Dictionary that keeps a reference of the VAr objects already saved
    :param diff_var_dict: Dictionary that keeps a reference of the DiffVar objects already saved
    :param composite_expressions: Composite graph nodes already parsed in the current block
    :return: Expression chil
    """
    active_composite_expressions: Dict[int, Expr]
    if composite_expressions is None:
        active_composite_expressions = dict()
    else:
        active_composite_expressions = composite_expressions

    t: str = data["type"]

    if t == "ExprRef":
        graph_id: int = int(data["graph_id"])
        referenced_expression: Expr | None = active_composite_expressions.get(graph_id, None)
        if referenced_expression is None:
            raise ValueError(f"Unknown backward expression reference '{graph_id}'")
        else:
            return referenced_expression

    elif t == "Const":
        return const_dict[data["uid"]]

    elif t == "Var":
        parsed_var: Var | None = find_var_by_persisted_identity(
            var_dict=var_dict,
            persisted_uid=data["uid"],
        )
        if parsed_var is not None:
            return parsed_var
        else:
            raise KeyError(f"Var with persisted uid {data['uid']} was not found")

    elif t == "DiffVar":
        parsed_diff_var: Var | None = find_var_by_persisted_identity(
            var_dict=diff_var_dict,
            persisted_uid=data["uid"],
        )
        if parsed_diff_var is not None:
            return parsed_diff_var
        else:
            raise KeyError(f"DiffVar with persisted uid {data['uid']} was not found")

    elif t == "BinOp":
        left = parse_expr(data=data["left"],
                          const_dict=const_dict,
                          var_dict=var_dict,
                          diff_var_dict=diff_var_dict,
                          composite_expressions=active_composite_expressions)

        right = parse_expr(data=data["right"],
                           const_dict=const_dict,
                           var_dict=var_dict,
                           diff_var_dict=diff_var_dict,
                           composite_expressions=active_composite_expressions)

        obj = BinOp(left=left, op=data["op"], right=right, uid=data["uid"])

    elif t == "UnOp":
        operand = parse_expr(data=data["operand"],
                             const_dict=const_dict,
                             var_dict=var_dict,
                             diff_var_dict=diff_var_dict,
                             composite_expressions=active_composite_expressions)
        obj = UnOp(op=data["op"], operand=operand, uid=data["uid"])

    elif t == "Func":
        arg = parse_expr(data=data["arg"],
                         const_dict=const_dict,
                         var_dict=var_dict,
                         diff_var_dict=diff_var_dict,
                         composite_expressions=active_composite_expressions)

        obj = Func(arg=arg, op=data["op"], uid=data["uid"])

    elif t == "Func2":
        arg1: Const | Var | UnOp | BinOp | Func | Func2 = parse_expr(data=data["arg1"],
                                                                      const_dict=const_dict,
                                                                      var_dict=var_dict,
                                                                      diff_var_dict=diff_var_dict,
                                                                      composite_expressions=active_composite_expressions)
        arg2: Const | Var | UnOp | BinOp | Func | Func2 = parse_expr(data=data["arg2"],
                                                                      const_dict=const_dict,
                                                                      var_dict=var_dict,
                                                                      diff_var_dict=diff_var_dict,
                                                                      composite_expressions=active_composite_expressions)

        obj = Func2(name=data["name"], arg1=arg1, arg2=arg2, uid=data["uid"])

    else:
        raise ValueError(f"Unknown type '{t}' in symbolic deserialization")

    # Graph-aware archives add ``graph_id`` only to composite nodes. Legacy
    # tree archives omit it and therefore keep following the same code path.
    graph_id_value: int | None = data.get("graph_id", None)
    if graph_id_value is None:
        pass
    else:
        active_composite_expressions[int(graph_id_value)] = obj

    return obj


def parse_expr_list(lst: List[Dict[str, Any]],
                    const_dict: Dict[int, Const],
                    var_dict: Dict[int, Var],
                    diff_var_dict: Dict[int, Var],
                    composite_expressions: Dict[int, Expr] | None = None) -> List[Const | Var | UnOp | BinOp | Func | Func2]:
    """

    :param lst:
    :param const_dict:
    :param var_dict:
    :param diff_var_dict:
    :param composite_expressions: Composite graph nodes already parsed in the current block
    :return:
    """
    active_composite_expressions: Dict[int, Expr]
    if composite_expressions is None:
        active_composite_expressions = dict()
    else:
        active_composite_expressions = composite_expressions

    lst2: List[Const | Var | UnOp | BinOp | Func | Func2] = list()
    data: Dict[str, Any]
    for data in lst:
        lst2.append(
            parse_expr(
                data=data,
                const_dict=const_dict,
                var_dict=var_dict,
                diff_var_dict=diff_var_dict,
                composite_expressions=active_composite_expressions
            )
        )
    return lst2


class BlockSaver:
    __slots__ = (
        "var_factory",
        "main_block_uids",
        "blocks",
    )

    def __init__(self, var_factory: VarFactory):
        """Create a serializer bound to one symbolic variable factory.

        :param var_factory: Factory containing the variables and shared references to serialize.
        """
        self.var_factory = var_factory
        self.main_block_uids: List[int] = list()
        self.blocks: Dict[int, Dict[str, Any]] = dict()

    def get_const_to_save(self) -> List[Dict[str, Any]]:
        """

        :return:
        """
        return symbolic_objects_to_dict(self.var_factory.get_const_dict())

    def get_vars_to_save(self) -> List[Dict[str, Any]]:
        """

        :return:
        """
        return symbolic_objects_to_dict(self.var_factory.get_vars_dict())

    def get_diff_vars_to_save(self) -> List[Dict[str, Any]]:
        """

        :return:
        """
        return symbolic_objects_to_dict(self.var_factory.get_diff_var_dict())

    def get_shared_references_to_save(self) -> List[Dict[str, Any]]:
        """

        :return:
        :rtype:
        """
        return symbolic_objects_to_dict(self.var_factory.get_references_dict())

    def get_connections_to_save(self) -> Dict[int, List[Any]]:
        """

        :return:
        :rtype:
        """
        return connections_to_dict(self.var_factory.get_connections_dict())

    def get_blocks(self) -> Dict[int, Dict[str, Any]]:
        return self.blocks

    def _ensure_var_registered(self, var: Var) -> None:
        """
        Ensure that one algebraic variable is present in the shared variable factory.

        Some blocks created through GUI/template workflows keep live variable objects
        that are not reinserted into the factory before serialization. The saver must
        register them instead of failing deep in a background thread.

        :param var: Variable to register.
        :return: None.
        """
        try:
            found_var = self.var_factory.get_var(var.non_mutable_uid)
        except Exception:
            found_var = None

        if found_var is None:
            self.var_factory._var_dict[var.non_mutable_uid] = var
        else:
            pass

    def _ensure_diff_var_registered(self, diff_var: Var) -> None:
        """
        Ensure that one differential variable is present in the shared variable factory.

        :param diff_var: Differential variable to register.
        :return: None.
        """
        try:
            found_var = self.var_factory.get_diff_var(diff_var.non_mutable_uid)
        except Exception:
            found_var = None

        if found_var is None:
            self.var_factory._diff_var_dict[diff_var.non_mutable_uid] = diff_var
        else:
            pass

    def save_block(self, blk: Block, main: bool = False) -> Dict[str, Any]:
        """
        Get a dictionary representing the block
        All "global references" such a as Conts, Var and DiffVar are stored in the class for later
        :param blk: Block
        :param main: is it the main block?
        :return: Dictionary representing the block
        """
        # One registry is shared by every expression owned by this block. Child
        # blocks create their own registry when ``save_block`` recurses.
        composite_expression_ids: Dict[int, int] = dict()

        state_expressions: List[Dict[str, Any]] = expr_list_to_list(
            lst=blk.state_eqs,
            const_dict=self.var_factory.get_const_dict(),
            var_dict=self.var_factory.get_vars_dict(),
            diff_var_dict=self.var_factory.get_diff_var_dict(),
            composite_expression_ids=composite_expression_ids
        )

        algebraic_expressions: List[Dict[str, Any]] = expr_list_to_list(
            lst=blk.algebraic_eqs,
            const_dict=self.var_factory.get_const_dict(),
            var_dict=self.var_factory.get_vars_dict(),
            diff_var_dict=self.var_factory.get_diff_var_dict(),
            composite_expression_ids=composite_expression_ids
        )

        differential_eqs_expressions: List[Dict[str, Any]] = expr_list_to_list(
            lst=blk.differential_eqs,
            const_dict=self.var_factory.get_const_dict(),
            var_dict=self.var_factory.get_vars_dict(),
            diff_var_dict=self.var_factory.get_diff_var_dict(),
            composite_expression_ids=composite_expression_ids
        )

        inequality_expressions: List[Dict[str, Any]] = expr_list_to_list(
            lst=blk.inequalities,
            const_dict=self.var_factory.get_const_dict(),
            var_dict=self.var_factory.get_vars_dict(),
            diff_var_dict=self.var_factory.get_diff_var_dict(),
            composite_expression_ids=composite_expression_ids
        )

        init_eq_list: List[Dict[str, Any]] = list()
        diff_init_eq_list: List[Dict[str, Any]] = list()
        for var, expr in blk.init_eqs.items():
            self._ensure_var_registered(var)

            init_eq_list.append(
                {
                    "var": var.non_mutable_uid,
                    "expr": expr_to_dict(
                        expr=expr,
                        const_dict=self.var_factory.get_const_dict(),
                        var_dict=self.var_factory.get_vars_dict(),
                        diff_var_dict=self.var_factory.get_diff_var_dict(),
                        composite_expression_ids=composite_expression_ids
                    )
                }
            )

        for diff_var, expr in blk.diff_init_eqs.items():
            self._ensure_diff_var_registered(diff_var)

            diff_init_eq_list.append(
                {
                    "var": diff_var.non_mutable_uid,
                    "expr": expr_to_dict(
                        expr=expr,
                        const_dict=self.var_factory.get_const_dict(),
                        var_dict=self.var_factory.get_vars_dict(),
                        diff_var_dict=self.var_factory.get_diff_var_dict(),
                        composite_expression_ids=composite_expression_ids
                    )
                }
            )

        events_list: List[Dict[str, Any]] = list()
        for var, expr in blk.event_dict.items():
            self._ensure_var_registered(var)

            events_list.append(
                {
                    "var": var.non_mutable_uid,
                    "expr": expr_to_dict(
                        expr=expr,
                        const_dict=self.var_factory.get_const_dict(),
                        var_dict=self.var_factory.get_vars_dict(),
                        diff_var_dict=self.var_factory.get_diff_var_dict(),
                        composite_expression_ids=composite_expression_ids
                    )
                }
            )

        mode_list: List[Dict[str, Any]] = list()
        for var, expr in blk.mode_dict.items():
            self._ensure_var_registered(var)
            mode_list.append(
                {
                    "var": var.non_mutable_uid,
                    "expr": expr_to_dict(
                        expr=expr,
                        const_dict=self.var_factory.get_const_dict(),
                        var_dict=self.var_factory.get_vars_dict(),
                        diff_var_dict=self.var_factory.get_diff_var_dict(),
                        composite_expression_ids=composite_expression_ids
                    )
                }
            )

        discrete_list: List[Dict[str, Any]] = list()
        for var, expr in blk.discrete_eqs.items():
            self._ensure_var_registered(var)
            discrete_list.append(
                {
                    "var": var.non_mutable_uid,
                    "expr": expr_to_dict(
                        expr=expr,
                        const_dict=self.var_factory.get_const_dict(),
                        var_dict=self.var_factory.get_vars_dict(),
                        diff_var_dict=self.var_factory.get_diff_var_dict(),
                        composite_expression_ids=composite_expression_ids
                    )
                }
            )

        boolean_guard_list: List[Dict[str, Any]] = list()
        for var, expr in blk.boolean_guards.items():
            self._ensure_var_registered(var)
            boolean_guard_list.append(
                {
                    "var": var.non_mutable_uid,
                    "expr": expr_to_dict(
                        expr=expr,
                        const_dict=self.var_factory.get_const_dict(),
                        var_dict=self.var_factory.get_vars_dict(),
                        diff_var_dict=self.var_factory.get_diff_var_dict(),
                        composite_expression_ids=composite_expression_ids
                    )
                }
            )

        in_vars: List[int] = list()
        for var in blk.in_vars:
            self._ensure_var_registered(var)

            in_vars.append(var.non_mutable_uid)

        out_vars: List[int] = list()
        for var in blk.out_vars:
            self._ensure_var_registered(var)

            out_vars.append(var.non_mutable_uid)

        init_values: List[Dict[str, float | int]] = list()
        for var, value in blk.init_values.items():
            self._ensure_var_registered(var)

            init_values.append({"var": var.non_mutable_uid, "value": value.value})

        parameters: List[Dict[str, float | int]] = list()
        for var, value in blk.parameters.items():
            self._ensure_var_registered(var)

            parameters.append({"var": var.non_mutable_uid, "value": value.value})

        # diff_vars: List[DiffVar] = list()
        for diff_var in blk.diff_vars:
            self._ensure_diff_var_registered(diff_var)

        for dyn_var_type, var in blk.external_mapping.items():
            if var is not None:
                self._ensure_var_registered(var)
            else:
                pass

        # save diagram
        diagram = blk.diagram.to_dict()

        # save children
        for child in blk.children:
            self.save_block(child)

        d = {
            "uid": blk.uid,

            "vars_glob_name2uid": blk.vars_glob_name2uid,

            "state_vars": [v.non_mutable_uid for v in blk.state_vars],

            "state_eqs": state_expressions,

            "inequalities": inequality_expressions,

            "algebraic_vars": [v.non_mutable_uid for v in blk.algebraic_vars],

            "algebraic_eqs": algebraic_expressions,

            "diff_vars": [v.non_mutable_uid for v in blk.diff_vars],

            "differential_eqs": differential_eqs_expressions,

            "reformulated_vars": [v.non_mutable_uid for v in blk.reformulated_vars],

            "init_eqs": init_eq_list,

            "diff_init_eqs": diff_init_eq_list,

            "discrete_eqs": discrete_list,

            "mode_dict": mode_list,

            "boolean_guards": boolean_guard_list,

            # Procedural-logic entries are runtime objects and cannot be
            # written to JSON directly.  Persist their typed dictionaries so
            # saving one sampled controller does not omit ``blocks.symbolic``
            # and leave every device model pointer unresolved on reload.
            "procedural_logic": blk._procedural_logic_to_dict(),

            "init_values": init_values,

            "parameters": parameters,

            "external_mapping": {dyn_var_type.value: var.non_mutable_uid if var is not None else None
                                 for dyn_var_type, var in blk.external_mapping.items()},

            "api_obj_mapping": {dyn_param_type.value: param.non_mutable_uid if param is not None else None
                                for dyn_param_type, param in blk.api_obj_mapping.items()},

            "event_dict": events_list,
            "name": blk.name,
            "children": [child.uid for child in blk.children],
            "in_vars": in_vars,
            "out_vars": out_vars,

            # Only the current semantic state is persisted. Graphical history
            # and topology-specific materialization remain outside the model.
            "connection_intents": [dynamic_connection_intent_to_dict(intent)
                                   for intent in blk.connection_intents],

            "diagram": diagram
        }

        self.blocks[blk.uid] = d
        if main:
            self.main_block_uids.append(blk.uid)

        return d


class BlockParser:
    __slots__ = (
        "var_factory",
        "block_dict",
        "logger",
        "_var_identity_lookup",
        "_diff_var_identity_lookup",
    )

    def __init__(self, var_factory: VarFactory, logger: Logger | None = None):
        """Create a block parser bound to one symbolic variable factory.

        :param var_factory: Factory used to resolve persisted symbolic identities.
        :param logger: Optional logger receiving recoverable parsing warnings.
        """
        self.var_factory = var_factory
        self.block_dict: Dict[int, Block] = dict()
        self.logger: Logger | None = logger
        self._var_identity_lookup: Dict[int, Var] = build_persisted_identity_lookup(
            var_dict=self.var_factory.get_vars_dict()
        )
        self._diff_var_identity_lookup: Dict[int, Var] = build_persisted_identity_lookup(
            var_dict=self.var_factory.get_diff_var_dict()
        )

    def _rebuild_persisted_identity_lookups(self) -> None:
        """
        Rebuild constant-time symbolic lookups after persisted data changes UIDs.

        Connection replay mutates runtime UIDs, so both lookup tables must be
        rebuilt after variables, differential variables or connections are
        parsed and before expression reconstruction begins.

        :return: None.
        """
        self._var_identity_lookup = build_persisted_identity_lookup(
            var_dict=self.var_factory.get_vars_dict()
        )
        self._diff_var_identity_lookup = build_persisted_identity_lookup(
            var_dict=self.var_factory.get_diff_var_dict()
        )

    def _add_warning(self,
                     msg: str,
                     block_name: str,
                     block_uid: int,
                     field_name: str,
                     missing_uid: int | None) -> None:
        """
        Record one non-fatal warning while rebuilding one dynamic block.

        :param msg: Warning message.
        :param block_name: Block name.
        :param block_uid: Block uid.
        :param field_name: Block field being parsed.
        :param missing_uid: Missing symbolic uid.
        :return: None.
        """
        if self.logger is not None:
            self.logger.add_warning(msg=msg,
                                    device=block_name,
                                    value=missing_uid,
                                    device_property=field_name,
                                    device_class=f"Block:{block_uid}")
        else:
            pass

    def _resolve_var_or_warn(self,
                             var_uid: int | None,
                             block_name: str,
                             block_uid: int,
                             field_name: str) -> Var | None:
        """
        Resolve one algebraic symbolic variable with legacy-tolerant fallback.

        :param var_uid: Variable uid.
        :param block_name: Block name.
        :param block_uid: Block uid.
        :param field_name: Block field being parsed.
        :return: Resolved variable or ``None``.
        """
        resolved_var: Var | None

        if var_uid is None:
            resolved_var = None
        else:
            resolved_var = self._var_identity_lookup.get(var_uid, None)

        if resolved_var is None:
            self._add_warning(msg="Missing symbolic variable while parsing dynamic block",
                              block_name=block_name,
                              block_uid=block_uid,
                              field_name=field_name,
                              missing_uid=var_uid)
        else:
            pass

        return resolved_var

    def _resolve_diff_var_or_warn(self,
                                  var_uid: int | None,
                                  block_name: str,
                                  block_uid: int,
                                  field_name: str) -> Var | None:
        """
        Resolve one differential symbolic variable with legacy-tolerant fallback.

        :param var_uid: Differential variable uid.
        :param block_name: Block name.
        :param block_uid: Block uid.
        :param field_name: Block field being parsed.
        :return: Resolved differential variable or ``None``.
        """
        resolved_var: Var | None

        if var_uid is None:
            resolved_var = None
        else:
            resolved_var = self._diff_var_identity_lookup.get(var_uid, None)

        if resolved_var is None:
            self._add_warning(msg="Missing differential symbolic variable while parsing dynamic block",
                              block_name=block_name,
                              block_uid=block_uid,
                              field_name=field_name,
                              missing_uid=var_uid)
        else:
            pass

        return resolved_var

    def _get_var_by_non_mutable_uid(self, non_mutable_uid: int) -> Var:
        """
        Recover one algebraic variable using its stable non-mutable UID.

        The symbolic connection system intentionally aliases connected
        variables by rewriting their runtime ``uid`` values. That aliasing is
        required by the solver, but block interfaces such as ``in_vars`` and
        ``out_vars`` must still be reconstructed with the original variable
        objects so metadata like ``ref`` keeps the semantic meaning assigned by
        the template author. Looking up ports by the mutable ``uid`` after
        replaying saved connections can therefore return a different connected
        variable, such as a bus variable replacing a branch terminal variable.

        :param non_mutable_uid: Stable symbolic variable identity.
        :return: Matching algebraic variable.
        :raises KeyError: If the variable is not present in the factory.
        """
        var_obj: Var | None = self._var_identity_lookup.get(non_mutable_uid, None)
        if var_obj is not None:
            return var_obj
        else:
            raise KeyError(f"Var with non_mutable_uid {non_mutable_uid} was not found in VarFactory")

    def _find_var_or_diff_var_by_non_mutable_uid(self, non_mutable_uid: int) -> Var | None:
        """
        Recover one symbolic variable or differential variable by stable identity.

        External mappings expose semantic power-flow references to specific
        symbolic variables. Saved connection replay may alias runtime ``uid``
        values across connected variables, so rebuilding external mappings by
        mutable ``uid`` can return a different connected variable and lose the
        original semantic role. This helper resolves the mapping through the
        stable dictionary keys used by the variable factory instead.

        :param non_mutable_uid: Stable symbolic identity stored in the file.
        :return: Matching variable or ``None`` when the mapping is unresolved.
        """
        var_obj: Var | None = self._var_identity_lookup.get(non_mutable_uid, None)
        if var_obj is not None:
            return var_obj
        else:
            diff_var_obj: Var | None = self._diff_var_identity_lookup.get(non_mutable_uid, None)
            if diff_var_obj is not None:
                return diff_var_obj
            else:
                return None

    def parse_consts(self, data: List[Dict[str, Any]]):
        """

        :param data:
        :return:
        """
        self.var_factory.parse_const_dict(data_list=data)

    def parse_vars(self, data: List[Dict[str, Any]]):
        """

        :param data:
        :return:
        """
        self.var_factory.parse_var_dict(data_list=data)
        self._rebuild_persisted_identity_lookups()

    def parse_diff_vars(self, data: List[Dict[str, Any]]):
        """

        :param data:
        :return:
        """
        self.var_factory.parse_diff_var_dict(data_list=data)
        self._rebuild_persisted_identity_lookups()

    def parse_references(self, data: List[Dict[str, Any]]):
        """

        :param data:
        :type data:
        :return:
        :rtype:
        """
        self.var_factory.parse_references_dict(datalist=data)

    def parse_connections(self, data: Dict[int, List[Any]]):
        """

        :param data:
        :type data:
        :return:
        :rtype:
        """
        self.var_factory.parse_connections_dict(datalist=data)
        self._rebuild_persisted_identity_lookups()

    def parse_blocks(self,
                     blocks_data: Dict[Any, Any] | List[Dict[str, Any]],
                     main_block_uids: List[Any] | None = None) -> List[Block]:
        """
        Parse a complete current or historical persisted block collection.

        Dynamics archives created before commit ``1a59bfa9b`` do not contain
        ``main_block_uids``. Their roots are inferred from the child graph after
        normalizing list-based and inline-child representations.

        :param blocks_data: Persisted block collection.
        :param main_block_uids: Explicit roots, or ``None`` for legacy inference.
        :return: Parsed root blocks.
        """
        normalized_blocks: Dict[int, Dict[str, Any]] = normalize_persisted_blocks(blocks_data=blocks_data)
        normalized_main_uids: List[int] = list()

        if main_block_uids is not None:
            persisted_main_uid: Any
            for persisted_main_uid in main_block_uids:
                normalized_main_uid: int | None = normalize_persisted_block_uid(persisted_main_uid)
                if normalized_main_uid is not None:
                    normalized_main_uids.append(normalized_main_uid)
                else:
                    self._add_warning(msg="Invalid main dynamic block UID in persisted symbolic data",
                                      block_name="",
                                      block_uid=0,
                                      field_name="main_block_uids",
                                      missing_uid=None)
        else:
            pass

        if len(normalized_main_uids) == 0:
            normalized_main_uids = infer_persisted_main_block_uids(blocks_data=normalized_blocks)
        else:
            pass

        parsed_blocks: List[Block] = list()
        main_block_uid: int
        for main_block_uid in normalized_main_uids:
            if main_block_uid in normalized_blocks:
                parsed_block: Block = self._parse_normalized_block(blocks_data=normalized_blocks,
                                                                    main_block_uid=main_block_uid,
                                                                    ancestor_uids=set())
                parsed_blocks.append(parsed_block)
            else:
                self._add_warning(msg="Missing main dynamic block while parsing persisted symbolic data",
                                  block_name="",
                                  block_uid=main_block_uid,
                                  field_name="main_block_uids",
                                  missing_uid=main_block_uid)

        return parsed_blocks

    def parse_block(self,
                    blocks_data: Dict[Any, Any] | List[Dict[str, Any]],
                    main_block_uid: int) -> Block:
        """
        Parse one current or historical persisted block tree.

        :param blocks_data: Persisted block collection.
        :param main_block_uid: Root block UID.
        :return: Parsed root block.
        """
        normalized_blocks: Dict[int, Dict[str, Any]] = normalize_persisted_blocks(blocks_data=blocks_data)
        normalized_main_uid: int | None = normalize_persisted_block_uid(main_block_uid)
        if normalized_main_uid is not None and normalized_main_uid in normalized_blocks:
            return self._parse_normalized_block(blocks_data=normalized_blocks,
                                                main_block_uid=normalized_main_uid,
                                                ancestor_uids=set())
        else:
            raise KeyError(f"Block with persisted uid {main_block_uid} was not found")

    def _parse_normalized_block(self,
                                blocks_data: Dict[int, Dict[str, Any]],
                                main_block_uid: int,
                                ancestor_uids: set[int]) -> Block:
        """
        Parse one block from an already normalized persisted block table.

        :param blocks_data: Flat integer-keyed block table.
        :param main_block_uid: Block UID to parse.
        :param ancestor_uids: Ancestors used to reject cyclic legacy child edges.
        :return: Parsed block.
        """
        existing_block: Block | None = self.block_dict.get(main_block_uid, None)
        if existing_block is not None:
            return existing_block
        else:
            pass

        data: Dict[str, Any] = blocks_data[main_block_uid]
        active_ancestor_uids: set[int] = set(ancestor_uids)
        active_ancestor_uids.add(main_block_uid)
        block_name: str = data.get("name", "")
        normalized_block_uid: int | None = normalize_persisted_block_uid(data.get("uid", main_block_uid))
        if normalized_block_uid is not None:
            block_uid_value: int = normalized_block_uid
        else:
            block_uid_value = main_block_uid

        # Graph identifiers are local to one block and may be shared across
        # several equation collections. Recursive child parsing creates an
        # independent registry for each child block.
        composite_expressions: Dict[int, Expr] = dict()

        state_vars: List[Var] = list()
        v_uid: int
        for v_uid in data.get("state_vars", list()):
            state_var: Var | None = self._resolve_var_or_warn(v_uid, block_name, block_uid_value, "state_vars")
            if state_var is not None:
                state_vars.append(state_var)
            else:
                pass

        state_eqs = parse_expr_list(lst=data.get("state_eqs", list()),
                                    const_dict=self.var_factory.get_const_dict(),
                                    var_dict=self._var_identity_lookup,
                                    diff_var_dict=self._diff_var_identity_lookup,
                                    composite_expressions=composite_expressions)

        algebraic_vars: List[Var] = list()
        for v_uid in data.get("algebraic_vars", list()):
            algebraic_var: Var | None = self._resolve_var_or_warn(v_uid,
                                                                  block_name,
                                                                  block_uid_value,
                                                                  "algebraic_vars")
            if algebraic_var is not None:
                algebraic_vars.append(algebraic_var)
            else:
                pass

        algebraic_eqs = parse_expr_list(lst=data.get("algebraic_eqs", list()),
                                        const_dict=self.var_factory.get_const_dict(),
                                        var_dict=self._var_identity_lookup,
                                        diff_var_dict=self._diff_var_identity_lookup,
                                        composite_expressions=composite_expressions)
        if data.get("diff_vars", list()):
            diff_vars: List[Var] = list()
            for v_uid in data.get("diff_vars", list()):
                diff_var: Var | None = self._resolve_diff_var_or_warn(v_uid,
                                                                      block_name,
                                                                      block_uid_value,
                                                                      "diff_vars")
                if diff_var is not None:
                    diff_vars.append(diff_var)
                else:
                    pass
        else:
            diff_vars = list()

        differential_eqs = parse_expr_list(lst=data.get("differential_eqs", list()),
                                           const_dict=self.var_factory.get_const_dict(),
                                           var_dict=self._var_identity_lookup,
                                           diff_var_dict=self._diff_var_identity_lookup,
                                           composite_expressions=composite_expressions)

        inequalities = parse_expr_list(lst=data.get("inequalities", list()),
                                       const_dict=self.var_factory.get_const_dict(),
                                       var_dict=self._var_identity_lookup,
                                       diff_var_dict=self._diff_var_identity_lookup,
                                       composite_expressions=composite_expressions)

        # Rebuild interface variables using the stable non-mutable UID stored
        # in the factory keys. This preserves the original port object and its
        # semantic reference even when runtime connections have aliased the
        # mutable ``uid`` to another connected variable.
        in_vars: List[Var] = list()
        for v_uid in data.get("in_vars", list()):
            in_var: Var | None = self._var_identity_lookup.get(v_uid, None)
            if in_var is not None:
                in_vars.append(in_var)
            else:
                self._add_warning(msg="Missing input symbolic variable while parsing dynamic block",
                                  block_name=block_name,
                                  block_uid=block_uid_value,
                                  field_name="in_vars",
                                  missing_uid=v_uid)

        # Apply the same stable lookup to outputs for consistency with inputs
        # and to avoid replacing exported branch variables with connected bus
        # variables after deserialization.
        out_vars: List[Var] = list()
        for v_uid in data.get("out_vars", list()):
            out_var: Var | None = self._var_identity_lookup.get(v_uid, None)
            if out_var is not None:
                out_vars.append(out_var)
            else:
                self._add_warning(msg="Missing output symbolic variable while parsing dynamic block",
                                  block_name=block_name,
                                  block_uid=block_uid_value,
                                  field_name="out_vars",
                                  missing_uid=v_uid)

        # Historical files may store child records inline, reference a missing
        # child from the short-lived pointer format, or contain an accidental
        # cyclic edge. Keep all valid children and report only the invalid edge.
        children: List[Block] = list()
        child_entry: Any
        for child_entry in data.get("children", list()):
            if isinstance(child_entry, dict):
                child_uid: int | None = normalize_persisted_block_uid(child_entry.get("uid", None))
            else:
                child_uid = normalize_persisted_block_uid(child_entry)

            if child_uid is None:
                self._add_warning(msg="Invalid child dynamic block UID in persisted symbolic data",
                                  block_name=block_name,
                                  block_uid=block_uid_value,
                                  field_name="children",
                                  missing_uid=None)
            elif child_uid in active_ancestor_uids:
                self._add_warning(msg="Cyclic child dynamic block reference ignored while parsing persisted data",
                                  block_name=block_name,
                                  block_uid=block_uid_value,
                                  field_name="children",
                                  missing_uid=child_uid)
            elif child_uid not in blocks_data:
                self._add_warning(msg="Missing child dynamic block while parsing persisted symbolic data",
                                  block_name=block_name,
                                  block_uid=block_uid_value,
                                  field_name="children",
                                  missing_uid=child_uid)
            else:
                child_block: Block = self._parse_normalized_block(blocks_data=blocks_data,
                                                                  main_block_uid=child_uid,
                                                                  ancestor_uids=active_ancestor_uids)
                children.append(child_block)

        init_eqs: Dict[Var, Expr] = dict()
        entry: Dict[str, Any]
        for entry in data.get("init_eqs", list()):
            var = self._resolve_var_or_warn(entry.get("var", None), block_name, block_uid_value, "init_eqs")
            if var is not None:
                init_eqs[var] = parse_expr(data=entry["expr"],
                                           const_dict=self.var_factory.get_const_dict(),
                                           var_dict=self._var_identity_lookup,
                                           diff_var_dict=self._diff_var_identity_lookup,
                                           composite_expressions=composite_expressions)
            else:
                pass

        diff_init_eqs: Dict[Var, Expr] = dict()
        for entry in data.get("diff_init_eqs", list()):
            diff_var_entry = self._resolve_diff_var_or_warn(entry.get("var", None),
                                                            block_name,
                                                            block_uid_value,
                                                            "diff_init_eqs")
            if diff_var_entry is not None:
                diff_init_eqs[diff_var_entry] = parse_expr(data=entry["expr"],
                                                           const_dict=self.var_factory.get_const_dict(),
                                                           var_dict=self._var_identity_lookup,
                                                           diff_var_dict=self._diff_var_identity_lookup,
                                                           composite_expressions=composite_expressions)
            else:
                pass

        event_dict: Dict[Var, Expr] = dict()
        for entry in data.get("event_dict", list()):
            var = self._resolve_var_or_warn(entry.get("var", None), block_name, block_uid_value, "event_dict")
            if var is not None:
                event_dict[var] = parse_expr(data=entry["expr"],
                                             const_dict=self.var_factory.get_const_dict(),
                                             var_dict=self._var_identity_lookup,
                                             diff_var_dict=self._diff_var_identity_lookup,
                                             composite_expressions=composite_expressions)
            else:
                pass

        mode_dict: Dict[Var, Expr] = dict()
        for entry in data.get("mode_dict", list()):
            var = self._resolve_var_or_warn(entry.get("var", None), block_name, block_uid_value, "mode_dict")
            if var is not None:
                mode_dict[var] = parse_expr(data=entry["expr"],
                                            const_dict=self.var_factory.get_const_dict(),
                                            var_dict=self._var_identity_lookup,
                                            diff_var_dict=self._diff_var_identity_lookup,
                                            composite_expressions=composite_expressions)
            else:
                pass

        discrete_eqs: Dict[Var, Expr] = dict()
        for entry in data.get("discrete_eqs", list()):
            var = self._resolve_var_or_warn(entry.get("var", None), block_name, block_uid_value, "discrete_eqs")
            if var is not None:
                discrete_eqs[var] = parse_expr(data=entry["expr"],
                                               const_dict=self.var_factory.get_const_dict(),
                                               var_dict=self._var_identity_lookup,
                                               diff_var_dict=self._diff_var_identity_lookup,
                                               composite_expressions=composite_expressions)
            else:
                pass

        boolean_guards: Dict[Var, Expr] = dict()
        for entry in data.get("boolean_guards", list()):
            var = self._resolve_var_or_warn(entry.get("var", None), block_name, block_uid_value, "boolean_guards")
            if var is not None:
                boolean_guards[var] = parse_expr(data=entry["expr"],
                                                 const_dict=self.var_factory.get_const_dict(),
                                                 var_dict=self._var_identity_lookup,
                                                 diff_var_dict=self._diff_var_identity_lookup,
                                                 composite_expressions=composite_expressions)
            else:
                pass

        parameters: Dict[Var, Const] = dict()
        for entry in data.get("parameters", list()):
            var = self._resolve_var_or_warn(entry.get("var", None), block_name, block_uid_value, "parameters")
            if var is not None:
                parameters[var] = Const(entry["value"])
            else:
                pass

        init_values: Dict[Var, Const] = dict()
        for entry in data.get("init_values", list()):
            var = self._resolve_var_or_warn(entry.get("var", None), block_name, block_uid_value, "init_values")
            if var is not None:
                init_values[var] = Const(entry["value"])
            else:
                pass

        external_mapping: Dict[VarPowerFlowReferenceType, Var | None] = dict()
        key_str: str
        var_uid: int | None
        for key_str, var_uid in data.get("external_mapping", dict()).items():
            key: VarPowerFlowReferenceType = VarPowerFlowReferenceType(key_str)
            if var_uid is None:
                # Legacy files use explicit nulls for optional power-flow
                # references, so retaining the empty slot is not data loss.
                external_mapping[key] = None
            else:
                # Rebuild PF-exposed mappings using the stable symbolic
                # identity. A non-null UID that is absent from both factory
                # dictionaries is a broken persisted reference and matters to
                # the user even though parsing can continue without it.
                var_in_varfactory: Var | None = self._find_var_or_diff_var_by_non_mutable_uid(var_uid)
                if var_in_varfactory is not None:
                    external_mapping[key] = var_in_varfactory
                else:
                    external_mapping[key] = None
                    self._add_warning(msg="Missing symbolic variable while parsing dynamic block",
                                      block_name=block_name,
                                      block_uid=block_uid_value,
                                      field_name="external_mapping",
                                      missing_uid=var_uid)

        api_obj_mapping: Dict[ParamPowerFlowReferenceType, Var] = dict()
        for key_str, var_uid in data.get("api_obj_mapping", dict()).items():
            key: ParamPowerFlowReferenceType = ParamPowerFlowReferenceType(key_str)
            if var_uid is None:
                # Older dynamic models persist optional API mappings as null.
                # The missing target is intentional and must not be presented
                # as a damaged symbolic reference in the open-file logger.
                pass
            else:
                # Non-null mapping UIDs are expected to identify a real
                # variable because dropping them can prevent static parameters
                # from reaching the dynamic model.
                api_var: Var | None = self._resolve_var_or_warn(var_uid,
                                                                block_name,
                                                                block_uid_value,
                                                                "api_obj_mapping")
                if api_var is not None:
                    api_obj_mapping[key] = api_var
                else:
                    pass

        reformulated_vars: List[Var] = list()
        for v_uid in data.get("reformulated_vars", list()):
            reformulated_var: Var | None = self._resolve_var_or_warn(v_uid,
                                                                     block_name,
                                                                     block_uid_value,
                                                                     "reformulated_vars")
            if reformulated_var is not None:
                reformulated_vars.append(reformulated_var)
            else:
                pass

        block = Block(
            state_vars=state_vars,
            state_eqs=state_eqs,
            algebraic_vars=algebraic_vars,
            algebraic_eqs=algebraic_eqs,
            inequalities=inequalities,
            diff_vars=diff_vars,
            differential_eqs=differential_eqs,
            in_vars=in_vars,
            out_vars=out_vars,
            init_eqs=init_eqs,
            diff_init_eqs=diff_init_eqs,
            discrete_eqs=discrete_eqs,
            event_dict=event_dict,
            mode_dict=mode_dict,
            boolean_guards=boolean_guards,
            # Rebuild the executable procedural-logic objects from the typed
            # JSON representation emitted by ``BlockSaver``.  The helper also
            # accepts legacy in-memory objects for backwards compatibility.
            procedural_logic=Block._procedural_logic_from_dict(
                data=list(data.get("procedural_logic", list()))
            ),
            children=children,  # TODO think about this
            parameters=parameters,
            init_values=init_values,
            external_mapping=external_mapping,
            api_obj_mapping=api_obj_mapping,
            reformulated_vars=reformulated_vars,
            name=block_name,
            uid=block_uid_value
        )

        # Children have already been parsed, so both current stable variable
        # UIDs and legacy positional port references can now be resolved.
        persisted_intent: object
        for persisted_intent in data.get("connection_intents", list()):
            if isinstance(persisted_intent, dict):
                parsed_intent: DynamicConnectionIntent | None = dynamic_connection_intent_from_dict(
                    data=persisted_intent,
                    root_block=block,
                )
                if parsed_intent is not None:
                    block.connection_intents.append(parsed_intent)
                else:
                    self._add_warning(msg="Invalid dynamic connection intent ignored while parsing persisted data",
                                      block_name=block_name,
                                      block_uid=block_uid_value,
                                      field_name="connection_intents",
                                      missing_uid=None)
            else:
                self._add_warning(msg="Invalid dynamic connection intent ignored while parsing persisted data",
                                  block_name=block_name,
                                  block_uid=block_uid_value,
                                  field_name="connection_intents",
                                  missing_uid=None)
        normalize_dynamic_connection_intents(block=block)

        diagram_data = data.get("diagram", None)
        if diagram_data is not None:
            block.diagram.parse(diagram_data)

        self.block_dict[block.uid] = block

        return block


def block_deep_copy(block: Block, var_factory: VarFactory):
    """
    Create depp copy of a block
    :param block:
    :param var_factory:
    :return:
    """
    # TODO: avoid passing to json
    saver = BlockSaver(var_factory)
    d = saver.save_block(block, main=True)
    const_save = saver.get_const_to_save()
    vars_save = saver.get_vars_to_save()
    diff_vars_save = saver.get_diff_vars_to_save()
    blocks = saver.get_blocks()

    parser = BlockParser(VarFactory())
    parser.parse_consts(data=const_save)
    parser.parse_vars(data=vars_save)
    parser.parse_diff_vars(data=diff_vars_save)
    block2 = parser.parse_block(blocks, block.uid)

    return block2


def duplicate_var(var_factory: VarFactory, old_to_new_var: Dict[int, Var], var: Var | None) -> Var | None:
    """
    Duplicate one symbolic variable while preserving UID-based reuse.

    The helper now accepts ``None`` because some FMU/EMT external mappings intentionally
    leave optional references unresolved. In those cases the missing mapping must stay
    missing after the block clone.

    :param var_factory: Variable factory used to allocate the cloned variable.
    :param old_to_new_var: UID-to-variable clone map.
    :param var: Source variable or ``None``.
    :return: Cloned variable or ``None``.
    """
    if var is None:
        new_var: Var | None = None
    else:
        if var.uid in old_to_new_var:
            new_var = old_to_new_var[var.uid]
        else:
            base_var_new: Var | None = None
            if var.base_var is not None:
                base_var_new = duplicate_required_var(var_factory, old_to_new_var, var.base_var)

                # Differential variables must be linked to the cloned base variable. Passing the
                # original differential pointer here would reconnect the new chain to the source.
                new_var = var_factory.add_diff_var(
                    name=var.name,
                    reference=var.ref,
                    network_conn=var.network_conn,
                    shared_reference=var.shared_ref,
                    diff_var=None,
                    base_var=base_var_new
                )

            else:
                # Base variables are allocated without pulling their derivative pointer through.
                # The derivative clone will attach itself when it is duplicated.
                new_var = var_factory.add_var(
                    name=var.name,
                    reference=var.ref,
                    network_conn=var.network_conn,
                    shared_reference=var.shared_ref,
                )

            old_to_new_var[var.uid] = new_var

    return new_var


def duplicate_required_var(var_factory: VarFactory, old_to_new_var: Dict[int, Var], var: Var) -> Var:
    """
    Duplicate a variable that must exist in the source block structure.

    :param var_factory: Variable factory used to allocate the cloned variable.
    :param old_to_new_var: UID-to-variable clone map.
    :param var: Source variable.
    :return: Cloned variable.
    """
    new_var: Var | None = duplicate_var(var_factory, old_to_new_var, var)
    if new_var is None:
        raise TypeError("duplicate_required_var: source variable cannot be None")
    else:
        return new_var


def duplicate_const(var_factory: VarFactory,
                    old_to_new_const: Dict[int, Const],
                    const: Const) -> Const:
    """

    :param var_factory:
    :param old_to_new_const:
    :param const:
    :return:
    """
    if const.uid in old_to_new_const:
        return old_to_new_const[const.uid]

    new_const = var_factory.add_const(value=const.value, name=const.name)
    old_to_new_const[const.uid] = new_const
    return new_const


def duplicate_expr(var_factory: VarFactory,
                   old_to_new_const: Dict[int, Const],
                   old_to_new_var: Dict[int, Var],
                   expr: Expr) -> Expr:
    """

    :param var_factory:
    :param old_to_new_const:
    :param old_to_new_var:
    :param expr:
    :return:
    """
    if isinstance(expr, Var):
        return duplicate_required_var(var_factory, old_to_new_var, expr)
    if isinstance(expr, Const):
        return duplicate_const(var_factory, old_to_new_const, expr)
    if isinstance(expr, BinOp):
        return BinOp(
            duplicate_expr(var_factory, old_to_new_const, old_to_new_var, expr.left),
            expr.op,
            duplicate_expr(var_factory, old_to_new_const, old_to_new_var, expr.right)
        )
    if isinstance(expr, UnOp):
        return UnOp(expr.op, duplicate_expr(var_factory, old_to_new_const, old_to_new_var, expr.operand))
    if isinstance(expr, Func):
        return Func(duplicate_expr(var_factory, old_to_new_const, old_to_new_var, expr.arg), expr.op)
    if isinstance(expr, Func2):
        return Func2(expr.name,
                     duplicate_expr(var_factory, old_to_new_const, old_to_new_var, expr.arg1),
                     duplicate_expr(var_factory, old_to_new_const, old_to_new_var, expr.arg2))
    return expr


def _remember_var(var: Var | None, vars_by_uid: Dict[int, Var]) -> None:
    """
    Collect one variable and its derivative chain by uid.

    :param var: Variable to collect, or ``None`` for optional mappings.
    :param vars_by_uid: Accumulator keyed by source variable UID.
    :return: Nothing.
    """
    if var is None:
        pass
    else:
        if var.uid in vars_by_uid:
            pass
        else:
            vars_by_uid[var.uid] = var
            _remember_var(var.base_var, vars_by_uid)
            _remember_var(var.diff_var, vars_by_uid)


def _remember_expr_vars(expr: Expr, vars_by_uid: Dict[int, Var]) -> None:
    """
    Collect variables referenced by one expression.

    :param expr: Expression to scan.
    :param vars_by_uid: Accumulator keyed by source variable UID.
    :return: Nothing.
    """
    var: Var
    for var in expr.get_vars():
        _remember_var(var, vars_by_uid)


def _collect_block_vars_by_uid(block: Block, vars_by_uid: Dict[int, Var] | None = None) -> Dict[int, Var]:
    """
    Collect all variables reachable from a block, including expression-only references.

    :param block: Block to scan.
    :param vars_by_uid: Optional accumulator for recursive child scans.
    :return: Variables keyed by source UID.
    """
    if vars_by_uid is None:
        result: Dict[int, Var] = dict()
    else:
        result = vars_by_uid

    for var_list in (
            block.state_vars,
            block.algebraic_vars,
            block.diff_vars,
            block.reformulated_vars,
            block.in_vars,
            block.out_vars,
    ):
        var: Var
        for var in var_list:
            _remember_var(var, result)

    for mapping in (
            block.parameters,
            block.init_values,
            block.init_eqs,
            block.diff_init_eqs,
            block.discrete_eqs,
            block.event_dict,
            block.mode_dict,
    ):
        mapping_key: Var
        mapping_value: Expr
        for mapping_key, mapping_value in mapping.items():
            _remember_var(mapping_key, result)
            if isinstance(mapping_value, Expr):
                _remember_expr_vars(mapping_value, result)
            else:
                pass

    external_var: Var | None
    for external_var in block.external_mapping.values():
        _remember_var(external_var, result)

    api_var: Var | None
    for api_var in block.api_obj_mapping.values():
        _remember_var(api_var, result)

    for expr_list in (
            block.state_eqs,
            block.algebraic_eqs,
            block.differential_eqs,
    ):
        expr: Expr
        for expr in expr_list:
            _remember_expr_vars(expr, result)

    child: Block
    for child in block.children:
        _collect_block_vars_by_uid(child, result)

    return result


def _build_var_mapping(old_vars_by_uid: Dict[int, Var], old_to_new_var: Dict[int, Var]) -> Dict[Expr | str, Expr]:
    """
    Build the object/name substitution map used by procedural logic cloning.

    :param old_vars_by_uid: Source variables keyed by UID.
    :param old_to_new_var: Cloned variables keyed by source UID.
    :return: Procedural logic variable substitution map.
    """
    mapping: Dict[Expr | str, Expr] = dict()
    uid: int
    old_var: Var
    for uid, old_var in old_vars_by_uid.items():
        new_var: Var | None = old_to_new_var.get(uid, None)
        if new_var is not None:
            mapping[old_var] = new_var
            mapping[old_var.name] = new_var
        else:
            pass
    return mapping


def _duplicate_block(block: Block,
                     var_factory: VarFactory,
                     old_to_new_var: Dict[int, Var],
                     old_to_new_const: Dict[int, Const],
                     old_to_new_block_uid: Dict[int, int]) -> Block:
    """
    Duplicate a block using shared maps so child/parent variable links remain coherent.

    :param block: Source block.
    :param var_factory: Variable factory used to allocate cloned variables and constants.
    :param old_to_new_var: UID-to-variable clone map shared across the block tree.
    :param old_to_new_const: UID-to-constant clone map shared across the block tree.
    :param old_to_new_block_uid: Source-to-clone block UID map shared across the block tree.
    :return: Duplicated block.
    """
    old_vars_by_uid: Dict[int, Var] = _collect_block_vars_by_uid(block)

    for old_var in old_vars_by_uid.values():
        duplicate_var(var_factory, old_to_new_var, old_var)

    const: Const
    for const in block.parameters.values():
        duplicate_const(var_factory, old_to_new_const, const)

    for const in block.init_values.values():
        duplicate_const(var_factory, old_to_new_const, const)

    # Clone the variable containers from the shared UID map so every repeated
    # reference inside the source block points to the same cloned object.
    new_state_vars: List[Var] = [duplicate_required_var(var_factory, old_to_new_var, v) for v in block.state_vars]
    new_algebraic_vars: List[Var] = [
        duplicate_required_var(var_factory, old_to_new_var, v)
        for v in block.algebraic_vars
    ]
    new_diff_vars: List[Var] = [duplicate_required_var(var_factory, old_to_new_var, v) for v in block.diff_vars]
    new_reformulated_vars: List[Var] = [
        duplicate_required_var(var_factory, old_to_new_var, v)
        for v in block.reformulated_vars
    ]
    new_in_vars: List[Var] = [duplicate_required_var(var_factory, old_to_new_var, v) for v in block.in_vars]
    new_out_vars: List[Var] = [duplicate_required_var(var_factory, old_to_new_var, v) for v in block.out_vars]

    # Clone equations after all variables are known, otherwise expression-only
    # variables could accidentally diverge from the block variable containers.
    new_state_eqs: List[Expr] = [
        duplicate_expr(var_factory, old_to_new_const, old_to_new_var, e)
        for e in block.state_eqs
    ]
    new_algebraic_eqs: List[Expr] = [
        duplicate_expr(var_factory, old_to_new_const, old_to_new_var, e)
        for e in block.algebraic_eqs
    ]
    new_differential_eqs: List[Expr] = [
        duplicate_expr(var_factory, old_to_new_const, old_to_new_var, e)
        for e in block.differential_eqs
    ]

    new_init_eqs: Dict[Var, Expr] = {
        duplicate_required_var(var_factory, old_to_new_var, k): duplicate_expr(
            var_factory,
            old_to_new_const,
            old_to_new_var,
            v,
        )
        for k, v in block.init_eqs.items()
    }

    new_diff_init_eqs: Dict[Var, Expr] = {
        duplicate_required_var(var_factory, old_to_new_var, k): duplicate_expr(
            var_factory,
            old_to_new_const,
            old_to_new_var,
            v,
        )
        for k, v in block.diff_init_eqs.items()
    }

    new_discrete_eqs: Dict[Var, Expr] = {
        duplicate_required_var(var_factory, old_to_new_var, k): duplicate_expr(
            var_factory,
            old_to_new_const,
            old_to_new_var,
            v,
        )
        for k, v in block.discrete_eqs.items()
    }

    new_event_dict: Dict[Var, Expr] = {
        duplicate_required_var(var_factory, old_to_new_var, k): duplicate_expr(
            var_factory,
            old_to_new_const,
            old_to_new_var,
            v,
        )
        for k, v in block.event_dict.items()
    }

    new_mode_dict: Dict[Var, Expr] = {
        duplicate_required_var(var_factory, old_to_new_var, k): duplicate_expr(
            var_factory,
            old_to_new_const,
            old_to_new_var,
            v,
        )
        for k, v in block.mode_dict.items()
    }

    new_parameters: Dict[Var, Const] = {
        duplicate_required_var(var_factory, old_to_new_var, k): duplicate_const(var_factory, old_to_new_const, v)
        for k, v in block.parameters.items()
    }

    new_init_values: Dict[Var, Const] = {
        duplicate_required_var(var_factory, old_to_new_var, k): duplicate_const(var_factory, old_to_new_const, v)
        for k, v in block.init_values.items()
    }

    new_external_mapping: Dict[VarPowerFlowReferenceType, Var | None] = {
        k: duplicate_var(var_factory, old_to_new_var, v)
        for k, v in block.external_mapping.items()
    }
    new_api_obj_mapping: Dict[ParamPowerFlowReferenceType, Var | None] = {
        k: duplicate_var(var_factory, old_to_new_var, v)
        for k, v in block.api_obj_mapping.items()
    }

    new_children: List[Block] = [
        _duplicate_block(child, var_factory, old_to_new_var, old_to_new_const, old_to_new_block_uid)
        for child in block.children
    ]

    if block.procedural_logic:
        from VeraGridEngine.Utils.procedural_logic import clone_procedural_logic_entries
        new_procedural_logic: List[Any] = clone_procedural_logic_entries(
            entries=block.procedural_logic,
            var_mapping=_build_var_mapping(old_vars_by_uid, old_to_new_var),
        )
    else:
        new_procedural_logic = list()

    new_block = Block(
        state_vars=new_state_vars,
        state_eqs=new_state_eqs,
        algebraic_vars=new_algebraic_vars,
        algebraic_eqs=new_algebraic_eqs,
        diff_vars=new_diff_vars,
        reformulated_vars=new_reformulated_vars,
        differential_eqs=new_differential_eqs,
        parameters=new_parameters,
        init_values=new_init_values,
        init_eqs=new_init_eqs,
        diff_init_eqs=new_diff_init_eqs,
        discrete_eqs=new_discrete_eqs,
        children=new_children,
        in_vars=new_in_vars,
        out_vars=new_out_vars,
        event_dict=new_event_dict,
        mode_dict=new_mode_dict,
        procedural_logic=new_procedural_logic,
        external_mapping=new_external_mapping,
        api_obj_mapping=new_api_obj_mapping,
        name=block.name,
    )

    # Intent targets use stable block and variable identities. Rebuild both
    # identities after the complete cloned child subtree has been allocated.
    old_to_new_block_uid[block.uid] = new_block.uid
    source_intent: DynamicConnectionIntent
    source_internal_block: Block | None
    source_internal_var: Var | None
    source_candidate_block: Block
    source_candidate_var: Var
    source_variables: List[Var]
    cloned_internal_block_uid: int | None
    cloned_internal_var: Var | None

    for source_intent in block.connection_intents:
        source_internal_block = None
        for source_candidate_block in block.get_all_blocks():
            if source_candidate_block.uid == source_intent.get_internal_block_uid():
                source_internal_block = source_candidate_block
            else:
                pass

        source_internal_var = None
        if source_internal_block is None:
            source_variables = list()
        elif source_intent.get_direction() == DynamicConnectionIntentDirection.INPUT:
            source_variables = source_internal_block.in_vars
        else:
            source_variables = source_internal_block.out_vars

        for source_candidate_var in source_variables:
            if source_candidate_var.non_mutable_uid == source_intent.get_internal_variable_uid():
                source_internal_var = source_candidate_var
            else:
                pass

        cloned_internal_block_uid = old_to_new_block_uid.get(source_intent.get_internal_block_uid(), None)
        if source_internal_var is None:
            cloned_internal_var = None
        else:
            cloned_internal_var = old_to_new_var.get(source_internal_var.uid, None)

        if cloned_internal_block_uid is None or cloned_internal_var is None:
            pass
        else:
            new_block.connection_intents.append(DynamicConnectionIntent(
                origin=source_intent.get_origin(),
                root_reference=source_intent.get_root_reference(),
                direction=source_intent.get_direction(),
                internal_block_uid=cloned_internal_block_uid,
                internal_variable_uid=cloned_internal_var.non_mutable_uid,
                suppressed=source_intent.is_suppressed(),
            ))

    normalize_dynamic_connection_intents(block=new_block)

    extra_key: str
    extra_value: Any
    for extra_key, extra_value in block.__dict__.items():
        if extra_key in new_block.__dict__:
            pass
        else:
            setattr(new_block, extra_key, copy.deepcopy(extra_value))

    return new_block


def duplicate_block(block: Block, var_factory: VarFactory | None) -> Block:
    """
    Create a duplicate of this block with new variable UIDs.

    The new block contains variables with the same names but different UIDs,
    and equations rebuilt using those new variables.

    :param block: Source block.
    :param var_factory: Variable factory used to allocate cloned variables and constants.
    :return: A new Block with duplicated variables and equations.
    """
    if var_factory is None:
        raise TypeError("duplicate_block: var_factory cannot be None")
    else:
        return _duplicate_block(
            block=block,
            var_factory=var_factory,
            old_to_new_var=dict(),
            old_to_new_const=dict(),
            old_to_new_block_uid=dict(),
        )


def compare_blocks(block1: Block, block2: Block, var_factory1: VarFactory, var_factory2: VarFactory, testing=False):
    """
    Create depp copy of a block
    :param block1:
    :param block2:
    :param var_factory:
    :param testing:
    :return:
    """
    # TODO: do not use dictionaries and compare directly using the block information
    saver1 = BlockSaver(var_factory1)
    d1 = saver1.save_block(block1, main=False)
    const_save1 = saver1.get_const_to_save()
    vars_save1 = saver1.get_vars_to_save()
    diff_vars_save1 = saver1.get_diff_vars_to_save()
    blocks1 = saver1.get_blocks()

    saver2 = BlockSaver(var_factory2)
    d2 = saver2.save_block(block2, main=False)
    const_save2 = saver2.get_const_to_save()
    vars_save2 = saver2.get_vars_to_save()
    diff_vars_save2 = saver2.get_diff_vars_to_save()
    blocks2 = saver2.get_blocks()

    return (blocks1, const_save1, vars_save1, diff_vars_save1) == (blocks2, const_save2, vars_save2, diff_vars_save2)
