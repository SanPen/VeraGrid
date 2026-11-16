# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check ACMT winding temperature and thermal-trip fraction equations."""
from __future__ import annotations

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.load_characteristics.acmt_thermal import (
    AcmtThermalParameters,
    build_acmt_thermal_relay,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def initialized_values(block: Block) -> dict[int, float]:
    """Resolve thermal component initial values and parameters.

    :param block: Built thermal relay block.
    :return: UID-indexed numeric initialization.
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
    """Evaluate thermal relay algebraic equations in declaration order.

    :param block: Built thermal relay block.
    :param values: Mutable UID-indexed state and input values.
    :return: None.
    """
    for equation in block.algebraic_eqs:
        if isinstance(equation.left, Var):
            values[equation.left.uid] = equation.right.eval_uid(values)
        else:
            pass


def test_acmt_thermal_fraction_ramps_between_trip_temperatures() -> None:
    """The surviving population falls linearly between Th1t and Th2t.

    :return: None.
    """
    block: Block = build_acmt_thermal_relay(
        VarFactory(), 'acmt_thermal', AcmtThermalParameters(5.0, 1.0, 3.0, .5),
    ).block
    values: dict[int, float] = initialized_values(block)
    temperature: Var = block.state_vars[0]
    values[temperature.uid] = 2.0
    update_algebraic_values(block, values)

    assert len(block.state_vars) == 1
    assert values[block.out_vars[0].uid] == pytest.approx(2.0)
    assert values[block.out_vars[1].uid] == pytest.approx(.5)
    assert block.state_eqs[0].eval_uid(values) == pytest.approx(-.3)


@pytest.mark.parametrize(
    ('start_temperature', 'end_temperature', 'expected_fraction'),
    ((1.0, 0.0, 0.0), (2.0, 1.0, 1.0), (2.0, 3.0, 1.0)),
)
def test_acmt_thermal_instant_trip_settings(
        start_temperature: float,
        end_temperature: float,
        expected_fraction: float,
) -> None:
    """Immediate-trip configuration stays connected only below Th1t.

    :param start_temperature: Thermal trip-start threshold.
    :param end_temperature: Thermal trip-completion threshold.
    :param expected_fraction: Fraction at the chosen initial temperature.
    :return: None.
    """
    parameters: AcmtThermalParameters = AcmtThermalParameters(
        0.0, start_temperature, end_temperature, 1.0,
    )
    block: Block = build_acmt_thermal_relay(
        VarFactory(), 'acmt_instant', parameters,
    ).block
    values: dict[int, float] = initialized_values(block)
    update_algebraic_values(block, values)

    assert len(block.state_vars) == 0
    assert values[block.out_vars[1].uid] == pytest.approx(expected_fraction)


def test_acmt_thermal_settings_reject_nonfinite_and_negative_time() -> None:
    """Reject invalid thermal state constants before assembling equations.

    :return: None.
    """
    with pytest.raises(ValueError, match='finite'):
        build_acmt_thermal_relay(
            VarFactory(), 'acmt_nan', AcmtThermalParameters(1.0, 1.0, 2.0, float('nan')),
        )
    with pytest.raises(ValueError, match='nonnegative'):
        build_acmt_thermal_relay(
            VarFactory(), 'acmt_negative', AcmtThermalParameters(-1.0, 1.0, 2.0, 0.0),
        )
