# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Thermal relay channel for the PSS/E ACMT compressor model."""
from __future__ import annotations

import math

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import CmpOp, Comparison, Const, Expr, Var


class AcmtThermalParameters:
    """Store the compressor winding thermal relay settings."""

    __slots__ = ('time_constant', 'trip_start_temperature', 'trip_end_temperature', 'initial_temperature')

    def __init__(
            self,
            time_constant: float,
            trip_start_temperature: float,
            trip_end_temperature: float,
            initial_temperature: float,
    ) -> None:
        """Store thermal constants and the solved initial winding temperature.

        :param time_constant: Winding temperature filter time constant in seconds.
        :param trip_start_temperature: Temperature where thermal tripping starts.
        :param trip_end_temperature: Temperature where the protected fraction is zero.
        :param initial_temperature: Solved initial output of the winding thermal filter.
        """
        self.time_constant: float = time_constant
        self.trip_start_temperature: float = trip_start_temperature
        self.trip_end_temperature: float = trip_end_temperature
        self.initial_temperature: float = initial_temperature


def build_acmt_thermal_relay(
        vf: VarFactory,
        name: str,
        parameters: AcmtThermalParameters,
) -> RmsModelTemplate:
    """Build one ACMT thermal state and its surviving compressor fraction.

    The host supplies ``I²Rstall`` as ``StallHeatPu``. PSS/E specifies immediate
    full tripping at the start threshold when ``Th2t`` is zero or ``Th1t >= Th2t``.

    :param vf: Variable factory owning the component symbols.
    :param name: Unique thermal-channel instance name.
    :param parameters: Thermal settings and initial state.
    :return: Component with temperature input and surviving-fraction output.
    :raises ValueError: If the thermal settings are nonfinite or invalid.
    """
    settings: tuple[float, ...] = (
        parameters.time_constant, parameters.trip_start_temperature,
        parameters.trip_end_temperature, parameters.initial_temperature,
    )
    if not all(math.isfinite(value) for value in settings):
        raise ValueError('ACMT thermal settings must be finite')
    elif parameters.time_constant < 0.0 or parameters.initial_temperature < 0.0:
        raise ValueError('ACMT thermal time and initial temperature must be nonnegative')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    heat: Var = control.input('StallHeatPu', Const(parameters.initial_temperature))
    time_constant: Var = control.parameter('Tth', parameters.time_constant)
    temperature: Var = control.lag(
        'WindingTemperaturePu', heat, time_constant, parameters.time_constant,
        Const(parameters.initial_temperature),
    )
    if (parameters.trip_end_temperature == 0.0
            or parameters.trip_start_temperature >= parameters.trip_end_temperature):
        surviving_fraction: Expr = Comparison(
            temperature, CmpOp.LT, Const(parameters.trip_start_temperature),
        ).to_expression()
        if parameters.initial_temperature < parameters.trip_start_temperature:
            initial_fraction: float = 1.0
        else:
            initial_fraction = 0.0
    else:
        surviving_fraction = sym.hard_sat(
            (Const(parameters.trip_end_temperature) - temperature)
            / Const(parameters.trip_end_temperature - parameters.trip_start_temperature),
            Const(0.0), Const(1.0),
        )
        initial_fraction = min(max(
            (parameters.trip_end_temperature - parameters.initial_temperature)
            / (parameters.trip_end_temperature - parameters.trip_start_temperature),
            0.0,
        ), 1.0)
    fraction_output: Var = control.algebraic(
        'ThermallyConnectedFraction', surviving_fraction, Const(initial_fraction),
    )
    return control.finish(
        (temperature, fraction_output),
        'PSS/E ACMT winding thermal filter and tripped-fraction curve.',
    )
