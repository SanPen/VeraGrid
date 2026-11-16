# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Connected Type 2 wind shaft, pseudo governor and rotor-resistance control."""
from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.wt12_mechanical_chain import (
    build_wt12_mechanical_chain,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wt12a1_pseudo_governor import Wt12a1Settings
from VeraGridEngine.Templates.Rms.renewable_controls.wt12t1_drive_train import Wt12t1DriveTrainSettings
from VeraGridEngine.Templates.Rms.renewable_controls.wt2e1_rotor_resistance import (
    Wt2e1Settings,
    build_wt2e1_rotor_resistance_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var


def build_wt2_control_chain(
        vf: VarFactory, name: str = 'WT2 Type 2 controls',
        governor_settings: Wt12a1Settings | None = None,
        shaft_settings: Wt12t1DriveTrainSettings | None = None,
        resistance_settings: Wt2e1Settings | None = None,
) -> RmsModelTemplate:
    """Share machine P/Te and generator speed across the Type 2 controls.

    The induction machine must still supply electrical power and torque and
    consume the external rotor-resistance fraction. The offset is an explicit
    initial operating-point input until that machine host is connected.

    :param vf: Shared symbolic variable factory.
    :param name: Unique Type 2 control-chain name.
    :param governor_settings: WT12A1 pseudo-governor data.
    :param shaft_settings: WT12T1 shaft data and initial speed.
    :param resistance_settings: WT2E1 and WT2G1 curve data.
    :return: Connected Type 2 control graph with open electrical machine ports.
    :raises ValueError: Inconsistent machine initial speed across components.
    """
    shaft_selected: Wt12t1DriveTrainSettings = (
        Wt12t1DriveTrainSettings() if shaft_settings is None else shaft_settings
    )
    resistance_selected: Wt2e1Settings = Wt2e1Settings() if resistance_settings is None else resistance_settings
    if shaft_selected.initial_speed != resistance_selected.initial_speed:
        raise ValueError('WT2 shaft and resistance controller need the same initial generator speed')
    else:
        pass
    template: RmsModelTemplate = build_wt12_mechanical_chain(
        vf, name + ' mechanical', governor_settings, shaft_selected,
    )
    host: Block = template.block
    resistance_template: RmsModelTemplate = build_wt2e1_rotor_resistance_template(
        vf, name + ' resistance', resistance_selected,
    )
    resistance_block: Block = resistance_template.block
    electrical_power: Var = host.in_vars[0]
    electrical_torque: Var = host.in_vars[1]
    power_reference: Var = host.in_vars[2]
    speed_reference: Var = host.in_vars[3]
    generator_speed: Var = host.out_vars[2]
    offset: Var = resistance_block.in_vars[2]
    resistance_fraction: Var = resistance_block.out_vars[0]
    outputs: list[Var] = list(host.out_vars)

    # The WT2E1 filters measure the same machine power and shaft speed that
    # close the Type 1/2 mechanical controls.
    host.merge_incoming_block(resistance_block)
    host.update_model_bulk({resistance_block.in_vars[0]: generator_speed,
                            resistance_block.in_vars[1]: electrical_power})
    host.in_vars = list((electrical_power, electrical_torque, power_reference,
                         speed_reference, offset))
    outputs.append(resistance_fraction)
    host.out_vars = outputs
    template.comment = 'Type 2 shaft, pseudo governor and rotor-resistance controller with open machine ports'
    return template
