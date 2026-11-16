# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check the AC9C bounded PID stage and its derivative washout memory."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_pid import (
    Ac9cPidSettings,
    build_ac9c_pid_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def make_ac9c_pid_bindings(block: Block, error: float, integral: float,
                           derivative_memory: float | None) -> dict[int, float]:
    """Bind PID constants, input and state memories for equation checks.

    :param block: Native AC9C PID block.
    :param error: Voltage error at this point.
    :param integral: PID integral memory.
    :param derivative_memory: Optional filtered derivative memory.
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
    bindings[block.in_vars[0].uid] = error
    bindings[block.state_vars[0].uid] = integral
    if derivative_memory is not None:
        bindings[block.state_vars[1].uid] = derivative_memory
    else:
        pass
    bindings[block.algebraic_vars[0].uid] = 0.0
    return bindings


def test_ac9c_pid_tracks_integral_and_filtered_derivative_before_output_limit() -> None:
    """Evaluate P/I/D terms and retain the source output bound.

    :return: None.
    """
    settings: Ac9cPidSettings = Ac9cPidSettings(
        kpr=2.0, kir=3.0, kdr=.4, tdr=.1,
        vpidmax=.5, vpidmin=-.5, error0=0.0, vpid0=0.0,
    )
    block: Block = build_ac9c_pid_template(vf=VarFactory(), settings=settings).block
    bindings: dict[int, float] = make_ac9c_pid_bindings(block, .1, .2, .05)
    assert len(block.state_vars) == 2
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(.3)
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(.5)
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(.5)


def test_ac9c_pid_zero_derivative_time_reduces_when_derivative_is_disabled() -> None:
    """Remove the derivative state when both TDR and KDR are zero.

    :return: None.
    """
    settings: Ac9cPidSettings = Ac9cPidSettings(
        kpr=2.0, kir=3.0, kdr=0.0, tdr=0.0,
        vpidmax=2.0, vpidmin=-2.0, error0=0.0, vpid0=0.0,
    )
    block: Block = build_ac9c_pid_template(vf=VarFactory(), settings=settings).block
    bindings: dict[int, float] = make_ac9c_pid_bindings(block, .1, .2, None)
    assert len(block.state_vars) == 1
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(.4)


def test_ac9c_pid_rejects_improper_derivative_and_invalid_limits() -> None:
    """Reject a nonzero derivative numerator with a zero lag denominator.

    :return: None.
    """
    with pytest.raises(ValueError, match='positive TDR'):
        build_ac9c_pid_template(
            vf=VarFactory(), settings=Ac9cPidSettings(kdr=.1, tdr=0.0),
        )
    with pytest.raises(ValueError, match='output limits must be ordered'):
        build_ac9c_pid_template(
            vf=VarFactory(), settings=Ac9cPidSettings(vpidmin=2.0, vpidmax=1.0),
        )
