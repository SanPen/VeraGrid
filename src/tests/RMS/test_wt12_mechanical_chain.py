# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Connected Type 1/2 wind mechanical-path checks."""

import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.wt12_mechanical_chain import (
    build_wt12_mechanical_chain,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wt12t1_drive_train import (
    Wt12t1DriveTrainSettings,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var


@pytest.mark.parametrize('turbine_fraction,expected_states', ((.25, 8), (0., 6)))
def test_wt12_power_to_torque_and_blade_speed_feedback(
        turbine_fraction: float, expected_states: int,
) -> None:
    """Connect both mechanical masses to one governor without a duplicate inertia.

    :param turbine_fraction: Turbine inertia share; zero selects one mass.
    :param expected_states: Governor plus shaft state count.
    :return: None.
    """
    block: Block = build_wt12_mechanical_chain(
        VarFactory(), shaft_settings=Wt12t1DriveTrainSettings(
            htfrac=turbine_fraction, initial_speed=1.03,
        ),
    ).block
    electrical_power: Var = block.in_vars[0]
    electrical_torque: Var = block.in_vars[1]
    mechanical_power: Var = block.out_vars[0]
    mechanical_torque: Var = block.out_vars[1]
    generator_speed: Var = block.out_vars[2]
    turbine_speed: Var = block.out_vars[3]
    assert len(block.state_vars) == expected_states
    assert block.state_eqs[1].contains_var(turbine_speed)
    assert not block.state_eqs[1].contains_var(generator_speed)
    assert block.state_eqs[-2].contains_var(electrical_torque)
    assert block.algebraic_eqs[-1].contains_var(mechanical_power)
    assert block.algebraic_eqs[-1].contains_var(turbine_speed)
    assert block.algebraic_eqs[-1].eval_uid({
        mechanical_torque.uid: .5,
        mechanical_power.uid: .515,
        turbine_speed.uid: 1.03,
    }) == pytest.approx(0.)
    assert block.init_eqs[mechanical_torque].eval_uid({
        electrical_power.uid: .515,
        turbine_speed.uid: 1.03,
    }) == pytest.approx(.5)
