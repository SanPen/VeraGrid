# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""REECA1 local terminal-voltage PI mode checks."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_local_voltage import (
    Reeca1LocalVoltageSettings,
    build_reeca1_local_voltage_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.renewable_partial_chain import build_renewable_partial_chain
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_constant_q import Reeca1ConstantQSettings
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def test_reeca1_local_voltage_applies_bias_capability_and_fault_freeze() -> None:
    """Use reference plus Vbias while preserving the shared voltage PI rules.

    :return: None.
    """
    block: Block = build_reeca1_local_voltage_template(
        vf=VarFactory(), settings=Reeca1LocalVoltageSettings(kvp=2., kvi=3., vbias=.01),
    ).block
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    bindings[block.in_vars[0].uid] = 1.02
    bindings[block.in_vars[1].uid] = 1.
    bindings[block.in_vars[2].uid] = 0.
    bindings[block.in_vars[3].uid] = .5
    bindings[block.state_vars[0].uid] = .1
    bindings[block.state_vars[1].uid] = .02
    bindings[block.algebraic_vars[0].uid] = 0.
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(.09)
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(.16)
    bindings[block.algebraic_vars[0].uid] = .16
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(7.)
    bindings[block.in_vars[3].uid] = .15
    bindings[block.algebraic_vars[0].uid] = 0.
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(.15)
    bindings[block.in_vars[2].uid] = 1.
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(0.)


def test_reeca1_local_voltage_rejects_ambiguous_mode_selection() -> None:
    """Require fault feedback and one reactive-control mode.

    :return: None.
    """
    with pytest.raises(ValueError, match='gains'):
        build_reeca1_local_voltage_template(
            vf=VarFactory(), settings=Reeca1LocalVoltageSettings(kvi=-1.),
        )
    with pytest.raises(ValueError, match='requires voltage-fault settings'):
        build_renewable_partial_chain(
            vf=VarFactory(), local_voltage_settings=Reeca1LocalVoltageSettings(),
        )
    with pytest.raises(ValueError, match='cannot be combined'):
        build_renewable_partial_chain(
            vf=VarFactory(), local_voltage_settings=Reeca1LocalVoltageSettings(),
            reactive_power_settings=Reeca1ConstantQSettings(),
        )
