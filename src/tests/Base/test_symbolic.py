# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import ast
import copy
import json
import pytest
import math
import numpy as np
from typing import Any, Callable, Dict
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicJacobian, SymbolicVector
from VeraGridEngine.Utils.Symbolic.explicit_initialization_symbolic import build_explicit_init_graph
from VeraGridEngine.Utils.Symbolic.jit_compiler import SubexpressionAnalyzer
from VeraGridEngine.Utils.Symbolic.compare_expressions_structure import DAGNode, structural_hash, to_dag
from VeraGridEngine.Utils.Symbolic.block import (
    Block,
    DynamicModelContract,
    RmsPhysicalMeterKind,
    RmsTerminalPowerContribution,
    RmsTerminalSide,
    dynamic_model_contract_from_data,
)
from VeraGridEngine.Utils.Symbolic.symbolic_io import (
    duplicate_block,
    duplicate_block_across_factories,
    duplicate_block_vars_uid,
    expr_to_dict,
    parse_expr,
    BlockSaver,
    BlockParser,
)
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagram
from VeraGridEngine.Devices.Dynamic.var_factory import Connection, VarFactory
from VeraGridEngine.enumerations import ParamPowerFlowReferenceType, VarPowerFlowReferenceType
from VeraGridEngine.Utils.procedural_logic import AnalogFlipFlopLogic, ProceduralLogicCodec, aflipflop
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_editor_models import copy_block_state
from tests.symbolic_block_roundtrip import parse_saved_blocks

# -----------------------------------------------------------------------------
# Atomic & basic operations
# -----------------------------------------------------------------------------

def test_seeded_equipment_output_breaks_explicit_initialization_cycle() -> None:
    """A solved Q boundary seeds susceptance without reinitializing Q from it."""
    q = sym.Var("Qsvs")
    b = sym.Var("bsvs")
    model = Block(
        name="SVC",
        algebraic_vars=[q, b],
        algebraic_eqs=[q - b],
        init_eqs={q: b, b: q},
        post_init_seed_eqs={b: q, q: b},
        external_mapping={VarPowerFlowReferenceType.Vm: None, VarPowerFlowReferenceType.Q: q},
    )
    equations, _, order, _ = build_explicit_init_graph(
        model, preserved_var_uids={q.uid},
    )
    assert q not in equations
    assert equations[b] is q
    assert order == [b]


def test_unrelated_explicit_initialization_cycle_still_raises() -> None:
    """A seed without a declared physical boundary must not hide a cycle."""
    a = sym.Var("a")
    b = sym.Var("b")
    model = Block(
        name="unrelated cycle",
        algebraic_vars=[a, b],
        init_eqs={a: b, b: a},
        external_mapping={VarPowerFlowReferenceType.Q: a},
    )
    with pytest.raises(RuntimeError, match="Cycle detected"):
        build_explicit_init_graph(model, preserved_var_uids={a.uid})


def test_seeded_equipment_boundary_handles_intermediate_initializer() -> None:
    """The known power-flow output can break a longer declared seed loop."""
    q = sym.Var("Q")
    b = sym.Var("susceptance")
    intermediate = sym.Var("intermediate")
    model = Block(
        name="equipment",
        algebraic_vars=[q, b, intermediate],
        init_eqs={q: intermediate, intermediate: b, b: q},
        post_init_seed_eqs={b: q},
        external_mapping={VarPowerFlowReferenceType.Q: q},
    )
    equations, _, order, _ = build_explicit_init_graph(
        model, preserved_var_uids={q.uid},
    )
    assert q not in equations
    assert [var.uid for var in order] == [b.uid, intermediate.uid]

@pytest.mark.parametrize("use_jit", (False, True))
def test_complex_projection_derivatives_match_real_coordinate_finite_difference(use_jit: bool) -> None:
    """Compare native projected Jacobians with an independent AC current oracle.

    :param use_jit: Whether to compile the symbolic derivative with numba.
    :return: None; verify three operating points and every real coordinate.
    """
    variables: list[sym.Var] = list(sym.Var(name) for name in ("P", "Q", "Vm", "angle", "P"))
    current: sym.Expr = sym.conj(variables[0] + 1j * variables[1]) / sym.conj(
        variables[2] * sym.exp(1j * variables[3]))
    names: dict[int, str] = dict((var.uid, f"x[{i}]") for i, var in enumerate(variables))
    aliases: dict[int, str] = dict((var.uid, f"coordinate_{i}") for i, var in enumerate(variables))
    jacobian: SymbolicJacobian = SymbolicJacobian(
        eqs=list((sym.real(current), sym.imag(current))), variables=variables,
        compiler_names_dict=names, alias_names_dict=aliases, VARS_NAME="x",
        DIFF_NAME="dx", EVENT_PARAMS_NAME="events", PARAMS_NAME="parameters", use_jit=use_jit)
    empty: np.ndarray = np.zeros(0, dtype=np.float64)
    # The final coordinate shares a display name with P but has a different UID;
    # it must contribute neither numerical values nor sparse Jacobian storage.
    assert jacobian.J.indptr[-1] == jacobian.J.indptr[-2]
    sample: tuple[float, float, float, float, float]
    for sample in ((0.8, 0.2, 1.0, 0.0, 0.7), (-0.4, 0.3, 0.73, -0.6, -1.4), (1.2, -0.5, 1.3, 1.1, 3.0)):
        values: np.ndarray = np.asarray(sample, dtype=np.float64)
        expected: np.ndarray = np.empty((2, 5), dtype=np.float64)
        index: int
        for index in range(5):
            plus: np.ndarray = values.copy()
            minus: np.ndarray = values.copy()
            plus[index] += 1e-6
            minus[index] -= 1e-6
            # The oracle uses NumPy directly and never symbolic differentiation.
            plus_current: complex = np.conj(plus[0] + 1j * plus[1]) / np.conj(plus[2] * np.exp(1j * plus[3]))
            minus_current: complex = np.conj(minus[0] + 1j * minus[1]) / np.conj(minus[2] * np.exp(1j * minus[3]))
            difference: complex = (plus_current - minus_current) / 2e-6
            expected[:, index] = (difference.real, difference.imag)
        observed: np.ndarray = jacobian(values, empty, empty, empty, h=1.0).toarray()
        np.testing.assert_allclose(observed, expected, atol=1e-8, rtol=1e-7)


def test_complex_projection_derivatives_preserve_uid_and_dt() -> None:
    """Preserve UID identity, nested conjugation and derivative scaling.

    :return: None; distinguish equal display names and propagate the dt chain.
    """
    variable: sym.Var = sym.Var("same name")
    unrelated: sym.Var = sym.Var("same name")
    expression: sym.Expr = sym.real(sym.conj(sym.conj(variable * variable)))
    assert expression.diff(unrelated).eval_uid(dict(((variable.uid, 3.0),))) == 0.0
    assert expression.diff(variable).eval_uid(dict(((variable.uid, 3.0),))) == 6.0
    derivative: sym.Var = sym.Var("derivative", base_var=variable)
    projected: sym.Expr = sym.real(sym.conj(derivative * (1.0 + 2.0j)))
    scaled: sym.Expr = projected.diff(variable, dt=sym.Const(0.25))
    assert scaled.eval_uid(dict(((derivative.uid, 2.0),))) == 4.0
    # Dependency selection must retain the base coordinate of a derivative
    # occurrence, so the existing timestep scaling survives sparse compilation.
    names: dict[int, str] = dict(((variable.uid, "x[0]"), (unrelated.uid, "x[1]"), (derivative.uid, "dx[0]")))
    aliases: dict[int, str] = dict(((variable.uid, "coordinate_0"), (unrelated.uid, "coordinate_1"), (derivative.uid, "derivative_0")))
    jacobian: SymbolicJacobian = SymbolicJacobian(
        eqs=list((projected,)), variables=list((variable, unrelated)),
        compiler_names_dict=names, alias_names_dict=aliases, VARS_NAME="x",
        DIFF_NAME="dx", EVENT_PARAMS_NAME="events", PARAMS_NAME="parameters", use_jit=False)
    empty: np.ndarray = np.zeros(0, dtype=np.float64)
    observed: np.ndarray = jacobian(np.asarray((3.0, 7.0)), np.asarray((2.0,)), empty, empty, h=0.25).toarray()
    np.testing.assert_array_equal(observed, np.asarray(((4.0, 0.0),)))
    assert jacobian.J.nnz == 1

def test_const_eval() -> None:
    assert sym.Const(42).eval() == 42


def test_var_eval() -> None:
    x = sym.Var("x")
    assert x.eval(x=3.14) == 3.14
    with pytest.raises(ValueError):
        x.eval()  # missing binding


def test_binary_arithmetic() -> None:
    x, y = sym.Var("x1"), sym.Var("y")
    expr = 2 * x + y / 4 - 1
    result = expr.eval(x1=8, y=20)  # 2*8 + 20/4 - 1 = 16 + 5 - 1 = 20
    assert result == 20


def test_safe_divide_uses_explicit_zero_denominator_value() -> None:
    """Verify the explicit denominator fallback and reject a zero fallback.

    :return: None.
    """
    numerator: sym.Var = sym.Var("numerator")
    denominator: sym.Var = sym.Var("denominator")
    expression: sym.Expr = sym.safe_divide(
        numerator=numerator,
        denominator=denominator,
        zero_denominator_value=sym.Const(0.25),
    )

    assert expression.eval(numerator=12.0, denominator=3.0) == 4.0
    assert expression.eval(numerator=12.0, denominator=0.0) == 48.0
    with pytest.raises(ValueError, match="must be non-zero"):
        sym.safe_divide(
            numerator=numerator,
            denominator=denominator,
            zero_denominator_value=sym.Const(0.0),
        )


def test_safe_divide_derivative_matches_generated_expression() -> None:
    """Verify safe division has consistent symbolic and generated derivatives.

    :return: None.
    """
    numerator: sym.Var = sym.Var("numerator")
    denominator: sym.Var = sym.Var("denominator")
    expression: sym.Expr = sym.safe_divide(
        numerator=numerator,
        denominator=denominator,
        zero_denominator_value=sym.Const(0.25),
    )
    numerator_derivative: sym.Expr = expression.diff(numerator)
    compiler_names: Dict[int, str] = {
        numerator.uid: "numerator",
        denominator.uid: "denominator",
    }
    generated_expression: str = sym.expression2numba(
        expr=expression,
        compiler_names_dict=compiler_names,
    )

    assert numerator_derivative.eval(numerator=12.0, denominator=3.0) == 1.0 / 3.0
    assert numerator_derivative.eval(numerator=12.0, denominator=0.0) == 4.0
    parsed_expression: ast.Expression = ast.parse(generated_expression, mode="eval")
    assert isinstance(parsed_expression.body, ast.BinOp)
    assert generated_expression == (
        "numerator / ((_heaviside(denominator) + _heaviside(-denominator)) * denominator + "
        "(1.0 - (_heaviside(denominator) + _heaviside(-denominator))) * 0.25)"
    )
    assert expression.eval(numerator=12.0, denominator=3.0) == 4.0
    assert expression.eval(numerator=12.0, denominator=0.0) == 48.0


def test_sqrt_derivative_uses_finite_zero_boundary_slope() -> None:
    """Keep square-root Jacobians finite at a limited zero boundary.

    :return: None.
    """
    argument: sym.Var = sym.Var("argument")
    derivative: sym.Expr = sym.sqrt(argument).diff(argument)
    compiler_names: Dict[int, str] = {argument.uid: "argument"}
    generated_derivative: str = sym.expression2numba(
        expr=derivative,
        compiler_names_dict=compiler_names,
    )

    assert derivative.eval(argument=0.0) == 0.0
    assert derivative.eval(argument=4.0) == pytest.approx(0.25)
    parsed_derivative: ast.Expression = ast.parse(generated_derivative, mode="eval")
    assert isinstance(parsed_derivative.body, ast.BinOp)
    assert generated_derivative == (
        "1 / ((_heaviside(2 * np.sqrt(argument)) + _heaviside(-(2 * np.sqrt(argument)))) * "
        "(2 * np.sqrt(argument)) + (1.0 - (_heaviside(2 * np.sqrt(argument)) + "
        "_heaviside(-(2 * np.sqrt(argument)))))) * _heaviside(argument)"
    )


def test_unary_neg_pow() -> None:
    x = sym.Var("x")
    expr = -(x ** 2)
    assert expr.eval(x=3) == -9

# -----------------------------------------------------------------------------
# Functional expressions (sin, cos, tan, exp)
# -----------------------------------------------------------------------------

def test_trig_and_exp() -> None:
    x = sym.Var("x")
    expr = sym.sin(x) + sym.exp(2 * x)
    val = expr.eval(x=0)
    assert math.isclose(val, 1.0)  # sin(0)=0, exp(0)=1

# -----------------------------------------------------------------------------
# UID behaviour
# -----------------------------------------------------------------------------

def test_uid_uniqueness() -> None:
    a, b = sym.Var("x"), sym.Var("x")
    assert a.uid != b.uid
    expr = a + b
    assert len({a.uid, b.uid, expr.uid}) == 3  # all distinct


def test_subexpression_analyzer_distinguishes_duplicate_names_by_uid() -> None:
    a = sym.Var("x")
    b = sym.Var("x")
    analyzer = SubexpressionAnalyzer()

    assert analyzer.hash_expr(a + sym.Const(1.0)) != analyzer.hash_expr(b + sym.Const(1.0))

# -----------------------------------------------------------------------------
# JSON round‑trip
# -----------------------------------------------------------------------------

def test_serialisation_roundtrip() -> None:
    x, y = sym.Var("x"), sym.Var("y")
    expr = sym.sin(x) * (y + 3)

    blob = expr.to_json()
    clone = sym.Expr.from_json(blob)

    assert expr.eval(x=0.5, y=2) == clone.eval(x=0.5, y=2)
    # ensure UIDs are preserved
    assert expr.uid == json.loads(blob)["uid"]


def test_symbolic_io_func2_roundtrip() -> None:
    x: sym.Var = sym.Var("x")
    y: sym.Var = sym.Var("y")
    expr: sym.Expr = sym.atan2(x + sym.Const(1.0), y * sym.Const(2.0))
    const_dict: Dict[int, sym.Const] = dict()
    var_dict: Dict[int, sym.Var] = {x.uid: x, y.uid: y}
    diff_var_dict: Dict[int, sym.Var] = dict()

    payload: Dict[str, object] = expr_to_dict(expr=expr,
                                              const_dict=const_dict,
                                              var_dict=var_dict,
                                              diff_var_dict=diff_var_dict)
    restored: sym.Expr = parse_expr(data=payload,
                                    const_dict=const_dict,
                                    var_dict=var_dict,
                                    diff_var_dict=diff_var_dict)
    payload_roundtrip: Dict[str, object] = expr_to_dict(expr=restored,
                                                        const_dict=const_dict,
                                                        var_dict=var_dict,
                                                        diff_var_dict=diff_var_dict)

    assert isinstance(restored, sym.Func2)
    assert restored.name == "atan2"
    assert payload_roundtrip == payload
    assert math.isclose(restored.eval(x=1.5, y=0.25), expr.eval(x=1.5, y=0.25), rel_tol=1.0e-12)

# -----------------------------------------------------------------------------
# Immutability guarantees
# -----------------------------------------------------------------------------

# def test_func2_impl_mappingproxy():
#     with pytest.raises(TypeError):
#         sym.Func2._impl["atan2"] = None


# -----------------------------------------------------------------------------
# String representations (non‑critical, but nice to see)
# -----------------------------------------------------------------------------

def test_str_roundtrip() -> None:
    x = sym.Var("x")
    expr = (2 * x) / 5 - sym.cos(x)
    s = str(expr)
    # rudimentary checks — parentheses and operator symbols appear
    assert "(" in s and ")" in s and "/" in s and "cos" in s

# -----------------------------------------------------------------------------
# Helper utilities
# -----------------------------------------------------------------------------

def _numdiff(f: Callable[[float], float], x: float, h: float = 1e-6) -> float:
    """Central finite‑difference derivative."""
    return (f(x + h) - f(x - h)) / (2 * h)

# -----------------------------------------------------------------------------
# 1. Constant & variable evaluation
# -----------------------------------------------------------------------------

def test_constant_and_variable_eval() -> None:
    c = sym.Const(7)
    assert c.eval() == 7

    x = sym.Var("x")
    assert x.eval(x=3.14) == 3.14
    with pytest.raises(ValueError):
        x.eval()  # missing binding

# -----------------------------------------------------------------------------
# 2. UID‑based evaluation for duplicate names
# -----------------------------------------------------------------------------

def test_eval_uid_duplicate_names() -> None:
    x1, x2 = sym.Var("x"), sym.Var("x")
    expr = x1 + 2 * x2
    # name‑based → same value for both
    assert expr.eval(x=2) == 6
    # uid‑based → independent values
    vals = {x1.uid: 2, x2.uid: 5}
    assert sym.eval_uid(expr, vals) == 12


@pytest.mark.parametrize('exponent',(1.0,2.0,3.5))
def test_parameter_exponent_derivative_at_zero(exponent: float) -> None:
    """A constant-with-respect-to-state exponent must not create removable singularities.

    :param exponent: Fixed positive exponent supplied through a parameter symbol.
    """
    state: sym.Var = sym.Var('flux')
    parameter: sym.Var = sym.Var('exponent')
    unrelated: sym.Var = sym.Var('other')
    expression: sym.Expr = state**parameter
    bindings: dict[int,float] = dict([(state.uid,0.0),(parameter.uid,exponent)])
    assert expression.diff(state).simplify().eval_uid(bindings) == (1.0 if exponent == 1 else 0.0)
    assert expression.diff(unrelated).simplify().eval_uid(bindings) == 0

# -----------------------------------------------------------------------------
# 3. Elementary functions – value & derivative
# -----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "sym_func, math_func, point",
    [
        (sym.sin, math.sin, 0.3),
        (sym.cos, math.cos, 0.3),
        (sym.tan, math.tan, 0.3),
        (sym.exp, math.exp, 0.3),
        (sym.log, math.log, 1.3),
        (sym.sqrt, math.sqrt, 1.3),
        (sym.asin, math.asin, 0.3),
        (sym.acos, math.acos, 0.3),
        (sym.atan, math.atan, 0.3),
        (sym.sinh, math.sinh, 0.3),
        (sym.cosh, math.cosh, 0.3),
    ],
)
def test_elementary_functions(sym_func: Callable[[sym.Expr], sym.Expr],
                              math_func: Callable[[float], float],
                              point: float) -> None:
    x = sym.Var("x")
    expr = sym_func(x)
    # value
    assert math.isclose(expr.eval(x=point), math_func(point), rel_tol=1e-9)
    # derivative (numeric check)
    d_expr = expr.diff(x).simplify()
    numeric = _numdiff(math_func, point)
    assert math.isclose(d_expr.eval(x=point), numeric, rel_tol=1e-5)

# -----------------------------------------------------------------------------
# 4. General power rule (u(x) ** v(x))
# -----------------------------------------------------------------------------

# def test_general_power_rule():
#     x = sym.Var("x")
#     expr = x ** x
#     d = expr.diff(x).simplify()           # x**x * (log(x) + 1)
#     expected = lambda t: t ** t * (math.log(t) + 1)  # noqa: E731
#     assert math.isclose(d.eval(x=2.0), expected(2.0), rel_tol=1e-9)

# -----------------------------------------------------------------------------
# 5. Higher‑order derivatives & simplification
# -----------------------------------------------------------------------------

def test_higher_order_derivatives() -> None:
    x = sym.Var("x")
    expr = x ** 3
    second = sym.diff(expr, x, 2).simplify()
    third  = sym.diff(expr, x, 3).simplify()
    # Numeric checks
    assert second.eval(x=4) == 6 * 4
    assert isinstance(third, sym.Const) and third.value == 6

# -----------------------------------------------------------------------------
# 6. Simplification rules
# -----------------------------------------------------------------------------

def test_simplification_identities() -> None:
    x = sym.Var("x")
    assert ((x + sym.Const(0)).simplify()).__str__() == "x"
    assert ((sym.Const(0) * x).simplify()).eval(x=99) == 0
    assert ((x ** sym.Const(0)).simplify()).eval(x=5) == 1

# -----------------------------------------------------------------------------
# 7. Substitution mechanics
# -----------------------------------------------------------------------------

def test_substitution() -> None:
    x, y = sym.Var("x"), sym.Var("y")
    expr = x ** 2 + y
    replaced = expr.subs({x: y + 1})
    assert replaced.eval(y=3) == (3 + 1) ** 2 + 3  # 16 + 3 = 19

# -----------------------------------------------------------------------------
# 8. JSON round‑trip with UID preservation
# -----------------------------------------------------------------------------

def test_json_roundtrip_uid() -> None:
    x = sym.Var("x")
    expr = sym.sin(x) + sym.sqrt(x)
    clone = sym.Expr.from_json(expr.to_json())
    assert expr.uid == clone.uid
    assert expr.eval(x=0.9) == clone.eval(x=0.9)


def test_symbolic_jacobian_nonlinear_5x5() -> None:
    # -----------------------------
    # Variables
    # --------sym.---------------------
    x0 = sym.Var("x0")
    x1 = sym.Var("x1")
    x2 = sym.Var("x2")
    x3 = sym.Var("x3")
    x4 = sym.Var("x4")

    variables = [x0, x1, x2, x3, x4]

    # -----------------------------
    # Functions
    # -----------------------------
    f1 = x0 ** 2 + sym.sin(x1) + x2 * x3
    f2 = x1 ** 2 + sym.cos(x2) + x3 * x4
    f3 = x0 * x4 + x1 * x2
    f4 = sym.sin(x0) + x2 ** 2 + x3
    f5 = x0 * x1 + x4 ** 2

    eqs = [f1, f2, f3, f4, f5]

    # -----------------------------
    # Dictionaries for compilation
    # -----------------------------
    compiler_names_dict: Dict[int, str] = {}
    alias_names_dict: Dict[int, str] = {}

    VARS_NAME = "x"

    for i, v in enumerate(variables):
        compiler_names_dict[v.uid] = f"{VARS_NAME}[{i}]"
        alias_names_dict[v.uid] = f"{VARS_NAME}_{i}"

    # -----------------------------
    # Symbolic Jacobian
    # -----------------------------
    jac = SymbolicJacobian(
        eqs=eqs,
        variables=variables,
        compiler_names_dict=compiler_names_dict,
        alias_names_dict=alias_names_dict,
        VARS_NAME="x",
        DIFF_NAME="dx",
        EVENT_PARAMS_NAME="vp",
        PARAMS_NAME="cp",
        use_jit=False,
        batch_size=10,
        n_jobs=1
    )

    # -----------------------------
    # Evaluation point
    # -----------------------------
    xval = np.array([1.0, 2.0, 0.5, -1.0, 0.8])
    dx = np.zeros_like(xval)
    vp = np.zeros(0)
    cp = np.zeros(0)

    J_compiled = jac(xval, dx, vp, cp, h=1e-8).toarray()

    # -----------------------------
    # Numeric calculation
    # -----------------------------
    J_expected = np.array([
        [2 * xval[0], np.cos(xval[1]), xval[3], xval[2], 0.0],
        [0.0, 2 * xval[1], -np.sin(xval[2]), xval[4], xval[3]],
        [xval[4], xval[2], xval[1], 0.0, xval[0]],
        [np.cos(xval[0]), 0.0, 2 * xval[2], 1.0, 0.0],
        [xval[1], xval[0], 0.0, 0.0, 2 * xval[4]]
    ])

    print("J_compiled:\n", J_compiled)
    print("J_expected:\n", J_expected)

    assert np.allclose(J_compiled, J_expected, atol=1e-8)


def test_diff_var_deepcopy_does_not_mutate_original_links() -> None:
    """
    Check that copying a differential variable never rewires the source chain.

    :return: Nothing.
    """
    vf: VarFactory = VarFactory()
    x: sym.Var = vf.add_var(
        name="x",
        reference=VarPowerFlowReferenceType.Vm,
        network_conn=True,
        shared_reference="shared-x",
    )
    dx: sym.Var = vf.add_diff_var("dx", base_var=x)

    copied_dx: sym.Var = copy.deepcopy(dx)

    assert x.diff_var is dx
    assert dx.base_var is x
    assert copied_dx is not dx
    assert copied_dx.uid == dx.uid
    assert copied_dx.base_var is not x
    assert copied_dx.base_var.uid == x.uid
    assert copied_dx.base_var.diff_var is copied_dx


def test_var_factory_deepcopy_keeps_copied_diff_links_internal() -> None:
    """
    Check that copied factories contain derivative links only to copied variables.

    :return: Nothing.
    """
    vf: VarFactory = VarFactory()
    x: sym.Var = vf.add_var(
        "x",
        reference=VarPowerFlowReferenceType.Vm,
        network_conn=True,
        shared_reference="shared-x",
    )
    dx: sym.Var = vf.add_diff_var("dx", base_var=x)

    copied_vf: VarFactory = copy.deepcopy(vf)
    copied_x_or_none: sym.Var | None = copied_vf.get_var(x.non_mutable_uid)
    assert copied_x_or_none is not None
    copied_x: sym.Var = copied_x_or_none
    copied_dx: sym.Var = copied_vf.get_diff_var(dx.non_mutable_uid)

    assert x.diff_var is dx
    assert dx.base_var is x
    assert copied_x is not x
    assert copied_dx is not dx
    assert copied_x.diff_var is copied_dx
    assert copied_dx.base_var is copied_x


def test_block_deepcopy_reuses_copied_vars_inside_equations() -> None:
    """
    Check that copied blocks reuse the same cloned variables in lists and equations.

    :return: Nothing.
    """
    vf: VarFactory = VarFactory()
    x: sym.Var = vf.add_var("x")
    dx: sym.Var = vf.add_diff_var("dx", base_var=x)
    p: sym.Var = vf.add_var("p")
    c: sym.Const = vf.add_const(3.0, name="p_value")
    block: Block = Block(
        state_vars=[x],
        diff_vars=[dx],
        state_eqs=[dx + x],
        init_eqs={x: x + sym.Const(1.0)},
        diff_init_eqs={dx: dx + sym.Const(2.0)},
        parameters={p: c},
    )

    copied: Block = copy.deepcopy(block)
    copied_x: sym.Var = copied.state_vars[0]
    copied_dx: sym.Var = copied.diff_vars[0]

    assert x.diff_var is dx
    assert dx.base_var is x
    assert copied_x is not x
    assert copied_dx is not dx
    assert copied_x.diff_var is copied_dx
    assert copied_dx.base_var is copied_x
    assert copied.state_eqs[0].left is copied_dx
    assert copied.state_eqs[0].right is copied_x

    copied_const: sym.Const = next(iter(copied.parameters.values()))
    copied_const.value = 9.0
    assert c.value == 3.0


def test_block_deepcopy_preserves_editor_structure_metadata() -> None:
    """Keep editor structure metadata available on an isolated block copy.

    The dynamic editor commits a deep working copy back into the owned block.
    Losing either field during that boundary makes a valid editor model
    impossible to apply or changes whether its internal structure is exposed.

    :return: None.
    """
    source_block: Block = Block(is_decomposable=False)
    source_block.tpe_uid = 73

    copied_block: Block = copy.deepcopy(source_block)

    assert copied_block.is_decomposable is False
    assert copied_block.tpe_uid == 73


def test_duplicate_block_vars_uid_creates_isolated_factory_graph() -> None:
    """Verify editor cloning preserves identities without sharing symbolic state.

    :return: None.
    """
    source_vf: VarFactory = VarFactory()
    source_var: sym.Var = source_vf.add_var(name="source")
    target_var: sym.Var = source_vf.add_var(name="target", shared_reference="shared_signal")
    parameter_var: sym.Var = source_vf.add_var(name="gain")
    parameter_const: sym.Const = source_vf.add_const(value=2.0, name="gain_value")
    source_vf.add_connection(var_to_subs=target_var, incoming_var=source_var)
    owner: object = object()
    source_vf.register_var(dev=owner, var=target_var)
    source_block: Block = Block(
        algebraic_vars=list((source_var, target_var)),
        algebraic_eqs=list((source_var, target_var)),
        parameters=dict(((parameter_var, parameter_const),)),
        in_vars=list((target_var,)),
        out_vars=list((source_var,)),
        name="source_block",
    )
    target_vf: VarFactory = VarFactory()

    duplicated_block: Block = duplicate_block_vars_uid(
        block=source_block,
        source_var_factory=source_vf,
        target_var_factory=target_vf,
    )
    duplicated_source: sym.Var = duplicated_block.out_vars[0]
    duplicated_target: sym.Var = duplicated_block.in_vars[0]

    assert duplicated_block is not source_block
    assert duplicated_block.uid == source_block.uid
    assert duplicated_source is not source_var
    assert duplicated_target is not target_var
    assert duplicated_source.uid == source_var.uid
    assert duplicated_source.non_mutable_uid == source_var.non_mutable_uid
    assert duplicated_target.uid == target_var.uid
    assert duplicated_target.non_mutable_uid == target_var.non_mutable_uid
    assert duplicated_block.algebraic_eqs[0] is duplicated_source
    assert duplicated_block.algebraic_eqs[1] is duplicated_target
    duplicated_parameter_var: sym.Var = next(iter(duplicated_block.parameters.keys()))
    duplicated_parameter_const: sym.Const = duplicated_block.parameters[duplicated_parameter_var]
    assert duplicated_parameter_var.uid == parameter_var.uid
    assert duplicated_parameter_const.uid == parameter_const.uid
    assert duplicated_parameter_const is not parameter_const
    assert target_vf.get_var(duplicated_source.non_mutable_uid) is duplicated_source
    assert target_vf.get_var(duplicated_target.non_mutable_uid) is duplicated_target
    assert target_vf.get_connections_dict() is not source_vf.get_connections_dict()
    assert len(target_vf.get_connections_dict()[duplicated_source.non_mutable_uid]) == 1

    target_vf.remove_connection(
        var_to_disconnect=duplicated_target,
        outgoing_var=duplicated_source,
    )

    assert duplicated_source.non_mutable_uid not in target_vf.get_connections_dict()
    assert source_var.non_mutable_uid in source_vf.get_connections_dict()

    source_vf.merge_editor_var_factory(working_var_factory=target_vf)

    assert source_vf.get_var(duplicated_source.non_mutable_uid) is duplicated_source
    assert source_vf.get_var(duplicated_target.non_mutable_uid) is duplicated_target
    assert source_vf.get_const(parameter_const.uid) is duplicated_parameter_const
    assert source_vf.vars_info[owner][0] is duplicated_target
    assert duplicated_target.shared_ref is source_vf.get_references_dict()["shared_signal"]
    assert duplicated_source.non_mutable_uid not in source_vf.get_connections_dict()


def test_duplicate_block_across_factories_copies_only_internal_graph() -> None:
    """Clone internal aliases without sharing source variables or references.

    :return: None.
    """
    source_vf: VarFactory = VarFactory()
    source_var: sym.Var = source_vf.add_var(name="source")
    target_var: sym.Var = source_vf.add_var(
        name="target",
        shared_reference="shared_signal",
    )
    external_var: sym.Var = source_vf.add_var(name="external")
    source_vf.add_connection(
        var_to_subs=target_var,
        incoming_var=source_var,
    )
    source_vf.add_connection(
        var_to_subs=external_var,
        incoming_var=source_var,
    )
    source_block: Block = Block(
        algebraic_vars=list((source_var, target_var)),
        in_vars=list((target_var,)),
        out_vars=list((source_var,)),
    )
    target_vf: VarFactory = VarFactory()

    duplicated_block: Block = duplicate_block_across_factories(
        block=source_block,
        source_var_factory=source_vf,
        target_var_factory=target_vf,
    )
    duplicated_source: sym.Var = duplicated_block.out_vars[0]
    duplicated_target: sym.Var = duplicated_block.in_vars[0]
    duplicated_connections: list[Connection] = target_vf.get_connections_dict()[
        duplicated_source.non_mutable_uid
    ]

    assert duplicated_source is not source_var
    assert duplicated_target is not target_var
    assert duplicated_source.non_mutable_uid != source_var.non_mutable_uid
    assert duplicated_target.non_mutable_uid != target_var.non_mutable_uid
    assert duplicated_target.uid == duplicated_source.uid
    assert duplicated_target.name == duplicated_source.name
    assert target_var.shared_ref is not None
    assert duplicated_target.shared_ref is not None
    assert duplicated_target.shared_ref is not target_var.shared_ref
    assert duplicated_target.shared_ref is target_vf.get_references_dict()["shared_signal"]
    assert duplicated_target.shared_ref.uid == target_var.shared_ref.uid
    assert len(duplicated_connections) == 1
    assert duplicated_connections[0].non_mutable_uid == duplicated_target.non_mutable_uid
    assert external_var.non_mutable_uid not in target_vf.get_vars_dict()
    assert len(source_vf.get_connections_dict()[source_var.non_mutable_uid]) == 2


def test_duplicate_block_preserves_parent_child_variable_links_with_new_uids() -> None:
    """
    Check that block duplication keeps parent and child references coherent.

    :return: Nothing.
    """
    x: sym.Var = sym.Var("x")
    dx: sym.Var = sym.Var("dx", base_var=x)
    parent_signal: sym.Var = sym.Var("parent_signal")
    guard: sym.Var = sym.Var("guard")
    child: Block = Block(
        state_vars=[x],
        diff_vars=[dx],
        algebraic_vars=[guard],
        state_eqs=[dx + x],
        algebraic_eqs=[x - parent_signal],
        inequalities=[x < parent_signal],
        boolean_guards={guard: x > parent_signal},
    )
    parent: Block = Block(
        children=[child],
        algebraic_vars=[parent_signal],
        in_vars=[x],
        out_vars=[dx],
    )

    target_vf: VarFactory = VarFactory()
    copied: Block = duplicate_block(parent, target_vf)
    copied_child: Block = copied.children[0]
    copied_x: sym.Var = copied_child.state_vars[0]
    copied_dx: sym.Var = copied_child.diff_vars[0]
    copied_parent_signal: sym.Var = copied.algebraic_vars[0]
    copied_guard: sym.Var = copied_child.algebraic_vars[0]
    copied_inequality: sym.Expr | sym.Comparison = copied_child.inequalities[0]
    copied_guard_condition: sym.Expr | sym.Comparison = copied_child.boolean_guards[
        copied_guard
    ]

    assert copied.in_vars[0] is copied_x
    assert copied.out_vars[0] is copied_dx
    assert copied_x.uid != x.uid
    assert copied_dx.uid != dx.uid
    assert copied_x.diff_var is copied_dx
    assert copied_dx.base_var is copied_x
    assert copied_child.state_eqs[0].left is copied_dx
    assert copied_child.state_eqs[0].right is copied_x
    assert copied_child.algebraic_eqs[0].left is copied_x
    assert copied_child.algebraic_eqs[0].right is copied_parent_signal
    assert isinstance(copied_inequality, sym.Comparison)
    assert copied_inequality.lhs is copied_x
    assert copied_inequality.rhs is copied_parent_signal
    assert isinstance(copied_guard_condition, sym.Comparison)
    assert copied_guard_condition.lhs is copied_x
    assert copied_guard_condition.rhs is copied_parent_signal
    assert target_vf.get_var(copied_x.non_mutable_uid) is copied_x
    assert target_vf.get_diff_var(copied_dx.non_mutable_uid) is copied_dx



def test_duplicate_block_preserves_expression_only_external_variables() -> None:
    """Keep measured network variables shared when duplicating a controller.

    :return: None.
    """
    measured_value: sym.Var = sym.Var("measured_value")
    external_bus_voltage: sym.Var = sym.Var("external_bus_voltage")
    source_block: Block = Block(
        algebraic_vars=[measured_value],
        algebraic_eqs=[measured_value - external_bus_voltage],
    )

    copied_block: Block = duplicate_block(source_block, VarFactory())
    copied_value: sym.Var = copied_block.algebraic_vars[0]

    assert copied_value is not measured_value
    assert copied_block.algebraic_eqs[0].left is copied_value
    assert copied_block.algebraic_eqs[0].right is external_bus_voltage


def test_runtime_duplication_retains_only_explicit_external_network_edges() -> None:
    """Runtime copies may keep remote measurements while editor copies stay isolated.

    :return: None.
    """
    factory: VarFactory = VarFactory()
    remote: sym.Var = factory.add_var('remote_bus_voltage')
    ordinary: sym.Var = factory.add_var('unrelated_controller_signal')
    measured: sym.Var = factory.add_var('measurement_input')
    unshared: sym.Var = factory.add_var('ordinary_input')
    output: sym.Var = factory.add_var('measured_output')
    source: Block = Block(in_vars=list((measured,unshared)),algebraic_vars=list((output,)),
        algebraic_eqs=list((output-measured-unshared,)),out_vars=list((output,)))
    factory.add_network_connection(measured,remote)
    factory.add_connection(unshared,ordinary)
    isolated: Block = duplicate_block(source,factory)
    runtime: Block = duplicate_block(source,factory,preserve_external_network_connections=True)
    assert isolated.in_vars[0].uid != remote.uid
    assert runtime.in_vars[0].uid == remote.uid
    assert runtime.in_vars[1].uid != ordinary.uid
    assert runtime.algebraic_vars[0].uid != output.uid
    assert measured.uid == remote.uid


def test_block_diagram_parse_accepts_empty_legacy_payload() -> None:
    """
    Check that empty legacy diagram payloads load as empty diagrams.

    :return: Nothing.
    """
    diagram: BlockDiagram = BlockDiagram()

    diagram.parse(dict())

    assert diagram.status is None
    assert diagram.node_data == dict()
    assert diagram.con_data == dict()


def test_var_factory_parse_var_dict_accepts_legacy_missing_identity_half() -> None:
    """
    Check that a legacy symbolic variable missing one id still loads.

    :return: Nothing.
    """
    vf: VarFactory = VarFactory()

    vf.parse_var_dict([
        {
            "type": "Var",
            "name": "omega_legacy",
            "uid": 55,
            "shared_ref": None,
        }
    ])

    parsed_var: sym.Var | None = vf.get_vars_dict().get(55, None)
    assert parsed_var is not None
    assert parsed_var.uid == 55
    assert parsed_var.non_mutable_uid == 55


def _save_block_parser_fixture(block: Block) -> tuple[dict[str, Any], BlockSaver]:
    """Prepare canonical symbolic tables and an editable root record.

    :param block: Test model whose variables and constants must survive parsing.
    :return: Independent root record and its corresponding symbolic tables.
    """
    saver: BlockSaver = BlockSaver(VarFactory())
    saver.save_block(block)
    records: dict[int, dict[str, Any]] = copy.deepcopy(saver.get_blocks())
    return records[block.uid], saver


def _parse_test_block(data: dict[str, Any], saver: BlockSaver,
                      procedural_logic_codec: ProceduralLogicCodec | None = None,
                      logger: Logger | None = None) -> Block:
    """Reconstruct one test root through the public collection parser.

    :param data: Editable canonical root record.
    :param saver: Symbolic tables produced before editing the block record.
    :param procedural_logic_codec: Optional procedural declaration decoder.
    :param logger: Optional sink for recoverable legacy-data diagnostics.
    :return: The single reconstructed root.
    """
    parser: BlockParser = BlockParser(VarFactory(), logger, procedural_logic_codec)
    records: dict[int, dict[str, Any]] = copy.deepcopy(saver.get_blocks())
    root_block_uid: int = data["uid"]
    records[root_block_uid] = data
    roots: list[Block] = parse_saved_blocks(parser=parser, saver=saver, data=records)
    assert len(roots) == 1
    return roots[0]


def test_block_saver_parser_roundtrip_preserves_declarative_procedural_logic() -> None:
    """
    Check that block saver/parser preserve declarative procedural logic.

    :return: Nothing.
    """
    vf: VarFactory = VarFactory()
    x: sym.Var = vf.add_var(
        "x",
        reference=VarPowerFlowReferenceType.Vm,
        network_conn=True,
        shared_reference="shared-x",
    )
    mode: sym.Var = vf.add_var("mode")
    out: sym.Var = vf.add_var("out")

    block: Block = Block(
        algebraic_vars=[x, mode, out],
        algebraic_eqs=[x + sym.Const(1.0), mode + sym.Const(0.0), out + sym.Const(0.0)],
        inequalities=[x > sym.Const(0.0)],
        discrete_eqs={mode: x + sym.Const(2.0)},
        mode_dict={mode: sym.Const(1.0)},
        procedural_logic=[aflipflop(x=x,
                                    boolset=x > sym.Const(1.0),
                                    boolreset=x < sym.Const(-1.0),
                                    output=out)],
        name="legacy_runtime_block",
    )
    source_data: dict[str, Any]
    saver: BlockSaver
    source_data, saver = _save_block_parser_fixture(block)

    direct_restored: Block = _parse_test_block(saver=saver,
        data=copy.deepcopy(source_data),
        procedural_logic_codec=ProceduralLogicCodec(),
    )
    direct_restored_x: sym.Var = direct_restored.algebraic_vars[0]
    assert direct_restored_x.ref is VarPowerFlowReferenceType.Vm
    # Symbolic archives retain the physical reference and shared identity;
    # network_conn is a runtime flag absent from their variable records.
    assert direct_restored_x.network_conn is False
    assert direct_restored_x.shared_ref is not None
    assert direct_restored_x.shared_ref.name == "shared-x"
    assert direct_restored_x.shared_ref.uid == x.shared_ref.uid

    truncated_data: dict[str, object] = copy.deepcopy(source_data)
    truncated_contract: object = truncated_data["dynamic_model_contract"]
    assert isinstance(truncated_contract, dict)
    truncated_contract.pop("modal_template_kind")
    with pytest.raises(KeyError, match="modal_template_kind"):
        _parse_test_block(saver=saver,
            data=truncated_data,
            procedural_logic_codec=ProceduralLogicCodec(),
        )

    invalid_uid_data: dict[str, object] = copy.deepcopy(source_data)
    invalid_uid_contract: object = invalid_uid_data["dynamic_model_contract"]
    assert isinstance(invalid_uid_contract, dict)
    invalid_uid_contract["dgs_elmsvs_remote_voltage_var_uid"] = -1
    with pytest.raises(KeyError, match="extra"):
        _parse_test_block(saver=saver,
            data=invalid_uid_data,
            procedural_logic_codec=ProceduralLogicCodec(),
        )

    saver: BlockSaver = BlockSaver(vf)
    saver.save_block(block)

    # The archive writer JSON-encodes the complete block table.  This check
    # prevents runtime procedural-logic objects from silently causing the
    # ``blocks.symbolic`` archive member to be omitted.
    json.dumps(saver.get_blocks())

    parser_without_codec: BlockParser = BlockParser(VarFactory())
    with pytest.raises(ValueError, match="requires an explicit codec"):
        parse_saved_blocks(
            parser=parser_without_codec,
            saver=saver,
            data=saver.get_blocks(),
        )

    parser: BlockParser = BlockParser(
        var_factory=VarFactory(),
        procedural_logic_codec=ProceduralLogicCodec(),
    )
    restored: Block = parse_saved_blocks(
        parser=parser,
        saver=saver,
        data=saver.get_blocks(),
    )[0]

    assert len(restored.discrete_eqs) == 1
    assert len(restored.mode_dict) == 1
    assert len(restored.procedural_logic) == 1
    assert isinstance(restored.procedural_logic[0], AnalogFlipFlopLogic)
    restored_x: sym.Var = restored.algebraic_vars[0]
    assert len(restored.inequalities) == 1
    restored_inequality: sym.Expr | sym.Comparison = restored.inequalities[0]
    assert isinstance(restored_inequality, sym.Comparison)
    assert restored_inequality.lhs is restored_x
    assert restored_inequality.op is sym.CmpOp.GT


def test_rms_terminal_power_contract_roundtrips_and_fails_closed() -> None:
    """Discard obsolete RMS terminal metadata while validating old payloads.

    :return: None.
    """
    var_factory: VarFactory = VarFactory()
    dc_power: sym.Var = var_factory.add_var(name="Pdc")
    ac_active_power: sym.Var = var_factory.add_var(name="Pac")
    ac_reactive_power: sym.Var = var_factory.add_var(name="Qac")
    block: Block = Block(
        algebraic_vars=list((dc_power, ac_active_power, ac_reactive_power)),
        algebraic_eqs=list((dc_power, ac_active_power, ac_reactive_power)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Pf, dc_power),
            (VarPowerFlowReferenceType.Pt, ac_active_power),
            (VarPowerFlowReferenceType.Qt, ac_reactive_power),
        )),
    )
    legacy_contributions = list((
        RmsTerminalPowerContribution(
            terminal_side=RmsTerminalSide.FROM,
            active_power_reference=VarPowerFlowReferenceType.Pf,
            reactive_power_reference=None,
        ),
        RmsTerminalPowerContribution(
            terminal_side=RmsTerminalSide.TO,
            active_power_reference=VarPowerFlowReferenceType.Pt,
            reactive_power_reference=VarPowerFlowReferenceType.Qt,
        ),
    ))
    block.modal_template_kind = "configurable_integrator"
    block.modal_template_config = dict((
        ("scaling", "GAIN"),
        ("scale_bounds_by_gain", True),
    ))

    source_data: dict[str, Any]
    saver: BlockSaver
    source_data, saver = _save_block_parser_fixture(block)
    persisted_data: dict[str, object] = copy.deepcopy(source_data)
    contract_data = persisted_data["dynamic_model_contract"]
    assert isinstance(contract_data, dict)
    assert contract_data["version"] == 15
    assert "emt_finite_reciprocal_source_mode_var_uid" not in contract_data
    assert "rms_terminal_power_contributions" not in contract_data
    restored: Block = _parse_test_block(saver=saver, data=persisted_data)
    copied: Block = copy.deepcopy(block)
    saver: BlockSaver = BlockSaver(var_factory)
    saver.save_block(block)
    parser: BlockParser = BlockParser(var_factory=VarFactory())
    symbolic_io_restored: Block = parse_saved_blocks(
        parser=parser,
        saver=saver,
        data=saver.get_blocks(),
    )[0]
    assert restored.modal_template_kind == "configurable_integrator"
    assert restored.modal_template_config == block.modal_template_config
    assert copied.modal_template_kind == "configurable_integrator"
    assert copied.modal_template_config == block.modal_template_config
    assert symbolic_io_restored.modal_template_kind == "configurable_integrator"
    assert symbolic_io_restored.modal_template_config == block.modal_template_config

    # Both branches used version seven. Exercise the editable fixture and direct
    # flat table so absent declarations keep their typed defaults.
    has_modal_fields: bool
    for has_modal_fields in (False, True):
        version_seven_data: dict[str, object] = copy.deepcopy(source_data)
        version_seven_contract: object = version_seven_data["dynamic_model_contract"]
        assert isinstance(version_seven_contract, dict)
        version_seven_contract["version"] = 7
        version_seven_contract["emt_finite_reciprocal_source_mode_var_uid"] = None
        if has_modal_fields:
            version_seven_contract.pop("emt_finite_reciprocal_source_mode_var_uid", None)
        else:
            version_seven_contract.pop("modal_template_kind")
            version_seven_contract.pop("modal_template_config")
        version_seven_restored: Block = _parse_test_block(saver=saver, data=version_seven_data)
        assert "emt_finite_reciprocal_source_mode_var_uid" not in version_seven_restored.dynamic_model_contract.to_data()
        assert version_seven_restored.to_dict()["dynamic_model_contract"]["version"] == 15
        if has_modal_fields:
            assert version_seven_restored.modal_template_kind == block.modal_template_kind
            assert version_seven_restored.modal_template_config == block.modal_template_config
        else:
            assert version_seven_restored.modal_template_kind is None
            assert version_seven_restored.modal_template_config is None

        version_seven_blocks: dict[int, dict[str, object]] = copy.deepcopy(saver.get_blocks())
        version_seven_blocks[block.uid]["dynamic_model_contract"] = version_seven_contract
        version_seven_parser: BlockParser = BlockParser(var_factory=VarFactory())
        version_seven_io_restored: Block = parse_saved_blocks(
            parser=version_seven_parser,
            saver=saver,
            data=version_seven_blocks,
        )[0]
        assert version_seven_io_restored.modal_template_kind == version_seven_restored.modal_template_kind
        assert version_seven_io_restored.modal_template_config == version_seven_restored.modal_template_config
    else:
        pass

    assert "rms_terminal_power_contributions" not in DynamicModelContract.__slots__

    # Version 1 predates both formulation-specific terminal contracts.
    legacy_data: dict[str, object] = copy.deepcopy(source_data)
    legacy_contract: object = legacy_data["dynamic_model_contract"]
    assert isinstance(legacy_contract, dict)
    legacy_contract["version"] = 1
    legacy_contract.pop("emt_finite_reciprocal_source_mode_var_uid", None)
    legacy_contract.pop("emt_internal_grounding_link", None)
    legacy_contract.pop("modal_template_kind")
    legacy_contract.pop("modal_template_config")
    legacy_restored: Block = _parse_test_block(saver=saver, data=legacy_data)

    # Version 2 retains the RMS declaration and predates only the EMT field.
    version_two_data: dict[str, object] = copy.deepcopy(source_data)
    version_two_contract: object = version_two_data["dynamic_model_contract"]
    assert isinstance(version_two_contract, dict)
    version_two_contract["version"] = 2
    version_two_contract.pop("emt_finite_reciprocal_source_mode_var_uid", None)
    version_two_contract["rms_terminal_power_contributions"] = [
        contribution.to_data() for contribution in legacy_contributions
    ]
    version_two_contract.pop("emt_internal_grounding_link", None)
    version_two_contract.pop("modal_template_kind")
    version_two_contract.pop("modal_template_config")
    version_two_restored: Block = _parse_test_block(saver=saver, data=version_two_data)

    # Version 3 includes both terminal contracts but predates typed grounding.
    version_three_data: dict[str, object] = copy.deepcopy(source_data)
    version_three_contract: object = version_three_data["dynamic_model_contract"]
    assert isinstance(version_three_contract, dict)
    version_three_contract["version"] = 3
    version_three_contract.pop("emt_finite_reciprocal_source_mode_var_uid", None)
    version_three_contract["rms_terminal_power_contributions"] = [
        contribution.to_data() for contribution in legacy_contributions
    ]
    version_three_contract.pop("emt_internal_grounding_link", None)
    version_three_contract.pop("modal_template_kind")
    version_three_contract.pop("modal_template_config")
    version_three_restored: Block = _parse_test_block(saver=saver, data=version_three_data)
    assert "emt_internal_grounding_link" not in version_three_restored.dynamic_model_contract.to_data()

    # Version 4 includes typed grounding but predates physical meter identity.
    version_four_data: dict[str, object] = copy.deepcopy(source_data)
    version_four_contract: object = version_four_data["dynamic_model_contract"]
    assert isinstance(version_four_contract, dict)
    version_four_contract["version"] = 4
    version_four_contract.pop("emt_finite_reciprocal_source_mode_var_uid", None)
    version_four_contract["rms_terminal_power_contributions"] = [
        contribution.to_data() for contribution in legacy_contributions
    ]
    version_four_contract.pop("modal_template_kind")
    version_four_contract.pop("modal_template_config")
    version_four_restored: Block = _parse_test_block(saver=saver, data=version_four_data)

    # Version 6 predates both branches' version-seven declarations.
    version_six_data: dict[str, object] = copy.deepcopy(source_data)
    version_six_contract: object = version_six_data["dynamic_model_contract"]
    assert isinstance(version_six_contract, dict)
    version_six_contract["version"] = 6
    version_six_contract.pop("emt_finite_reciprocal_source_mode_var_uid", None)
    version_six_contract.pop("modal_template_kind")
    version_six_contract.pop("modal_template_config")
    version_six_restored: Block = _parse_test_block(saver=saver, data=version_six_data)
    assert version_six_restored.modal_template_kind is None
    assert version_six_restored.modal_template_config is None

    malformed_data: dict[str, object] = copy.deepcopy(source_data)
    malformed_contract: object = malformed_data["dynamic_model_contract"]
    assert isinstance(malformed_contract, dict)
    malformed_contract["version"] = 5
    malformed_contract.pop("emt_finite_reciprocal_source_mode_var_uid", None)
    malformed_contract["rms_terminal_power_contributions"] = [
        contribution.to_data() for contribution in legacy_contributions
    ]
    malformed_contract.pop("modal_template_kind")
    malformed_contract.pop("modal_template_config")
    malformed_contributions: object = malformed_contract[
        "rms_terminal_power_contributions"
    ]
    assert isinstance(malformed_contributions, list)
    malformed_first: object = malformed_contributions[0]
    assert isinstance(malformed_first, dict)
    malformed_first["active_power_reference"] = VarPowerFlowReferenceType.Vm.value
    with pytest.raises(ValueError, match="from-terminal active power"):
        _parse_test_block(saver=saver, data=malformed_data)








@pytest.mark.parametrize(
    "invalid_resistance",
    (math.nan, math.inf, -math.inf, 0.0, -1.0),
)
def test_dynamic_model_contract_rejects_removed_fields_in_current_schema(
        invalid_resistance: float,
) -> None:
    """Reject removed import fields in the current persistent schema.

    :param invalid_resistance: Invalid serialized resistance value.
    :return: Nothing.
    """
    source_data: dict[str, Any]
    saver: BlockSaver
    source_data, saver = _save_block_parser_fixture(Block())
    source_contract: object = source_data["dynamic_model_contract"]
    assert isinstance(source_contract, dict)
    source_contract["dgs_logical_actuator_root_id"] = "root-fid"
    source_contract["dgs_open_resistance_ohm"] = invalid_resistance

    with pytest.raises(KeyError, match="extra"):
        _parse_test_block(saver=saver, data=source_data)


def test_block_parser_handles_malformed_structural_fields() -> None:
    """Reject unusable containers and diagnose recoverable invalid references.

    :return: None.
    """
    source_block: Block = Block(name="typed persistence boundary")
    source_data: dict[str, Any]
    saver: BlockSaver
    source_data, saver = _save_block_parser_fixture(source_block)

    # A non-iterable variable collection cannot be reconstructed.
    malformed_sequence_data: dict[str, object] = copy.deepcopy(source_data)
    malformed_sequence_data["state_vars"] = None
    with pytest.raises(TypeError, match="not iterable"):
        _parse_test_block(saver=saver, data=malformed_sequence_data)

    # The archive parser skips invalid child links and reports the lost edge.
    malformed_child_data: dict[str, object] = copy.deepcopy(source_data)
    malformed_child_data["children"] = list((None,))
    logger: Logger = Logger()
    restored: Block = _parse_test_block(saver=saver, data=malformed_child_data, logger=logger)
    assert restored.children == list()
    assert logger.warning_count() == 1
    assert "Missing child dynamic block" in str(logger)

    # Invalid root identities cannot materialize a block. Unlike the old
    # Block.parse name check, this is the collection parser's identity boundary.
    malformed_identity_data: dict[str, object] = copy.deepcopy(source_data)
    malformed_identity_data["uid"] = "invalid-root-uid"
    identity_logger: Logger = Logger()
    parser: BlockParser = BlockParser(VarFactory(), logger=identity_logger)
    assert parse_saved_blocks(
        parser=parser,
        saver=saver,
        data=dict(((source_block.uid, malformed_identity_data),)),
    ) == list()
    assert identity_logger.warning_count() == 1
    assert "Invalid dynamic block UID" in str(identity_logger)


def test_block_parsers_migrate_legacy_frequency_mapping() -> None:
    """Migrate persisted ``fn`` API mappings to the canonical ``freq`` key.

    :return: Nothing.
    """
    source_factory: VarFactory = VarFactory()
    frequency: sym.Var = source_factory.add_var("frequency")
    source_block: Block = Block(
        parameters=dict(((frequency, sym.Const(50.0)),)),
        api_obj_mapping=dict({ParamPowerFlowReferenceType.freq: frequency}),
        name="legacy_frequency_mapping",
    )

    # Exercise an editable root record after replacing the current key with the
    # spelling emitted by older saved dynamic-model files.
    source_data: dict[str, Any]
    saver: BlockSaver
    source_data, saver = _save_block_parser_fixture(source_block)
    declarative_data: Dict[str, Any] = copy.deepcopy(source_data)
    declarative_mapping: Dict[str, Any] = declarative_data["api_obj_mapping"]
    declarative_mapping["fn"] = declarative_mapping.pop(ParamPowerFlowReferenceType.freq.value)
    declarative_restored: Block = _parse_test_block(saver=saver, data=declarative_data)
    declarative_frequency: sym.Var | None = declarative_restored.api_obj_mapping.get(
        ParamPowerFlowReferenceType.freq,
        None,
    )

    assert declarative_frequency is not None
    assert declarative_frequency.uid == frequency.uid

    # Exercise a flat UID-based block table because historical project files
    # use this persistence representation as well.
    saver: BlockSaver = BlockSaver(source_factory)
    saver.save_block(source_block)
    legacy_blocks: Dict[int, Dict[str, Any]] = copy.deepcopy(saver.get_blocks())
    legacy_block_data: Dict[str, Any] = legacy_blocks[source_block.uid]
    legacy_mapping: Dict[str, int | None] = legacy_block_data["api_obj_mapping"]
    legacy_mapping["fn"] = legacy_mapping.pop(ParamPowerFlowReferenceType.freq.value)

    legacy_parser: BlockParser = BlockParser(VarFactory(), logger=Logger())
    legacy_restored: Block = parse_saved_blocks(
        parser=legacy_parser,
        saver=saver,
        data=legacy_blocks,
    )[0]
    legacy_frequency: sym.Var | None = legacy_restored.api_obj_mapping.get(
        ParamPowerFlowReferenceType.freq,
        None,
    )

    assert legacy_frequency is not None
    assert legacy_frequency.uid == frequency.uid


def test_block_parser_only_warns_for_broken_optional_mapping_references() -> None:
    """
    Check that optional null mappings are silent while broken UIDs warn.

    :return: Nothing.
    """
    source_factory: VarFactory = VarFactory()
    variable: sym.Var = source_factory.add_var("x")
    source_block: Block = Block(
        algebraic_vars=[variable],
        algebraic_eqs=[variable],
        external_mapping=dict({VarPowerFlowReferenceType.Vm: None}),
        api_obj_mapping=dict({ParamPowerFlowReferenceType.r: None}),
        name="optional_mapping_block",
    )
    saver: BlockSaver = BlockSaver(source_factory)
    saver.save_block(source_block)

    # Parse the explicit legacy nulls first. They represent optional empty
    # mapping slots and therefore must not interrupt file opening with warnings.
    null_logger: Logger = Logger()
    null_parser: BlockParser = BlockParser(VarFactory(), logger=null_logger)
    restored_block: Block = parse_saved_blocks(
        parser=null_parser,
        saver=saver,
        data=saver.get_blocks(),
    )[0]

    assert null_logger.warning_count() == 0
    assert restored_block.api_obj_mapping == dict()
    assert restored_block.external_mapping[VarPowerFlowReferenceType.Vm] is None

    # Replace both optional nulls with non-null UIDs absent from the factory.
    # Those references claim that data exists, so silently dropping them could
    # change model initialization and must remain visible to the user.
    broken_blocks: Dict[int, Dict[str, Any]] = copy.deepcopy(saver.get_blocks())
    broken_block_data: Dict[str, Any] = broken_blocks[source_block.uid]
    broken_api_mapping: Dict[str, int | None] = broken_block_data["api_obj_mapping"]
    broken_external_mapping: Dict[str, int | None] = broken_block_data["external_mapping"]
    broken_api_mapping[ParamPowerFlowReferenceType.r.value] = variable.uid + 1
    broken_external_mapping[VarPowerFlowReferenceType.Vm.value] = variable.uid + 2

    broken_logger: Logger = Logger()
    broken_parser: BlockParser = BlockParser(VarFactory(), logger=broken_logger)
    parse_saved_blocks(
        parser=broken_parser,
        saver=saver,
        data=broken_blocks,
    )

    assert broken_logger.warning_count() == 2
    assert {entry.device_property for entry in broken_logger.entries} == {
        "api_obj_mapping",
        "external_mapping",
    }


def test_block_update_model_replaces_complete_symbolic_interface() -> None:
    """Replace one variable consistently across ports, owners and mappings.

    :return: None.
    """
    original_var: sym.Var = sym.Var(name="signal")
    replacement_var: sym.Var = sym.Var(name="measured_signal")
    child_block: Block = Block(
        name="consumer",
        in_vars=list((original_var,)),
        out_vars=list((original_var,)),
        algebraic_vars=list((original_var,)),
        algebraic_eqs=list((original_var - sym.Const(1.0),)),
    )
    child_block.var_mapping["signal"] = original_var
    root_block: Block = Block(
        name="root",
        children=list((child_block,)),
        in_vars=list((original_var,)),
        out_vars=list((original_var,)),
    )

    root_block.update_model(old=original_var, new=replacement_var)

    assert root_block.in_vars[0] is replacement_var
    assert root_block.out_vars[0] is replacement_var
    assert child_block.in_vars[0] is replacement_var
    assert child_block.out_vars[0] is replacement_var
    assert child_block.algebraic_vars[0] is replacement_var
    assert child_block.var_mapping["signal"] is replacement_var
    assert original_var not in child_block.algebraic_eqs[0].get_vars()
    assert replacement_var in child_block.algebraic_eqs[0].get_vars()


# -----------------------------------------------------------------------------
# 9. Immutability checks
# -----------------------------------------------------------------------------
#
# def test_mappingproxy_immutable():
#     assert isinstance(sym.BinOp._impl, MappingProxyType)
#     with pytest.raises(TypeError):
#         sym.BinOp._impl["+"] = None  # type: ignore[misc]

#
# def test_frozen_dataclass_immutable():
#     c = sym.Const(1)
#     with pytest.raises(AttributeError):
#         c.value = 2  # type: ignore[attr-defined]


@pytest.mark.parametrize("use_jit", [False, True])
@pytest.mark.parametrize("point", [(0.7, 1.2), (-0.7, 1.2), (0.7, -1.2), (-0.7, -1.2)])
def test_generated_values_and_jacobian_preserve_ordered_operations(use_jit: bool,
                                                                  point: tuple[float, float]) -> None:
    """Check emitted angle, powers and negation against independent formulas.

    :param use_jit: Whether the same expression is executed through Numba.
    :param point: Nonsymmetric point away from the atan2 singularity/branch cut.
    :return: None; value, analytic slope and finite-difference evidence must agree.
    """
    x: sym.Var = sym.Var("x")
    y: sym.Var = sym.Var("y")
    expressions: list[sym.Expr] = list((sym.atan2(x, y), (x ** 2) ** 3,
                                        x ** (sym.Const(2) ** 3), (-x) ** 2,
                                        -(x ** 2), (-x) * y, x - (y - x)))
    names: Dict[int, str] = dict(((x.uid, "values[0]"), (y.uid, "values[1]")))
    aliases: Dict[int, str] = dict(((x.uid, "x0"), (y.uid, "y0")))
    values: np.ndarray = np.array(point, dtype=float)
    empty: np.ndarray = np.zeros(0, dtype=float)
    vector: SymbolicVector = SymbolicVector(expressions, names, aliases,
                                           "values", "diff", "events", "params", use_jit=use_jit)
    jacobian: SymbolicJacobian = SymbolicJacobian(expressions, list((x, y)), names, aliases,
                                                 "values", "diff", "events", "params", use_jit=use_jit)
    xv: float = point[0]
    yv: float = point[1]
    expected: np.ndarray = np.array((np.arctan2(xv, yv), xv ** 6, xv ** 8,
                                      xv ** 2, -xv ** 2, -xv * yv, 2 * xv - yv))
    expected_jacobian: np.ndarray = np.array(((yv / (xv*xv + yv*yv), -xv / (xv*xv + yv*yv)),
                                               (6*xv**5, 0), (8*xv**7, 0), (2*xv, 0),
                                               (-2*xv, 0), (-yv, -xv), (2, -1)))
    np.testing.assert_allclose(vector(values, empty, empty, empty), expected, rtol=2e-12, atol=2e-12)
    np.testing.assert_allclose(jacobian(values, empty, empty, empty, 0.01).toarray(),
                               expected_jacobian, rtol=2e-12, atol=2e-12)
    numerical: np.ndarray = np.zeros((len(expressions), 2))
    index: int
    for index in range(2):
        upper: np.ndarray = values.copy()
        lower: np.ndarray = values.copy()
        upper[index] += 1e-6
        lower[index] -= 1e-6
        upper_result: np.ndarray = vector(upper, empty, empty, empty).copy()
        lower_result: np.ndarray = vector(lower, empty, empty, empty).copy()
        numerical[:, index] = (upper_result - lower_result) / 2e-6
    np.testing.assert_allclose(numerical, expected_jacobian, rtol=2e-7, atol=2e-7)
    # A negative constant base with a variable exponent must keep its grouping;
    # integer-valued runtime exponents provide an independent real-valued oracle.
    negative_base: SymbolicVector = SymbolicVector(list((sym.Const(-2.0) ** x,)),
        names, aliases, "values", "diff", "events", "params", use_jit=use_jit)
    assert negative_base(np.array((2.0, 0.0)), empty, empty, empty)[0] == 4.0
    assert negative_base(np.array((4.0, 0.0)), empty, empty, empty)[0] == 16.0

    # Native initialization binds finite boundary values with repr(value).
    # A compound binding exercises the same inline fallback without alias reuse.
    binding: str
    binding_value: float
    expression: sym.Expr
    target: float
    for binding, binding_value in (("-2.0", -2.0), ("values[0] - values[1]", xv - yv)):
        boundary_names: Dict[int, str] = dict(((x.uid, binding), (y.uid, "values[1]")))
        for expression, target in ((x ** 2, binding_value * binding_value), (-x, -binding_value), (x * 3, binding_value * 3)):
            boundary_vector: SymbolicVector = SymbolicVector(list((expression,)), boundary_names, aliases,
                "values", "diff", "events", "params", use_jit=use_jit)
            assert boundary_vector(values, empty, empty, empty)[0] == pytest.approx(target, rel=2e-12, abs=2e-12)


def test_binary_structural_identity_keeps_atan2_order() -> None:
    """Retain ordered angle operands without losing minimum/maximum symmetry.

    :return: None; swapped angles must have distinct structural/DAG identity.
    """
    x: sym.Var = sym.Var("x")
    y: sym.Var = sym.Var("y")
    memo: Dict[str, DAGNode] = dict()
    assert structural_hash(sym.atan2(x, y)) != structural_hash(sym.atan2(y, x))
    assert to_dag(sym.atan2(x, y), memo) is not to_dag(sym.atan2(y, x), memo)
    assert structural_hash(sym.Func2("min", x, y)) == structural_hash(sym.Func2("min", y, x))
    assert structural_hash(sym.Func2("max", x, y)) == structural_hash(sym.Func2("max", y, x))


@pytest.mark.parametrize("use_jit", [False, True])
def test_ordered_emission_preserves_uid_randomness_and_output_aliasing(use_jit: bool) -> None:
    """Exercise compiler boundaries that algebraic or global CSE can violate.

    :param use_jit: Execute the alias-collision controls through Python or Numba.
    :return: None; distinct UIDs, stochastic calls and output ordering survive.
    """
    x: sym.Var = sym.Var("same")
    y: sym.Var = sym.Var("same")
    analyzer: SubexpressionAnalyzer = SubexpressionAnalyzer()
    names: Dict[int, str] = dict(((x.uid, "values[0]"), (y.uid, "values[1]")))
    aliases: Dict[int, str] = dict(((x.uid, "a0"), (y.uid, "a1")))
    empty: np.ndarray = np.zeros(0)
    vector: SymbolicVector = SymbolicVector(list(((x + 1) * (y + 1),)), names, aliases,
                                           "values", "diff", "events", "params", use_jit=False)
    assert vector(np.array((2.0, 4.0)), empty, empty, empty)[0] == 15.0
    # The alias is used only by later roots, but is assigned before the entire
    # batch. A first-root temporary must reserve it even when that root reads x.
    late_aliases: Dict[int, str] = dict(((x.uid, "a0"), (y.uid, "_vg_shared_0")))
    late_alias_vector: SymbolicVector = SymbolicVector(list((x + 1, y + 1, 2 * y)), names,
        late_aliases, "values", "diff", "events", "params", use_jit=use_jit)
    np.testing.assert_array_equal(late_alias_vector(np.array((2.0, 4.0)), empty, empty, empty),
                                   np.array((3.0, 5.0, 8.0)))
    late_alias_jacobian: SymbolicJacobian = SymbolicJacobian(list((x*x, y*y, y*y*y)),
        list((x, y)), names, late_aliases, "values", "diff", "events", "params", use_jit=use_jit)
    np.testing.assert_array_equal(late_alias_jacobian(np.array((2.0, 4.0)), empty, empty,
        empty, 0.01).toarray(), np.array(((4.0, 0.0), (0.0, 8.0), (0.0, 48.0))))
    stochastic: sym.Expr = sym.Func(sym.Const(0), "rand")
    assignments: list[str]
    replacements: Dict[int, str]
    assignments, replacements = analyzer.emit_ordered_assignments(stochastic + stochastic, names)
    assert assignments == list() and replacements == dict()
    stochastic_source: str = sym.expression2numba(stochastic + stochastic, names, 0, replacements)
    assert stochastic_source.count("np.random.rand()") == 2
    assignments, replacements = analyzer.emit_ordered_assignments(x * x, dict(((x.uid, "np.random.rand()"),)))
    assert assignments == list() and replacements == dict()
    # Two different UIDs can intentionally read the same slot. A first output
    # write must be visible to the next equation when the original inline path
    # would read that slot again. Sharing must stop at the output boundary.
    shared_slot_names: Dict[int, str] = dict(((x.uid, "values[0]"), (y.uid, "values[0]")))
    aliased: SymbolicVector = SymbolicVector(list((x + 1, 2 * y)), shared_slot_names, aliases,
                                            "values", "diff", "events", "params", use_jit=False)
    values: np.ndarray = np.array((2.0, 0.0))
    assert aliased.func is not None
    aliased.func(values, empty, empty, empty, values)
    np.testing.assert_array_equal(values, np.array((3.0, 6.0)))
    # Exact singular-domain behavior remains owned by the original emitter and
    # simplification path; a zero-slope floor derivative stays canonical zero.
    singular: sym.Expr = sym.Func(sym.BinOp(sym.Const(0), "**", sym.Const(0)), "floor")
    derivative: sym.Expr = singular.diff(x)
    assert isinstance(derivative, sym.Const) and derivative.value == 0


def _modal_template_block() -> tuple[Block, VarFactory]:
    """Build a block carrying modal template metadata.

    :return: Block and the variable factory that owns its variables.
    """
    var_factory: VarFactory = VarFactory()
    value: sym.Var = var_factory.add_var(name="modal_x")
    block: Block = Block(algebraic_vars=list((value,)), algebraic_eqs=list((value,)))
    block.modal_template_kind = "configurable_integrator"
    block.modal_template_config = dict((("scaling", "GAIN"), ("scale_bounds_by_gain", True)))
    return block, var_factory


def _make_version_six_contract(contract: object) -> None:
    """Turn a current contract record into the version-6 shape that had no modal fields.

    :param contract: Dynamic-model contract record, edited in place.
    :return: None.
    """
    assert isinstance(contract, dict)
    contract["version"] = 6
    contract.pop("modal_template_kind")
    contract.pop("modal_template_config")
    contract.pop("emt_finite_reciprocal_source_mode_var_uid", None)


def _parse_through_symbolic_io(block_records: dict[str, object], saver: BlockSaver) -> Block:
    """Parse saved block records with the symbolic IO parser.

    :param block_records: Block records to parse (possibly edited).
    :param saver: Saver that produced the variables and constants.
    :return: Parsed block.
    """
    parser: BlockParser = BlockParser(var_factory=VarFactory())
    return parse_saved_blocks(parser=parser, saver=saver, data=block_records)[0]


def test_modal_template_is_stored_only_in_the_contract() -> None:
    """Modal metadata lives in the dynamic-model contract and new records carry no top-level copy.

    :return: None.
    """
    block: Block
    var_factory: VarFactory
    block, var_factory = _modal_template_block()
    source_data: dict[str, Any]
    saver: BlockSaver
    source_data, saver = _save_block_parser_fixture(block)
    data: dict[str, object] = copy.deepcopy(source_data)
    assert "modal_template_kind" not in data
    assert "modal_template_config" not in data
    contract_data: object = data["dynamic_model_contract"]
    assert isinstance(contract_data, dict)
    assert contract_data["modal_template_kind"] == "configurable_integrator"
    assert contract_data["modal_template_config"] == block.modal_template_config
    saver: BlockSaver = BlockSaver(var_factory)
    saver.save_block(block)
    record: object = saver.get_blocks()[block.uid]
    assert isinstance(record, dict)
    assert "modal_template_kind" not in record
    assert "modal_template_config" not in record
    block.modal_template_kind = None
    block.modal_template_config = None
    assert block.dynamic_model_contract.modal_template_kind is None
    assert block.dynamic_model_contract.modal_template_config is None
    cleared_data: dict[str, Any]
    cleared_data, saver = _save_block_parser_fixture(block)
    assert _parse_test_block(saver=saver, data=cleared_data).modal_template_kind is None


def test_modal_template_legacy_keys_fill_null_contract_fields() -> None:
    """Legacy top-level keys fill each null contract field, and a non-null contract value wins.

    :return: None.
    """
    block: Block
    var_factory: VarFactory
    block, var_factory = _modal_template_block()
    expected_config: Dict[str, object] = dict((("scaling", "GAIN"), ("scale_bounds_by_gain", True)))

    source_data: dict[str, Any]
    saver: BlockSaver
    source_data, saver = _save_block_parser_fixture(block)
    version_six: dict[str, object] = copy.deepcopy(source_data)
    _make_version_six_contract(version_six["dynamic_model_contract"])
    version_six["modal_template_kind"] = "configurable_integrator"
    version_six["modal_template_config"] = dict(expected_config)
    restored: Block = _parse_test_block(saver=saver, data=version_six)
    assert restored.modal_template_kind == "configurable_integrator"
    assert restored.modal_template_config == expected_config
    assert restored.dynamic_model_contract.modal_template_config == expected_config

    resaved: dict[str, object] = copy.deepcopy(source_data)
    resaved_contract: object = resaved["dynamic_model_contract"]
    assert isinstance(resaved_contract, dict)
    resaved_contract["modal_template_kind"] = None
    resaved_contract["modal_template_config"] = None
    resaved["modal_template_kind"] = "configurable_integrator"
    resaved["modal_template_config"] = dict(expected_config)
    restored = _parse_test_block(saver=saver, data=resaved)
    assert restored.modal_template_kind == "configurable_integrator"
    assert restored.modal_template_config == expected_config

    without_contract: dict[str, object] = copy.deepcopy(source_data)
    without_contract.pop("dynamic_model_contract")
    without_contract["modal_template_kind"] = "configurable_integrator"
    without_contract["modal_template_config"] = dict(expected_config)
    restored = _parse_test_block(saver=saver, data=without_contract)
    assert restored.modal_template_kind == "configurable_integrator"
    assert restored.modal_template_config == expected_config

    conflicting: dict[str, object] = copy.deepcopy(source_data)
    conflicting["modal_template_kind"] = "startup_freeze_integrator"
    conflicting["modal_template_config"] = dict((("scaling", "NONE"),))
    restored = _parse_test_block(saver=saver, data=conflicting)
    assert restored.modal_template_kind == "configurable_integrator"
    assert restored.modal_template_config == expected_config

    per_field: dict[str, object] = copy.deepcopy(source_data)
    per_field_contract: object = per_field["dynamic_model_contract"]
    assert isinstance(per_field_contract, dict)
    per_field_contract["modal_template_config"] = None
    per_field["modal_template_kind"] = "startup_freeze_integrator"
    per_field["modal_template_config"] = dict(expected_config)
    restored = _parse_test_block(saver=saver, data=per_field)
    assert restored.modal_template_kind == "configurable_integrator"
    assert restored.modal_template_config == expected_config

    saver: BlockSaver = BlockSaver(var_factory)
    saver.save_block(block)
    saved_records: dict[str, object] = copy.deepcopy(saver.get_blocks())
    saved_record: object = saved_records[block.uid]
    assert isinstance(saved_record, dict)
    _make_version_six_contract(saved_record["dynamic_model_contract"])
    saved_record["modal_template_kind"] = "configurable_integrator"
    saved_record["modal_template_config"] = dict(expected_config)
    parsed: Block = _parse_through_symbolic_io(saved_records, saver)
    assert parsed.modal_template_kind == "configurable_integrator"
    assert parsed.modal_template_config == expected_config

    resaved_records: dict[str, object] = copy.deepcopy(saver.get_blocks())
    resaved_record: object = resaved_records[block.uid]
    assert isinstance(resaved_record, dict)
    resaved_record_contract: object = resaved_record["dynamic_model_contract"]
    assert isinstance(resaved_record_contract, dict)
    resaved_record_contract["modal_template_kind"] = None
    resaved_record_contract["modal_template_config"] = None
    resaved_record["modal_template_kind"] = "configurable_integrator"
    resaved_record["modal_template_config"] = dict(expected_config)
    parsed = _parse_through_symbolic_io(resaved_records, saver)
    assert parsed.modal_template_kind == "configurable_integrator"
    assert parsed.modal_template_config == expected_config


def test_modal_template_legacy_keys_are_validated_like_the_contract() -> None:
    """Malformed legacy top-level keys raise TypeError, also when the contract value wins.

    :return: None.
    """
    block: Block
    var_factory: VarFactory
    block, var_factory = _modal_template_block()
    source_data: dict[str, Any]
    saver: BlockSaver
    source_data, saver = _save_block_parser_fixture(block)
    nested: dict[str, object] = copy.deepcopy(source_data)
    nested["modal_template_config"] = dict((("scaling", dict((("inner", 1),))),))
    with pytest.raises(TypeError):
        _parse_test_block(saver=saver, data=nested)
    version_six: dict[str, object] = copy.deepcopy(source_data)
    _make_version_six_contract(version_six["dynamic_model_contract"])
    version_six["modal_template_config"] = dict((("scaling", list((1, 2))),))
    with pytest.raises(TypeError):
        _parse_test_block(saver=saver, data=version_six)
    wrong_kind: dict[str, object] = copy.deepcopy(source_data)
    wrong_kind["modal_template_kind"] = 7
    with pytest.raises(TypeError):
        _parse_test_block(saver=saver, data=wrong_kind)
    saver: BlockSaver = BlockSaver(var_factory)
    saver.save_block(block)
    saved_records: dict[str, object] = copy.deepcopy(saver.get_blocks())
    saved_record: object = saved_records[block.uid]
    assert isinstance(saved_record, dict)
    saved_record["modal_template_config"] = dict((("scaling", dict((("inner", 1),))),))
    with pytest.raises(TypeError):
        _parse_through_symbolic_io(saved_records, saver)


def test_modal_template_survives_block_copies() -> None:
    """Deep copy, duplicate_block and the editor's copy_block_state keep the metadata in the contract.

    :return: None.
    """
    block: Block
    var_factory: VarFactory
    block, var_factory = _modal_template_block()
    copied: Block = copy.deepcopy(block)
    assert copied.modal_template_kind == block.modal_template_kind
    assert copied.modal_template_config == block.modal_template_config
    assert copied.modal_template_config is not block.modal_template_config
    duplicated: Block = duplicate_block(block=block, var_factory=var_factory)
    assert duplicated.modal_template_kind == block.modal_template_kind
    assert duplicated.modal_template_config == block.modal_template_config
    target_value: sym.Var = var_factory.add_var(name="modal_target")
    target: Block = Block(algebraic_vars=list((target_value,)), algebraic_eqs=list((target_value,)))
    copy_block_state(block, target)
    assert target.modal_template_kind == block.modal_template_kind
    assert target.modal_template_config == block.modal_template_config


def test_dynamic_model_contract_contains_only_retained_runtime_fields() -> None:
    """Keep the persistent contract limited to the two supported declarations.

    :return: None.
    """
    fields: set[str] = set((
        "modal_template_kind", "modal_template_config",
    ))
    contract: DynamicModelContract = DynamicModelContract()
    payload: dict[str, object] = contract.to_data()
    assert set(DynamicModelContract.__slots__) == fields
    assert set(payload) == fields | set(("version",))
    assert payload["version"] == 15
    with pytest.raises(AttributeError):
        contract.dgs_elmsym_runtime_adapter = True
    restored: DynamicModelContract = dynamic_model_contract_from_data(payload)
    assert restored.to_data() == payload


def test_legacy_dynamic_model_contract_discards_import_metadata_on_resave() -> None:
    """Load old import declarations while preserving retained runtime settings.

    :return: None.
    """
    legacy: dict[str, object] = DynamicModelContract().to_data()
    legacy["version"] = 8
    legacy["emt_finite_reciprocal_source_mode_var_uid"] = None
    legacy["dgs_elmsym_runtime_adapter"] = True
    legacy["dgs_elmsym_speed_var_uid"] = 123
    legacy["dgs_open_resistance_ohm"] = 99999.0
    legacy["explicit_init_excluded_var_names"] = list(("boundary",))
    legacy["emt_internal_grounding_link"] = True
    legacy["modal_template_kind"] = "example"
    legacy["modal_template_config"] = dict(gain=2.0)
    restored: DynamicModelContract = dynamic_model_contract_from_data(legacy)
    current: dict[str, object] = restored.to_data()
    assert current["version"] == 15
    assert "explicit_init_excluded_var_names" not in current
    assert "emt_internal_grounding_link" not in current
    assert restored.modal_template_config == dict(gain=2.0)
    assert "dgs_elmsym_runtime_adapter" not in current
    assert "dgs_elmsym_speed_var_uid" not in current
    assert "dgs_open_resistance_ohm" not in current
    legacy["unexpected_field"] = True
    with pytest.raises(KeyError, match="extra"):
        dynamic_model_contract_from_data(legacy)


@pytest.mark.parametrize("grounding", (False, True))
def test_version_thirteen_discards_grounding_flag(grounding: bool) -> None:
    """Discard historical grounding flags and reject them in the current schema.

    :param grounding: Historical flag value to discard.
    :return: None.
    """
    legacy: dict[str, object] = DynamicModelContract().to_data()
    legacy["version"] = 13
    legacy["emt_finite_reciprocal_source_mode_var_uid"] = None
    legacy["emt_internal_grounding_link"] = grounding
    restored: DynamicModelContract = dynamic_model_contract_from_data(legacy)
    assert restored.to_data() == DynamicModelContract().to_data()
    # Current records must not silently accept retired declarations.
    legacy["version"] = 15
    legacy.pop("emt_finite_reciprocal_source_mode_var_uid")
    with pytest.raises(KeyError, match="emt_internal_grounding_link"):
        dynamic_model_contract_from_data(legacy)
