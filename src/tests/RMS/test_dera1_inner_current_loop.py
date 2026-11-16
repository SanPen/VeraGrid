# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check the DERA1 trip-gated Id/Iq loop realization."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_inner_current_loop import (
    Dera1InnerCurrentLoopSettings,
    build_dera1_inner_current_loop_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def test_dera1_inner_current_loops_have_tg_states_and_rrpwr_limit() -> None:
    """The trip multiplier gates both channels and Rrpwr limits active order."""
    block: Block = build_dera1_inner_current_loop_template(
        VarFactory(),
        settings=Dera1InnerCurrentLoopSettings(
            tg=0.1, rrpwr=0.25, initial_active_current=0.4,
            initial_reactive_current=-0.2,
        ),
    ).block
    assert len(block.state_vars) == 2
    assert len(block.procedural_logic) == 0
    active_equation: Expr = block.state_eqs[0]
    reactive_equation: Expr = block.state_eqs[1]
    bindings: dict[int, float] = dict()
    parameter: Var
    expression: Expr
    for parameter, expression in block.event_dict.items():
        if isinstance(expression, Const):
            bindings[parameter.uid] = float(expression.value)
        else:
            pass
    bindings[block.in_vars[0].uid] = 0.8
    bindings[block.in_vars[1].uid] = -0.4
    bindings[block.in_vars[2].uid] = 0.5
    bindings[block.state_vars[0].uid] = 0.4
    bindings[block.state_vars[1].uid] = -0.2
    target: Var = block.algebraic_vars[0]
    bindings[target.uid] = 0.0
    bindings[target.uid] = -block.algebraic_eqs[0].eval_uid(bindings)
    assert bindings[target.uid] == pytest.approx(0.4)
    bindings[target.uid] = 0.8
    assert active_equation.eval_uid(bindings) == pytest.approx(0.25)
    bindings[target.uid] = -0.2
    assert active_equation.eval_uid(bindings) == pytest.approx(-0.25)
    assert reactive_equation.eval_uid(bindings) == pytest.approx(0.0)


def test_dera1_inner_current_loop_rejects_invalid_settings() -> None:
    """Require positive Tg and nonnegative active-current recovery rate."""
    with pytest.raises(ValueError, match='Tg'):
        build_dera1_inner_current_loop_template(
            VarFactory(), settings=Dera1InnerCurrentLoopSettings(tg=0.0),
        )
    with pytest.raises(ValueError, match='Rrpwr'):
        build_dera1_inner_current_loop_template(
            VarFactory(), settings=Dera1InnerCurrentLoopSettings(rrpwr=-0.1),
        )
