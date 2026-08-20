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

import math
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


def _format_real_number_latex(value: float) -> str:
    """Format one real scalar as unambiguous mathematical LaTeX.

    :param value: Real constant stored by the symbolic expression.
    :return: Integer, decimal, or scientific notation suitable for MathText.
    """
    if not math.isfinite(value):
        return str(value)
    elif value == int(value) and abs(value) < 1e15:
        return str(int(value))
    else:
        pass
    formatted: str = f"{value:.6g}"
    if "e" in formatted:
        mantissa: str
        exponent: str
        mantissa, exponent = formatted.split("e", 1)
        return rf"{mantissa} \times 10^{{{int(exponent)}}}"
    else:
        return formatted


def _print_const(expr: Const) -> str:
    """Render a constant as a plain number."""
    if expr.value is None:
        return r"\bot"
    else:
        pass
    value: object = expr.value
    if isinstance(value, complex):
        real_component: float = float(value.real)
        imaginary_component: float = float(value.imag)
        if imaginary_component == 0.0:
            return _format_real_number_latex(real_component)
        else:
            pass
        imaginary_magnitude: float = abs(imaginary_component)
        if imaginary_magnitude == 1.0:
            imaginary_term: str = r"\mathrm{j}"
        else:
            imaginary_term = (
                _format_real_number_latex(imaginary_magnitude) + r"\mathrm{j}"
            )
        if real_component == 0.0:
            if imaginary_component < 0.0:
                return f"-{imaginary_term}"
            else:
                return imaginary_term
        else:
            pass
        if imaginary_component < 0.0:
            sign: str = "-"
        else:
            sign = "+"
        real_term: str = _format_real_number_latex(real_component)
        return f"({real_term} {sign} {imaginary_term})"
    elif isinstance(value, float):
        return _format_real_number_latex(value)
    else:
        return str(value)


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
        # Explicit multiplication avoids rendering ``speed * RPM`` as
        # ``speed(RPM)`` when the right atom was previously parenthesized.
        return f"{left_latex} \\cdot {right_latex}"

    if _is_atom_like(right):
        return f"{left_latex} \\cdot {right_latex}"

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
    """Render a binary expression while preserving operator precedence.

    :param expr: Binary symbolic node to convert.
    :param parent_prec: Precedence required by the parent expression.
    :return: Semantically equivalent LaTeX.
    """
    op: str = expr.op

    if op == "+":
        lp: str = _latex(expr.left, _ADD)
        rp: str = _latex(expr.right, _ADD, right=True)
        return _wrap(f"{lp} + {rp}", _needs_parens(expr, parent_prec, _ADD))

    elif op == "-":
        lp = _latex(expr.left, _ADD)
        rp = _latex(expr.right, _ADD, right=True)
        if isinstance(expr.right, BinOp) and expr.right.op in ("+", "-"):
            # Subtraction is not associative. Retaining the right-hand group
            # is essential: a - (b + c) and a - (b - c) otherwise change
            # mathematical meaning when exported.
            rp = _wrap(rp, True)
        else:
            pass
        return _wrap(f"{lp} - {rp}", _needs_parens(expr, parent_prec, _ADD))

    elif op == "*":
        # Each recursive child printer already compares its real precedence
        # with ``_MUL``. Applying ``_needs_parens`` with a hard-coded child
        # precedence of ``_MUL`` parenthesized every right-hand atom and made a
        # product such as ``speed * RPM`` look like a function call.
        lp = _latex(expr.left, _MUL)
        rp = _latex(expr.right, _MUL, right=True)
        result: str = _print_mul(lp, rp, expr.left, expr.right)
        return _wrap(result, _needs_parens(expr, parent_prec, _MUL))

    elif op == "/":
        numerator: str = _latex(expr.left, _CMP)
        denominator: str = _latex(expr.right, _CMP)
        return _wrap(
            f"\\frac{{{numerator}}}{{{denominator}}}",
            _needs_parens(expr, parent_prec, _DIV),
        )

    elif op == "**":
        base_needs: bool = _needs_parens(expr.left, _POW, _POW)
        base: str = _wrap(_latex(expr.left, _POW), base_needs, big=base_needs)
        exponent: str = _latex(expr.right, _POW, right=True)
        return _wrap(
            f"{base}^{{{exponent}}}",
            _needs_parens(expr, parent_prec, _POW),
        )

    else:
        lp = _latex(expr.left, _ATOM)
        rp = _latex(expr.right, _ATOM)
        return f"{lp} {op} {rp}"


def _print_func(expr: Func) -> str:
    """Render one unary symbolic function with valid MathText grouping.

    :param expr: Unary symbolic function to convert.
    :return: MathText-compatible LaTeX.
    """
    tex_name: str = _FUNC_LATEX.get(expr.op, r"\operatorname{" + expr.op + "}")
    inner: str = _latex(expr.arg, _CMP)

    if expr.op == "sqrt":
        # MathText requires a braced radicand. Supplying a scalable delimiter
        # as the next token made square roots fall back to visible source code.
        return f"{tex_name}{{{inner}}}"
    elif expr.op == "abs":
        return f"{tex_name}{inner}\\rvert"
    elif expr.op in ("floor", "ceil"):
        close: str = r"\rfloor" if expr.op == "floor" else r"\rceil"
        return f"{tex_name}{inner}{close}"
    else:
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
