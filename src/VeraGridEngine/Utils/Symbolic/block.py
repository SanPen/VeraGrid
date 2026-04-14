# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import uuid
import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, Sequence, List, Dict, Any, Optional

from VeraGridEngine.Devices.Dynamic.events import RmsEvent
from VeraGridEngine.Devices.Parents.physical_device import PhysicalDevice
from VeraGridEngine.Utils.Symbolic.symbolic import Var, LagVar, Const, Expr, make_symbolic, UndefinedConst, cos, sin, \
    real, sqrt, atan, \
    imag, conj, angle, exp, log, abs, piecewise, DiffVar, hard_sat, f_exc
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType


def _new_uid() -> int:
    """
    Generate a fresh UUID‑v4 string.
    :return: UUIDv4 in integer format
    """
    return uuid.uuid4().int


def _serialize_expr_list(exprs: List[Expr]) -> List[Dict[str, Any]]:
    """

    :param exprs:
    :return:
    """
    return [expr.to_dict() for expr in exprs]


def _serialize_var_list(vars_: List[Var | Const]) -> List[Dict[str, Any]]:
    """
    Serialize list of variables or constants
    :param vars_: list of Var or Const
    :return: List of dictionaries with the serialized data
    """
    return [v.to_dict() for v in vars_]


def _serialize_undefinedconst_list(undefconsts_: List[UndefinedConst]) -> List[Dict[str, Any]]:
    """
    Serialize list of variables or constants
    :param vars_: list of Var or Const
    :return: List of dictionaries with the serialized data
    """
    return [undefconst.to_dict() for undefconst in undefconsts_]


def _deserialize_expr_list(expr_dicts: List[Dict[str, Any]]) -> List[Expr]:
    """

    :param expr_dicts:
    :return:
    """
    return [Expr.from_dict(d) for d in expr_dicts]


def _deserialize_var_list(var_dicts: List[Dict[str, Any]]) -> List[Var | Const | UndefinedConst]:
    """
    De-serialize previously serialized data into List of Vars or Const
    :param var_dicts: List of serialized data
    :return: List of Vars or Const
    """
    result = list()
    for d in var_dicts:
        if d["type"] == "Var":
            result.append(Var(name=d["name"], uid=d["uid"]))
        elif d["type"] == "Const":
            result.append(Const(value=d["value"], uid=d["uid"]))
        elif d['type'] == "UndefinedConst":
            result.append(UndefinedConst())
        else:
            raise ValueError(f"Unknown variable type {d['type']}")
    return result


def block2diffblock(block: Block):
    diff_block = DiffBlock.from_block(block)

    for i, eq in enumerate(block.state_eqs):
        state_var = block.state_vars[i]
        dt_var = DiffVar.get_or_create(name='dt_' + state_var.name, base_var=state_var)
        eq = eq - dt_var
        diff_block.algebraic_eqs.append(eq)
        diff_block.algebraic_vars.append(state_var)
        if dt_var not in diff_block.diff_vars:
            diff_block.diff_vars.append(dt_var)

    diff_block.state_eqs = []
    diff_block.state_vars = []

    for i, child_block in enumerate(diff_block.children):
        diff_block.children[i] = block2diffblock(child_block)

    return diff_block


def tf_to_diffblock(num: np.ndarray, den: np.ndarray, x: Var | Expr, y: Var = None, name: Optional[str] = ''):
    """
    num: list of numerator coefficients [b0, b1, ..., bm]
    den: list of denominator coefficients [a0, a1, ..., an]
    x:   sympy symbol for input
    y:   sympy function of t for output
    """
    if len(num) > len(den):
        raise ValueError("Transfer function is improper: numerator degree > denominator degree.")
    if num[-1] == 0 or den[-1] == 0:
        raise ValueError("Leading coefficient of cannot be zero.")

    if y is None:
        y = Var('y_' + name)

    aux_eqs = []
    aux_vars = []
    # check if is an expression
    if not isinstance(x, Var):
        u = Var('u_' + name)
        aux_eqs.append((u - x).simplify())
        aux_vars.append(u)
        x = u

    diff_vars_x = [x]
    diff_vars_y = [y]
    diff_vars = []
    base_var = x
    for i in range(1, len(num)):
        in_registry = base_var.uid in DiffVar._registry
        new_diff = DiffVar.get_or_create(name=f'dt_{i}_' + x.name, base_var=base_var)
        diff_vars_x.append(new_diff)
        if not in_registry:
            diff_vars.append(new_diff)
        base_var = new_diff
    base_var = y
    for i in range(1, len(den)):
        in_registry = base_var.uid in DiffVar._registry
        new_diff = DiffVar.get_or_create(name=f'dt_{i}_' + y.name, base_var=base_var)
        diff_vars_y.append(new_diff)
        if not in_registry:
            diff_vars.append(new_diff)
        base_var = new_diff

    # Create the diff equation
    rhs = np.array(diff_vars_x) @ np.array(num)
    lhs = np.array(diff_vars_y) @ np.array(den)

    block = DiffBlock()
    block.algebraic_vars = [y] + aux_vars
    block.algebraic_eqs = [lhs - rhs] + aux_eqs
    block.diff_vars = diff_vars

    return block, y


def tf_to_diffblock_with_states(num: np.ndarray, den: np.ndarray, x, y: Var = None, name: Optional[str] = ''):
    """
    num: numerator coefficients [b0,...,bm]
    den: denominator coefficients [a0,...,an], with an != 0
    u:   input Var
    y:   output Var
    """
    if len(num) > len(den):
        raise ValueError("Transfer function is improper: numerator degree > denominator degree.")
    if num[-1] == 0 or den[-1] == 0:
        raise ValueError("Leading coefficient of cannot be zero.")

    if y is None:
        y = Var('y_' + name)

    aux_eqs = []
    aux_vars = []
    # check if x is a expression
    if not isinstance(x, Var):
        u = Var('u_' + name)
        aux_eqs.append(u - x)
        aux_vars.append(u)
        x = u

    # Normalize
    den = [c / den[-1] for c in den]
    num = [c / den[-1] for c in num]

    # States
    x_states = [x]
    y_states = [y]
    y_states.extend([Var(f"y{i}") for i in range(1, len(den))])  # y1,...,yn
    x_states.extend([Var(f"x{i}") for i in range(1, len(num))])  # x1,...,xm

    # Differential equations (canonical form)
    diff_eqs = []
    diff_vars = []
    for i in range(len(y_states) - 1):
        in_registry = y_states[i].uid in DiffVar._registry
        dy = DiffVar.get_or_create(f"d_{y_states[i].name}", base_var=y_states[i])
        diff_eqs.append(y_states[i + 1] - dy)
        if not in_registry:
            diff_vars.append(dy)

    for i in range(len(num) - 1):
        in_registry = x_states[i].uid in DiffVar._registry
        dx = DiffVar.get_or_create(f"d^{i}_{x.name}", base_var=x_states[i])
        diff_eqs.append(x_states[i + 1] - dx)
        if not in_registry:
            diff_vars.append(dx)

            # Last equation: linear combination
    last_eq = (
            sum(den[i] * y_states[i] for i in range(len(y_states)))
            - sum(num[i] * x_states[i] for i in range(len(x_states)))
    )
    diff_eqs.append(last_eq)

    block = DiffBlock(
        algebraic_vars=y_states + x_states[1:] + aux_vars,
        algebraic_eqs=diff_eqs + aux_eqs,
    )
    block.diff_vars = diff_vars
    block.name = 'TF'
    return block, y_states[0]


def tf_to_block_with_states(num: np.ndarray, den: np.ndarray, x):
    """
    num: numerator coefficients [b0,...,bm]
    den: denominator coefficients [a0,...,an], with an != 0
    u:   input Expr or Var
    y:   output Var
    """
    if len(num) >= len(den):
        raise ValueError("Transfer function is improper: numerator degree > denominator degree.")
    if num[-1] == 0 or den[-1] == 0:
        raise ValueError("Leading coefficient of cannot be zero.")

    aux_eqs = []
    aux_vars = []
    # check if xis a expression
    if not isinstance(x, Var):
        u = Var('u')
        aux_eqs.append(u - x)
        aux_vars.append(u)
        x = u

    # Normalize
    den = [c / den[-1] for c in den]
    num = [c / den[-1] for c in num]

    order = len(den)  # system order
    x_states = [x]  # x0
    x_states.extend([Var(f"x{i}") for i in range(1, order + 1)])  # x1,...,xn

    # Differential equations (canonical form)
    state_eqs = []
    state_vars = []
    for i in range(1, order):
        state_eqs.append(x_states[i])
        state_vars.append(x_states[i + 1])

    y_states = [Var(f"y{i}") for i in range(len(num) + 1)]  # x1,...,xn
    for i in range(len(num)):
        state_eqs.append(y_states[i])
        state_vars.append(y_states[i + 1])

    # Last equation: linear combination
    last_eq = (
            sum(den[i] * y_states[i] for i in range(order))
            - sum(num[i] * x_states[i] for i in range(len(num)))
    )

    block = Block(
        state_eqs=state_eqs,
        state_vars=state_vars,
        algebraic_eqs=[last_eq] + aux_eqs,
        algebraic_vars=x_states[0] + y_states[0] + aux_vars,
    )
    return block, y_states[0]


class Block:
    """
    Class representing a Block
    """

    def __init__(self,
                 state_vars: List[Var] | None = None,
                 state_eqs: List[Expr] | None = None,
                 algebraic_vars: List[Var] | None = None,
                 algebraic_eqs: List[Expr] | None = None,
                 parameters: Dict[str, Const] | None = None,
                 init_eqs: Dict[Var, Expr] | None = None,
                 children: List["Block"] | None = None,
                 in_vars: List[Var] | None = None,
                 out_vars: List[Var] | None = None,
                 event_dict: Dict[Var, Expr] | None = None,
                 external_mapping: Dict[VarPowerFlowRefferenceType, Var] | None = None,
                 name: str = ""):
        """
        This represents a group of equations or a group of blocks

        :param algebraic_vars: List of non differential variables (AKA algebraic)
        :param algebraic_eqs: List of equations that provide values for the algebraic variables
        :param state_vars: List of differential variables (AKA state variables)
        :param state_eqs: List of equations that provide values for the state variables
        :param children: List of other blocks to be flattened later into this block
        :param in_vars: List of variables from other blocks that we use here
        :param out_vars: List of variables that already exist in algebraic_vars or state_vars that we want to expose
        :param init_eqs: List of equations that help initializing the block variables (algebraic and state)
        :param event_dict: Dictionary of parameters that can change during the simulations
        :param external_mapping: Dictionary of vars that are related to the Power flow initialization
        :param name: name of the block
        """

        self.name: str = name

        self.uid: int = _new_uid()
        self.vars2device: Dict[int, PhysicalDevice] = dict()
        self.vars_glob_name2uid: Dict[str, int] = dict()

        self.state_vars: List[Var] = list() if state_vars is None else state_vars
        self.state_eqs: List[Expr] = list() if state_eqs is None else state_eqs

        self.algebraic_vars: List[Var] = list() if algebraic_vars is None else algebraic_vars
        self.algebraic_eqs: List[Expr] = list() if algebraic_eqs is None else algebraic_eqs

        # initialization
        self.init_eqs: Dict[Var, Expr] = dict() if init_eqs is None else init_eqs

        # vars to make this recursive
        self.children: List["Block"] = list() if children is None else children

        self.in_vars: List[Var] = list() if in_vars is None else in_vars
        self.out_vars: List[Var] = list() if out_vars is None else out_vars

        self.parameters: Dict[str, Const] = dict() if parameters is None else parameters

        self.external_mapping: Dict[
            VarPowerFlowRefferenceType, Var] = dict() if external_mapping is None else external_mapping

        # initialization
        self.init_values: Dict[Var, Const] = dict()

        # fix vars will disappear when the exciter and governor models are decoupled from generator
        self.fix_vars: List[UndefinedConst] = list()
        self.fix_vars_eqs: Dict[Any, Expr] = dict()

        self.var_mapping = {v.name: v for v in self.algebraic_vars}

        # Dictionary of Variables and their Expressions that appear due to an event
        # this is the dictionary of "parameters" that may change and their equations
        self.event_dict: Dict[Var, Expr] = dict() if event_dict is None else event_dict

    def check_empty(self) -> bool:
        """

        :return:
        """
        return (len(self.state_vars) + len(self.algebraic_vars)) == 0

    def empty(self) -> bool:
        """

        :return:
        """
        if not self.children:
            empty = self.check_empty()
            if empty:
                return empty
        else:
            empty = self.check_empty()
            if not empty:
                return empty

            for child in self.children:
                child.empty()

        return False

    def E(self, d: VarPowerFlowRefferenceType) -> Var:
        """

        :param d:
        :return:
        """
        return self.external_mapping[d]

    def V(self, d: str) -> Var:
        """

        :param d:
        :return:
        """
        return self.var_mapping[d]

    def add(self, val: "Block"):
        """
        Add another block
        :param val: Block
        """
        self.children.append(val)

    def remove(self, val: Block):
        """
        Remove a block from block children
        :param val: Block
        """
        self.children.remove(val)

    def apply_events(self, events: List[RmsEvent]):
        """
        Apply events to this block
        :param events:
        :return:
        """
        # TODO Implement filling self.event_dicts with the RmsEvents info
        pass

    def get_all_blocks(self) -> List[Block]:
        """
        Depth-first collection of all *primitive* Blocks.
        """

        flat: List[Block] = [self]
        for el in self.children:
            flat.extend(el.get_all_blocks())

        return flat

    def get_vars(self) -> List[Var]:
        """
        Get a list of algebraic + state vars
        :return: List[Var]
        """
        return self.algebraic_vars + self.state_vars

    def get_all_vars(self):
        """

        :return:
        """
        variables: List[Var] = list()
        all_blocks = self.get_all_blocks()
        for blk in all_blocks:
            variables.extend(blk.get_vars())
        return variables

    def to_dict(self) -> Dict[str, Any]:
        """

        :return:
        """
        return {
            "uid": self.uid,
            "vars2device": {var_uid: dev.idtag for var_uid, dev in self.vars2device.items()},
            "vars_glob_name2uid": self.vars_glob_name2uid,
            "state_vars": _serialize_var_list(self.state_vars),
            "state_eqs": _serialize_expr_list(self.state_eqs),
            "algebraic_vars": _serialize_var_list(self.algebraic_vars),
            "algebraic_eqs": _serialize_expr_list(self.algebraic_eqs),
            "init_eqs": [
                {"var": var.to_dict(), "expr": expr.to_dict()}
                for var, expr in self.init_eqs.items()
            ],
            "init_values": [
                {"var": var.to_dict(), "value": value.value}
                for var, value in self.init_values.items()
            ],
            "parameters": [
                {"name": name, "value": value.value}
                for name, value in self.parameters.items()
            ],
            "fix_vars": _serialize_undefinedconst_list(self.fix_vars),
            "fix_vars_eqs": [
                {"uid": undef.uid, "expr": expr.to_dict()}
                for undef, expr in self.fix_vars_eqs.items()
            ],
            "external_mapping": {str(dynvartype): var.to_dict() for dynvartype, var in self.external_mapping.items()},
            "event_dict": [
                {"var": var.to_dict(), "expr": expr.to_dict()}
                for var, expr in self.event_dict.items()
            ],
            "name": self.name,
            "children": [child.to_dict() for child in self.children],
            "in_vars": [var.to_dict() for var in self.in_vars],
            "out_vars": [var.uid for var in self.out_vars]
        }

    @staticmethod
    def parse(data: Dict[str, Any]) -> "Block":
        """

        :param data:
        :return:
        """
        state_vars = _deserialize_var_list(data.get("state_vars", []))
        state_eqs = _deserialize_expr_list(data.get("state_eqs", []))
        algebraic_vars = _deserialize_var_list(data.get("algebraic_vars", []))
        algebraic_eqs = _deserialize_expr_list(data.get("algebraic_eqs", []))
        children = [Block.parse(child) for child in data.get("children", [])]

        algebraic_vars_dict = {v.uid: v for v in algebraic_vars}

        block = Block(
            state_vars=state_vars,
            state_eqs=state_eqs,
            algebraic_vars=algebraic_vars,
            algebraic_eqs=algebraic_eqs,
            init_eqs={},
            children=children,
            name=data.get("name", "")
        )

        block.uid = int(data.get("uid", block.uid))
        block.vars_glob_name2uid = data.get("vars_glob_name2uid", {})
        block.vars2device = {int(k): v for k, v in data.get("vars2device", {}).items()}

        for pair in data.get("init_eqs", []):
            var_dict = pair["var"]
            expr_dict = pair["expr"]
            var = Var(name=var_dict["name"], uid=var_dict.get("uid"))
            expr = Expr.from_dict(expr_dict)
            block.init_eqs[var] = expr

        for pair in data.get("init_values", []):
            var_dict = pair["var"]
            value = pair["value"]
            var = Var(name=var_dict["name"], uid=var_dict.get("uid"))
            const_value = Const(value)
            block.init_values[var] = const_value

        for pair in data.get("parameters", []):
            name = pair["name"]
            value = pair["value"]
            const_value = Const(value)
            block.init_values[name] = const_value

        fv_list = _deserialize_var_list(data.get("fix_vars", []))
        block.fix_vars = [v for v in fv_list if isinstance(v, UndefinedConst)]

        undef_by_uid = {getattr(u, "uid", None): u for u in block.fix_vars}
        for item in data.get("fix_vars_eqs", []):
            uid = item.get("uid")
            expr = Expr.from_dict(item["expr"])
            undef = undef_by_uid.get(uid)
            if undef is not None:
                block.fix_vars_eqs[undef] = expr
            else:
                new_undef = UndefinedConst()
                block.fix_vars_eqs[new_undef] = expr
                block.fix_vars.append(new_undef)

        for key_str, var_dict in data.get("external_mapping", {}).items():
            key = VarPowerFlowRefferenceType(key_str)
            var = Var(name=var_dict["name"], uid=var_dict.get("uid"))
            block.external_mapping[key] = var

        for pair in data.get("event_dict", []):
            var_dict = pair["var"]
            expr_dict = pair["expr"]
            var = Var(name=var_dict["name"], uid=var_dict.get("uid"))
            expr = Expr.from_dict(expr_dict)
            block.event_dict[var] = expr

        for pair in data.get("in_vars", []):

            var_dict = pair["var"]
            var = Var(name=var_dict["name"], uid=var_dict.get("uid"))
            block.in_vars.append(var)

        for pair in data.get("out_vars", []):
            var_dict = pair["var"]
            uid = var_dict.get("uid")
            block.out_vars.append(algebraic_vars_dict[uid])

        block.var_mapping = {v.name: v for v in block.algebraic_vars}
        return block

    def copy(self) -> "Block":
        """
        Make a deep copy of this
        :return: deep copy Block
        """
        return Block.parse(data=self.to_dict())

    def __eq__(self, other: "Block") -> bool:
        """
        Equality check
        :param other: another block
        :return: True / False
        """
        if isinstance(other, Block):
            return self.to_dict() == other.to_dict()
        else:
            return False


class DiffBlock(Block):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.diff_vars: List[DiffVar] = []
        self.lag_vars: List[LagVar] = []
        self.reformulated_vars: List[DiffVar] = []
        self.differential_eqs: List[Expr] = []

    @classmethod
    def from_block(cls, block: Block, **kwargs):
        if isinstance(block, DiffBlock):
            return block  # already a DiffBlock

        # Create a new instance of DiffBlock, copying fields from the original Block
        obj = cls.__new__(cls)  # create instance without __init__
        obj.__dict__ = block.__dict__.copy()

        # Ensure DiffBlock-specific fields are always initialised
        obj.diff_vars = []
        obj.lag_vars = []
        obj.reformulated_vars = []
        obj.differential_eqs = []

        obj.__dict__.update(kwargs)  # add DiffBlock-specific fields
        return obj


# ----------------------------------------------------------------------------------------------------------------------
# Pre defined blocks
# ----------------------------------------------------------------------------------------------------------------------

def constant(item_name: str = "") -> Block:
    """

    :param item_name:
    :return:
    """
    name: str = "const_"
    y = Var(name + item_name)
    param = Var("param_" + item_name)

    blk = Block(
        algebraic_vars=[y],
        algebraic_eqs=[y - param],
        out_vars=[y],
        event_dict={param: Const(0.0)},
        name="const"
    )

    return blk


def gain(item_name: str = "") -> Block:
    """

    :param item_name:
    :return:
    """
    inputs = [Var("inp_num_" + item_name)]
    name: str = "gain"
    y = Var(name + item_name)
    gain_param = Var("gain_param_" + item_name)

    expr: Expr = gain_param * inputs[0]
    blk = Block(
        algebraic_vars=[y],
        algebraic_eqs=[y - expr],
        out_vars=[y],
        in_vars=inputs,
        event_dict={gain_param: Const(0.0)},
        name="gain"
    )
    return blk


def variable(name: str = "variable_", vartype: str = "vartype_") -> Tuple[Var, Block]:
    y = Var(name)
    if vartype == 'state':
        blk = Block(state_vars=[y])
    else:
        blk = Block(algebraic_vars=[y])
    return y, blk


def equation(expr: str = 'expression', etype: str = "etype") -> Block:
    if etype == 'state':
        blk = Block(state_eqs=[make_symbolic(expr)])
    else:
        blk = Block(algebraic_eqs=[make_symbolic(expr)])
    return blk


def adder(item_name: str = "") -> Block:
    """

    :param item_name:
    :return:
    """
    inputs = [Var("sum_in_1_" + item_name),
              Var("sum_in_2_" + item_name)]  # will not be specified if inputs can be more than 2
    y = Var("sum_out_" + item_name)

    expr: Expr = inputs[0]
    for i, inpt in enumerate(inputs):
        if i > 0:
            expr += inpt

    blk = Block(
        algebraic_vars=[y],
        algebraic_eqs=[y - expr],
        in_vars=inputs,
        out_vars=[y],
        name="sum"
    )

    return blk


def substract(item_name: str = "") -> Block:
    """

    :param item_name:
    :return:
    """
    inputs = [Var("minuend_" + item_name), Var("subtrahend_" + item_name)]
    y = Var("difference_" + item_name)

    expr: Expr = inputs[0] - inputs[1]

    blk = Block(
        algebraic_vars=[y],
        algebraic_eqs=[y - expr],
        in_vars=inputs,
        out_vars=[y],
        name="substraction"
    )

    return blk


def product(item_name: str = "") -> Block:
    """

    :param item_name:
    :return:
    """
    inputs = [Var("factor1_" + item_name),
              Var("factor2_" + item_name)]  # will not be specified if inputs can be more than 2
    y = Var("product_out_" + item_name)

    expr: Expr = inputs[0] * inputs[1]

    blk = Block(
        algebraic_vars=[y],
        algebraic_eqs=[y - expr],
        in_vars=inputs,
        out_vars=[y],
        name="product"
    )

    return blk


def divide(item_name: str = "") -> Block:
    """

    :param item_name:
    :return:
    """
    inputs = [Var("divident_" + item_name),
              Var("divisor_" + item_name)]  # will not be specified if inputs can be more than 2
    y = Var("quotient_" + item_name)

    expr: Expr = inputs[0] / inputs[1]

    blk = Block(
        algebraic_vars=[y],
        algebraic_eqs=[y - expr],
        in_vars=inputs,
        out_vars=[y],
        name="divide"
    )

    return blk


def absolut(item_name: str = "") -> Block:
    """

    :param item_name:
    :return:
    """
    inputs = [Var("inp_num_" + item_name)]  # will not be specified if inputs can be more than 2
    y = Var("absolut_" + item_name)

    expr: Expr = abs(inputs[0])

    blk = Block(
        algebraic_vars=[y],
        algebraic_eqs=[y - expr],
        in_vars=inputs,
        out_vars=[y],
        name="abs"
    )

    return blk


def integrator(u: Var | Const, name: str = "x") -> Tuple[Var, Block]:
    x = Var(name)
    blk = Block(state_vars=[x], state_eqs=[u])
    return x, blk


def pi_controller(err: Var, kp: float, ki: float, name: str = "pi") -> Block:
    up, blk_kp = gain(kp, err, f"{name}_up")
    ie, blk_int = integrator(err, f"{name}_int")
    ui, blk_ki = gain(ki, ie, f"{name}_ui")
    u, blk_sum = adder([up, ui], f"{name}_u")
    return Block(name="",
                 children=[blk_kp, blk_int, blk_ki, blk_sum],
                 in_vars=[err],
                 out_vars=[u])


def exciter_fake(item_name: str = "") -> Block:
    """

    :param item_name:
    :return:
    """
    vf = Var("vf" + item_name)
    vf_fixed = Var("vf_fixed")
    # event_dict = {vf_fixed: Const(1.2028205849036708)}
    blk = Block()
    blk.algebraic_vars.append(vf)
    # blk.algebraic_eqs.append(vf-vf_fixed)
    # blk.event_dict = event_dict
    blk.in_vars = dict()
    blk.out_vars = [vf]
    blk.name = "const"
    return blk


def governor_fake(item_name: str = "") -> Block:
    """

    :param item_name:
    :return:
    """
    tm = Var("tm" + item_name)
    tm_fixed = Var("tm_fixed")
    # event_dict = {tm_fixed: Const(6.99999999999765)}
    blk = Block()
    blk.algebraic_vars.append(tm)
    # blk.algebraic_eqs.append(tm-tm_fixed)
    # blk.event_dict = event_dict
    blk.in_vars = dict()
    blk.out_vars = [tm]
    blk.name = "const"
    return blk


def generator(name: str = "") -> Block:
    """

    :param name:
    :return:
    """
    inputs = [Var("Vm_" + name), Var("Va_" + name)]

    delta = Var("delta")
    omega = Var("omega")
    psid = Var("psid")
    psiq = Var("psiq")
    i_d = Var("i_d")
    i_q = Var("i_q")
    v_d = Var("v_d")
    v_q = Var("v_q")
    te = Var("te")
    et = Var("et")
    tm = Var("tm")
    P_g = Var("P_g")
    Q_g = Var("Q_g")

    R1 = Var("R1")
    X1 = Var("X1")
    freq = Var("frequ")
    M = Var("M")
    D = Var("D")
    omega_ref = Var("omega_ref")
    Kp = Var("Kp")
    Ki = Var("Ki")

    # vf = UndefinedConst() # this will disappear when the generator and the exciter model are decoupled
    # vf.name ="vf" # this will disappear when the generator and the exciter model are decoupled
    # tm0 = UndefinedConst() # this will disappear when the generator and the exciter model are decoupled
    # tm0.name = "tm0" # this will disappear when the generator and the exciter model are decoupled

    vf = Var("Vf")
    tm0 = Var("tm0")
    event_dict = {R1: Const(0.0),
                  X1: Const(0.3),
                  freq: Const(60.0),
                  M: Const(4.0),
                  D: Const(1.0),
                  omega_ref: Const(1.0),
                  Kp: Const(0.0),
                  Ki: Const(0.0)}

    gen_block = Block(
        state_eqs=[
            (2 * np.pi * freq) * (omega - omega_ref),
            (tm - te - D * (omega - omega_ref)) / M,
        ],
        state_vars=[delta, omega],
        algebraic_eqs=[
            psid - (R1 * i_q + v_q),
            psiq + (R1 * i_d + v_d),
            0 - (psid + X1 * i_d - inputs[1]),
            0 - (psiq + X1 * i_q),
            v_d - (inputs[0] * sin(delta - inputs[1])),
            v_q - (inputs[0] * cos(delta - inputs[1])),
            te - (psid * i_q - psiq * i_d),
            P_g - (v_d * i_d + v_q * i_q),
            Q_g - (v_q * i_d - v_d * i_q),
            tm - (tm0 + Kp * (omega - omega_ref) + Ki * et),
            2 * np.pi * freq * et - delta,  #
        ],
        algebraic_vars=[P_g, Q_g, v_d, v_q, i_d, i_q, psid, psiq, te, tm, et],
        init_eqs={
            delta: imag(
                log((inputs[0] * exp(1j * inputs[1]) + (R1 + 1j * X1) * (
                    conj((P_g + 1j * Q_g) / (inputs[0] * exp(1j * inputs[1]))))) / (
                        abs(inputs[0] * exp(1j * inputs[1]) + (R1 + 1j * X1) * (
                            conj((P_g + 1j * Q_g) / (inputs[0] * exp(1j * inputs[1])))))))),
            omega: omega_ref,
            v_d: real((inputs[0] * exp(1j * inputs[1])) * exp(-1j * (delta - np.pi / 2))),
            v_q: imag((inputs[0] * exp(1j * inputs[1])) * exp(-1j * (delta - np.pi / 2))),
            i_d: real(conj((P_g + 1j * Q_g) / (inputs[0] * exp(1j * inputs[1]))) * exp(-1j * (delta - np.pi / 2))),
            i_q: imag(conj((P_g + 1j * Q_g) / (inputs[0] * exp(1j * inputs[1]))) * exp(-1j * (delta - np.pi / 2))),
            psid: R1 * i_q + v_q,
            psiq: -R1 * i_d - v_d,
            te: psid * i_q - psiq * i_d,
            tm: te,
            et: Const(0),
        },
        event_dict=event_dict,
        in_vars=inputs,
        out_vars=[P_g, Q_g],
        external_mapping={
            VarPowerFlowRefferenceType.P: P_g,
            VarPowerFlowRefferenceType.Q: Q_g
        }
    )

    return gen_block


def load(name: str = "load") -> Block:
    """

    :param name:
    :return:
    """
    Ql = Var("Ql")
    Pl = Var("Pl")

    load_block = Block(
        algebraic_eqs=[
            # Pl - load_object.Pl0,
            # Ql - load_object.Ql0
        ],
        algebraic_vars=[Pl, Ql],
        init_eqs={},
        external_mapping={
            VarPowerFlowRefferenceType.P: Pl,
            VarPowerFlowRefferenceType.Q: Ql
        }
    )

    return load_block


def line(item_name: str, api_object: Any) -> Block:
    """

    :param item_name:
    :param api_object:
    :return:
    """
    line_object = api_object
    Qf = Var("Qf_" + item_name)
    Qt = Var("Qt_" + item_name)
    Pf = Var("Pf_" + item_name)
    Pt = Var("Pt_" + item_name)

    g = Const(1.0 / complex(line_object.R, line_object.X).real)
    b = Const(1.0 / complex(line_object.R, line_object.X).imag)
    bsh = Const(line_object.B)

    Vmf = line_object.bus_from.rms_model.model.E(VarPowerFlowRefferenceType.Vm)
    Vaf = line_object.bus_from.rms_model.model.E(VarPowerFlowRefferenceType.Va)
    Vmt = line_object.bus_to.rms_model.model.E(VarPowerFlowRefferenceType.Vm)
    Vat = line_object.bus_to.rms_model.model.E(VarPowerFlowRefferenceType.Va)

    line_block = Block(
        algebraic_eqs=[
            Pf - ((Vmf ** 2 * g) - g * Vmf * Vmt * cos(Vaf - Vat) + b * Vmf * Vmt * cos(Vaf - Vat + np.pi / 2)),
            Qf - (Vmf ** 2 * (-bsh / 2 - b) - g * Vmf * Vmt * sin(Vaf - Vat) + b * Vmf * Vmt * sin(
                Vaf - Vat + np.pi / 2)),
            Pt - ((Vmt ** 2 * g) - g * Vmt * Vmf * cos(Vat - Vaf) + b * Vmt * Vmf * cos(Vat - Vaf + np.pi / 2)),
            Qt - (Vmt ** 2 * (-bsh / 2 - b) - g * Vmt * Vmf * sin(Vat - Vaf) + b * Vmt * Vmf * sin(
                Vat - Vaf + np.pi / 2)),
        ],
        algebraic_vars=[Pf, Pt, Qf, Qt],
        init_eqs={},
        parameters=[],
        external_mapping={
            VarPowerFlowRefferenceType.Pf: Pf,
            VarPowerFlowRefferenceType.Pt: Pt,
            VarPowerFlowRefferenceType.Qf: Qf,
            VarPowerFlowRefferenceType.Qt: Qt,
        }
    )

    return line_block


def generic(state_inputs: int,
            state_outputs: Sequence[str],
            algebraic_inputs: int,
            algebraic_outputs: Sequence[str]) -> Block:
    """

    :param state_inputs:
    :param state_outputs:
    :param algebraic_inputs:
    :param algebraic_outputs:
    :return:
    """
    blk = Block(
        name="generic",
        in_vars=[Var(f"Vport{i}") for i in range(state_inputs + algebraic_inputs)]
    )

    for i, v in enumerate(state_outputs):
        var = Var(v)
        blk.state_vars.append(var)
        blk.out_vars.append(var)

    for i, v in enumerate(algebraic_outputs):
        var = Var(v)
        blk.algebraic_vars.append(var)
        blk.out_vars.append(var)

    return blk
