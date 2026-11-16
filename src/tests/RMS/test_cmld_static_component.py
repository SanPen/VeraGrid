# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Verify the CMLD static-load component equations."""
from __future__ import annotations

import math

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.load_characteristics.cmld_static import (
    CmldStaticLoadParameters,
    build_cmld_static_load_component,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def initialized_values(block: Block) -> dict[int, float]:
    """Resolve the static component's declared scalar initial values.

    :param block: Built component block.
    :return: Numeric values keyed by symbolic variable UID.
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


def update_algebraic_values(block: Block, values: dict[int, float]) -> None:
    """Evaluate the ordered output equations after changing component inputs.

    :param block: Built component block.
    :param values: Numeric symbolic state updated in place.
    :return: None.
    """
    for equation in block.algebraic_eqs:
        if isinstance(equation.left, Var):
            values[equation.left.uid] = equation.right.eval_uid(values)
        else:
            pass


def source_parameters() -> CmldStaticLoadParameters:
    """Return a finite representative CMLD operating point.

    :return: Parameters with a 40-percent static fraction.
    """
    return CmldStaticLoadParameters(
        active_power_pu=.8,
        static_power_factor=.9,
        motor_a_fraction=.1,
        motor_b_fraction=.1,
        motor_c_fraction=.2,
        motor_d_fraction=.1,
        electronic_fraction=.1,
        p1_exponent=1.0,
        p1_coefficient=.5,
        p2_exponent=2.0,
        p2_coefficient=.3,
        p_frequency_coefficient=1.5,
        q1_exponent=1.0,
        q1_coefficient=.4,
        q2_exponent=2.0,
        q2_coefficient=.4,
        q_frequency_coefficient=2.0,
        initial_voltage_pu=.98,
    )


def test_cmld_static_branch_matches_nominal_power_and_frequency_slopes() -> None:
    """The source voltage terms sum to one at V0 and frequency zero.

    :return: None.
    """
    block: Block = build_cmld_static_load_component(
        VarFactory(), 'cmld_static', source_parameters(),
    ).block
    values: dict[int, float] = initialized_values(block)
    update_algebraic_values(block, values)
    active: float = values[block.out_vars[0].uid]
    reactive: float = values[block.out_vars[1].uid]
    expected_active: float = .8 * .4
    expected_reactive: float = expected_active * math.sqrt(1.0 - .9 ** 2) / .9

    assert len(block.state_vars) == 0
    assert active == pytest.approx(expected_active)
    assert reactive == pytest.approx(expected_reactive)

    voltage_ratio: float = 1.05
    values[block.in_vars[0].uid] = .98 * voltage_ratio
    update_algebraic_values(block, values)
    assert values[block.out_vars[0].uid] == pytest.approx(
        expected_active * (.5 * voltage_ratio + .3 * voltage_ratio ** 2 + .2),
    )
    assert values[block.out_vars[1].uid] == pytest.approx(
        expected_reactive * (.4 * voltage_ratio + .4 * voltage_ratio ** 2 + .2),
    )

    values[block.in_vars[0].uid] = .98
    values[block.in_vars[1].uid] = .01
    update_algebraic_values(block, values)
    assert values[block.out_vars[0].uid] == pytest.approx(
        expected_active * (1.0 + 1.5 * .01),
    )
    assert values[block.out_vars[1].uid] == pytest.approx(
        expected_reactive * (1.0 + 2.0 * .01),
    )


def test_cmld_static_fraction_vanishes_when_dynamic_fractions_exceed_one() -> None:
    """PSS/E normalizes dynamic fractions above one and leaves no static share.

    :return: None.
    """
    parameters: CmldStaticLoadParameters = source_parameters()
    parameters.motor_a_fraction = .5
    parameters.motor_b_fraction = .5
    parameters.motor_c_fraction = .5
    block: Block = build_cmld_static_load_component(
        VarFactory(), 'cmld_no_static', parameters,
    ).block
    values: dict[int, float] = initialized_values(block)
    update_algebraic_values(block, values)

    assert values[block.out_vars[0].uid] == pytest.approx(0.0)
    assert values[block.out_vars[1].uid] == pytest.approx(0.0)


@pytest.mark.parametrize(
    'parameters',
    (
        CmldStaticLoadParameters(.8,.9,-.1,.1,.2,.1,.1,1.,.5,2.,.3,0.,1.,.4,2.,.4,0.),
        CmldStaticLoadParameters(.8,0.,.1,.1,.2,.1,.1,1.,.5,2.,.3,0.,1.,.4,2.,.4,0.),
    ),
)
def test_cmld_static_component_rejects_invalid_fraction_or_power_factor(
        parameters: CmldStaticLoadParameters,
) -> None:
    """Reject invalid source fraction and singular static PF settings.

    :param parameters: Invalid parameter set.
    :return: None.
    """
    with pytest.raises(ValueError):
        build_cmld_static_load_component(VarFactory(), 'cmld_invalid', parameters)
