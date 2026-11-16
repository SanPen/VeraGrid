# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check AC9C field-current PI behavior and limits."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_current_regulator import (
    Ac9cCurrentRegulatorSettings,
    build_ac9c_current_regulator_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def make_current_regulator_bindings(block: Block, error: float, integral: float) -> dict[int, float]:
    """Bind current-regulator parameters, input and memory for equation checks.

    :param block: Native AC9C current-regulator block.
    :param error: Routed field-current error.
    :param integral: Integral memory.
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
    bindings[block.algebraic_vars[0].uid] = 0.0
    return bindings


def test_ac9c_current_regulator_integrates_and_limits_output() -> None:
    """Evaluate PI state rate and bounded VAVR output.

    :return: None.
    """
    settings: Ac9cCurrentRegulatorSettings = Ac9cCurrentRegulatorSettings(
        kpa=2.0, kia=3.0, vamax=0.5, vamin=-0.5, error0=0.0, vavr0=0.0,
    )
    block: Block = build_ac9c_current_regulator_template(
        vf=VarFactory(), settings=settings,
    ).block
    bindings: dict[int, float] = make_current_regulator_bindings(block, .1, .2)
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(.3)
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(.4)
    bindings[block.in_vars[0].uid] = 1.0
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(.5)


def test_ac9c_current_regulator_rejects_invalid_limits_and_gains() -> None:
    """Reject invalid PI domain and an infeasible initial output.

    :return: None.
    """
    with pytest.raises(ValueError, match='gains must be nonnegative'):
        build_ac9c_current_regulator_template(
            vf=VarFactory(), settings=Ac9cCurrentRegulatorSettings(kpa=-1.0),
        )
    with pytest.raises(ValueError, match='limits must be ordered'):
        build_ac9c_current_regulator_template(
            vf=VarFactory(), settings=Ac9cCurrentRegulatorSettings(vamin=2.0, vamax=1.0),
        )
