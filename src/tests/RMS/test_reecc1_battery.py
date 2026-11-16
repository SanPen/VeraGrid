# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check the REEC_C SOC state and its boundary-controlled power limits."""
from __future__ import annotations

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.reecc1_battery import (
    Reecc1BatterySettings,
    build_reecc1_battery_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_active_power import (
    Reeca1ActivePowerSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.renewable_partial_chain import (
    build_renewable_partial_chain,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var


def test_reecc1_battery_declares_energy_state_and_boundary_gates() -> None:
    """Expose SOC and power-order gates while integrating generated energy."""
    template: RmsModelTemplate = build_reecc1_battery_template(VarFactory())
    block: Block = template.block

    assert len(block.state_vars) == 1
    assert len(block.state_eqs) == 1
    assert block.out_vars[0].name.startswith('StateOfChargePu_')
    assert block.out_vars[1].name.startswith('BatteryIpminPu_')
    assert block.out_vars[2].name.startswith('BatteryIpmaxPu_')
    assert block.out_vars[3].name.startswith('ActiveCurrentCommandPu_')
    assert block.init_eqs[block.state_vars[0]] == 0

    energy_derivative: Expr = block.state_eqs[0]
    discharge_time: Var = next(parameter for parameter in block.event_dict
                               if parameter.name.startswith('T_'))
    discharge_bindings: dict[str, float] = {
        block.in_vars[0].name: 0.5,
        discharge_time.name: 20.0,
    }
    charge_bindings: dict[str, float] = {
        block.in_vars[0].name: -0.5,
        discharge_time.name: 20.0,
    }
    assert energy_derivative.eval(**discharge_bindings) == pytest.approx(0.025)
    assert energy_derivative.eval(**charge_bindings) == pytest.approx(-0.025)

    active_current_equation: Expr = block.algebraic_eqs[3]
    active_bindings: dict[str, float] = {
        block.in_vars[1].name: 0.3,
        block.in_vars[2].name: 0.2,
        block.out_vars[1].name: -1.0,
        block.out_vars[2].name: 1.0,
        block.out_vars[3].name: 0.5,
    }
    assert active_current_equation.eval(**active_bindings) == 0.0

    pmin_equation: Expr = block.algebraic_eqs[1]
    soc_maximum: Var = next(parameter for parameter in block.event_dict
                            if parameter.name.startswith('SOCMAX_'))
    pmin_bindings: dict[str, float] = {
        block.out_vars[0].name: 1.0,
        block.in_vars[3].name: -0.8,
        block.out_vars[1].name: 0.0,
        soc_maximum.name: 1.0,
    }
    assert pmin_equation.eval(**pmin_bindings) == 0.0

    pmax_equation: Expr = block.algebraic_eqs[2]
    soc_minimum: Var = next(parameter for parameter in block.event_dict
                            if parameter.name.startswith('SOCMIN_'))
    pmax_bindings: dict[str, float] = {
        block.out_vars[0].name: 0.0,
        block.in_vars[4].name: 0.9,
        block.out_vars[2].name: 0.0,
        soc_minimum.name: 0.0,
    }
    assert pmax_equation.eval(**pmax_bindings) == 0.0


def test_reecc1_battery_rejects_invalid_soc_initialization() -> None:
    """Require the initial SOC to lie inside the allowed SOC range."""
    with pytest.raises(ValueError):
        build_reecc1_battery_template(
            VarFactory(), settings=Reecc1BatterySettings(
                soc_initial=0.1, soc_minimum=0.2,
            ),
        )


def test_reecc1_battery_connects_to_the_renewable_current_source_chain() -> None:
    """Assemble charging limits, Paux and SOC into the native converter host."""
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=VarFactory(),
        name='Battery integration',
        active_power_settings=Reeca1ActivePowerSettings(
            pmin=-0.8, pmax=0.8, bidirectional=True,
        ),
        battery_settings=Reecc1BatterySettings(
            time_seconds=20.0, soc_initial=0.5, soc_maximum=1.0, soc_minimum=0.0,
        ),
    )
    block: Block = template.block
    state_names: tuple[str, ...] = tuple(state.name for state in block.state_vars)
    algebraic_names: tuple[str, ...] = tuple(signal.name for signal in block.algebraic_vars)
    input_names: tuple[str, ...] = tuple(signal.name for signal in block.event_dict)

    assert any('StateOfChargePu_Battery integration battery' in name for name in algebraic_names)
    assert any('PauxCurrentOrder_Battery integration' in name for name in input_names)
    assert any('BatteryEnergyOutputPu_Battery integration battery' in name for name in state_names)
