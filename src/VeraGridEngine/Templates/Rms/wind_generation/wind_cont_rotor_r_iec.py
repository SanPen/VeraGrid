# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed IEC 61400-27-1 rotor-resistance controller."""

import math
from typing import Sequence

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_catalogue import (
    _build_clipped_lookup_expression,
)
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_wind_cont_rotor_r_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        kirr: float = 0.0,
        komegafilt: float = 1.0,
        kpfilt: float = 1.0,
        kprr: float = 0.0,
        rmax: float = 1.0,
        rmin: float = 0.0,
        tomegafiltrr: float = 0.0,
        tpfiltrr: float = 0.0,
        prr_curve: Sequence[tuple[float, float]] = (),
        initial_power: float = 0.0,
        initial_speed: float = 1.0,
        initial_frequency: float = 1.0,
        initial_rotor_resistance: float | None = None,
) -> RmsModelTemplate:
    """Build IEC Figure 30 filtered power/slip PI rotor-resistance control.

    :param vfactory: Factory allocating equation variables.
    :param name: Optional unique runtime model name.
    :param kirr: Rotor-resistance PI integral gain.
    :param komegafilt: Generator-speed filter gain.
    :param kpfilt: Active-power filter gain.
    :param kprr: Rotor-resistance PI proportional gain.
    :param rmax: Maximum rotor resistance in the IEC base.
    :param rmin: Minimum rotor resistance in the IEC base.
    :param tomegafiltrr: Generator-speed filter time constant in seconds.
    :param tpfiltrr: Active-power filter time constant in seconds.
    :param prr_curve: Ordered `(slip, power)` lookup points.
    :param initial_power: Solved generator active power in pu.
    :param initial_speed: Solved generator speed in pu.
    :param initial_frequency: Solved stator frequency in pu.
    :param initial_rotor_resistance: Solved rotor resistance; defaults to ``rmin``.
    :return: Equation-backed `RrotPu` output and explicit power/speed/frequency inputs.
    :raises ValueError: Invalid parameters, lookup curve, or initial rotor resistance.
    """
    initial_resistance: float = rmin if initial_rotor_resistance is None else initial_rotor_resistance
    scalar_values: tuple[float, ...] = (
        kirr, komegafilt, kpfilt, kprr, rmax, rmin, tomegafiltrr, tpfiltrr,
        initial_power, initial_speed, initial_frequency, initial_resistance,
    )
    if not all(math.isfinite(value) for value in scalar_values):
        raise ValueError('CGMES WindContRotorRIEC values must be finite')
    elif min(kirr, komegafilt, kpfilt, kprr, tomegafiltrr, tpfiltrr, initial_power) < 0.0:
        raise ValueError('CGMES WindContRotorRIEC gains, times and power must be nonnegative')
    elif rmin < 0.0 or rmax <= rmin or not rmin <= initial_resistance <= rmax:
        raise ValueError('CGMES WindContRotorRIEC requires rmin <= initial resistance <= rmax')
    elif len(prr_curve) < 2:
        raise ValueError('CGMES WindContRotorRIEC requires at least two prr lookup points')
    else:
        pass

    point_index: int
    for point_index in range(len(prr_curve)):
        slip_point: float = float(prr_curve[point_index][0])
        power_point: float = float(prr_curve[point_index][1])
        if not math.isfinite(slip_point) or not math.isfinite(power_point):
            raise ValueError('CGMES WindContRotorRIEC lookup values must be finite')
        elif point_index > 0 and slip_point <= float(prr_curve[point_index - 1][0]):
            raise ValueError('CGMES WindContRotorRIEC slip lookup values must increase')
        else:
            pass
    else:
        pass

    template_name: str = 'WindContRotorRIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    integral_gain: Var = model.parameter('WindContRotorRIEC.kirr', kirr)
    speed_filter_gain: Var = model.parameter('WindContRotorRIEC.komegafilt', komegafilt)
    power_filter_gain: Var = model.parameter('WindContRotorRIEC.kpfilt', kpfilt)
    proportional_gain: Var = model.parameter('WindContRotorRIEC.kprr', kprr)
    resistance_maximum: Var = model.parameter('WindContRotorRIEC.rmax', rmax)
    resistance_minimum: Var = model.parameter('WindContRotorRIEC.rmin', rmin)
    speed_filter_time: Var = model.parameter('WindContRotorRIEC.tomegafiltrr', tomegafiltrr)
    power_filter_time: Var = model.parameter('WindContRotorRIEC.tpfiltrr', tpfiltrr)

    active_power: Var = model.input('PwtPu', Const(initial_power))
    generator_speed: Var = model.input('OmegaGenPu', Const(initial_speed))
    stator_frequency: Var = model.input('FwtPu', Const(initial_frequency))
    filtered_power: Var = model.lag(
        'FilteredPwtPu', power_filter_gain * active_power, power_filter_time,
        tpfiltrr, Const(kpfilt * initial_power),
    )
    filtered_speed: Var = model.lag(
        'FilteredOmegaGenPu', speed_filter_gain * generator_speed,
        speed_filter_time, tomegafiltrr, Const(komegafilt * initial_speed),
    )

    lookup_slip: list[Var] = list()
    lookup_power: list[Var] = list()
    for point_index in range(len(prr_curve)):
        lookup_slip.append(model.parameter(
            f'WindContRotorRIEC.prr_slip_{point_index}',
            float(prr_curve[point_index][0]),
        ))
        lookup_power.append(model.parameter(
            f'WindContRotorRIEC.prr_power_{point_index}',
            float(prr_curve[point_index][1]),
        ))
    else:
        pass

    # Generator sign convention uses filtered P minus the negative-slip lookup.
    speed_difference: Expr = stator_frequency - filtered_speed
    expected_rotor_power: Expr = _build_clipped_lookup_expression(
        speed_difference, lookup_slip, lookup_power,
    )
    controller_error: Expr = filtered_power - expected_rotor_power
    integral_state: Var = vfactory.add_var(f'WindRotorResistanceIntegral_{template_name}')
    initial_error: float = kpfilt * initial_power - _interpolate_prr_curve(
        prr_curve, initial_frequency - komegafilt * initial_speed,
    )
    initial_integral: Const = Const(initial_resistance - kprr * initial_error)
    integral_minimum: Expr = resistance_minimum - proportional_gain * controller_error
    integral_maximum: Expr = resistance_maximum - proportional_gain * controller_error
    model.differential(
        integral_state,
        integral_gain * controller_error,
        initial_integral,
        integral_minimum,
        integral_maximum,
    )
    rotor_resistance: Var = model.algebraic(
        'RrotPu',
        sym.hard_sat(
            proportional_gain * controller_error + integral_state,
            resistance_minimum,
            resistance_maximum,
        ),
        Const(initial_resistance),
    )
    # IEC 61400-27-1 leaves the machine equations external; its RrotPu interface has no defined machine base here.
    return model.finish(
        (rotor_resistance,),
        'IEC 61400-27-1:2015 Figure 30 filtered power/slip PI rotor-resistance controller.',
    )


def _interpolate_prr_curve(
        curve: Sequence[tuple[float, float]],
        value: float,
) -> float:
    """Evaluate the clipped piecewise-linear prr curve for controller seeding.

    :param curve: Strictly increasing slip/power points.
    :param value: Initial slip coordinate.
    :return: Clipped linearly interpolated power.
    """
    if value <= float(curve[0][0]):
        return float(curve[0][1])
    elif value >= float(curve[-1][0]):
        return float(curve[-1][1])
    else:
        pass
    for point_index in range(1, len(curve)):
        lower_slip: float = float(curve[point_index - 1][0])
        upper_slip: float = float(curve[point_index][0])
        if lower_slip <= value <= upper_slip:
            lower_power: float = float(curve[point_index - 1][1])
            upper_power: float = float(curve[point_index][1])
            fraction: float = (value - lower_slip) / (upper_slip - lower_slip)
            return lower_power + fraction * (upper_power - lower_power)
        else:
            pass
    else:
        pass
    return float(curve[-1][1])
