# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""TGOV3 fast-valving schedule boundaries from PSS/E 33.10."""
from __future__ import annotations

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.governors.tgov3_fast_valving import (
    Tgov3FastValvingSettings,
    build_tgov3_fast_valving_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const


def tgov3_intercept_position(block: Block, time: float) -> float:
    """Evaluate the schedule's single algebraic output at one global time.

    :param block: Stateless TGOV3 valve schedule block.
    :param time: Simulation time in seconds.
    :return: Intercept-valve position in per unit.
    """
    bindings: dict[int, float] = dict()
    for variable, expression in block.event_dict.items():
        assert isinstance(expression, Const)
        bindings[variable.uid] = float(expression.value)
    global_time: list = [variable for variable in block.algebraic_eqs[0].get_vars()
                         if variable.name == 'glob_time']
    assert len(global_time) == 1
    bindings[global_time[0].uid] = time
    equation = block.algebraic_eqs[0]
    return float(equation.right.eval_uid(bindings))


def test_tgov3_fast_valving_tracks_close_hold_reopen_boundaries() -> None:
    """Check source TI/TA/TB/TC transition points and linear ramps."""
    template = build_tgov3_fast_valving_template(
        VarFactory(),
        settings=Tgov3FastValvingSettings(
            start_time=2.0, close_time=.1, reopen_time=.3, open_time=1.0,
        ),
    )
    block: Block = template.block
    assert tgov3_intercept_position(block, 1.99) == pytest.approx(1.0)
    assert tgov3_intercept_position(block, 2.0) == pytest.approx(1.0)
    assert tgov3_intercept_position(block, 2.05) == pytest.approx(.5)
    assert tgov3_intercept_position(block, 2.1) == pytest.approx(0.0)
    assert tgov3_intercept_position(block, 2.3) == pytest.approx(0.0)
    assert tgov3_intercept_position(block, 2.65) == pytest.approx(.5)
    assert tgov3_intercept_position(block, 3.0) == pytest.approx(1.0)


@pytest.mark.parametrize(
    'settings',
    (
        Tgov3FastValvingSettings(start_time=-1.0, close_time=.1, reopen_time=.2, open_time=.3),
        Tgov3FastValvingSettings(start_time=0.0, close_time=.3, reopen_time=.2, open_time=.4),
        Tgov3FastValvingSettings(start_time=0.0, close_time=.1, reopen_time=.3, open_time=.3),
    ),
)
def test_tgov3_fast_valving_rejects_invalid_time_order(
        settings: Tgov3FastValvingSettings,
) -> None:
    """Reject schedules whose intervals cannot satisfy the source diagram."""
    with pytest.raises(ValueError):
        build_tgov3_fast_valving_template(VarFactory(), settings=settings)
