# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import Dict, Any, List

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Expr, Const, BinOp, UnOp, Func, Func2
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType, ParamPowerFlowRefferenceType


def symbolic_objects_to_dict(obj_dict: Dict[int, Var | Const | Var]) -> List[Dict[str, Any]]:
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

            if expr.base_var is not None:
                if type(expr.ref) == str:
                    lst.append({
                        "type": "DiffVar",
                        "name": expr.name,
                        "uid": expr.uid,
                        "base_var": expr.base_var.uid,
                        "ref": expr.ref if expr.ref is not None else None,
                    })
                else:
                    lst.append({
                        "type": "DiffVar",
                        "name": expr.name,
                        "uid": expr.uid,
                        "base_var": expr.base_var.uid,
                        "ref": expr.ref.value if expr.ref is not None else None,
                    })



            else:
                # it is a normal var
                if type(expr.ref) == str:
                    lst.append({"type": "Var",
                                "name": expr.name,
                                "uid": expr.uid,
                                "base_var": None,
                                "ref": expr.ref if expr.ref is not None else None})
                else:
                    lst.append({"type": "Var",
                                "name": expr.name,
                                "uid": expr.uid,
                                "base_var": None,
                                "ref": expr.ref.value if expr.ref is not None else None})



    return lst


def expr_to_dict(expr: Expr,
                 const_dict: Dict[int, Const],
                 var_dict: Dict[int, Var],
                 diff_var_dict: Dict[int, Var]) -> Dict[str, Any]:
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
    :return: Dict to save in jason
    """

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

            c = diff_var_dict.get(expr.uid, None)

            if c is None:
                # add it to the references dict
                diff_var_dict[expr.uid] = expr

            # the diffvar already exists
            return {
                "type": "DiffVar",
                "uid": expr.uid
            }

        else:
            c = var_dict.get(expr.uid, None)

            if c is None:
                # add it to the references dict
                var_dict[expr.uid] = expr

            # the var already exists
            return {
                "type": "Var",
                "uid": expr.uid
            }

    elif isinstance(expr, BinOp):
        return {
            "type": "BinOp",
            "op": expr.op,
            "left": expr_to_dict(expr=expr.left,
                                 const_dict=const_dict, var_dict=var_dict, diff_var_dict=diff_var_dict),
            "right": expr_to_dict(expr=expr.right,
                                  const_dict=const_dict, var_dict=var_dict, diff_var_dict=diff_var_dict),
            "uid": expr.uid,
        }

    elif isinstance(expr, UnOp):
        return {
            "type": "UnOp",
            "op": expr.op,  # only \"-\" for now
            "operand": expr_to_dict(expr=expr.operand,
                                    const_dict=const_dict, var_dict=var_dict, diff_var_dict=diff_var_dict),
            "uid": expr.uid,
        }

    elif isinstance(expr, Func):
        return {
            "type": "Func",
            "op": expr.op,  # sin, cos, log, …
            "arg": expr_to_dict(expr=expr.arg,
                                const_dict=const_dict, var_dict=var_dict, diff_var_dict=diff_var_dict),
            "uid": expr.uid,
        }

    else:
        raise TypeError(f"Unsupported Expr subclass: {type(expr).__name__}")


def expr_list_to_list(lst: List[Expr],
                      const_dict: Dict[int, Const],
                      var_dict: Dict[int, Var],
                      diff_var_dict: Dict[int, Var]) -> List[Dict[str, Any]]:
    """

    :param lst:
    :param const_dict:
    :param var_dict:
    :param diff_var_dict:
    :return:
    """
    lst2: List[Dict[str, Any]] = list()

    for expr in lst:
        lst2.append(
            expr_to_dict(expr=expr,
                         const_dict=const_dict,
                         var_dict=var_dict,
                         diff_var_dict=diff_var_dict)
        )
    return lst2


def parse_expr(data: Dict[str, Any],
               const_dict: Dict[int, Const],
               var_dict: Dict[int, Var],
               diff_var_dict: Dict[int, Var]) -> Const | Var | Var | UnOp | BinOp | Func:
    """
    De-Serialize expression from dictionary
    :param data: Some dictionary containing the expression
    :param const_dict: Dictionary that keeps a reference of the Const objects already saved
    :param var_dict: Dictionary that keeps a reference of the VAr objects already saved
    :param diff_var_dict: Dictionary that keeps a reference of the DiffVar objects already saved
    :return: Expression chil
    """
    t = data["type"]

    if t == "Const":
        return const_dict[data["uid"]]

    elif t == "Var":
        return var_dict[data["uid"]]

    elif t == "DiffVar":

        return diff_var_dict[data["uid"]]

    elif t == "BinOp":
        left = parse_expr(data=data["left"],
                          const_dict=const_dict,
                          var_dict=var_dict,
                          diff_var_dict=diff_var_dict)

        right = parse_expr(data=data["right"],
                           const_dict=const_dict,
                           var_dict=var_dict,
                           diff_var_dict=diff_var_dict)

        obj = BinOp(left=left, op=data["op"], right=right, uid=data["uid"])

    elif t == "UnOp":
        operand = parse_expr(data=data["operand"],
                             const_dict=const_dict,
                             var_dict=var_dict,
                             diff_var_dict=diff_var_dict)
        obj = UnOp(op=data["op"], operand=operand, uid=data["uid"])

    elif t == "Func":
        arg = parse_expr(data=data["arg"],
                         const_dict=const_dict,
                         var_dict=var_dict,
                         diff_var_dict=diff_var_dict)

        obj = Func(arg=arg, op=data["op"], uid=data["uid"])

    else:
        raise ValueError(f"Unknown type '{t}' in symbolic deserialization")

    return obj


def parse_expr_list(lst: List[Dict[str, Any]],
                    const_dict: Dict[int, Const],
                    var_dict: Dict[int, Var],
                    diff_var_dict: Dict[int, Var]) -> List[Const | Var | Var | UnOp | BinOp | Func]:
    """

    :param lst:
    :param const_dict:
    :param var_dict:
    :param diff_var_dict:
    :return:
    """
    lst2 = list()
    for data in lst:
        lst2.append(
            parse_expr(
                data=data,
                const_dict=const_dict,
                var_dict=var_dict,
                diff_var_dict=diff_var_dict
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
            found_var = self.var_factory.get_var(var.uid)
        except Exception:
            found_var = None

        if found_var is None:
            self.var_factory._var_dict[var.uid] = var
        else:
            pass

    def _ensure_diff_var_registered(self, diff_var: Var) -> None:
        """
        Ensure that one differential variable is present in the shared variable factory.

        :param diff_var: Differential variable to register.
        :return: None.
        """
        try:
            found_var = self.var_factory.get_diff_var(diff_var.uid)
        except Exception:
            found_var = None

        if found_var is None:
            self.var_factory._diff_var_dict[diff_var.uid] = diff_var
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
        state_expressions = expr_list_to_list(
            lst=blk.state_eqs,
            const_dict=self.var_factory.get_const_dict(),
            var_dict=self.var_factory.get_vars_dict(),
            diff_var_dict=self.var_factory.get_diff_var_dict()
        )

        algebraic_expressions = expr_list_to_list(
            lst=blk.algebraic_eqs,
            const_dict=self.var_factory.get_const_dict(),
            var_dict=self.var_factory.get_vars_dict(),
            diff_var_dict=self.var_factory.get_diff_var_dict()
        )

        differential_eqs_expressions = expr_list_to_list(
            lst=blk.differential_eqs,
            const_dict=self.var_factory.get_const_dict(),
            var_dict=self.var_factory.get_vars_dict(),
            diff_var_dict=self.var_factory.get_diff_var_dict()
        )

        init_eq_list = list()
        diff_init_eq_list = list()
        for var, expr in blk.init_eqs.items():
            self._ensure_var_registered(var)

            init_eq_list.append(
                {
                    "var": var.uid,
                    "expr": expr_to_dict(
                        expr=expr,
                        const_dict=self.var_factory.get_const_dict(),
                        var_dict=self.var_factory.get_vars_dict(),
                        diff_var_dict=self.var_factory.get_diff_var_dict()
                    )
                }
            )

        for diff_var, expr in blk.diff_init_eqs.items():
            self._ensure_diff_var_registered(diff_var)

            diff_init_eq_list.append(
                {
                    "var": diff_var.uid,
                    "expr": expr_to_dict(
                        expr=expr,
                        const_dict=self.var_factory.get_const_dict(),
                        var_dict=self.var_factory.get_vars_dict(),
                        diff_var_dict=self.var_factory.get_diff_var_dict()
                    )
                }
            )

        events_list = list()
        for var, expr in blk.event_dict.items():
            self._ensure_var_registered(var)

            events_list.append(
                {
                    "var": var.uid,
                    "expr": expr_to_dict(
                        expr=expr,
                        const_dict=self.var_factory.get_const_dict(),
                        var_dict=self.var_factory.get_vars_dict(),
                        diff_var_dict=self.var_factory.get_diff_var_dict()
                    )
                }
            )

        in_vars: List[int] = list()
        for var in blk.in_vars:
            self._ensure_var_registered(var)

            in_vars.append(var.uid)

        out_vars: List[int] = list()
        for var in blk.out_vars:
            self._ensure_var_registered(var)

            out_vars.append(var.uid)

        init_values: List[Dict[str, float | int]] = list()
        for var, value in blk.init_values.items():
            self._ensure_var_registered(var)

            init_values.append({"var": var.uid, "value": value.value})

        parameters: List[Dict[str, float | int]] = list()
        for var, value in blk.parameters.items():
            self._ensure_var_registered(var)

            parameters.append({"var": var.uid, "value": value.value})

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

            "state_vars": [v.uid for v in blk.state_vars],

            "state_eqs": state_expressions,

            "algebraic_vars": [v.uid for v in blk.algebraic_vars],

            "algebraic_eqs": algebraic_expressions,

            "diff_vars": [v.uid for v in blk.diff_vars],

            "differential_eqs": differential_eqs_expressions,

            "reformulated_vars": [v.uid for v in blk.reformulated_vars],

            "init_eqs": init_eq_list,

            "diff_init_eqs": diff_init_eq_list,

            "init_values": init_values,

            "parameters": parameters,

            "external_mapping": {dyn_var_type.value: var.uid if var is not None else None
                                 for dyn_var_type, var in blk.external_mapping.items()},

            "api_obj_mapping": {dyn_param_type.value: param.uid if param is not None else None
                                for dyn_param_type, param in blk.api_obj_mapping.items()},

            "event_dict": events_list,
            "name": blk.name,
            "children": [child.uid for child in blk.children],
            "in_vars": in_vars,
            "out_vars": out_vars,

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
    )

    def __init__(self, var_factory: VarFactory):
        self.var_factory = var_factory
        self.block_dict: Dict[int, Block] = dict()

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

    def parse_diff_vars(self, data: List[Dict[str, Any]]):
        """

        :param data:
        :return:
        """
        self.var_factory.parse_diff_var_dict(data_list=data)

    def parse_block(self,
                    blocks_data: Dict[int, Dict[str, Any]],
                    main_block_uid: int) -> Block:
        """
        Parse block as
        :param main_block_uid:
        :param blocks_data:
        :return:
        """

        if main_block_uid not in blocks_data:
            main_block_uid = str(main_block_uid)

        data = blocks_data[main_block_uid]

        state_vars = [self.var_factory.get_var(v_uid) for v_uid in data["state_vars"]]

        state_eqs = parse_expr_list(lst=data["state_eqs"],
                                    const_dict=self.var_factory.get_const_dict(),
                                    var_dict=self.var_factory.get_vars_dict(),
                                    diff_var_dict=self.var_factory.get_diff_var_dict())

        algebraic_vars = [self.var_factory.get_var(v_uid) for v_uid in data["algebraic_vars"]]

        algebraic_eqs = parse_expr_list(lst=data["algebraic_eqs"],
                                        const_dict=self.var_factory.get_const_dict(),
                                        var_dict=self.var_factory.get_vars_dict(),
                                        diff_var_dict=self.var_factory.get_diff_var_dict())
        if data["diff_vars"]:
            diff_vars = [self.var_factory.get_diff_var(v_uid) for v_uid in data["diff_vars"]]
        else:
            diff_vars = []

        differential_eqs = parse_expr_list(lst=data["differential_eqs"],
                                           const_dict=self.var_factory.get_const_dict(),
                                           var_dict=self.var_factory.get_vars_dict(),
                                           diff_var_dict=self.var_factory.get_diff_var_dict())

        in_vars = [self.var_factory.get_var(v_uid) for v_uid in data["in_vars"]]

        out_vars = [self.var_factory.get_var(v_uid) for v_uid in data["out_vars"]]

        children = [self.parse_block(blocks_data, child_uid) for child_uid in data["children"]]

        init_eqs: Dict[Var, Expr] = dict()
        for entry in data["init_eqs"]:
            var = self.var_factory.get_var(entry["var"])
            init_eqs[var] = parse_expr(data=entry["expr"],
                                       const_dict=self.var_factory.get_const_dict(),
                                       var_dict=self.var_factory.get_vars_dict(),
                                       diff_var_dict=self.var_factory.get_diff_var_dict())

        event_dict: Dict[Var, Expr] = dict()
        for entry in data["event_dict"]:
            var = self.var_factory.get_var(entry["var"])
            event_dict[var] = parse_expr(data=entry["expr"],
                                         const_dict=self.var_factory.get_const_dict(),
                                         var_dict=self.var_factory.get_vars_dict(),
                                         diff_var_dict=self.var_factory.get_diff_var_dict())

        parameters: Dict[Var, Const] = dict()
        for entry in data["parameters"]:
            var = self.var_factory.get_var(entry["var"])
            parameters[var] = Const(entry["value"])

        init_values: Dict[Var, Const] = dict()
        for entry in data["init_values"]:
            var = self.var_factory.get_var(entry["var"])
            init_values[var] = Const(entry["value"])

        external_mapping: Dict[VarPowerFlowRefferenceType, Var|None] = dict()
        for key_str, var_uid in data["external_mapping"].items():
            key = VarPowerFlowRefferenceType(key_str)
            var_in_varfactory = self.var_factory.find_var_or_diff_var(var_uid)
            if var_in_varfactory is not None:
                external_mapping[key] = var_in_varfactory
            else:
                external_mapping[key] = None

        api_obj_mapping: Dict[ParamPowerFlowRefferenceType, Var] = dict()
        for key_str, var_uid in data["api_obj_mapping"].items():
            key = ParamPowerFlowRefferenceType(key_str)
            api_obj_mapping[key] = self.var_factory.get_var(var_uid)

        reformulated_vars = [self.var_factory.get_var(v_uid) for v_uid in data["reformulated_vars"]]

        block = Block(
            state_vars=state_vars,
            state_eqs=state_eqs,
            algebraic_vars=algebraic_vars,
            algebraic_eqs=algebraic_eqs,
            diff_vars=diff_vars,
            differential_eqs=differential_eqs,
            in_vars=in_vars,
            out_vars=out_vars,
            init_eqs=init_eqs,
            event_dict=event_dict,
            children=children,  # TODO think about this
            parameters=parameters,
            init_values=init_values,
            external_mapping=external_mapping,
            api_obj_mapping=api_obj_mapping,
            reformulated_vars=reformulated_vars,
            name=data["name"],
            uid=data["uid"]
        )
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
                    # diff_var=None,
                    # base_var=base_var_new
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
                     old_to_new_const: Dict[int, Const]) -> Block:
    """
    Duplicate a block using shared maps so child/parent variable links remain coherent.

    :param block: Source block.
    :param var_factory: Variable factory used to allocate cloned variables and constants.
    :param old_to_new_var: UID-to-variable clone map shared across the block tree.
    :param old_to_new_const: UID-to-constant clone map shared across the block tree.
    :return: Duplicated block.
    """
    old_vars_by_uid: Dict[int, Var] = _collect_block_vars_by_uid(block)
    old_var: Var
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

    new_external_mapping: Dict[VarPowerFlowRefferenceType, Var | None] = {
        k: duplicate_var(var_factory, old_to_new_var, v)
        for k, v in block.external_mapping.items()
    }
    new_api_obj_mapping: Dict[ParamPowerFlowRefferenceType, Var | None] = {
        k: duplicate_var(var_factory, old_to_new_var, v)
        for k, v in block.api_obj_mapping.items()
    }

    new_children: List[Block] = [
        _duplicate_block(child, var_factory, old_to_new_var, old_to_new_const)
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

    return Block(
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
