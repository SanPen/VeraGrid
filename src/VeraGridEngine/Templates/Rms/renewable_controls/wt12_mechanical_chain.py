# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Connected Type 1/2 wind governor and shaft mechanical path."""
from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.wt12a1_pseudo_governor import (
    Wt12a1Settings,
    build_wt12a1_pseudo_governor_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wt12t1_drive_train import (
    Wt12t1DriveTrainSettings,
    build_wt12t1_drive_train_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var


def build_wt12_mechanical_chain(
        vf: VarFactory, name: str = 'WT12 Type 1/2 mechanical chain',
        governor_settings: Wt12a1Settings | None = None,
        shaft_settings: Wt12t1DriveTrainSettings | None = None,
) -> RmsModelTemplate:
    """Connect WT12A1 power control to WT12T1 blade-speed feedback.

    The first two inputs are electrical power and electrical torque from the
    induction machine. The machine host must make them consistent with its
    electrical states and generator speed.

    :param vf: Shared symbolic variable factory.
    :param name: Unique composite name.
    :param governor_settings: WT12A1 source parameters.
    :param shaft_settings: WT12T1 source parameters and initial machine speed.
    :return: Connected mechanical template with open machine inputs.
    """
    governor: RmsModelTemplate = build_wt12a1_pseudo_governor_template(
        vf, name + ' governor', governor_settings,
    )
    shaft: RmsModelTemplate = build_wt12t1_drive_train_template(
        vf, name + ' shaft', shaft_settings,
    )
    host: Block = governor.block
    shaft_block: Block = shaft.block
    electrical_power: Var = host.in_vars[0]
    power_reference: Var = host.in_vars[2]
    speed_reference: Var = host.in_vars[3]
    mechanical_power: Var = host.out_vars[0]
    electrical_torque: Var = shaft_block.in_vars[0]
    mechanical_torque: Var = shaft_block.in_vars[1]
    generator_speed: Var = shaft_block.out_vars[0]
    turbine_speed: Var = shaft_block.out_vars[1]

    # The governor measures blade-side speed, while the shaft receives its
    # mechanical command as torque on the common machine MVA base.
    host.merge_incoming_block(shaft_block)
    host.update_model_bulk({host.in_vars[1]: turbine_speed})
    host.algebraic_vars.append(mechanical_torque)
    torque_equation: Expr = mechanical_torque - mechanical_power / turbine_speed
    host.algebraic_eqs.append(torque_equation)
    host.init_eqs[mechanical_torque] = electrical_power / turbine_speed
    host.in_vars = list((electrical_power, electrical_torque, power_reference, speed_reference))
    host.out_vars = list((mechanical_power, mechanical_torque, generator_speed,
                          turbine_speed, shaft_block.out_vars[2]))
    governor.comment = 'WT12A1 governor and WT12T1 shaft with open induction-machine power and torque'
    return governor
