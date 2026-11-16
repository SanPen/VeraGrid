# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""PSS/E DERA1 current-circle priority and generator/storage bounds."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_current_limit import (
    build_dera1_current_limit_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def evaluate_currents(
        block: Block,
        active_command: float,
        reactive_command: float,
) -> tuple[float, float]:
    """Evaluate an algebraic DERA1 current-limit block in declaration order.

    :param block: Native current-limit block.
    :param active_command: Requested active current.
    :param reactive_command: Requested reactive current.
    :return: Limited active and reactive current.
    """
    values: dict[int, float] = dict()
    for parameter, expression in block.event_dict.items():
        assert isinstance(expression, Const)
        values[parameter.uid] = float(expression.value)
    values[block.in_vars[0].uid] = active_command
    values[block.in_vars[1].uid] = reactive_command
    signal: Var
    equation: Expr
    for signal, equation in zip(block.algebraic_vars, block.algebraic_eqs):
        values[signal.uid] = 0.0
        values[signal.uid] = -equation.eval_uid(values)
    return (values[block.out_vars[0].uid], values[block.out_vars[1].uid])


def test_dera1_reactive_priority_reserves_q_capability() -> None:
    """Reactive command gets first use of Imax and active current uses remainder."""
    block: Block = build_dera1_current_limit_template(
        VarFactory(), imax=1.0,
    ).block
    active, reactive = evaluate_currents(block, 0.8, 0.8)
    assert active == pytest.approx(0.6)
    assert reactive == pytest.approx(0.8)


def test_dera1_active_priority_reserves_p_capability() -> None:
    """Active command gets first use of Imax and reactive current uses remainder."""
    block: Block = build_dera1_current_limit_template(
        VarFactory(), imax=1.0, active_current_priority=True,
    ).block
    active, reactive = evaluate_currents(block, 0.8, 0.8)
    assert active == pytest.approx(0.8)
    assert reactive == pytest.approx(0.6)


def test_dera1_storage_allows_negative_active_current() -> None:
    """Storage mode accepts charging current inside the remaining Q-priority circle."""
    block: Block = build_dera1_current_limit_template(
        VarFactory(), imax=1.0, generator=False,
    ).block
    active, reactive = evaluate_currents(block, -0.8, 0.8)
    assert active == pytest.approx(-0.6)
    assert reactive == pytest.approx(0.8)


def test_dera1_generator_blocks_negative_active_current() -> None:
    """Generator mode applies the source-defined zero lower active-current bound."""
    block: Block = build_dera1_current_limit_template(
        VarFactory(), imax=1.0, generator=True,
    ).block
    active, reactive = evaluate_currents(block, -0.4, 0.3)
    assert active == pytest.approx(0.0)
    assert reactive == pytest.approx(0.3)


def test_dera1_rejects_nonpositive_current_capability() -> None:
    """A missing physical converter limit is rejected at template construction."""
    with pytest.raises(ValueError):
        build_dera1_current_limit_template(VarFactory(), imax=0.0)
