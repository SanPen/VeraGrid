# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Unsaturated Type 2 wind chain with the WT12A1U_B active-stall controller."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.induction_machines.wt2g1_electrical_core import (
    Wt2g1ElectricalSettings, build_wt2g1_electrical_core,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wt12a1u_b_active_stall import (
    Wt12a1uBSettings, build_wt12a1u_b_active_stall_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wt12t1_drive_train import (
    Wt12t1DriveTrainSettings, build_wt12t1_drive_train_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.wt2e1_rotor_resistance import (
    Wt2e1Settings, build_wt2e1_rotor_resistance_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Utils.procedural_logic import ProceduralLogicBase


def build_wt2_active_stall_chain(
        vf: VarFactory, name: str = 'WT2 active-stall chain',
        machine_settings: Wt2g1ElectricalSettings | None = None,
        stall_settings: Wt12a1uBSettings | None = None,
        shaft_settings: Wt12t1DriveTrainSettings | None = None,
        resistance_settings: Wt2e1Settings | None = None,
) -> RmsModelTemplate:
    """Connect active stall, shaft and rotor control to one Type 2 machine.

    The active-stall controller receives live terminal voltage and the fixed
    initial mechanical power. Electrical power and torque feed the resistance
    controller and shaft; the network host supplies the d/q terminal voltage.

    :param vf: Shared symbolic variable factory.
    :param name: Unique connected model name.
    :param machine_settings: Unsaturated WT2G1 source data and operating point.
    :param stall_settings: WT12A1U_B controller source data.
    :param shaft_settings: WT12T1 shaft data.
    :param resistance_settings: WT2E1 rotor-resistance controller data.
    :return: Connected Type 2 machine with active-stall mechanical power.
    :raises ValueError: Inconsistent component initial operating points.
    """
    selected_machine: Wt2g1ElectricalSettings = (
        Wt2g1ElectricalSettings() if machine_settings is None else machine_settings
    )
    machine: RmsModelTemplate = build_wt2g1_electrical_core(
        vf, name + ' machine', selected_machine,
    )
    host: Block = machine.block
    initial_power_expr: Expr = host.init_eqs[host.out_vars[0]]
    initial_torque_expr: Expr = host.init_eqs[host.out_vars[2]]
    if not isinstance(initial_power_expr, Const) or not isinstance(initial_torque_expr, Const):
        raise ValueError('WT2 active-stall machine operating point must be constant')
    else:
        pass
    initial_power: float = float(initial_power_expr.value)
    initial_torque: float = float(initial_torque_expr.value)
    selected_shaft: Wt12t1DriveTrainSettings = (
        Wt12t1DriveTrainSettings(initial_speed=selected_machine.initial_speed)
        if shaft_settings is None else shaft_settings
    )
    selected_resistance: Wt2e1Settings = (
        Wt2e1Settings(initial_speed=selected_machine.initial_speed,
                      initial_power=initial_power,
                      initial_fraction=selected_machine.initial_resistance_fraction)
        if resistance_settings is None else resistance_settings
    )
    if selected_shaft.initial_speed != selected_machine.initial_speed:
        raise ValueError('WT2 active-stall shaft and machine speeds must agree')
    elif (selected_resistance.initial_speed != selected_machine.initial_speed
          or not math.isclose(selected_resistance.initial_power, initial_power,
                              rel_tol=1e-9, abs_tol=1e-12)
          or selected_resistance.initial_fraction != selected_machine.initial_resistance_fraction):
        raise ValueError('WT2 active-stall resistance and machine initial values must agree')
    else:
        pass

    stall: Block = build_wt12a1u_b_active_stall_template(
        vf, name + ' stall', stall_settings,
    ).block
    shaft: Block = build_wt12t1_drive_train_template(
        vf, name + ' shaft', selected_shaft,
    ).block
    resistance: Block = build_wt2e1_rotor_resistance_template(
        vf, name + ' resistance', selected_resistance,
    ).block
    voltage_d: Var = host.in_vars[0]
    voltage_q: Var = host.in_vars[1]
    machine_speed: Var = host.in_vars[2]
    machine_resistance: Var = host.in_vars[3]
    electrical_power: Var = host.out_vars[0]
    electrical_torque: Var = host.out_vars[2]
    generator_speed: Var = shaft.out_vars[0]
    turbine_speed: Var = shaft.out_vars[1]
    resistance_fraction: Var = resistance.out_vars[0]
    rotor_offset: Var = resistance.in_vars[2]
    stall_power: Var = stall.out_vars[0]
    source_outputs: list[Var] = list(host.out_vars)
    source_outputs.extend(stall.out_vars)
    source_outputs.extend(shaft.out_vars)
    source_outputs.extend(resistance.out_vars)

    # The shaft must start at the machine's air-gap torque. Its initial
    # mechanical power is held as a constant during later voltage faults.
    initial_mechanical_power: Var = vf.add_var('InitialMechanicalPowerPu_' + name)
    host.event_dict[initial_mechanical_power] = Const(initial_torque * selected_machine.initial_speed)
    mechanical_torque: Var = vf.add_var('MechanicalTorquePu_' + name)
    terminal_voltage: Var = vf.add_var('TerminalVoltagePu_' + name)
    host.algebraic_vars.extend((mechanical_torque, terminal_voltage))
    host.algebraic_eqs.extend((mechanical_torque - stall_power / turbine_speed,
                              terminal_voltage - sym.sqrt(voltage_d * voltage_d
                                                          + voltage_q * voltage_q)))
    host.init_eqs[mechanical_torque] = Const(initial_torque)
    host.init_eqs[terminal_voltage] = Const(math.hypot(selected_machine.initial_vd,
                                                       selected_machine.initial_vq))
    host.merge_incoming_block(stall)
    host.merge_incoming_block(shaft)
    host.merge_incoming_block(resistance)
    stall_logic: ProceduralLogicBase
    for stall_logic in stall.procedural_logic:
        host.procedural_logic.append(stall_logic)
    host.update_model_bulk({
        stall.in_vars[0]: terminal_voltage,
        stall.in_vars[1]: initial_mechanical_power,
        shaft.in_vars[0]: electrical_torque,
        shaft.in_vars[1]: mechanical_torque,
        resistance.in_vars[0]: generator_speed,
        resistance.in_vars[1]: electrical_power,
        machine_speed: generator_speed,
        machine_resistance: resistance_fraction,
    })
    host.init_eqs[electrical_power] = Const(initial_power)
    host.init_eqs[electrical_torque] = Const(initial_torque)
    host.init_eqs[generator_speed] = Const(selected_machine.initial_speed)
    host.init_eqs[resistance_fraction] = Const(selected_machine.initial_resistance_fraction)
    host.in_vars = list((voltage_d, voltage_q, rotor_offset))
    host.out_vars = source_outputs
    machine.comment = 'Unsaturated Type 2 machine with active stall, shaft and rotor resistance'
    return machine
