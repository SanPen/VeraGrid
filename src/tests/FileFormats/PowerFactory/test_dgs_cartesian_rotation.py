# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Reduce only exact, private polar round trips with no independent semantics."""
from __future__ import annotations

import math

import numpy as np
import pytest

from VeraGridEngine.IO.dgs.dgs_cartesian_rotation import simplify_dgs_cartesian_rotations
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Func2, Var, cos, sin, sqrt
from VeraGridEngine.Utils.procedural_logic import SampledValueLogic


def make_rotation(sign: float = 1.0) -> tuple[Block, Block, Var]:
    """Build an arbitrarily named rotation without any DGS-name assumptions.

    :param sign: Sign of the applied external angle.
    :return: Complete root, rotation macro and its private polar angle.
    """
    real: Var = Var('a')
    imaginary: Var = Var('b')
    theta: Var = Var('c')
    magnitude: Var = Var('length')
    phase: Var = Var('bearing')
    angle: Var = Var('shifted')
    x: Var = Var('output_x')
    y: Var = Var('output_y')
    polar: Block = Block(name='arbitrary 1', in_vars=list((real, imaginary)),
        out_vars=list((magnitude, phase)), algebraic_vars=list((magnitude, phase)),
        algebraic_eqs=list((magnitude - sqrt(real*real + imaginary*imaginary),
                           phase - Func2('atan2', imaginary, real))))
    addition: Block = Block(name='arbitrary 2', in_vars=list((phase, theta)), out_vars=list((angle,)),
        algebraic_vars=list((angle,)), algebraic_eqs=list((angle - (Const(0) + phase + Const(sign)*theta),)))
    rectangular: Block = Block(name='arbitrary 3', in_vars=list((magnitude, angle)), out_vars=list((x,y)),
        algebraic_vars=list((x,y)), algebraic_eqs=list((x-magnitude*cos(angle), y-magnitude*sin(angle))))
    rotation: Block = Block(name='not a known macro name', in_vars=list((real, imaginary, theta)),
                            out_vars=list((x,y)), children=list((polar, addition, rectangular)))
    return Block(children=list((rotation,))), rotation, phase


@pytest.mark.parametrize('sign', (-1.0, 1.0))
@pytest.mark.parametrize('real,imaginary', ((-1.0, 1e-17), (-1.0, -1e-17), (0.0, 0.0), (0.3, -0.7)))
def test_cartesian_rotation_preserves_outputs_without_branch_singularities(sign: float, real: float, imaginary: float) -> None:
    """Keep exact rotation behavior at the polar branch cut and at zero input.

    :param sign: Angle addition or subtraction.
    :param real: Real input.
    :param imaginary: Imaginary input.
    :return: None.
    """
    root: Block
    rotation: Block
    phase: Var
    root, rotation, phase = make_rotation(sign)
    outputs: tuple[int, int] = (rotation.out_vars[0].uid, rotation.out_vars[1].uid)
    # A public output initializer survives the realization change.
    rotation.init_eqs[rotation.out_vars[0]] = Const(0.8)
    assert simplify_dgs_cartesian_rotations(root) == 1
    assert not rotation.children
    assert tuple(variable.uid for variable in rotation.out_vars) == outputs
    assert rotation.init_eqs[rotation.out_vars[0]].value == 0.8
    theta: float = 0.4
    values: dict[int, float] = dict(zip((v.uid for v in rotation.in_vars), (real, imaginary, theta)))
    values[outputs[0]] = real*math.cos(sign*theta) - imaginary*math.sin(sign*theta)
    values[outputs[1]] = real*math.sin(sign*theta) + imaginary*math.cos(sign*theta)
    equation: Expr
    variable: Var
    for equation in rotation.algebraic_eqs:
        assert equation.eval_uid(values) == pytest.approx(0.0)
        for variable in rotation.in_vars:
            assert np.isfinite(equation.diff(variable).eval_uid(values))
    assert simplify_dgs_cartesian_rotations(root) == 0


@pytest.mark.parametrize('use', ('public', 'equation', 'initialization', 'procedural', 'state', 'guard'))
def test_private_polar_semantics_are_not_discarded(use: str) -> None:
    """Keep polar intermediates when their values have independently visible uses.

    :param use: Kind of dependency that prohibits removing the polar angle.
    :return: None.
    """
    root: Block
    rotation: Block
    phase: Var
    root, rotation, phase = make_rotation()
    if use == 'public':
        root.out_vars = list((phase,))
    elif use == 'equation':
        output: Var = Var('probe')
        root.algebraic_vars = list((output,))
        root.algebraic_eqs = list((output-phase,))
    elif use == 'initialization':
        rotation.init_eqs[phase] = Const(1.0)
    elif use == 'procedural':
        root.procedural_logic = list((SampledValueLogic(output_var_name='held', source_expr=phase),))
    elif use == 'state':
        rotation.children[0].state_vars = list((Var('state'),))
    else:
        root.boolean_guards[Var('guard')] = phase > Const(0.0)
    assert simplify_dgs_cartesian_rotations(root) == 0
    assert len(rotation.children) == 3


def test_non_euclidean_magnitude_is_not_simplified() -> None:
    """Avoid treating regularized or scaled polar expressions as exact rotations.

    :return: None.
    """
    root: Block
    rotation: Block
    phase: Var
    root, rotation, phase = make_rotation()
    polar: Block = rotation.children[0]
    real: Var = rotation.in_vars[0]
    imaginary: Var = rotation.in_vars[1]
    polar.algebraic_eqs[0] = polar.out_vars[0] - sqrt(real*real + imaginary*imaginary + Const(1e-6))
    assert simplify_dgs_cartesian_rotations(root) == 0
