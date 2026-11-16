# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Connected WT2 Type 2 controller topology checks."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.wt12t1_drive_train import (
    Wt12t1DriveTrainSettings,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wt2_control_chain import (
    build_wt2_control_chain,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wt2e1_rotor_resistance import Wt2e1Settings
from VeraGridEngine.Utils.Symbolic.block import Block
from tests.symbolic_block_roundtrip import roundtrip_block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var


def test_wt2_chain_shares_machine_power_and_generator_speed() -> None:
    """Connect WT2E1 to the shaft without introducing a second machine state.

    :return: None.
    """
    block: Block = build_wt2_control_chain(VarFactory()).block
    machine_power: Var = block.in_vars[0]
    machine_torque: Var = block.in_vars[1]
    generator_speed: Var = block.out_vars[2]
    resistance: Var = block.out_vars[-1]
    assert len(block.state_vars) == 11
    assert len(block.in_vars) == 5
    assert block.in_vars[-1].name.startswith('PowerCurveOffsetPu_')
    assert resistance.name.startswith('RotorResistanceFraction_')
    assert block.state_eqs[-3].contains_var(generator_speed)
    assert block.state_eqs[-2].contains_var(machine_power)
    assert block.state_eqs[-1].contains_var(block.state_vars[-3])
    assert block.state_eqs[-1].contains_var(block.state_vars[-2])
    assert block.state_eqs[6].contains_var(machine_torque)
    equation: Expr
    for equation in block.state_eqs:
        assert not equation.contains_var(resistance)
    restored: Block = roundtrip_block(block)
    assert len(restored.state_vars) == 11
    assert len(restored.in_vars) == 5
    assert restored.out_vars[-1].name == resistance.name


def test_wt2_chain_rejects_inconsistent_initial_speed() -> None:
    """Reject a source composition with conflicting shaft and rotor slip.

    :return: None.
    """
    with pytest.raises(ValueError, match='same initial generator speed'):
        build_wt2_control_chain(
            VarFactory(), shaft_settings=Wt12t1DriveTrainSettings(initial_speed=1.02),
            resistance_settings=Wt2e1Settings(initial_speed=1.03),
        )
