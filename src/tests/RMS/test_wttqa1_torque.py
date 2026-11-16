# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Source-diagram checks for the WTTQA1 torque-reference controller."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.wttqa1_torque import (
    Wttqa1TorqueMode,
    Wttqa1TorqueSettings,
    build_wttqa1_torque_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def _wttqa1_bindings(block: Block) -> dict[int, float]:
    """Seed constant parameters and default algebraic values for expression checks.

    :param block: Stand-alone WTTQA1 block.
    :return: UID bindings for evaluated equations.
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


def test_wttqa1_power_error_divides_by_speed_and_returns_power() -> None:
    """Keep the torque PI between power error and speed-multiplied Pref.

    :return: None.
    """
    block: Block = build_wttqa1_torque_template(
        vf=VarFactory(), settings=Wttqa1TorqueSettings(
            kpp=2., kip=3., tp=.05, twref=30.,
            mode=Wttqa1TorqueMode.POWER_ERROR,
        ),
    ).block
    assert len(block.state_vars) == 3
    bindings: dict[int, float] = _wttqa1_bindings(block)
    bindings[block.in_vars[0].uid] = .6
    bindings[block.in_vars[1].uid] = 1.2
    bindings[block.in_vars[2].uid] = .8
    bindings[block.in_vars[3].uid] = 0.
    bindings[block.in_vars[4].uid] = 100.
    bindings[block.state_vars[0].uid] = .6
    bindings[block.state_vars[1].uid] = 1.
    bindings[block.state_vars[2].uid] = .5
    assert block.state_eqs[2].eval_uid(bindings) == pytest.approx(.5)
    bindings[block.algebraic_vars[0].uid] = 0.
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(.8333333333333334)
    bindings[block.algebraic_vars[0].uid] = .8333333333333334
    bindings[block.algebraic_vars[1].uid] = 0.
    assert -block.algebraic_eqs[1].eval_uid(bindings) == pytest.approx(1.)
    bindings[block.in_vars[3].uid] = 1.
    assert block.state_eqs[2].eval_uid(bindings) == pytest.approx(0.)


def test_wttqa1_speed_curve_scales_turbine_rating() -> None:
    """Convert machine-base Pe to the four-point TRATE curve base.

    :return: None.
    """
    curve: tuple[tuple[float, float], ...] = (
        (.2, .6), (.4, .7), (.6, .8), (.8, .9),
    )
    block: Block = build_wttqa1_torque_template(
        vf=VarFactory(), settings=Wttqa1TorqueSettings(
            tp=0., twref=.1, trate=50., curve=curve,
            mode=Wttqa1TorqueMode.SPEED_ERROR,
        ),
    ).block
    bindings: dict[int, float] = _wttqa1_bindings(block)
    bindings[block.in_vars[0].uid] = .25
    bindings[block.in_vars[1].uid] = .8
    bindings[block.in_vars[2].uid] = .25
    bindings[block.in_vars[3].uid] = 0.
    bindings[block.in_vars[4].uid] = 100.
    filtered: Var = next(signal for signal in block.algebraic_vars
                         if signal.name.startswith('FilteredElectricalPowerPu_'))
    bindings[filtered.uid] = .25
    reference: Var = next(state for state in block.state_vars
                          if state.name.startswith('SpeedReferencePu_'))
    bindings[reference.uid] = .65
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(1.)
    bindings[reference.uid] = .8
    integral: Var = next(state for state in block.state_vars
                         if state.name.startswith('TorqueIntegral_'))
    bindings[integral.uid] = .25 / .8
    assert block.state_eqs[1].eval_uid(bindings) == pytest.approx(0.)


def test_wttqa1_rejects_ambiguous_source_curve_and_mode() -> None:
    """Require increasing four-pair data or the all-zero unity-speed code.

    :return: None.
    """
    with pytest.raises(ValueError, match='curve'):
        build_wttqa1_torque_template(
            vf=VarFactory(), settings=Wttqa1TorqueSettings(
                curve=((.2, .7), (.4, .6), (.6, .8), (.8, .9)),
            ),
        )
    with pytest.raises(ValueError, match='mode'):
        build_wttqa1_torque_template(
            vf=VarFactory(), settings=Wttqa1TorqueSettings(mode=1),
        )
