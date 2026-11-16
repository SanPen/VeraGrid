# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Source-order checks for REECA1 local constant-Q control."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_constant_q import (
    Reeca1ConstantQSettings,
    build_reeca1_constant_q_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def test_reeca1_constant_q_limits_power_then_lags_current() -> None:
    """Apply Qmax before dividing by filtered voltage and Tiq.

    :return: None.
    """
    block: Block = build_reeca1_constant_q_template(
        vf=VarFactory(), settings=Reeca1ConstantQSettings(tiq=.1, qmin=-.3, qmax=.3),
    ).block
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    bindings[block.in_vars[0].uid] = .4
    bindings[block.in_vars[1].uid] = .8
    bindings[block.state_vars[0].uid] = .2
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(1.75)
    bindings[block.in_vars[0].uid] = -.4
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(-5.75)


def test_reeca1_constant_q_zero_tiq_reduces_algebraically() -> None:
    """Keep zero Tiq exact and reject invalid reference bounds.

    :return: None.
    """
    block: Block = build_reeca1_constant_q_template(
        vf=VarFactory(), settings=Reeca1ConstantQSettings(tiq=0., qmax=.3),
    ).block
    assert len(block.state_vars) == 0
    assert len(block.algebraic_vars) == 1
    with pytest.raises(ValueError, match='time or limits'):
        build_reeca1_constant_q_template(
            vf=VarFactory(), settings=Reeca1ConstantQSettings(qmin=.5, qmax=.4),
        )
