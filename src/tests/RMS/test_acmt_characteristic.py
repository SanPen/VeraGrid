# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check the documented ACMT running and stalled power characteristics."""
from __future__ import annotations

import math

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.load_characteristics.acmt_characteristic import (
    AcmtCharacteristicParameters,
    build_acmt_power_characteristic,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def acmt_parameters() -> AcmtCharacteristicParameters:
    """Return a representative compressor characteristic.

    :return: ACMT coefficients with a 0.75 pu running-curve breakpoint.
    """
    return AcmtCharacteristicParameters(
        power_factor=.95,
        stall_resistance_pu=.12,
        stall_reactance_pu=.16,
        kp1=1.0,
        np1=1.0,
        kq1=.8,
        nq1=1.0,
        kp2=2.0,
        np2=2.0,
        kq2=1.5,
        nq2=2.0,
        breakdown_voltage_pu=.75,
        active_frequency_coefficient=1.2,
        reactive_frequency_coefficient=.6,
    )


def evaluate_algebraics(block: Block, values: dict[int, float]) -> None:
    """Evaluate algebraic outputs using the project symbolic interpreter.

    :param block: Characteristic block to evaluate.
    :param values: UID-indexed state/input values.
    :return: None.
    """
    for equation in block.algebraic_eqs:
        if isinstance(equation.left, Var):
            values[equation.left.uid] = equation.right.eval_uid(values)
        else:
            pass


def initial_values(block: Block) -> dict[int, float]:
    """Resolve component initialization and parameter expressions.

    :param block: Built symbolic characteristic.
    :return: UID-indexed initialized values.
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


def test_acmt_running_curve_meets_source_power_at_nominal_voltage() -> None:
    """Nominal ACMT running P/Q equal the source unit-power normalization.

    :return: None.
    """
    block: Block = build_acmt_power_characteristic(
        VarFactory(), 'acmt_nominal', acmt_parameters(),
    ).block
    values: dict[int, float] = initial_values(block)
    for variable in block.in_vars:
        if (variable.name.endswith('Running_acmt_nominal')
                or variable.name.endswith('VoltageMagnitudePu_acmt_nominal')):
            values[variable.uid] = 1.0
        else:
            values[variable.uid] = 0.0
    evaluate_algebraics(block, values)

    assert len(block.state_vars) == 0
    assert values[block.out_vars[0].uid] == pytest.approx(1.0)
    assert values[block.out_vars[1].uid] == pytest.approx(
        math.sqrt(1.0 - .95 ** 2) / .95,
    )


def test_acmt_running_curve_and_frequency_response() -> None:
    """Apply both published voltage sections and frequency multipliers.

    :return: None.
    """
    block: Block = build_acmt_power_characteristic(
        VarFactory(), 'acmt_curve', acmt_parameters(),
    ).block
    values: dict[int, float] = initial_values(block)
    for variable in block.in_vars:
        if variable.name.endswith('VoltageMagnitudePu_acmt_curve'):
            values[variable.uid] = .7
        elif variable.name.endswith('Running_acmt_curve'):
            values[variable.uid] = 1.0
        elif variable.name.endswith('FrequencyDeviationPu_acmt_curve'):
            values[variable.uid] = .01
        else:
            values[variable.uid] = 0.0
    evaluate_algebraics(block, values)
    p0: float = 1.0 - 1.0 * (1.0 - .75)
    q0: float = math.sqrt(1.0 - .95 ** 2) / .95 - .8 * (1.0 - .75)
    expected_p: float = (p0 + 2.0 * (.75 - .7) ** 2) * (1.0 + 1.2 * .01)
    expected_q: float = (
        q0 + 1.5 * (.75 - .7) ** 2
    ) * (1.0 + .6 * .01 / math.sqrt(1.0 - .95 ** 2))

    assert values[block.out_vars[0].uid] == pytest.approx(expected_p)
    assert values[block.out_vars[1].uid] == pytest.approx(expected_q)


def test_acmt_stall_impedance_and_invalid_unity_pf_frequency() -> None:
    """Select the stall impedance and reject its singular Q frequency slope.

    :return: None.
    """
    parameters: AcmtCharacteristicParameters = acmt_parameters()
    block: Block = build_acmt_power_characteristic(
        VarFactory(), 'acmt_stalled', parameters,
    ).block
    values: dict[int, float] = initial_values(block)
    for variable in block.in_vars:
        if variable.name.endswith('VoltageMagnitudePu_acmt_stalled'):
            values[variable.uid] = .6
        elif variable.name.endswith('Running_acmt_stalled'):
            values[variable.uid] = 0.0
        else:
            values[variable.uid] = 0.0
    evaluate_algebraics(block, values)
    impedance_squared: float = .12 ** 2 + .16 ** 2

    assert values[block.out_vars[0].uid] == pytest.approx(.6 ** 2 * .12 / impedance_squared)
    assert values[block.out_vars[1].uid] == pytest.approx(.6 ** 2 * .16 / impedance_squared)

    unity_power_factor: AcmtCharacteristicParameters = acmt_parameters()
    unity_power_factor.power_factor = 1.0
    with pytest.raises(ValueError, match='singular'):
        build_acmt_power_characteristic(
            VarFactory(), 'acmt_singular', unity_power_factor,
        )
