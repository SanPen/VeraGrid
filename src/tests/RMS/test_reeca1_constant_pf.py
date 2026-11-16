# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""REECA1 local constant-power-factor reference checks."""

import math

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_constant_pf import (
    Reeca1ConstantPfSettings,
    build_reeca1_constant_pf_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.renewable_partial_chain import build_renewable_partial_chain
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def test_reeca1_pf_reference_uses_filtered_electrical_power() -> None:
    """Lag Pe before multiplying by the fixed power-factor angle.

    :return: None.
    """
    block: Block = build_reeca1_constant_pf_template(
        vf=VarFactory(), settings=Reeca1ConstantPfSettings(tp=.1),
    ).block
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    bindings[block.in_vars[0].uid] = .8
    bindings[block.in_vars[1].uid] = math.atan(.25)
    bindings[block.state_vars[0].uid] = .6
    bindings[block.out_vars[0].uid] = 0.
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(2.)
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(.15)


def test_reeca1_pf_zero_tp_reduces_algebraically() -> None:
    """Keep zero Tp exact and reject a negative filter time.

    :return: None.
    """
    block: Block = build_reeca1_constant_pf_template(
        vf=VarFactory(), settings=Reeca1ConstantPfSettings(tp=0.),
    ).block
    assert len(block.state_vars) == 0
    assert len(block.algebraic_vars) == 2
    with pytest.raises(ValueError, match='filter time'):
        build_reeca1_constant_pf_template(
            vf=VarFactory(), settings=Reeca1ConstantPfSettings(tp=-.01),
        )
    with pytest.raises(ValueError, match='requires reactive-current settings'):
        build_renewable_partial_chain(
            vf=VarFactory(), power_factor_settings=Reeca1ConstantPfSettings(),
        )
