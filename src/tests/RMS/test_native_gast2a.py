# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Verify the GAST2A native equations and 13-state source structure."""
from __future__ import annotations

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms import build_international_standard_template
from VeraGridEngine.Templates.Rms.governors.gast2a import (
    Gast2aParameters,
    build_gast2a_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import InternationalStandardModel


def initialized_values(block: Block) -> dict[int, float]:
    """Resolve the block's declared parameter and initialization expressions.

    :param block: GAST2A graph with closed default operating-point values.
    :return: Values keyed by symbolic variable UID.
    """
    expressions: dict[Var, Expr | Const] = dict(block.parameters)
    expressions.update(block.event_dict)
    expressions.update(block.init_eqs)
    values: dict[int, float] = dict()
    for _ in range(len(expressions) + 1):
        for variable, expression in expressions.items():
            if variable.uid not in values and all(
                    item.uid in values for item in expression.get_vars()):
                values[variable.uid] = expression.eval_uid(values)
            else:
                pass
    assert all(variable.uid in values for variable in expressions)
    return values


def test_gast2a_catalogue_template_has_thirteen_equilibrium_states() -> None:
    """The complete source state allocation initializes at the test point.

    :return: None.
    """
    block: Block = build_international_standard_template(
        InternationalStandardModel.GAST2A, VarFactory(), 'gast2a_catalogue',
    ).block
    values: dict[int, float] = initialized_values(block)
    assert len(block.in_vars) == 2
    assert len(block.out_vars) == 1
    assert len(block.state_vars) == 13
    assert len(block.state_eqs) == 13
    assert [equation.eval_uid(values) for equation in block.state_eqs] == pytest.approx(
        [0.0] * 13, abs=1e-10,
    )
    assert [equation.eval_uid(values) for equation in block.algebraic_eqs] == pytest.approx(
        [0.0] * len(block.algebraic_eqs), abs=1e-10,
    )
    assert block.out_vars[0].name.startswith('MechanicalPowerPu_')


def test_gast2a_speed_controller_responds_to_reference_increase() -> None:
    """A larger speed reference opens the governor at the source sign.

    :return: None.
    """
    block: Block = build_gast2a_template(VarFactory(), 'gast2a_step').block
    values: dict[int, float] = initialized_values(block)
    reference: Var = block.in_vars[1]
    values[reference.uid] += 0.01
    for _ in range(len(block.algebraic_eqs) + 1):
        for equation in block.algebraic_eqs:
            if isinstance(equation.left, Var):
                values[equation.left.uid] = equation.right.eval_uid(values)
            else:
                pass
    assert block.state_eqs[0].eval_uid(values) > 0.0


def test_gast2a_isochronous_mode_and_zero_delays_reduce_exactly() -> None:
    """Z=0 uses integral speed control and zero delays remove their states.

    :return: None.
    """
    parameters: Gast2aParameters = Gast2aParameters(
        z=0, t=0.0, ecr=0.0, etd=0.0,
    )
    block: Block = build_gast2a_template(
        VarFactory(), 'gast2a_isochronous', parameters,
    ).block
    values: dict[int, float] = initialized_values(block)
    assert len(block.state_vars) == 7
    assert [equation.eval_uid(values) for equation in block.state_eqs] == pytest.approx(
        [0.0] * 7, abs=1e-10,
    )
    assert block.out_vars[0].eval_uid(values) == pytest.approx(.8)


@pytest.mark.parametrize(
    'parameters',
    (
        Gast2aParameters(z=2),
        Gast2aParameters(y=0.0),
        Gast2aParameters(trate=0.0),
        Gast2aParameters(minimum=1.0, maximum=1.0),
    ),
)
def test_gast2a_rejects_unreviewed_source_settings(parameters: Gast2aParameters) -> None:
    """Reject source selectors and constants outside the supported region.

    :param parameters: Invalid source parameter combination.
    :return: None.
    """
    with pytest.raises(ValueError):
        build_gast2a_template(VarFactory(), 'gast2a_invalid', parameters)
