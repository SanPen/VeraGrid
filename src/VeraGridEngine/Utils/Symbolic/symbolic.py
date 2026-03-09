# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
import json
import math
import ast
import uuid
import numpy as np
from enum import Enum
import numba as nb
from dataclasses import dataclass, field
from types import MappingProxyType

from typing import Any, Callable, ClassVar, Dict, Mapping, Union, List, Sequence, Tuple, Set, Optional

from VeraGridEngine.enumerations import VarPowerFlowRefferenceType

NUMBER = Union[int, float, complex]


# -----------------------------------------------------------------------------
# UUID helper
# -----------------------------------------------------------------------------

def _new_uid() -> int:
    """Generate a fresh UUID‑v4 string."""
    return uuid.uuid4().int


# -----------------------------------------------------------------------------
# Generic helpers
# -----------------------------------------------------------------------------


def _to_expr(val: Any) -> "Expr":
    """

    returns an expression

    :param val:
    :type val: Union[VeraGridEngine.Utils.Symbolic.symbolic.Const, VeraGridEngine.Utils.Symbolic.symbolic.Var, int, float, VeraGridEngine.Utils.Symbolic.symbolic.Func, complex, VeraGridEngine.Utils.Symbolic.symbolic.BinOp, VeraGridEngine.Utils.Symbolic.symbolic.DiffVar, VeraGridEngine.Utils.Symbolic.symbolic.UnOp]
    :return:
    :rtype: Union[VeraGridEngine.Utils.Symbolic.symbolic.Const, VeraGridEngine.Utils.Symbolic.symbolic.Var, VeraGridEngine.Utils.Symbolic.symbolic.Func, VeraGridEngine.Utils.Symbolic.symbolic.BinOp, VeraGridEngine.Utils.Symbolic.symbolic.DiffVar, VeraGridEngine.Utils.Symbolic.symbolic.UnOp]
    """
    if isinstance(val, Expr):
        return val
    if isinstance(val, (int, float, complex)):
        return Const(val)
    if val is None:
        return Const(None)
    raise TypeError(f"Cannot convert {val!r} to Expr")


# ----------------------------------------------------------------------------
# Function helpers
# ----------------------------------------------------------------------------


class CmpOp(Enum):
    """
    comparisions
    """
    LE = "≤"  # ≤
    GE = "≥"  # ≥
    LT = "<"
    GT = ">"
    EQ = "="  # =


@dataclass(frozen=True, slots=True)
class Comparison:
    lhs: "Expr"
    op: CmpOp  # "<=", ">=", "=="
    rhs: Union["Expr", NUMBER]

    def to_expression(self) -> Expr:
        if self.op == CmpOp.LE or self.op == CmpOp.LT:
            return heaviside(self.rhs - self.lhs)
        elif self.op == CmpOp.GE or self.op == CmpOp.GT:
            return heaviside(self.lhs - self.rhs)
        elif self.op == CmpOp.EQ:
            eps = Const(1e-6)
            return heaviside(self.lhs - self.rhs + eps) * heaviside(self.rhs - self.lhs + eps)
        else:
            raise ValueError(f"operator not supported {self.op}")


class Expr:
    """
    Abstract base class for all expression nodes.
    """

    __slots__ = ("uid",)

    def __init__(self, uid: int | None = None):
        """

        :param uid: (optional UID)
        """
        self.uid: int = _new_uid() if uid is None else uid  # real dataclass field lives in subclasses

    def eval(self, **bindings: float | int) -> float | int:  # pragma: no cover – abstract
        """
        Numeric evaluation
        :param bindings:
        :return:
        """
        raise NotImplementedError

    def eval_uid(self, uid_bindings: Dict[int, float]) -> NUMBER:  # pragma: no cover – abstract
        """

        :param uid_bindings:
        :return:
        """
        raise NotImplementedError

    __call__ = eval  # allow f(x=…)

    def diff(self, var: Var | str, order: int = 1, dt: Var | None = None) -> "Expr":
        """
        Differentiation (higher‑order)
        :param var:
        :param order:
        :return:
        """
        if order < 0:
            raise ValueError("order must be >= 0")
        expr: Expr = self
        for _ in range(order):
            expr = expr._diff1(var, dt).simplify()
        return expr

    def _diff1(self, var: Var | str, dt: Var | None) -> Expr:
        raise NotImplementedError

    def simplify(self) -> "Expr":
        """
        Simplification & substitution (no‑ops by default)
        :return:
        """
        return self

    def subs(self, mapping: Dict[Any, "Expr"]) -> "Expr":
        """
        substitute variables
        :param mapping:
        :type mapping:
        :return:
        :rtype:
        """
        return mapping.get(self, self)

    def to_dict(self) -> Dict[str, Any]:
        """
        returns a dictionary

        :return:
        :rtype:
        """
        return _expr_to_dict(self)

    def to_json(self, **json_kwargs: Any) -> str:
        return json.dumps(self.to_dict(), **json_kwargs)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Expr":
        return _dict_to_expr(data)

    @staticmethod
    def from_json(blob: str) -> "Expr":
        return _dict_to_expr(json.loads(blob))

    # ------------------------------------------------------------------
    # Operator helpers
    # ------------------------------------------------------------------
    def __add__(self, other: Any) -> Expr:
        return BinOp(self, "+", _to_expr(other))

    def __radd__(self, other: Any) -> Expr:
        return BinOp(_to_expr(other), "+", self)

    def __sub__(self, other: Any) -> Expr:
        return BinOp(self, "-", _to_expr(other))

    def __rsub__(self, other: Any) -> Expr:
        return BinOp(_to_expr(other), "-", self)

    def __mul__(self, other: Any) -> Expr:
        return BinOp(self, "*", _to_expr(other))

    def __rmul__(self, other: Any) -> Expr:
        return BinOp(_to_expr(other), "*", self)

    def __truediv__(self, other: Any) -> Expr:
        return BinOp(self, "/", _to_expr(other))

    def __rtruediv__(self, other: Any) -> Expr:
        return BinOp(_to_expr(other), "/", self)

    def __pow__(self, other: Any) -> Expr:
        return BinOp(self, "**", _to_expr(other))

    def __rpow__(self, other: Any) -> Expr:
        return BinOp(_to_expr(other), "**", self)

    def __neg__(self) -> "Expr":
        return UnOp("-", self)

    def __le__(self, other: Expr | NUMBER) -> Comparison:
        return Comparison(self, CmpOp.LE, other)

    def __ge__(self, other: Expr | NUMBER) -> Comparison:
        return Comparison(self, CmpOp.GE, other)

    def __eq__(self, other: Expr | NUMBER) -> Comparison:  # type: ignore[override]
        return Comparison(self, CmpOp.EQ, other)

    def __lt__(self, other: Expr | NUMBER) -> Comparison:
        return Comparison(self, CmpOp.LT, other)

    def __gt__(self, other: Expr | NUMBER) -> Comparison:
        return Comparison(self, CmpOp.GT, other)

    def __str__(self) -> str:  # pragma: no cover – abstract
        """
        Display helper
        :return:
        """
        raise NotImplementedError

    def __repr__(self):
        return self.__str__()

    def __hash__(self) -> int:
        return hash(self.uid)

    def get_vars(self) -> List["Var"]:
        """
        Get all variables in this expression.
        :return: List of Var objects
        """
        result: Set[Var] = set()
        _collect_vars(self, result)
        return list(result)


# ----------------------------------------------------------------------------------------------------------------------
# Atomic nodes
# ----------------------------------------------------------------------------------------------------------------------


class Const(Expr):

    # class to represent constants symbolically

    def __init__(self, value: NUMBER | None = None, uid: int | None = None, name: str = ""):
        super().__init__(uid=uid)
        self.value: NUMBER | None = value
        self.name: str = name

    def __deepcopy__(self, memo):
        return Const(self.value, self.uid, self.name)

    def eval(self, **bindings: NUMBER) -> NUMBER | None:
        return self.value

    def eval_uid(self, uid_bindings: Dict[int, float]) -> float | None:
        return self.value

    def _diff1(self, var: Var | str, dt: Var | None = None) -> "Expr":
        return Const(0)

    def subs(self, mapping: Dict[Any, Expr]) -> Expr:
        if self in mapping:
            return mapping[self]
        if self.name in mapping:
            return mapping[self.name]
        if self.value is None:
            # has_none = False
            # for key in mapping.keys():
            #     if isinstance(key, Const) and key.value is None:
            #         has_none = True
            #         none_key = key
            # if has_none:
            #     return mapping[none_key]

            for key in mapping.keys():
                if isinstance(key, Const) and key.value is None:
                    return mapping[key]

        return self

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return self.__str__()

    def to_dict(self) -> Dict[str, Any]:

        d = super().to_dict()

        d["type"] = "Const"

        if isinstance(self.value, complex):
            d["value"] = [self.value.real, self.value.imag]
            d["kind"] = "complex"
            return d

        if self.value is None:
            d["value"] = None
            d["kind"] = "undefined"
            return d

        d["value"] = self.value
        d["kind"] = "float"
        return d


class VarType(Enum):
    Parameter = "parameter"
    State = "state"
    Algebraic = "algebraic"
    Differential = "differential"


class Var(Expr):
    """
    Any variable
    """

    __slots__ = ("name", "_ref", "uid", "diff_var", "base_var", "_origin_var")

    def __init__(self, name: str, reference: VarPowerFlowRefferenceType | None = None, uid: int | None = None, diff_var: Var | None = None, base_var: Var | None = None):

        """

        :param name:
        :param uid:
        :param diff_var:
        """
        super().__init__(uid=uid)
        self.name: str = name
        self._ref: VarPowerFlowRefferenceType | None = reference
        self.diff_var = diff_var
        self.base_var: Var = base_var  # assign reference to base var
        self._origin_var: Var | None = None


        if base_var is not None:
            self.base_var.diff_var = self  # assign reference to me in the base var

    def __deepcopy__(self, memo):
        return Var(self.name, self.uid, self.diff_var)

    def eval(self, **bindings: float) -> float:
        """
        Evaluate this variable
        :param bindings: dictionary like mapping Var: float
        :return:
        """
        try:
            return bindings[self.name]
        except KeyError as exc:
            raise ValueError(f"No value for variable '{self.name}'.") from exc

    def eval_uid(self, uid_bindings: Dict[int, float]) -> float:
        """
        Evaluate using the uid
        :param uid_bindings:
        :return:
        """
        try:
            return uid_bindings[self.uid]
        except KeyError as exc:
            raise ValueError(f"No value for uid '{self.uid}'.") from exc

    def subs(self, mapping: Dict[Var | str, Expr]) -> Expr:
        """
        Substitute this variable
        :param mapping:
        :return:
        """
        if self in mapping:
            return mapping[self]
        if self.name in mapping:
            return mapping[self.name]
        return self

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

    def __eq__(self, other):
        # Var comparison using the uid
        if isinstance(other, Var):
            return self.uid == other.uid

        # Symbolic comparison between any expression Expr or float or int
        if isinstance(other, Expr) or isinstance(other, (int, float)):
            return Comparison(self, CmpOp.EQ, other)

        return NotImplemented

    @staticmethod
    def parse(data: Dict[str, Any]) -> "Var":
        """
        Parse the data
        :param data:
        :return:
        """
        # reconstruct base_var
        base_data = data["base_var"]
        base_var = _dict_to_expr(base_data)
        if not isinstance(base_var, Var):
            raise TypeError("base_var must be a Var")

        obj = Var(name=data["name"], base_var=base_var)
        obj.uid = data["uid"]
        return obj

    @property
    def diff_order(self) -> int:
        order = 0
        var = self
        while var.base_var is not None:
            var = var.base_var
            order += 1
        return order

    @property
    def origin_var(self) -> Var:

        if self._origin_var is None:
            # lazy evaluation, since this is tied to the base var, we do it only once
            self._origin_var = self.base_var
            while self._origin_var.base_var is not None:
                self._origin_var = self._origin_var.base_var

        return self._origin_var

    @property
    def ref(self) -> VarPowerFlowRefferenceType:
        return self._ref

    def _diff1(self, var: Var | str, dt: Var | None = None) -> Expr:
        """
        differentiation
        :param var:
        :type var: VeraGridEngine.Utils.Symbolic.symbolic.Var
        :param dt:
        :type dt: Union[None, VeraGridEngine.Utils.Symbolic.symbolic.Var]
        :return:
        :rtype: Union[VeraGridEngine.Utils.Symbolic.symbolic.Const, None, VeraGridEngine.Utils.Symbolic.symbolic.BinOp]
        """
        if dt is None or self.base_var is None:
            return Const(1 if self.uid == var.uid else 0)
        elif self.base_var is not None:
            # ∂(dx/dt)/∂x = 1/h
            if var.uid == self.uid:
                return Const(1)
            elif var.uid == self.base_var.uid:
                # Differentiating by immediate base: return 1/dt
                return Const(1) / dt
            elif var.uid == self.origin_var.uid:
                # Differentiating by origin (root) variable: apply chain rule
                # This happens for nested diff vars like d2x when diff'ing by x
                result = (Const(1) / dt) * self.base_var.diff(var, dt=dt)
                return result
            else:
                return Const(0)


    def populate_initial_lag(self, x0: float, dx0: np.ndarray, lag_x: float, dt: Optional[Const]):
        """

        :param dx0:
        :param dt:
        :return:
        """
        # function that initializes the lag of the same order for the same original_var
        diff_order = self.diff_order
        res = Expr()
        for i in range(diff_order):
            res += (dt ** (i + 1)) * (-1) ** (i + 1) * dx0[i]
        return res.eval()

    def approximation_expr(self, dt: Optional[Var | None], central=False) -> Tuple:
        """
        Computes the n-th backward finite difference approximation of the derivative
        using the closed-form backward difference formula.
        """
        origin_name = self.origin_var.name
        lag_var_0 = self.origin_var
        if dt is None:
            dt = Const(1.0)
        origin_name = self.origin_var.name
        lag_total = self.diff_order
        if self.diff_order == 1 and central:
            lag_var_2 = Var("aux_2")
            return (lag_var_0 - lag_var_2) / (2 * dt), lag_total

        # Compute the sum: ∑_{i=0}^{n} (-1)^i * C(n, i) * f(x - i*dt)
        terms = []
        minus1 = Const(-1)

        for i in range(lag_total + 1):
            if i == 0:
                lag_var = lag_var_0
            else:
                lag_var = Var(name=f"{origin_name}_lag_{i}")
            coeff = minus1 ** i * Const(math.comb(lag_total, i))
            terms.append(coeff * lag_var)

        finite_diff_sum = sum(terms)

        # Divide by dt^n for n-th derivative
        result = finite_diff_sum / (dt ** lag_total)
        return result.simplify(), lag_total

    def __hash__(self) -> int:
        return hash(repr(self))


def get_expr_factors(expr: Expr) -> List[Expr]:
    """

    :param expr:
    :type expr: Union[VeraGridEngine.Utils.Symbolic.symbolic.BinOp, VeraGridEngine.Utils.Symbolic.symbolic.UnOp, VeraGridEngine.Utils.Symbolic.symbolic.Const, VeraGridEngine.Utils.Symbolic.symbolic.Var, VeraGridEngine.Utils.Symbolic.symbolic.Func]
    :return:
    :rtype: Union[List[VeraGridEngine.Utils.Symbolic.symbolic.BinOp], List[VeraGridEngine.Utils.Symbolic.symbolic.UnOp], List[VeraGridEngine.Utils.Symbolic.symbolic.Const], List[VeraGridEngine.Utils.Symbolic.symbolic.Var], List[VeraGridEngine.Utils.Symbolic.symbolic.Func]]
    """
    if isinstance(expr, BinOp) and expr.op == '*':
        return get_expr_factors(expr.left.simplify()) + get_expr_factors(expr.right.simplify())
    # Limited expansion of integer powers
    elif isinstance(expr, BinOp) and expr.op == '**':
        base, exp_ = expr.left.simplify(), expr.right.simplify()

        if isinstance(exp_, Const):
            n = exp_.value
            if isinstance(n, int) and n >= 1:
                return get_expr_factors(base) * n

        # otherwise: keep power atomic
        return [expr]
    return [expr]


def build_mul(factors: List[Expr]) -> Expr:
    """

    :param factors:
    :type factors: List[Expr]
    :return:Expr
    """
    if not factors:
        return Const(1)
    expr = factors[0]
    for f in factors[1:]:
        expr = expr * f
    return expr


class BinOp(Expr):
    """
    Binary operation expression
    """

    __slots__ = ("op", "left", "right")

    def __init__(self, left: Expr, op: str, right: Expr, uid: int | None = None):
        """

        :param left:
        :param op:
        :param right:
        :param uid:
        """
        super().__init__(uid=uid)
        self.op: str = op
        self.left: Expr = left
        self.right: Expr = right

    def eval(self, **bindings: NUMBER) -> NUMBER:
        """
        Evaluation using names
        :param bindings:
        :return:
        """
        # return self._impl[self.op](self.left.eval(**bindings), self.right.eval(**bindings))
        if self.op == "+":
            return self.left.eval(**bindings) + self.right.eval(**bindings)
        elif self.op == "-":
            return self.left.eval(**bindings) - self.right.eval(**bindings)
        elif self.op == "*":
            return self.left.eval(**bindings) * self.right.eval(**bindings)
        elif self.op == "/":
            return self.left.eval(**bindings) / self.right.eval(**bindings)
        elif self.op == "**":
            return self.left.eval(**bindings) ** self.right.eval(**bindings)
        else:
            raise Exception(f"operation {self.op} not implemented")

    def eval_uid(self, uid_bindings: Dict[str, NUMBER]) -> NUMBER:
        """
        Evaluate using uuid's
        :param uid_bindings:
        :return:
        """
        # return self._impl[self.op](self.left.eval_uid(uid_bindings), self.right.eval_uid(uid_bindings))
        if self.op == "+":
            return self.left.eval_uid(uid_bindings) + self.right.eval_uid(uid_bindings)
        elif self.op == "-":
            return self.left.eval_uid(uid_bindings) - self.right.eval_uid(uid_bindings)
        elif self.op == "*":
            return self.left.eval_uid(uid_bindings) * self.right.eval_uid(uid_bindings)
        elif self.op == "/":
            return self.left.eval_uid(uid_bindings) / self.right.eval_uid(uid_bindings)
        elif self.op == "**":
            return self.left.eval_uid(uid_bindings) ** self.right.eval_uid(uid_bindings)
        else:
            raise Exception(f"operation {self.op} not implemented")

    def _diff1(self, var: Var | str, dt: Var | None = None) -> Expr:
        """
        Differentiation of this expression w.r.t var
        :param var: variable to differentiate with respect to
        :return: Expression
        """
        u, v = self.left, self.right
        du, dv = u._diff1(var, dt), v._diff1(var, dt)
        if self.op == "+":
            return du + dv
        if self.op == "-":
            return du - dv
        if self.op == "*":
            return du * v + u * dv
        if self.op == "/":
            return (du * v - u * dv) / (v ** Const(2))
        if self.op == "**":
            if isinstance(v, Const):
                # numeric exponent
                n = v.value
                return Const(n) * (u ** Const(n - 1)) * du
            elif isinstance(v, Var) and v.tpe == VarType.Parameter:
                return Const(n) * (u ** Const(n - 1)) * du
            else:
                # general exponent: u**v = exp(v*log u)
                return self * (dv * log(u) + du * v / u)
        raise ValueError("Unsupported operator for diff")

    def simplify(self) -> Expr:
        """
        Simplify expression
        :return: Simplified expression
        """
        l, r = self.left.simplify(), self.right.simplify()
        if isinstance(l, Const) and isinstance(r, Const):
            if self.op == "+":
                return Const(r.value + l.value)
            elif self.op == "-":
                return Const(l.value - r.value)
            elif self.op == "*":
                return Const(r.value * l.value)
            elif self.op == "/":
                if r.value != 0:
                    return Const(l.value / r.value)
                else:
                    raise Exception("Division by zero :/")
            elif self.op == "**":
                return Const(l.value ** r.value)
            else:
                raise Exception(f"operation {self.op} not implemented")

        if self.op == "+":
            if isinstance(l, Const) and l.value == 0:
                return r
            if isinstance(r, Const) and r.value == 0:
                return l

        if self.op == "-":
            if isinstance(l, Const) and l.value == 0:
                return -r
            if isinstance(r, Const) and r.value == 0:
                return l
            if l.uid == r.uid:
                return Const(0)

        if self.op == "*":
            for a, b in ((l, r), (r, l)):
                if isinstance(a, Const):
                    if a.value == 0:
                        return Const(0)
                    if a.value == 1:
                        return b

        if self.op == "**" and isinstance(r, Const):
            if r.value == 1:
                return l
            if r.value == 0:
                return Const(1)

        if self.op == '/':
            if isinstance(l, Const) and l.value == 0:
                return Const(0)
            elif isinstance(r, Const) and r.value == 1:
                return l
            elif l.uid == r.uid:
                return Const(1)
            else:
                num_factors = get_expr_factors(l)
                den_factors = get_expr_factors(r)

                new_num = []
                new_den = den_factors.copy()

                for f in num_factors:
                    for g in new_den:
                        if f.uid == g.uid:  # or f == g if structural equality
                            new_den.remove(g)
                            break
                    else:
                        new_num.append(f)

                num_expr = build_mul(new_num)
                den_expr = build_mul(new_den)

                if isinstance(den_expr, Const) and den_expr.value == 1:
                    return num_expr
                return BinOp(num_expr, '/', den_expr)

        return BinOp(l, self.op, r)

    def subs(self, mapping: Dict[Any, Expr]) -> Expr:
        """
        Substitution
        :param mapping: mapping of variables to expressions
        :return:
        """
        if self in mapping:
            return mapping[self]
        return BinOp(self.left.subs(mapping), self.op, self.right.subs(mapping))

    def __str__(self) -> str:
        return f"({self.left}) {self.op} ({self.right})"

    def __repr__(self) -> str:
        return self.__str__()

    def __print__(self) -> str:
        return self.__str__()

    @staticmethod
    def parse(data: Dict[str, Any]) -> Expr:
        obj = BinOp(_dict_to_expr(data["left"]), data["op"], _dict_to_expr(data["right"]))
        obj.uid = data["uid"]
        return obj

    def to_dict(self) -> Dict[str, Any]:
        """

        :return:
        """
        d = super().to_dict()
        d["type"] = "BinOp"
        d["op"] = self.op
        d["left"] = self.left.to_dict()
        d["right"] = self.right.to_dict()
        return d


class UnOp(Expr):
    """
    Unary operation expression
    """

    __slots__ = ("op", "operand",)

    def __init__(self, op: str, operand: Expr, uid: int | None = None):
        """

        :param op:
        :param operand:
        :param uid:
        """
        super().__init__(uid=uid)
        self.op: str = op
        self.operand = operand

    def eval(self, **bindings: NUMBER) -> NUMBER:
        """

        :param bindings:
        :return:
        """
        val = self.operand.eval(**bindings)
        return -val if self.op == "-" else math.nan

    def eval_uid(self, uid_bindings: Dict[str, NUMBER]) -> NUMBER:
        """

        :param uid_bindings:
        :return:
        """
        val = self.operand.eval_uid(uid_bindings)
        if self.op == "-":
            return -val
        else:
            raise Exception(f"Unknown operand {self.op}")

    def _diff1(self, var: Var | str, dt: Var | None = None) -> "Expr":
        """

        :param var:
        :return:
        """
        if self.op == "-":
            return -self.operand._diff1(var, dt)
        else:
            raise Exception(f"Unknown operand {self.op}")

    def simplify(self) -> Expr:
        """

        :return:
        """
        opr = self.operand.simplify()
        if isinstance(opr, Const):
            return Const(-opr.value)
        return UnOp(self.op, opr)

    def subs(self, mapping: Dict[Any, Expr]) -> Expr:
        """

        :param mapping:
        :return:
        """
        if self in mapping:
            return mapping[self]
        return UnOp(self.op, self.operand.subs(mapping))

    def __str__(self) -> str:
        return f"{self.op}({self.operand})"

    def __repr__(self) -> str:
        return self.__str__()

    @staticmethod
    def parse(data: Dict[str, Any]) -> Expr:
        obj = UnOp(data["op"], _dict_to_expr(data["operand"]))
        obj.uid = data["uid"]
        return obj

    def to_dict(self) -> Dict[str, Any]:
        """

        :return:
        """
        d = super().to_dict()
        d["type"] = "UnOp"
        d["op"] = self.op
        d["operand"] = self.operand.to_dict()
        return d


# ----------------------------------------------------------------------------------------------------------------------
# Functional nodes
# ----------------------------------------------------------------------------------------------------------------------
@nb.njit
def heaviside_num(x):
    return 0.0 if x <= 0 else 1.0


def get_namespace() -> Dict[str, Any]:
    namespace = {
        "math": math,
        "np": np,
        "nb": nb,
        "_heaviside": heaviside_num,
    }
    return namespace


functions_dict: Mapping[str, Callable[[NUMBER], NUMBER]] = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "exp": np.exp,
    "log": math.log,
    "sqrt": math.sqrt,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "real": np.real,
    "imag": np.imag,
    "conj": np.conj,
    "angle": np.angle,
    "abs": np.abs,
    "heaviside": heaviside_num
}


class Func(Expr):
    __slots__ = ("op", "arg", "fn", "fnd")

    def __init__(self, arg: Expr, op: str = "", uid: int | None = None):
        """

        :param op:
        :param uid:
        """
        super().__init__(uid=uid)
        self.op: str = op
        self.arg: Expr = arg

        self.fn: Callable[[NUMBER], NUMBER] = functions_dict[self.op]
        self.fnd: Callable[[Expr, Expr], Expr] = functions_diff_dict.get(self.op, None)

    # --- evaluation ----------------------------------------------------------
    def eval(self, **bindings: NUMBER) -> NUMBER:
        return self.fn(self.arg.eval(**bindings))

    def eval_uid(self, uid_bindings: Dict[str, NUMBER]) -> NUMBER:
        return self.fn(self.arg.eval_uid(uid_bindings))

    @staticmethod
    def parse(data: Dict[str, Any]) -> Expr:
        op = data["op"]
        if op is None:
            op = data["name"]
        obj = Func(_dict_to_expr(data["arg"]), op)
        obj.uid = data["uid"]
        return obj

    def to_dict(self) -> Dict[str, Any]:
        """

        :return:
        """
        d = super().to_dict()
        d["type"] = "Func"
        d["op"] = self.op
        d["arg"] = self.arg.to_dict()
        return d

    # --- differentiation (chain rule) ---------------------------------------
    def _diff1(self, var: Var | str, dt: Var | None = None) -> "Expr":
        u = self.arg
        du = u._diff1(var, dt)
        if isinstance(du, Const) and du.value == 0:
            return Const(0)
        else:
            if self.fnd is not None:
                return self.fnd(u, du)
            else:
                raise Exception(f"No derivative defined for {self.op}")

    def subs(self, mapping: Dict[Any, "Expr"]) -> "Expr":
        if self in mapping:
            return mapping[self]
        return Func(self.arg.subs(mapping), self.op)

    def __str__(self) -> str:
        return f"{self.op}({self.arg})"

    def __repr__(self) -> str:
        return self.__str__()


def abs(x: Expr):  # TODO: Rename to not shadow
    return Func(_to_expr(x), "abs")


def abs_diff(u: Expr, du: Expr) -> Expr:
    return heaviside(u) * du


def real(x: Expr):
    return Func(_to_expr(x), "real")


def imag(x: Expr):
    return Func(_to_expr(x), "imag")


def conj(x: Expr):
    return Func(_to_expr(x), "conj")


def angle(x: Expr):
    return Func(_to_expr(x), "angle")


def sin(x: Expr):
    return Func(_to_expr(x), "sin")


def sin_diff(u: Expr, du: Expr) -> Expr:
    return cos(u) * du


def cos(x: Expr):
    return Func(_to_expr(x), "cos")


def cos_diff(u: Expr, du: Expr) -> Expr:
    return -sin(u) * du


def sec(x: Any) -> Expr:
    return Const(1) / cos(x)


def tan(x: Expr):
    return Func(_to_expr(x), "tan")


def tan_diff(u: Expr, du: Expr):
    return (sec(u) ** Const(2)) * du


def exp(x: Expr):
    return Func(_to_expr(x), "exp")


def exp_diff(u: Expr, du: Expr):
    return exp(u) * du


def log(x: Expr):
    return Func(_to_expr(x), "log")


def log_diff(u: Expr, du: Expr):
    return du / u


def sqrt(x: Expr):
    return Func(_to_expr(x), "sqrt")


def sqrt_diff(u: Expr, du: Expr):
    return du / (Const(2) * sqrt(u))


def asin(x: Expr):
    return Func(_to_expr(x), "asin")


def asin_diff(u: Expr, du: Expr) -> Expr:
    return du / sqrt(Const(1) - u ** Const(2))


def acos(x: Expr):
    return Func(_to_expr(x), "acos")


def acos_diff(u: Expr, du: Expr) -> Expr:
    return -du / sqrt(Const(1) - u ** Const(2))


def atan(x: Expr):
    return Func(_to_expr(x), "atan")


def atan_diff(u: Expr, du: Expr) -> Expr:
    return du / (Const(1) + u ** Const(2))


def sinh(x: Expr):
    return Func(_to_expr(x), "sinh")


def cosh(x: Expr):
    return Func(_to_expr(x), "cosh")


def sinh_diff(u: Expr, du: Expr) -> Expr:
    return cosh(u) * du


def cosh_diff(u: Expr, du: Expr) -> Expr:
    return sinh(u) * du


def heaviside(x: Expr):
    return Func(_to_expr(x), "heaviside")


#
# def heaviside(x: Expr):
#     return  _heaviside(x)


def heaviside_diff(u: Expr, du: Expr) -> Expr:
    return du * heaviside(u)


def max(x: Expr, y: Expr) -> Expr:
    return x * heaviside((x - y)) + y * (Const(1) - heaviside((x - y)))


def min(x: Expr, y: Expr) -> Expr:
    return x * heaviside(y - x) + y * (Const(1) - heaviside(y - x))


def hard_sat(x: Expr, x_min: Expr | float, x_max: Expr | float) -> Expr:
    return x_min + (x - x_min) * heaviside(x - x_min) - (x - x_max) * heaviside(x - x_max)


def f_exc(In: Expr) -> Expr:
    exp1 = (Const(1) - Const(0.577) * In)
    exp2 = sqrt(max(Const(1e-6), Const(0.75) - In ** 2))
    exp3 = (Const(1.732) - In * Const(1.732))
    b = (exp1 - exp2) * heaviside(Const(0.433) - In)
    c = (exp2 - exp3) * heaviside(Const(0.75) - In)
    d = exp3 * heaviside(Const(1.0) - In)
    return b + c + d


def piecewise(time_var: Expr, t_events: np.ndarray, new_values: np.ndarray, default_value: Any) -> Expr:
    """
    Symbolic piecewise function.
    Returns default_value before the first event, then switches to
    corresponding new_values after each t_event.

    Parameters
    ----------
    time_var : Expr
        Symbolic time expression
    t_events : np.ndarray
        1D array of event times (must be sorted ascending)
    new_values : np.ndarray
        1D array of values after each event time
    default_value : Any
        Value before the first event
    """
    t_expr = _to_expr(time_var)
    result = _to_expr(default_value)

    for t_event, new_value in zip(t_events, new_values):
        step = heaviside(t_expr - Const(t_event))
        result = step * _to_expr(new_value) + (Const(1) - step) * result

    return result


functions_diff_dict: Mapping[str, Callable[[Expr, Expr], Expr]] = {
    "sin": sin_diff,
    "cos": cos_diff,
    "tan": tan_diff,
    "exp": exp_diff,
    "log": log_diff,
    "sqrt": sqrt_diff,
    "asin": asin_diff,
    "acos": acos_diff,
    "atan": atan_diff,
    "sinh": sinh_diff,
    "cosh": cosh_diff,
    "abs": abs_diff,
    "heaviside": heaviside_diff
}


@dataclass(frozen=True)
class Func2(Expr):
    name: str
    arg1: Expr
    arg2: Expr
    uid: int = field(default_factory=_new_uid, init=False)

    _impl: ClassVar[Mapping[str, Callable[[NUMBER, NUMBER], NUMBER]]] = MappingProxyType({
        "min": np.minimum,
        "max": np.maximum,
    })

    def eval(self, **bindings: NUMBER) -> NUMBER:
        return self._impl[self.name](
            self.arg1.eval(**bindings),
            self.arg2.eval(**bindings),
        )

    def eval_uid(self, uid_bindings: Dict[str, NUMBER]) -> NUMBER:
        return self._impl[self.name](
            self.arg1.eval_uid(uid_bindings),
            self.arg2.eval_uid(uid_bindings),
        )

    def _diff1(self, var: Var | str, dt: Var | None) -> Expr:
        """

        differentiation

        :param var:
        :type var:
        :param dt:
        :type dt:
        :return:
        :rtype:
        """
        x = self.arg1
        y = self.arg2

        dx = x._diff1(var, dt)
        dy = y._diff1(var, dt)

        # short-circuit: constant
        if (
                isinstance(dy, Const) and dy.value == 0 and
                isinstance(dx, Const) and dx.value == 0
        ):
            return Const(0)

        if self.name == "atan2":
            return (x * dy - y * dx) / (x ** Const(2) + y ** Const(2))
        if self.name == "min":
            return heaviside(x - y) * dx + heaviside(x - y) * dy
        if self.name == "max":
            return heaviside(y - x) * dx + heaviside(x - y) * dy

        raise ValueError(f"Unknown binary function '{self.name}'")

    # --- simplification ------------------------------------------------------
    def simplify(self) -> "Expr":
        """

        simplification

        :return:
        :rtype:
        """
        a_s = self.arg1.simplify()
        b_s = self.arg2.simplify()

        # constant folding
        if isinstance(a_s, Const) and isinstance(b_s, Const):
            try:
                return Const(Func2._impl[self.name](a_s.value, b_s.value))
            except ValueError:
                pass  # domain error – keep symbolic

        # min(x, x) → x ; max(x, x) → x
        if (a_s == b_s) and self.name in ("min", "max"):
            return a_s

        # return simplified symbolic form
        return Func2(self.name, a_s, b_s)

    def subs(self, mapping: Dict[Any, "Expr"]) -> "Expr":
        """

        substitude

        :param mapping:
        :type mapping:
        :return:
        :rtype:
        """
        if self in mapping:
            return mapping[self]
        return Func2(
            self.name,
            self.arg1.subs(mapping),
            self.arg2.subs(mapping),
        )

    def __str__(self) -> str:
        return f"{self.name}({self.arg1}, {self.arg2})"

    def __repr__(self) -> str:
        return self.__str__()


# -----------------------------------------------------------------------------
# Public constructor helpers
# -----------------------------------------------------------------------------


def _expr_to_dict(expr: Expr) -> Dict[str, Any]:
    """
    Serialise any `Expr` tree into a plain Python dictionary that’s
    JSON-friendly.  Each node type becomes a small dict that records:

        • its own type      (\"Const\", \"Var\", \"BinOp\", …)
        • the data it carries (value, name, operator…)
        • its unique uid     (string, so it survives round-trip)
        • nested children    (recursively serialised)

    The reverse operation is handled by `_dict_to_expr`.
    """
    # ------------------------------------------------------------------
    # Atomic nodes
    # ------------------------------------------------------------------

    if isinstance(expr, Const):
        val = expr.value
        if isinstance(val, complex):
            return {"type": "Const", "value": [val.real, val.imag], "kind": "complex", "uid": expr.uid}
        return {"type": "Const", "value": val, "uid": expr.uid}

    if isinstance(expr, Var):
        if expr.base_var is None:
            return {
                "type": "Var",
                "name": expr.name,
                "uid": expr.uid,
                "base_var": "None"
            }
        else:
            return {
                "type": "Var",
                "name": expr.name,
                "uid": expr.uid,
                "base_var": _expr_to_dict(expr.base_var),
            }

    # ------------------------------------------------------------------
    # Composite nodes
    # ------------------------------------------------------------------
    if isinstance(expr, BinOp):
        return {
            "type": "BinOp",
            "op": expr.op,
            "left": _expr_to_dict(expr.left),
            "right": _expr_to_dict(expr.right),
            "uid": expr.uid,
        }

    if isinstance(expr, UnOp):
        return {
            "type": "UnOp",
            "op": expr.op,  # only \"-\" for now
            "operand": _expr_to_dict(expr.operand),
            "uid": expr.uid,
        }

    if isinstance(expr, Func):
        return {
            "type": "Func",
            "op": expr.op,
            "arg": _expr_to_dict(expr.arg),
            "uid": expr.uid,
        }

    # ------------------------------------------------------------------
    # Anything else is an API bug
    # ------------------------------------------------------------------
    raise TypeError(f"Unsupported Expr subclass: {type(expr).__name__}")


def _dict_to_expr(data: Dict[str, Any]) -> Expr | Var | Const:
    """
    De-Serialize expression from dictionary
    :param data:
    :return:
    """
    t = data["type"]
    if t == "Const":
        if data.get("kind") == "complex":
            arr = data["value"]
            obj = Const(complex(arr[0], arr[1]))
        elif data.get("kind") == "undefined":
            obj = Const()
        else:
            obj = Const(data["value"])
    elif t == "Var":
        if data["base_var"] == "None":
            obj = Var(data["name"])
        else:
            # reconstruct base_var
            base_data = data["base_var"]
            base_var = _dict_to_expr(base_data)
            if not isinstance(base_var, Var):
                raise TypeError("base_var must be a Var")

            obj = Var(name=data["name"], base_var=base_var)


    elif t == "BinOp":
        obj = BinOp(_dict_to_expr(data["left"]), data["op"], _dict_to_expr(data["right"]))

    elif t == "UnOp":
        obj = UnOp(data["op"], _dict_to_expr(data["operand"]))

    elif t == "Func":
        op = data.get("op", None)
        if op is None:
            op = data["name"]
        obj = Func(_dict_to_expr(data["arg"]), op)

    else:
        raise ValueError(f"Unknown type '{t}' in deserialisation")

    object.__setattr__(obj, "uid", data["uid"])
    return obj


# ----------------------------------------------------------------------------------------------------------------------
# Convenience top‑level helpers
# ----------------------------------------------------------------------------------------------------------------------

def diff(expr: Expr, var: Var | str, order: int = 1) -> Expr:  # noqa: D401 – simple
    """
    Return ∂^order(expr)/∂var^order.
    :param expr: Expression
    :param var: Variable to differentiate against
    :param order: Derivative order
    :return: Derivative expression
    """
    return expr.diff(var, order)


def eval_uid(expr: Expr, uid_bindings: Dict[str, NUMBER]) -> NUMBER:  # noqa: D401 – simple
    """
    Evaluate *expr* with a mapping from node UID → numeric value.
    :param expr:
    :param uid_bindings:
    :return:
    """
    return expr.eval_uid(uid_bindings)


def _collect_vars(expr: Expr, out: Set[Var]) -> None:
    """
    Collect variables in a deterministic order
    Depth-first, left-to-right variable harvest.
    :param expr: Some expression
    :param out: List to fill
    :return: None
    """
    if isinstance(expr, Var):
        if expr not in out:
            out.add(expr)
    elif isinstance(expr, BinOp):
        _collect_vars(expr.left, out)
        _collect_vars(expr.right, out)
    elif isinstance(expr, UnOp):
        _collect_vars(expr.operand, out)
    elif isinstance(expr, Func):
        _collect_vars(expr.arg, out)


def _all_vars(expressions: Sequence[Expr]) -> List[Var]:
    """
    Collect all variables in a list of expressions
    :param expressions: Any iterable of expressions
    :return: List of non-repeated variables
    """
    res: Set[Var] = set()
    for e in expressions:
        _collect_vars(e, res)
    return list(res)


_OP_PRECEDENCE = {
    '+': 10,
    '-': 10,
    '*': 20,
    '/': 20,
    '**': 30,
}


def _precedence(expr):
    if isinstance(expr, BinOp):
        return _OP_PRECEDENCE[expr.op]
    if isinstance(expr, UnOp):
        return 40
    if isinstance(expr, (Const, Var)):
        return 100
    if isinstance(expr, Func):
        return 50
    return 0


def expression2numba(expr: Expr,
                     compiler_names_dict: Dict[int, str],
                     parent_prec: int = 0) -> str:
    """
    Emit a precedence-aware, Numba-friendly Python expression.
    Parentheses are added only when required.
    """

    my_prec = _precedence(expr)

    if isinstance(expr, Const):
        s = repr(expr.value)

    elif isinstance(expr, Var):
        s = compiler_names_dict[expr.uid]

    elif isinstance(expr, UnOp):
        operand = expression2numba(expr.operand,
                                   compiler_names_dict,
                                   my_prec)
        s = f"-{operand}"

    elif isinstance(expr, BinOp):
        left = expression2numba(expr.left,
                                compiler_names_dict,
                                my_prec)

        # +1 enforces left associativity
        right = expression2numba(expr.right,
                                 compiler_names_dict,
                                 my_prec + 1)

        s = f"{left} {expr.op} {right}"

    elif isinstance(expr, Func):
        arg = expression2numba(expr.arg,
                               compiler_names_dict,
                               0)
        if expr.op == "heaviside":
            s = f"_heaviside({arg})"
        else:
            s = f"np.{expr.op}({arg})"

    else:
        raise TypeError(type(expr))

    # Add parentheses only if this expression binds weaker than the parent
    if my_prec < parent_prec:
        return f"({s})"
    else:
        return s


def _emit_event_params_eq(expr: Expr, uid_map_t: Dict[int, str] = None) -> str:
    """
    TODO: proper docstring
    Emit a pure-Python (Numba-friendly) expression string
    :param expr: Expr (expression)
    :param uid_map_t:
    :return:
    """

    if isinstance(expr, Const):
        return repr(expr.value)

    if isinstance(expr, Var):
        if expr.uid in uid_map_t.keys():
            return uid_map_t[expr.uid]

    if isinstance(expr, UnOp):
        return f"-({_emit_event_params_eq(expr.operand, uid_map_t)})"

    if isinstance(expr, BinOp):
        return f"({_emit_event_params_eq(expr.left, uid_map_t)} {expr.op} {_emit_event_params_eq(expr.right, uid_map_t)})"

    if isinstance(expr, Func):

        if expr.op == "heaviside":
            return f"_heaviside({_emit_event_params_eq(expr.arg, uid_map_t)})"
        else:
            return f"np.{expr.op}({_emit_event_params_eq(expr.arg, uid_map_t)})"
    else:
        raise ValueError(f"Unknown function '{expr.name}' in _emit_params_eq")


def _emit_one(expr: Expr, uid_map_vars: Dict[int, str], uid_map_event_params: Dict[int, str],
              uid_map_params: Dict[int, str]) -> str:
    """
    Emit a pure-Python (Numba-friendly) expression string
    :param expr: Expr (expression)
    :param uid_map_vars:
    :return:
    """
    if isinstance(expr, Const):
        return repr(expr.value)

    if isinstance(expr, Var):
        if expr.uid in uid_map_vars.keys():
            return uid_map_vars[expr.uid]  # positional variable
        elif expr.uid in uid_map_event_params.keys():
            return uid_map_event_params[expr.uid]  # positional variable
        else:
            return uid_map_params[expr.uid]

    if isinstance(expr, UnOp):
        return f"-({_emit_one(expr.operand, uid_map_vars, uid_map_event_params, uid_map_params)})"

    if isinstance(expr, BinOp):
        return (f"({_emit_one(expr.left, uid_map_vars, uid_map_event_params, uid_map_params)} "
                f"{expr.op} {_emit_one(expr.right, uid_map_vars, uid_map_event_params, uid_map_params)})")

    if isinstance(expr, Func):

        if expr.op == "heaviside":
            return f"_heaviside({_emit_one(expr.arg, uid_map_vars, uid_map_event_params, uid_map_params)})"
        else:
            return f"np.{expr.op}({_emit_one(expr.arg, uid_map_vars, uid_map_event_params, uid_map_params)})"

    raise TypeError(expr)


def find_vars_order(expressions: Union[Expr, Sequence[Expr]],
                    ordering: Sequence[Var] | None = None,
                    var_dict: Dict[int, Var] | None = None) -> List[Var]:
    """
    Return the variable list that positional JIT functions will expect.
    :param expressions: Single expression or any iterable of expressions.
    :param ordering: Is provided, it overrides the default left‑to‑right order.
                    Items in *ordering* can be Var objects or variable names (strings).
    :param var_dict: Dictionary of var uid to var ({v.uid: v for v in vars_list})
    :return:
    """

    if isinstance(expressions, Expr):

        vars_list = _all_vars([expressions])
    else:
        vars_list = _all_vars(expressions)

    if ordering is None:
        return vars_list

    if var_dict is None:
        var_dict: Dict[int, Var] = {v.uid: v for v in vars_list}

    return [v if isinstance(v, Var) else var_dict[v.uid] for v in ordering]


def get_expression_vars(expr: Expr, vars_found: Optional[List[Var]] = None) -> List[Var]:
    """
    Get the list of variables from any expression
    :param expr: Expression Expr
    :param vars_found: already existing list of vars
    :return: Final list of vars
    """
    if vars_found is None:
        vars_found = list()

    if isinstance(expr, Var):
        if expr not in vars_found:
            vars_found.append(expr)

    elif isinstance(expr, BinOp):
        get_expression_vars(expr.left, vars_found)
        get_expression_vars(expr.right, vars_found)

    elif isinstance(expr, UnOp):
        get_expression_vars(expr.operand, vars_found)

    elif isinstance(expr, Func):
        get_expression_vars(expr.arg, vars_found)

    # Todo: add comparisions

    return vars_found


# mapping of Python operator nodes → our BinOp symbols
# TODO: eliminate with all its consequences -> Marina
_BINOP_MAP = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.Pow: "**",
}

# TODO: eliminate with all its consequences -> Marina
_UNOP_MAP = {
    ast.USub: "-",
}

# mapping of allowed function names → our constructor functions
# TODO: eliminate with all its consequences -> Marina
_FUNC_MAP = {
    "sin": sin,
    "cos": cos,
    "tan": tan,
    "exp": exp,
    "log": log,
    "sqrt": sqrt,
    "asin": asin,
    "acos": acos,
    "atan": atan,
    "sinh": sinh,
    "cosh": cosh,
    "heaviside": heaviside,
    "_dict_to_expression": _dict_to_expr
}


def symbolic_to_string(expr: Expr) -> str:
    """
    Convert a symbolic expression into a string (parsable by parse_expr).
    """
    if isinstance(expr, Const):
        return str(expr.value)
    elif isinstance(expr, Var):
        return expr.name
    elif isinstance(expr, UnOp):
        if expr.op == "-":
            return f"-({symbolic_to_string(expr.operand)})"
        return f"{expr.op}({symbolic_to_string(expr.operand)})"
    elif isinstance(expr, BinOp):
        left = symbolic_to_string(expr.left)
        right = symbolic_to_string(expr.right)
        return f"({left} {expr.op} {right})"
    elif isinstance(expr, Func):
        return f"{expr.op}({symbolic_to_string(expr.arg)})"
    elif isinstance(expr, Comparison):
        left = symbolic_to_string(expr.lhs)
        right = symbolic_to_string(expr.rhs)
        return f"({left} {expr.op} {right})"
    else:
        raise TypeError(f"Unsupported expression type: {type(expr)}")


# -----------------------------------------------------------------------------
# Public interface
# -----------------------------------------------------------------------------

__all__ = [
    "Expr", "Const", "Var", "BinOp", "UnOp", "Func", "CmpOp", "Comparison",
    "sin", "cos", "tan", "exp", "log", "sqrt",
    "asin", "acos", "atan", "sinh", "cosh",
    "diff", "eval_uid",
    "find_vars_order",
    "heaviside",
    "piecewise",
    "symbolic_to_string",
    "hard_sat",
    "f_exc",
    'expression2numba',
    'heaviside_num',
    'get_expression_vars',
    '_dict_to_expr',
    '_expr_to_dict',
    'abs',
    '_to_expr',
    'get_namespace'
]
