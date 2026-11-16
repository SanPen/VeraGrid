# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Source-order checks for the partial REECA1 active-power path."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_active_power import (
    Reeca1ActivePowerMode,
    Reeca1ActivePowerSettings,
    build_reeca1_active_power_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.renewable_partial_chain import build_renewable_partial_chain
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def test_reeca1_active_order_lags_power_before_voltage_conversion() -> None:
    """Respond to Pref through Pord, then divide by filtered voltage.

    :return: None.
    """
    block: Block = build_reeca1_active_power_template(
        vf=VarFactory(), settings=Reeca1ActivePowerSettings(tpord=.05, pmax=1.),
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
    bindings[block.in_vars[1].uid] = .5
    bindings[block.state_vars[0].uid] = .6
    bindings[block.out_vars[0].uid] = 0.
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(4.)
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(1.2)
    bindings[block.in_vars[1].uid] = 0.
    assert -block.algebraic_eqs[0].eval_uid(bindings) == pytest.approx(60.)


def test_reeca1_active_order_zero_time_is_exactly_algebraic() -> None:
    """Use the source zero-time reduction and reject invalid power bounds.

    :return: None.
    """
    block: Block = build_reeca1_active_power_template(
        vf=VarFactory(), settings=Reeca1ActivePowerSettings(tpord=0., pmax=.7),
    ).block
    assert len(block.state_vars) == 0
    assert len(block.algebraic_vars) == 2
    with pytest.raises(ValueError, match='time or limits'):
        build_reeca1_active_power_template(
            vf=VarFactory(), settings=Reeca1ActivePowerSettings(tpord=-.01),
        )


def test_reeca1_speed_mode_multiplies_pref_before_pord_lag() -> None:
    """Use the source PFLAG speed path without changing direct-power mode.

    :return: None.
    """
    settings: Reeca1ActivePowerSettings = Reeca1ActivePowerSettings(
        tpord=.05, mode=Reeca1ActivePowerMode.TORQUE_TIMES_SPEED,
    )
    block: Block = build_reeca1_active_power_template(
        vf=VarFactory(), settings=settings,
    ).block
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    assert len(block.in_vars) == 3
    bindings[block.in_vars[0].uid] = .8
    bindings[block.in_vars[1].uid] = 1.
    bindings[block.in_vars[2].uid] = .9
    bindings[block.state_vars[0].uid] = .6
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(2.4)
    bindings[block.in_vars[2].uid] = 1.1
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(5.6)
    with pytest.raises(ValueError, match='mode'):
        build_reeca1_active_power_template(
            vf=VarFactory(), settings=Reeca1ActivePowerSettings(mode=1),
        )
    chain: Block = build_renewable_partial_chain(
        vf=VarFactory(), active_power_settings=settings,
    ).block
    assert any(parameter.name.startswith('TurbineSpeedOrder_')
               for parameter in chain.event_dict)
