from __future__ import annotations
import copy
import json
import pytest
import math
import numpy as np
from typing import Any, Callable, Dict
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicJacobian
from VeraGridEngine.Utils.Symbolic.jit_compiler import SubexpressionAnalyzer
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic_io import (duplicate_block, expr_to_dict, parse_expr,
                                                       BlockSaver, BlockParser)
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagram
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import ParamPowerFlowReferenceType, VarPowerFlowReferenceType
from VeraGridEngine.Utils.procedural_logic import AnalogFlipFlopLogic, aflipflop

# -----------------------------------------------------------------------------
# Atomic & basic operations
# -----------------------------------------------------------------------------

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
    x: sym.Var = vf.add_var("x")
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
    x: sym.Var = vf.add_var("x")
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


def test_duplicate_block_preserves_parent_child_variable_links_with_new_uids() -> None:
    """
    Check that block duplication keeps parent and child references coherent.

    :return: Nothing.
    """
    x: sym.Var = sym.Var("x")
    dx: sym.Var = sym.Var("dx", base_var=x)
    child: Block = Block(
        state_vars=[x],
        diff_vars=[dx],
        state_eqs=[dx + x],
    )
    parent: Block = Block(
        children=[child],
        in_vars=[x],
        out_vars=[dx],
    )

    target_vf: VarFactory = VarFactory()
    copied: Block = duplicate_block(parent, target_vf)
    copied_child: Block = copied.children[0]
    copied_x: sym.Var = copied_child.state_vars[0]
    copied_dx: sym.Var = copied_child.diff_vars[0]

    assert copied.in_vars[0] is copied_x
    assert copied.out_vars[0] is copied_dx
    assert copied_x.uid != x.uid
    assert copied_dx.uid != dx.uid
    assert copied_x.diff_var is copied_dx
    assert copied_dx.base_var is copied_x
    assert copied_child.state_eqs[0].left is copied_dx
    assert copied_child.state_eqs[0].right is copied_x
    assert target_vf.get_var(copied_x.non_mutable_uid) is copied_x
    assert target_vf.get_diff_var(copied_dx.non_mutable_uid) is copied_dx


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


def test_block_saver_parser_roundtrip_preserves_dynamic_runtime_fields() -> None:
    """
    Check that block saver/parser preserve dynamic runtime-only fields.

    :return: Nothing.
    """
    vf: VarFactory = VarFactory()
    x: sym.Var = vf.add_var("x")
    mode: sym.Var = vf.add_var("mode")
    out: sym.Var = vf.add_var("out")

    block: Block = Block(
        algebraic_vars=[x, mode, out],
        algebraic_eqs=[x + sym.Const(1.0), mode + sym.Const(0.0), out + sym.Const(0.0)],
        discrete_eqs={mode: x + sym.Const(2.0)},
        mode_dict={mode: sym.Const(1.0)},
        procedural_logic=[aflipflop(x=x,
                                    boolset=x > sym.Const(1.0),
                                    boolreset=x < sym.Const(-1.0),
                                    output=out)],
        name="legacy_runtime_block",
    )

    saver: BlockSaver = BlockSaver(vf)
    saver.save_block(block, main=True)

    # The archive writer JSON-encodes the complete block table.  This check
    # prevents runtime procedural-logic objects from silently causing the
    # ``blocks.symbolic`` archive member to be omitted.
    json.dumps(saver.get_blocks())

    parser: BlockParser = BlockParser(VarFactory())
    parser.parse_consts(saver.get_const_to_save())
    parser.parse_vars(saver.get_vars_to_save())
    parser.parse_diff_vars(saver.get_diff_vars_to_save())
    restored: Block = parser.parse_block(saver.get_blocks(), block.uid)

    assert len(restored.discrete_eqs) == 1
    assert len(restored.mode_dict) == 1
    assert len(restored.procedural_logic) == 1
    assert isinstance(restored.procedural_logic[0], AnalogFlipFlopLogic)


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
    saver.save_block(source_block, main=True)

    # Parse the explicit legacy nulls first. They represent optional empty
    # mapping slots and therefore must not interrupt file opening with warnings.
    null_logger: Logger = Logger()
    null_parser: BlockParser = BlockParser(VarFactory(), logger=null_logger)
    null_parser.parse_consts(saver.get_const_to_save())
    null_parser.parse_vars(saver.get_vars_to_save())
    null_parser.parse_diff_vars(saver.get_diff_vars_to_save())
    restored_block: Block = null_parser.parse_block(saver.get_blocks(), source_block.uid)

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
    broken_parser.parse_consts(saver.get_const_to_save())
    broken_parser.parse_vars(saver.get_vars_to_save())
    broken_parser.parse_diff_vars(saver.get_diff_vars_to_save())
    broken_parser.parse_block(broken_blocks, source_block.uid)

    assert broken_logger.warning_count() == 2
    assert {entry.device_property for entry in broken_logger.entries} == {
        "api_obj_mapping",
        "external_mapping",
    }


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
