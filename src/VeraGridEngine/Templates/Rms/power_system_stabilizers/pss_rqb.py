# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the canonical CGMES PssRQB model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.procedural_logic import delay
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class PssRQBParameters:
    """Canonical PssRQB scalar parameters."""

    __slots__ = ('ki2', 'ki3', 'ki4', 't4m', 'tomd', 'tomsl', 't4mom', 'sibv', 'kdpm', 't4f')

    def __init__(
            self,
            ki2: float = 3.43,
            ki3: float = -11.45,
            ki4: float = 11.86,
            t4m: float = 5.0,
            tomd: float = 0.02,
            tomsl: float = 0.04,
            t4mom: float = 1.27,
            sibv: float = 0.006,
            kdpm: float = 0.185,
            t4f: float = 0.045,
    ) -> None:
        """Retain the CGMES attributes with the standard typical values.

        :param ki2: Speed-channel gain.
        :param ki3: Electrical-power-channel gain.
        :param ki4: Mechanical-power-channel gain.
        :param t4m: Electrical and mechanical power measurement time.
        :param tomd: Rotor-speed transport delay.
        :param tomsl: Rotor-speed measurement lag.
        :param t4mom: Speed-signal washout time.
        :param sibv: Speed-input deadband.
        :param kdpm: Mechanical-power lead coefficient.
        :param t4f: Mechanical-power lead-lag time.
        """
        self.ki2: float = ki2
        self.ki3: float = ki3
        self.ki4: float = ki4
        self.t4m: float = t4m
        self.tomd: float = tomd
        self.tomsl: float = tomsl
        self.t4mom: float = t4mom
        self.sibv: float = sibv
        self.kdpm: float = kdpm
        self.t4f: float = t4f


def build_pss_r_q_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: PssRQBParameters | None = None,
) -> RmsModelTemplate:
    """Build the IEC 61970-302 PssRQB measurement and stabilization graph.

    :param vfactory: Factory allocating equation and parameter symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Imported canonical CGMES values.
    :return: Controller with rotor speed, Pe, Pm and Vs ports.
    :raises ValueError: Invalid time constants, gains, or deadband.
    """
    settings: PssRQBParameters = PssRQBParameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        settings.ki2, settings.ki3, settings.ki4, settings.t4m, settings.tomd,
        settings.tomsl, settings.t4mom, settings.sibv, settings.kdpm, settings.t4f,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES PssRQB parameters must be finite')
    elif min(settings.t4m, settings.tomd, settings.tomsl, settings.t4mom, settings.t4f) < 0.0:
        raise ValueError('CGMES PssRQB time constants must be nonnegative')
    elif settings.sibv < 0.0:
        raise ValueError('CGMES PssRQB speed deadband must be nonnegative')
    elif settings.t4f == 0.0 and settings.kdpm != 0.0:
        raise ValueError('CGMES PssRQB T4F must be positive when KDPM is nonzero')
    else:
        pass

    template_name: str = 'PssRQB' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    speed: Var = model.input('OmegaPu', Const(1.0))
    electrical_power: Var = model.input('PePu', Const(0.0))
    mechanical_power: Var = model.input('PmPu', Const(0.0))
    delay_time: Var = model.parameter('PssRQB.tomd', settings.tomd)

    # The IEC diagram models shaft speed as a delayed, filtered 50 Hz frequency.
    if settings.tomd > 0.0:
        speed_delay: Var = vfactory.add_var(f'DelayedOmegaPu_{template_name}')
        model.block.mode_dict[speed_delay] = Const(0.0)
        model.block.init_eqs[speed_delay] = speed
        model.block.procedural_logic.append(delay(
            speed,
            delay_time,
            speed_delay,
            name=f'PssRQB.Delay_{template_name}',
        ))
    else:
        speed_delay = speed
    speed_filter: Var = model.lag(
        'FilteredOmegaPu', speed_delay,
        model.parameter('PssRQB.tomsl', settings.tomsl), settings.tomsl, speed_delay,
    )
    speed_error: Var = model.algebraic(
        'SpeedErrorRadPerSecond',
        Const(100.0 * math.pi) * (speed_filter - Const(1.0)),
        Const(0.0),
    )
    speed_washout: Var
    washout_time: Var = model.parameter('PssRQB.t4mom', settings.t4mom)
    if settings.t4mom > 0.0:
        speed_washout = model.washout(
            'SpeedWashout', speed_error,
            washout_time, settings.t4mom,
            Const(1.0), Const(0.0),
        )
    else:
        speed_washout = model.algebraic('SpeedWashout', Const(0.0), Const(0.0))
    speed_deadband: Var = model.parameter('PssRQB.sibv', settings.sibv)
    positive_speed: Var = model.algebraic(
        'PositiveDeadbandSignal',
        (speed_washout - speed_deadband) * sym.heaviside(speed_washout - speed_deadband),
        Const(0.0),
    )
    negative_speed: Var = model.algebraic(
        'NegativeDeadbandSignal',
        (speed_washout + speed_deadband) * sym.heaviside(-speed_washout - speed_deadband),
        Const(0.0),
    )
    speed_channel: Var = model.algebraic(
        'SpeedChannelPu', model.parameter('PssRQB.ki2', settings.ki2)
        * (positive_speed + negative_speed), Const(0.0),
    )

    power_measurement_time: Var = model.parameter('PssRQB.t4m', settings.t4m)
    measured_electrical_power: Var = model.lag(
        'MeasuredElectricalPowerPu', electrical_power,
        power_measurement_time, settings.t4m, electrical_power,
    )
    electrical_channel: Var = model.algebraic(
        'ElectricalPowerChannelPu',
        model.parameter('PssRQB.ki3', settings.ki3) * measured_electrical_power,
        Const(settings.ki3) * electrical_power,
    )
    measured_mechanical_power: Var = model.lag(
        'MeasuredMechanicalPowerPu', mechanical_power,
        power_measurement_time, settings.t4m, mechanical_power,
    )
    mechanical_lead_gain: Var = model.parameter('PssRQB.kdpm', settings.kdpm)
    mechanical_lead_lag_time: Var = model.parameter('PssRQB.t4f', settings.t4f)
    mechanical_compensation: Var = model.lead_lag(
        'MechanicalPowerCompensationPu', measured_mechanical_power,
        mechanical_lead_gain + mechanical_lead_lag_time,
        mechanical_lead_lag_time,
        settings.kdpm + settings.t4f, settings.t4f, mechanical_power,
    )
    mechanical_channel: Var = model.algebraic(
        'MechanicalPowerChannelPu',
        model.parameter('PssRQB.ki4', settings.ki4) * mechanical_compensation,
        Const(settings.ki4) * mechanical_power,
    )
    output: Var = model.algebraic(
        'VsPu', speed_channel + electrical_channel + mechanical_channel,
        speed_channel + electrical_channel + mechanical_channel,
    )
    template: RmsModelTemplate = model.finish((output,), 'CGMES PssRQB power-system stabilizer')
    template.comment = (
        'CGMES PssRQB IEC 61970-302 Fig. 152: delayed speed washout/deadband, '
        'filtered Pe and compensated Pm channels.'
    )
    enabled: Var = vfactory.add_var(f'PssRQB.enabled_{template_name}')
    template.block.event_dict[enabled] = vfactory.add_const(value=None)
    return template
