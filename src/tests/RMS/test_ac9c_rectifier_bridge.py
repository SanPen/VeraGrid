# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check AC9C bounded controlled-rectifier bridge behavior."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_bridge import (
    Ac9cRectifierBridgeSettings,
    build_ac9c_rectifier_bridge_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def make_bridge_bindings(block: Block, vavr: float, va: float) -> dict[int, float]:
    """Bind bridge parameters, input and state/output for equation checks.

    :param block: Native AC9C controlled-bridge block.
    :param vavr: Regulator output input.
    :param va: Bridge state or algebraic output.
    :return: UID-keyed numeric expression bindings.
    """
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    bindings[block.in_vars[0].uid] = vavr
    if len(block.state_vars) > 0:
        bindings[block.state_vars[0].uid] = va
    else:
        bindings[block.algebraic_vars[0].uid] = va
    return bindings


def test_ac9c_bridge_lag_applies_gain_and_directional_limits() -> None:
    """Evaluate the KA gain, positive-time lag and upper output stop.

    :return: None.
    """
    settings: Ac9cRectifierBridgeSettings = Ac9cRectifierBridgeSettings(
        ka=2.0, ta=.5, vrmax=.8, vrmin=-.8, vavr0=0.0, va0=.2,
    )
    block: Block = build_ac9c_rectifier_bridge_template(
        vf=VarFactory(), settings=settings,
    ).block
    bindings: dict[int, float] = make_bridge_bindings(block, .5, .2)
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(1.6)
    bindings[block.state_vars[0].uid] = .8
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(0.0)
    bindings[block.in_vars[0].uid] = 0.0
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(-1.6)


def test_ac9c_bridge_zero_time_is_a_bounded_static_gain() -> None:
    """Reduce TA=0 to a bounded algebraic KA gain.

    :return: None.
    """
    settings: Ac9cRectifierBridgeSettings = Ac9cRectifierBridgeSettings(
        ka=2.0, ta=0.0, vrmax=.8, vrmin=-.8, vavr0=0.0, va0=0.0,
    )
    block: Block = build_ac9c_rectifier_bridge_template(
        vf=VarFactory(), settings=settings,
    ).block
    bindings: dict[int, float] = make_bridge_bindings(block, .2, .4)
    assert len(block.state_vars) == 0
    assert block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(0.0)
    bindings[block.in_vars[0].uid] = 1.0
    bindings[block.algebraic_vars[0].uid] = .8
    assert block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(0.0)


def test_ac9c_bridge_rejects_invalid_parameters() -> None:
    """Reject invalid bridge gain, lag and voltage boundaries.

    :return: None.
    """
    with pytest.raises(ValueError, match='positive KA'):
        build_ac9c_rectifier_bridge_template(
            vf=VarFactory(), settings=Ac9cRectifierBridgeSettings(ka=0.0),
        )
    with pytest.raises(ValueError, match='limits must be ordered'):
        build_ac9c_rectifier_bridge_template(
            vf=VarFactory(), settings=Ac9cRectifierBridgeSettings(vrmin=2.0, vrmax=1.0),
        )
