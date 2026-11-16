# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check ACMT voltage and frequency measurement-filter states."""
from __future__ import annotations

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.load_characteristics.acmt_measurement_filters import (
    AcmtMeasurementFilterParameters,
    build_acmt_measurement_filters,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def initialized_values(block: Block) -> dict[int, float]:
    """Resolve initial values and event parameters for the filter block.

    :param block: Built ACMT filter block.
    :return: UID-indexed numeric values.
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


def update_algebraics(block: Block, values: dict[int, float]) -> None:
    """Evaluate filter output equations in their declared order.

    :param block: Built ACMT filter block.
    :param values: Mutable UID-indexed runtime values.
    :return: None.
    """
    for equation in block.algebraic_eqs:
        if isinstance(equation.left, Var):
            values[equation.left.uid] = equation.right.eval_uid(values)
        else:
            pass


def test_acmt_measurement_filters_track_voltage_and_frequency() -> None:
    """Both positive time constants contribute one correctly initialized state.

    :return: None.
    """
    block: Block = build_acmt_measurement_filters(
        VarFactory(), 'acmt_filters', AcmtMeasurementFilterParameters(.2, .5, .98),
    ).block
    values: dict[int, float] = initialized_values(block)
    for input_variable in block.in_vars:
        if input_variable.name.endswith('BusVoltageMagnitudePu_acmt_filters'):
            values[input_variable.uid] = .9
        else:
            values[input_variable.uid] = .99
    update_algebraics(block, values)

    assert len(block.state_vars) == 2
    assert values[block.out_vars[0].uid] == pytest.approx(.98)
    assert values[block.out_vars[1].uid] == pytest.approx(0.0)
    assert block.state_eqs[0].eval_uid(values) == pytest.approx(-.4)
    assert block.state_eqs[1].eval_uid(values) == pytest.approx(-.02)


def test_acmt_measurement_zero_times_reduce_to_algebraic_signals() -> None:
    """Zero lag times expose the source terminal quantities directly.

    :return: None.
    """
    block: Block = build_acmt_measurement_filters(
        VarFactory(), 'acmt_static_filters',
        AcmtMeasurementFilterParameters(0.0, 0.0, .97, 1.0),
    ).block
    values: dict[int, float] = initialized_values(block)
    for input_variable in block.in_vars:
        if input_variable.name.endswith('BusVoltageMagnitudePu_acmt_static_filters'):
            values[input_variable.uid] = .91
        else:
            values[input_variable.uid] = .985
    update_algebraics(block, values)

    assert len(block.state_vars) == 0
    assert values[block.out_vars[0].uid] == pytest.approx(.91)
    assert values[block.out_vars[1].uid] == pytest.approx(-.015)
