# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Connected unsaturated Type 2 wind electrical and mechanical core."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.induction_machines.wt2g1_electrical_core import (
    Wt2g1ElectricalSettings,
    build_wt2g1_electrical_core,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wt12a1_pseudo_governor import Wt12a1Settings
from VeraGridEngine.Templates.Rms.renewable_controls.wt12t1_drive_train import Wt12t1DriveTrainSettings
from VeraGridEngine.Templates.Rms.renewable_controls.wt2_control_chain import build_wt2_control_chain
from VeraGridEngine.Templates.Rms.renewable_controls.wt2e1_rotor_resistance import Wt2e1Settings
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def build_wt2_unsaturated_chain(
        vf: VarFactory, name: str = 'WT2 unsaturated chain',
        machine_settings: Wt2g1ElectricalSettings | None = None,
        governor_settings: Wt12a1Settings | None = None,
        shaft_settings: Wt12t1DriveTrainSettings | None = None,
        resistance_settings: Wt2e1Settings | None = None,
) -> RmsModelTemplate:
    """Close Type 2 electrical torque, shaft speed and rotor resistance.

    The terminal d/q voltages remain open to a network host. Nonzero magnetic
    saturation and power-flow Q-matching shunts remain outside this core.

    :param vf: Shared symbolic variable factory.
    :param name: Unique composite name.
    :param machine_settings: WT2G1 electrical data and initial operating point.
    :param governor_settings: WT12A1 pseudo-governor data.
    :param shaft_settings: WT12T1 shaft data.
    :param resistance_settings: WT2E1 and WT2G1 power-slip curve data.
    :return: Connected unsaturated Type 2 control and electrical graph.
    :raises ValueError: Inconsistent component operating points.
    """
    machine_selected: Wt2g1ElectricalSettings = (
        Wt2g1ElectricalSettings() if machine_settings is None else machine_settings
    )
    machine: RmsModelTemplate = build_wt2g1_electrical_core(
        vf, name + ' machine', machine_selected,
    )
    host: Block = machine.block
    initial_power_expr: Expr = host.init_eqs[host.out_vars[0]]
    initial_torque_expr: Expr = host.init_eqs[host.out_vars[2]]
    if not isinstance(initial_power_expr, Const) or not isinstance(initial_torque_expr, Const):
        raise ValueError('WT2G1 machine operating point must be a solved constant')
    else:
        pass
    initial_power: float = float(initial_power_expr.value)
    initial_torque: float = float(initial_torque_expr.value)
    shaft_selected: Wt12t1DriveTrainSettings = (
        Wt12t1DriveTrainSettings(initial_speed=machine_selected.initial_speed)
        if shaft_settings is None else shaft_settings
    )
    resistance_selected: Wt2e1Settings = (
        Wt2e1Settings(initial_speed=machine_selected.initial_speed,
                      initial_power=initial_power,
                      initial_fraction=machine_selected.initial_resistance_fraction)
        if resistance_settings is None else resistance_settings
    )
    if shaft_selected.initial_speed != machine_selected.initial_speed:
        raise ValueError('WT2 shaft and machine initial speeds must agree')
    elif (resistance_selected.initial_speed != machine_selected.initial_speed
          or not math.isclose(resistance_selected.initial_power, initial_power, rel_tol=1e-9, abs_tol=1e-12)
          or resistance_selected.initial_fraction != machine_selected.initial_resistance_fraction):
        raise ValueError('WT2 resistance control and machine initial values must agree')
    else:
        pass
    controls: RmsModelTemplate = build_wt2_control_chain(
        vf, name + ' controls', governor_settings, shaft_selected, resistance_selected,
    )
    control_block: Block = controls.block
    voltage_d: Var = host.in_vars[0]
    voltage_q: Var = host.in_vars[1]
    machine_speed: Var = host.in_vars[2]
    machine_resistance: Var = host.in_vars[3]
    machine_power: Var = host.out_vars[0]
    machine_torque: Var = host.out_vars[2]
    control_power: Var = control_block.in_vars[0]
    control_torque: Var = control_block.in_vars[1]
    power_reference: Var = control_block.in_vars[2]
    speed_reference: Var = control_block.in_vars[3]
    curve_offset: Var = control_block.in_vars[4]
    generator_speed: Var = control_block.out_vars[2]
    resistance_fraction: Var = control_block.out_vars[-1]
    outputs: list[Var] = list(host.out_vars)

    # Close the two physical feedback loops while preserving one machine-owned
    # electrical power and torque signal throughout the composite.
    host.merge_incoming_block(control_block)
    host.update_model_bulk({control_power: machine_power,
                            control_torque: machine_torque,
                            machine_speed: generator_speed,
                            machine_resistance: resistance_fraction})
    host.init_eqs[machine_power] = Const(initial_power)
    host.init_eqs[machine_torque] = Const(initial_torque)
    host.init_eqs[generator_speed] = Const(machine_selected.initial_speed)
    host.init_eqs[resistance_fraction] = Const(machine_selected.initial_resistance_fraction)
    host.in_vars = list((voltage_d, voltage_q, power_reference, speed_reference,
                         curve_offset))
    outputs.extend(control_block.out_vars)
    host.out_vars = outputs
    machine.comment = 'Unsaturated Type 2 electrical machine, shaft and rotor-resistance controls'
    return machine
