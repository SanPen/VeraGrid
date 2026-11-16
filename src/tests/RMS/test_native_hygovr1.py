# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Native HYGOVR1 equilibrium and structural checks."""
from __future__ import annotations

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.governors.hygovr1 import (
    Hygovr1Parameters, build_hygovr1_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Expr, Var


def _initialized_values(block: Block) -> dict[int, float]:
    """Resolve the constant initial equations of one controller graph.

    :param block: Built HYGOVR1 block.
    :return: Numerical values keyed by symbolic variable ID.
    """
    values: dict[int, float] = dict()
    expressions: dict[Var, Expr] = dict(block.parameters)
    expressions.update(block.event_dict)
    expressions.update(block.init_eqs)
    for _ in range(len(expressions) + 1):
        for variable, expression in expressions.items():
            if variable.uid not in values and all(item.uid in values for item in expression.get_vars()):
                values[variable.uid] = expression.eval_uid(values)
            else:
                pass
    assert all(variable.uid in values for variable in expressions)
    for _ in range(len(block.algebraic_eqs) + 1):
        for equation in block.algebraic_eqs:
            assert isinstance(equation, BinOp) and equation.op == '-' and isinstance(equation.left, Var)
            values[equation.left.uid] = equation.right.eval_uid(values)
    return values


@pytest.mark.parametrize('power_feedback_time', (0.0, 0.2))
def test_hygovr1_initializes_all_states_and_hydraulic_equations(power_feedback_time: float) -> None:
    """Both gate and filtered-electrical-power feedback start at zero residual.

    :param power_feedback_time: Zero selects gate feedback; positive selects Pelec.
    :return: None.
    """
    settings: Hygovr1Parameters = Hygovr1Parameters(tt=power_feedback_time, db2_mw=0.002)
    template = build_hygovr1_template(VarFactory(), 'hydro', settings)
    block: Block = template.block
    values: dict[int, float] = _initialized_values(block)
    assert len(block.state_vars) == 10
    assert len(block.in_vars) == 3
    assert len(block.out_vars) == 3
    assert max(abs(equation.eval_uid(values)) for equation in block.state_eqs) < 1e-12
    assert max(abs(equation.eval_uid(values)) for equation in block.algebraic_eqs) < 1e-12
    assert values[block.out_vars[0].uid] == pytest.approx(settings.initial_power)
    assert values[block.out_vars[2].uid] == pytest.approx(
        settings.initial_power / settings.at + settings.no_load_flow,
    )


def test_hygovr1_rejects_singular_flow_and_improper_lead_lag() -> None:
    """Reject zero effective gate and improper lead-only stages.

    :return: None.
    """
    with pytest.raises(ValueError, match='gate limits'):
        build_hygovr1_template(
            VarFactory(), 'singular_gate', Hygovr1Parameters(gate_min=0.0),
        )
    with pytest.raises(ValueError, match='zero lead'):
        build_hygovr1_template(
            VarFactory(), 'improper_stage',
            Hygovr1Parameters(lead_lag_times=(0.1, 0.0, 0.0, 0.1, 0.0, 0.1, 0.0, 0.1)),
        )


def test_hygovr1_overspeed_damping_reduces_mechanical_power() -> None:
    """Use the diagram's raw speed-deviation damping sign.

    :return: None.
    """
    settings: Hygovr1Parameters = Hygovr1Parameters(damping=0.2)
    block: Block = build_hygovr1_template(VarFactory(), 'damping', settings).block
    values: dict[int, float] = _initialized_values(block)
    initial_power: float = values[block.out_vars[0].uid]
    values[block.in_vars[0].uid] = 1.01
    for equation in block.algebraic_eqs:
        assert isinstance(equation, BinOp) and equation.op == '-' and isinstance(equation.left, Var)
        values[equation.left.uid] = equation.right.eval_uid(values)
    assert values[block.out_vars[0].uid] < initial_power
