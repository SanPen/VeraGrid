# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Reduce private polar round trips to their equivalent Cartesian rotation."""
from __future__ import annotations

from VeraGridEngine.Utils.procedural_logic import ProceduralLogicBase
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Comparison, Const, Expr, Func, Func2, Var, cos, diff, sin


def _same_expression(left: Expr, right: Expr) -> bool:
    """Compare symbolic structure using variable identities, never port names.

    :param left: First expression.
    :param right: Second expression.
    :return: Whether both trees represent the same structural expression.
    """
    if isinstance(left, Var) and isinstance(right, Var):
        return left.uid == right.uid
    elif isinstance(left, Const) and isinstance(right, Const):
        return left.value == right.value
    elif isinstance(left, BinOp) and isinstance(right, BinOp):
        return (left.op == right.op and _same_expression(left.left, right.left)
                and _same_expression(left.right, right.right))
    else:
        return False


def _is_square(expression: Expr, variable: Var) -> bool:
    """Recognize either exported spelling of a Cartesian component squared.

    :param expression: Candidate magnitude term.
    :param variable: Cartesian input.
    :return: Whether the term is the square of this input.
    """
    if isinstance(expression, BinOp) and expression.op == '*':
        return _same_expression(expression.left, variable) and _same_expression(expression.right, variable)
    elif isinstance(expression, BinOp) and expression.op == '**':
        return (_same_expression(expression.left, variable)
                and isinstance(expression.right, Const) and expression.right.value == 2)
    else:
        return False


def _polar_magnitude(expression: Expr, real: Var, imaginary: Var) -> bool:
    """Verify the exact Euclidean magnitude used by a polar conversion.

    :param expression: Magnitude definition.
    :param real: Real Cartesian input.
    :param imaginary: Imaginary Cartesian input.
    :return: Whether the expression is sqrt(real squared plus imaginary squared).
    """
    if isinstance(expression, Func) and expression.op == 'sqrt':
        argument: Expr = expression.arg
        if isinstance(argument, BinOp) and argument.op == '+':
            return ((_is_square(argument.left, real) and _is_square(argument.right, imaginary))
                    or (_is_square(argument.left, imaginary) and _is_square(argument.right, real)))
        else:
            return False
    else:
        return False


def _rectangular_angle(expression: Expr, magnitude: Var, operation: str) -> Var | None:
    """Read the common angle from magnitude times a trigonometric function.

    :param expression: Cartesian output definition.
    :param magnitude: Polar magnitude variable.
    :param operation: Required symbolic sine or cosine operation.
    :return: Angle variable, or None for another expression.
    """
    if isinstance(expression, BinOp) and expression.op == '*':
        factor: Expr
        trig: Expr
        for factor, trig in ((expression.left, expression.right), (expression.right, expression.left)):
            if (_same_expression(factor, magnitude) and isinstance(trig, Func)
                    and trig.op == operation and isinstance(trig.arg, Var)):
                return trig.arg
            else:
                pass
        return None
    else:
        return None


def _record_uses_internal(value: object, uids: set[int], names: set[str]) -> bool:
    """Conservatively inspect persisted procedural references before reduction.

    :param value: Declarative procedural record or nested value.
    :param uids: Private variable identities proposed for removal.
    :param names: Private labels, including procedural name-only references.
    :return: Whether a record could reference a private variable.
    """
    if isinstance(value, dict):
        return any(_record_uses_internal(item, uids, names) for item in value.values())
    elif isinstance(value, (list, tuple)):
        return any(_record_uses_internal(item, uids, names) for item in value)
    elif isinstance(value, int):
        return value in uids
    elif isinstance(value, str):
        return value in names or value in set(str(uid) for uid in uids)
    else:
        return False


def _uses_private(expression: Expr | Comparison, uids: set[int]) -> bool:
    """Inspect ordinary expressions and boolean guards by canonical UID.

    :param expression: Saved symbolic dependency.
    :param uids: Variables proposed for removal.
    :return: Whether the dependency reaches a private intermediate.
    """
    numeric: Expr
    if isinstance(expression, Comparison):
        numeric = expression.to_expression()
    else:
        numeric = expression
    return any(variable.uid in uids for variable in numeric.get_vars())


def _private_rotation(root: Block, candidate: Block) -> tuple[Var, Var, Expr] | None:
    """Recognize a complete stateless Cartesian-polar-angle-Cartesian macro.

    :param root: Complete assembled model used to check external consumers.
    :param candidate: Macro whose public interface must remain unchanged.
    :return: Real input, imaginary input and angle offset when safe to reduce.
    """
    if len(candidate.in_vars) != 3 or len(candidate.out_vars) != 2 or len(candidate.children) == 0:
        return None
    else:
        pass
    owners: list[Block] = candidate.get_all_blocks()
    definitions: dict[int, tuple[Var, Expr]] = dict()
    owner: Block
    equation: Expr
    for owner in owners:
        # State, initialization and procedural semantics must never disappear.
        if (owner.state_vars or owner.diff_vars or owner.state_eqs or owner.differential_eqs
                or owner.parameters or owner.event_dict or owner.mode_dict or owner.procedural_logic
                or owner.inequalities or owner.boolean_guards or owner.discrete_eqs
                or owner.external_mapping or owner.api_obj_mapping
                or (owner is not candidate and (owner.init_eqs or owner.diff_init_eqs
                                               or owner.init_values or owner.post_init_seed_eqs))):
            return None
        else:
            pass
        for equation in owner.algebraic_eqs:
            if (isinstance(equation, BinOp) and equation.op == '-' and isinstance(equation.left, Var)
                    and equation.left.uid not in definitions):
                definitions[equation.left.uid] = (equation.left, equation.right)
            else:
                return None
    input_uids: set[int] = set(variable.uid for variable in candidate.in_vars)
    if len(definitions) != 5 or not input_uids.isdisjoint(definitions):
        return None
    else:
        pass
    real: Var = candidate.in_vars[0]
    imaginary: Var = candidate.in_vars[1]
    phase: Var | None = None
    magnitude: Var | None = None
    variable: Var
    expression: Expr
    for variable, expression in definitions.values():
        if (isinstance(expression, Func2) and expression.name == 'atan2'
                and _same_expression(expression.arg1, imaginary) and _same_expression(expression.arg2, real)):
            phase = variable
        elif _polar_magnitude(expression, real, imaginary):
            magnitude = variable
        else:
            pass
    if phase is None or magnitude is None:
        return None
    else:
        pass
    output_real: tuple[Var, Expr] | None = definitions.get(candidate.out_vars[0].uid, None)
    output_imaginary: tuple[Var, Expr] | None = definitions.get(candidate.out_vars[1].uid, None)
    if output_real is None or output_imaginary is None:
        return None
    else:
        pass
    angle_real: Var | None = _rectangular_angle(output_real[1], magnitude, 'cos')
    angle_imaginary: Var | None = _rectangular_angle(output_imaginary[1], magnitude, 'sin')
    if angle_real is None or angle_imaginary is None or angle_real.uid != angle_imaginary.uid:
        return None
    else:
        pass
    angle_definition: tuple[Var, Expr] | None = definitions.get(angle_real.uid, None)
    if angle_definition is None:
        return None
    else:
        pass
    angle: Expr = angle_definition[1]
    coefficient: Expr = diff(angle, phase).simplify()
    offset: Expr = angle.subs(dict(((phase, Const(0.0)),))).simplify()
    if not isinstance(coefficient, Const) or coefficient.value != 1:
        return None
    elif any(variable.uid != candidate.in_vars[2].uid for variable in offset.get_vars()):
        return None
    else:
        pass
    public_uids: set[int] = set(variable.uid for variable in candidate.out_vars)
    private_vars: list[Var] = list(variable for variable, expression in definitions.values()
                                   if variable.uid not in public_uids)
    private_uids: set[int] = set(variable.uid for variable in private_vars)
    private_names: set[str] = set(variable.name for variable in private_vars)
    for owner in root.get_all_blocks():
        if owner in owners and owner is not candidate:
            pass
        else:
            # Public aliases, saved initial conditions and procedural references
            # also count as consumers, even when they own no algebraic equation.
            for variable in private_vars:
                if owner is not candidate and (owner.find_var_in_equations(variable)
                        or any(port.uid == variable.uid for port in owner.in_vars)
                        or any(port.uid == variable.uid for port in owner.out_vars)
                        or any(port.uid == variable.uid for port in owner.state_vars)
                        or any(port.uid == variable.uid for port in owner.algebraic_vars)
                        or any(port.uid == variable.uid for port in owner.api_obj_mapping.values())):
                    return None
                else:
                    pass
            mapping: dict
            for mapping in (owner.init_eqs, owner.diff_init_eqs, owner.init_values,
                            owner.post_init_seed_eqs, owner.parameters, owner.boolean_guards):
                for variable, expression in mapping.items():
                    if variable.uid in private_uids or _uses_private(expression, private_uids):
                        return None
                    else:
                        pass
            logic: ProceduralLogicBase
            for logic in owner.procedural_logic:
                if _record_uses_internal(logic.to_data(), private_uids, private_names):
                    return None
                else:
                    pass
    return real, imaginary, offset


def simplify_dgs_cartesian_rotations(root: Block) -> int:
    """Remove safe private polar round trips after complete DGS assembly.

    :param root: Model with final connections and symbolic initial conditions.
    :return: Number of equivalent Cartesian realizations constructed.
    """
    count: int = 0
    candidate: Block
    for candidate in reversed(root.get_all_blocks()):
        rotation: tuple[Var, Var, Expr] | None = _private_rotation(root, candidate)
        if rotation is None:
            pass
        else:
            real: Var
            imaginary: Var
            angle: Expr
            real, imaginary, angle = rotation
            # Keep the macro identity, public variables and their initialization.
            # Only the redundant private realization is replaced.
            candidate.algebraic_vars = list(candidate.out_vars)
            candidate.algebraic_eqs = list((
                candidate.out_vars[0] - (real * cos(angle) - imaginary * sin(angle)),
                candidate.out_vars[1] - (real * sin(angle) + imaginary * cos(angle))))
            candidate.children = list()
            count += 1
    return count
