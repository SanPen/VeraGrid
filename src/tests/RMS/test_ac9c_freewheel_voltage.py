# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check the AC9C KFW freewheel-voltage gain and limits."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_freewheel_voltage import (
    Ac9cFreewheelVoltageSettings,
    build_ac9c_freewheel_voltage_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def make_freewheel_bindings(block: Block, feedback: float, output: float) -> dict[int, float]:
    """Bind freewheel parameters, input and algebraic output.

    :param block: Native AC9C freewheel-voltage block.
    :param feedback: Filtered field-feedback input.
    :param output: Bounded VFW output.
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
    bindings[block.in_vars[0].uid] = feedback
    bindings[block.algebraic_vars[0].uid] = output
    return bindings


def test_ac9c_freewheel_voltage_applies_gain_and_both_limits() -> None:
    """Evaluate unsaturated gain and upper/lower freewheel clipping.

    :return: None.
    """
    settings: Ac9cFreewheelVoltageSettings = Ac9cFreewheelVoltageSettings(
        kfw=2.0, vfwmax=.6, vfwmin=-.4, feedback0=.1, vfw0=.2,
    )
    block: Block = build_ac9c_freewheel_voltage_template(
        vf=VarFactory(), settings=settings,
    ).block
    bindings: dict[int, float] = make_freewheel_bindings(block, .1, .2)
    assert block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(0.0)
    bindings[block.in_vars[0].uid] = 1.0
    bindings[block.algebraic_vars[0].uid] = .6
    assert block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(0.0)
    bindings[block.in_vars[0].uid] = -1.0
    bindings[block.algebraic_vars[0].uid] = -.4
    assert block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(0.0)


def test_ac9c_freewheel_voltage_rejects_inconsistent_initial_output() -> None:
    """Require a feasible equilibrium consistent with gain and output limits.

    :return: None.
    """
    with pytest.raises(ValueError, match='must match its bounded gain'):
        build_ac9c_freewheel_voltage_template(
            vf=VarFactory(),
            settings=Ac9cFreewheelVoltageSettings(
                kfw=2.0, vfwmax=1.0, vfwmin=0.0, feedback0=.5, vfw0=.5,
            ),
        )
