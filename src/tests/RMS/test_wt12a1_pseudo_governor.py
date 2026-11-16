# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Equation and source-record checks for the Type 1/2 wind pseudo governor."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.wt12a1_pseudo_governor import (
    Wt12a1Settings,
    build_wt12a1_pseudo_governor_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def _parameter_bindings(block: Block) -> dict[int, float]:
    """Read the construction constants into UID-based expression bindings.

    :param block: Stand-alone WT12A1 controller block.
    :return: Numeric parameter bindings.
    """
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    return bindings


def test_wt12a1_droop_integral_and_two_output_lags() -> None:
    """Follow the four source states and limit the PI before the output lags.

    :return: None.
    """
    block: Block = build_wt12a1_pseudo_governor_template(
        VarFactory(), settings=Wt12a1Settings(droop=.1, kp=2., ti=.5,
                                               t1=.2, t2=.4, tp=.1,
                                               limmax=.5, limmin=0.),
    ).block
    assert len(block.state_vars) == 4
    assert tuple(state.name.split('_')[0] for state in block.state_vars) == (
        'FilteredElectricalPowerPu', 'PowerIntegral', 'FirstOutputPu', 'MechanicalPowerPu',
    )
    bindings: dict[int, float] = _parameter_bindings(block)
    bindings[block.in_vars[0].uid] = .6
    bindings[block.in_vars[1].uid] = 1.
    bindings[block.in_vars[2].uid] = .8
    bindings[block.in_vars[3].uid] = 1.
    bindings[block.state_vars[0].uid] = .6
    bindings[block.state_vars[1].uid] = .4
    bindings[block.state_vars[2].uid] = .4
    bindings[block.state_vars[3].uid] = .4
    bindings[block.algebraic_vars[0].uid] = 0.
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(0.)
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(.04)
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(.44)
    bindings[block.algebraic_vars[0].uid] = .44
    assert block.state_eqs[2].eval_uid(bindings) == pytest.approx(.2)
    assert block.state_eqs[3].eval_uid(bindings) == pytest.approx(0.)
    bindings[block.in_vars[2].uid] = 5.
    bindings[block.algebraic_vars[0].uid] = 0.
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(.5)
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(0.)
    bindings[block.state_vars[1].uid] = -.1
    bindings[block.in_vars[2].uid] = -.5
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(0.)


def test_wt12a1_zero_lags_keep_integrator_only() -> None:
    """Reduce zero-time filters to algebraic paths without fake states.

    :return: None.
    """
    block: Block = build_wt12a1_pseudo_governor_template(
        VarFactory(), settings=Wt12a1Settings(tp=0., t1=0., t2=0.),
    ).block
    assert len(block.state_vars) == 1
    assert block.state_vars[0].name.startswith('PowerIntegral_')
    assert len(block.algebraic_vars) == 4


@pytest.mark.parametrize('settings', (
    Wt12a1Settings(ti=0.),
    Wt12a1Settings(t1=-.1),
    Wt12a1Settings(limmax=0., limmin=0.),
    Wt12a1Settings(droop=float('nan')),
))
def test_wt12a1_rejects_invalid_source_values(settings: Wt12a1Settings) -> None:
    """Reject settings that cannot produce the documented state equations.

    :param settings: Invalid source parameter set.
    :return: None.
    """
    with pytest.raises(ValueError):
        build_wt12a1_pseudo_governor_template(VarFactory(), settings=settings)
