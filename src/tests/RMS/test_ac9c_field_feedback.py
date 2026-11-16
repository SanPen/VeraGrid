# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check the AC9C filtered field-feedback transfer."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_field_feedback import (
    Ac9cFieldFeedbackSettings,
    build_ac9c_field_feedback_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def make_feedback_bindings(block: Block, signal: float, feedback: float) -> dict[int, float]:
    """Bind feedback filter parameters, input and state/output.

    :param block: Native AC9C feedback block.
    :param signal: Source feedback input.
    :param feedback: Filter state or algebraic output.
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
    bindings[block.in_vars[0].uid] = signal
    if len(block.state_vars) > 0:
        bindings[block.state_vars[0].uid] = feedback
    else:
        bindings[block.algebraic_vars[0].uid] = feedback
    return bindings


def test_ac9c_field_feedback_positive_time_retains_filter_state() -> None:
    """Evaluate KF/(1+s*TF) using its explicit state equation.

    :return: None.
    """
    settings: Ac9cFieldFeedbackSettings = Ac9cFieldFeedbackSettings(
        kf=2.0, tf=.5, signal0=.5, feedback0=1.0,
    )
    block: Block = build_ac9c_field_feedback_template(
        vf=VarFactory(), settings=settings,
    ).block
    bindings: dict[int, float] = make_feedback_bindings(block, .75, 1.0)
    assert len(block.state_vars) == 1
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(1.0)


def test_ac9c_field_feedback_zero_time_reduces_to_static_gain() -> None:
    """Reduce TF=0 to the exact static gain and reject wrong initialization.

    :return: None.
    """
    settings: Ac9cFieldFeedbackSettings = Ac9cFieldFeedbackSettings(
        kf=2.0, tf=0.0, signal0=.5, feedback0=1.0,
    )
    block: Block = build_ac9c_field_feedback_template(
        vf=VarFactory(), settings=settings,
    ).block
    bindings: dict[int, float] = make_feedback_bindings(block, .75, 1.5)
    assert len(block.state_vars) == 0
    assert block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(0.0)
    with pytest.raises(ValueError, match='must match static gain'):
        build_ac9c_field_feedback_template(
            vf=VarFactory(),
            settings=Ac9cFieldFeedbackSettings(kf=2.0, tf=0.0, signal0=.5, feedback0=0.0),
        )
