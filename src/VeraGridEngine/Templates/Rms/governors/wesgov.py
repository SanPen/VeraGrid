# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Westinghouse sampled gas-turbine governor and deadband variant."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.procedural_logic import PeriodicSampleLogic, SampledPiLimiterLogic
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


class WesgovSettings:
    """Source parameters for WESGOV and WESGOVD."""

    __slots__ = (
        'delta_tc', 'delta_tp', 'droop', 'kp', 'ti', 't1', 't2', 'alim',
        'tpe', 'deadband_high', 'deadband_low',
    )

    def __init__(
            self,
            delta_tc: float,
            delta_tp: float,
            droop: float,
            kp: float,
            ti: float,
            t1: float,
            t2: float,
            alim: float,
            tpe: float,
            deadband_high: float = 0.0,
            deadband_low: float = 0.0,
    ) -> None:
        """Store and validate the source control, sample and lag values.

        :param delta_tc: Control sample interval in seconds.
        :param delta_tp: Electrical-power sample interval in seconds.
        :param droop: Speed droop on the selected governor power base.
        :param kp: Proportional gain of the sampled PI.
        :param ti: Positive integral time in seconds.
        :param t1: First mechanical-power lag time in seconds.
        :param t2: Second mechanical-power lag time in seconds.
        :param alim: Maximum absolute command change per control sample.
        :param tpe: Electrical-power measurement filter time in seconds.
        :param deadband_high: Nonnegative overspeed deadband for WESGOVD.
        :param deadband_low: Nonpositive underspeed deadband for WESGOVD.
        :raises ValueError: A source value is nonfinite or outside its documented domain.
        """
        values: tuple[float, ...] = (
            delta_tc, delta_tp, droop, kp, ti, t1, t2, alim, tpe,
            deadband_high, deadband_low,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError('WESGOV parameters must be finite')
        elif delta_tc <= 0.0 or delta_tp <= 0.0 or droop <= 0.0 or ti <= 0.0:
            raise ValueError('WESGOV sample periods, droop and TI must be positive')
        elif min(t1, t2, tpe, alim, deadband_high) < 0.0 or deadband_low > 0.0:
            raise ValueError('WESGOV lag, ALIM and deadband values are invalid')
        else:
            pass
        self.delta_tc: float = delta_tc
        self.delta_tp: float = delta_tp
        self.droop: float = droop
        self.kp: float = kp
        self.ti: float = ti
        self.t1: float = t1
        self.t2: float = t2
        self.alim: float = alim
        self.tpe: float = tpe
        self.deadband_high: float = deadband_high
        self.deadband_low: float = deadband_low


def build_wesgov_template(
        vf: VarFactory,
        settings: WesgovSettings,
        name: str = 'WESGOV',
) -> RmsModelTemplate:
    """Build the sampled WESGOV control and two-lag mechanical-power chain.

    Speed is sampled every ``delta_tc``. Electrical power first passes through
    the PSS/E ``Tpe`` transducer and is sampled every ``delta_tp``. The sampled
    droop/power error updates the PI command every ``delta_tc``; each command
    movement is limited by ``alim`` before the ``T1`` and ``T2`` lags.

    :param vf: Shared symbolic variable factory.
    :param settings: Validated PSS/E source parameters.
    :param name: Unique template instance name.
    :return: Open-port governor block whose output is mechanical power on its
        selected PSS/E base.
    """
    control: ControlRealization = ControlRealization(vf, name)
    speed: Var = control.input('MachineSpeedPu', Const(1.0))
    electrical_power: Var = control.input('ElectricalPowerPu', Const(0.0))
    reference: Var = control.input('MechanicalPowerReferencePu', Const(0.0))
    tpe: Var = control.parameter('Tpe', settings.tpe)
    droop: Var = control.parameter('Droop', settings.droop)
    ti: Var = control.parameter('Ti', settings.ti)
    t1: Var = control.parameter('T1', settings.t1)
    t2: Var = control.parameter('T2', settings.t2)
    alim: Var = control.parameter('Alim', settings.alim)

    speed_deviation: Var = control.speed_deviation(
        speed,
        lower=settings.deadband_low,
        upper=settings.deadband_high,
    )
    pe_filter: Var = control.lag(
        'FilteredElectricalPowerPu',
        electrical_power,
        tpe,
        settings.tpe,
        electrical_power,
    )
    sampled_speed: Var = control.parameter('SampledSpeedDeviationPu', 0.0)
    sampled_power: Var = control.parameter('SampledElectricalPowerPu', 0.0)
    valve_command: Var = control.parameter('ValveCommandPu', 0.0)
    control.block.procedural_logic.append(PeriodicSampleLogic(
        output_var_name=sampled_speed.name,
        output_var_uid=sampled_speed.uid,
        source_expr=speed_deviation,
        sample_period=settings.delta_tc,
        name='WESGOV speed sample',
    ))
    control.block.procedural_logic.append(PeriodicSampleLogic(
        output_var_name=sampled_power.name,
        output_var_uid=sampled_power.uid,
        source_expr=pe_filter,
        sample_period=settings.delta_tp,
        name='WESGOV electrical-power sample',
    ))
    error: Expr = reference - sampled_power - sampled_speed / droop
    control.block.procedural_logic.append(SampledPiLimiterLogic(
        output_var_name=valve_command.name,
        output_var_uid=valve_command.uid,
        error_expr=error,
        sample_period=settings.delta_tc,
        proportional_gain=settings.kp,
        integral_time=settings.ti,
        maximum_change=settings.alim,
        name='WESGOV sampled PI and ALIM',
    ))

    valve_position: Var = control.lag(
        'ValvePositionPu', valve_command, t1, settings.t1, Const(0.0),
    )
    mechanical_power: Var = control.lag(
        'MechanicalPowerPu', valve_position, t2, settings.t2, Const(0.0),
    )
    return control.finish(
        (mechanical_power,),
        'Sampled WESGOV PI governor with PSS/E speed/power holds and two turbine lags',
    )
