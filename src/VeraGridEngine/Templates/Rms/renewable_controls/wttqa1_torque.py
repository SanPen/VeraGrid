# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Native wind torque reference controller for the Type 3 wind chain."""
from __future__ import annotations

import math
from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Wttqa1TorqueMode(Enum):
    """Select the source TFLAG error entering the torque PI."""

    SPEED_ERROR = 0
    POWER_ERROR = 1


class Wttqa1TorqueSettings:
    """Store PI, filter, torque-stop and power-speed curve parameters."""

    __slots__ = ('kpp', 'kip', 'tp', 'twref', 'temax', 'temin', 'curve', 'trate', 'mode')

    def __init__(self, kpp: float = 1., kip: float = 1., tp: float = .05,
                 twref: float = 30., temax: float = 1.2, temin: float = 0.,
                 curve: tuple[tuple[float, float], ...] = ((0., 0.), (0., 0.), (0., 0.), (0., 0.)),
                 trate: float = 0., mode: Wttqa1TorqueMode = Wttqa1TorqueMode.SPEED_ERROR) -> None:
        """Store source parameters on turbine and machine power bases.

        :param kpp: Torque PI proportional gain.
        :param kip: Torque PI integral gain.
        :param tp: Electrical-power measurement filter time, seconds.
        :param twref: Speed-reference filter time, seconds.
        :param temax: Maximum torque request, per unit.
        :param temin: Minimum torque request, per unit.
        :param curve: Four ordered (power, shaft speed) pairs.
        :param trate: Turbine rating in MW; zero uses machine MVA base.
        :param mode: Speed-error or power-error TFLAG path.
        :return: None.
        """
        self.kpp: float = kpp
        self.kip: float = kip
        self.tp: float = tp
        self.twref: float = twref
        self.temax: float = temax
        self.temin: float = temin
        self.curve: tuple[tuple[float, float], ...] = curve
        self.trate: float = trate
        self.mode: Wttqa1TorqueMode = mode


def _validate_wttqa1_curve(curve: tuple[tuple[float, float], ...]) -> bool:
    """Accept four increasing pairs or the source's all-zero unity-speed code.

    :param curve: Power and shaft-speed pairs in source order.
    :return: Whether interpolation is well-defined.
    """
    if len(curve) != 4:
        return False
    elif all(power == 0 and speed == 0 for power, speed in curve):
        return True
    else:
        pass
    previous_power: float = -math.inf
    previous_speed: float = -math.inf
    power: float
    speed: float
    for power, speed in curve:
        if not math.isfinite(power) or not math.isfinite(speed) or power < 0 or speed <= 0:
            return False
        elif power <= previous_power or speed <= previous_speed:
            return False
        else:
            previous_power = power
            previous_speed = speed
    return True


def _wttqa1_speed_curve(
        control: ControlRealization, power: Expr,
        curve: tuple[tuple[float, float], ...],
) -> Expr:
    """Interpolate filtered power to shaft speed with held endpoints.

    :param control: Parameter and symbol owner.
    :param power: Filtered electrical power on the curve's power base.
    :param curve: Validated four-pair source table.
    :return: Shaft-speed reference in per unit.
    """
    if all(point_power == 0 and point_speed == 0 for point_power, point_speed in curve):
        return Const(1.)
    else:
        pass
    previous_p: Var = control.parameter('P1', curve[0][0])
    previous_speed: Var = control.parameter('SPD1', curve[0][1])
    result: Expr = previous_speed
    index: int
    for index in range(1, 4):
        next_p: Var = control.parameter('P' + str(index + 1), curve[index][0])
        next_speed: Var = control.parameter('SPD' + str(index + 1), curve[index][1])
        span: Expr = sym.hard_sat(power - previous_p, Const(0.), next_p - previous_p)
        result = result + (next_speed - previous_speed) * span / (next_p - previous_p)
        previous_p = next_p
        previous_speed = next_speed
    return result


def build_wttqa1_torque_template(
        vf: VarFactory,
        name: str = 'WTTQA1 torque',
        settings: Wttqa1TorqueSettings | None = None,
) -> RmsModelTemplate:
    """Build the filtered-power, speed-reference and bounded torque PI paths.

    Inputs are generator electrical power, generator speed, Pref0, fault flag
    and generator MVA base. Output is power reference for REECA1 PFLAG=0.
    A full source binding still needs the pitch and renewable electrical
    controllers and operating-point checks.

    :param vf: Shared symbolic variable factory.
    :param name: Unique torque-controller name.
    :param settings: Source controller parameters and mode.
    :return: Stand-alone native torque-control block.
    :raises ValueError: Invalid gains, limits, curve, time or mode.
    """
    selected: Wttqa1TorqueSettings = Wttqa1TorqueSettings() if settings is None else settings
    values: tuple[float, ...] = (selected.kpp, selected.kip, selected.tp, selected.twref,
                                 selected.temax, selected.temin, selected.trate)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('WTTQA1 settings must be finite')
    elif min(selected.kpp, selected.kip, selected.tp, selected.twref, selected.trate) < 0:
        raise ValueError('WTTQA1 gains, times and turbine rating are invalid')
    elif selected.temax <= selected.temin:
        raise ValueError('WTTQA1 torque limits are invalid')
    elif not isinstance(selected.mode, Wttqa1TorqueMode):
        raise ValueError('WTTQA1 TFLAG mode is invalid')
    elif not _validate_wttqa1_curve(selected.curve):
        raise ValueError('WTTQA1 power-speed curve is invalid')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    electrical_power: Var = control.input('ElectricalPowerPu', Const(0.))
    generator_speed: Var = control.input('GeneratorSpeedPu', Const(1.))
    pref0: Var = control.input('InitialPowerReferencePu', electrical_power)
    fault_flag: Var = control.input('VoltageDipFlag', Const(0.))
    machine_mva: Var = control.input('MachineBaseMva', Const(100.))
    kpp: Var = control.parameter('KPP', selected.kpp)
    kip: Var = control.parameter('KIP', selected.kip)
    tp: Var = control.parameter('TP', selected.tp)
    twref: Var = control.parameter('TWREF', selected.twref)
    temax: Var = control.parameter('TEMAX', selected.temax)
    temin: Var = control.parameter('TEMIN', selected.temin)
    trate: Var = control.parameter('TRATE', selected.trate)
    filtered_power: Var = control.lag('FilteredElectricalPowerPu', electrical_power,
                                      tp, selected.tp, electrical_power)
    curve_power: Expr = filtered_power
    if selected.trate > 0:
        curve_power = filtered_power * machine_mva / trate
    else:
        pass
    speed_target: Expr = _wttqa1_speed_curve(control, curve_power, selected.curve)
    initial_speed_target: Expr = speed_target.subs(dict(((filtered_power, electrical_power),)))
    speed_reference: Var = control.lag('SpeedReferencePu', speed_target,
                                       twref, selected.twref, initial_speed_target)
    error: Expr
    if selected.mode is Wttqa1TorqueMode.POWER_ERROR:
        error = (pref0 - filtered_power) / generator_speed
    else:
        error = generator_speed - speed_reference
    torque_integral: Var = vf.add_var('TorqueIntegral_' + name)
    torque: Var = control.algebraic(
        'TorqueCommandPu', sym.hard_sat(kpp * error + torque_integral, temin, temax),
        electrical_power / generator_speed,
    )
    control.differential(
        torque_integral, (Const(1.) - fault_flag) * kip * error,
        electrical_power / generator_speed, temin, temax,
    )
    power_reference: Var = control.algebraic(
        'PowerReferencePu', torque * generator_speed, electrical_power,
    )
    return control.finish((power_reference, speed_reference, torque),
                          'Wind torque PI and REECA power reference')
