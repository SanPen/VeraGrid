# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
LaTeX printer for symbolic expressions.

Converts an :class:`Expr` tree into a LaTeX string suitable for
rendering with matplotlib's mathtext engine.

This module lives entirely inside ``VeraGridEngine`` and has **no**
dependency on Qt, matplotlib, or any GUI library.

Precedence levels (higher binds tighter):

    1  comparison   (≤  ≥  <  >  =)
    2  addition     (+  −)
    3  multiplication  (implicit / \\cdot)
    4  division     (fraction)
    5  power        (^{…})
    6  unary minus  (−)
    7  atom         (Var, Const, Func, Func2, parenthesised)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from VeraGridEngine.Utils.Symbolic.symbolic import Expr

from VeraGridEngine.Utils.Symbolic.symbolic import (
    BinOp,
    CmpOp,
    Comparison,
    Const,
    Func,
    Func2,
    UnOp,
    Var,
)

# ---------------------------------------------------------------------------
# Precedence constants
# ---------------------------------------------------------------------------

_CMP = 1
_ADD = 2
_MUL = 3
_DIV = 4
_POW = 5
_UNARY = 6
_ATOM = 7

# ---------------------------------------------------------------------------
# Name → LaTeX mapping tables
# ---------------------------------------------------------------------------

_FUNC_LATEX: dict[str, str] = {
    "sin": r"\sin",
    "cos": r"\cos",
    "tan": r"\tan",
    "asin": r"\arcsin",
    "acos": r"\arccos",
    "atan": r"\arctan",
    "sinh": r"\sinh",
    "cosh": r"\cosh",
    "tanh": r"\tanh",
    "exp": r"\exp",
    "log": r"\ln",
    "log10": r"\log_{10}",
    "sqrt": r"\sqrt",
    "floor": r"\lfloor",
    "ceil": r"\lceil",
    "round": r"\operatorname{round}",
    "abs": r"\lvert",
    "heaviside": r"\Theta",
    "real": r"\operatorname{Re}",
    "imag": r"\operatorname{Im}",
    "conj": r"\operatorname{conj}",
    "angle": r"\operatorname{angle}",
}

_CMP_LATEX: dict[CmpOp, str] = {
    CmpOp.LE: r"\leq",
    CmpOp.GE: r"\geq",
    CmpOp.LT: "<",
    CmpOp.GT: ">",
    CmpOp.EQ: "=",
}

_FUNC2_LATEX: dict[str, str] = {
    "atan2": r"\operatorname{atan2}",
    "min": r"\min",
    "max": r"\max",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _needs_parens(child: Expr, parent_prec: int, child_prec: int,
                  right: bool = False) -> bool:
    """
    Decide whether *child* needs surrounding parentheses.

    Parentheses are needed when the child's precedence is lower than
    (or equal for the right side of non-commutative ops) the parent's.
    """
    if child_prec < parent_prec:
        return True
    if child_prec == parent_prec and right and parent_prec != _ADD:
        return True
    return False


def _wrap(latex: str, needs: bool, *, big: bool = False) -> str:
    """Wrap *latex* in parentheses if *needs* is True."""
    if not needs:
        return latex
    if big:
        return r"\left(" + latex + r"\right)"
    return "(" + latex + ")"


# ---------------------------------------------------------------------------
# Leaf printers
# ---------------------------------------------------------------------------


def _print_const(expr: Const) -> str:
    """Render a constant as a plain number."""
    if expr.value is None:
        return r"\bot"
    v = expr.value
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e15:
            return str(int(v))
        return f"{v:.6g}"
    return str(v)


def _print_var(expr: Var) -> str:
    """Render a variable, turning the first ``_`` into a subscript."""
    name = expr.name
    if "_" in name:
        base, sub = name.split("_", 1)
        escaped_sub = sub.replace("_", r"\_")
        return f"{base}_{{{escaped_sub}}}"
    return name


# ---------------------------------------------------------------------------
# Multiplication
# ---------------------------------------------------------------------------


def _is_atom_like(expr: Expr) -> bool:
    """True if the expression renders as a single compact token."""
    return isinstance(expr, (Const, Var))


def _print_mul(left_latex: str, right_latex: str,
               left: Expr, right: Expr) -> str:
    """
    Render multiplication using implicit notation when possible.

    Rules::

        Const × Const   →  2 \\cdot 3
        Const × atom    →  2x
        Const × complex →  2\\sin(x)
        atom  × atom    →  xy
        atom  × complex →  x\\sin(x)
        complex × atom  →  (a+b)x
        complex × complex →  (a+b) \\cdot \\sin(x)
    """
    left_is_num = isinstance(left, Const) and left.value is not None
    right_is_num = isinstance(right, Const) and right.value is not None

    if left_is_num and right_is_num:
        return f"{left_latex} \\cdot {right_latex}"

    if left_is_num:
        return f"{left_latex}{right_latex}"

    if right_is_num:
        return f"{left_latex} \\cdot {right_latex}"

    if _is_atom_like(left) and _is_atom_like(right):
        return f"{left_latex}{right_latex}"

    if _is_atom_like(right):
        return f"{left_latex}{right_latex}"

    return f"{left_latex} \\cdot {right_latex}"


# ---------------------------------------------------------------------------
# Composite printers
# ---------------------------------------------------------------------------


def _print_unop(expr: UnOp) -> str:
    if expr.op == "-":
        inner = _latex(expr.operand, _UNARY)
        return f"-{inner}"
    inner = _latex(expr.operand, _ATOM)
    return f"{expr.op}{{{inner}}}"


def _print_binop(expr: BinOp, parent_prec: int) -> str:
    op = expr.op

    if op == "+":
        lp = _latex(expr.left, _ADD)
        rp = _latex(expr.right, _ADD, right=True)
        return _wrap(f"{lp} + {rp}", _needs_parens(expr, parent_prec, _ADD))

    if op == "-":
        lp = _latex(expr.left, _ADD)
        rp = _latex(expr.right, _ADD, right=True)
        return _wrap(f"{lp} - {rp}", _needs_parens(expr, parent_prec, _ADD))

    if op == "*":
        left_needs = _needs_parens(expr.left, _MUL, _MUL)
        right_needs = _needs_parens(expr.right, _MUL, _MUL, right=True)
        lp = _wrap(_latex(expr.left, _MUL), left_needs)
        rp = _wrap(_latex(expr.right, _MUL, right=True), right_needs)
        result = _print_mul(lp, rp, expr.left, expr.right)
        return _wrap(result, _needs_parens(expr, parent_prec, _MUL))

    if op == "/":
        num = _latex(expr.left, _CMP)
        den = _latex(expr.right, _CMP)
        return _wrap(
            f"\\frac{{{num}}}{{{den}}}",
            _needs_parens(expr, parent_prec, _DIV),
        )

    if op == "**":
        base_needs = _needs_parens(expr.left, _POW, _POW)
        base = _wrap(_latex(expr.left, _POW), base_needs, big=base_needs)
        exp_str = _latex(expr.right, _POW, right=True)
        return _wrap(
            f"{base}^{{{exp_str}}}",
            _needs_parens(expr, parent_prec, _POW),
        )

    lp = _latex(expr.left, _ATOM)
    rp = _latex(expr.right, _ATOM)
    return f"{lp} {op} {rp}"


def _print_func(expr: Func) -> str:
    tex_name = _FUNC_LATEX.get(expr.op, r"\operatorname{" + expr.op + "}")
    inner = _latex(expr.arg, _CMP)

    if expr.op == "abs":
        return f"{tex_name}{inner}\\rvert"

    if expr.op in ("floor", "ceil"):
        close = r"\rfloor" if expr.op == "floor" else r"\rceil"
        return f"{tex_name}{inner}{close}"

    return f"{tex_name}\\left({inner}\\right)"


def _print_func2(expr: Func2) -> str:
    tex_name = _FUNC2_LATEX.get(expr.name, r"\operatorname{" + expr.name + "}")
    a1 = _latex(expr.arg1, _CMP)
    a2 = _latex(expr.arg2, _CMP)
    return f"{tex_name}\\left({a1}, {a2}\\right)"


def _print_comparison(expr: Comparison) -> str:
    left = _latex(expr.lhs, _CMP)
    right = _latex(expr.rhs, _CMP, right=True)
    op = _CMP_LATEX.get(expr.op, "=")
    return f"{left} {op} {right}"


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------


def _latex(expr: Expr, prec: int = _ATOM, *, right: bool = False) -> str:
    """
    Recursively convert *expr* to LaTeX.

    :param expr:  Symbolic expression node.
    :param prec:  Minimum precedence of the parent context.
    :param right: True when *expr* is the right child of its parent
                  (affects parentheses for equal-precedence cases).
    :return: LaTeX math string.
    """
    if isinstance(expr, Const):
        return _print_const(expr)

    if isinstance(expr, Var):
        return _print_var(expr)

    if isinstance(expr, UnOp):
        return _wrap(_print_unop(expr),
                     _needs_parens(expr, prec, _UNARY, right=right))

    if isinstance(expr, BinOp):
        return _print_binop(expr, prec)

    if isinstance(expr, Func):
        return _wrap(_print_func(expr),
                     _needs_parens(expr, prec, _ATOM, right=right))

    if isinstance(expr, Func2):
        return _wrap(_print_func2(expr),
                     _needs_parens(expr, prec, _ATOM, right=right))

    if isinstance(expr, Comparison):
        return _wrap(_print_comparison(expr),
                     _needs_parens(expr, prec, _CMP, right=right))

    return str(expr)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def symbolic_to_latex(expr: Expr) -> str:
    """
    Convert a symbolic expression into a LaTeX math string.

    The output is intended for matplotlib mathtext rendering (no
    ``\\begin{equation}`` wrappers, no ``$`` delimiters).

    :param expr: Symbolic expression to convert.
    :return: LaTeX math string.
    """
    return _latex(expr)
